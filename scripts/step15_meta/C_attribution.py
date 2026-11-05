"""step15 C：归因——同一类改动在不同论文里倍数为什么不同（11-06 用户同意先做；不花钱，只用开发集，不碰考试集）。

数据：方案 A 的比较表与两步估计（A_meta.load、stage1：先扣掉全类共用的条件效应）。只用开发集。
C1 调节因素：对每类性能、每个主改动组（开发集 ≥ 3 篇），逐个检验“调节因素”能否解释各篇倍数的差别：
   效应 dy_adj ~ 1 + 调节因素 + 论文随机效应（与 A 相同的 MixedLM / OLS 聚类）。调节因素（都取参照一侧、即比较所在的情境）：
   - 测试条件：锂硫类 ln E/S、硫载量、正极含硫、ln 倍率、软包；Li‖Cu ln 电流、ln 沉积容量、Aurbach 法；
   - 参照是否含 LiNO₃、参照是否标准醚；改动幅度（本组对应描述符的 |Δ|，见 SIZE）；论文编号（≈ 发表年份顺序）；
   - 同测试比较还是跨测试比较；数据是否用了默认值或换算（E/S、温度、溶剂比例默认，基准未写明，由容量换算）。
   输出：斜率、95% 区间、论文层面置换检验 p（少数论文时聚类标准误偏小，判定改用置换 p）及其 BH q 值（每类全部检验一起校正）、
   论文间差异减少比例，以及留一篇检验：
   每次留出一篇，用其余论文预测这篇的效应，比较“只用合并倍数”和“合并倍数＋调节因素”的误差（误差降低比例 > 0 才算让倍数变准）。
   最低数据量：≥ 5 篇；二值因素每个取值 ≥ 2 篇；连续因素各篇平均值 ≥ 4 个不同取值（只有 3 篇时一条线总能穿过 3 个点、
   聚类标准误又被低估，第一次运行出现过 q≈0 的假发现）。组小、检验多，结果是探索性的：q < 0.1 且留一篇误差降低的才写成发现。
C2 条件化倍数：C1 里成立的，给出标准条件与实用条件（E/S 5、载量 4）下的倍数；另对方案 A 里 q < 0.1 的描述符
   检验 Δ描述符 × 参照条件 的交互（描述符的作用是否随条件变）。
C5 倍数能不能变准：按改动的定义方向（只看组成：浓度升高、配位位点变多、含氟比例升高、加入 X 等）把比较翻到同一方向，
   比较“原始 / 定向 / 定向＋只同测试”三种口径的论文间差异占比、方向一致比例和留一篇预测误差（见 c5）。
C3 矛盾候选与读原文：每组里平均效应与合并方向相反（且 |效应| > ln 1.05）或偏离合并值 3 倍以上的论文，
   列出两侧原句、配方文字、配方系统说明、本篇对比说明（comparison_notes）、相关机制、调节因素在本组的位置，
   写入 归因复核表.xlsx；Claude 读原文后的判定写在 归因判定.json（✅ 原因明确 / 🔶 有线索 / ⚠️ 数据或配对问题 / ❌ 没找到），
   ✍ 列留给用户。
用法：python -X utf8 C_attribution.py
"""
import sys
import json
import math
import re
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from A_meta import (load, stage1, offset, dys, papers, mixed, fit_mixed, bh, DESC_ALL, COND, STD, PRACT, CLASSES, INTER, NOTE,
                    dd, diffrec, interactions)

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
OUT = ROOT / "output" / "归因_313篇_2026-11-06"
AOUT = ROOT / "output" / "方案A_meta回归_313篇_2026-11-06"
PAP = ROOT / "output" / "试跑313篇_2026-11-05" / "papers"
STF = ROOT / "output" / "表述试跑313篇_2026-11-05" / "表述.json"
MEAS = ROOT / "output" / "meta共同准备_313篇_2026-11-06" / "测量表.json"
SIZE = {"加/换氟化醚": "溶剂_含氟分子比例", "LiNO₃ 用量": "LiNO3_M", "改浓度/配比": "ln_Li总浓度", "高浓": "ln_Li总浓度",
        "局部高浓": "稀释剂摩尔比例", "换溶剂（其他）": "ln_配位位点每Li", "加有机硫": "有机硫", "加介体": "介体"}
