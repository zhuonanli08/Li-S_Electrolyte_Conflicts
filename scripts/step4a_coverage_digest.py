"""方案 4 §3 B1：全库 669 篇资格筛选的代码定位 + 判定用摘录

对每篇正文 + SI：取题名、摘要、配方句（浓度 + 盐）、对照句（baseline / reference / control electrolyte 等）、
诊断句（剩余锂、滴定气相色谱、定量 NMR、补液、电解液耗尽、HPLC 等）、介体 / 添加剂线索；给出代码建议层别。

输出：
  output/第二阶段_资格筛选/代码定位.csv          每篇一行（计数、建议层别、诊断关键词）
  output/第二阶段_资格筛选/摘录_批NN.txt          每批 30 篇，供逐篇判定
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 -I step4a_coverage_digest.py
"""
import json
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step1c_checkup as S  # noqa: E402

ROOT = S.ROOT
OUT = os.path.join(ROOT, "output", "第二阶段_资格筛选")
os.makedirs(OUT, exist_ok=True)
BATCH = 30

SALT = (r"(?:LiTFSI|LiFSI|LiNO\s?3|LiPF6|LiOTf|LiTf\b|LiCF3SO3|LiClO4|LiBr|LiI\b|LiDFOB|LiBOB|LiBETI|LiSCN|LiTDI|LiBF4|LiFTFSI|LiPDI"
        r"|lithium (?:bis\(|bis-|trifluorometh|perchlorate|nitrate|triflate|bromide|iodide|difluoro|hexafluoro))")
FORMULA = re.compile(r"\b\d+(?:\.\d+)?\s*(?:M|mol\s*(?:L|dm)\s*[-−–]?\s*1|mol/L|mol\s*kg\s*[-−–]?\s*1|m)\b[^.;]{0,60}?" + SALT)
COMP = re.compile(r"\b(?:baseline|reference|control|conventional|blank|routine|commercial|pristine|standard|traditional|typical|benchmark|normal|regular|"
                  r"ether[\s-]*based|DOL/DME|DME/DOL)\s+(?:ether[\s-]*based\s+|liquid\s+)?electrolytes?\b"
                  r"|compared (?:with|to) (?:the |that (?:of|in) the )?[^.]{0,60}?electrolyte"
                  r"|electrolytes? (?:without|w/o)\b|\bwith(?:out)? (?:the )?(?:addition of|additive)\b", re.I)
DIAG = [
    ("剩余锂", r"(?:remaining|residual|reversible|active|inactive|dead)\s+(?:metallic\s+)?(?:Li|lithium)(?:\s+metal)?\s+(?:inventory|capacity|amount|content|quantif)"
              r"|lithium inventory|Li inventory|titration gas chromatography|\bTGC\b|stripp\w+ (?:capacity )?of the (?:cycled|harvested|retrieved) (?:Li|lithium)"),
    ("电解液余量/组成", r"quantitative (?:1H |19F |7Li )?NMR|\bq-?NMR\b|\bQNMR\b|electrolyte (?:depletion|dry[\s-]*(?:out|up)|exhaustion)|(?:remaining|residual) electrolyte"
                     r"|electrolyte (?:consumption|loss) (?:was |is )?(?:quantif|measur|determin)|(?:LiNO3|nitrate|salt|solvent) (?:consumption|depletion) (?:was |is )?(?:quantif|measur|determin)"),
    ("补液恢复", r"re-?inject\w*|replenish\w* (?:the |fresh |new )?electrolyte|refill\w*|(?:fresh|new) electrolyte (?:was |were )?(?:re)?(?:added|injected|introduced)|electrolyte (?:re-?)?addition"),
    ("硫库存/物种定量", r"\bHPLC\b|inactive sulfur|dead sulfur|sulfur (?:inventory|retention) (?:quantif|measur)|(?:quantif\w*|amount of) (?:dissolved |soluble )?polysulfides? in (?:the )?(?:cycled|harvested) electrolyte"
                      r"|sulfur (?:loss|content) (?:on|in) the (?:cycled )?(?:Li|lithium) (?:anode|metal)"),
]
DIAG = [(k, re.compile(p, re.I)) for k, p in DIAG]
MED = re.compile(r"redox[\s-]*mediat|\bmediat(?:or|ors)\b|homogeneous(?:ly)?[\s-]*catal|soluble catalysts?|molecular catalysts?|redox[\s-]*active (?:additive|molecule|species)"
                 r"|catalytic (?:electrolyte|additive)|electrocatalytic additive|comediator", re.I)
CORE = re.compile(r"\bsolvents?\b|co[\s-]*solvents?|\bdiluents?\b|solvation|solvating|concentrat\w+ electrolyte|salt concentration|\banions?\b|lithium salts?|dual[\s-]*salt"
                  r"|ionic liquid|\bLHCEs?\b|\bHCEs?\b|\bethers?\b|sulfolane|fluorinated", re.I)
ADD = re.compile(r"\badditives?\b", re.I)
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


def sentences(t):
    return [s.strip() for s in SENT.split(S.norm(t)) if 25 <= len(s.strip()) <= 600]


def body(raw):
    cut = None
    for m in S.HEAD_REF.finditer(raw):
        if m.start() > 0.4 * len(raw):
            cut = m.start()
    return raw[:cut] if cut else raw


