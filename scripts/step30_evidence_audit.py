"""step30：证据审计（阶段总结_2026-11-09 §4.1；11-10 用户“你帮我继续做吧”）。

问的是：每张问题卡的两派各用什么证据；哪些常用证据原理上分不出两种解释——这就是争论一直没定论的原因，也决定实验必须补什么测量。
做法：
  1. 313 篇已提取机制（candidate.json 的 mechanisms，中文摘要）→ 经 test_ids 和 measurements.supports_mechanisms 找到测试 → 按测试名归方法类（一个测试可归多类）。
  2. Q1/Q2（LiF 从哪来）：除了方法，还看“设计”——表征所用配方里有几种氟来源（阴离子 / 含氟溶剂 / 含氟添加剂，按组分表的 F 原子数）。
     XPS 等只看得到 LiF 有多少；只有“单一氟源”的配方（无氟溶剂配含氟盐，或无氟盐配含氟溶剂）才能把 LiF 归到某一来源。
  3. Q3（高盐与 LiNO₃）：“LiNO₃ 耗尽”类说法是直接测了剩余硝酸根、做了补加恢复，还是只从循环曲线推断；“高盐少溶多硫化物”是否测过溶解度。
  4. 两层：step20 已逐条归立场的两派说法（问题 1 用 11-09 读英文原句后重标的主说法标签）；全库关键词筛出的说法（粗，要抽查）。
  5. Q1 另数：Li‖Cu CE 测试按主盐阴离子 × 温度，看库里有没有能分开“盐”和“温度”的数据。
只用提取摘要和测试名，没有回原文核对；关键词会漏和误归。AI 辅助，用户尚未逐项人工确认。
仓库公开：json/xlsx 只放论文号、机制编号、来源类型、标签、方法和测试名；机制摘要只进本机“（含原句）”文件（.gitignore 排除）。
输出：output/证据审计_313篇_2026-11-10/
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step30_evidence_audit.py
"""
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
from step13_common import write_xlsx

PAPERS = ROOT / "output" / "试跑313篇_2026-11-05" / "papers"
COMP = ROOT / "output" / "组分结构表_试跑313篇_2026-11-05"
EVID = ROOT / "output" / "机制证据_313篇_2026-11-08" / "机制证据.json"
OUT = ROOT / "output" / "证据审计_313篇_2026-11-10"

# ---------------------------------------------------------------- 方法分类（按测试名＋提取时的测试类别）
PERF_KINDS = {"全电池性能", "对称电池", "锂铜效率", "机理电池", "其他"}   # 只有这些类别的测试才按名字归到性能类方法
METHODS = [  # (方法类, 测试名正则, 直接归入的测试类别, 是否只对性能类测试生效)
    ("XPS", r"XPS|HAXPES|光电子|F\s?1s|N\s?1s|S\s?2p", None, False),
    ("XAS/XANES", r"XAS|XANES|EXAFS|K-edge|K边", None, False),
    ("ToF-SIMS", r"SIMS", None, False),
    ("TEM/冷冻电镜", r"TEM|[Cc]ryo|冷冻|SAED|EELS", None, False),
    ("核磁", r"NMR|核磁", None, False),
    ("拉曼/红外", r"Raman|拉曼|FTIR|红外|ATR", None, False),
    ("计算", r"DFT|AIMD|\bMD\b|分子动力学|LUMO|HOMO|计算|ReaxFF|模拟|NBO|势能面", "模拟", False),
    ("Li‖Cu CE", r"Aurbach|库仑效率|库伦效率|(Li\s*\|{1,2}\s*Cu|Li‖Cu|Li\s*[/–-]\s*Cu|LiCu).{0,12}(CE|效率|循环)", "锂铜效率", True),
    ("全电池循环", None, "全电池性能", True),
    ("对称电池", r"Li\s*\|{1,2}\s*Li|Li‖Li|LiLi|Li\s*[/–-]\s*Li\b|对称", "对称电池", True),
    ("SEM/EDS/AFM", r"SEM|EDS|EDX|形貌|AFM|光学|照片|截面|EPMA|外观|拆解", None, False),
    ("EIS", r"EIS|阻抗", None, False),
    ("CV/LSV", r"CV|LSV|伏安", None, False),
    ("UV-vis/溶解度", r"UV|紫外|溶解度|溶出|比色|饱和", None, False),
    ("气体/质谱", r"GC|DEMS|气体|产气|质谱|\bMS\b|鼓胀", None, False),
    ("XRD", r"XRD", None, False),
    ("硝酸根定量", r"离子色谱|\bIC\b|HPLC|硝酸根|NO3.{0,10}(定量|浓度|残余|剩余)|(残余|剩余).{0,10}(LiNO|NO3|硝酸)", None, False),
    ("补加/补液", r"补加|补液|再加|[Rr]eplenish|[Rr]efill", None, False),
    ("浸泡", r"浸泡|[Ss]oak", "浸泡", False),
]
SURFACE = {"XPS", "XAS/XANES", "ToF-SIMS", "TEM/冷冻电镜", "核磁"}          # 直接看界面产物
INDIRECT = {"计算", "拉曼/红外", "CV/LSV"}                                  # 溶剂化、倾向、还原电位
OUTCOME = {"Li‖Cu CE", "全电池循环", "对称电池", "EIS", "SEM/EDS/AFM"}      # 只看结果或形貌

