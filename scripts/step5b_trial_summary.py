"""方案 §5.5 C 步试提（选项 B）汇总：原句核验 + 字段可得率 + 权衡可判定性

读 output/第二阶段_C步试提/json/Pxxx.json（Claude 在会话中逐篇提取），对照原文（text_cache 正文 + SI）：
  1. 原句核验：去空白、小写后做子串匹配，✅ 找到 / ❌ 找不到 / — 无原句
  2. 每篇的条件字段可得率（硫载量、E/S 直接或可算、锂厚或 N/P、倍率、温度）
  3. 每组 Li–S 配方比较：指标数、同一指标的取值点数、能否判定权衡、是否出现权衡 / 随运行时间变化
输出：output/第二阶段_C步试提/C步试提_汇总.xlsx（指标明细、论文汇总、可得率汇总三页）
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 -I step5b_trial_summary.py
"""
import glob
import json
import os
import re
import sys
from collections import Counter

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step1c_checkup as S  # noqa: E402

ROOT = S.ROOT
OUT = os.path.join(ROOT, "output", "第二阶段_C步试提")
DISCHARGE = {"首圈容量", "指定圈数放电容量"}   # 同一个量（放电容量）在不同圈数：方案 §6.6 的"随运行时间变化"
DECIDED = {"A更好", "A更差"}


def squash(t):
    """只保留字母和数字再比对：PDF 抽取的上标负号、私用区字符等不可见字符会让原句抄写对不上。"""
    return re.sub(r"[^0-9a-z]", "", S.norm(t.replace("\x00", "")).lower())


def load_text(doi):
    key = re.sub(r"[^\w.-]+", "_", doi)
    out = ""
    for suf in ("main", "si"):
        p = os.path.join(S.CACHE, f"{key}.{suf}.txt")
        if os.path.exists(p):
            out += open(p, encoding="utf-8", errors="ignore").read() + "\n"
    return squash(out)


def has(v):
    return bool(str(v or "").strip())


