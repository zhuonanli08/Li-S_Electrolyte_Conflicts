"""草稿：在 243 篇试跑数据上加溶剂化/物化性质特征（11-04 用户要求逐项试）。
A 组成算出的溶剂化状态：每个 Li⁺ 的可配位位点数（取对数）、稀释剂摩尔比例、Li⁺ 总浓度（每升溶剂）。
  可配位位点（每个溶剂分子）＝不含氟醚氧（α、β 氟化醚氧不算）＋羰基＋砜/亚砜＋P=O＋腈；位点为 0 的溶剂算稀释剂。
B 分子性质（溶剂摩尔分数加权）：介电常数、ln 黏度（PubChem 15–30 °C 实验值）、配位原子最负 Gasteiger 电荷（给电子能力粗近似）。
  任一溶剂缺值则该配方记缺失，不填 0。
C 论文实测：ln 电导率（mS/cm）、ln 黏度（mPa·s），同篇同配方，从原文数值文字重新解析（优先 25 °C/室温）。"""
from pathlib import Path
from feats2 import *

SP = Path(__file__).parent
_MOLF = SP / "溶剂分子性质.json"  # 11-05：文件已移到 243 篇输出的 物性对比/，这里找不到就读那里
if not _MOLF.exists():
    _MOLF = SP.parents[1] / "output" / "表述试跑243篇_2026-11-04" / "物性对比" / "溶剂分子性质.json"
MOL = json.loads(_MOLF.read_text(encoding="utf-8"))
A_COLS = ["ln_配位位点每Li", "稀释剂摩尔比例", "Li总浓度"]
B_COLS = ["介电常数_w", "ln黏度_w", "配位电荷_w"]
C_COLS = ["ln电导率_实测", "ln黏度_实测"]
AL, BE = "α氟化醚氧数（相邻CF₂/CF₃）", "β氟化醚氧数（隔一个碳为CF₂/CF₃，不含α）"


def sites(cid):
    d = DWHOLE.get(cid)
    if not d:
        return None
    eo = max((d.get("醚氧数") or 0) - (d.get(AL) or 0) - (d.get(BE) or 0), 0)
    return eo + (d.get("羰基数") or 0) + (d.get("砜/亚砜基数") or 0) + (d.get("P=O数") or 0) + (d.get("腈基数") or 0)


def solvents(r):
    return [i["组分"] for i in r["组分"] if CTAB.get(i["组分"], {}).get("类别") in ("溶剂", "溶剂/添加剂") and i["组分"] in DWHOLE]


def state(pid, rid):
    r = COMPREC.get((pid, rid)); out = dict.fromkeys(A_COLS)
    if not r:
        return out
    n = r.get("每升溶剂物质的量_mol") or {}
    sv = solvents(r)
    if not sv or any(c not in n for c in sv):
        return out
    li = sum(m for c, m in n.items() if "锂盐" in CTAB.get(c, {}).get("类别", "") or c == "LiNO3")
    tot = sum(n[c] for c in sv)
    coord = sum(n[c] * sites(c) for c in sv)
    dil = sum(n[c] for c in sv if sites(c) == 0)
    if li > 0 and coord > 0:
        out["ln_配位位点每Li"] = math.log(coord / li)
    out["稀释剂摩尔比例"] = dil / tot if tot else None
    out["Li总浓度"] = li or None
    return out


def molprops(pid, rid):
    r = COMPREC.get((pid, rid)); out = dict.fromkeys(B_COLS)
    if not r:
        return out
    sv = solvents(r)
    if not sv:
        return out
    xf, vf = r.get("摩尔分数") or {}, r.get("体积分数") or {}
    w = np.array([xf[c] for c in sv]) if all(c in xf for c in sv) else np.array([vf[c] for c in sv]) if all(c in vf for c in sv) else np.ones(len(sv))
    w = w / w.sum()
    eps = [MOL.get(c, {}).get("介电常数") for c in sv]
    eta = [MOL.get(c, {}).get("黏度cP") for c in sv]
    if all(e is not None for e in eps):
        out["介电常数_w"] = float(np.dot(w, eps))
    if all(e is not None and e > 0 for e in eta):
        out["ln黏度_w"] = float(np.dot(w, np.log(eta)))
    co = [(wi, MOL.get(c, {}).get("最负配位原子电荷")) for wi, c in zip(w, sv) if (sites(c) or 0) > 0]
    if co and all(q is not None for _, q in co):
        ww = np.array([a for a, _ in co]); out["配位电荷_w"] = float(np.dot(ww / ww.sum(), [q for _, q in co]))
    return out


def _num(t):
    m = re.match(r"(\d+(?:\.\d+)?)(?:\s*[×x]\s*10\s*-\s*(\d+))?", t)
    return float(m.group(1)) * (10 ** -int(m.group(2)) if m.group(2) else 1) if m else None


def first_value(t):
    t = t.replace("−", "-").replace("–", "-").replace("℃", "°C")
    m = re.search(r"(?:25\s*°\s*C|室温|RT|room temperature)[^0-9]{0,10}(\d+(?:\.\d+)?(?:\s*[×x]\s*10\s*-\s*\d+)?)", t, re.I)
    if m:
        return _num(m.group(1)), t
    for m in re.finditer(r"(\d+(?:\.\d+)?(?:\s*[×x]\s*10\s*-\s*\d+)?)", t):
        if not re.match(r"\s*°", t[m.end():]):
            return _num(m.group(1)), t
    return None, t


def parse_cond(t):
    v, t = first_value(t)
    if v is None:
        return None
    if re.search(r"[µμ]S", t):
        v /= 1000
    elif re.search(r"(?<![mµμ])S\s*/?\s*cm", t) and not re.search(r"mS", t):
        v *= 1000
    return v if 0.001 <= v <= 100 else None


def parse_visc(t):
    if not re.search(r"cP|mPa|centipoise", t, re.I) and "°" not in t:
        return None
    v, _ = first_value(t)
    return v if v is not None and 0.1 <= v <= 5000 else None


MEAS = defaultdict(lambda: {"cond": [], "visc": []})
for s in read_json("表述.json"):
    k = (s["论文"], s["recipe"])
    for x in s["物性"].get("离子电导率", []):
        if x["来源类型"] == "实测":
            v = parse_cond(str(x["值"]))
            if v: MEAS[k]["cond"].append(v)
    for x in s["物性"].get("黏度", []):
        if x["来源类型"] == "实测":
            v = parse_visc(str(x["值"]))
            if v: MEAS[k]["visc"].append(v)


def measured(pid, rid):
    m = MEAS.get((pid, rid))
    return {"ln电导率_实测": math.log(np.median(m["cond"])) if m and m["cond"] else None,
            "ln黏度_实测": math.log(np.median(m["visc"])) if m and m["visc"] else None}


def class_rows3(cname):
    rows = class_rows2(cname)
    for r in rows:
        k = (r["s"]["论文"], r["s"]["recipe"])
        r["x"].update(state(*k)); r["x"].update(molprops(*k)); r["x"].update(measured(*k))
    return rows
