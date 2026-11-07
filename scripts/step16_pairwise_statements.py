"""step16：两两比较表述（11-06 用户定；找张力改用它，step13c 的“一个数值一条”表述保留不动）。

一条记录 = 同一篇论文、同一类性能里的两次测量（测试 × 配方）比一次，写“A 相对 B”，每对只比一次（不再出现 B 相对 A）。
三种比较都记、都纳入分析（11-06 用户：测试条件也是重要因素）：同测试换配方、同配方换条件、配方和条件都变。
写法：组分变化 → 分子描述符 → 物性 → 条件 → 性能，各写“变高 / 变低 / 相近”。规则（11-06 用户定）：
- 性能三类：首圈容量、每圈衰减率、Li‖Cu CE（全电池 CE 不用）。口径沿用第 0 步 v2 测量表（首圈容量只用首圈；每圈衰减率同毕设口径；
  CE 不含首圈；同一测试、同一配方只留一个值）。全部温度都纳入，温度当作条件记录（不再只用室温）。
- 性能相差 < 5% 记“相近”：容量按容量之比，衰减按每圈衰减率之比，CE 按损失 100 − CE 之比；倍数存在记录里，表述文字只写方向。
- 描述符（step13h 的 22 个结构描述符 ＋ LiNO₃）由组成算出、没有测量误差，相差 < 1% 记“相近”；只写变了的，每个单独一行，不合并成组。
  作者没改用量、因加入别的组分被稀释而变的（LiNO₃；主盐及随它变的阴离子 F、阴离子磺酰；Li⁺ 总浓度）标“被动”。
- 物性：从原值文字重新取第一段的数值（上游“数值”字段约 4% 误取了开头的测试温度），两边单位相同、测试温度相同才比，相差 < 5% 记“相近”。条件：报告或换算的设定值，相差 < 1% 记“相近”，温度相差 ≥ 1 °C 才算变。
- 汇总给每个描述符“有变化 / 组内单独变化 / 全部单独变化”的对数与篇数（组 = meta v3 的轴），统计同时给对数和篇数。
- 11-07 描述符修正（step12b/13h）：“羰基”改为“其他羰基（酯、酮）”，与碳酸酯、酰胺/脲羰基互不重叠；VC 的羰基、碳酸酯补上；
  脲按 1 个羰基计；Si–O–C 氧计入醚氧和配位位点；吡啶型芳香 N 计入配位位点。每对另标“特殊组分变化”：作者改动的组分里
  有成膜/活性溶剂（FEC、VC、DMTS、三聚甲醛、有机硫、CS₂ 等）或描述符看不到的组分（添加剂、介体、多硫化物、非锂盐、无结构组分）。
- 只放原文句子编号，不放原句（仓库公开）。
同测试的比较另按“样品对”合并成一条（性能按测试分别列出），即用户给的格式：实验样 X 相对对比样 Y，描述符……；物性……；条件……；性能……。
输入（只读）：meta共同准备_313篇_v2_2026-11-06/测量表.json，表述试跑313篇_2026-11-05/表述.json，组分结构表_试跑313篇_2026-11-05/（经 step13h），
     meta_v3_全部测量_313篇_2026-11-06/汇总.json（只取描述符分组）。
输出：output/两两比较表述_313篇_2026-11-06/（比较表述.json、样品对表述.json、比较表述表.xlsx、汇总.json）。初步；AI 辅助，用户尚未逐项人工确认。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step16_pairwise_statements.py
"""
import re
import sys
import json
import math
from pathlib import Path
from itertools import combinations
from collections import defaultdict, Counter

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "step15_meta"))
import step13h_descriptor_figures as H
import F_pooled as F
from step13_common import write_xlsx

