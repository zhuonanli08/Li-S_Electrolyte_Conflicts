"""组会第 16–18 页与网站 07 页：三个无定论问题各一张图，左边数据、右边机制示意（11-08 用户同意按 zy 意见改：用图、少字、更有科学意味）。图英文。

问题 1（fig_q1）：左 = 同一测试里成对比较的箭头图，箭头从溶剂 F 原子数少的一侧指向多的一侧；纵轴 Li‖Cu CE（按损失 100 − CE 取对数刻度，越上越好）；
  读原文判为真张力候选的对（P381、P371）标红。右 = LiF 两条来源的示意（step20：稀释剂分解 9 篇 vs 阴离子分解 13 篇）与一句可检验的假设。
问题 2（fig_q2）：左 = 所有 LiNO₃ 浓度不同的同测试每圈衰减率比较（每对一条横线，从少到多，高度 = 多的一侧衰减变化，正 = 变慢），
  > 0.5 M 区域标出只有 2 篇；下方是 345 个配方的 LiNO₃ 用量分布。右 = 概念示意（负极收益会饱和、正极代价随用量增加 → 最佳用量，
  随截止电压与电解液用量移动；示意，不是拟合）。
问题 3（fig_q3）：左 = P112 的 2×2 交互图；右 = 313 篇“主盐浓度 × LiNO₃”覆盖热图（配方数），空格 = 没人测过。
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
def q1():
    R, res = load(PAIRS), results()
    ev = load(EV)["T1"]
    side = {k[0]: v for k, v in ev["各立场论文"].items()}
    yrs = defaultdict(list)
    for c in load(VEC)["说法"]:
        if c["问题"] == "T1" and c["立场"] in "AB":
            yrs[c["立场"]].append(c["年份"])
    pts = []
    for r in R:
        if r["类别"] != "LiCu_CE" or r["比较类型"] != T.SAME:
            continue
        x = next((y for y in r["描述符"] if y["描述符"] == "fat"), None)
        if not x:
            continue
        (xl, cl), (xh, ch) = sorted([(x["B"], r["性能"]["值B"]), (x["A"], r["性能"]["值A"])])
        e = T.effect(r) * (1 if x["A"] > x["B"] else -1)
        pts.append({"论文": r["论文"], "编号": r["编号"], "x": (xl, xh), "ce": (cl, ch), "e": e, "结果": res.get(r["编号"], "")})
    good, bad = sum(p["e"] > T.T for p in pts), sum(p["e"] < -T.T for p in pts)
    fig = plt.figure(figsize=(13.5, 5.8))
    ax = fig.add_axes([0.06, 0.12, 0.47, 0.76])
    loss = lambda ce: max(100 - ce, 0.15)
    for real in (False, True):
        for p in pts:
            if (p["结果"] == "真张力候选") != real:
                continue
            col = RED if real else ("#a9bfd8" if p["e"] > T.T else "#e0b9b3" if p["e"] < -T.T else LIGHT)
            arrow(ax, (p["x"][0], loss(p["ce"][0])), (p["x"][1], loss(p["ce"][1])), col, lw=2.6 if real else 0.8, ms=14 if real else 6)
    ax.set_yscale("log")
    ax.invert_yaxis()
    ticks = [80, 90, 95, 98, 99, 99.5, 99.8]
    ax.set_yticks([100 - t for t in ticks])
    ax.set_yticklabels([f"{t:g}" for t in ticks])
    ax.minorticks_off()
    ax.set_ylim(25, 0.15)
    ax.set_xlim(-0.4, max(max(p["x"]) for p in pts) + 0.6)
    ax.set_xlabel("F atoms per solvent molecule (mole-fraction average)")
    ax.set_ylabel("Li‖Cu Coulombic efficiency (%)")
    ax.grid(axis="y", color="#eeeeea", lw=0.8)
    ax.annotate("P381: non-fluorinated DBE diluent\n99.4% vs TTE 98.8%", xy=(2.0, loss(99.1)), xytext=(4.6, loss(99.75)), fontsize=9, color=RED,
                arrowprops=dict(arrowstyle="-", color=RED, lw=0.8))
    ax.annotate("P371: partially fluorinated F3DEE\n90.8% vs DEE 95.4%", xy=(1.5, loss(93.0)), xytext=(3.4, loss(86)), fontsize=9, color=RED,
                arrowprops=dict(arrowstyle="-", color=RED, lw=0.8))
    ax.set_title(f"Data · {len(pts)} same-test comparisons; arrow = fewer F → more F\n"
                 f"CE higher with more F in {good}, lower in {bad}", fontsize=10.5, loc="left", color=INK)
    leg = [plt.Line2D([], [], color="#a9bfd8", lw=1.5, label="more F, higher CE (consensus)"),
           plt.Line2D([], [], color="#e0b9b3", lw=1.5, label="more F, lower CE — explained after reading"),
           plt.Line2D([], [], color=RED, lw=2.5, label="genuine counterexample (P381, P371)")]
    ax.legend(handles=leg, loc="lower right", frameon=False, fontsize=8.5)
    # 右：机制示意
    s = fig.add_axes([0.57, 0.04, 0.42, 0.86])
    s.set_xlim(0, 10); s.set_ylim(0, 10); s.axis("off")
    s.add_patch(Rectangle((0.6, 2.2), 8.8, 0.9, fc="#c9c8c2", ec="none"))
    s.text(5, 2.65, "Li metal", ha="center", va="center", fontsize=10, color=INK)
    s.add_patch(Rectangle((0.6, 3.1), 8.8, 1.0, fc="#f3f2ee", ec="#c9c8c2"))
    for xx in np.linspace(1.1, 8.9, 14):
        s.add_patch(Rectangle((xx - 0.17, 3.35 + 0.25 * (int(xx * 7) % 2)), 0.34, 0.34, fc="#7fa7d9", ec="white", lw=0.6))
    s.text(9.3, 4.35, "SEI (LiF-rich)", ha="right", va="bottom", fontsize=9, color=INK2)
    box(s, 0.5, 7.0, 4.0, 1.25, "Diluent / fluorinated solvent\n(e.g. TTE, HFE)", "#eaf2fc", BLUE, fs=9.5, weight="bold", color=BLUE)
    box(s, 5.5, 7.0, 4.0, 1.25, "Anion\n(FSI⁻, TFSI⁻)", "#fdeee7", ORANGE, fs=9.5, weight="bold", color=ORANGE)
    arrow(s, (2.5, 7.0), (2.5, 4.15), BLUE, lw=2.2, ms=16)
    arrow(s, (7.5, 7.0), (7.5, 4.15), ORANGE, lw=2.2, ms=16)
    s.text(2.65, 5.6, "C–F cleavage → LiF\n(+ organic by-products)", fontsize=8.8, color=BLUE, va="center")
    s.text(7.65, 5.6, "S–F cleavage → LiF", fontsize=8.8, color=ORANGE, va="center")
    s.text(2.5, 8.55, f"Route 1 · {len(side['A'])} papers ({min(yrs['A'])}–{max(yrs['A'])})\n“diluent decomposition helps”",
           ha="center", va="bottom", fontsize=9, color=INK)
    s.text(7.5, 8.55, f"Route 2 · {len(side['B'])} papers ({sum(y >= 2022 for y in yrs['B'])} since 2022)\n“diluent should stay intact”",
           ha="center", va="bottom", fontsize=9, color=INK)
    s.text(7.3, 6.3, "P381, P371\nfit here", ha="right", fontsize=8.8, color=RED, fontweight="bold")
    box(s, -0.1, -0.2, 10.3, 1.85, "Testable hypothesis — fix the anion (same LiFSI) and vary only the diluent’s\n"
        "fluorination degree and position (DEE → F3/F4/F5/F6DEE); measure Li‖Cu CE and\nwhether the SEI LiF comes from C–F (diluent) or S–F (anion) bonds (XPS / ToF-SIMS).",
        "#fafaf7", MUTED, fs=8.8, color=INK, ha="left")
    s.set_title("Mechanism · where does the LiF come from?", fontsize=10.5, loc="left", color=INK)
    fig.suptitle("Open question 1 · Should the diluent decompose? More fluorine is not always better", x=0.06, y=0.995, ha="left",
                 fontsize=13, fontweight="bold", color=INK)
    save(fig, "fig_q1.png")
    DATA["q1"] = {"比较": len(pts), "更多 F 时 CE 变好": good, "变差": bad, "真张力候选对": [p["编号"] for p in pts if p["结果"] == "真张力候选"],
                  "路线 1 论文": side["A"], "路线 2 论文": side["B"]}


# ---------------- 问题 2 ----------------
def formulations():
    """每个配方（论文 × recipe）的主盐浓度（M）与 LiNO₃ 浓度（M）。"""
    out, seen = [], set()
    for r in load(MEAS):
        if r["recipe"] is None:
            continue
        k = (r["论文"], r["recipe"])
        if k in seen:
            continue
        seen.add(k)
        h, _ = P16.H.descriptors(r["论文"], r["recipe"])
        out.append({"论文": r["论文"], "recipe": r["recipe"], "salt": h.get("salt"), "lino3": r["描述符"].get("LiNO3_M")})
    return out, len(seen)


def q2(F):
    R, res = load(PAIRS), results()
    ev = load(EV)["T3"]
    side = {k[0]: v for k, v in ev["各立场论文"].items()}
    segs = []
    for r in R:
        if r["类别"] != "每圈衰减率" or r["比较类型"] != T.SAME:
            continue
        x = next((y for y in r["描述符"] if y["描述符"] == "lino3"), None)
        if not x:
            continue
        lo, hi = sorted((x["A"], x["B"]))
        segs.append({"论文": r["论文"], "lo": lo, "hi": hi, "e": T.effect(r) * (1 if x["A"] > x["B"] else -1), "结果": res.get(r["编号"], "")})
    hiR = [g for g in segs if g["hi"] > 0.5]
    fig = plt.figure(figsize=(13.5, 5.8))
    ax = fig.add_axes([0.06, 0.30, 0.47, 0.58])
    axh = fig.add_axes([0.06, 0.10, 0.47, 0.12], sharex=ax)
    xmax = 1.08
    ax.axvspan(0.5, xmax, color="#f1f0ec", zorder=0)
    ax.text(0.79, 0.97, f"> 0.5 M: {len(hiR)} comparisons\nfrom only {len({g['论文'] for g in hiR})} papers", transform=ax.get_xaxis_transform(),
            ha="center", va="top", fontsize=9, color=INK2)
    ax.axhline(0, color=MUTED, lw=1)
    for g in sorted(segs, key=lambda g: g["论文"] == "P111"):
        p111 = g["论文"] == "P111"
        col = BLUE if g["e"] > T.T else RED if g["e"] < -T.T else GREY
        ax.plot([g["lo"], g["hi"]], [g["e"], g["e"]], color=INK if p111 else col, lw=3.2 if p111 else 2.0, solid_capstyle="round", alpha=1 if p111 else 0.85)
        ax.plot([g["hi"]], [g["e"]], "o", ms=5.5 if p111 else 4, color=INK if p111 else col)
    p = [g for g in segs if g["论文"] == "P111"]
    ax.annotate("P111: 0.1 → 0.5 M slower fade,\n0.5 → 1.0 M faster (volcano)", xy=(0.75, min(g["e"] for g in p) * 0.6), xytext=(0.56, -1.9),
                fontsize=9, color=INK, arrowprops=dict(arrowstyle="-", color=INK, lw=0.8))
    ax.set_ylabel("Fade change when LiNO₃ increases\n(ln ratio, + = slower fade)")
    ax.set_xlim(-0.02, xmax)
    plt.setp(ax.get_xticklabels(), visible=False)
    good = sum(g["e"] > T.T for g in segs)
    ax.set_title(f"Data · {len(segs)} same-test comparisons from {len({g['论文'] for g in segs})} papers; line = LiNO₃ range compared\n"
                 f"blue = more LiNO₃ slowed fading ({good}), red = sped it up ({sum(g['e'] < -T.T for g in segs)})",
                 fontsize=10.5, loc="left", color=INK)
    lv = [f["lino3"] for f in F if f["lino3"] is not None]
    axh.hist([min(v, xmax - 0.01) for v in lv], bins=np.arange(0, xmax + 0.05, 0.05), color="#9fb3c8", edgecolor="white")
    axh.set_xlabel("LiNO₃ concentration (M)")
    axh.set_ylabel("formul.", fontsize=8.5)
    axh.text(0.99, 0.9, f"{len(lv)} formulations in 313 papers; {sum(v > 0.6 for v in lv)} above 0.6 M", transform=axh.transAxes, ha="right", va="top",
             fontsize=8.5, color=INK2)
    # 右：概念模型
    s = fig.add_axes([0.60, 0.36, 0.38, 0.52])
    c = np.linspace(0, 1, 400)
    ben = lambda c0: 1 - np.exp(-c / c0)
    for c0, k, ls, lab, col in ((0.15, 0.9, "-", "baseline", INK), (0.15, 1.7, "--", "lower discharge cut-off", "#6250d6"),
                                (0.30, 0.9, ":", "lean electrolyte / long cycling", "#1baf7a")):
        net = ben(c0) - k * c
        i = int(np.argmax(net))
        if ls == "-":
            s.plot(c, ben(c0), color=BLUE, lw=2, label=f"anode benefit (saturates) · {len(side['A'])} papers")
            s.plot(c, k * c, color=ORANGE, lw=2, label=f"cathode cost (≲1.7 V reduction) · {len(side['B'])} papers")
        s.plot(c, net, color=col, lw=2.4 if ls == "-" else 1.8, ls=ls, label=f"net · {lab}")
        s.plot([c[i]], [net[i]], "o", color=col, ms=7)
    s.annotate("", xy=(0.20, -0.32), xytext=(0.30, -0.32), arrowprops=dict(arrowstyle="-|>", color="#6250d6", lw=1.5))
    s.annotate("", xy=(0.40, -0.32), xytext=(0.30, -0.32), arrowprops=dict(arrowstyle="-|>", color="#1baf7a", lw=1.5))
    s.text(0.30, -0.42, "optimum moves", ha="center", fontsize=8.5, color=INK2)
    s.set_xlim(0, 1); s.set_ylim(-0.55, 1.15)
    s.set_xticks([]); s.set_yticks([])
    s.set_xlabel("LiNO₃ dose →"); s.set_ylabel("effect on cycle life (schematic)")
    s.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False, fontsize=8.3)
    s.set_title("Mechanism · conceptual model (not fitted)", fontsize=10.5, loc="left", color=INK)
    fig.text(0.60, 0.02, "Prediction: the best LiNO₃ dose shifts with discharge cut-off and E/S —\n"
             "test 0.1–1.0 M at two cut-offs (1.7 vs 1.9 V) and two E/S ratios.", fontsize=9, color=INK,
             bbox=dict(boxstyle="round,pad=0.5", fc="#fafaf7", ec=MUTED))
    fig.suptitle("Open question 2 · How much LiNO₃ is best? Benefit on the anode vs cost on the cathode", x=0.06, y=0.995, ha="left",
                 fontsize=13, fontweight="bold", color=INK)
    save(fig, "fig_q2.png")
    DATA["q2"] = {"比较": len(segs), "篇": len({g["论文"] for g in segs}), "变好": good, "高于 0.5 M": len(hiR),
                  "高于 0.5 M 的论文": sorted({g["论文"] for g in hiR}), "有 LiNO3 数值的配方": len(lv), "高于 0.6 M 的配方": sum(v > 0.6 for v in lv)}


# ---------------- 问题 3 ----------------
SB = [("<0.5", lambda s: s < 0.5), ("0.5–1", lambda s: 0.5 <= s <= 1.0), ("1–2", lambda s: 1.0 < s <= 2.0), ("2–4", lambda s: 2.0 < s <= 4.0), (">4", lambda s: s > 4.0)]
LB = [("0", lambda v: v == 0), ("≤0.1", lambda v: 0 < v <= 0.1), ("0.1–0.3", lambda v: 0.1 < v <= 0.3), ("0.3–0.6", lambda v: 0.3 < v <= 0.6), (">0.6", lambda v: v > 0.6)]


def q3(F, n_form):
    R = load(PAIRS)
    val = {}
    for r in R:
        if r["论文"] == "P112" and r["类别"] == "LiCu_CE":
            for sd, k in (("A", "值A"), ("B", "值B")):
                val[r[sd]["配方名"]] = r["性能"][k]
    v = {("1", 0): val["1 M LiTFSI DOL/DME"], ("4", 0): val["4 M LiTFSI DOL/DME"],
         ("1", 1): val["1 M LiTFSI DOL/DME +0.5 M LiNO3"], ("4", 1): val["4 M LiTFSI DOL/DME +0.5 M LiNO3"]}
    fx = load(O / "说法地图_313篇_2026-11-08" / "图07汇总.json")["图7f_交叉图.html"]
    fig = plt.figure(figsize=(13.5, 5.8))
    ax = fig.add_axes([0.06, 0.14, 0.32, 0.72])
    for lino, col, lab in ((0, ORANGE, "without LiNO₃"), (1, BLUE, "with 0.5 M LiNO₃")):
        y = [v[("1", lino)], v[("4", lino)]]
        ax.plot([0, 1], y, "-o", color=col, lw=2.6, ms=9, label=lab)
        for xx, yy in zip((0, 1), y):
            ax.text(xx + (-0.07 if xx == 0 else 0.07), yy, f"{yy:.1f}", ha="right" if xx == 0 else "left", va="center", fontsize=10, color=col, fontweight="bold")
    ax.text(0.56, (v[("1", 0)] + v[("4", 0)]) / 2 - 0.6, f"+{v[('4', 0)] - v[('1', 0)]:.1f} points", color=ORANGE, ha="left", fontsize=9.5)
    ax.text(0.5, v[("1", 1)] + 0.5, f"{v[('4', 1)] - v[('1', 1)]:+.1f} point", color=BLUE, ha="center", fontsize=9.5)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["1 M LiTFSI", "4 M LiTFSI"])
    ax.set_xlim(-0.3, 1.3); ax.set_ylim(77, 101)
    ax.set_ylabel("Li‖Cu Coulombic efficiency (%)")
    ax.legend(loc="center left", bbox_to_anchor=(0.0, 0.62), frameon=False, fontsize=9)
    ax.set_title("Data · P112, the only crossed test (DOL/DME)\nlines not parallel → the two effects overlap", fontsize=10.5, loc="left", color=INK)
    ne, wi = fx["效应"]["参照无 LiNO3"], fx["效应"]["参照有 LiNO3"]
    ax.text(-0.28, 77.6, f"Other salt-only comparisons: without LiNO₃ {sum(e > T.T for e in ne)}/{len(ne)} better "
            f"({len(fx['篇']['参照无 LiNO3'])} papers);\nwith LiNO₃ {min(wi):+.2f} to {max(wi):+.2f} (ln, {len(fx['篇']['参照有 LiNO3'])} papers)",
            fontsize=8.3, color=INK2, va="bottom")
    # 右：覆盖热图
    cnt, pap = Counter(), defaultdict(set)
    for f in F:
        if f["salt"] is None or f["lino3"] is None:
            continue
        i = next(k for k, (_, t) in enumerate(SB) if t(f["salt"]))
        j = next(k for k, (_, t) in enumerate(LB) if t(f["lino3"]))
        cnt[(j, i)] += 1
        pap[(j, i)].add(f["论文"])
    n_both = sum(cnt.values())
    h = fig.add_axes([0.47, 0.14, 0.40, 0.72])
    M = np.array([[cnt.get((j, i), 0) for i in range(len(SB))] for j in range(len(LB))], float)
    from matplotlib.colors import LogNorm, ListedColormap
    cmap = ListedColormap(["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"])
    im = h.imshow(np.where(M > 0, M, np.nan), cmap=cmap, norm=LogNorm(vmin=1, vmax=M.max()), aspect="auto", origin="lower")
    for j in range(len(LB)):
        for i in range(len(SB)):
            n = int(M[j, i])
            if n == 0:
                h.add_patch(Rectangle((i - 0.5, j - 0.5), 1, 1, fc="white", ec=LIGHT, hatch="////", lw=0.5))
                h.text(i, j, "never\ntested", ha="center", va="center", fontsize=8, color=MUTED)
            else:
                h.text(i, j, f"{n}\n({len(pap[(j, i)])} p.)", ha="center", va="center", fontsize=8.5,
                       color="white" if n >= 20 else INK, linespacing=1.15)
    for (i, j) in ((1, 3), (3, 3)):  # P112：1 M 与 4 M LiTFSI，各加 0.5 M LiNO₃
        h.add_patch(Rectangle((i - 0.47, j - 0.47), 0.94, 0.94, fill=False, ec=RED, lw=2.2))
    for i in (1, 3):
        h.text(i + 0.44, 3.44, "P112", ha="right", va="top", fontsize=8, color=RED, fontweight="bold")
    h.add_patch(Rectangle((1.5, 0.5), 3.0, 4.0, fill=False, ec=INK, lw=1.6, ls=(0, (5, 3))))
    h.text(4.45, 4.42, "high salt + LiNO₃", ha="right", va="top", fontsize=9, color=INK, fontweight="bold")
    h.set_xticks(range(len(SB))); h.set_xticklabels([s for s, _ in SB])
    h.set_yticks(range(len(LB))); h.set_yticklabels([s for s, _ in LB])
    h.set_xlabel("Main lithium-salt concentration (M)"); h.set_ylabel("LiNO₃ concentration (M)")
    hs = sum(cnt.get((j, i), 0) for j in range(1, len(LB)) for i in range(2, len(SB)))
    hp = set().union(*[pap[(j, i)] for j in range(1, len(LB)) for i in range(2, len(SB))]) if hs else set()
    h.set_title(f"Coverage · {n_both} formulations with both values (of {n_form}) · number = formulations (papers)\n"
                f"salt > 1 M together with LiNO₃: only {hs} formulations from {len(hp)} papers", fontsize=10.5, loc="left", color=INK)
    h.spines[:].set_visible(False)
    cb = fig.colorbar(im, cax=fig.add_axes([0.885, 0.14, 0.012, 0.72]))
    cb.set_label("formulations", fontsize=8.5); cb.outline.set_visible(False)
    cb.set_ticks([1, 10, 100]); cb.set_ticklabels(["1", "10", "100"]); cb.minorticks_off()
    fig.suptitle("Open question 3 · High salt and LiNO₃: substitutes or complements? — the combination is almost untested", x=0.06, y=0.995,
                 ha="left", fontsize=13, fontweight="bold", color=INK)
    save(fig, "fig_q3.png")
    DATA["q3"] = {"P112": {f"{k[0]} M{' +LiNO3' if k[1] else ''}": x for k, x in v.items()}, "有两个数值的配方": n_both, "配方总数": n_form,
                  "热图": {f"LiNO3 {LB[j][0]} · 盐 {SB[i][0]}": [int(M[j, i]), len(pap[(j, i)])] for j in range(len(LB)) for i in range(len(SB))},
                  "高盐且含 LiNO3": [hs, sorted(hp)]}


def main():
    F, n_form = formulations()
    q1()
    q2(F)
    q3(F, n_form)
    (OUT / "组会图数据.json").write_text(json.dumps(DATA, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(DATA, ensure_ascii=False)[:1500])


if __name__ == "__main__":
    main()
