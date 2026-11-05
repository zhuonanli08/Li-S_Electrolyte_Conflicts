"""step15 方案 A：meta 回归（比较“差值”，11-06 用户批准）。

数据：第 0 步的比较表（同一篇论文内：同测试不同配方、跨测试不同配方、同配方换条件）。效应 dy = 实验 − 参照（ln 比，越大越好：
容量比、每圈衰减率之比的倒数、CE 损失比的倒数）。四类性能分开做。只用开发集；考试集只在 --exam 时用一次。
范围：两边温度相差超过 10 °C 的比较不用（低温、高温测试的温度效应不是线性，少数 −40 / 60 °C 跨温度比较会主导条件效应）；
  同一温度下的比较（含 60 °C 下同测试的两个配方）保留。
两步估计：
  第 1 步 条件效应 γ：岭回归 dy ~ [不同配方] + Δ条件（惩罚强度按论文分组的内层 5 折选），用全部比较；
          同测试的比较 Δ条件 = 0；跨测试缺值记 0（同一篇里没写的条件按与参照相同）。衰减类不含圈数。
  第 2 步 扣掉条件差：dy_adj = dy − γ·Δ条件，再做下面的随机效应分析（statsmodels MixedLM，论文随机截距；
          不收敛时退回 OLS＋按论文聚类稳健标准误）。区间没有计入 γ 的不确定性，略偏窄。
  [不同配方] 吸收“新配方通常会赢”（发表偏差），单独报告，不算进描述符效应。
A1 分策略 meta：按主改动分组（第 0 步规则，局部高浓单列），开发集 ≥ 3 篇的组才做：合并提升、95% 区间、
   论文间差异占比 = τ² ÷ (τ² + σ²)（论文没有报误差棒，这不是经典 I²，而是各篇平均提升的差异占总差异的比例，
   越大说明各篇结论越不一致）、方向一致比例；另报只用“同测试、不同配方”的结果作核对。
A2 描述符筛查：一次放一个描述符：dy_adj ~ [不同配方] + Δ描述符 + 论文效应。同配方换条件的 Δ描述符 = 0。
   输出 β、95% 区间、BH 校正 q 值（每类 16 个一起校正）、论文间差异减少比例、5 折整篇留出中方向一致的折数。
   标准化效应 = β × 该描述符在本类开发集测量中的标准差，换成倍数 exp(·)。至少 3 篇论文里 Δ描述符 ≠ 0 才估计。
   Li⁺ 总浓度取对数（ln_Li总浓度）：12 M 高浓与 1 M 相差 11，线性时少数高浓比较决定斜率。
A3 权衡图：横轴容量效应，纵轴衰减率效应（另一张：纵轴 Li‖Cu CE），每个描述符一个点。
A4 多描述符模型（规则跑前写定，见 预先登记.json）：q < 0.1、方向稳定（至少 4 折可估计且至少 4 折一致）、
   每个机制组最多 1 个（取 q 最小）、总数 ≤ min(4, 开发集论文数 ÷ 10)。加事先指定的交互：Δ描述符 × (参照 ln E/S − 标准)、
   Δ描述符 × (参照载量 − 标准)；Li‖Cu 用 ln 电流、ln 沉积容量。
   预测用岭回归（描述符、交互、[不同配方]、Δ条件一起，惩罚按内层 5 折选）；系数与区间另用第 2 步的随机效应模型报告。
   没有描述符入选时 A4 = 只用条件的模型。
A5 验证：开发集按论文 5 折；指标 = 篇内排序一致率（同一篇里任两个不同配方的比较，预测先后与实测一致的比例，0.5 = 不会排序）、
   同测试内排序一致率、篇内 Spearman（≥ 3 个比较的篇）、dy 的 R²；基线 = 只用条件（岭回归）、只有截距。
   描述符是用全部开发集选的，开发集分数偏乐观；考试集才是真实水平。
成功标准（事先定）：至少 1 个描述符 q < 0.1 且方向稳定；A4 的篇内排序一致率在开发集和考试集上都高于“只用条件”基线
   （按论文重抽样的差值 95% 区间下限 > 0）。
开发集诊断后修正（11-06，考试前）：第一版用不加惩罚的回归，条件 7 列＋缺值指示列＋交互项在一百多个比较上过拟合
   （Li‖Cu 一折里 ΔLiNO₃×沉积容量系数 71，留出 R² −89）；MixedLM 因读取方差的写法错误全部退回 OLS。改为上面的两步估计、
   去掉缺值指示列、跨温度（相差 > 10 °C）的比较不用、Li⁺ 总浓度取对数、修 MixedLM 读取。
   （中间试过只留 15–35 °C 的比较，Li‖Cu 137 个比较剩 81，60 °C、−40 °C 下同测试的干净比较也被丢掉，改为按温度差剔除。）
用法：python -X utf8 A_meta.py          （开发集：A1–A5，写 预先登记.json）
      python -X utf8 A_meta.py --exam   （考试集只算一次；已算过会拒绝）
"""
import sys
import json
import math
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
from sklearn.model_selection import GroupKFold

