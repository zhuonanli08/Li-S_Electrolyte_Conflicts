"""step15 方案 B：归一化（比较“绝对值”，11-06 用户批准）。

数据：第 0 步测量表，每行 = 论文 × 测试 × 配方的一个数值（同一测试同一配方只留一个）。四类性能分开做。
范围：只用 15–35 °C 的测量（含未写按 25 °C 的），因为要换算到 25 °C 标准条件，低温、高温测量外推不可靠。
Li⁺ 总浓度取对数（同方案 A）。考试集只在 --exam 时用一次。
B1 只在论文内部学条件效应：y = g(条件) + 每个“论文 × 配方”一个截距 + 误差，用组内去均值（固定效应），所以 g 只能从
   同一篇、同一配方在不同条件下的变化里学出来。g = 线性项（相对标准条件居中）＋事先指定的交互：锂硫类
   ln倍率 × 载量、ln E/S × 载量；Li‖Cu ln电流 × ln沉积容量。岭回归，惩罚按论文分组的内层 5 折选；系数区间按论文重抽样 200 次。
   缺值：组内有观测值的用组内均值补，整组都缺的用标准值补（组内常数，去均值后不起作用）。
   检查方向是否符合物理常识（容量：E/S ↑、载量 ↓、倍率 ↓；衰减率倒数：E/S ↑、载量 ↓；Li‖Cu：电流 ↓）。
B2 换算：y_标准 = y − g(实测条件)（g 在标准条件下为 0）；另按实用条件（E/S 5、载量 4）算 y_实用 = y_标准 + g(实用)。
   原文没报告的条件按上面的补法，逐条标记“条件补值”。
   标准条件（11-04 用户定）：E/S 10、载量 1.5、含硫 50%、扣式、0.2 C；全电池 CE 100 圈；Li‖Cu 0.5 mA cm⁻²、1 mAh cm⁻²、100 圈、非 Aurbach。
B3 分离实验室效应、加入描述符：y_标准 = 总体 + β·描述符 + 论文随机效应 + 配方身份随机效应 + 误差（statsmodels 交叉随机效应）。
   配方身份 = 第 0 步配方键，LiNO₃ 改为分档（0 / ≤0.15 / ≤0.3 / >0.3 M），让同一种基础配方能跨论文对上。
   ① 16 个描述符一次一个（与方案 A 对照方向）；② 方案 A 选出的描述符一起再估一遍。
B4 验证（开发集按论文 5 折；考试集只用一次）：
   ① B1 的 g 能否预测留出论文里“同配方换条件”的变化（对照“条件变了性能不变”）；
   ② 标准醚的跨论文离散度（各篇平均值的标准差），归一化前后；
   ③ 锚点预测：每篇留出论文取一个锚点（本篇标准醚，没有就取对照），预测本篇其余测量：
      ŷ = y锚 + [g(条件) − g(锚条件)] + β·(描述符 − 锚描述符) + (配方身份效应 − 锚的配方身份效应，训练里见过才用)；
      基线 = 与锚点相同、锚点＋条件效应。指标：相对锚点的差值 R²、均方误差、篇内排序一致率。
B5 产出：标准条件、实用条件下的配方排名（扣掉论文效应，近似区间）、策略排名（相对标准醚）、描述符效应与方案 A 对比。
成功标准（事先定）：B1 优于“条件变了性能不变”；归一化后标准醚离散度变小；锚点预测的均方误差在开发集和考试集上都低于
   “与锚点相同”基线（按论文重抽样的差值 95% 区间不含 0）。
用法：python -X utf8 B_normalize.py          （开发集，写 预先登记.json）
      python -X utf8 B_normalize.py --exam   （考试集只算一次）
"""
import sys
import json
import math
import re
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
from sklearn.model_selection import GroupKFold

sys.path.insert(0, str(Path(__file__).parent))
from mm import fit_mixed, bh, concordance, r2, boot_by_paper, font, Ridge

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
IN = ROOT / "output" / "meta共同准备_313篇_2026-11-06"
OUT = ROOT / "output" / "方案B_归一化_313篇_2026-11-06"
AOUT = ROOT / "output" / "方案A_meta回归_313篇_2026-11-06"
CLASSES = ["首圈容量", "每圈衰减率", "全电池CE", "LiCu_CE"]
DESC = {"G1 溶剂化/配位": ["ln_配位位点每Li", "ln_Li总浓度", "稀释剂摩尔比例", "醚氧数"],
        "G2 氟化": ["sO_β氟化醚", "sO_α氟化醚", "溶剂_含氟分子比例", "F/O"],
        "G3 阴离子": ["aF"],
        "G4 添加剂": ["LiNO3_M", "有机硫", "介体", "含碘"],
        "G5 溶剂骨架": ["溶剂_环醚比例", "溶剂_碳酸酯比例", "可旋转键数"]}
