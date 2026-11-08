"""组会第 13 页“文字向量地图”（11-08 用户同意；zy 批注：解释向量转化方法，在地图中标注差距明显的两点并解释）。

左：四组示例句子的向量相似度——立场相反的两句话几乎重合（0.95–0.96），讲两件事的才远，说明向量按“讲什么”摆放、不按“支持还是反对”。
右：7477 条机制说法的二维地图（step22：bge-small-zh → UMAP），无定论问题 1 两派用蓝橙标出，“离得最近、立场相反”的一对连线并注释。
图英文。输出 output/组会图_2026-11-08/fig_p13_vectors.png（300 dpi），复制到网站 图/。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/fig_p13_vectors.py
"""
import json
import shutil
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
O = ROOT / "output"
ATLAS = O / "说法地图_313篇_2026-11-08" / "全部说法二维.json"
EV = O / "机制证据_313篇_2026-11-08" / "机制证据.json"
OUT = O / "组会图_2026-11-08"
SITE = O / "表述与矛盾试跑_F版30篇_2026-11-04" / "网站" / "图"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE, RED = "#2a78d6", "#eb6834", "#d03b3b"
# 最近的相反一对的英文转述（Claude 据 step20 的一句话写；只用于图注）
EN = {"P179|MC10": "P179: HFE decomposes quickly to a passivating LiF layer\n→ better Li compatibility (author’s hypothesis)",
      "P338|MC11": "P338: LiF comes from LiFSA reduction;\nHFE decomposing to LiF is unlikely"}