IN = ROOT / "output" / "meta共同准备_313篇_v2_2026-11-06" / "测量表.json"
STF = ROOT / "output" / "表述试跑313篇_2026-11-05" / "表述.json"
# 11-07 描述符修正（拆羰基、VC、脲、Si–O–C、吡啶型 N）后写到 v2；11-06 版本留在 两两比较表述_313篇_2026-11-06/（step18 的 40 条判定基于它）
OUT = ROOT / "output" / "两两比较表述_313篇_v2_2026-11-07"
CLASSES = {"首圈容量": "首圈容量", "每圈衰减率": "每圈衰减率", "LiCu_CE": "Li‖Cu CE"}
TH_PERF, TH_DESC, TH_PROP, TH_COND, TH_TEMP = 0.05, 0.01, 0.05, 0.01, 1.0
DKEYS = list(dict.fromkeys(list(F.KEYS) + ["lino3"]))  # F.KEYS 已含 lino3，去重
DCN = {"eo": "非氟醚氧", "eo_a": "α 氟化醚氧", "eo_b": "β 氟化醚氧", "carbonate": "碳酸酯", "carbonyl": "其他羰基（酯、酮）", "sulfone": "砜/亚砜", "nitrile": "腈",
       "amide": "酰胺/脲羰基", "thio": "硫醚/多硫 S", "fat": "溶剂 F 原子数", "ring": "溶剂环数", "rotb": "可旋转键数", "tpsa": "TPSA", "mw": "溶剂分子量",
       "ffrac": "含氟溶剂比例", "lnsites": "每个 Li⁺ 的配位位点", "dil": "稀释剂摩尔比例", "li": "Li⁺ 总浓度", "salt": "主盐浓度",
       "anF": "阴离子 F（每升）", "anSO2": "阴离子磺酰（每升）", "lino3": "LiNO₃ 浓度"}
AXES = json.loads((F.OUT / "汇总.json").read_text(encoding="utf-8"))["轴"]
AXCN = {g: (F.AXES.get(g) or {}).get("中文", "其他基团") for g in AXES}
GROUP = {d: g for g, x in AXES.items() for d in x["成员"]}
GROUP.setdefault("lino3", "LiNO₃")
MEMBERS = defaultdict(set)
for d, g in GROUP.items():
    MEMBERS[g].add(d)
# 条件：测量表的键 → (中文名, 测量表里存的是对数)
CONDN = {"ln_ES": ("E/S", True), "载量": ("硫载量", False), "含硫": ("正极含硫", False), "ln_倍率": ("倍率", True), "温度": ("温度", False),
         "软包": ("电池形式", None), "ln_电流": ("电流密度", True), "ln_沉积容量": ("沉积容量", True), "Aurbach法": ("测试方法", None)}
BINARY = {"软包": ("扣式", "软包"), "Aurbach法": ("非 Aurbach", "Aurbach 法")}
PTYPE = ("同测试换配方", "同配方换条件", "配方和条件都变")


def rel(a, b):
    m = max(abs(a), abs(b))
    return 0.0 if m == 0 else abs(a - b) / m


def word(a, b, th):
    """a 相对 b 的方向；缺值返回 None。"""
    if a is None or b is None:
        return None
    if rel(a, b) < th:
        return "相近"
    if b == 0:
        return "变高（从无到有）"
    if a == 0:
        return "变低（变为 0）"
    return "变高" if a > b else "变低"


def sample_key(r):
    return r["recipe"] if r["recipe"] is not None else "F:" + r["配方"]


def comps(pid, rid):
    rec = H.COMPREC.get((pid, rid))
    return {i["组分"]: i for i in rec["组分"]} if rec else None


def amt(i):
    return f"{i['原文用量']} {i['原文单位']}".strip()


def comp_change(ca, cb):
    """作者改了什么（按原文用量和单位比）；返回文字和改动过的组分。"""
    if ca is None or cb is None:
        return "配方组成未记录", None
    out, changed = [], set()
    for c, i in ca.items():
        if c not in cb:
            out.append(f"加入 {c}（{amt(i)}）"); changed.add(c)
        elif (i["原文用量"], i["原文单位"]) != (cb[c]["原文用量"], cb[c]["原文单位"]):
            out.append(f"{c} {amt(cb[c])} → {amt(i)}"); changed.add(c)
    for c in cb:
        if c not in ca:
            out.append(f"去掉 {c}"); changed.add(c)
    return "；".join(out) or "组分与用量相同", changed


