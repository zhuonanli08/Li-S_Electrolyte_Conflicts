"""补充下载的正文核对（2026-10-23）：已下载的新论文逐篇用正文复核用户标准。

用户标准：液态锂硫；一定要讲电解液溶剂化；必须有电池实验；电解液本身是研究对象；不要综述/纯计算/表征方法创新。
step7a 只看了题名/摘要（第 3、5 层只有题名，第 4 层摘要没写溶剂化），这里对全部已下载论文用正文再判一次：
  1) 代码计数：正文（去参考文献）里 solvat*/desolvat*/donor number 等词次数、恒流循环类词次数——客观信号；
  2) DeepSeek 读正文开头约 5000 字 + 溶剂化词附近最多 10 段原文，判 5 条 + 研究对象，给一句原文；
  3) 代码核对原句确实在正文里（✅/❌）。
结果缓存 output/补充下载_筛选/正文核对.json，并把列并回 补充下载_筛选表.csv（step7a 重跑时也会并入）。
判定是 AI 辅助，用户未复核。
运行：D:/anaconda/envs/papertrail/python.exe -X utf8 scripts/step7b_supplement_fulltext_check.py
"""
from __future__ import annotations

import asyncio
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "补充下载_筛选"
PT = Path("D:/Desktop/锂电催化/机器学习/skills/Open-Papertrail/Open-Papertrail")
LIB = PT / "corpus" / "library"
MF = LIB / "_staging" / "LiS_t2_solv_supp" / "manifest.json"
CACHE = OUT / "正文核对.json"
TABLE = OUT / "补充下载_筛选表.csv"

SOLV_RE = re.compile(r"\b(de)?solvat\w*|donor number|solvent[- ]separated ion pair|contact ion pair|"
                     r"coordination (structure|number|environment)|first (solvation )?shell", re.I)
CELL_RE = re.compile(r"galvanostatic|charge[-/ ]discharge|cycling (performance|stability)|capacity retention|"
                     r"rate (performance|capability)|coin cells?|pouch cells?", re.I)
REF_RE = re.compile(r"\n\s*(References|REFERENCES|Notes and references|Bibliography)\s*\n")


def lp(p: Path) -> str:
    s = str(p.resolve())
    return s if s.startswith("\\\\?\\") else "\\\\?\\" + s


