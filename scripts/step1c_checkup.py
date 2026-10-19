"""第 1 步 c：669 篇零成本体检（正则，不调 LLM）。

读 output/text_cache（step1a）与 output/abstracts.json（step1b），输出：
  output/第1步_体检表.xlsx   汇总 + 逐篇（每格带原句，✅ 有本文自述证据 / 🔶 只有泛泛提及或来源存疑 / ❌ 没提到）
  output/step1_rows.pkl       逐篇结果（给验证脚本与后续步骤用）

判"本文自述"的规则：实验部分、SI 里的命中直接算；其余正文要求句子带 we/our/Fig/cells were… 等自述标志，
且不是"应当/实用要求/文献报道"这类泛泛说法。参考文献区整段切掉，像参考文献的上下文丢弃。
"""
import json
import os
import re
import sys

import pandas as pd

LIB = r"D:\Desktop\锂电催化\机器学习\skills\Open-Papertrail\Open-Papertrail\corpus\library"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "output", "text_cache")
OUT_XLSX = os.path.join(ROOT, "output", "第1步_体检表.xlsx")
OUT_PKL = os.path.join(ROOT, "output", "step1_rows.pkl")

NUM = r"(\d+(?:\.\d+)?)"

# ---------------------------------------------------------------- 文本预处理


def norm(t):
    t = (t.replace("μ", "µ").replace("\u2212", "-").replace("\u2013", "-").replace("\u2010", "-")
         .replace("\u2011", "-").replace("\u00a0", " ").replace("\u2009", " ").replace("\u202f", " ")
         .replace("ﬁ", "fi").replace("ﬂ", "fl").replace("\u00ad", "").replace("·", " ").replace("⋅", " ")
         .replace("‖", "||").replace("∥", "||"))
    t = re.sub(r"<<PAGE \d+>>", " ", t)
    t = re.sub(r"\s+", " ", t)
    # Elsevier 等 PDF 的 µ 常被识别成 l（"200 lm thick"、"5 lL mg"），数字后的 lm/lL 不会是别的单位
    t = re.sub(r"(\d)\s*l([mL])\b", r"\1 µ\2", t)
    return t


HEAD_REF = re.compile(r"\n\s*(?:References?(?: and [Nn]otes)?|REFERENCES?|Notes and references|Literature [Cc]ited)\s*\n")
HEAD_EXP = re.compile(
    r"\n\s*(?:\d+(?:\.\d+)*\.?\s*)?(?:Experimental(?: [Ss]ection| [Pp]rocedures?| [Mm]ethods?| [Dd]etails)?|EXPERIMENTAL(?: SECTION| PROCEDURES?)?"
    r"|Methods?|METHODS?|Materials and [Mm]ethods|MATERIALS AND METHODS|Experimental [Ss]ection)\s*\n")
HEAD_END = re.compile(
    r"\n\s*(?:\d+\.?\s*)?(?:Results(?: and [Dd]iscussion)?|RESULTS(?: AND DISCUSSION)?|Conclusions?|CONCLUSIONS?|Acknowledg|ACKNOWLEDG"
    r"|Supporting Information|ASSOCIATED CONTENT|Author [Cc]ontributions|AUTHOR INFORMATION|Conflicts? of [Ii]nterest"
    r"|Declaration of|Data [Aa]vailability|CRediT|References?\s*\n|REFERENCES?)")
HEAD_ELECTROCHEM = re.compile(
    r"\n\s*(?:\d+(?:\.\d+)*\.?\s*)?(?:Electrochemical (?:[Mm]easurements?|[Cc]haracteri[sz]ations?|[Tt]ests?|[Ee]valuations?)"
    r"|(?:Coin |Pouch |Battery |Cell )?(?:[Cc]ell|[Bb]attery) [Aa]ssembl(?:y|ies)(?: and [^\n]{0,40})?)\s*\n")


def zones(raw_main):
    """返回 (实验部分文本, 其余正文文本)，均已切掉参考文献区并归一化。"""
    t = raw_main
    cut = None
    for m in HEAD_REF.finditer(t):
        if m.start() > 0.4 * len(t):
            cut = m.start()
    if cut:
        t = t[:cut]
    spans = []
    m = HEAD_EXP.search(t)
    if m:
        e = HEAD_END.search(t, m.end() + 200)
        spans.append((m.start(), e.start() if e else len(t)))
    for m in HEAD_ELECTROCHEM.finditer(t):
        spans.append((m.start(), min(len(t), m.end() + 4000)))
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(e, merged[-1][1]))
        else:
            merged.append((s, e))
    exp = " ".join(t[s:e] for s, e in merged)
    rest, last = [], 0
    for s, e in merged:
        rest.append(t[last:s])
        last = e
    rest.append(t[last:])
    return norm(exp), norm(" ".join(rest))