COND_MOD = {c: (["ln_电流", "ln_沉积容量", "Aurbach法"] if c == "LiCu_CE" else ["ln_ES", "载量", "含硫", "ln_倍率", "软包"]) for c in CLASSES}
MIN_EFF, BIG = math.log(1.05), math.log(3.0)
MIN_PAPERS = 5
JUDGE = OUT / "归因判定.json"


def moderators(q, cls, std_ether):
    m = {f"条件:{k}": q["参照条件"].get(k) for k in COND_MOD[cls]}
    ln = q["参照描述符"].get("LiNO3_M")
    m["参照含LiNO3"] = None if ln is None else float(ln > 0)
    m["参照是标准醚"] = std_ether.get((q["论文"], q["参照"]))
    d = SIZE.get(q["主改动"])
    m["改动幅度"] = None if d is None or q["Δ描述符"].get(d) is None else abs(q["Δ描述符"][d])
    m["论文编号（≈年份）"] = float(int(re.sub(r"\D", "", q["论文"]) or 0))
    m["同测试比较"] = float(q["配对类型"] == "同测试、不同配方")
    m["用了默认值或换算"] = float(any(("默认" in f) or f in ("基准未写明", "由容量换算") for f in q["标记"]))
    return m


def enough(R, x):
    """调节因素检验的最低数据量：≥ 5 篇；二值的每个取值 ≥ 2 篇；连续的各篇平均值 ≥ 4 个不同取值。
    （只有 3 篇时一条线总能穿过 3 个点，按论文聚类的标准误又被严重低估，会出现 q≈0 的假发现。）"""
    ps = papers(R)
    if len(set(ps)) < MIN_PAPERS:
        return False
    by = defaultdict(list)
    for p, v in zip(ps, x):
        by[p].append(v)
    pm = [round(float(np.mean(v)), 6) for v in by.values()]
    if set(np.round(x, 6)) <= {0.0, 1.0}:
        return sum(1 for v in by.values() if 1.0 in v) >= 2 and sum(1 for v in by.values() if 0.0 in v) >= 2
    return len(set(pm)) >= 4


def perm_p(R, ya, x, n=4000, seed=0):
    """论文层面的置换检验（少数论文的 meta 回归常用）：每篇取效应与调节因素的平均，按比较数加权求斜率；
    把调节因素在论文之间随机打乱，看打乱后斜率绝对值 ≥ 实际值的比例。论文 ≤ 7 篇时穷举全部排列。"""
    import itertools
    by = defaultdict(list)
    for r, a, v in zip(R, ya, x):
        by[r["论文"]].append((a, v))
    ps = sorted(by)
    Y = np.array([np.mean([a for a, _ in by[p]]) for p in ps]); X = np.array([np.mean([v for _, v in by[p]]) for p in ps])
    W = np.array([len(by[p]) for p in ps], float)

    def slope(xx):
        xm, ym = np.average(xx, weights=W), np.average(Y, weights=W)
        den = np.sum(W * (xx - xm) ** 2)
        return np.sum(W * (xx - xm) * (Y - ym)) / den if den > 0 else 0.0
    s0 = abs(slope(X))
    if len(ps) <= 7:
        perms = [np.array(t) for t in itertools.permutations(X)]
    else:
        rng = np.random.default_rng(seed)
        perms = [rng.permutation(X) for _ in range(n)]
    return float(np.mean([abs(slope(pp)) >= s0 - 1e-12 for pp in perms]))


