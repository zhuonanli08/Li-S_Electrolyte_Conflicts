"""step20：每条矛盾的跨论文机制证据（11-08 用户：“可以”——在 313 篇里找出与每条矛盾相关的机制说法，看哪些支持、哪些反对）。

做法：在 313 篇已提取的机制（candidate.json 的 mechanisms，共 7477 条，提取时写的中文摘要）里按关键词筛出与每条矛盾相关的，
Claude 逐条读后归到“立场”（写在下面的 EV 里）。只用提取摘要，没有回原文核对；关键词筛选可能漏掉相关机制。AI 辅助，用户尚未逐项人工确认。
仓库公开：提交的 json/xlsx 只放论文号、机制编号、来源类型、立场和 Claude 写的一句话；机制摘要只写进本机文件“（含原句）”（.gitignore 排除）。
输出：output/机制证据_313篇_2026-11-08/（机制证据.json、机制证据表.xlsx；机制证据（含原句）.xlsx 本机）。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step20_mechanism_evidence.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
from step13_common import write_xlsx

PAPERS = ROOT / "output" / "试跑313篇_2026-11-05" / "papers"
OUT = ROOT / "output" / "机制证据_313篇_2026-11-08"

# 矛盾：编号 → (矛盾是什么, 怎么找到的, 两种立场的名字)
T = {
    "T1": ("多数论文：含氟越多 → Li‖Cu CE 越好（含氟溶剂比例 81%）；P381 不含氟的 DBE 稀释剂反而比含氟 TTE 好（99.4% 对 98.8%），"
           "P371 部分氟化的 F3DEE（90.8%）比不含氟 DEE（95.4%）还差",
           "反例（P381 强、P371 弱），读原文确认",
           {"A": "稀释剂/含氟溶剂自身分解出 LiF，对负极有利（支持多数）",
            "B": "LiF 主要来自阴离子，稀释剂宜稳定不分解，分解有害或不必要（支持反例）",
            "C": "相关但不站队"}),
    "T2": ("通常认为碳酸酯不能用于锂硫；P108 非晶 S/C 正极里碳酸酯 20 圈保持率 94.8%，醚 72.7%",
           "反例（强），读原文确认",
           {"A": "碳酸酯能不能用取决于正极：限域/短链硫/SPAN 走固-固转化，长链多硫化物不出来就不攻击碳酸酯",
            "B": "正极能用碳酸酯时，限制转到锂负极（碳酸酯里锂 CE 低）",
            "C": "相关但不站队"}),
    "T3": ("多数论文：LiNO₃ 越多 → 衰减越慢（69%）；P111 0.5 M 最好、1.0 M 最差（1000 圈 436 对 262 mAh/g）",
           "反例（强）＋剂量系列（协同作用候选 SY01）",
           {"A": "LiNO₃ 在负极持续被消耗、耗尽即失效 → 多加有利",
            "B": "LiNO₃ 在正极低电位（约 1.7 V 以下）不可逆还原、消耗活性硫 → 多加有害",
            "C": "相关但不站队"}),
    "T4": ("P112：不加 LiNO₃ 时盐 1→4 M 使 CE 80.0→95.3%，加了 0.5 M LiNO₃ 后提盐 CE 不再变化（98.1→98.0%）",
           "协同作用（交叉设计，SY02）",
           {"A": "不靠 LiNO₃、靠别的手段（弱溶剂化、含氟、有机 SEI 等）也能稳定负极（间接支持“作用可以重叠/替代”）",
            "B": "LiNO₃ 的作用有独特之处，别的替代不了",
            "C": "相关但不站队"}),
}

# 证据：矛盾 → {论文|机制编号: (立场, Claude 写的一句话)}
EV = {
    "T1": {
        "P049|MC17": ("A", "BTFE 与预锂化石墨反应生成 LiF、形成稳定 SEI（作者推测）"),
        "P096|ME09": ("A", "OFE 与 FSI⁻ 一起还原生成富 LiF SEI"),
        "P123|K18": ("A", "HFE 与锂反应生成 LiF，是富 LiF 的另一来源"),
        "P179|MC10": ("A", "HFE 快速分解形成 LiF 钝化层（作者假设，未直接表征）"),
        "P199|K11": ("A", "HFE 的 LUMO 较低、更易还原成 SEI"),
        "P245|ME10": ("A", "适当稀释使 TFSI⁻、FSI⁻ 和 TTE 都参与富 LiF SEI"),
        "P279|K01": ("A", "局部高浓的 FSI⁻ 与 TTE 的富氟基团共同促成 LiF"),
        "P388|K16": ("A", "FEC 换成不含氟的 EC/PC 后低温锂 CE 下降，氟化共溶剂关键"),
        "P425|K17": ("A", "模拟中 TTE 更易与锂反应，很快分解成均匀富 LiF 膜，利于大电流"),
        "P085|ME07": ("B", "不含氟的 DBE 4 M 液里 FSI⁻ 优先还原，同样得到富 LiF SEI，锂沉积致密"),
        "P217|K16": ("B", "适量 TTE 的作用是让更多阴离子参与 SEI 而提高 LiF；过度稀释反而 LiF 下降（K17）"),
        "P233|K14": ("B", "HFE 还原稳定，封装结构得以保留"),
        "P263|K06": ("B", "氟苯 FB3 比 TTE 的 SEI 更好；TTE 中锂多孔、副反应重（K03）"),
        "P303|K4": ("B", "TFEE 液中阴离子优先还原形成无机 SEI"),
        "P310|K1": ("B", "TTE 外壳还原稳定，减轻多硫化物与锂的副反应"),
        "P313|K3": ("B", "作者排除 HFE 参与 SEI 形成，差异归于溶剂化结构"),
        "P338|MC11": ("B", "LiF 增加来自 LiFSA 还原，HFE 直接分解生成 LiF 不太可能"),
        "P354|K14": ("B", "HFE 比例高时更多 FSI⁻ 配位 Li⁺，其分解形成富 LiF SEI"),
        "P362|K7": ("B", "PC/HFE 中阴离子主导分解，SEI 薄而富 LiF"),
        "P371|K14": ("B", "F4DMB 的 SEI 富含阴离子来源的 LiF/Li₂O"),
        "P381|K004": ("B", "TTE 还原虽给出 LiF，但伴生的有机副产物抵消了好处；DBE 还原更稳定（K003）"),
        "P451|K23": ("B", "DBE 的 LUMO 接近 DME，作者推测与锂兼容（孤立分子计算）"),
        "P149|K33": ("C", "DME 与 TTE 的 LUMO 相近，在锂表面分解倾向相同（孤立分子计算）"),
        "P277|ME037": ("C", "正极侧 Li₂S₂ 会化学进攻 TTE 的 C–F，分解出 LiF（说明 TTE 并不惰性）"),
        "P279|K25": ("C", "LiF 主导的 SEI/CEI 导电性低，DME/TTE 的电荷转移电阻更高"),
    },
    "T2": {
        "P003|K23": ("A", "S@pPAN 放电产物在碳酸酯中不溶，不发生穿梭"),
        "P089|K22": ("A", "超微孔限域使硫和多硫化物不进入碳酸酯，可逆还原要求超微孔限域（K29）"),
        "P097|Z16": ("A", "S@pPAN 走固-固转化能兼容碳酸酯，但残留单质硫生成的长链多硫化物会亲核攻击碳酸酯"),
        "P122|K25": ("A", "没有溶解中间体的固-固过程消除穿梭"),
        "P165|K02": ("A", "微孔碳布限制高阶多硫化物扩散，大孔不行"),
        "P183|MC07": ("A", "固相路径使碳酸酯中可逆循环、消除穿梭"),
        "P187|ME41": ("A", "小分子硫正极限域在碳里，减少对碳酸酯的亲核攻击（转述）"),
        "P221|K23": ("A", "EC 形成的保形 CEI 使碳酸酯体系能稳定 SPAN"),
        "P339|K06": ("A", "致密 CEI 阻隔碳酸酯副反应，支持固-固转化"),
        "P381|K028": ("A", "高容量 SPAN 含活泼单质硫，常规碳酸酯形成不了足够的 CEI（转述）"),
        "P627|K47": ("A", "短链硫限域加上限制电解液接触，促成碳酸酯中的固-固转化；长链多硫化物攻击碳酸酯成膜（K07）"),
        "P279|K21": ("B", "常规碳酸酯 Li-SPAN 容量快速衰减归因于锂负极 CE 低"),
        "P369|K25": ("B", "EC/DMC 的界面稳定性差，Li‖SPAN 极化比 DMMS 大"),
        "P221|K14": ("C", "含 EC 的醚液能稳定 SPAN，但锂可逆性差"),
    },
    "T3": {
        "P039|K35": ("A", "LiNO₃ 每次沉积/剥离都与新鲜锂反应而持续消耗，0.3 M 很快耗尽"),
        "P056|MC21": ("A", "长循环后失效主要归咎于 LiNO₃ 耗尽"),
        "P131|K12": ("A", "LiNO₃ 耗尽后多硫化物重新穿梭，贫液高面容量下更早耗尽（K11）"),
        "P337|K026": ("A", "LiNO₃ 耗尽导致约 25 圈后容量快速下降"),
        "P384|MC19": ("A", "LiNO₃ 耗尽使 CE 从 30 圈起持续下降"),
        "P083|K16": ("A", "LiNO₃ 浓度较高时保护层更有效，自放电更低（作者推测）"),
        "P049|MC02": ("B", "首圈 1.8 V 以下平台来自 LiNO₃ 在正极的还原"),
        "P054|K02": ("B", "约 1.7 V 平台可能来自正极上 LiNO₃ 不可逆还原（作者推测）"),
        "P083|K08": ("B", "LiNO₃ 在正极还原不利于可逆性和容量；含量越高这一过程越明显（K06），高浓度策略受此限制（K32）"),
        "P113|K15": ("B", "过量 LiNO₃ 产生不可逆放电产物，造成放电曲线畸变"),
        "P187|ME18": ("B", "低截止电压使 LiNO₃ 还原分解，过放到 1.7 V 会耗尽 LiNO₃ 并产气（转述）"),
        "P229|K6": ("B", "低于 1.7 V 时 LiNO₃ 在正极不可逆还原成钝化层，可能导致衰减（作者推测）"),
        "P111|H16": ("C", "P111 作者：低浓度破坏 GO 结构，高浓度消耗活性硫并积累非活性硫，0.5 M 是两者的平衡"),
    },
    "T4": {
        "P050|ME004": ("A", "ACN–TTE 不加 LiNO₃ 也接近 100% CE"),
        "P215|K07": ("A", "DEE 液 LiNO₃ 只有约 0.006 M，CE 仍 >99%"),
        "P252|ME10": ("A", "不加 LiNO₃ 时 DIPS 弱溶剂化液 CE 更高、穿梭更小"),
        "P278|K29": ("A", "氟化吡啶促成富 LiF SEI，使不加 LiNO₃ 的高载量贫液循环可行"),
        "P313|K2": ("A", "不加 LiNO₃ 时弱溶剂化抑制多硫化物对锂的副反应"),
        "P377|ME10": ("A", "不加 LiNO₃ 时富有机 SEI 减轻多硫化物与锂的副反应"),
        "P039|K26": ("B", "Li₂O 是 LiNO₃ 体系的关键 SEI 组分，不加 LiNO₃ 时没有（作者推测）"),
        "P139|MEC20": ("B", "LiNO₃ 钝化锂表面，减轻高给体溶剂 DMI 的分解"),
        "P234|K03": ("B", "LiPO₂F₂ 形成的 SEI 保护不如 LiNO₃"),
        "P112|K22": ("C", "P112 作者推测：LiNO₃ 促进 SEI/CEI 形成，高盐抑制多硫化物溶解、减少 LiNO₃ 消耗（两者分工互补）"),
        "P212|ME15": ("C", "高浓醚液里放电到更低电压促进 LiNO₃ 还原、巩固 SEI，有利"),
    },
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mech = {}
    for k in {x.split("|")[0] for t in EV.values() for x in t}:
        c = json.loads((PAPERS / k / "candidate.json").read_text(encoding="utf-8"))
        for m in c.get("mechanisms", []):
            mech[f"{k}|{m['id']}"] = m
    rows, local, out = [], [], {}
    for t, (what, how, sides) in T.items():
        ev = EV[t]
        miss = [x for x in ev if x not in mech]
        if miss:
            raise SystemExit(f"{t} 机制编号没找到：{miss}")
        items = []
        for x, (s, note) in ev.items():
            m = mech[x]
            p, mid = x.split("|")
            items.append({"论文": p, "机制": mid, "来源类型": m.get("source_type"), "立场": s, "立场说明": sides[s], "Claude 一句话": note})
            rows.append([t, p, mid, m.get("source_type"), s, sides[s], note, ""])
            local.append(rows[-1][:-1] + [m.get("summary", ""), ""])
        cnt = {s: sorted({i["论文"] for i in items if i["立场"] == s}) for s in sides}
        out[t] = {"矛盾是什么": what, "怎么找到的": how, "立场": sides,
                  "各立场论文": {f"{s}（{len(v)} 篇）": v for s, v in cnt.items()},
                  "其中只是推测或转述的": Counter(i["立场"] for i in items if i["来源类型"] in ("本文推测", "转述他文或通用说法")),
                  "证据": items}
    (OUT / "机制证据.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=dict), encoding="utf-8")
    head = ["矛盾", "论文", "机制编号", "来源类型", "立场", "立场说明", "Claude 一句话"]
    note = ["每条矛盾在 313 篇已提取机制里的相关说法（step20，11-08）。按关键词筛选后 Claude 逐条归立场；只看提取摘要，未回原文核对，可能有漏。",
            "AI 辅助，用户尚未逐项人工确认。✍ 列留给用户填写。"]
    write_xlsx(OUT / "机制证据表.xlsx", [("机制证据", head + ["✍ 用户意见"], rows),
                                     ("矛盾", ["矛盾", "矛盾是什么", "怎么找到的", "立场 A", "立场 B", "A 的论文", "B 的论文"],
                                      [[t, v["矛盾是什么"], v["怎么找到的"], v["立场"]["A"], v["立场"]["B"],
                                        "、".join(next(p for k, p in v["各立场论文"].items() if k.startswith("A"))),
                                        "、".join(next(p for k, p in v["各立场论文"].items() if k.startswith("B")))] for t, v in out.items()])],
               notes=note)
    write_xlsx(OUT / "机制证据（含原句）.xlsx", [("机制证据", head + ["提取摘要（本机，不提交）", "✍ 用户意见"], local)], notes=note)
    for t, v in out.items():
        print(t, {k: len(p) for k, p in v["各立场论文"].items()}, "推测或转述：", dict(v["其中只是推测或转述的"]))


if __name__ == "__main__":
    main()
