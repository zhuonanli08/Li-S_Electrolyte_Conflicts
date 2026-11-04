"""243 篇试跑：V3（用户 11-04 确认口径）＋范围判断＋整类留出＋增益的误差范围。规则先定后跑：
- V3：同篇同测试同圈数、实验样对对比样、两侧都不是“非同条件”结果、这对配方只在一篇里比过；整篇留出后推算差距。
- 范围：留出某篇时，以其余论文的配方为训练集；配方有训练集里全为 0 的结构特征非零，或到最近训练配方的距离
  （标准化后的配方特征）超过训练配方之间最近距离的 95% 分位，记“外推”；配对任一侧外推即外推配对。
- 整类留出：含氟溶剂（sF>0 或 α/β 氟化醚氧>0）、有机硫（硫醚/多硫 S>0）两类，训练时拿掉该类全部配方的数据，
  评估“该类配方 vs 本篇非该类对照”的配对。
- 增益：V3 R² 最高的模型（六选一，偏乐观），按论文重抽样 20 次，给标准条件下相对标准醚（P034 R_C）的增益中位数和 2.5–97.5% 区间。
用法：设好试跑环境变量后 python run2.py <类别> [输出名]"""
import sys, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
from feats2 import *
from explore import mat
from v3net import fkey

CNAME = sys.argv[1]
TAG = sys.argv[2] if len(sys.argv) > 2 else CNAME
OUTD = Path(__file__).parent / "结果_243篇"
OUTD.mkdir(exist_ok=True)
REF = ("P034", "R_C")
t00 = time.time()

rows = class_rows2(CNAME)
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
obs = np.array([y[i] - y[j] for _, i, j in V3])
V3P = sorted({p for p, *_ in V3})
print(f"## {TAG}: {len(rows)} 条 / {len(set(g))} 篇；配对 {len(pairs)}，V3 配对 {len(V3)}（{len(V3P)} 篇）；限制统计 {dict(STATS)}", flush=True)

# ---- 范围判断（与模型无关，按留出论文算）----
FCOLS = [c for c in FORM_ALL if sum(r["x"].get(c) is not None for r in rows) >= 3]
FX = mat(rows, FCOLS)
extrap = np.zeros(len(rows), bool)
for q in V3P:
    tr = g != q
    A = FX[tr]; med = np.nanmedian(A, 0); med = np.where(np.isnan(med), 0, med)
    sd = np.nanstd(A, 0); sd = np.where((sd == 0) | np.isnan(sd), 1, sd)
    Z = lambda M: np.where(np.isnan((M - med) / sd), 0, (M - med) / sd)
    U = np.unique(np.round(Z(A), 6), axis=0)
    D = np.sqrt(((U[:, None, :] - U[None, :, :]) ** 2).sum(-1)); np.fill_diagonal(D, np.inf)
    thr = np.quantile(D.min(1), 0.95) if len(U) > 2 else np.inf
    zero = np.nan_to_num(A, nan=0).__abs__().max(0) == 0
    for i in np.where(g == q)[0]:
        xi = FX[i]
        novel = np.any(zero & (np.nan_to_num(xi, nan=0) != 0))
        d = np.sqrt(((U - Z(xi[None])[0]) ** 2).sum(1)).min()
        extrap[i] = novel or d > thr
pext = np.array([extrap[i] or extrap[j] for _, i, j in V3])


def r2(o, p):
    return float(1 - ((o - p) ** 2).sum() / ((o - o.mean()) ** 2).sum()) if len(o) > 2 and o.std() > 0 else float("nan")


def lopo_pred(M, cols, papers):
    X = mat(rows, cols); pred = np.full(len(y), np.nan)
    for q in papers:
        tr = g != q
        pred[g == q] = M(cols, CNAME).fit(X[tr], y[tr], g[tr], w[tr]).f(X[g == q])
    return pred


res = {"类别": CNAME, "版本": TAG, "条数": len(rows), "论文": len(set(g)), "V3配对": len(V3), "V3论文": len(V3P),
       "外推配对": int(pext.sum()), "限制统计": dict(STATS), "模型": {}}
mo = np.array([obs[[p != q for p, *_ in V3]].mean() for q, *_ in V3]) if len(V3) else np.array([])
res["基线"] = {"猜没差别": {"R2": r2(obs, np.zeros_like(obs)), "RMSE": float(np.sqrt(np.mean(obs ** 2)))},
              "猜其他论文平均提升": {"R2": r2(obs, mo), "RMSE": float(np.sqrt(np.mean((obs - mo) ** 2)))}}