# 每种方法对“LiF 来自阴离子还是稀释剂”能说明什么（原理层面，Claude 写；用户未确认）
LIF_POWER = [
    ("XPS（F 1s、深度剖析）", "看得到 LiF 有多少、在哪一层；含氟盐配含氟稀释剂时，两种来源的 LiF 是同一个峰", "分不出"),
    ("XAS/XANES、冷冻电镜", "看得到 LiF 的存在、晶粒和分布", "分不出"),
    ("ToF-SIMS", "看得到含氟碎片的深度分布；LiF₂⁻ 等碎片不带来源信息", "分不出（配合单一氟源可以）"),
    ("固体 ¹⁹F 核磁", "看得到稀释剂碎片（C–F）是否进了 SEI；LiF 本身不管来源是同一个峰", "只能说明稀释剂参与了分解"),
    ("计算（LUMO、AIMD、反应路径）", "给出谁更容易还原的倾向；孤立分子 LUMO 不含溶剂化效应", "不是测量，只能提示"),
    ("拉曼/红外/溶液核磁（溶剂化）", "看阴离子进不进第一壳层，推出“阴离子优先还原”", "间接，排除不了稀释剂也贡献"),
    ("Li‖Cu CE、全电池、对称电池、SEM", "只看结果或形貌", "分不出机理"),
    ("设计：无氟溶剂配含氟盐", "LiF 只能来自阴离子（或含氟添加剂）", "能证明阴离子够用，不能证明稀释剂不贡献"),
    ("设计：无氟盐配含氟稀释剂", "LiF 只能来自稀释剂", "能分（库里很少）"),
    ("设计：同盐、有/无含氟稀释剂对照", "换稀释剂同时改变溶剂化结构，阴离子分解量也跟着变", "分不干净"),
    ("设计：同位素或无氟盐对照＋定量", "直接分账", "能分"),
]


def classify_test(t: dict) -> set:
    name, kind = t.get("name", "") or "", t.get("kind", "") or ""
    got = set()
    for label, rx, k, perf_only in METHODS:
        if k and kind == k:
            got.add(label)
            continue
        if rx and (not perf_only or kind in PERF_KINDS) and re.search(rx, name):
            got.add(label)
    return got or {"其他"}


def tier(methods: set) -> str:
    if methods & SURFACE:
        return "有界面表征"
    if methods & INDIRECT:
        return "只有间接证据（计算、溶剂化、电位）"
    if methods - {"其他"}:
        return "只有性能或形貌"
    return "无关联测试"


# ---------------------------------------------------------------- 配方的氟来源
FSOLV = set()      # 组分表里的含氟溶剂名，并入稀释剂词表


def load_fluorine():
    comps = json.loads((COMP / "组分表.json").read_text(encoding="utf-8"))
    desc = {d["组分"]: d for d in json.loads((COMP / "描述符.json").read_text(encoding="utf-8"))}
    src = {}
    for c in comps:
        cid, cat = c["id"], c["类别"]
        nf = desc.get(cid, {}).get("F原子数") or 0
        if cid in ("ION_FSI", "ION_TFSI", "ION_PF6"):
            src[cid] = "阴离子"
        elif nf <= 0:
            continue
        elif "盐" in cat or cid.endswith("TFSI"):          # 离子液体按溶剂收录，但氟在 TFSI⁻ 上
            src[cid] = "阴离子"
        elif cat.startswith("溶剂"):
            src[cid] = "含氟溶剂"
            FSOLV.add(cid)
        else:
            src[cid] = "含氟添加剂"
    rec = json.loads((COMP / "配方组成.json").read_text(encoding="utf-8"))
    form, fcomp = {}, {}
    for r in rec:
        ids = {x["组分"] for x in r.get("组分", [])}
        fs = frozenset(src[i] for i in ids if i in src)
        fc = {"阴离子": sorted(i for i in ids if src.get(i) == "阴离子"),
              "含氟溶剂": sorted(i for i in ids if src.get(i) == "含氟溶剂")}
        for n in [r["配方"]] + (r.get("配方名", []) or []):
            form[(r["论文"], n)] = fs
            fcomp[(r["论文"], n)] = fc
    return form, fcomp


