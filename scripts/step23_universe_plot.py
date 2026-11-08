"""step23 第三步（papertrail 环境）：SES 式分子宇宙图（11-08 用户：“你看看人家 SES 怎么画的，你完全是两模两样”）。

照 SES AI Molecular Universe（NVIDIA 技术博客 2025-05 图 2、图 3）的版式：黑底；背景分子按局部密度着色（紫 → 橙）；文献报道过的分子用亮绿点叠在上面；
常用分子用白框配结构式标出，白色引线指到点上；文字直接写在画面上，不要坐标轴和图例框。
  左 = 全景：QM9 全部 133,885 个分子＋313 篇的 167 个中性有机分子（坐标.npz）→ 文献分子只落在化学空间的几个角落。
  右 = 近景：167 个分子＋各自最相近的 120 个 QM9 分子（共 8,811 个）重新降维（坐标_近邻.npz）→ 文献分子按结构分成几块，
       每块周围的暗点 = 结构相近、但 313 篇里没人用过的小分子。红点 = 无定论问题 1 的含氟稀释剂/溶剂。
图上文字英文。输出 output/分子宇宙_SES式_2026-11-08/分子宇宙_SES式.png（300 dpi），并复制到网站 图/ 与 组会图文件夹。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step23_universe_plot.py
"""
import json
import shutil
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.offsetbox import AnnotationBbox, OffsetImage, TextArea, VPacker

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
OUT = ROOT / "output" / "分子宇宙_SES式_2026-11-08"
SITE = ROOT / "output" / "表述与矛盾试跑_F版30篇_2026-11-04" / "网站" / "图"
MEET = ROOT / "output" / "组会图_2026-11-08"
plt.rcParams.update({"font.family": ["Arial", "DejaVu Sans"]})

BG_CMAP = LinearSegmentedColormap.from_list("ses", ["#2b0a57", "#5b1a8f", "#9b2f9a", "#d4508a", "#f6874f", "#fdc35a"])
GREEN, RED, PURPLE_TXT, GREY_TXT = "#39e75f", "#ff4040", "#c77dff", "#9a9a9a"
# 无定论问题 1 涉及的含氟稀释剂/溶剂（与 step13m 的 Q1_MOLS 一致，只取含氟一侧）
Q1_F = {"TTE", "BTFE", "OFE", "TFEE", "TFTFE", "F3DEE", "F4DEE", "F5DEE", "DTFEG", "F4DMB", "FB", "F4EO2"}
# 近景里画结构式的分子与标注框位置（数据坐标；坐标.npz 由固定随机种子算出，换数据要重看位置）
CALLOUTS = {"DOL": (-1.6, 11.3), "EC": (5.2, 13.0), "SULFOLANE": (3.4, 4.6), "DME": (14.6, 8.6), "TTE": (6.4, 1.0), "DMC": (6.4, -4.6)}
# 近景的“大陆”名：放在该类分子附近（数据坐标）
REGIONS = [("chain ethers &\nfluorinated ethers", (14.8, 2.6), "left"), ("carbonates, esters, amides", (12.0, -5.9), "left"),
           ("cyclic carbonates", (8.0, 10.75), "left"), ("cyclic ethers", (2.4, 10.9), "center"),
           ("aromatics, S / Se / N rings\n(additives, redox mediators)", (-3.6, 4.6), "center"), ("lactams, cyclic ureas", (4.0, 6.9), "center")]


def density(xy, bins=300):
    """每个点所在格子的点数（log），用于按局部密度着色。"""
    H, xe, ye = np.histogram2d(xy[:, 0], xy[:, 1], bins=bins)
    i = np.clip(np.searchsorted(xe, xy[:, 0]) - 1, 0, bins - 1)
    j = np.clip(np.searchsorted(ye, xy[:, 1]) - 1, 0, bins - 1)
    return np.log1p(H[i, j])


def background(ax, xy, s, bins):
    d = density(xy, bins)
    o = np.argsort(d)
    ax.scatter(xy[o, 0], xy[o, 1], s=s, c=d[o], cmap=BG_CMAP, lw=0, alpha=0.95, rasterized=True)


def callout(ax, mid, xy_pt, xy_box):
    img = plt.imread(OUT / "结构图" / f"{mid}.png")
    pack = VPacker(children=[OffsetImage(img, zoom=0.30), TextArea(mid, textprops=dict(color="white", fontsize=10, fontweight="bold"))],
                   align="center", pad=0, sep=1)
    ab = AnnotationBbox(pack, xy_pt, xybox=xy_box, xycoords="data", boxcoords="data", frameon=True, pad=0.25,
                        bboxprops=dict(fc="black", ec="white", lw=1.4), arrowprops=dict(arrowstyle="-", color="white", lw=1.2, shrinkA=0, shrinkB=3),
                        zorder=6)
    ax.add_artist(ab)


