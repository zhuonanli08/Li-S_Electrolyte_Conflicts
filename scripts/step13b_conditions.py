"""step13b：整理性能测试的测试条件（派生层，不改提取结果）。

条件：E/S、硫面载量、正极硫含量（极片基准，方案 §8.7 规则）、锂厚、N/P、倍率、电流密度（Li‖Cu）、温度、电池形式、正极类型。
来源：每个测试 condition_refs → condition_definitions 的文字；取值点（point）里写的倍率/温度/载量在 step13c 覆盖测试级条件。
人工判断层：正极硫含量核定.json（Claude 读原文后写；键 = 论文|条件编号），优先于解析结果。
输出：条件表.json、条件表.xlsx
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter

from step13_common import LABEL, OUT, load_papers, read_json, write_json, write_xlsx

S_IN_LI2S = 32.06 / 45.95
F = r"(\d+(?:\.\d+)?)"


def clean(t: str) -> str:
    return (t or "").replace("−", "-").replace("µ", "μ").replace("–", "-").replace("～", "~")


def per_formulation(text: str, fids: set[str]) -> dict[str, str]:
    """“F_N117=1.17:1；F_N130=…”这类按配方分开写的条件拆开。"""
    out = {}
    for seg in re.split(r"[；;]", text):
        m = re.match(r"\s*([A-Za-z0-9_\-]+)\s*[=＝:：]\s*(.+)", seg)
        if m and m.group(1) in fids:
            out[m.group(1)] = m.group(2)
    return out


def status_of(text: str, cstatus: str, approx: bool = False) -> str:
    if cstatus == "冲突" or re.search(r"冲突|未调和|不一致", text):
        return "⚠️"
    if cstatus == "推定" or re.search(r"推定|估算|换算|假设", text) or approx:
        return "🔶"
    return "✅"


def mid(a, b):
    return (float(a) + float(b)) / 2 if b else float(a)


# ---------- 各字段解析：返回 (值, 状态, 说明) ----------
def p_es(t: str, cst: str):
    t = clean(t)
    m = re.search(rf"E/S\s*(?:ratio)?\s*(?:=|:|为|of|比|is)?\s*(?:约|~|≈|about)?\s*{F}\s*(?:-|~)?\s*{F}?", t)
    if m:
        g = [x for x in m.groups() if x]
        v = mid(g[0], g[1] if len(g) > 1 else None)
        return v, status_of(t, cst, len(g) > 1), "范围取中值" if len(g) > 1 else ""
    m = re.search(rf"(?<![\d.]){F}\s*:\s*1(?![\d.])", t)  # 先认“15:1 μL mg−1”，免得下一条把“1 μL mg”读成 1
    if m:
        return float(m.group(1)), "🔶", "只写比值 x:1，按 μL:mg 硫理解"
    # 11-05：数值＋体积单位＋（electrolyte/电解液）＋质量单位＋（硫），如“20 μL electrolyte mg−1 sulfur”“4.5 mL电解液 g−1硫”
    m = re.search(rf"(?<![\d.:]){F}\s*(?:-|~)?\s*{F}?\s*(μL|uL|mL)[\s_\-(（]*(?:of\s+)?(?:electrolyte|电解液|E\b)?[\s_\-)）]*(?:/|per)?\s*[(（]?\s*(mg|g)[\s_\-(（]*(Li2S|SPAN|SeS2?|Se/S)?", t)
    if m:
        ml_as_ul = m.group(3) == "mL" and bool(re.search(r"疑\s*(?:为\s*)?μL|μL\s*符号疑", t))  # 提取已注“疑μL”（P425）
        v = mid(m.group(1), m.group(2)) * (1000 if m.group(3) == "mL" and not ml_as_ul else 1) / (1000 if m.group(4) == "g" else 1)
        if m.group(5) == "SPAN":
            return None, "⚠️", "按 SPAN 质量给出，未换算成硫"
        if m.group(5) and m.group(5).startswith("Se"):
            return None, "⚠️", "按 Se/S 质量给出，未换算成硫"
        note = "范围取中值" if m.group(2) else ""
        if ml_as_ul:
            return round(v, 3), "🔶", (note + "；原文 mL 提取已注疑为 μL，按 μL").strip("；")
        if m.group(5) == "Li2S":
            return round(v / S_IN_LI2S, 3), "🔶", (note + "；按 Li₂S 质量给出，÷0.698 换算为硫").strip("；")
        return round(v, 3), status_of(t, cst, bool(m.group(2))), note
    m = re.search(rf"(?:S|硫|sulfur)\s*/\s*(?:电解液|electrolyte)[^0-9]{{0,12}}?{F}\s*(?:g\s*/\s*L|g\s*L-1|mg\s*/\s*mL)", t, re.I)
    if m:
        return round(1000 / float(m.group(1)), 3), "🔶", f"原文给硫/电解液 {m.group(1)} g L⁻¹，E/S = 1000 ÷ 该值"
    if re.search(r"mElectrolyte|质量比|weight ratio", t):
        return None, "⚠️", "以电解液/正极质量比给出，未换算成 E/S"
    return None, "未解析", ""


# ---------- E/S 由电解液体积 ÷ 硫质量算（11-05 用户定：同毕设口径） ----------
V_DEFAULT_UL = 50.0   # 论文没写电解液用量时按 50 μL（毕设 文献提取/README“默认值”）
D_DEFAULT_MM = 12.0   # 论文没写极片尺寸时按直径 12 mm（同上）
NOT_REPORTED = re.compile(r"^\s*(?:未报告|未明确|未说明|未给出|不适用)")


def p_volume(t: str):
    """电解液体积（μL）。返回 (值, 说明)；无法唯一确定时值为 None。"""
    t = clean(t)
    if not t or NOT_REPORTED.match(t) or re.search(r"^\s*适量|appropriate (?:volume|amount)|未给数值", t, re.I):
        return None, "未报告"
    nums = [float(x) * (1000 if u == "mL" else 1) for x, u in re.findall(rf"{F}\s*(μL|uL|ul|μl|mL)(?!\s*[/\s]*m?g)", t)]
    if not nums:
        return None, "有文字未解析"
    if re.search(r"未报告|未明确|未说明", t):
        return None, "部分配方体积未报告"
    if "+" in t:
        return sum(nums), "各部分相加"
    if len(set(nums)) == 1:
        return nums[0], ""
    if re.search(r"各|each", t) and nums[0] == 2 * nums[1]:
        return nums[0], "取总量"
    return None, f"多个体积 {nums}"


def p_area(texts: list[str]):
    """极片面积（cm²）：直接写面积，或写直径（mm/cm）。多个不同尺寸时返回 None。"""
    t = clean(" ".join(texts))
    areas = {float(x) for x in re.findall(rf"(?<![\d.]){F}\s*cm\s*(?:\^?2|²)(?![\d])", t)}
    if not areas:
        for m in re.finditer(rf"(?:直径|Φ|φ|ø|⌀|diameter(?:\s+of)?|disc of|圆片)\s*(?:约|为|=|:|of)?\s*{F}\s*(mm|cm)|{F}\s*(mm|cm)\s*(?:直径|diameter|discs?|disks?|圆片|圆盘)", t, re.I):
            d = float(m.group(1) or m.group(3)) * (10 if (m.group(2) or m.group(4)) == "cm" else 1)
            if 5 <= d <= 30:
                areas.add(round(math.pi * (d / 20) ** 2, 4))
    if len(areas) == 1:
        return areas.pop(), "原文"
    return None, ("多个电极尺寸" if areas else "未报告")


def p_smass(t: str):
    """每个电极的硫质量（mg），如“硫重约1.0mg”“每片1.2 mg硫”；面载量（mg cm⁻²）不算。"""
    t = clean(t)
    m = re.search(rf"(?:硫重|硫质量|硫的质量|每片|S mass|sulfur mass|mass of sulfur)\s*(?:约|为|=|:|of)?\s*{F}\s*mg(?!\s*[-\s]*(?:S|sulfur|硫)?\s*(?:/|cm|per))", t, re.I) or \
        re.search(rf"{F}\s*mg\s*(?:硫|sulfur)(?!\s*/?\s*cm)(?![^；;]{{0,6}}cm)", t, re.I)
    return float(m.group(1)) if m else None


def es_from_volume(vol, vol_note, area, area_src, smass, loading, allow_default=True, fmt=None):
    """E/S = 体积 ÷ 硫质量；硫质量 = 原文每片硫质量，或 载量 × 面积。返回 (值, 默认值列表, 说明)。
    allow_default=False：E/S 字段有文字（如质量比）但没解析出来时，不用默认体积，免得盖掉原文信息。
    fmt：电池形式。50 μL、直径 12 mm 是扣式电池的默认值，软包、流动电池不用（P056、P184、P272）；
    扣式电池体积 ≥1 mL 视为 μL 印成 mL（P183“30 mL”），按 μL 计并注明。"""
    dflt, notes = [], []
    coin_only = fmt in ("软包", "流动电池")
    if vol is None:
        if vol_note != "未报告" or not allow_default or coin_only:
            return None, [], f"电解液体积：{vol_note}" + ("（软包/流动电池不用扣式默认值）" if coin_only else "")
        vol = V_DEFAULT_UL
        dflt.append("体积50μL")
    elif fmt == "扣式" and vol >= 1000:
        vol /= 1000
        notes.append("扣式电池原文体积写作 mL，按 μL 计")
    if smass:
        m, how = smass, f"硫 {smass:g} mg"
    elif loading:
        if area is None:
            if area_src != "未报告" or coin_only:
                return None, [], f"极片面积：{area_src}"
            area = round(math.pi * (D_DEFAULT_MM / 20) ** 2, 4)
            dflt.append("直径12mm")
        m, how = loading * area, f"载量 {loading:g} × 面积 {area:g} cm²"
    else:
        return None, [], "缺载量和硫质量"
    notes.insert(0, f"{vol:g} μL ÷ ({how})")
    if dflt:
        notes.append("用了默认值：" + "、".join(dflt) + "（毕设口径）")
    return round(vol / m, 2), dflt, "；".join(notes)


def p_loading(t: str, cst: str, ctx: str = ""):
    t0 = clean(t)
    if re.match(r"\s*0\s*[（(]", t0):
        return 0.0, "✅", "无硫正极"
    m = re.search(rf"{F}\s*(?:±\s*[\d.]+)?\s*(?:-|~)?\s*{F}?\s*(?:±\s*[\d.]+)?\s*mg\s*[-\s]?(S|sulfur|硫|SPAN|Li2S|Se/S)?\s*(?:/|\s|per|[·•∙])?\s*cm", t0)  # 11-05：补“mg·cm−2”（P376）
    if m:
        v = mid(m.group(1), m.group(2))
        tag = (m.group(3) or "")
        note = "范围取中值" if m.group(2) else ""
        st = status_of(t0, cst, bool(m.group(2)))
        if tag == "Se/S":
            r = re.search(r"Se\s*/\s*S\s*=\s*(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)", clean(ctx))
            if r:
                fs = float(r.group(2)) / (float(r.group(1)) + float(r.group(2)))
                return round(v * fs, 3), "🔶", (note + f"；按 Se/S 质量给出，按正极条件 Se:S={r.group(1)}:{r.group(2)} 换算为硫").strip("；")
            return None, "⚠️", "按 Se/S 质量给出，缺 Se:S 比例"
        if re.search(r"Li2S", tag + t0[m.end():m.end() + 12]) or "按Li2S" in t0:
            return round(v * S_IN_LI2S, 3), "🔶", (note + "；按 Li₂S 质量换算为硫（×0.698）").strip("；")
        if tag == "SPAN" or re.search(r"mgSPAN|SPAN复合物\s*[\d.]+\s*mg|非mgS", t0):
            s = re.search(rf"(?:硫|S)\s*(?:约)?\s*{F}\s*wt\.?\s*%|含硫\s*{F}", t0) or re.search(rf"{F}\s*wt\.?\s*%", t0)
            if s:
                frac = float(next(x for x in s.groups() if x)) / 100
                return round(v * frac, 3), "🔶", (note + f"；按 SPAN 含硫 {frac:.1%} 换算为硫").strip("；")
            return None, "⚠️", "按 SPAN 复合物质量给出，缺含硫量"
        return round(v, 3), st, note
    m = re.search(rf"{F}\s*mg\s*S\s*/\s*电极.*?面积\s*{F}\s*cm", t0)
    if m:
        return round(float(m.group(1)) / float(m.group(2)), 3), "🔶", "每电极硫质量÷电极面积"
    return None, "未解析", ""


def p_li(t: str, cst: str):
    t = clean(t)
    m = re.search(rf"{F}\s*mm[（(][^）)]*疑\s*μm", t)
    if m:
        return float(m.group(1)), "🔶", "原文写 mm，按 μm 理解（提取已注“疑μm”）"
    m = re.search(rf"{F}\s*(?:μm|um|微米)", t)
    if m:
        return float(m.group(1)), status_of(t, cst), ""
    return None, "未解析", ""


def p_np(texts: list[str], fid: str | None):
    for t in texts:
        t = clean(t)
        if fid:
            m = re.search(rf"{re.escape(fid)}\s*[=＝]\s*{F}\s*:\s*1", t)
            if m:
                return float(m.group(1)), "✅", "按配方分开写"
        m = re.search(rf"[Nn]\s*/\s*[Pp]\s*(?:=|:|为|比|ratio)?\s*(?:约)?\s*{F}(?:\s*:\s*1)?", t)
        if m:
            return float(m.group(1)), status_of(t, ""), ""
    return None, "未报告", ""


def p_rate(t: str, cst: str, oneC: str):
    t = clean(t)
    rates = re.findall(rf"(?<![\d.]){F}\s*C(?![a-zA-Z°])", t) + [str(round(1 / float(x), 4)) for x in re.findall(rf"(?<![°℃])(?<!°\s)C\s*/\s*{F}", t)
                                                                 if float(x) > 0]  # 11-05：同 step13a，°C/ 是温度
    rates = sorted({float(x) for x in rates})
    if len(rates) == 1:
        return rates[0], status_of(t, cst), ""
    if len(rates) > 1:
        return None, "⚠️", f"多个倍率 {rates}，以取值点为准"
    m = re.search(rf"{F}\s*A\s*/?\s*g", t) or re.search(rf"{F}\s*mA\s*/?\s*g", t)
    if m:
        cur = float(m.group(1)) * (1000 if "A" in m.group(0) and "mA" not in m.group(0) else 1)
        one = re.search(rf"{F}\s*mA?\s*h?\s*g", clean(oneC))
        base = float(one.group(1)) if one else 1672
        return round(cur / base, 3), "🔶", f"电流 {cur:g} mA g⁻¹ ÷ 1C({base:g}) 换算"
    return None, "未解析", ""


def p_current(t: str):
    t = clean(t)
    m = re.search(rf"{F}\s*mA\s*cm", t)
    if m:
        return float(m.group(1)), "✅", ""
    m = re.search(rf"{F}\s*μA\s*cm", t)
    if m:
        return float(m.group(1)) / 1000, "✅", "μA cm⁻² 换算"
    return None, "未解析", ""


def p_temp(t: str, cst: str):
    t = clean(t)
    m = re.search(rf"(-?\d+(?:\.\d+)?)\s*(?:±\s*[\d.]+\s*)?°\s*C", t)
    if m:
        return float(m.group(1)), status_of(t, cst), ""
    m = re.search(r"(\d{3})\s*K\b", t)
    if m:
        return float(m.group(1)) - 273.15, status_of(t, cst), "K 换算"
    if re.search(r"室温|room temperature|\bRT\b|ambient", t, re.I):
        return 25.0, "🔶", "“室温”按 25 °C"
    return None, "未解析", ""


def p_format(texts: list[str]):
    t = " ".join(texts)
    if re.search(r"软包|pouch", t, re.I):
        return "软包", "✅"
    if re.search(r"扣式|coin|CR20|20[0-9]{2}型|20[0-9]{2}\s*扣", t, re.I):
        return "扣式", "✅"
    if re.search(r"Swagelok|三电极|模具", t, re.I):
        return "其他", "✅"
    return None, "未报告"


# ---------- 正极硫含量（极片基准） ----------
RATIO = r"(\d+(?:\.\d+)?)\s*[:：]\s*(\d+(?:\.\d+)?)" + r"(?:\s*[:：]\s*(\d+(?:\.\d+)?))?" * 4  # 11-05：最多 6 项（P185 S8:Mo6S8:CNTs:GNs:CMC:SBR）


def p_sulfur_content(t: str):
    """返回 (极片含硫 %, 状态, 计算式)。规则见方案 §8.7：
    直接写极片含硫 → 直接用；复合物含硫 × 复合物在浆料中的占比；只有复合物含硫无浆料配比 → 缺失。"""
    t = clean(t)
    # 1) 浆料第一项就是硫本身：S:SuperP:PVDF=70:20:10、硫/Super P/PVDF=70:20:10
    # 11-05 修正：只认至少三项、且名称个数与比例个数相同的配比。原规则把复合物投料比（S:MWCNT=4:1）
    # 和以复合物开头的浆料（S/C:乙炔黑:PVDF=7:2:1）也当成极片配比，漏乘第二步（P001、P276、P350 等）
    m = re.search(r"(?<![A-Za-z@/\-一-鿿])(?:S8?|硫|[Ss]ulfur)\s*[:/]\s*[A-Za-z一-鿿][^=＝；;]{0,40}?(?:=|质量比|比)\s*" + RATIO, t)
    if m:
        parts = [float(x) for x in m.groups() if x]
        names = re.split(r"\s*[:/：]\s*", re.split(r"\s*(?:=|质量比|比)\s*", m.group(0))[0].strip())
        if len(parts) >= 3 and len(names) == len(parts):
            return round(parts[0] / sum(parts) * 100, 2), "✅", f"浆料直接写硫：{m.group(0)}"
    # 2) 复合物含硫
    fc, how = None, ""
    for pat in (rf"(?:含硫|硫含量|S含量|sulfur content|中硫)\s*(?:约|为|=|:)?\s*{F}\s*(?:±\s*[\d.]+\s*)?(?:wt\.?\s*%|%)",
                rf"{F}\s*(?:±\s*[\d.]+\s*)?(?:wt\.?\s*%|%)\s*(?:的)?\s*(?:硫|S\b|sulfur|Se/S)",
                rf"{F}\s*(?:±\s*[\d.]+\s*)?wt\.?\s*%\s*S"):
        mm = re.search(pat, t, re.I)
        if mm:
            fc, how = float(mm.group(1)) / 100, f"复合物含硫 {mm.group(0)}"
            break
    if fc is None:
        mm = re.search(rf"([A-Za-z\-]+)\s*:\s*S\s*=\s*{F}\s*:\s*{F}", t) or re.search(rf"(?<![A-Za-z])S\s*:\s*([A-Za-z\-]+)\s*=\s*{F}\s*:\s*{F}", t)
        if mm:
            a, b = float(mm.group(2)), float(mm.group(3))
            fc = (b if mm.re.pattern.startswith("([") else a) / (a + b)
            how = f"复合物投料比 {mm.group(0)}"
        mm2 = re.search(rf"{F}\s*mg\s*S\s*\+\s*{F}\s*mg\s*C", t)
        if mm2:
            fc = float(mm2.group(1)) / (float(mm2.group(1)) + float(mm2.group(2)))
            how = f"复合物投料 {mm2.group(0)}"
    # 3) 复合物在浆料中的占比
    fs, how2 = None, ""
    mm = re.search(rf"{F}\s*wt\.?\s*%\s*(?:活性物|活性材料|复合物|active)", t)
    if mm:
        fs, how2 = float(mm.group(1)) / 100, mm.group(0)
    else:
        for mm in re.finditer(r"([A-Za-z0-9@/\-]+(?:/S|-S|@S|S\d*|SPAN|复合物)[A-Za-z0-9@\-]*)\s*[:：][^=＝；;]{0,40}?(?:=|＝)\s*" + RATIO, t):
            parts = [float(x) for x in mm.groups()[1:] if x]
            fs, how2 = parts[0] / sum(parts), mm.group(0)
            break
        if fs is None:
            mm = re.search(r"复合物\s*[:：]\s*[^=＝]{0,20}?=\s*" + RATIO, t)
            if mm:
                parts = [float(x) for x in mm.groups() if x]
                fs, how2 = parts[0] / sum(parts), mm.group(0)
    if fc is not None and fs is not None:
        return round(fc * fs * 100, 2), "✅", f"{how} × 浆料占比（{how2}）"
    if fc is not None:
        return None, "缺浆料配比", how
    return None, "未解析", ""


def main() -> None:
    papers = load_papers()
    cls = read_json("结果归类.json")
    perf_tests = {(r["论文"], r["测试"]) for r in cls if r["性能类别"] != "不进四类"}
    manual = {}
    mf = OUT / "正极硫含量核定.json"
    if mf.exists():
        manual = json.loads(mf.read_text(encoding="utf-8"))
    ef = OUT / "E_S核定.json"  # 11-05：Claude 读原文写的 E/S 核定（键 = 论文|测试），优先于解析和计算
    es_manual = json.loads(ef.read_text(encoding="utf-8")) if ef.exists() else {}
    rows, cath_rows = [], {}
    for pid, d in papers.items():
        cd = d["condition_definitions"]
        fids = {f["id"] for f in d["formulations"]}
        for t in d["tests"]:
            if (pid, t["id"]) not in perf_tests:
                continue
            refs = t["condition_refs"]

            def get(f):
                c = cd.get(refs.get(f, ""), {})
                return c.get("value", "未报告") if c else "未报告", c.get("status", "未报告") if c else "未报告", refs.get(f, "")

            row = {"论文": pid, "测试": t["id"], "测试名": t.get("name", ""), "测试类型": t["kind"], "电池": t.get("cell", ""),
                   "配方": t.get("formulations", [])}
            spec = {}
            cath_txt = get("cathode")[0]
            for field, fn in (("ES", p_es), ("sulfur_loading", lambda x, c: p_loading(x, c, cath_txt)), ("Li_thickness", p_li),
                              ("temperature", p_temp)):
                txt, cst, ref = get(field)
                if cst == "未报告" or txt == "未报告":
                    spec[field] = {"值": None, "状态": "未报告", "原文": txt, "条件编号": ref}
                    continue
                pf = per_formulation(txt, fids)
                if pf:
                    spec[field] = {"按配方": {k: dict(zip(("值", "状态", "说明"), fn(v, cst))) for k, v in pf.items()},
                                   "值": None, "状态": "按配方", "原文": txt, "条件编号": ref}
                else:
                    v, st, note = fn(txt, cst)
                    spec[field] = {"值": v, "状态": st, "说明": note, "原文": txt, "条件编号": ref}
            # 温度：原文没写（未报告）的按室温 25 °C（11-05 用户定），标记为默认值；有文字没解析出的不套
            if spec["temperature"]["值"] is None and spec["temperature"]["状态"] == "未报告":
                spec["temperature"].update({"值": 25.0, "状态": "🔶", "说明": "原文未写温度，按室温 25 °C（11-05 用户定）", "默认": ["室温25°C"]})
            # E/S：原文没给就按 电解液体积 ÷ 硫质量 算；计算用料存下来，step13c 用取值点载量时重算
            es = spec["ES"]
            es["来源"] = "原文" if es["值"] is not None or es["状态"] == "按配方" else None
            if es["来源"] is None:
                vol, vnote = p_volume(get("electrolyte_volume")[0])
                area, asrc = p_area([get(f)[0] for f in ("electrodes", "cathode", "sulfur_loading", "cell_format")]
                                    + [t.get("cell", ""), t.get("name", "")])
                ftxt = [get("cell_format")[0], t.get("cell", ""), t.get("name", "")]
                fmt = "流动电池" if re.search(r"流动电池|flow (?:cell|battery)", " ".join(ftxt), re.I) else p_format(ftxt)[0]
                es["计算"] = {"体积μL": vol, "体积说明": vnote, "面积cm2": area, "面积来源": asrc,
                              "硫质量mg": p_smass(get("sulfur_loading")[0]), "可用默认": es["状态"] == "未报告", "电池形式": fmt}
                c_ = es["计算"]
                v, dflt, note = es_from_volume(c_["体积μL"], vnote, area, asrc, c_["硫质量mg"], spec["sulfur_loading"]["值"],
                                               c_["可用默认"], fmt)
                if v is not None:
                    es.update({"值": v, "状态": "🔶", "说明": note, "默认": dflt, "来源": "体积÷硫质量"})
                else:
                    es["说明"] = note
            m = es_manual.get(f"{pid}|{t['id']}")
            if m:
                es.update({"值": m["值"], "状态": m["状态"], "说明": m["说明"], "默认": m.get("默认", []), "来源": "人工核定",
                           "依据": m.get("依据", [])})
            txt, cst, ref = get("rate")
            one, _, _ = get("one_C")
            if cst == "未报告":
                spec["rate"] = {"值": None, "状态": "未报告", "原文": txt, "条件编号": ref}
            else:
                v, st, note = p_rate(txt, cst, one)
                spec["rate"] = {"值": v, "状态": st, "说明": note, "原文": txt, "条件编号": ref}
            if t["kind"] == "锂铜效率" or "Cu" in t.get("cell", ""):
                cur = p_current(txt)
                ac, _, _ = get("areal_capacity")
                capm = re.search(rf"{F}\s*mAh\s*cm", clean(ac + " " + txt))
                spec["current"] = {"值": cur[0], "状态": cur[1] if cur[0] is not None else "未报告", "原文": txt}
                spec["Li_Cu_capacity"] = {"值": float(capm.group(1)) if capm else None,
                                          "状态": "✅" if capm else "未报告", "原文": ac}
            np_texts = [get(f)[0] for f in ("areal_capacity", "Li_thickness", "other", "lithium_reservoir")] + [t.get("name", "")]
            spec["NP"] = {"按配方": {f: dict(zip(("值", "状态", "说明"), p_np(np_texts, f))) for f in t.get("formulations", [])}}
            vals = {k: v for k, v in spec["NP"]["按配方"].items() if v["值"] is not None}
            spec["NP"]["值"] = next(iter(vals.values()))["值"] if len({v["值"] for v in vals.values()}) == 1 else None
            spec["NP"]["状态"] = ("✅" if spec["NP"]["值"] is not None else "按配方" if vals else "未报告")
            fmt_texts = [get("cell_format")[0], t.get("cell", ""), t.get("name", "")]
            fv, fst = p_format(fmt_texts)
            spec["cell_format"] = {"值": fv, "状态": fst, "原文": get("cell_format")[0]}
            # 正极
            ctxt, cst, cref = get("cathode")
            key = f"{pid}|{cref}"
            if cref and key not in cath_rows:
                v, st, how = p_sulfur_content(ctxt) if cst != "未报告" else (None, "未报告", "")
                m = manual.get(key)
                cath_rows[key] = {"论文": pid, "条件编号": cref, "原文": ctxt, "解析值": v, "解析状态": st, "解析式": how,
                                  "核定值": m.get("值") if m else None, "核定状态": m.get("状态") if m else None,
                                  "核定说明": m.get("说明") if m else None, "依据": m.get("依据") if m else None,
                                  "核定按配方": m.get("按配方") if m else None,
                                  "解析与核定一致": (None if not m else (v is not None and m.get("值") is not None and abs(v - m["值"]) < 0.05)
                                               or (v is None and m.get("值") is None))}
            c = cath_rows.get(key, {})
            if c.get("核定状态"):
                spec["S_content"] = {"值": c["核定值"], "状态": c["核定状态"], "说明": c["核定说明"], "原文": ctxt, "条件编号": cref}
                if c.get("核定按配方"):
                    spec["S_content"]["按配方"] = c["核定按配方"]
            else:
                spec["S_content"] = {"值": c.get("解析值"), "状态": c.get("解析状态", "未报告"), "说明": c.get("解析式", ""),
                                     "原文": ctxt, "条件编号": cref}
            ct = next((r["正极类型"] for r in cls if r["论文"] == pid and r["测试"] == t["id"]), None)
            spec["cathode_type"] = {"值": ct}
            row["条件"] = spec
            rows.append(row)
    write_json("条件表.json", rows)
    cath = list(cath_rows.values())
    write_json("正极硫含量解析.json", cath)

    names = {"ES": "E/S (μL mg⁻¹ S)", "sulfur_loading": "硫面载量 (mg cm⁻²)", "S_content": "正极硫含量 (极片 wt%)",
             "Li_thickness": "锂厚 (μm)", "NP": "N/P", "rate": "倍率 (C)", "temperature": "温度 (°C)",
             "cell_format": "电池形式", "current": "Li‖Cu 电流 (mA cm⁻²)", "Li_Cu_capacity": "Li‖Cu 容量 (mAh cm⁻²)"}
    stat = {k: Counter(r["条件"][k]["状态"] for r in rows if k in r["条件"]) for k in names}
    summary = {"性能测试数": len(rows), "各条件状态": {names[k]: dict(v) for k, v in stat.items()},
               "正极条件文字种数": len(cath),
               "正极硫含量：解析状态": dict(Counter(c["解析状态"] for c in cath)),
               "正极硫含量：核定状态": dict(Counter(c["核定状态"] for c in cath if c["核定状态"])),
               "正极硫含量：解析与核定一致": dict(Counter(str(c["解析与核定一致"]) for c in cath))}
    write_json("step13b_汇总.json", summary)

    def cell(r, k):
        c = r["条件"].get(k)
        if not c:
            return "", "", ""
        if c.get("按配方") and c.get("值") is None:
            return "；".join(f"{f}={x['值']}" for f, x in c["按配方"].items() if x["值"] is not None) or "", c["状态"], c.get("原文", "")
        return c.get("值"), c.get("状态"), c.get("原文", "")

    header = ["论文", "测试", "测试名", "测试类型", "配方"]
    for k in names:
        header += [names[k], "状态", "原文"] if k in ("ES", "sulfur_loading", "S_content", "rate", "temperature") else [names[k], "状态"]
    body = []
    for r in rows:
        line = [r["论文"], r["测试"], r["测试名"], r["测试类型"], r["配方"]]
        for k in names:
            v, s, o = cell(r, k)
            line += [v, s, o] if k in ("ES", "sulfur_loading", "S_content", "rate", "temperature") else [v, s]
        body.append(line)
    write_xlsx(OUT / "条件表.xlsx", [
        ("条件表", header, body),
        ("正极硫含量核对", ["论文", "条件编号", "原文", "解析值", "解析状态", "解析式", "核定值", "核定状态", "核定说明", "核定按配方", "依据", "解析与核定一致"],
         [[c[k] for k in ["论文", "条件编号", "原文", "解析值", "解析状态", "解析式", "核定值", "核定状态", "核定说明", "核定按配方", "依据", "解析与核定一致"]] for c in cath]),
    ], widths={"原文": 40, "测试名": 22, "解析式": 40, "核定说明": 40, "依据": 30},
        notes=[f"step13b 测试条件表｜{LABEL}｜2026-11-04 生成",
               "只整理有四类性能数值的测试；条件文字来自提取结果 condition_definitions，原文列照抄。",
               "状态：✅ 原文直接写明（含“约”）；🔶 有换算或推定（室温按 25 °C、按 Li₂S/SPAN 换算硫、x:1 比值等）；⚠️ 冲突或多值；未报告 = 原文没写。",
               "正极硫含量按方案 §8.7：直接写极片含硫的直接用；复合物含硫 × 复合物在浆料中的占比；只有复合物含硫、没有浆料配比的记缺失。",
               "正极硫含量核对页：解析值由脚本正则得出，核定值由 Claude 读原文写入 正极硫含量核定.json，有核定值时以核定值为准。",
               "取值点里写的倍率、温度、载量（如 P451“−20 °C”、P156“3.02 mg cm⁻²”）在表述表中覆盖本表的测试级条件。"])
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
