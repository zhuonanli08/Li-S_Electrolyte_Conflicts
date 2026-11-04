"""草稿：11-04 用户确认的输入特征（第 1 步取舍结果）。
配方：13 个元素比例（sO 另带三档）＋ RDKit 中元素比例没有的 5 个（溶剂按摩尔分数加权）＋ LiNO3 浓度、添加剂类别。
条件：E/S、硫载量、正极含硫、倍率、温度、软包、圈数（首圈容量不用）、截止电压下限；Li‖Cu 用电流、沉积容量、温度、圈数。
线性模型不放 O、C、F、sO（它们分别等于分项之和）。"""
from xdata import *

ER = ["sO", "sO_不含氟", "sO_β氟化醚", "sO_α氟化醚", "aO", "C", "sC", "aC", "O", "F", "sF", "aF", "F/C", "O/C", "F/O", "InOr"]
ER_SUM = {"O", "C", "F", "sO"}
RD5 = {"醚氧数": "醚氧数", "环数": "环数", "可旋转键数": "可旋转键数", "碳酸酯基数": "碳酸酯基数", "硫醚/多硫S": "硫醚/多硫链S原子数"}
OTHER = ["LiNO3浓度M", "介体", "其他添加剂"]
FORM_ALL = ER + list(RD5) + OTHER
FORM_LIN = [c for c in FORM_ALL if c not in ER_SUM]
COND_LIS = ["ln_ES", "载量", "含硫", "ln_倍率", "温度", "软包", "ln_圈数", "截止下限V"]
LINEAR = {"线性岭回归", "线性混合模型"}


def rd5(pid, rid):
    r = COMPREC.get((pid, rid))
    out = {k: None for k in RD5}
    if not r:
        return out
    solv = [i["组分"] for i in r["组分"] if CTAB.get(i["组分"], {}).get("类别") in ("溶剂", "溶剂/添加剂") and i["组分"] in DWHOLE]
    if not solv:
        return out
    xf, vf = r.get("摩尔分数") or {}, r.get("体积分数") or {}
    w = np.array([xf[c] for c in solv]) if all(c in xf for c in solv) else \
        np.array([vf[c] for c in solv]) if all(c in vf for c in solv) else np.ones(len(solv))
    w = w / w.sum()
    return {k: float(sum(wi * (DWHOLE[c].get(col) or 0) for wi, c in zip(w, solv))) for k, col in RD5.items()}


def other(pid, rid):
    r = COMPREC.get((pid, rid))
    if not r:
        return {k: None for k in OTHER}
    comps = [i["组分"] for i in r["组分"]]
    l = next((i for i in r["组分"] if i["组分"] == "LiNO3"), None)
    return {"LiNO3浓度M": 0.0 if l is None else (l["数值"] if l["单位类别"] == "摩尔浓度" else None),
            "介体": float(any("介体" in CTAB.get(c, {}).get("类别", "") or CTAB.get(c, {}).get("化学类别") in ("醌", "金属配合物") for c in comps)),
            "其他添加剂": float(any("添加剂" in CTAB.get(c, {}).get("类别", "") and c != "LiNO3" and CTAB.get(c, {}).get("类别") != "溶剂/添加剂" for c in comps))}


def class_rows(cname):
    spec = N.CLASSES[cname]
    cu = "Li‖Cu" in cname
    rows = []
    for s in N.dedup(read_json("表述.json")):
        if s["标准指标"] in spec["std"] and s["数值类型"] in ("精确", "约数", "范围") and N.yval(s, spec["y"]) is not None \
                and (not spec.get("stage") or s["阶段"] == spec["stage"]):
            er = s["元素比例"] or {}
            x = {k: er.get(k) for k in ER}
            x.update(rd5(s["论文"], s["recipe"]))
            x.update(other(s["论文"], s["recipe"]))
            x.update(N.Feat.cond(s, cu))
            x["截止下限V"] = None if cu else cutoff(s["论文"], s["测试"])
            rows.append(dict(s=s, y=N.yval(s, spec["y"]), x=x))
    pc = Counter(r["s"]["论文"] for r in rows)
    return [r for r in rows if pc[r["s"]["论文"]] >= 2]


def cols_for(cname, rows, linear):
    cu = "Li‖Cu" in cname
    cond = N.COND_CU if cu else [c for c in COND_LIS if not (N.CLASSES[cname].get("stage") and c == "ln_圈数")]
    base = (FORM_LIN if linear else FORM_ALL) + cond
    return [c for c in base if sum(r["x"].get(c) is not None for r in rows) >= 3
            and len({round(r["x"][c], 6) for r in rows if r["x"].get(c) is not None}) > 1]
