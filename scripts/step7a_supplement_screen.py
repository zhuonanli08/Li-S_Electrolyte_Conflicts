"""补充下载候选：检索 + 去重 + DeepSeek 初筛 + 排序（用户 2026-10-22 要求再补 100 篇）。

用户标准：液态锂硫电池；一定要讲电解液溶剂化；必须有电池实验；不要综述、不要纯计算、
不要以表征方法创新为主的电解液研究。用户定：DeepSeek 初筛、Claude 抽查；顺序 = top_journal_missing_dois.json
里符合的在前，其余按被引数从高到低。

候选 = output/top_journal_missing_dois.json（19 个 DOI）+ OpenAlex 补检索（锂硫含 sulphur 拼写 × 溶剂化类词 × electrolyte，
2016 起，不设数量上限），去掉 Open-Papertrail 库里已有的（DOI、Angewandte anie/ange 双 DOI、规范化标题）。
没有摘要的只按题名判，标"仅题名"，排在有摘要确认的之后作后备；下载后再用正文复核。

输出：
  output/补充下载_筛选/候选池.json            OpenAlex 记录缓存（可续跑）
  output/补充下载_筛选/deepseek_判定.json      逐篇判定缓存（可续跑）
  output/补充下载_筛选/补充下载_筛选表.csv     一行一篇：判定、各条标准、理由、摘要原句、原句核验、下载顺序
  Open-Papertrail corpus/runs/dois_t2_solvation_supp.txt   下载顺序清单（只含进入下载的）
运行（papertrail 环境，需 OPENALEX_API_KEY 和 DeepSeek key）：
  D:/anaconda/envs/papertrail/python.exe -X utf8 scripts/step7a_supplement_screen.py
"""
from __future__ import annotations

import asyncio
import csv
import html
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "补充下载_筛选"
PT = Path("D:/Desktop/锂电催化/机器学习/skills/Open-Papertrail/Open-Papertrail")
LIB = PT / "corpus" / "library" / "library.json"
FILE_LIST = ROOT / "output" / "top_journal_missing_dois.json"
DL_LIST = PT / "corpus" / "runs" / "dois_t2_solvation_supp.txt"
POOL = OUT / "候选池.json"
JUDGE = OUT / "deepseek_判定.json"
TABLE = OUT / "补充下载_筛选表.csv"

KEY = os.environ.get("OPENALEX_API_KEY", "")
LIS = ('("lithium-sulfur" OR "lithium sulfur" OR "lithium-sulphur" OR "lithium sulphur" OR "Li-S" OR "Li–S")')
SOLV = ('(solvation OR solvated OR "solvation structure" OR "solvent" OR "co-solvent" OR cosolvent OR '
        '"diluent" OR "localized high-concentration" OR "high-concentration electrolyte" OR "weakly solvating" OR '
        '"sparingly solvating" OR "donor number" OR "polysulfide solubility")')
FILTER = ",".join([f"title_and_abstract.search:{LIS} AND {SOLV} AND electrolyte",
                   "from_publication_date:2016-01-01", "type:article|review"])
SELECT = "doi,publication_year,title,type,primary_location,abstract_inverted_index,cited_by_count"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", html.unescape(str(s or ""))).lower()
    return re.sub(r"[^a-z0-9]", "", s)


def twin(doi: str) -> str:
    for a, b in (("10.1002/anie.", "10.1002/ange."), ("10.1002/ange.", "10.1002/anie.")):
        if doi.startswith(a):
            return b + doi[len(a):]
    return ""


def inv(ii) -> str:
    if not ii:
        return ""
    words = [""] * (max(p for ps in ii.values() for p in ps) + 1)
    for w, ps in ii.items():
        for p in ps:
            words[p] = w
    return " ".join(words)


def rec(w: dict) -> dict:
    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    return {"doi": (w.get("doi") or "").replace("https://doi.org/", "").lower(), "year": w.get("publication_year"),
            "type": w.get("type"), "venue": src, "title": w.get("title") or "", "cites": w.get("cited_by_count", 0),
            "abstract": inv(w.get("abstract_inverted_index"))}


