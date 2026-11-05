"""step13f：打分模型＋归一化到标准条件＋跨篇比较（方案 §8.7“跨文献比较方法”“验证”，初步，30 篇）。

模型形式：每条表述 y = f(配方特征, 条件) + 论文效应 + 误差。
  - 论文效应扣掉（固定效应或回拟合），等价于只用同一篇内的差距训练：论文自身的正极、工艺、课题组影响抵消；
    n 个同篇数值只提供 n−1 条信息，不重复计数。线性混合模型把论文效应当随机效应，作对照。
  - y：容量、保持率取 ln；CE 取 −ln(100−CE)（每圈锂损失的对数，越大越好；方案 11-02 定 CE 用损失比）。
  - 每篇按 1/√n 加权（高斯过程、混合模型不支持权重）。
六种 f 并列比较（11-04 用户：不限于线性和梯度提升）：线性岭回归、线性混合模型、梯度提升、单调约束梯度提升（物理常识：
  容量随圈数/倍率/载量下降、随 E/S 上升；保持率随圈数/载量下降、随 E/S 上升）、随机森林、高斯过程。
评估：V1 按论文留出（篇内差距算得准不准）；V2 按测试留出（同篇换一个没见过的条件，检验归一化）；
  物理越界率 = 归一化后容量 >1672 mAh g⁻¹（含有机硫共溶剂的配方除外）或保持率 >100% 的比例（非外推表述中）。
选择规则（先定后跑）：越界率 ≤5% 的模型中选 V2 提升 R² 最高者；没有 V2 时看 V1；都越界时选越界率最低者。
归一化：y_标准 = y + f(x, 标准条件) − f(x, 实测条件)；原文没报告的条件不换算（记“未换算”）；
  离标准条件太远（圈数差 >10 倍，E/S、倍率差 >2 倍，载量差超过标准值本身）记“外推”。
  标准条件（11-04 用户定“全类统一一套”，取值由 Claude 按 30 篇数据定，依据见 标准条件依据.json）：
    E/S 10、硫载量 1.5、正极含硫 50%、25 °C、扣式；倍率 0.2 C；圈数按类定义（放电容量只用首圈、保持率 200 圈、全电池 CE 100 圈）；
    Li‖Cu 0.5 mA cm⁻²、1 mAh cm⁻²、100 圈。实用条件 = 在此基础上 E/S 5、载量 4（方案 §7.8）。
  分析集（11-04 用户定）：倍率容量这次不纳入；放电容量只看第一圈。
输出：归一化结果.json、归一化_表述.json、归一化与跨篇比较.xlsx、网站/图/图5a、5b、6、7，step13f_汇总.json
"""
from __future__ import annotations

import json
import math
import re
import time
import warnings
from collections import Counter, defaultdict

import numpy as np

from step13_common import COMP, LABEL, OUT, read_json, write_json, write_xlsx
from step13e_conflicts import recipe_items

warnings.filterwarnings("ignore")
FIG = OUT / "网站" / "图"
S_THEORY = 1672.0

CLASSES = {
    # 11-04 用户定：倍率容量这次不纳入分析；放电容量只看第一圈（圈数不再作输入）
    "放电容量类": {"std": ["硫比放电容量"], "y": "log", "unit": "mAh g⁻¹(S)", "cap": True, "stage": "首圈"},
    # 11-05 用户定：保持率改为每圈衰减率（毕设口径），圈数不再作输入；论文直接报的每圈衰减率、容量损失率一并换算
    "衰减类": {"std": ["容量保持率", "容量损失率", "每圈容量衰减率"], "y": "decay", "unit": "%/圈", "no_cycle": True},
    "库仑效率类·全电池": {"std": ["全电池 CE"], "y": "loss", "unit": "%"},
    "库仑效率类·Li‖Cu": {"std": ["Li‖Cu CE"], "y": "loss", "unit": "%"},
}
MONO = {"放电容量类": {"ln_圈数": -1, "ln_倍率": -1, "载量": -1, "ln_ES": 1},
        "衰减类": {"载量": -1, "ln_ES": 1}}  # y = −ln(每圈衰减率)：载量高衰减快、E/S 高衰减慢
FORM_F = ["sO_不含氟", "sO_β氟化醚", "sO_α氟化醚", "aC", "F/O", "InOr", "LiNO3_M", "主盐_M", "含其他添加剂"]
COND_LIS = ["ln_ES", "载量", "含硫", "ln_倍率", "温度", "软包", "ln_圈数"]
COND_CU = ["ln_电流", "ln_沉积容量", "温度", "ln_圈数"]
LN = math.log
STD_COMMON = {"ln_ES": LN(10.0), "载量": 1.5, "含硫": 50.0, "温度": 25.0, "软包": 0.0}
STD_CLASS = {"放电容量类": {"ln_倍率": LN(0.2)},
             "衰减类": {"ln_倍率": LN(0.2)},
             "库仑效率类·全电池": {"ln_倍率": LN(0.2), "ln_圈数": LN(100)},
             "库仑效率类·Li‖Cu": {"ln_电流": LN(0.5), "ln_沉积容量": LN(1.0), "温度": 25.0, "ln_圈数": LN(100)}}
REF_RECIPE = ("P034", "R_C")  # 标准醚电解液：1 M LiTFSI，DOL:DME=1:1（体积）；LiNO₃ 取本类标准醚配方中位数
SMALL = math.log(1.05)
SHOW = {"ln_ES": "E/S", "ln_倍率": "倍率C", "ln_圈数": "圈数", "ln_电流": "电流mA/cm2", "ln_沉积容量": "沉积容量mAh/cm2"}


def dedup(sts):
    seen, out = set(), []
    for s in sts:
        g = s.get("疑似重复组")
        if g and g in seen:
            continue
        seen.add(g)
        out.append(s)
    return out


def cycles_elapsed(s):
    """保持率/损失率经历的圈数：有基准圈（如“第50/2圈”、相对第2圈）时 = 圈数 − 基准圈，否则 = 圈数。"""
    try:
        n = int(s.get("圈数"))
    except (TypeError, ValueError):
        return None
    n -= int(s.get("基准圈") or 0)
    return n if n >= 1 else None


