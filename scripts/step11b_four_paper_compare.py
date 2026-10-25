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


def wrap_n(t, n):
    import textwrap
    return "\n".join(textwrap.wrap(t, n))


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
# 颜色只表示“哪一侧的短板”；过程大类是行，测量写成文字
SIDE_COL = {0: "#553c9a", 1: "#2c7a7b"}          # 0 = 强溶剂化一侧，1 = 弱溶剂化一侧
SIDE_NAME = {0: "强溶剂化一侧的短板", 1: "弱溶剂化一侧的短板"}
WHERE = {"Li‖S": "Li‖S\u00a0电池", "简化": "简化体系/半电池"}     # 不换行空格：别在“Li‖S 电池”中间断行


def figB():
    cl = [c for c in A.claims() if not (c["p"] == "S33" and c["id"] == "M2")]   # ETFE 自身腐蚀锂，不属溶剂化强弱
    rows = [f"{pr}" for pr in A.PROCS]
    heights = [2.3, 2.0, 2.3, 2.0]
    fig, ax, spans = frame("图B  每个过程是哪一侧的短板？四篇怎么说、测了没有（Q2 机制）", rows, heights)
    said = {}
    for c in cl:
        if c["eff"] == "same":
            continue
        side = 0 if c["eff"] == "good" else 1       # 变弱后变好 → 强的一侧的短板
        e = said.setdefault((c["p"], c["proc"], side), {"own": False, "ids": []})
        e["own"] |= c["own"]
        e["ids"].append(c["id"])
    for i, pr in enumerate(A.PROCS):
        y0, y1 = spans[i]
        hgt = y1 - y0
        for j, p in enumerate(PAPERS):
            x = col_x(j) + 0.008
            w = W_PAPER - 0.016
            chips = [(side, said[(p, pr, side)]) for side in (0, 1) if (p, pr, side) in said]
            ch = hgt * 0.17
            yy = y1 - hgt * 0.08
            if not chips:
                ax.text(x + w / 2, yy - ch / 2, "没说", ha="center", va="center", fontsize=8.5, color="#a0aec0")
                yy -= ch
            for side, v in chips:
                yy -= ch
                lab = f"{SIDE_NAME[side]}  {'、'.join(v['ids'])}" + ("" if v["own"] else "（推测）")
                chip(ax, x, yy, w, ch * 0.88, lab, SIDE_COL[side], ls="-" if v["own"] else "--",
                     tc="white" if v["own"] else SIDE_COL[side], fs=7.8) if v["own"] else \
                    chip(ax, x, yy, w, ch * 0.88, lab, "white", ec=SIDE_COL[side], ls="--", tc=SIDE_COL[side], fs=7.8)
                yy -= ch * 0.12
            ms = A.MEASURED.get((p, pr), [])
            if ms:
                lines = [("✓\u00a0定量\u00a0" if mass else "") + f"{WHERE[where]}｜{what}" for where, what, mass in ms]
                txt = "测：\n" + "\n".join(wrap_n(t, 19) for t in lines)
                mass_any = any(m for _, _, m in ms)
            else:
                txt = "测：无对应测量" if chips else ""
                mass_any = False
            ax.text(x + 0.004, yy - hgt * 0.04, txt, ha="left", va="top", fontsize=7.3, linespacing=1.25,
                    color="#22543d" if mass_any else "#4a5568", weight="bold" if mass_any else "normal")
    notes = [
        ("弱的一侧：4 篇都说 → 共识候选\n强的一侧也有 2 篇（S21、S39）\n→ 正极两侧都差，与“最优在中间”一致\n"
         "⚠ 候选矛盾：S11 vs S39 M3 都说多硫化物\n溶剂化变弱，S11 说正极变差、S39 说不变\n——测法不同（恒电位 Li₂S 沉积 vs 溶液正极 GITT）\n"
         "测法各不相同；S33 没有对应测量", "#2c7a7b"),
        ("强的一侧：2 篇（S11、S21）\n两篇都在不含 LiNO₃ 的 Li‖S 电池里测\n（穿梭电流、自放电）\n"
         "→ 含 LiNO₃ 时穿梭是不是短板，这 4 篇回答不了", "#553c9a"),
        ("强的一侧：4 篇都说 → 共识候选\n但在失效电池里定量剩余活性锂的只有 S33\n"
         "其余是 XPS、对称电池、Li‖Cu CE、EIS\n→ 常说少测", "#553c9a"),
        ("强的一侧：S33 定量测过（QNMR + 补液恢复）\nS39 只是推测；S11、S21 没说", "#553c9a"),
    ]
    for i, (t, c) in enumerate(notes):
        summary(ax, spans[i], t, color=c, bold=False)
    # 图例
    lx = W_LAB
    fig.text(0.01, 0.06, "怎么看：每行一个过程，往右扫比四篇。", fontsize=8.8, color="#2d3748")
    for k, (side, name) in enumerate(SIDE_NAME.items()):
        fig.patches.append(FancyBboxPatch((0.20 + k * 0.30, 0.052), 0.015, 0.018, boxstyle="round,pad=0.001",
                                          fc=SIDE_COL[side], ec=SIDE_COL[side], transform=fig.transFigure, figure=fig))
        fig.text(0.218 + k * 0.30, 0.061, name + ("（溶剂化变弱后这个过程变好）" if side == 0 else "（变弱后变差）"),
                 fontsize=8.6, va="center", color=SIDE_COL[side])
    fig.text(0.01, 0.035, "实心 = 本文结论，虚线框 = 只有推测/转述原句；编号是该篇的机制说法。“测”= 该篇对这个过程做了什么测量，"
             "绿色加粗“✓ 定量”= 在失效电池里定量了物质收支。把测量对应到过程是 Claude 的归类（待确认）。S33 M2（ETFE 自身腐蚀锂）不属溶剂化强弱，未列。",
             fontsize=8.4, color="#2d3748")
    fig.text(0.01, 0.01, FOOT, fontsize=7.5, color="#718096")
    save(fig, "图B_机制_四篇横向对比")


if __name__ == "__main__":
    import logging
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    figA()
    figB()
