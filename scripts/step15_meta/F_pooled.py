"""step15 F：全部文献一起分析（11-06 用户要求：数据量要够、用用户自己的分子结构描述符、所有文献一起分析而不是单独比较；先不做补值）。

数据：第 0 步 v2 测量表（全部 313 篇的全部测量，含只测了一个配方的论文）；描述符用 step13h 的结构描述符（用户的 28 个里去掉 Kim 元素比例 6 个，
     剩 22 个：溶剂结构 15、溶剂化状态 3、盐与添加剂 4）；LiNO₃ 用第 0 步 v2 的 LiNO3_M（质量分数已换算，覆盖更全）。
     只用室温附近的测量（15–35 °C；没写温度的按 25 °C，同 11-05 用户定），借鉴 Yari 等 2025 剔除非室温电池的做法。
模型（多层模型的篇内/篇间分解，Mundlak 1978；Bell & Jones 2015）：
  y = 条件 + β_同测试·(x − 本测试均值) + β_跨测试·(本测试均值 − 本篇均值) + β_篇间·本篇均值 + 论文随机截距 + 误差。
  同测试 β 只用同一个测试里换配方的差别（条件完全相同，最干净，主证据）；跨测试 β 是同一篇里不同测试之间的差别（条件靠协变量扣）；
  篇间 β 来自不同论文整体用的配方不同，受实验室差异与“谁研究什么”影响，只作旁证：与同测试同向才算跨文献也站得住。
  条件：方案 A 的条件列＋温度；缺的按本类中位数补（不补描述符，描述符缺的测量不进该描述符的模型）。效应写成“描述符变 1 个标准差，性能变几倍”。
① 单描述符：22 个描述符各估一次，用该描述符有值的全部测量（数据量最大）；篇内 p 做 BH 校正（每类 22 个）。
② 去重叠：跨配方 |ρ| ≥ 0.5 的描述符归为同一条轴（平均连接聚类）（数据得出，见 轴.json），每条轴取一个代表放进同一个模型（只用代表都有值的测量）。
结果写到 output/meta_v3_全部测量_313篇_2026-11-06/。初步、未裁定；AI 辅助，用户尚未逐项人工确认。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 F_pooled.py
"""
import sys
import json
import math
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy import stats
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))
import step13h_descriptor_figures as H
import A_meta as A
from mm import fit_mixed, bh

IN = ROOT / "output" / "meta共同准备_313篇_v2_2026-11-06"
OUT = ROOT / "output" / "meta_v3_全部测量_313篇_2026-11-06"
CLASSES = A.CLASSES
KEYS = [k for k, _, f in H.DESCS if f != "Elemental ratio"]  # 22 个
LAB = dict(H.DLAB)
LAB["lino3"] = "LiNO₃ (M)"
T_LO, T_HI = 15.0, 35.0
# 去重叠的轴：成员按跨配方 |ρ| ≥ 0.6 归组（main() 里重新计算并核对）；代表 = 化学含义清楚、篇内有变化的论文多
AXES = {"Coordination (ether O)": {"代表": "lnsites", "成员": ["lnsites", "eo"], "中文": "配位（醚氧）"},
        "Fluorination & dilution": {"代表": "ffrac", "成员": ["ffrac", "fat", "eo_a", "dil"], "中文": "氟化/稀释"},
        "Salt amount": {"代表": "salt", "成员": ["salt", "li", "anF", "anSO2"], "中文": "盐用量"},
        "Solvent backbone": {"代表": "rotb", "成员": ["rotb", "ring", "mw"], "中文": "溶剂骨架"},
        "Carbonyl / carbonate": {"代表": "carbonate", "成员": ["carbonate", "carbonyl"], "中文": "羰基/碳酸酯"},
        "LiNO₃": {"代表": "lino3", "成员": ["lino3"], "中文": "LiNO₃"},
        "Other groups": {"代表": None, "成员": ["tpsa", "eo_b", "sulfone", "nitrile", "amide", "thio"], "中文": "其他（单独成组或数据少）"}}
AXIS_OF = {m: a for a, v in AXES.items() for m in v["成员"]}


def jdump(path, obj):
    def conv(o):
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=conv), encoding="utf-8")


def load():
    M = json.loads((IN / "测量表.json").read_text(encoding="utf-8"))
    keep, drop_t = [], defaultdict(int)
    for r in M:
        t = r["条件"].get("温度")
        if t is not None and not (T_LO <= t <= T_HI):
            drop_t[r["类别"]] += 1
            continue
        h, how = H.descriptors(r["论文"], r["recipe"])
        r["D"] = {k: h.get(k) for k in KEYS}
        r["D"]["lino3"] = r["描述符"].get("LiNO3_M")
        r["权重来源"] = how
        keep.append(r)
    return keep, dict(drop_t)


