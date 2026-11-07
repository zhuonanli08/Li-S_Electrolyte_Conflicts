"""step19：协同作用候选（11-07 用户定：一次改好几样很正常，正好看各变量的协同作用；第 5 类张力候选）。

思路：同一篇、同一类性能、同一个测试里，同一种改动（同样的组分、同样的增减方向，用量可以不同）在两个以上不同的配方“底子”上做过，
比较这一改动在各底子上的效果（变好 / 变差 / 相近，门槛同 step17：倍数 5%）。
- 交叉设计：两个底子差的是另一种组分（如 P112：盐 1→4 M，在不加 LiNO₃ 的底子上 CE 80.0→95.3，在加了 LiNO₃ 的底子上 98.1→98.0）→ 协同作用候选。
- 剂量系列：两个底子只差这个组分自己的用量（如 P111：LiNO₃ 0.1→0.5 衰减变好、0.5→1.0 变差）→ 剂量依赖候选（协同作用的小类）。
同一改动在不同底子上一好一差记“方向相反”，一边有效一边相近记“一边有效一边相近”，都列为候选；其余记“一致”。
只用同测试换配方的比较；组成未记录、用量没法比大小的比较跳过。特殊组分照样算，只标出。初步；AI 辅助，用户尚未逐项人工确认。
输入（只读）：output/两两比较表述_313篇_v2_2026-11-07/比较表述.json；配方组成经 step16 → step13h 读取（组分结构表_试跑313篇_2026-11-05）。
输出：output/协同候选_313篇_v2_2026-11-07/（协同候选.json、协同候选表.xlsx、汇总.json）。只放比较编号和数值，不放原句。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step19_synergy.py
"""
import json
import math
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
import step16_pairwise_statements as P16
import step17_tension_trial as S
from step13_common import write_xlsx

IN = ROOT / "output" / "两两比较表述_313篇_v2_2026-11-07" / "比较表述.json"
OUT = ROOT / "output" / "协同候选_313篇_v2_2026-11-07"
MAJ = ROOT / "output" / "张力候选_313篇_v2_2026-11-07" / "张力候选.json"
VOTES = MAJ.with_name("票数.json")
OPT_RATIO = 2.0  # 同一组分、同一性能、同一单位，几篇的最佳用量相差 ≥ 2 倍记“最佳用量各篇不同”
CN = {"首圈容量": "首圈容量", "每圈衰减率": "每圈衰减率", "LiCu_CE": "Li‖Cu CE"}
WORD = {"好": "变好", "差": "变差", "近": "相近"}


def comp(p, rid):
    return P16.comps(p, rid) if rid is not None else None


def num(i):
    """用量数值：先用 step13h 解析的“数值”；没有时，原文用量是纯数字才用（如 0.8 mol/mol、50 ppm）；写明为 0 的记 0。"""
    v = i.get("数值")
    if isinstance(v, (int, float)):
        return v
    t = str(i.get("原文用量", "")).strip()
    if t == "0" or t.startswith("0（"):
        return 0.0
    try:
        return float(t)
    except ValueError:
        return None


def signs(r):
    """A 相对 B 改了哪些组分、各是增是减；有一个分不出增减就返回 None。"""
    ca, cb = comp(r["论文"], r["A"]["recipe"]), comp(r["论文"], r["B"]["recipe"])
    if not ca or not cb:
        return None
    _, changed = P16.comp_change(ca, cb)
    if not changed:
        return None
    out = []
    for c in sorted(changed):
        if c in ca and c not in cb:
            out.append((c, 1))
        elif c in cb and c not in ca:
            out.append((c, -1))
        else:
            x, y = num(ca[c]), num(cb[c])
            if x is None or y is None or x == y or (ca[c]["原文单位"] != cb[c]["原文单位"] and 0 not in (x, y)):
                return None
            out.append((c, 1 if x > y else -1))
    return tuple(out)


def amount(p, rid, c):
    i = (comp(p, rid) or {}).get(c)
    return 0.0 if i is None else num(i)


def sig_text(sig):
    return "；".join(f"{c} {'增加' if s > 0 else '减少'}" for c, s in sig)