# 11-07：作者改动的组分里，有按结构计入溶剂描述符、但作用不只是溶剂化的（成膜/活性溶剂），
# 或描述符根本看不到的（添加剂、介体、多硫化物、非锂盐、没有结构的组分）——单独标出，不改投票
FILM_CAT = {"溶剂/添加剂"}
FILM_CHEM = {"环缩醛", "有机硫（二硫醚）", "有机硫（硫醚）", "有机硫（多硫醚）", "二硫化碳"}
HIDDEN_CAT = {"添加剂", "添加剂（介体）", "其他盐/添加剂", "硫物种", "锂盐/添加剂", "离子", "盐", "氧化还原介体（原文称均相催化剂）"}


def special(changed):
    out = []
    for c in sorted(changed or ()):
        if c == "LiNO3":
            continue
        t = H.CTAB.get(c)
        if t is None:
            out.append({"组分": c, "类型": "描述符看不到（组分未收录）"})
        elif t.get("类别") in FILM_CAT or t.get("化学类别") in FILM_CHEM:
            out.append({"组分": c, "类型": "成膜/活性溶剂"})
        elif t.get("类别") in HIDDEN_CAT or ("溶剂" in t.get("类别", "") and c not in H.DWHOLE):
            out.append({"组分": c, "类型": "描述符看不到"})
    return out


def passive(d, ca, cb, changed):
    """浓度类描述符变了，但对应组分作者没改用量（被别的组分稀释）。"""
    if changed is None or d not in ("lino3", "salt", "anF", "anSO2", "li"):
        return False
    allc = set(ca) | set(cb)
    salts = {c for c in allc if "锂盐" in H.CTAB.get(c, {}).get("类别", "")}
    lino3 = {c for c in allc if c == "LiNO3"}
    dep = {"lino3": lino3, "salt": salts, "anF": salts, "anSO2": salts, "li": salts | lino3}[d]
    return bool(dep) and dep <= (set(ca) & set(cb)) and not (dep & changed)


def desc_val(D, k):
    v = D.get(k)
    return math.exp(v) if (k == "lnsites" and v is not None) else v


TEMP = re.compile(r"(-?\d+(?:\.\d+)?)\s*°\s*C")
NUMX = re.compile(r"(-?\d+(?:\.\d+)?)(?:\s*[×x]\s*10\s*\^?\s*([−-]?\s*\d+))?")
UNIT_TAIL = re.compile(r"[A-Za-zμµΩ][A-Za-z0-9μµΩ/·\-\^ ]*$")


def prop_num(raw):
    """从物性原值文字取第一段的数值、单位和测试温度。上游“数值”字段有约 4% 取成了开头的温度（如“30°C≈2.50 cP”取 30），这里重新解析。"""
    seg = re.split(r"[；;]", raw)[0]
    t = TEMP.search(seg)
    seg2 = TEMP.sub(" ", seg)
    m = NUMX.search(seg2)
    if not m:
        return None
    v = float(m.group(1)) * (10 ** int(m.group(2).replace("−", "-").replace(" ", "")) if m.group(2) else 1)
    unit = seg2[m.end():].strip(" ≈~约，,）)")
    if not unit:
        u = UNIT_TAIL.search(raw)
        unit = u.group(0).strip() if u else ""
    return v, unit, float(t.group(1)) if t else None


def props(s):
    out = {}
    for k, v in (s.get("物性") or {}).items():
        for x in v:
            if x.get("数值") is None:  # 上游判定没有数值的（定性描述等）不比
                continue
            p = prop_num(str(x.get("值") or ""))
            if p:
                out[k] = p
                break
    return out


