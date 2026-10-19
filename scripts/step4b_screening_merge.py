"""方案 4 §3 B2/B3：合并逐篇判定 → 资格筛选表；抽漏检复核样本；出存疑 / 抽查用全文摘录

输入：
  output/第二阶段_资格筛选/判定_原始.txt     Claude 逐篇判定（编号|Ⅰ类|层|改变的因素|Ⅱ类|Ⅱ内容|备注或排除理由）
  output/第二阶段_资格筛选/代码定位.csv       step4a 输出
输出：
  output/第二阶段_资格筛选.csv                         每篇一行（判定 + 代码定位）
  output/第二阶段_资格筛选/复核摘录_漏检抽查.txt        Ⅰ 类判 N 的论文按固定种子抽 ≥10%，全文中与电解液相关的全部句子
  output/第二阶段_资格筛选/复核摘录_存疑.txt            Ⅰ 类判 ? 的论文，同上
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 -I step4b_screening_merge.py
"""
import math
import os
import random
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step1c_checkup as S  # noqa: E402
import step4a_coverage_digest as D  # noqa: E402

ROOT = S.ROOT
DIR = os.path.join(ROOT, "output", "第二阶段_资格筛选")
SEED = 20261019
COLS = ["编号", "Ⅰ类", "层", "改变的因素", "Ⅱ类", "Ⅱ内容", "备注或排除理由"]
KEY = re.compile(r"electrolytes?\b|additives?\b|LiNO\s?3|\bsolvents?\b|co-?solvent|diluent|\bsalts?\b|\bE/S\b|catholyte|mediator|catalys", re.I)
CAP = 150


def read_rows(name, ncol):
    rows = []
    for line in open(os.path.join(DIR, name), encoding="utf-8"):
        if line.startswith("P"):
            f = line.rstrip("\n").split("|")
            assert len(f) == ncol, line
            rows.append(f)
    return rows


def load_judgments():
    df = pd.DataFrame([dict(zip(COLS, f)) for f in read_rows("判定_原始.txt", 7)])
    assert df["编号"].is_unique and len(df) == 669
    df["初判Ⅰ类"], df["初判Ⅱ类"], df["复核依据"] = df["Ⅰ类"], df["Ⅱ类"], ""
    fix = {f[0]: f for f in read_rows("判定_复核.txt", 8)}
    for i, r in df.iterrows():
        if r["编号"] in fix:
            f = fix[r["编号"]]
            for c, v in zip(COLS[1:] + ["复核依据"], f[1:]):
                df.at[i, c] = v
    return df


def flag(r):
    note = r["备注或排除理由"]
    out = []
    if "范围边界" in note or "是否纳入待定" in note:
        out.append("范围边界")
    if r["初判Ⅰ类"] == "?":
        out.append("存疑已改判")
    if r["Ⅰ类"] == "Y" and ("待核" in note or "边界" in note) and "范围边界" not in note:
        out.append("层别或对照待核")
    if r["Ⅱ类"] == "?":
        out.append("Ⅱ类定性或待核")
    return "；".join(out)


def related_sentences(doi):
    key = re.sub(r"[^\w.-]+", "_", doi)
    fm, fs = os.path.join(S.CACHE, f"{key}.main.txt"), os.path.join(S.CACHE, f"{key}.si.txt")
    raw = open(fm, encoding="utf-8").read() if os.path.exists(fm) else ""
    si = open(fs, encoding="utf-8").read() if os.path.exists(fs) else ""
    sm = [s for s in D.sentences(D.body(raw)) if KEY.search(s)] if raw else []
    ss = [("［SI］" + s) for s in D.sentences(si) if KEY.search(s)] if si else []
    return sm, ss


def digest(df, ids, title):
    out = [f"# {title}", f"# 每篇列出正文（去参考文献）+ SI 中含 electrolyte / additive / LiNO3 / solvent / salt / E/S / mediator / catalyst 的全部句子（每篇上限 {CAP} 句）", ""]
    for _, r in df[df["编号"].isin(ids)].iterrows():
        sm, ss = related_sentences(r["doi"])
        allv = sm + ss
        out.append(f"#### {r['编号']} | {r['doi']} | {r['题名']}")
        out.append(f"原判：Ⅰ={r['Ⅰ类']} 层={r['层']} 因素={r['改变的因素']} Ⅱ={r['Ⅱ类']} 备注={r['备注或排除理由']}")
        out.append(f"相关句 {len(sm)}（正文）+ {len(ss)}（SI）" + ("，已截断" if len(allv) > CAP else ""))
        for s in allv[:CAP]:
            out.append("· " + D.clip(s, 320))
        out.append("")
    return "\n".join(out)


