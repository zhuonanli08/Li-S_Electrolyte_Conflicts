"""图 3（试画，11-08 用户：“你试试这个点图吧”）：已知张力“溶剂化变弱 → 负极好、容量低”能否从票数里找回。

每行一个描述符（统一成“溶剂化变弱”的方向：含氟比例、F 原子数、稀释剂比例升高；每个 Li⁺ 配位位点变少），
每行三个点 = Li‖Cu CE、每圈衰减率、首圈容量在“溶剂化变弱时变好”的票占比（相近不计）；实心 = 全部票，空心 = 去掉特殊组分的对。
背景三段：< 1/3 变差有共识，1/3–2/3 没有共识，> 2/3 变好有共识（另需多数方向 ≥ 5 篇，不够的标 *）。
计票口径与 step17 相同（同测试换配方、一对一票、5% 门槛）。图英文。初步；AI 辅助，用户尚未逐项人工确认。
输出：output/图_313篇_2026-11-08/fig3_known_tension.png（及 .json 数值）。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/fig03_known_tension.py
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
import step17_tension_trial as T

IN = ROOT / "output" / "两两比较表述_313篇_v2_2026-11-07" / "比较表述.json"
OUT = ROOT / "output" / "图_313篇_2026-11-08"
ROWS = [("含氟溶剂比例", 1, r"Fluorinated solvent fraction $\uparrow$"),
        ("溶剂 F 原子数", 1, r"Solvent F atoms $\uparrow$"),
        ("稀释剂摩尔比例", 1, r"Diluent mole fraction $\uparrow$"),
        ("每个 Li⁺ 的配位位点", -1, r"Li$^+$ coordination sites $\downarrow$")]
METRICS = [("Li‖Cu CE", r"Li$\Vert$Cu CE", "#2a78d6", "o"),
           ("每圈衰减率", "Fade rate per cycle", "#eb6834", "s"),
           ("首圈容量", "Initial capacity", "#1baf7a", "^")]
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"


def count(R, byid, key, d, sign, c, clean):
    vs = [v | {"效应": sign * v["效应"]} for v in T.votes(R, key[d], {v: k for k, v in T.CN.items()}[c], {T.SAME})]
    if clean:
        vs = [v for v in vs if not byid[v["编号"]].get("特殊组分变化")]
    t, _ = T.tally(vs)
    share = 100 * t["好"] / (t["好"] + t["差"]) if t["好"] + t["差"] else None
    return {"好": t["好"], "差": t["差"], "篇": t["篇"], "变好占比%": None if share is None else round(share, 1),
            "判定": t["判定"], "多数": t["多数"], "多数方向来自几篇": t["多数方向来自几篇"]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    R = json.loads(IN.read_text(encoding="utf-8"))
    byid = {r["编号"]: r for r in R}
    key = {x["中文"]: x["描述符"] for r in R for x in r["描述符"]}
    data = []
    for d, sign, _ in ROWS:
        for c, *_ in METRICS:
            data.append({"描述符": d, "方向": "升高" if sign > 0 else "变少", "性能": c,
                         "全部": count(R, byid, key, d, sign, c, False), "去掉特殊组分": count(R, byid, key, d, sign, c, True)})
    (OUT / "fig3_known_tension.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    plt.rcParams.update({"font.family": ["Arial", "DejaVu Sans"], "font.size": 10, "axes.edgecolor": MUTED,
                         "xtick.color": INK2, "ytick.color": INK2})
    fig, ax = plt.subplots(figsize=(11, 6.8), dpi=200)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    lo, hi = 100 / 3, 200 / 3
    for a, b, col in ((0, lo, "#ebeae6"), (lo, hi, "#f6f5f2"), (hi, 100, "#ebeae6")):
        ax.axvspan(a, b, color=col, zorder=0, lw=0)
    for x in (lo, hi):
        ax.axvline(x, color=MUTED, lw=0.8, ls=(0, (3, 3)), zorder=1)
    yt, yl, ytop = [], [], 0
    gap, step = 1.2, 0.85
    y = 0
    pos = {}
    for gi, (d, sign, lab) in enumerate(ROWS):
        for mi, (c, mlab, col, mk) in enumerate(METRICS):
            pos[(d, c)] = y
            yt.append(y)
            yl.append(mlab)
            y -= step
        ax.text(-0.5, pos[(d, METRICS[0][0])] + 0.55, lab, ha="right", va="bottom", fontsize=10.5, fontweight="bold", color=INK, clip_on=False)
        y -= gap
    for x in data:
        d, c = x["描述符"], x["性能"]
        _, mlab, col, mk = next(m for m in METRICS if m[0] == c)
        yy = pos[(d, c)]
        a, b = x["全部"], x["去掉特殊组分"]
        if a["变好占比%"] is not None and b["变好占比%"] is not None and abs(a["变好占比%"] - b["变好占比%"]) >= 1:
            ax.annotate("", xy=(b["变好占比%"], yy), xytext=(a["变好占比%"], yy),
                        arrowprops=dict(arrowstyle="-|>", color=col, lw=1.2, shrinkA=5, shrinkB=5, mutation_scale=9), zorder=2)
        ax.plot(b["变好占比%"], yy, mk, ms=11, mfc="#fcfcfb", mec=col, mew=1.8, zorder=3)
        ax.plot(a["变好占比%"], yy, mk, ms=6.5, color=col, mec=col, zorder=4)
        star = lambda t: "*" if t["多数方向来自几篇"] < T.MIN_PAPERS and max(t["变好占比%"], 100 - t["变好占比%"]) >= 200 / 3 else ""
        txt = f"{a['好']}:{a['差']} ({a['篇']} papers){star(a)}   →   {b['好']}:{b['差']} ({b['篇']}){star(b)}"
        ax.text(102, yy, txt, va="center", ha="left", fontsize=8.5, color=INK2, clip_on=False)
    ax.set_yticks(yt)
    ax.set_yticklabels(yl, fontsize=9)
    ax.tick_params(axis="y", length=0)
    ax.set_ylim(y + gap - 0.6, 0.95)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 100 / 3, 50, 200 / 3, 75, 100])
    ax.set_xticklabels(["0", "25", "33", "50", "67", "75", "100"])
    ax.set_xlabel("Share of votes saying 'better' when solvation weakens (%)   [better = higher CE, lower fade, higher capacity]",
                  color=INK2, fontsize=9)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    for xm, t in ((lo / 2, "Consensus: worse"), ((lo + hi) / 2, "No consensus"), ((hi + 100) / 2, "Consensus: better")):
        ax.text(xm, 1.02, t, ha="center", va="bottom", fontsize=9, color=INK2, fontweight="bold", transform=ax.get_xaxis_transform())
    ax.text(1.02, 1.02, "better : worse votes (papers)\nall  →  excluding special", ha="left", va="bottom", fontsize=8.5, color=INK2, transform=ax.transAxes)
    h = [plt.Line2D([], [], marker=mk, ls="", ms=8, color=col, mec="#fcfcfb", label=mlab) for _, mlab, col, mk in METRICS]
    h += [plt.Line2D([], [], marker="o", ls="", ms=6.5, color=MUTED, label="All votes"),
          plt.Line2D([], [], marker="o", ls="", ms=10, mfc="#fcfcfb", mec=MUTED, mew=1.8, label="Excluding special components")]
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(0.02, 0.935), ncol=5, frameon=False, fontsize=9, handletextpad=0.3, columnspacing=1.2)
    fig.text(0.02, 0.955, "Known tension check: does weaker solvation give a better anode but lower capacity?", fontsize=12.5,
             fontweight="bold", color=INK)
    fig.text(0.02, 0.012, "313 papers (73 used here); same-test pairwise comparisons, one pair = one vote, |change| < 5% not counted.\n"
             "Consensus also needs the majority from ≥ 5 papers (* = fewer). Preliminary; AI-assisted, not yet manually verified.",
             fontsize=7.5, color=MUTED)
    fig.subplots_adjust(left=0.25, right=0.72, top=0.80, bottom=0.14)
    f = OUT / "fig3_known_tension.png"
    fig.savefig(f, facecolor=fig.get_facecolor())
    print(json.dumps([{k: x[k] for k in ("描述符", "性能")} | {"全部": x["全部"]["变好占比%"], "去掉": x["去掉特殊组分"]["变好占比%"],
                       "判定": x["全部"]["判定"] + " → " + x["去掉特殊组分"]["判定"]} for x in data], ensure_ascii=False, indent=0))
    print(f)


if __name__ == "__main__":
    main()