# ------------------------------------------------------------------ 1. candidates
def build_pool() -> list[dict]:
    if POOL.exists():
        return json.loads(POOL.read_text(encoding="utf-8"))
    rows, cursor = {}, "*"
    with httpx.Client(timeout=60, trust_env=False) as c:
        def get(params):
            for attempt in range(5):
                r = c.get("https://api.openalex.org/works", params={**params, "api_key": KEY, "select": SELECT})
                if r.status_code == 200:
                    return r.json()
                time.sleep(5 * (attempt + 1))
            r.raise_for_status()
        while cursor:
            j = get({"filter": FILTER, "per-page": 200, "cursor": cursor})
            for w in j["results"]:
                x = rec(w)
                if x["doi"]:
                    x["source"] = "补检索"
                    rows[x["doi"]] = x
            cursor = j["meta"].get("next_cursor")
            time.sleep(0.2)
        file_dois = [d.lower() for d in json.loads(FILE_LIST.read_text(encoding="utf-8"))]
        j = get({"filter": "doi:" + "|".join(file_dois), "per-page": 50})
        for w in j["results"]:
            x = rec(w)
            x["source"] = "顶刊清单"
            rows[x["doi"]] = {**rows.get(x["doi"], {}), **x}
    pool = list(rows.values())
    OUT.mkdir(parents=True, exist_ok=True)
    POOL.write_text(json.dumps(pool, ensure_ascii=False, indent=1), encoding="utf-8")
    return pool


def fill_abstracts_s2(pool: list[dict]) -> None:
    """OpenAlex has no abstract for many Elsevier/Nature papers; Semantic Scholar's free batch API fills ~1/4."""
    miss = [x for x in pool if not x["abstract"] and not x.get("s2_checked")]
    if not miss:
        return
    with httpx.Client(timeout=60, trust_env=False) as c:
        for i in range(0, len(miss), 400):
            chunk = miss[i:i + 400]
            for attempt in range(5):
                try:
                    r = c.post("https://api.semanticscholar.org/graph/v1/paper/batch", params={"fields": "abstract"},
                               json={"ids": ["DOI:" + x["doi"] for x in chunk]})
                except httpx.HTTPError as e:            # SSL EOF / reset now and then
                    print(f"[pool] Semantic Scholar {type(e).__name__}; retry {attempt + 1}")
                    time.sleep(10 * (attempt + 1))
                    continue
                if r.status_code == 200:
                    break
                time.sleep(10 * (attempt + 1))
            else:
                print("[pool] Semantic Scholar unavailable for this chunk; left unchecked (re-run to retry)")
                continue
            for x, s in zip(chunk, r.json()):
                x["s2_checked"] = True
                if s and s.get("abstract"):
                    x["abstract"] = s["abstract"]
                    x["abstract_src"] = "Semantic Scholar"
    print(f"[pool] Semantic Scholar filled {sum(x.get('abstract_src') == 'Semantic Scholar' for x in pool)} abstracts")
    POOL.write_text(json.dumps(pool, ensure_ascii=False, indent=1), encoding="utf-8")


def dedup(pool: list[dict]) -> tuple[list[dict], dict]:
    lib = json.loads(LIB.read_text(encoding="utf-8"))["papers"]
    dois = {k.lower() for k in lib}
    titles = {norm(r.get("title")) for r in lib.values() if len(norm(r.get("title"))) >= 25}
    keep, why, seen_t = [], {}, set()
    for x in sorted(pool, key=lambda r: (r["source"] != "顶刊清单", -r["cites"])):
        d, t = x["doi"], norm(x["title"])
        reason = ("已在库（DOI）" if d in dois else "已在库（Angewandte 双 DOI）" if twin(d) in dois
                  else "已在库（同标题）" if len(t) >= 25 and t in titles
                  else "候选内重复（同标题）" if len(t) >= 25 and t in seen_t else "")
        if reason:
            why[d] = reason
            continue
        seen_t.add(t)
        keep.append(x)
    return keep, why