def decay_rate(s):
    """每圈衰减率（%/圈），毕设口径：（100 − 保持率）÷ 圈数；容量损失率 ÷ 圈数；论文直接报的 %/圈 原样用。
    保持率 ≥ 100%、算出 ≤ 0、圈数不明的返回 None（方案 §8.7：衰减率 ≤ 0 回原文核对）。"""
    v, std, u = s["数值"], s["标准指标"], s.get("单位") or ""
    if v is None or "%" not in u:  # mAh g⁻¹ cycle⁻¹、“相对比例”“定性”等不用
        return None
    if std == "每圈容量衰减率" or re.search(r"per\s*cycle|/\s*cycle|/\s*圈|cycle\s*[−-]1|每圈", u, re.I):
        d = v  # 已经是每圈值（含单位写成 % per cycle 的“容量损失率”）
    else:
        n = cycles_elapsed(s)
        d = None if n is None else ((100 - v) if std == "容量保持率" else v) / n
    return d if d is not None and d > 0 else None


def yval(s, kind):
    if kind == "decay":  # y = −ln(每圈衰减率)，越大越好；同篇同圈数两配方之差 = ln[(100−R对照)/(100−R实验)]
        d = decay_rate(s)
        return None if d is None else -math.log(d)
    v = s["数值"]
    if v is None or v <= 0:
        return None
    if kind == "loss":
        return None if v >= 100 else -math.log(100 - v)
    return math.log(v)


def inv_y(y, kind):
    if kind == "decay":
        return math.exp(-y)
    return 100 - math.exp(-y) if kind == "loss" else math.exp(y)


class Feat:
    def __init__(self, comp, ctab):
        self.comp, self.ctab = comp, ctab

    def items(self, s):
        return recipe_items(self.comp.get((s["论文"], s["recipe"])), None)

    def organosulfur(self, s) -> bool:
        return any(str(self.ctab.get(k, {}).get("化学类别", "")).startswith("有机硫") for k in self.items(s))

    def form(self, s) -> dict:
        r = s["元素比例"] or {}
        it = self.items(s)
        lino3 = it.get("LiNO3")
        salt = sum(v[1] for k, v in it.items() if self.ctab.get(k, {}).get("类别") == "锂盐" and v[0] == "摩尔浓度" and v[1] is not None)
        return {"sO_不含氟": r.get("sO_不含氟"), "sO_β氟化醚": r.get("sO_β氟化醚"), "sO_α氟化醚": r.get("sO_α氟化醚"),
                "aC": r.get("aC"), "F/O": r.get("F/O"), "InOr": r.get("InOr"),
                "LiNO3_M": (0.0 if lino3 is None else lino3[1] if lino3[0] == "摩尔浓度" else None),
                "主盐_M": salt or None, "含其他添加剂": 1.0 if s["分块"]["添加剂与介体"] else 0.0}

    @staticmethod
    def cond(s, cu=False) -> dict:
        c = s["条件"]
        v = lambda f: c.get(f, {}).get("值")
        ln = lambda x: math.log(x) if x is not None and x > 0 else None
        if cu:
            return {"ln_电流": ln(v("current")), "ln_沉积容量": ln(v("Li_Cu_capacity")), "温度": v("temperature"), "ln_圈数": ln(s["圈数"])}
        return {"ln_ES": ln(v("ES")), "载量": v("sulfur_loading"), "含硫": v("S_content"), "ln_倍率": ln(v("rate")),
                "温度": v("temperature"), "软包": None if v("cell_format") is None else float(v("cell_format") == "软包"),
                "ln_圈数": ln(s["圈数"])}


# ---------------- 模型库 ----------------
class Prep:
    """缺失值填训练中位数，再标准化。"""

    def fit(self, X):
        self.mu = np.nanmedian(X, 0)
        self.mu = np.where(np.isnan(self.mu), 0, self.mu)
        sd = np.nanstd(X, 0)
        self.sd = np.where((sd == 0) | np.isnan(sd), 1, sd)
        return self

    def tr(self, X):
        Z = (X - self.mu) / self.sd
        return np.where(np.isnan(Z), 0.0, Z)


class Linear:
    """岭回归＋论文固定效应（组内去均值），含 sO×lnE/S、F/O×lnE/S 交互。"""
    name = "线性岭回归"

    def __init__(self, cols, cname="", seed=0, lam=30.0):  # λ 在 1/10/30/100/300 中按 V1 选的共用值（看过验证结果，偏乐观）
        self.cols, self.lam = cols, lam
        self.inter = [(a, "ln_ES") for a in ("sO_不含氟", "F/O") if a in cols and "ln_ES" in cols]

    def _design(self, X):
        Z = self.p.tr(X)
        extra = [Z[:, self.cols.index(a)] * Z[:, self.cols.index(b)] for a, b in self.inter]
        return np.column_stack([Z] + extra) if extra else Z

    def fit(self, X, y, g, w):
        self.p = Prep().fit(X)
        D = self._design(X)
        Dd, yd = D.copy(), y.copy()
        for q in np.unique(g):
            m = g == q
            ww = w[m] / w[m].sum()
            Dd[m] -= ww @ D[m]
            yd[m] -= ww @ y[m]
        W = np.sqrt(w)[:, None]
        self.beta = np.linalg.solve((Dd * W).T @ (Dd * W) + self.lam * np.eye(D.shape[1]), (Dd * W).T @ (yd * W[:, 0]))
        return self

    def f(self, X):
        return self._design(X) @ self.beta

    def coef_names(self):
        return list(self.cols) + [f"{a}×{b}" for a, b in self.inter]


class MixedLM:
    """线性混合模型：论文随机截距（statsmodels）；f 只取固定效应部分。"""
    name = "线性混合模型"

    def __init__(self, cols, cname="", seed=0):
        self.cols = cols

    def fit(self, X, y, g, w):
        import statsmodels.api as sm
        self.p = Prep().fit(X)
        Z = self.p.tr(X)
        keep = Z.std(0) > 1e-9
        self.keep = keep
        try:
            r = sm.MixedLM(y, sm.add_constant(Z[:, keep], has_constant="add"), groups=g).fit(reml=True, method="lbfgs", maxiter=300)
            self.beta = np.asarray(r.fe_params)[1:]
        except Exception:
            self.beta = np.zeros(int(keep.sum()))
        return self

    def f(self, X):
        return self.p.tr(X)[:, self.keep] @ self.beta