def main():
    screen = pd.read_csv(os.path.join(ROOT, "output", "第二阶段_资格筛选.csv"), encoding="utf-8-sig", dtype=str).fillna("")
    doi = dict(zip(screen["编号"], screen["doi"]))
    rows, papers = [], []
    for f in sorted(glob.glob(os.path.join(OUT, "json", "P*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        pid = d["编号"]
        text = load_text(doi[pid])
        conds = d.get("条件", {})
        lis = {k: c for k, c in conds.items() if not str(c.get("正极", "")).startswith("无")}
        c0 = next(iter(lis.values()), {})
        es_ok = has(c0.get("E/S")) or (has(c0.get("电解液体积")) and has(c0.get("面积")) and has(c0.get("硫载量")))
        cmp_li, judge, cross, time_rev, time_small, src = 0, 0, 0, 0, 0, Counter()
        for i, c in enumerate(d.get("比较", [])):
            is_li = c.get("条件") in lis
            inds = c.get("指标", [])
            for m in inds:
                q = m.get("原句", "")
                mark = "—" if not q.strip() else ("✅" if squash(q)[:220] in text else "❌")
                src[m.get("来源", "").split("（")[0]] += 1
                rows.append({"论文": pid, "比较": f"{pid}-K{i + 1}", "A": c.get("A"), "B": c.get("B"), "条件": c.get("条件"),
                             "Li–S 电池": "是" if is_li else "否", "层": c.get("层"), "改变因素": "、".join(c.get("改变因素", [])),
                             "指标": m.get("指标"), "取值点": m.get("取值点"), "A 值": m.get("A"), "B 值": m.get("B"), "单位": m.get("单位"),
                             "方向": m.get("方向"), "值来源": m.get("来源"), "原句核验": mark, "原句": q, "备注": m.get("备注", ""),
                             "复核 ✍": ""})
            if not is_li:
                continue
            cmp_li += 1
            dec = [m for m in inds if m.get("方向") in DECIDED]
            kinds = {m.get("指标") for m in dec}
            same_multi = any(sum(1 for m in dec if m.get("指标") == k) >= 2 for k in kinds)
            if len(kinds) >= 2 or same_multi:
                judge += 1
            # 跨指标权衡：不同指标（放电容量一类算一个指标）给出相反方向
            fam = {}
            for m in dec:
                fam.setdefault("放电容量" if m.get("指标") in DISCHARGE else m.get("指标"), set()).add(m.get("方向"))
            if len(fam) >= 2 and any("A更好" in a and "A更差" in b for a in fam.values() for b in fam.values()):
                cross += 1
            # 随运行时间变化：放电容量在不同圈数方向相反；或一侧进入差异小区间
            dis = {m.get("方向") for m in inds if m.get("指标") in DISCHARGE}
            if dis >= DECIDED:
                time_rev += 1
            elif "差异小" in dis and dis & DECIDED:
                time_small += 1
        papers.append({"论文": pid, "层（B 步）": screen.loc[screen["编号"] == pid, "层"].iloc[0],
                       "有 Li–S 配方比较": "是" if cmp_li else "否", "Li–S 比较组数": cmp_li,
                       "硫载量": "有" if has(c0.get("硫载量")) else "缺", "E/S（直接或可算）": "有" if es_ok else "缺",
                       "锂厚或 N/P": "有" if (has(c0.get("锂厚")) or has(c0.get("N/P"))) else "缺",
                       "倍率": "有" if has(c0.get("倍率")) else "缺", "温度": "有" if has(c0.get("温度")) else "缺",
                       "可判定权衡的比较组": judge, "跨指标权衡组数": cross, "放电容量随圈数反转组数": time_rev,
                       "放电容量一侧进入差异小组数": time_small,
                       "值来源": "；".join(f"{k}{v}" for k, v in src.most_common()), "备注": d.get("备注", "")})
    det, pap = pd.DataFrame(rows), pd.DataFrame(papers)
    n = len(pap)
    li = pap[pap["有 Li–S 配方比较"] == "是"]
    summ = [("论文数", n, ""),
            ("有 Li–S 全电池 / 半电池配方比较", len(li), f"{len(li) / n:.0%}"),
            ("其中至少一组可判定权衡（≥2 个有方向的指标，或同一指标 ≥2 个取值点）", int((li["可判定权衡的比较组"] > 0).sum()), ""),
            ("其中出现跨指标权衡（不同指标胜方相反）", int((li["跨指标权衡组数"] > 0).sum()), ""),
            ("其中放电容量随圈数反转（同一量、不同圈数胜方相反）", int((li["放电容量随圈数反转组数"] > 0).sum()), ""),
            ("其中放电容量一侧进入差异小区间（无反转）", int(((li["放电容量一侧进入差异小组数"] > 0) & (li["放电容量随圈数反转组数"] == 0)).sum()), "")]
    for col in ["硫载量", "E/S（直接或可算）", "锂厚或 N/P", "倍率", "温度"]:
        summ.append((f"条件可得：{col}", int((pap[col] == "有").sum()), f"{(pap[col] == '有').mean():.0%}"))
    vs = Counter(r["值来源"].split("（")[0] for r in rows)
    for k, v in vs.most_common():
        summ.append((f"指标值来源：{k}", v, f"{v / len(rows):.0%}"))
    ok = Counter(r["原句核验"] for r in rows)
    for k in ("✅", "❌", "—"):
        summ.append((f"原句核验 {k}", ok.get(k, 0), ""))
    summ.append(("指标条目总数", len(rows), ""))
    sm = pd.DataFrame(summ, columns=["项目", "数量", "比例"])
    with pd.ExcelWriter(os.path.join(OUT, "C步试提_汇总.xlsx")) as w:
        sm.to_excel(w, sheet_name="可得率汇总", index=False)
        pap.to_excel(w, sheet_name="论文汇总", index=False)
        det.to_excel(w, sheet_name="指标明细", index=False)
    print(sm.to_string(index=False))
    print(det[det["原句核验"] == "❌"][["比较", "指标", "原句"]].to_string())


if __name__ == "__main__":
    main()
