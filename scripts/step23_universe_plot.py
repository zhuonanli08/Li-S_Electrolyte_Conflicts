"""step23 第三步（papertrail 环境）：SES 式分子宇宙图（11-08 用户：“你看看人家 SES 怎么画的，你完全是两模两样”）。

照 SES AI Molecular Universe（NVIDIA 技术博客 2025-05 图 2、图 3）的做法：背景分子按局部密度着色；文献报道过的分子用醒目的点叠在上面；
常用分子用方框配结构式标出，引线指到点上；文字直接写在画面上，不要坐标轴和图例框。
11-08 晚用户：“可以，但是不要黑底的这种图，改成白底＋合适配色” → 白底；结构式白底。
11-08 晚用户：“颜色改成红蓝渐变配色吧，这样更明显一点” → 背景密度蓝（稀）→ 紫 → 红（密），中间不经过近白色；文献分子绿不变；
  问题 1 含氟分子由红改金黄（避免与高密度红混淆）。
11-08 晚用户：“我看到的好像还是紫色”“右边画的跟左边不太一样，太平面了，没有左边好看” →
  配色改为蓝红对比（RdBu 去掉中间的白，浅蓝直接接浅橙红，不经过紫）；按局部密度的排名着色，蓝、红各占一部分；
  近景改为每个文献分子取 400 个近邻（23,132 个背景分子）、点画小、密度分得更细，和全景一样有疏密纹理。
  左 = 全景：QM9 全部 133,885 个分子＋313 篇的 167 个中性有机分子（坐标.npz）→ 文献分子只落在化学空间的几个角落。
  右 = 近景：168 个分子＋各自最相近的 400 个 QM9 分子（共 23,132 个）重新降维（坐标_近邻.npz）→ 文献分子按结构分成几块，
       每块周围的浅色点 = 结构相近、但 313 篇里没人用过的小分子。红点 = 无定论问题 1 的含氟稀释剂/溶剂。
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

PAPER = "white"
BG_CMAP = LinearSegmentedColormap.from_list("mu_rb", [(0, "#2c5aa0"), (0.3, "#4f86c6"), (0.49, "#8fb8de"), (0.51, "#f4a582"), (0.75, "#d6604d"), (1, "#b2182b")])
INK, INK2 = "#1a1a1a", "#4a4a4a"
GREEN, GOLD, GOLD_TXT, BLUE_TXT, GREY_TXT = "#14955a", "#f2b200", "#a87b00", "#2b5fae", "#6b6b6b"
# 无定论问题 1 涉及的含氟稀释剂/溶剂（与 step13m 的 Q1_MOLS 一致，只取含氟一侧）
Q1_F = {"TTE", "BTFE", "OFE", "TFEE", "TFTFE", "F3DEE", "F4DEE", "F5DEE", "DTFEG", "F4DMB", "FB", "F4EO2"}
# 近景里画结构式的分子与标注框位置（数据坐标；坐标.npz 由固定随机种子算出，换数据要重看位置）
# 11-08 晚 DEE 修正后加入 DEE12（168 个分子），坐标重算，位置按新坐标重定
CALLOUTS = {"DOL": (13.8, 12.9), "EC": (-1.4, 11.6), "SULFOLANE": (17.0, 8.4), "DME": (17.0, 3.6), "TTE": (17.0, -2.4), "DMC": (3.9, -3.0)}
# 近景的“大陆”名：放在该类分子附近（数据坐标）
REGIONS = [("chain ethers &\nfluorinated ethers", (13.3, -3.9), "center"), ("carbonates, esters, amides", (9.0, -4.7), "center"),
           ("cyclic carbonates", (4.3, 12.0), "center"), ("cyclic ethers", (10.0, 12.1), "center"),
           ("aromatics, S / Se / N rings\n(additives, redox mediators)", (-1.6, 6.5), "center"), ("lactams, cyclic ureas", (3.5, 7.8), "center")]
XLIM, YLIM = (-5.6, 18.8), (-6.6, 14.4)


def usage(M):
    """11-08 夜：原句“they sit in a few corners”只对一半——集中的是用量，不是种类（文献分子两两相似度中位 0.04，低于随机 QM9 对的 0.07）。
    改报用量：非氟醚（链醚、环醚、缩醛，不含二硫醚等含“醚”字的有机硫/硒）占全部“论文 × 分子”使用次数的比例，以及只在 1 篇出现的分子数。"""
    def ether(c):
        c = c or ""
        if any(k in c for k in ("有机硫", "二硫化碳", "硒", "碲", "硅", "氟化醚")):
            return False
        return "醚" in c or "缩醛" in c
    n = {m["id"]: m["论文数"] or 0 for m in M}
    tot = sum(n.values())
    return {"非氟醚使用占比": sum(n[m["id"]] for m in M if ether(m.get("化学类别"))) / tot, "使用次数": tot,
            "DME": n.get("DME"), "DOL": n.get("DOL"), "只在1篇出现": sum(v <= 1 for v in n.values())}


def density(xy, bins=300):
    """每个点所在格子的点数（log），用于按局部密度着色。"""
    H, xe, ye = np.histogram2d(xy[:, 0], xy[:, 1], bins=bins)
    i = np.clip(np.searchsorted(xe, xy[:, 0]) - 1, 0, bins - 1)
    j = np.clip(np.searchsorted(ye, xy[:, 1]) - 1, 0, bins - 1)
    return np.log1p(H[i, j])


def background(ax, xy, s, bins):
    d = density(xy, bins)
    r = np.argsort(np.argsort(d + 1e-9 * np.random.default_rng(0).random(len(d)))) / (len(d) - 1)  # 按密度排名着色：蓝、红各占一部分
    o = np.argsort(r)
    ax.scatter(xy[o, 0], xy[o, 1], s=s, c=r[o], cmap=BG_CMAP, vmin=0, vmax=1, lw=0, alpha=0.9, rasterized=True)


def callout(ax, mid, xy_pt, xy_box):
    img = plt.imread(OUT / "结构图" / f"{mid}.png")
    pack = VPacker(children=[OffsetImage(img, zoom=0.30), TextArea(mid, textprops=dict(color=INK, fontsize=10, fontweight="bold"))],
                   align="center", pad=0, sep=1)
    ab = AnnotationBbox(pack, xy_pt, xybox=xy_box, xycoords="data", boxcoords="data", frameon=True, pad=0.25,
                        bboxprops=dict(fc="white", ec=INK2, lw=1.2), arrowprops=dict(arrowstyle="-", color=INK2, lw=1.1, shrinkA=0, shrinkB=3),
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

    fig = plt.figure(figsize=(16, 9), facecolor=PAPER)
    # ---- 左：全景 ----
    a = fig.add_axes([0.015, 0.05, 0.35, 0.66])
    a.set_facecolor(PAPER); a.axis("off")
    background(a, ge[:nb], s=0.35, bins=420)
    lit = ge[nb:]
    a.scatter(lit[~q1, 0], lit[~q1, 1], s=12, c=GREEN, lw=0.3, edgecolors="white", zorder=4)
    a.scatter(lit[q1, 0], lit[q1, 1], s=18, c=GOLD, lw=0.6, edgecolors=INK, zorder=5)
    pos = {i: lit[k] for k, i in enumerate(ids)}
    for anchor, text, dx, dy, ha in (("DME", "chain ethers, carbonates,\namides, fluorinated ethers", 2.2, -1.2, "left"),
                                     ("DOL", "cyclic ethers\n(DOL, THF)", 0.0, -1.0, "center"),
                                     ("EC", "EC", 0.5, 0.6, "left"), ("FEC", "PC, FEC", 0.6, -0.9, "left"),
                                     ("SULFOLANE", "sulfolane", 0.5, 0.5, "left"),
                                     ("TOLUENE", "aromatics,\nS / Se rings", -0.8, 0.0, "right")):
        x, y = pos[anchor]
        a.text(x + dx, y + dy, text, ha=ha, va="top" if dy < 0 else "bottom", fontsize=9, color=INK, linespacing=1.15, zorder=6)
    fig.text(0.015, 0.935, "Molecular universe", fontsize=22, fontweight="bold", color=INK, va="bottom")
    fig.text(0.015, 0.875, f"{nb:,} small molecules (QM9: all stable C/N/O/F\nmolecules with ≤ 9 heavy atoms in GDB-17)",
             fontsize=11.5, color=BLUE_TXT, va="bottom", linespacing=1.2)
    fig.text(0.015, 0.835, f"{len(M)} molecules used in 313 Li–S papers", fontsize=13, color=GREEN, fontweight="bold", va="bottom")
    u = usage(M)
    fig.text(0.015, 0.758, f"use is concentrated: non-fluorinated ethers are {u['非氟醚使用占比']:.0%} of all uses\n"
             f"(DME in {u['DME']} papers, DOL in {u['DOL']}); {u['只在1篇出现']} of the {len(M)} molecules\nappear in only one paper",
             fontsize=11, color=INK, va="bottom", linespacing=1.25)

    # ---- 右：近景 ----
    b = fig.add_axes([0.40, 0.07, 0.59, 0.80])
    b.set_facecolor(PAPER); b.axis("off")
    background(b, le[:-nl], s=1.6, bins=300)
    L = le[-nl:]
    size = 14 + 9 * np.sqrt(npap)
    b.scatter(L[~q1, 0], L[~q1, 1], s=size[~q1], c=GREEN, lw=0.7, edgecolors="white", zorder=4)
    b.scatter(L[q1, 0], L[q1, 1], s=size[q1] + 14, c=GOLD, lw=0.9, edgecolors=INK, zorder=5)
    b.set_xlim(*XLIM); b.set_ylim(*YLIM)
    lpos = {i: L[k] for k, i in enumerate(ids)}
    for mid, box in CALLOUTS.items():
        callout(b, mid, tuple(lpos[mid]), box)
    for text, (x, y), ha in REGIONS:
        b.text(x, y, text, ha=ha, va="center", fontsize=9.5, color=INK2, fontstyle="italic", linespacing=1.15, zorder=6)
    b.text(0.0, 1.075, f"Close-up · the {len(M)} literature molecules and their {len(le) - nl:,} nearest QM9 neighbours (re-mapped)",
           transform=b.transAxes, fontsize=12.5, color=INK, fontweight="bold", va="bottom")
    b.text(0.0, 1.035, "background = similar small molecules no paper used (not screened for stability — not candidates) · "
           "blue = few, red = many nearby · dot size = papers", transform=b.transAxes, fontsize=9.5, color=BLUE_TXT, va="bottom")
    b.text(0.0, -0.01, "● open question 1 · fluorinated diluents\n   (TTE, BTFE, F3–F6DEE, FB …)", transform=b.transAxes, ha="left", va="bottom",
           fontsize=11, color=GOLD_TXT, fontweight="bold", linespacing=1.2)
    b.text(0.0, 0.075, f"● used in the 313 papers ({len(M)})", transform=b.transAxes, ha="left", va="bottom", fontsize=11, color=GREEN, fontweight="bold")
    fig.text(0.015, 0.012, "Position = shared substructures, not properties (Morgan fingerprint r = 2, presence only; Jaccard distance; UMAP — SES AI's recipe): "
             "glymes of different length coincide, and the degree of fluorination cannot be read from position.\n"
             f"Salts, ions and polysulfides not shown. {sum(m['在QM9中'] for m in M)} of the {len(M)} molecules are themselves in QM9; larger ones (e.g. TEGDME, TTE) "
             "sit next to their closest small relatives. Background: QM9 (Ramakrishnan et al., Sci. Data 2014).", fontsize=8.3, color=GREY_TXT, va="bottom", linespacing=1.3)
    f = OUT / "分子宇宙_SES式.png"
    fig.savefig(f, dpi=300, facecolor=PAPER)
    plt.close(fig)
    for d in (SITE, MEET):
        shutil.copy(f, d / "fig_molecular_universe.png")
    s = {"背景分子": nb, "文献分子": len(M), "其中在 QM9 中": sum(m["在QM9中"] for m in M), "近景背景分子": int(len(le) - nl),
         "问题 1 含氟分子": sorted(i for i in ids if i in Q1_F), "用量": u}
    (OUT / "汇总.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f, s)


if __name__ == "__main__":
    main()