def pdf_abstract(raw_main):
    t = raw_main[:20000]
    m = re.search(r"(?:Abstract|ABSTRACT|A B S T R A C T|Summary|SUMMARY)\s*[:.]?\s*", t)
    if m:
        return norm(t[m.end():m.end() + 2000])
    return norm(t[:3000])


# ---------------------------------------------------------------- 上下文判定

OWN = re.compile(
    r"\b(?:we|our|this work|herein|here|in this study|in this work|the as-prepared|assembled|was (?:set|fixed|controlled|used|added|kept|maintained|injected)"
    r"|were (?:set|fixed|controlled|used|added|kept|maintained|injected|assembled|tested|cycled)|cells? (?:with|using|employing|were|was)"
    r"|Fig(?:ure)?s?\.?\s*S?\d|Table\s*S?\d)\b", re.I)
GENERIC = re.compile(
    r"\b(?:should|must|needs? to|required?|requirements?|practical (?:applications?|requirements?|targets?)|commerciali[sz]\w*|target(?:s|ed)?"
    r"|reported|previous(?:ly)?|literature|most (?:studies|works|reports|research)|typically|generally|usually|state-of-the-art|recent(?:ly)?)\b", re.I)
STRONG_OWN = re.compile(r"\b(?:we|our|this work|herein|in this (?:study|work)|assembled|Fig(?:ure)?s?\.?\s*S?\d)\b", re.I)
# 能量密度测算、参数假设、模拟里的 E/S、N/P 不是实测条件
CALC = re.compile(r"\bproject(?:ed|ion)s?\b|calculat|estimat|simulat|assum|\bmodel(?:ed|ing)?\b|Parameters of|energy density vs|we predict|hypothetical|target(?:ed)? (?:cell|value)", re.I)
REF_LIKE = re.compile(r"\bet al\.|doi:|doi\.org|\b(?:19|20)\d{2},\s*\d+\s*[,:(]|\b(?:19|20)\d{2}\)\s*\d+")
CITE_NEAR = re.compile(r"\[\d+(?:[,-]\s*\d+)*\]|\bRefs?\.\s*\d|\bRef\b")


def ctx(text, s, e, w=150):
    return text[max(0, s - w):min(len(text), e + w)]


def tier(zone, text, s, e):
    """A=实验部分/SI；B=正文自述；C=泛泛/存疑；None=像参考文献，丢弃"""
    c = ctx(text, s, e, 120)
    if REF_LIKE.search(c):
        return None
    if CALC.search(ctx(text, s, e, 100)):
        return "C"
    if zone == "EXP":
        return "A"
    if zone == "SI":
        return "C" if CITE_NEAR.search(ctx(text, s, e, 80)) else "A"
    sent = ctx(text, s, e, 160)
    if STRONG_OWN.search(sent):
        return "B"
    if OWN.search(sent) and not GENERIC.search(sent):
        return "B"
    return "C"


def find_all(pattern, zones_, value_fn=None, flags=re.I, vmin=None, vmax=None):
    """在各区里找匹配，返回 [(tier, value, snippet)]"""
    out = []
    for zone, text in zones_:
        for m in re.finditer(pattern, text, flags):
            t = tier(zone, text, m.start(), m.end())
            if t is None:
                continue
            v = value_fn(m) if value_fn else None
            if v is not None and ((vmin is not None and v < vmin) or (vmax is not None and v > vmax)):
                continue
            out.append((t, v, f"[{zone}] …{ctx(text, m.start(), m.end(), 110)}…"))
    return out


def summarize(hits, agg=min):
    """✅ 有 A/B 档；🔶 只有 C 档；❌ 没有。返回 (标记, 代表值, 值列表, 原句)"""
    own = [h for h in hits if h[0] in ("A", "B")]
    use = own or hits
    if not use:
        return "❌", None, "", ""
    vals = sorted({h[1] for h in use if h[1] is not None})
    rep = agg(vals) if vals else None
    # 原句：优先放代表值所在句，最多 2 句
    snips = [h[2] for h in use if h[1] == rep][:1] + [h[2] for h in use if h[1] != rep][:1]
    return ("✅" if own else "🔶"), rep, ", ".join(f"{v:g}" for v in vals[:12]), "\n".join(snips)


