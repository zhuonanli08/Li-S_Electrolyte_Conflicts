"""网站 05 页的工作流漏斗图（11-08 用户定：网站 meta 分析部分只放这张图，其余用文字写矛盾与原因）。

每层的单位不同（篇、对、条），条宽只示意逐层收窄，不按数量比例；数字全部从结果文件读。图英文。
输入：两两比较表述 v2、张力候选 v2（票数.json、张力候选.json）、张力判定（判定_v2.json、判定_v2_弱.json）、协同候选、机制证据（step20）。
输出：output/图_313篇_2026-11-08/fig0_funnel.png，并复制到网站 图/。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/fig00_funnel.py
"""
import json
import shutil
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
O = ROOT / "output"
OUT = O / "图_313篇_2026-11-08"
SITE = O / "表述与矛盾试跑_F版30篇_2026-11-04" / "网站" / "图"
RAMP = ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95"]
INK, INK2, MUTED, BG = "#0b0b0b", "#52514e", "#8a8984", "#fcfcfb"


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def numbers():
    n_all = sum(1 for _ in (O / "试跑313篇_2026-11-05" / "papers").iterdir())
    R = load(O / "两两比较表述_313篇_v2_2026-11-07" / "比较表述.json")
    V = load(O / "张力候选_313篇_v2_2026-11-07" / "票数.json")
    C = load(O / "张力候选_313篇_v2_2026-11-07" / "张力候选.json")["反例（按同一批比较合并）"]
    J = load(O / "张力判定_313篇_2026-11-07" / "判定_v2.json") + load(O / "张力判定_313篇_2026-11-07" / "判定_v2_弱.json")
    jr = Counter(x["真假"] for x in J)
    real = sorted({x["论文"] for x in J if x["真假"] == "真张力候选"})
    sy = [x for x in load(O / "协同候选_313篇_v2_2026-11-07" / "协同候选.json")["候选"] if x["结果"] == "协同作用候选"]
    ev = load(O / "机制证据_313篇_2026-11-08" / "机制证据.json")
    return {"papers": n_all, "comparable": len({r["论文"] for r in R}), "pairs": len(R),
            "same": sum(r["比较类型"] == "同测试换配方" for r in R), "rules": len(V),
            "consensus": sum(v["同测试"]["判定"] == "有多数" for v in V), "cex": len(C), "cex_papers": len({x["论文"] for x in C}),
            "unequal": jr["比较不对等"], "data": jr["数据问题"], "known": jr["已知条件"], "pending": jr["待定"], "real": jr["真张力候选"],
            "real_papers": real, "cross": [x["论文"] for x in sy], "questions": len(ev) - 1}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    n = numbers()
    stages = [
        (f"{n['papers']} papers extracted", "full text + SI, one structured record per paper"),
        (f"{n['comparable']} papers with comparable formulations", "at least two electrolytes measured on the same metric"),
        (f"{n['pairs']:,} pairwise comparisons", f"{n['same']} within the same test (used for counting)"),
        (f"{n['rules']} descriptor → performance rules", f"{n['consensus']} with a consensus (≥ 2/3 of votes, ≥ 5 papers)"),
        (f"{n['cex']} counterexamples to a consensus", f"from {n['cex_papers']} papers; each read against the original text"),
        (f"{n['pending'] + n['real']} not explained after reading", f"{n['real']} genuine-tension candidates ({', '.join(n['real_papers'])}), {n['pending']} pending"),
        (f"{n['questions']} open questions", "diluent decomposition · LiNO₃ dose · salt × LiNO₃"),
    ]
    fig, ax = plt.subplots(figsize=(11, 6.6), dpi=200)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.55, len(stages) - 0.45)
    ax.axis("off")
    plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]
    cx, h = 35, 0.76
    for i, (big, small) in enumerate(stages):
        y = len(stages) - 1 - i
        w = 66 - i * 4.4
        col = RAMP[min(i + 1, len(RAMP) - 1)]
        ax.add_patch(FancyBboxPatch((cx - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.18", fc=col, ec=BG, lw=2))
        tc = "white" if i >= 2 else INK
        ax.text(cx, y + 0.1, big, ha="center", va="center", fontsize=11.5, fontweight="bold", color=tc)
        ax.text(cx, y - 0.2, small, ha="center", va="center", fontsize=8.3, color=tc, alpha=0.95)
    # 第 5 → 6 层：读原文后分出去的
    y5 = len(stages) - 1 - 4
    ax.annotate("", xy=(70, y5 - 0.5), xytext=(cx + (66 - 4 * 4.4) / 2 + 0.5, y5 - 0.5),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.1, mutation_scale=10))
    ax.text(71, y5 - 0.5, f"Explained after reading ({n['unequal'] + n['data'] + n['known']}):\n"
            f"• unequal comparison {n['unequal']} (another change mixed in,\n   weak/strong reference)\n• data issue {n['data']}\n"
            f"• already-known condition {n['known']} (P108: carbonate\n   works with confined-sulfur cathodes)",
            ha="left", va="center", fontsize=8.5, color=INK2, linespacing=1.35)
    # 协同作用（交叉设计）汇入最后一层
    y7 = 0
    ax.annotate("", xy=(cx + (66 - 6 * 4.4) / 2 + 0.5, y7), xytext=(70, y7),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.1, mutation_scale=10))
    ax.text(71, y7, f"+ same-paper cross design ({', '.join(n['cross'])}):\n   salt concentration × LiNO₃",
            ha="left", va="center", fontsize=8.5, color=INK2, linespacing=1.35)
    fig.text(0.03, 0.955, "How the workflow found the open questions (313 of 535 papers so far)", fontsize=13.5, fontweight="bold", color=INK)
    fig.text(0.03, 0.915, "Bar widths are schematic: each level counts a different unit (papers, comparisons, rules, counterexamples).",
             fontsize=8.5, color=MUTED)
    fig.text(0.03, 0.02, "Preliminary; AI-assisted reading and mechanism grouping, not yet manually verified.", fontsize=8, color=MUTED)
    fig.subplots_adjust(left=0.02, right=0.99, top=0.89, bottom=0.06)
    f = OUT / "fig0_funnel.png"
    fig.savefig(f, facecolor=BG)
    SITE.mkdir(parents=True, exist_ok=True)
    shutil.copy(f, SITE / f.name)
    print(json.dumps(n, ensure_ascii=False))
    print(f)


if __name__ == "__main__":
    main()
