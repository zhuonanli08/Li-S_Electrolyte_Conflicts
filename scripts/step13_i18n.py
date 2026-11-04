"""step13 英文显示用的对照表（11-04 用户要求网站用英文）。Excel/JSON 仍是中文；这里只做显示层翻译。

提取结果里的自由文字（取值点、物性描述、作者原话转述）本身是中文，不翻译，按原样显示并在页面上注明。
"""
from __future__ import annotations

import re

CAT = {"放电容量类": "Discharge capacity", "倍率容量类": "Rate capacity", "衰减类": "Capacity fade",
       "库仑效率类": "Coulombic efficiency", "库仑效率类·全电池": "CE · full cell", "库仑效率类·Li‖Cu": "CE · Li‖Cu",
       "不进四类": "Not in the four classes"}
STD = {"硫比放电容量": "S-specific discharge capacity", "倍率硫比放电容量": "S-specific rate capacity",
       "容量保持率": "Capacity retention", "全电池 CE": "Full-cell CE", "Li‖Cu CE": "Li‖Cu CE",
       "复合物比放电容量": "Composite-specific discharge capacity", "循环寿命（圈）": "Cycle life (cycles)",
       "比放电容量（基准未写明）": "Specific discharge capacity (basis not stated)", "Li‖Cu 稳定循环圈数": "Li‖Cu stable cycles",
       "电池放电容量（绝对）": "Cell discharge capacity (absolute)", "面积放电容量": "Areal discharge capacity",
       "能量密度（Wh kg⁻¹）": "Energy density (Wh kg⁻¹)", "比放电容量（按正极＋电解液总质量）": "Specific capacity (cathode + electrolyte mass)",
       "比放电容量（按 Se/S 总质量）": "Specific capacity (Se/S mass)", "每圈容量衰减率": "Fade rate per cycle",
       "倍率比放电容量（按 SnO₂ 质量）": "Rate capacity (SnO₂ mass)", "倍率比放电容量（按 Li₂S 质量）": "Rate capacity (Li₂S mass)",
       "倍率硫利用率（%）": "Rate S utilisation (%)", "容量损失率": "Capacity loss (%)", "比放电容量（按 Li₂S 质量）": "Specific capacity (Li₂S mass)",
       "倍率复合物比放电容量": "Composite-specific rate capacity", "比放电容量（按 SnO₂ 质量）": "Specific capacity (SnO₂ mass)",
       "倍率容量比（高/低倍率）": "Rate capacity ratio (high/low)", "放电能量（绝对）": "Discharge energy (absolute)",
       "CE（单位异常）": "CE (unit anomaly)", "—": "—"}
STAGE = {"首圈": "1st cycle", "第 N 圈": "cycle N", "平均": "average", "未写圈数": "cycle not stated",
         "活化后（未写圈数）": "after activation (cycle not stated)", None: "—"}
PROP = {"Li⁺溶剂化结构": "Li⁺ solvation structure", "多硫化物溶解度": "Polysulfide solubility", "离子电导率": "Ionic conductivity",
        "多硫化物溶剂化（含结合能）": "Polysulfide solvation (incl. binding energy)", "非电解液本体性质（不进表述）": "Not a bulk-electrolyte property (excluded)",
        "黏度": "Viscosity", "分子计算性质": "Computed molecular property", "Li⁺迁移数": "Li⁺ transference number",
        "作者解释（不进表述）": "Author interpretation (excluded)", "扩散系数": "Diffusion coefficient", "盐或添加剂溶解度": "Salt/additive solubility",
        "Li₂S 溶解": "Li₂S dissolution", "密度": "Density", "相态": "Phase behaviour", "热稳定与安全": "Thermal stability & safety",
        "润湿性": "Wettability", "其他溶液性质": "Other solution property", "电化学稳定性": "Electrochemical stability",
        "其他（未归类）": "Other (unclassified)", "Li⁺脱溶剂化能": "Li⁺ desolvation energy", "硫溶解": "Sulfur dissolution",
        "电导活化能": "Conduction activation energy"}
SRC = {"实测": "measured", "计算": "computed", "定性描述": "qualitative", "文献转述": "cited", "未报告": "not reported"}
CHEM = {"多硫化锂（名义物种）": "Li polysulfide (nominal)", "链醚": "Linear ether", "阴离子": "Anion", "氟化醚": "Fluorinated ether",
        "环状碳酸酯": "Cyclic carbonate", "烃": "Hydrocarbon", "环醚": "Cyclic ether", "链状碳酸酯": "Linear carbonate",
        "磺酰亚胺盐": "Sulfonylimide salt", "磺酸盐": "Sulfonate", "卤化物": "Halide", "醌": "Quinone", "胺": "Amine", "阳离子": "Cation",
        "酰胺（内酰胺）": "Amide (lactam)", "有机硫（二硫醚）": "Organosulfur (disulfide)", "有机硫（多硫醚）": "Organosulfur (polysulfide)",
        "硝酸盐": "Nitrate", "氟磷酸盐": "Fluorophosphate", "氟硼酸盐": "Fluoroborate", "硼酸盐": "Borate", "多卤化物": "Polyhalide",
        "磺酰亚胺盐（环状）": "Cyclic sulfonylimide salt", "金属卤化物": "Metal halide", "季铵盐": "Quaternary ammonium salt",
        "酰亚胺": "Imide", "金属配合物": "Metal complex", "硫": "Sulfur", "未分类": "Unclassified"}
