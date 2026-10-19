"""方案2 §5.3 第 2 步：给初筛池每篇做摘录（题名、摘要、结论段、E/S 与锂厚原句），供人工 / Claude 初筛。

输出：output/第一阶段_初筛摘录.txt
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 -I step2c_screen_digest.py
"""
import json
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step1c_checkup as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD_CONC = re.compile(r"\n\s*(?:\d+\.?\s*)?(?:Conclusions?|CONCLUSIONS?|Summary and outlook|Summary|SUMMARY|Outlook)\b[^\n]{0,40}\n")


def body(raw):
    """切掉参考文献区"""
    cut = None
    for m in S.HEAD_REF.finditer(raw):
        if m.start() > 0.4 * len(raw):
            cut = m.start()
    return raw[:cut] if cut else raw


def conclusion(raw, n=1300):
    t = body(raw)
    ms = [m for m in HEAD_CONC.finditer(t) if m.start() > 0.5 * len(t)]
    if ms:
        return S.norm(t[ms[-1].end():ms[-1].end() + n])
    return "（未找到结论标题，取正文末尾）" + S.norm(t[-n:])


def main():
    pool = pd.read_csv(os.path.join(ROOT, "output", "第一阶段_初筛池.csv"), encoding="utf-8-sig")
    rows = pd.read_pickle(os.path.join(ROOT, "output", "step1_rows_derived.pkl")).set_index("doi")
    ab = json.load(open(os.path.join(ROOT, "output", "abstracts.json"), encoding="utf-8"))
    out = []
    for _, p in pool.iterrows():
        key = re.sub(r"[^\w.-]+", "_", p.doi)
        raw = open(os.path.join(S.CACHE, f"{key}.main.txt"), encoding="utf-8").read()
        a = ab.get(p.doi.lower(), {}).get("abstract", "") or S.pdf_abstract(raw)
        out.append(f"===== {p.池编号} | {p.doi} | {p.年份} {p.期刊} | 来源：{p.来源} | 正极层：{p.正极层}")
        out.append(f"题名：{p.题名}")
        out.append(f"摘要：{S.norm(a)[:1200]}")
        out.append(f"结论：{conclusion(raw)}")
        if p.doi in rows.index:
            r = rows.loc[p.doi]
            for col in ("E/S原句", "锂厚原句", "N/P原句"):
                s = str(r.get(col, "") or "")
                if s and s != "nan":
                    out.append(f"{col}：" + " ‖ ".join(x[:220] for x in s.split("\n")[:2]))
        out.append("")
    p = os.path.join(ROOT, "output", "第一阶段_初筛摘录.txt")
    open(p, "w", encoding="utf-8").write("\n".join(out))
    print(p, sum(len(x) for x in out), "字符")


if __name__ == "__main__":
    main()