# ------------------------------------------------------------------ 2. DeepSeek screening
SYSTEM = """You screen papers for a meta-analysis of LIQUID-electrolyte lithium-sulfur (Li-S) batteries.
A paper QUALIFIES only if ALL of these hold:
1. li_s_liquid: it is about Li-S batteries (sulfur, Li2S or SPAN cathode; Li-metal or Li-ion anode) with a LIQUID
   electrolyte as studied system. Not Na-S/K-S/Mg-S/Li-Se/Li-O2/Li-ion intercalation cells; not solid or gel-polymer
   electrolytes as the main system.
2. solvation: the paper explicitly discusses ELECTROLYTE SOLVATION as part of its argument - Li+ solvation
   structure/sheath, solvent-salt-polysulfide interactions, polysulfide solubility set by the solvent, weakly or
   sparingly solvating electrolytes, (localized) high-concentration electrolytes, diluents/co-solvents chosen for
   solvation, solvent donor number. Merely naming the solvents of a standard electrolyte is NOT enough.
3. battery_experiment: it reports Li-S cell experiments (galvanostatic cycling / rate tests of real cells).
   Pure DFT/MD/ML/theory/modeling papers without cells fail this.
4. not_review: not a review, perspective, comment, tutorial or roadmap.
5. not_method: the main innovation is NOT a new characterization / measurement / analytical technique
   (e.g. a new operando NMR/X-ray/optical method or protocol applied to electrolytes). Using standard
   characterization to support an electrolyte design is fine.
Judge only from the given text. For each criterion answer "yes", "no" or "unclear".
verdict: "符合" if all five are "yes"; "不符合" if any is "no"; otherwise "不确定".
reason: one short sentence in Chinese. evidence: copy ONE short verbatim phrase (<=25 words) from the abstract
that best supports the solvation or experiment judgement; empty string if judged from the title only."""

CRIT = ["li_s_liquid", "solvation", "battery_experiment", "not_review", "not_method"]
TOOL = {
    "name": "screen_papers",
    "description": "Screening decision for each paper.",
    "input_schema": {"type": "object", "required": ["papers"], "properties": {"papers": {"type": "array", "items": {
        "type": "object", "required": ["id", *CRIT, "verdict", "reason", "evidence"],
        "properties": {"id": {"type": "integer"},
                       **{k: {"type": "string", "enum": ["yes", "no", "unclear"]} for k in CRIT},
                       "verdict": {"type": "string", "enum": ["符合", "不符合", "不确定"]},
                       "reason": {"type": "string"}, "evidence": {"type": "string"}}}}}},
}


async def screen(cands: list[dict]) -> dict:
    sys.path.insert(0, str(PT))
    from discovery.llm import acomplete_with_tool, load_llm_config, stage_config
    cfg = stage_config(load_llm_config(str(PT / "config.yaml")), "screen")
    done = json.loads(JUDGE.read_text(encoding="utf-8")) if JUDGE.exists() else {}
    basis = lambda x: "摘要" if x["abstract"] else "仅题名"   # noqa: E731
    # re-screen papers judged from the title before an abstract became available
    todo = [x for x in cands if x["doi"] not in done or done[x["doi"]].get("basis") != basis(x)]
    if os.environ.get("T2_LIMIT"):            # smoke test: screen only the first N
        todo = todo[: int(os.environ["T2_LIMIT"])]
    print(f"[screen] {len(done)} cached, {len(todo)} to screen")
    for i in range(0, len(todo), 10):
        chunk = todo[i:i + 10]
        listing = "\n\n".join(
            f"{n}. [{x['year']}, {x['venue']}] {x['title']}\n   "
            + (f"Abstract: {x['abstract'][:2200]}" if x["abstract"] else "Abstract: (not available - judge from title only)")
            for n, x in enumerate(chunk, 1))
        for attempt in range(3):
            try:
                out = await acomplete_with_tool(cfg, system=SYSTEM, user=f"Screen these {len(chunk)} papers:\n\n{listing}",
                                                tool_schema=TOOL, tool_name="screen_papers", max_tokens=4096)
                break
            except Exception as e:  # DeepSeek drops connections now and then
                print(f"[screen] LLM error {type(e).__name__}: {str(e)[:120]}; retry")
                await asyncio.sleep(10)
        else:
            continue
        by_id = {int(p.get("id", 0)): p for p in (out.get("papers") or []) if isinstance(p, dict)}
        for n, x in enumerate(chunk, 1):
            if n in by_id:
                done[x["doi"]] = {**{k: by_id[n].get(k, "") for k in [*CRIT, "verdict", "reason", "evidence"]},
                                  "basis": basis(x)}
        JUDGE.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[screen] {min(i + 10, len(todo))}/{len(todo)}")
    return done


