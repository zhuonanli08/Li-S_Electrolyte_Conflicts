"""step23 第二步（papertrail 环境）：SES 式分子宇宙的两张坐标，指纹同 step23_universe_fp.py（Morgan r=2，2048 位），距离 = Jaccard，降维 = UMAP（SES 同法）。

全景：QM9 133,885 个背景分子 ＋ 313 篇 167 个中性有机分子一起降维 → 坐标.npz（emb，前 n_bg 行为背景）。
  看到的是“文献分子只落在化学空间的几个角落”；但 QM9 以小环分子为主，链状分子（甘醇二甲醚、氟化醚）在全景里挤成一点，看不出彼此关系。
放大：每个文献分子取 Jaccard 最相近的 K 个背景分子（并集），连同 167 个文献分子重新降维 → 坐标_近邻.npz（emb、bg_idx = 背景行号）。
  看到的是文献分子按结构分成哪几块、每块周围还有多少没人试过的同类小分子。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step23_universe_embed.py
"""
import time
from pathlib import Path

import numpy as np
import umap

OUT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因") / "output" / "分子宇宙_SES式_2026-11-08"
K = 400  # 11-08 晚用户：右边“太平面了，没有左边好看” → 近邻从 120 增到 400，点更多、能画出和全景一样的疏密纹理
z = np.load(OUT / "指纹.npz")
X = np.unpackbits(z["bits"], axis=1)[:, :2048].astype(bool)
nb = int(z["n_bg"])

if not (OUT / "坐标.npz").exists():
    t = time.time()
    emb = umap.UMAP(n_neighbors=15, min_dist=0.05, metric="jaccard", random_state=42, low_memory=True, verbose=True).fit_transform(X)
    np.savez_compressed(OUT / "坐标.npz", emb=emb.astype(np.float32), n_bg=nb, n_lit=len(X) - nb)
    print(f"global {X.shape} in {time.time() - t:.0f}s")

# 近邻：Jaccard = |A∩B| / |A∪B|
B, L = X[:nb].astype(np.float32), X[nb:].astype(np.float32)
inter = L @ B.T
union = L.sum(1)[:, None] + B.sum(1)[None, :] - inter
sim = inter / np.maximum(union, 1)
idx = np.unique(np.argsort(-sim, axis=1)[:, :K].ravel())
Xs = np.vstack([X[idx], X[nb:]])
t = time.time()
emb2 = umap.UMAP(n_neighbors=15, min_dist=0.05, metric="jaccard", random_state=42, verbose=False).fit_transform(Xs)
np.savez_compressed(OUT / "坐标_近邻.npz", emb=emb2.astype(np.float32), bg_idx=idx, n_lit=len(X) - nb, K=K)
print(f"local: {len(idx)} background neighbours (K = {K}) + {len(X) - nb} literature, {time.time() - t:.0f}s")
