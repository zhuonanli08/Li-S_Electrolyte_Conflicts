# -*- coding: utf-8 -*-
"""
论断式提取表样（2026-10-22 用户与师兄讨论定，方案 §5.7）。

流程：每篇一个 JSON（主存储，大模型以后也按这个格式输出）
      → 本脚本逐条到全文缓存核对原句、自动判"总体"、拼一句话结论
      → 输出 Excel 供人复核（Excel 只是查看用，不回写 JSON）

一条记录 = 同一篇论文、同一组条件下的一对配方（A 新配方 vs B 对照）。
"""
import json
import re
import unicodedata
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "output" / "text_cache"
OUT_DIR = ROOT / "output" / "云端_2026-10-22_论断式提取表样"
JSON_DIR = OUT_DIR / "json"
OUT_FILE = OUT_DIR / "论断式提取表样_S39_S11_S21.xlsx"

# ---------- 1. 电池表现：哪个方向算"变好" ----------
# ↑ 表示数值变大；阻抗、过电位、衰减率、自放电是越小越好
BETTER = {
    "首圈容量": "↑", "库仑效率": "↑", "容量保持率": "↑", "寿命": "↑",
    "倍率容量": "↑", "衰减率": "↓", "阻抗": "↓", "过电位": "↓", "自放电": "↓",
}


def judge(item):
    """返回 '好' / '差' / '平'（差异小）。"""
    if item["方向"] == "差异小":
        return "平"
    return "好" if item["方向"] == BETTER[item["指标"]] else "差"


def overall(perf):
    """总体：全部变好→总体变好；全部变差→总体变差；否则写出哪些好、哪些差。"""
    good = [p["指标"] for p in perf if judge(p) == "好"]
    bad = [p["指标"] for p in perf if judge(p) == "差"]
    if good and not bad:
        return "总体变好"
    if bad and not good:
        return "总体变差"
    return f"变好：{'、'.join(good)}；变差：{'、'.join(bad)}"


# ---------- 2. 原句核对 ----------
def norm(s):
    """统一字符后去掉空白再比较：
    NFKC 把 ﬀ 这类连写字母拆开；去掉 PDF 转文字留下的 \\x00 和私用区字符。"""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[\x00-]", "", s)
    return re.sub(r"\s+", "", s)


_cache = {}


def fulltext(stem, part):
    key = (stem, part)
    if key not in _cache:
        p = CACHE / f"{stem}.{part}.txt"
        if p.exists():
            raw = p.read_text(encoding="utf-8", errors="ignore")
            # 另存一份去掉行尾断词连字符的版本（"de-\ncay" → "decay"），两份都查
            _cache[key] = (norm(raw), norm(re.sub(r"-[ \t]*\n", "", raw)))
        else:
            _cache[key] = None
    return _cache[key]


def check(stem, part, quote):
    """原句可能由多段用 ‖ 拼成，每段都在原文找到才打 ✅。"""
    if not quote:
        return "—"
    text = fulltext(stem, part)
    if text is None:
        return "❌"
    return "✅" if all(any(norm(q) in t for t in text) for q in quote.split("‖")) else "❌"


# ---------- 3. 读 JSON，展开成表格行 ----------
papers = [json.loads(p.read_text(encoding="utf-8"))
          for p in sorted(JSON_DIR.glob("S*.json"))]
solvents = json.loads((JSON_DIR / "溶剂表.json").read_text(encoding="utf-8"))

sentence_rows, detail_rows, review_rows = [], [], []


def add_review(rec_id, stem, item, what):
    """把一处原句放进复核表。"""
    q = item.get("原句", "")
    mark = check(stem, item.get("部分", "main"), q)
    review_rows.append([rec_id, what, q, item.get("位置", ""), mark, ""])
    return mark


def fmt_prop(name, d):
    """溶剂化/溶解度一格的显示：方向（数值；依据；测量体系）。"""
    extra = "；".join(x for x in (d.get("数值"), d.get("依据"), d.get("测量体系")) if x)
    return f"{d['方向']}（{extra}）" if extra else d["方向"]