def fclass_tag(c: frozenset) -> str:
    if c == {"阴离子"}:
        return "只有阴离子含氟"
    if c == {"含氟溶剂"}:
        return "只有溶剂含氟"
    if c == {"含氟添加剂"}:
        return "只有添加剂含氟"
    if not c:
        return "都不含氟"
    return "两种以上氟源"


def claim_tags(pid: str, ref, form: dict, fdefs: dict, groups: dict) -> set:
    """说法 A 或 B 指向的配方（配方组展开成员）→ 氟来源标签。"""
    if ref in (None, "", []):
        return set()
    refs = ref if isinstance(ref, list) else [ref]
    out = set()
    for r in refs:
        for f in groups.get(r, [r]):
            key = (pid, f) if (pid, f) in form else (pid, fdefs.get(f))
            if key in form:
                out.add(fclass_tag(form[key]))
    return out


def test_design(pid: str, t: dict, form: dict, fdefs: dict) -> set:
    """测试所用配方的氟来源组合 → 设计标签。"""
    classes = []
    for f in t.get("formulations", []) or []:
        key = (pid, f) if (pid, f) in form else (pid, fdefs.get(f))
        if key in form:
            classes.append(form[key])
    if not classes:
        return {"配方未知"}
    tags = {fclass_tag(c) for c in classes}
    if "只有阴离子含氟" in tags and "两种以上氟源" in tags:
        tags.add("同测试有/无含氟溶剂对照")
    return tags


# ---------------------------------------------------------------- 说法的关键词分类
ANION = r"(阴离子|FSI|TFSI|FSA|TFSA|PF6|BF4|DFOB|锂盐|盐分解|盐还原|盐衍生|盐来源)"
LIF = r"LiF(?![A-Za-z])"          # 不匹配 LiFSI、LiFSA
DIL_BASE = (r"稀释剂|HFE|TDE|BTFE|TFEO|OFE|TTFE|F\d?DEE|F\d?DMB|F\dEO\d|氟化醚|含氟醚|氟醚|氟代醚|含氟溶剂|氟化溶剂|"
            r"氟化共溶剂|氟苯|全氟|部分氟化|氟化稀释")      # 不放 CF3/CF2/C–F：TFSI⁻ 也有
DIL = "(" + DIL_BASE + ")"
ACT = r"(分解|还原|衍生|来源|来自|源于|贡献|参与|生成|产生|转化|形成|促成)"
NEG = r"(不参与|不分解|不易分解|还原稳定|稳定不|不太可能|排除|未参与|惰性)"


def lif_source(s: str) -> str:
    a = re.search(ANION + r".{0,22}" + ACT, s) or re.search(r"(来自|源于|来源于|衍生自)\s*" + ANION, s)
    d = re.search(DIL + r".{0,22}" + ACT, s) or re.search(r"(来自|源于|来源于|衍生自)\s*" + DIL, s)
    neg = re.search(DIL + r".{0,15}" + NEG, s)
    if neg and not (d and not a):
        return "稀释剂不分解" if not a else "阴离子（稀释剂不分解）"
    if a and d:
        return "两者都出"
    if a:
        return "阴离子"
    if d:
        return "稀释剂/含氟溶剂"
    return "未说来源"


NO3 = r"LiNO|硝酸"
DEP = (r"(LiNO3|LiNO₃|硝酸盐?|NO3−?|NO₃⁻|添加剂).{0,12}(消耗|耗尽|耗竭|用完|deplet)|"
       r"(消耗|耗尽|耗竭|用完).{0,6}(LiNO3|LiNO₃|硝酸)")
CATH = r"(正极|阴极|cathode).{0,15}还原|还原.{0,10}(正极|阴极)|1\.[5-8]\d?\s*V|低电位|截止电压|过放"
FILM = r"SEI|钝化|保护层|保护膜|成膜|LixNOy|LiNxOy|Li3N|Li2O|Li2SO|硫酸|亚硫酸"
HISALT = (r"(高浓|高盐|浓盐|超浓|盐浓度|局部高浓|浓度升高|浓度提高|溶剂化盐).{0,30}(溶解|溶出|溶解度)|"
          r"(溶解|溶出|溶解度).{0,30}(高浓|高盐|浓盐|超浓|盐浓度)")
PS = r"多硫|LiPS|Li2S[x4-8n]|PS\b"
NOT_MEASURED = r"未.{0,6}(直接)?(测|测定|测得|测量)|没有.{0,4}测|不是.{0,6}测量"


def no3_kind(s: str) -> str:
    if re.search(DEP, s):
        return "消耗/耗尽"
    if re.search(CATH, s):
        return "正极还原"
    if re.search(FILM, s):
        return "负极成膜"
    return "其他"