DESC_ALL = [d for g in DESC.values() for d in g]
COND = {"首圈容量": ["ln_ES", "载量", "含硫", "ln_倍率", "软包"],
        "每圈衰减率": ["ln_ES", "载量", "含硫", "ln_倍率", "软包"],
        "全电池CE": ["ln_ES", "载量", "含硫", "ln_倍率", "软包", "ln_圈数"],
        "LiCu_CE": ["ln_电流", "ln_沉积容量", "ln_圈数", "Aurbach法"]}
INTER = {"首圈容量": [("ln_倍率", "载量"), ("ln_ES", "载量")], "每圈衰减率": [("ln_倍率", "载量"), ("ln_ES", "载量")],
         "全电池CE": [("ln_倍率", "载量"), ("ln_ES", "载量")], "LiCu_CE": [("ln_电流", "ln_沉积容量")]}
STD = {"ln_ES": math.log(10), "载量": 1.5, "含硫": 50.0, "软包": 0.0, "ln_倍率": math.log(0.2), "ln_圈数": math.log(100),
       "ln_电流": math.log(0.5), "ln_沉积容量": math.log(1.0), "Aurbach法": 0.0}
PRACT = {"ln_ES": math.log(5), "载量": 4.0}
PHYS = {"首圈容量": {"ln_ES": 1, "载量": -1, "ln_倍率": -1}, "每圈衰减率": {"ln_ES": 1, "载量": -1},
        "全电池CE": {}, "LiCu_CE": {"ln_电流": -1}}
TEMP = (15.0, 35.0)
UNIT = {"首圈容量": ("mAh g⁻¹", lambda y: math.exp(y)), "每圈衰减率": ("%/圈", lambda y: math.exp(-y)),
        "全电池CE": ("%", lambda y: 100 - math.exp(-y)), "LiCu_CE": ("%", lambda y: 100 - math.exp(-y))}
NOTE = "初步、未裁定；AI 辅助，用户尚未逐项人工确认"


def lino3_bin(v):
    return "0" if v == 0 else "≤0.15" if v <= 0.15 else "≤0.3" if v <= 0.3 else ">0.3"


def load():
    M = json.loads((IN / "测量表.json").read_text(encoding="utf-8"))
    out, drop = [], Counter()
    for r in M:
        t = r["条件"].get("温度") if "温度" in r["条件"] else None
        v = r["描述符"].pop("Li总浓度", None)
        r["描述符"]["ln_Li总浓度"] = math.log(v) if v else None
        if t is not None and not TEMP[0] <= t <= TEMP[1]:
            drop[r["类别"]] += 1
            continue
        k = r["配方键"]
        if "LiNO3=" in k and r["描述符"].get("LiNO3_M") is not None:
            k = re.sub(r"LiNO3=[^|]+", "LiNO3=" + lino3_bin(r["描述符"]["LiNO3_M"]), k)
        r["身份"] = k
        out.append(r)
    return out, drop


# ---------------- B1 ----------------
def zmat(R, cls, fill=None):
    """条件相对标准值居中；fill = {(论文, recipe): {条件: 组内均值}} 用于补缺；返回 (Z, 列名, 每行是否补值)。"""
    cols = COND[cls]
    Z, filled = [], []
    for r in R:
        g = (fill or {}).get((r["论文"], r["recipe"]), {})
        row, f = [], False
        for k in cols:
            v = r["条件"].get(k)
            if v is None:
                v = g.get(k, STD[k]); f = True
            row.append(v - STD[k])
        z = dict(zip(cols, row))
        row += [z[a] * z[b] for a, b in INTER[cls]]
        Z.append(row); filled.append(f)
    return np.array(Z, float), cols + [f"{a}×{b}" for a, b in INTER[cls]], filled


def group_fill(R, cls):
    by = defaultdict(lambda: defaultdict(list))
    for r in R:
        for k in COND[cls]:
            if r["条件"].get(k) is not None:
                by[(r["论文"], r["recipe"])][k].append(r["条件"][k])
    return {g: {k: float(np.mean(v)) for k, v in d.items()} for g, d in by.items()}


def within(R, Z, y):
    """组内去均值；只留有 ≥2 行的“论文 × 配方”组。"""
    by = defaultdict(list)
    for i, r in enumerate(R):
        by[(r["论文"], r["recipe"])].append(i)
    idx = [i for g in by.values() if len(g) >= 2 for i in g]
    Zd, yd = Z.copy(), y.copy()
    for g in by.values():
        Zd[g] -= Z[g].mean(0); yd[g] -= y[g].mean()
    return idx, Zd, yd


