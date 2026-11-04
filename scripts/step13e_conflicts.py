"""step13e：找矛盾候选并生成复核表（方案 §8.7，11-04 用户定两种候选）。

① 方向相反：两篇论文做了同一种改动（配方差异签名相同，如都是“+TTE”），同一类性能一篇变好、一篇变坏。
   篇内配对来自提取的 A/B 比较；方向用数值算（容量等取对数比，CE 用损失比 ln[(100−CE_A)/(100−CE_B)]，|效应|<ln1.05 记差异小），
   两侧没有数值时用作者定性方向（标“定性”）。
② 数值相差大：不同论文、配方相同（组分集合相同、用量相近、LiNO₃ 同有同无且浓度 0.5–2 倍内）、
   条件相近（已知的 E/S、载量比 ≤1.5 倍，含硫差 ≤10 个百分点，倍率比 ≤2 倍，温度差 ≤10 °C，电池形式相同；E/S 与载量至少一项两侧都已知）、
   同一标准指标同一阶段（第 N 圈的圈数比 ≤1.5 倍），性能相差 ≥1.5 倍（CE 损失比 ≥2 倍）。
人工判断层：矛盾核对.json（Claude 逐条回原文核对后写入；键 = 候选编号），本脚本把它并进复核表。
输出：矛盾候选.json、矛盾候选复核表.xlsx、step13e_汇总.json
"""
from __future__ import annotations

import itertools
import json
import math
from collections import Counter, defaultdict

from step13_common import COMP, LABEL, OUT, load_papers, load_sources, read_json, sentences, write_json, write_xlsx

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