# ------------------------------------------------------------------ 2b. extended pool (user, 10-22)
# The strict pool gives only ~50 papers. User chose: also take Li-S papers whose TITLE is about the electrolyte
# but whose abstract does not mention solvation (tier 4, after tiers 1-3); solvation is checked on the full text
# after download and papers that never discuss it are flagged in the table for the user to decide.
POOL_EXT = OUT / "候选池_扩展.json"
EXT_TITLE = ('(electrolyte OR electrolytes OR solvent OR solvents OR cosolvent OR "co-solvent" OR diluent OR '
             '"ionic liquid" OR solvation OR solvating OR concentrated)')


def build_pool_ext(pool: list[dict]) -> list[dict]:
    if not os.environ.get("T2_EXT"):
        return pool
    if POOL_EXT.exists():
        ext = json.loads(POOL_EXT.read_text(encoding="utf-8"))
    else:
        flt = ",".join([f"title_and_abstract.search:{LIS}", f"title.search:{EXT_TITLE}",
                        "from_publication_date:2016-01-01", "type:article"])
        ext, cursor = [], "*"
        with httpx.Client(timeout=60, trust_env=False) as c:
            while cursor:
                for attempt in range(5):
                    try:
                        r = c.get("https://api.openalex.org/works", params={
                            "filter": flt, "per-page": 200, "cursor": cursor, "api_key": KEY, "select": SELECT})
                        if r.status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(5 * (attempt + 1))
                j = r.json()
                ext += [{**rec(w), "source": "扩展检索"} for w in j["results"] if w.get("doi")]
                cursor = j["meta"].get("next_cursor")
                time.sleep(0.2)
        POOL_EXT.write_text(json.dumps(ext, ensure_ascii=False, indent=1), encoding="utf-8")
    have = {x["doi"] for x in pool}
    added = [x for x in ext if x["doi"] not in have]
    print(f"[pool] extended search: {len(ext)} records, {len(added)} new")
    return pool + added


# Claude's title review of the title-only tiers (3 and 5), 2026-10-23: clear misses that would otherwise use up
# download slots. The DeepSeek judgements are left as they are; the table shows this column instead.
MANUAL_DROP = {
    "10.1038/nenergy.2016.114": "综述（电解液与界面设计原则）",
    "10.1016/j.jechem.2020.11.017": "综述（离子液体用于锂金属电池）",
    "10.12028/j.issn.2095-4239.2019.0182": "综述（锂硫软包电解液研究概述）",
    "10.12028/j.issn.2095-4239.2017.0032": "综述（高比能锂硫功能电解液）",
    "10.1016/j.electacta.2019.135108": "聚合物/凝胶电解质，非液态",
    "10.1007/s10853-016-0671-4": "凝胶电解质，非液态",
    "10.1016/j.jechem.2026.08.061": "PVDF 基聚合物电解质，非液态",
    "10.1016/j.mtchem.2026.103421": "原位聚合交联聚合物电解质，非液态",
    "10.1016/j.apsusc.2021.149034": "液/固 Li2S-P2S5 混合电解质，非纯液态",
    "10.1016/j.nanoen.2021.106708": "MOF 材料为主、锂金属沉积，非电解液研究",
    "10.1016/j.nanoen.2020.104725": "氮化硼纳米片整平剂、锂金属负极，非锂硫",
    "10.1016/j.ensm.2021.08.008": "碳点添加剂、锂金属负极，非锂硫",
    "10.1016/j.cej.2020.127123": "碳化氮添加剂、锂金属电池，非锂硫",
    "10.1016/j.jelechem.2022.116126": "VC 添加剂衍生 SEI 机理，未指向锂硫溶剂化",
    "10.1016/j.ensm.2018.11.001": "硅负极添加剂为主（锂化 Si-S 次要）",
    "10.1016/j.jpowsour.2022.232567": "高压正极 + SPAN 负极的锂离子电池，非锂硫",
    "10.1016/j.cej.2021.131586": "液流电解液中多硫化物动力学，非常规电池",
}

