"""同一种改动（加了哪些组分、去掉哪些组分，不看用量）在不同论文里的效果是否一致：可达 R² 上限估计。"""
import warnings; warnings.filterwarnings("ignore")
from feats2 import *
from v3net import fkey
for cname in N.CLASSES:
    rows = class_rows2(cname)
    for r in rows: r["fk"] = fkey(r["s"]["论文"], r["s"]["recipe"])
    y = np.array([r["y"] for r in rows]); g = [r["s"]["论文"] for r in rows]
    by = defaultdict(list)
    for i, r in enumerate(rows):
        if not r["noncomp"] and r["fk"]: by[(g[i], r["s"]["测试"], r["s"]["圈数"])].append(i)
    sig = defaultdict(list)
    for k, idx in by.items():
        ref = next((i for i in idx if rows[i]["s"]["是否对照"]), idx[0])
        for i in idx:
            if i == ref or rows[i]["fk"] == rows[ref]["fk"]: continue
            a = {c for c, *_ in rows[i]["fk"]}; b = {c for c, *_ in rows[ref]["fk"]}
            s = ("加 " + "+".join(sorted(a - b)) if a - b else "") + (" 去 " + "+".join(sorted(b - a)) if b - a else "") or "只改用量/比例"
            sig[s].append((k[0], y[i] - y[ref]))
    multi = {s: v for s, v in sig.items() if len({p for p, _ in v}) >= 2}
    allv = np.array([d for v in multi.values() for _, d in v])
    if len(allv) < 5:
        print(f"## {cname}: 在 ≥2 篇里出现的同种改动太少"); continue
    # 每种改动先按论文取平均（每篇一票），再看篇与篇之间的分散
    within = []; tot = []
    for s, v in multi.items():
        pm = defaultdict(list)
        for p, d in v: pm[p].append(d)
        m = np.array([np.mean(x) for x in pm.values()])
        within += list(m - m.mean()); tot += list(m)
    within, tot = np.array(within), np.array(tot)
    ceil = 1 - (within ** 2).sum() / ((tot - tot.mean()) ** 2).sum()
    print(f"## {cname}: 在 ≥2 篇里出现的同种改动 {len(multi)} 种，涉及 {len(tot)} 个“论文×改动”；"
          f"即使完全知道改动类型，最多能解释的比例（R² 上限）≈ {ceil:.2f}")
    for s, v in sorted(multi.items(), key=lambda kv: -len({p for p, _ in kv[1]}))[:6]:
        pm = defaultdict(list)
        for p, d in v: pm[p].append(d)
        eff = [math.exp(np.mean(x)) for x in pm.values()]
        print(f"   {s[:40]:40s} {len(pm)} 篇：各篇效果（倍数）{', '.join(f'{e:.2f}' for e in sorted(eff))}")
