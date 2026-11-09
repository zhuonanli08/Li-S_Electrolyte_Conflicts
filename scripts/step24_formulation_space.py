"""step24（papertrail 环境）：配方空间——用项目已有描述符的两个平面，把 Li‖Cu 同篇比较画成箭头，同时显示多数规律与矛盾。

11-09 用户：“配方空间你是想说明什么问题，我感觉你的横轴就不合理了”“也可以用我现有的描述符表示，看能不能呈现我找到的矛盾。就像我描述符版的分子宇宙一样”
“可能需要颜色/大小还是其它啥的单作一个维度，来证明库伦效率大小”；方案“可以”。
旧版（11-08）横轴“每个 Li⁺ 的配位位点” = 溶剂位点 ÷ Li⁺ 浓度，与纵轴盐浓度秩相关 −0.62、43% 的变化来自 Li⁺ 浓度，且含氟醚氧不计位点 → 废弃。
新版两栏，轴全部是项目已有描述符（step13h DESCS），彼此独立：
  A 溶剂结构平面：横 = 非氟醚氧（每个溶剂分子，按摩尔分数加权；没有用量时等权），纵 = 溶剂 F 原子数（同样加权，开方刻度，0 附近拉开）。
     计票（step17 v2，Li‖Cu 同测试）：非氟醚氧越多越差（75%，20 篇），F 原子数越多越好（77%，19 篇）→ 共识方向 = 左上。
  B 盐与 LiNO₃ 平面：横 = LiNO₃（M，以 M 计的用量；同 fig_questions.formulations），纵 = 主盐浓度（M，对数）。
     计票：主盐浓度越高越好（79%，14 篇），LiNO₃ 越多越好（82%，6 篇）→ 共识方向 = 右上。
CE 这一维用箭头表示（跨论文绝对 CE 不可比，证据本来就来自同篇比较）：一个箭头 = 同一篇、同一个 Li‖Cu 测试里的两个配方，
  箭头一律指向本平面的共识方向那一侧，蓝 = 箭头指向的配方 CE 更好、红 = 更差、灰 = 相差 5% 以内（同 step17 阈值），线宽 = 变化大小；
  同一对配方在多个测试里比过的合成一个箭头（取效果中位数）。实线 = 只有本平面的描述符变了；虚线 = 同时还改了另一平面的量
  （A 栏：盐浓度或 LiNO₃ 也变了；B 栏：溶剂结构也变了），对应“比较不对等”。两侧本平面描述符完全相同的比较不画。
红箭头 = 往共识方向走却变差 = 反例；读原文已判定的反例论文（P371、P381 等）会出现在这里。
背景：全部配方的分布（灰点，越密底色越深）。图上文字英文。
输出 output/组会图_2026-11-08/fig_formulation_space.png（300 dpi，复制到网站 图/）、配方空间汇总.json。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step24_formulation_space.py
"""
import json
import math
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch
from scipy.ndimage import gaussian_filter

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "step15_meta"))
import fig_questions as Q
import step17_tension_trial as T

O = ROOT / "output"
OUT = O / "组会图_2026-11-08"
SITE = O / "表述与矛盾试跑_F版30篇_2026-11-04" / "网站" / "图"
PAIRS = O / "两两比较表述_313篇_v2_2026-11-07" / "比较表述.json"
VOTES = O / "张力候选_313篇_v2_2026-11-07" / "票数.json"
plt.rcParams.update({"font.family": ["Arial", "DejaVu Sans"]})
INK, INK2, MUTED, PAPER = "#1a1a1a", "#4a4a4a", "#6b6b6b", "white"
BETTER, WORSE, NEAR = "#1f6fd1", "#d03b3b", "#a3a3a3"
GLOW = LinearSegmentedColormap.from_list("glow", [(0, (1, 1, 1, 0)), (0.15, "#e6eef7"), (0.5, "#c3d5ea"), (1, "#8fb0d6")])
HALO = [pe.withStroke(linewidth=3, foreground="white")]
FWD = lambda v: np.sqrt(np.clip(v, 0, None))
INV = lambda v: np.square(v)


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def votes():
    v = {(r["描述符"], r["性能"]): r["同测试"] for r in load(VOTES)}
    g = lambda d: (v[(d, "Li‖Cu CE")]["多数"], v[(d, "Li‖Cu CE")]["多数占比"], v[(d, "Li‖Cu CE")]["篇"])
    return {"非氟醚氧": g("非氟醚氧"), "F原子数": g("溶剂 F 原子数"), "主盐浓度": g("主盐浓度"), "LiNO3": g("LiNO₃ 浓度")}