def lopo(R, ya, x=None):
    """留一篇：返回 每个比较的预测误差平方（只用合并倍数；或加调节因素 x）。"""
    ps = sorted(set(papers(R)))
    err = np.zeros(len(R))
    pa = np.array(papers(R))
    for p in ps:
        te = pa == p; tr = ~te
        Rt = [r for r, t in zip(R, tr) if t]
        if x is None:
            res = fit_mixed(ya[tr], np.zeros((tr.sum(), 0)), papers(Rt), [])
            pred = np.full(te.sum(), res["b"][0])
        else:
            if np.std(x[tr]) < 1e-9:
                res = fit_mixed(ya[tr], np.zeros((tr.sum(), 0)), papers(Rt), [])
                pred = np.full(te.sum(), res["b"][0])
            else:
                res = fit_mixed(ya[tr], x[tr][:, None], papers(Rt), ["m"])
                pred = res["b"][0] + res["b"][1] * x[te]
        err[te] = (ya[te] - pred) ** 2
    return err


def c1(P, cls, g1, std_ether):
    out, groups = [], defaultdict(list)
    for q in P:
        if q["配对类型"] != "同配方、换条件":
            groups[q["主改动"]].append(q)
    for g, R in groups.items():
        if len(set(papers(R))) < 3:
            continue
        ya = dys(R) - offset(g1, R, cls)
        e0 = lopo(R, ya)
        null = fit_mixed(ya, np.zeros((len(R), 0)), papers(R), [])
        mods = [moderators(q, cls, std_ether) for q in R]
        for k in mods[0]:
            v = np.array([np.nan if m[k] is None else m[k] for m in mods], float)
            ok = ~np.isnan(v)
            Rk = [r for r, o in zip(R, ok) if o]
            if not enough(Rk, v[ok]):
                continue
            x = v[ok]
            res = fit_mixed(ya[ok], x[:, None], papers(Rk), [k])
            r0 = fit_mixed(ya[ok], np.zeros((ok.sum(), 0)), papers(Rk), [])
            e_null, e_mod = lopo(Rk, ya[ok]), lopo(Rk, ya[ok], x)
            b, se = float(res["b"][1]), float(res["se"][1])
            out.append({"类别": cls, "主改动": g, "调节因素": k, "论文": len(set(papers(Rk))), "比较": int(ok.sum()),
                        "方法": res["方法"], "斜率": b, "SE": se, "p": float(res["p"][1]), "95%区间": [b - 1.96 * se, b + 1.96 * se],
                        "调节因素标准差": float(np.std(x)), "每1SD的倍数变化": math.exp(b * np.std(x)),
                        "论文间差异减少比例": (1 - res["tau2"] / r0["tau2"]) if r0["tau2"] > 1e-9 else None,
                        "留一篇误差降低比例": float(1 - e_mod.mean() / e_null.mean()) if e_null.mean() > 0 else None,
                        "合并倍数（本组）": math.exp(float(null["b"][0])), "置换p": perm_p(Rk, ya[ok], x)})
    q = bh([e["置换p"] for e in out])
    for e, qq in zip(out, q):
        e["q"] = None if not np.isfinite(qq) else float(qq)
        e["成立"] = bool(e["q"] is not None and e["q"] < 0.1 and (e["留一篇误差降低比例"] or 0) > 0)
    return out, groups


def conditional(groups, cls, g1, std_ether, found):
    """C2：成立的调节因素 → 标准 / 实用条件下的倍数（把调节因素移到目标值后重拟合，截距即目标处效应）。"""
    out = []
    for e in found:
        if not e["调节因素"].startswith("条件:"):
            continue
        k = e["调节因素"].split(":", 1)[1]
        R = groups[e["主改动"]]
        ya = dys(R) - offset(g1, R, cls)
        v = np.array([np.nan if q["参照条件"].get(k) is None else q["参照条件"][k] for q in R])
        ok = ~np.isnan(v)
        Rk = [r for r, o in zip(R, ok) if o]
        row = {"类别": cls, "主改动": e["主改动"], "调节因素": k}
        for lab, t in (("标准条件", STD[k]), ("实用条件", PRACT.get(k, STD[k])), ("数据中位数", float(np.median(v[ok])))):
            res = fit_mixed(ya[ok], (v[ok] - t)[:, None], papers(Rk), [k])
            b, se = float(res["b"][0]), float(res["se"][0])
            row[lab] = {"取值": t if k not in ("ln_ES", "ln_倍率", "ln_电流", "ln_沉积容量") else math.exp(t),
                        "倍数": math.exp(b), "95%区间": [math.exp(b - 1.96 * se), math.exp(b + 1.96 * se)]}
        out.append(row)
    return out