def cond_items(a, b, cls):
    out = []
    for k, (cn, is_ln) in CONDN.items():
        if k not in a["条件"] and k not in b["条件"]:
            continue
        x, y = a["条件"].get(k), b["条件"].get(k)
        if x is None and y is None:
            continue
        if x is None or y is None:
            out.append({"条件": cn, "方向": "一边未报告", "A": x, "B": y}); continue
        if k in BINARY:
            w = "相同" if x == y else f"{BINARY[k][int(y)]} → {BINARY[k][int(x)]}"
            out.append({"条件": cn, "方向": w, "A": x, "B": y}); continue
        if is_ln:
            x, y = math.exp(x), math.exp(y)
        if k == "温度":
            w = "相近" if abs(x - y) < TH_TEMP else ("变高" if x > y else "变低")
        else:
            w = word(x, y, TH_COND)
        out.append({"条件": cn, "方向": w, "A": round(x, 4), "B": round(y, 4)})
    if cls != "首圈容量":
        w = word(a["圈数"], b["圈数"], TH_COND) if a["圈数"] and b["圈数"] else ("一边未报告" if (a["圈数"] or b["圈数"]) else None)
        if w:
            out.append({"条件": "圈数", "方向": w, "A": a["圈数"], "B": b["圈数"]})
    return out


def perf(cls, a, b):
    dy = a["y"] - b["y"]
    r = math.exp(dy) if cls == "首圈容量" else math.exp(-dy)
    if abs(r - 1) < TH_PERF:
        w = "相近"
    elif cls == "首圈容量":
        w = "变高" if r > 1 else "变低"
    elif cls == "每圈衰减率":
        w = "变低" if r < 1 else "变高"
    else:
        w = "变高" if r < 1 else "变低"
    val = (lambda m: round(math.exp(-m["y"]), 4)) if cls == "每圈衰减率" else (lambda m: m["数值"])
    # 11-07：衰减类的值是换算后的每圈衰减率（%/圈），指标名写明，避免误读成保持率
    lab = (lambda m: f"每圈衰减率（%/圈，由{m['标准指标']}换算）") if cls == "每圈衰减率" else (lambda m: m["标准指标"])
    return {"方向": w, "倍数": round(r, 4), "倍数含义": {"首圈容量": "容量之比", "每圈衰减率": "每圈衰减率之比", "LiCu_CE": "损失（100 − CE）之比"}[cls],
            "好于参照": dy > 0 if w != "相近" else None, "值A": val(a), "值B": val(b), "指标A": lab(a), "指标B": lab(b)}


def side(r, ST):
    s = ST.get(r["表述"], {})
    return {"测试": r["测试"], "测试名": s.get("测试名", ""), "配方": r["配方"], "配方名": r["配方名"], "recipe": r["recipe"], "是否对照": r["是否对照"],
            "配方文字": s.get("配方文字", ""), "表述编号": r["表述"], "证据句子": s.get("证据句子", []), "标记": r["标记"]}


def fmt_desc(ds):
    return "；".join(f"{x['中文']} {x['方向']}" + ("（被动）" if x["被动"] else "") for x in ds) or "无变化"


def fmt_list(xs, key):
    return "；".join(f"{x[key]} {x['方向']}" for x in xs)