def differ(a, b, rel=0.01):
    return a is not None and b is not None and abs(a - b) > rel * max(abs(a), abs(b), 1e-9)


def arrows(R, coord, score, other_changed):
    """把同篇同测试比较合成箭头：(论文, 尾配方, 头配方) → 效果中位数；头 = 本平面共识方向那一侧。"""
    grp = defaultdict(list)
    n_pairs, same = 0, 0
    for r in R:
        p, ra, rb = r["论文"], r["A"]["recipe"], r["B"]["recipe"]
        a, b = coord(p, ra), coord(p, rb)
        if a is None or b is None:
            continue
        if a == b:
            same += 1
            continue
        n_pairs += 1
        e = T.effect(r)  # A 相对 B，正 = A 更好
        if score(a) >= score(b):
            grp[(p, rb, ra)].append((e, other_changed(p, ra, rb)))
        else:
            grp[(p, ra, rb)].append((-e, other_changed(p, ra, rb)))
    out = []
    for (p, tail, head), es in grp.items():
        e = float(np.median([x for x, _ in es]))
        out.append({"论文": p, "尾": tail, "头": head, "效果": e, "次数": len(es), "混改": any(c for _, c in es),
                    "结果": "好" if e > T.T else "差" if e < -T.T else "近"})
    return out, n_pairs, same


def draw_arrows(ax, A, coord):
    """蓝、灰箭头细而淡（多数规律的流向），红箭头粗、在最上层（反例）。"""
    order = sorted(A, key=lambda x: {"近": 0, "好": 1, "差": 2}[x["结果"]])
    for x in order:
        t, h = coord(x["论文"], x["尾"]), coord(x["论文"], x["头"])
        col = {"好": BETTER, "差": WORSE, "近": NEAR}[x["结果"]]
        m = min(abs(x["效果"]), 2.0) / 2.0
        lw = (1.4 + 1.8 * m) if x["结果"] == "差" else (0.6 + 1.2 * m)
        ax.add_patch(FancyArrowPatch(t, h, arrowstyle="-|>", mutation_scale=7 + 3 * lw, color=col, lw=lw,
                                     alpha={"差": 1.0, "好": 0.45, "近": 0.45}[x["结果"]],
                                     linestyle=(0, (3, 2)) if x["混改"] else "-", shrinkA=2, shrinkB=2, zorder=5 if x["结果"] == "差" else 3))


def label_red(ax, A, coord):
    """每篇有反例的论文标一次（取变化最大的红箭头头部）；标签在屏幕上互相错开。须在设好坐标范围之后调用。"""
    best = {}
    for x in A:
        if x["结果"] == "差" and (x["论文"] not in best or abs(x["效果"]) > abs(best[x["论文"]]["效果"])):
            best[x["论文"]] = x
    placed = []
    for p, x in sorted(best.items(), key=lambda t: -coord(t[0], t[1]["头"])[1]):
        h = coord(p, x["头"])
        px, py = ax.transData.transform(h) * 72 / ax.figure.dpi  # 换成磅，与 xytext 的偏移同单位
        dy = 4
        while any(abs(px + 5 - qx) < 30 and abs(py + dy - qy) < 11 for qx, qy in placed):
            dy -= 11
        placed.append((px + 5, py + dy))
        ax.annotate(p, h, xytext=(5, dy), textcoords="offset points", fontsize=8.8, color=WORSE, fontweight="bold", zorder=8, path_effects=HALO,
                    arrowprops=dict(arrowstyle="-", color=WORSE, lw=0.6) if dy < -8 else None)


def tally(A):
    c = {k: sum(x["结果"] == k for x in A) for k in ("好", "差", "近")}
    c["好占比"] = c["好"] / max(1, c["好"] + c["差"])
    c["反例论文"] = sorted({x["论文"] for x in A if x["结果"] == "差"})
    return c


def glow(ax, xs, ys, xr, yr, fy=lambda v: v, iy=lambda v: v, sigma=3.0):
    gx = np.linspace(*xr, 260)
    gy = np.linspace(fy(np.array(yr[0])), fy(np.array(yr[1])), 200)
    Hh, _, _ = np.histogram2d(xs, fy(np.asarray(ys)), bins=[gx, gy])
    G = gaussian_filter(Hh.T, sigma=sigma)
    G = np.sqrt(G / G.max())
    ax.pcolormesh(gx, iy(gy), G, cmap=GLOW, shading="flat", zorder=1, rasterized=True)