def desc_interactions(P, cls, g1, descs):
    out = []
    for d in descs:
        R = [q for q in P if q["Δ描述符"][d] is not None]
        ya = dys(R) - offset(g1, R, cls)
        c, n = interactions(R, cls, d)
        res = mixed(R, ya, [diffrec(R), dd(R, d)] + c, ["不同配方", "Δ" + d] + n)
        row = {"类别": cls, "描述符": d, "方法": res["方法"], "比较": len(R), "论文": len(set(papers(R)))}
        for nm in ["Δ" + d] + n:
            if nm in res["names"]:
                i = res["names"].index(nm)
                row[nm] = {"系数": float(res["b"][i]), "95%区间": [float(res["b"][i] - 1.96 * res["se"][i]), float(res["b"][i] + 1.96 * res["se"][i])],
                           "p": float(res["p"][i])}
        out.append(row)
    return out


# ---------------- C3 证据 ----------------
_cache = {}


def paper(p):
    if p not in _cache:
        _cache[p] = (json.loads((PAP / p / "candidate.json").read_text(encoding="utf-8")),
                     {s["id"]: s for s in json.loads((PAP / p / "source.json").read_text(encoding="utf-8"))})
    return _cache[p]


def sent(p, ids, n=320):
    """句子编号 → 原文（读原文判定时用）。"""
    src = paper(p)[1]
    out = []
    for i in ids:
        if i in src:
            t = re.sub(r"\s+", " ", src[i]["text"])[:n]
            out.append(f"[{i}] {t}")
    return "\n".join(out)


def evidence(q, ST):
    p = q["论文"]
    d, _ = paper(p)
    a, b = ST[q["实验"]], ST[q["参照"]]
    fm = {f["id"]: f for f in d["formulations"]}
    tests = {a["测试"], b["测试"]}
    forms = {a["配方"], b["配方"]}
    mech = [m for m in d.get("mechanisms") or [] if set(m.get("test_ids") or []) & tests or {m.get("A"), m.get("B")} & forms]
    notes = d.get("comparison_notes") or {}
    return {"实验": f"{a['配方']}｜{a['配方文字']}｜{a['测试名']}｜{a['标准指标']} {a['数值原文']}{a.get('单位') or ''}（{a['阶段']} {a['圈数'] or ''}）",
            "参照": f"{b['配方']}｜{b['配方文字']}｜{b['测试名']}｜{b['标准指标']} {b['数值原文']}{b.get('单位') or ''}（{b['阶段']} {b['圈数'] or ''}）",
            "配方系统说明": "；".join(f"{k}: {fm[k].get('system', '')}" for k in forms if k in fm),
            "实验原句": a["原句"][:600], "参照原句": b["原句"][:600],
            "对比说明": "\n".join(f"{k}: {v}" for k, v in (notes.items() if isinstance(notes, dict) else enumerate(notes))),
            "相关机制": "\n".join(f"{m['id']}（{m.get('source_type', '')}）: {m.get('summary', '')}" for m in mech[:8])}


