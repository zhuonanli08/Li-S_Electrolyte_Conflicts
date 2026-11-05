"""step15 第 0 步：方案 A（meta 回归）与方案 B（归一化）共用的测量表和比较表（11-06 用户批准）。

只读 313 篇试跑数据（试跑313篇_2026-11-05、组分结构表_试跑313篇_2026-11-05、表述试跑313篇_2026-11-05），
结果写到 output/meta共同准备_313篇_2026-11-06/。规则（11-05、11-06 用户定）：
- 四类性能分开：首圈容量、每圈衰减率、全电池 CE、Li‖Cu CE。主层 = Li‖S + 硫碳正极，Li‖Cu 单列。字段限制同 feats2
  （不可用论文、被剔除的结果、“非同条件”结果不进；冲突条件置空）。
- 首圈容量：只用初始容量，即首圈；首圈没报的，用前 5 圈内最早的一圈，标“前5圈替代”。“基准未写明”的按硫计，逐条标记；
  超过 1675 mAh g⁻¹（硫的理论容量）或低于 10 的不进。后面圈数的容量不进容量类。
- 每圈衰减率：毕设口径（step13f decay_rate）。圈数不作输入，也不要求两边圈数相同（跨论文看，圈数是结果的代理）。
  另用同一测试的“初始容量＋第 N 圈容量”换算，标“由容量换算”：
  ① 这个测试、这个配方已有保持率或衰减率表述的不换算（论文的保持率通常就是这两个容量算的，防止同一数据算两次）；
  ② 换算出保持率 ≥ 100%（活化）的不进，列入待回原文；③ 两点至少相隔 10 圈。比值与容量基准无关，所以基准未写明的也能用。
- 全电池 CE：只用循环 CE（不含首圈），y = −ln(100 − CE)。Li‖Cu 同样不含首圈。
- Li‖Cu 条件补解析：电流密度补认“0.5 mA/cm2”“0.50mA cm−2”等写法；面容量没写时 = 电流 × 单次沉积时间（标记）；
  测试协议分 Aurbach 法 / 多圈平均 / 单圈。列出多个电流的测试不取值。
- 同一测试、同一配方有多个数值时只留一个（容量取最早的一圈；衰减率取圈数最长的；CE 优先取多圈平均，否则取圈数最大的），
  避免同一颗电池重复计数。
- LiNO₃：没加的记 0；按质量分数给的，用配方组成算出的每升物质的量。
- 16 个候选描述符，分 5 个机制组（见 DESC）；策略按主改动分组，局部高浓单列：按组成判（有稀释剂且每个 Li⁺ 的可配位位点少），
  作者自己的用语另存，两者不一致的列出来。
- 测试名写明是逐行引用其他论文数据的（如 P293“表S1文献44第1行容量”）不进：不同课题组的数据不能当同一篇比较。
- 考试集：沿用 改动模型_313篇_2026-11-05/划分.json 的 31 篇；不在原划分论文全集里的论文一律归开发集。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 common.py
"""
import os
import sys
import re
import math
import json
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
os.environ.setdefault("KETI2_PAPERS", str(ROOT / "output" / "试跑313篇_2026-11-05" / "papers"))
os.environ.setdefault("KETI2_COMP", str(ROOT / "output" / "组分结构表_试跑313篇_2026-11-05"))
os.environ.setdefault("KETI2_OUT", str(ROOT / "output" / "表述试跑313篇_2026-11-05"))
sys.path.insert(0, str(ROOT / "scripts" / "step13g_试跑243篇建模"))
from feats3 import *  # noqa: F401,F403  N、PAPERS、COMPREC、CTAB、struct、state、rd5、字段限制等

OUTD = ROOT / "output" / "meta共同准备_313篇_2026-11-06"
SPLIT = json.loads((ROOT / "output" / "改动模型_313篇_2026-11-05" / "划分.json").read_text(encoding="utf-8"))
TEST = set(SPLIT["考试集论文"])
CLASSES = ["首圈容量", "每圈衰减率", "全电池CE", "LiCu_CE"]
S_THEORY = 1675.0
CAP_STD = ("硫比放电容量", "比放电容量（基准未写明）")