def fv(m, g=1):
    try:
        return float(m.group(g))
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- 各字段的正则

ES_TERM = r"(?:E\s*/\s*S|E\s*:\s*S|E\s*/\s*Li2S|electrolyte[\s-]*(?:/|to[\s-]*)\s*(?:sul(?:f|ph)ur|Li2S|active material)(?:\s*\(E/S\))?)"
# µ 常被 PDF 乱码成 m（"28 mL mg1"），"mL mg" 在锂硫文献里只会是 E/S
ES_UNIT = r"(?:µ\s*[lL]|u[lL]|m[lL](?=\s*(?:/\s*|per\s*)?mg))\s*(?:/\s*|per\s*)?mg\s*(?:\(\s*S\s*\)|S\b|sulfur|sulphur|-?S\b)?"
ES_UNIT2 = r"m[lL]\s*(?:/\s*)?g\s*(?:\(\s*S\s*\)|S\b|sulfur|sulphur)?\s*-?\s*1"
P_ES_UNIT = NUM + r"\s*" + ES_UNIT
P_ES_TERM = ES_TERM + r"\s*(?:ratios?|values?|of|=|:|is|was|were|as low as|as lean as|down to|reduced to|\(|~|≈|≤|<|\s)*\s*" + NUM + r"(?!\s*(?:wt|%|mg\s*cm|mAh|C\b|°|h\b|M\b|:\s*1))"
P_ES_UNIT2 = ES_TERM + r"[^.;]{0,40}?" + NUM + r"\s*" + ES_UNIT2
P_EL_AMOUNT = NUM + r"\s*(?:µ\s*[lL]|u[lL])\b(?!\s*(?:/\s*|per\s*)?mg)(?:\s*(?:of\s*)?(?:the\s*)?(?:[\w-]+\s*){0,3}(?:electrolytes?|catholytes?))"
P_EL_AMOUNT2 = r"(?:electrolytes?|catholytes?)\b[^.;]{0,30}?(?:amount|volume|of|was|were|\()\s*[^.;]{0,15}?" + NUM + r"\s*(?:µ\s*[lL]|u[lL])\b(?!\s*(?:/\s*|per\s*)?mg)"

LI_TERM = r"(?:Li|lithium)(?:\s*\(Li\))?(?:\s*metal)?\s*(?:foils?|chips?|disks?|discs?|sheets?|anodes?|ribbons?|strips?|plates?|tapes?|electrodes?|belts?|counter electrodes?)"
LI_ADJ = r"(?:(?:metallic|commercial|pure|bare|fresh|pristine|(?:ultra-?)?thin|thick|high-purity|limited|double-sided|single-sided|rolled)\s+){0,2}"
P_LI1 = NUM + r"\s*-?\s*µm[\s-]*(?:thick(?:ness)?|thin)?[\s-]*(?:of\s*)?" + LI_ADJ + LI_TERM
P_LI2 = NUM + r"\s*-?\s*µm[\s-]*(?:thick[\s-]*|thin[\s-]*)?(?:Li|lithium)(?![\w+])"
P_LI3 = LI_TERM + r"\s*\(\s*[^()]{0,40}?" + NUM + r"\s*µm"  # "Li anode (~ 450 µm)"、"(signal side with 50 µm)"
P_LI8 = r"(?:Li|lithium)(?:\s*metal)?\s*(?:foil\s*|anode\s*)?thickness\s*(?:of|:|=|is|was|\()?\s*(?:about|approximately|~|≈)?\s*" + NUM + r"\s*(µm|mm)"
NOEND = r"(?:[^.;]|\.(?=\d))"  # 句内字符：数字里的小数点（"99.9%"）不算句末
P_LI4 = LI_TERM + NOEND + r"{0,50}?thick(?:ness)?\s*(?:of|:|=|is|was|\()?\s*(?:about|approximately|~)?\s*" + NUM + r"\s*(µm|mm)"
P_LI5 = LI_TERM + NOEND + r"{0,50}?" + NUM + r"\s*(µm|mm)\s*(?:in\s*)?(?:thick(?:ness)?)"
# 直径 × 厚度（"Ф15.6 × 1.0 mm"）；厚度写在前（"thickness of the Li foil was 50 µm"，不收 "has decreased from"）
P_LI6 = LI_TERM + NOEND + r"{0,60}?(?:Φ|Ф|ϕ|φ|Ø|diameter(?: of)?)\s*:?\s*\d+(?:\.\d+)?\s*(?:mm)?\s*[×x*]\s*" + NUM + r"\s*(µm|mm)"
P_LI7 = (r"thick(?:ness)?\s*of\s*(?:the\s*)?(?:fresh\s*|pristine\s*|initial\s*|bare\s*)?" + LI_TERM
         + r"\s*(?:is|was|were|of|:|=|\()?\s*(?:about|approximately|~|≈)?\s*" + NUM + r"\s*(µm|mm)")
