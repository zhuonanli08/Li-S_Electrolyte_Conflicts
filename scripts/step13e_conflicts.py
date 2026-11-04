"""step13e：矛盾候选（11-04 用户要求归一化后重做）。在 step13f 之后运行。

五种候选（方案 §8.7 两种的扩展；11-04 讨论）：
  NORM 归一化后同配方跨篇差距大：同一配方（组分集合相同、溶剂体积分数差 ≤0.1、盐浓度 ≤1.5 倍、LiNO₃ 0.5–2 倍）在不同论文中，
       各自归一化到普遍条件（非外推表述）后中位数仍相差 ≥1.5 倍（CE 损失比 ≥2 倍）。
  LOPO 篇内结论与跨文献模型相反：某篇同一测试、同一取值点，配方 vs 对照的实测方向，与“不含这篇”训练的主模型预测方向相反，
       两者 |差距| 都 ≥ln1.1；只在主模型 V1 篇内 R² > 0 的类别做。
  FLIP 条件依赖翻转：同篇同一对配方、同一类性能，换测试条件（或圈数）后方向相反。
  DESC 设计方向相反：跨篇，改动只涉及溶剂与主盐（LiNO₃、添加剂不变，两侧元素比例都可算），sO 或 F/O 往同一方向变，一篇变好一篇变坏。
  SAME 严格同一改动：主改动签名完全相同，一篇变好一篇变坏。
方向：容量等取对数比，CE 用损失比 ln[(100−CE_A)/(100−CE_B)]，|效应| < ln1.05 记差异小；两侧没有数值时用作者定性方向（标“定性”）。
人工判断层：矛盾核对.json（Claude 逐条回原文核对后写入；键 = 候选编号）。
输出：矛盾候选.json、篇内配对_方向.json、矛盾候选复核表.xlsx、step13e_汇总.json
"""
from __future__ import annotations

import itertools
import json
import math
from collections import Counter, defaultdict

from step13_common import COMP, LABEL, OUT, in_analysis, load_papers, load_sources, read_json, sentences, write_json, write_xlsx

SMALL = math.log(1.05)


def effect(std: str, a: float, b: float, higher_better) -> float | None:
    """A 相对 B 的效应，>0 表示 A 更好。"""
    if a is None or b is None:
        return None
    if "CE" in std and "圈数" not in std:
        if a >= 100 or b >= 100:
            return None
        return -math.log((100 - a) / (100 - b))
    if a <= 0 or b <= 0:
        return None
    e = math.log(a / b)
    return e if higher_better is not False else -e


LINO3_MW, SOLN_DENSITY = 68.95, 1.2  # g/mol；醚类 1 M 盐溶液密度约 1.2 g/mL（近似，只用于 LiNO₃ 0.5–2 倍匹配）


def recipe_items(comp: dict | None, raw: dict | None) -> dict[str, tuple]:
    out = {}
    if comp:
        for i in comp["组分"]:
            cid = i["组分"]
            if cid in out and out[cid][1] is not None and i["数值"] is not None and out[cid][0] == i["单位类别"]:
                out[cid] = (i["单位类别"], out[cid][1] + i["数值"])
            else:
                out.setdefault(cid, (i["单位类别"], i["数值"]))
        if "LiNO3" in out and out["LiNO3"][0] == "质量分数" and out["LiNO3"][1] is not None:
            out["LiNO3"] = ("摩尔浓度", round(out["LiNO3"][1] * SOLN_DENSITY * 1000 / LINO3_MW, 3), "wt%近似换算")
        if "LiNO3" in out and out["LiNO3"][1] == 0:
            del out["LiNO3"]  # 用量为 0 等于不含
        vf = comp.get("体积分数") or {}
        for cid, v in vf.items():  # 溶剂按体积分数比较
            if cid in out:
                out[cid] = ("体积分数", round(v, 3))
    elif raw:
        for c in raw["components"]:
            out[c["name"]] = (c.get("unit", ""), None)
    return out