DESC = {  # 机制组 → 描述符（覆盖率见 汇总.json）
    "G1 溶剂化/配位": ["ln_配位位点每Li", "Li总浓度", "稀释剂摩尔比例", "醚氧数"],
    "G2 氟化": ["sO_β氟化醚", "sO_α氟化醚", "溶剂_含氟分子比例", "F/O"],
    "G3 阴离子": ["aF"],
    "G4 添加剂": ["LiNO3_M", "有机硫", "介体", "含碘"],
    "G5 溶剂骨架": ["溶剂_环醚比例", "溶剂_碳酸酯比例", "可旋转键数"],
}
DESC_ALL = [d for g in DESC.values() for d in g]
DESC_GROUP = {d: g for g, ds in DESC.items() for d in ds}
COND = {"首圈容量": ["ln_ES", "载量", "含硫", "ln_倍率", "温度", "软包"],
        "每圈衰减率": ["ln_ES", "载量", "含硫", "ln_倍率", "温度", "软包"],  # 不含圈数（11-05 用户定，11-06 修泄漏）
        "全电池CE": ["ln_ES", "载量", "含硫", "ln_倍率", "温度", "软包", "ln_圈数"],
        "LiCu_CE": ["ln_电流", "ln_沉积容量", "温度", "ln_圈数", "Aurbach法"]}
# 局部高浓 / 高浓的组成判据（只看组成，不看性能；阈值按常见配方定：1 M LiTFSI DOL/DME 每 Li⁺ 约 24 个位点，
# 3 M 以上或 LiFSI:DME:TTE = 1:1.2:3 这类每 Li⁺ ≤ 6 个）
HC_SITES, DIL_MIN = 6.0, 0.2


def ln(x):
    return math.log(x) if x is not None and x > 0 else None


def split_of(p):
    return "考试" if p in TEST else "开发"


# ---------------- 条件 ----------------
def test_of(s):
    return next((t for t in PAPERS[s["论文"]]["tests"] if t["id"] == s["测试"]), {})


def cond_text(s, field):
    d = PAPERS[s["论文"]]
    ref = (test_of(s).get("condition_refs") or {}).get(field)
    v = (d["condition_definitions"].get(ref) or {}).get("value") if ref else None
    return None if v in (None, "未报告") else str(v)


_NUMS = r"(\d+(?:\.\d+)?)"


def one_value(t, unit_re):
    """文字里只出现一个“数＋单位”时取这个数；列出多个值（如 0.2、0.5、1.0 mA cm−2）不取。"""
    if not t:
        return None
    t = t.replace("−", "-").replace("⁻", "-")
    hits = re.findall(_NUMS + r"\s*" + unit_re, t)
    if len(set(hits)) != 1 or re.search(r"\d\s*[、,，/]\s*\d+(?:\.\d+)?\s*" + unit_re, t):
        return None
    return float(hits[0])


def hours(t):
    if not t:
        return None
    m = re.findall(_NUMS + r"\s*(?:h\b|小时|hours?)", t)
    if len(set(m)) == 1:
        return float(m[0])
    m = re.findall(_NUMS + r"\s*(?:min|分钟)", t)
    return float(m[0]) / 60 if len(set(m)) == 1 else None


# Aurbach 法特有写法：储锂量 QT/Qd/Qex、nQc 公式、储备锂、预沉积；连续镀剥的 QP/QS 不算（P384）
AURBACH = re.compile(r"Aurbach|reservoir|储备锂|预沉积|储锂|Q\s*_?\s*[Tt](?![a-z])|Q\s*_?\s*d\s*=|Qex|n\s*Q\s*_?\s*[Cc]")


def cu_cond(s, x, flags):
    cur, cap = x.get("ln_电流"), x.get("ln_沉积容量")
    if cur is None:
        v = one_value(cond_text(s, "rate") or cond_text(s, "current"), r"mA\s*(?:/|\s)?\s*cm")
        if v:
            x["ln_电流"] = ln(v); flags.append("电流补解析")
    if cap is None:
        v = one_value(cond_text(s, "areal_capacity") or cond_text(s, "Li_Cu_capacity"), r"mAh\s*(?:/|\s)?\s*cm")
        if v:
            x["ln_沉积容量"] = ln(v); flags.append("面容量补解析")
        elif x.get("ln_电流") is not None:
            h = hours(cond_text(s, "pulse_duration"))
            if h:
                x["ln_沉积容量"] = ln(math.exp(x["ln_电流"]) * h); flags.append("面容量=电流×时间")
    txt = " ".join(filter(None, [cond_text(s, f) for f in ("lithium_reservoir", "pretreatment", "sampling_point", "normalization",
                                                           "measurement_settings", "other", "cycle_count")] + [test_of(s).get("name", "")]))
    proto = "Aurbach法" if AURBACH.search(txt) else "多圈平均" if s["阶段"] == "平均" else "单圈"
    x["Aurbach法"] = float(proto == "Aurbach法")
    return proto


