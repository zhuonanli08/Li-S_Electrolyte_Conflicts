"""组会第13页文字向量地图：全图 + 局部放大 + 底部相似度示例。
复用 step22 的既有二维坐标（UMAP 10 / 0.0），不重跑或调整嵌入。
仅按展示点云跨度转90度、两轴等比例；按关键词着色与二维密度调节散点深浅；无高斯光晕。
全图保留问题1全部22条说法，局部框取75%核心及原向量最相似一对；框外点显式标注。
立场来自既有AI辅助原文判读；原向量相似度与二维距离明确区分。
输出300 dpi PNG、PDF及计数JSON，并将PNG复制至现有网站。
11-08 夜（用户：“文字向量地图可以改”）：放大框是围着问题 1 的 22 条画的，“20/22 落在框里”不能当证据，B 栏改写原始向量里的检验
（step22b：50 近邻里同问题说法是随机的几倍、两派能否分开的 AUC）；C 栏每条加“随机两条说法”的中位数刻度，并注明示例句是人造的；
图注补二维图保真度（原向量 10 近邻在二维图里只保留约 16%）与同篇聚团（10 近邻约 14% 来自同一篇）。数字读 向量检验.json。
运行：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/fig_p13_vectors.py
"""
import glob
import json
import re
import shutil
from collections import Counter
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Rectangle

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
O = ROOT / "output"
ATLAS = O / "说法地图_313篇_2026-11-08" / "全部说法二维.json"
CHECK = O / "说法地图_313篇_2026-11-08" / "向量检验.json"  # step22b
PAPERS = O / "试跑313篇_2026-11-05" / "papers"
OUT = O / "组会图_2026-11-08"
SITE = O / "表述与矛盾试跑_F版30篇_2026-11-04" / "网站" / "图"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE, RED = "#2a78d6", "#eb6834", "#d03b3b"
# 话题（按顺序取第一个命中的；浅色，避开问题 1 两派的蓝、橙）
THEMES = [("LiF / SEI / Li anode", r"LiF|SEI|固体电解质界面|锂负极|锂金属|枝晶|沉积|负极界面", "#6fb487"),
          ("polysulfide shuttle / dissolution", r"穿梭|溶解", "#d9a94a"),
          ("conversion kinetics / catalysis", r"动力学|催化|转化|成核|Li2S|能垒|介体", "#a48ad6"),
          ("solvation structure", r"溶剂化|配位|接触离子对|溶剂鞘", "#e38fb0"),
          ("LiNO₃", r"LiNO|硝酸", "#4fb8b6")]