class G:
    """条件效应 g（相对标准条件）。"""

    def fit(self, R, cls, lam=None):
        self.cls = cls
        self.fill = group_fill(R, cls)
        Z, self.names, _ = zmat(R, cls, self.fill)
        y = np.array([r["y"] for r in R])
        idx, Zd, yd = within(R, Z, y)
        self.n_rows, self.n_groups = len(idx), len({(R[i]["论文"], R[i]["recipe"]) for i in idx})
        self.n_papers = len({R[i]["论文"] for i in idx})
        if len(idx) < 5 or self.n_papers < 3:
            self.coef = np.zeros(len(self.names)); self.lam = None
            return self
        m = Ridge(lam).fit(Zd[idx], yd[idx], [R[i]["论文"] for i in idx])
        self.lam = m.lam
        self.coef = m.coef()
        return self

    def __call__(self, R, fill=None):
        """fill 不给时用训练集的组内均值补缺；留出论文传它自己的 group_fill。"""
        Z, _, filled = zmat(R, self.cls, fill if fill is not None else getattr(self, "fill", None))
        return Z @ self.coef, filled

    def at(self, cond):
        r = {"论文": "", "recipe": "", "条件": cond}
        return float((zmat([r], self.cls)[0] @ self.coef)[0])


def g_ci(R, cls, lam, n=200, seed=0):
    rng = np.random.default_rng(seed)
    by = defaultdict(list)
    for r in R:
        by[r["论文"]].append(r)
    ps = sorted(by)
    B = []
    for _ in range(n):
        S = [dict(r, 论文=f"{r['论文']}#{j}") for j, p in enumerate(rng.choice(ps, len(ps))) for r in by[p]]
        B.append(G().fit(S, cls, lam).coef)
    B = np.array(B)
    return np.percentile(B, 2.5, 0), np.percentile(B, 97.5, 0)


def b1_cv(R, cls):
    """留出论文里同配方换条件的变化：预测组内偏差 vs 实测；基线 = 0（条件变了性能不变）。"""
    pa = np.array([r["论文"] for r in R])
    obs, pred, grp = [], [], []
    for tr, te in GroupKFold(5).split(R, groups=pa):
        g = G().fit([R[i] for i in tr], cls)
        Re = [R[i] for i in te]
        Z, _, _ = zmat(Re, cls, group_fill(Re, cls))
        y = np.array([r["y"] for r in Re])
        idx, Zd, yd = within(Re, Z, y)
        obs += list(yd[idx]); pred += list(Zd[idx] @ g.coef); grp += [Re[i]["论文"] for i in idx]
    obs, pred = np.array(obs), np.array(pred)
    if len(obs) < 3:
        return {"n": len(obs)}
    mse_m, mse_0 = float(np.mean((obs - pred) ** 2)), float(np.mean(obs ** 2))
    pidx = defaultdict(list)
    for i, p in enumerate(grp):
        pidx[p].append(i)
    ci = boot_by_paper(lambda ps: float(np.mean([(obs[i] - pred[i]) ** 2 - obs[i] ** 2 for p in ps for i in pidx[p]])), grp)
    return {"n": len(obs), "论文": len(set(grp)), "R²（对 0 基线）": 1 - mse_m / mse_0 if mse_0 > 0 else None,
            "均方误差_g": mse_m, "均方误差_不变": mse_0, "差值（g−不变）95%区间": ci,
            "篇内排序一致率": concordance(pred, obs, grp)[0]}


# ---------------- B3 ----------------
def crossed(R, y, X, names):
    """y ~ X + 论文随机效应 + 配方身份随机效应；失败时退回只有论文随机效应。"""
    import pandas as pd
    import statsmodels.formula.api as smf
    d = pd.DataFrame({"y": y, "paper": [r["论文"] for r in R], "rkey": [r["身份"] for r in R], "one": 1})
    cols = []
    for i in range(X.shape[1]):
        if np.std(X[:, i]) > 1e-9:
            d[f"x{i}"] = X[:, i]; cols.append(i)
    f = "y ~ " + (" + ".join(f"x{i}" for i in cols) if cols else "1")
    for meth in (["lbfgs"], ["powell"]):
        try:
            m = smf.mixedlm(f, d, groups="one", re_formula="0", vc_formula={"paper": "0 + C(paper)", "rkey": "0 + C(rkey)"}).fit(reml=True, method=meth)
            if not m.converged:
                continue
            vc = dict(zip(m.model.exog_vc.names, np.asarray(m.vcomp)))
            re_ = m.random_effects[1]
            up = {re.search(r"\[(?:T\.)?([^\[\]]+)\]\]$", k).group(1): float(v) for k, v in re_.items() if k.startswith("paper[")}
            ur = {re.search(r"C\(rkey\)\[(.+)\]\]$", k).group(1): float(v) for k, v in re_.items() if k.startswith("rkey[")}
            b = {"截距": float(m.fe_params["Intercept"])}
            se = {"截距": float(m.bse["Intercept"])}
            for i in cols:
                b[names[i]] = float(m.fe_params[f"x{i}"]); se[names[i]] = float(m.bse[f"x{i}"])
            return {"b": b, "se": se, "τ²_论文": float(vc["paper"]), "τ²_配方": float(vc["rkey"]), "σ²": float(m.scale),
                    "论文效应": up, "配方效应": ur, "方法": "交叉随机效应"}
        except Exception:
            continue
    r = fit_mixed(y, X[:, cols] if cols else np.zeros((len(y), 0)), [q["论文"] for q in R], [names[i] for i in cols])
    return {"b": dict(zip(r["names"], r["b"])), "se": dict(zip(r["names"], r["se"])), "τ²_论文": r["tau2"], "τ²_配方": None,
            "σ²": r["sigma2"], "论文效应": r["re"], "配方效应": {}, "方法": "只有论文随机效应（" + r["方法"] + "）"}