def conditions(s, cu, flags):
    x = N.Feat.cond(s, cu)
    for f, cid in (test_of(s).get("condition_refs") or {}).items():
        if (s["论文"], cid) in EXCL_COND and FIELD2FEAT.get(f) in x:
            x[FIELD2FEAT[f]] = None
            flags.append(f"条件冲突置空:{f}")
    proto = cu_cond(s, x, flags) if cu else None
    c = s["条件"]
    for k, lab in (("ES", "E/S默认"), ("temperature", "温度默认")):
        if (c.get(k) or {}).get("默认"):
            flags.append(lab)
    return x, proto


# ---------------- 描述符与策略 ----------------
def lino3_M(p, rid, st):
    v = st.get("LiNO3_M")
    if v is not None:
        return v, None
    rec = COMPREC.get((p, rid)) or {}
    n = (rec.get("每升溶剂物质的量_mol") or {}).get("LiNO3")
    return (n, "LiNO3按质量分数换算") if n else (None, None)


def descriptors(s, flags):
    p, rid = s["论文"], s["recipe"]
    er = s["元素比例"] or {}
    st, _ = struct(p, rid)
    sa = state(p, rid)
    r5 = rd5(p, rid)
    d = {"ln_配位位点每Li": sa["ln_配位位点每Li"], "Li总浓度": sa["Li总浓度"], "稀释剂摩尔比例": sa["稀释剂摩尔比例"],
         "醚氧数": r5["醚氧数"], "可旋转键数": r5["可旋转键数"],
         "sO_β氟化醚": er.get("sO_β氟化醚"), "sO_α氟化醚": er.get("sO_α氟化醚"), "F/O": er.get("F/O"), "aF": er.get("aF"),
         **{k: st.get(k) for k in ("溶剂_含氟分子比例", "溶剂_环醚比例", "溶剂_碳酸酯比例", "有机硫", "介体", "含碘", "主盐_M")}}
    d["LiNO3_M"], fl = lino3_M(p, rid, st)
    if fl:
        flags.append(fl)
    if (COMPREC.get((p, rid)) or {}).get("默认"):
        flags.append("溶剂比例默认")
    return d


LHCE_RE = re.compile(r"局部高浓|局域高浓|locali[sz]ed\s*high[- ]?concentrat|LHCE|LHCSE", re.I)
HCE_RE = re.compile(r"(?<!局部)(?<!局域)高浓|(?<!locali[sz]ed )high[- ]concentrat|\bHCE\b|solvent[- ]in[- ]salt", re.I)
WEAK_RE = re.compile(r"弱溶剂化|weakly[- ]solvat|\bWSE\b", re.I)
SPARSE_RE = re.compile(r"难溶|sparingly[- ]solvat|\bSSE\b", re.I)


def author_labels(p):
    d = PAPERS[p]
    txt = " ".join([c.get("summary", "") for c in d.get("design_claims") or []] + [f.get("name", "") for f in d.get("formulations") or []])
    return sorted(k for k, r in (("局部高浓", LHCE_RE), ("高浓", HCE_RE), ("弱溶剂化", WEAK_RE), ("难溶", SPARSE_RE)) if r.search(txt))