SUBJECT_JSON = OUT / "deepseek_研究对象.json"
SUBJECT_SYSTEM = """For each lithium-sulfur battery paper decide whether the LIQUID ELECTROLYTE ITSELF is the main
research object: the paper designs or studies an electrolyte formulation (solvents, co-solvents, diluents, salts,
salt concentration, ionic liquids, additives dissolved in the electrolyte, solvation structure of the electrolyte).
Answer "no" when the main innovation is a separator, interlayer, cathode host, catalyst, binder, current collector,
sulfur cathode material or anode coating - even if the paper discusses Li+ desolvation or uses a special electrolyte.
electrolyte_subject: "yes", "no" or "unclear"; reason: one short sentence in Chinese."""
SUBJECT_TOOL = {
    "name": "subject_papers", "description": "Is the electrolyte the research object?",
    "input_schema": {"type": "object", "required": ["papers"], "properties": {"papers": {"type": "array", "items": {
        "type": "object", "required": ["id", "electrolyte_subject", "reason"],
        "properties": {"id": {"type": "integer"},
                       "electrolyte_subject": {"type": "string", "enum": ["yes", "no", "unclear"]},
                       "reason": {"type": "string"}}}}}},
}


async def subject_check(cands: list[dict]) -> dict:
    sys.path.insert(0, str(PT))
    from discovery.llm import acomplete_with_tool, load_llm_config, stage_config
    cfg = stage_config(load_llm_config(str(PT / "config.yaml")), "screen")
    done = json.loads(SUBJECT_JSON.read_text(encoding="utf-8")) if SUBJECT_JSON.exists() else {}
    todo = [x for x in cands if x["doi"] not in done]
    print(f"[subject] {len(done)} cached, {len(todo)} to check")
    for i in range(0, len(todo), 10):
        chunk = todo[i:i + 10]
        listing = "\n\n".join(f"{n}. {x['title']}\n   " + (f"Abstract: {x['abstract'][:1800]}" if x["abstract"]
                              else "Abstract: (not available)") for n, x in enumerate(chunk, 1))
        for attempt in range(3):
            try:
                out = await acomplete_with_tool(cfg, system=SUBJECT_SYSTEM, user=f"Judge these {len(chunk)} papers:\n\n{listing}",
                                                tool_schema=SUBJECT_TOOL, tool_name="subject_papers", max_tokens=2048)
                break
            except Exception as e:
                print(f"[subject] LLM error {type(e).__name__}; retry")
                await asyncio.sleep(10)
        else:
            continue
        by_id = {int(p.get("id", 0)): p for p in (out.get("papers") or []) if isinstance(p, dict)}
        for n, x in enumerate(chunk, 1):
            if n in by_id:
                done[x["doi"]] = {"electrolyte_subject": by_id[n].get("electrolyte_subject", ""),
                                  "subject_reason": by_id[n].get("reason", "")}
        SUBJECT_JSON.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
    return done