sys.path.insert(0, str(Path(__file__).parent))
from mm import fit_mixed, bh, concordance, spearman_mean, r2, boot_by_paper, font, Ridge

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
IN = ROOT / "output" / "meta共同准备_313篇_2026-11-06"
OUT = ROOT / "output" / "方案A_meta回归_313篇_2026-11-06"
CLASSES = ["首圈容量", "每圈衰减率", "全电池CE", "LiCu_CE"]
DESC = {"G1 溶剂化/配位": ["ln_配位位点每Li", "ln_Li总浓度", "稀释剂摩尔比例", "醚氧数"],
        "G2 氟化": ["sO_β氟化醚", "sO_α氟化醚", "溶剂_含氟分子比例", "F/O"],
        "G3 阴离子": ["aF"],
        "G4 添加剂": ["LiNO3_M", "有机硫", "介体", "含碘"],
        "G5 溶剂骨架": ["溶剂_环醚比例", "溶剂_碳酸酯比例", "可旋转键数"]}
DESC_ALL = [d for g in DESC.values() for d in g]
GROUP_OF = {d: g for g, ds in DESC.items() for d in ds}
COND = {"首圈容量": ["ln_ES", "载量", "含硫", "ln_倍率", "软包"],
        "每圈衰减率": ["ln_ES", "载量", "含硫", "ln_倍率", "软包"],
        "全电池CE": ["ln_ES", "载量", "含硫", "ln_倍率", "软包", "ln_圈数"],
        "LiCu_CE": ["ln_电流", "ln_沉积容量", "ln_圈数", "Aurbach法"]}
DT_MAX = 10.0  # 两边温度相差超过 10 °C 的比较不用
STD = {"ln_ES": math.log(10), "载量": 1.5, "含硫": 50.0, "温度": 25.0, "软包": 0.0, "ln_倍率": math.log(0.2), "ln_圈数": math.log(100),
       "ln_电流": math.log(0.5), "ln_沉积容量": math.log(1.0), "Aurbach法": 0.0}
PRACT = {"ln_ES": math.log(5), "载量": 4.0}
INTER = {c: (["ln_电流", "ln_沉积容量"] if c == "LiCu_CE" else ["ln_ES", "载量"]) for c in CLASSES}
LABEL = {"首圈容量": "首圈容量", "每圈衰减率": "每圈衰减率（倒数）", "全电池CE": "全电池 CE 损失（倒数）", "LiCu_CE": "Li‖Cu CE 损失（倒数）"}
NOTE = "初步、未裁定；AI 辅助，用户尚未逐项人工确认"




def load():
    """读第 0 步结果；Li⁺ 总浓度换成对数；跨温度（相差 > 10 °C）的比较不用。返回 比较表、测量表、剔除计数。"""
    P = json.loads((IN / "比较表.json").read_text(encoding="utf-8"))
    M = json.loads((IN / "测量表.json").read_text(encoding="utf-8"))
    for r in M:
        v = r["描述符"].pop("Li总浓度", None)
        r["描述符"]["ln_Li总浓度"] = math.log(v) if v else None
    drop = Counter()
    keep = []
    for q in P:
        ref = q["参照描述符"].pop("Li总浓度", None)
        dl = q["Δ描述符"].pop("Li总浓度", None)
        q["参照描述符"]["ln_Li总浓度"] = math.log(ref) if ref else None
        q["Δ描述符"]["ln_Li总浓度"] = (math.log(ref + dl) - math.log(ref)) if ref and dl is not None and ref + dl > 0 else None
        if q["配对类型"] == "同配方、换条件":
            q["Δ描述符"] = {k: 0.0 for k in DESC_ALL}
        dt = q["Δ条件"].get("温度")
        if dt is not None and abs(dt) > DT_MAX:
            drop[q["类别"]] += 1
            continue
        keep.append(q)
    return keep, M, drop