def salt_solvent_ratio(p, rid):
    """（每个主盐 Li⁺ 的可配位位点数，稀释剂摩尔比例）。只按主盐的锂算（LiNO₃ 是添加剂，P111 F10 加 1 M LiNO₃ 不算高浓）；
    稀释剂 = 可配位位点为 0 的溶剂，离子液体不算。没有每升物质的量时，全部盐和溶剂都按摩尔份／分子数给出的直接用份数（P248、P338）。"""
    rec = COMPREC.get((p, rid))
    if not rec:
        return None, None
    sv = [c for c in solvents(rec) if CTAB.get(c, {}).get("化学类别") != "离子液体"]
    salt = [i["组分"] for i in rec["组分"] if CTAB.get(i["组分"], {}).get("类别") == "锂盐"]
    n = rec.get("每升溶剂物质的量_mol") or {}
    if not (sv and salt and all(c in n for c in sv + salt)):
        it = {i["组分"]: i for i in rec["组分"]}
        if not (sv and salt and all(it[c]["单位类别"] in ("摩尔比", "分子数") and it[c]["数值"] for c in sv + salt)):
            return None, None
        n = {c: it[c]["数值"] for c in sv + salt}
    li = sum(n[c] for c in salt)
    tot = sum(n[c] for c in sv)
    coord = sum(n[c] * (sites(c) or 0) for c in sv)
    return (coord / li if li else None), (sum(n[c] for c in sv if (sites(c) or 0) == 0) / tot if tot else None)


def comp_class(p, rid, flags=None):
    """按组成判：局部高浓（稀释剂 ≥ 20 mol% 且每个主盐 Li⁺ ≤ 6 个可配位位点）、高浓（稀释剂不足但每 Li⁺ ≤ 6）、常规。
    组成算不出时：作者自称局部高浓、且配方含可配位位点为 0 的氟化醚，记局部高浓并标“局部高浓按作者用语”。"""
    r, dil = salt_solvent_ratio(p, rid)
    if r is None:
        c = comps(p, rid) or {}
        if "局部高浓" in author_labels(p) and any(CTAB.get(k, {}).get("化学类别") == "氟化醚" and sites(k) == 0 for k in c):
            if flags is not None:
                flags.append("局部高浓按作者用语")
            return "局部高浓"
        return None
    if r == 0:  # 只有单一弱配位溶剂（P371 F4DEE、P369 DMMS、P278 FPY3），没有溶剂化溶剂，不是局部高浓
        return "无配位溶剂"
    if r <= HC_SITES:
        return "局部高浓" if (dil or 0) >= DIL_MIN else "高浓"
    return "常规"


def comps(p, rid):
    rec = COMPREC.get((p, rid))
    return {i["组分"]: i for i in rec["组分"]} if rec else None


def kind_of(c):
    t = CTAB.get(c, {})
    cat, chem = t.get("类别", ""), str(t.get("化学类别", ""))
    if c == "LiNO3":
        return "LiNO3"
    if c in ("LiI", "LiI3", "InI3"):
        return "含碘"
    if "介体" in cat or chem in ("醌", "金属配合物"):
        return "介体"
    if cat == "锂盐":
        return "主盐"
    if cat in ("溶剂", "溶剂/添加剂"):
        return "氟化醚" if chem == "氟化醚" else "有机硫" if chem.startswith("有机硫") else "溶剂"
    if chem.startswith("有机硫"):
        return "有机硫"
    return "添加剂"


PRIORITY = ["局部高浓", "高浓", "加介体", "加含碘添加剂", "加有机硫", "加其他添加剂", "加/换氟化醚", "换溶剂（其他）", "换主盐",
            "LiNO₃ 用量", "改浓度/配比"]


def main_change(p, rid_exp, rid_ref, d_exp, d_ref):
    """实验配方相对参照配方的主改动（按 PRIORITY 取第一个），以及全部改动。"""
    if rid_exp == rid_ref:
        return "同配方", []
    ce, cr = comps(p, rid_exp), comps(p, rid_ref)
    ch = []
    ke, kr = comp_class(p, rid_exp), comp_class(p, rid_ref)
    if ke in ("局部高浓", "高浓") and ke != kr:
        ch.append(ke)
    if ce is None or cr is None:
        return (ch[0] if ch else "组成不明"), ch
    add = set(ce) - set(cr)
    rem = set(cr) - set(ce)
    kinds_add = {kind_of(c) for c in add}
    kinds_chg = kinds_add | {kind_of(c) for c in rem}
    for k, lab in (("介体", "加介体"), ("含碘", "加含碘添加剂"), ("有机硫", "加有机硫"), ("添加剂", "加其他添加剂")):
        if k in kinds_add:
            ch.append(lab)
    if "氟化醚" in kinds_chg:
        ch.append("加/换氟化醚")
    if "溶剂" in kinds_chg:
        ch.append("换溶剂（其他）")
    if "主盐" in kinds_chg:
        ch.append("换主盐")
    if "LiNO3" in kinds_chg or (d_exp.get("LiNO3_M") is not None and d_ref.get("LiNO3_M") is not None
                                and abs(d_exp["LiNO3_M"] - d_ref["LiNO3_M"]) > 1e-6):
        ch.append("LiNO₃ 用量")
    if not ch:
        ch.append("改浓度/配比")
    ch = sorted(set(ch), key=PRIORITY.index)
    return ch[0], ch


