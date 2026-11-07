"""step17：张力候选（按细则 ③“计数”“张力候选口径”，11-07 用户定完规则后的正式版；11-06 的试算版见 git 95365f7）。

只读 step16 的 比较表述.json。
1. 统一方向：每对写成“描述符 X 变高时，性能变好还是变差”（X 变低的对翻过来）。效应 = ln 倍数，> 0 = 变好
   （容量取容量之比；衰减取每圈衰减率之比的倒数；CE 取损失比的倒数）。|效应| < ln1.05 记“相近”。
2. 数票：一对一票为主；另按论文复核（每篇一票，取本篇各对效应的中位数）。只用同测试换配方的比较数一遍，
   全部比较（再加上配方和条件都变的）数一遍。几个描述符同时变的对照样投票，另数“只有它变”和“组内只有它变”的对；
   被动（被稀释）的对照样投票，另报去掉被动后的多数。
3. 判定（同测试）：多数占比 = 多数方向票 /（变好＋变差），“相近”不计；
   - 有多数：占比 ≥ 2/3，且多数方向的对来自 ≥ 5 篇；
   - 没有共识：≥ 5 篇，但不满足上一条（占比不到 2/3，或两边持平）；
   - 不足 5 篇：只记录、不判。
4. 张力四类：
   - 反对多数：有多数的组合里有对与多数相反的论文。强 = 本篇涉及该描述符的各对，中位效应也与多数相反（整篇都反）；
     弱 = 只有个别对相反。强弱只排读原文的先后，不代表真假和原因。每条附“还一起变了什么”（组分变化、其他变了的描述符
     及其多数方向、被动标记），供 ④ 读原文参考，程序不判原因。同一批比较在几个描述符下各出现一次的，另按
     “论文 × 性能 × 同一批比较”合并；
   - 没有共识：见上；
   - 条件依赖：同一篇、同一对配方、同一类性能，在两个测试里一个变好一个变差；
   - 权衡：同一描述符在两类性能上都“有多数”（各自 ≥ 2/3）且方向相反。
   只作提醒、不单列为张力：一对一票与一篇一票多数方向不同；同测试与全部比较多数方向不同。
初步；AI 辅助，用户尚未逐项人工确认。只用原句编号，不放原句。
输出：output/张力候选_313篇_v2_2026-11-07/（票数.json、张力候选.json、张力候选表.xlsx、汇总.json）；11-07 描述符修正前的结果在 张力候选_313篇_2026-11-07/。
“特殊组分变化”（step16 v2）：作者改动的组分里有成膜/活性溶剂或描述符看不到的组分；照样计票，另报去掉这些对以后的多数（同被动的处理）。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step17_tension_trial.py
"""
import sys
import json
import math
import statistics as st
from pathlib import Path
from itertools import combinations
from collections import defaultdict, Counter

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
from step13_common import write_xlsx

# 11-07 描述符修正后读 step16 v2，写到 v2；修正前的结果留在 张力候选_313篇_2026-11-07/（step18 的 40 条判定基于它）
IN = ROOT / "output" / "两两比较表述_313篇_v2_2026-11-07" / "比较表述.json"
OUT = ROOT / "output" / "张力候选_313篇_v2_2026-11-07"
CN = {"首圈容量": "首圈容量", "每圈衰减率": "每圈衰减率", "LiCu_CE": "Li‖Cu CE"}
T, MIN_PAPERS, MIN_SHARE = math.log(1.05), 5, 2 / 3
SAME, MIXED = "同测试换配方", "配方和条件都变"
WORD = {"好": "变好", "差": "变差", "近": "相近"}


def effect(r):
    lr = math.log(r["性能"]["倍数"])
    return lr if r["类别"] == "首圈容量" else -lr


def lab(v):
    return "好" if v > T else "差" if v < -T else "近"


def sample(s):
    return s["recipe"] or s["配方"]


