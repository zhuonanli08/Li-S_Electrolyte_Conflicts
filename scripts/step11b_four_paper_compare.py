"""
step11b：四篇表样（S11、S21、S33、S39）横向对照图——“同一个问题，四篇怎么答”。

每行一个问题，四篇各一列，最右一列写跨篇怎么读；颜色只表示方向。
数据复用 step11a 的读取与换算（v4 表样 Excel“明细-配方 / 明细-方向”和四篇 JSON），不新增提取。
输出：output/云端_2026-10-25_组会图_四篇横向对比/
四篇只演示形式，不是结论；AI 辅助提取，用户未逐项人工确认。
"""
import importlib.util
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("s11a", ROOT / "scripts" / "step11a_cross_paper_figs_v4.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

# ---------- 参数 ----------
OUT = ROOT / "output" / "云端_2026-10-25_组会图_四篇横向对比"
PAPERS = A.PAPERS
COL = {"good": "#2b6cb0", "bad": "#dd6b20", "same": "#a0aec0", "na": "#cbd5e0"}
ARROW = {"good": "↑ 变好", "bad": "↓ 变坏", "same": "≈ 差异小", "na": "× 不判"}
PROC_COL = {"正极反应": "#805ad5", "多硫化物穿梭": "#d69e2e", "负极锂": "#2f855a", "电解液消耗": "#c53030"}
W_LAB, W_PAPER, W_SUM = 0.15, 0.155, 0.23     # 左标签列、每篇一列、右汇总列（占图宽比例）
DPI = 200
FOOT = A.FOOT
HEAD = {   # 列头：体系、对照类型、尺子范围（尺子值来自 Excel，见 step11a）
    "S11": "S11\nDOL/DME + TTE 稀释剂\n对照：常规醚，含 LiNO₃\n尺子 12.0 → 8.4",
    "S21": "S21\nDME/THF + 邻二甲苯稀释剂\n对照：自配，不含 LiNO₃\n尺子 9.8 → 4.0",
    "S33": "S33\nDME + 氟化醚共溶剂\n对照：DME 单溶剂，含 LiNO₃\n尺子：放不上",
    "S39": "S39\nDOL + DME / F4DEE / TTE\n对照：常规醚，含 LiNO₃\n尺子 12.0 → 11.4（最优放不上）",
}

plt.rcParams["font.family"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["svg.fonttype"] = "none"


def col_x(j):
    """第 j 篇所在列的左边界。"""
    return W_LAB + j * W_PAPER


LIGHT = {"#a0aec0", "#cbd5e0"}


def chip(ax, x, y, w, h, text, fc, ec=None, ls="-", tc="white", fs=8):
    if fc in LIGHT and tc == "white":
        tc = "#1a202c"      # 浅色底用深色字
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.002,rounding_size=0.006",
                                fc=fc, ec=ec or fc, ls=ls, lw=1.2, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, zorder=3)


def frame(title, rows, heights, n_head=1.6):
    """画表格框架，返回 (fig, ax, 每行的 (y下, y上))。"""
    fig = plt.figure(figsize=(16, 2.2 + 0.62 * sum(heights)))
    ax = fig.add_axes([0.01, 0.07, 0.98, 0.80])
    ax.axis("off")
    total = sum(heights) + n_head
    u = 1 / total
    top = 1 - n_head * u
    for j, p in enumerate(PAPERS):
        ax.text(col_x(j) + W_PAPER / 2, 1 - n_head * u / 2, HEAD[p], ha="center", va="center", fontsize=8.6,
                linespacing=1.35, color="#2d3748")
    ax.text(W_LAB + 4 * W_PAPER + W_SUM / 2, 1 - n_head * u / 2, "跨篇怎么读", ha="center", va="center", fontsize=11, weight="bold")
    spans = []
    for i, (lab, hgt) in enumerate(zip(rows, heights)):
        y1, y0 = top, top - hgt * u
        ax.add_patch(Rectangle((0, y0), 1, y1 - y0, color="#f7fafc" if i % 2 == 0 else "white", zorder=0))
        ax.text(0.005, (y0 + y1) / 2, lab, va="center", fontsize=9.6, color="#1a202c", linespacing=1.3)
        spans.append((y0, y1))
        top = y0
    for j in range(5):
        ax.plot([col_x(j), col_x(j)], [top, 1 - n_head * u], color="#e2e8f0", lw=1)
    ax.plot([0, 1], [1 - n_head * u, 1 - n_head * u], color="#718096", lw=1.2)
    fig.text(0.01, 0.955, title, fontsize=14, weight="bold")
    return fig, ax, spans


def stack_chips(ax, j, span, items, fs=7.8):
    """items: [(文字, 底色, 边框线型)]，在第 j 列的格子里竖着排。"""
    y0, y1 = span
    if not items:
        ax.text(col_x(j) + W_PAPER / 2, (y0 + y1) / 2, "—", ha="center", va="center", color="#cbd5e0", fontsize=10)
        return
    n = len(items)
    pad = (y1 - y0) * 0.08
    h = min((y1 - y0 - 2 * pad) / n * 0.82, 0.05)
    gap = ((y1 - y0 - 2 * pad) - n * h) / max(n - 1, 1) if n > 1 else 0
    ytop = y1 - pad - (0 if n > 1 else ((y1 - y0 - 2 * pad) - h) / 2)
    for k, (t, fc, ls) in enumerate(items):
        y = ytop - h - k * (h + gap)
        hollow = ls != "-"
        chip(ax, col_x(j) + 0.008, y, W_PAPER - 0.016, h, t, "white" if hollow else fc, ec=fc, ls=ls,
             tc=fc if hollow else "white", fs=fs)


def summary(ax, span, text, color="#2d3748", bold=False):
    y0, y1 = span
    ax.text(W_LAB + 4 * W_PAPER + 0.008, (y0 + y1) / 2, text, ha="left", va="center", fontsize=8.4,
            color=color, weight="bold" if bold else "normal", linespacing=1.4)


def wrap14(t):
    import textwrap
    return "\n".join(textwrap.wrap(t, 15))


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.png", dpi=DPI, bbox_inches="tight")
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)
    print("写出", OUT / f"{name}.png")