def cond_matrix(rows, cls):
    cond = list(A.COND[cls]) + ([] if "温度" in A.COND[cls] else ["温度"])
    C = np.array([[r["条件"].get(c) if r["条件"].get(c) is not None else np.nan for c in cond] for r in rows], float)
    med = np.nanmedian(C, 0)
    med = np.where(np.isnan(med), 0.0, med)
    return np.where(np.isnan(C), med, C), cond


LEVELS = (("T", "同测试"), ("C", "跨测试"), ("B", "篇间"))


def within_between(rows, ds, sd):
    pap = [r["论文"] for r in rows]
    tst = [(r["论文"], r["测试"]) for r in rows]
    cols, names = [], []
    for d in ds:
        x = np.array([r["D"][d] for r in rows], float)
        bp, bt = defaultdict(list), defaultdict(list)
        for p, t, xi in zip(pap, tst, x):
            bp[p].append(xi)
            bt[t].append(xi)
        xp = np.array([np.mean(bp[p]) for p in pap])
        xt = np.array([np.mean(bt[t]) for t in tst])
        cols += [(x - xt) / sd[d], (xt - xp) / sd[d], xp / sd[d]]
        names += [f"T:{d}", f"C:{d}", f"B:{d}"]
    return cols, names


def fit(rows, cls, ds, sd):
    C, cond = cond_matrix(rows, cls)
    cols, names = within_between(rows, ds, sd)
    X = np.column_stack([C] + cols)
    y = np.array([r["y"] for r in rows])
    res = fit_mixed(y, X, [r["论文"] for r in rows], cond + names)
    out = {}
    for d in ds:
        e = {}
        for t, lab in LEVELS:
            j = res["names"].index(f"{t}:{d}")
            b, se = float(res["b"][j]), float(res["se"][j])
            e[lab] = {"倍数_每1SD": math.exp(b), "区间": [math.exp(b - 1.96 * se), math.exp(b + 1.96 * se)], "p": float(res["p"][j]), "β": b, "SE": se}
        out[d] = e
    return out, res["方法"], float(res["tau2"]), float(res["sigma2"])


def nvary(rows, d, test=False):
    """篇内有变化的论文数；test=True 时只数“同一个测试里就有变化”的论文。"""
    by = defaultdict(set)
    for r in rows:
        by[(r["论文"], r["测试"]) if test else r["论文"]].add(round(r["D"][d], 6))
    return len({k[0] if test else k for k, v in by.items() if len(v) > 1})


def verdict(e):
    w, b = e["同测试"], e["篇间"]
    if w.get("q", 1) >= 0.1:
        return "同测试不显著"
    same = np.sign(w["β"]) == np.sign(b["β"])
    if same and b["p"] < 0.05:
        return "同测试与篇间同向且都显著"
    return "同测试显著、篇间同向" if same else "同测试显著、篇间反向"


def vif_T(rows, ds, sd):
    cols, _ = within_between(rows, ds, sd)
    X = np.column_stack(cols[0::3])  # 只看同测试分量
    X = X[np.abs(X).sum(1) > 0]
    if len(X) < len(ds) + 3:
        return None
    X = (X - X.mean(0)) / np.where(X.std(0) > 0, X.std(0), 1)
    out = {}
    for k, d in enumerate(ds):
        y, Z = X[:, k], np.column_stack([np.ones(len(X)), np.delete(X, k, 1)])
        b, *_ = np.linalg.lstsq(Z, y, rcond=None)
        r2 = 1 - ((y - Z @ b) ** 2).sum() / max(((y - y.mean()) ** 2).sum(), 1e-12)
        out[d] = round(float(1 / max(1 - r2, 1e-9)), 2)
    return out


