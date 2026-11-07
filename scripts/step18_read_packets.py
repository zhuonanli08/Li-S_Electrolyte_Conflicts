"""step18：为强的“反对多数”候选生成读原文包（11-07 用户同意：④ 先读强的 40 条）。

每条候选（step17 合并后的“反对多数”，强弱 = 强）配齐：相反的对（两边配方、测试、性能数值、组分变化、还一起变了什么）、
两边测量的证据原句、本篇的对照说明、对比说明、缺口、作者机制与设计结论摘要，以及 11-06 读原文时对本篇其他候选的判定（如有）。
读原文包含原句（版权；仓库公开）：文件名带“（含原句）”，.gitignore 已排除，不提交。
数据：output/张力候选_313篇_2026-11-07/张力候选.json、output/两两比较表述_313篇_2026-11-06/比较表述.json、
     output/试跑313篇_2026-11-05/papers/<论文>/candidate.json 与 source.json、output/归因_313篇_2026-11-06/归因判定.json。
输出：output/张力判定_313篇_2026-11-07/读原文包（含原句）.json
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step18_read_packets.py
"""
import json
from pathlib import Path

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
CAND = ROOT / "output" / "张力候选_313篇_2026-11-07" / "张力候选.json"
PAIRS = ROOT / "output" / "两两比较表述_313篇_2026-11-06" / "比较表述.json"
PAPERS = ROOT / "output" / "试跑313篇_2026-11-05" / "papers"
PRIOR = ROOT / "output" / "归因_313篇_2026-11-06" / "归因判定.json"
OUT = ROOT / "output" / "张力判定_313篇_2026-11-07"
CUT = 500


def short(t, n=CUT):
    t = " ".join(str(t).split())
    return t if len(t) <= n else t[:n] + "…"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cand = json.loads(CAND.read_text(encoding="utf-8"))["反对多数（按同一批比较合并）"]
    byid = {r["编号"]: r for r in json.loads(PAIRS.read_text(encoding="utf-8"))}
    prior = json.loads(PRIOR.read_text(encoding="utf-8")) if PRIOR.exists() else {}
    strong = [g for g in cand if g["强弱"] == "强"]
    packets, cache = [], {}
    for k, g in enumerate(strong, 1):
        p = g["论文"]
        if p not in cache:
            c = json.loads((PAPERS / p / "candidate.json").read_text(encoding="utf-8"))
            src = {s["id"]: s.get("text", "") for s in json.loads((PAPERS / p / "source.json").read_text(encoding="utf-8"))}
            cache[p] = (c, src)
        c, src = cache[p]
        pairs, ids = [], []
        for x in g["相反的对"]:
            r = byid[x["编号"]]
            side = {}
            for s in ("A", "B"):
                e = r[s]
                side[s] = {"配方": e["配方"], "配方名": e["配方名"], "是否对照": e["是否对照"], "配方文字": e["配方文字"],
                           "测试": e["测试"], "测试名": e["测试名"], "证据句子": e["证据句子"], "标记": e.get("标记", [])}
                ids += e["证据句子"]
            pairs.append({"编号": r["编号"], "比较类型": r["比较类型"], "A": side["A"], "B": side["B"],
                          "性能": r["性能"], "条件": [y for y in r["条件"] if y["方向"] not in ("相近", "相同") or y["条件"] == "圈数"],
                          "组分变化": r["组分变化"], "还一起变了什么": x["描述符"]})
        ids = list(dict.fromkeys(ids))
        packets.append({
            "候选编号": f"TC{k:02d}", "论文": p, "性能": g["性能"], "涉及描述符": g["涉及描述符"], "全是被动": g["全是被动"],
            "相反的对": pairs,
            "证据原句": {i: short(src.get(i, "（source.json 无此编号）")) for i in ids},
            "对照": c.get("control_type"), "对比说明": c.get("comparison_notes"),
            "缺口": [short(x.get("reason", ""), 300) for x in c.get("gaps", [])],
            "作者机制": [{"编号": m["id"], "摘要": short(m.get("summary", ""), 200), "来源": m.get("source_type"), "测试": m.get("test_ids"),
                       "证据": m.get("evidence_ids")} for m in c.get("mechanisms", [])],
            "设计结论": [short(d.get("summary", ""), 200) for d in c.get("design_claims", [])],
            "11-06 本篇其他判定": {kk: {"判定": v["判定"], "原因": v["原因"], "归类": v["归类"]} for kk, v in prior.items() if kk.endswith("|" + p)},
        })
    f = OUT / "读原文包（含原句）.json"
    f.write_text(json.dumps(packets, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(packets)} 条候选，{len({x['论文'] for x in packets})} 篇；{f.stat().st_size // 1024} KB → {f}")


if __name__ == "__main__":
    main()
