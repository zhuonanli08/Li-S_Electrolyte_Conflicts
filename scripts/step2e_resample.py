"""方案2 Q7：随机层补抽。

做法：用 step2b 的同一套分层、同一种子 20261018 重放原抽样（先核对能抽出原来的 6 篇随机样本 + 3 篇 SPAN），
再沿同一随机数流，对两个随机层各自的剩余候选（去掉已在初筛池里的论文）做一次 permutation，得到固定的逐篇判定顺序。
输出：output/第一阶段_补抽摘录.txt（按顺序的题名 / 摘要 / 结论 / E/S 与锂厚原句，供逐篇判资格）
判定结果写回 output/第一阶段_初筛池.csv（来源 = 补抽(层)，带补抽顺序、结论、理由）。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 -I step2e_resample.py
"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step1c_checkup as S  # noqa: E402
import step1g_figures as G  # noqa: E402
from step2b_pilot_pool import MUST_TITLES, SEED, vals  # noqa: E402
from step2c_screen_digest import conclusion  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "output", "第一阶段_初筛池.csv")
OUT = os.path.join(ROOT, "output", "第一阶段_补抽摘录.txt")
STRATA = ["随机(弱×常规)", "随机(强/适中×常规)"]


def strata_and_order():
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
    picked = set(X.index[(weak | strong) & main_ & (es_span | li_span)])
    picked |= set(X.index[main_ & ((strong & ~weak & anode) | (weak & ~strong & cath))])
    picked |= set(X.index[main_ & weak & strong])
    for t in MUST_TITLES:
        picked |= set(X.index[X["题名"].str.contains(re.escape(t), case=False, na=False)])
    picked |= set(X.index[X["doi"].str.lower().str.contains("pnas.2301260120")])

    # 重放原抽样（与 step2b 完全相同的调用顺序）
    rng = np.random.default_rng(SEED)
    masks = {STRATA[0]: main_ & weak & ~strong & ~anode & ~cath, STRATA[1]: main_ & strong & ~weak & ~anode & ~cath}
    orig = {}
    for lab in STRATA:
        cand = sorted(set(X.index[masks[lab]]) - picked)
        orig[lab] = list(rng.choice(cand, size=min(3, len(cand)), replace=False))
        picked |= set(orig[lab])
    cand = sorted(set(X.index[span & (weak | strong)]) - picked)
    orig["SPAN"] = list(rng.choice(cand, size=min(3, len(cand)), replace=False))

    # 补抽顺序：沿同一随机数流，对每层"全部层内候选去掉原抽样与池内论文"后做 permutation
    pool_dois = set(pd.read_csv(POOL, encoding="utf-8-sig")["doi"].str.lower())
    order = {}
    for lab in STRATA:
        rest = sorted(i for i in set(X.index[masks[lab]]) if X.loc[i, "doi"].lower() not in pool_dois)
        order[lab] = [rest[j] for j in rng.permutation(len(rest))]
    return X, masks, orig, order


def main():
    X, masks, orig, order = strata_and_order()
    pool = pd.read_csv(POOL, encoding="utf-8-sig")
    for lab in STRATA + ["SPAN"]:
        want = set(pool.loc[pool["来源"].str.contains(re.escape(lab if lab != "SPAN" else "SPAN")), "doi"].str.lower())
        got = {X.loc[i, "doi"].lower() for i in orig[lab]}
        print(f"重放核对 {lab}：{'一致' if got == want else '不一致！'}  {sorted(got)}")
    rows = pd.read_pickle(os.path.join(ROOT, "output", "step1_rows_derived.pkl")).set_index("doi")
    ab = json.load(open(os.path.join(ROOT, "output", "abstracts.json"), encoding="utf-8"))
    out = []
    for lab in STRATA:
        print(f"{lab}：层内 {int(masks[lab].sum())} 篇，补抽候选 {len(order[lab])} 篇")
        for k, i in enumerate(order[lab], 1):
            r = X.loc[i]
            key = re.sub(r"[^\w.-]+", "_", r.doi)
            p = os.path.join(S.CACHE, f"{key}.main.txt")
            raw = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
            a = ab.get(r.doi.lower(), {}).get("abstract", "") or (S.pdf_abstract(raw) if raw else "")
            out.append(f"===== {lab} 第 {k} 位 | {r.doi} | {r['年份']} {r['期刊']} | 标签：{r['电解液类别(题名+摘要)']}")
            out.append(f"题名：{r['题名']}")
            out.append(f"摘要：{S.norm(a)[:1200]}")
            out.append(f"结论：{conclusion(raw) if raw else '（无全文缓存）'}")
            if r.doi in rows.index:
                rr = rows.loc[r.doi]
                for col in ("E/S原句", "锂厚原句"):
                    s = str(rr.get(col, "") or "")
                    if s and s != "nan":
                        out.append(f"{col}：" + " ‖ ".join(x[:200] for x in s.split("\n")[:2]))
            out.append("")
    open(OUT, "w", encoding="utf-8").write("\n".join(out))
    print("→", OUT)


if __name__ == "__main__":
    main()