def clip(s, n):
    return s if len(s) <= n else s[:n] + "…"


def main():
    rows = pd.read_pickle(os.path.join(ROOT, "output", "step1_rows_derived.pkl"))
    ab = json.load(open(os.path.join(ROOT, "output", "abstracts.json"), encoding="utf-8"))
    pool = pd.read_csv(os.path.join(ROOT, "output", "第一阶段_初筛池.csv"), encoding="utf-8-sig")
    pid = dict(zip(pool["doi"].str.lower(), pool["池编号"]))
    jdir = os.path.join(ROOT, "output", "第一阶段_证据表", "json")
    deep = {json.load(open(os.path.join(jdir, f), encoding="utf-8"))["paper"]["doi"].lower() for f in os.listdir(jdir) if f.endswith(".json")}
    hold = {"S34", "S35", "S38", "S52", "S55", "S56"}
    rows = rows.sort_values(["年份", "doi"]).reset_index(drop=True)
    recs, dig = [], []
    for i, r in rows.iterrows():
        code = f"P{i + 1:03d}"
        key = re.sub(r"[^\w.-]+", "_", r["doi"])
        fm, fs = os.path.join(S.CACHE, f"{key}.main.txt"), os.path.join(S.CACHE, f"{key}.si.txt")
        raw = open(fm, encoding="utf-8").read() if os.path.exists(fm) else ""
        si = open(fs, encoding="utf-8").read() if os.path.exists(fs) else ""
        a = S.norm(ab.get(r["doi"].lower(), {}).get("abstract", "") or (S.pdf_abstract(raw) if raw else ""))
        sm = sentences(body(raw)) if raw else []
        ss = sentences(si) if si else []
        form = [s for s in sm if FORMULA.search(s)] + [("［SI］" + s) for s in ss if FORMULA.search(s)]
        comp = [s for s in sm if COMP.search(s)]
        diag = []
        for k, p in DIAG:
            hit = [s for s in sm + ss if p.search(s)]
            if hit:
                diag.append((k, hit))
        ta = f"{r['题名']} {a}"
        med, core, add = bool(MED.search(ta)), bool(CORE.search(ta)), bool(ADD.search(ta))
        sug = "；".join(x for x, f in (("介体/催化", med), ("核心", core), ("功能添加剂", add and not med)) if f) or "未定"
        d = r["doi"].lower()
        tag = "深读" if d in deep else ""
        if pid.get(d) in hold:
            tag = "留出（仅判资格）"
        recs.append({"编号": code, "doi": r["doi"], "年份": r["年份"], "期刊": r["期刊"], "题名": r["题名"], "初筛池编号": pid.get(d, ""), "已有身份": tag,
                     "有电池测试": r["有电池测试"], "正极层": r["正极层"], "负极": r["负极"], "凝胶/固态嫌疑": r["凝胶/固态嫌疑"], "主层": r["主层"],
                     "正文字数": len(raw), "有SI": bool(si), "配方句数": len(form), "对照句数": len(comp),
                     "诊断关键词": "、".join(k for k, _ in diag), "代码建议层别": sug, "题名摘要标签": r["电解液类别(题名+摘要)"]})
        head = (f"#### {code} | {r['doi']} | {r['年份']} {r['期刊']} | 正极 {r['正极层']}·负极 {r['负极']}·电池测试 {'有' if r['有电池测试'] else '无'}"
                f"{'·凝胶嫌疑' if r['凝胶/固态嫌疑'] else ''}{('·' + tag) if tag else ''} | 建议 {sug} | 配方句 {len(form)}·对照句 {len(comp)}")
        out = [head, f"题名：{r['题名']}", f"摘要：{clip(a, 650)}"]
        seen = set()
        for s in form[:3]:
            k = s[:80]
            if k not in seen:
                seen.add(k)
                out.append(f"配方：{clip(s, 230)}")
        for s in comp[:2]:
            out.append(f"对照：{clip(s, 200)}")
        for k, hit in diag:
            out.append(f"诊断[{k}]：{clip(hit[0], 230)}")
        if not raw:
            out.append("（无正文文本）")
        dig.append("\n".join(out))
    df = pd.DataFrame(recs)
    df.to_csv(os.path.join(OUT, "代码定位.csv"), index=False, encoding="utf-8-sig")
    for b in range(0, len(dig), BATCH):
        open(os.path.join(OUT, f"摘录_批{b // BATCH + 1:02d}.txt"), "w", encoding="utf-8").write("\n\n".join(dig[b:b + BATCH]))
    print(len(df), "篇；批数", (len(dig) + BATCH - 1) // BATCH, "；平均摘录", round(sum(map(len, dig)) / len(dig)), "字符")
    print("建议层别：", df["代码建议层别"].value_counts().to_dict())
    print("有诊断关键词：", (df["诊断关键词"] != "").sum(), df["诊断关键词"].str.split("、").explode().value_counts().to_dict())
    print("配方句=0：", (df["配方句数"] == 0).sum(), "；无电池测试：", (~df["有电池测试"]).sum(), "；无正文：", (df["正文字数"] == 0).sum())


if __name__ == "__main__":
    main()