REASON = [("纯计算 / 模拟 / 模型", r"纯计算|纯模拟|模型|模拟为主|DFT|MD|计算数据库|机器学习"), ("综述 / 观点 / 评述 / 封面", r"综述|观点|评述|Preview|封面|文献数据"),
          ("无锂硫电池，或只有对称电池 / 物性测试", r"无锂硫电池|无电池|非锂硫|LFP|Li-O2|Na-S|铜离子|物性|对称电池"),
          ("电解液固定，比较正极 / 隔膜 / 负极等", r"电解液固定|非电解液变量|电解液非变量|正极|隔膜|夹层|负极|碳|同位素|声场"),
          ("单一电解液（表征 / 方法 / E/S 等）", r"单一|E/S|配方固定|配方不变|老化"), ("有电解液对比但无配方性能比较", r"无性能|无.*配方性能比较|传输性质"),
          ("非液态电解液", r"固液混合|固态")]


def stats(df):
    import json
    y = df[df["Ⅰ类"] == "Y"]
    lay = {k: int(y["层"].str.split("+").apply(lambda s: k in s).sum()) for k in ["C", "M", "A", "N"]}
    only = y["层"].value_counts().to_dict()
    main = y[y["主层"] == True]  # noqa: E712
    untagged = y[y["题名摘要标签"].fillna("").str.strip() == ""]
    neg = df[df["Ⅰ类"] == "N"]
    why = {}
    for _, r in neg.iterrows():
        k = next((n for n, p in REASON if re.search(p, r["备注或排除理由"])), "其他")
        why[k] = why.get(k, 0) + 1
    s = {"总数": len(df), "Ⅰ类": df["Ⅰ类"].value_counts().to_dict(), "Ⅱ类": df["Ⅱ类"].value_counts().to_dict(),
         "Ⅰ或Ⅱ合格": int(((df["Ⅰ类"] == "Y") | (df["Ⅱ类"] == "Y")).sum()), "Ⅰ不合格但Ⅱ合格": int(((df["Ⅰ类"] == "N") & (df["Ⅱ类"] == "Y")).sum()),
         "Ⅰ类含层": lay, "Ⅰ类层组合": only, "Ⅰ类主层（液态+硫碳+锂金属）": len(main),
         "主层含层": {k: int(main["层"].str.split("+").apply(lambda s: k in s).sum()) for k in ["C", "M", "A", "N"]},
         "Ⅰ类按正极": y["正极层"].value_counts().to_dict(), "Ⅰ类按负极": y["负极"].value_counts().to_dict(),
         "Ⅰ类无旧题名摘要标签": len(untagged), "Ⅰ类含C且无旧标签": int(untagged["层"].str.contains("C").sum()),
         "Ⅰ类按年份": y["年份"].value_counts().sort_index().to_dict(), "排除理由": why,
         "需人工看": df["需人工看"].str.split("；").explode().replace("", pd.NA).dropna().value_counts().to_dict(),
         "深读与留出": df[df["已有身份"].fillna("") != ""][["编号", "初筛池编号", "Ⅰ类", "Ⅱ类"]].values.tolist(),
         "Ⅱ类合格": df[df["Ⅱ类"] == "Y"][["编号", "初筛池编号", "Ⅰ类", "Ⅱ内容"]].fillna("").values.tolist()}
    json.dump(s, open(os.path.join(DIR, "统计.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    for k, v in s.items():
        if k not in ("深读与留出", "Ⅱ类合格"):
            print(k, v)


def main():
    j = load_judgments()
    loc = pd.read_csv(os.path.join(DIR, "代码定位.csv"), encoding="utf-8-sig")
    df = j.merge(loc, on="编号", how="left", validate="one_to_one")
    df["判定者"] = "Claude（AI 判定，用户未复核）"
    df["需人工看"] = df.apply(flag, axis=1)
    front = ["编号", "doi", "年份", "期刊", "题名", "已有身份", "初筛池编号"] + COLS[1:] + ["需人工看", "复核依据", "初判Ⅰ类", "初判Ⅱ类", "判定者"]
    df = df[front + [c for c in df.columns if c not in front]]
    df.to_csv(os.path.join(ROOT, "output", "第二阶段_资格筛选.csv"), index=False, encoding="utf-8-sig")
    stats(df)
    if "--digest" not in sys.argv:
        return

    neg = sorted(j.loc[j["初判Ⅰ类"] == "N", "编号"])
    k = math.ceil(0.10 * len(neg))
    samp = sorted(random.Random(SEED).sample(neg, k))
    unsure = sorted(j.loc[j["初判Ⅰ类"] == "?", "编号"])
    open(os.path.join(DIR, "复核摘录_漏检抽查.txt"), "w", encoding="utf-8").write(
        digest(df, samp, f"B3 漏检抽查：Ⅰ 类判 N 共 {len(neg)} 篇，种子 {SEED} 抽 {k} 篇"))
    open(os.path.join(DIR, "复核摘录_存疑.txt"), "w", encoding="utf-8").write(
        digest(df, unsure, f"存疑复核：Ⅰ 类判 ? 共 {len(unsure)} 篇"))
    print("合并", len(df), "篇；Ⅰ类", df["Ⅰ类"].value_counts().to_dict(), "；Ⅱ类", df["Ⅱ类"].value_counts().to_dict())
    print("漏检抽查", k, "/", len(neg), "：", " ".join(samp))
    print("存疑", len(unsure), "：", " ".join(unsure))


if __name__ == "__main__":
    main()
