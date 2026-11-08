"""step22b：文字向量地图的检验数字（11-08 夜用户：“文字向量地图可以改”“其它的问题也一起改了”）。

原图 B 栏写“问题 1 的 22 条里 20 条落在放大框里”，但放大框本来就是围着这 22 条画的，不能当证据。这里改在原始向量（未降维）里检验：
① 尺度：随机两条说法的余弦相似度分布（中位数、99 分位），让读者知道 0.55 ≈ 不相关；
② 话题聚集：每条问题说法的 50 个最近邻里有几条同问题说法，与随机期望之比；
③ 立场：同派两两相似度 vs 跨派两两相似度的 AUC（0.5 = 分不开）；另报留一法“两派中心”打分的 AUC 与置换 p；
④ 检索找回：留出一条，用其余同问题说法的中心在全部说法里检索，它排第几、前 200 条找回几成；
⑤ 二维图保真：原向量 10 近邻在二维图里仍是 10 近邻的比例、二维距离与余弦的秩相关；10 近邻里同一篇论文的比例。
立场来自 step20 读原文。只存数字，不存摘要（仓库公开）。随机数种子固定。
环境：D:\\envs\\textvec（sentence-transformers；模型 BAAI/bge-small-zh-v1.5 已缓存，离线运行）。
输出：output/说法地图_313篇_2026-11-08/向量检验.json
用法：set HF_HUB_OFFLINE=1 & D:\\envs\\textvec\\Scripts\\python.exe -X utf8 scripts/step22b_vector_checks.py
"""
import glob
import json
import os
from pathlib import Path

import numpy as np

os.environ.setdefault("HF_HUB_OFFLINE", "1")
ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
O = ROOT / "output"
PAPERS = O / "试跑313篇_2026-11-05" / "papers"
EV = O / "机制证据_313篇_2026-11-08" / "机制证据.json"
ATLAS = O / "说法地图_313篇_2026-11-08" / "全部说法二维.json"
OUT = O / "说法地图_313篇_2026-11-08" / "向量检验.json"
MODEL = "BAAI/bge-small-zh-v1.5"
NAME = {"T1": "问题1 稀释剂该不该分解", "T2": "已降级 碳酸酯/P108", "T3": "问题2 LiNO3 加多少", "T4": "问题3 高盐与 LiNO3"}


def auc(pos, neg):
    pos, neg = np.asarray(pos)[:, None], np.asarray(neg)[None, :]
    return float((pos > neg).mean() + 0.5 * (pos == neg).mean())