def up(x):
    return 1 if x["方向"].startswith("变高") else -1


def votes(R, d, c, types):
    out = []
    for r in R:
        if r["类别"] != c or r["比较类型"] not in types:
            continue
        ds = r["描述符"]
        x = next((y for y in ds if y["描述符"] == d), None)
        if not x:
            continue
        out.append({"论文": r["论文"], "效应": up(x) * effect(r), "只有它变": len(ds) == 1,
                    "组内只有它变": not any(y["组"] == x["组"] and y["描述符"] != d for y in ds), "被动": x["被动"],
                    "特殊": bool(r.get("特殊组分变化")),
                    "编号": r["编号"], "A": r["A"]["配方名"], "B": r["B"]["配方名"], "比较类型": r["比较类型"]})
    return out


EMPTY = {"对": 0, "篇": 0, "好": 0, "差": 0, "近": 0, "多数": "—", "多数占比": None, "多数方向来自几篇": 0,
         "判定": "不足 5 篇", "有多数": False, "按篇": {"好": 0, "差": 0, "近": 0, "多数": "—"}}


def tally(P):
    if not P:
        return dict(EMPTY), {}
    c = Counter(lab(p["效应"]) for p in P)
    per = defaultdict(list)
    for p in P:
        per[p["论文"]].append(p["效应"])
    cp = Counter(lab(st.median(v)) for v in per.values())
    maj = "好" if c["好"] > c["差"] else "差" if c["差"] > c["好"] else "平"
    majp = "好" if cp["好"] > cp["差"] else "差" if cp["差"] > cp["好"] else "平"
    nmaj = len({p["论文"] for p in P if lab(p["效应"]) == maj}) if maj != "平" else 0
    share = max(c["好"], c["差"]) / (c["好"] + c["差"]) if c["好"] + c["差"] else None
    has = maj != "平" and nmaj >= MIN_PAPERS and share >= MIN_SHARE - 1e-9
    verdict = "有多数" if has else "没有共识" if len(per) >= MIN_PAPERS else "不足 5 篇"
    return {"对": len(P), "篇": len(per), "好": c["好"], "差": c["差"], "近": c["近"], "多数": maj,
            "多数占比": round(share, 3) if share is not None else None, "多数方向来自几篇": nmaj,
            "判定": verdict, "有多数": has,
            "按篇": {"好": cp["好"], "差": cp["差"], "近": cp["近"], "多数": majp}}, per


def flips(R):
    """同一篇、同一对配方、同一类性能，在不同测试里一个变好一个变差。"""
    g = defaultdict(list)
    for r in R:
        if r["比较类型"] == SAME:
            g[(r["论文"], r["类别"], sample(r["A"]), sample(r["B"]))].append(r)
    out = []
    for (p, c, _, _), rs in sorted(g.items()):
        labs = {lab(effect(r)) for r in rs}
        if not {"好", "差"} <= labs:
            continue
        cond = {r["A"]["测试"]: {x["条件"]: x["A"] for x in r["条件"]} for r in rs}
        diffs = set()
        for t1, t2 in combinations(cond, 2):
            diffs |= {k for k in set(cond[t1]) | set(cond[t2]) if cond[t1].get(k) != cond[t2].get(k)}
        out.append({"论文": p, "性能": CN[c], "A": rs[0]["A"]["配方名"], "B": rs[0]["B"]["配方名"],
                    "各测试": [{"测试": r["A"]["测试"], "测试名": r["A"]["测试名"], "方向": lab(effect(r)), "倍数": r["性能"]["倍数"], "编号": r["编号"]} for r in rs],
                    "测试之间不同的条件": sorted(diffs), "组分变化": rs[0]["组分变化"]})
    return out


