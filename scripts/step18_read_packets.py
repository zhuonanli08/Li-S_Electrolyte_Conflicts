"""step18：为强的“反对多数”候选生成读原文包（11-07 用户同意：④ 先读强的 40 条）。

每条候选（step17 合并后的“反对多数”，强弱 = 强）配齐：相反的对（两边配方、测试、性能数值、组分变化、还一起变了什么）、
两边测量的证据原句、本篇的对照说明、对比说明、缺口、作者机制与设计结论摘要，以及 11-06 读原文时对本篇其他候选的判定（如有）。
读原文包含原句（版权；仓库公开）：文件名带“（含原句）”，.gitignore 已排除，不提交。
数据：output/张力候选_313篇_2026-11-07/张力候选.json、output/两两比较表述_313篇_2026-11-06/比较表述.json、
     output/试跑313篇_2026-11-05/papers/<论文>/candidate.json 与 source.json、output/归因_313篇_2026-11-06/归因判定.json。
输出：output/张力判定_313篇_2026-11-07/读原文包（含原句）.json；加参数 v2 时读 v2 候选，写 读原文包_v2（含原句）.json；
     参数 weak（11-07 用户：读弱的）读 v2 的弱候选，写 读原文包_v2_弱（含原句）.json，编号 W01…；
     参数 nocons（11-07 用户：读没有共识）按“描述符 → 性能”列出两边论文的各对比较，写 读原文包_v2_没有共识（含原句）.json，编号 N01…
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step18_read_packets.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
WEAK, NOCONS = "weak" in sys.argv[1:], "nocons" in sys.argv[1:]
V2 = "v2" in sys.argv[1:] or WEAK or NOCONS  # 11-07 描述符修正后的 v2 候选：python step18_read_packets.py v2
CAND = ROOT / "output" / ("张力候选_313篇_v2_2026-11-07" if V2 else "张力候选_313篇_2026-11-07") / "张力候选.json"
PAIRS = ROOT / "output" / ("两两比较表述_313篇_v2_2026-11-07" if V2 else "两两比较表述_313篇_2026-11-06") / "比较表述.json"
PAPERS = ROOT / "output" / "试跑313篇_2026-11-05" / "papers"
PRIOR = ROOT / "output" / "归因_313篇_2026-11-06" / "归因判定.json"
OUT = ROOT / "output" / "张力判定_313篇_2026-11-07"
CUT = 500


def short(t, n=CUT):
    t = " ".join(str(t).split())
    return t if len(t) <= n else t[:n] + "…"


def paper(cache, p):
    if p not in cache:
        c = json.loads((PAPERS / p / "candidate.json").read_text(encoding="utf-8"))
        src = {s["id"]: s.get("text", "") for s in json.loads((PAPERS / p / "source.json").read_text(encoding="utf-8"))}
        cache[p] = (c, src)
    return cache[p]


def nocons():
    """没有共识：每个组合列出两边论文、各自的同测试比较（组分变化、测试、方向、倍数、特殊组分）与本篇对比说明。"""
    sys.path.insert(0, str(ROOT / "scripts"))
    import step17_tension_trial as T
    allc = json.loads(CAND.read_text(encoding="utf-8"))
    R = json.loads(PAIRS.read_text(encoding="utf-8"))
    key = {x["中文"]: x["描述符"] for r in R for x in r["描述符"]}
    cls = {v: k for k, v in T.CN.items()}
    J = OUT / "判定_v2.json"
    judged = json.loads(J.read_text(encoding="utf-8")) if J.exists() else []
    cache, packets = {}, []
    for k, x in enumerate(allc["没有共识"], 1):
        S = T.votes(R, key[x["描述符"]], cls[x["性能"]], {T.SAME})
        byid = {r["编号"]: r for r in R}
        per = {}
        for v in S:
            r = byid[v["编号"]]
            per.setdefault(v["论文"], []).append({"编号": r["编号"], "票": T.lab(v["效应"]), "倍数（变好方向）": round(2.718281828 ** v["效应"], 3),
                                                "A": r["A"]["配方名"], "B": r["B"]["配方名"], "测试": r["A"]["测试名"], "组分变化": short(r["组分变化"], 160),
                                                "特殊组分": "；".join(f"{y['组分']}（{y['类型']}）" for y in r.get("特殊组分变化") or []), "被动": v["被动"]})
        papers = []
        for p, ps in sorted(per.items()):
            c, _ = paper(cache, p)
            papers.append({"论文": p, "对": ps, "对照": short(c.get("control_type"), 120), "对比说明": short(json.dumps(c.get("comparison_notes"), ensure_ascii=False), 300),
                           "本篇已有判定": [f"{j['候选编号']} {j['性能']} {j['真假']}：{short(j['原因'], 120)}" for j in judged if j["论文"] == p]})
        packets.append({"编号": f"N{k:02d}", "描述符": x["描述符"], "性能": x["性能"], "好": x["好"], "差": x["差"], "近": x["近"],
                        "多数占比": x["多数占比"], "篇": x["篇"], "按篇": x["按篇"], "论文": papers})
    f = OUT / "读原文包_v2_没有共识（含原句）.json"
    f.write_text(json.dumps(packets, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(packets)} 个没有共识的组合；{f.stat().st_size // 1024} KB → {f}")


def main():
    if NOCONS:
        return nocons()
    OUT.mkdir(parents=True, exist_ok=True)
    cand = json.loads(CAND.read_text(encoding="utf-8"))["反对多数（按同一批比较合并）"]
    byid = {r["编号"]: r for r in json.loads(PAIRS.read_text(encoding="utf-8"))}
    prior = json.loads(PRIOR.read_text(encoding="utf-8")) if PRIOR.exists() else {}
    strong = [g for g in cand if g["强弱"] == ("弱" if WEAK else "强")]
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
            "候选编号": f"{'W' if WEAK else 'TC'}{k:02d}", "论文": p, "性能": g["性能"], "涉及描述符": g["涉及描述符"], "全是被动": g["全是被动"],
            "相反的对": pairs,
            "证据原句": {i: short(src.get(i, "（source.json 无此编号）")) for i in ids},
            "对照": c.get("control_type"), "对比说明": c.get("comparison_notes"),
            "缺口": [short(x.get("reason", ""), 300) for x in c.get("gaps", [])],
            "作者机制": [{"编号": m["id"], "摘要": short(m.get("summary", ""), 200), "来源": m.get("source_type"), "测试": m.get("test_ids"),
                       "证据": m.get("evidence_ids")} for m in c.get("mechanisms", [])],
            "设计结论": [short(d.get("summary", ""), 200) for d in c.get("design_claims", [])],
            "11-06 本篇其他判定": {kk: {"判定": v["判定"], "原因": v["原因"], "归类": v["归类"]} for kk, v in prior.items() if kk.endswith("|" + p)},
        })
    f = OUT / ("读原文包_v2_弱（含原句）.json" if WEAK else "读原文包_v2（含原句）.json" if V2 else "读原文包（含原句）.json")
    f.write_text(json.dumps(packets, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(packets)} 条候选，{len({x['论文'] for x in packets})} 篇；{f.stat().st_size // 1024} KB → {f}")


if __name__ == "__main__":
    main()