class Backfit:
    """非线性 f 的论文效应：交替拟合 f 与各篇平均残差（回拟合）。"""
    iters = 5
    use_w = True

    def __init__(self, cols, cname="", seed=0):
        self.cols, self.cname, self.seed = cols, cname, seed

    def _px(self, X):
        return X

    def fit(self, X, y, g, w):
        self._prep(X)
        Xp = self._px(X)
        alpha = np.zeros(len(y))
        for _ in range(self.iters):
            self.est = self._new()
            if self.use_w:
                self.est.fit(Xp, y - alpha, sample_weight=w)
            else:
                self.est.fit(Xp, y - alpha)
            fx = self.est.predict(Xp)
            for q in np.unique(g):
                m = g == q
                alpha[m] = np.average(y[m] - fx[m], weights=w[m])
        return self

    def _prep(self, X):
        pass

    def f(self, X):
        return self.est.predict(self._px(X))


class GBM(Backfit):
    name = "梯度提升"
    mono = False

    def _new(self):
        import lightgbm as lgb
        mc = [MONO.get(self.cname, {}).get(c, 0) for c in self.cols] if self.mono else None
        return lgb.LGBMRegressor(n_estimators=150, learning_rate=0.05, num_leaves=7, min_child_samples=4, subsample=0.8, subsample_freq=1,
                                 colsample_bytree=0.8, reg_lambda=1.0, random_state=self.seed, verbose=-1, monotone_constraints=mc)


class GBMMono(GBM):
    name = "单调约束梯度提升"
    mono = True


class RF(Backfit):
    name = "随机森林"

    def _new(self):
        from sklearn.ensemble import RandomForestRegressor
        return RandomForestRegressor(n_estimators=150, min_samples_leaf=3, max_features=0.6, random_state=self.seed, n_jobs=1)


class GP(Backfit):
    name = "高斯过程"
    iters = 3
    use_w = False

    def _prep(self, X):
        self.p = Prep().fit(X)

    def _px(self, X):
        return self.p.tr(X)

    def _new(self):
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel
        d = len(self.cols)
        k = ConstantKernel(1.0, (1e-2, 1e2)) * RBF(np.full(d, 3.0), (0.3, 100.0)) + WhiteKernel(0.3, (1e-3, 10.0))
        return GaussianProcessRegressor(kernel=k, normalize_y=True, random_state=self.seed)


MODELS = [Linear, MixedLM, GBM, GBMMono, RF, GP]


def weights(g):
    c = Counter(g)
    return np.array([1 / math.sqrt(c[q]) for q in g])


def within_r2(obs, pred, g):
    """篇内去均值后的 R²：只看同一篇里配方之间的差距算得准不准。"""
    od, pd_ = obs.copy(), pred.copy()
    for q in np.unique(g):
        m = g == q
        od[m] -= obs[m].mean()
        pd_[m] -= pred[m].mean()
    ss = (od ** 2).sum()
    return (1 - ((od - pd_) ** 2).sum() / ss if ss > 0 else float("nan")), float(np.sqrt(np.mean((od - pd_) ** 2))), od, pd_


def pair_direction(obs, pred, g, tests, ctrl):
    """同一测试内，每个配方与本测试对照（没有对照时取第一个）比较，方向是否一致。"""
    ok = n = 0
    for key in set(zip(g, tests)):
        idx = [i for i in range(len(g)) if (g[i], tests[i]) == key]
        if len(idx) < 2:
            continue
        ref = next((i for i in idx if ctrl[i]), idx[0])
        for i in idx:
            if i != ref and abs(obs[i] - obs[ref]) > SMALL:
                n += 1
                ok += (obs[i] - obs[ref] > 0) == (pred[i] - pred[ref] > 0)
    return (ok / n if n else float("nan")), n


def at_obs(x, cond, cols):
    """表述归一化：只换算原文报告了的条件。"""
    x = x.copy()
    for k, v in cond.items():
        j = cols.index(k) if k in cols else None
        if j is not None and not np.isnan(x[j]):
            x[j] = v
    return x


def at_all(x, cond, cols):
    """配方排名：所有条件都设成标准条件。"""
    x = x.copy()
    for k, v in cond.items():
        if k in cols:
            x[cols.index(k)] = v
    return x


def far_flags(x, cond, cols):
    out = []
    for k, lim, lab in (("ln_圈数", math.log(10), "圈数"), ("ln_ES", math.log(2), "E/S"), ("ln_倍率", math.log(2), "倍率"),
                        ("ln_电流", math.log(2), "电流"), ("ln_沉积容量", math.log(2), "沉积容量")):
        if k in cond and k in cols and not np.isnan(x[cols.index(k)]) and abs(x[cols.index(k)] - cond[k]) > lim:
            out.append(lab)
    if "载量" in cond and "载量" in cols and not np.isnan(x[cols.index("载量")]) and abs(x[cols.index("载量")] - cond["载量"]) > cond["载量"]:
        out.append("载量")
    return out


def show(d):
    return {SHOW.get(k, k): (round(math.exp(v), 3) if k.startswith("ln_") else round(v, 2)) for k, v in d.items()}


