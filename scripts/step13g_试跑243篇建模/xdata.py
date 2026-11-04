"""草稿：在 step13f 的数据行基础上加结构特征和截止电压（只读项目文件）。"""
import sys, re, math, json
from collections import Counter, defaultdict
sys.path.insert(0, r"D:\Desktop\课题二锂硫电解液矛盾归因\scripts")
import numpy as np
import step13f_normalize as N
from step13_common import COMP, read_json, load_papers

DESC = read_json("描述符.json", COMP)
DWHOLE = {d["组分"]: d for d in DESC if d["对象"] == "整体"}
DANION = {d["组分"]: d for d in DESC if d["对象"] == "阴离子"}
CTAB = {c["id"]: c for c in read_json("组分表.json", COMP)}
COMPREC = {(r["论文"], r["配方"]): r for r in read_json("配方组成.json", COMP)}
PAPERS = load_papers()

SOLV_KEYS = {  # 溶剂按摩尔分数加权的每分子官能团数
    "醚氧": "醚氧数", "α氟醚氧": "α氟化醚氧数（相邻CF₂/CF₃）", "β氟醚氧": "β氟化醚氧数（隔一个碳为CF₂/CF₃，不含α）",
    "碳酸酯": "碳酸酯基数", "羰基": "羰基数", "酰胺": "酰胺/脲基数", "砜": "砜/亚砜基数", "腈": "腈基数",
    "硫醚S": "硫醚/多硫链S原子数", "F原子": "F原子数", "环": "环数", "TPSA": "TPSA", "分子量": "分子量",
    "可旋转键": "可旋转键数", "C原子": "C原子数",
}


def cutoff(pid, tid):
    d = PAPERS.get(pid)
    if not d:
        return None
    t = next((t for t in d["tests"] if t["id"] == tid), None)
    if not t:
        return None
    ref = t.get("condition_refs", {}).get("voltage_window")
    v = d["condition_definitions"].get(ref, {}).get("value") if ref else None
    if not v:
        return None
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*[–\-~−至到]\s*(\d+(?:\.\d+)?)", str(v))
    if not m:
        return None
    lo = float(m.group(1))
    return lo if 1.0 <= lo <= 2.2 else None


def struct(pid, rid):
    """配方结构特征：溶剂官能团（摩尔分数加权）、阴离子、LiNO3、添加剂类型。"""
    r = COMPREC.get((pid, rid))
    out = {}
    if not r:
        return out, "无配方"
    comps = [i["组分"] for i in r["组分"]]
    solv = [c for c in comps if CTAB.get(c, {}).get("类别") in ("溶剂", "溶剂/添加剂") and c in DWHOLE]
    xf = r.get("摩尔分数") or {}
    vf = r.get("体积分数") or {}
    how = "摩尔分数"
    if solv and all(c in xf for c in solv):
        w = np.array([xf[c] for c in solv])
    elif solv and all(c in vf for c in solv):
        # 体积分数 → 摩尔：用密度/分子量
        dens = read_json("密度表.json", COMP) if False else None
        w = np.array([vf[c] for c in solv]); how = "体积分数近似"
    elif solv:
        w = np.ones(len(solv)); how = "等权（用量缺）"
    if solv:
        w = w / w.sum()
        for k, col in SOLV_KEYS.items():
            out["溶剂_" + k] = float(sum(wi * (DWHOLE[c].get(col) or 0) for wi, c in zip(w, solv)))
        # 每个醚氧上的平均氟化程度、溶剂氟化分子比例
        out["溶剂_含氟分子比例"] = float(sum(wi for wi, c in zip(w, solv) if (DWHOLE[c].get("F原子数") or 0) > 0))
        out["溶剂_有机硫比例"] = float(sum(wi for wi, c in zip(w, solv) if str(CTAB[c].get("化学类别", "")).startswith("有机硫")))
        out["溶剂_碳酸酯比例"] = float(sum(wi for wi, c in zip(w, solv) if "碳酸酯" in str(CTAB[c].get("化学类别", ""))))
        out["溶剂_烃比例"] = float(sum(wi for wi, c in zip(w, solv) if CTAB[c].get("化学类别") == "烃"))
        out["溶剂_环醚比例"] = float(sum(wi for wi, c in zip(w, solv) if CTAB[c].get("化学类别") == "环醚"))
    # 盐：主盐阴离子
    salt_M, aF, aSO2, nsalt = 0.0, 0.0, 0.0, 0
    for i in r["组分"]:
        c = i["组分"]
        if CTAB.get(c, {}).get("类别") == "锂盐" and i["单位类别"] == "摩尔浓度" and i["数值"]:
            salt_M += i["数值"]
            an = DANION.get(c, {})
            aF += i["数值"] * (an.get("F原子数") or 0)
            aSO2 += i["数值"] * (an.get("磺酰基数（磺酰亚胺/磺酸根等，不含砜）") or 0)
            nsalt += 1
    out["主盐_M"] = salt_M or None
    out["阴离子F_每升"] = aF if salt_M else None
    out["阴离子磺酰_每升"] = aSO2 if salt_M else None
    lino3 = next((i for i in r["组分"] if i["组分"] == "LiNO3"), None)
    out["LiNO3_M"] = 0.0 if lino3 is None else (lino3["数值"] if lino3["单位类别"] == "摩尔浓度" else None)
    adds = [c for c in comps if "添加剂" in CTAB.get(c, {}).get("类别", "") and c != "LiNO3" and CTAB.get(c, {}).get("类别") != "溶剂/添加剂"]
    out["介体"] = float(any("介体" in CTAB.get(c, {}).get("类别", "") or CTAB.get(c, {}).get("化学类别") in ("醌", "金属配合物") for c in comps))
    out["含碘"] = float(any(c in ("LiI", "LiI3", "InI3") for c in comps))
    out["其他添加剂"] = float(bool(adds))
    out["有机硫"] = float(any(str(CTAB.get(c, {}).get("化学类别", "")).startswith("有机硫") for c in comps))
    return out, how


def rows_for(cname):
    spec = N.CLASSES[cname]
    cu = "Li‖Cu" in cname
    sts = N.dedup(read_json("表述.json"))
    F = N.Feat({(r["论文"], r["配方"]): r for r in read_json("配方组成.json", COMP)}, CTAB)
    rows = []
    for s in sts:
        if s["标准指标"] in spec["std"] and s["数值类型"] in ("精确", "约数", "范围") and N.yval(s, spec["y"]) is not None \
                and (not spec.get("stage") or s["阶段"] == spec["stage"]):
            st, how = struct(s["论文"], s["recipe"])
            feats = {**F.form(s), **F.cond(s, cu), **st, "截止下限V": cutoff(s["论文"], s["测试"])}
            rows.append(dict(s=s, y=N.yval(s, spec["y"]), x=feats, how=how))
    pc = Counter(r["s"]["论文"] for r in rows)
    rows = [r for r in rows if pc[r["s"]["论文"]] >= 2]
    return rows


if __name__ == "__main__":
    for c in ("放电容量类", "衰减类"):
        rows = rows_for(c)
        print(c, len(rows), "篇", len({r["s"]["论文"] for r in rows}), Counter(r["how"] for r in rows))
        keys = sorted({k for r in rows for k in r["x"]})
        for k in keys:
            vals = [r["x"].get(k) for r in rows]
            nn = [v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))]
            print(f"   {k:14s} 有值 {len(nn):3d}  不同值 {len(set(round(v,4) for v in nn)):3d}")
