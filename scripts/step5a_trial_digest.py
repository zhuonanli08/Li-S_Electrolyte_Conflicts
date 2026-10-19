"""方案 §5.5 C 步试提（选项 B）：从主层核心层随机抽 30 篇，生成供 Claude 逐篇提取的摘录

抽样框：第二阶段_资格筛选.csv 中 Ⅰ类 = Y、主层 = True、层含 C，且不在第一阶段初筛池（深入证据集、留出、后备都排除）。
固定种子 20261019。试提只用来摸字段可得率、修订字段表，不计入正式结果。

每篇摘录：题名、B 步判定（层、改变的因素）、实验部分全文、正文中含数字的句子、图注 / 表注，SI 中含数字的电池相关句子。
输出：
  output/第二阶段_C步试提/抽样名单.csv
  output/第二阶段_C步试提/摘录/Pxxx.txt
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 -I step5a_trial_digest.py
"""
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step1c_checkup as S  # noqa: E402

ROOT = S.ROOT
OUT = os.path.join(ROOT, "output", "第二阶段_C步试提")
DIG = os.path.join(OUT, "摘录")
os.makedirs(DIG, exist_ok=True)
SEED, N = 20261019, 30

SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")
CAP = re.compile(r"^(?:Fig(?:ure)?\.?\s*S?\d+|Table\s*S?\d+|Scheme\s*S?\d+)", re.I)
DIGIT = re.compile(r"\d")
CELL = re.compile(r"mAh|mA\s*g|mA\s*cm|\bC\b|\d\s*C\b|cycles?|Coulombic|\bCE\b|retention|retain|decay|capacity|E/S|µL|uL|mg\s*cm|loading|"
                  r"thick|µm|N/P|overpotential|polarization|self-discharge|pouch|coin|lean|electrolyte", re.I)


def sentences(t):
    return [s.strip() for s in SENT.split(S.norm(t)) if 20 <= len(s.strip()) <= 700]


def split_body(raw):
    """切掉参考文献区；返回 (实验部分, 其余正文)。"""
    cut = None
    for m in S.HEAD_REF.finditer(raw):
        if m.start() > 0.4 * len(raw):
            cut = m.start()
    t = raw[:cut] if cut else raw
    exp = ""
    m = None
    for m0 in S.HEAD_EXP.finditer(t):
        m = m0
    if m:
        rest = t[m.end():]
        e = S.HEAD_END.search(rest)
        exp = rest[:e.start()] if e else rest
        t = t[:m.start()] + (rest[e.start():] if e else "")
    return S.norm(exp), t


def main():
    df = pd.read_csv(os.path.join(ROOT, "output", "第二阶段_资格筛选.csv"), encoding="utf-8-sig", dtype=str).fillna("")
    frame = df[(df["Ⅰ类"] == "Y") & (df["主层"] == "True") & df["层"].str.contains("C") & (df["初筛池编号"] == "") & (df["已有身份"] == "")]
    pick = frame.sample(n=N, random_state=SEED).sort_values("编号")
    print(f"抽样框 {len(frame)} 篇，抽 {len(pick)} 篇")
    pick[["编号", "doi", "年份", "期刊", "题名", "层", "改变的因素", "备注或排除理由"]].to_csv(
        os.path.join(OUT, "抽样名单.csv"), index=False, encoding="utf-8-sig")
    for _, r in pick.iterrows():
        key = re.sub(r"[^\w.-]+", "_", r["doi"])
        fm, fs = os.path.join(S.CACHE, f"{key}.main.txt"), os.path.join(S.CACHE, f"{key}.si.txt")
        raw = open(fm, encoding="utf-8").read() if os.path.exists(fm) else ""
        si = open(fs, encoding="utf-8").read() if os.path.exists(fs) else ""
        exp, rest = split_body(raw)
        body = [s for s in sentences(rest) if DIGIT.search(s) or CAP.match(s)]
        sis = [s for s in sentences(si) if (DIGIT.search(s) and CELL.search(s)) or CAP.match(s)]
        out = [f"# {r['编号']}  {r['doi']}  {r['年份']} {r['期刊']}", f"题名：{r['题名']}",
               f"B 步：层 {r['层']}；改变的因素：{r['改变的因素']}；备注：{r['备注或排除理由']}", "",
               "## 实验部分", exp or "（未切出实验部分）", "", "## 正文（含数字的句子与图表注）"]
        out += [f"- {s}" for s in body]
        if sis:
            out += ["", "## SI（含数字的电池相关句子与图表注）"] + [f"- {s}" for s in sis]
        txt = "\n".join(out)
        with open(os.path.join(DIG, f"{r['编号']}.txt"), "w", encoding="utf-8") as f:
            f.write(txt)
        print(r["编号"], len(txt), "SI" if si else "")


if __name__ == "__main__":
    main()