for paper in papers:
    stem = paper["全文缓存"]
    for r in paper["记录"]:
        rid = r["编号"]
        cond = r["条件"]
        perf = r["电池表现"]
        att = r["作者归因"]

        # 复核表：组成、溶剂化、溶解度、其他性质、条件、表现、归因的原句逐条核对
        add_review(rid, stem, r["组成原句"], "组成")
        for key in ("Li溶剂化", "多硫化物溶解度"):
            if r[key].get("原句"):
                add_review(rid, stem, r[key], key.replace("Li", "Li⁺ "))
        for p in r["其他性质"]:
            if p.get("原句"):
                add_review(rid, stem, p, p["性质"])
        for c in cond["原句"]:
            add_review(rid, stem, c, "条件")
        for p in perf:
            add_review(rid, stem, p, f"表现：{p['指标']}")
        add_review(rid, stem, att, "作者归因")

        # 一格写完的"其他性质"和"电池表现"
        others = "；".join(
            f"{p['性质']}{p['方向']}" + (f"（{p['数值']}）" if p.get("数值") else "")
            for p in r["其他性质"])
        perf_text = "；".join(
            f"{p['指标']}{p['方向']}（{p['取值点']}：{p['数值']}）" for p in perf)
        total = overall(perf)

        # 一句话结论：由字段拼出来，保证和明细一致
        cond_text = "、".join(f"{k} {cond[k]}" for k in
                             ("电池", "倍率", "硫载量", "E/S", "锂厚或N/P", "温度", "LiNO₃"))
        sentence = (
            f"{r['A配方']}，对比 {r['B对照']}（{r['B角色']}）；改变：{r['改变了什么']}。"
            f"Li⁺ 溶剂化{r['Li溶剂化']['方向']}，多硫化物溶解度{r['多硫化物溶解度']['方向']}"
            + (f"（{r['多硫化物溶解度']['数值']}）" if r['多硫化物溶解度'].get('数值') else "")
            + f"。条件：{cond_text}。"
            f"电池表现：{'；'.join(p['指标'] + p['方向'] for p in perf)}。"
            f"总体：{total}。作者归因：{att['概括']}（证据：{att['证据等级']}）。")

        sentence_rows.append([rid, paper["文献"], sentence, total, att["证据等级"], ""])
        detail_rows.append([
            rid, paper["文献"], r["A配方"], r["B对照"], r["B角色"], r["改变了什么"],
            fmt_prop("Li⁺ 溶剂化", r["Li溶剂化"]), fmt_prop("多硫化物溶解度", r["多硫化物溶解度"]),
            others, cond["电池"], cond["倍率"], cond["硫载量"], cond["E/S"], cond["锂厚或N/P"],
            cond["温度"], cond["LiNO₃"], perf_text, total,
            att["概括"], att["证据等级"], att["依据"], "；".join(r.get("备注", []))])

# 溶剂表：原句同样核对
solvent_rows = []
for s in solvents["溶剂"]:
    mark = check(s["全文缓存"], s["部分"], s["原句"]) if s["原句"] else "—"
    if mark == "✅" and s["核验说明"].startswith("⚠️"):
        mark = "⚠️"  # 原句找到了，但数值本身有疑问
    solvent_rows.append([s["简称"], s["全称"], s["DN"], s["介电常数"], s["来源"], s["原句"],
                         mark, s["核验说明"]])

