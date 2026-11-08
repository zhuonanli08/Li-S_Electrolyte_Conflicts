"""组会第 16–18 页与网站 07 页：三个无定论问题各一张图，左边数据、右边机制示意（11-08 用户同意按 zy 意见改：用图、少字、更有科学意味）。图英文。
11-08 晚第二版（用户：“线很杂乱，不能直观传达意思”“一定要清晰，同时能准确传达那个问题，不是为了展示数据而画一堆线”）：

问题 1（fig_q1）：左 = 两篇反例各一条线——P371 同一骨架（1,2-二乙氧基乙烷）逐步加氟 DEE→F3/F4/F5/F6DEE 的 Li‖Cu CE（部分氟化最差），
  P381 同一 LiFSI–TEP 体系里稀释剂 DBE（不含氟）对 TTE；多数结论（每个比较都是含氟多 CE 高的论文数）写在标题里。右 = LiF 两条来源示意（step20：9 篇 vs 13 篇）。
问题 2（fig_q2）：左 = 只改 LiNO₃ 用量、至少 3 个浓度的剂量系列（P111、P139），纵轴 = 相对本篇最低浓度衰减慢了几倍；≤ 0.5 M 的多数结论写在标题；
  下方 = 403 个配方的 LiNO₃ 用量分布。右 = 概念示意三条线（负极收益在 0 上方、正极代价在 0 下方、两者之和与最佳点），条件变化只画最佳点的位置。
问题 3（fig_q3）：左 = P112 四个电解液每圈损失的锂（100 − CE）；中 = 313 篇里“盐 ≤/> 1 M × 有/无 LiNO₃”四种组合的配方数（方块面积）；
  右 = 两种解释示意：替代（同一靶点）还是互补（不同靶点，高盐减少多硫化物从而少耗 LiNO₃）。
数字全部从结果文件读。输出 output/组会图_2026-11-08/fig_q1.png、fig_q2.png、fig_q3.png（300 dpi）并复制到网站 图/；数值写 组会图数据.json。
初步；读原文与立场判断为 AI 辅助，用户尚未逐项人工确认。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/fig_questions.py
"""
import json
import math
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "step15_meta"))
import step17_tension_trial as T
import step16_pairwise_statements as P16

