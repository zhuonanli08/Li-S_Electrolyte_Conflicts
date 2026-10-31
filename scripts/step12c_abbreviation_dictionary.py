"""领域缩写词典（2026-10-31）：用本机锂硫电解液文献全文（output/text_cache，正文＋SI）统计缩写的定义。

原文只写缩写、没写全称时，公共库（PubChem 等）按缩写查会返回错误化合物，所以改用本领域文献自己的定义：
在每篇全文里找“全称 (缩写)”和“缩写 (全称)”，取离缩写最近的全称，按篇计数。
缩写取组分核定.json 里的短写法（A 档）；候选全称 = 本组分全称正则 ＋ 其他 A 档组分全称正则 ＋ 下面的易混全称。
判定：定义该缩写的文献 ≥5 篇且 ≥90% 指本组分 → 通用；<90% → 有歧义（必须看本篇全称）；<5 篇 → 样本不足。
方案 §5.8；step12a build 读本词典，原文只有缩写且词典判“通用”时按通用含义记 ✅。
输出 output/组分结构表_F版30篇_2026-10-31/缩写词典.json。
运行：D:/anaconda/envs/rdkit/python.exe -X utf8 scripts/step12c_abbreviation_dictionary.py
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TC = ROOT / "output" / "text_cache"
OUT = ROOT / "output" / "组分结构表_F版30篇_2026-10-31"
CURATION = OUT / "组分核定.json"
MIN_PAPERS, MIN_SHARE = 5, 0.9

LIG = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "−": "-", "‐": "-", "–": "-", "‑": "-"}
# 本领域常见的写错或同缩写异物；10-31 统计见过：DME 写成 dimethyl ether / dimethoxymethane，DOL 写成 1,2-dioxolane，
# DEE 既指乙醚也指 1,2-二乙氧基乙烷，DIOX 既指 1,3-二氧戊环也指 1,4-二氧六环
CONFUSABLE = {
    "二甲醚（dimethyl ether）": r"(?<!glycol )(?<!glycol-)(?<!glycol\) )\bdimethyl ether",
    "二甲氧基甲烷": r"dimethoxy-?\s?methane",
    "1,1-二甲氧基乙烷": r"1,\s?1-\s?dimethoxy-?\s?ethane",
    "1,2-二氧戊环": r"1,\s?2-\s?dioxolane",
    "1,4-二氧六环": r"dioxane",
    "二乙氧基乙烷": r"diethoxy-?\s?ethane|ethylene glycol diethyl ether",
}
SHORT = re.compile(r"^[A-Za-z][A-Za-z0-9\[\]\-]{1,9}$")


def norm(t: str) -> str:
    for a, b in LIG.items():
        t = t.replace(a, b)
    t = re.sub(r"(?<=[a-z])-\s*\n\s*(?=[a-z])", "", t)
    return re.sub(r"\s+", " ", t)


def closest(window: str, cands: dict, before: bool):
    """全称须紧贴缩写：before=True 时全称结尾到“(缩写”之间 ≤25 字且不含“(”（排除“lithium nitrate (LiNO3) in DOL/(DME”）；
    否则全称须在“缩写 (”的括号里、开头 25 字内（排除“DME (1:1, v/v) with lithium nitrate”）。取离缩写最近的一个。"""
    best, key = None, None
    for k, pat in cands.items():
        for m in pat.finditer(window):
            if before:
                gap = window[m.end():]
                ok, score = len(gap) <= 25 and "(" not in gap, m.end()
            else:
                head = window[:m.start()]
                ok, score = m.start() <= 25 and "(" not in head and ")" not in head, -m.start()
            if ok and (key is None or score > key):
                best, key = k, score
    return best


def main() -> None:
    cur = json.loads(CURATION.read_text(encoding="utf-8"))
    comps = {c["id"]: c for c in cur["组分"] if c["档"] == "A"}
    targets = {}
    for a in cur["别名"]:
        w = a["写法"]
        if len(a["组分"]) == 1 and a["组分"][0] in comps and SHORT.match(w) and w not in targets:
            targets[w] = a["组分"][0]
    names = {cid: re.compile(c["全称正则"], re.I) for cid, c in comps.items()}
    extra = {k: re.compile(v, re.I) for k, v in CONFUSABLE.items()}

    hits = {w: defaultdict(set) for w in targets}
    examples = defaultdict(list)
    papers = sorted({p.name.rsplit(".", 2)[0] for p in TC.glob("*.txt")})
    pats = {w: (re.compile(r"\(\s?(?:Li\s?\[?)?" + re.escape(w) + r"\]?\s?[,;)]"),
                re.compile(r"(?<![A-Za-z])" + re.escape(w) + r"\s?\(")) for w in targets}
    for paper in papers:
        text = " ".join(norm(f.read_text(encoding="utf-8", errors="ignore")) for f in sorted(TC.glob(paper + ".*.txt")))
        for w, cid in targets.items():
            cands = {cid: names[cid], **{k: p for k, p in names.items() if k != cid}, **extra}
            before, after = pats[w]
            found = [(text[max(0, m.start() - 90):m.start()], True) for m in before.finditer(text)]
            found += [(text[m.end():m.end() + 90], False) for m in after.finditer(text)]
            for win, is_before in found:
                k = closest(win, cands, is_before)
                if k:
                    hits[w][k].add(paper)
                    if len(examples[(w, k)]) < 5 and all(e["文献"] != paper for e in examples[(w, k)]):
                        examples[(w, k)].append({"文献": paper, "原句": win.strip()})

    out = {}
    for w, cid in targets.items():
        d = hits[w]
        total = set().union(*d.values()) if d else set()
        own = len(d.get(cid, ()))
        share = own / len(total) if total else 0.0
        verdict = ("样本不足" if own < MIN_PAPERS else "通用" if share >= MIN_SHARE else "有歧义")
        out[w] = {"组分": cid, "定义篇数": len(total), "定义为本组分": own, "占比": round(share, 3), "判定": verdict,
                  "其他定义": {(comps[k]["名称"] if k in comps else k): len(v) for k, v in
                               sorted(d.items(), key=lambda x: -len(x[1])) if k != cid},
                  "例句": {(comps[k]["名称"] if k in comps else k): examples[(w, k)] for k in d}}
    doc = {"说明": f"本机文献全文 {len(papers)} 篇（output/text_cache，正文＋SI）中缩写的定义统计，按篇计数。"
                 f"判定：定义篇数中指本组分 ≥{MIN_PAPERS} 篇且占比 ≥{int(MIN_SHARE * 100)}% 为通用；"
                 "占比不足为有歧义（必须看本篇全称）；不足 5 篇为样本不足。少数“其他定义”多为作者把全称写错"
                 "（如标准 DOL/DME 电解液里写 dimethyl ether），例句可查。AI 辅助，用户尚未逐项确认。",
           "文献篇数": len(papers), "缩写": out}
    (OUT / "缩写词典.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    for w, e in sorted(out.items(), key=lambda x: -x[1]["定义篇数"]):
        print(f"{w:<10} → {e['组分']:<10} {e['判定']}：{e['定义为本组分']}/{e['定义篇数']} 篇"
              + (f"；其他 {e['其他定义']}" if e["其他定义"] else ""))


if __name__ == "__main__":
    main()