ROLE = {"溶剂": "Solvent", "锂盐": "Li salt", "添加剂": "Additive", "添加剂（介体）": "Additive (mediator)", "溶剂/添加剂": "Solvent/additive",
        "锂盐/添加剂": "Li salt/additive", "其他盐/添加剂": "Other salt/additive", "氧化还原介体（原文称均相催化剂）": "Redox mediator",
        "硫物种": "Sulfur species", "离子": "Ion", "未分类": "Unclassified"}
BIN = {"E/S≤5（贫液）": "E/S ≤5 (lean)", "E/S 5–10": "E/S 5–10", "E/S>10（富液）": "E/S >10 (flooded)",
       "硫载量<2": "S loading <2", "硫载量2–4": "S loading 2–4", "硫载量≥4（高载量）": "S loading ≥4 (high)",
       "正极含硫<50%": "Cathode S <50%", "正极含硫50–65%": "Cathode S 50–65%", "正极含硫≥65%": "Cathode S ≥65%",
       "倍率≤0.2C": "Rate ≤0.2C", "倍率0.2–1C": "Rate 0.2–1C", "倍率≥1C": "Rate ≥1C",
       "温度≤0°C": "T ≤0 °C", "温度>40°C": "T >40 °C", "常温": "Room T",
       "锂≤50μm（薄锂）": "Li ≤50 μm (thin)", "锂>50μm": "Li >50 μm", "扣式": "Coin", "软包": "Pouch", "其他": "Other"}
BATT = {"Li‖S": "Li‖S", "硫正极‖非锂金属负极": "S cathode ‖ non-Li anode", "Li‖Cu": "Li‖Cu", "对称电池": "Symmetric", "非性能测试": "Non-performance",
        "负极半电池（非锂硫）": "Anode half-cell (not Li–S)"}
CATHODE = {"硫碳类": "Sulfur–carbon", "SPAN": "SPAN", "Li₂S 正极": "Li₂S cathode"}
VTYPE = {"精确": "exact", "约数": "approx.", "范围": "range (mid)", "下限": "lower bound", "上限": "upper bound"}
CSTATE = {"未报告": "not reported", "冲突或多值": "conflicting / multiple", "有文字未解析": "text not parsed", "本配方未单列": "not given for this formulation",
          "不适用": "n/a", "缺失": "missing", "缺复合物含硫": "composite S missing", "缺浆料配比": "slurry ratio missing", "按配方": "per formulation"}
MODEL = {"线性岭回归": "Ridge (fixed effects)", "线性混合模型": "Linear mixed model", "梯度提升": "Gradient boosting",
         "单调约束梯度提升": "Monotone gradient boosting", "随机森林": "Random forest", "高斯过程": "Gaussian process"}
CTYPE = {"NORM": "Same formulation, still far apart after normalisation", "LOPO": "Paper's finding vs. model trained without it",
         "FLIP": "Condition-dependent flip", "DESC": "Same design direction, opposite outcome", "SAME": "Identical change, opposite outcome"}
DIR = {"变好": "better", "变坏": "worse", "差异小": "similar"}
BASIS = {"数值": "numeric", "定性": "qualitative", None: "—"}
FAR = {"圈数": "cycles", "E/S": "E/S", "倍率": "rate", "载量": "loading", "电流": "current", "沉积容量": "plating capacity"}
STDKEY = {"E/S": "E/S (μL mg⁻¹)", "载量": "S loading (mg cm⁻²)", "含硫": "Cathode S (%)", "倍率C": "Rate (C)", "温度": "T (°C)",
          "软包": "Pouch", "圈数": "Cycle", "电流mA/cm2": "Current (mA cm⁻²)", "沉积容量mAh/cm2": "Plating capacity (mAh cm⁻²)"}
STDSET = {"普遍条件": "Common condition", "实用条件": "Practical condition"}
COND_LABEL = [("ES", "E/S", "μL mg⁻¹"), ("sulfur_loading", "S loading", "mg cm⁻²"), ("S_content", "cathode S", "%"),
              ("Li_thickness", "Li", "μm"), ("NP", "N/P", ""), ("rate", "rate", "C"), ("temperature", "T", "°C"), ("cell_format", "cell", "")]