def recipe_key(p, rid, d):
    """跨论文的配方身份：组分集合＋主盐浓度（0.1 M）＋溶剂体积分数（0.1）＋LiNO₃（0.05 M）。组成不明时只在本篇内唯一。"""
    rec = COMPREC.get((p, rid))
    if not rec or rec.get("状态") != "完整":
        return f"{p}:{rid}"
    vf = rec.get("体积分数") or {}
    parts = []
    for c in sorted(i["组分"] for i in rec["组分"]):
        if c == "LiNO3":
            parts.append(f"LiNO3={round((d.get('LiNO3_M') or 0) / 0.05) * 0.05:.2f}" if d.get("LiNO3_M") is not None else f"LiNO3=?{p}")
        elif kind_of(c) == "主盐":
            m = (comps(p, rid)[c].get("数值") if comps(p, rid)[c].get("单位类别") == "摩尔浓度" else None)
            parts.append(f"{c}={round(m, 1)}" if m else f"{c}=?{p}")
        elif c in vf:
            parts.append(f"{c}={round(vf[c], 1)}")
        else:
            parts.append(f"{c}=?{p}")
    return "|".join(parts)


def is_std_ether(p, rid, d):
    """标准醚：LiTFSI 0.8–1.2 M，溶剂只有 DOL+DME 且 DOL 体积分数 0.4–0.6，除 LiNO₃ 外无其他组分。"""
    c = comps(p, rid)
    rec = COMPREC.get((p, rid)) or {}
    if not c or set(c) - {"LiTFSI", "DOL", "DME", "LiNO3"} or not {"LiTFSI", "DOL", "DME"} <= set(c):
        return False
    m = c["LiTFSI"].get("数值") if c["LiTFSI"].get("单位类别") == "摩尔浓度" else None
    vf = (rec.get("体积分数") or {}).get("DOL")
    return m is not None and 0.8 <= m <= 1.2 and vf is not None and 0.4 <= vf <= 0.6


# ---------------- 测量表 ----------------
LIT_TEST = re.compile(r"文献\s*\d+")


def base_ok(s, cu, drop):
    if s["数值类型"] not in ("精确", "约数", "范围") or s["数值"] is None:
        return False
    if s["论文"] in BAD_PAPERS:
        drop["论文不可用"] += 1; return False
    if not cu and (s["电池类型"] != "Li‖S" or s["正极类型"] != "硫碳类"):
        drop["非主层"] += 1; return False
    if LIT_TEST.search(test_of(s).get("name", "")):  # 11-06：P293 表 S1 逐行引用他文数据（文献 16、36–52），不是本篇测量
        drop["引用他文数据"] += 1; return False
    res = {(s["论文"], str(r).lower()) for r in s.get("来源结果") or []}
    if res & EXCL_RES:
        drop["结果被限制剔除"] += 1; return False
    if res & NONCOMP:
        drop["非同条件结果"] += 1; return False
    return True


def cyc(s):
    try:
        return int(s["圈数"])
    except (TypeError, ValueError):
        return None


def make_row(cls, s, y, flags, extra=None):
    fl = list(flags)
    cu = cls == "LiCu_CE"
    x, proto = conditions(s, cu, fl)
    d = descriptors(s, fl)
    p = s["论文"]
    row = {"类别": cls, "论文": p, "划分": split_of(p), "测试": s["测试"], "recipe": s["recipe"], "配方": s["配方"],
           "配方名": s.get("配方名"), "是否对照": bool(s["是否对照"]), "表述": s["表述编号"], "标准指标": s["标准指标"],
           "阶段": s["阶段"], "圈数": cyc(s), "数值": s["数值"], "y": y, "条件": {k: x.get(k) for k in COND[cls]},
           "圈数_ln": ln(cyc(s)), "描述符": d, "组成类": comp_class(p, s["recipe"], fl), "标准醚": is_std_ether(p, s["recipe"], d),
           "配方键": recipe_key(p, s["recipe"], d), "标记": sorted(set(fl))}
    if proto:
        row["协议"] = proto
    row.update(extra or {})
    return row