P_NP = r"\b(?:N\s*/\s*P|n\s*/\s*p|negative[\s-]*(?:to|/)[\s-]*positive)(?:\s*\(N/P\))?\s*(?:capacity\s*)?(?:ratios?|values?)?\s*(?:of|=|:|is|was|were|≈|~|around|about|approximately|as low as|\()*\s*" + NUM
P_NP2 = NUM + r"\s*(?:N\s*/\s*P|n\s*/\s*p)\b"
P_LIEX = NUM + r"\s*%\s*(?:Li|lithium)\s*excess|excess (?:Li|lithium)\s*(?:of\s*)?" + NUM + r"\s*%"
P_ANODEFREE = r"anode[\s-]*(?:free|less)|Cu\s*\|\|\s*(?:S|Li2S|SPAN)|(?:Li|lithium)[\s-]*free anode"

P_LOAD = NUM + r"\s*mg\s*(?:\(\s*S\s*\)|S\b|sulfur|sulphur|of sulfur|-?S\b)?\s*(?:/\s*cm\s*2|cm\s*-?\s*2\b|per\s*cm\s*2|cm\^-2)"
LOAD_CTX = re.compile(r"load|sulfur|sulphur|\bS\b", re.I)

P_LINO3 = r"LiNO\s*3|lithium nitrate"
P_LINO3_C1 = NUM + r"\s*(wt\s*\.?\s*%|%|M\b|mol\s*/?\s*L|mol\s*L\s*-?1|mM)\s*(?:of\s*)?(?:LiNO\s*3|lithium nitrate)"
P_LINO3_C2 = r"(?:LiNO\s*3|lithium nitrate)\s*\(\s*" + NUM + r"\s*(wt\s*\.?\s*%|%|M\b|mM)"
P_LINO3_FREE = r"(?:without|free of|absence of|\bno|w/o)\s+(?:the\s+|any\s+)?(?:LiNO\s*3|lithium nitrate)|(?:LiNO\s*3|nitrate)[\s-]*free"

T_CTX = re.compile(r"cycl|test|operat|discharg|charg|capacit|perform|\bcells?\b|batter", re.I)
T_BAD_LOW = re.compile(r"stor|freez|DSC|glass transition|melting|melt|boil|flash point|liquid range|cool(?:ed|ing) to", re.I)
T_BAD_HIGH = re.compile(r"dr(?:y|ied|ying)|vacuum|oven|anneal|heat(?:ed|ing)|stirr|calcin|synthes|reflux|overnight|\bh\b|hours?|solution|mix|polymeri[sz]|cur(?:e|ing)|evaporat|ag(?:ed|ing)|stored?|soak|hot plate|water bath|dissolv", re.I)
P_LOWT = r"(?:^|[\s(,;:~])-\s?(\d{1,2})\s*°\s*C"
P_HIGHT = r"\b(4[5-9]|[5-9]\d|1[0-2]\d)\s*°\s*C"