def overlap(rows):
    F = {}
    for r in rows:
        F[(r["论文"], r["recipe"])] = r["D"]
    ks = [k for k in KEYS if sum(v.get(k) is not None for v in F.values()) > 100 and np.std([v[k] for v in F.values() if v.get(k) is not None]) > 0]
    n = len(ks)
    R = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            v = [(x[ks[i]], x[ks[j]]) for x in F.values() if x.get(ks[i]) is not None and x.get(ks[j]) is not None]
            R[i, j] = R[j, i] = stats.spearmanr(*zip(*v))[0] if len(v) > 20 else 0.0
    R = np.nan_to_num(R)
    lab = fcluster(linkage(squareform(1 - np.abs(R), checks=False), "average"), 0.5, "distance")
    groups = defaultdict(list)
    for k, l in zip(ks, lab):
        groups[int(l)].append(k)
    pairs = [{"a": ks[i], "b": ks[j], "ρ": float(R[i, j])} for i in range(n) for j in range(i + 1, n) if abs(R[i, j]) >= 0.5]
    return {"描述符": ks, "相关矩阵": R.tolist(), "配方数": len(F), "数据聚类_|ρ|≥0.5": list(groups.values()), "|ρ|≥0.5 的对": pairs}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    M, drop_t = load()
    ov = overlap(M)
    res = {"说明": __doc__.split("用法")[0].strip(), "非室温剔除": drop_t, "轴": AXES, "重叠": ov, "单描述符": {}, "去重叠联合": {}, "覆盖": {}}
    for cls in CLASSES:
        R0 = [r for r in M if r["类别"] == cls]
        sd = {d: float(np.std([r["D"][d] for r in R0 if r["D"][d] is not None]) or 1.0) for d in KEYS}
        single = {}
        for d in KEYS:
            rows = [r for r in R0 if r["D"][d] is not None]
            nv = nvary(rows, d)
            cov = {"测量": len(rows), "论文": len({r['论文'] for r in rows}), "篇内有变化的论文": nv, "同测试有变化的论文": nvary(rows, d, True)}
            if nv < 3 or sd[d] <= 1e-9:
                single[d] = {**cov, "状态": "数据不足（篇内有变化的论文 < 3）"}
                continue
            e, meth, tau2, s2 = fit(rows, cls, [d], sd)
            single[d] = {**cov, "状态": "已估计", "方法": meth, **e[d]}
        est = [d for d in single if single[d]["状态"] == "已估计"]
        for d, q in zip(est, bh([single[d]["同测试"]["p"] for d in est])):
            single[d]["同测试"]["q"] = float(q)
        for d in est:
            single[d]["判断"] = verdict(single[d])
        res["单描述符"][cls] = single
        res["覆盖"][cls] = {"测量": len(R0), "论文": len({r['论文'] for r in R0})}
        reps = [v["代表"] for v in AXES.values() if v["代表"]]
        rows = [r for r in R0 if all(r["D"][d] is not None for d in reps)]
        use = [d for d in reps if nvary(rows, d, True) >= 5 and np.std([r["D"][d] for r in rows]) > 0]
        rows = [r for r in R0 if all(r["D"][d] is not None for d in use)]
        e, meth, tau2, s2 = fit(rows, cls, use, sd)
        res["去重叠联合"][cls] = {"测量": len(rows), "论文": len({r['论文'] for r in rows}), "方法": meth, "代表": use,
                              "同测试有变化的论文": {d: nvary(rows, d, True) for d in use}, "结果": e, "论文间方差": tau2, "篇内方差": s2,
                              "VIF_同测试": vif_T(rows, use, sd)}
    jdump(OUT / "汇总.json", res)
    # 屏幕摘要
    print("非室温剔除", drop_t)
    print("数据聚类（|ρ| ≥ 0.5）：", [[LAB[k] for k in g] for g in ov["数据聚类_|ρ|≥0.5"]])
    for cls in CLASSES:
        print(f"\n== {cls}：{res['覆盖'][cls]}")
        for d, s_ in res["单描述符"][cls].items():
            if s_["状态"] == "已估计" and (s_["同测试"]["q"] < 0.1 or d in ("lnsites", "salt", "ffrac")):
                t, c, b = s_["同测试"], s_["跨测试"], s_["篇间"]
                print(f"  {LAB[d]:<32} 同测试 ×{t['倍数_每1SD']:.2f} q={t['q']:.3f} | 跨测试 ×{c['倍数_每1SD']:.2f} p={c['p']:.3f}"
                      f" | 篇间 ×{b['倍数_每1SD']:.2f} p={b['p']:.3f} | {s_['测量']}/{s_['论文']} 篇，同测试变化 {s_['同测试有变化的论文']} 篇 · {s_['判断']}")
        j_ = res["去重叠联合"][cls]
        print(f"  联合（{j_['测量']} 测量/{j_['论文']} 篇；VIF {j_['VIF_同测试']}）：")
        for d in j_["代表"]:
            t, b = j_["结果"][d]["同测试"], j_["结果"][d]["篇间"]
            print(f"     {LAB[d]:<32} 同测试 ×{t['倍数_每1SD']:.2f} [{t['区间'][0]:.2f}, {t['区间'][1]:.2f}] p={t['p']:.3f} | 篇间 ×{b['倍数_每1SD']:.2f} p={b['p']:.3f}")


if __name__ == "__main__":
    main()