def members():
    """按（论文, 性能, 测试, 改动）分组；改动统一成第一个组分“增加”的方向，底子 = 改动前的配方。"""
    R = json.loads(IN.read_text(encoding="utf-8"))
    g, skip = defaultdict(list), Counter()
    for r in R:
        if r["比较类型"] != S.SAME:
            continue
        if r.get("电解液相同但样品编号不同"):
            skip["电解液相同"] += 1
            continue
        sig = signs(r)
        if sig is None:
            skip["组成未记录或增减分不出"] += 1
            continue
        e = S.effect(r)
        lo, hi, vlo, vhi = r["B"], r["A"], r["性能"]["值B"], r["性能"]["值A"]
        if sig[0][1] < 0:
            sig = tuple((c, -s) for c, s in sig)
            e, lo, hi, vlo, vhi = -e, hi, lo, vhi, vlo
        g[(r["论文"], r["类别"], r["A"]["测试"], sig)].append({
            "编号": r["编号"], "底子": lo["配方名"], "底子配方": lo["recipe"], "改后": hi["配方名"], "改后配方": hi["recipe"],
            "测试名": r["A"]["测试名"], "值（底子）": vlo, "值（改后）": vhi, "倍数（变好方向）": round(math.exp(e), 3), "效应": e,
            "票": S.lab(e), "特殊组分": [x["组分"] for x in r.get("特殊组分变化") or []]})
    return g, skip, len(R)


def relation(p, m1, m2, sig):
    """两个成员之间：底子（和改后）只差改动组分自己的用量 → 剂量系列；还差别的组分 → 交叉设计。"""
    comps_in_sig = {c for c, _ in sig}
    d_lo, t_lo = set(), ""
    if m1["底子配方"] != m2["底子配方"]:
        t_lo, ch = P16.comp_change(comp(p, m2["底子配方"]), comp(p, m1["底子配方"]))
        d_lo = set(ch or ())
    d_hi = set()
    if m1["改后配方"] != m2["改后配方"]:
        _, ch = P16.comp_change(comp(p, m2["改后配方"]), comp(p, m1["改后配方"]))
        d_hi = set(ch or ())
    if not d_lo and not d_hi:
        return None, ""
    other = (d_lo | d_hi) - comps_in_sig
    return ("交叉设计" if other else "剂量系列"), t_lo


def series(p, ms, sig):
    """剂量系列：改动组分的用量 → 性能值；返回 [(用量, 配方名, 值, 单位)]，按用量排序。"""
    c0 = sig[0][0]
    vals = {}
    for m in ms:
        vals.setdefault(m["底子配方"], (m["底子"], m["值（底子）"]))
        vals.setdefault(m["改后配方"], (m["改后"], m["值（改后）"]))
    pts = []
    for rid, (name, v) in vals.items():
        a = amount(p, rid, c0)
        if a is not None:
            i = (comp(p, rid) or {}).get(c0)
            pts.append((a, name, v, i["原文单位"] if i else ""))
    return sorted(pts, key=lambda x: x[0])


def shape(pts, cls):
    """序列形状（按性能好坏说）：中间最好 / 中间最差 / 来回变；返回 (形状, 最佳用量, 单位)。"""
    if len(pts) < 3:
        return "", None, ""
    vs = [v for _, _, v, _ in pts]
    good = (lambda v: -v) if cls == "每圈衰减率" else (lambda v: v)
    ib = max(range(len(vs)), key=lambda i: good(vs[i]))
    iw = min(range(len(vs)), key=lambda i: good(vs[i]))
    if 0 < ib < len(vs) - 1:
        return "中间最好", pts[ib][0], pts[ib][3]
    if 0 < iw < len(vs) - 1:
        return "中间最差", None, ""
    return "来回变", None, ""