def main():
    from scipy.stats import spearmanr
    from sentence_transformers import SentenceTransformer
    M = []
    for f in sorted(glob.glob(str(PAPERS / "*" / "candidate.json"))):
        c = json.loads(Path(f).read_text(encoding="utf-8"))
        p = Path(f).parent.name
        for m in c.get("mechanisms", []):
            M.append((p, m["id"], m.get("summary", "")))
    keys = [f"{p}|{i}" for p, i, _ in M]
    key = {k: n for n, k in enumerate(keys)}
    N = len(M)
    E = SentenceTransformer(MODEL).encode([s for *_, s in M], normalize_embeddings=True, batch_size=64)
    rng = np.random.default_rng(0)
    out = {"模型": MODEL, "说法数": N, "说明": "全部在原始向量（未降维）里算；立场来自 step20 读原文；AI 辅助，用户尚未逐项人工确认"}
    # ① 尺度
    a, b = rng.integers(0, N, 200000), rng.integers(0, N, 200000)
    ok = a != b
    r = np.sum(E[a[ok]] * E[b[ok]], 1)
    out["随机两条说法的余弦"] = {"中位数": round(float(np.median(r)), 3), "90分位": round(float(np.percentile(r, 90)), 3),
                          "99分位": round(float(np.percentile(r, 99)), 3)}
    # ②③④ 每个问题
    ev = json.loads(EV.read_text(encoding="utf-8"))
    qs = {}
    for t, x in ev.items():
        A = [key[f"{e['论文']}|{e['机制']}"] for e in x["证据"] if e["立场"] == "A"]
        B = [key[f"{e['论文']}|{e['机制']}"] for e in x["证据"] if e["立场"] == "B"]
        S = A + B
        hits = []
        for i in S:
            sim = E @ E[i]
            sim[i] = -9
            top = np.argpartition(-sim, 50)[:50]
            hits.append(len(set(top.tolist()) & set(S)))
        exp = 50 * (len(S) - 1) / (N - 1)
        same = [float(E[u] @ E[v]) for g in (A, B) for n, u in enumerate(g) for v in g[n + 1:]]
        cross = [float(E[u] @ E[v]) for u in A for v in B]
        # 留一法“两派中心”打分与置换
        def loo(Aa, Bb):
            s = []
            for i in Aa + Bb:
                ca = E[[j for j in Aa if j != i]].mean(0)
                cb = E[[j for j in Bb if j != i]].mean(0)
                s.append(E[i] @ ca / np.linalg.norm(ca) - E[i] @ cb / np.linalg.norm(cb))
            s = np.array(s)
            return auc(s[:len(Aa)], s[len(Aa):])
        real = loo(A, B)
        null = []
        for _ in range(500):
            perm = rng.permutation(S)
            null.append(loo(list(perm[:len(A)]), list(perm[len(A):])))
        ranks = []
        for i in S:
            rest = [j for j in S if j != i]
            sc = E @ E[rest].mean(0)
            sc[rest] = -9
            ranks.append(int((sc > sc[i]).sum()) + 1)
        ranks = np.array(ranks)
        qs[t] = {"名称": NAME.get(t, t), "A": len(A), "B": len(B),
                 "50近邻里同问题说法_平均": round(float(np.mean(hits)), 2), "随机期望": round(exp, 3), "倍数": round(float(np.mean(hits) / exp), 1),
                 "组内平均余弦": round(float(np.mean(same + cross)), 3),
                 "分立场AUC_两两": round(auc(same, cross), 2), "同派平均余弦": round(float(np.mean(same)), 3), "跨派平均余弦": round(float(np.mean(cross)), 3),
                 "分立场AUC_留一中心": round(real, 2), "置换p": round(float((np.array(null) >= real).mean()), 3),
                 "检索排名中位": int(np.median(ranks)), "前200找回": round(float((ranks <= 200).mean()), 2), "前1000找回": round(float((ranks <= 1000).mean()), 2)}
    out["问题"] = qs
    # ⑤ 二维图保真
    xy_d = json.loads(ATLAS.read_text(encoding="utf-8"))["说法"]
    assert [f"{d['论文']}|{d['机制']}" for d in xy_d] == keys, "二维坐标与说法顺序不一致"
    XY = np.array([[d["x"], d["y"]] for d in xy_d])
    pap = np.array([p for p, *_ in M])
    idx = rng.choice(N, 1500, replace=False)
    keep, samep = [], []
    for i in idx:
        sim = E @ E[i]
        sim[i] = -9
        nh = np.argpartition(-sim, 10)[:10]
        d2 = ((XY - XY[i]) ** 2).sum(1)
        d2[i] = 1e18
        n2 = np.argpartition(d2, 10)[:10]
        keep.append(len(set(nh.tolist()) & set(n2.tolist())) / 10)
        samep.append(float((pap[nh] == pap[i]).mean()))
    a, b = rng.integers(0, N, 20000), rng.integers(0, N, 20000)
    rho = spearmanr(-np.sum(E[a] * E[b], 1), np.sqrt(((XY[a] - XY[b]) ** 2).sum(1))).correlation
    out["二维图保真"] = {"原向量10近邻在二维图仍为10近邻": round(float(np.mean(keep)), 2), "二维距离与余弦的秩相关": round(float(rho), 2),
                    "10近邻来自同一篇论文": round(float(np.mean(samep)), 2),
                    "同一篇论文随机期望": round(float(np.mean([(pap == p).mean() for p in pap[idx]])), 3), "抽样说法数": len(idx)}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
