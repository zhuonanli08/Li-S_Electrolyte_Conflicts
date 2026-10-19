"""第 1 步 h：高倍率长循环（快充）条件判读（零成本正则）。

定义（用户 2026-10-13 提）：在 ≥3C 下跑长循环；倍率阶梯测试（rate capability）不算。
判读：同一句（或相邻 ±150 字符）里同时有 ①倍率 ≥3C（或 ≥5 A g⁻¹，按 1C = 1.675 A g⁻¹ 折算）②循环圈数 ≥100，
      且上下文不是倍率阶梯（rate capability / various rates / from 0.1 C to …）。只收本文自述（实验部分 / SI / 正文自述句）。
输出：output/step1_fastcycling.pkl（每篇：标记、最高倍率、最多圈数、原句）
"""
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step1c_checkup as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# C 倍率：数字 + C，前面不能是 °（温度）或负号，后面不能接字母（Ca、Cu、CE…）
P_C = r"(?<![°\d.\-−])(\d+(?:\.\d+)?)\s*C\b(?![a-zA-Z°])"
P_AG = r"(?<![\d.])(\d+(?:\.\d+)?)\s*A\s*g\s*-?\s*1"
P_CYC = r"(?<![\d.])(\d{1,2},\d{3}|\d{3,5})\s*(?:charge[\s/-]*discharge\s*)?cycles"
RATE_TEST = re.compile(r"rate (?:capabilit|performance|test)|various (?:current|rate|C-rate)|different (?:current|rate|C-rate)s|"
                       r"from 0\.\d+\s*C (?:to|up to)|0\.1\s*C\s*,\s*0\.2|stepwise|step-wise|increas\w+ (?:current|rate)s? (?:from|to)", re.I)
TEMP = re.compile(r"°|temperature|-\s?\d+\s*C\b", re.I)


RATE_TEST2 = re.compile(r"rate (?:capabilit|capacit|performance|test)", re.I)
# 倍率之后 60 字符内跟圈数（可跨 ". After/Over/For" 这种接续句），中间不能再出现别的倍率、表格分隔符
GAP = r"(?:[^.;|]|\.(?=\d)|\.\s+(?=(?:After|Over|For|During|Throughout)\b)){0,130}?"
CYC = r"\b(\d{1,2},\d{3}|\d{3,5})\s*(?:charge[\s/-]*discharge\s*)?cycles"
RATE_C = r"(\d+(?:\.\d+)?)\s*C\b(?![a-zA-Z°])"
RATE_AG = r"(\d+(?:\.\d+)?)\s*A\s*g\s*-?\s*1"


def bound_hits(text):
    """返回 [(倍率C, 圈数, start, end)]：倍率在前（"at 4 C … for 1000 cycles"）或圈数在前（"1000 cycles at 4 C"）"""
    out = []
    for rpat, conv in [(RATE_C, 1.0), (RATE_AG, 1 / 1.675)]:
        tail = re.compile(GAP + CYC)
        bwd = re.compile(CYC + r"\s*(?:at|under|with)\s*(?:a\s*)?(?:high\s*)?(?:(?:current\s*)?(?:rate|density)\s*(?:of\s*)?)?" + rpat)
        for m in re.finditer(rpat, text):  # 每个倍率位置各自往后找，避免"2C and 5C"里 5C 被吞掉
            t = tail.match(text, m.end())
            if not t:
                continue
            gap = text[m.end():t.start(1)]
            if re.search(r"\d\s*C\b|A\s*g\s*-?\s*1", gap):  # 中间又出现别的倍率 → 圈数不属于这个倍率
                continue
            after = text[t.end():t.end() + 25]
            am = re.match(r"\s*(?:\(|,)?\s*(?:at|under)\s*(?:a\s*)?(?:rate\s*of\s*)?(\d+(?:\.\d+)?)\s*C\b", after)
            if am and abs(float(am.group(1)) - float(m.group(1))) > 1e-9:  # "after 600 cycles at 2C"：圈数属于后面那个倍率
                continue
            if text[max(0, m.start() - 1):m.start()] == "/":  # "1/12 C"
                continue
            out.append((float(m.group(1)) * conv, int(t.group(1).replace(",", "")), m.start(), t.end()))
        for m in bwd.finditer(text):
            out.append((float(m.group(2)) * conv, int(m.group(1).replace(",", "")), m.start(), m.end()))
    return out


