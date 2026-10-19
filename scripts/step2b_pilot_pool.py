"""方案2 §5.2：生成证据表试点的初筛池。

来源：同篇跨条件（主层）、稀有格（主层）、两侧都比过（主层）、必读、随机 6 篇、SPAN 3 篇。
输出：output/第一阶段_初筛池.csv
用法：D:\\anaconda\\envs\\papertrail\\python.exe -I step2b_pilot_pool.py
"""
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step1g_figures as G  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 20261018

# v1 附录 B"权衡与适中溶剂化"6 篇 + ChemElectroChem 2026 电解液用量与类型；按题名片段找
MUST_TITLES = [
    "Balancing Anodic Stability and Cathodic Kinetics",
    "Solvation-Mediated Trade-Off between Anode Stability and Cathode Kinetics",
    "Dynamic Balance Between Solvation Strength and Polysulfides Reaction Heterogeneity",
    "Designing Moderately-Solvating Electrolytes",
    "Low-Density Moderately Solvating Electrolytes",
    "Decoupling the Roles of Li",
    "Effect of the Electrolyte Amount and Type",
]
KIM2024 = "10.1038/s41467-023-44527-x"  # 不在 02 库，单独补下载到 补充文献/kim2024


def vals(s):
    return [float(v) for v in re.findall(r"\d+(?:\.\d+)?", str(s))] if pd.notna(s) else []


def main():
    X, B, cat, conds = G.build()
    fam = X["电解液类别(题名+摘要)"].fillna("").str.split("; ")
    has = lambda ks: fam.apply(lambda xs: any(k in xs for k in ks))  # noqa: E731
    weak = has(["弱溶剂化", "局部高浓", "高浓", "难溶"])
    strong = has(["强溶剂化", "适中溶剂化"])
    main_ = X["主层"].astype(bool)
    span = X["正极层"] == "SPAN"
    anode = B[conds[1]]
    cath = B[conds[0]] & B[conds[2]] & ~anode
    es_span = X["E/S值"].apply(vals).apply(lambda v: bool(v) and min(v) <= 5 and max(v) >= 10)
    li_span = X["锂厚值"].apply(vals).apply(lambda v: bool(v) and min(v) <= 50 and max(v) >= 200)

    src = {i: [] for i in X.index}
    for i in X.index[(weak | strong) & main_ & es_span]:
        src[i].append("跨E/S")
    for i in X.index[(weak | strong) & main_ & li_span]:
        src[i].append("跨锂厚")
    for i in X.index[main_ & ((strong & ~weak & anode) | (weak & ~strong & cath))]:
        src[i].append("稀有格")
    for i in X.index[main_ & weak & strong]:
        src[i].append("两侧都有")
    for t in MUST_TITLES:
        hit = X.index[X["题名"].str.contains(re.escape(t), case=False, na=False)]
        if len(hit) == 0:
            print("必读未找到：", t)
        for i in hit:
            src[i].append("必读")
    gao = X.index[X["doi"].str.lower().str.contains("pnas.2301260120")]
    for i in gao:
        src[i].append("必读")

    rng = np.random.default_rng(SEED)
    picked = {i for i, s in src.items() if s}
    for lab, m in [("随机(弱×常规)", main_ & weak & ~strong & ~anode & ~cath),
                   ("随机(强/适中×常规)", main_ & strong & ~weak & ~anode & ~cath)]:
        cand = sorted(set(X.index[m]) - picked)
        for i in rng.choice(cand, size=min(3, len(cand)), replace=False):
            src[i].append(lab)
            picked.add(i)
    cand = sorted(set(X.index[span & (weak | strong)]) - picked)
    for i in rng.choice(cand, size=min(3, len(cand)), replace=False):
        src[i].append("SPAN")

    rows = []
    for i, s in src.items():
        if not s:
            continue
        r = X.loc[i]
        rows.append({"doi": r.doi, "年份": r["年份"], "期刊": r["期刊"], "题名": r["题名"], "来源": "；".join(dict.fromkeys(s)),
                     "主层": bool(r["主层"]), "正极层": r["正极层"], "溶剂化标签": r["电解液类别(题名+摘要)"],
                     "E/S值": r["E/S值"], "锂厚值": r["锂厚值"], "N/P值": r["N/P值"], "硫载量值": r["硫载量值"]})
    rows.append({"doi": KIM2024, "年份": 2024, "期刊": "Nature Communications",
                 "题名": "Solvation-property relationship of lithium-sulphur battery electrolytes", "来源": "必读",
                 "主层": True, "正极层": "硫碳(待核)", "溶剂化标签": "", "E/S值": "", "锂厚值": "", "N/P值": "", "硫载量值": ""})
    out = pd.DataFrame(rows)
    order = {"跨E/S": 0, "跨锂厚": 0, "稀有格": 1, "两侧都有": 1, "必读": 2}
    out["_k"] = out["来源"].apply(lambda s: min(order.get(x, 3) for x in s.split("；")))
    out = out.sort_values(["_k", "年份"]).drop(columns="_k").reset_index(drop=True)
    out.insert(0, "池编号", [f"S{n + 1:02d}" for n in range(len(out))])
    p = os.path.join(ROOT, "output", "第一阶段_初筛池.csv")
    out.to_csv(p, index=False, encoding="utf-8-sig")
    print("初筛池", len(out), "篇 →", p)
    print(out["来源"].str.split("；").explode().value_counts().to_string())


if __name__ == "__main__":
    main()