P_CELL = r"coin[\s-]*cells?|CR\s*20\d\d|pouch[\s-]*cells?|Swagelok|galvanostatic(?:ally)?\s*(?:charge|discharge|cycl)|cycling (?:performance|stability)|charge[\s/-]*discharge"
P_POUCH = r"pouch[\s-]*cells?|pouch[\s-]*type"
P_AH = r"(?<![\d.])" + NUM + r"\s*-?\s*Ah\b(?![\s-]*(?:g|kg|L|cm))"
P_LICU = r"Li\s*(?:\|\||/|\||-|//)\s*Cu\b|Cu\s*(?:\|\||/|\||-|//)\s*Li\b|Li[\s-]+Cu (?:half[\s-]*)?cells?|Aurbach"
P_PSSOL = r"solubilit(?:y|ies)[^.;]{0,80}?\d+(?:\.\d+)?\s*(?:mM|M\b|mmol|mol\s*L|g\s*L|mg\s*mL|mg\s*/\s*mL)|(?:Li2S\s*\d|Li2S[468x]|polysulfides?|LiPSs?)[^.;]{0,40}?solubilit"
P_SOLV = r"molecular dynamics|\bMD\b simulations?|radial distribution|\bRDF\b|Raman|solvation (?:structure|sheath)"
P_BASE = (r"1(?:\.0)?\s*M\s*LiTFSI[^.;]{0,60}?(?:DOL|1,3-dioxolane|dioxolane)[^.;]{0,30}?(?:DME|dimethoxyethane)"
          r"|(?:DOL|1,3-dioxolane)\s*(?:/|and|:|-|\+)\s*(?:DME|1,2-dimethoxyethane)[^.;]{0,60}?1(?:\.0)?\s*M\s*LiTFSI"
          r"|(?:DME|1,2-dimethoxyethane)\s*(?:/|and|:|-|\+)\s*(?:DOL|1,3-dioxolane)[^.;]{0,60}?1(?:\.0)?\s*M\s*LiTFSI"
          r"|1(?:\.0)?\s*M\s*LiTFSI[^.;]{0,30}?(?:DME|dimethoxyethane)[^.;]{0,30}?(?:DOL|dioxolane)")

# 正极类型
P_SPAN = r"\bS-?PAN\b|sulfuri[sz]ed\s*poly\s*\(?acrylonitrile\)?|\bpPAN\b|S@pPAN|\bSPAN-based"
P_LI2S_CATH = r"Li2S[\s-]*(?:based\s*)?(?:cathodes?|positive electrodes?)|Li2S@|Li2S\s*/\s*C\b|Li2S-C\b|Li2S[\s-]*(?:graphite|Si)\b"
P_CATHOLYTE = r"catholyte"
P_SC = (r"\bS\s*/\s*C\b|S@C\b|S/KB|KB/S|S/CNTs?|CNTs?/S\b|S/rGO|rGO/S\b|sulfur[/-]carbon|carbon[/-]sulfur|S/Super\s*P|S/AB\b|sulfur cathodes?"
        r"|S8 cathode|sulfur composite|S/MWCNTs?|C/S\b|S/CMK|CMK-3/S|S/BP\b|S/Ketjen|sulfur electrodes?|\bS cathodes?|sulfur-loaded|S-loaded")
P_IONANODE = (r"graphite anodes?|graphite\s*\|\||\|\|\s*graphite|silicon anodes?|\bSi anodes?|Si/C anodes?|prelithiated (?:graphite|silicon|Si)"
              r"|lithium[\s-]*ion[\s-]*sulfur|Li[\s-]*ion[\s-]*S\b|Li2S[\s-]*(?:/|\|\||-)\s*(?:graphite|Si)\b|hard carbon anode")
P_GEL = r"gel(?:led)?[\s-]*(?:polymer\s*)?electrolytes?|quasi[\s-]*solid|solid[\s-]*state electrolytes?|polymer electrolytes?|in[\s-]*situ polymeri"

