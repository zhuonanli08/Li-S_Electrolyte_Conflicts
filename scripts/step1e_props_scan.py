"""第 1 步 e：统计电解液物性值的报告情况（零成本正则，沿用 step1c 的分区与自述判定）。

字段：Li⁺ 迁移数、离子电导率、给体数 DN、粘度、电化学稳定窗口、界面 / 电荷转移阻抗、库仑效率（Li‖Cu 与全电池分开）
输出：output/第1步_物性报告率.xlsx（汇总 + 逐篇，每格附原句）
"""
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step1c_checkup as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM = S.NUM
NOEND = S.NOEND

PROPS = {
    # 名称: (正则, 值范围, 说明)
    "Li⁺迁移数": (r"(?:transference number|transfer(?:ence)? number|\bt\s*Li\s*\+?|\btLi\+?|\bt\s*\+)\s*" + NOEND + r"{0,60}?(?<![\d.])(0\.\d+)",
                (0.01, 1.0)),
    "离子电导率": (r"conductivit\w*" + NOEND + r"{0,80}?" + NUM + r"\s*(?:×\s*10\s*-?\s*\d\s*)?(?:mS|S|µS)\s*(?:cm\s*-?\s*1|/\s*cm)", (0, 1000)),
    "给体数DN": (r"(?:donor numbers?|\bDNs?\b)\s*(?:\(DN\))?" + NOEND + r"{0,40}?(?<![\d.])" + NUM + r"(?!\s*(?:%|wt|M\b|mg|µ|°|nm|V\b|mA))", (0, 70)),
    "粘度": (r"viscosit\w*" + NOEND + r"{0,80}?" + NUM + r"\s*(?:mPa\s*\.?\s*s|mPa|cP\b|cp\b|Pa\s*s)", (0, 10000)),
    "电化学稳定窗口": (r"(?:electrochemical (?:stability )?windows?|stability windows?|oxidation (?:stability|potential|limit|voltage)|anodic stability|decomposition (?:voltage|potential)|oxidative stability)"
                 + NOEND + r"{0,80}?" + NUM + r"\s*V\b", (0.5, 7)),
    "界面/电荷转移阻抗": (r"(?:interfac\w* (?:resistance|impedance)|interface (?:resistance|impedance)|charge[\s-]*transfer resistances?|\bR\s*ct\b|\bR\s*SEI\b|\bR\s*int\b|\bR\s*interface\b)"
                   + NOEND + r"{0,80}?" + NUM + r"\s*(?:Ω|Ω|ohm|Ohm|W\s*cm|kΩ)", (0, 1e5)),
    "库仑效率_Li‖Cu": (r"(?:Coulombic efficienc\w*|\bCEs?\b)" + NOEND + r"{0,80}?(?<![\d.])(9\d(?:\.\d+)?|100(?:\.0+)?)\s*%", (90, 100)),
    "库仑效率_全电池": (r"(?:Coulombic efficienc\w*|\bCEs?\b)" + NOEND + r"{0,80}?(?<![\d.])(\d{2}(?:\.\d+)?|100(?:\.0+)?)\s*%", (50, 100)),
}
LICU_CTX = re.compile(r"Li\s*(?:\|\||/|\||-|//)\s*Cu|Cu\s*(?:\|\||/|\||-|//)\s*Li|Aurbach|Li[\s-]+Cu|plating|stripping|deposition", re.I)


def scan(doi):
    key = re.sub(r"[^\w.-]+", "_", doi)
    raw = open(os.path.join(S.CACHE, f"{key}.main.txt"), encoding="utf-8").read()
    p = os.path.join(S.CACHE, f"{key}.si.txt")
    exp, rest = S.zones(raw)
    si = S.norm(open(p, encoding="utf-8").read()) if os.path.exists(p) else ""
    Z = [("EXP", exp), ("SI", si), ("MAIN", rest)]
    r = {"doi": doi}
    for name, (pat, (lo, hi)) in PROPS.items():
        hits = S.find_all(pat, Z, S.fv, vmin=lo, vmax=hi)
        if name == "库仑效率_Li‖Cu":
            hits = [h for h in hits if LICU_CTX.search(h[2])]
        elif name == "库仑效率_全电池":
            hits = [h for h in hits if not LICU_CTX.search(h[2])]
        mark, rep, vals, snip = S.summarize(hits, max)
        r[name], r[name + "_值"], r[name + "_原句"] = mark, vals, snip
    return r


def main():
    base = pd.read_pickle(os.path.join(ROOT, "output", "step1_rows_derived.pkl"))
    base = base[base["正文字数"] > 5000]
    rows = []
    for i, d in enumerate(base["doi"], 1):
        rows.append(scan(d))
        if i % 200 == 0:
            print(i, flush=True)
    df = base[["doi", "年份", "题名", "主层", "有电池测试", "正极层"]].merge(pd.DataFrame(rows), on="doi")
    df.to_pickle(os.path.join(ROOT, "output", "step1_props.pkl"))
    out = []
    for name in PROPS:
        for label, sub in [("全部", df), ("主层", df[df["主层"]])]:
            n = len(sub)
            ok = (sub[name] == "✅").sum()
            anym = (sub[name] != "❌").sum()
            out.append((name, label, n, f"{ok} ({ok / n:.0%})", f"{anym} ({anym / n:.0%})"))
    summ = pd.DataFrame(out, columns=["物性", "范围", "篇数", "有本文数值 ✅", "含泛泛提及 ✅+🔶"])
    print(summ.to_string(index=False))
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
    per = df.map(lambda v: ILLEGAL_CHARACTERS_RE.sub(" ", v) if isinstance(v, str) else v)
    with pd.ExcelWriter(os.path.join(ROOT, "output", "第1步_物性报告率.xlsx"), engine="openpyxl") as xw:
        summ.to_excel(xw, sheet_name="汇总", index=False)
        per.to_excel(xw, sheet_name="逐篇", index=False)


if __name__ == "__main__":
    main()