# ---------- 图A 表现：作者最优 vs 对照 ----------
def test_label(p, tcode, e):
    t = next(t for t in A.J[p]["测试"] if t["编号"] == tcode)
    name = t["名称"]
    if e["es"] is None:
        cell = name.split()[0] if "‖" in name.split()[0] else name[:8]
        base = cell
    else:
        base = f"E/S {e['es']:g}"
        if "软包" in name:
            base += " 软包"
        if "GITT" in name:
            base += " GITT"
    if not e["lino3"]:
        base += " 无LiNO₃"
    if e["fig"]:
        base += " 读图"
    return base


def figA():
    pts = A.fig2_points()
    cats = A.CATS
    rows = ["对照是谁", "最优档在梯度哪里"] + cats
    heights = [0.9, 1.0] + [max(1.0, 0.55 * max(sum(1 for k in pts if k[0] == p and k[2] == c) for p in PAPERS)) for c in cats]
    fig, ax, spans = frame("图A  作者最优配方 vs 对照：同一个问题，四篇怎么答（Q1 表现）", rows, heights)
    # 对照
    ctl = {"S11": ("常规醚 DOL/DME\n含 LiNO₃ 2 wt%", "#4a5568"), "S21": ("自配 DME/THF\n不含 LiNO₃（偏弱）", "#c05621"),
           "S33": ("DME 单溶剂\n含 LiNO₃", "#4a5568"), "S39": ("常规醚 DOL/DME\n含 LiNO₃ 0.2 M", "#4a5568")}
    for j, p in enumerate(PAPERS):
        t, c = ctl[p]
        ax.text(col_x(j) + W_PAPER / 2, sum(spans[0]) / 2, t, ha="center", va="center", fontsize=8.2, color=c, linespacing=1.3)
    summary(ax, spans[0], "3 篇对照含 LiNO₃；S21 对照不含\n→ 跨篇比较时 S21 单独看")
    # 梯度最优位置：点串，星 = 作者最优
    for j, p in enumerate(PAPERS):
        order = A.gradient_order(p)
        y0, y1 = spans[1]
        yc = (y0 + y1) / 2 + 0.006
        xs = [col_x(j) + 0.02 + k * (W_PAPER - 0.04) / (len(order) - 1) for k in range(len(order))]
        ax.plot([xs[0], xs[-1]], [yc, yc], color="#cbd5e0", lw=2, zorder=1)
        for x, code in zip(xs, order):
            opt = code == A.OPTIMUM[p]
            ax.plot(x, yc, marker="*" if opt else "o", ms=14 if opt else 6, mfc="#e53e3e" if opt else "white",
                    mec="#2d3748", zorder=3)
            ax.text(x, yc - 0.018, code, ha="center", va="top", fontsize=6.6, color="#4a5568")
        ax.text(col_x(j) + 0.01, y1 - 0.006, "强", fontsize=7, va="top", color="#718096")
        ax.text(col_x(j) + W_PAPER - 0.01, y1 - 0.006, "弱", fontsize=7, va="top", ha="right", color="#718096")
    summary(ax, spans[1], "4 篇的最优都不在最弱一端\n（S33 在第 4/5 档）→ 与“适中最好”一致", bold=True)
    # 各指标
    notes = {
        "首圈容量 / 能量": "含 LiNO₃ 的 3 篇：没有一次变好\n唯一变好的是 S21（不含 LiNO₃）",
        "倍率容量": "S11 变坏（含 LiNO₃）\nS21 变好（不含 LiNO₃）",
        "过电位": "S33、S39 变坏（含 LiNO₃）\nS21 变好（不含 LiNO₃）",
    }
    for i, c in enumerate(cats):
        span = spans[2 + i]
        cnt = {"good": 0, "bad": 0, "same": 0, "na": 0}
        papers = set()
        for j, p in enumerate(PAPERS):
            items = []
            for (pp, tcode, cc), e in sorted(pts.items(), key=lambda kv: int(kv[0][1][1:])):
                if pp != p or cc != c:
                    continue
                d = "mix" if len(e["dirs"]) > 1 else next(iter(e["dirs"]))
                cnt[d] = cnt.get(d, 0) + 1
                papers.add(p)
                items.append((f"{ARROW[d]}  {tcode} {test_label(p, tcode, e)}", COL[d], "-" if e["lino3"] else "--"))
            stack_chips(ax, j, span, items, fs=7.4)
        auto = f"{len(papers)} 篇 {sum(cnt.values())} 个测试：变好 {cnt['good']}、变坏 {cnt['bad']}" + \
               (f"、差异小 {cnt['same']}" if cnt["same"] else "") + (f"、不判 {cnt['na']}" if cnt["na"] else "")
        txt = (notes[c] + "\n" + auto) if c in notes else auto
        summary(ax, span, txt, color="#c05621" if c in notes else "#2d3748", bold=c in notes)
    fig.text(0.01, 0.035, "怎么看：往右扫一行比四篇。蓝 = 作者最优比对照变好，橙 = 变坏，灰 = 差异小或不判（v4 规则）；虚线框 = 该测试不含 LiNO₃。"
             "格子里是该篇的测试编号和条件（E/S 单位 µL mg⁻¹）。\n读出来的苗头：寿命、库仑效率、穿梭、锂负极几行没有橙（变坏）；首圈容量、倍率、过电位三行，含 LiNO₃ 的测试没有蓝——"
             "“打破权衡”只出现在对照不含 LiNO₃ 的 S21。S11 T5 为软包 medium vs E0（medium 对应哪档原文未写）。",
             fontsize=8.6, color="#2d3748", linespacing=1.5)
    fig.text(0.01, 0.008, FOOT, fontsize=7.5, color="#718096")
    save(fig, "图A_表现_四篇横向对比")