# 电解液类别（作者自称：题名 + 摘要）
FAMILY = [
    ("强溶剂化", r"high(?:ly)?[\s-]*solvating|strong(?:ly)?[\s-]*solvating|strong(?:er)? solvation|high[\s-]*donor[\s-]*number|high[\s-]*DN\b|\bHSEs?\b"
               r"|\bDMSO\b|dimethyl sulfoxide|\bDMA\b|dimethylacetamide|\bDMF\b|dimethylformamide|1-methylimidazole|tetramethylurea|\bTMU\b|high[\s-]*dielectric"),
    ("适中溶剂化", r"moderate(?:ly)?[\s-]*solvating|moderate solvation|moderate(?:ly)? (?:\w+ ){0,2}solubilit|intermediate solvation|medium[\s-]*solvating|\bMSEs?\b"),
    ("弱溶剂化", r"weak(?:ly)?[\s-]*solvat|weak(?:er)? solvation|weakly[\s-]*coordinating solvent|low[\s-]*solvating|\bWSEs?\b|weak(?:ly)?[\s-]*solvated"),
    ("难溶/固相转化", r"sparingly[\s-]*solvat|non[\s-]*solvating|polysulfide[\s-]*insoluble|insoluble polysulfide|low (?:polysulfide|LiPSs?|Li2Sx) solubilit"
                  r"|suppress\w* (?:the )?(?:polysulfide|LiPSs?|Li2Sx) (?:dissolution|solubilit)|quasi[\s-]*solid[\s-]*(?:state )?(?:conversion|reaction)"
                  r"|solid[\s-]*solid (?:conversion|reaction)|solvate[\s-]*ionic[\s-]*liquid|\bSSEs?\b|\bSIL\b"),
    ("局部高浓", r"locali[sz]ed[\s-]*(?:high|super)[\s-]*concentrat|\bLHCEs?\b|\bdiluents?\b|hydrofluoroether|\bHFEs?\b|\bTTE\b|\bBTFE\b|\bOFE\b|\bTFEO\b|\bHFPM\b"),
    ("高浓", r"high[\s-]*concentrat\w* electrolytes?|highly[\s-]*concentrated|super[\s-]*concentrated|concentrated electrolytes?|solvent[\s-]*in[\s-]*salt|\bHCEs?\b"
           r"|(?<![\d.])(?:[3-9]|1\d)(?:\.\d+)?\s*M\s*Li(?:TFSI|FSI)"),
    ("低浓", r"low[\s-]*concentrat\w* electrolytes?|dilute(?:d)? electrolytes?|ultra[\s-]*low[\s-]*concentrat|\bLCEs?\b"),
    ("介体/均相催化", r"redox[\s-]*mediat|\bmediat(?:or|ors|ed|ing)\b|homogeneous(?:ly)?[\s-]*catal|soluble catalysts?|molecular catalysts?|redox[\s-]*active (?:additive|molecule)"
                  r"|organodiselenide|organodisulfide|catalytic (?:electrolyte|additive)|electrocatalytic additive|redox comediator"),
    ("LiNO3", r"LiNO\s*3|lithium nitrate|\bnitrates?\b"),
    ("盐/阴离子", r"\bLiFSI\b|\bLiTFSI\b|\bLiPF6\b|\bLiBOB\b|\bLiDFOB\b|\bLiOTf\b|triflate|\banions?\b|lithium salts?|dual[\s-]*salt|binary[\s-]*salt"),
    ("氟化/无氟", r"fluorinated|fluorine[\s-]*free|non[\s-]*fluorinated|perfluoro|fluorine[\s-]*rich"),
    ("离子液体", r"ionic liquids?"),
    ("溶剂(其他)", r"\bsolvents?\b|co[\s-]*solvents?|\bethers?\b|\bsulfolane\b|\bcarbonates?\b|nitrile"),
    ("添加剂(其他)", r"additives?"),
]
COND_TAG = [
    ("贫液", r"lean[\s-]*electrolyte|low (?:E/S|electrolyte[\s/-]*(?:to[\s-]*)?sulfur)|limited electrolyte|E/S\b"),
    ("低温", r"low[\s-]*temperature|sub[\s-]*zero|wide[\s-]*temperature|all[\s-]*climate|cold|(?:^|\s)-\s?\d{1,2}\s*°\s*C"),
    ("高温", r"high[\s-]*temperature|elevated temperatures?|wide[\s-]*temperature"),
    ("软包", r"pouch"),
]


# ---------------------------------------------------------------- 逐篇


def li_value(m):
    v = fv(m)
    unit = m.group(m.lastindex) if m.lastindex and m.lastindex >= 2 else "µm"
    if v is None:
        return None
    # mm 且 <5 按毫米换算；≥5 的 "mm" 是 µ 乱码（"125 mm thick" 实为 125 µm）
    return v * 1000 if unit == "mm" and v < 5 else v


