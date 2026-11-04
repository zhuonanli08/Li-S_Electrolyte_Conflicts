"""草稿第 4 步：模型解释（置换重要性＋按论文重抽样看稳定性）。规则先定后跑：
每类、每种模型（线性岭回归、随机森林）按论文有放回抽样 30 次；在袋外论文的篇内配对上，
把某一列在袋外各行之间打乱 5 次，看配对差距的均方误差平均增加多少（相对未打乱的比例）。
保留：平均增加 >0，且至少一种模型中 ≥50% 的抽样排进前 5；舍去：两种模型平均增加都 ≤0；其余待定。"""
import json, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
from feats2 import *
from explore import mat
from v3net import fkey, pairs_of

OUTD = Path(__file__).parent / "结果_243篇"
B, NPERM, TOP = 30, 5, 5
MODS = {"线性岭回归": (N.Linear, True), "随机森林": (N.RF, False)}

out = {}
for cname in N.CLASSES:
    rows = class_rows2(cname)
    for r in rows:
        r["fk"] = fkey(r["s"]["论文"], r["s"]["recipe"])
    prs = [(i, j) for _, _, i, j in pairs_of(rows) if not rows[i]["noncomp"] and not rows[j]["noncomp"]]
    y = np.array([r["y"] for r in rows]); g = np.array([r["s"]["论文"] for r in rows])
    papers = sorted(set(g)); rng = np.random.default_rng(0)
    out[cname] = {}
    for mn, (M, lin) in MODS.items():
        cols = cols_for(cname, rows, lin); X = mat(rows, cols)
        imp = {c: [] for c in cols}; topc = Counter(); nb = 0
        for b in range(B):
            pick = rng.choice(papers, len(papers), replace=True)
            oob = [p for p in papers if p not in set(pick)]
            op = [(i, j) for i, j in prs if g[i] in oob]
            if len(op) < 3:
                continue
            idx = np.concatenate([np.where(g == p)[0] for p in pick])
            gb = np.concatenate([[f"{p}#{k}"] * int((g == p).sum()) for k, p in enumerate(pick)])
            m = M(cols, cname, seed=b).fit(X[idx], y[idx], gb, N.weights(gb))
            orow = np.where(np.isin(g, oob))[0]
            def err(XX):
                p = np.full(len(y), np.nan); p[orow] = m.f(XX[orow])
                return np.mean([((y[i] - y[j]) - (p[i] - p[j])) ** 2 for i, j in op])
            e0 = err(X); nb += 1
            this = {}
            for k, c in enumerate(cols):
                inc = []
                for _ in range(NPERM):
                    Xp = X.copy(); Xp[orow, k] = rng.permutation(X[orow, k]); inc.append(err(Xp) / e0 - 1)
                this[c] = float(np.mean(inc)); imp[c].append(this[c])
            for c in sorted(this, key=lambda c: -this[c])[:TOP]:
                topc[c] += 1
        out[cname][mn] = {c: {"平均增加": float(np.mean(v)) if v else None, "前5比例": topc[c] / nb if nb else None} for c, v in imp.items()}
        out[cname][mn]["_有效抽样"] = nb
        print(f"{cname} {mn}: 有效抽样 {nb}", flush=True)

# 汇总成保留/待定/舍去
table = {}
for cname, d in out.items():
    feats = sorted({c for mn in d for c in d[mn] if not c.startswith("_")})
    for c in feats:
        vals = [d[mn].get(c) for mn in d if c in d[mn]]
        means = [v["平均增加"] for v in vals if v and v["平均增加"] is not None]
        keep = any(v and v["平均增加"] and v["平均增加"] > 0 and v["前5比例"] >= 0.5 for v in vals)
        drop = means and all(m <= 0 for m in means)
        table.setdefault(c, {})[cname] = "保留" if keep else "舍去" if drop else "待定"
json.dump({"明细": out, "判定": table}, open(OUTD / "模型解释.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n描述符/条件 | " + " | ".join(N.CLASSES))
for c, d in table.items():
    print(f"{c:12s} | " + " | ".join(d.get(k, "—") for k in N.CLASSES))