def build():
    M = [r for r in json.loads(IN.read_text(encoding="utf-8")) if r["类别"] in CLASSES]
    ST = {s["表述编号"]: s for s in json.loads(STF.read_text(encoding="utf-8"))}
    DES, CMP = {}, {}
    for r in M:
        k = (r["论文"], sample_key(r))
        if k not in DES:
            h, _ = H.descriptors(r["论文"], r["recipe"]) if r["recipe"] is not None else ({}, "")
            D = {d: h.get(d) for d in F.KEYS}
            D["lino3"] = r["描述符"].get("LiNO3_M")
            DES[k] = D
            CMP[k] = comps(r["论文"], r["recipe"]) if r["recipe"] is not None else None
    # 参照方向：对照在前，其余按在测量表里第一次出现的顺序
    rank, idx = {}, {}
    for i, r in enumerate(M):
        k = (r["论文"], sample_key(r))
        idx.setdefault(id(r), i)
        if k not in rank:
            rank[k] = [1, i]
        if r["是否对照"]:
            rank[k][0] = 0
    by = defaultdict(list)
    for r in M:
        by[(r["论文"], r["类别"])].append(r)
    recs, skipped_same = [], 0
    for (p, cls), rows in sorted(by.items()):
        for r1, r2 in combinations(rows, 2):
            k1, k2 = (p, sample_key(r1)), (p, sample_key(r2))
            if k1 == k2 and r1["测试"] == r2["测试"]:
                skipped_same += 1
                continue
            if k1 != k2:
                a, b = (r2, r1) if tuple(rank[k1]) < tuple(rank[k2]) else (r1, r2)
            else:
                a, b = (r2, r1) if idx[id(r1)] < idx[id(r2)] else (r1, r2)
            ka, kb = (p, sample_key(a)), (p, sample_key(b))
            ptype = PTYPE[0] if a["测试"] == b["测试"] else PTYPE[1] if ka == kb else PTYPE[2]
            ca, cb = CMP[ka], CMP[kb]
            ctext, changed = comp_change(ca, cb) if ka != kb else ("配方相同", set())
            ds = []
            if ka != kb:
                for d in DKEYS:
                    x, y = desc_val(DES[ka], d), desc_val(DES[kb], d)
                    w = word(x, y, TH_DESC)
                    if w in (None, "相近"):
                        continue
                    ds.append({"描述符": d, "中文": DCN[d], "组": AXCN.get(GROUP.get(d), "其他基团"), "方向": w,
                               "A": round(x, 4), "B": round(y, 4), "被动": passive(d, ca, cb, changed)})
            pa, pb = props(ST.get(a["表述"], {})), props(ST.get(b["表述"], {}))
            ps = []
            for k in pa:
                if k in pb and pa[k][1] == pb[k][1] and pa[k][2] == pb[k][2]:  # 同单位、同测试温度才比
                    w = word(pa[k][0], pb[k][0], TH_PROP)
                    if w:
                        ps.append({"物性": k, "方向": w, "A": pa[k][0], "B": pb[k][0], "单位": pa[k][1], "温度": pa[k][2]})
            cs = cond_items(a, b, cls)
            pf = perf(cls, a, b)
            dflt = sorted({m for m in a["标记"] + b["标记"] if "默认" in m})
            rec = {"编号": f"PC{len(recs) + 1:05d}", "论文": p, "类别": cls, "比较类型": ptype, "A": side(a, ST), "B": side(b, ST),
                   "组分变化": ctext, "作者改动的组分": sorted(changed) if changed is not None else None,
                   "特殊组分变化": special(changed),
                   "电解液相同但样品编号不同": ka == kb and a["配方"] != b["配方"],
                   "描述符": ds, "物性": ps, "条件": cs, "条件含默认值": dflt, "性能": pf}
            cvar = [x for x in cs if x["方向"] not in ("相近", "相同")]
            role = lambda s: "对比样" if s["是否对照"] else "实验样"
            rec["表述文字"] = (f"【{p}｜{CLASSES[cls]}｜{ptype}】{role(rec['A'])} {a['配方名']}（{rec['A']['配方文字']}，测试 {a['测试']}）相对 "
                           f"{role(rec['B'])} {b['配方名']}（{rec['B']['配方文字']}，测试 {b['测试']}）｜组分变化：{ctext}"
                           + (f"（其中 {'、'.join(x['组分'] + '：' + x['类型'] for x in rec['特殊组分变化'])}）" if rec["特殊组分变化"] else "")
                           + f"｜描述符：{fmt_desc(ds) if ka != kb else '配方相同'}｜物性：{fmt_list(ps, '物性') or '两边没有都报告的'}"
                           f"｜条件：{fmt_list(cvar, '条件') or '相同'}" + (f"（含默认值：{'、'.join(dflt)}）" if dflt else "")
                           + f"｜性能：{CLASSES[cls]} {pf['方向']}")
            recs.append(rec)
    return M, recs, skipped_same, DES