OTHER = ("other", "#dcdcd7")
# 最近的相反一对的英文转述（Claude 据 step20 的一句话写；只用于图注）
plt.rcParams.update({"font.family": ["Arial", "DejaVu Sans"], "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False})


def texts():
    T = {}
    for f in sorted(glob.glob(str(PAPERS / "*" / "candidate.json"))):
        c = json.loads(Path(f).read_text(encoding="utf-8"))
        p = Path(f).parent.name
        for m in c.get("mechanisms", []):
            T[f"{p}|{m['id']}"] = m.get("summary", "")
    return T


def theme(s):
    return next((k for k, (_, r, _) in enumerate(THEMES) if re.search(r, s)), len(THEMES))


def density_rank(xy, bins=96):
    """Smoothed local counts sampled at each point; ties retain the same density."""
    from scipy.ndimage import gaussian_filter
    h, xe, ye = np.histogram2d(xy[:, 0], xy[:, 1], bins=bins)
    h = gaussian_filter(h, sigma=1.0)
    i = np.clip(np.searchsorted(xe, xy[:, 0], side="right") - 1, 0, bins - 1)
    j = np.clip(np.searchsorted(ye, xy[:, 1], side="right") - 1, 0, bins - 1)
    d = h[i, j]
    return np.clip(d / np.quantile(d, .97), 0, 1)


def shaded(hex_cols, r):
    """Opaque, crisp dots: pale in sparse regions and darker in dense regions."""
    base = np.array([to_rgb(c) for c in hex_cols])
    light = base + (1 - base) * .38
    dark = base * .63
    t = r[:, None] ** .7
    return light * (1 - t) + dark * t


def main():
    a = json.loads(ATLAS.read_text(encoding="utf-8"))
    ck = json.loads(CHECK.read_text(encoding="utf-8"))
    c1, rnd, fid = ck["问题"]["T1"], ck["随机两条说法的余弦"], ck["二维图保真"]
    pts = a["说法"]
    raw = np.array([[p["x"], p["y"]] for p in pts])
    keys = [f"{p['论文']}|{p['机制']}" for p in pts]
    key = {v: i for i, v in enumerate(keys)}
    T = texts()
    assert len(keys) == len(set(keys)) and all(v in T for v in keys)
    eng = np.array([not re.search(r"[\u4e00-\u9fff]", T[v]) for v in keys])
    k = ~eng
    # Only rotate the displayed cloud, without changing distances or re-fitting UMAP.
    span = np.ptp(raw[k], axis=0)
    xy = np.c_[raw[:, 1], -raw[:, 0]] if span[1] > span[0] else raw.copy()
    th = np.array([theme(T[v]) for v in keys])
    cols = np.array([c for _, _, c in THEMES] + [OTHER[1]])
    q, pair = a["问题"]["T1"], a["最近的相反一对"]["T1"]
    ii = q["A"] + q["B"]
    ia, ib = key[pair["A"]], key[pair["B"]]
    assert not set(q["A"]) & set(q["B"]) and k[ii].all()
    lo, hi = xy[k].min(0), xy[k].max(0)
    pad = (hi - lo) * 0.035

    # Keep the same 75% core rule; the other question claims remain on the overview.
    dist = np.linalg.norm(xy[ii] - np.median(xy[ii], axis=0), axis=1)
    core = sorted(set([i for i, d in zip(ii, dist) if d <= np.quantile(dist, .75)] + [ia, ib]))
    zlo, zhi = xy[core].min(0), xy[core].max(0)
    zp = (zhi - zlo) * .18 + .05
    zlo, zhi = zlo - zp, zhi + zp
    # A square zoom gives a true local crop; never stretch either coordinate axis.
    zc = (zlo + zhi) / 2
    half = max(zhi - zlo) / 2
    zlo, zhi = zc - half, zc + half
    shift = np.maximum(lo - pad - zlo, 0) - np.maximum(zhi - (hi + pad), 0)
    zlo, zhi = zlo + shift, zhi + shift
    inside = k & np.all((xy >= zlo) & (xy <= zhi), axis=1)
    assert np.all(inside[core])
    n_q_in = int(inside[ii].sum())
    n_in, n_an = int(inside.sum()), int((inside & (th == 0)).sum())
    outside = [i for i in ii if not inside[i]]
    assert n_in < k.sum() / 2, "放大框已覆盖大半张图，应重新检查局部选择"

    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.text(.035, .956, "Text-vector map", fontsize=23, fontweight="bold", color=INK)
    fig.text(.035, .918, "Semantic similarity locates related claims; reading the papers identifies their positions.", fontsize=12, color=INK2)
    fig.text(.035, .868, f"A   OVERVIEW  /  {k.sum():,} claims", fontsize=12, fontweight="bold", color=INK)
    fig.text(.635, .868, f"B   LOCAL VIEW  /  {n_in:,} claims", fontsize=12, fontweight="bold", color=INK)
    # 放大框是围着这 22 条画的，框内条数不能当证据；改写原始向量里的检验（step22b）
    for yy, line in ((.848, f"Box drawn around the {len(ii)} Question-1 claims (not evidence). In the original vectors:"),
                     (.830, f"each claim's 50 nearest neighbours hold {c1['50近邻里同问题说法_平均']:.1f} other Q1 claims ({c1['倍数']:.0f}× chance) → same topic;"),
                     (.812, f"the two positions do not separate (AUC {c1['分立场AUC_两两']:.2f}; 0.5 = chance) → stance needs reading.")):
        fig.text(.635, yy, line, fontsize=9.2, color=INK2)
    m = fig.add_axes([.035, .31, .55, .49])
    z = fig.add_axes([.635, .31, .275625, .49])

    density = np.zeros(len(xy))
    density[k] = density_rank(xy[k])

    def cloud(ax, mask, lower, upper, dot_size):
        ids = np.flatnonzero(mask)
        ids = ids[np.argsort(density[ids], kind="stable")]
        ax.scatter(xy[ids, 0], xy[ids, 1], s=dot_size * (.7 + .8*density[ids]),
                   c=shaded(cols[th[ids]], density[ids]), linewidths=0,
                   alpha=1, rasterized=True, zorder=2)
        ax.set(xlim=(lower[0], upper[0]), ylim=(lower[1], upper[1]), xticks=[], yticks=[])
        ax.set_aspect("equal", adjustable="box")

    cloud(m, k, np.minimum(lo - pad, zlo), np.maximum(hi + pad, zhi), 2.4)
    cloud(z, inside, zlo, zhi, 7.0)
    for side, col in (("A", BLUE), ("B", ORANGE)):
        for ax, mask, size in ((m, k, 28), (z, inside, 65)):
            ids = [i for i in q[side] if mask[i]]
            ax.scatter(xy[ids, 0], xy[ids, 1], s=size, color=col,
                       edgecolor="white", linewidths=.9, zorder=5)
    m.add_patch(Rectangle(zlo, *(zhi-zlo), fill=False, ec=INK, lw=1.3, zorder=6))
    # Explicitly mark the claims omitted by the crop, instead of silently hiding them.
    for j, i in enumerate(outside):
        m.annotate(pts[i]["论文"] + " · outside zoom", xy=xy[i], xytext=((12, 12) if xy[i, 0] > (zlo[0]+zhi[0])/2 else (-12, 12)),
                   textcoords="offset points", fontsize=8, color=INK,
                   ha="left" if xy[i, 0] > (zlo[0]+zhi[0])/2 else "right",
                   bbox=dict(fc="white", ec="none", alpha=.9, pad=2),
                   arrowprops=dict(arrowstyle="-", lw=.7, color=INK2), zorder=8)
    for sp in m.spines.values():
        sp.set_visible(False)
    for sp in z.spines.values():
        sp.set_visible(True); sp.set_color("#c5cbc9"); sp.set_linewidth(.8)
    z.plot(xy[[ia, ib], 0], xy[[ia, ib], 1], color=INK2, lw=1, ls=(0, (3, 3)), zorder=4)
    for i, col, offset in ((ia, BLUE, (10, 10)), (ib, ORANGE, (10, -16))):
        for ax, size in ((m, 70), (z, 155)):
            ax.scatter(*xy[i], s=size, facecolor=col, edgecolor=INK, lw=1.2, zorder=7)
        z.annotate(pts[i]["论文"], xy=xy[i], xytext=offset, textcoords="offset points",
                   fontsize=10, fontweight="bold", color=INK,
                   bbox=dict(fc="white", ec="none", alpha=.85, pad=1.5), zorder=8)

    # Legends are outside the clouds so that labels cannot conceal the highlighted claims.
    lg = [plt.Line2D([], [], ls="", marker="o", ms=6, color=c,
                     label=f"{n} ({int((k & (th == t)).sum()):,})")
          for t, (n, _, c) in enumerate(THEMES + [(OTHER[0], "", OTHER[1])])]
    fig.legend(handles=lg, loc="upper left", bbox_to_anchor=(.035, .30), ncol=2,
               frameon=False, fontsize=9, handletextpad=.35, columnspacing=1.3, borderaxespad=0)
    fig.text(.635, .287, "●  A · Diluent decomposition helps (9 claims)", color=BLUE, fontsize=10)
    fig.text(.635, .263, "●  B · Anion-derived LiF / stable diluent (13 claims)", color=ORANGE, fontsize=10)
    fig.text(.635, .235, f"P179 ↔ P338: highest cross-position cosine = {pair['相似度']:.2f}", fontsize=10, fontweight="bold", color=INK)
    fig.text(.635, .218, "P179: HFE decomposition forms a protective LiF layer (hypothesis).\nP338: LiF comes from LiFSA; HFE decomposition is unlikely.", fontsize=8.8, color=INK2, linespacing=1.5, va="top")

    # Compact examples retain the explanation without taking space away from the map.
    fig.text(.035, .163, "C   WHY POSITION IS NOT STANCE", fontsize=10, fontweight="bold", color=INK)
    fig.text(.235, .163, f"constructed example sentences · tick = two random claims from the corpus (median cosine {rnd['中位数']:.2f}; "
             f"99% of random pairs ≤ {rnd['99分位']:.2f})", fontsize=8.6, color=INK2)
    labels = ["TTE decomposition: beneficial vs harmful", "More LiNO₃: longer vs shorter life",
              "Longer life: more LiNO₃ vs more salt", "TTE-derived LiF vs cathode LiNO₃ reduction"]
    for j, (e, label) in enumerate(zip(a["示例"], labels)):
        x = .035 + .239 * j
        col = RED if j < 2 else MUTED
        fig.text(x, .137, label, fontsize=8.4, color=INK)
        fig.text(x, .116, e["关系"], fontsize=8, color=INK2)
        bar = fig.add_axes([x, .088, .192, .014])
        bar.barh([0], [1], color="#eef0ef", height=1)
        bar.barh([0], [e["相似度"]], color=col, height=1)
        bar.plot([rnd["中位数"]] * 2, [-.95, .95], color=INK, lw=1.4, clip_on=False, zorder=3)  # 随机两条说法的中位数
        bar.set(xlim=(0, 1), ylim=(-.5, .5)); bar.axis("off")
        fig.text(x + .198, .087, f"{e['相似度']:.2f}", fontsize=10, color=col, fontweight="bold")
    fig.text(.035, .052, "METHOD  Chinese mechanism summaries → bge-small-zh-v1.5 → cosine UMAP (n_neighbors=10, min_dist=0, seed=42). Equal axis scales.", fontsize=8, color=INK2)
    fig.text(.035, .033, f"Topic colours: keyword-based orientation; darker dots: greater 2D density. {eng.sum()} English summaries from 4 papers omitted; corpus: 7,477 claims / 313 papers.", fontsize=8, color=INK2)
    fig.text(.035, .014, f"Positions A/B: AI-assisted paper reading. Read regions, not distances: the 2D map keeps only {fid['原向量10近邻在二维图仍为10近邻']:.0%} of each claim's "
             f"10 nearest neighbours (rank correlation with cosine {fid['二维距离与余弦的秩相关']:.2f}), and {fid['10近邻来自同一篇论文']:.0%} of neighbours come from the same paper "
             f"(chance {fid['同一篇论文随机期望']:.1%}). The labelled pair is chosen in the original vectors.", fontsize=8, color=INK2)
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "fig_p13_vectors.png"
    fig.savefig(f, dpi=300, facecolor="white")
    fig.savefig(OUT / "fig_p13_vectors.pdf", dpi=300, facecolor="white")
    shutil.copy(f, SITE / f.name)
    d = {"画出的说法": int(k.sum()), "英文摘要未画": int(eng.sum()),
         "英文摘要未画_按论文": dict(Counter(p["论文"] for p, omit in zip(pts, eng) if omit)),
         "图中论文数": len({p["论文"] for p, keep in zip(pts, k) if keep}),
         "话题计数（关键词粗分）": {n: int((k & (th == t)).sum()) for t, (n, _, _) in enumerate(THEMES + [(OTHER[0], "", OTHER[1])])},
         "放大区说法": n_in, "放大区 LiF/SEI/锂负极": n_an, "问题 1 站队说法": len(ii), "其中在放大区（框按这些点画，不作证据）": n_q_in,
         "原始向量检验（step22b）": {"问题1": c1, "随机两条说法的余弦": rnd, "二维图保真": fid},
         "放大区外的问题1说法": [keys[i] for i in outside], "最近相反一对相似度": pair["相似度"],
         "相反一对选择依据": "原始向量余弦相似度最高，不是二维距离最近",
         "放大框规则": "离22条说法中位点最近的75% + 原向量最相似的一对；18%留白；补齐正方形并平移至全图范围内",
         "显示坐标放大框": {"min": zlo.tolist(), "max": zhi.tolist()},
         "UMAP": {"n_neighbors": 10, "min_dist": 0.0, "metric": "cosine", "random_state": 42}}
    assert sum(d["话题计数（关键词粗分）"].values()) == d["画出的说法"]
    (OUT / "第13页向量图数据.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f, d)
    plt.close(fig)


if __name__ == "__main__":
    main()
