"""step13c：生成标准化表述（方案 §8.7，11-04 用户定）。

一个性能数值一条表述 = 配方（组分、用量、描述符）＋物理化学性质（同篇对同一 recipe 报告的值，没报告写“未报告”）
＋测试条件（E/S、硫载量、正极硫含量、锂厚或 N/P、倍率、温度、电池形式、圈数）＋性能数值。
每条附原文句子编号；机制和支撑测量只在后台保留编号链接，不写进表述文字。

输入（只读）：结果归类.json、物性归类.json、条件表.json（step13a/13b）、组分结构表 配方组成.json、规则处理版 candidate/source。
输出：表述.json、表述表.xlsx、step13c_汇总.json
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

from step13_common import COMP, LABEL, OUT, load_papers, load_sources, read_json, sentences, write_json, write_xlsx
from step13b_conditions import es_from_volume

MAIN_PROPS = ["离子电导率", "黏度", "Li⁺迁移数", "密度", "多硫化物溶解度", "多硫化物溶剂化（含结合能）",
              "Li⁺溶剂化结构", "Li₂S 溶解", "Li⁺脱溶剂化能", "扩散系数"]
SKIP_PROPS = {"作者解释（不进表述）", "非电解液本体性质（不进表述）"}
COND_FIELDS = [("ES", "E/S", "μL mg⁻¹"), ("sulfur_loading", "硫载量", "mg cm⁻²"), ("S_content", "正极含硫", "%"),
               ("Li_thickness", "锂厚", "μm"), ("NP", "N/P", ""), ("rate", "倍率", "C"), ("temperature", "温度", "°C"),
               ("cell_format", "电池形式", "")]


def short_unit(u: str) -> str:
    if (u or "").startswith("M（原文 m"):
        return u
    return re.split(r"[（(，,；;]", u or "")[0].strip()


def recipe_text(comp: dict | None, raw_recipe: dict | None) -> str:
    """配方文字：原文用量＋原文单位；体积份/摩尔比的溶剂合写成 A:B=x:y。"""
    if comp:
        items = comp["组分"]
        get = lambda i: (i["组分"], i["原文用量"],
                         ("M（原文 m，已核实）" if i.get("采用单位") == "mol/L" and str(i["原文单位"]).startswith("m") else i["原文单位"]),
                         i["单位类别"])
    elif raw_recipe:
        items = raw_recipe["components"]
        get = lambda i: (i["name"], i.get("amount", ""), i.get("unit", ""), "")
    else:
        return "（配方未记录）"
    parts, ratio = [], defaultdict(list)
    for i in items:
        name, amt, unit, cat = get(i)
        u = short_unit(unit)
        if cat == "体积份" and not re.search(r"vol", unit):
            ratio["体积"].append((name, amt))
        elif cat == "摩尔比":
            ratio["摩尔"].append((name, amt))
        elif cat == "不可用" or not amt or amt in ("未报告",):
            parts.append(f"{name}（用量未报告）" if not amt or amt == "未报告" else f"{name} {amt}{(' ' + u) if u else ''}")
        else:
            parts.append(f"{amt} {u} {name}".replace("  ", " ").strip())
    for k, lst in ratio.items():
        if len(lst) == 1:
            parts.append(f"{lst[0][0]}（{lst[0][1]} {k}份）")
        else:
            parts.append(f"{':'.join(n for n, _ in lst)} = {':'.join(str(a) for _, a in lst)}（{k}比）")
    return "；".join(parts)


def blocks(comp: dict | None, ctab: dict) -> dict:
    """分块字段：主盐、溶剂、LiNO₃、添加剂/介体。"""
    out = {"主盐": [], "溶剂": [], "LiNO3": None, "添加剂与介体": []}
    if not comp:
        return out
    for i in comp["组分"]:
        cid = i["组分"]
        cat = ctab.get(cid, {}).get("类别", "")
        val = f"{i['原文用量']} {short_unit(i['原文单位'])}".strip()
        if cid == "LiNO3":
            out["LiNO3"] = val
        elif cat == "锂盐":
            out["主盐"].append(f"{cid} {val}")
        elif cat.startswith("溶剂"):
            out["溶剂"].append(cid)
        elif cat:
            out["添加剂与介体"].append(f"{cid} {val}")
    return out


def fmt_num(v, unit=""):
    if v is None:
        return None
    s = f"{v:.3g}" if isinstance(v, float) and abs(v) < 1000 else f"{v:g}"
    return f"{s} {unit}".strip()


def main() -> None:
    papers, sources = load_papers(), load_sources()
    cls = read_json("结果归类.json")
    props = read_json("物性归类.json")
    conds = {(r["论文"], r["测试"]): r for r in read_json("条件表.json")}
    comp = {(r["论文"], r["配方"]): r for r in read_json("配方组成.json", COMP)}
    ctab = {c["id"]: c for c in read_json("组分表.json", COMP)}
    res_index = {(p, t["id"], r["id"]): (t, r) for p, d in papers.items() for t in d["tests"] for r in t["results"]}

    props_by = defaultdict(list)
    for p in props:
        if p["值"] is None or p["标准物性"] in SKIP_PROPS or p["来源类型"] == "文献转述":
            continue
        for f in p["挂接配方"]:
            props_by[(p["论文"], f)].append(p)
        for rid in p["挂接recipe"]:
            props_by[(p["论文"], "recipe:" + rid)].append(p)

    groups: dict[tuple, dict] = {}
    skipped = Counter()
    for c in cls:
        if c["性能类别"] == "不进四类":
            continue
        if c["状态"] == "⚠️":
            skipped["归类⚠️（单位异常等）"] += 1
            continue
        pid, tid = c["论文"], c["测试"]
        test, res = res_index[(pid, tid, c["结果"])]
        for side in ("A", "B"):
            fid, val = c[side], c[side + "值"]
            if not fid:
                continue
            if val["值"] is None:
                if val["类型"] == "非数值":
                    skipped["数值无法解析为单值"] += 1
                continue
            # 同一测试内：按解析后的取值点合并（取值点原文常把 A、B 两侧写在一起，原文不同不代表是不同数值）
            key = (pid, tid, fid, c["标准指标"], c.get("阶段"), c.get("圈数"), c.get("倍率_C"), c.get("电流_A每g"),
                   c.get("温度_C"), c.get("硫载量_mg每cm2"), round(val["值"], 6), val["类型"])
            g = groups.setdefault(key, {"cls": c, "test": test, "fid": fid, "val": val, "raw": res["value_" + side],
                                        "results": [], "evidence": []})
            g["results"].append(c["结果"])
            for e in res.get("evidence_ids", []):
                if e not in g["evidence"]:
                    g["evidence"].append(e)

    statements = []
    for n, (key, g) in enumerate(sorted(groups.items(), key=lambda x: (x[0][0], x[0][1], x[0][2], x[0][3])), 1):
        pid, tid, fid = key[0], key[1], key[2]
        d, c, test = papers[pid], g["cls"], g["test"]
        form = next((f for f in d["formulations"] if f["id"] == fid), None)
        rid = form["recipe_id"] if form else None
        cp = comp.get((pid, rid))
        raw_recipe = next((r for r in d["recipes"] if r["id"] == rid), None)
        er = (cp or {}).get("元素比例", {})
        ratios = er.get("比例") if er.get("状态") == "可算" else None
        # 物性：同一配方编号或同一 recipe
        plist = {id(p): p for p in props_by.get((pid, fid), []) + props_by.get((pid, "recipe:" + str(rid)), [])}.values()
        pmap = defaultdict(list)
        for p in plist:
            pmap[p["标准物性"]].append(p)
        # 条件
        crow = conds.get((pid, tid), {"条件": {}})["条件"]
        cond = {}
        for f, label, unit in COND_FIELDS:
            x = crow.get(f, {})
            v, st, note = x.get("值"), x.get("状态", "未报告"), x.get("说明", "")
            if x.get("按配方") and fid in x["按配方"]:
                y = x["按配方"][fid]
                v, st, note = y.get("值"), y.get("状态"), y.get("说明", "按配方")
            if v is None and st not in ("未报告", "不适用"):
                st = {"⚠️": "冲突或多值", "未解析": "有文字未解析", "按配方": "本配方未单列"}.get(st, st)
            cond[f] = {"值": v, "状态": st, "说明": note}
            if x.get("默认") and not (x.get("按配方") and fid in x["按配方"]):
                cond[f]["默认"] = x["默认"]  # 11-05：默认值标记（如未写温度按室温）带进表述
        if "倍率_C" in c:
            cond["rate"] = {"值": c["倍率_C"], "状态": "✅", "说明": "取值点写明"}
        elif "电流_A每g" in c:
            one = d["condition_definitions"].get(test["condition_refs"].get("one_C", ""), {}).get("value", "")
            m = re.search(r"(\d{3,4}(?:\.\d+)?)\s*m?A", one)
            base = float(m.group(1)) if m else 1672.0
            cond["rate"] = {"值": round(c["电流_A每g"] * 1000 / base, 3), "状态": "🔶", "说明": f"取值点 {c['电流_A每g']} A g⁻¹ ÷ 1C({base:g})"}
        if "温度_C" in c:
            cond["temperature"] = {"值": c["温度_C"], "状态": "✅", "说明": "取值点写明"}
        if "硫载量_mg每cm2" in c:
            cond["sulfur_loading"] = {"值": c["硫载量_mg每cm2"], "状态": "✅", "说明": "取值点写明"}
        if "NP" in c:
            cond["NP"] = {"值": c["NP"], "状态": "✅", "说明": "取值点写明"}
        # 11-05：E/S 是由体积 ÷ 硫质量算出来的（不是原文值、不是人工核定），用本表述最终的载量重算
        es_t = crow.get("ES", {})
        if es_t.get("计算") and es_t.get("来源") in (None, "体积÷硫质量"):
            k_ = es_t["计算"]
            v, dflt, note = es_from_volume(k_["体积μL"], k_["体积说明"], k_["面积cm2"], k_["面积来源"], k_["硫质量mg"],
                                           cond["sulfur_loading"]["值"], k_["可用默认"], k_.get("电池形式"))
            cond["ES"] = {"值": v, "状态": "🔶" if v is not None else cond["ES"]["状态"], "说明": note, "默认": dflt,
                          "来源": "体积÷硫质量" if v is not None else None}
        else:
            cond["ES"].update({"默认": es_t.get("默认", []), "来源": es_t.get("来源")})
        if c["电池类型"] == "Li‖Cu":
            for f, label in (("current", "电流"), ("Li_Cu_capacity", "沉积容量")):
                x = crow.get(f, {})
                cond[f] = {"值": x.get("值"), "状态": x.get("状态", "未报告"), "说明": ""}
        cyc = c.get("圈数")
        stage = c.get("阶段")
        # 机制与支撑测量（后台链接）
        mechs = [m["id"] for m in d.get("mechanisms", []) if tid in (m.get("test_ids") or []) and fid in (m.get("A"), m.get("B"))]
        if not mechs:
            mechs = [m["id"] for m in d.get("mechanisms", []) if tid in (m.get("test_ids") or [])]
        meas = [m["id"] for m in d.get("measurements", []) if m.get("test_id") == tid]

        # ---- 拼表述文字 ----
        rt = recipe_text(cp, raw_recipe)
        f_ = lambda k, nd: "—" if ratios.get(k) is None else f"{ratios[k]:.{nd}f}"  # 不含氧/碳的配方（如纯正己烷）F/O、InOr 为空
        desc = (f"sO {f_('sO', 3)}、aC {f_('aC', 3)}、F/O {f_('F/O', 2)}、InOr {f_('InOr', 2)}"
                if ratios else f"元素比例不可算（{er.get('原因') or '无配方组成'}）")
        ptxt = []
        for k in MAIN_PROPS + sorted(set(pmap) - set(MAIN_PROPS)):
            if k in pmap:
                v = "；".join(f"{p['值'][:40]}{'…' if len(p['值']) > 40 else ''}（{p['来源类型']}）" for p in pmap[k][:2])
                ptxt.append(f"{k} {v}")
        ptxt = "；".join(ptxt) + "；其余未报告" if ptxt else "未报告"
        ctxt = []
        for f, label, unit in COND_FIELDS:
            x = cond[f]
            shown = (fmt_num(x["值"], unit) if f != "cell_format" else x["值"]) if x["值"] is not None else x["状态"]
            ctxt.append(f"{label} {shown}" + ("（推定）" if x["状态"] == "🔶" else ""))
        if c["电池类型"] == "Li‖Cu":
            for f, label, unit in (("current", "电流", "mA cm⁻²"), ("Li_Cu_capacity", "沉积容量", "mAh cm⁻²")):
                ctxt.append(f"{label} {fmt_num(cond[f]['值'], unit) or '未报告'}")
        ctxt.append(stage if stage in ("首圈",) else f"第 {cyc} 圈" if stage == "第 N 圈" else
                    f"平均（{cyc} 圈）" if stage == "平均" and cyc else stage)
        vt = g["val"]["类型"]
        vshow = str(g["raw"])
        perf = f"{c['性能类别']}·{c['标准指标']} = {vshow} {c['单位'] if c['单位'] not in vshow else ''}".strip()
        text = (f"【配方】{pid} {fid}：{rt}｜{desc}　【物性】{ptxt}　【条件】{'；'.join(ctxt)}；{c['电池类型']}、{c['正极类型']}"
                f"　【性能】{perf}（取值点：{c['取值点'] or '未写'}）")
        statements.append({
            "表述编号": f"ST{n:04d}", "论文": pid, "测试": tid, "测试名": test.get("name", ""), "配方": fid,
            "配方名": form["name"] if form else "", "recipe": rid, "是否对照": fid == d.get("control_id"),
            "配方文字": rt, "分块": blocks(cp, ctab), "元素比例状态": er.get("状态", "无配方组成"), "元素比例": ratios,
            "物性": {k: [{"值": p["值"], "来源类型": p["来源类型"], "数值": p["数值"], "单位": p["单位"], "原名": p["原名"],
                         "证据": p["证据"]} for p in v] for k, v in pmap.items()},
            "条件": cond, "阶段": stage, "圈数": cyc, "基准圈": c.get("基准圈"),
            "电池类型": c["电池类型"], "正极类型": c["正极类型"],
            "性能类别": c["性能类别"], "标准指标": c["标准指标"], "越大越好": c["越大越好"],
            "数值原文": vshow, "数值": g["val"]["值"], "数值类型": vt, "单位": c["单位"], "取值点": c["取值点"],
            "容量基准": c.get("容量基准"), "保持率基准": c.get("保持率基准"), "归类状态": c["状态"], "归类原因": c["原因"],
            "来源结果": g["results"], "证据句子": g["evidence"],
            "原句": sentences(sources[pid], g["evidence"][:3], 300),
            "机制链接": mechs, "支撑测量链接": meas, "表述文字": text})
    # 跨测试疑似重复：同篇、同配方、同指标、同阶段/圈数、同数值，且证据句有交集 → 标同一重复组（不删，下游按组去重）
    dup = defaultdict(list)
    for x in statements:
        dup[(x["论文"], x["配方"], x["标准指标"], x["阶段"], x["圈数"], x["数值"], x["数值类型"])].append(x)
    gid = 0
    for v in dup.values():
        if len({x["测试"] for x in v}) < 2:
            continue
        comps = []
        for x in v:  # 按证据交集连通
            hit = [cg for cg in comps if any(set(x["证据句子"]) & set(y["证据句子"]) for y in cg)]
            merged = [x] + [y for cg in hit for y in cg]
            comps = [cg for cg in comps if cg not in hit] + [merged]
        for cg in comps:
            # 条件有两个不同的已知值（如正极含硫 32% 与 56%）说明是不同电池，不算重复
            clash = any(len({x["条件"][f]["值"] for x in cg if x["条件"][f]["值"] is not None}) > 1 for f, _, _ in COND_FIELDS)
            if len({x["测试"] for x in cg}) > 1 and not clash:
                gid += 1
                for x in cg:
                    x["疑似重复组"] = f"D{gid:03d}"
    write_json("表述.json", statements)

    # ---------- 汇总 ----------
    st = statements
    has_prop = [s for s in st if s["物性"]]
    summary = {
        "表述条数": len(st), "论文数": len({s["论文"] for s in st}), "配方数": len({(s["论文"], s["配方"]) for s in st}),
        "按性能类别": dict(Counter(s["性能类别"] for s in st)),
        "按标准指标": dict(Counter(s["标准指标"] for s in st).most_common()),
        "数值类型": dict(Counter(s["数值类型"] for s in st)),
        "归类状态": dict(Counter(s["归类状态"] for s in st)),
        "电池类型": dict(Counter(s["电池类型"] for s in st)), "正极类型": dict(Counter(s["正极类型"] for s in st)),
        "元素比例可算的表述": sum(s["元素比例"] is not None for s in st),
        "有物性的表述": len(has_prop), "有物性表述涉及配方": len({(s["论文"], s["配方"]) for s in has_prop}),
        "物性类别出现次数（按表述）": dict(Counter(k for s in has_prop for k in s["物性"]).most_common()),
        "条件有值的表述数": {lab: sum(s["条件"][f]["值"] is not None for s in st) for f, lab, _ in COND_FIELDS},
        "有机制链接的表述": sum(bool(s["机制链接"]) for s in st),
        "跳过（未生成表述）": dict(skipped),
        "跨测试疑似重复：组数／涉及表述": [len({s.get("疑似重复组") for s in st if s.get("疑似重复组")}),
                               sum(bool(s.get("疑似重复组")) for s in st)],
    }
    write_json("step13c_汇总.json", summary)

    cols = ["表述编号", "论文", "测试", "配方", "是否对照", "性能类别", "标准指标", "数值原文", "数值", "数值类型", "单位", "阶段", "圈数",
            "E/S", "硫载量", "正极含硫", "锂厚", "N/P", "倍率", "温度", "电池形式", "电池类型", "正极类型",
            "配方文字", "sO", "aC", "F/O", "InOr"] + MAIN_PROPS + ["其他物性", "取值点", "容量基准", "保持率基准", "归类状态", "归类原因",
                                                                     "证据句子", "原句", "机制链接", "支撑测量链接", "疑似重复组", "表述文字"]
    rows = []
    for s in st:
        cv = lambda f: (s["条件"][f]["值"] if s["条件"][f]["值"] is not None else s["条件"][f]["状态"])
        r = s["元素比例"] or {}
        pv = lambda k: "；".join(f"{p['值']}（{p['来源类型']}）" for p in s["物性"].get(k, [])) or "未报告"
        other = "；".join(f"{k}：{p['值']}（{p['来源类型']}）" for k, v in s["物性"].items() if k not in MAIN_PROPS for p in v)
        rows.append([s["表述编号"], s["论文"], s["测试"], s["配方"], "是" if s["是否对照"] else "", s["性能类别"], s["标准指标"],
                     s["数值原文"], s["数值"], s["数值类型"], s["单位"], s["阶段"], s["圈数"],
                     cv("ES"), cv("sulfur_loading"), cv("S_content"), cv("Li_thickness"), cv("NP"), cv("rate"), cv("temperature"),
                     cv("cell_format"), s["电池类型"], s["正极类型"], s["配方文字"],
                     r.get("sO"), r.get("aC"), r.get("F/O"), r.get("InOr")] + [pv(k) for k in MAIN_PROPS] +
                    [other, s["取值点"], s["容量基准"], s["保持率基准"], s["归类状态"], s["归类原因"], s["证据句子"], s["原句"],
                     s["机制链接"], s["支撑测量链接"], s.get("疑似重复组", ""), s["表述文字"]])
    write_xlsx(OUT / "表述表.xlsx", [("表述表", cols, rows),
                                    ("统计", ["项目", "值"], [[k, v] for k, v in summary.items()])],
               widths={"配方文字": 40, "原句": 60, "表述文字": 90, "取值点": 24, "标准指标": 22, "归类原因": 28},
               notes=[f"step13c 标准化表述表｜{LABEL}｜2026-11-04 生成",
                      "一个性能数值一条表述（方案 §8.7，11-04 用户定）；同一数值在多条比较记录里重复出现的已合并，“来源结果”列见 表述.json。",
                      "四部分：配方（原文用量＋配方级元素比例）、物性（只用同篇对同一 recipe 报告的值，没报告写“未报告”）、测试条件、性能。",
                      "条件列显示数值；没有数值时显示原因（未报告／未得到）。取值点里写的倍率、温度、载量覆盖测试级条件。",
                      "机制不写进表述文字，“机制链接”“支撑测量链接”两列是后台编号，分析矛盾时调用。",
                      "疑似重复组：同一个数值被提取进同篇两个测试（如 P034 的 2485 同时在 T_OMC40 和 T_Cratio）。不自动删，因为也有作者对不同电池都写“约 1200”的情况；统计和找矛盾时按组只计一次。",
                      "数值类型：精确／约数／下限／上限／范围（取中值）；归类状态 ⚠️ 的结果和无法解析成单值的数值不生成表述。"])
    import json
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