def against_majority():
    """step17 的反例（逐个描述符）：比较编号 → 它反对的多数规律（与张力候选同一口径）。"""
    c = json.loads(MAJ.read_text(encoding="utf-8"))["反例（逐个描述符）"]
    V = {(v["描述符"], v["性能"]): (v.get("去掉特殊组分后") or {}).get("判定") for v in json.loads(VOTES.read_text(encoding="utf-8"))}
    out = defaultdict(list)
    for x in c:
        t = V.get((x["描述符"], x["性能"]))
        note = f"；去掉特殊组分后{t}，这条多数站不住" if t and t != "有多数" else ""
        for i in x["相反的对编号"]:
            out[i].append(f"{x['描述符']} → {x['性能']}（多数变{x['多数']} {round(100 * x['多数占比'])}%{note}）")
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g, skip, n_all = members()
    groups = []
    for (p, cls, test, sig), ms in sorted(g.items()):
        if len({(m["底子配方"], m["改后配方"]) for m in ms}) < 2:
            continue
        found = []
        for m1, m2 in combinations(ms, 2):
            kind, diff = relation(p, m1, m2, sig)
            if kind is None:
                continue
            labs = {m1["票"], m2["票"]}
            rel = "方向相反" if labs == {"好", "差"} else "一边有效一边相近" if len(labs) == 2 else "一致"
            found.append({"类型": kind, "关系": rel, "成员": [m1["编号"], m2["编号"]], "底子差在": diff})
        if not found:
            continue
        hits = [f for f in found if f["关系"] != "一致"]
        hc = [f for f in hits if f["类型"] == "交叉设计"]
        hd = [f for f in hits if f["类型"] == "剂量系列"]
        rel = lambda hs: "方向相反" if any(f["关系"] == "方向相反" for f in hs) else "一边有效一边相近" if hs else "一致"
        x = {"论文": p, "性能": CN[cls], "测试": test, "测试名": ms[0]["测试名"], "改动": sig_text(sig),
             "交叉设计": rel(hc) if hc else "", "剂量系列": rel(hd) if hd else "",
             "成员": [{k: v for k, v in m.items() if k not in ("底子配方", "改后配方", "效应")} for m in ms],
             "发现": hits, "底子差在": sorted({f["底子差在"] for f in hc if f["底子差在"]}),
             "特殊组分": sorted({c for m in ms for c in m["特殊组分"]})}
        if hd and len(sig) == 1:
            pts = series(p, ms, sig)
            x["剂量序列"] = [f"{a:g} {u}：{name} {v}".replace(" ：", "：") for a, name, v, u in pts]
            x["形状"], x["最佳用量"], x["单位"] = shape(pts, cls)
            x["组分"] = sig[0][0]
        groups.append(x)
    # 11-07 用户定：交叉设计（方向相反、一边有效一边相近）都是协同作用候选；剂量系列只留方向相反（有峰或谷），
    # 一边有效一边相近（单调加一段平台）不列为候选；剂量依赖只在与多数规律相反、或同一组分各篇最佳用量相差 ≥ 2 倍时才算张力
    anti = against_majority()
    opt = defaultdict(list)
    for x in groups:
        if x["剂量系列"] == "方向相反" and x.get("形状") == "中间最好":
            opt[(x["组分"], x["性能"], x["单位"])].append(x)
    for x in groups:
        if x["交叉设计"]:
            x["结果"] = "协同作用候选"
        elif x["剂量系列"] == "方向相反":
            why = []
            a = sorted({s for m in x["成员"] for s in anti.get(m["编号"], [])})
            if a:
                why.append("与多数相反：" + "；".join(a))
            peers = opt.get((x.get("组分"), x["性能"], x.get("单位")), [])
            ps = [y for y in peers if y["论文"] != x["论文"]]
            if x.get("最佳用量") and ps:
                lo = min([x["最佳用量"]] + [y["最佳用量"] for y in ps])
                hi = max([x["最佳用量"]] + [y["最佳用量"] for y in ps])
                if lo > 0 and hi / lo >= OPT_RATIO:
                    why.append("最佳用量各篇不同：" + "；".join(f"{y['论文']} {y['最佳用量']:g} {y['单位']}" for y in [x] + ps))
            solid = (a and any("站不住" not in s for s in a)) or any(w.startswith("最佳用量") for w in why)
            x["结果"] = ("剂量依赖·算张力" if solid else "剂量依赖·待定（反对的多数去掉特殊组分后站不住）") if why \
                else "剂量依赖·不算张力（作者找最佳用量）"
            x["为什么"] = why
        elif x["剂量系列"] == "一边有效一边相近":
            x["结果"] = "不列为候选（剂量系列单调加一段平台）"
        else:
            x["结果"] = "不列为候选（各底子上一致）"
    cand = [x for x in groups if x["结果"] == "协同作用候选" or x["结果"].startswith("剂量依赖")]
    for k, x in enumerate(cand, 1):
        x["编号"] = f"SY{k:02d}"
    summ = {"能分出增减的同测试比较": sum(len(ms) for ms in g.values()), "跳过": dict(skip),
            "同一改动在 ≥2 个底子上做过的组": len(groups), "篇": len({x["论文"] for x in groups}),
            "按结果": Counter(x["结果"] for x in groups),
            "候选": len(cand), "候选篇": len({x["论文"] for x in cand}),
            "算张力的": [f"{x['编号']} {x['论文']} {x['性能']} {x['改动']}" for x in cand if x["结果"] in ("协同作用候选", "剂量依赖·算张力")],
            "按性能": Counter(x["性能"] for x in cand), "含特殊组分的候选": sum(bool(x["特殊组分"]) for x in cand)}
    (OUT / "协同候选.json").write_text(json.dumps({"候选": cand, "不列为候选的组": [x for x in groups if x not in cand]},
                                               ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "汇总.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1, default=dict), encoding="utf-8")

    def eff(x):
        return "；".join(f"{m['底子']} → {m['改后']}：{m['值（底子）']} → {m['值（改后）']}（{WORD[m['票']]}）" for m in x["成员"])
    j = "；".join
    head_c = ["编号", "论文", "性能", "测试", "改动", "关系", "各底子上的效果", "底子差在", "特殊组分", "比较编号", "✍ 用户意见"]
    rows_c = [[x["编号"], x["论文"], x["性能"], x["测试名"], x["改动"], x["交叉设计"], eff(x), x["底子差在"], x["特殊组分"],
               [m["编号"] for m in x["成员"]], ""] for x in cand if x["结果"] == "协同作用候选"]
    head_d = ["编号", "论文", "性能", "测试", "改动", "结果", "为什么算张力", "形状", "剂量序列（用量：配方 值）", "各对比较", "特殊组分", "比较编号", "✍ 用户意见"]
    rows_d = [[x["编号"], x["论文"], x["性能"], x["测试名"], x["改动"], x["结果"], j(x.get("为什么", [])), x.get("形状", ""), x.get("剂量序列", ""),
               eff(x), x["特殊组分"], [m["编号"] for m in x["成员"]], ""] for x in cand if x["结果"].startswith("剂量依赖")]
    allrows = [[x.get("编号", ""), x["论文"], x["性能"], x["测试名"], x["改动"], x["结果"], x["交叉设计"], x["剂量系列"], x.get("剂量序列", ""), eff(x), x["特殊组分"]]
               for x in groups]
    write_xlsx(OUT / "协同候选表.xlsx", [
        ("交叉设计（协同作用）", head_c, rows_c),
        ("剂量系列（有峰或谷）", head_d, rows_d),
        ("全部组", ["编号", "论文", "性能", "测试", "改动", "结果", "交叉设计", "剂量系列", "剂量序列", "各对比较", "特殊组分"], allrows)],
        notes=["协同作用候选（step19，11-07）：同一篇、同一性能、同一测试里，同一种改动（同组分、同增减方向）在 ≥ 2 个不同底子上做过，比较各底子上的效果。",
               "交叉设计 = 底子差的是另一种组分（协同作用候选）；剂量系列 = 只差这个组分自己的用量（剂量依赖）。",
               "关系：方向相反 = 一个底子上变好、另一个变差；一边有效一边相近 = 一个底子上变化 ≥ 5%、另一个 < 5%。CE 按损失（100 − CE）之比，衰减按每圈衰减率之比。",
               "11-07 用户定：剂量系列只留方向相反（有峰或谷），单调加一段平台的不列为候选；剂量依赖只在与多数规律相反（用 step17 反例的同一口径）、"
               "或同一组分同一单位各篇最佳用量相差 ≥ 2 倍时算张力，其余记“不算张力（作者找最佳用量）”；反对的多数去掉特殊组分后都不再是多数的，记“待定”。",
               "只用同测试换配方；特殊组分照样算、只标出。只放比较编号和数值，不放原句。初步；AI 辅助，用户尚未逐项人工确认。✍ 列留给用户填写。"])
    print(json.dumps(summ, ensure_ascii=False, indent=1, default=dict))
    for x in cand:
        print(x["编号"], x["论文"], x["性能"], x["改动"], x["结果"], x.get("形状", ""), "|", j(x.get("为什么", []))[:160])


if __name__ == "__main__":
    main()