def c3(groups, cls, g1, std_ether, ST):
    out = []
    for g, R in groups.items():
        ps = sorted(set(papers(R)))
        if len(ps) < 3:
            continue
        ya = dys(R) - offset(g1, R, cls)
        mu = float(fit_mixed(ya, np.zeros((len(R), 0)), papers(R), [])["b"][0])
        pm = defaultdict(list)
        for q, a in zip(R, ya):
            pm[q["论文"]].append((q, a))
        mods_all = [moderators(q, cls, std_ether) for q in R]
        for p, v in pm.items():
            m = float(np.mean([a for _, a in v]))
            kind = "方向相反" if np.sign(m) != np.sign(mu) and abs(m) > MIN_EFF else "幅度异常" if abs(m - mu) > BIG else None
            if not kind:
                continue
            pos = {}
            for k in mods_all[0]:
                vals = [x[k] for x in mods_all if x[k] is not None]
                mine = [moderators(q, cls, std_ether)[k] for q, _ in v]
                mine = [x for x in mine if x is not None]
                if vals and mine and k.startswith("条件:"):
                    t = float(np.mean(mine)); kk = k.split(":", 1)[1]
                    show = math.exp(t) if kk in ("ln_ES", "ln_倍率", "ln_电流", "ln_沉积容量") else t
                    pos[kk] = f"{show:.3g}（本组 {sum(x < t for x in vals)}/{len(vals)} 低于它）"
            for q, a in v:
                out.append({"类别": cls, "主改动": g, "论文": p, "类型": kind, "本组合并倍数": math.exp(mu), "本篇平均倍数": math.exp(m),
                            "这一比较倍数": math.exp(a), "实验表述": q["实验"], "参照表述": q["参照"], "配对类型": q["配对类型"],
                            "全部改动": q["全部改动"], "标记": q["标记"], "条件在本组的位置": pos, **evidence(q, ST)})
    return out


def write_xlsx(rows, judge):
    sys.path.insert(0, str(ROOT / "scripts"))
    from step13_common import write_xlsx as wx
    hdr = ["编号", "类别", "主改动", "论文", "类型", "本组合并倍数", "本篇平均倍数", "这一比较倍数", "配对类型", "全部改动", "实验", "参照",
           "条件在本组的位置", "标记", "配方系统说明", "对比说明", "相关机制", "实验原句", "参照原句",
           "读原文判定", "候选原因", "原因归类", "依据句", "✍ 用户意见"]
    data = []
    for r in rows:
        j = judge.get(r["编号"]) or judge.get(f"{r['类别']}|{r['主改动']}|{r['论文']}") or {}
        data.append([r["编号"], r["类别"], r["主改动"], r["论文"], r["类型"], round(r["本组合并倍数"], 3), round(r["本篇平均倍数"], 3),
                     round(r["这一比较倍数"], 3), r["配对类型"], r["全部改动"], r["实验"], r["参照"],
                     "；".join(f"{k} {v}" for k, v in r["条件在本组的位置"].items()), r["标记"], r["配方系统说明"], r["对比说明"], r["相关机制"],
                     r["实验原句"], r["参照原句"], j.get("判定", ""), j.get("原因", ""), j.get("归类", ""), j.get("依据", ""), ""])
    wx(OUT / "归因复核表.xlsx", [("矛盾候选与读原文", hdr, data)],
       widths={"实验": 40, "参照": 40, "实验原句": 60, "参照原句": 60, "对比说明": 50, "相关机制": 50, "候选原因": 50, "依据句": 40},
       notes=["归因复核表（313 篇开发集；初步、未裁定；AI 辅助，用户尚未逐项人工确认）。",
              "每行 = 一个矛盾候选里的一次比较：本篇平均效应与本组合并方向相反（且超过 5%），或偏离合并值 3 倍以上。倍数已扣掉全类共用的条件效应，>1 = 变好。",
              "读原文判定：✅ 原因明确 / 🔶 有线索 / ⚠️ 数据或配对问题（比较里混了别的改动、提取或归类有误） / ❌ 没找到。由 Claude 读两侧原句、配方系统说明、"
              "对比说明与机制后填写（归因判定.json）；“✍ 用户意见”列留给用户，Claude 不填。",
              "条件在本组的位置：例如“E/S 2（本组 0/9 低于它）”表示本篇的 E/S 是本组最低。"])


CATS = ["条件不同", "混了别的改动", "参照很弱或很强", "改动方向不同", "实验/对照方向标反", "归组或提取问题", "指标放大", "指标问题",
        "取值点不同", "真实大效应", "真实机制差异", "符合描述符趋势", "差异小于噪声"]