def main() -> None:
    t0 = time.time()
    sts = dedup(read_json("表述.json"))
    comp = {(r["论文"], r["配方"]): r for r in read_json("配方组成.json", COMP)}
    ctab = {c["id"]: c for c in read_json("组分表.json", COMP)}
    F = Feat(comp, ctab)
    results, st_out, summary = {}, [], {"标签": LABEL, "选择规则": "越界率≤5% 的模型中选 V2 提升R² 最高；无 V2 看 V1；都越界选越界率最低", "类别": {}}

    for cname, spec in CLASSES.items():
        cu = "Li‖Cu" in cname
        cond_cols = COND_CU if cu else [c for c in COND_LIS if not ((spec.get("stage") or spec.get("no_cycle")) and c == "ln_圈数")]
        rows = []
        for s in sts:
            if s["标准指标"] in spec["std"] and s["数值类型"] in ("精确", "约数", "范围") and yval(s, spec["y"]) is not None                     and (not spec.get("stage") or s["阶段"] == spec["stage"]):
                rows.append((s, yval(s, spec["y"]), {**F.form(s), **F.cond(s, cu)}))
        pc = Counter(r[0]["论文"] for r in rows)
        rows = [r for r in rows if pc[r[0]["论文"]] >= 2]  # 只有一个数值的论文不提供篇内信息
        if len(rows) < 8 or len({r[0]["论文"] for r in rows}) < 3:
            summary["类别"][cname] = {"跳过": f"可用数值 {len(rows)} 条，太少"}
            continue
        cols = [c for c in FORM_F + cond_cols if sum(r[2][c] is not None for r in rows) >= 3]
        X = np.array([[np.nan if r[2][c] is None else r[2][c] for c in cols] for r in rows], dtype=float)
        y = np.array([r[1] for r in rows])
        g = np.array([r[0]["论文"] for r in rows])
        tests = np.array([r[0]["测试"] for r in rows])
        ctrl = [r[0]["是否对照"] for r in rows]
        orgS = np.array([F.organosulfur(r[0]) for r in rows])
        w = weights(g)
        papers = sorted(set(g))
        base_std = ({} if cu else dict(STD_COMMON)) | STD_CLASS[cname]
        med = {c: v for c, v in base_std.items() if c in cols}
        std_sets = {"普遍条件": med}
        if not cu and "ln_ES" in cols and "载量" in cols:
            std_sets["实用条件"] = {**med, "ln_ES": math.log(5.0), "载量": 4.0}
        far = {sn: [far_flags(X[i], c, cols) for i in range(len(y))] for sn, c in std_sets.items()}
        unknown = [[SHOW.get(k, k) for k in med if k in cols and np.isnan(X[i, cols.index(k)])] for i in range(len(y))]

        # ---------- 各模型：V1、V2、物理越界 ----------
        comp_rows, detail = [], {}
        for M in MODELS:
            tm = time.time()
            pred = np.full(len(y), np.nan)
            for q in papers:
                tr = g != q
                pred[g == q] = M(cols, cname).fit(X[tr], y[tr], g[tr], w[tr]).f(X[g == q])
            r2, rmse, od, pdd = within_r2(y, pred, g)
            acc, npair = pair_direction(y, pred, list(g), list(tests), ctrl)
            o2, p2, b2, lab2 = [], [], [], []
            for q in papers:
                tl = sorted(set(tests[g == q]))
                if len(tl) < 2:
                    continue
                for t in tl:
                    te = (g == q) & (tests == t)
                    m = M(cols, cname).fit(X[~te], y[~te], g[~te], w[~te])
                    rest = (g == q) & ~te
                    a = np.average(y[rest] - m.f(X[rest]), weights=w[rest])
                    o2 += list(y[te])
                    p2 += list(a + m.f(X[te]))
                    b2 += [np.average(y[rest], weights=w[rest])] * int(te.sum())
                    lab2 += [f"{rows[i][0]['表述编号']} {q} {t}" for i in np.where(te)[0]]
            v2 = None
            if o2:
                o2a, p2a, b2a = map(np.array, (o2, p2, b2))
                den = ((o2a - b2a) ** 2).sum()
                v2 = {"n": len(o2), "RMSE(ln)": round(float(np.sqrt(np.mean((o2a - p2a) ** 2))), 3),
                      "基线RMSE(ln)": round(float(np.sqrt(np.mean((o2a - b2a) ** 2))), 3),
                      "提升R2": round(float(1 - ((o2a - p2a) ** 2).sum() / den), 3) if den > 0 else None,
                      "散点": {"实测": o2, "预测": p2, "标签": lab2}}
            full = M(cols, cname).fit(X, y, g, w)
            yn = np.array([y[i] + full.f(at_obs(X[i], med, cols)[None])[0] - full.f(X[i][None])[0] for i in range(len(y))])
            vn = np.array([inv_y(v, spec["y"]) for v in yn])
            bad = (vn > S_THEORY) & ~orgS if spec.get("cap") else (vn > 100.5) if spec.get("ret") else (vn <= 0) if spec["y"] == "decay" else np.zeros(len(y), bool)
            near = np.array([not far["普遍条件"][i] for i in range(len(y))])
            viol = float(bad[near].mean()) if near.any() else float("nan")
            row = {"模型": M.name, "V1篇内R2": round(r2, 3), "V1方向正确率": round(acc, 3) if acc == acc else None, "V1方向对数": npair,
                   "V1篇内RMSE(ln)": round(rmse, 3), "V1约误差%": round((math.exp(rmse) - 1) * 100) if rmse < 10 else None,
                   "V2提升R2": v2["提升R2"] if v2 else None, "V2 RMSE(ln)": v2["RMSE(ln)"] if v2 else None,
                   "V2基线RMSE(ln)": v2["基线RMSE(ln)"] if v2 else None, "V2条数": v2["n"] if v2 else 0,
                   "越界率（非外推）": round(viol, 3), "越界率（全部）": round(float(bad.mean()), 3), "耗时s": round(time.time() - tm, 1)}
            comp_rows.append(row)
            detail[M.name] = {"V1散点": {"实测": od.tolist(), "预测": pdd.tolist(),
                                         "标签": [f"{rows[i][0]['表述编号']} {g[i]} {rows[i][0]['配方']}" for i in range(len(y))]},
                              "V2": v2, "留出预测": pred.tolist()}
            print(f"  {cname} {M.name}: {json.dumps({k: v for k, v in row.items() if k != '模型'}, ensure_ascii=False)}", flush=True)
        ok = [r for r in comp_rows if r["越界率（非外推）"] == r["越界率（非外推）"] and r["越界率（非外推）"] <= 0.05]
        if ok:
            key = (lambda r: (r["V2提升R2"] if r["V2提升R2"] is not None else -9, r["V1篇内R2"])) if any(r["V2提升R2"] is not None for r in ok) \
                else (lambda r: r["V1篇内R2"])
            prim = max(ok, key=key)["模型"]
        else:
            prim = min(comp_rows, key=lambda r: r["越界率（非外推）"])["模型"]
        Mp = next(M for M in MODELS if M.name == prim)

        # ---------- 主模型：归一化、基准、配方排名 ----------
        full = Mp(cols, cname).fit(X, y, g, w)
        y_norm = {sn: np.array([y[i] + full.f(at_obs(X[i], c, cols)[None])[0] - full.f(X[i][None])[0] for i in range(len(y))])
                  for sn, c in std_sets.items()}
        std_ether = [i for i, r in enumerate(rows) if tuple(sorted(F.items(r[0]))) == ("DME", "DOL", "LiNO3", "LiTFSI")]
        base = {sn: (float(np.median([y_norm[sn][i] for i in std_ether if not far[sn][i]] or [y_norm[sn][i] for i in std_ether]))
                     if std_ether else None) for sn in std_sets}
        ref_s = next((r[0] for r in rows if (r[0]["论文"], r[0]["recipe"]) == REF_RECIPE), rows[std_ether[0]][0] if std_ether else None)
        lin = [X[i, cols.index("LiNO3_M")] for i in std_ether if "LiNO3_M" in cols and not np.isnan(X[i, cols.index("LiNO3_M")])]
        REFX = None
        if ref_s is not None:
            refd = {**F.form(ref_s), "LiNO3_M": float(np.median(lin)) if lin else 0.2}
            REFX = np.array([np.nan if refd.get(c) is None else refd[c] for c in cols], dtype=float)
        rng = np.random.default_rng(42)
        B = 20 if prim == "高斯过程" else 40
        boots = []
        for b in range(B):
            pick = rng.choice(papers, len(papers), replace=True)
            idx = np.concatenate([np.where(g == q)[0] for q in pick])
            gb = np.concatenate([[f"{q}#{k}"] * int((g == q).sum()) for k, q in enumerate(pick)])
            boots.append(Mp(cols, cname, seed=b).fit(X[idx], y[idx], gb, weights(gb)))
        forms = defaultdict(list)
        for i, r in enumerate(rows):
            forms[(r[0]["论文"], r[0]["配方"])].append(i)
        form_rows = []
        v4 = None
        for sn, cond in std_sets.items():
            keys = list(forms)
            xs = np.array([at_all(X[forms[k][0]], cond, cols) for k in keys])
            rx = at_all(REFX, cond, cols)[None] if REFX is not None else None
            pt = full.f(xs) - (full.f(rx)[0] if rx is not None else 0)
            bs = np.array([m.f(xs) - (m.f(rx)[0] if rx is not None else 0) for m in boots])
            ext = []
            for k in keys:  # 配方级外推：本配方所有实测都离标准条件很远
                fl = [far_flags(X[i], cond, cols) for i in forms[k]]
                ext.append("；".join(sorted(set.intersection(*[set(f) for f in fl]))) if all(fl) else "")
            inr = [j for j in range(len(keys)) if not ext[j]]
            prank = {keys[j]: r + 1 for r, j in enumerate(sorted(inr, key=lambda j: -pt[j]))}
            rk = np.array([[sorted(inr, key=lambda j: -row[j]).index(j) + 1 if j in inr else 0 for j in range(len(keys))] for row in bs])
            if sn == "普遍条件" and len(inr) >= 3:
                from scipy.stats import spearmanr
                rho = [spearmanr(pt[inr], row[inr])[0] for row in bs]
                top = set(sorted(inr, key=lambda j: -pt[j])[:5])
                ovl = [len(top & set(sorted(inr, key=lambda j: -row[j])[:5])) / len(top) for row in bs]
                v4 = {"重抽样次数": len(bs), "参与排名配方数": len(inr),
                      "名次相关_中位数": round(float(np.median(rho)), 3), "名次相关_2.5–97.5%": [round(float(np.percentile(rho, 2.5)), 3), round(float(np.percentile(rho, 97.5)), 3)],
                      "前5重合率_平均": round(float(np.mean(ovl)), 3),
                      "说明": "按论文重抽样后重新训练，看配方名次与全数据结果的 Spearman 相关和前 5 名重合比例；越接近 1 越稳"}
            for j, k in enumerate(keys):
                s0 = rows[forms[k][0]][0]
                lo, hi = np.percentile(bs[:, j], [2.5, 97.5])
                form_rows.append({
                    "类别": cname, "标准条件": sn, "论文": k[0], "配方": k[1], "配方文字": s0["配方文字"], "是否对照": s0["是否对照"],
                    "表述数": len(forms[k]), "元素比例可算": s0["元素比例"] is not None,
                    "相对标准醚_ln": round(float(pt[j]), 4), "区间_ln": [round(float(lo), 4), round(float(hi), 4)],
                    "倍数": round(math.exp(pt[j]), 3) if spec["y"] == "log" else None,
                    "损失倍数": round(math.exp(-pt[j]), 3) if spec["y"] == "loss" else None,
                    "归一化值": round(inv_y(base[sn] + pt[j], spec["y"]), 2) if base[sn] is not None else None,
                    "归一化值区间": [round(inv_y(base[sn] + lo, spec["y"]), 2), round(inv_y(base[sn] + hi, spec["y"]), 2)] if base[sn] is not None else None,
                    "名次": prank.get(k), "名次区间": ([int(np.percentile(rk[:, j], 2.5)), int(np.percentile(rk[:, j], 97.5))] if not ext[j] else None),
                    "参与排名配方数": len(inr), "外推": ext[j]})
        for i, r in enumerate(rows):
            s = r[0]
            st_out.append({"表述编号": s["表述编号"], "类别": cname, "论文": s["论文"], "测试": s["测试"], "配方": s["配方"], "是否对照": s["是否对照"],
                           "实测值": s["数值"], "实测_y": round(float(y[i]), 4),
                           **{f"{sn}_归一化值": round(inv_y(y_norm[sn][i], spec["y"]), 2) for sn in std_sets},
                           **{f"{sn}_y": round(float(y_norm[sn][i]), 4) for sn in std_sets},
                           **{f"{sn}_外推": "；".join(far[sn][i]) for sn in std_sets},
                           "未换算条件": "；".join(unknown[i]),
                           "V1留出预测_主模型": round(float(detail[prim]["留出预测"][i]), 4),
                           "标准醚": i in std_ether, "含有机硫共溶剂": bool(orgS[i])})
        lm = Linear(cols).fit(X, y, g, w)
        bl = []
        for b in range(60):
            pick = rng.choice(papers, len(papers), replace=True)
            idx = np.concatenate([np.where(g == q)[0] for q in pick])
            gb = np.concatenate([[f"{q}#{k}"] * int((g == q).sum()) for k, q in enumerate(pick)])
            bl.append(Linear(cols).fit(X[idx], y[idx], gb, weights(gb)).beta)
        bl = np.array(bl)
        coef = [{"特征": n, "系数(标准化)": round(float(b), 4), "区间": [round(float(np.percentile(bl[:, k], 2.5)), 4), round(float(np.percentile(bl[:, k], 97.5)), 4)]}
                for k, (n, b) in enumerate(zip(lm.coef_names(), lm.beta))]
        pr = next(r for r in comp_rows if r["模型"] == prim)
        results[cname] = {"y": spec["y"], "单位": spec["unit"], "主模型": prim, "特征": cols, "模型比较": comp_rows,
                          "主模型V1散点": detail[prim]["V1散点"], "主模型V2": detail[prim]["V2"],
                          "标准条件": {k: show(v) for k, v in std_sets.items()}, "标准条件_内部": std_sets,
                          "标准醚基准": {k: (round(inv_y(v, spec["y"]), 2) if v is not None else None) for k, v in base.items()},
                          "标准醚各篇归一化值": {sn: [{"表述": rows[i][0]["表述编号"], "论文": g[i], "实测": rows[i][0]["数值"],
                                                    "归一化": round(inv_y(y_norm[sn][i], spec["y"]), 2), "外推": "；".join(far[sn][i])}
                                                   for i in std_ether] for sn in std_sets},
                          "配方": form_rows, "线性系数": coef, "论文数": len(papers), "数值条数": len(y), "重抽样次数": len(boots), "V4": v4}
        summary["类别"][cname] = {"论文": len(papers), "数值": len(y), "配方": len(forms), "主模型": prim,
                                 "主模型指标": {k: v for k, v in pr.items() if k != "模型"}, "标准条件": {k: show(v) for k, v in std_sets.items()},
                                 "标准醚基准": results[cname]["标准醚基准"],
                                 "外推表述数（普遍条件）": sum(bool(f) for f in far["普遍条件"]), "V4": v4}
        print(cname, "→ 主模型", prim, flush=True)
    summary["耗时s"] = round(time.time() - t0)
    write_json("标准条件依据.json", std_basis(sts))
    write_json("归一化结果.json", results)
    write_json("归一化_表述.json", st_out)
    write_json("step13f_汇总.json", summary)
    figures(results)
    excel(results, st_out)