def sample_pairs(recs):
    """同测试的比较按样品对合并：一对样品一条，性能按测试分别列出（用户给的格式）。"""
    g = defaultdict(list)
    for r in recs:
        if r["比较类型"] == PTYPE[0]:
            g[(r["论文"], r["A"]["recipe"] or r["A"]["配方"], r["B"]["recipe"] or r["B"]["配方"])].append(r)
    out = []
    for (p, _, _), rs in sorted(g.items()):
        r0 = rs[0]
        role = lambda s: "对比样" if s["是否对照"] else "实验样"
        pf = "；".join(f"{CLASSES[r['类别']]} {r['性能']['方向']}（测试 {r['A']['测试']}）" for r in rs)
        cvar = sorted({f"{x['条件']} {x['方向']}" for r in rs for x in r["条件"] if x["方向"] not in ("相近", "相同")})
        props_ = {x["物性"]: x["方向"] for r in rs for x in r["物性"]}
        txt = (f"【样本】{p}：{role(r0['A'])} {r0['A']['配方名']}（{r0['A']['配方文字']}）相对 {role(r0['B'])} {r0['B']['配方名']}（{r0['B']['配方文字']}）"
               f"｜组分变化：{r0['组分变化']}｜分子描述符：{fmt_desc(r0['描述符'])}"
               f"｜物性：{'；'.join(f'{k} {v}' for k, v in props_.items()) or '两边没有都报告的'}"
               f"｜条件：{'相同（同一测试）' if not cvar else '同一测试，但 ' + '；'.join(cvar)}｜性能：{pf}")
        out.append({"论文": p, "A": r0["A"]["配方名"], "B": r0["B"]["配方名"], "A是对照": r0["A"]["是否对照"], "B是对照": r0["B"]["是否对照"],
                    "组分变化": r0["组分变化"], "描述符": r0["描述符"], "物性": props_, "性能": [{"类别": r["类别"], "测试": r["A"]["测试"], **r["性能"]} for r in rs],
                    "比较编号": [r["编号"] for r in rs], "表述文字": txt})
    return out