# ---------- 图B 机制 ----------
def figB():
    cl = [c for c in A.claims() if not (c["p"] == "S33" and c["id"] == "M2")]   # ETFE 自身腐蚀锂，不属溶剂化强弱
    rows = ["强溶剂化一侧的短板\n（变弱后这个过程变好）", "弱溶剂化一侧的短板\n（变弱后这个过程变差）",
            "溶剂化变弱时\n正极反应怎样", "负极锂短板\n是怎么测的", "电解液消耗\n测了吗", "正极反应\n是怎么测的"]
    heights = [1.9, 1.1, 2.2, 1.5, 1.2, 1.5]
    fig, ax, spans = frame("图B  两侧的限制机制：同一个问题，四篇怎么答（Q2 机制）", rows, heights)
    side_items = {}
    for c in cl:
        if c["eff"] == "same":
            continue
        side = 0 if c["eff"] == "good" else 1
        lst = side_items.setdefault((side, c["p"]), {})
        e = lst.setdefault(c["proc"], {"own": False, "ids": []})
        e["own"] |= c["own"]
        e["ids"].append(c["id"])
    for side in (0, 1):
        for j, p in enumerate(PAPERS):
            d = side_items.get((side, p), {})
            items = [(f"{pr}  {'、'.join(v['ids'])}" + ("" if v["own"] else "（推测）"), PROC_COL[pr], "-" if v["own"] else "--")
                     for pr, v in sorted(d.items(), key=lambda kv: A.PROCS.index(kv[0]))]
            stack_chips(ax, j, spans[side], items)
    summary(ax, spans[0], "负极锂：4 篇都说 → 共识候选\n（但多数没在失效电池里定量，见第 4 行）", color="#2f855a", bold=True)
    summary(ax, spans[1], "正极反应：4 篇都说 → 共识候选\n正极在两侧都出现 → 与“最优在中间”一致", color="#805ad5", bold=True)
    # 正极反应方向：只取过程 = 正极反应 的说法，写明是哪种溶剂化、哪一段
    for j, p in enumerate(PAPERS):
        merged = {}
        for c in cl:
            if c["p"] != p or c["proc"] != "正极反应":
                continue
            kind = c["kind"].replace("其他（离子电导率）", "电导率下降").replace("Li⁺ + 多硫化物溶剂化", "Li⁺+多硫化物")
            e = merged.setdefault((c["strong"], c["weak"], kind, c["eff"]), {"ids": [], "own": False})
            e["ids"].append(c["id"])
            e["own"] |= c["own"]
        items = [(f"{ARROW[eff][:1]} {st}→{wk}｜{kind}  {'、'.join(v['ids'])}", COL[eff], "-" if v["own"] else "--")
                 for (st, wk, kind, eff), v in merged.items()]
        stack_chips(ax, j, spans[2], items, fs=7.2)
    summary(ax, spans[2], "S21、S39：先变好、再变差（过弱时）\nS11：只说变差；S33：只在最弱端变差\n"
                          "⚠ S11 vs S39 M3：同为多硫化物溶剂化，一个变差、\n一个不变 → 候选矛盾，测法不同（见第 6 行）",
            color="#c53030", bold=True)
    # 测量（Claude 的归类，待确认；来自 step11a 的 MEASURED）
    def meas_items(pr):
        out = {}
        for p in PAPERS:
            said = any(c["p"] == p and c["proc"] == pr for c in cl if c["eff"] != "same")
            ms = A.MEASURED.get((p, pr), [])
            items = []
            for where, what, mass in ms:
                fc = "#2f855a" if mass else ("#4a5568" if where == "Li‖S" else "#a0aec0")
                items.append((wrap14(("✓ 定量 " if mass else "") + what), fc, "-"))
            if said and not ms:
                items.append(("说了，但没有对应测量", "#a0aec0", "--"))
            out[p] = items
        return out
    for row, pr in ((3, "负极锂"), (4, "电解液消耗"), (5, "正极反应")):
        mi = meas_items(pr)
        for j, p in enumerate(PAPERS):
            stack_chips(ax, j, spans[row], mi[p], fs=7.2)
    summary(ax, spans[3], "4 篇测法各不相同；在失效电池里\n定量剩余活性锂的只有 S33 → 常说少测", color="#c53030", bold=True)
    summary(ax, spans[4], "只有 S33 测过（QNMR + 补液恢复）\nS39 只是推测；S11、S21 没说")
    summary(ax, spans[5], "测法 4 种各不相同（恒电位 Li₂S 沉积、\n平台比、GITT）→ 正极这条要先统一测法再比")
    fig.text(0.01, 0.035, "怎么看：往右扫一行比四篇。前两行颜色 = 过程大类（紫 正极反应、黄 穿梭、绿 负极锂、红 电解液消耗），虚线框 = 只有推测/转述原句；"
             "第 3 行蓝 = 变弱后正极变好、橙 = 变差、灰 = 不变，“A→B”是从哪档到哪档。\n后三行：绿 = 在失效电池里定量收支，深灰 = 在 Li‖S 电池里测，浅灰 = 简化体系或半电池。"
             "把测量对应到过程大类是 Claude 的归类（待确认）。S33 M2（ETFE 自身腐蚀锂）不属溶剂化强弱，未列。",
             fontsize=8.6, color="#2d3748", linespacing=1.5)
    fig.text(0.01, 0.008, FOOT, fontsize=7.5, color="#718096")
    save(fig, "图B_机制_四篇横向对比")


if __name__ == "__main__":
    import logging
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    figA()
    figB()
