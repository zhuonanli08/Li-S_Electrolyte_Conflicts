"""step15 共用的统计工具：混合效应模型（论文随机截距）、多重比较校正、篇内排序一致率、按论文重抽样。"""
import warnings
import numpy as np
from collections import defaultdict
from scipy import stats

warnings.filterwarnings("ignore")


def fit_mixed(y, X, groups, names):
    """y = X·b + 论文随机截距 + 误差（REML）。X 不含截距列时自动加。
    返回 dict(b, se, p, tau2 论文间方差, sigma2 篇内方差, 方法)。MixedLM 不收敛或方差估到 0 时退回 OLS＋按论文聚类的稳健标准误。"""
    import statsmodels.api as sm
    y = np.asarray(y, float)
    X = np.column_stack([np.ones(len(y)), np.asarray(X, float)]) if np.asarray(X).size else np.ones((len(y), 1))
    names = ["截距"] + list(names)
    g = np.asarray(groups)
    out = None
    for meth in (["lbfgs"], ["powell"], ["nm"]):
        try:
            m = sm.MixedLM(y, X, groups=g).fit(reml=True, method=meth)
            bse = np.asarray(m.bse)[: X.shape[1]]
            if np.all(np.isfinite(bse)) and m.converged:  # cov_re / random_effects 可能是数组，统一用 asarray
                out = {"b": np.asarray(m.fe_params), "se": bse, "tau2": float(np.asarray(m.cov_re).ravel()[0]), "sigma2": float(m.scale),
                       "方法": "MixedLM", "re": {k: float(np.asarray(v).ravel()[0]) for k, v in m.random_effects.items()}}
                break
        except Exception:
            continue
    if out is None or out["tau2"] < 1e-8:
        m = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": _codes(g)})
        resid = y - X @ m.params
        tau2, s2 = _moment_var(resid, g)
        out = {"b": m.params, "se": m.bse, "tau2": tau2, "sigma2": s2, "方法": "OLS聚类稳健", "re": {}}
    b, se = np.asarray(out["b"], float), np.asarray(out["se"], float)
    z = b / np.where(se > 0, se, np.nan)
    out["p"] = 2 * stats.norm.sf(np.abs(z))
    out["names"] = names
    out["b"], out["se"] = b, se
    return out


def _codes(g):
    u = {k: i for i, k in enumerate(dict.fromkeys(g))}
    return np.array([u[k] for k in g])


def _moment_var(resid, g):
    by = defaultdict(list)
    for r, k in zip(resid, g):
        by[k].append(r)
    within = [np.var(v, ddof=1) for v in by.values() if len(v) > 1]
    s2 = float(np.mean(within)) if within else float(np.var(resid))
    means = [np.mean(v) for v in by.values()]
    nbar = np.mean([len(v) for v in by.values()])
    return max(float(np.var(means, ddof=1)) - s2 / nbar, 0.0) if len(means) > 1 else 0.0, s2


def bh(p):
    """Benjamini–Hochberg q 值（忽略 NaN）。"""
    p = np.asarray(p, float)
    q = np.full_like(p, np.nan)
    ok = np.isfinite(p)
    if not ok.any():
        return q
    pv = p[ok]
    o = np.argsort(pv)
    r = pv[o] * len(pv) / (np.arange(len(pv)) + 1)
    r = np.minimum.accumulate(r[::-1])[::-1]
    qq = np.empty_like(pv)
    qq[o] = np.minimum(r, 1)
    q[ok] = qq
    return q


def concordance(pred, obs, groups):
    """篇内排序一致率：同一组（同一篇或同一测试）里任取两个比较，预测的先后与实测一致的比例；预测打平记 0.5，实测打平不计。
    返回（一致率, 对数）。基线（不会排序）= 0.5。"""
    by = defaultdict(list)
    for p, o, g in zip(pred, obs, groups):
        by[g].append((p, o))
    num = den = 0.0
    for v in by.values():
        for i in range(len(v)):
            for j in range(i + 1, len(v)):
                do = v[i][1] - v[j][1]
                if abs(do) < 1e-12:
                    continue
                dp = v[i][0] - v[j][0]
                den += 1
                num += 0.5 if abs(dp) < 1e-12 else float(np.sign(dp) == np.sign(do))
    return (num / den if den else np.nan), int(den)


def spearman_mean(pred, obs, groups, min_n=3):
    """每组（≥ min_n 个比较）算 Spearman，按组内个数加权平均。预测全相同的组记 0。"""
    by = defaultdict(list)
    for p, o, g in zip(pred, obs, groups):
        by[g].append((p, o))
    rs, ws = [], []
    for v in by.values():
        if len(v) < min_n:
            continue
        p, o = np.array(v).T
        r = 0.0 if np.ptp(p) < 1e-12 or np.ptp(o) < 1e-12 else stats.spearmanr(p, o).correlation
        rs.append(r); ws.append(len(v))
    return (float(np.average(rs, weights=ws)) if rs else np.nan), len(rs)


def r2(obs, pred):
    obs, pred = np.asarray(obs, float), np.asarray(pred, float)
    ss = np.sum((obs - obs.mean()) ** 2)
    return float(1 - np.sum((obs - pred) ** 2) / ss) if ss > 0 else np.nan


def boot_by_paper(fn, papers, n=500, seed=0):
    """按论文重抽样：fn(选中的论文列表) → 数值；返回 2.5% 与 97.5% 分位。"""
    rng = np.random.default_rng(seed)
    u = sorted(set(papers))
    vals = []
    for _ in range(n):
        v = fn(list(rng.choice(u, len(u))))
        if v is not None and np.isfinite(v):
            vals.append(v)
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if len(vals) > 20 else [None, None]


LAMS = (0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0)


class Ridge:
    """岭回归（列先按训练集标准化，截距不惩罚）。lam=None 时按论文分组的内层 5 折从 LAMS 里选。"""

    def __init__(self, lam=None):
        self.lam = lam

    def _fit(self, X, y, lam):
        mu, sd = X.mean(0), X.std(0)
        sd = np.where(sd < 1e-12, 1.0, sd)
        Z = (X - mu) / sd
        y0 = y.mean()
        b = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (y - y0)) if Z.shape[1] else np.zeros(0)
        return mu, sd, y0, b

    def fit(self, X, y, groups):
        X, y = np.asarray(X, float), np.asarray(y, float)
        if self.lam is None:
            from sklearn.model_selection import GroupKFold
            g = np.asarray(groups)
            k = min(5, len(set(g)))
            best = None
            for lam in LAMS:
                err = 0.0
                for tr, te in GroupKFold(k).split(X, groups=g):
                    mu, sd, y0, b = self._fit(X[tr], y[tr], lam)
                    err += np.sum((y[te] - (y0 + ((X[te] - mu) / sd) @ b)) ** 2)
                if best is None or err < best[0]:
                    best = (err, lam)
            self.lam = best[1]
        self.mu, self.sd, self.y0, self.b = self._fit(X, y, self.lam)
        return self

    def predict(self, X):
        return self.y0 + ((np.asarray(X, float) - self.mu) / self.sd) @ self.b

    def coef(self):
        """换回原始单位的系数（每单位变化的效应）。"""
        return self.b / self.sd


def font():
    import matplotlib
    matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False