def std_basis(sts) -> dict:
    """标准条件取值依据：每篇一票的中位数，以及各类不同标准倍率下 2 倍内的数据覆盖。"""
    v = lambda s, f: s["条件"].get(f, {}).get("值")
    def pmed(rows, get):
        per = defaultdict(list)
        for s in rows:
            x = get(s)
            if x is not None:
                per[s["论文"]].append(x)
        pm = [float(np.median(x)) for x in per.values()]
        return {"按论文中位数": round(float(np.median(pm)), 3) if pm else None, "论文数": len(pm),
                "按表述中位数": round(float(np.median([x for l in per.values() for x in l])), 3) if pm else None,
                "表述数": sum(len(l) for l in per.values()), "各篇中位数": sorted(round(x, 3) for x in pm)}
    LS = [s for s in sts if s["电池类型"] == "Li‖S"]
    out = {"说明": "每篇论文先取自己的中位数，再取各篇的中位数（每篇一票，避免测得多的论文主导）；倍率另看“标准倍率 2 倍以内的数据有多少条”。",
           "共同条件": {lab: pmed(LS, lambda s, f=f: v(s, f)) for f, lab in (("ES", "E/S"), ("sulfur_loading", "硫载量"), ("S_content", "正极含硫"),
                                                                             ("rate", "倍率"), ("temperature", "温度"))},
           "按类": {}}
    for std, cname in (("硫比放电容量", "放电容量类（首圈）"), ("容量保持率", "衰减类"), ("全电池 CE", "库仑效率类·全电池")):
        rows = [s for s in sts if s["标准指标"] == std and (std != "硫比放电容量" or s["阶段"] == "首圈")]
        rates = [v(s, "rate") for s in rows if v(s, "rate") is not None]
        out["按类"][cname] = {"圈数": pmed(rows, lambda s: s["圈数"]), "倍率": pmed(rows, lambda s: v(s, "rate")),
                             "标准倍率覆盖（2 倍内条数/总数）": {f"{c} C": f"{sum(abs(math.log(r / c)) <= math.log(2) for r in rates)}/{len(rates)}"
                                                           for c in (0.1, 0.2, 0.5, 1.0)}}
    CU = [s for s in sts if s["电池类型"] == "Li‖Cu"]
    out["Li‖Cu"] = {"电流": pmed(CU, lambda s: v(s, "current")), "沉积容量": pmed(CU, lambda s: v(s, "Li_Cu_capacity")),
                     "圈数": pmed([s for s in CU if s["标准指标"] == "Li‖Cu CE"], lambda s: s["圈数"])}
    out["采用"] = {"共同": "E/S 10、硫载量 1.5、正极含硫 50%、25 °C、扣式", "倍率": "0.2 C（首圈放电容量、保持率、全电池 CE 覆盖最多或接近最多）",
                 "圈数": "放电容量只用首圈（用户定）、保持率 200 圈、全电池 CE 100 圈；倍率容量这次不纳入分析（用户定）", "Li‖Cu": "0.5 mA cm⁻²、1 mAh cm⁻²、100 圈",
                 "实用条件": "在上面基础上 E/S 5、载量 4（方案 §7.8）"}
    return out


