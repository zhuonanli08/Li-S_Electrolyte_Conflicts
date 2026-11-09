"""step24（papertrail 环境）：配方比较图——多数规律与反例（原“配方空间”）。

11-09 用户：“配方空间一堆线，不直观，不知道要表达什么，换种表现方式”。
上一版（同日上午，提交 1e30438）把 Li‖Cu 同篇比较画成配方平面上的箭头，箭头互相交叉 → 改为点图，每个点 = 一次比较，不画线：
  四个小图，各对应一个项目已有描述符（step13h）：非氟醚氧、溶剂 F 原子数（问题 1）；主盐浓度、LiNO₃（问题 3）。
  横轴 = 这对比较里该描述符变了多少（主盐取倍数、对数刻度）；纵轴 = 往共识方向变的那一侧的 Li‖Cu CE 变化，
  用每圈锂损失之比表示（对数刻度，往上 = 损失更少 = 更好）。四个小图统一成“往共识方向变 → CE 更高？”：
  非氟醚氧画“减少”（计票的共识是越多越差），其余三个画“增加”。所以四个图都是上半（蓝）= 符合共识、下半（红）= 反例。
  计法与计票完全相同（step17.votes：同测试换配方、该描述符在这对比较里有变化、|效果| < ln1.05 记相近），
  每个小图的蓝、红、灰点数就是 张力候选 v2 票数.json 的同测试票数（脚本里 assert 核对）。
  实心 = 这对比较只改了这一类东西；空心 = 同时还改了别的（溶剂图：盐或 LiNO₃ 也变了；盐/LiNO₃ 图：溶剂结构或另一个也变了；
  或有特殊组分变化），对应读原文时的“比较不对等”。只给问题论文（P371、P381、P112）的反例点标号，优先标实心点。
旧版（11-08）横轴“每个 Li⁺ 的配位位点”以盐浓度为分母、与纵轴重复，已废弃。
图上文字英文。输出 output/组会图_2026-11-08/fig_formulation_space.png（300 dpi，复制到网站 图/）、配方空间汇总.json。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step24_formulation_space.py
"""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
import step17_tension_trial as T

O = ROOT / "output"
OUT = O / "组会图_2026-11-08"
SITE = O / "表述与矛盾试跑_F版30篇_2026-11-04" / "网站" / "图"
PAIRS = O / "两两比较表述_313篇_v2_2026-11-07" / "比较表述.json"
VOTES = O / "张力候选_313篇_v2_2026-11-07" / "票数.json"
plt.rcParams.update({"font.family": ["Arial", "DejaVu Sans"]})
INK, INK2, MUTED = "#1a1a1a", "#4a4a4a", "#6b6b6b"
BETTER, WORSE, NEAR = "#1f6fd1", "#d03b3b", "#b0b0b0"
TINT_OK, TINT_NO = "#eef4fc", "#fcefee"
HALO = [pe.withStroke(linewidth=3, foreground="white")]
LN5 = math.log(1.05)
SOLV = {"eo", "eo_a", "eo_b", "carbonate", "carbonyl", "sulfone", "nitrile", "amide", "thio", "fat", "ring", "rotb", "tpsa", "mw", "ffrac"}
# (描述符键, 票数.json 里的中文名, 小图标题, 横轴说明, 横轴取对数, 画“减少”)
PANELS = [("eo", "非氟醚氧", "Fewer non-fluorinated ether O", "decrease in non-F ether O per solvent molecule", False, True),
          ("fat", "溶剂 F 原子数", "More F atoms in the solvent", "increase in F atoms per solvent molecule", False, False),
          ("salt", "主盐浓度", "More main lithium salt", "main-salt concentration, high ÷ low (×)", True, False),
          ("lino3", "LiNO₃ 浓度", "More LiNO₃", "increase in LiNO₃ (M)", False, False)]