def diffrec(P):
    return np.array([float(q["配对类型"] != "同配方、换条件") for q in P])


def cond_X(P, cls):
    return np.array([[q["Δ条件"].get(k) or 0.0 for k in COND[cls]] for q in P], float).reshape(len(P), -1)


def dys(P):
    return np.array([q["dy"] for q in P], float)


def papers(P):
    return [q["论文"] for q in P]


def stage1(P, cls):
    """条件效应 γ（岭回归）；返回模型和每个比较的条件贡献（相对 Δ条件 = 0）。"""
    X = np.column_stack([diffrec(P), cond_X(P, cls)])
    m = Ridge().fit(X, dys(P), papers(P))
    return m


def offset(m, P, cls):
    return cond_X(P, cls) @ m.coef()[1:]


def mixed(P, y, cols, names):
    X = np.column_stack(cols) if cols else np.zeros((len(P), 0))
    ok = [i for i in range(X.shape[1]) if np.std(X[:, i]) > 1e-9]
    return fit_mixed(y, X[:, ok], papers(P), [names[i] for i in ok])


def dd(P, d):
    return np.array([q["Δ描述符"][d] for q in P], float)


def interactions(P, cls, d):
    out, names = [], []
    for k in INTER[cls]:
        ref = np.array([0.0 if q["参照条件"].get(k) is None else q["参照条件"][k] - STD[k] for q in P])
        out.append(dd(P, d) * ref); names.append(f"Δ{d}×{k}")
    return out, names


# ---------------- A2 ----------------
def sd_desc(M, cls, d):
    v = [r["描述符"].get(d) for r in M if r["类别"] == cls and r["划分"] == "开发" and r["描述符"].get(d) is not None]
    return float(np.std(v)) if len(v) > 2 else None


def screen(P, M, cls, g1):
    out = []
    for d in DESC_ALL:
        R = [q for q in P if q["Δ描述符"][d] is not None]
        nzp = sorted({q["论文"] for q in R if abs(q["Δ描述符"][d]) > 1e-9})
        e = {"类别": cls, "描述符": d, "机制组": GROUP_OF[d], "比较数": len(R),
             "Δ≠0 的比较": sum(abs(q["Δ描述符"][d]) > 1e-9 for q in R), "Δ≠0 的论文": len(nzp)}
        if len(nzp) < 3:
            out.append({**e, "状态": "数据不足（Δ≠0 的论文 < 3）"}); continue
        ya = dys(R) - offset(g1, R, cls)
        res = mixed(R, ya, [diffrec(R), dd(R, d)], ["不同配方", "Δ" + d])
        res0 = mixed(R, ya, [diffrec(R)], ["不同配方"])
        i = res["names"].index("Δ" + d)
        b, se, p = float(res["b"][i]), float(res["se"][i]), float(res["p"][i])
        sd = sd_desc(M, cls, d)
        agree = est = 0
        pa = np.array(papers(R))
        for tr, _ in GroupKFold(5).split(R, groups=pa):
            Rt = [R[j] for j in tr]
            if len({q["论文"] for q in Rt if abs(q["Δ描述符"][d]) > 1e-9}) < 3:
                continue
            rt = mixed(Rt, ya[tr], [diffrec(Rt), dd(Rt, d)], ["不同配方", "Δ" + d])
            est += 1
            agree += int(np.sign(rt["b"][rt["names"].index("Δ" + d)]) == np.sign(b))
        tau_red = (1 - res["tau2"] / res0["tau2"]) if res0["tau2"] > 1e-9 else None
        out.append({**e, "状态": "已估计", "方法": res["方法"], "β": b, "SE": se, "p": p,
                    "95%区间": [b - 1.96 * se, b + 1.96 * se], "描述符标准差": sd,
                    "标准化效应_ln": None if sd is None else b * sd,
                    "倍数_每1SD": None if sd is None else math.exp(b * sd),
                    "倍数95%区间": None if sd is None else [math.exp((b - 1.96 * se) * sd), math.exp((b + 1.96 * se) * sd)],
                    "论文间差异减少比例": tau_red, "τ²_无描述符": res0["tau2"], "τ²_有描述符": res["tau2"],
                    "方向稳定": f"{agree}/{est}", "稳定折数": agree, "可估计折数": est,
                    "不同配方的平均提升_ln": float(res["b"][res["names"].index("不同配方")]) if "不同配方" in res["names"] else None})
    q = bh([e.get("p", np.nan) for e in out])
    for e, qq in zip(out, q):
        e["q"] = None if not np.isfinite(qq) else float(qq)
    return out