best, bestR = None, -1e9
for M in N.MODELS:
    t0 = time.time()
    cols = cols_for(CNAME, rows, M.name in LINEAR)
    pred = lopo_pred(M, cols, V3P)
    pd_ = np.array([pred[i] - pred[j] for _, i, j in V3])
    d = {"R2": r2(obs, pd_), "RMSE": float(np.sqrt(np.mean((obs - pd_) ** 2))),
         "范围内R2": r2(obs[~pext], pd_[~pext]), "范围内RMSE": float(np.sqrt(np.mean((obs[~pext] - pd_[~pext]) ** 2))) if (~pext).any() else None,
         "外推R2": r2(obs[pext], pd_[pext]), "外推RMSE": float(np.sqrt(np.mean((obs[pext] - pd_[pext]) ** 2))) if pext.any() else None,
         "列数": len(cols), "obs": obs.tolist(), "pred": pd_.tolist(), "外推": pext.tolist(),
         "标签": [f"{p} {rows[i]['s']['配方']} vs {rows[j]['s']['配方']}" for p, i, j in V3]}
    res["模型"][M.name] = d
    if d["R2"] == d["R2"] and d["R2"] > bestR and M.name != "线性混合模型":
        best, bestR = M, d["R2"]
    print(f"   {M.name:8s} V3 R²={d['R2']:+.2f} RMSE={d['RMSE']:.3f} | 范围内({int((~pext).sum())}对) R²={d['范围内R2']:+.2f} | 外推({int(pext.sum())}对) R²={d['外推R2']:+.2f}  {time.time()-t0:.0f}s", flush=True)
print(f"   基线：{json.dumps(res['基线'], ensure_ascii=False)}", flush=True)

# ---- 整类留出（用 V3 最好的模型）----
fam = {"含氟溶剂": lambda x: any((x.get(k) or 0) > 0 for k in ("sF", "sO_α氟化醚", "sO_β氟化醚")),
       "有机硫": lambda x: (x.get("硫醚/多硫S") or 0) > 0}
res["整类留出"] = {}
cols = cols_for(CNAME, rows, best.name in LINEAR)
X = mat(rows, cols)
for fn, f in fam.items():
    inf = np.array([f(r["x"]) for r in rows])
    fp = [(p, i, j) for p, i, j in pairs if inf[i] != inf[j]]
    if len(fp) < 3:
        res["整类留出"][fn] = {"配对": len(fp), "说明": "配对太少"}; continue
    m = best(cols, CNAME).fit(X[~inf], y[~inf], g[~inf], w[~inf])
    pr = m.f(X)
    o = np.array([y[i] - y[j] for _, i, j in fp]); p_ = np.array([pr[i] - pr[j] for _, i, j in fp])
    res["整类留出"][fn] = {"配对": len(fp), "论文": len({p for p, *_ in fp}), "R2": r2(o, p_), "RMSE": float(np.sqrt(np.mean((o - p_) ** 2))),
                       "猜没差别R2": r2(o, np.zeros_like(o))}
    print(f"   整类留出 {fn}：{len(fp)} 对 R²={res['整类留出'][fn]['R2']:+.2f} RMSE={res['整类留出'][fn]['RMSE']:.3f}（猜没差别 R²={res['整类留出'][fn]['猜没差别R2']:+.2f}）", flush=True)

# ---- 标准条件增益与误差范围 ----
std = ({} if "Li‖Cu" in CNAME else dict(N.STD_COMMON)) | N.STD_CLASS[CNAME]
refx = next((r["x"] for r in rows if (r["s"]["论文"], r["s"]["recipe"]) == REF), None)
if refx is None:
    s0 = next((s for s in read_json("表述.json") if (s["论文"], s["recipe"]) == REF), None)
    refx = {k: (s0["元素比例"] or {}).get(k) for k in ER} | rd5(*REF) | other(*REF)
at = lambda x: N.at_all(np.array([np.nan if x.get(c) is None else x[c] for c in cols], float), std, cols)[None]
forms = {}
for r in rows:
    forms.setdefault((r["s"]["论文"], r["s"]["recipe"]), r)
papers = sorted(set(g)); rng = np.random.default_rng(0); B = 20
G = defaultdict(list)
for b in range(B):
    pick = rng.choice(papers, len(papers), replace=True)
    idx = np.concatenate([np.where(g == p)[0] for p in pick])
    gb = np.concatenate([[f"{p}#{k}"] * int((g == p).sum()) for k, p in enumerate(pick)])
    m = best(cols, CNAME, seed=b).fit(X[idx], y[idx], gb, N.weights(gb))
    fr = m.f(at(refx))[0]
    for k, r in forms.items():
        G[k].append(m.f(at(r["x"]))[0] - fr)
res["增益"] = [{"论文": k[0], "配方": r["s"]["配方"], "配方名": r["s"]["配方名"], "中位数": float(np.median(G[k])),
               "下": float(np.percentile(G[k], 2.5)), "上": float(np.percentile(G[k], 97.5))} for k, r in forms.items()]
wid = np.array([d["上"] - d["下"] for d in res["增益"]])
res["增益说明"] = {"模型": best.name, "重抽样": B, "配方数": len(forms), "区间宽度中位数(ln)": float(np.median(wid))}
print(f"   增益：{best.name}，{len(forms)} 个配方，95% 区间宽度中位数 {np.median(wid):.2f}（ln）；用时 {time.time()-t00:.0f}s", flush=True)
json.dump(res, open(OUTD / f"V3_{TAG}.json", "w", encoding="utf-8"), ensure_ascii=False)