FOCUS = {"eo": ("P371", "P381"), "fat": ("P371", "P381"), "salt": ("P112",), "lino3": ("P112",)}  # 各图只标对应问题的论文（问题 1 / 问题 3）


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def mixed(d, r):
    """这对比较是否同时还改了别的（对应“比较不对等”）。"""
    ds = {y["描述符"] for y in r["描述符"]}
    if r.get("特殊组分变化"):
        return True
    if d in ("eo", "fat"):
        return bool(ds & {"salt", "lino3"})
    return bool(ds & (SOLV | ({"lino3"} if d == "salt" else {"salt"})))


def points(R, d, logx, down):
    """与 step17.votes 相同的计法：一对一票。效果 = 往共识方向变的一侧相对另一侧（down = 画“减少”）。"""
    out = []
    for r in R:
        if r["类别"] != "LiCu_CE" or r["比较类型"] != T.SAME:
            continue
        x = next((y for y in r["描述符"] if y["描述符"] == d), None)
        if not x:
            continue
        hi, lo = max(x["A"], x["B"]), min(x["A"], x["B"])
        dx = (hi / lo if lo > 0 else float("nan")) if logx else hi - lo
        e = T.up(x) * T.effect(r) * (-1 if down else 1)
        out.append({"论文": r["论文"], "dx": dx, "e": e, "混改": mixed(d, r), "A": r["A"]["配方名"], "B": r["B"]["配方名"]})
    return out