plt.rcParams.update({"font.family": ["Arial", "DejaVu Sans"], "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False})


def main():
    a = json.loads(ATLAS.read_text(encoding="utf-8"))
    pts = a["说法"]
    xy = np.array([[p["x"], p["y"]] for p in pts])
    key = {f"{p['论文']}|{p['机制']}": k for k, p in enumerate(pts)}
    q = a["问题"]["T1"]
    pair = a["最近的相反一对"]["T1"]
    ev = json.loads(EV.read_text(encoding="utf-8"))["T1"]
    fig = plt.figure(figsize=(14, 6.4))
    # 左：示例句子的相似度
    ax = fig.add_axes([0.035, 0.16, 0.25, 0.66])
    ex = a["示例"]
    cols = [RED if e["关系"].endswith("opposite stance") else MUTED for e in ex]
    yy = np.arange(len(ex))[::-1]
    ax.barh(yy, [e["相似度"] for e in ex], color=cols, height=0.55)
    for y, e in zip(yy, ex):
        ax.text(0.02, y + 0.42, f"“{e['英文1']}”\nvs “{e['英文2']}”", fontsize=7.8, color=INK, va="bottom", linespacing=1.2)
        ax.text(e["相似度"] + 0.015, y, f"{e['相似度']:.2f}", va="center", fontsize=10, color=INK, fontweight="bold")
        ax.text(0.02, y, e["关系"], va="center", fontsize=8.3, color="white", fontweight="bold")
    ax.set_xlim(0, 1.08); ax.set_ylim(-0.6, len(ex) - 0.05)
    ax.set_yticks([]); ax.set_xlabel("cosine similarity of the two sentence vectors")
    ax.spines["left"].set_visible(False)
    ax.set_title("Why opposite claims are neighbours\n(bge-small-zh, sentences in Chinese)", fontsize=10.5, loc="left", color=INK)
    # 中：全部说法地图（按 0.5–99.5 分位定范围，去掉少数离群小簇对版面的影响），方框 = 问题 1 所在区域
    m = fig.add_axes([0.31, 0.10, 0.27, 0.72])
    lo, hi = np.percentile(xy, 0.5, axis=0), np.percentile(xy, 99.5, axis=0)
    keep = np.all((xy >= lo - (hi - lo) * 0.04) & (xy <= hi + (hi - lo) * 0.04), axis=1)  # 不画 1% 以内的离群小簇
    m.scatter(xy[keep, 0], xy[keep, 1], s=2.2, color="#cfd6de", alpha=0.6, lw=0, rasterized=True)
    ii = q["A"] + q["B"]
    for side, col in (("A", BLUE), ("B", ORANGE)):
        m.scatter(xy[q[side], 0], xy[q[side], 1], s=14, color=col, lw=0, zorder=3)
    lo, hi = np.percentile(xy, 0.5, axis=0), np.percentile(xy, 99.5, axis=0)
    pad = (hi - lo) * 0.04
    m.set_xlim(lo[0] - pad[0], hi[0] + pad[0]); m.set_ylim(lo[1] - pad[1], hi[1] + pad[1])
    zlo, zhi = xy[ii].min(0), xy[ii].max(0)
    zp = (zhi - zlo) * 0.18 + 0.05
    zlo, zhi = zlo - zp, zhi + zp
    from matplotlib.patches import Rectangle
    m.add_patch(Rectangle(zlo, *(zhi - zlo), fill=False, ec=INK, lw=1.3))
    m.set_xticks([]); m.set_yticks([])
    for sp in m.spines.values():
        sp.set_visible(False)
    m.set_title(f"All {q['全部说法数']:,} mechanism claims (313 papers)\nbge-small-zh → UMAP; box = open question 1", fontsize=10.5, loc="left", color=INK)
    # 右：放大
    z = fig.add_axes([0.61, 0.10, 0.38, 0.72])
    inside = (xy[:, 0] >= zlo[0]) & (xy[:, 0] <= zhi[0]) & (xy[:, 1] >= zlo[1]) & (xy[:, 1] <= zhi[1])
    z.scatter(xy[inside, 0], xy[inside, 1], s=10, color="#cfd6de", alpha=0.8, lw=0)
    for side, col, lab in (("A", BLUE, "Route 1 · diluent decomposition helps"), ("B", ORANGE, "Route 2 · LiF from the anion; diluent should stay intact")):
        z.scatter(xy[q[side], 0], xy[q[side], 1], s=70, color=col, edgecolor="white", lw=1, zorder=3, label=f"{lab} ({len(q[side])} claims)")
    ia, ib = key[pair["A"]], key[pair["B"]]
    z.plot(xy[[ia, ib], 0], xy[[ia, ib], 1], color=RED, lw=2.2, zorder=4)
    for i, col in ((ia, BLUE), (ib, ORANGE)):
        z.scatter([xy[i, 0]], [xy[i, 1]], s=230, facecolor=col, edgecolor=RED, lw=2.4, zorder=5)
    w, h = zhi - zlo
    z.set_xlim(zlo[0], zhi[0]); z.set_ylim(zlo[1], zhi[1])
    za = [(ia, (zlo[0] + 0.03 * w, zhi[1] - 0.10 * h), "left"), (ib, (zhi[0] - 0.03 * w, zlo[1] + 0.13 * h), "right")]
    for i, xyt, ha in za:
        z.annotate(EN[pts[i]["论文"] + "|" + pts[i]["机制"]], xy=xy[i], xytext=xyt, ha=ha, va="center", fontsize=9, color=INK,
                   bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=RED, lw=1), arrowprops=dict(arrowstyle="-", color=RED, lw=1), zorder=6)
    mid = xy[[ia, ib]].mean(0)
    z.text(mid[0] - 0.06 * w, mid[1] + 0.02 * h, f"cosine {pair['相似度']:.2f}\nsame topic,\nopposite answer", ha="right", va="center", fontsize=9, color=RED,
           fontweight="bold", zorder=6)
    z.set_xticks([]); z.set_yticks([])
    for sp in z.spines.values():
        sp.set_edgecolor(INK); sp.set_visible(True)
    z.legend(loc="lower left", frameon=True, framealpha=0.9, edgecolor="none", fontsize=8.5)
    rk = q["对方派中位排名"]
    z.set_title(f"Zoom · open question 1: the two sides are mixed in one region\nopposite-side claims rank {rk:.0f} of {q['全部说法数']:,} in similarity "
                f"(top {100 * rk / q['全部说法数']:.0f}%; random ≈ 50%)", fontsize=10.5, loc="left", color=INK)
    fig.text(0.31, 0.015, "Vectors find claims about the same thing; reading the paper decides which side each claim is on "
             "(stance from AI-assisted reading, not from the vectors).", fontsize=9, color=INK2)
    fig.suptitle("Text-vector map: contradictory claims sit next to each other", x=0.035, y=0.995, ha="left", fontsize=13.5,
                 fontweight="bold", color=INK)
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "fig_p13_vectors.png"
    fig.savefig(f, dpi=300, facecolor="white", bbox_inches="tight")
    shutil.copy(f, SITE / f.name)
    print(f)


if __name__ == "__main__":
    main()