def dvec(R, d):
    return np.array([np.nan if r["描述符"].get(d) is None else r["描述符"][d] for r in R], float)


def screen_b(R, ystd, cls):
    out = []
    for d in DESC_ALL:
        x = dvec(R, d)
        ok = ~np.isnan(x)
        Rk = [r for r, o in zip(R, ok) if o]
        if len({r["论文"] for r in Rk}) < 5 or np.std(x[ok]) < 1e-9:
            out.append({"描述符": d, "状态": "数据不足"}); continue
        res = crossed(Rk, ystd[ok], x[ok][:, None], [d])
        if d not in res["b"]:
            out.append({"描述符": d, "状态": "无变化"}); continue
        b, se = res["b"][d], res["se"][d]
        sd = float(np.std(x[ok]))
        from scipy import stats
        out.append({"描述符": d, "状态": "已估计", "方法": res["方法"], "行": int(ok.sum()), "论文": len({r['论文'] for r in Rk}),
                    "β": b, "SE": se, "p": float(2 * stats.norm.sf(abs(b / se))) if se > 0 else None, "描述符标准差": sd,
                    "倍数_每1SD": math.exp(b * sd), "倍数95%区间": [math.exp((b - 1.96 * se) * sd), math.exp((b + 1.96 * se) * sd)]})
    q = bh([e.get("p") if e.get("p") is not None else np.nan for e in out])
    for e, qq in zip(out, q):
        e["q"] = None if not np.isfinite(qq) else float(qq)
    return out


# ---------------- B4 ----------------
def anchor_of(rs):
    by_t = Counter(r["测试"] for r in rs)
    order = sorted(rs, key=lambda r: (not r["标准醚"], not r["是否对照"], -by_t[r["测试"]]))
    return order[0]


def anchor_eval(train, test, cls, descs):
    """在 train 上学 g 和 B3，预测 test 每篇相对锚点的差值。返回每行 (论文, 实测差, 预测差_完整, 预测差_条件)。"""
    g = G().fit(train, cls)
    gt, _ = g(train)
    ystd = np.array([r["y"] for r in train]) - gt
    X = np.column_stack([dvec(train, d) for d in descs]) if descs else np.zeros((len(train), 0))
    keep = ~np.isnan(X).any(1) if descs else np.ones(len(train), bool)
    res = crossed([r for r, k in zip(train, keep) if k], ystd[keep], X[keep], descs)
    by = defaultdict(list)
    for r in test:
        by[r["论文"]].append(r)
    ft = group_fill(test, cls)
    rows = []
    for p, rs in by.items():
        if len(rs) < 2:
            continue
        a = anchor_of(rs)
        ga = g([a], ft)[0][0]
        for r in rs:
            if r is a:
                continue
            gc = g([r], ft)[0][0] - ga
            dd = sum(res["b"].get(d, 0) * ((r["描述符"].get(d) or 0) - (a["描述符"].get(d) or 0))
                     for d in descs if r["描述符"].get(d) is not None and a["描述符"].get(d) is not None)
            ur = res["配方效应"]
            du = (ur.get(r["身份"], 0) - ur.get(a["身份"], 0)) if r["身份"] in ur and a["身份"] in ur else 0.0
            rows.append((p, r["y"] - a["y"], gc + dd + du, gc, r["身份"] in ur))
    return rows


def anchor_metrics(rows):
    if len(rows) < 3:
        return {"n": len(rows)}
    p = [x[0] for x in rows]
    o = np.array([x[1] for x in rows]); f = np.array([x[2] for x in rows]); c = np.array([x[3] for x in rows])
    pidx = defaultdict(list)
    for i, q in enumerate(p):
        pidx[q].append(i)
    out = {"n": len(rows), "论文": len(set(p)), "配方身份在训练里见过": int(sum(x[4] for x in rows))}
    for lab, pr in (("完整", f), ("锚点＋条件", c), ("与锚点相同", np.zeros(len(o)))):
        out[lab] = {"均方误差": float(np.mean((o - pr) ** 2)), "R²（差值）": r2(o, pr), "篇内排序一致率": concordance(pr, o, p)[0]}
    out["完整−与锚点相同 均方误差差 95%区间"] = boot_by_paper(lambda ps: float(np.mean([(o[i] - f[i]) ** 2 - o[i] ** 2 for q in ps for i in pidx[q]])), p)
    out["完整−锚点＋条件 均方误差差 95%区间"] = boot_by_paper(lambda ps: float(np.mean([(o[i] - f[i]) ** 2 - (o[i] - c[i]) ** 2 for q in ps for i in pidx[q]])), p)
    return out