def main():
    R = load(PAIRS)
    V = {(r["描述符"], r["性能"]): r["同测试"] for r in load(VOTES)}
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.text(0.045, 0.935, "Formulation comparisons: does the consensus hold, and where does it break?", fontsize=21, fontweight="bold",
             color=INK, va="bottom")
    fig.text(0.045, 0.85, "Each dot = one pair of electrolytes compared in the same paper and the same Li‖Cu test (313 papers).  "
             "Across: how much the descriptor changed in the consensus direction.  Up: how the Li‖Cu CE changed.\n"
             "Blue upper half = agrees with the consensus;  red lower half = counterexample;  grey band = within 5 %.\n"
             "Filled dot = nothing else changed in that pair;  open dot = something else changed too (salt, LiNO₃, solvent or a special component).",
             fontsize=11, color=INK2, va="bottom", linespacing=1.5)
    pos = [(0.06, 0.465), (0.555, 0.465), (0.06, 0.075), (0.555, 0.075)]
    summary = {}
    ylim = (-math.log(12), math.log(12))
    for (d, cn, title, xl, logx, down), (px, py) in zip(PANELS, pos):
        P = [p for p in points(R, d, logx, down) if not math.isnan(p["dx"])]
        ax = fig.add_axes([px, py, 0.40, 0.27])
        x = np.array([p["dx"] for p in P])
        e = np.clip(np.array([p["e"] for p in P]), *ylim)
        mx = np.array([p["混改"] for p in P])
        good, bad = e > LN5, e < -LN5
        near = ~good & ~bad
        xr = (0.9, max(x) * 1.3) if logx else (0, max(x) * 1.08)
        if logx:
            ax.set_xscale("log")
        ax.axhspan(0, ylim[1], color=TINT_OK, zorder=0)
        ax.axhspan(ylim[0], 0, color=TINT_NO, zorder=0)
        ax.axhspan(-LN5, LN5, color="#e6e6e6", zorder=1)
        ax.axhline(0, color=MUTED, lw=0.8, zorder=1)
        rng = np.random.default_rng(1)
        xj = x * np.exp(rng.normal(0, 0.03, len(x))) if logx else x + rng.normal(0, 0.006 * (xr[1] - xr[0]), len(x))
        for m, col, s, z in ((near, NEAR, 26, 3), (good, BETTER, 34, 4), (bad, WORSE, 44, 5)):
            ax.scatter(xj[m & ~mx], e[m & ~mx], s=s, c=col, lw=0.4, edgecolors="white", zorder=z)
            ax.scatter(xj[m & mx], e[m & mx], s=s, facecolors="white", edgecolors=col, lw=1.4, zorder=z)
        lab = {}  # 问题论文：每篇标一个反例点，优先实心（只改了这一类），再取离 0 最远的
        for i, p in enumerate(P):
            if p["论文"] in FOCUS[d] and bad[i]:
                k = (not mx[i], abs(e[i]))
                if p["论文"] not in lab or k > lab[p["论文"]][0]:
                    lab[p["论文"]] = (k, i)
        for k, (pid, (_, i)) in enumerate(sorted(lab.items())):
            ax.annotate(pid, (xj[i], e[i]), xytext=(14, -14 - 14 * k), textcoords="offset points", fontsize=10,
                        color=WORSE, fontweight="bold", zorder=7, path_effects=HALO, arrowprops=dict(arrowstyle="-", color=WORSE, lw=0.7))
        v = V[(cn, "Li‖Cu CE")]
        ng, nb, nn = int(good.sum()), int(bad.sum()), int(near.sum())
        exp = (v["差"], v["好"]) if down else (v["好"], v["差"])
        assert (ng, nb, nn) == (*exp, v["近"]), (d, ng, nb, nn, v)
        nbc = int((bad & ~mx).sum())
        ax.set_title(f"{title} → higher CE?    {ng / max(1, ng + nb):.0%} agree ({v['篇']} papers)\n", loc="left", fontsize=12.5,
                     color=INK, fontweight="bold")
        ax.text(0, 1.025, f"{ng} with the consensus", transform=ax.transAxes, fontsize=11, color=BETTER, fontweight="bold", va="bottom")
        ax.text(0.31, 1.025, f"{nb} counterexamples, {nbc} with nothing else changed" + (f";  {nn} within 5 %" if nn else ""),
                transform=ax.transAxes, fontsize=11, color=WORSE, fontweight="bold", va="bottom")
        ax.set_xlim(*xr); ax.set_ylim(*ylim)
        ax.set_yticks([math.log(t) for t in (1 / 8, 1 / 4, 1 / 2, 1, 2, 4, 8)])
        ax.set_yticklabels(["Li loss ×8", "×4", "×2", "same", "÷2", "÷4", "÷8"])
        ax.set_xlabel(xl, fontsize=10, color=INK2)
        if logx:
            ax.set_xticks([1, 2, 4, 8, 16]); ax.set_xticklabels(["×1", "×2", "×4", "×8", "×16"]); ax.minorticks_off()
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color("#bdbdbd")
        ax.tick_params(colors="#555555", labelsize=9)
        summary[cn] = {"画法": "减少" if down else "增加", "比较": len(P), "共识一侧": ng, "反例": nb, "相近": nn, "论文": v["篇"],
                       "反例中实心（只改了这一类）": nbc, "共识一侧中空心（混改）": int((good & mx).sum()),
                       "实心反例": [{"论文": P[i]["论文"], "配方": f"{P[i]['B']} vs {P[i]['A']}"} for i in np.flatnonzero(bad & ~mx)],
                       "反例论文": sorted({p["论文"] for p, b in zip(P, bad) if b}), "标号": sorted(lab)}
    fig.text(0.045, 0.012, "Counted exactly as the votes (step17, same-test pairs; a dot counts when the descriptor changed within the pair); "
             "values beyond ×12 are drawn at the edge. Labelled: counterexample dots from the papers behind the open questions "
             "(P371, P381 → question 1; P112 → question 3).", fontsize=8.5, color=MUTED, va="bottom")
    f = OUT / "fig_formulation_space.png"
    fig.savefig(f, dpi=300, facecolor="white")
    plt.close(fig)
    shutil.copy(f, SITE / "fig_formulation_space.png")
    (OUT / "配方空间汇总.json").write_text(json.dumps({"说明": "Li‖Cu 同测试换配方，一对一票，计法同 step17；每个点 = 一次比较", "小图": summary},
                                                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f, json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