def depletion_verdict(methods: set) -> str:
    if "硝酸根定量" in methods:
        return "直接测了剩余硝酸根"
    if "补加/补液" in methods:
        return "补加后恢复（间接但有判别力）"
    if methods & SURFACE:
        return "界面产物（XPS 等）推断"
    if methods - {"其他"}:
        return "只从循环/CE 曲线推断"
    return "无关联测试"


# ---------------------------------------------------------------- Q1：Li‖Cu CE 按阴离子 × 温度
def temp_class(cdefs: dict, ref: str | None) -> str:
    d = cdefs.get(ref or "", {})
    v = str(d.get("value", ""))
    if not d or d.get("status") == "未报告" or "未报告" in v:
        return "未写（默认室温）"
    nums = [float(x.replace("−", "-")) for x in re.findall(r"[−-]?\d+(?:\.\d+)?(?=\s*°?\s*C)", v)]
    if not nums:
        return "室温（文字）" if re.search(r"室温|room|RT|ambient", v, re.I) else "未写（默认室温）"
    t = max(nums, key=abs)
    if t > 35:
        return "高温 >35 °C"
    if t < 15:
        return "低温 <15 °C"
    return "室温 15–35 °C"


# 问题 1 的 25 条主说法：11-09 Claude 读英文原句后重标（output/英文向量试跑_2026-11-09/问题1单一说法.json，未提交，故抄在这里）
# 机制：D 稀释剂自身出 LiF；A 阴离子出 LiF；B 两者都出；N 稀释剂分解的净利弊；O 主说法不是 LiF 来源
Q1_LABEL = {
    "P049|MC17": ("D", "+", "speculation"), "P096|ME09": ("B", "+", "conclusion"), "P123|K18": ("B", "+", "conclusion"),
    "P179|MC10": ("D", "+", "speculation"), "P199|K11": ("A", "+", "conclusion"), "P245|ME10": ("B", "+", "conclusion"),
    "P279|K01": ("B", "+", "conclusion"), "P388|K16": ("O", "+", "conclusion"), "P425|K17": ("D", "+", "simulation"),
    "P085|ME07": ("A", "+", "conclusion"), "P217|K16": ("A", "+", "conclusion"), "P233|K14": ("O", "+", "conclusion"),
    "P263|K06": ("O", "+", "conclusion"), "P303|K4": ("A", "+", "conclusion"), "P310|K1": ("O", "+", "conclusion"),
    "P313|K3": ("D", "−", "conclusion"), "P338|MC11": ("D", "−", "speculation"), "P354|K14": ("A", "+", "conclusion"),
    "P362|K7": ("A", "+", "conclusion"), "P371|K14": ("A", "+", "conclusion"), "P381|K004": ("N", "−", "conclusion"),
    "P451|K23": ("O", "+", "speculation"), "P149|K33": ("O", "+", "conclusion"), "P277|ME037": ("D", "+", "conclusion"),
    "P279|K25": ("O", "−", "conclusion"),
}
Q1_NAME = {"D": "稀释剂自身出 LiF", "A": "阴离子出 LiF", "B": "两者都出", "N": "稀释剂分解净利弊", "O": "主说法不是 LiF 来源"}


def lif_design_verdict(src: str, methods: set, a_tags: set, b_tags: set, test_tags: set) -> str:
    """说法所依据的表征能不能把 LiF 归到它说的来源。先看说法自己的配方（A，对照 B）；A 对不上配方时退回测试所用配方。"""
    if not methods & SURFACE:
        return "没有界面表征（只靠性能、计算或推测）"
    tags, note = (a_tags, "") if a_tags else (test_tags - {"同测试有/无含氟溶剂对照"}, "（按测试配方）")
    if src in ("阴离子", "A") and tags == {"只有阴离子含氟"}:
        return "能：无氟溶剂里也有 LiF（证明阴离子够用，不证明稀释剂不贡献）" + note
    if src in ("稀释剂/含氟溶剂", "D") and tags == {"只有溶剂含氟"}:
        return "能：无氟盐配含氟溶剂" + note
    if "两种以上氟源" in tags:
        if "只有阴离子含氟" in (b_tags if a_tags else tags):
            return "有/无含氟溶剂对照（溶剂化同时变，分不干净）" + note
        return "分不出：两种氟源并存" + note
    if tags & {"只有阴离子含氟", "只有溶剂含氟", "只有添加剂含氟"}:
        return "单一氟源，但与说法的来源不对应" + note
    return "配方未知或不含氟"