# ------------------------------------------------------------------ 3. table + order
def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    pool = build_pool()
    fill_abstracts_s2(pool)
    pool = build_pool_ext(pool)
    cands, dropped = dedup(pool)
    print(f"[pool] {len(pool)} records; {len(dropped)} already in library/duplicate; {len(cands)} to screen")
    judged = asyncio.run(screen(cands))

    def base_tier(x, j):
        """Tier before the research-object check (1-3 = solvation shown; 4 = electrolyte paper, solvation not shown)."""
        if x["abstract"]:
            if j.get("verdict") == "符合":
                return 1 if x["source"] == "顶刊清单" else 2
            # tier 4: everything holds except that the abstract does not show solvation
            if (j.get("solvation") in ("no", "unclear") and j.get("li_s_liquid") == "yes"
                    and j.get("battery_experiment") == "yes" and j.get("not_review") == "yes"
                    and j.get("not_method") != "no"):
                return 4
            return None
        # title only: a title can't show cell experiments, so "unclear" is allowed there; the title must
        # clearly be about solvation and nothing may be judged "no". Re-checked on the full text after download.
        if (j.get("solvation") == "yes" and j.get("li_s_liquid") != "no"
                and all(j.get(k) != "no" for k in CRIT)):
            return 1 if x["source"] == "顶刊清单" else 3
        # tier 5 (last fallback, 10-23): title only, nothing but solvation judged "no"; kept only if the title
        # check below says the electrolyte formulation is the research object. Full text decides after download.
        if all(j.get(k) != "no" for k in CRIT if k != "solvation") and j:
            return 5
        return None

    pre = [x for x in cands if base_tier(x, judged.get(x["doi"], {}))]
    subject = asyncio.run(subject_check(pre))

    def tier(x, j):
        if x["doi"] in MANUAL_DROP:
            return None
        t = base_tier(x, j)
        s = subject.get(x["doi"], {}).get("electrolyte_subject")
        if not t or s == "no" or (s != "yes" and (x["abstract"] or t in (4, 5))):
            return None          # user, 10-22: the electrolyte itself must be the research object
        return t

    need_ft = {1: "", 2: "", 3: "电池实验、溶剂化", 4: "溶剂化", 5: "电池实验、溶剂化、研究对象"}

    rows = []
    for x in cands:
        j = judged.get(x["doi"], {})
        ev = j.get("evidence", "")
        ev_ok = ("" if not ev else "✅" if norm(ev) and norm(ev) in norm(x["abstract"]) else "❌ 摘要中找不到")
        t = tier(x, j)
        rows.append({**x, **j, **subject.get(x["doi"], {}), "依据": "摘要" if x["abstract"] else "仅题名",
                     "Claude题名人工剔除": MANUAL_DROP.get(x["doi"], ""),
                     "原句核验": ev_ok, "_tier": t,
                     "下载后正文核": need_ft[5] if t == 5 else "电池实验、溶剂化" if t and not x["abstract"]
                     else need_ft.get(t, "")})
    order = sorted([r for r in rows if r["_tier"]], key=lambda r: (r["_tier"], -r["cites"]))
    for i, r in enumerate(order, 1):
        r["下载顺序"] = i
    tier_name = {1: "1 顶刊清单", 2: "2 摘要确认", 3: "3 仅题名(后备)", 4: "4 电解液论文·摘要未提溶剂化",
                 5: "5 仅题名·电解液论文(兜底)"}
    cols = ["下载顺序", "下载层", "下载后正文核", "Claude题名人工剔除", "verdict", "electrolyte_subject", "依据",
            "source", "doi", "year",
            "venue", "cites", "title", *CRIT, "reason", "subject_reason", "evidence", "原句核验", "abstract"]
    with TABLE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r.get("下载顺序") or 10**6, -r["cites"])):
            w.writerow({**r, "下载层": tier_name.get(r["_tier"], ""), "verdict": r.get("verdict", "未判")})
        for d, why in dropped.items():
            w.writerow({"doi": d, "verdict": why, "source": next((x["source"] for x in pool if x["doi"] == d), "")})
    DL_LIST.write_text("\n".join(r["doi"] for r in order) + "\n", encoding="utf-8")
    from collections import Counter
    print("[result] verdicts:", dict(Counter(r.get("verdict", "未判") for r in rows)))
    print("[result] download tiers:", dict(Counter(tier_name[r["_tier"]] for r in order)))
    print("[result] evidence check:", dict(Counter(r["原句核验"] for r in rows if r.get("verdict"))))
    print(f"[result] table -> {TABLE}\n[result] download list ({len(order)}) -> {DL_LIST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
