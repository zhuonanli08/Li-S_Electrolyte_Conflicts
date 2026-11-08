"""step25b（papertrail 环境）：描述符版分子宇宙（11-08 夜用户：“横纵坐标都用两个比较重要的描述符”“用我现有的描述符”
“好像不太分子宇宙啊”“可以直接改吧，确保像分子宇宙就好了”）。原版分子宇宙（step23，指纹 + UMAP）保留不动。

坐标 = sO（横）× InOr（纵），定义与选择理由见 step25a。和原版分子宇宙用同一套视觉语言：背景小点按局部密度着色（蓝 = 稀、红 = 密），
文献分子用醒目的绿点（含氟为金黄）叠在上面、点大小 = 论文数，常用分子用方框配结构式，区域名直接写在画面上，不要网格和色标。
与原版不同：两根轴有物理含义，所以保留很淡的刻度；QM9 小分子的两个比值是小整数之比，只落在几百个位置上，
背景画成“平滑后的密度”的抽样：每个分子在精确值附近按高斯散开（sd：sO 0.01、InOr 0.07），图注写明“看区域、不看单点”；文献分子不散开、位置精确。
11-08 夜第一版：只画非质子分子、散开 0.0035/0.022 → 点稀、成格子和横纹，用户“不太分子宇宙” → 背景改全部 QM9（同原版）、散开加大；
  P371、P381 的数值移到左栏，图上只留短标记；去掉 DEE、F6DEE 两个结构框（改文字标签）；文字加白描边。
箭头 = 同一篇里只换一种溶剂/稀释剂的 Li‖Cu CE 比较（问题 1 的两篇反例 P371、P381）：蓝 = 变好、红 = 变差。
共识方向（左上 = 溶剂氧少、杂原子多）来自计票与 meta；往“更好”方向走却变差的红箭头就是问题 1 的矛盾。
只画溶剂与稀释剂（组分角色为“溶剂”“溶剂/添加剂”）；添加剂、介体不画。图上文字英文。
输出 output/分子宇宙_描述符版_2026-11-08/分子宇宙_描述符版.png（300 dpi）、汇总.json，并复制到组会图文件夹与网站 图/（fig_molecular_map.png）。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step25b_descriptor_universe_plot.py
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.offsetbox import AnnotationBbox, OffsetImage, TextArea, VPacker
from matplotlib.patches import FancyArrowPatch
import matplotlib.patheffects as pe

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
import step13h_descriptor_figures as H

O = ROOT / "output"
OUT = O / "分子宇宙_描述符版_2026-11-08"
SES = O / "分子宇宙_SES式_2026-11-08"
MEET = O / "组会图_2026-11-08"
SITE = O / "表述与矛盾试跑_F版30篇_2026-11-04" / "网站" / "图"
CRED = O / "可信度检验_313篇_2026-11-06" / "汇总.json"
VOTES = O / "张力候选_313篇_v2_2026-11-07" / "票数.json"
plt.rcParams.update({"font.family": ["Arial", "DejaVu Sans"]})
PAPER = "white"
BG_CMAP = LinearSegmentedColormap.from_list("mu_rb", [(0, "#2c5aa0"), (0.3, "#4f86c6"), (0.49, "#8fb8de"), (0.51, "#f4a582"), (0.75, "#d6604d"), (1, "#b2182b")])
INK, INK2, GREY_TXT = "#1a1a1a", "#4a4a4a", "#6b6b6b"
GREEN, GOLD, GOLD_TXT, BLUE_TXT = "#14955a", "#f2b200", "#a87b00", "#2b5fae"
BETTER, WORSE = "#1f6fd1", "#d03b3b"
XL, YL = (-0.012, 0.405), (-0.07, 2.55)
JIT = (0.010, 0.070)  # 背景点散开的标准差（sO、InOr）：等于按这个带宽平滑后的密度抽样；只为显示密度
# 方框结构式：分子 → 方框中心（数据坐标）
CALLOUTS = {"DME": (0.215, 0.18), "DOL": (0.275, 0.45), "SULFOLANE": (0.36, 0.60), "DMC": (0.205, 1.45), "EC": (0.36, 1.36),
            "TTE": (0.150, 2.22)}
# 区域名（斜体，数据坐标）
REGIONS = [("glymes & chain ethers", (0.150, 0.415)), ("cyclic ethers", (0.198, 0.59)), ("carbonates", (0.275, 0.905)),
           ("fluorinated ethers", (0.030, 2.06)), ("no O: hydrocarbons,\nfluoroarenes", (0.018, -0.035))]
# 文字标签：分子 → (显示名, x 偏移, y 偏移, 对齐)
TEXT_ONLY = {"DEE12": ("DEE", -7, -3, "right"), "F3DEE": ("F3DEE", -7, 0, "right"), "F4DEE": ("F4DEE", -7, 0, "right"),
             "F5DEE": ("F5DEE", -7, 0, "right"), "DTFEG": ("F6DEE", -7, 0, "right"), "DMSO": ("DMSO", 7, 3, "left"), "BTFE": ("BTFE", 7, 2, "left"),
             "DBE": ("DBE", 7, -4, "left"), "TEGDME": ("TEGDME", 6, 6, "left"), "THF": ("THF", 7, -3, "left"), "FEC": ("FEC", 7, 2, "left"),
             "TEP": ("TEP", 7, 2, "left")}
HALO = [pe.withStroke(linewidth=3, foreground="white")]


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def lit_points():
    """文献溶剂/稀释剂：坐标用描述符表（DWHOLE）的原子数。"""
    out = {}
    for m in load(SES / "分子.json")["文献分子"]:
        if m.get("角色") not in ("溶剂", "溶剂/添加剂"):
            continue
        d = H.DWHOLE.get(m["id"])
        if not d or not d.get("C原子数"):
            continue
        tot, c, h = d["原子总数（含H）"], d["C原子数"], d["H原子数（含隐含氢）"]
        out[m["id"]] = {"x": d["O原子数"] / tot, "y": (tot - c - h) / c, "n": m.get("论文数") or 1, "F": (d.get("F原子数") or 0) > 0}
    return out


def evidence():
    """轴的依据：可信度检验里 sO、InOr 的方向与 q；计票里对应描述符的 Li‖Cu CE 多数占比与篇数。"""
    k = {r["特征"]: r for r in load(CRED)["Kim外部对照"]["四个特征各自的方向"]}
    v = {(r["描述符"], r["性能"]): r["同测试"] for r in load(VOTES)}
    eo, fa = v[("非氟醚氧", "Li‖Cu CE")], v[("溶剂 F 原子数", "Li‖Cu CE")]
    return {"sO_q": k["sO"]["q"], "InOr_q": k["InOr"]["q"], "sO_同号": k["sO"]["与Kim同号"], "InOr_同号": k["InOr"]["与Kim同号"],
            "非氟醚氧": (eo["多数"], eo["多数占比"], eo["篇"]), "F原子数": (fa["多数"], fa["多数占比"], fa["篇"])}


def density_rank(x, y, bins=320):
    Hh, xe, ye = np.histogram2d(x, y, bins=bins, range=[XL, YL])
    i = np.clip(np.searchsorted(xe, x) - 1, 0, bins - 1)
    j = np.clip(np.searchsorted(ye, y) - 1, 0, bins - 1)
    d = np.log1p(Hh[i, j]) + 1e-9 * np.random.default_rng(1).random(len(x))
    return np.argsort(np.argsort(d)) / (len(d) - 1)


def callout(ax, mid, xy_pt, xy_box):
    f = OUT / "结构图" / f"{mid}.png"
    f = f if f.exists() else SES / "结构图" / f"{mid}.png"
    label = {"DEE12": "DEE (1,2-diethoxyethane)", "DTFEG": "F6DEE"}.get(mid, mid)
    pack = VPacker(children=[OffsetImage(plt.imread(f), zoom=0.24), TextArea(label, textprops=dict(color=INK, fontsize=9.5, fontweight="bold"))],
                   align="center", pad=0, sep=1)
    ax.add_artist(AnnotationBbox(pack, xy_pt, xybox=xy_box, xycoords="data", boxcoords="data", frameon=True, pad=0.22,
                                 bboxprops=dict(fc="white", ec=INK2, lw=1.1), arrowprops=dict(arrowstyle="-", color=INK2, lw=1.0, shrinkA=0, shrinkB=3),
                                 zorder=7))


def main():
    bg = np.load(OUT / "背景_sO_InOr.npz")
    rng = np.random.default_rng(0)
    bx = bg["sO"] + rng.normal(0, JIT[0], len(bg["sO"]))
    by = bg["InOr"] + rng.normal(0, JIT[1], len(bg["InOr"]))
    keep = (bx > XL[0]) & (bx < XL[1]) & (by > YL[0]) & (by < YL[1])
    L = lit_points()
    ev = evidence()
    q1 = load(MEET / "组会图数据.json")["q1"]
    s371, s381 = q1["P371 系列（Taur，60 °C）"], q1["P381（T01）DBE / TTE"]

    fig = plt.figure(figsize=(16, 9), facecolor=PAPER)
    ax = fig.add_axes([0.335, 0.125, 0.645, 0.83])
    ax.set_facecolor(PAPER)
    r = density_rank(bx[keep], by[keep])
    o = np.argsort(r)
    ax.scatter(bx[keep][o], by[keep][o], s=0.9, c=r[o], cmap=BG_CMAP, vmin=0, vmax=1, lw=0, alpha=0.9, rasterized=True, zorder=1)
    ids = list(L)
    X = np.array([L[i]["x"] for i in ids]); Y = np.array([L[i]["y"] for i in ids])
    N = np.array([L[i]["n"] for i in ids], float); Fm = np.array([L[i]["F"] for i in ids])
    size = 16 + 10 * np.sqrt(N)
    ax.scatter(X[~Fm], Y[~Fm], s=size[~Fm], c=GREEN, lw=0.8, edgecolors="white", zorder=4)
    ax.scatter(X[Fm], Y[Fm], s=size[Fm] + 10, c=GOLD, lw=0.9, edgecolors=INK, zorder=5)
    P = {i: (L[i]["x"], L[i]["y"]) for i in ids}

    # 同篇换溶剂的箭头（问题 1 的两篇反例）
    def arrow(a, b, better, rad):
        ax.add_patch(FancyArrowPatch(P[a], P[b], connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>", mutation_scale=15,
                                     color=BETTER if better else WORSE, lw=2.2, shrinkA=6, shrinkB=6, zorder=6))
    base = s371["DEE"]
    for tgt, key, rad in (("F3DEE", "F3DEE", 0.55), ("F4DEE", "F4DEE", -0.30), ("F5DEE", "F5DEE", -0.38), ("DTFEG", "F6DEE", -0.42)):
        arrow("DEE12", tgt, s371[key] > base, rad)
    arrow("DBE", "TTE", s381[1] > s381[0], 0.0)
    ax.text(P["DEE12"][0] + 0.024, P["DEE12"][1] + 0.30, "P371", ha="left", va="center", fontsize=10.5, color=INK, fontweight="bold", zorder=8,
            path_effects=HALO)
    ax.text(P["DBE"][0] - 0.004, 1.02, "P381", ha="right", va="center", fontsize=10.5, color=INK, fontweight="bold", zorder=8, path_effects=HALO)
    # 共识方向
    ax.add_patch(FancyArrowPatch((0.395, 1.92), (0.335, 2.40), arrowstyle="-|>", mutation_scale=18, color=INK2, lw=1.6, zorder=6))
    ax.text(0.392, 2.43, "consensus · higher Li‖Cu CE\n(less solvent O, more F / heteroatoms)", ha="right", va="bottom", fontsize=9.5, color=INK2, zorder=8)

    for mid, box in CALLOUTS.items():
        if mid in P:
            callout(ax, mid, P[mid], box)
    for mid, (lab, dx, dy, ha) in TEXT_ONLY.items():
        if mid in P:
            ax.annotate(lab, P[mid], xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=9, color=INK, zorder=8,
                        fontweight="bold" if "DEE" in lab else "normal", path_effects=HALO)
    for t, (x, y) in REGIONS:
        ax.text(x, y, t, ha="center", va="center", fontsize=10.5, color=INK2, fontstyle="italic", zorder=7, linespacing=1.1, path_effects=HALO)
    ax.set_xlim(*XL); ax.set_ylim(*YL)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#cfcfcf")
    ax.tick_params(colors="#9a9a9a", labelsize=9, length=3)
    ax.set_xticks([0, 0.1, 0.2, 0.3, 0.4]); ax.set_yticks([0, 0.5, 1, 1.5, 2, 2.5])
    ax.set_xlabel("sO · solvent O atoms ÷ all atoms   (more O → stronger solvation) →", color=INK2, fontsize=10.5)
    ax.set_ylabel("InOr · non-C/H atoms (F, O, N, S) ÷ C   (more F → up) →", color=INK2, fontsize=10.5)

    # 左栏文字（SES 式）
    tx = 0.018
    fig.text(tx, 0.905, "Molecular universe", fontsize=24, fontweight="bold", color=INK, va="bottom")
    fig.text(tx, 0.872, "· two project descriptors as axes", fontsize=14, color=INK, va="bottom")
    fig.text(tx, 0.808, f"{int(keep.sum()):,} small molecules (QM9: all stable\nC/N/O/F molecules with ≤ 9 heavy atoms)", fontsize=11.5, color=BLUE_TXT,
             va="bottom", linespacing=1.2)
    fig.text(tx, 0.772, f"{len(ids)} solvents & diluents from 313 Li–S papers", fontsize=12, color=GREEN, fontweight="bold", va="bottom")
    eo, fa = ev["非氟醚氧"], ev["F原子数"]
    why = (f"Why these two axes (Li‖Cu CE):\n"
           f"• sO: more solvent O → lower CE\n   (meta q = {ev['sO_q']:.2f}; votes on non-F ether O:\n   {eo[1]:.0%} 'worse', {eo[2]} papers)\n"
           f"• InOr: more heteroatoms → higher CE\n   (meta q = {ev['InOr_q']:.2f}; votes on F atoms:\n   {fa[1]:.0%} 'better', {fa[2]} papers)\n"
           "Both match Kim et al. 2023 (PNAS).")
    fig.text(tx, 0.745, why, fontsize=10.2, color=INK, va="top", linespacing=1.3)
    yy = 0.43
    for mk, txt in (((GREEN, "white"), "used in the papers · size = number of papers"), ((GOLD, INK), "contains fluorine")):
        a = fig.add_axes([tx, yy - 0.012, 0.016, 0.028]); a.axis("off"); a.set_xlim(-1, 1); a.set_ylim(-1, 1)
        a.scatter([0], [0], s=110, c=mk[0], edgecolors=mk[1], linewidths=1)
        fig.text(tx + 0.02, yy, txt, fontsize=10.5, color=INK, va="center")
        yy -= 0.042
    for col, txt in ((BETTER, "same-paper solvent swap: CE better"), (WORSE, "same-paper solvent swap: CE worse")):
        a = fig.add_axes([tx, yy - 0.012, 0.016, 0.028]); a.axis("off"); a.set_xlim(0, 1); a.set_ylim(-1, 1)
        a.add_patch(FancyArrowPatch((0.0, 0), (1.0, 0), arrowstyle="-|>", mutation_scale=11, color=col, lw=2))
        fig.text(tx + 0.02, yy, txt, fontsize=10.5, color=INK, va="center")
        yy -= 0.042
    fig.text(tx, yy - 0.005, "Open question 1, read from position:\nthe swaps move up (more F), the 'better'\ndirection, yet two of them get worse.",
             fontsize=10.5, color=GOLD_TXT, fontweight="bold", va="top", linespacing=1.3)
    fig.text(tx, yy - 0.105, f"P371 (60 °C, Aurbach): DEE {base:.1f} → F3DEE {s371['F3DEE']:.1f} %  ✗\n"
             f"   → F4 / F5 / F6DEE {s371['F4DEE']:.1f} / {s371['F5DEE']:.1f} / {s371['F6DEE']:.1f} %  ✓\n"
             f"P381 (30 °C): DBE {s381[0]:.1f} → TTE {s381[1]:.1f} %  ✗", fontsize=10, color=INK, va="top", linespacing=1.4)
    fig.text(tx, 0.012, "Background: QM9 (Ramakrishnan et al., Sci. Data 2014); colour = how many molecules nearby (blue = few, red = many). Small-molecule ratios take few distinct values, "
             f"so the background is drawn as a sample of the smoothed density (Gaussian sd {JIT[0]} in sO, {JIT[1]} in InOr): read regions, not single dots;\n"
             "literature dots are exact (descriptor table, step13h). Only solvents and diluents are shown (additives, mediators omitted). "
             "sO counts O donors only (nitrile N not counted). Arrows: Li‖Cu CE within one paper; papers are not compared with each other.",
             fontsize=8.1, color=GREY_TXT, va="bottom", linespacing=1.3)
    f = OUT / "分子宇宙_描述符版.png"
    fig.savefig(f, dpi=300, facecolor=PAPER)
    plt.close(fig)
    shutil.copy(f, MEET / "fig_molecular_map.png")
    shutil.copy(f, SITE / "fig_molecular_map.png")
    s = {"背景分子（QM9 全部含碳分子，画在范围内）": int(keep.sum()), "QM9 总数": int(bg["n_qm9"]), "其中质子性（含 O–H/N–H，照画）": int(bg["n_protic"]),
         "文献溶剂/稀释剂": len(ids), "含氟": int(Fm.sum()), "背景散开标准差": JIT, "轴的依据": ev,
         "箭头": {"P371（Taur，60 °C）": s371, "P381（T01）DBE→TTE": s381},
         "关键分子坐标": {i: [round(L[i]["x"], 3), round(L[i]["y"], 3)] for i in list(CALLOUTS) + list(TEXT_ONLY) if i in L}}
    (OUT / "汇总.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f, json.dumps(s, ensure_ascii=False)[:600])


if __name__ == "__main__":
    main()