def signature(a: dict, b: dict) -> tuple[str, ...]:
    sig = []
    for k in sorted(set(a) | set(b)):
        if k in a and k not in b:
            sig.append(f"+{k}")
        elif k in b and k not in a:
            sig.append(f"−{k}")
        else:
            (ua, va), (ub, vb) = a[k][:2], b[k][:2]
            if ua == ub and va is not None and vb is not None and abs(va - vb) > 1e-9 * max(abs(va), abs(vb), 1):
                sig.append(f"{k}↑" if va > vb else f"{k}↓")
    return tuple(sig)


def invert(sig):
    inv = {"+": "−", "−": "+"}
    out = []
    for s in sig:
        if s[0] in inv:
            out.append(inv[s[0]] + s[1:])
        else:
            out.append(s[:-1] + ("↓" if s.endswith("↑") else "↑"))
    return tuple(sorted(out))


BASE_SOLVENTS = {"DME", "DOL"}


def drivers(sig):
    """主改动：加共溶剂/改用量时 DME、DOL 体积分数的被动变化不算改动；全是被动变化时保留原签名。"""
    core = tuple(x for x in sig if not (x[-1] in "↑↓" and x[:-1] in BASE_SOLVENTS))
    return core or tuple(sig)


def canonical(sig):
    """改动签名取“加入/增加”多的一侧为正向；返回 (签名, 是否翻转)。"""
    score = lambda s: sum(x.startswith("+") or x.endswith("↑") for x in s)
    inv = invert(sig)
    if score(inv) > score(sig) or (score(inv) == score(sig) and inv < tuple(sorted(sig))):
        return inv, True
    return tuple(sorted(sig)), False


FLIPD = {"变好": "变坏", "变坏": "变好", "差异小": "差异小"}


def comp_match(a: dict, b: dict) -> tuple[bool, str]:
    if not a or set(a) != set(b):
        return False, ""
    notes = []
    for k in a:
        (ua, va), (ub, vb) = a[k][:2], b[k][:2]
        if k == "LiNO3" and (len(a[k]) > 2 or len(b[k]) > 2):
            notes.append("LiNO₃ 由 wt% 近似换算")
        if va is None or vb is None:
            if k != "LiNO3":
                return False, ""
            notes.append("LiNO₃ 用量缺")
            continue
        if ua != ub:
            return False, ""
        if ua == "体积分数":
            if abs(va - vb) > 0.1:
                return False, ""
        elif k == "LiNO3":
            if not (0.5 <= va / vb <= 2):
                return False, ""
            if va != vb:
                notes.append(f"LiNO₃ {va:g} vs {vb:g} M")
        elif max(va, vb) / max(min(va, vb), 1e-9) > 1.5:
            return False, ""
        elif va != vb:
            notes.append(f"{k} {va:g} vs {vb:g}")
    return True, "；".join(notes)