def figures(results):
    """英文图（11-04 用户要求网站用英文）。可用 `python step13f_normalize.py figs` 只重画图。"""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from step13_i18n import CAT, MODEL, STDSET, recipe_en, t as tr
    note = "<span style='font-size:12px;color:#62777a'>Preliminary · 30 papers (F-version) · association, not causation</span>"
    font = dict(family="Segoe UI, Arial, sans-serif", color="#172d32")
    comp = {(r["论文"], r["配方"]): r for r in read_json("配方组成.json", COMP)}
    rec_en = {(s["论文"], s["配方"]): recipe_en(comp.get((s["论文"], s["recipe"])), s["配方文字"]) for s in read_json("表述.json")}
    names = list(results)
    cn = lambda n: tr(CAT, n)
    mn = lambda m: tr(MODEL, m)
    # 图5a 模型比较
    fig = make_subplots(rows=1, cols=len(names), subplot_titles=[f"{cn(n)}<br><sup>selected: {mn(results[n]['主模型'])}</sup>" for n in names],
                        shared_yaxes=True, horizontal_spacing=0.05)
    for j, n in enumerate(names, 1):
        cr = results[n]["模型比较"]
        for met, lab, col in (("V1篇内R2", "V1 within-paper R²", "#007e70"), ("V2提升R2", "V2 skill R²", "#7159a7"),
                              ("越界率（非外推）", "Physical-violation rate", "#c2504a")):
            fig.add_trace(go.Bar(x=[mn(r["模型"]) for r in cr], y=[max(-1, r[met]) if r[met] is not None else 0 for r in cr], name=lab,
                                 marker_color=col, legendgroup=lab, showlegend=(j == 1),
                                 customdata=[r[met] for r in cr], hovertemplate="%{x}<br>" + lab + " = %{customdata}<extra></extra>"), row=1, col=j)
    fig.add_hline(y=0, line=dict(color="#62777a", width=1))
    fig.update_layout(title=f"Fig. 5a · Six models compared (values below −1 clipped)<br>{note}", barmode="group", template="plotly_white",
                      height=560, font=font, yaxis=dict(range=[-1.05, 1]), legend=dict(orientation="h", y=-0.32), margin=dict(t=120))
    fig.update_xaxes(tickangle=-40)
    fig.write_html(FIG / "图5a_模型比较.html", include_plotlyjs="directory")
    # 图5b 主模型验证散点
    fig = make_subplots(rows=2, cols=len(names), subplot_titles=[f"V1 · {cn(n)}" for n in names] + [f"V2 · {cn(n)}" for n in names],
                        horizontal_spacing=0.05, vertical_spacing=0.14)
    for j, n in enumerate(names, 1):
        r = results[n]
        pr = next(x for x in r["模型比较"] if x["模型"] == r["主模型"])
        for row, sc, txt in ((1, r["主模型V1散点"], f"R² = {pr['V1篇内R2']} · direction {pr['V1方向正确率']}"),
                             (2, (r["主模型V2"] or {}).get("散点"), f"skill R² = {pr['V2提升R2']}")):
            if not sc:
                continue
            fig.add_trace(go.Scatter(x=sc["实测"], y=sc["预测"], mode="markers", marker=dict(size=6, color="#007e70", opacity=0.7), showlegend=False,
                                     text=sc["标签"], hovertemplate="%{text}<br>measured %{x:.3f}<br>predicted %{y:.3f}<extra></extra>"), row=row, col=j)
            lo, hi = min(sc["实测"] + sc["预测"]), max(sc["实测"] + sc["预测"])
            fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", line=dict(color="#9fb3ad", dash="dash"), showlegend=False, hoverinfo="skip"),
                          row=row, col=j)
            ax = (row - 1) * len(names) + j
            fig.add_annotation(text=f"{mn(r['主模型'])}: {txt}", xref=f"x{'' if ax == 1 else ax} domain", yref=f"y{'' if ax == 1 else ax} domain",
                               x=0.02, y=0.98, showarrow=False, font=dict(size=10), bgcolor="rgba(255,255,255,0.8)")
    fig.update_layout(title=f"Fig. 5b · Selected models: V1 within-paper differences (paper mean removed) and V2 unseen conditions, ln units<br>{note}",
                      template="plotly_white", height=800, font=font, margin=dict(t=120))
    fig.write_html(FIG / "图5b_主模型验证散点.html", include_plotlyjs="directory")

    # 图6 归一化排名（森林图）
    traces, btn, heights = [], [], []
    combos = [(n, sn) for n in names for sn in results[n]["标准条件"]]
    for ci, (n, sn) in enumerate(combos):
        rows = sorted([x for x in results[n]["配方"] if x["标准条件"] == sn], key=lambda x: x["相对标准醚_ln"])
        lab = [f"{x['论文']}:{x['配方']}{' (control)' if x['是否对照'] else ''}{' [extrap.]' if x['外推'] else ''}" for x in rows]
        hov = [f"{rec_en.get((x['论文'], x['配方']), '')[:80]}<br>normalised value {x['归一化值']} ({x['归一化值区间']})<br>"
               f"rank {x['名次'] or '—'} (interval {x['名次区间']}) of {x['参与排名配方数']}<br>extrapolated: {'yes' if x['外推'] else 'no'}" for x in rows]
        traces.append(go.Scatter(x=[x["相对标准醚_ln"] for x in rows], y=lab, mode="markers",
                                 marker=dict(color=["#b9c7c2" if x["外推"] else "#007e70" for x in rows], size=8),
                                 error_x=dict(type="data", symmetric=False, array=[x["区间_ln"][1] - x["相对标准醚_ln"] for x in rows],
                                              arrayminus=[x["相对标准醚_ln"] - x["区间_ln"][0] for x in rows], color="#9fb3ad", thickness=1),
                                 text=hov, hovertemplate="%{y}<br>%{text}<extra></extra>", visible=(ci == 0), showlegend=False))
        heights.append(max(500, 18 * len(rows) + 220))
        btn.append(dict(label=f"{cn(n)} · {tr(STDSET, sn)}", method="update",
                        args=[{"visible": [k == ci for k in range(len(combos))]},
                              {"title": f"Fig. 6 · Cross-paper comparison after normalisation: {cn(n)} · {tr(STDSET, sn)} (model: {mn(results[n]['主模型'])})"
                                        f"<br>x = ln ratio vs the standard ether electrolyte (CE: −ln loss ratio); >0 is better; grey = extrapolated, not ranked<br>{note}",
                               "height": heights[-1]}]))
    fig = go.Figure(traces)
    fig.add_vline(x=0, line=dict(color="#c2504a", dash="dash"))
    n0, s0 = combos[0]
    fig.update_layout(title=f"Fig. 6 · Cross-paper comparison after normalisation: {cn(n0)} · {tr(STDSET, s0)} (model: {mn(results[n0]['主模型'])})"
                            f"<br>x = ln ratio vs the standard ether electrolyte; >0 is better; grey = extrapolated, not ranked<br>{note}",
                      template="plotly_white", height=heights[0], font=font, updatemenus=[dict(buttons=btn, x=1.0, y=1.06, xanchor="right")],
                      yaxis=dict(tickfont=dict(size=10)), xaxis=dict(title="ln (relative to standard ether electrolyte)"), margin=dict(l=230, t=140))
    fig.write_html(FIG / "图6_归一化跨篇排名.html", include_plotlyjs="directory")

    # 图7 标准醚电解液各篇：实测 vs 归一化
    fig = go.Figure()
    labels = []
    for n in names:
        for x in results[n]["标准醚各篇归一化值"].get("普遍条件", []):
            labels.append(f"{cn(n)} · {x['论文']} {x['表述']}{' [extrap.]' if x['外推'] else ''}")
            fig.add_trace(go.Scatter(x=[x["实测"], x["归一化"]], y=[labels[-1]] * 2, mode="lines+markers",
                                     marker=dict(color=["#9fb3ad", "#b9c7c2" if x["外推"] else "#007e70"], size=8,
                                                 symbol=["circle", "circle-open" if x["外推"] else "circle"]),
                                     line=dict(color="#dbe5e1"), showlegend=False,
                                     hovertemplate=f"{labels[-1]}<br>measured {x['实测']} → normalised {x['归一化']}<extra></extra>"))
    fig.update_layout(title=f"Fig. 7 · The same electrolyte (standard ether: LiTFSI + DOL/DME + LiNO₃) across papers: measured (grey) → normalised to the common condition (green; open = extrapolated)"
                            f"<br>A large gap left after normalisation cannot be explained by the recorded conditions<br>{note}",
                      template="plotly_white", height=max(500, 22 * len(labels) + 220), font=font,
                      xaxis=dict(title="Performance value (units differ by class)"), yaxis=dict(tickfont=dict(size=10)), margin=dict(l=300, t=140))
    fig.write_html(FIG / "图7_标准醚跨篇归一化前后.html", include_plotlyjs="directory")