# ---------------- A1 ----------------
def strategy(P, cls, g1):
    adj = dys(P) - offset(g1, P, cls)
    out = []
    groups = defaultdict(list)
    for q, a in zip(P, adj):
        if q["配对类型"] != "同配方、换条件":
            groups[q["主改动"]].append((q, a))
    for g, v in sorted(groups.items(), key=lambda kv: -len({q["论文"] for q, _ in kv[1]})):
        ps = sorted({q["论文"] for q, _ in v})
        e = {"类别": cls, "主改动": g, "论文": len(ps), "比较": len(v)}
        if len(ps) < 3:
            out.append({**e, "状态": "论文 < 3，不合并"}); continue
        r = fit_mixed([a for _, a in v], np.zeros((len(v), 0)), [q["论文"] for q, _ in v], [])
        mu, se = float(r["b"][0]), float(r["se"][0])
        pm = defaultdict(list)
        for q, a in v:
            pm[q["论文"]].append(a)
        means = {p: float(np.mean(x)) for p, x in pm.items()}
        st = [(q, q["dy"]) for q, _ in v if q["配对类型"] == "同测试、不同配方"]
        one = all(len(x) == 1 for x in pm.values())  # 每篇只有 1 个比较：论文间与篇内差异分不开
        if not se > 1e-9:
            out.append({**e, "状态": "区间不可靠（比较太少，标准误估为 0）", "合并倍数": math.exp(mu)}); continue
        if one:
            r["tau2"], r["sigma2"] = float("nan"), float("nan")
        e.update({"状态": "已合并", "方法": r["方法"], "合并提升_ln": mu, "95%区间_ln": [mu - 1.96 * se, mu + 1.96 * se],
                  "合并倍数": math.exp(mu), "倍数95%区间": [math.exp(mu - 1.96 * se), math.exp(mu + 1.96 * se)],
                  "τ²": r["tau2"], "σ²": r["sigma2"],
                  "论文间差异占比": (r["tau2"] / (r["tau2"] + r["sigma2"]) if r["tau2"] + r["sigma2"] > 0 else None) if not one else None,
                  "备注": "每篇只有 1 个比较，论文间与篇内差异分不开" if one else "",
                  "方向一致比例": float(np.mean([np.sign(m) == np.sign(mu) for m in means.values()])),
                  "各篇平均提升倍数": {p: round(math.exp(m), 3) for p, m in sorted(means.items())}, "仅同测试": None})
        if len({q["论文"] for q, _ in st}) >= 3:
            r2_ = fit_mixed([a for _, a in st], np.zeros((len(st), 0)), [q["论文"] for q, _ in st], [])
            e["仅同测试"] = {"论文": len({q["论文"] for q, _ in st}), "比较": len(st), "合并倍数": math.exp(float(r2_["b"][0])),
                         "倍数95%区间": [math.exp(float(r2_["b"][0] - 1.96 * r2_["se"][0])), math.exp(float(r2_["b"][0] + 1.96 * r2_["se"][0]))]}
        out.append(e)
    return out