def main():
    F, n_form = Q.formulations()
    H = Q.P16.H
    lmap = {(f["论文"], f["recipe"]): f["lino3"] for f in F}
    desc = {}

    def d(p, r):
        if (p, r) not in desc:
            desc[(p, r)] = H.descriptors(p, r)[0]
        return desc[(p, r)]

    R = [r for r in load(PAIRS) if r["类别"] == "LiCu_CE" and r["比较类型"] == T.SAME]
    V = votes()

    # ---- A：非氟醚氧 × F 原子数 ----
    def cA(p, r):
        h = d(p, r)
        return None if h.get("eo") is None or h.get("fat") is None else (round(h["eo"], 4), round(h["fat"], 4))
    ptsA = np.array([c for c in (cA(f["论文"], f["recipe"]) for f in F) if c is not None])
    sdA = ptsA.std(0)
    scoreA = lambda c: c[1] / sdA[1] - c[0] / sdA[0]
    otherA = lambda p, a, b: differ(d(p, a).get("salt"), d(p, b).get("salt")) or differ(lmap.get((p, a)), lmap.get((p, b)), 0.0)
    AA, nA, sameA = arrows(R, cA, scoreA, otherA)

    # ---- B：LiNO₃ × 主盐浓度 ----
    def cB(p, r):
        s, l = d(p, r).get("salt"), lmap.get((p, r))
        return None if s is None or l is None or s <= 0 else (round(l, 4), round(s, 4))
    ptsB = np.array([c for c in (cB(f["论文"], f["recipe"]) for f in F) if c is not None])
    sdB = np.array([ptsB[:, 0].std(), np.log(ptsB[:, 1]).std()])
    scoreB = lambda c: c[0] / sdB[0] + math.log(c[1]) / sdB[1]
    otherB = lambda p, a, b: cA(p, a) != cA(p, b) and cA(p, a) is not None and cA(p, b) is not None
    AB, nB, sameB = arrows(R, cB, scoreB, otherB)
    tA, tB = tally(AA), tally(AB)

    fig = plt.figure(figsize=(16, 9), facecolor=PAPER)
    fig.text(0.04, 0.935, "Formulation space", fontsize=24, fontweight="bold", color=INK, va="bottom")
    fig.text(0.04, 0.895, "Li‖Cu comparisons within the same paper and test, drawn as arrows on two planes of project descriptors. "
             "Every arrow points toward that plane's consensus direction:\nblue = the formulation it points to has the higher CE, red = lower (a counterexample), "
             "grey = within 5 %; width = size of the change; dashed = something on the other plane changed too.",
             fontsize=10.5, color=INK2, va="bottom", linespacing=1.35)

    # A 栏
    a = fig.add_axes([0.05, 0.115, 0.42, 0.70])
    xrA, yrA = (-0.15, max(5.3, ptsA[:, 0].max() + 0.2)), (0, max(10.5, ptsA[:, 1].max() + 0.5))
    a.set_yscale("function", functions=(FWD, INV))
    glow(a, ptsA[:, 0], ptsA[:, 1], xrA, yrA, FWD, INV)
    a.scatter(ptsA[:, 0], ptsA[:, 1], s=9, c="#8a8a8a", alpha=0.45, lw=0, zorder=2)
    draw_arrows(a, AA, cA)
    a.set_xlim(*xrA); a.set_ylim(*yrA)
    label_red(a, AA, cA)
    a.set_yticks([0, 0.5, 1, 2, 4, 6, 8, 10])
    a.set_xlabel("Non-fluorinated ether O per solvent molecule", fontsize=11, color=INK)
    a.set_ylabel("F atoms per solvent molecule (square-root scale)", fontsize=11, color=INK)
    a.add_patch(FancyArrowPatch((xrA[1] * 0.95, 3.0), (xrA[1] * 0.80, 7.2), arrowstyle="-|>", mutation_scale=16, color=INK2, lw=1.6, zorder=6))
    a.text(xrA[1] * 0.99, 2.55, f"consensus · higher Li‖Cu CE\nfewer non-F ether O ({V['非氟醚氧'][1]:.0%} of votes, {V['非氟醚氧'][2]} papers)\n"
           f"more F ({V['F原子数'][1]:.0%}, {V['F原子数'][2]} papers)", ha="right", va="top", fontsize=9, color=INK2, zorder=7, path_effects=HALO)
    a.set_title(f"A · solvent structure    {nA} comparisons → {len(AA)} arrows, {len({x['论文'] for x in AA})} papers\n"
                f"toward the consensus: {tA['好']} better, {tA['差']} worse, {tA['近']} within 5 %  ({tA['好占比']:.0%} better)",
                loc="left", fontsize=11, color=INK)
    # B 栏
    b = fig.add_axes([0.56, 0.115, 0.40, 0.70])
    xrB, yrB = (-0.04, max(1.08, ptsB[:, 0].max() + 0.05)), (0.08, max(14, ptsB[:, 1].max() * 1.3))
    b.set_yscale("log")
    glow(b, ptsB[:, 0], ptsB[:, 1], xrB, yrB, np.log10, lambda v: 10 ** v)
    b.scatter(ptsB[:, 0], ptsB[:, 1], s=9, c="#8a8a8a", alpha=0.45, lw=0, zorder=2)
    draw_arrows(b, AB, cB)
    b.set_xlim(*xrB); b.set_ylim(*yrB)
    label_red(b, AB, cB)
    b.set_yticks([0.1, 0.2, 0.5, 1, 2, 4, 8]); b.set_yticklabels(["0.1", "0.2", "0.5", "1", "2", "4", "8"]); b.minorticks_off()
    b.set_xlabel("LiNO₃ (M)", fontsize=11, color=INK)
    b.set_ylabel("Main lithium salt (M, log scale)", fontsize=11, color=INK)
    b.add_patch(FancyArrowPatch((xrB[1] * 0.70, 4.2), (xrB[1] * 0.93, 9.5), arrowstyle="-|>", mutation_scale=16, color=INK2, lw=1.6, zorder=6))
    b.text(xrB[1] * 0.68, 12.5, f"consensus · higher Li‖Cu CE\nmore salt ({V['主盐浓度'][1]:.0%}, {V['主盐浓度'][2]} papers)\n"
           f"more LiNO₃ ({V['LiNO3'][1]:.0%}, {V['LiNO3'][2]} papers)", ha="right", va="top", fontsize=9, color=INK2, zorder=7, path_effects=HALO)
    b.set_title(f"B · salt and LiNO₃    {nB} comparisons → {len(AB)} arrows, {len({x['论文'] for x in AB})} papers\n"
                f"toward the consensus: {tB['好']} better, {tB['差']} worse, {tB['近']} within 5 %  ({tB['好占比']:.0%} better)",
                loc="left", fontsize=11, color=INK)
    for ax in (a, b):
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color("#bdbdbd")
        ax.tick_params(colors="#666666", labelsize=9.5)
    leg = [Line2D([], [], color=BETTER, lw=2.2, label="CE better"), Line2D([], [], color=WORSE, lw=2.2, label="CE worse (counterexample)"),
           Line2D([], [], color=NEAR, lw=2.2, label="within 5 %"), Line2D([], [], color=INK2, lw=1.6, ls=(0, (3, 2)), label="other plane changed too"),
           Line2D([], [], ls="", marker="o", ms=5, color="#8a8a8a", alpha=0.6, label="formulation (all papers; shading = how many)")]
    fig.legend(handles=leg, loc="lower left", bbox_to_anchor=(0.05, 0.022), ncol=5, frameon=False, fontsize=9.5, handlelength=2.4, columnspacing=1.6)
    fig.text(0.05, 0.006, "Axes: project descriptors (step13h), solvent values averaged by mole fraction (equal weights if amounts unknown). "
             "Red labels = papers with a counterexample arrow.", fontsize=8.3, color=MUTED, ha="left", va="bottom")
    f = OUT / "fig_formulation_space.png"
    fig.savefig(f, dpi=300, facecolor=PAPER)
    plt.close(fig)
    shutil.copy(f, SITE / "fig_formulation_space.png")
    s = {"说明": "两栏均为 Li‖Cu 同篇同测试比较；箭头指向本平面共识方向；同一对配方多测试取效果中位数",
         "配方总数": n_form, "计票": V,
         "A_溶剂结构": {"背景配方": int(len(ptsA)), "比较": nA, "两侧相同未画": sameA, "箭头": len(AA), "论文": len({x["论文"] for x in AA}), **tA},
         "B_盐与LiNO3": {"背景配方": int(len(ptsB)), "比较": nB, "两侧相同未画": sameB, "箭头": len(AB), "论文": len({x["论文"] for x in AB}), **tB},
         "红箭头": [{k: x[k] for k in ("论文", "尾", "头", "效果", "次数", "混改")} for x in AA + AB if x["结果"] == "差"]}
    (OUT / "配方空间汇总.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f, json.dumps({k: v for k, v in s.items() if k != "红箭头"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