O = ROOT / "output"
OUT = O / "组会图_2026-11-08"
SITE = O / "表述与矛盾试跑_F版30篇_2026-11-04" / "网站" / "图"
PAIRS = O / "两两比较表述_313篇_v2_2026-11-07" / "比较表述.json"
JUD = [O / "张力判定_313篇_2026-11-07" / "判定_v2.json", O / "张力判定_313篇_2026-11-07" / "判定_v2_弱.json"]
EV = O / "机制证据_313篇_2026-11-08" / "机制证据.json"
VEC = O / "说法地图_313篇_2026-11-08" / "说法向量.json"
MEAS = O / "meta共同准备_313篇_v2_2026-11-06" / "测量表.json"
INK, INK2, MUTED, BG = "#0b0b0b", "#52514e", "#8a8984", "#ffffff"
BLUE, ORANGE, RED, GREY, LIGHT = "#2a78d6", "#eb6834", "#d03b3b", "#b8b7b2", "#e4e3de"
plt.rcParams.update({"font.family": ["Arial", "DejaVu Sans"], "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False})
DATA = {}


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def results():
    out = {}
    for f in JUD:
        for r in load(f):
            for p in r["相反的对"]:
                out[p.split()[0]] = r["真假"]
    return out


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / name
    fig.savefig(f, dpi=300, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    SITE.mkdir(parents=True, exist_ok=True)
    shutil.copy(f, SITE / name)
    print(f)


def box(ax, x, y, w, h, text, fc, ec, fs=9.5, color=INK, weight="normal", ha="center"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.25", fc=fc, ec=ec, lw=1.2, clip_on=False))
    ax.text(x + (w / 2 if ha == "center" else 0.25), y + h / 2, text, ha=ha, va="center", fontsize=fs, color=color, fontweight=weight, linespacing=1.35)


def arrow(ax, p0, p1, color, lw=1.6, style="-|>", ms=12, ls="-"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, linestyle=ls, shrinkA=0, shrinkB=0))


# ---------------- 问题 1 ----------------
# 11-08 晚用户：“线很杂乱，不能直观传达意思……不是为了展示数据而画一堆线” → 左边只画两篇反例各自的一条线（P371 同一骨架逐步加氟、P381 换稀释剂），
# 多数结论（多数论文“含氟越多 CE 越高”）只写成一句话，不再画 104 根箭头。
P371_SERIES = [("DEE", 0), ("F3DEE", 3), ("F4DEE", 4), ("F5DEE", 5), ("F6DEE", 6)]  # 1,2-二乙氧基乙烷骨架，两端逐步加氟；P371 测试 Taur（Aurbach 法，60 °C）


def q1():
    R, res = load(PAIRS), results()
    ev = load(EV)["T1"]
    side = {k[0]: v for k, v in ev["各立场论文"].items()}
    yrs = defaultdict(list)
    for c in load(VEC)["说法"]:
        if c["问题"] == "T1" and c["立场"] in "AB":
            yrs[c["立场"]].append(c["年份"])
    per, ce = defaultdict(list), {}
    for r in R:
        if r["类别"] != "LiCu_CE" or r["比较类型"] != T.SAME:
            continue
        for sd, k in (("A", "值A"), ("B", "值B")):
            ce[(r["论文"], r[sd]["测试"], r[sd]["配方"])] = r["性能"][k]
        x = next((y for y in r["描述符"] if y["描述符"] == "fat"), None)
        if x and x["A"] != x["B"]:
            per[r["论文"]].append(T.effect(r) * (1 if x["A"] > x["B"] else -1))
    n_pap, all_up = len(per), sum(all(e > T.T for e in v) for v in per.values())
    y371 = [ce[("P371", "Taur", n)] for n, _ in P371_SERIES]
    y381 = [ce[("P381", "T01", "F01")], ce[("P381", "T01", "F02")]]  # TD = LiFSI–TEP + DBE；TT = LiFSI–TEP + TTE
    PURPLE = "#6250d6"
    fig = plt.figure(figsize=(13.5, 5.8))
    ax = fig.add_axes([0.06, 0.15, 0.40, 0.64])
    xs = [f for _, f in P371_SERIES]
    ax.plot(xs, y371, "-o", color=RED, lw=2.6, ms=9, zorder=3)
    for (n, f), y in zip(P371_SERIES, y371):
        nm = n + ("*" if n == "F6DEE" else "")
        if n == "F4DEE":  # 左边是从 F3DEE 上来的线，标签放左侧
            ax.text(f - 0.18, y + 0.25, f"{nm}  {y:.1f}", ha="right", va="center", fontsize=9.5, color=RED)
        else:
            ax.text(f + (-0.25 if f == 0 else 0), y - 0.45, f"{nm}\n{y:.1f}", ha="right" if f == 0 else "center", va="top", fontsize=9.5, color=RED, linespacing=1.2)
    ax.plot([0, 8], y381, "-o", color=PURPLE, lw=2.6, ms=9, zorder=3)
    ax.text(0, y381[0] + 0.3, f"DBE (no F)  {y381[0]:.1f}", ha="left", va="bottom", fontsize=9.5, color=PURPLE)
    ax.text(8, y381[1] + 0.3, f"TTE  {y381[1]:.1f}", ha="right", va="bottom", fontsize=9.5, color=PURPLE)
    ax.text(2.7, 99.75, "P381 · LiFSI–TEP, diluent swapped (30 °C)", ha="left", va="bottom", fontsize=9.5, color=PURPLE, fontweight="bold")
    ax.text(4.4, 94.4, "P371 · 1,2-diethoxyethane,\nF added step by step\n(1.2 M LiTFSI, single solvent, 60 °C)", ha="left", va="center",
            fontsize=9.5, color=RED, fontweight="bold", linespacing=1.3)
    ax.annotate("partial fluorination is the worst", xy=(3.1, y371[1]), xytext=(4.4, 91.2), fontsize=9, color=INK2,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8), va="center")
    ax.set_xlim(-1.3, 8.6); ax.set_ylim(89.2, 100.6)
    ax.set_xticks(range(0, 9)); ax.set_yticks([90, 92, 94, 96, 98, 100])
    ax.set_xlabel("F atoms per solvent / diluent molecule")
    ax.set_ylabel("Li‖Cu Coulombic efficiency (%)")
    ax.grid(axis="y", color="#eeeeea", lw=0.8)
    ax.set_title(f"Data · usual result: more F → higher CE (every comparison in {all_up} of {n_pap} papers)\n"
                 "but within these two papers, adding F did not keep helping", fontsize=10.5, loc="left", color=INK)
    fig.text(0.06, 0.03, "* F6DEE is saturated (< 1.2 M LiTFSI). Each line = one paper, same salt and same test; papers are not compared with each other.",
             fontsize=8.3, color=MUTED)
    # 右：机制示意（两条 LiF 来源）
    s = fig.add_axes([0.55, 0.06, 0.44, 0.84])
    s.set_xlim(0, 10); s.set_ylim(0, 10); s.axis("off")
    s.add_patch(Rectangle((0.6, 2.3), 8.8, 0.9, fc="#c9c8c2", ec="none"))
    s.text(5, 2.75, "Li metal", ha="center", va="center", fontsize=10, color=INK)
    s.add_patch(Rectangle((0.6, 3.2), 8.8, 0.75, fc="#eef3f9", ec="#9fb3c8"))
    s.text(5, 3.57, "LiF-rich SEI", ha="center", va="center", fontsize=9.5, color=INK2)
    box(s, 0.5, 6.9, 4.0, 1.2, "Diluent / fluorinated solvent\n(e.g. TTE, F3DEE)", "#eaf2fc", BLUE, fs=9.5, weight="bold", color=BLUE)
    box(s, 5.5, 6.9, 4.0, 1.2, "Salt anion\n(FSI⁻, TFSI⁻)", "#fdeee7", ORANGE, fs=9.5, weight="bold", color=ORANGE)
    arrow(s, (2.5, 6.9), (2.5, 4.0), BLUE, lw=2.2, ms=16)
    arrow(s, (7.5, 6.9), (7.5, 4.0), ORANGE, lw=2.2, ms=16)
    s.text(2.7, 5.45, "C–F bonds break → LiF\n(+ organic by-products)", fontsize=9, color=BLUE, va="center")
    s.text(7.7, 5.45, "S–F bonds break → LiF", fontsize=9, color=ORANGE, va="center")
    s.text(2.5, 8.35, f"Route 1 · {len(side['A'])} papers ({min(yrs['A'])}–{max(yrs['A'])})\n“the diluent should decompose”",
           ha="center", va="bottom", fontsize=9.5, color=INK)
    s.text(7.5, 8.35, f"Route 2 · {len(side['B'])} papers ({sum(y >= 2022 for y in yrs['B'])} since 2022)\n“the diluent should stay intact”",
           ha="center", va="bottom", fontsize=9.5, color=INK)
    s.text(7.3, 6.5, "P381, P371 are on this side", ha="right", va="top", fontsize=9, color=RED, fontweight="bold")
    box(s, 0.0, 0.0, 10.0, 1.75, "Testable — keep the salt fixed (LiTFSI), vary only how many F the diluent carries and where\n"
        "(DEE → F3/F4/F5/F6DEE); measure Li‖Cu CE and whether the SEI LiF comes from C–F (diluent)\n"
        "or S–F (anion) bonds (XPS depth profile / ToF-SIMS).", "#fafaf7", MUTED, fs=8.8, color=INK, ha="left")
    s.set_title("Mechanism · where does the LiF come from?", fontsize=10.5, loc="left", color=INK)
    fig.suptitle("Open question 1 · Should the diluent decompose? More fluorine is not always better", x=0.06, y=0.995, ha="left",
                 fontsize=13, fontweight="bold", color=INK)
    save(fig, "fig_q1.png")
    DATA["q1"] = {"有含氟数变化的同测试比较的论文": n_pap, "每个比较都是含氟多 CE 高的论文": all_up,
                  "P371 系列（Taur，60 °C）": dict(zip([n for n, _ in P371_SERIES], y371)), "P381（T01）DBE / TTE": y381,
                  "路线 1 论文": side["A"], "路线 2 论文": side["B"],
                  "注": "组分表把 DEE 记成乙醚（CCOCC），P371 的 DEE 实为 1,2-二乙氧基乙烷；F6DEE 即 DTFEG，饱和（< 1.2 M）"}


# ---------------- 问题 2 ----------------
def formulations():
    """每个配方（论文 × recipe）的主盐浓度（M）、LiNO₃ 浓度（M）与是否含 LiNO₃。
    11-08 晚核对：108 个配方含 LiNO₃ 但没有以 M 计的用量（79 个原文没给用量、20 个按 wt% 给），LiNO3_M 为空；
    “有没有加 LiNO₃”看配方组分，不能用 LiNO3_M 是否为空代替（否则高盐 + LiNO₃ 会少数 7 个配方）。"""
    out, seen = [], set()
    for r in load(MEAS):
        if r["recipe"] is None:
            continue
        k = (r["论文"], r["recipe"])
        if k in seen:
            continue
        seen.add(k)
        h, _ = P16.H.descriptors(r["论文"], r["recipe"])
        v = r["描述符"].get("LiNO3_M")
        comp = P16.H.COMPREC.get(k)
        if v is not None:  # 有以 M 计的用量就按用量判断（“LiNO3 0 M”这类对照组分里列着 LiNO₃，但用量是 0）
            has = v > 0
        else:
            has = bool(comp and any(i["组分"] == "LiNO3" and i.get("数值") != 0 for i in comp["组分"]))
        out.append({"论文": r["论文"], "recipe": r["recipe"], "salt": h.get("salt"), "lino3": v, "has_lino3": has})
    return out, len(seen)


# 11-08 晚：左边只画“只改 LiNO₃ 用量、至少 3 个浓度”的剂量系列（P111、P139），P121 的 1.0 M 配方同时把 LiTFSI 从 1.1 降到 0.5 M，不算剂量系列；
# 多数结论写成一句话；右边概念图只留三条线（收益在 0 上方、代价在 0 下方、两者之和），条件变化只用最佳点的位置表示。
DOSE_SERIES = {"P111": "T1", "P139": "T09"}


def q2(F):
    R = load(PAIRS)
    ev = load(EV)["T3"]
    side = {k[0]: v for k, v in ev["各立场论文"].items()}
    segs, ser = [], defaultdict(dict)
    for r in R:
        if r["类别"] != "每圈衰减率" or r["比较类型"] != T.SAME:
            continue
        x = next((y for y in r["描述符"] if y["描述符"] == "lino3"), None)
        if not x:
            continue
        lo, hi = sorted((x["A"], x["B"]))
        segs.append({"论文": r["论文"], "hi": hi, "e": T.effect(r) * (1 if x["A"] > x["B"] else -1)})
        if DOSE_SERIES.get(r["论文"]) == r["A"]["测试"]:
            ser[r["论文"]][x["A"]] = r["性能"]["值A"]
            ser[r["论文"]][x["B"]] = r["性能"]["值B"]
    low = [g for g in segs if g["hi"] <= 0.5]
    good_low = sum(g["e"] > T.T for g in low)
    fig = plt.figure(figsize=(13.5, 5.8))
    ax = fig.add_axes([0.06, 0.37, 0.40, 0.44])
    axh = fig.add_axes([0.06, 0.12, 0.40, 0.15], sharex=ax)
    xmax = 1.06
    ax.axvspan(0.5, xmax, color="#f4f3ef", zorder=0)
    ax.axhline(1, color=MUTED, lw=0.9, ls=(0, (4, 3)))
    rel = {}
    for p, col in (("P111", RED), ("P139", BLUE)):
        d = sorted(ser[p])
        y = [ser[p][d[0]] / ser[p][c] for c in d]
        rel[p] = dict(zip(d, [round(v, 3) for v in y]))
        ax.plot(d, y, "-o", color=col, lw=2.6, ms=9, zorder=3)
    ax.text(0.55, 0.86, "P111 · best at 0.5 M;\nat 1.0 M worse than at 0.1 M\n(1000 cycles)", ha="left", va="center", fontsize=9.5, color=RED,
            fontweight="bold", linespacing=1.3)
    ax.text(0.02, 1.36, "P139 · still improving at 0.5 M\n(highest dose tested)", ha="left", va="center", fontsize=9.5, color=BLUE, fontweight="bold",
            linespacing=1.3)
    ax.text(0.78, 1.62, "above 0.5 M: one clean\ndose series (P111)", ha="center", va="top", fontsize=9, color=INK2)
    ax.set_ylim(0.68, 1.7); ax.set_xlim(-0.03, xmax)
    ax.set_ylabel("Slower fading than at the\npaper's lowest dose (×)")
    plt.setp(ax.get_xticklabels(), visible=False)
    ax.set_title(f"Data · up to 0.5 M, more LiNO₃ slowed fading in {good_low} of {len(low)} comparisons "
                 f"({len({g['论文'] for g in low})} papers)\nbut the only clean series beyond 0.5 M turns down", fontsize=10.5, loc="left", color=INK)
    lv = [f["lino3"] for f in F if f["lino3"] is not None]
    axh.hist([min(v, xmax - 0.01) for v in lv], bins=np.arange(0, xmax + 0.05, 0.05), color="#9fb3c8", edgecolor="white")
    axh.set_xlabel("LiNO₃ concentration (M)")
    axh.set_ylabel("formulations", fontsize=8.5)
    axh.text(0.99, 0.92, f"{len(lv)} formulations in 313 papers · only {sum(v > 0.6 for v in lv)} above 0.6 M", transform=axh.transAxes,
             ha="right", va="top", fontsize=9, color=INK2)
    # 右：概念示意
    s = fig.add_axes([0.58, 0.36, 0.40, 0.46])
    c = np.linspace(0, 1, 400)
    ben = lambda c0: 1 - np.exp(-c / c0)
    s.axhline(0, color=MUTED, lw=1)
    s.plot(c, ben(0.15), color=BLUE, lw=2.4)
    s.plot(c, -0.9 * c, color=ORANGE, lw=2.4)
    net = ben(0.15) - 0.9 * c
    s.plot(c, net, color=INK, lw=3)
    i0 = int(np.argmax(net))
    s.plot([c[i0]], [net[i0]], "o", color=INK, ms=10, zorder=4)
    s.text(c[i0], net[i0] + 0.09, "best dose", ha="center", va="bottom", fontsize=9.5, color=INK, fontweight="bold")
    s.text(0.98, 1.03, f"anode benefit · saturates\n({len(side['A'])} papers: LiNO₃ is used up at the Li anode)", ha="right", va="bottom", fontsize=9, color=BLUE)
    s.text(0.98, -1.0, f"cathode cost · grows with dose\n({len(side['B'])} papers: LiNO₃ reduced below ~1.7 V)", ha="right", va="top", fontsize=9, color=ORANGE)
    s.text(0.98, net[-1] + 0.05, "net", ha="right", va="bottom", fontsize=9.5, color=INK, fontweight="bold")
    s.set_xlim(0, 1); s.set_ylim(-1.45, 1.35)
    s.set_xticks([]); s.set_yticks([])
    s.set_ylabel("effect on cycle life (schematic)")
    s.spines["bottom"].set_position(("data", -1.45))
    s.set_title("Mechanism · conceptual model (not fitted)", fontsize=10.5, loc="left", color=INK)
    # 最佳用量随条件移动：只画最佳点的位置
    st = fig.add_axes([0.58, 0.20, 0.40, 0.09], sharex=s)
    st.axis("off")
    opt = lambda c0, k: c[int(np.argmax(ben(c0) - k * c))]
    o_lo, o_lean = opt(0.15, 1.7), opt(0.30, 0.9)
    st.plot([0, 1], [0, 0], color=LIGHT, lw=6, solid_capstyle="round")
    for xo, col, lab, ha in ((o_lo, "#6250d6", "lower discharge cut-off\n(more LiNO₃ reduced)", "right"), (c[i0], INK, "baseline", "center"),
                             (o_lean, "#1baf7a", "lean electrolyte / long cycling\n(LiNO₃ used up sooner)", "left")):
        st.plot([xo], [0], "o", color=col, ms=10, zorder=3)
        st.text(xo + (-0.015 if ha == "right" else 0.015 if ha == "left" else 0), -0.55, lab, ha=ha, va="top", fontsize=8.8, color=col, linespacing=1.2)
    st.text(0, 0.6, "where the best dose sits →", ha="left", va="bottom", fontsize=9, color=INK2)
    st.set_ylim(-1.6, 1.2)
    fig.text(0.58, 0.015, "Prediction: the best LiNO₃ dose moves with discharge cut-off and E/S — test 0.1–1.0 M\n"
             "at two cut-offs (1.7 vs 1.9 V) and two E/S ratios.", fontsize=9, color=INK, bbox=dict(boxstyle="round,pad=0.5", fc="#fafaf7", ec=MUTED))
    fig.suptitle("Open question 2 · How much LiNO₃ is best? Benefit on the anode vs cost on the cathode", x=0.06, y=0.995, ha="left",
                 fontsize=13, fontweight="bold", color=INK)
    save(fig, "fig_q2.png")
    DATA["q2"] = {"同测试比较": len(segs), "较高浓度 ≤ 0.5 M 的比较": len(low), "其中变好": good_low, "≤ 0.5 M 涉及论文": len({g["论文"] for g in low}),
                  "剂量系列（相对最低浓度的衰减倍数）": rel, "有 LiNO3 数值的配方": len(lv), "高于 0.6 M 的配方": sum(v > 0.6 for v in lv),
                  "注": "P121 的 1.0 M 配方同时把 LiTFSI 从 1.1 M 降到 0.5 M，不算剂量系列；> 0.5 M 的干净剂量系列只有 P111"}


# ---------------- 问题 3 ----------------
# 11-08 晚用户：“q3 的线就是只有两条的那个，很单调，不知道你要表达啥” → 左边改成 P112 四个电解液“每圈损失多少锂”（100 − CE）的柱子：
# 单加高盐或单加 LiNO₃ 都大幅减少锂损失，两者一起并不比只加 LiNO₃ 更好；旁边 2×2 方块表示 313 篇里这四种组合各测过多少配方；
# 右边是两种解释的示意：同一个靶点（可以互相替代）还是不同靶点（在锂硫全电池里叠加）。
def q3(F, n_form):
    R = load(PAIRS)
    ev = load(EV)["T4"]
    side = {k[0]: v for k, v in ev["各立场论文"].items()}
    val = {}
    for r in R:
        if r["论文"] == "P112" and r["类别"] == "LiCu_CE":
            for sd, k in (("A", "值A"), ("B", "值B")):
                val[r[sd]["配方名"]] = r["性能"][k]
    v = {("1", 0): val["1 M LiTFSI DOL/DME"], ("4", 0): val["4 M LiTFSI DOL/DME"],
         ("1", 1): val["1 M LiTFSI DOL/DME +0.5 M LiNO3"], ("4", 1): val["4 M LiTFSI DOL/DME +0.5 M LiNO3"]}
    PURPLE = "#6250d6"
    fig = plt.figure(figsize=(13.5, 5.8))
    ax = fig.add_axes([0.06, 0.17, 0.29, 0.62])
    bars = [(("1", 0), "1 M LiTFSI", GREY), (("4", 0), "4 M LiTFSI", ORANGE), (("1", 1), "1 M\n+ 0.5 M LiNO₃", BLUE), (("4", 1), "4 M\n+ 0.5 M LiNO₃", PURPLE)]
    loss = [100 - v[k] for k, _, _ in bars]
    ax.bar(range(4), loss, color=[c for _, _, c in bars], width=0.66)
    for i, ((k, _, col), L) in enumerate(zip(bars, loss)):
        ax.text(i, L + 0.4, f"{L:.1f} %", ha="center", va="bottom", fontsize=10.5, color=col if col != GREY else INK2, fontweight="bold")
    base = loss[0]
    for i, txt in ((1, f"÷{int(base / loss[1])}"), (2, f"÷{int(base / loss[2])}"), (3, f"÷{int(base / loss[3])}\nsame as\nLiNO₃ alone")):
        ax.text(i, loss[i] + 2.3, txt, ha="center", va="bottom", fontsize=9, color=INK2, linespacing=1.2)
    ax.set_xticks(range(4))
    ax.set_xticklabels([f"{lab}\n(CE {v[k]:.1f} %)" for k, lab, _ in bars], fontsize=8.8)
    ax.set_ylim(0, 23.5)
    ax.set_ylabel("Li lost per cycle (100 − CE, %)")
    ax.set_title("Data · P112, the only paper that crossed the two\n(Li‖Cu, DOL/DME): either one is enough", fontsize=10.5, loc="left", color=INK)
    # 2×2 覆盖：313 篇里四种组合各有多少配方
    cnt, pap = Counter(), defaultdict(set)
    for f in F:
        if f["salt"] is None:  # 是否含 LiNO₃ 看组分，不要求有以 M 计的用量
            continue
        k = (int(f["has_lino3"]), int(f["salt"] > 1.0))
        cnt[k] += 1
        pap[k].add(f["论文"])
    n_both = sum(cnt.values())
    g = fig.add_axes([0.40, 0.17, 0.15, 0.50])
    g.set_xlim(-0.5, 1.5); g.set_ylim(-0.5, 1.5); g.set_aspect("equal")
    mx = max(cnt.values())
    for (li, hs), n in cnt.items():
        side_len = 0.92 * math.sqrt(n / mx)
        hot = li == 1 and hs == 1
        g.add_patch(Rectangle((hs - side_len / 2, li - side_len / 2), side_len, side_len, fc=RED if hot else "#9fb3c8", ec="none"))
        if hot:  # 方块太小，数字写在方块下方
            g.text(hs, li - side_len / 2 - 0.06, f"only {n}\n({len(pap[(li, hs)])} papers)", ha="center", va="top", fontsize=9, color=RED,
                   fontweight="bold", linespacing=1.15)
        else:
            g.text(hs, li, f"{n}", ha="center", va="center", fontsize=10, color="white" if n > 40 else INK, fontweight="bold")
    hot_n = cnt[(1, 1)]
    for li in (0, 1):
        for hs in (0, 1):
            g.add_patch(Rectangle((hs - 0.5, li - 0.5), 1, 1, fill=False, ec=LIGHT, lw=0.8))
    g.set_xticks([0, 1]); g.set_xticklabels(["salt ≤ 1 M", "salt > 1 M"], fontsize=9)
    g.set_yticks([0, 1]); g.set_yticklabels(["no LiNO₃", "+ LiNO₃"], fontsize=9)
    g.tick_params(length=0)
    g.spines[:].set_visible(False)
    g.set_title("Coverage · formulations in 313 papers\nthat tested each combination", fontsize=10, loc="left", color=INK)
    # 右：两种解释
    s = fig.add_axes([0.58, 0.04, 0.41, 0.84])
    s.set_xlim(0, 10); s.set_ylim(0, 10); s.axis("off")
    s.plot([5, 5], [3.0, 9.6], color=LIGHT, lw=1)
    # 替代：两个输入指向同一个靶点
    s.text(2.4, 9.55, f"Substitutes · {len(side['A'])} papers", ha="center", va="top", fontsize=10, color=INK, fontweight="bold")
    s.text(2.4, 8.95, "Li can be stabilized without LiNO₃", ha="center", va="top", fontsize=8.8, color=INK2)
    box(s, 0.2, 6.8, 2.0, 0.95, "High salt", "#fdeee7", ORANGE, fs=9.5, weight="bold", color=ORANGE)
    box(s, 2.6, 6.8, 2.0, 0.95, "LiNO₃", "#eaf2fc", BLUE, fs=9.5, weight="bold", color=BLUE)
    box(s, 1.0, 4.3, 2.8, 1.0, "Li-anode SEI", "#f3f2ee", MUTED, fs=9.5, weight="bold", color=INK)
    arrow(s, (1.2, 6.8), (2.0, 5.3), ORANGE, lw=2, ms=14)
    arrow(s, (3.6, 6.8), (2.8, 5.3), BLUE, lw=2, ms=14)
    s.text(2.4, 3.9, "same job → either one is enough", ha="center", va="top", fontsize=9, color=INK)
    # 互补：各管一个靶点，高盐还帮 LiNO₃ 省着用
    s.text(7.6, 9.55, f"Complements · {len(side['B'])} papers + P112 authors", ha="center", va="top", fontsize=10, color=INK, fontweight="bold")
    s.text(7.6, 8.95, "LiNO₃ does something nothing else does", ha="center", va="top", fontsize=8.8, color=INK2)
    box(s, 5.4, 6.8, 2.0, 0.95, "LiNO₃", "#eaf2fc", BLUE, fs=9.5, weight="bold", color=BLUE)
    box(s, 7.8, 6.8, 2.0, 0.95, "High salt", "#fdeee7", ORANGE, fs=9.5, weight="bold", color=ORANGE)
    box(s, 5.4, 4.3, 2.0, 1.0, "Li-anode SEI", "#f3f2ee", MUTED, fs=9.5, weight="bold", color=INK)
    box(s, 7.8, 4.1, 2.0, 1.2, "fewer dissolved\npolysulfides →\nLiNO₃ lasts longer", "#f3f2ee", MUTED, fs=8.8, weight="bold", color=INK)
    arrow(s, (6.4, 6.8), (6.4, 5.3), BLUE, lw=2, ms=14)
    arrow(s, (8.8, 6.8), (8.8, 5.3), ORANGE, lw=2, ms=14)
    s.text(7.6, 3.9, "different jobs → they add up in a Li–S cell", ha="center", va="top", fontsize=9, color=INK)
    box(s, 0.0, 0.3, 10.0, 1.9, "Li‖Cu has no polysulfides, so it can only show the overlap (P112).\n"
        "Testable in Li–S cells: 1 M vs 4 M LiTFSI, each ± 0.5 M LiNO₃; track cycle life and\n"
        "how much NO₃⁻ is left in the electrolyte. Complements ⇒ LiNO₃ runs out more slowly at 4 M.",
        "#fafaf7", MUTED, fs=8.8, color=INK, ha="left")
    s.set_title("Mechanism · same target or different targets?", fontsize=10.5, loc="left", color=INK)
    fig.suptitle("Open question 3 · High salt and LiNO₃: substitutes or complements?", x=0.06, y=0.995,
                 ha="left", fontsize=13, fontweight="bold", color=INK)
    save(fig, "fig_q3.png")
    DATA["q3"] = {"P112": {f"{k[0]} M{' +LiNO3' if k[1] else ''}": x for k, x in v.items()}, "有两个数值的配方": n_both, "配方总数": n_form,
                  "2×2（LiNO3 有/无 × 盐 ≤1 / >1 M）": {f"LiNO3 {'有' if li else '无'} · 盐 {'> 1' if hs else '≤ 1'} M": [n, len(pap[(li, hs)])]
                                                   for (li, hs), n in sorted(cnt.items())},
                  "高盐且含 LiNO3": [hot_n, sorted(pap[(1, 1)])], "替代一方": side["A"], "互补一方": side["B"]}


def main():
    F, n_form = formulations()
    q1()
    q2(F)
    q3(F, n_form)
    (OUT / "组会图数据.json").write_text(json.dumps(DATA, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(DATA, ensure_ascii=False)[:1500])


if __name__ == "__main__":
    main()