# ---------------- A4 / A5 ----------------
def select(scr, n_papers):
    cap = min(4, n_papers // 10)
    ok = [e for e in scr if e.get("状态") == "已估计" and e["q"] is not None and e["q"] < 0.1
          and e["可估计折数"] >= 4 and e["稳定折数"] >= 4]
    best = {}
    for e in sorted(ok, key=lambda e: e["q"]):
        best.setdefault(e["机制组"], e)
    return [e["描述符"] for e in sorted(best.values(), key=lambda e: e["q"])][:cap]


def usable(P, descs):
    return [q for q in P if all(q["Δ描述符"][d] is not None for d in descs)]


def pred_X(P, cls, descs):
    cols = []
    for d in descs:
        cols.append(dd(P, d))
        cols += interactions(P, cls, d)[0]
    return np.column_stack(cols + [diffrec(P), cond_X(P, cls)])


def fit_pred(P, cls, descs):
    return Ridge().fit(pred_X(P, cls, descs), dys(P), papers(P))


def a4_inference(P, cls, descs, g1):
    """A4 系数与区间：dy_adj ~ [不同配方] + Δ描述符 + 交互 + 论文效应。"""
    ya = dys(P) - offset(g1, P, cls)
    cols, names = [diffrec(P)], ["不同配方"]
    for d in descs:
        cols.append(dd(P, d)); names.append("Δ" + d)
        c, n = interactions(P, cls, d); cols += c; names += n
    return mixed(P, ya, cols, names)


def evaluate(pred, P):
    dr = [i for i, q in enumerate(P) if q["配对类型"] != "同配方、换条件"]
    obs = dys(P)
    pp = np.asarray(pred, float)
    st = [i for i in dr if P[i]["配对类型"] == "同测试、不同配方"]
    c1, n1 = concordance(pp[dr], obs[dr], [P[i]["论文"] for i in dr])
    c2, n2 = concordance(pp[st], obs[st], [(P[i]["论文"], P[i]["实验测试"]) for i in st]) if st else (np.nan, 0)
    sp, ns = spearman_mean(pp[dr], obs[dr], [P[i]["论文"] for i in dr])
    return {"篇内排序一致率": c1, "比较对数": n1, "同测试排序一致率": c2, "同测试对数": n2, "篇内Spearman": sp, "Spearman篇数": ns,
            "R²_全部比较": r2(obs, pp), "R²_不同配方": r2(obs[dr], pp[dr]) if dr else None}


def cv(P, cls, descs, k=5):
    pa = np.array(papers(P))
    pred = {"A4": np.zeros(len(P)), "只用条件": np.zeros(len(P)), "只有截距": np.zeros(len(P))}
    for tr, te in GroupKFold(k).split(P, groups=pa):
        Pt, Pe = [P[i] for i in tr], [P[i] for i in te]
        for lab, ds in (("A4", descs), ("只用条件", [])):
            pred[lab][te] = fit_pred(Pt, cls, ds).predict(pred_X(Pe, cls, ds))
        pred["只有截距"][te] = dys(Pt).mean()
    return pred


def diff_ci(P, pa, pb):
    """篇内排序一致率差值（A4 − 只用条件）按论文重抽样的 95% 区间。"""
    idx = defaultdict(list)
    for i, q in enumerate(P):
        idx[q["论文"]].append(i)

    def fn(ps):
        sel = [j for p in ps for j in idx[p]]
        Q = [dict(P[j], 论文=f"{P[j]['论文']}#{n}") for n, p in enumerate(ps) for j in idx[p]]
        a = evaluate(pa[sel], Q)["篇内排序一致率"]; b = evaluate(pb[sel], Q)["篇内排序一致率"]
        return a - b if np.isfinite(a) and np.isfinite(b) else None
    return boot_by_paper(fn, papers(P), n=300)


def std_ether_desc(M, cls):
    se = [r for r in M if r["类别"] == cls and r["标准醚"] and r["划分"] == "开发"] or [r for r in M if r["标准醚"]]
    return {d: (float(np.median([r["描述符"][d] for r in se if r["描述符"].get(d) is not None]))
                if any(r["描述符"].get(d) is not None for r in se) else None) for d in DESC_ALL}


def gain_table(res, M, cls, descs):
    """A4：各配方相对标准醚的预测提升（标准条件、实用条件；用随机效应模型的固定效应），只列选中描述符齐全的配方。"""
    if not descs:
        return []
    d0 = std_ether_desc(M, cls)
    b = dict(zip(res["names"], res["b"]))
    seen, out = set(), []
    for r in M:
        if r["类别"] != cls or r["划分"] != "开发" or r["配方键"] in seen or any(r["描述符"].get(d) is None for d in descs):
            continue
        seen.add(r["配方键"])
        g_std = sum(b.get("Δ" + d, 0) * (r["描述符"][d] - d0[d]) for d in descs)
        g_pr = g_std + sum(b.get(f"Δ{d}×{k}", 0) * (r["描述符"][d] - d0[d]) * (PRACT.get(k, STD[k]) - STD[k]) for d in descs for k in INTER[cls])
        out.append({"论文": r["论文"], "配方": r["配方"], "配方名": r["配方名"], "配方键": r["配方键"],
                    "标准条件预测倍数": math.exp(g_std), "实用条件预测倍数": math.exp(g_pr) if cls != "LiCu_CE" else None})
    return sorted(out, key=lambda e: -e["标准条件预测倍数"])


# ---------------- 图 ----------------
def figures(scr_all, strat_all):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    font()
    fig, axes = plt.subplots(1, 4, figsize=(17, 7.5), sharey=True)
    ylab = [f"{d}（{GROUP_OF[d].split()[0]}）" for d in DESC_ALL]
    for ax, cls in zip(axes, CLASSES):
        for j, d in enumerate(DESC_ALL):
            e = next(e for e in scr_all[cls] if e["描述符"] == d)
            if e.get("状态") != "已估计" or e.get("标准化效应_ln") is None:
                ax.text(0, j, "数据不足", ha="center", va="center", fontsize=7, color="#999")
                continue
            m = e["标准化效应_ln"]; lo, hi = np.array(e["95%区间"]) * e["描述符标准差"]
            sig = e["q"] is not None and e["q"] < 0.1
            ax.plot([lo, hi], [j, j], color="#c0392b" if sig else "#7f8c8d", lw=1.4)
            ax.plot(m, j, "o", color="#c0392b" if sig else "white", mec="#c0392b" if sig else "#34495e", ms=6)
        ax.axvline(0, color="k", lw=0.8)
        ax.set_title(LABEL[cls], fontsize=11)
        ax.set_xlabel("每 1 个标准差的效应（ln 倍数，>0 = 变好）", fontsize=8)
        ax.grid(axis="x", alpha=0.3)
    axes[0].set_yticks(range(len(DESC_ALL))); axes[0].set_yticklabels(ylab, fontsize=8); axes[0].invert_yaxis()
    fig.suptitle("方案 A｜描述符筛查（一次一个，已扣条件差；实心红点 = q < 0.1）　初步，313 篇开发集", fontsize=12)
    fig.tight_layout(); fig.savefig(OUT / "图A1_描述符森林图.png", dpi=170); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    for ax, (cx, cy) in zip(axes, (("首圈容量", "每圈衰减率"), ("首圈容量", "LiCu_CE"))):
        for d in DESC_ALL:
            ex = next(e for e in scr_all[cx] if e["描述符"] == d); ey = next(e for e in scr_all[cy] if e["描述符"] == d)
            if ex.get("标准化效应_ln") is None or ey.get("标准化效应_ln") is None:
                continue
            x, y = ex["标准化效应_ln"], ey["标准化效应_ln"]
            xe = 1.96 * ex["SE"] * ex["描述符标准差"]; ye = 1.96 * ey["SE"] * ey["描述符标准差"]
            sig = (ex["q"] or 1) < 0.1 or (ey["q"] or 1) < 0.1
            ax.errorbar(x, y, xerr=xe, yerr=ye, fmt="o", color="#c0392b" if sig else "#2c3e50", alpha=0.75, ms=5, lw=0.8)
            ax.annotate(d, (x, y), fontsize=7, xytext=(3, 3), textcoords="offset points")
        ax.axhline(0, color="k", lw=0.8); ax.axvline(0, color="k", lw=0.8)
        ax.set_xlabel(f"对{LABEL[cx]}的效应（ln 倍数 / 1 SD）"); ax.set_ylabel(f"对{LABEL[cy]}的效应（ln 倍数 / 1 SD）")
        ax.text(0.98, 0.98, "右上：两项都变好", transform=ax.transAxes, ha="right", va="top", fontsize=8, color="#27ae60")
        ax.text(0.02, 0.98, "左上 / 右下：此消彼长", transform=ax.transAxes, ha="left", va="top", fontsize=8, color="#8e44ad")
        ax.grid(alpha=0.3)
    fig.suptitle("方案 A｜权衡图（误差棒 = 95% 区间；红 = 至少一项 q < 0.1）　初步", fontsize=12)
    fig.tight_layout(); fig.savefig(OUT / "图A2_权衡图.png", dpi=170); plt.close(fig)
    fig, axes = plt.subplots(1, 4, figsize=(19, 6))
    for ax, cls in zip(axes, CLASSES):
        S = [e for e in strat_all[cls] if e.get("状态") == "已合并"]
        for j, e in enumerate(S):
            lo, hi = e["倍数95%区间"]
            ax.plot([lo, hi], [j, j], color="#2c3e50"); ax.plot(e["合并倍数"], j, "s", color="#2980b9")
            sh = "—" if e["论文间差异占比"] is None else f"{e['论文间差异占比']:.0%}"
            ax.text(hi, j, f"  {e['论文']} 篇｜差异占比 {sh}", va="center", fontsize=7)
        ax.axvline(1, color="k", lw=0.8); ax.set_xscale("log")
        ax.set_yticks(range(len(S))); ax.set_yticklabels([e["主改动"] for e in S], fontsize=8); ax.invert_yaxis()
        ax.set_title(LABEL[cls], fontsize=10); ax.set_xlabel("相对参照的合并倍数（>1 = 变好）", fontsize=8)
    fig.suptitle("方案 A｜分策略 meta（扣除条件差；≥ 3 篇的组）　初步", fontsize=12)
    fig.tight_layout(); fig.savefig(OUT / "图A3_策略森林图.png", dpi=170); plt.close(fig)


def jdump(name, obj):
    def conv(o):
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=conv), encoding="utf-8")