def build():
    sts = N.dedup(read_json("表述.json"))
    drop = defaultdict(Counter)
    out, todo = [], []
    # ---- 首圈容量 ----
    cand = {}
    for s in sts:
        if s["标准指标"] not in CAP_STD:
            continue
        n = cyc(s)
        order = 1 if s["阶段"] == "首圈" else n if s["阶段"] == "第 N 圈" and n is not None and n <= 5 else None
        if order is None or not base_ok(s, False, drop["首圈容量"]):
            continue
        v = s["数值"]
        if not 10 <= v <= S_THEORY:
            drop["首圈容量"]["<10 或 >1675"] += 1
            if v > S_THEORY:
                todo.append({"类别": "首圈容量", "论文": s["论文"], "表述": s["表述编号"], "数值": v, "问题": "超过硫理论容量" + ("（原文明写按硫计：含碳、有机硫等其他物种贡献，不代表硫利用率）" if s["标准指标"] == "硫比放电容量" else "（基准未写明，按硫计不可能）"),
                             "核对": "11-06 已对原句，原文数值",
                             "原句": s["原句"][:300]})
            continue
        k = (s["论文"], s["测试"], s["recipe"])
        key = (order, s["标准指标"] != "硫比放电容量")
        if k not in cand or key < cand[k][0]:
            cand[k] = (key, s)
    init = {}
    for k, (key, s) in cand.items():
        fl = (["基准未写明"] if key[1] else []) + (["前5圈替代"] if key[0] > 1 else [])
        out.append(make_row("首圈容量", s, math.log(s["数值"]), fl))
        init[k] = (key[0], s)
    # ---- 每圈衰减率 ----
    spec = N.CLASSES["衰减类"]
    have_decay, dec = set(), {}
    for s in sts:
        if s["标准指标"] not in spec["std"]:
            continue
        have_decay.add((s["论文"], s["测试"], s["recipe"]))
        y = N.yval(s, "decay")
        if y is None or not base_ok(s, False, drop["每圈衰减率"]):
            continue
        k = (s["论文"], s["测试"], s["recipe"])
        n = N.cycles_elapsed(s) or cyc(s) or 0
        if k not in dec or n > dec[k][0]:
            dec[k] = (n, s, y)
    for k, (n, s, y) in dec.items():
        out.append(make_row("每圈衰减率", s, y, [], {"经历圈数": n or None, "来源": "保持率/衰减率表述"}))
    conv = {}
    for s in sts:  # 由容量换算（可选扩充，标记）
        if s["标准指标"] not in CAP_STD or s["阶段"] != "第 N 圈" or cyc(s) is None:
            continue
        k = (s["论文"], s["测试"], s["recipe"])
        if k in have_decay or k not in init or not base_ok(s, False, Counter()):
            continue
        n0, s0 = init[k]
        if cyc(s) - n0 < 10:
            continue
        R = 100 * s["数值"] / s0["数值"]
        if R >= 100:
            todo.append({"类别": "每圈衰减率（由容量换算）", "论文": s["论文"], "表述": [s0["表述编号"], s["表述编号"]],
                         "数值": [s0["数值"], s["数值"]], "问题": f"第{cyc(s)}圈容量 ≥ 第{n0}圈（保持率 {R:.0f}%，可能是活化）；每圈衰减率 ≤ 0 不能取对数，不进",
                         "核对": "11-06 已对原句，原文数值",
                         "原句": s["原句"][:300]})
            continue
        if k not in conv or cyc(s) > cyc(conv[k][0]):
            conv[k] = (s, s0, n0, R)
    for k, (s, s0, n0, R) in conv.items():
        d = (100 - R) / (cyc(s) - n0)
        fl = ["由容量换算"] + (["基准不一致"] if s["标准指标"] != s0["标准指标"] else [])
        out.append(make_row("每圈衰减率", s, -math.log(d), fl,
                            {"经历圈数": cyc(s) - n0, "来源": f"由容量换算（{s0['表述编号']} 第{n0}圈 {s0['数值']} → 第{cyc(s)}圈 {s['数值']}）"}))
    # ---- CE ----
    for cls, std, cu in (("全电池CE", "全电池 CE", False), ("LiCu_CE", "Li‖Cu CE", True)):
        best = {}
        for s in sts:
            if s["标准指标"] != std or s["阶段"] == "首圈":
                continue
            y = N.yval(s, "loss")
            if y is None or not base_ok(s, cu, drop[cls]):
                continue
            k = (s["论文"], s["测试"], s["recipe"])
            key = (s["阶段"] == "平均", cyc(s) or 0)
            if k not in best or key > best[k][0]:
                best[k] = (key, s, y)
        for k, (key, s, y) in best.items():
            out.append(make_row(cls, s, y, []))
    pc = Counter((r["类别"], r["论文"]) for r in out)
    for r in out:
        if pc[(r["类别"], r["论文"])] < 2:
            r["标记"].append("本篇只有1个")
    return out, drop, todo