def main() -> None:
    papers, sources = load_papers(), load_sources()
    sts = read_json("表述.json")
    stmap = {s["表述编号"]: s for s in sts}
    cls = read_json("结果归类.json")
    comp = {(r["论文"], r["配方"]): r for r in read_json("配方组成.json", COMP)}
    conds = {(r["论文"], r["测试"]): r for r in read_json("条件表.json")}
    norm = read_json("归一化结果.json")
    nst = read_json("归一化_表述.json")
    rec_of = {(p, f["id"]): f["recipe_id"] for p, d in papers.items() for f in d["formulations"]}
    raw_rec = {(p, r["id"]): r for p, d in papers.items() for r in d["recipes"]}
    res_index = {(p, t["id"], r["id"]): (t, r) for p, d in papers.items() for t in d["tests"] for r in t["results"]}
    er_of = {(s["论文"], s["配方"]): s["元素比例"] for s in sts if s["元素比例"]}

    def items(pid, fid):
        rid = rec_of.get((pid, fid))
        return recipe_items(comp.get((pid, rid)), raw_rec.get((pid, rid)))

    def counted(pid, fid):
        rid = rec_of.get((pid, fid))
        return set(((comp.get((pid, rid)) or {}).get("元素比例") or {}).get("计入", {}))

    # ---------- 篇内配对（A 相对 B 的方向，不翻转） ----------
    pairs = []
    for c in cls:
        if c["性能类别"] == "不进四类" or c["状态"] == "⚠️" or not c["A"] or not c["B"] or c["A"] == c["B"]:
            continue
        if not in_analysis(c["性能类别"], c.get("阶段")):  # 分析集：倍率容量不纳入，放电容量只看首圈
            continue
        pid = c["论文"]
        t, r = res_index[(pid, c["测试"], c["结果"])]
        a, b = c["A值"], c["B值"]
        e, basis, d = None, None, None
        if a["类型"] in ("精确", "约数", "范围") and b["类型"] in ("精确", "约数", "范围"):
            e, basis = effect(c["标准指标"], a["值"], b["值"], c["越大越好"]), "数值"
        if e is not None:
            d = "变好" if e > SMALL else "变坏" if e < -SMALL else "差异小"
        else:
            for src in (r, r.get("author_qualitative") or {}):
                if src.get("direction_text") in ("变好", "变坏", "差异小"):
                    d, basis = src["direction_text"], "定性"
                    break
        if not d:
            continue
        sig = signature(items(pid, c["A"]), items(pid, c["B"]))
        cat = c["性能类别"]
        if cat == "库仑效率类":  # 方案：Li‖Cu CE 与全电池 CE 分开
            cat += "·Li‖Cu" if c["电池类型"] == "Li‖Cu" else "·全电池"
        pairs.append({"论文": pid, "测试": c["测试"], "结果": c["结果"], "A": c["A"], "B": c["B"], "完整签名": list(sig),
                      "性能类别": cat, "标准指标": c["标准指标"], "取值点": c["取值点"], "阶段": c.get("阶段"), "圈数": c.get("圈数"),
                      "倍率_C": c.get("倍率_C"), "温度_C": c.get("温度_C"),
                      "A值": r.get("value_A"), "B值": r.get("value_B"), "效应": e, "方向": d, "依据": basis, "证据": r.get("evidence_ids", [])})

    def pline(p, flip=False):
        if flip:
            a, b, va, vb, d = p["B"], p["A"], p["B值"], p["A值"], FLIPD[p["方向"]]
        else:
            a, b, va, vb, d = p["A"], p["B"], p["A值"], p["B值"], p["方向"]
        return f"{p['测试']} {p['结果']}：{a}（{va}） vs {b}（{vb}）｜{p['标准指标']}｜{p['取值点']}｜{a} 相对 {b} {d}（{p['依据']}）"

    strongest = lambda lst: sorted(lst, key=lambda x: (x[0]["依据"] != "数值", -abs(x[0]["效应"] or 0)))[0]
    cands = []

    # ---------- FLIP 条件依赖翻转 ----------
    grp = defaultdict(list)
    for p in pairs:
        if p["方向"] == "差异小":
            continue
        a, b = sorted([p["A"], p["B"]])
        grp[(p["论文"], a, b, p["性能类别"])].append((p, p["A"] != a))
    for (pid, a, b, cat), lst in grp.items():
        good = [x for x in lst if (x[0]["方向"] == "变好") != x[1]]  # a 相对 b 变好
        bad = [x for x in lst if (x[0]["方向"] == "变好") == x[1]]
        if not good or not bad:
            continue
        pg, pb = strongest(good), strongest(bad)
        diff = []
        if pg[0]["测试"] != pb[0]["测试"]:
            c1 = conds.get((pid, pg[0]["测试"]), {}).get("条件", {})
            c2 = conds.get((pid, pb[0]["测试"]), {}).get("条件", {})
            for f, lab in (("ES", "E/S"), ("sulfur_loading", "载量"), ("S_content", "含硫"), ("rate", "倍率"), ("temperature", "温度"),
                           ("cell_format", "电池形式"), ("Li_thickness", "锂厚")):
                v1, v2 = c1.get(f, {}).get("值"), c2.get(f, {}).get("值")
                if v1 != v2:
                    diff.append(f"{lab} {v1 if v1 is not None else '—'} → {v2 if v2 is not None else '—'}")
        for k, lab in (("倍率_C", "取值点倍率"), ("温度_C", "取值点温度"), ("圈数", "圈数")):
            if pg[0].get(k) != pb[0].get(k):
                diff.append(f"{lab} {pg[0].get(k)} → {pb[0].get(k)}")
        same_test = pg[0]["测试"] == pb[0]["测试"]
        sub = "阶段翻转（同一测试、不同圈数）" if same_test and not any(x.startswith("取值点") for x in diff) else "条件翻转"
        cands.append({"类型": "FLIP", "子类": sub, "性能类别": cat, "论文甲": pid, "论文乙": pid,
                      "摘要": f"{pid}：{a} 相对 {b} 在一种条件下变好、另一种条件下变坏（{'；'.join(diff) or '条件差异未记录'}）",
                      "甲例": pline(*pg), "乙例": pline(*pb), "证据甲": pg[0]["证据"], "证据乙": pb[0]["证据"],
                      "强度": min(abs(pg[0]["效应"] or 0), abs(pb[0]["效应"] or 0))})

    # ---------- SAME 严格同一改动 / DESC 设计方向相反 ----------
    def paper_dirs(key_of):
        g = defaultdict(lambda: defaultdict(list))
        for p in pairs:
            if p["方向"] == "差异小":
                continue
            k = key_of(p)
            if k is not None:
                g[k[0]][p["论文"]].append((p, k[1]))
        return g

    def oppose(g, typ, label):
        for kk, per in g.items():
            maj = {}
            for pid, lst in per.items():
                n_good = sum((p["方向"] == "变好") != fl for p, fl in lst)
                if n_good * 2 != len(lst):
                    maj[pid] = "变好" if n_good * 2 > len(lst) else "变坏"
            goods = [q for q, v in maj.items() if v == "变好"]
            bads = [q for q, v in maj.items() if v == "变坏"]
            for pg, pb in itertools.product(goods, bads):
                eg = strongest([x for x in per[pg] if (x[0]["方向"] == "变好") != x[1]])
                eb = strongest([x for x in per[pb] if (x[0]["方向"] == "变好") == x[1]])
                cands.append({"类型": typ, "子类": label(kk), "性能类别": kk[-1], "论文甲": pg, "论文乙": pb,
                              "摘要": f"{label(kk)}：{pg} 变好，{pb} 变坏",
                              "甲例": pline(*eg) + f"｜改动 {' '.join(eg[0]['完整签名'])}",
                              "乙例": pline(*eb) + f"｜改动 {' '.join(eb[0]['完整签名'])}",
                              "证据甲": eg[0]["证据"], "证据乙": eb[0]["证据"],
                              "强度": min(abs(eg[0]["效应"] or 0), abs(eb[0]["效应"] or 0))})

    def same_key(p):
        if not p["完整签名"]:
            return None
        cs, fl = canonical(drivers(tuple(p["完整签名"])))
        return (cs, p["性能类别"]), fl
    oppose(paper_dirs(same_key), "SAME", lambda kk: "主改动 " + " ".join(kk[0]) + f"｜{kk[1]}")

    def desc_key_factory(desc, thr):
        def key(p):
            ra, rb = er_of.get((p["论文"], p["A"])), er_of.get((p["论文"], p["B"]))
            if not ra or not rb or not p["完整签名"]:
                return None
            allowed = counted(p["论文"], p["A"]) | counted(p["论文"], p["B"])
            if any(x.strip("+−↑↓") not in allowed for x in p["完整签名"]):  # LiNO₃、添加剂等也变了 → 元素比例代表不了主改动
                return None
            dv = ra[desc] - rb[desc]
            if abs(dv) < thr:
                return None
            return (f"{desc} 降低", p["性能类别"]), dv > 0  # 统一成“降低”方向：dv>0 时把 A、B 对调
        return key
    for desc, thr in (("sO", 0.005), ("F/O", 0.1)):
        oppose(paper_dirs(desc_key_factory(desc, thr)), "DESC", lambda kk: f"{kk[0]}（只改溶剂/主盐）｜{kk[1]}")

    # ---------- NORM 归一化后同配方跨篇差距大 ----------
    byf = defaultdict(list)
    for x in nst:
        if not x.get("普遍条件_外推"):
            byf[(x["类别"], x["论文"], x["配方"])].append(x)
    for cname in sorted({k[0] for k in byf}):
        keys = [k for k in byf if k[0] == cname]
        lim = math.log(2) if norm[cname]["y"] == "loss" else math.log(1.5)
        for k1, k2 in itertools.combinations(keys, 2):
            if k1[1] == k2[1]:
                continue
            ok, note = comp_match(items(k1[1], k1[2]), items(k2[1], k2[2]))
            if not ok:
                continue
            m1 = sorted(x["普遍条件_y"] for x in byf[k1])[len(byf[k1]) // 2]
            m2 = sorted(x["普遍条件_y"] for x in byf[k2])[len(byf[k2]) // 2]
            if abs(m1 - m2) < lim:
                continue
            hi, lo = (k1, k2) if m1 > m2 else (k2, k1)
            sh = lambda k: "；".join(f"{x['表述编号']} 实测 {x['实测值']} → 归一化 {x['普遍条件_归一化值']}"
                                    + (f"（未换算：{x['未换算条件']}）" if x["未换算条件"] else "") for x in byf[k])
            cands.append({"类型": "NORM", "子类": "同配方跨篇", "性能类别": cname, "论文甲": hi[1], "论文乙": lo[1],
                          "摘要": f"同一配方 {hi[1]}:{hi[2]} 与 {lo[1]}:{lo[2]} 归一化后相差 {math.exp(abs(m1 - m2)):.2f} 倍" + (f"（{note}）" if note else ""),
                          "甲例": f"{hi[1]}:{hi[2]}｜" + sh(hi), "乙例": f"{lo[1]}:{lo[2]}｜" + sh(lo),
                          "证据甲": [e for x in byf[hi][:2] for e in stmap[x["表述编号"]]["证据句子"][:2]],
                          "证据乙": [e for x in byf[lo][:2] for e in stmap[x["表述编号"]]["证据句子"][:2]],
                          "强度": abs(m1 - m2)})

    # ---------- LOPO 篇内结论与跨文献模型相反 ----------
    lopo_skip = []
    for cname, r in norm.items():
        pr = next(m for m in r["模型比较"] if m["模型"] == r["主模型"])
        if not (pr["V1篇内R2"] is not None and pr["V1篇内R2"] > 0):
            lopo_skip.append(f"{cname}（主模型 {r['主模型']} 的 V1 篇内 R² = {pr['V1篇内R2']}）")
            continue
        grp2 = defaultdict(list)
        for x in (x for x in nst if x["类别"] == cname):
            s = stmap[x["表述编号"]]
            grp2[(x["论文"], x["测试"], s["阶段"], s["圈数"], s["条件"]["rate"]["值"], s["条件"]["temperature"]["值"])].append(x)
        best = {}
        for lst in grp2.values():
            ref = next((x for x in lst if x["是否对照"]), None)
            if ref is None or len(lst) < 2:
                continue
            for x in lst:
                if x is ref:
                    continue
                obs = x["实测_y"] - ref["实测_y"]
                pred = x["V1留出预测_主模型"] - ref["V1留出预测_主模型"]
                if obs * pred < 0 and abs(obs) >= math.log(1.1) and abs(pred) >= math.log(1.1):
                    k = (x["论文"], x["配方"], ref["配方"])
                    if k in best and min(abs(obs), abs(pred)) <= best[k]["强度"]:
                        continue
                    s, sr = stmap[x["表述编号"]], stmap[ref["表述编号"]]
                    best[k] = {"类型": "LOPO", "子类": f"主模型 {r['主模型']}", "性能类别": cname, "论文甲": x["论文"], "论文乙": "（其他论文合起来）",
                               "摘要": f"{x['论文']}：{x['配方']} 相对对照 {ref['配方']} 实测{'变好' if obs > 0 else '变坏'}（ln {obs:+.2f}），"
                                       f"不含此篇训练的模型预测{'变好' if pred > 0 else '变坏'}（ln {pred:+.2f}）",
                               "甲例": f"{x['表述编号']} {x['配方']}：{s['数值原文']}（{s['取值点']}） vs {ref['表述编号']} {ref['配方']}：{sr['数值原文']}",
                               "乙例": f"模型预测差距 ln {pred:+.2f}｜配方：{s['配方文字'][:70]}｜对照：{sr['配方文字'][:70]}",
                               "证据甲": s["证据句子"][:2] + sr["证据句子"][:1], "证据乙": [], "强度": min(abs(obs), abs(pred))}
        cands += list(best.values())

    # ---------- 编号、并入人工核对 ----------
    order = ["NORM", "LOPO", "FLIP", "DESC", "SAME"]
    cands.sort(key=lambda c: (order.index(c["类型"]), -c["强度"]))
    cnt = Counter()
    mf = OUT / "矛盾核对.json"
    manual = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}
    for c in cands:
        cnt[c["类型"]] += 1
        c["候选编号"] = f"{c['类型']}{cnt[c['类型']]:03d}"
        m = manual.get(c["候选编号"], {})
        c["判定"], c["核对说明"], c["依据句子"] = m.get("判定", ""), m.get("说明", ""), m.get("依据句子", [])
        c["可能原因"], c["机制线索"] = m.get("可能原因", ""), m.get("机制线索", "")
        c["原句甲"] = sentences(sources[c["论文甲"]], c["证据甲"][:3], 350) if c["论文甲"] in sources else ""
        c["原句乙"] = sentences(sources[c["论文乙"]], c["证据乙"][:3], 350) if c["论文乙"] in sources else ""
    write_json("矛盾候选.json", cands)
    write_json("篇内配对_方向.json", pairs)
    summary = {"篇内有方向的配对": len(pairs), "配对依据": dict(Counter(p["依据"] for p in pairs)),
               "候选数": {t: cnt[t] for t in order}, "未做 LOPO 的类别": lopo_skip,
               "判定统计": {t: dict(Counter(c["判定"] or "未核对" for c in cands if c["类型"] == t)) for t in order if cnt[t]}}
    write_json("step13e_汇总.json", summary)
    names = {"NORM": "归一化后同配方跨篇差距大", "LOPO": "篇内结论与跨文献模型相反", "FLIP": "条件依赖翻转", "DESC": "设计方向相反", "SAME": "严格同一改动"}
    cols = ["候选编号", "判定", "子类", "性能类别", "摘要", "论文甲", "甲例", "原句甲", "论文乙", "乙例", "原句乙", "核对说明", "依据句子", "可能原因", "机制线索"]
    write_xlsx(OUT / "矛盾候选复核表.xlsx", [(names[t], cols, [[c[k] for k in cols] for c in cands if c["类型"] == t]) for t in order],
               widths={"摘要": 50, "甲例": 50, "乙例": 50, "原句甲": 60, "原句乙": 60, "核对说明": 55, "可能原因": 40, "机制线索": 40},
               notes=[f"step13e 矛盾候选复核表（归一化后重做）｜{LABEL}｜2026-11-04 生成",
                      "五种候选：NORM 归一化后同配方跨篇差距大；LOPO 篇内结论与不含该篇训练的模型预测相反；FLIP 同篇同一对配方换条件后方向相反；"
                      "DESC 跨篇只改溶剂/主盐、元素比例同向变化但结论相反；SAME 主改动完全相同但结论相反。",
                      "判定（Claude 逐条回原文核对）：✅ 原文支持、确实值得解释的矛盾；🔶 原文数值无误，但有未对齐的条件或定义差异可能解释差别；⚠️ 提取或归类有问题；❌ 不构成矛盾。",
                      "LOPO 依赖模型：主模型 V1 很弱时预测方向本身不可靠，只作线索；V1 篇内 R² ≤ 0 的类别不做。",
                      "“可能原因”“机制线索”是 Claude 读原文后的初步看法；AI 辅助复核，用户尚未逐项人工确认。"])
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
