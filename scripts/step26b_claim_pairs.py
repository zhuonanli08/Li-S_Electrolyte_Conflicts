"""step26b：路线二“比说法”初筛（11-09 新方案；借鉴 ContraCrow：每条论点到其他文献里找相反说法）。

做法：
1. 313 篇已提取的 7477 条机制说法（candidate.json 的 mechanisms，中文摘要）用 bge-small-zh 编码（与 step22 相同，离线）。
2. 每条说法找其他论文里最相近的 20 条，余弦 ≥ 0.80 的留下（随机两条说法中位 0.57、99 分位 0.71，见 step22b）。
3. 方向词粗判每条说法的“结果方向”：好（提高、改善、抑制穿梭……）记 +1，坏（衰减、腐蚀、加剧……）记 −1；
   “抑制/减少/避免 + 坏事”先算作好再删掉，避免重复计。两条方向相反的才留作候选配对。只是初筛，真假由 step26c 逐对读。
4. 每对论文只留相似度最高的一对；按相似度排序。
输出：output/说法对说法_313篇_2026-11-09/
  候选配对.json（公开：论文、机制编号、相似度、方向，不含摘要）
  候选配对（含原句）.json（本机：附两条摘要，供逐对读；.gitignore 排除）
环境：D:\\envs\\textvec（sentence-transformers，模型已缓存）。
用法：set HF_HUB_OFFLINE=1 & D:\\envs\\textvec\\Scripts\\python.exe -X utf8 scripts/step26b_claim_pairs.py
"""
import glob
import json
import os
import re
from pathlib import Path

import numpy as np

os.environ.setdefault("HF_HUB_OFFLINE", "1")
ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
PAPERS = ROOT / "output" / "试跑313篇_2026-11-05" / "papers"
OUT = ROOT / "output" / "说法对说法_313篇_2026-11-09"
MODEL = "BAAI/bge-small-zh-v1.5"
K, TAU = 20, 0.80

BAD = r"(穿梭|枝晶|副反应|腐蚀|消耗|溶解|极化|过电位|阻抗|衰减|自放电|短路|钝化|分解|团聚|体积膨胀|失活)"
GOOD_FIRST = re.compile(r"(抑制|减少|减轻|缓解|避免|防止|降低|减缓|阻止|阻挡|限制)了?(多硫化物|锂|电解液|溶剂|活性物质)?(的)?" + BAD)
POS = ["提高", "提升", "改善", "增强", "有利", "延长", "更稳定", "稳定性好", "均匀", "致密", "优于", "加快", "加速转化", "促进转化",
       "高库仑效率", "保护", "可逆", "更好", "有益", "利于", "增加容量", "容量更高", "寿命更长"]
NEG = ["降低容量", "容量下降", "容量衰减", "衰减", "恶化", "加剧", "有害", "缩短", "不稳定", "腐蚀", "耗尽", "失效", "短路", "变差",
       "阻碍", "增大极化", "极化增大", "阻抗增大", "增加阻抗", "钝化", "不利", "损失", "降低库仑效率", "库仑效率低", "穿梭严重", "副反应"]


def polarity(s):
    g = len(GOOD_FIRST.findall(s))
    s2 = GOOD_FIRST.sub("", s)
    pos = g + sum(s2.count(w) for w in POS)
    neg = sum(s2.count(w) for w in NEG)
    return (pos > neg) - (pos < neg), pos, neg


def main():
    from sentence_transformers import SentenceTransformer
    OUT.mkdir(parents=True, exist_ok=True)
    M = []
    for f in sorted(glob.glob(str(PAPERS / "*" / "candidate.json"))):
        p = Path(f).parent.name
        for m in json.loads(Path(f).read_text(encoding="utf-8")).get("mechanisms", []):
            s = m.get("summary", "") or ""
            pol, ps, ng = polarity(s)
            M.append({"论文": p, "机制": m["id"], "摘要": s, "来源": m.get("source_type"), "类别": m.get("categories") or [],
                      "性质": m.get("property"), "方向": pol, "好词": ps, "坏词": ng})
    E = SentenceTransformer(MODEL).encode([m["摘要"] for m in M], normalize_embeddings=True, batch_size=64)
    paper = np.array([m["论文"] for m in M])
    pol = np.array([m["方向"] for m in M])
    best = {}
    for i in range(len(M)):
        if pol[i] == 0:
            continue
        sim = E @ E[i]
        sim[paper == paper[i]] = -9
        top = np.argpartition(-sim, K)[:K]
        for j in top:
            if sim[j] < TAU or pol[j] * pol[i] >= 0:
                continue
            a, b = sorted([i, int(j)])
            key = (M[a]["论文"], M[b]["论文"])
            if key not in best or sim[j] > best[key][2]:
                best[key] = (a, b, float(sim[j]))
    pairs = sorted(best.values(), key=lambda x: -x[2])
    pub, loc = [], []
    for n, (a, b, s) in enumerate(pairs, 1):
        row = {"配对": f"CP{n:03d}", "相似度": round(s, 3)}
        for tag, i in (("甲", a), ("乙", b)):
            m = M[i]
            row[tag] = {"论文": m["论文"], "机制": m["机制"], "来源": m["来源"], "类别": m["类别"], "方向": "好" if m["方向"] > 0 else "坏"}
        pub.append(row)
        loc.append({**row, "甲摘要": M[a]["摘要"], "乙摘要": M[b]["摘要"]})
    summary = {"说法": len(M), "有方向的说法": int((pol != 0).sum()), "方向好": int((pol > 0).sum()), "方向坏": int((pol < 0).sum()),
               "候选配对（论文对去重后）": len(pairs), "相似度门槛": TAU, "每条找的近邻": K, "模型": MODEL,
               "说明": "方向词初筛，噪声大；真假由 step26c 逐对读。AI 辅助，用户尚未逐项人工确认。"}
    (OUT / "候选配对.json").write_text(json.dumps({"汇总": summary, "配对": pub}, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "候选配对（含原句）.json").write_text(json.dumps(loc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