def check(row, ab_json):
    key = re.sub(r"[^\w.-]+", "_", row["doi"])
    raw_main = open(os.path.join(CACHE, f"{key}.main.txt"), encoding="utf-8").read() if os.path.exists(os.path.join(CACHE, f"{key}.main.txt")) else ""
    raw_si = open(os.path.join(CACHE, f"{key}.si.txt"), encoding="utf-8").read() if os.path.exists(os.path.join(CACHE, f"{key}.si.txt")) else ""
    exp, rest = zones(raw_main)
    si = norm(raw_si)
    Z = [("EXP", exp), ("SI", si), ("MAIN", rest)]
    full = " ".join([exp, si, rest])
    ab = ab_json.get(row["doi"].lower(), {}).get("abstract", "")
    ab_src = "OpenAlex" if ab else "PDF首页"
    if not ab:
        ab = pdf_abstract(raw_main)
    ta = norm(row["title"] + " . " + ab)
    r = {"doi": row["doi"], "年份": int(row["year"]), "期刊": row["journal"], "题名": row["title"],
         "正文字数": len(raw_main), "有SI文本": bool(raw_si.strip()), "摘要来源": ab_src}

    # 范围
    n_cell = len(re.findall(P_CELL, full, re.I))
    r["有电池测试"] = n_cell >= 2
    n_span = len(re.findall(P_SPAN, full))
    n_li2s = len(re.findall(P_LI2S_CATH, full, re.I))
    n_cath = len(re.findall(P_CATHOLYTE, full, re.I))
    n_sc = len(re.findall(P_SC, full, re.I))
    title_l = row["title"]
    if re.search(P_SPAN, title_l, re.I) or re.search(r"Li-?SPAN|lithium[\s-]*sulfuri[sz]ed", title_l, re.I):
        cat = "SPAN"
    elif n_span >= 5 and n_span >= n_sc:
        cat = "SPAN"
    elif re.search(r"Li2S[\s-]*(?:based\s*)?cathode|Li2S[\s-]*(?:graphite|Si)\b|Li2S-?based", title_l, re.I) or (n_li2s >= 5 and n_li2s > n_sc):
        cat = "Li2S"
    elif n_cath >= 5 and n_cath > n_sc:
        cat = "溶液正极(catholyte)"
    else:
        cat = "硫碳"
    if cat == "硫碳" and n_span >= 5:
        cat = "硫碳+SPAN"
    r["正极层"] = cat
    r["正极计数(SPAN/Li2S/catholyte/硫碳)"] = f"{n_span}/{n_li2s}/{n_cath}/{n_sc}"
    ion = re.search(P_IONANODE, ta, re.I) or len(re.findall(P_IONANODE, exp + " " + si, re.I)) >= 2
    af = re.search(P_ANODEFREE, ta, re.I) or len(re.findall(P_ANODEFREE, exp + " " + si, re.I)) >= 2
    r["负极"] = "石墨/硅(锂离子-硫)" if ion else ("无负极" if af else "锂金属")
    r["凝胶/固态嫌疑"] = bool(re.search(P_GEL, row["title"], re.I))

    # 类别
    ta_no_lhce = re.sub(r"locali[sz]ed[\s-]*(?:high|super)[\s-]*concentrat\w*", " ", ta, flags=re.I)
    fams = []
    for name, pat in FAMILY:
        src = ta_no_lhce if name == "高浓" else ta
        if re.search(pat, src, re.I if name not in ("强溶剂化",) else 0) or (name == "强溶剂化" and re.search(pat, src, re.I) and re.search(r"solvat|donor|DN\b", src, re.I)):
            fams.append(name)
    r["电解液类别(题名+摘要)"] = "; ".join(fams)
    r["条件标签(题名+摘要)"] = "; ".join(n for n, p in COND_TAG if re.search(p, ta, re.I))

    # E/S
    es = (find_all(P_ES_UNIT, Z, fv, vmin=0.3, vmax=100) + find_all(P_ES_TERM, Z, fv, vmin=0.3, vmax=100)
          + find_all(P_ES_UNIT2, Z, fv, vmin=0.3, vmax=100))
    mark, rep, vals, snip = summarize(es, min)
    r["E/S"], r["E/S最小"], r["E/S值"], r["E/S原句"] = mark, rep, vals, snip
    amt = find_all(P_EL_AMOUNT, Z, fv, vmin=1, vmax=5000) + find_all(P_EL_AMOUNT2, Z, fv, vmin=1, vmax=5000)
    mk, rp, vl, sn = summarize(amt, min)
    r["电解液用量µL"], r["用量值"], r["用量原句"] = mk, vl, sn

    # 锂量
    li = (find_all(P_LI1, Z, fv, vmin=5, vmax=1500) + find_all(P_LI2, Z, fv, vmin=5, vmax=1500) + find_all(P_LI3, Z, fv, vmin=5, vmax=1500)
          + find_all(P_LI4, Z, li_value, vmin=5, vmax=1500) + find_all(P_LI5, Z, li_value, vmin=5, vmax=1500)
          + find_all(P_LI6, Z, li_value, vmin=5, vmax=1500) + find_all(P_LI7, Z, li_value, vmin=5, vmax=1500)
          + find_all(P_LI8, Z, li_value, vmin=5, vmax=1500))
    mark, rep, vals, snip = summarize(li, min)
    r["锂厚"], r["锂厚最小µm"], r["锂厚值"], r["锂厚原句"] = mark, rep, vals, snip
    np_ = find_all(P_NP, Z, fv, vmin=0, vmax=100, flags=0) + find_all(P_NP2, Z, fv, vmin=0, vmax=100, flags=0)
    mark, rep, vals, snip = summarize(np_, min)
    r["N/P"], r["N/P最小"], r["N/P值"], r["N/P原句"] = mark, rep, vals, snip
    ex = find_all(P_LIEX, Z, None)
    r["锂过量%"] = summarize(ex)[0]
    afh = find_all(P_ANODEFREE, Z, None)
    r["无负极提及"] = summarize(afh)[0]

    # 载量
    ld = [h for h in find_all(P_LOAD, Z, fv, vmin=0.1, vmax=60) if LOAD_CTX.search(h[2])]
    mark, rep, vals, snip = summarize(ld, max)
    r["硫载量"], r["硫载量最大"], r["硫载量值"], r["硫载量原句"] = mark, rep, vals, snip

    # LiNO3
    ln = find_all(P_LINO3, Z, None)
    lc = find_all(P_LINO3_C1, Z, fv, vmin=0, vmax=50) + find_all(P_LINO3_C2, Z, fv, vmin=0, vmax=50)
    lf = find_all(P_LINO3_FREE, Z, None)
    r["LiNO3提及"] = summarize(ln)[0]
    mk, rp, vl, sn = summarize(lc, max)
    r["LiNO3浓度"], r["LiNO3浓度值"], r["LiNO3原句"] = mk, vl, sn
    r["无LiNO3对照"] = summarize(lf)[0]

    # 温度（粗）
    lo = [h for h in find_all(P_LOWT, Z, fv) if T_CTX.search(h[2]) and not T_BAD_LOW.search(h[2])]
    hi = [h for h in find_all(P_HIGHT, Z, fv) if T_CTX.search(h[2][max(0, len(h[2]) // 2 - 70):len(h[2]) // 2 + 70]) and not T_BAD_HIGH.search(h[2][max(0, len(h[2]) // 2 - 70):len(h[2]) // 2 + 70])]
    mk, rp, vl, sn = summarize(lo, max)
    r["低温测试(粗)"], r["低温值"], r["低温原句"] = mk, vl, sn
    mk, rp, vl, sn = summarize(hi, max)
    r["高温测试(粗)"], r["高温值"], r["高温原句"] = mk, vl, sn

    # 其他
    r["软包"] = summarize(find_all(P_POUCH, Z, None))[0]
    ah = [h for h in find_all(P_AH, Z, fv, vmin=0.1, vmax=100) if re.search(r"pouch", h[2], re.I)]
    mk, rp, vl, sn = summarize(ah, max)
    r["软包Ah"], r["软包Ah值"] = mk, vl
    r["Li||Cu"] = summarize(find_all(P_LICU, Z, None))[0]
    r["多硫化物溶解度测定"] = summarize(find_all(P_PSSOL, Z, None))[0]
    r["溶剂化表征(Raman/MD)"] = summarize(find_all(P_SOLV, Z, None))[0]
    bh = find_all(P_BASE, Z, None)
    mk, rp, vl, sn = summarize(bh)
    r["常规醚基准(1M LiTFSI DOL/DME)"], r["基准原句"] = mk, sn
    return r


def main():
    lib = pd.read_csv(os.path.join(LIB, "library_index.csv"))
    lib = lib[lib.topic == "electrolyte"].fillna("")
    ab_json = json.load(open(os.path.join(ROOT, "output", "abstracts.json"), encoding="utf-8"))
    rows = []
    for i, row in enumerate(lib.to_dict("records"), 1):
        rows.append(check(row, ab_json))
        if i % 100 == 0:
            print(i, flush=True)
    df = pd.DataFrame(rows)
    df.to_pickle(OUT_PKL)
    print("saved", OUT_PKL, len(df), flush=True)


if __name__ == "__main__":
    sys.exit(main())