# ---------------------------------------------------------------- 主程序
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    form, fcomp = load_fluorine()
    global DIL
    fsolv = sorted(FSOLV, key=len, reverse=True)
    DIL = "(" + DIL_BASE + "|" + "|".join(re.escape(x) for x in fsolv) + ")"
    claims = {}          # 论文|机制 → 行
    licu = []            # Q1：Li‖Cu CE 测试
    for f in sorted(PAPERS.glob("*/candidate.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        pid = f.parent.name
        tests = {t["id"]: t for t in d.get("tests", [])}
        fdefs = {x["id"]: x.get("recipe_id") for x in d.get("formulations", [])}
        groups = {g.get("id"): g.get("members", []) for g in d.get("formulation_groups", []) or []}
        cdefs = d.get("condition_definitions", {}) or {}
        m2t = defaultdict(set)
        for m in d.get("measurements", []):
            for mc in m.get("supports_mechanisms", []) or []:
                if m.get("test_id"):
                    m2t[mc].add(m["test_id"])
        tinfo = {}
        for tid, t in tests.items():
            tinfo[tid] = (classify_test(t), test_design(pid, t, form, fdefs))
            if t.get("kind") == "锂铜效率":
                ani, fsol = set(), set()
                for fid in t.get("formulations", []) or []:
                    key = (pid, fid) if (pid, fid) in fcomp else (pid, fdefs.get(fid))
                    ani |= set(fcomp.get(key, {}).get("阴离子", []))
                    fsol |= set(fcomp.get(key, {}).get("含氟溶剂", []))
                licu.append({"论文": pid, "测试": tid, "测试名": t.get("name", ""),
                             "温度": temp_class(cdefs, (t.get("condition_refs") or {}).get("temperature")),
                             "含氟盐/阴离子": sorted(ani), "含氟溶剂": sorted(fsol),
                             "配方数": len(t.get("formulations", []) or [])})
        for m in d.get("mechanisms", []):
            tids = sorted(set(m.get("test_ids") or []) | m2t.get(m["id"], set()))
            tids = [x for x in tids if x in tests]
            meth, des, sdes = set(), set(), set()
            for x in tids:
                mm, dd = tinfo[x]
                meth |= mm
                des |= dd
                if mm & SURFACE:
                    sdes |= dd          # 设计只看界面表征测试用的配方
            claims[f"{pid}|{m['id']}"] = {
                "论文": pid, "机制": m["id"], "来源类型": m.get("source_type", ""), "摘要": m.get("summary", ""),
                "测试": tids, "测试名": [tests[x].get("name", "") for x in tids],
                "方法": sorted(meth), "证据层级": tier(meth), "表征所用配方的氟来源": sorted(sdes),
                "说法配方A的氟来源": sorted(claim_tags(pid, m.get("A"), form, fdefs, groups)),
                "对照配方B的氟来源": sorted(claim_tags(pid, m.get("B"), form, fdefs, groups)),
            }

    # ---------- Q1/Q2：全库含 LiF 的说法
    lif = [c for c in claims.values() if re.search(LIF, c["摘要"])]
    vd = lambda c, src: lif_design_verdict(src, set(c["方法"]), set(c["说法配方A的氟来源"]),
                                           set(c["对照配方B的氟来源"]), set(c["表征所用配方的氟来源"]))
    for c in lif:
        c["LiF来源（关键词）"] = lif_source(c["摘要"])
        c["设计能否分来源"] = vd(c, c["LiF来源（关键词）"])
        c["说的是含氟稀释剂体系"] = "两种以上氟源" in c["说法配方A的氟来源"] or "只有溶剂含氟" in c["说法配方A的氟来源"]
    lif_papers = sorted({c["论文"] for c in lif})
    per_paper_meth = defaultdict(set)
    for c in lif:
        per_paper_meth[c["论文"]] |= set(c["方法"])
    only_xps = [p for p, ms in per_paper_meth.items() if ms & SURFACE and (ms & SURFACE) <= {"XPS"}]
    no_surface = [p for p, ms in per_paper_meth.items() if not ms & SURFACE]
    src_claims = [c for c in lif if c["LiF来源（关键词）"] != "未说来源"]

    def paper_count(rows, key):
        out = defaultdict(set)
        for r in rows:
            vals = r[key] if isinstance(r[key], list) else [r[key]]
            for v in vals:
                out[v].add(r["论文"])
        return {k: len(v) for k, v in sorted(out.items(), key=lambda kv: -len(kv[1]))}

    method_by_src = defaultdict(lambda: defaultdict(set))
    for c in lif:
        for mth in c["方法"] or ["（无关联测试）"]:
            method_by_src[c["LiF来源（关键词）"]][mth].add(c["论文"])

    # 单一氟源设计在全库里有多少（任何界面表征测试）
    design_any = defaultdict(set)
    for c in claims.values():
        if set(c["方法"]) & SURFACE:
            for tag in c["表征所用配方的氟来源"]:
                design_any[tag].add(c["论文"])

    # ---------- Q1/Q2：step20 两派（问题 1 用 11-09 重标）
    ev = json.loads(EVID.read_text(encoding="utf-8"))
    camp_rows = {}
    for tk in ("T1", "T3", "T4"):
        rows = []
        for e in ev[tk]["证据"]:
            key = f"{e['论文']}|{e['机制']}"
            c = claims.get(key, {})
            meth = set(c.get("方法", []))
            row = {"论文": e["论文"], "机制": e["机制"], "来源类型": e["来源类型"], "step20 立场": e["立场"],
                   "Claude 一句话": e["Claude 一句话"], "方法": sorted(meth), "证据层级": c.get("证据层级", "未找到"),
                   "测试名": c.get("测试名", []), "表征所用配方的氟来源": c.get("表征所用配方的氟来源", []),
                   "说法配方A的氟来源": c.get("说法配方A的氟来源", [])}
            if tk == "T1":
                lab = Q1_LABEL.get(key, ("?", "", ""))
                row["重标机制"] = f"{lab[0]} {Q1_NAME.get(lab[0], '')}{'（不分解）' if lab[1] == '−' and lab[0] == 'D' else ''}"
                row["设计能否分来源"] = vd(c, lab[0]) if c else "未找到"
            if tk == "T3" and e["立场"] == "A":
                row["耗尽证据"] = depletion_verdict(meth)
            rows.append(row)
        camp_rows[tk] = rows

    # ---------- Q3：LiNO₃
    no3 = [c for c in claims.values() if re.search(NO3, c["摘要"])]
    for c in no3:
        c["LiNO3说法类"] = no3_kind(c["摘要"])
    dep = [c for c in no3 if c["LiNO3说法类"] == "消耗/耗尽"]
    cath = [c for c in no3 if c["LiNO3说法类"] == "正极还原"]
    for c in dep:
        c["耗尽证据"] = depletion_verdict(set(c["方法"]))
        c["摘要自注未测"] = bool(re.search(NOT_MEASURED, c["摘要"]))
        c["与多硫化物相关"] = bool(re.search(PS, c["摘要"]))
    hs = [c for c in claims.values() if re.search(HISALT, c["摘要"]) and re.search(PS + r"|硫", c["摘要"])]
    for c in hs:
        c["溶解度证据"] = "直接测了溶解度（UV-vis/浸泡/饱和）" if set(c["方法"]) & {"UV-vis/溶解度", "浸泡"} else \
            ("界面表征" if set(c["方法"]) & SURFACE else ("只从性能推断" if set(c["方法"]) - {"其他"} else "无关联测试"))

    # ---------- Q1：Li‖Cu CE 阴离子 × 温度
    licu_tab = Counter(r["温度"] for r in licu)
    licu_papers = defaultdict(set)
    for r in licu:
        licu_papers[r["温度"]].add(r["论文"])
    rt = lambda t: t in ("未写（默认室温）", "室温（文字）", "室温 15–35 °C")
    by_p = defaultdict(list)
    for r in licu:
        by_p[r["论文"]].append(r)
    papers_rt_hot = sorted(p for p, rs in by_p.items()
                           if any(rt(r["温度"]) for r in rs) and any(r["温度"] == "高温 >35 °C" for r in rs))
    papers_fsi_tfsi = sorted(p for p, rs in by_p.items()
                             if any("LiFSI" in r["含氟盐/阴离子"] for r in rs) and any("LiTFSI" in r["含氟盐/阴离子"] for r in rs))
    hot_rows = [{k: r[k] for k in ("论文", "测试", "测试名", "含氟盐/阴离子", "含氟溶剂")} for r in licu if r["温度"] == "高温 >35 °C"]
    fsys = [c for c in lif if c["说的是含氟稀释剂体系"]]

    # ---------- 汇总
    S = {
        "说明": "AI 辅助，用户尚未逐项人工确认；只用提取摘要和测试名，关键词会漏和误归，见抽查表",
        "全库": {"论文": len({c['论文'] for c in claims.values()}), "机制说法": len(claims),
                "无关联测试的说法": sum(1 for c in claims.values() if not c["测试"])},
        "Q1Q2_LiF": {
            "含 LiF 的说法": len(lif), "论文": len(lif_papers),
            "说法按来源（关键词）": dict(Counter(c["LiF来源（关键词）"] for c in lif).most_common()),
            "说法按证据层级": dict(Counter(c["证据层级"] for c in lif).most_common()),
            "论文按证据层级（取该篇最强）": dict(Counter(
                "有界面表征" if per_paper_meth[p] & SURFACE else tier(per_paper_meth[p]) for p in lif_papers).most_common()),
            "界面表征只有 XPS 的论文": len(only_xps), "没有界面表征的论文": len(no_surface),
            "各方法涉及论文数": paper_count(lif, "方法"),
            "说了来源的说法": len(src_claims),
            "说了来源的说法按设计判定": dict(Counter(c["设计能否分来源"] for c in src_claims).most_common()),
            "说了来源的论文按设计判定": paper_count(src_claims, "设计能否分来源"),
            "说的是含氟稀释剂体系的说法": len(fsys), "其论文": len({c['论文'] for c in fsys}),
            "含氟稀释剂体系说法按来源": dict(Counter(c["LiF来源（关键词）"] for c in fsys).most_common()),
            "含氟稀释剂体系说法按设计判定": dict(Counter(c["设计能否分来源"] for c in fsys).most_common()),
            "含氟稀释剂体系论文按设计判定": paper_count(fsys, "设计能否分来源"),
            "全库界面表征测试所用配方的氟来源（论文数）": {k: len(v) for k, v in sorted(design_any.items(), key=lambda kv: -len(kv[1]))},
            "只有溶剂含氟的论文": sorted(design_any.get("只有溶剂含氟", set())),
        },
        "Q3_LiNO3": {
            "提到 LiNO₃ 的说法": len(no3), "论文": len({c['论文'] for c in no3}),
            "说法类": dict(Counter(c["LiNO3说法类"] for c in no3).most_common()),
            "耗尽类说法": len(dep), "耗尽类论文": len({c['论文'] for c in dep}),
            "耗尽类按证据": dict(Counter(c["耗尽证据"] for c in dep).most_common()),
            "耗尽类论文按证据": paper_count(dep, "耗尽证据"),
            "耗尽类来源类型": dict(Counter(c["来源类型"] for c in dep).most_common()),
            "摘要里自注“未直接测”": sum(c["摘要自注未测"] for c in dep),
            "耗尽类且提到多硫化物": sum(c["与多硫化物相关"] for c in dep),
            "补加/补液论文": sorted({c['论文'] for c in dep if c["耗尽证据"].startswith("补加")}),
            "直接测剩余硝酸根论文": sorted({c['论文'] for c in dep if c["耗尽证据"].startswith("直接")}),
            "正极还原类说法": len(cath), "正极还原类论文": len({c['论文'] for c in cath}),
            "正极还原类各方法涉及论文数": paper_count(cath, "方法"),
            "正极还原类做了截止电压对照（测试名含截止/cutoff/1.x V）": sorted({c['论文'] for c in cath
                                                                 if any(re.search(r"截止|cut-?off|1\.[5-9]\s*V", n, re.I) for n in c["测试名"])}),
            "高盐少溶多硫化物类说法": len(hs), "其论文": len({c['论文'] for c in hs}),
            "高盐少溶按证据": dict(Counter(c["溶解度证据"] for c in hs).most_common()),
        },
        "Q1_LiCu_温度": {"Li‖Cu CE 测试": len(licu), "论文": len({r['论文'] for r in licu}),
                         "测试按温度": dict(licu_tab.most_common()),
                         "论文按温度": {k: len(v) for k, v in licu_papers.items()},
                         "高温测试": hot_rows,
                         "同篇既有室温又有高温": papers_rt_hot,
                         "同篇既有 LiFSI 又有 LiTFSI": papers_fsi_tfsi,
                         "两者都有": sorted(set(papers_rt_hot) & set(papers_fsi_tfsi))},
    }

    # ---------- 写文件（公开：不含摘要）
    pub = lambda c, extra: {k: c[k] for k in ["论文", "机制", "来源类型", "测试", "测试名", "方法", "证据层级",
                                                "表征所用配方的氟来源"] + extra if k in c}
    (OUT / "证据审计.json").write_text(json.dumps({
        "汇总": S, "方法能说明什么（LiF 来源）": [dict(zip(["方法或设计", "能看到什么", "能否分 LiF 来源"], r)) for r in LIF_POWER],
        "两派_Q1Q2（step20 T1＋11-09 重标）": camp_rows["T1"], "两派_LiNO3用量（step20 T3）": camp_rows["T3"],
        "两派_高盐与LiNO3（step20 T4）": camp_rows["T4"],
        "全库LiF说法": [pub(c, ["说法配方A的氟来源", "对照配方B的氟来源", "LiF来源（关键词）", "设计能否分来源", "说的是含氟稀释剂体系"]) for c in lif],
        "全库LiNO3耗尽说法": [pub(c, ["耗尽证据", "摘要自注未测", "与多硫化物相关"]) for c in dep],
        "全库高盐少溶说法": [pub(c, ["溶解度证据"]) for c in hs],
        "LiCu测试": licu,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    j = lambda v: "；".join(v) if isinstance(v, list) else v
    camp_hdr = ["论文", "机制", "来源类型", "step20 立场", "Claude 一句话", "方法", "证据层级", "测试名", "表征所用配方的氟来源", "说法配方A的氟来源"]
    cross = []
    for src, md in method_by_src.items():
        for mth, ps in sorted(md.items(), key=lambda kv: -len(kv[1])):
            cross.append([src, mth, len(ps), j(sorted(ps))])
    summary_rows = []

    def flat(prefix, obj):
        for k, v in obj.items():
            if isinstance(v, dict):
                flat(f"{prefix}{k} / ", v)
            else:
                summary_rows.append([f"{prefix}{k}", json.dumps(v, ensure_ascii=False) if isinstance(v, list) and v and isinstance(v[0], dict) else (j(v) if isinstance(v, list) else v)])
    flat("", S)
    write_xlsx(OUT / "证据审计表.xlsx", [
        ("汇总", ["项目", "数值"], summary_rows),
        ("方法能说明什么", ["方法或设计", "能看到什么", "能否分 LiF 来源"], [list(r) for r in LIF_POWER]),
        ("Q1Q2两派", camp_hdr + ["重标机制", "设计能否分来源"],
         [[j(r.get(h, "")) for h in camp_hdr + ["重标机制", "设计能否分来源"]] for r in camp_rows["T1"]]),
        ("Q1Q2全库_来源×方法", ["LiF 来源（关键词）", "方法", "论文数", "论文"], cross),
        ("Q1Q2全库_说法", ["论文", "机制", "来源类型", "LiF来源（关键词）", "方法", "证据层级", "说法配方A的氟来源", "对照配方B的氟来源", "表征所用配方的氟来源", "设计能否分来源", "测试名"],
         [[j(c[h]) for h in ["论文", "机制", "来源类型", "LiF来源（关键词）", "方法", "证据层级", "说法配方A的氟来源", "对照配方B的氟来源", "表征所用配方的氟来源", "设计能否分来源", "测试名"]] for c in lif]),
        ("Q3两派_LiNO3用量", camp_hdr + ["耗尽证据"], [[j(r.get(h, "")) for h in camp_hdr + ["耗尽证据"]] for r in camp_rows["T3"]]),
        ("Q3两派_高盐与LiNO3", camp_hdr, [[j(r.get(h, "")) for h in camp_hdr] for r in camp_rows["T4"]]),
        ("Q3全库_耗尽说法", ["论文", "机制", "来源类型", "耗尽证据", "摘要自注未测", "与多硫化物相关", "方法", "测试名"],
         [[j(c[h]) for h in ["论文", "机制", "来源类型", "耗尽证据", "摘要自注未测", "与多硫化物相关", "方法", "测试名"]] for c in dep]),
        ("Q3全库_高盐少溶", ["论文", "机制", "来源类型", "溶解度证据", "方法", "测试名"],
         [[j(c[h]) for h in ["论文", "机制", "来源类型", "溶解度证据", "方法", "测试名"]] for c in hs]),
        ("Q1_LiCu测试", ["论文", "测试", "测试名", "温度", "含氟盐/阴离子", "含氟溶剂", "配方数"],
         [[j(r[h]) for h in ["论文", "测试", "测试名", "温度", "含氟盐/阴离子", "含氟溶剂", "配方数"]] for r in licu]),
    ], notes=["证据审计（step30，11-10）。AI 辅助，用户尚未逐项人工确认。",
              "只用提取摘要和测试名；方法按测试名关键词归类，说法按摘要关键词归类，会漏和误归，见本机抽查表（含原句）。",
              "设计：只看界面表征测试（XPS、XAS、ToF-SIMS、TEM、核磁）所用配方的氟来源，按组分表 F 原子数；离子液体的氟算阴离子。"])

    # ---------- 抽查表（本机，含摘要）
    rnd = random.Random(30)
    samp = rnd.sample(lif, 20) + rnd.sample(dep, min(10, len(dep)))
    write_xlsx(OUT / "抽查表（含原句）.xlsx", [
        ("抽查", ["论文", "机制", "摘要", "关键词判的类", "测试名", "归到的方法", "设计判定或耗尽证据", "Claude 抽查", "✍ 你的判断"],
         [[c["论文"], c["机制"], c["摘要"], c["LiF来源（关键词）"], j(c["测试名"]), j(c["方法"]), c["设计能否分来源"], "", ""]
          for c in samp[:20]] +
         [[c["论文"], c["机制"], c["摘要"], c["LiNO3说法类"], j(c["测试名"]), j(c["方法"]), c["耗尽证据"], "", ""]
          for c in samp[20:]]),
    ], notes=["本机文件，含提取摘要，不提交。前 20 条是含 LiF 的说法，后 10 条是 LiNO₃ 耗尽类说法；随机种子 30。"])
    print(json.dumps(S, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