def std_ether_spread(R, ystd):
    by_raw, by_std = defaultdict(list), defaultdict(list)
    for r, s in zip(R, ystd):
        if r["标准醚"]:
            by_raw[r["论文"]].append(r["y"]); by_std[r["论文"]].append(s)
    ps = sorted(by_raw)
    if len(ps) < 3:
        return {"论文": len(ps)}
    raw = np.array([np.mean(by_raw[p]) for p in ps]); st = np.array([np.mean(by_std[p]) for p in ps])
    idx = {p: i for i, p in enumerate(ps)}
    ci = boot_by_paper(lambda q: float(np.std(st[[idx[x] for x in q]], ddof=1) / np.std(raw[[idx[x] for x in q]], ddof=1))
                       if np.std(raw[[idx[x] for x in q]]) > 0 else None, ps)
    return {"论文": len(ps), "测量": int(sum(len(v) for v in by_raw.values())), "SD_归一化前": float(np.std(raw, ddof=1)),
            "SD_归一化后": float(np.std(st, ddof=1)), "比值": float(np.std(st, ddof=1) / np.std(raw, ddof=1)), "比值95%区间": ci}


# ---------------- B5 ----------------
def tag(r):
    d = r["描述符"]
    if r.get("组成类") in ("局部高浓", "高浓", "无配位溶剂"):
        return r["组成类"]
    if r["标准醚"]:
        return "标准醚"
    if d.get("介体"):
        return "含介体"
    if d.get("含碘"):
        return "含碘"
    if d.get("有机硫"):
        return "含有机硫"
    if (d.get("溶剂_含氟分子比例") or 0) > 0:
        return "含氟化溶剂"
    if (d.get("溶剂_碳酸酯比例") or 0) > 0:
        return "含碳酸酯"
    return "其他常规"


def rankings(R, ystd, yprac, res0, cls):
    unit, inv = UNIT[cls]
    up = res0["论文效应"]
    ref = [s - up.get(r["论文"], 0) for r, s in zip(R, ystd) if r["标准醚"]]
    ref_m = float(np.mean(ref)) if ref else None
    by = defaultdict(list)
    for i, r in enumerate(R):
        by[r["身份"]].append(i)
    out = []
    for k, ix in by.items():
        adj = [ystd[i] - up.get(R[i]["论文"], 0) for i in ix]
        adjp = [yprac[i] - up.get(R[i]["论文"], 0) for i in ix]
        ps = sorted({R[i]["论文"] for i in ix})
        half = 1.96 * math.sqrt(res0["σ²"] / len(ix) + (res0["τ²_论文"] or 0) / len(ps))
        m, mp = float(np.mean(adj)), float(np.mean(adjp))
        out.append({"配方身份": k, "配方名": R[ix[0]]["配方名"], "策略": tag(R[ix[0]]), "论文": ps, "测量": len(ix),
                    f"标准条件（{unit}）": inv(m), "标准条件近似区间": sorted([inv(m - half), inv(m + half)]),
                    f"实用条件（{unit}）": inv(mp) if cls != "LiCu_CE" else None,
                    "相对标准醚（ln，越大越好）": None if ref_m is None else m - ref_m, "条件补值": any(R[i]["_补值"] for i in ix)})
    return sorted(out, key=lambda e: -(e["相对标准醚（ln，越大越好）"] or -99))


def strategy_b(R, ystd):
    tags = [tag(r) for r in R]
    levels = [t for t, _ in Counter(tags).most_common() if t != "标准醚" and sum(1 for x, r in zip(tags, R) if x == t) >= 3
              and len({r["论文"] for x, r in zip(tags, R) if x == t}) >= 3]
    if not any(t == "标准醚" for t in tags):
        return {"状态": "没有标准醚测量，无法作参照"}
    keep = [i for i, t in enumerate(tags) if t == "标准醚" or t in levels]
    Rk = [R[i] for i in keep]
    X = np.array([[float(tags[i] == t) for t in levels] for i in keep]).reshape(len(keep), -1)
    res = crossed(Rk, ystd[keep], X, levels)
    out = {"方法": res["方法"], "参照": "标准醚", "组": {}}
    for t in levels:
        if t in res["b"]:
            b, se = res["b"][t], res["se"][t]
            out["组"][t] = {"测量": sum(x == t for x in tags), "论文": len({r["论文"] for x, r in zip(tags, R) if x == t}),
                           "相对标准醚倍数": math.exp(b), "95%区间": [math.exp(b - 1.96 * se), math.exp(b + 1.96 * se)]}
    return out


# ---------------- 主流程 ----------------
def jdump(name, obj):
    def conv(o):
        if isinstance(o, (np.floating, np.integer, np.bool_)):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=conv), encoding="utf-8")


def a_selected():
    f = AOUT / "预先登记.json"
    return json.loads(f.read_text(encoding="utf-8"))["A4选中描述符"] if f.exists() else {c: [] for c in CLASSES}


