"""step24（papertrail 环境）：SES 式配方空间图（11-08 用户：配方空间“还是不满意，你看看人家 SES 怎么画的”）。

与分子宇宙同一套视觉语言：黑底；配方越密的地方越亮（紫 → 橙）；文字直接写在画面上。
坐标仍用两个有物理意义的描述符（11-06 用户：配方图用描述符、按数值画）：
  横轴 = 每个 Li⁺ 分到的配位位点（醚氧、羰基氧等，按整个配方的用量算；越少 = 溶剂化越弱，高浓/局部高浓电解液在左边），对数；
  纵轴 = 锂盐浓度（M），对数。
点：绿 = 含 LiNO₃（点的大小 = 用量 M）；绿圈 = 含 LiNO₃ 但原文没给以 M 计的用量；灰 = 不含 LiNO₃；红边 = 含含氟溶剂/稀释剂。
图上直接标出三个无定论问题各在配方空间的哪里。配方与 LiNO₃ 判定同 fig_questions.formulations()；溶剂化描述符同 step13h.descriptors。
图上文字英文。输出 output/组会图_2026-11-08/fig_formulation_space.png（300 dpi），并复制到网站 图/。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step24_formulation_space.py
"""
import json
import math
import shutil
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from scipy.ndimage import gaussian_filter

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "step15_meta"))
import fig_questions as Q

OUT = ROOT / "output" / "组会图_2026-11-08"
SITE = ROOT / "output" / "表述与矛盾试跑_F版30篇_2026-11-04" / "网站" / "图"
plt.rcParams.update({"font.family": ["Arial", "DejaVu Sans"]})
GLOW = LinearSegmentedColormap.from_list("glow", [(0, (0, 0, 0, 0)), (0.08, "#2b0a57"), (0.3, "#6a1b9a"), (0.55, "#c2408a"), (0.8, "#f6874f"), (1, "#fdd36a")])
GREEN, RED, GREY, PURPLE_TXT, MUTED = "#39e75f", "#ff4040", "#8c8c8c", "#c77dff", "#9a9a9a"
XL, YL = (0.6, 160), (0.08, 14)