def summarize(M, recs, skipped_same, DES, sp):
    S = {"说明": __doc__.split("输入")[0].strip(), "门槛": {"性能": TH_PERF, "描述符": TH_DESC, "物性": TH_PROP, "条件": TH_COND, "温度_°C": TH_TEMP},
         "测量": {}, "比较": {}, "性能方向": {}, "描述符": {}, "样品对表述": len(sp), "同测试同样品被跳过": skipped_same}
    for cls in CLASSES:
        m = [r for r in M if r["类别"] == cls]
        S["测量"][CLASSES[cls]] = {"测量": len(m), "论文": len({r["论文"] for r in m})}
        rc = [r for r in recs if r["类别"] == cls]
        S["比较"][CLASSES[cls]] = {t: {"对": sum(r["比较类型"] == t for r in rc), "篇": len({r["论文"] for r in rc if r["比较类型"] == t})} for t in PTYPE}
        S["比较"][CLASSES[cls]]["合计"] = {"对": len(rc), "篇": len({r["论文"] for r in rc})}
        S["性能方向"][CLASSES[cls]] = {t: dict(Counter(r["性能"]["方向"] for r in rc if r["比较类型"] == t)) for t in PTYPE}
        st = {}
        for d in DKEYS:
            ch = [r for r in rc if any(x["描述符"] == d for x in r["描述符"])]
            sets = [{x["描述符"] for x in r["描述符"]} for r in ch]
            grp = [r for r, s_ in zip(ch, sets) if not (s_ & (MEMBERS[GROUP.get(d)] - {d}))]
            alone = [r for r, s_ in zip(ch, sets) if s_ == {d}]
            pas = [r for r in ch if any(x["描述符"] == d and x["被动"] for x in r["描述符"])]
            st[DCN[d]] = {"组": AXCN.get(GROUP.get(d), "其他基团"), "有变化": [len(ch), len({r["论文"] for r in ch})],
                          "组内单独变化": [len(grp), len({r["论文"] for r in grp})], "全部单独变化": [len(alone), len({r["论文"] for r in alone})],
                          "被动": [len(pas), len({r["论文"] for r in pas})]}
        S["描述符"][CLASSES[cls]] = st
    # 同一篇里没有任何一类性能可比的样品对
    cls_of = defaultdict(set)
    for r in M:
        cls_of[(r["论文"], sample_key(r))].add(r["类别"])
    byp = defaultdict(list)
    for k in cls_of:
        byp[k[0]].append(k)
    none = [(p, a[1], b[1]) for p, ks in byp.items() for a, b in combinations(ks, 2) if not (cls_of[a] & cls_of[b])]
    S["没有共同性能类别的样品对"] = {"对": len(none), "篇": len({x[0] for x in none})}
    S["描述符全部算不出的样品"] = sum(1 for v in DES.values() if all(x is None for x in v.values()))
    S["样品"] = len(DES)
    return S


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    M, recs, skipped_same, DES = build()
    sp = sample_pairs(recs)
    S = summarize(M, recs, skipped_same, DES, sp)
    dump = lambda n, o: (OUT / n).write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")
    dump("比较表述.json", recs)
    dump("样品对表述.json", sp)
    dump("汇总.json", S)
    j = lambda xs: "；".join(xs)
    rows1 = [[x["论文"], x["A"], x["B"], x["组分变化"], fmt_desc(x["描述符"]), j(f"{k} {v}" for k, v in x["物性"].items()),
              j(f"{CLASSES[y['类别']]} {y['方向']}（{y['测试']}，×{y['倍数']}）" for y in x["性能"]), x["表述文字"]] for x in sp]
    rows2 = [[r["编号"], r["论文"], CLASSES[r["类别"]], r["比较类型"], r["A"]["配方名"], r["A"]["测试"], r["B"]["配方名"], r["B"]["测试"], r["组分变化"],
              fmt_desc(r["描述符"]) if r["比较类型"] != PTYPE[1] else "配方相同", fmt_list(r["物性"], "物性"),
              fmt_list([x for x in r["条件"] if x["方向"] not in ("相近", "相同")], "条件") or "相同", j(r["条件含默认值"]),
              r["性能"]["方向"], r["性能"]["倍数"], r["性能"]["值A"], r["性能"]["值B"], j(f"{x['组分']}（{x['类型']}）" for x in r["特殊组分变化"]),
              j(r["A"]["证据句子"]), j(r["B"]["证据句子"])] for r in recs]
    rows3 = [[c, d, v["组"], *v["有变化"], *v["组内单独变化"], *v["全部单独变化"], *v["被动"]] for c, st in S["描述符"].items() for d, v in st.items()]
    write_xlsx(OUT / "比较表述表.xlsx", [
        ("样品对表述（同测试）", ["论文", "A", "B（参照）", "组分变化", "分子描述符", "物性", "性能（测试，倍数）", "表述文字"], rows1),
        ("全部比较（逐对）", ["编号", "论文", "性能", "比较类型", "A", "A 测试", "B（参照）", "B 测试", "组分变化", "描述符", "物性", "条件变化", "含默认值的条件",
                         "性能方向", "倍数", "A 值", "B 值", "特殊组分变化", "A 证据句", "B 证据句"], rows2),
        ("描述符变化统计", ["性能", "描述符", "组", "有变化·对", "有变化·篇", "组内单独·对", "组内单独·篇", "全部单独·对", "全部单独·篇", "被动·对", "被动·篇"], rows3)],
        notes=["两两比较表述（step16，11-07 描述符修正版）。倍数：容量 = 容量之比；衰减 = 每圈衰减率之比（<1 更好）；CE = 损失（100 − CE）之比（<1 更好）。",
               "性能、物性相差 < 5% 记“相近”；描述符、条件相差 < 1% 记“相近”。“被动” = 作者没改用量、因别的组分加入被稀释。只列原文句子编号。初步，AI 辅助，用户尚未逐项人工确认。"])
    print(json.dumps({k: S[k] for k in ("测量", "比较", "性能方向", "样品对表述", "同测试同样品被跳过", "没有共同性能类别的样品对", "样品", "描述符全部算不出的样品")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
