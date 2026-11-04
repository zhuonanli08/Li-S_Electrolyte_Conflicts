"""草稿：几种数据形式 × 特征组 × 模型，诚实验证（按论文留出为主）。"""
import sys, math, warnings
warnings.filterwarnings("ignore")
from xdata import *

COND = ["ln_ES", "载量", "含硫", "ln_倍率", "温度", "软包", "ln_圈数"]
FS = {
    "FS0 现行": N.FORM_F,
    "FS1 现行+截止+有机硫": N.FORM_F + ["截止下限V", "有机硫"],
    "FS2 结构官能团": ["溶剂_醚氧", "溶剂_环醚比例", "溶剂_有机硫比例", "溶剂_F原子", "溶剂_α氟醚氧", "溶剂_β氟醚氧", "溶剂_碳酸酯",
                   "阴离子F_每升", "阴离子磺酰_每升", "主盐_M", "LiNO3_M", "介体", "其他添加剂", "截止下限V"],
    "FS3 精简": ["溶剂_有机硫比例", "溶剂_醚氧", "LiNO3_M", "阴离子F_每升", "截止下限V"],
}
MODELS = {"岭回归": N.Linear, "单调梯度提升": N.GBMMono, "高斯过程": N.GP}


def mat(rows, cols):
    return np.array([[np.nan if r["x"].get(c) is None else r["x"][c] for c in cols] for r in rows], float)


def usable(rows, cols):
    return [c for c in cols if sum(r["x"].get(c) is not None for r in rows) >= 3
            and len({round(r["x"][c], 6) for r in rows if r["x"].get(c) is not None}) > 1]


def r2(o, p):
    o, p = np.asarray(o), np.asarray(p)
    return 1 - ((o - p) ** 2).sum() / ((o - o.mean()) ** 2).sum()


def run(cname, rows, cols, M, design):
    X = mat(rows, cols); y = np.array([r["y"] for r in rows]); g = np.array([r["s"]["论文"] for r in rows])
    w = N.weights(g); papers = sorted(set(g))
    if design == "D1 篇内·按论文留出":
        pred = np.full(len(y), np.nan)
        for q in papers:
            tr = g != q
            pred[g == q] = M(cols, cname).fit(X[tr], y[tr], g[tr], w[tr]).f(X[g == q])
        R, rmse, *_ = N.within_r2(y, pred, g)
        acc, n = N.pair_direction(y, pred, list(g), [r["s"]["测试"] for r in rows], [r["s"]["是否对照"] for r in rows])
        return R, rmse, acc
    if design == "D3 同篇补全·留一条":
        pred = np.full(len(y), np.nan)
        for i in range(len(y)):
            tr = np.arange(len(y)) != i
            m = M(cols, cname).fit(X[tr], y[tr], g[tr], w[tr])
            rest = tr & (g == g[i])
            a = np.average(y[rest] - m.f(X[rest]), weights=w[rest])
            pred[i] = a + m.f(X[i][None])[0]
        return r2(y, pred), float(np.sqrt(np.mean((y - pred) ** 2))), None


if __name__ == "__main__":
    for cname in ("放电容量类", "衰减类"):
        rows = rows_for(cname)
        cond = [c for c in COND if not (cname == "放电容量类" and c == "ln_圈数")]
        print(f"\n##### {cname}  {len(rows)} 条 / {len({r['s']['论文'] for r in rows})} 篇")
        for fs, fcols in FS.items():
            cols = usable(rows, fcols + cond)
            for mn, M in MODELS.items():
                out = []
                for d in ("D1 篇内·按论文留出", "D3 同篇补全·留一条"):
                    R, rmse, acc = run(cname, rows, cols, M, d)
                    out.append(f"{d[:2]} R²={R:+.2f} RMSE={rmse:.3f}" + (f" 方向={acc:.2f}" if acc is not None else ""))
                print(f"  {fs:18s} {mn:7s} ({len(cols)}列) | " + " | ".join(out), flush=True)