def figures(b1, spread, scr, scr_a):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    font()
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.8))
    for ax, cls in zip(axes, CLASSES):
        e = b1[cls]
        names = e["列"]
        y = np.arange(len(names))
        ax.barh(y, e["系数"], color=["#c0392b" if e["物理方向"].get(n) == "相反" else "#2980b9" for n in names])
        lo, hi = np.array(e["95%区间"]).T if e["95%区间"] else (None, None)
        if lo is not None:
            ax.errorbar(e["系数"], y, xerr=[np.array(e["系数"]) - lo, hi - np.array(e["系数"])], fmt="none", color="k", lw=0.8)
        ax.set_yticks(y); ax.set_yticklabels(names, fontsize=8); ax.invert_yaxis(); ax.axvline(0, color="k", lw=0.8)
        ax.set_title(f"{cls}（{e['论文']} 篇 {e['组']} 组）", fontsize=10); ax.set_xlabel("每单位条件变化的效应（ln）", fontsize=8)
    fig.suptitle("方案 B｜B1 条件效应（只用同一篇同一配方换条件；红 = 与物理常识相反）　初步", fontsize=12)
    fig.tight_layout(); fig.savefig(OUT / "图B1_条件效应.png", dpi=170); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    cs = [c for c in CLASSES if "SD_归一化前" in spread[c]]
    x = np.arange(len(cs))
    ax.bar(x - 0.18, [spread[c]["SD_归一化前"] for c in cs], 0.36, label="归一化前", color="#95a5a6")
    ax.bar(x + 0.18, [spread[c]["SD_归一化后"] for c in cs], 0.36, label="归一化后", color="#2980b9")
    for i, c in enumerate(cs):
        ax.text(i, max(spread[c]["SD_归一化前"], spread[c]["SD_归一化后"]) * 1.03, f"{spread[c]['论文']} 篇", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(cs); ax.set_ylabel("标准醚各篇平均值的标准差（ln）"); ax.legend()
    ax.set_title("方案 B｜标准醚跨论文离散度，归一化前后　初步", fontsize=11)
    fig.tight_layout(); fig.savefig(OUT / "图B2_标准醚离散度.png", dpi=170); plt.close(fig)
    fig, axes = plt.subplots(1, 4, figsize=(17, 6.5), sharey=True)
    for ax, cls in zip(axes, CLASSES):
        for j, d in enumerate(DESC_ALL):
            e = next(e for e in scr[cls] if e["描述符"] == d)
            ea = next((x for x in scr_a.get(cls, []) if x["描述符"] == d), None)
            if e.get("状态") == "已估计":
                lo, hi = [math.log(v) for v in e["倍数95%区间"]]
                ax.plot([lo, hi], [j + 0.15, j + 0.15], color="#2980b9"); ax.plot(math.log(e["倍数_每1SD"]), j + 0.15, "o", color="#2980b9", ms=5)
            if ea and ea.get("状态") == "已估计" and ea.get("标准化效应_ln") is not None:
                m = ea["标准化效应_ln"]; lo, hi = np.array(ea["95%区间"]) * ea["描述符标准差"]
                ax.plot([lo, hi], [j - 0.15, j - 0.15], color="#e67e22"); ax.plot(m, j - 0.15, "s", color="#e67e22", ms=5)
        ax.axvline(0, color="k", lw=0.8); ax.set_title(cls, fontsize=10); ax.set_xlabel("每 1 SD 的效应（ln，>0 = 变好）", fontsize=8)
    axes[0].set_yticks(range(len(DESC_ALL))); axes[0].set_yticklabels(DESC_ALL, fontsize=8); axes[0].invert_yaxis()
    axes[0].plot([], [], "o", color="#2980b9", label="方案 B（绝对值）"); axes[0].plot([], [], "s", color="#e67e22", label="方案 A（差值）")
    axes[0].legend(fontsize=8, loc="lower left")
    fig.suptitle("方案 B｜描述符效应，与方案 A 对照　初步", fontsize=12)
    fig.tight_layout(); fig.savefig(OUT / "图B3_描述符AB对照.png", dpi=170); plt.close(fig)


def main_dev():
    OUT.mkdir(parents=True, exist_ok=True)
    M, drop = load()
    sel = a_selected()
    scr_a = json.loads((AOUT / "A2_描述符筛查.json").read_text(encoding="utf-8"))["结果"] if (AOUT / "A2_描述符筛查.json").exists() else {}
    b1, b1v, spread, scr, multi, anchor, ranks, strat, norm_rows, agree = {}, {}, {}, {}, {}, {}, {}, {}, [], {}
    for cls in CLASSES:
        R = [r for r in M if r["类别"] == cls and r["划分"] == "开发"]
        print(f"\n=== {cls}：开发集测量 {len(R)}（{len({r['论文'] for r in R})} 篇；温度范围外剔除 {drop[cls]}）", flush=True)
        g = G().fit(R, cls)
        lo, hi = g_ci(R, cls, g.lam) if g.lam else (None, None)
        phys = {n: ("" if n not in PHYS[cls] else "符合" if np.sign(c) == PHYS[cls][n] else "相反") for n, c in zip(g.names, g.coef)}
        b1[cls] = {"λ": g.lam, "列": g.names, "系数": g.coef.tolist(), "95%区间": None if lo is None else [[float(a), float(b)] for a, b in zip(lo, hi)],
                   "物理方向": phys, "行": g.n_rows, "组": g.n_groups, "论文": g.n_papers}
        b1v[cls] = b1_cv(R, cls)
        print("  B1 g:", {n: round(float(c), 3) for n, c in zip(g.names, g.coef)}, "物理:", {k: v for k, v in phys.items() if v}, flush=True)
        print("  B1 留出验证:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in b1v[cls].items()}, flush=True)
        gt, filled = g(R)
        for r, f in zip(R, filled):
            r["_补值"] = f
        ystd = np.array([r["y"] for r in R]) - gt
        gp = g.at({**{k: STD[k] for k in COND[cls]}, **{k: v for k, v in PRACT.items() if k in COND[cls]}})
        yprac = ystd + gp
        spread[cls] = std_ether_spread(R, ystd)
        print("  标准醚离散度:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in spread[cls].items()}, flush=True)
        res0 = crossed(R, ystd, np.zeros((len(R), 0)), [])
        scr[cls] = screen_b(R, ystd, cls)
        agree[cls] = []
        for e in scr[cls]:
            ea = next((x for x in scr_a.get(cls, []) if x["描述符"] == e["描述符"]), None)
            if e.get("状态") == "已估计" and ea and ea.get("状态") == "已估计":
                agree[cls].append({"描述符": e["描述符"], "B倍数": e["倍数_每1SD"], "B_q": e["q"], "A倍数": ea["倍数_每1SD"], "A_q": ea["q"],
                                   "方向一致": bool(np.sign(math.log(e["倍数_每1SD"])) == np.sign(math.log(ea["倍数_每1SD"]))),
                                   "两边都 q<0.1": bool((e["q"] or 1) < 0.1 and (ea["q"] or 1) < 0.1)})
        for e in scr[cls]:
            if e.get("状态") == "已估计" and (e["q"] or 1) < 0.2:
                print(f"  B3 {e['描述符']:14s} 倍数/SD {e['倍数_每1SD']:.3f} [{e['倍数95%区间'][0]:.3f},{e['倍数95%区间'][1]:.3f}] q {e['q']:.3f}", flush=True)
        if sel.get(cls):
            X = np.column_stack([dvec(R, d) for d in sel[cls]]); k = ~np.isnan(X).any(1)
            multi[cls] = crossed([r for r, kk in zip(R, k) if kk], ystd[k], X[k], sel[cls])
            multi[cls] = {kk: v for kk, v in multi[cls].items() if kk not in ("论文效应", "配方效应")}
        rows = []
        pa = np.array([r["论文"] for r in R])
        for tr, te in GroupKFold(5).split(R, groups=pa):
            rows += anchor_eval([R[i] for i in tr], [R[i] for i in te], cls, sel.get(cls, []))
        anchor[cls] = anchor_metrics(rows)
        a = anchor[cls]
        if "完整" in a:
            print(f"  锚点预测（开发 5 折）n={a['n']}：均方误差 完整 {a['完整']['均方误差']:.3f} / 锚点＋条件 {a['锚点＋条件']['均方误差']:.3f} / "
                  f"与锚点相同 {a['与锚点相同']['均方误差']:.3f}；差值区间 {a['完整−与锚点相同 均方误差差 95%区间']}；排序 {a['完整']['篇内排序一致率']:.3f}", flush=True)
        ranks[cls] = rankings(R, ystd, yprac, res0, cls)
        strat[cls] = strategy_b(R, ystd)
        ids = Counter(r["身份"] for r in R)
        multi.setdefault("_配方身份跨篇", {})[cls] = sum(1 for k in ids if len({r["论文"] for r in R if r["身份"] == k}) >= 2)
        multi.setdefault("_随机效应方差", {})[cls] = {k: res0[k] for k in ("τ²_论文", "τ²_配方", "σ²", "方法")}
        for r, s, sp in zip(R, ystd, yprac):
            norm_rows.append({"类别": cls, "论文": r["论文"], "测试": r["测试"], "配方": r["配方"], "配方名": r["配方名"], "身份": r["身份"],
                              "策略": tag(r), "实测": r["数值"], "y": r["y"], "y_标准": float(s), "y_实用": float(sp),
                              "标准条件值": UNIT[cls][1](float(s)), "条件补值": r["_补值"], "标记": r["标记"]})
    jdump("B1_条件效应.json", {"说明": NOTE, "结果": b1, "留出验证": b1v})
    jdump("B3_描述符与随机效应.json", {"说明": NOTE, "逐个描述符": scr, "方案A选中描述符合估": multi, "与方案A方向对照": agree})
    jdump("B4_开发集验证.json", {"说明": NOTE, "标准醚离散度": spread, "锚点预测": anchor})
    jdump("B5_排名.json", {"说明": NOTE + "；区间为近似（残差方差/测量数 + 论文效应方差/论文数）", "配方排名": ranks, "策略相对标准醚": strat})
    jdump("归一化测量.json", norm_rows)
    jdump("预先登记.json", {"说明": "方案 B 考试前登记（规则见 B_normalize.py 文件头）。考试只算一次。", "描述符": sel,
                        "考试指标": "锚点预测：相对锚点差值的均方误差（主）、R²、篇内排序一致率；基线 = 与锚点相同、锚点＋条件",
                        "成功标准": "B1 优于条件不变基线；标准醚离散度变小；锚点预测均方误差在开发集和考试集都低于与锚点相同（差值 95% 区间不含 0）"})
    figures(b1, spread, scr, scr_a)
    write_xlsx(ranks, strat, b1, agree)


def write_xlsx(ranks, strat, b1, agree):
    sys.path.insert(0, str(ROOT / "scripts"))
    from step13_common import write_xlsx as wx
    sheets = []
    for cls in CLASSES:
        unit = UNIT[cls][0]
        rs = ranks[cls]
        sheets.append((f"{cls}_配方排名", ["配方身份", "配方名", "策略", "论文", "测量", f"标准条件（{unit}）", "标准条件近似区间",
                                       f"实用条件（{unit}）", "相对标准醚（ln，越大越好）", "条件补值"],
                       [[e[k] for k in ("配方身份", "配方名", "策略", "论文", "测量", f"标准条件（{unit}）", "标准条件近似区间",
                                        f"实用条件（{unit}）", "相对标准醚（ln，越大越好）", "条件补值")] for e in rs]))
    sheets.append(("策略相对标准醚", ["类别", "策略", "测量", "论文", "相对标准醚倍数", "95%区间"],
                   [[c, t, v["测量"], v["论文"], v["相对标准醚倍数"], v["95%区间"]] for c in CLASSES for t, v in (strat[c].get("组") or {}).items()]))
    sheets.append(("B1条件效应", ["类别", "条件", "系数", "95%区间", "物理方向"],
                   [[c, n, b1[c]["系数"][i], None if not b1[c]["95%区间"] else b1[c]["95%区间"][i], b1[c]["物理方向"].get(n)]
                    for c in CLASSES for i, n in enumerate(b1[c]["列"])]))
    sheets.append(("描述符AB对照", ["类别", "描述符", "B倍数/SD", "B q", "A倍数/SD", "A q", "方向一致", "两边都q<0.1"],
                   [[c, e["描述符"], e["B倍数"], e["B_q"], e["A倍数"], e["A_q"], e["方向一致"], e["两边都 q<0.1"]] for c in CLASSES for e in agree[c]]))
    wx(OUT / "方案B_归一化结果.xlsx", sheets, notes=["方案 B 归一化（313 篇开发集，初步、未裁定；AI 辅助，用户尚未逐项人工确认）。",
                                                    "标准条件：E/S 10、载量 1.5、含硫 50%、扣式、0.2 C；全电池 CE 100 圈；Li‖Cu 0.5 mA cm⁻²、1 mAh cm⁻²、100 圈。",
                                                    "实用条件：E/S 5、载量 4。配方排名已扣掉论文（实验室）效应；区间为近似。规则见 scripts/step15_meta/B_normalize.py。"])


def main_exam():
    f = OUT / "考试结果.json"
    if f.exists():
        sys.exit("方案 B 考试集已经算过，不再重算")
    reg = json.loads((OUT / "预先登记.json").read_text(encoding="utf-8"))
    M, _ = load()
    out = {"运行次数": 1, "登记": reg, "类别": {}}
    for cls in CLASSES:
        tr = [r for r in M if r["类别"] == cls and r["划分"] == "开发"]
        te = [r for r in M if r["类别"] == cls and r["划分"] == "考试"]
        rows = anchor_eval(tr, te, cls, reg["描述符"].get(cls, []))
        out["类别"][cls] = a = anchor_metrics(rows)
        if "完整" in a:
            print(f"{cls}：考试 {a['n']} 个测量 / {a['论文']} 篇；均方误差 完整 {a['完整']['均方误差']:.3f}，锚点＋条件 {a['锚点＋条件']['均方误差']:.3f}，"
                  f"与锚点相同 {a['与锚点相同']['均方误差']:.3f}；差值区间 {a['完整−与锚点相同 均方误差差 95%区间']}；排序 {a['完整']['篇内排序一致率']:.3f}")
        else:
            print(cls, "考试可评测量不足", a)
    jdump("考试结果.json", out)


if __name__ == "__main__":
    main_exam() if "--exam" in sys.argv else main_dev()