_UNIT_FIX = [("（体积比）", " (v/v)"), ("（摩尔比）", " (mol/mol)"), ("体积份", "vol. parts"), ("用量未报告", "amount not reported"),
             ("M（原文 m，已核实）", "M (source writes m; verified)"), ("体积比", "v/v"), ("摩尔份", "mol. parts"), ("份", " parts")]


def t(d: dict, k, default=None):
    return d.get(k, default if default is not None else k)


def fmt(v, unit=""):
    if v is None:
        return None
    s = f"{v:.3g}" if isinstance(v, float) and abs(v) < 1000 else f"{v:g}" if isinstance(v, (int, float)) else str(v)
    return f"{s} {unit}".strip()


def short_unit(u: str) -> str:
    if (u or "").startswith("M（原文 m"):
        return "M (source writes m; verified)"
    return re.split(r"[（(，,；;]", u or "")[0].strip()


def recipe_en(comp: dict | None, fallback: str = "") -> str:
    """配方英文写法：原文用量＋原文单位；体积份/摩尔比的组分合写成 A:B = x:y (v/v)。"""
    if not comp:
        s = fallback
        for a, b in _UNIT_FIX:
            s = s.replace(a, b)
        return s.replace("；", "; ") or "(formulation not recorded)"
    parts, ratio = [], {"v/v": [], "mol/mol": []}
    for i in comp["组分"]:
        name, amt, unit, cat = i["组分"], i["原文用量"], i["原文单位"], i["单位类别"]
        if i.get("采用单位") == "mol/L" and str(unit).startswith("m"):
            unit = "M（原文 m，已核实）"
        if cat == "体积份" and "vol" not in str(unit):
            ratio["v/v"].append((name, amt))
        elif cat == "摩尔比":
            ratio["mol/mol"].append((name, amt))
        elif cat == "不可用" or not amt or amt == "未报告":
            parts.append(f"{name} (amount not reported)")
        else:
            u = short_unit(unit).replace("体积份", "vol. parts")
            parts.append(f"{amt} {u} {name}".replace("  ", " ").strip())
    for k, lst in ratio.items():
        if len(lst) == 1:
            amt = str(lst[0][1])
            parts.append(f"{lst[0][0]} (single solvent)" if not re.match(r"^[\d.]+$", amt) or "单一" in amt else f"{lst[0][0]} ({amt} {k} parts)")
        elif lst:
            parts.append(f"{':'.join(n for n, _ in lst)} = {':'.join(str(a) for _, a in lst)} ({k})")
    return "; ".join(parts)


def cond_text(cond: dict) -> str:
    out = []
    for f, lab, unit in COND_LABEL:
        x = cond.get(f, {})
        v = x.get("值")
        if f == "cell_format":
            shown = t(BIN, v) if v else t(CSTATE, x.get("状态", "未报告"))
        else:
            shown = fmt(v, unit) if v is not None else t(CSTATE, x.get("状态", "未报告"))
        out.append(f"{lab} {shown}" + (" (inferred)" if x.get("状态") == "🔶" else ""))
    return "; ".join(out)


def statement_en(s: dict, comp: dict | None) -> str:
    r = s.get("元素比例")
    desc = (f"sO {r['sO']:.3f}, aC {r['aC']:.3f}, F/O {r['F/O']:.2f}, InOr {r['InOr']:.2f}" if r else "elemental ratios not calculable")
    props = []
    for k, lst in s["物性"].items():
        v = "; ".join(f"{p['值'][:40]}{'…' if len(p['值']) > 40 else ''} ({t(SRC, p['来源类型'])})" for p in lst[:2])
        props.append(f"{t(PROP, k)}: {v}")
    ptxt = "; ".join(props) + "; others not reported" if props else "not reported"
    stage = s["阶段"]
    cyc = "1st cycle" if stage == "首圈" else f"cycle {s['圈数']}" if stage == "第 N 圈" else \
        f"average ({s['圈数']} cycles)" if stage == "平均" and s["圈数"] else t(STAGE, stage)
    perf = f"{t(CAT, s['性能类别'])} · {t(STD, s['标准指标'])} = {s['数值原文']} {s['单位'] if s['单位'] not in str(s['数值原文']) else ''}".strip()
    return (f"[Formulation] {s['论文']} {s['配方']}: {recipe_en(comp, s['配方文字'])} | {desc}   [Properties] {ptxt}   "
            f"[Conditions] {cond_text(s['条件'])}; {cyc}; {t(BATT, s['电池类型'])}, {t(CATHODE, s['正极类型'])}   "
            f"[Performance] {perf}   (sampling point as extracted: {s['取值点'] or '—'})")