def main():
    F, n_form = Q.formulations()
    H = Q.P16.H
    pts = []
    for f in F:
        h, _ = H.descriptors(f["论文"], f["recipe"])
        if h.get("lnsites") is None or not (h.get("salt") or 0) > 0:
            continue
        pts.append({**f, "sites": math.exp(h["lnsites"]), "fsolv": (h.get("ffrac") or 0) > 0, "comp": tuple(sorted(i["组分"] for i in H.COMPREC[(f["论文"], f["recipe"])]["组分"]))})
    x = np.array([p["sites"] for p in pts]); y = np.array([p["salt"] for p in pts])
    has = np.array([p["has_lino3"] for p in pts]); dose = np.array([p["lino3"] if p["lino3"] is not None else np.nan for p in pts])
    fs = np.array([p["fsolv"] for p in pts])

    fig = plt.figure(figsize=(16, 9), facecolor="black")
    ax = fig.add_axes([0.06, 0.10, 0.60, 0.74])
    ax.set_facecolor("black")
    # 发光：对数坐标里的二维直方图 + 高斯平滑
    lx, ly = np.log10(x), np.log10(y)
    gx = np.linspace(*np.log10(XL), 520); gy = np.linspace(*np.log10(YL), 380)
    Hh, _, _ = np.histogram2d(lx, ly, bins=[gx, gy])
    G = gaussian_filter(Hh.T, sigma=6)
    G = np.sqrt(G / G.max())
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.pcolormesh(10 ** gx, 10 ** gy, G, cmap=GLOW, shading="flat", zorder=1, rasterized=True)  # 对数轴上要按格子边界画，imshow 会按线性铺开
    ax.set_xlim(*XL); ax.set_ylim(*YL)
    # 高盐 + LiNO₃（问题 3）的区域
    ax.add_patch(Rectangle((XL[0], 1.0001), XL[1] - XL[0], YL[1] - 1.0001, fill=False, ec="white", lw=1.0, ls=(0, (4, 4)), zorder=2))
    # 点
    no = ~has
    ax.scatter(x[no], y[no], s=16, c=GREY, edgecolors=np.where(fs[no], RED, "none"), linewidths=1.2, zorder=3)
    kd = has & ~np.isnan(dose)
    ax.scatter(x[kd], y[kd], s=14 + 260 * dose[kd], c=GREEN, alpha=0.85, edgecolors=np.where(fs[kd], RED, "black"), linewidths=1.2, zorder=4)
    ku = has & np.isnan(dose)
    ax.scatter(x[ku], y[ku], s=30, facecolors="none", edgecolors=np.where(fs[ku], RED, GREEN), linewidths=1.4, zorder=4)
    # 热点：位置相同（四舍五入后）的配方最多的一点
    cell = Counter((round(math.log(p["sites"]), 2), round(math.log10(p["salt"]), 2)) for p in pts)
    (cx, cy), n_hot = cell.most_common(1)[0]
    hot = [p for p in pts if (round(math.log(p["sites"]), 2), round(math.log10(p["salt"]), 2)) == (cx, cy)]
    dd = sum({"DOL", "DME", "LiTFSI"} <= set(p["comp"]) for p in hot)
    ax.annotate(f"{n_hot} formulations at one point\n{dd} of them: 1 M LiTFSI in DOL/DME (± LiNO₃, ± additive)",
                xy=(math.exp(cx), 10 ** cy), xytext=(55, 0.16), color="white", fontsize=10.5, fontweight="bold", ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.6", fc="black", ec="white", lw=1.3),
                arrowprops=dict(arrowstyle="-", color="white", lw=1.2), zorder=6)
    # 区域名（斜体白字）
    for t, (xx, yy), ha in (("dilute ether electrolytes", (60, 1.4), "center"), ("high-concentration\n(few free solvent molecules)", (1.6, 6.5), "center"),
                            ("fluorinated diluent added\n(localized high-concentration)", (1.6, 0.68), "center")):
        ax.text(xx, yy, t, color="#e8e8e8", fontsize=11, fontstyle="italic", ha=ha, va="center", zorder=5, linespacing=1.15)
    ax.text(XL[1] * 0.93, 12.2, "salt > 1 M", color="white", fontsize=10, ha="right", va="top", zorder=5)
    # 坐标轴（暗色）
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#666666")
    ax.tick_params(colors="#cccccc", labelsize=11, which="both")
    ax.set_xticks([1, 2, 5, 10, 20, 50, 100]); ax.set_xticklabels(["1", "2", "5", "10", "20", "50", "100"])
    ax.set_yticks([0.1, 0.2, 0.5, 1, 2, 4, 8]); ax.set_yticklabels(["0.1", "0.2", "0.5", "1", "2", "4", "8"])
    ax.minorticks_off()
    ax.set_xlabel("Coordinating sites per Li⁺  (fewer = weaker solvation)", color="white", fontsize=12)
    ax.set_ylabel("Lithium-salt concentration (M)", color="white", fontsize=12)
    # 右侧文字（SES 式：大字直接写在画面上）
    n_pap = len({p["论文"] for p in pts})
    tx = 0.70
    fig.text(tx, 0.90, "Formulation space", fontsize=24, fontweight="bold", color="white", va="bottom")
    fig.text(tx, 0.845, f"{len(pts)} of {n_form} formulations in 313 papers\n(those with solvent amounts and a salt in M; {n_pap} papers)",
             fontsize=11.5, color=PURPLE_TXT, va="bottom", linespacing=1.25)
    fig.text(tx, 0.805, "glow = how many formulations sit there", fontsize=11, color="white", va="bottom")
    yy = 0.735
    for mk, txt in (((GREEN, "black", 140), "with LiNO₃ · dot size = dose (M)"), (("none", GREEN, 40), "with LiNO₃, dose not given in M"),
                    ((GREY, "none", 30), "without LiNO₃"), ((GREY, RED, 40), "red edge = contains a fluorinated\nsolvent / diluent")):
        fig.lines  # noqa: keep matplotlib quiet about unused
        a = fig.add_axes([tx, yy - 0.012, 0.02, 0.03]); a.axis("off"); a.set_xlim(-1, 1); a.set_ylim(-1, 1)
        a.scatter([0], [0], s=mk[2], c=mk[0] if mk[0] != "none" else "none", edgecolors=mk[1], linewidths=1.4)
        fig.text(tx + 0.025, yy, txt, fontsize=11, color="white", va="center", linespacing=1.2)
        yy -= 0.055
    # 三个问题各在哪里
    q3 = int(sum(has & (y > 1))); q3p = len({p["论文"] for p, h_, yv in zip(pts, has, y) if h_ and yv > 1})
    all_hi = [f for f in F if f["salt"] is not None and f["salt"] > 1 and f["has_lino3"]]
    lv = [f["lino3"] for f in F if f["lino3"] is not None]
    nf = int(fs.sum())
    yy -= 0.02
    for col, head, body in ((RED, "Open question 1", f"fluorinated diluents move formulations left\n(fewer sites per Li⁺) · {nf} formulations here"),
                            (GREEN, "Open question 2", f"big green dots are rare: only {sum(v > 0.6 for v in lv)} of {len(lv)}\nformulations use > 0.6 M LiNO₃"),
                            ("white", "Open question 3", f"above the dashed line, green is rare:\nsalt > 1 M with LiNO₃ in {len(all_hi)} formulations\n"
                                                         f"({len({f['论文'] for f in all_hi})} papers; {q3} of them placed here)")):
        fig.text(tx, yy, head, fontsize=12.5, fontweight="bold", color=col, va="top")
        fig.text(tx, yy - 0.032, body, fontsize=10.8, color="white", va="top", linespacing=1.25)
        yy -= 0.032 + 0.033 * (body.count("\n") + 1) + 0.03
    fig.text(0.06, 0.015, "Coordinating sites per Li⁺ = (solvent molecules per litre × donor sites per molecule) ÷ Li⁺ per litre, from each full recipe. "
             "Same-position formulations overlap; the glow shows how many.", fontsize=9, color=MUTED, va="bottom")
    f = OUT / "fig_formulation_space.png"
    fig.savefig(f, dpi=300, facecolor="black")
    plt.close(fig)
    shutil.copy(f, SITE / "fig_formulation_space.png")
    s = {"配方总数": n_form, "上图配方": len(pts), "论文": n_pap, "热点": {"配方数": n_hot, "其中 DOL/DME+LiTFSI": dd, "每Li位点": round(math.exp(cx), 2), "盐M": round(10 ** cy, 2)},
         "含 LiNO3（有 M 用量）": int(kd.sum()), "含 LiNO3（无 M 用量）": int(ku.sum()), "不含 LiNO3": int(no.sum()), "含含氟溶剂": nf,
         "高盐且含 LiNO3（全部配方）": [len(all_hi), sorted({f['论文'] for f in all_hi})], "高盐且含 LiNO3（上图）": [q3, q3p]}
    (OUT / "配方空间汇总.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f, json.dumps(s, ensure_ascii=False))


if __name__ == "__main__":
    main()
