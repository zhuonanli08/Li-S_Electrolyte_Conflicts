"""step22：全部机制说法的文字向量地图（组会第 13 页“文字向量地图”；11-08 用户同意）。

7477 条已提取机制（candidate.json mechanisms 的中文摘要）→ bge-small-zh-v1.5 向量（归一化）→ UMAP 降到二维（余弦距离，random_state=42）。
另算：① 四组示例句子的相似度（说明“立场相反的两句话向量几乎重合”）；② 每个无定论问题里两派说法在全部说法中的近邻程度；
③ 问题 1 中“离得最近、立场相反”的一对。立场来自 step20 读原文，不来自向量。
环境：D:\\envs\\textvec（需 umap-learn）。输出只存坐标、编号和数字，不存摘要：output/说法地图_313篇_2026-11-08/全部说法二维.json
用法：set HF_HUB_OFFLINE=1 & D:\\envs\\textvec\\Scripts\\python.exe -X utf8 scripts/step22_claim_atlas.py
"""
import glob
import json
import os
from pathlib import Path

import numpy as np

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
PAPERS = ROOT / "output" / "试跑313篇_2026-11-05" / "papers"
EV = ROOT / "output" / "机制证据_313篇_2026-11-08" / "机制证据.json"
OUT = ROOT / "output" / "说法地图_313篇_2026-11-08" / "全部说法二维.json"
MODEL = "BAAI/bge-small-zh-v1.5"
EXAMPLES = [  # (句子 1, 句子 2, 关系)；中文原句与英文译文
    ("TTE 分解生成 LiF，对锂负极有利。", "TTE 分解生成 LiF，但对锂负极有害。", "same topic, opposite stance",
     "TTE decomposes to LiF — good for the Li anode", "TTE decomposes to LiF — bad for the Li anode"),
    ("加入更多 LiNO3 可以延长电池寿命。", "加入更多 LiNO3 会缩短电池寿命。", "same topic, opposite stance",
     "more LiNO₃ extends cycle life", "more LiNO₃ shortens cycle life"),
    ("加入更多 LiNO3 可以延长电池寿命。", "提高盐浓度可以延长电池寿命。", "same stance, different topic",
     "more LiNO₃ extends cycle life", "higher salt concentration extends cycle life"),
    ("TTE 分解生成 LiF，对锂负极有利。", "LiNO3 在正极低电位下不可逆还原。", "different topic",
     "TTE decomposes to LiF — good for the Li anode", "LiNO₃ is reduced irreversibly on the cathode"),
]


def main():
    from sentence_transformers import SentenceTransformer
    import umap
    M = []
    for f in sorted(glob.glob(str(PAPERS / "*" / "candidate.json"))):
        c = json.loads(Path(f).read_text(encoding="utf-8"))
        p = Path(f).parent.name
        for m in c.get("mechanisms", []):
            M.append((p, m["id"], m.get("summary", "")))
    model = SentenceTransformer(MODEL)
    E = model.encode([s for _, _, s in M], normalize_embeddings=True, batch_size=64)
    XY = umap.UMAP(n_neighbors=30, min_dist=0.15, metric="cosine", random_state=42).fit_transform(E)
    key = {f"{p}|{i}": k for k, (p, i, _) in enumerate(M)}
    ev = json.loads(EV.read_text(encoding="utf-8"))
    qs, pairs = {}, {}
    for t, x in ev.items():
        A = [key[f"{e['论文']}|{e['机制']}"] for e in x["证据"] if e["立场"] == "A"]
        B = [key[f"{e['论文']}|{e['机制']}"] for e in x["证据"] if e["立场"] == "B"]
        ranks = []
        for i in A + B:
            sim = E @ E[i]
            pos = np.empty(len(sim), int)
            pos[np.argsort(-sim)] = np.arange(len(sim))
            ranks.append(float(np.median([pos[j] for j in (B if i in A else A)])))
        S = E[A] @ E[B].T if A and B else np.zeros((0, 0))
        best = np.unravel_index(int(np.argmax(S)), S.shape) if S.size else None
        qs[t] = {"A": A, "B": B, "对方派中位排名": float(np.median(ranks)) if ranks else None, "全部说法数": len(M)}
        if best is not None:
            a, b = A[best[0]], B[best[1]]
            pairs[t] = {"A": f"{M[a][0]}|{M[a][1]}", "B": f"{M[b][0]}|{M[b][1]}", "相似度": round(float(S[best]), 3)}
    ex = model.encode([s for e in EXAMPLES for s in e[:2]], normalize_embeddings=True)
    examples = [{"句子1": e[0], "句子2": e[1], "关系": e[2], "英文1": e[3], "英文2": e[4], "相似度": round(float(ex[2 * k] @ ex[2 * k + 1]), 3)}
                for k, e in enumerate(EXAMPLES)]
    OUT.write_text(json.dumps({"模型": MODEL, "说明": "坐标 = UMAP(余弦)；立场来自 step20 读原文",
                               "说法": [{"论文": p, "机制": i, "x": round(float(a), 4), "y": round(float(b), 4)} for (p, i, _), (a, b) in zip(M, XY)],
                               "问题": qs, "最近的相反一对": pairs, "示例": examples}, ensure_ascii=False), encoding="utf-8")
    print(len(M), "条说法 →", OUT)
    print(json.dumps({"最近的相反一对": pairs, "示例": [(e["关系"], e["相似度"]) for e in examples],
                      "对方派中位排名": {t: q["对方派中位排名"] for t, q in qs.items()}}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