SYSTEMIC = [  # 读原文时发现、会系统性制造“矛盾”的问题（下次重建第 0 步数据时修；本次不改 A、B 已考过的数据）
    "参照配方里以 0 用量列出的组分（P266 THE 0 vt.%、P175 N-CDs 0 wt%、P103 IL 0 wt%）使“加 X”被判成“改浓度/配比”：主改动判定应把 0 用量当作没有。",
    "LiNO₃ 按质量分数换算后，溶剂组成不同会让同为 2 wt% 的两个配方每升物质的量略有差别，被判成“LiNO₃ 用量”改动（P313、P272）：应先比原文用量。",
    "LiNO₃ 用量未报告的“加 LiNO₃”被判成“改浓度/配比”（P377）：有无 LiNO₃ 应单独判。",
    "“每圈保持率 99.5%”被当成 100 圈总保持率（P052）：数值原文含 per cycle、/cycle 的保持率要换算为 100 − 值。",
    "本篇新电解液被标成对照、常规电解液被当成实验（P311、P204、P279）：没有天然方向的分组（换溶剂、改浓度/配比、换主盐）不能按“实验 − 参照”合并倍数；只有“加 X”类有方向。",
    "“高浓”只按每个 Li⁺ 的位点数判，2 M 的弱配位单溶剂（DBE）也会被判成高浓（P288）：应同时要求主盐浓度高。",
    "跨测试比较常常把高载量、贫液、软包或低温测试的数值和常规测试的参照配在一起，条件效应的线性修正不足以扣掉（P176、P332、P034、P366 等）。",
    "全电池 CE 会被穿梭扭曲（>100% 或初始 CE 很低，P296、P135），CE 接近 100% 时损失比又被放大（P185、P319、P386）。",
    "不属于电解液比较的测试进了比较表：活性物质对比（P143）、饱和多硫化物工作液（P371）、流动电池（P272）。",
]


def summarize(rows, judge):
    units = {}
    for r in rows:
        units.setdefault(f"{r['类别']}|{r['主改动']}|{r['论文']}", r)
    out = {"组数": len(units), "已判": sum(k in judge for k in units), "判定": dict(Counter(judge[k]["判定"] for k in units if k in judge)),
           "原因出现次数": {}, "主要原因": {}, "按类别": {}}
    for k in units:
        if k not in judge:
            continue
        cats = [c for c in CATS if c in judge[k]["归类"]]
        for c in cats:
            out["原因出现次数"][c] = out["原因出现次数"].get(c, 0) + 1
        main = cats[0] if cats else "其他"
        out["主要原因"][main] = out["主要原因"].get(main, 0) + 1
        cls = k.split("|")[0]
        out["按类别"].setdefault(cls, Counter())[main] += 1
    out["按类别"] = {c: dict(v) for c, v in out["按类别"].items()}
    real = [k for k in units if k in judge and any(c in judge[k]["归类"] for c in ("真实机制差异",))]
    out["真正的机制矛盾"] = real
    out["系统性问题"] = SYSTEMIC
    return out


