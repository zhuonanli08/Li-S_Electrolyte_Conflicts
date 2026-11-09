"""step26a：作者偏好复核（11-09 新方案 路线一）。

问题：同测试换配方的 571 对里，268 对是“作者的新配方 对 对照”，新配方赢 76%。“多数”里可能混着“作者推荐的总赢”。
做法：沿用 step17 的计票规则（一对一票、≥ 5 篇且 ≥ 2/3 才算有多数），把同测试比较分成两组各数一遍：
  - 系列内：两边都不是对照（作者自己的一组实验样之间，或两个对照之间），没有“新配方总赢”的偏好；
  - 新对对照：一边是对照。
再与全部同测试的结果（= step17 v2）逐条对比：多数方向是否一致、判定是否变化。
只读 两两比较表述_313篇_v2_2026-11-07/比较表述.json；输出 output/作者偏好复核_313篇_2026-11-09/。
初步；AI 辅助，用户尚未逐项人工确认。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step26a_series_recount.py
"""
import sys
import json
from pathlib import Path
from collections import Counter

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
from step13_common import write_xlsx
from step17_tension_trial import IN, CN, SAME, WORD, votes, tally, lab, effect

OUT = ROOT / "output" / "作者偏好复核_313篇_2026-11-09"


def is_series(r):
    return r["A"]["是否对照"] == r["B"]["是否对照"]


def fmt(t):
    if not t["对"]:
        return "—"
    return f"{t['好']} 好 : {t['差']} 差（{t['篇']} 篇）{t['判定']}" + (f"，多数{WORD[t['多数']]}" if t["有多数"] else "")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    R = json.loads(IN.read_text(encoding="utf-8"))
    S = [r for r in R if r["比较类型"] == SAME]
    ser = [r for r in S if is_series(r)]
    nvc = [r for r in S if not is_series(r)]
    names = {x["描述符"]: x["中文"] for r in R for x in r["描述符"]}

    # 新配方对对照：新配方赢几成（按性能方向，不分描述符）
    win = Counter()
    for r in nvc:
        e = effect(r)  # A 相对 B；B 恒为对照（已核对：A 从不是对照）
        win[lab(e)] += 1

    rows = []
    for d in names:
        for c in CN:
            tA, _ = tally(votes(S, d, c, {SAME}))
            if not tA["对"]:
                continue
            tS, _ = tally(votes(ser, d, c, {SAME}))
            tN, _ = tally(votes(nvc, d, c, {SAME}))
            if tA["有多数"]:
                if tS["有多数"] and tS["多数"] == tA["多数"]:
                    res = "共识保留"
                elif tS["有多数"]:
                    res = "方向反过来"
                elif tS["篇"] >= 5 and tS["好"] + tS["差"] and tS["多数"] == tA["多数"]:
                    res = "方向相同但不到门槛"
                elif tS["篇"] >= 5:
                    res = "系列内没有共识"
                else:
                    res = "系列内不足 5 篇"
            else:
                res = "原本无共识" + ("；系列内出现共识" if tS["有多数"] else "")
            share_new = (tN["好"] / (tN["好"] + tN["差"])) if tN["好"] + tN["差"] else None
            rows.append({"描述符": names[d], "性能": CN[c], "全部同测试": fmt(tA), "系列内": fmt(tS), "新对对照": fmt(tN),
                         "全部·判定": tA["判定"], "全部·多数": tA["多数"], "系列内·好": tS["好"], "系列内·差": tS["差"], "系列内·篇": tS["篇"],
                         "新对对照·好": tN["好"], "新对对照·差": tN["差"],
                         "新对对照里该描述符变高时变好的占比": round(share_new, 3) if share_new is not None else None,
                         "复核结果": res})
    order = ["共识保留", "方向相同但不到门槛", "系列内没有共识", "方向反过来", "系列内不足 5 篇"]
    rows.sort(key=lambda x: (order.index(x["复核结果"]) if x["复核结果"] in order else 9, x["性能"], x["描述符"]))
    summary = {"同测试换配方": len(S), "系列内": len(ser), "新对对照": len(nvc),
               "新对对照：新配方变好/相近/变差": {"好": win["好"], "近": win["近"], "差": win["差"]},
               "原有共识": sum(r["全部·判定"] == "有多数" for r in rows),
               "复核结果（原有共识的）": dict(Counter(r["复核结果"] for r in rows if r["全部·判定"] == "有多数")),
               "原本无共识但系列内出现共识": sum(r["复核结果"].endswith("系列内出现共识") for r in rows),
               "说明": "系列内 = 两边都不是对照；判定规则同 step17（≥ 5 篇、≥ 2/3）。初步，AI 辅助，用户尚未逐项人工确认。"}
    (OUT / "复核表.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "汇总.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    write_xlsx(OUT / "作者偏好复核.xlsx", [
        ("逐条对比", ["描述符", "性能", "全部同测试（= step17 v2）", "只用系列内", "只用新对对照", "复核结果"],
         [[r["描述符"], r["性能"], r["全部同测试"], r["系列内"], r["新对对照"], r["复核结果"]] for r in rows])],
        notes=["作者偏好复核（step26a，11-09）：同测试比较分成“系列内”（两边都不是对照）和“新对对照”各数一遍。",
               "共识保留 = 系列内也 ≥ 5 篇、≥ 2/3 同向；方向相同但不到门槛 = 系列内多数同向但篇数或占比不够。初步，AI 辅助，用户尚未逐项人工确认。"])
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
