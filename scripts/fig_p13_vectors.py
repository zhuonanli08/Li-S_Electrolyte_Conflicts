"""组会第 13 页“文字向量地图”（11-08 用户同意；zy 批注：解释向量转化方法，在地图中标注差距明显的两点并解释）。

左：四组示例句子的向量相似度——立场相反的两句话几乎重合（0.95–0.96），讲两件事的才远，说明向量按“讲什么”摆放、不按“支持还是反对”。
中：全部机制说法的二维地图（step22：bge-small-zh → UMAP），按话题浅色上色并标话题名；方框 = 问题 1 所在区域。
右：方框放大，无定论问题 1 两派用蓝橙标出，“离得最近、立场相反”的一对连线并注释。
11-08 晚用户：“中间那个感觉太窄了，好像比例不对”“没有被标蓝的点和标红的点是什么情况，让人感觉现在只是零星几个点” →
  ① P017 的 83 条摘要是英文，单独聚成远处一小簇，把横轴撑宽、主图被挤窄 → 不画，脚注说明；坐标等比例，并转 90°（UMAP 方向无意义）让主图横放；
  ② 其余点按说法里的关键词粗分话题（LiF / SEI / 锂负极、多硫化物穿梭与溶解、转化动力学与催化、溶剂化结构、LiNO₃、其他）浅色上色，
     说明灰点是“同一话题、但没在问题 1 上站队的说法”，不是空的。关键词只作定位，不作结论。
图英文。输出 output/组会图_2026-11-08/fig_p13_vectors.png（300 dpi），复制到网站 图/；数字写 第13页向量图数据.json（不含摘要原文）。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/fig_p13_vectors.py
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
from matplotlib.patches import Rectangle

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
O = ROOT / "output"
ATLAS = O / "说法地图_313篇_2026-11-08" / "全部说法二维.json"
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
EN = {"P179|MC10": "P179: HFE decomposes quickly to a passivating LiF layer\n→ better Li compatibility (author’s hypothesis)",
      "P338|MC11": "P338: LiF comes from LiFSA reduction;\nHFE decomposing to LiF is unlikely"}
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


def main():
    a = json.loads(ATLAS.read_text(encoding="utf-8"))
    pts = a["说法"]
    raw = np.array([[p["x"], p["y"]] for p in pts])
    xy = np.c_[raw[:, 1], -raw[:, 0]]  # 转 90°：主图横放（UMAP 坐标方向无意义）
    keys = [f"{p['论文']}|{p['机制']}" for p in pts]
    key = {k: i for i, k in enumerate(keys)}
    T = texts()
    eng = np.array([not re.search(r"[\u4e00-\u9fff]", T.get(k, "")) for k in keys])  # 英文摘要（P017）单独成簇，不画
    th = np.array([theme(T.get(k, "")) for k in keys])
    cols = np.array([c for _, _, c in THEMES] + [OTHER[1]])
    q = a["问题"]["T1"]
    pair = a["最近的相反一对"]["T1"]
    fig = plt.figure(figsize=(14, 6.4))
    # 左：示例句子的相似度
    ax = fig.add_axes([0.035, 0.16, 0.235, 0.66])
    ex = a["示例"]
    yy = np.arange(len(ex))[::-1]
    ax.barh(yy, [e["相似度"] for e in ex], color=[RED if e["关系"].endswith("opposite stance") else MUTED for e in ex], height=0.55)
    for y, e in zip(yy, ex):
        ax.text(0.02, y + 0.42, f"“{e['英文1']}”\nvs “{e['英文2']}”", fontsize=7.8, color=INK, va="bottom", linespacing=1.2)
        ax.text(e["相似度"] + 0.015, y, f"{e['相似度']:.2f}", va="center", fontsize=10, color=INK, fontweight="bold")
        ax.text(0.02, y, e["关系"], va="center", fontsize=8.3, color="white", fontweight="bold")
    ax.set_xlim(0, 1.08); ax.set_ylim(-0.6, len(ex) - 0.05)
    ax.set_yticks([]); ax.set_xlabel("cosine similarity of the two sentence vectors")
    ax.spines["left"].set_visible(False)
    ax.set_title("Why opposite claims are neighbours\n(bge-small-zh, sentences in Chinese)", fontsize=10.5, loc="left", color=INK)
    # 中：全部说法（不含英文簇），按话题浅色上色，等比例
    m = fig.add_axes([0.295, 0.20, 0.32, 0.62])
    k = ~eng
    m.scatter(xy[k, 0], xy[k, 1], s=3.2, c=cols[th[k]], lw=0, alpha=0.85, rasterized=True)
    ii = q["A"] + q["B"]
    for side, col in (("A", BLUE), ("B", ORANGE)):
        m.scatter(xy[q[side], 0], xy[q[side], 1], s=16, color=col, edgecolor=INK, lw=0.4, zorder=3)
    lo, hi = xy[k].min(0), xy[k].max(0)
    pad = (hi - lo) * 0.03
    m.set_xlim(lo[0] - pad[0], hi[0] + pad[0]); m.set_ylim(lo[1] - pad[1], hi[1] + pad[1])
    m.set_aspect("equal", adjustable="box")
    zlo, zhi = xy[ii].min(0), xy[ii].max(0)
    zp = (zhi - zlo) * 0.18 + 0.05
    zlo, zhi = zlo - zp, zhi + zp
    ZW, ZH = 0.345 * 14, 0.72 * 6.4  # 放大图的版面（英寸）；放大区按同样宽高比补齐，等比例时不留空
    w, h = zhi - zlo
    if w / h < ZW / ZH:
        d = (h * ZW / ZH - w) / 2; zlo, zhi = zlo - [d, 0], zhi + [d, 0]
    else:
        d = (w * ZH / ZW - h) / 2; zlo, zhi = zlo - [0, d], zhi + [0, d]
    mlo, mhi = lo - pad, hi + pad  # 补齐后超出地图的一边往里平移（问题 1 的点靠近点云左缘）
    sh = np.maximum(mlo - zlo, 0) - np.maximum(zhi - mhi, 0)
    zlo, zhi = zlo + sh, zhi + sh
    assert np.all(xy[ii] >= zlo) and np.all(xy[ii] <= zhi), "问题 1 的点跑出放大区"
    m.add_patch(Rectangle(zlo, *(zhi - zlo), fill=False, ec=INK, lw=1.3, zorder=4))
    for t, (name, _, col) in enumerate(THEMES):  # 话题名标在该话题点最密的地方
        s = xy[k & (th == t)]
        H, xe, ye = np.histogram2d(s[:, 0], s[:, 1], bins=12)
        i, j = np.unravel_index(np.argmax(H), H.shape)
        m.text((xe[i] + xe[i + 1]) / 2, (ye[j] + ye[j + 1]) / 2, name.replace(" / ", "\n/ ", 1) if len(name) > 22 else name,
               ha="center", va="center", fontsize=8.6, color=INK, fontweight="bold", zorder=5, linespacing=1.1,
               bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.75))
    m.set_xticks([]); m.set_yticks([])
    for sp in m.spines.values():
        sp.set_visible(False)
    m.set_title(f"All {int(k.sum()):,} mechanism claims (313 papers), coloured by topic\nbge-small-zh → UMAP; box = open question 1",
                fontsize=10.5, loc="left", color=INK)
    # 话题图例（放中图下方）
    lg = [plt.Line2D([], [], ls="", marker="o", ms=6, color=c, label=f"{n} ({int((k & (th == t)).sum()):,})")
          for t, (n, _, c) in enumerate(THEMES + [(OTHER[0], "", OTHER[1])])]
    m.legend(handles=lg, loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=2, frameon=False, fontsize=8.2, handletextpad=0.2, columnspacing=1.0)
    # 右：放大
    z = fig.add_axes([0.645, 0.10, 0.345, 0.72])
    inside = k & (xy[:, 0] >= zlo[0]) & (xy[:, 0] <= zhi[0]) & (xy[:, 1] >= zlo[1]) & (xy[:, 1] <= zhi[1])
    z.scatter(xy[inside, 0], xy[inside, 1], s=11, c=cols[th[inside]], lw=0)
    for side, col, lab in (("A", BLUE, "Route 1 · diluent decomposition helps"), ("B", ORANGE, "Route 2 · LiF from the anion; diluent should stay intact")):
        z.scatter(xy[q[side], 0], xy[q[side], 1], s=75, color=col, edgecolor=INK, lw=0.8, zorder=3, label=f"{lab} ({len(q[side])} claims)")
    ia, ib = key[pair["A"]], key[pair["B"]]
    z.plot(xy[[ia, ib], 0], xy[[ia, ib], 1], color=RED, lw=1.6, ls=(0, (3, 2)), zorder=4)
    for i, col in ((ia, BLUE), (ib, ORANGE)):
        z.scatter([xy[i, 0]], [xy[i, 1]], s=230, facecolor=col, edgecolor=RED, lw=2.4, zorder=5)
    z.set_xlim(zlo[0], zhi[0]); z.set_ylim(zlo[1], zhi[1])
    z.set_aspect("equal", adjustable="box")
    w, h = zhi - zlo
    # 两条注释放在各自点的外侧（左上、右下），引线不穿过另一点
    left, right = (ia, ib) if xy[ia, 0] < xy[ib, 0] else (ib, ia)
    for i, xyt, ha in ((left, (zlo[0] + 0.02 * w, zhi[1] - 0.09 * h), "left"), (right, (zhi[0] - 0.02 * w, zlo[1] + 0.20 * h), "right")):
        z.annotate(EN[keys[i]], xy=xy[i], xytext=xyt, ha=ha, va="center", fontsize=8.8, color=INK,
                   bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=RED, lw=1), arrowprops=dict(arrowstyle="-", color=RED, lw=1), zorder=6)
    z.set_xticks([]); z.set_yticks([])
    for sp in z.spines.values():
        sp.set_edgecolor(INK); sp.set_visible(True)
    z.legend(loc="lower left", frameon=True, framealpha=0.92, edgecolor="none", fontsize=8.3)
    n_in = int(inside.sum()); n_an = int((inside & (th == 0)).sum())
    rk = q["对方派中位排名"]
    z.set_title(f"Zoom · {n_in:,} claims here, {n_an:,} of them about LiF / SEI / Li anode;\nreading put {len(ii)} of them on a side of open question 1 "
                f"· closest opposite pair: cosine {pair['相似度']:.2f}", fontsize=10.5, loc="left", color=INK)
    fig.text(0.295, 0.015, f"Topic = keyword in the claim (rough, for orientation only). {int(eng.sum())} claims written in English (one paper, P017) form a separate cluster "
             f"and are not shown. Vectors find claims about the same thing; reading the paper decides the side\n(stance from AI-assisted reading, not from the vectors). "
             f"Opposite-side claims rank {rk:.0f} of {q['全部说法数']:,} in similarity (top {100 * rk / q['全部说法数']:.0f}%; random ≈ 50%).",
             fontsize=8.6, color=INK2, linespacing=1.3)
    fig.suptitle("Text-vector map: contradictory claims sit next to each other", x=0.035, y=0.995, ha="left", fontsize=13.5,
                 fontweight="bold", color=INK)
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "fig_p13_vectors.png"
    fig.savefig(f, dpi=300, facecolor="white", bbox_inches="tight")
    shutil.copy(f, SITE / f.name)
    d = {"画出的说法": int(k.sum()), "英文摘要未画（P017）": int(eng.sum()),
         "话题计数（关键词粗分）": {n: int((k & (th == t)).sum()) for t, (n, _, _) in enumerate(THEMES + [(OTHER[0], "", OTHER[1])])},
         "放大区说法": n_in, "放大区 LiF/SEI/锂负极": n_an, "问题 1 站队说法": len(ii), "最近相反一对相似度": pair["相似度"]}
    (OUT / "第13页向量图数据.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f, d)


if __name__ == "__main__":
    main()