def fig_summary(S):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mm import font
    font()
    items = sorted(S["原因出现次数"].items(), key=lambda kv: -kv[1])
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh([k for k, _ in items], [v for _, v in items], color="#2980b9")
    for j, (k, v) in enumerate(items):
        ax.text(v + 0.2, j, str(v), va="center", fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel(f"出现次数（{S['已判']} 组矛盾候选，一组可有多个原因）")
    ax.set_title("归因｜文献里“结论相反/幅度异常”的原因（读原文判定，初步）", fontsize=11)
    fig.tight_layout(); fig.savefig(OUT / "图C1_矛盾原因.png", dpi=170); plt.close(fig)


ORIENT = {"改浓度/配比": ("ln_Li总浓度", "Li⁺ 浓度升高"), "高浓": ("ln_Li总浓度", "Li⁺ 浓度升高"),
          "换溶剂（其他）": ("ln_配位位点每Li", "每个 Li⁺ 的配位位点变多（换成配位更强的溶剂）"),
          "加/换氟化醚": ("溶剂_含氟分子比例", "含氟溶剂比例升高"), "局部高浓": ("稀释剂摩尔比例", "稀释剂比例升高"),
          "LiNO₃ 用量": ("LiNO3_M", "LiNO₃ 增加"), "加有机硫": ("有机硫", "加入有机硫"), "加介体": ("介体", "加入介体")}


def c5(groups, cls, g1):
    """C5：倍数能不能变准。按改动的定义方向（ORIENT，只看组成、不看结果）把每个比较翻到同一方向，
    比较三种口径：原始（实验 − 参照）、定向、定向＋只用同测试。指标：合并倍数与区间、论文间差异占比、方向一致比例、
    留一篇预测误差（用其余论文的合并倍数预测这篇的平均效应，论文层面均方根误差，ln 单位）与方向预测正确率。"""
    out = []
    for g, R in groups.items():
        if g not in ORIENT:
            continue
        d, lab = ORIENT[g]
        ya_all = dys(R) - offset(g1, R, cls)
        ver = {"原始": [(q, a) for q, a in zip(R, ya_all)]}
        ori = []
        for q, a in zip(R, ya_all):
            x = q["Δ描述符"].get(d)
            if x is not None and abs(x) > 1e-9:
                ori.append((q, a * np.sign(x)))
        ver["定向"] = ori
        ver["定向＋只同测试"] = [(q, a) for q, a in ori if q["配对类型"] == "同测试、不同配方"]
        row = {"类别": cls, "主改动": g, "方向": lab}
        for k, v in ver.items():
            ps = sorted({q["论文"] for q, _ in v})
            if len(ps) < 4:
                row[k] = {"论文": len(ps), "状态": "论文 < 4"}; continue
            y = np.array([a for _, a in v]); pp = [q["论文"] for q, _ in v]
            r = fit_mixed(y, np.zeros((len(y), 0)), pp, [])
            mu, se = float(r["b"][0]), float(r["se"][0])
            pm = {p: float(np.mean([a for q, a in v if q["论文"] == p])) for p in ps}
            errs, hits = [], []
            for p in ps:
                keep = [i for i, x in enumerate(pp) if x != p]
                m0 = float(fit_mixed(y[keep], np.zeros((len(keep), 0)), [pp[i] for i in keep], [])["b"][0])
                errs.append(pm[p] - m0); hits.append(np.sign(pm[p]) == np.sign(m0))
            row[k] = {"论文": len(ps), "比较": len(v), "合并倍数": math.exp(mu), "95%区间": [math.exp(mu - 1.96 * se), math.exp(mu + 1.96 * se)],
                      "论文间差异占比": (r["tau2"] / (r["tau2"] + r["sigma2"])) if r["tau2"] + r["sigma2"] > 0 else None,
                      "方向一致比例": float(np.mean([np.sign(m) == np.sign(mu) for m in pm.values()])),
                      "留一篇误差_RMSE_ln": float(np.sqrt(np.mean(np.square(errs)))), "留一篇方向正确率": float(np.mean(hits))}
        out.append(row)
    return out


def fig_c5(C5):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mm import font
    font()
    rows = [r for r in C5 if "合并倍数" in r["原始"] and "合并倍数" in r["定向＋只同测试"]]
    fig, ax = plt.subplots(figsize=(10, 0.75 * len(rows) + 1.5))
    for j, r in enumerate(rows):
        for off, k, col in ((-0.15, "原始", "#95a5a6"), (0.15, "定向＋只同测试", "#c0392b")):
            v = r[k]
            ax.plot(v["95%区间"], [j + off] * 2, color=col, lw=1.6)
            ax.plot(v["合并倍数"], j + off, "o", color=col, ms=6)
            ax.text(v["95%区间"][1] * 1.05, j + off, f"{v['论文']} 篇｜同向 {v['方向一致比例']:.0%}｜留一篇误差 {v['留一篇误差_RMSE_ln']:.2f}",
                    va="center", fontsize=7, color=col)
    ax.axvline(1, color="k", lw=0.8); ax.set_xscale("log")
    lab = lambda t: t.replace("Li⁺", "Li+").replace("LiNO₃", "LiNO3")  # 字体缺上下标字形
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([lab(f"{r['类别']}｜{r['方向']}") for r in rows], fontsize=8); ax.invert_yaxis()
    ax.set_xticks([0.3, 0.5, 1, 2, 4, 8]); ax.set_xticklabels(["0.3", "0.5", "1", "2", "4", "8"]); ax.minorticks_off()
    ax.plot([], [], "o", color="#95a5a6", label="原始（实验 − 参照，含跨测试）"); ax.plot([], [], "o", color="#c0392b", label="方向统一＋只用同测试")
    ax.legend(fontsize=8, loc="upper left"); ax.set_xlabel("合并倍数（>1 = 变好，已扣条件差）")
    ax.set_title("归因｜按组成统一改动方向、只用同测试后，倍数是否更一致（初步，开发集）", fontsize=11)
    fig.tight_layout(); fig.savefig(OUT / "图C2_定向前后倍数.png", dpi=170); plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    P, M, _ = load()
    std_ether = {(r["论文"], r["表述"]): float(r["标准醚"]) for r in M}
    ST = {s["表述编号"]: s for s in json.loads(STF.read_text(encoding="utf-8"))}
    a2 = json.loads((AOUT / "A2_描述符筛查.json").read_text(encoding="utf-8"))["结果"]
    C1, C2, C2d, C3, C5 = [], [], [], [], []
    for cls in CLASSES:
        Pc = [q for q in P if q["划分"] == "开发" and q["类别"] == cls]
        g1 = stage1(Pc, cls)
        res, groups = c1(Pc, cls, g1, std_ether)
        C1 += res
        found = [e for e in res if e["成立"]]
        C2 += conditional(groups, cls, g1, std_ether, found)
        C2d += desc_interactions(Pc, cls, g1, [e["描述符"] for e in a2[cls] if e.get("q") is not None and e["q"] < 0.1])
        C3 += c3(groups, cls, g1, std_ether, ST)
        C5 += c5(groups, cls, g1)
        print(f"\n=== {cls}：组 {sum(len(set(papers(R))) >= 3 for R in groups.values())}，检验 {len(res)}，成立 {len(found)}", flush=True)
        for e in sorted(res, key=lambda e: e["置换p"])[:6]:
            print(f"  {e['主改动']:10s} {e['调节因素']:14s} {e['论文']}篇 每SD倍数 {e['每1SD的倍数变化']:.2f} 置换p {e['置换p']:.3f} q {e['q']:.3f} "
                  f"差异减少 {e['论文间差异减少比例'] if e['论文间差异减少比例'] is None else round(e['论文间差异减少比例'], 2)} "
                  f"留一篇误差降低 {e['留一篇误差降低比例']:.2f}{' ✔' if e['成立'] else ''}", flush=True)
    for i, r in enumerate(C3, 1):
        r["编号"] = f"C{i:03d}"
    judge = json.loads(JUDGE.read_text(encoding="utf-8")) if JUDGE.exists() else {}
    for name, obj in (("C1_调节因素.json", {"说明": NOTE + "；探索性，q<0.1 且留一篇误差降低才写成发现", "结果": C1}),
                      ("C2_条件化倍数.json", {"说明": NOTE, "调节因素成立的组": C2, "描述符×条件交互": C2d}),
                      ("C3_矛盾候选.json", C3), ("C5_定向后倍数.json", {"说明": NOTE + "；方向只按组成定义（ORIENT），不看结果", "结果": C5})):
        (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    write_xlsx(C3, judge)
    print("\n矛盾候选", len(C3), "个比较 /", len({(r['类别'], r['主改动'], r['论文']) for r in C3}), "个（类别, 改动, 论文）",
          Counter(r["类型"] for r in C3))
    fig_c5(C5)
    if judge:
        S = summarize(C3, judge)
        (OUT / "C4_归因汇总.json").write_text(json.dumps(S, ensure_ascii=False, indent=1), encoding="utf-8")
        fig_summary(S)
        print("已判", S["已判"], "/", S["组数"], S["判定"])
        print("原因出现次数", S["原因出现次数"])
        print("主要原因", S["主要原因"])


if __name__ == "__main__":
    main()