# ---------- 4. 说明与词表 ----------
guide = [
    ["这是什么", "按 10-22 与师兄讨论后定的“论断式提取”格式，用 S39、S11、S21 三篇已精读论文做的表样。AI 辅助提取与核对，用户尚未逐项人工确认。"],
    ["一行是什么", "同一篇论文、同一组条件下的一对配方：A 新配方 vs B 对照。一篇论文可以有多行。"],
    ["主存储", "json/ 文件夹里每篇一个 JSON，是正式数据；本 Excel 由 scripts/step6c_claim_records_sample.py 从 JSON 生成，只用来看和复核。改数据改 JSON，再重新生成。"],
    ["怎么看", "先看“一句话结论”；要看细节看“明细”；要核原文看“复核表”（每句原句都由代码到全文缓存里查过）。"],
    ["溶剂化分两项", "Li⁺ 溶剂化 和 多硫化物溶解度 分开记，都是相对 B 对照：更强/相当/更弱、更高/相当/更低；论文没测就写未报告。"],
    ["总体怎么来", "由程序按“电池表现”自动判：全部变好→总体变好；全部变差→总体变差；否则写出哪些变好、哪些变差。"],
    ["证据等级", "直接：在电池里直接测到作者说的那个东西；间接：测了相关的东西，或在简化体系里测；只是说法：没有对应测量。"],
    ["DN、介电常数", "是溶剂本身的性质，不逐篇提取，放在“溶剂表”，每种溶剂一行并注明来源。"],
    ["复核", "带 ✍ 的列由用户填写，AI 不改。"],
]
vocab = [
    ["电池表现指标", "首圈容量、库仑效率、容量保持率、寿命、衰减率、阻抗、过电位、倍率容量、自放电", "↑/↓ 表示数值变大/变小；阻抗、过电位、衰减率、自放电越小越好"],
    ["溶剂化方向", "更强 / 相当 / 更弱 / 未报告", "Li⁺ 溶剂化"],
    ["溶解度方向", "更高 / 相当 / 更低 / 未报告", "多硫化物溶解度"],
    ["其他性质", "离子电导率、黏度、离子迁移数（记测法）", "↑ / ↓ / 未报告 / 仅图未读"],
    ["条件（6 项＋电池）", "电池（电极组合＋形式）、倍率、硫载量、E/S、锂厚或 N/P、温度、LiNO₃", "未写的记未报告"],
    ["证据等级", "直接 / 间接 / 只是说法", "附“依据”说明为什么"],
    ["核验", "✅ 原句找到 / ⚠️ 原句找到但内容有疑问 / ❌ 找不到 / — 无原句", ""],
]

# ---------- 5. 写 Excel ----------
HEAD_FILL = PatternFill("solid", fgColor="DDEBF7")
USER_FILL = PatternFill("solid", fgColor="FFF2CC")
WIDE = {"一句话结论": 110, "原句": 60, "电池表现": 50, "作者归因": 45, "依据": 40, "备注": 40,
        "A配方": 32, "B对照": 32, "Li⁺ 溶剂化": 36, "多硫化物溶解度": 36, "其他性质": 30,
        "总体": 26, "说明": 100, "核验说明": 45, "可选写法": 50, "含义": 40, "全称": 30}


def add_sheet(wb, title, head, rows):
    ws = wb.create_sheet(title)
    ws.append(head)
    for row in rows:
        ws.append(row)
    for i, h in enumerate(head, start=1):
        c = ws.cell(row=1, column=i)
        c.font = Font(bold=True)
        c.fill = USER_FILL if "✍" in h else HEAD_FILL
        ws.column_dimensions[get_column_letter(i)].width = WIDE.get(h, 14)
        for (cell,) in ws.iter_rows(min_row=2, min_col=i, max_col=i):
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            if "✍" in h:
                cell.fill = USER_FILL
    ws.freeze_panes = "B2"


wb = Workbook()
wb.remove(wb.active)
add_sheet(wb, "说明", ["项目", "说明"], guide)
add_sheet(wb, "一句话结论", ["编号", "文献", "一句话结论", "总体", "证据等级", "复核 ✍"], sentence_rows)
add_sheet(wb, "明细", ["编号", "文献", "A配方", "B对照", "B角色", "改变了什么", "Li⁺ 溶剂化",
                     "多硫化物溶解度", "其他性质", "电池", "倍率", "硫载量", "E/S", "锂厚或N/P",
                     "温度", "LiNO₃", "电池表现", "总体", "作者归因", "证据等级", "依据", "备注"],
          detail_rows)
add_sheet(wb, "复核表", ["编号", "项目", "原句", "位置", "核验", "复核 ✍"], review_rows)
add_sheet(wb, "溶剂表", ["简称", "全称", "DN", "介电常数", "来源", "原句", "核验", "核验说明"],
          solvent_rows)
add_sheet(wb, "词表", ["项目", "可选写法", "含义"], vocab)
wb.save(OUT_FILE)

marks = [r[4] for r in review_rows]
print("写出：", OUT_FILE.relative_to(ROOT))
print("记录数：", len(sentence_rows), " 原句数：", len(review_rows),
      " ✅", marks.count("✅"), " ❌", marks.count("❌"))
for r in review_rows:
    if r[4] == "❌":
        print("  找不到：", r[0], r[1], r[2][:80])
for s in sentence_rows:
    print(s[0], "→", s[3])