def also_changed(r, rule, names, against_ds=()):
    """这对比较里还一起变了什么：组分变化＋各个变了的描述符（及按多数应变好/变差）。"""
    c = r["类别"]
    parts = []
    for x in r["描述符"]:
        d = x["描述符"]
        if (d, c) in rule:
            maj, share = rule[(d, c)]
            pred = "好" if (maj == "好") == (up(x) > 0) else "差"
            note = f"按多数应{WORD[pred]} {share:.0%}"
        else:
            note = "无多数"
        tag = "【反对】" if d in against_ds else ""
        parts.append(f"{tag}{names[d]} {x['方向']}（{note}{'，被动' if x['被动'] else ''}）")
    e = effect(r)
    return {"编号": r["编号"], "A": r["A"]["配方名"], "B": r["B"]["配方名"], "测试": r["A"]["测试名"],
            "性能": f"{WORD[lab(e)]}（{CN[c]} {r['性能']['方向']}；{r['性能']['倍数含义']} ×{r['性能']['倍数']}）",
            "组分变化": r["组分变化"], "描述符": "；".join(parts),
            "特殊组分变化": "；".join(f"{x['组分']}（{x['类型']}）" for x in r.get("特殊组分变化") or [])}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    R = json.loads(IN.read_text(encoding="utf-8"))
    byid = {r["编号"]: r for r in R}
    names = {x["描述符"]: x["中文"] for r in R for x in r["描述符"]}

    # 第一遍：每个“描述符 → 性能”数票
    rows, S_of, per_of = [], {}, {}
    for d in names:
        for c in CN:
            S = votes(R, d, c, {SAME})
            A = votes(R, d, c, {SAME, MIXED})
            if not A:
                continue
            tS, perS = tally(S)
            tA, _ = tally(A)
            only = Counter(lab(p["效应"]) for p in S if p["只有它变"])
            grp = Counter(lab(p["效应"]) for p in S if p["组内只有它变"])
            npas = sum(p["被动"] for p in S)
            tNP = tally([p for p in S if not p["被动"]])[0] if npas and len(S) > npas else None
            nsp = sum(p["特殊"] for p in S)
            tNS = tally([p for p in S if not p["特殊"]])[0] if nsp else None
            rows.append({"d": d, "c": c, "描述符": names[d], "性能": CN[c], "同测试": tS, "全部比较": tA,
                         "只有它变": {"好": only["好"], "差": only["差"], "近": only["近"]},
                         "组内只有它变": {"好": grp["好"], "差": grp["差"], "近": grp["近"]},
                         "被动的对": npas,
                         "去掉被动后": ({"好": tNP["好"], "差": tNP["差"], "近": tNP["近"], "多数": tNP["多数"], "判定": tNP["判定"]} if tNP else None),
                         "含特殊组分的对": nsp,
                         "去掉特殊组分后": ({"好": tNS["好"], "差": tNS["差"], "近": tNS["近"], "多数": tNS["多数"], "判定": tNS["判定"]} if tNS else None)})
            S_of[(d, c)], per_of[(d, c)] = S, perS
    rule = {(r["d"], r["c"]): (r["同测试"]["多数"], r["同测试"]["多数占比"]) for r in rows if r["同测试"]["有多数"]}

    # 反对多数（逐个描述符）
    against = []
    for r in rows:
        tS = r["同测试"]
        if not tS["有多数"]:
            continue
        d, c = r["d"], r["c"]
        opp = "差" if tS["多数"] == "好" else "好"
        for p, effs in sorted(per_of[(d, c)].items()):
            ps = [x for x in S_of[(d, c)] if x["论文"] == p and lab(x["效应"]) == opp]
            if not ps:
                continue
            med = st.median(effs)
            against.append({"d": d, "描述符": names[d], "性能": CN[c], "多数": tS["多数"], "多数占比": tS["多数占比"], "论文": p,
                            "强弱": "强" if lab(med) == opp else "弱",
                            "相反的对数": len(ps), "本篇对数": len(effs), "本篇中位倍数（变好方向）": round(math.exp(med), 3),
                            "相反的对里有只有它变的": any(x["只有它变"] for x in ps),
                            "相反的对里有组内只有它变的": any(x["组内只有它变"] for x in ps),
                            "相反的对里被动的": sum(x["被动"] for x in ps),
                            "相反的对里有特殊组分的": sum(x["特殊"] for x in ps),
                            "相反的对编号": [x["编号"] for x in ps]})
    # 按“论文 × 性能 × 同一批比较”合并
    merged = defaultdict(list)
    for a in against:
        merged[(a["论文"], a["性能"], tuple(sorted(a["相反的对编号"])))].append(a)
    grouped = []
    for (p, c, ids), g in merged.items():
        ds = {a["d"] for a in g}
        grouped.append({"论文": p, "性能": c, "强弱": "强" if any(a["强弱"] == "强" for a in g) else "弱",
                        "涉及描述符": [f"{a['描述符']}（多数{WORD[a['多数']]} {a['多数占比']:.0%}；本篇 {a['相反的对数']}/{a['本篇对数']} 对相反，{a['强弱']}"
                                    + ("；相反的对里有被动" if a["相反的对里被动的"] else "") + "）" for a in g],
                        "全是被动": all(a["相反的对里被动的"] == a["相反的对数"] for a in g),
                        "全有特殊组分": all(a["相反的对里有特殊组分的"] == a["相反的对数"] for a in g),
                        "相反的对": [also_changed(byid[i], rule, names, ds) for i in ids]})
    grouped.sort(key=lambda g: (g["强弱"] != "强", g["性能"], g["论文"]))

    # 没有共识
    nocons = []
    for r in rows:
        tS = r["同测试"]
        if tS["判定"] != "没有共识":
            continue
        per = per_of[(r["d"], r["c"])]
        side = defaultdict(list)
        for p, effs in sorted(per.items()):
            side[lab(st.median(effs))].append(f"{p}（{len(effs)}）")
        nocons.append({"描述符": r["描述符"], "性能": r["性能"], "好": tS["好"], "差": tS["差"], "近": tS["近"],
                       "多数占比": tS["多数占比"], "篇": tS["篇"], "按篇": tS["按篇"],
                       "本篇多数变好的论文": side["好"], "本篇多数变差的论文": side["差"], "本篇相近的论文": side["近"]})
    nocons.sort(key=lambda x: (x["性能"], x["多数占比"] or 0))

    # 权衡：两类性能上都有多数且方向相反
    trade = []
    by_d = defaultdict(dict)
    for r in rows:
        if r["同测试"]["有多数"]:
            by_d[r["描述符"]][r["性能"]] = (r["同测试"]["多数"], r["同测试"]["多数占比"], r["同测试"]["篇"], r["同测试"]["好"], r["同测试"]["差"])
    for d, m in by_d.items():
        if {"好", "差"} <= {v[0] for v in m.values()}:
            trade.append({"描述符": d, "各性能": {k: f"多数{WORD[v[0]]}（{v[3]} 好 : {v[4]} 差，{v[1]:.0%}，{v[2]} 篇）" for k, v in m.items()}})

    fl = flips(R)

    # 提醒
    count_flip, cond_flip = [], []
    for r in rows:
        tS, tA = r["同测试"], r["全部比较"]
        perS = per_of[(r["d"], r["c"])]
        if tS["篇"] >= MIN_PAPERS and "平" not in (tS["多数"], tS["按篇"]["多数"]) and tS["多数"] != tS["按篇"]["多数"]:
            count_flip.append({"描述符": r["描述符"], "性能": r["性能"], "按对": f"好 {tS['好']} 差 {tS['差']}",
                               "按篇": f"好 {tS['按篇']['好']} 差 {tS['按篇']['差']}",
                               "贡献对数最多的论文": [f"{p}（{len(v)} 对）" for p, v in sorted(perS.items(), key=lambda x: -len(x[1]))[:3]]})
        if tA["篇"] >= MIN_PAPERS and tS["对"] and "平" not in (tS["多数"], tA["多数"]) and tS["多数"] != tA["多数"]:
            cond_flip.append({"描述符": r["描述符"], "性能": r["性能"], "同测试": f"好 {tS['好']} 差 {tS['差']}（{tS['篇']} 篇）",
                              "全部比较": f"好 {tA['好']} 差 {tA['差']}（{tA['篇']} 篇）"})

    for r in rows:
        r.pop("d"), r.pop("c")
    for a in against:
        a.pop("d")
    cand = {"反对多数（按同一批比较合并）": grouped, "反对多数（逐个描述符）": against, "没有共识": nocons,
            "条件依赖": fl, "权衡": trade, "提醒：计数方法不一致": count_flip, "提醒：同测试与全部不一致": cond_flip}
    verdicts = Counter(r["同测试"]["判定"] for r in rows)
    summary = {"组合": len(rows), "判定": dict(verdicts),
               "反对多数：合并后": len(grouped), "其中强": sum(g["强弱"] == "强" for g in grouped), "其中弱": sum(g["强弱"] == "弱" for g in grouped),
               "反对多数：论文": len({g["论文"] for g in grouped}),
               "反对多数：按性能": dict(Counter(g["性能"] for g in grouped)),
               "合并后只因被动变化": sum(g["全是被动"] for g in grouped),
               "合并后相反的对都有特殊组分变化": sum(g["全有特殊组分"] for g in grouped),
               "反对多数：逐个描述符": len(against),
               "没有共识": len(nocons), "条件依赖": len(fl), "权衡": len(trade),
               "提醒：计数方法不一致": len(count_flip), "提醒：同测试与全部不一致": len(cond_flip),
               "规则": "一对一票；≥ 5 篇且多数占比 ≥ 2/3 才算有多数；强 = 本篇中位效应也相反；初步，AI 辅助，用户尚未逐项人工确认"}
    (OUT / "票数.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "张力候选.json").write_text(json.dumps(cand, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "汇总.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")

    j = lambda x: "；".join(map(str, x))
    s1 = [[r["描述符"], r["性能"], r["同测试"]["判定"], r["同测试"]["对"], r["同测试"]["篇"], r["同测试"]["好"], r["同测试"]["差"], r["同测试"]["近"],
           r["同测试"]["多数"], r["同测试"]["多数占比"], r["同测试"]["多数方向来自几篇"],
           r["同测试"]["按篇"]["好"], r["同测试"]["按篇"]["差"], r["同测试"]["按篇"]["多数"],
           f"{r['只有它变']['好']}/{r['只有它变']['差']}", f"{r['组内只有它变']['好']}/{r['组内只有它变']['差']}",
           r["全部比较"]["对"], r["全部比较"]["篇"], r["全部比较"]["好"], r["全部比较"]["差"], r["全部比较"]["多数"],
           r["被动的对"], (f"好 {r['去掉被动后']['好']} 差 {r['去掉被动后']['差']}，{r['去掉被动后']['判定']}" if r["去掉被动后"] else ""),
           r["含特殊组分的对"], (f"好 {r['去掉特殊组分后']['好']} 差 {r['去掉特殊组分后']['差']}，{r['去掉特殊组分后']['判定']}" if r["去掉特殊组分后"] else "")] for r in rows]
    s2 = []
    for g in grouped:
        for k, x in enumerate(g["相反的对"]):
            s2.append([g["论文"], g["性能"], g["强弱"], j(g["涉及描述符"]) if k == 0 else "", "是" if g["全是被动"] and k == 0 else "",
                       x["编号"], x["A"], x["B"], x["测试"], x["性能"], x["组分变化"], x["特殊组分变化"], x["描述符"]])
    s3 = [[a["描述符"], a["性能"], a["多数"], a["多数占比"], a["论文"], a["强弱"], a["相反的对数"], a["本篇对数"], a["本篇中位倍数（变好方向）"],
           "有" if a["相反的对里有只有它变的"] else "", "有" if a["相反的对里有组内只有它变的"] else "", a["相反的对里被动的"], j(a["相反的对编号"])] for a in against]
    s4 = [[x["描述符"], x["性能"], x["好"], x["差"], x["近"], x["多数占比"], x["篇"], f"好 {x['按篇']['好']} 差 {x['按篇']['差']} 近 {x['按篇']['近']}",
           j(x["本篇多数变好的论文"]), j(x["本篇多数变差的论文"]), j(x["本篇相近的论文"])] for x in nocons]
    s5 = [[x["论文"], x["性能"], x["A"], x["B"], j(f"{t['测试']}（{t['测试名']}）{WORD[t['方向']]} ×{t['倍数']}" for t in x["各测试"]),
           j(x["测试之间不同的条件"]), x["组分变化"]] for x in fl]
    s6 = [[x["描述符"], j(f"{k}：{v}" for k, v in x["各性能"].items())] for x in trade]
    s7 = [[x["描述符"], x["性能"], x["按对"], x["按篇"], j(x["贡献对数最多的论文"])] for x in count_flip]
    s8 = [[x["描述符"], x["性能"], x["同测试"], x["全部比较"]] for x in cond_flip]
    write_xlsx(OUT / "张力候选表.xlsx", [
        ("票数（描述符×性能）", ["描述符", "性能", "判定", "同测试·对", "同测试·篇", "好", "差", "近", "多数", "多数占比", "多数方向来自几篇",
                          "按篇·好", "按篇·差", "按篇·多数", "只有它变 好/差", "组内只有它变 好/差", "全部·对", "全部·篇", "全部·好", "全部·差", "全部·多数",
                          "被动的对", "去掉被动后", "含特殊组分的对", "去掉特殊组分后"], s1),
        ("反对多数（按比较合并）", ["论文", "性能", "强弱", "涉及的描述符", "只因被动变化", "编号", "A", "B（参照）", "测试", "性能变化", "组分变化", "特殊组分变化",
                         "还一起变了什么（描述符；【反对】= 本条反对的描述符）"], s2),
        ("反对多数（逐个描述符）", ["描述符", "性能", "多数", "多数占比", "论文", "强弱", "相反的对数", "本篇对数", "本篇中位倍数（变好方向）",
                         "相反的对里有只有它变的", "相反的对里有组内只有它变的", "相反的对里被动的", "相反的对编号"], s3),
        ("没有共识", ["描述符", "性能", "好", "差", "近", "多数占比", "篇", "按篇", "本篇多数变好的论文（对数）", "本篇多数变差的论文（对数）", "本篇相近的论文（对数）"], s4),
        ("条件依赖", ["论文", "性能", "A", "B（参照）", "各测试的方向", "测试之间不同的条件", "组分变化"], s5),
        ("权衡", ["描述符", "各性能的多数方向"], s6),
        ("提醒·计数方法不一致", ["描述符", "性能", "一对一票", "一篇一票", "贡献对数最多的论文"], s7),
        ("提醒·同测试与全部不一致", ["描述符", "性能", "只用同测试", "全部比较"], s8)],
        notes=["张力候选（step17，11-07 规则，描述符修正版 v2）。“特殊组分变化”= 作者改动的组分里有成膜/活性溶剂或描述符看不到的组分，照样计票、单独标出。“好/差/近”= 描述符变高时性能变好/变差/相差 < 5%。一对一票为主，按篇为复核。",
               "有多数 = 多数占比 ≥ 2/3 且多数方向的对来自 ≥ 5 篇；没有共识 = ≥ 5 篇但不满足；强 = 本篇中位效应也与多数相反，只排阅读先后。",
               "“还一起变了什么”供读原文参考，程序不判原因。初步，AI 辅助，用户尚未逐项人工确认。"])
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
