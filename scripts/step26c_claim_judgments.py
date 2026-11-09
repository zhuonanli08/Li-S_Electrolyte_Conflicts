"""step26c：路线二“比说法”逐对判读（11-09）。读 step26b 的 103 对候选配对，Claude 逐对读两条摘要后判定。

判定只写在下面的 J 里：真对立（两条对同一件事给出相反结论）列出；其余 94 对读过、判“不对立”（多是方向词判错，
如两条都说“抑制穿梭有利”；或两条说的不是一回事）。真对立按话题归组；另记一个“阵营”：几条说法彼此一致、
但与路线一的共识相反（R2-B），这类对立要两条路线放在一起才看得出。
只用提取摘要，没有回原文核对；AI 辅助，用户尚未逐项人工确认。
输出：output/说法对说法_313篇_2026-11-09/（判读.json、话题.json、说法对说法表.xlsx；均不含摘要）。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step26c_claim_judgments.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
from step13_common import write_xlsx

D = ROOT / "output" / "说法对说法_313篇_2026-11-09"
PAPERS = ROOT / "output" / "试跑313篇_2026-11-05" / "papers"

TOPIC = {
    "R2-A": "贫液、高载量下，多硫化物该多溶还是少溶（多溶：正极转化快、防钝化、硫利用率高；少溶：电解液变稠、穿梭、锂腐蚀）",
    "R2-B": "LiFSI 在锂硫里对锂负极是好是坏（与路线一共识“阴离子磺酰多 → Li‖Cu CE 好”相反的一派）",
    "R2-C": "LiNO₃ 耗尽以后：多硫化物多时 LiNO₃ 仍能压住穿梭，还是耗尽后穿梭回来、贫液靠接近溶解度上限才稳定",
}
# 配对 → (话题, 甲方立场, 乙方立场, 一句话)
J = {
    "CP014": ("R2-A", "多溶", "少溶", "P106 转述：限制溶解的电解液电导低；P270：高 E/S 成为多硫化物储库、加剧穿梭"),
    "CP024": ("R2-A", "多溶", "少溶", "P006：高载量需在有限电解液里溶更多多硫化物、低载量最优不能外推；P270：电解液多 → 穿梭与活性物损失"),
    "CP034": ("R2-A", "少溶", "多溶", "P234：缩短可溶多硫化物停留时间有利；P336：降低盐浓度促进多硫化物溶解，改善高载量/低 E/S 利用率"),
    "CP038": ("R2-A", "少溶", "多溶", "P294：多硫化物溶入使黏度升高、阻碍传输；P336：低浓度促进多硫化物与 Li₂S 生成，E/S 5 下硫利用率更高"),
    "CP044": ("R2-A", "少溶", "多溶", "P006：电解液黏度高使活性物电子隔离；P201：溶解态 Li₂S 更易氧化，高载量下动力学更快"),
    "CP066": ("R2-A", "少溶", "多溶", "P107：短链硫化物沉积使阻抗增加；P334：短链硫化物溶解加速扩散、改善动力学与倍率"),
    "CP095": ("R2-A", "少溶", "多溶", "P202 转述：溶解多硫化物在负极还原、损失容量；P275 推测：溶解一定量 Li₂S 改善充电动力学"),
    "CP101": ("R2-A", "多溶", "少溶", "P336：低浓度促进多硫化物生成、E/S 5 下利用率高；P352 推测：高载量低 E/S 增大电阻、阻碍液–固转化"),
    "CP063": ("R2-C", "LiNO₃ 压得住", "耗尽后回来", "P049：大量多硫化物溶解时 LiNO₃ 仍抑制穿梭、CE≈100%；P131：LiNO₃ 耗尽后穿梭重现，贫液接近多硫化物溶解度上限时反而稳定"),
}
# 阵营（彼此一致，但与路线一共识相反）：配对 → 一句话
CAMP = {
    "CP058": ("R2-B", "P268：纯 LiFSI 不能形成稳固 SEI；P350：含 LiFSI 液 Li 表面粗糙、SEI 不稳定"),
    "CP060": ("R2-B", "P001：LiFSI 比 LiTFSI 在 Li 表面生成更多不可逆 LiSOx、循环更差；P350：FSI 与 Li 反应降低整体表现"),
    "CP068": ("R2-B", "P199 转述：LiTFSI 可提高 LiFSI 稳定性；P204：高浓 LiFSI 触发 DOL 自聚、缩短存储寿命"),
}
# 路线一里与 R2-B 相反的证据（step18 判定、step26a 票数）
R2B_OTHER = ["路线一共识：阴离子磺酰（每升）→ Li‖Cu CE 变好（44 好 : 13 差，16 篇；只用系列内 25 : 10，12 篇，共识保留）",
             "P384（W25、TC16）：只用 LiTFSI 的砜类局部高浓与锂不兼容（58.1%），部分换成 LiFSI 后成膜问题解决",
             "P388（W30）：同一 MTFP/FEC 里 LiFSI 97.6% 好于 LiPF6 92.4%",
             "P350（TC29）：主盐换成 LiFSI 后 20 圈衰减更快，作者结论 TFSI 比 FSI 更稳定——与负极侧结论方向不同（负极 CE vs 循环）"]


def year(p):
    f = PAPERS / p / "input_meta.json"
    return (json.loads(f.read_text(encoding="utf-8")).get("year") or None) if f.exists() else None


def main():
    C = json.loads((D / "候选配对.json").read_text(encoding="utf-8"))["配对"]
    rows, topics = [], {k: {"话题": v, "配对": [], "各方论文": {}} for k, v in TOPIC.items()}
    for c in C:
        a, b = c["甲"], c["乙"]
        if c["配对"] in J:
            t, sa, sb, note = J[c["配对"]]
            verdict = "真对立"
            for p, s in ((a["论文"], sa), (b["论文"], sb)):
                topics[t]["各方论文"].setdefault(s, set()).add(p)
            topics[t]["配对"].append(c["配对"])
        elif c["配对"] in CAMP:
            t, note = CAMP[c["配对"]]
            verdict = "同一阵营（与路线一共识相反）"
            topics[t]["各方论文"].setdefault("LiFSI 对负极/循环不利", set()).update({a["论文"], b["论文"]})
            topics[t]["配对"].append(c["配对"])
        else:
            t, note, verdict = "", "", "不对立"
        rows.append({"配对": c["配对"], "相似度": c["相似度"], "甲": f"{a['论文']}/{a['机制']}（{a['来源']}）", "乙": f"{b['论文']}/{b['机制']}（{b['来源']}）",
                     "判定": verdict, "话题": t, "说明": note})
    for k, t in topics.items():
        t["各方论文"] = {s: [f"{p}（{year(p) or '年份未知'}）" for p in sorted(ps)] for s, ps in t["各方论文"].items()}
        if k == "R2-B":
            t["路线一里的相反证据"] = R2B_OTHER
    cnt = Counter(r["判定"] for r in rows)
    summary = {"候选配对": len(rows), "判定": dict(cnt), "初筛精确率（真对立/候选）": round(cnt["真对立"] / len(rows), 3),
               "话题": dict(TOPIC),
               "说明": "只读提取摘要、未回原文；方向词初筛精确率低，召回未知（没被方向词抓到的对立看不到）。AI 辅助，用户尚未逐项人工确认。"}
    (D / "判读.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    (D / "话题.json").write_text(json.dumps({"汇总": summary, "话题": topics}, ensure_ascii=False, indent=1), encoding="utf-8")
    write_xlsx(D / "说法对说法表.xlsx", [
        ("逐对判读", ["配对", "相似度", "甲（论文/机制）", "乙（论文/机制）", "判定", "话题", "Claude 一句话"],
         [[r["配对"], r["相似度"], r["甲"], r["乙"], r["判定"], r["话题"], r["说明"]] for r in rows]),
        ("话题", ["话题", "内容", "配对", "各方论文（年份）"],
         [[k, v["话题"], "；".join(v["配对"]), "；".join(f"{s}：{'、'.join(ps)}" for s, ps in v["各方论文"].items())] for k, v in topics.items()])],
        notes=["路线二“比说法”（step26b 初筛 → step26c 逐对判读，11-09）。摘要不放进公开文件，本机见 候选配对（含原句）.json。",
               "初步，AI 辅助，用户尚未逐项人工确认；只读提取摘要、未回原文。"])
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    for k, v in topics.items():
        print(k, v["各方论文"])


if __name__ == "__main__":
    main()