def main_dev():
    OUT.mkdir(parents=True, exist_ok=True)
    P, M, drop = load()
    dev = [q for q in P if q["划分"] == "开发"]
    scr_all, strat_all, gam, sel, val, gains, models = {}, {}, {}, {}, {}, {}, {}
    for cls in CLASSES:
        Pc = [q for q in dev if q["类别"] == cls]
        npap = len({q["论文"] for q in Pc})
        print(f"\n=== {cls}：开发集比较 {len(Pc)}（{npap} 篇；跨温度剔除 {drop[cls]}）", flush=True)
        g1 = stage1(Pc, cls)
        gam[cls] = {"λ": g1.lam, "γ（每单位）": dict(zip(["不同配方"] + ["Δ" + k for k in COND[cls]], g1.coef().tolist()))}
        print("  条件效应 γ:", {k: round(v, 3) for k, v in gam[cls]["γ（每单位）"].items()}, "λ", g1.lam, flush=True)
        strat_all[cls] = strategy(Pc, cls, g1)
        scr_all[cls] = screen(Pc, M, cls, g1)
        for e in scr_all[cls]:
            if e.get("状态") == "已估计":
                print(f"  {e['描述符']:14s} 倍数/SD {e['倍数_每1SD']:.3f} 区间 {e['倍数95%区间'][0]:.3f}–{e['倍数95%区间'][1]:.3f}"
                      f" q {e['q']:.3f} 稳定 {e['方向稳定']} Δ≠0 论文 {e['Δ≠0 的论文']} 方法 {e['方法']}", flush=True)
        sel[cls] = select(scr_all[cls], npap)
        Pu = usable(Pc, sel[cls])
        inf = a4_inference(Pu, cls, sel[cls], g1)
        models[cls] = {"描述符": sel[cls], "列": inf["names"], "系数": inf["b"], "SE": inf["se"], "p": inf["p"], "方法": inf["方法"],
                       "τ²": inf["tau2"], "σ²": inf["sigma2"], "比较数": len(Pu), "论文": len({q['论文'] for q in Pu})}
        gains[cls] = gain_table(inf, M, cls, sel[cls])
        pred = cv(Pu, cls, sel[cls])
        ev = {k: evaluate(v, Pu) for k, v in pred.items()}
        ev["A4−只用条件 篇内排序一致率差 95%区间"] = diff_ci(Pu, pred["A4"], pred["只用条件"]) if sel[cls] else None
        val[cls] = ev
        print(f"  A4 选中：{sel[cls] or '无（= 只用条件）'}；开发集 5 折 篇内排序一致率 A4 {ev['A4']['篇内排序一致率']:.3f} / 只用条件 "
              f"{ev['只用条件']['篇内排序一致率']:.3f}；同测试 {ev['A4']['同测试排序一致率']:.3f} / {ev['只用条件']['同测试排序一致率']:.3f}；"
              f"R² {ev['A4']['R²_全部比较']:.3f} / {ev['只用条件']['R²_全部比较']:.3f} / 截距 {ev['只有截距']['R²_全部比较']:.3f}；"
              f"差值区间 {ev['A4−只用条件 篇内排序一致率差 95%区间']}", flush=True)
    jdump("A1_分策略meta.json", {"说明": NOTE, "条件效应γ": gam, "结果": strat_all})
    jdump("A2_描述符筛查.json", {"说明": NOTE, "结果": scr_all})
    jdump("A4_多描述符模型.json", {"说明": NOTE, "模型": models, "相对标准醚的预测提升": gains})
    jdump("A5_开发集验证.json", {"说明": NOTE + "；描述符用全部开发集选出，开发集分数偏乐观", "结果": val})
    jdump("预先登记.json", {"说明": "方案 A 考试前登记（规则见 A_meta.py 文件头）。考试只算一次。", "A4选中描述符": sel,
                        "考试指标": "篇内排序一致率（主）、同测试排序一致率、篇内 Spearman、R²；基线 = 只用条件、只有截距",
                        "成功标准": "至少 1 个描述符 q<0.1 且方向稳定；A4 篇内排序一致率在开发集与考试集都高于只用条件基线（差值 95% 区间下限 > 0）",
                        "考试集": "改动模型_313篇_2026-11-05/划分.json 的 31 篇；对方案 A 是第一次使用（step14 衰减类已用两次、其余三类一次）"})
    figures(scr_all, strat_all)


