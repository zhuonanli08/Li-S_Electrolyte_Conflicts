"""草稿：逐项加溶剂化/物化性质，比较 V3（规则先定后跑）。
特征组：对照（现行）、+A、+B、+A+B、+A+B+C（实测物性直接用，没测留空）、+A+B+D（实测优先，没测的用小模型补；
小模型＝HistGradientBoosting，输入为配方元素比例、RDKit 5 个、A、B，只用训练论文的实测配方训练）。
模型：线性岭回归、单调约束梯度提升、随机森林。指标：V3 R²/RMSE，另报“只换溶剂”配对的 R²/RMSE。
另报补值小模型按论文留出的 R²（物性本身能否从组成预测）。用法：python run3.py <类别>"""
import sys, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
from feats3 import *
from explore import mat
from v3net import fkey
from sklearn.ensemble import HistGradientBoostingRegressor

CNAME = sys.argv[1]
OUTD = Path(__file__).parent / "结果_243篇"
rows = class_rows3(CNAME)
for r in rows:
    r["fk"] = fkey(r["s"]["论文"], r["s"]["recipe"])
y = np.array([r["y"] for r in rows]); g = np.array([r["s"]["论文"] for r in rows]); w = N.weights(g)
by = defaultdict(list)
for i, r in enumerate(rows):
    if not r["noncomp"] and r["fk"]:
        by[(g[i], r["s"]["测试"], r["s"]["圈数"])].append(i)
pairs = []
for k, idx in by.items():
    ref = next((i for i in idx if rows[i]["s"]["是否对照"]), idx[0])
    pairs += [(k[0], i, ref) for i in idx if i != ref and rows[i]["fk"] != rows[ref]["fk"]]
npap = defaultdict(set)
for p, i, j in pairs:
    npap[frozenset((rows[i]["fk"], rows[j]["fk"]))].add(p)
V3 = [t for t in pairs if len(npap[frozenset((rows[t[1]]["fk"], rows[t[2]]["fk"]))]) == 1]
V3P = sorted({p for p, *_ in V3})
obs = np.array([y[i] - y[j] for _, i, j in V3])


def solv_part(i):
    return {c: x for c, u, x in rows[i]["fk"] if CTAB.get(c, {}).get("类别") in ("溶剂", "溶剂/添加剂")}


def rest_part(i):
    return {c: x for c, u, x in rows[i]["fk"] if CTAB.get(c, {}).get("类别") not in ("溶剂", "溶剂/添加剂")}


only_solv = np.array([solv_part(i) != solv_part(j) and rest_part(i) == rest_part(j) for _, i, j in V3])
cov = {c: sum(r["x"].get(c) is not None for r in rows) for c in A_COLS + B_COLS + C_COLS}
print(f"## {CNAME}: {len(rows)} 条，V3 {len(V3)} 对（只换溶剂 {only_solv.sum()} 对）；新特征有值的条数 {cov}", flush=True)

# 补值小模型：配方级数据
SUBX = ER + list(RD5) + A_COLS + B_COLS
forms = {}
for i, r in enumerate(rows):
    forms.setdefault((g[i], r["s"]["recipe"]), i)


def sub_predict(target, train_papers):
    ks = [k for k, i in forms.items() if k[0] in train_papers and rows[i]["x"].get(target) is not None]
    if len(ks) < 15:
        return None, len(ks)
    Xs = mat([rows[forms[k]] for k in ks], SUBX); ys = np.array([rows[forms[k]]["x"][target] for k in ks])
    keep = ~np.all(np.isnan(Xs), 0)  # 全空的列（如介电常数）去掉
    m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, min_samples_leaf=5, random_state=0).fit(Xs[:, keep], ys)
    return _Sub(m, keep), len(ks)


class _Sub:
    def __init__(self, m, keep):
        self.m, self.keep = m, keep

    def predict(self, X):
        return self.m.predict(X[:, self.keep])


def sub_quality(target):
    ks = [k for k, i in forms.items() if rows[i]["x"].get(target) is not None]
    ps = sorted({k[0] for k in ks}); o, p = [], []
    for q in ps:
        m, n = sub_predict(target, set(ps) - {q})
        if m is None:
            continue
        te = [k for k in ks if k[0] == q]
        o += [rows[forms[k]]["x"][target] for k in te]; p += list(m.predict(mat([rows[forms[k]] for k in te], SUBX)))
    o, p = np.array(o), np.array(p)
    return {"配方": len(ks), "论文": len(ps), "按论文留出R2": float(1 - ((o - p) ** 2).sum() / ((o - o.mean()) ** 2).sum()) if len(o) > 2 else None}


def r2(o, p):
    return float(1 - ((o - p) ** 2).sum() / ((o - o.mean()) ** 2).sum()) if len(o) > 2 and o.std() > 0 else float("nan")


SETS = {"对照": [], "+A": A_COLS, "+B": B_COLS, "+A+B": A_COLS + B_COLS, "+A+B+C": A_COLS + B_COLS + C_COLS, "+A+B+D": A_COLS + B_COLS + ["ln电导率_补", "ln黏度_补"]}
MODS = {"线性岭回归": (N.Linear, True), "单调约束梯度提升": (N.GBMMono, False), "随机森林": (N.RF, False)}
res = {"类别": CNAME, "V3配对": len(V3), "只换溶剂": int(only_solv.sum()), "新特征覆盖": cov,
       "补值小模型质量": {"ln电导率_实测": sub_quality("ln电导率_实测"), "ln黏度_实测": sub_quality("ln黏度_实测")}, "结果": {}}
print("   补值小模型（组成→物性，按论文留出）：", json.dumps(res["补值小模型质量"], ensure_ascii=False), flush=True)
for sn, extra in SETS.items():
    for mn, (M, lin) in MODS.items():
        t0 = time.time()
        pred = np.full(len(y), np.nan)
        for q in V3P:
            tr = g != q
            if sn == "+A+B+D":
                for tgt, col in (("ln电导率_实测", "ln电导率_补"), ("ln黏度_实测", "ln黏度_补")):
                    m, _ = sub_predict(tgt, set(g[tr]))
                    allp = m.predict(mat(rows, SUBX)) if m is not None else np.full(len(rows), np.nan)
                    for i, r in enumerate(rows):
                        r["x"][col] = r["x"][tgt] if r["x"].get(tgt) is not None else (None if np.isnan(allp[i]) else float(allp[i]))
            cols = cols_for(CNAME, rows, lin)
            cols += [c for c in extra if sum(r["x"].get(c) is not None for r in rows) >= 3 and c not in cols]
            X = mat(rows, cols)
            pred[g == q] = M(cols, CNAME).fit(X[tr], y[tr], g[tr], w[tr]).f(X[g == q])
        pd_ = np.array([pred[i] - pred[j] for _, i, j in V3])
        d = {"R2": r2(obs, pd_), "RMSE": float(np.sqrt(np.mean((obs - pd_) ** 2))),
             "只换溶剂R2": r2(obs[only_solv], pd_[only_solv]), "只换溶剂RMSE": float(np.sqrt(np.mean((obs[only_solv] - pd_[only_solv]) ** 2))) if only_solv.any() else None}
        res["结果"][f"{sn}｜{mn}"] = d
        print(f"   {sn:8s} {mn:8s} V3 R²={d['R2']:+.2f} RMSE={d['RMSE']:.3f} | 只换溶剂 R²={d['只换溶剂R2']:+.2f} RMSE={d['只换溶剂RMSE']:.2f}  {time.time()-t0:.0f}s", flush=True)
json.dump(res, open(OUTD / f"物性对比_{CNAME}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