# ---------------- 比较表（方案 A） ----------------
def build_pairs(rows):
    """每篇 n 个测量 → n−1 个比较（规则同 step14 pairs.py）：同测试里有对照配方 → 和它比；否则和本篇参照测量比，
    参照 = 本篇对照配方在配方数最多的那个测试里的测量。容量、衰减率按测试分组（圈数不要求相同），CE 按测试＋圈数分组。"""
    out = []
    for cls in CLASSES:
        byp = defaultdict(list)
        for r in rows:
            if r["类别"] == cls:
                byp[r["论文"]].append(r)
        for p, rs in byp.items():
            if len(rs) < 2:
                continue
            grp = defaultdict(list)
            for r in rs:
                grp[(r["测试"],) if cls in ("首圈容量", "每圈衰减率") else (r["测试"], r["圈数"])].append(r)
            ctl = [r for r in rs if r["是否对照"]] or rs
            big = max(grp.values(), key=lambda g: len({r["recipe"] for r in g}))
            ref = next((r for r in big if r in ctl), ctl[0])
            for g in grp.values():
                gref = next((r for r in g if r["是否对照"]), None)
                for a in g:
                    if a is ref:
                        continue
                    if gref is not None and a is not gref and a["recipe"] != gref["recipe"]:
                        b, kind = gref, "同测试、不同配方"
                    else:
                        b = ref
                        kind = "同配方、换条件" if a["recipe"] == b["recipe"] else "跨测试、不同配方"
                    mc, allc = main_change(p, a["recipe"], b["recipe"], a["描述符"], b["描述符"])
                    na, nb = a.get("经历圈数") or a["圈数"], b.get("经历圈数") or b["圈数"]
                    out.append({"类别": cls, "论文": p, "划分": a["划分"], "配对类型": kind, "实验": a["表述"], "参照": b["表述"],
                                "实验测试": a["测试"], "参照测试": b["测试"], "实验配方": a["配方"], "参照配方": b["配方"],
                                "dy": a["y"] - b["y"], "主改动": mc, "全部改动": allc,
                                "Δ描述符": {k: (None if a["描述符"].get(k) is None or b["描述符"].get(k) is None
                                             else a["描述符"][k] - b["描述符"][k]) for k in DESC_ALL},
                                "参照描述符": {k: b["描述符"].get(k) for k in DESC_ALL},
                                "Δ条件": {k: (0.0 if kind == "同测试、不同配方" else None if a["条件"].get(k) is None or b["条件"].get(k) is None
                                           else a["条件"][k] - b["条件"][k]) for k in COND[cls]},
                                "参照条件": dict(b["条件"]), "圈数比": (max(na, nb) / min(na, nb)) if na and nb else None,
                                "标记": sorted(set(a["标记"]) | set(b["标记"]) - {"本篇只有1个"})})
    return out


