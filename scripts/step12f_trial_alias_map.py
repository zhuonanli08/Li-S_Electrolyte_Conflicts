"""11-04 243 篇试跑：按规则把新论文的组分写法对应到已核定的组分（方案 §5.8），只写试跑文件夹里的核定表副本。

规则（依次尝试，命中即停）：
  ① 写法去掉括号部分、空白和“nominal”等修饰后，等于已有通配别名或组分 ID（不分大小写，下标数字统一）；
  ② 写法里出现的全称与某个组分的“全称正则”匹配，且只匹配一个组分；
  ③ 缩写词典（step12c）判“通用”的缩写；
  ④ 已有通配“未收录”写法规范化后相同的，记同一原因。
命中的写法以通配形式（论文 *）加入核定表副本，备注写明依据（备注不改核验状态）；剩下的列入 待核定写法.json，由 Claude 读原文核定。
用法：KETI2_COMP=<试跑组分表文件夹> python -X utf8 scripts/step12f_trial_alias_map.py [--write]
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ["KETI2_COMP"])
CURATION = OUT / "组分核定.json"
CANDS = OUT / "work" / "候选组分.json"
SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁺⁻−–", "0123456789+---")


def norm(s: str) -> str:
    s = s.translate(SUB)
    s = re.sub(r"[（(\[].*?[)）\]]", " ", s)
    s = re.sub(r"\b(nominal|pure|anhydrous|dry|commercial|neat)\b", " ", s, flags=re.I)
    return re.sub(r"\s+", "", s).lower()


def inner(s: str) -> list[str]:
    return [m.strip() for m in re.findall(r"[（(\[](.*?)[)）\]]", s.translate(SUB))] + [s.translate(SUB)]


def main(write: bool) -> None:
    cur = json.loads(CURATION.read_text(encoding="utf-8"))
    rows = json.loads(CANDS.read_text(encoding="utf-8"))
    comps = {c["id"]: c for c in cur["组分"]}
    alias = {(a["论文"], a["写法"]) for a in cur["别名"]}
    excl = {(e["论文"], e["写法"]) for e in cur["未收录"]}
    wild = {}
    for a in cur["别名"]:
        if a["论文"] == "*":
            wild.setdefault(norm(a["写法"]), a["组分"])
    for cid in comps:
        wild.setdefault(norm(cid), [cid])
    wild_ex = {norm(e["写法"]): e["原因"] for e in cur["未收录"] if e["论文"] == "*"}
    abbr = json.loads((OUT / "缩写词典.json").read_text(encoding="utf-8"))["缩写"]
    full_re = {cid: re.compile(c["全称正则"], re.I) for cid, c in comps.items() if c.get("全称正则")}

    todo = defaultdict(list)
    for r in rows:
        k = (r["paper_id"], r["name"])
        if k in alias or k in excl or ("*", r["name"]) in alias or ("*", r["name"]) in excl:
            continue
        todo[r["name"]].append(r)
    new_alias, new_excl, left, how = [], [], {}, Counter()
    for name, rs in sorted(todo.items()):
        hit, basis = None, None
        n = norm(name)
        if n in wild:
            hit, basis = wild[n], "① 规范化后与已核定写法相同"
        if not hit:
            m = {cid for cid, rx in full_re.items() for t in inner(name) if rx.search(t)}
            if len(m) == 1:
                hit, basis = sorted(m), "② 写法中的全称与组分全称一致"
        if not hit:
            a = abbr.get(re.sub(r"\s*[（(].*", "", name).strip())
            if a and a["判定"] == "通用" and a.get("组分") in comps:
                hit, basis = [a["组分"]], f"③ 领域通用缩写（{a['定义为本组分']}/{a['定义篇数']} 篇）"
        if hit:
            new_alias.append({"论文": "*", "写法": name, "组分": hit, "备注": f"11-04 试跑规则映射：{basis}"})
            how[basis[:1]] += len(rs)
            continue
        if n in wild_ex:
            new_excl.append({"论文": "*", "写法": name, "原因": wild_ex[n]})
            how["④"] += len(rs)
            continue
        uses = {k for r in rs for k in r["用途"]}
        reason = None
        if uses <= {"计算模型"}:
            reason = "只出现在计算模型中（试跑规则 ⑤）"
        elif uses <= {"表征测量液", "计算模型"}:
            reason = "只出现在表征测量液或计算模型中（试跑规则 ⑤）"
        elif uses <= {"固体/材料", "未被配方引用", "计算模型"}:
            reason = "固体/材料或未被配方引用（试跑规则 ⑤）"
        elif re.search(r"未报告|未知|未明确|未写明|身份及浓度|占位|不详", name):
            reason = "占位：原文未写明身份（试跑规则 ⑥）"
        else:  # ⑦ 多硫化物/硫：与 30 篇口径一致，对应到已有硫物种组分（B 档）
            t = name.translate(SUB)
            ps = re.findall(r"Li2S(\d)", t)
            sp = [f"Li2S{ps[0]}"] if len(set(ps)) == 1 and f"Li2S{ps[0]}" in comps else \
                ["LiPS_x"] if re.search(r"多硫化|polysulfide|Li2S[xmn]\b|LiPS", t, re.I) else \
                ["S8"] if re.fullmatch(r"\s*(S8|sulfur|硫|elemental sulfur)\s*", t, re.I) else None
            if sp:
                new_alias.append({"论文": "*", "写法": name, "组分": sp, "备注": "11-04 试跑规则映射：⑦ 多硫化物/硫物种"})
                how["⑦"] += len(rs)
                continue
        if reason:
            new_excl.append({"论文": "*", "写法": name, "原因": reason})
            how[reason[-3:-1].strip() or "⑤"] += len(rs)
            continue
        left[name] = {"条数": len(rs), "论文": sorted({r["paper_id"] for r in rs}),
                      "用途": sorted({k for r in rs for k in r["用途"]}), "角色": sorted({r["role"] for r in rs}),
                      "原文片段": rs[0]["原文片段"][:2]}
    total = sum(len(v) for v in todo.values())
    print(f"待对应 {total} 条（{len(todo)} 种写法）；规则命中：{dict(how)}；剩余 {sum(v['条数'] for v in left.values())} 条、{len(left)} 种写法")
    print("剩余按用途：", Counter(u for v in left.values() for u in v["用途"]).most_common())
    if write:
        cur["别名"] += new_alias
        cur["未收录"] += new_excl
        CURATION.write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
        (OUT / "work" / "待核定写法.json").write_text(json.dumps(left, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"已写入：别名 +{len(new_alias)}，未收录 +{len(new_excl)} → {CURATION}")


if __name__ == "__main__":
    main("--write" in sys.argv)