def scan(doi):
    key = re.sub(r"[^\w.-]+", "_", doi)
    raw = open(os.path.join(S.CACHE, f"{key}.main.txt"), encoding="utf-8").read()
    p = os.path.join(S.CACHE, f"{key}.si.txt")
    exp, rest = S.zones(raw)
    si = S.norm(open(p, encoding="utf-8").read()) if os.path.exists(p) else ""
    hits = []
    for zone, text in [("EXP", exp), ("SI", si), ("MAIN", rest)]:
        for rate, cyc, s, e in bound_hits(text):
            if not (3 <= rate <= 30 and 100 <= cyc <= 50000):
                continue
            before, w = text[max(0, s - 25):s], text[max(0, s - 150):e + 100]
            if re.search(r"Fig(?:ure)?s?\.?\s*$|Fig(?:ure)?s?\.?\s*S?$", before):  # "Figure 5C" 是图号
                continue
            if re.search(r"NMR|\b1H\b|\b19F\b", text[max(0, s - 30):s + 40]):  # "13C NMR"
                continue
            if re.search(r"[-−]\s*$|°", text[max(0, s - 3):s + 12]) or TEMP.search(before[-12:]):  # 丢了°的温度、负温度
                continue
            if re.search(r"\d+(?:\.\d+)?\s*C\b[\s,]*$", before[-20:]):  # "0.1C 1C 5C" 这种倍率罗列
                continue
            if RATE_TEST2.search(text[max(0, s - 40):e]):  # 只看倍率前 40 字到圈数这一段，摘要里同句另提 rate capability 不算
                continue
            # 带具体倍率和圈数的句子很少是转述别人的：不像参考文献、不带引文标记、不出现 reported/previous 就算本文
            near = text[max(0, s - 100):e + 120]
            if (S.REF_LIKE.search(near) or S.CITE_NEAR.search(near) or re.search(r"\breported\b|\bprevious|literature|have been|has been", near, re.I)
                    or re.search(r"Angew|Adv\.\s*(?:Mater|Energy|Funct|Sci)|Nat\.\s*(?:Commun|Energy)|J\.\s*Am\.|ACS\s+(?:Nano|Energy)|Energy Storage Mater", near)):
                continue  # SI 里的文献对比表会带期刊名
                continue
            hits.append((rate, cyc, f"[{zone}] …{w}…"))
    if not hits:
        return {"doi": doi, "高倍率长循环": False, "最高倍率C": None, "该倍率下最多圈数": None, "快充原句": ""}
    best = max(hits, key=lambda h: (h[0], h[1]))
    return {"doi": doi, "高倍率长循环": True, "最高倍率C": round(best[0], 2), "该倍率下最多圈数": best[1], "快充原句": best[2]}


def main():
    base = pd.read_pickle(os.path.join(ROOT, "output", "step1_rows_derived.pkl"))
    base = base[base["正文字数"] > 5000]
    out = pd.DataFrame([scan(d) for d in base["doi"]])
    out.to_pickle(os.path.join(ROOT, "output", "step1_fastcycling.pkl"))
    X = base.merge(out, on="doi")
    for lab, sub in [("全部", X), ("有电池测试", X[X["有电池测试"]]), ("主层", X[X["主层"]])]:
        f = sub["高倍率长循环"]
        print(f"{lab}: {f.sum()} / {len(sub)} ({f.mean():.0%})；其中 ≥500 圈 {(sub['该倍率下最多圈数'] >= 500).sum()}")
    m = X[X["主层"] & X["高倍率长循环"]]
    print("主层快充里：有贫液实验", int(m["贫液实验"].fillna(False).sum()), "有负极受限", int(m["负极受限(薄锂/N/P≤3/无负极)"].fillna(False).sum()),
          "有高载量", int(m["高载量实验"].fillna(False).sum()))
    print(X.groupby("时段")["高倍率长循环"].mean().round(3).to_dict())


if __name__ == "__main__":
    main()
