"""step26d：两个检验的材料（11-09 新方案；回答“效果如何”）。

1. 准不准：从 ④ 的 76 条反例判定（判定_v2 强 39 ＋ 弱 37）里随机抽 20 条（种子 20261109，按“真假”分层：每类至少 1 条），
   做成核对表给用户和导师填（✍ 列）。表里附相反的那对比较、两边数值、证据原句、作者机制和 AI 判定。
   含原句的表只写本机（文件名带“（含原句）”，.gitignore 排除）；公开文件只放抽中的编号。
2. 全不全：领域公认争论清单（草稿）。由 Claude 在看过本轮结果之后按领域常识列出，会偏向已找到的，不能直接算召回率；
   要用户或导师先从综述定清单，再对照。这里只给模板和逐条对照位置。
输出：output/检验材料_313篇_2026-11-09/
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step26d_check_materials.py
"""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
from step13_common import write_xlsx

J = ROOT / "output" / "张力判定_313篇_2026-11-07"
OUT = ROOT / "output" / "检验材料_313篇_2026-11-09"
SEED, N = 20261109, 20

KNOWN = [
    ("LiNO₃ 的两面性：负极成膜 vs 正极低电位还原、耗尽", "找到", "step20 T3；P111；step26a 系列内 6 : 7；step26c R2-C"),
    ("强、弱溶剂化的权衡：容量（正极动力学）vs 稳定性（穿梭、负极）", "部分", "P313 直接证据；去掉特殊组分后“含氟 → 首圈容量低”6 : 13；方案 §2 已知张力对照"),
    ("局部高浓的稀释剂：惰性 vs 参与成膜", "找到", "step20 T1（9 对 13 篇，年份偏斜）；P381、P371"),
    ("高浓电解液：抑制多硫化物溶解 vs 黏度高、润湿差", "部分", "共识“主盐浓度 → Li‖Cu CE 好”；只改盐浓度呈 CE 好、容量与衰减差（篇数不足）；P123 TC02"),
    ("贫液下多硫化物该多溶还是少溶（溶剂化型 vs 稀溶剂化型）", "找到", "step26c R2-A（8 对）"),
    ("碳酸酯能否用于锂硫：取决于正极（SPAN、限域硫）", "找到", "P108；step20 T2（11 篇，降为已知条件）"),
    ("LiFSI vs LiTFSI：负极成膜好 vs 与多硫化物反应、循环差", "找到", "step26c R2-B；反例回收 P350、P384、P388"),
    ("DOL 开环聚合：有利成膜 vs 电解液变质", "部分", "step26c 只碰到 P204（高浓 LiFSI 触发 DOL 自聚）"),
    ("贫液失效主因：电解液耗尽 vs 锂负极粉化 vs 多硫化物溶解不足", "没找到", "说法相似但多数一致（P025、P139 都说电解液耗尽；P536 说溶解不足），没成对出现"),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jud = json.loads((J / "判定_v2.json").read_text(encoding="utf-8")) + json.loads((J / "判定_v2_弱.json").read_text(encoding="utf-8"))
    pk = {x["候选编号"]: x for f in ("读原文包_v2（含原句）.json", "读原文包_v2_弱（含原句）.json")
          for x in json.loads((J / f).read_text(encoding="utf-8"))}
    by = defaultdict(list)
    for x in jud:
        by[x["真假"]].append(x)
    rng = random.Random(SEED)
    pick = [rng.choice(v) for k, v in sorted(by.items())]           # 每类至少 1 条
    rest = [x for x in jud if x not in pick]
    pick += rng.sample(rest, N - len(pick))
    pick.sort(key=lambda x: x["候选编号"])
    rows = []
    for x in pick:
        p = pk.get(x["候选编号"], {})
        pairs = "\n".join(f"{c['编号']}：{c['A']['配方名']} 对 {c['B']['配方名']}（{c['性能']['指标A']} {c['性能']['值A']} vs {c['性能']['值B']}，{c['性能']['方向']}）"
                          for c in p.get("相反的对", []))
        quotes = "\n".join(f"{k}：{v}" for k, v in (p.get("证据原句") or {}).items())
        mech = p.get("作者机制")
        mech = "\n".join(f"{m.get('编号', '')}（{m.get('来源', '')}）：{m.get('摘要', '')}" for m in mech) if isinstance(mech, list) else (json.dumps(mech, ensure_ascii=False)[:1500] if mech else "")
        ds = x["涉及描述符"] if isinstance(x["涉及描述符"], list) else [x["涉及描述符"]]
        rows.append([x["候选编号"], x["论文"], x["性能"], "\n".join(ds), pairs, quotes, mech[:3000],
                     x["真假"], x["归类"], x["原因"], "", "", ""])
    write_xlsx(OUT / "抽样核对表（含原句）.xlsx", [
        ("抽样 20 条", ["编号", "论文", "性能", "反对的规律", "相反的那对比较", "证据原句", "作者机制（提取摘要）",
                    "AI 判定", "AI 归类", "AI 理由", "✍ 同意吗（同意/不同意/拿不准）", "✍ 你的判断", "✍ 备注"], rows)],
        notes=[f"从 76 条反例判定里随机抽 {N} 条（种子 {SEED}，每类至少 1 条）。请只看证据原句和作者机制，判断 AI 的“真假”和理由对不对。",
               "填完后：同意的条数 / 20 = 判定的准确率（粗估）；不同意的请写你的判断，用来改 ④ 的规则。本表含原句，只在本机，不要上传。"])
    pub = {"种子": SEED, "抽中": [x["候选编号"] for x in pick], "各类条数": {k: sum(x["真假"] == k for x in pick) for k in by},
           "总体各类条数": {k: len(v) for k, v in by.items()}}
    (OUT / "抽样编号.json").write_text(json.dumps(pub, ensure_ascii=False, indent=1), encoding="utf-8")
    write_xlsx(OUT / "公认争论对照（草稿）.xlsx", [
        ("对照", ["公认争论（Claude 草稿，待你或导师从综述替换）", "本流程找到了吗", "在哪里", "✍ 综述出处", "✍ 你的判断"],
         [[a, b, c, "", ""] for a, b, c in KNOWN])],
        notes=["这份清单是 Claude 看过本轮结果后按领域常识列的，会偏向已找到的，不能直接当召回率。",
               "正确做法：你或导师先从 2–3 篇综述列出公认争论（不看本流程结果），再逐条对照“找到了吗”。"])
    print(json.dumps(pub, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