def coverage(rows):
    cov = {}
    for cls in CLASSES:
        rs = [r for r in rows if r["类别"] == cls and r["划分"] == "开发"]
        cov[cls] = {k: round(sum(r["描述符"].get(k) is not None for r in rs) / max(len(rs), 1), 2) for k in DESC_ALL}
        cov[cls].update({f"条件:{k}": round(sum(r["条件"].get(k) is not None for r in rs) / max(len(rs), 1), 2) for k in COND[cls]})
    return cov


if __name__ == "__main__":
    OUTD.mkdir(parents=True, exist_ok=True)
    rows, drop, todo = build()
    pairs = build_pairs(rows)
    labels = {p: author_labels(p) for p in sorted({r["论文"] for r in rows})}
    # 局部高浓：组成判定 vs 作者用语
    lhce = []
    for p in labels:
        comp_l = sorted({r["配方"] for r in rows if r["论文"] == p and r["组成类"] == "局部高浓"})
        auth = "局部高浓" in labels[p]
        if bool(comp_l) != auth:
            lhce.append({"论文": p, "组成判为局部高浓的配方": comp_l, "作者用语": labels[p],
                         "说明": "组成像局部高浓、作者没这样说" if comp_l else "作者说局部高浓、组成未达判据（或组成不明）"})
    summ = {"说明": "第 0 步测量表与比较表（初步、未裁定，AI 辅助，用户尚未逐项确认）",
            "测量点": {c: {"开发": sum(r["类别"] == c and r["划分"] == "开发" for r in rows),
                        "考试": sum(r["类别"] == c and r["划分"] == "考试" for r in rows),
                        "论文": len({r["论文"] for r in rows if r["类别"] == c})} for c in CLASSES},
            "比较": {c: dict(Counter(q["配对类型"] for q in pairs if q["类别"] == c and q["划分"] == "开发")) for c in CLASSES},
            "标记计数": {c: dict(Counter(f for r in rows if r["类别"] == c for f in r["标记"])) for c in CLASSES},
            "剔除计数": {c: dict(v) for c, v in drop.items()},
            "Li‖Cu协议": dict(Counter(r["协议"] for r in rows if r["类别"] == "LiCu_CE")),
            "组成类": {c: dict(Counter(r["组成类"] for r in rows if r["类别"] == c)) for c in CLASSES},
            "主改动（开发集、不同配方）": {c: dict(Counter(q["主改动"] for q in pairs if q["类别"] == c and q["划分"] == "开发"
                                               and q["配对类型"] != "同配方、换条件")) for c in CLASSES},
            "标准醚测量点": {c: sum(r["类别"] == c and r["标准醚"] for r in rows) for c in CLASSES},
            "描述符与条件覆盖率（开发集）": coverage(rows),
            "规则": __doc__}
    for name, obj in (("测量表.json", rows), ("比较表.json", pairs), ("待回原文.json", todo), ("局部高浓_组成与作者用语不一致.json", lhce),
                      ("作者策略用语.json", labels), ("汇总.json", summ)):
        (OUTD / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    # Li‖Cu 补解析抽查：列出全部补出来的条件与原文
    chk = [{"论文": r["论文"], "测试": r["测试"], "标记": [f for f in r["标记"] if "补解析" in f or "电流×时间" in f],
            "ln_电流→mA cm⁻²": round(math.exp(r["条件"]["ln_电流"]), 3) if r["条件"]["ln_电流"] is not None else None,
            "ln_沉积容量→mAh cm⁻²": round(math.exp(r["条件"]["ln_沉积容量"]), 3) if r["条件"]["ln_沉积容量"] is not None else None,
            "协议": r["协议"]} for r in rows if r["类别"] == "LiCu_CE"]
    (OUTD / "LiCu条件解析.json").write_text(json.dumps(chk, ensure_ascii=False, indent=1), encoding="utf-8")
    for c in CLASSES:
        m = summ["测量点"][c]
        print(f"{c}：测量点 开发 {m['开发']} / 考试 {m['考试']}（{m['论文']} 篇）；开发集比较 {summ['比较'][c]}")
    print("标记：", json.dumps(summ["标记计数"], ensure_ascii=False))
    print("Li‖Cu 协议：", summ["Li‖Cu协议"], "；组成类：", json.dumps(summ["组成类"], ensure_ascii=False))
    print("待回原文", len(todo), "条；局部高浓 组成与作者用语不一致", len(lhce), "篇")