def fulltext(pdf: Path) -> str:
    import fitz
    with fitz.open(lp(pdf)) as doc:
        text = "\n".join(page.get_text() for page in doc)
    m = REF_RE.search(text)
    if m and m.start() > len(text) * 0.4:
        text = text[: m.start()]
    return text


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def snippets(text: str, k: int = 10, width: int = 260) -> list[str]:
    out, last = [], -10**9
    for m in SOLV_RE.finditer(text):
        if m.start() - last < width:
            continue
        last = m.start()
        out.append(re.sub(r"\s+", " ", text[max(0, m.start() - width // 2): m.start() + width]))
        if len(out) >= k:
            break
    return out


SYSTEM = """You check full texts of papers collected for a meta-analysis of LIQUID-electrolyte lithium-sulfur batteries.
For the paper decide, from the text given (opening part + passages around solvation words):
- li_s_liquid: Li-S cells (S/Li2S/SPAN cathode) with a liquid electrolyte are the studied system ("yes"/"no")
- solvation: the paper DISCUSSES electrolyte solvation as part of its argument (Li+ solvation structure/sheath,
  desolvation, solvent-polysulfide interactions or polysulfide solubility set by the solvent, weakly/sparingly
  solvating or (localized) high-concentration electrolytes, donor number). A passing mention is "no".
- battery_experiment: real Li-S cell cycling / rate tests are reported ("yes"/"no")
- electrolyte_subject: the liquid electrolyte formulation itself is the research object (not a separator,
  host, catalyst, binder or anode coating) ("yes"/"no")
- not_review: it is an original research article, not a review/perspective ("yes"/"no")
- not_method: its main innovation is not a new characterization/measurement technique ("yes"/"no")
verdict: "正文符合" if all are yes, "正文不符合" if any is clearly no, else "存疑".
reason: one short Chinese sentence. quote: copy ONE verbatim sentence fragment (<=30 words) from the given text
that best shows how the paper treats solvation (or shows its absence/main topic)."""
FIELDS = ["li_s_liquid", "solvation", "battery_experiment", "electrolyte_subject", "not_review", "not_method"]
TOOL = {"name": "check_paper", "description": "Full-text check of one paper.",
        "input_schema": {"type": "object", "required": [*FIELDS, "verdict", "reason", "quote"], "properties": {
            **{k: {"type": "string", "enum": ["yes", "no", "unclear"]} for k in FIELDS},
            "verdict": {"type": "string", "enum": ["正文符合", "正文不符合", "存疑"]},
            "reason": {"type": "string"}, "quote": {"type": "string"}}}}


async def main_async() -> dict:
    sys.path.insert(0, str(PT))
    from discovery.llm import acomplete_with_tool, load_llm_config, stage_config
    cfg = stage_config(load_llm_config(str(PT / "config.yaml")), "screen")
    lib = json.loads((LIB / "library.json").read_text(encoding="utf-8"))["papers"]
    new = [d for d, r in json.loads(MF.read_text(encoding="utf-8"))["papers"].items() if r.get("pdf_status") == "ok"]
    done = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    for i, d in enumerate(new, 1):
        if d in done:
            continue
        row = lib.get(d) or next((r for k, r in lib.items() if k.lower() == d.lower()), None)
        if not row:
            print(f"[skip] {d} not in library")
            continue
        try:
            text = fulltext(LIB / "02_LiS_electrolyte" / row["pdf_file"])
        except Exception as e:
            print(f"[skip] {d} PDF unreadable: {e!r}")
            continue
        n_solv, n_cell = len(SOLV_RE.findall(text)), len(CELL_RE.findall(text))
        snip = snippets(text)
        opening = re.sub(r"\s+", " ", text[:5000])
        passages = "\n---\n".join(snip) if snip else "(none)"
        user = (f"Title: {row.get('title', '')}\n\nOPENING TEXT:\n{opening}\n\n"
                f"PASSAGES AROUND SOLVATION WORDS ({n_solv} matches in the body):\n{passages}")
        for attempt in range(3):
            try:
                out = await acomplete_with_tool(cfg, system=SYSTEM, user=user, tool_schema=TOOL,
                                                tool_name="check_paper", max_tokens=1024)
                break
            except Exception as e:
                print(f"[check] LLM error {type(e).__name__}; retry")
                await asyncio.sleep(10)
        else:
            continue
        q = out.get("quote", "")
        done[d] = {**{k: out.get(k, "") for k in [*FIELDS, "verdict", "reason", "quote"]},
                   "n_solvation_words": n_solv, "n_cell_words": n_cell,
                   "quote_check": "✅" if q and norm(q) in norm(text) else "❌ 正文中找不到"}
        CACHE.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[check] {i}/{len(new)} {done[d]['verdict']} solv={n_solv} {d}")
    return done


def merge_into_table(done: dict) -> None:
    rows = list(csv.DictReader(TABLE.open(encoding="utf-8-sig")))
    cols = list(rows[0].keys())
    add = ["正文核_判定", "正文核_溶剂化", "正文核_电池实验", "正文核_研究对象", "正文核_溶剂化词次",
           "正文核_理由", "正文核_原句", "正文核_原句核验", "已下载"]
    for c in add:
        if c not in cols:
            cols.insert(cols.index("下载后正文核") + 1 + add.index(c), c)
    for r in rows:
        j = done.get(r.get("doi", ""))
        r["已下载"] = "是" if j else r.get("已下载", "")
        if j:
            r.update({"正文核_判定": j["verdict"], "正文核_溶剂化": j["solvation"], "正文核_电池实验": j["battery_experiment"],
                      "正文核_研究对象": j["electrolyte_subject"], "正文核_溶剂化词次": j["n_solvation_words"],
                      "正文核_理由": j["reason"], "正文核_原句": j["quote"], "正文核_原句核验": j["quote_check"]})
    with TABLE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    done = asyncio.run(main_async())
    merge_into_table(done)
    from collections import Counter
    print("[result]", dict(Counter(j["verdict"] for j in done.values())),
          "| quote check:", dict(Counter(j["quote_check"] for j in done.values())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