def main() -> None:
    papers, sources = load_papers(), load_sources()
    sts = read_json("表述.json")
    cls = read_json("结果归类.json")
    comp = {(r["论文"], r["配方"]): r for r in read_json("配方组成.json", COMP)}
    rec_of = {(p, f["id"]): f["recipe_id"] for p, d in papers.items() for f in d["formulations"]}
    raw_rec = {(p, r["id"]): r for p, d in papers.items() for r in d["recipes"]}
    st_index = defaultdict(list)
    for s in sts:
        st_index[(s["论文"], s["测试"], s["配方"], s["标准指标"])].append(s)
    res_index = {(p, t["id"], r["id"]): (t, r) for p, d in papers.items() for t in d["tests"] for r in t["results"]}

    def items(pid, fid):
        rid = rec_of.get((pid, fid))
        return recipe_items(comp.get((pid, rid)), raw_rec.get((pid, rid)))

    # ---------- ① 方向相反 ----------
    pairs = []
    for c in cls:
        if c["性能类别"] == "不进四类" or c["状态"] == "⚠️" or not c["A"] or not c["B"] or c["A"] == c["B"]:
            continue
        pid = c["论文"]
        t, r = res_index[(pid, c["测试"], c["结果"])]
        sig = signature(items(pid, c["A"]), items(pid, c["B"]))
        if not sig:
            continue
        a, b = c["A值"], c["B值"]
        e, basis = None, None
        if a["类型"] in ("精确", "约数", "范围") and b["类型"] in ("精确", "约数", "范围"):
            e, basis = effect(c["标准指标"], a["值"], b["值"], c["越大越好"]), "数值"
        if e is not None:
            d = "变好" if e > SMALL else "变坏" if e < -SMALL else "差异小"
        else:
            d = r.get("direction_text") if r.get("direction_text") in ("变好", "变坏", "差异小") else None
            if d is None and r.get("author_qualitative"):
                d = r["author_qualitative"].get("direction_text") if r["author_qualitative"].get("direction_text") in ("变好", "变坏", "差异小") else None
            basis = "定性" if d else None
        if not d:
            continue
        csig, flip = canonical(drivers(sig))
        if flip:
            d = {"变好": "变坏", "变坏": "变好", "差异小": "差异小"}[d]
            e = -e if e is not None else None
        pairs.append({"论文": pid, "测试": c["测试"], "结果": c["结果"], "A": c["A"], "B": c["B"], "翻转": flip,
                      "签名": csig, "完整签名": sig, "性能类别": c["性能类别"], "标准指标": c["标准指标"], "取值点": c["取值点"],
                      "A值": r.get("value_A"), "B值": r.get("value_B"), "效应": e, "方向": d, "依据": basis,
                      "证据": r.get("evidence_ids", []), "改动数": len(csig)})
    by_sig = defaultdict(list)
    for p in pairs:
        by_sig[(p["签名"], p["性能类别"])].append(p)
    dir_cands = []
    for (sig, cat), lst in by_sig.items():
        per_paper = defaultdict(Counter)
        for p in lst:
            per_paper[p["论文"]][p["方向"]] += 1
        good = [k for k, v in per_paper.items() if v["变好"] > v["变坏"]]
        bad = [k for k, v in per_paper.items() if v["变坏"] > v["变好"]]
        for pg, pb in itertools.product(good, bad):
            ex_g = sorted([p for p in lst if p["论文"] == pg and p["方向"] == "变好"], key=lambda x: (x["依据"] != "数值", -abs(x["效应"] or 0)))
            ex_b = sorted([p for p in lst if p["论文"] == pb and p["方向"] == "变坏"], key=lambda x: (x["依据"] != "数值", -abs(x["效应"] or 0)))
            dir_cands.append({"类型": "方向相反", "签名": " ".join(sig), "改动数": len(sig), "性能类别": cat,
                              "论文甲": pg, "甲方向统计": dict(per_paper[pg]), "论文乙": pb, "乙方向统计": dict(per_paper[pb]),
                              "甲例": ex_g[:3], "乙例": ex_b[:3]})
    for c in dir_cands:
        c["匹配"] = "主改动相同"
    paper_dir = defaultdict(Counter)
    paper_ex = defaultdict(list)
    for p in pairs:
        if len(p["签名"]) <= 2:
            paper_dir[(p["论文"], p["签名"], p["性能类别"])][p["方向"]] += 1
            paper_ex[(p["论文"], p["签名"], p["性能类别"])].append(p)
    keys = list(paper_dir)
    done = {(c["论文甲"], c["论文乙"], c["签名"], c["性能类别"]) for c in dir_cands}
    for k1, k2 in itertools.combinations(keys, 2):
        (p1, s1, c1), (p2, s2, c2) = k1, k2
        if p1 == p2 or c1 != c2 or s1 == s2 or not (set(s1) & set(s2)):
            continue
        d1, d2 = paper_dir[k1], paper_dir[k2]
        g1, g2 = d1["变好"] > d1["变坏"], d2["变好"] > d2["变坏"]
        b1, b2 = d1["变坏"] > d1["变好"], d2["变坏"] > d2["变好"]
        if not ((g1 and b2) or (b1 and g2)):
            continue
        (kg, dg), (kb, db) = ((k1, d1), (k2, d2)) if g1 else ((k2, d2), (k1, d1))
        if (kg[0], kb[0], " ".join(sorted(set(s1) & set(s2))), c1) in done:
            continue
        pick = lambda k, d: sorted([p for p in paper_ex[k] if p["方向"] == d], key=lambda x: (x["依据"] != "数值", -abs(x["效应"] or 0)))[:3]
        dir_cands.append({"类型": "方向相反", "匹配": "主改动部分相同", "签名": f"{' '.join(kg[1])}  vs  {' '.join(kb[1])}（共同：{' '.join(sorted(set(s1) & set(s2)))}）",
                          "改动数": max(len(s1), len(s2)), "性能类别": c1, "论文甲": kg[0], "甲方向统计": dict(dg),
                          "论文乙": kb[0], "乙方向统计": dict(db), "甲例": pick(kg, "变好"), "乙例": pick(kb, "变坏")})
    dir_cands.sort(key=lambda x: (x["匹配"] != "主改动相同", x["改动数"], x["签名"], x["性能类别"]))

    # ---------- ② 数值相差大 ----------
    def comp_match(s1, s2):
        a, b = items(s1["论文"], s1["配方"]), items(s2["论文"], s2["配方"])
        if not a or set(a) != set(b):
            return False, ""
        notes = []
        for k in a:
            (ua, va), (ub, vb) = a[k][:2], b[k][:2]
            if k == "LiNO3" and (len(a[k]) > 2 or len(b[k]) > 2):
                notes.append("LiNO₃ 由 wt% 近似换算为 M（密度按 1.2 g/mL）")
            if va is None or vb is None:
                if k != "LiNO3":
                    return False, ""
                notes.append(f"{k} 用量缺")
                continue
            if ua != ub:
                return False, ""
            if ua == "体积分数":
                if abs(va - vb) > 0.1:
                    return False, ""
            elif k == "LiNO3":
                if not (0.5 <= (va / vb if vb else 99) <= 2):
                    return False, ""
                if va != vb:
                    notes.append(f"LiNO₃ {va:g} vs {vb:g} {ua}")
            elif max(va, vb) / max(min(va, vb), 1e-9) > 1.5:
                return False, ""
            elif va != vb:
                notes.append(f"{k} {va:g} vs {vb:g} {ua}")
        return True, "；".join(notes)

    def cond_match(s1, s2):
        c1, c2 = s1["条件"], s2["条件"]
        v = lambda c, f: c[f]["值"]
        notes, known = [], 0
        for f, lim, kind in (("ES", 1.5, "比"), ("sulfur_loading", 1.5, "比"), ("rate", 2.0, "比"),
                             ("S_content", 10, "差"), ("temperature", 10, "差")):
            a, b = v(c1, f), v(c2, f)
            if a is None or b is None:
                if f in ("ES", "sulfur_loading"):
                    notes.append(f"{f} 有一侧未知")
                continue
            if f in ("ES", "sulfur_loading"):
                known += 1
            if kind == "比":
                if a <= 0 or b <= 0 or max(a, b) / min(a, b) > lim:
                    return False, ""
            elif abs(a - b) > lim:
                return False, ""
        if v(c1, "cell_format") and v(c2, "cell_format") and v(c1, "cell_format") != v(c2, "cell_format"):
            return False, ""
        if s1["正极类型"] != s2["正极类型"] or s1["电池类型"] != s2["电池类型"]:
            return False, ""
        if known == 0:
            return False, ""
        return True, "；".join(notes)

    usable = [s for s in sts if s["数值类型"] in ("精确", "约数") and s["数值"] is not None]
    seen_dup, uniq = set(), []
    for s in usable:
        g = s.get("疑似重复组")
        if g and g in seen_dup:
            continue
        seen_dup.add(g)
        uniq.append(s)
    by_metric = defaultdict(list)
    for s in uniq:
        by_metric[(s["标准指标"], s["阶段"])].append(s)
    num_cands, matched = [], []
    for (std, stage), lst in by_metric.items():
        for s1, s2 in itertools.combinations(lst, 2):
            if s1["论文"] == s2["论文"]:
                continue
            if stage == "第 N 圈" and (not s1["圈数"] or not s2["圈数"] or max(s1["圈数"], s2["圈数"]) / min(s1["圈数"], s2["圈数"]) > 1.5):
                continue
            if stage in ("未写圈数", "活化后（未写圈数）"):
                continue
            ok1, n1 = comp_match(s1, s2)
            if not ok1:
                continue
            ok2, n2 = cond_match(s1, s2)
            if not ok2:
                continue
            e = effect(std, s1["数值"], s2["数值"], s1["越大越好"])
            if e is None:
                continue
            lim = math.log(2) if ("CE" in std and "圈数" not in std) else math.log(1.5)
            matched.append({"标准指标": std, "阶段": stage, "倍数": round(math.exp(abs(e)), 3),
                            "甲": f"{s1['表述编号']} {s1['论文']} {s1['配方']} {s1['数值原文']}", "乙": f"{s2['表述编号']} {s2['论文']} {s2['配方']} {s2['数值原文']}",
                            "配方差异": n1, "条件说明": n2})
            if abs(e) < lim:
                continue
            hi, lo = (s1, s2) if e > 0 else (s2, s1)
            num_cands.append({"类型": "数值相差大", "标准指标": std, "阶段": stage, "效应": abs(e),
                              "倍数": round(math.exp(abs(e)), 2), "好的一侧": hi["表述编号"], "差的一侧": lo["表述编号"],
                              "论文甲": hi["论文"], "论文乙": lo["论文"], "配方差异": n1, "条件说明": n2})
    num_cands.sort(key=lambda x: -x["效应"])

    # ---------- 编号、并入人工核对 ----------
    cands = []
    for i, c in enumerate(dir_cands, 1):
        c["候选编号"] = f"DIR{i:03d}"
        cands.append(c)
    for i, c in enumerate(num_cands, 1):
        c["候选编号"] = f"NUM{i:03d}"
        cands.append(c)
    mf = OUT / "矛盾核对.json"
    manual = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}
    stmap = {s["表述编号"]: s for s in sts}
    for c in cands:
        m = manual.get(c["候选编号"], {})
        c["判定"] = m.get("判定", "")
        c["核对说明"] = m.get("说明", "")
        c["依据句子"] = m.get("依据句子", [])
        c["可能原因"] = m.get("可能原因", "")
        c["机制线索"] = m.get("机制线索", "")
    write_json("矛盾候选.json", cands)
    write_json("篇内配对_方向.json", pairs)

    # ---------- 复核表 ----------
    def ex_text(ex):
        return "\n".join(f"{p['测试']} {p['结果']}：{p['A']}（{p['A值']}） vs {p['B']}（{p['B值']}）"
                         f"{'［已翻转为签名方向］' if p['翻转'] else ''}｜{p['标准指标']}｜{p['取值点']}｜{p['方向']}（{p['依据']}）" for p in ex)

    def ex_src(pid, ex):
        ids = []
        for p in ex[:2]:
            ids += [e for e in p["证据"] if e not in ids]
        return sentences(sources[pid], ids[:4], 350)

    dir_rows = [[c["候选编号"], c["判定"], c["签名"], c["性能类别"], c["论文甲"], c["甲方向统计"], ex_text(c["甲例"]), ex_src(c["论文甲"], c["甲例"]),
                 c["论文乙"], c["乙方向统计"], ex_text(c["乙例"]), ex_src(c["论文乙"], c["乙例"]), c["核对说明"], c["依据句子"], c["可能原因"],
                 c["机制线索"]] for c in cands if c["类型"] == "方向相反"]

    def st_line(s):
        cnd = s["条件"]
        f = lambda k: cnd[k]["值"] if cnd[k]["值"] is not None else "—"
        return (f"{s['表述编号']} {s['论文']} {s['测试']} {s['配方']}：{s['数值原文']} {s['单位']}（{s['取值点']}）\n"
                f"E/S {f('ES')}｜载量 {f('sulfur_loading')}｜含硫 {f('S_content')}｜倍率 {f('rate')}｜温度 {f('temperature')}｜{f('cell_format')}\n配方：{s['配方文字']}")

    num_rows = []
    for c in cands:
        if c["类型"] != "数值相差大":
            continue
        a, b = stmap[c["好的一侧"]], stmap[c["差的一侧"]]
        num_rows.append([c["候选编号"], c["判定"], c["标准指标"], c["阶段"], c["倍数"], st_line(a), sentences(sources[a["论文"]], a["证据句子"][:3], 350),
                         st_line(b), sentences(sources[b["论文"]], b["证据句子"][:3], 350), c["配方差异"], c["条件说明"],
                         c["核对说明"], c["依据句子"], c["可能原因"], c["机制线索"]])
    summary = {"篇内有方向的配对": len(pairs), "配对依据": dict(Counter(p["依据"] for p in pairs)),
               "改动签名种数": len({p["签名"] for p in pairs}),
               "方向相反候选": len(dir_rows), "数值相差大候选": len(num_rows),
               "判定统计": dict(Counter(c["判定"] or "未核对" for c in cands)),
               "数值相差大·按标准指标": dict(Counter(c["标准指标"] for c in cands if c["类型"] == "数值相差大")),
               "配方与条件都配上的跨篇对（不论差距）": len(matched),
               "配上的对·按指标（对数，最大倍数）": {f"{k[0]}｜{k[1]}": [n, max(x["倍数"] for x in matched if (x["标准指标"], x["阶段"]) == k)]
                                          for k, n in Counter((x["标准指标"], x["阶段"]) for x in matched).items()},
               "说明": "数值相差大是未归一化的初筛：只比配方相同、已知条件相近的跨篇表述；正式版本在第⑥步归一化到标准条件后，按“归一化后仍差得远”重新找。"}
    write_json("step13e_汇总.json", summary)
    write_xlsx(OUT / "矛盾候选复核表.xlsx", [
        ("方向相反", ["候选编号", "判定", "改动签名", "性能类别", "论文甲（变好）", "甲方向统计", "甲例", "甲原句", "论文乙（变坏）", "乙方向统计", "乙例", "乙原句",
                  "核对说明", "依据句子", "可能原因", "机制线索"], dir_rows),
        ("数值相差大", ["候选编号", "判定", "标准指标", "阶段", "倍数", "好的一侧", "好侧原句", "差的一侧", "差侧原句", "配方差异", "条件说明",
                   "核对说明", "依据句子", "可能原因", "机制线索"], num_rows),
        ("配上的跨篇对（未到阈值）", ["标准指标", "阶段", "倍数", "甲", "乙", "配方差异", "条件说明"],
         [[x[k] for k in ["标准指标", "阶段", "倍数", "甲", "乙", "配方差异", "条件说明"]] for x in sorted(matched, key=lambda x: -x["倍数"])]),
    ], widths={"甲": 40, "乙": 40, "甲例": 45, "乙例": 45, "甲原句": 60, "乙原句": 60, "好的一侧": 50, "差的一侧": 50, "好侧原句": 60, "差侧原句": 60,
               "核对说明": 50, "可能原因": 40, "机制线索": 40},
        notes=[f"step13e 矛盾候选复核表｜{LABEL}｜2026-11-04 生成",
               "注意：“数值相差大”是未归一化的初筛（只比配方相同、已知条件相近的跨篇表述），正式版本要等第⑥步归一化到标准条件之后，按归一化后仍差得远重新找；“方向相反”比的是篇内比值，不需要归一化。",
               "两种候选（方案 §8.7）：① 方向相反 = 两篇做了同一种改动（改动签名相同），同一类性能一篇变好一篇变坏；② 数值相差大 = 不同论文、配方与条件相近，性能相差 ≥1.5 倍（CE 损失比 ≥2 倍）。",
               "改动签名：+X 加入 X，−X 去掉 X，X↑/X↓ 用量增减；比较方向统一成签名方向（必要时把 A、B 对调，表中注“已翻转”）。",
               "判定（Claude 逐条回原文核对）：✅ 原文支持、条件已对齐，是值得解释的矛盾；🔶 原文数值无误，但有未对齐的条件或定义差异可能解释差别；⚠️ 提取或归类有问题；❌ 不构成矛盾。",
               "“可能原因”“机制线索”是 Claude 读原文后的初步看法，机制编号来自表述的后台链接；AI 辅助复核，用户尚未逐项人工确认。"])
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