def excel(results, st_out):
    sheets = []
    mrows = [[n, r["主模型"] == m["模型"] and "主模型" or "", m["模型"], m["V1篇内R2"], m["V1方向正确率"], m["V1方向对数"], m["V2提升R2"], m["V2条数"],
              m["越界率（非外推）"], m["越界率（全部）"], r["论文数"], r["数值条数"]] for n, r in results.items() for m in r["模型比较"]]
    sheets.append(("模型比较", ["类别", "选中", "模型", "V1篇内R2", "V1方向正确率", "V1方向对数", "V2提升R2", "V2条数", "越界率（非外推）", "越界率（全部）", "论文数", "数值条数"], mrows))
    srows = [[n, sn, json.dumps(v, ensure_ascii=False), r["标准醚基准"].get(sn)] for n, r in results.items() for sn, v in r["标准条件"].items()]
    sheets.append(("标准条件与基准", ["类别", "标准条件", "取值", "标准醚电解液基准（各篇归一化后中位数，不含外推）"], srows))
    frows = [[x["类别"], x["标准条件"], x["名次"], x["名次区间"], x["参与排名配方数"], x["论文"], x["配方"], "是" if x["是否对照"] else "", x["配方文字"],
              x["倍数"] if x["倍数"] is not None else x["损失倍数"], x["区间_ln"], x["归一化值"], x["归一化值区间"], x["外推"], x["表述数"]]
             for r in results.values() for x in sorted(r["配方"], key=lambda z: (z["标准条件"], z["名次"] or 999))]
    sheets.append(("配方排名", ["类别", "标准条件", "名次", "名次区间", "参与排名配方数", "论文", "配方", "对照", "配方文字", "相对标准醚倍数（CE 为损失倍数）",
                            "区间(ln)", "归一化值", "归一化值区间", "外推（不排名）", "表述数"], frows))
    sheets.append(("线性系数", ["类别", "特征", "系数（标准化）", "重抽样95%区间"],
                   [[n, c["特征"], c["系数(标准化)"], c["区间"]] for n, r in results.items() for c in r["线性系数"]]))
    keys = ["表述编号", "类别", "论文", "测试", "配方", "实测值", "普遍条件_归一化值", "普遍条件_外推", "实用条件_归一化值", "实用条件_外推", "未换算条件", "标准醚", "含有机硫共溶剂"]
    sheets.append(("表述归一化值", keys, [[x.get(k) for k in keys] for x in st_out]))
    write_xlsx(OUT / "归一化与跨篇比较.xlsx", sheets, widths={"配方文字": 45, "取值": 60},
               notes=[f"step13f 打分模型、归一化与跨篇比较｜{LABEL}｜2026-11-04 生成",
                      "模型：y = f(配方特征, 条件) + 论文效应；论文效应扣掉后只用篇内差距训练（方案 §8.7）。容量、保持率取 ln，CE 取 −ln(100−CE)。",
                      "六种 f：线性岭回归、线性混合模型、梯度提升、单调约束梯度提升、随机森林、高斯过程（11-04 用户：可以不只线性和梯度提升）。",
                      "选择规则（先定后跑）：物理越界率 ≤5% 的模型中选 V2 提升 R² 最高者；没有 V2 时看 V1；都越界时选越界率最低。",
                      "V1 按论文留出：对没见过的论文，同篇配方间差距的 R²（去掉各篇平均后）和方向正确率。V2 按测试留出：同篇换一个没见过的条件，相对“用本篇其他测试平均值猜”的提升。",
                      "物理越界：归一化后硫比容量 >1672 mAh g⁻¹（含有机硫共溶剂、共溶剂本身贡献容量的配方除外）或保持率 >100%。",
                      "归一化只换算原文报告了的条件（“未换算条件”列）；离标准条件太远的记外推（圈数差 >10 倍，E/S、倍率差 >2 倍，载量差超过标准值）。",
                      "标准条件（用户定全类统一一套；取值依据见 标准条件依据.json）：E/S 10、载量 1.5、含硫 50%、25 °C、扣式；倍率 0.2 C；圈数按类定义；实用条件 E/S 5、载量 4。分析集：倍率容量不纳入，放电容量只看第一圈（用户定）。参照 = 标准醚电解液（1 M LiTFSI，DOL:DME 1:1，LiNO₃ 取本类中位数）。",
                      "归一化值 = 标准醚电解液基准 × 倍数；基准取各篇标准醚实测值归一化后的中位数（方案中基准取法待定，此为试跑取法，待用户定）。区间来自按论文重抽样。",
                      "RMSE 是 ln 单位：RMSE 0.2 约等于典型误差 ±22%（e^0.2−1）。V4 = 按论文重抽样后名次与全数据名次的 Spearman 相关、前 5 名重合率。",
                      "数据少：两种 CE 各只有 5 篇，首圈放电容量 11 篇；30 篇试跑只说明流程能跑通，不作结论。"])


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "figs":
        figures(read_json("归一化结果.json"))
    else:
        main()
