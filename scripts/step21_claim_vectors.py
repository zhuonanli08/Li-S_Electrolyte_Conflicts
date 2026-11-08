"""step21：说法地图的文字向量与发表年份（11-08 用户：说法地图要把发表顺序和相近程度结合起来；一个点 = 一篇论文的一条说法）。

文字向量只用来判断“两条说法讲的是不是同一件事”（话题相近）；立场（哪一派）来自 step20 读原文的判断，不来自向量——
11-08 试验过：字片段 TF-IDF、bge-small-zh 向量、两种 NLI 模型（两两判断、以问题为准）都分不出问题 1 的两派（区分度 0.50–0.56）。
向量：BAAI/bge-small-zh-v1.5，输入 = 该机制的提取摘要（本机 candidate.json），归一化。输出只存数字，不存摘要（仓库公开）。
年份：F 版清单 manifest.json 的 year；缺的按编号推断（编号与年份秩相关 0.992），取编号最近的 4 篇有年份论文的中位数，标“推断”。
环境：D:\\envs\\textvec（torch CPU＋sentence-transformers，11-08 新建；不动 papertrail）。模型经 hf-mirror 下载。
输出：output/说法地图_313篇_2026-11-08/说法向量.json
用法：D:\\envs\\textvec\\Scripts\\python.exe -X utf8 scripts/step21_claim_vectors.py
"""
import json
import os
from pathlib import Path

import numpy as np

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
EV = ROOT / "output" / "机制证据_313篇_2026-11-08" / "机制证据.json"
PAPERS = ROOT / "output" / "试跑313篇_2026-11-05" / "papers"
MANI = ROOT / "output" / "F版全量提取_2026-11-02" / "manifest.json"
OUT = ROOT / "output" / "说法地图_313篇_2026-11-08"
MODEL = "BAAI/bge-small-zh-v1.5"


def years():
    m = {x["id"]: x.get("year") for x in json.loads(MANI.read_text(encoding="utf-8"))}
    known = sorted((int(k[1:]), int(v)) for k, v in m.items() if v and str(v).isdigit())

    def get(p):
        v = m.get(p)
        if v and str(v).isdigit():
            return int(v), False
        n = int(p[1:])
        near = sorted(known, key=lambda x: abs(x[0] - n))[:4]
        return int(np.median([y for _, y in near])), True
    return get


def main():
    from sentence_transformers import SentenceTransformer
    OUT.mkdir(parents=True, exist_ok=True)
    ev = json.loads(EV.read_text(encoding="utf-8"))
    yr = years()
    rows, texts = [], []
    for t, x in ev.items():
        for i in x["证据"]:
            c = json.loads((PAPERS / i["论文"] / "candidate.json").read_text(encoding="utf-8"))
            m = next(m for m in c["mechanisms"] if m["id"] == i["机制"])
            y, inferred = yr(i["论文"])
            rows.append({"问题": t, "论文": i["论文"], "机制": i["机制"], "立场": i["立场"], "来源类型": i["来源类型"],
                         "Claude 一句话": i["Claude 一句话"], "年份": y, "年份是推断": inferred})
            texts.append(m.get("summary", ""))
    E = SentenceTransformer(MODEL).encode(texts, normalize_embeddings=True)
    for r, v in zip(rows, E):
        r["向量"] = [round(float(a), 5) for a in v]
    (OUT / "说法向量.json").write_text(json.dumps({"模型": MODEL, "说明": "向量只表示话题相近；立场来自 step20 读原文", "说法": rows},
                                              ensure_ascii=False), encoding="utf-8")
    print(len(rows), "条说法；年份推断", sum(r["年份是推断"] for r in rows), "条 →", OUT / "说法向量.json")


if __name__ == "__main__":
    main()
