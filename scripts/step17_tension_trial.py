"""step17：张力候选试算（11-06 用户同意先按已定规则在 313 篇上试算，看了结果再定“张力强弱”和“张力类型”）。

只读 step16 的 比较表述.json。按细则 ③“计数”：
1. 统一方向：每对写成“描述符 X 变高时，性能变好还是变差”（X 变低的对翻过来）。效应 = ln 倍数，> 0 = 变好
   （容量取容量之比；衰减取每圈衰减率之比的倒数；CE 取损失比的倒数）。|效应| < ln1.05 记“相近”。
2. 数票：一对一票为主；另按论文复核（每篇一票，取本篇各对效应的中位数）。只用同测试换配方的比较数一遍，
   全部比较（再加上配方和条件都变的）数一遍。几个描述符同时变的对照样投票；另数“只有它变”（22 个描述符＋LiNO₃ 里只有它变）
   和“组内只有它变”（meta v3 同一轴里只有它变）的对。多数方向 = 变好、变差两边对数多的一边；多数方向的对至少来自 5 篇论文
   才判“有多数”，否则只记录。被动变化的对照样计入，另报去掉被动后的多数方向。
3. 列出（试算；张力类型和强弱用户尚未定，下面只是供讨论的分组）：
   - 反对多数：有多数的组合里，给出相反方向对的论文；附本篇中位效应是否超出“粗略正常范围”
     （各篇中位效应的平均 ± 2 倍标准差，未加权，仅供讨论）；同一批比较在几个描述符下各出现一次的，另按“论文 × 性能 × 同一批比较”合并；
   - 计数方法不一致：一对一票与一篇一票的多数方向不同（组合至少 5 篇）；
   - 同测试与全部不一致：两遍的多数方向不同（提示条件依赖；全部比较至少 5 篇）；
   - 换条件方向相反（细则 ③ FLIP）：同一篇、同一对配方、同一类性能，在两个测试里一个变好一个变差；
   - 权衡：同一描述符在两类性能上都有多数，且方向相反。
初步；AI 辅助，用户尚未逐项人工确认。只用原句编号，不放原句。
输出：output/张力试算_313篇_2026-11-06/（票数.json、张力候选.json、张力试算表.xlsx）。
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

IN = ROOT / "output" / "两两比较表述_313篇_2026-11-06" / "比较表述.json"
OUT = ROOT / "output" / "张力试算_313篇_2026-11-06"
CN = {"首圈容量": "首圈容量", "每圈衰减率": "每圈衰减率", "LiCu_CE": "Li‖Cu CE"}
T, MIN_PAPERS = math.log(1.05), 5
SAME, MIXED = "同测试换配方", "配方和条件都变"


def effect(r):
    lr = math.log(r["性能"]["倍数"])
    return lr if r["类别"] == "首圈容量" else -lr


def lab(v):
    return "好" if v > T else "差" if v < -T else "近"


def sample(s):
    return s["recipe"] or s["配方"]


def votes(R, d, c, types):
    out = []
    for r in R:
        if r["类别"] != c or r["比较类型"] not in types:
            continue
        ds = r["描述符"]
        x = next((y for y in ds if y["描述符"] == d), None)
        if not x:
            continue
        s = 1 if x["方向"].startswith("变高") else -1
        out.append({"论文": r["论文"], "效应": s * effect(r), "只有它变": len(ds) == 1,
                    "组内只有它变": not any(y["组"] == x["组"] and y["描述符"] != d for y in ds), "被动": x["被动"],
                    "编号": r["编号"], "A": r["A"]["配方名"], "B": r["B"]["配方名"], "比较类型": r["比较类型"]})
    return out


def tally(P):
    c = Counter(lab(p["效应"]) for p in P)
    per = defaultdict(list)
    for p in P:
        per[p["论文"]].append(p["效应"])
    cp = Counter(lab(st.median(v)) for v in per.values())
    maj = "好" if c["好"] > c["差"] else "差" if c["差"] > c["好"] else "平"
    majp = "好" if cp["好"] > cp["差"] else "差" if cp["差"] > cp["好"] else "平"
    nmaj = len({p["论文"] for p in P if lab(p["效应"]) == maj}) if maj != "平" else 0
    return {"对": len(P), "篇": len(per), "好": c["好"], "差": c["差"], "近": c["近"], "多数": maj,
            "多数占比": round(max(c["好"], c["差"]) / (c["好"] + c["差"]), 3) if c["好"] + c["差"] else None,
            "多数方向来自几篇": nmaj, "有多数": maj != "平" and nmaj >= MIN_PAPERS,
            "按篇": {"好": cp["好"], "差": cp["差"], "近": cp["近"], "多数": majp}}, per


def normal_range(per):
    meds = [st.median(v) for v in per.values()]
    if len(meds) < MIN_PAPERS:
        return None
    m, sd = st.mean(meds), st.stdev(meds)
    return (m - 2 * sd, m + 2 * sd)


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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    R = json.loads(IN.read_text(encoding="utf-8"))
    names = {x["描述符"]: x["中文"] for r in R for x in r["描述符"]}
    rows, against, count_flip, cond_flip = [], [], [], []
    for d in names:
        for c in CN:
            S = votes(R, d, c, {SAME})
            A = votes(R, d, c, {SAME, MIXED})
            if not A:
                continue
            tS, perS = tally(S) if S else ({"对": 0, "篇": 0, "好": 0, "差": 0, "近": 0, "多数": "—", "多数占比": None, "多数方向来自几篇": 0,
                                            "有多数": False, "按篇": {"好": 0, "差": 0, "近": 0, "多数": "—"}}, {})
            tA, _ = tally(A)
            only = Counter(lab(p["效应"]) for p in S if p["只有它变"])
            grp = Counter(lab(p["效应"]) for p in S if p["组内只有它变"])
            npas = sum(p["被动"] for p in S)
            tNP = tally([p for p in S if not p["被动"]])[0]["多数"] if npas and len(S) > npas else None
            rng = normal_range(perS) if S else None
            row = {"描述符": names[d], "性能": CN[c], "同测试": tS, "全部比较": tA,
                   "只有它变": {"好": only["好"], "差": only["差"], "近": only["近"]}, "组内只有它变": {"好": grp["好"], "差": grp["差"], "近": grp["近"]},
                   "被动的对": npas, "去掉被动后的多数": tNP,
                   "粗略正常范围_倍数": [round(math.exp(x), 3) for x in rng] if rng else None}
            rows.append(row)
            if tS["有多数"]:
                opp = "差" if tS["多数"] == "好" else "好"
                for p, effs in sorted(perS.items()):
                    ps = [x for x in S if x["论文"] == p and lab(x["效应"]) == opp]
                    if not ps:
                        continue
                    med = st.median(effs)
                    against.append({"描述符": names[d], "性能": CN[c], "多数": tS["多数"], "多数占比": tS["多数占比"], "论文": p,
                                    "相反的对": len(ps), "本篇对数": len(effs), "本篇中位倍数（变好方向）": round(math.exp(med), 3),
                                    "超出粗略正常范围": (med < rng[0] or med > rng[1]) if rng else None,
                                    "相反的对里有只有它变的": any(x["只有它变"] for x in ps), "相反的对里有组内只有它变的": any(x["组内只有它变"] for x in ps),
                                    "相反的对里被动的": sum(x["被动"] for x in ps),
                                    "相反的对": [f"{x['编号']} {x['A']} 相对 {x['B']}" for x in ps]})
            if tS["篇"] >= MIN_PAPERS and "平" not in (tS["多数"], tS["按篇"]["多数"]) and tS["多数"] != tS["按篇"]["多数"]:
                count_flip.append({"描述符": names[d], "性能": CN[c], "按对": f"好 {tS['好']} 差 {tS['差']}", "按篇": f"好 {tS['按篇']['好']} 差 {tS['按篇']['差']}",
                                   "贡献对数最多的论文": [f"{p}（{len(v)} 对）" for p, v in sorted(perS.items(), key=lambda x: -len(x[1]))[:3]]})
            if tA["篇"] >= MIN_PAPERS and S and "平" not in (tS["多数"], tA["多数"]) and tS["多数"] != tA["多数"]:
                cond_flip.append({"描述符": names[d], "性能": CN[c], "同测试": f"好 {tS['好']} 差 {tS['差']}（{tS['篇']} 篇）",
                                  "全部比较": f"好 {tA['好']} 差 {tA['差']}（{tA['篇']} 篇）"})
    trade = []
    by_d = defaultdict(dict)
    for r in rows:
        if r["同测试"]["有多数"]:
            by_d[r["描述符"]][r["性能"]] = (r["同测试"]["多数"], r["同测试"]["多数占比"], r["同测试"]["篇"])
    for d, m in by_d.items():
        if {"好", "差"} <= {v[0] for v in m.values()}:
            trade.append({"描述符": d, "各性能": {k: f"多数{'变好' if v[0] == '好' else '变差'}（{v[1]:.0%}，{v[2]} 篇）" for k, v in m.items()}})
    fl = flips(R)
    # 同一批相反的比较常在好几个描述符下各出现一次（几个描述符一起变），按“论文 × 性能 × 同一批比较”合并成一条
    merged = defaultdict(list)
    for a in against:
        merged[(a["论文"], a["性能"], tuple(sorted(a["相反的对"])))].append(a)
    grouped = [{"论文": p, "性能": c, "相反的对": list(ps), "涉及描述符": [f"{a['描述符']}（多数{'变好' if a['多数'] == '好' else '变差'} {a['多数占比']:.0%}"
                                                                    + ("，被动" if a["相反的对里被动的"] else "") + ("，超出粗略范围" if a["超出粗略正常范围"] else "") + "）" for a in g],
                "全是被动": all(a["相反的对里被动的"] == len(a["相反的对"]) for a in g)} for (p, c, ps), g in sorted(merged.items())]
    cand = {"反对多数": against, "反对多数（按同一批比较合并）": grouped, "计数方法不一致": count_flip, "同测试与全部不一致": cond_flip,
            "换条件方向相反": fl, "权衡": trade}
    (OUT / "票数.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "张力候选.json").write_text(json.dumps(cand, ensure_ascii=False, indent=1), encoding="utf-8")
    j = lambda x: "；".join(map(str, x))
    s1 = [[r["描述符"], r["性能"], r["同测试"]["对"], r["同测试"]["篇"], r["同测试"]["好"], r["同测试"]["差"], r["同测试"]["近"], r["同测试"]["多数"],
           r["同测试"]["多数占比"], r["同测试"]["多数方向来自几篇"], "是" if r["同测试"]["有多数"] else "", r["同测试"]["按篇"]["好"], r["同测试"]["按篇"]["差"],
           r["同测试"]["按篇"]["多数"], f"{r['只有它变']['好']}/{r['只有它变']['差']}", f"{r['组内只有它变']['好']}/{r['组内只有它变']['差']}",
           r["全部比较"]["对"], r["全部比较"]["篇"], r["全部比较"]["好"], r["全部比较"]["差"], r["全部比较"]["多数"], r["被动的对"], r["去掉被动后的多数"] or "",
           "–".join(f"×{x}" for x in r["粗略正常范围_倍数"]) if r["粗略正常范围_倍数"] else ""] for r in rows]
    s2 = [[a["描述符"], a["性能"], a["多数"], a["多数占比"], a["论文"], a["相反的对"], a["本篇对数"], a["本篇中位倍数（变好方向）"],
           {True: "超出", False: "范围内", None: ""}[a["超出粗略正常范围"]], "有" if a["相反的对里有只有它变的"] else "", "有" if a["相反的对里有组内只有它变的"] else "",
           j(a["相反的对"])] for a in against]
    s2g = [[g["论文"], g["性能"], len(g["相反的对"]), j(g["相反的对"]), len(g["涉及描述符"]), j(g["涉及描述符"]), "是" if g["全是被动"] else ""] for g in grouped]
    s3 = [[x["描述符"], x["性能"], x["按对"], x["按篇"], j(x["贡献对数最多的论文"])] for x in count_flip]
    s4 = [[x["描述符"], x["性能"], x["同测试"], x["全部比较"]] for x in cond_flip]
    s5 = [[x["论文"], x["性能"], x["A"], x["B"], j(f"{t['测试']}（{t['测试名']}）{t['方向']} ×{t['倍数']}" for t in x["各测试"]), j(x["测试之间不同的条件"]),
           x["组分变化"]] for x in fl]
    s6 = [[x["描述符"], j(f"{k}：{v}" for k, v in x["各性能"].items())] for x in trade]
    write_xlsx(OUT / "张力试算表.xlsx", [
        ("票数（描述符×性能）", ["描述符", "性能", "同测试·对", "同测试·篇", "好", "差", "近", "多数", "多数占比", "多数方向来自几篇", "有多数（≥5 篇）",
                          "按篇·好", "按篇·差", "按篇·多数", "只有它变 好/差", "组内只有它变 好/差", "全部·对", "全部·篇", "全部·好", "全部·差", "全部·多数",
                          "被动的对", "去掉被动后的多数", "粗略正常范围（各篇中位倍数）"], s1),
        ("反对多数（按比较合并）", ["论文", "性能", "相反的对数", "相反的对", "涉及几个描述符", "涉及的描述符（多数方向，标记）", "只因被动变化"], s2g),
        ("反对多数（逐个描述符）", ["描述符", "性能", "多数", "多数占比", "论文", "相反的对", "本篇对数", "本篇中位倍数", "粗略正常范围", "相反的对里有只有它变的",
                     "相反的对里有组内只有它变的", "相反的对"], s2),
        ("计数方法不一致", ["描述符", "性能", "一对一票", "一篇一票", "贡献对数最多的论文"], s3),
        ("同测试与全部不一致", ["描述符", "性能", "只用同测试", "全部比较"], s4),
        ("换条件方向相反", ["论文", "性能", "A", "B（参照）", "各测试的方向", "测试之间不同的条件", "组分变化"], s5),
        ("权衡", ["描述符", "各性能的多数方向"], s6)],
        notes=["张力候选试算（step17，11-06）。“好/差/近”= 描述符变高时性能变好/变差/相差 < 5%。一对一票为主，按篇为复核。",
               "“有多数”= 多数方向的对至少来自 5 篇论文。粗略正常范围 = 各篇中位效应平均 ± 2 倍标准差（未加权，仅供讨论）。张力类型与强弱尚未定。初步，AI 辅助，用户尚未逐项人工确认。"])
    print(json.dumps({"组合": len(rows), "有多数的组合": sum(r["同测试"]["有多数"] for r in rows),
                      "反对多数：条目": len(against), "反对多数：论文": len({a["论文"] for a in against}),
                      "反对多数：合并后": len(grouped), "合并后只因被动变化": sum(g["全是被动"] for g in grouped),
                      "其中超出粗略正常范围": sum(1 for a in against if a["超出粗略正常范围"]),
                      "计数方法不一致": len(count_flip), "同测试与全部不一致": len(cond_flip), "换条件方向相反": len(fl), "权衡": len(trade)},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