def main_exam():
    f = OUT / "考试结果.json"
    if f.exists():
        sys.exit("方案 A 考试集已经算过，不再重算")
    reg = json.loads((OUT / "预先登记.json").read_text(encoding="utf-8"))
    P, M, _ = load()
    out = {"运行次数": 1, "登记": reg, "类别": {}}
    for cls in CLASSES:
        ds = reg["A4选中描述符"][cls]
        tr = usable([q for q in P if q["划分"] == "开发" and q["类别"] == cls], ds)
        te = usable([q for q in P if q["划分"] == "考试" and q["类别"] == cls], ds)
        pr = {lab: fit_pred(tr, cls, d).predict(pred_X(te, cls, d)) for lab, d in (("A4", ds), ("只用条件", []))}
        pr["只有截距"] = np.full(len(te), dys(tr).mean())
        ev = {k: evaluate(v, te) for k, v in pr.items()}
        ev["比较"] = len(te); ev["论文"] = len({q["论文"] for q in te})
        ev["A4−只用条件 篇内排序一致率差 95%区间"] = diff_ci(te, pr["A4"], pr["只用条件"]) if ds else None
        out["类别"][cls] = ev
        print(f"{cls}：考试 {len(te)} 个比较 / {ev['论文']} 篇；篇内排序一致率 A4 {ev['A4']['篇内排序一致率']:.3f}，只用条件 "
              f"{ev['只用条件']['篇内排序一致率']:.3f}；同测试 {ev['A4']['同测试排序一致率']:.3f}；R² A4 {ev['A4']['R²_全部比较']:.3f}，"
              f"只用条件 {ev['只用条件']['R²_全部比较']:.3f}；差值区间 {ev['A4−只用条件 篇内排序一致率差 95%区间']}")
    jdump("考试结果.json", out)


if __name__ == "__main__":
    main_exam() if "--exam" in sys.argv else main_dev()
