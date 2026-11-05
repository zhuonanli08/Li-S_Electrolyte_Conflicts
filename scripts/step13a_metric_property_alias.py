"""step13a：统一指标名称（归到四类性能）和物性名称。

输入（只读）：规则处理版 30 篇 candidate.json。
输出（OUT）：
  结果归类.json      —— 每条结果（1054 条）的性能类别、标准指标、取值阶段、圈数、基准、方向含义、状态
  指标别名表.json     —— 原名×单位×测试类型 → 标准指标
  物性归类.json      —— 每个物性取值（448 个）的标准物性、来源类型、数值、挂到哪个配方
  物性别名表.json
  别名表与复核表.xlsx —— 两张别名表 + 复核表（🔶⚠️ 项与原因）
规则都写在本文件里；改规则后重跑即可。
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

from step13_common import LABEL, OUT, load_papers, parse_value, write_json, write_xlsx

# ---------- 电池类型 ----------
def battery_type(test: dict) -> str:
    k, cell, name = test["kind"], test.get("cell", ""), test.get("name", "")
    txt = f"{cell} {name}"
    # 11-05：Li|Ni（P333 LiMg|Ni、P382 Li|Ni）同属沉积/剥离 CE 测试，并入 Li‖Cu
    if k == "锂铜效率" or re.search(r"Li\s*\|+\s*Cu|Cu\s*\|+\s*Li|Li-Cu|Li–Cu|Cu工作|Li[A-Za-z]*\s*\|+\s*Ni\b", txt):
        return "Li‖Cu"
    if k == "对称电池":
        return "对称电池"
    if k not in ("全电池性能", "其他"):
        return "非性能测试"
    if re.search(r"石墨\s*\|\|\s*Li|Gr\s*\|\|\s*Li|^Li/SnO2", cell.strip()):
        return "负极半电池（非锂硫）"
    if re.search(r"Li\s*\|+\s*(?:prelithiated\s+|预锂化)?(?:SiO|Si\b)", cell):  # 11-05：P269 Li||SiO 负极半电池
        return "负极半电池（非锂硫）"
    if re.search(r"Gr|石墨|SnO2", cell):
        return "硫正极‖非锂金属负极"
    if re.search(r"Li2S\s*[/|‖]+\s*Cu|无负极|anode[\s\-]*free", txt, re.I):  # 11-05：P258 Li2S/Cu 无锂负极电池
        return "硫正极‖非锂金属负极"
    return "Li‖S"


def cathode_type(paper: dict, test: dict, cdefs: dict) -> str:
    txt = test.get("cell", "") + " " + test.get("name", "")
    ref = test["condition_refs"].get("cathode")
    if ref and ref in cdefs:
        txt += " " + cdefs[ref]["value"]
    # 11-05：补 S@pPAN、pPAN-S 等写法（P003）；排除词不再误配 “Li2S/Cu” 里的 “S/C”（P258）
    if re.search(r"SPAN|PAN\s*[@/\-]\s*S\b|S\s*[@/]\s*p?PAN|pPAN|硫化聚丙烯腈|sulfuri[sz]ed\s+polyacrylonitrile", txt, re.I):
        return "SPAN"
    if re.search(r"Li2S(?![\d])", txt) and not re.search(r"(?<!Li2)S/C|C/S(?!\d)|(?<!Li2)S@|KB", txt):
        return "Li₂S 正极"
    # 11-05：非硫正极（P212 Li/LFP）与有机硫正极（P264 PMTT）不进硫碳类
    if re.search(r"\bLFP\b|LiFePO4|\bNCM\d*|\bNMC\d*|LiCoO2|\bLCO\b|LiMn2O4", txt):
        return "非硫正极"
    if re.search(r"PMTT|thiuram", txt, re.I):
        return "有机硫正极"
    return "硫碳类"


# ---------- 取值点解析 ----------
def parse_point(point: str, metric: str) -> dict:
    p = point or ""
    out: dict = {}
    m = re.search(r"第\s*(\d+)\s*圈|(\d+)\s*(?:th|st|nd|rd)(?![a-z])|(\d+)\s*圈|(\d+)\s*cycles?", p)
    if re.search(r"首圈|第\s*1\s*圈|1st|first|初始|initial|首次", p + metric, re.I) and not (m and int(next(g for g in m.groups() if g)) > 1):
        out["阶段"], out["圈数"] = "首圈", 1
    elif re.search(r"平均|average|avg", p + metric, re.I):
        out["阶段"] = "平均"
        if m:
            out["圈数"] = int(next(g for g in m.groups() if g))
    elif m:
        n = int(next(g for g in m.groups() if g))
        out["阶段"], out["圈数"] = ("首圈", 1) if n == 1 else ("第 N 圈", n)
    elif re.search(r"活化后|稳定", p):
        out["阶段"] = "活化后（未写圈数）"
    else:
        out["阶段"] = "未写圈数"
    # 11-05：C/n 前面是 ° 或 ℃ 的是温度（P338“30 °C/0.5 mA”曾被读成 C/0 而除零）
    r = re.search(r"(\d+(?:\.\d+)?)\s*C(?![a-zA-Zl°])", p) or re.search(r"(?<![°℃])(?<!°\s)C\s*/\s*([1-9]\d*(?:\.\d+)?)", p)
    if r:
        out["倍率_C"] = float(r.group(1)) if "/" not in r.group(0) else round(1 / float(r.group(1)), 4)
    r = re.search(r"(\d+(?:\.\d+)?)\s*A\s*/?\s*g", p)
    if r:
        out["电流_A每g"] = float(r.group(1))
    r = re.search(r"([−-]?\d+)\s*°\s*C", p) or re.search(r"(\d{3})\s*K\b", p)
    if r:
        v = float(r.group(1).replace("−", "-"))
        out["温度_C"] = v - 273.15 if r.group(0).strip().endswith("K") else v
    r = re.search(r"(\d+(?:\.\d+)?)\s*mg\s*cm", p)
    if r:
        out["硫载量_mg每cm2"] = float(r.group(1))
    r = re.search(r"N/P\s*(\d+(?:\.\d+)?)", p, re.I)
    if r:
        out["NP"] = float(r.group(1))
    return out


# ---------- 指标规则 ----------
NON_FOUR = r"阻抗|电阻|Rct|过电位|极化|滞后|平台|穿梭电流|自放电|OCV|扩散|嵌锂|脱锂|充电容量|无硫|不可逆容量|容量损失（降低E/S）|E/S"
CAP_UNIT = r"mAh|mA h|Ah"


def basis_from_unit(unit: str, norm_text: str, metric: str = "") -> tuple[str, str]:
    """容量基准：先看指标名，再看单位，最后看本测试“归一化”条件文字。"""
    u, t = unit or "", norm_text or ""
    if re.search(r"representative", metric, re.I):
        return "按正极＋电解液总质量（代表容量）", "✅"
    if re.search(r"硫比|硫贡献", metric):
        return "按硫", "✅"
    if re.search(r"复合物", metric):
        return "按复合物", "✅"
    if re.search(r"cm", u):
        return "按面积", "✅"
    if re.fullmatch(r"\s*m?Ah(/cell)?\s*", u):
        return "电池绝对容量", "✅"
    if re.search(r"Gr", u):
        return "按石墨", "✅"
    if re.search(r"compos|comp", u, re.I):
        return "按复合物", "✅"
    if re.search(r"g\s*S|gS|gs|\(S\)|（硫）|sulfur", u) and "未标s" not in u:
        return "按硫", "✅"
    # 单位没写清，看归一化条件文字（顺序重要：非纯硫基准先判）
    if re.search(r"Se/S", t):
        return "按 Se/S 总质量", "✅"
    if re.search(r"SnO2质量", t):
        return "按 SnO₂ 质量", "✅"
    if re.search(r"Li2S质量", t):
        return "按 Li₂S 质量", "✅"
    if re.search(r"SPAN", t) and re.search(r"复合|活性|聚合物", t):
        return "按复合物（SPAN）", "✅"
    if re.search(r"未明确|未知|未在|不一致", t):
        return "基准未写明", "🔶"
    if re.search(r"硫", t):
        return ("按硫", "🔶") if "推定" in t else ("按硫", "✅")
    return "基准未写明", "🔶"


def classify(paper: dict, test: dict, res: dict, cdefs: dict) -> dict:
    m, u = res["metric"], res.get("unit") or ""
    bt = battery_type(test)
    pt = parse_point(res.get("point") or "", m)
    norm_ref = test["condition_refs"].get("normalization")
    norm = cdefs.get(norm_ref, {}).get("value", "") if norm_ref else ""
    o = {"电池类型": bt, **pt}
    tname = f"{test['id']} {test.get('name','')}"

    def done(cat, std, pol, st="✅", why=""):
        o.update({"性能类别": cat, "标准指标": std, "越大越好": pol, "状态": st, "原因": why})
        return o

    if bt in ("非性能测试", "负极半电池（非锂硫）"):
        return done("不进四类", "—", None, "✅", f"测试类型为{test['kind']}／{bt}")
    if res.get("component") not in (None, "", "整体") and not re.search(r"容量|CE|效率", m):
        return done("不进四类", "—", None, "✅", f"分量指标（{res.get('component')}）")
    if re.search(r"自放电测试CE", m):
        return done("不进四类", "—", None, "✅", "自放电测试中的 CE，属自放电测量")
    if re.search(r"CE|库仑效率|库伦效率|coulombic", m, re.I) and not re.search(r"寿命|稳定", m):
        if "%" not in u:
            return done("库仑效率类", "CE（单位异常）", True, "⚠️", f"单位为“{u}”")
        if bt == "Li‖Cu":
            return done("库仑效率类", "Li‖Cu CE", True)
        if bt in ("Li‖S", "硫正极‖非锂金属负极"):
            return done("库仑效率类", "全电池 CE", True)
        return done("不进四类", "—", None, "✅", f"{bt}中的 CE（非锂金属／非全电池）")
    if re.search(NON_FOUR, m):
        return done("不进四类", "—", None, "✅", "非四类性能测量（阻抗、过电位、自放电等）")
    if bt == "对称电池":
        return done("不进四类", "—", None, "✅", "对称电池指标不进四类")
    if bt == "Li‖Cu":
        if re.search(r"寿命|圈数|失效|稳定", m) and re.search(r"圈|cycle", u):
            return done("库仑效率类", "Li‖Cu 稳定循环圈数", True)
        return done("不进四类", "—", None, "✅", "Li‖Cu 测试中的非 CE 指标")
    # 以下为 Li‖S 或 硫‖非锂负极
    if re.search(r"每圈.*衰减|衰减率", m) or re.search(r"/圈|cycle−1|cycle-1", u):
        return done("衰减类", "每圈容量衰减率", False)
    if re.search(r"相对低倍率", m):
        return done("倍率容量类", "倍率容量比（高/低倍率）", True)
    if re.search(r"保持|相对初始", m):
        if "%" not in u and "首圈" not in u:
            return done("衰减类", "容量保持率", True, "⚠️", f"单位为“{u}”")
        nm = re.search(r"保持率[^；。]*", norm)  # 归一化条件里关于保持率分母的那一句
        txt = (res.get("point") or "") + u + m + (nm.group(0) if nm and not re.search(r"未明|未报告", nm.group(0)) else "")
        o["保持率基准"] = ("相对首圈或初始" if re.search(r"首圈|初始|initial", txt)
                      else "相对活化后" if re.search(r"活化|稳定后|第\s*[2-9]\s*圈", txt) else "基准未写明")
        return done("衰减类", "容量保持率", True, "✅" if o["保持率基准"] != "基准未写明" else "🔶",
                    "" if o["保持率基准"] != "基准未写明" else "保持率分母（首圈/活化后）未写明")
    if re.search(r"容量衰减|容量损失", m) and "%" in u:
        return done("衰减类", "容量损失率", False, "🔶", "累计损失百分比，与保持率互补（100−保持率），分开存放")
    if re.search(r"寿命|圈数|失效|短路|可运行|衰减起点|穿梭出现|循环稳定性|循环终止", m) and re.search(r"圈|cycle", u):
        return done("衰减类", "循环寿命（圈）", True, "🔶" if "穿梭" in m else "✅",
                    "以穿梭出现作失效判据" if "穿梭" in m else "")
    if re.search(r"能量", m):
        if re.search(r"Wh\s*kg", u):
            return done("放电容量类", "能量密度（Wh kg⁻¹）", True, "🔶" if "堆叠" in m else "✅",
                        "估算值（堆叠计算）" if "堆叠" in m else "")
        return done("放电容量类", "放电能量（绝对）", True)
    if re.search(r"利用率", m):
        return done("倍率容量类", "倍率硫利用率（%）", True, "🔶", "以理论容量百分比表示，未换算成容量")
    if u in ("", "定性", "倍数", "未给", "原文定性") or re.search(r"未给|无数值", u):
        return done("不进四类", "—", None, "⚠️", f"单位为“{u or '空'}”，数值含义不明（可能是圈数、倍数或定性）")
    if re.search(r"容量|capacity", m, re.I) and re.search(CAP_UNIT, u):
        b, bst = basis_from_unit(u, norm, m)
        o["容量基准"] = b
        rate_test = bool(re.search(r"倍率", m)) or bool(re.search(r"倍率|rate", tname, re.I))
        rate_ok = bool(re.search(r"倍率", m)) or "倍率_C" in pt or "电流_A每g" in pt
        if b == "按面积":
            std = "面积放电容量"
        elif b.startswith("按正极"):
            std = "比放电容量（按正极＋电解液总质量）"
        elif b == "电池绝对容量":
            std = "电池放电容量（绝对）"
        elif b.startswith("按复合物"):
            std = "复合物比放电容量"
        elif b == "按硫":
            std = "硫比放电容量"
        elif b == "基准未写明":
            std = "比放电容量（基准未写明）"
        else:
            std = f"比放电容量（{b}）"
        if rate_test:
            st = "✅" if rate_ok else "🔶"
            why = "" if st == "✅" else "按测试名（倍率/rate）归入倍率类，取值点未写倍率"
            if bst == "🔶":
                st, why = "🔶", "；".join(x for x in (why, f"容量基准：{b}") if x)
            return done("倍率容量类", "倍率" + std, True, st, why)
        return done("放电容量类", std, True, bst, "" if bst == "✅" else f"容量基准：{b}")
    return done("不进四类", "—", None, "⚠️", "未匹配到任何规则，需人工看")


# ---------- 物性规则（按顺序，先匹配先得） ----------
PROP_RULES = [
    (r"解释|推测|转述|文献|物理含义|作用", "作者解释（不进表述）"),
    (r"SEI|碳载体|碳基体|孔结构|孔体积|硫限域|固体键合|固体中间体|中间体Li|浆料|原位静置|原位枝晶|扩散阶段差异|Li\+扩散系数", "非电解液本体性质（不进表述）"),
    (r"活化能", "电导活化能"),
    (r"电导", "离子电导率"),
    (r"黏度|粘度", "黏度"),
    (r"迁移数|传输量", "Li⁺迁移数"),
    (r"密度", "密度"),
    (r"脱溶", "Li⁺脱溶剂化能"),
    (r"LiNO3.*溶解|LiFSI溶解|NH4BS.*溶解|Cu-2-T溶解", "盐或添加剂溶解度"),
    (r"Li2S(?![\d])[^溶]*溶解|Li2S溶解|Li2S粉末", "Li₂S 溶解"),
    (r"元素硫", "硫溶解"),
    (r"多硫化物溶剂化|LiPS溶剂化|多硫化物–溶剂|Li2S6结合能|LiPS结合|多硫化物溶剂化/", "多硫化物溶剂化（含结合能）"),
    (r"多硫化物|多硫化锂|LiPS|Li2S4|Li2S2|长链|短链|有机硫化锂|理论硫浓度", "多硫化物溶解度"),
    (r"Li\+|离子对|离子聚集|离子缔合|NMR溶剂结构|Raman溶剂化|K\+|解离|配位", "Li⁺溶剂化结构"),
    (r"^D\(|FSC|扩散", "扩散系数"),
    (r"氧化|还原敏感|电化学窗口", "电化学稳定性"),
    (r"阻燃|热稳定|沸点|低温|冻结", "热稳定与安全"),
    (r"润湿|接触角", "润湿性"),
    (r"LUMO|HOMO|前线轨道|ESP|静电势|键解离|DN|供体数|极性|单分子|热力学稳定性|结合|晶格能", "分子计算性质"),
    (r"相态|相稳定|混合", "相态"),
    (r"氧溶解度|水含量|理论容量|输运", "其他溶液性质"),
]
CALC = r"模拟|MD|DFT|计算|结合能|LUMO|HOMO|ESP|RDF|轨道|BDE|模型|ΔG|理论"


def prop_std(name: str) -> str:
    for pat, std in PROP_RULES:
        if re.search(pat, name):
            return std
    return "其他（未归类）"


def prop_source(prop: dict, v: str) -> str:
    txt = " ".join([prop["name"], prop.get("method") or "", prop.get("system") or ""])
    if re.search(r"引言转述|文献", v + prop["name"]):
        return "文献转述"
    if re.search(CALC, txt):
        return "计算"
    has_num = bool(re.search(r"\d", re.sub(r"Li2S\d?|Li\+|S\d|\d+\s*M\b|NO3|TFSI|FSI", "", v)))
    if not has_num or re.search(r"作者称|推测|可能|判断|认为", v):
        return "定性描述"
    return "实测"


PROP_NUM = re.compile(r"([−-]?\d+(?:\.\d+)?)(?:\s*[×x]\s*10\s*([−-]?\d+))?\s*(mS\s*cm|S\s*cm|mS/cm|mPa\s*s|cP|g\s*cm|M\b|mol|kJ|eV|kcal|ppm|cm−1|°|V\b|nm|Å|m2|wt%)?")


def prop_number(v: str):
    """取物性值里的第一个“数＋单位”；无单位的纯数（迁移数等）也取。"""
    for m in PROP_NUM.finditer(v.replace("−", "-")):
        num = float(m.group(1)) * (10 ** int(m.group(2).replace("−", "-")) if m.group(2) else 1)
        return num, (m.group(3) or "").strip()
    return None, ""


def link_keys(key: str, paper: dict) -> tuple[list[str], str]:
    """物性键 → 本篇配方（formulation）编号；按 recipe 判断是否同一配方。"""
    fids = {f["id"] for f in paper["formulations"]}
    rids = {r["id"] for r in paper["recipes"]}
    if key in fids:
        return [key], "✅"
    parts = [x.strip() for x in re.split(r"→|/|,|，|、|；|;|\s+与\s+|和", key) if x.strip()]
    hit = [x for x in parts if x in fids]
    if hit and len(hit) == len(parts):
        return hit, "✅"
    if hit:
        return hit, "🔶"
    rhit = [f["id"] for f in paper["formulations"] if f["recipe_id"] == key]
    if rhit:
        return rhit, "✅"
    return [], "未挂到配方"


def main() -> None:
    papers = load_papers()
    res_rows, by_alias = [], defaultdict(lambda: {"条数": 0, "有数值": 0, "论文": set(), "标准指标": Counter(),
                                                 "类别": Counter(), "状态": Counter(), "原因": Counter()})
    for pid, d in papers.items():
        cdefs = d["condition_definitions"]
        for t in d["tests"]:
            ctype = cathode_type(d, t, cdefs)
            for r in t["results"]:
                c = classify(d, t, r, cdefs)
                va, vb = parse_value(r.get("value_A")), parse_value(r.get("value_B"))
                row = {"论文": pid, "测试": t["id"], "结果": r["id"], "原名": r["metric"], "单位": r.get("unit") or "",
                       "测试类型": t["kind"], "取值点": r.get("point") or "", "正极类型": ctype,
                       "A": r.get("A"), "B": r.get("B"), "A值": va, "B值": vb, **c}
                res_rows.append(row)
                key = (r["metric"], r.get("unit") or "", t["kind"], c["电池类型"])
                a = by_alias[key]
                a["条数"] += 1
                a["有数值"] += int(va["值"] is not None or vb["值"] is not None)
                a["论文"].add(pid)
                a["标准指标"][c["标准指标"]] += 1
                a["类别"][c["性能类别"]] += 1
                a["状态"][c["状态"]] += 1
                if c["原因"]:
                    a["原因"][c["原因"]] += 1
    alias = []
    for (m, u, k, bt), a in sorted(by_alias.items(), key=lambda x: -x[1]["条数"]):
        alias.append({"原名": m, "单位": u, "测试类型": k, "电池类型": bt,
                      "性能类别": "；".join(f"{x}×{n}" for x, n in a["类别"].most_common()),
                      "标准指标": "；".join(f"{x}×{n}" for x, n in a["标准指标"].most_common()),
                      "条数": a["条数"], "有数值条数": a["有数值"], "论文数": len(a["论文"]),
                      "论文": sorted(a["论文"]),
                      "状态": "；".join(f"{x}×{n}" for x, n in a["状态"].most_common()),
                      "原因": "；".join(f"{x}×{n}" for x, n in a["原因"].most_common())})
    write_json("结果归类.json", res_rows)
    write_json("指标别名表.json", alias)

    # ---------- 物性 ----------
    prop_rows, palias = [], defaultdict(lambda: {"条数": 0, "论文": set(), "来源": Counter()})
    for pid, d in papers.items():
        rec_of = {f["id"]: f["recipe_id"] for f in d["formulations"]}
        for i, p in enumerate(d["properties"]):
            std = prop_std(p["name"])
            if not p["values"]:
                prop_rows.append({"论文": pid, "物性序号": i, "原名": p["name"], "标准物性": std, "键": None,
                                  "值": None, "来源类型": "未报告", "数值": None, "单位": "", "挂接配方": [],
                                  "挂接recipe": [], "挂接状态": "无取值", "证据": p.get("evidence_ids", []),
                                  "体系": p.get("system", ""), "方法": p.get("method", "")})
                continue
            for k, v in p["values"].items():
                v = str(v)
                fids, lst = link_keys(k, d)
                num, unit = prop_number(v)
                src = prop_source(p, v)
                prop_rows.append({"论文": pid, "物性序号": i, "原名": p["name"], "标准物性": std, "键": k, "值": v,
                                  "来源类型": src, "数值": num if src in ("实测", "计算") else None, "单位": unit,
                                  "挂接配方": fids, "挂接recipe": sorted({rec_of[f] for f in fids if f in rec_of}),
                                  "挂接状态": lst, "证据": p.get("evidence_ids", []),
                                  "体系": p.get("system", ""), "方法": p.get("method", "")})
                pa = palias[(p["name"], std)]
                pa["条数"] += 1
                pa["论文"].add(pid)
                pa["来源"][src] += 1
    palias_rows = [{"原名": n, "标准物性": s, "取值数": a["条数"], "论文": sorted(a["论文"]),
                    "来源类型": "；".join(f"{x}×{c}" for x, c in a["来源"].most_common())}
                   for (n, s), a in sorted(palias.items(), key=lambda x: (x[0][1], -x[1]["条数"]))]
    write_json("物性归类.json", prop_rows)
    write_json("物性别名表.json", palias_rows)

    # ---------- 汇总与 Excel ----------
    num_rows = [r for r in res_rows if r["A值"]["值"] is not None or r["B值"]["值"] is not None]
    cat = Counter(r["性能类别"] for r in num_rows)
    std = Counter((r["性能类别"], r["标准指标"]) for r in num_rows if r["性能类别"] != "不进四类")
    pv = [r for r in prop_rows if r["值"] is not None]
    summary = {
        "结果总数": len(res_rows), "有数值结果": len(num_rows), "原名种数": len({r["原名"] for r in res_rows}),
        "有数值结果按类别": dict(cat), "四类标准指标种数": len(std),
        "四类标准指标": {f"{a}｜{b}": n for (a, b), n in std.most_common()},
        "状态（有数值、四类内）": dict(Counter(r["状态"] for r in num_rows if r["性能类别"] != "不进四类")),
        "物性记录": len(papers and [p for d in papers.values() for p in d["properties"]]),
        "物性取值": len(pv), "物性原名种数": len({r["原名"] for r in pv}),
        "标准物性种数": len({r["标准物性"] for r in pv}),
        "物性取值按标准物性": dict(Counter(r["标准物性"] for r in pv).most_common()),
        "物性取值按来源类型": dict(Counter(r["来源类型"] for r in pv)),
        "物性取值挂接": dict(Counter(r["挂接状态"] for r in pv)),
        "带数值的物性取值（实测或计算）": sum(r["数值"] is not None for r in pv),
    }
    write_json("step13a_汇总.json", summary)

    review = [r for r in res_rows if r["状态"] in ("🔶", "⚠️") and (r["A值"]["值"] is not None or r["B值"]["值"] is not None)]
    write_xlsx(OUT / "别名表与复核表.xlsx", [
        ("指标别名表", ["原名", "单位", "测试类型", "电池类型", "性能类别", "标准指标", "条数", "有数值条数", "论文数", "论文", "状态", "原因"],
         [[a[k] for k in ["原名", "单位", "测试类型", "电池类型", "性能类别", "标准指标", "条数", "有数值条数", "论文数", "论文", "状态", "原因"]] for a in alias]),
        ("物性别名表", ["标准物性", "原名", "取值数", "论文", "来源类型"],
         [[a["标准物性"], a["原名"], a["取值数"], a["论文"], a["来源类型"]] for a in palias_rows]),
        ("指标复核（有数值的🔶⚠️）", ["状态", "原因", "论文", "测试", "结果", "原名", "单位", "取值点", "电池类型", "性能类别", "标准指标", "A", "A值", "B", "B值"],
         [[r["状态"], r["原因"], r["论文"], r["测试"], r["结果"], r["原名"], r["单位"], r["取值点"], r["电池类型"], r["性能类别"], r["标准指标"],
           r["A"], r["A值"].get("值"), r["B"], r["B值"].get("值")] for r in review]),
        ("物性取值", ["论文", "标准物性", "原名", "键", "值", "来源类型", "数值", "单位", "挂接配方", "挂接状态", "体系"],
         [[r["论文"], r["标准物性"], r["原名"], r["键"], r["值"], r["来源类型"], r["数值"], r["单位"], r["挂接配方"], r["挂接状态"], r["体系"]] for r in pv]),
    ], widths={"原名": 22, "原因": 40, "标准指标": 28, "论文": 24, "值": 50, "体系": 30, "取值点": 30},
        notes=[f"step13a 指标与物性别名表｜{LABEL}｜2026-11-04 生成",
               "四类性能：放电容量类、倍率容量类、衰减类、库仑效率类（方案 §8.7）；其余测量记“不进四类”，不生成性能表述。",
               "状态：✅ 规则直接判定；🔶 有推定（如容量基准由条件文字推定、保持率分母未写明）；⚠️ 单位与指标不符或未匹配规则。",
               "物性：只挂到同一篇里键能对应到配方编号的取值；“作者解释”“非电解液本体性质”两类不进表述。",
               "规则写在 scripts/step13a_metric_property_alias.py；人工意见请写在本表右侧空列，Claude 不改人工格。"])
    for k, v in summary.items():
        print(k, ":", v)


if __name__ == "__main__":
    main()