def main():
    meta = json.loads((OUT / "分子.json").read_text(encoding="utf-8"))
    M = meta["文献分子"]
    ids = [m["id"] for m in M]
    npap = np.array([m["论文数"] or 1 for m in M], float)
    q1 = np.array([i in Q1_F for i in ids])
    g = np.load(OUT / "坐标.npz")
    ge, nb = g["emb"], int(g["n_bg"])
    loc = np.load(OUT / "坐标_近邻.npz")
    le, nl = loc["emb"], int(loc["n_lit"])

    fig = plt.figure(figsize=(16, 9), facecolor="black")
    # ---- 左：全景 ----
    a = fig.add_axes([0.015, 0.05, 0.35, 0.66])
    a.set_facecolor("black"); a.axis("off")
    background(a, ge[:nb], s=0.35, bins=420)
    lit = ge[nb:]
    a.scatter(lit[~q1, 0], lit[~q1, 1], s=10, c=GREEN, lw=0, zorder=4)
    a.scatter(lit[q1, 0], lit[q1, 1], s=12, c=RED, lw=0, zorder=5)
    pos = {i: lit[k] for k, i in enumerate(ids)}
    for anchor, text, dx, dy, ha in (("DME", "chain ethers, carbonates,\namides, fluorinated ethers", 2.2, -1.2, "left"),
                                     ("DOL", "cyclic ethers\n(DOL, THF)", 0.0, -1.0, "center"),
                                     ("EC", "EC", 0.5, 0.6, "left"), ("FEC", "PC, FEC", 0.6, -0.9, "left"),
                                     ("SULFOLANE", "sulfolane", 0.5, 0.5, "left"),
                                     ("TOLUENE", "aromatics,\nS / Se rings", 0.0, 1.7, "center")):
        x, y = pos[anchor]
        a.text(x + dx, y + dy, text, ha=ha, va="top" if dy < 0 else "bottom", fontsize=9, color="white", linespacing=1.15, zorder=6)
    fig.text(0.015, 0.935, "Molecular universe", fontsize=22, fontweight="bold", color="white", va="bottom")
    fig.text(0.015, 0.875, f"{nb:,} small molecules (QM9: all stable C/N/O/F\nmolecules with ≤ 9 heavy atoms in GDB-17)",
             fontsize=11.5, color=PURPLE_TXT, va="bottom", linespacing=1.2)
    fig.text(0.015, 0.835, f"{len(M)} molecules used in 313 Li–S papers", fontsize=13, color=GREEN, fontweight="bold", va="bottom")
    fig.text(0.015, 0.808, "they sit in a few corners of the map", fontsize=11, color="white", va="bottom")

    # ---- 右：近景 ----
    b = fig.add_axes([0.40, 0.07, 0.59, 0.80])
    b.set_facecolor("black"); b.axis("off")
    background(b, le[:-nl], s=7, bins=140)
    L = le[-nl:]
    size = 14 + 9 * np.sqrt(npap)
    b.scatter(L[~q1, 0], L[~q1, 1], s=size[~q1], c=GREEN, lw=0.6, edgecolors="black", zorder=4)
    b.scatter(L[q1, 0], L[q1, 1], s=size[q1] + 10, c=RED, lw=0.6, edgecolors="black", zorder=5)
    b.set_xlim(-7.6, 18.2); b.set_ylim(-7.2, 14.6)
    lpos = {i: L[k] for k, i in enumerate(ids)}
    for mid, box in CALLOUTS.items():
        callout(b, mid, tuple(lpos[mid]), box)
    for text, (x, y), ha in REGIONS:
        b.text(x, y, text, ha=ha, va="center", fontsize=9.5, color="#e8e8e8", fontstyle="italic", linespacing=1.15, zorder=6)
    b.text(0.0, 1.075, f"Close-up · the {len(M)} literature molecules and their {len(le) - nl:,} nearest QM9 neighbours (re-mapped)",
           transform=b.transAxes, fontsize=12.5, color="white", fontweight="bold", va="bottom")
    b.text(0.0, 1.035, "dim dots = similar small molecules that none of the 313 papers used · dot size = number of papers",
           transform=b.transAxes, fontsize=10, color=PURPLE_TXT, va="bottom")
    b.text(0.0, 0.035, "● open question 1 · fluorinated diluents\n   (TTE, BTFE, F3–F6DEE, FB …)", transform=b.transAxes, ha="left", va="bottom",
           fontsize=11, color=RED, fontweight="bold", linespacing=1.2)
    b.text(0.0, 0.13, f"● used in the 313 papers ({len(M)})", transform=b.transAxes, ha="left", va="bottom", fontsize=11, color=GREEN, fontweight="bold")
    fig.text(0.015, 0.012, "Position = structural similarity (Morgan fingerprint r = 2, Jaccard distance, UMAP — the same recipe as SES AI's Molecular Universe). "
             "Salts, ions and polysulfides not shown. 62 of the 167 molecules are themselves in QM9;\nlarger ones (e.g. TEGDME, TTE) sit next to their closest "
             "small relatives. Background: QM9 (Ramakrishnan et al., Sci. Data 2014).", fontsize=8.3, color=GREY_TXT, va="bottom", linespacing=1.3)
    f = OUT / "分子宇宙_SES式.png"
    fig.savefig(f, dpi=300, facecolor="black")
    plt.close(fig)
    for d in (SITE, MEET):
        shutil.copy(f, d / "fig_molecular_universe.png")
    s = {"背景分子": nb, "文献分子": len(M), "其中在 QM9 中": sum(m["在QM9中"] for m in M), "近景背景分子": int(len(le) - nl),
         "问题 1 含氟分子": sorted(i for i in ids if i in Q1_F)}
    (OUT / "汇总.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f, s)


if __name__ == "__main__":
    main()
