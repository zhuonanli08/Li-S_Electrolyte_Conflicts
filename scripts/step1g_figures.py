"""第 1 步 g：研究现状图（零成本）。读 step1f 的 step1_landscape.pkl。

图1 共现网络（VOSviewer 风格）：节点 = 溶剂 / 稀释剂 / 盐 / 介体（实验里用到）+ 电解液策略（题名摘要）+ 测试条件（第 1 步判读）；
     节点面积 ∝ 篇数；连线 = 同一篇论文里同时出现，按关联强度（实际共现 / 随机期望）布局，只画每个节点最强的几条
图2 空白热图：每种化学品 × 测试条件的篇数，以及三个时段的使用比例
输出：output/图/图1_共现网络.png、图2_空白热图.png
"""
import math
import os

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

matplotlib.rcParams["font.family"] = ["Arial", "Microsoft YaHei"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "图")
os.makedirs(OUT, exist_ok=True)

# 分类色：参考配色的前 7 个槽位，固定顺序；每个节点都有文字标签，颜色只是辅助
CATS = [("Ether solvent", "#2a78d6"), ("Diluent (fluorinated / hydrocarbon)", "#eb6834"), ("Other solvent", "#1baf7a"),
        ("Lithium salt", "#eda100"), ("Redox mediator", "#e87ba4"), ("Electrolyte strategy (title/abstract)", "#008300"),
        ("Test condition", "#4a3aa7")]
COL = dict(CATS)
TEXT = "#0b0b0b"
MUTED = "#52514e"

CHEM = [  # (图上名称, landscape 列名, 类别)
    ("DME", "DME", "Ether solvent"), ("DOL", "DOL", "Ether solvent"), ("G2", "二甘醇二甲醚 G2", "Ether solvent"),
    ("G3", "三甘醇二甲醚 G3", "Ether solvent"), ("G4 (TEGDME)", "四甘醇二甲醚 G4", "Ether solvent"), ("DEE", "1,2-二乙氧基乙烷 DEE", "Ether solvent"),
    ("DMM", "二甲氧基甲烷 DMM", "Ether solvent"), ("THF", "THF", "Ether solvent"), ("1,4-dioxane", "1,4-二氧六环", "Ether solvent"),
    ("DBE", "DBE 二丁醚", "Ether solvent"), ("DIPE", "DIPE 二异丙醚", "Ether solvent"), ("DPE", "DPE 二丙醚", "Ether solvent"),
    ("MTBE", "MTBE", "Ether solvent"), ("CPME", "CPME", "Ether solvent"), ("THP", "THP", "Ether solvent"),
    ("TTE", "TTE", "Diluent (fluorinated / hydrocarbon)"), ("BTFE", "BTFE", "Diluent (fluorinated / hydrocarbon)"),
    ("Other HFE", "TFEE/OFE/其他 HFE", "Diluent (fluorinated / hydrocarbon)"),
    ("Alkanes", "己烷/庚烷/环己烷", "Diluent (fluorinated / hydrocarbon)"), ("Aromatics", "苯/甲苯/氟苯/三氟甲苯", "Diluent (fluorinated / hydrocarbon)"),
    ("Carbonates", "碳酸酯(EC/DEC/DMC/EMC/PC)", "Other solvent"), ("FEC/VC", "FEC/VC", "Other solvent"), ("Sulfolane", "环丁砜 SL", "Other solvent"),
    ("DMSO", "DMSO", "Other solvent"), ("Acetonitrile", "乙腈 ACN", "Other solvent"), ("DMA/DMF", "DMA/DMF", "Other solvent"),
    ("TMU/DMI", "TMU/DMI/环脲", "Other solvent"), ("Phosphates", "TEP/TMP/磷腈", "Other solvent"), ("Ionic liquids", "离子液体", "Other solvent"),
    ("Siloxanes", "硅氧烷/硅烷", "Other solvent"),
    ("LiTFSI", "LiTFSI", "Lithium salt"), ("LiFSI", "LiFSI", "Lithium salt"), ("LiNO3", "LiNO3", "Lithium salt"),
    ("LiDFOB/LiBOB", "LiDFOB/LiBOB", "Lithium salt"), ("LiPF6/LiBF4/LiClO4", "LiPF6/LiBF4/LiClO4", "Lithium salt"),
    ("LiOTf", "LiOTf", "Lithium salt"), ("LiI/LiBr", "卤化锂(LiI/LiBr)", "Lithium salt"), ("Hückel salts", "Hückel 阴离子(LiTDI等)", "Lithium salt"),
    ("Quinones", "醌类", "Redox mediator"), ("Organo-Se/S", "有机硒/有机硫介体", "Redox mediator"), ("Metal complexes/ions", "金属有机/金属离子", "Redox mediator"),
]
STRAT = [("Highly solvating", "强溶剂化"), ("Moderately solvating", "适中溶剂化"), ("Weakly solvating", "弱溶剂化"),
         ("Sparingly solvating", "难溶/固相转化"), ("LHCE", "局部高浓"), ("HCE", "高浓"), ("Low concentration", "低浓"), ("Fluorination", "氟化/无氟")]


FAST = pd.read_pickle(os.path.join(ROOT, "output", "step1_fastcycling.pkl")).set_index("doi")["高倍率长循环"]


def build():
    X = pd.read_pickle(os.path.join(ROOT, "output", "step1_landscape.pkl"))
    fam = X["电解液类别(题名+摘要)"].fillna("").str.split("; ")
    B = pd.DataFrame(index=X.index)
    cat = {}
    for lab, col, c in CHEM:
        B[lab] = X["用到|" + col]
        cat[lab] = c
    for lab, k in STRAT:
        B[lab] = fam.apply(lambda xs, k=k: k in xs)
        cat[lab] = "Electrolyte strategy (title/abstract)"
    conds = {"Lean (E/S ≤ 5)": X["贫液实验"].fillna(False).astype(bool),
             "Anode-limited (thin Li / N/P ≤ 3)": X["负极受限(薄锂/N/P≤3/无负极)"].fillna(False).astype(bool),
             "High S loading (≥ 4 mg/cm²)": X["高载量实验"].fillna(False).astype(bool),
             "Pouch cell": X["软包"] == "✅", "Low-T test": X["低温测试(粗)"] == "✅",
             "Fast cycling (≥ 3C, ≥ 100 cycles)": X["doi"].map(FAST).fillna(False).astype(bool),  # 用户 10-13 加：倍率阶梯不算
             "SPAN cathode": X["正极层"] == "SPAN"}
    for lab, s in conds.items():
        B[lab] = s
        cat[lab] = "Test condition"
    return X, B.astype(bool), cat, list(conds)


def place_labels(fig, ax, items):
    """候选位置法放标签：按节点从大到小，依次试节点周围 8 个方位（再试远一圈），
    取第一个不压已放标签、不压其他节点、不出画布的位置；都不行就取重叠最小的。位置有限，不会发散。
    items: [(文字, 节点坐标, 字号, 节点半径pt, 篇数)]"""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    px = fig.dpi / 72  # 点 → 像素
    frame = ax.get_window_extent(rend)
    node_boxes = []
    for _, xy, _, r, _ in items:
        cx, cy = ax.transData.transform(xy)
        node_boxes.append(matplotlib.transforms.Bbox([[cx - r * px, cy - r * px], [cx + r * px, cy + r * px]]))
    dirs = [(1, 1, "left", "bottom"), (1, -1, "left", "top"), (-1, 1, "right", "bottom"), (-1, -1, "right", "top"),
            (1, 0, "left", "center"), (-1, 0, "right", "center"), (0, 1, "center", "bottom"), (0, -1, "center", "top")]
    placed = []
    order = sorted(range(len(items)), key=lambda i: -items[i][4])
    for i in order:
        text, xy, fs, r, _ = items[i]
        best = None
        for scale in (1.0, 1.9, 2.8):
            for dx, dy, ha, va in dirs:
                d = (r + 2) * scale
                a = ax.annotate(text, xy, xytext=(dx * d * (0.75 if dy else 1), dy * d * (0.75 if dx else 1)),
                                textcoords="offset points", ha=ha, va=va, fontsize=fs, color=TEXT, zorder=4)
                bb = a.get_window_extent(rend).expanded(1.04, 1.12)
                cost = sum(max(0, min(bb.x1, o.x1) - max(bb.x0, o.x0)) * max(0, min(bb.y1, o.y1) - max(bb.y0, o.y0))
                           for o in placed + [nb for j, nb in enumerate(node_boxes) if j != i])
                if not frame.contains(bb.x0, bb.y0) or not frame.contains(bb.x1, bb.y1):
                    cost += 1e7
                if best is None or cost < best[0]:
                    if best:
                        best[1].remove()
                    best = (cost, a, bb)
                else:
                    a.remove()
                if cost == 0:
                    break
            if best[0] == 0:
                break
        placed.append(best[2])


def network(B, cat):
    N = len(B)
    n = B.sum()
    keep = [c for c in B.columns if n[c] >= 5]
    M = B[keep].astype(int)
    C = M.T @ M
    G = nx.Graph()
    for c in keep:
        G.add_node(c, n=int(n[c]))
    cand = []
    for i, a in enumerate(keep):
        for b in keep[i + 1:]:
            cij = int(C.loc[a, b])
            if cij >= 3:
                s = cij * N / (n[a] * n[b])  # 关联强度：实际共现 / 随机期望
                cand.append((a, b, cij, s))
    E = pd.DataFrame(cand, columns=["a", "b", "c", "s"])
    chosen = set()
    for node in keep:  # 每个节点保留关联最强的 4 条（且至少共现 4 篇）
        sub = E[((E.a == node) | (E.b == node)) & (E.c >= 4)].nlargest(4, "s")
        chosen.update(sub.index)
    for _, e in E.loc[sorted(chosen)].iterrows():
        G.add_edge(e.a, e.b, c=int(e.c), w=min(float(e.s), 6.0))
    pos = nx.spring_layout(G, weight="w", k=1.6 / math.sqrt(len(G)), iterations=800, seed=11)

    fig, ax = plt.subplots(figsize=(15, 11.5), dpi=200)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    for a, b, d in G.edges(data=True):
        src = a if n[a] < n[b] else b  # 边用较小节点的颜色，像 VOSviewer
        ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]], color=COL[cat[src]],
                alpha=0.18 + 0.25 * min(d["c"] / 150, 1), lw=0.6 + 2.6 * min(d["c"] / 150, 1), zorder=1, solid_capstyle="round")
    items = []
    for v in G.nodes:
        size = 40 + 3.2 * G.nodes[v]["n"]
        ax.scatter(*pos[v], s=size, color=COL[cat[v]], edgecolor="#fcfcfb", linewidth=1.5, zorder=3)
        fs = 8.5 + 4.5 * math.sqrt(G.nodes[v]["n"] / 550)
        items.append((f"{v} ({G.nodes[v]['n']})", pos[v], fs, math.sqrt(size) / 2, G.nodes[v]["n"]))
    ax.set_axis_off()
    place_labels(fig, ax, items)
    handles = [plt.Line2D([], [], marker="o", ls="", color=c, markersize=9, label=l) for l, c in CATS]
    # 图例放在框外右上，布局怎么变都不会压住节点
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.0, 1.0), frameon=False, fontsize=10, labelcolor=MUTED)
    ax.set_title("Li–S liquid-electrolyte literature (667 papers, 2016–2026): co-occurrence of solvents, salts, mediators, strategies and test conditions",
                 fontsize=12.5, color=TEXT, loc="left")
    fig.text(0.01, 0.01, "Node size ∝ number of papers (in brackets). Lines link items appearing in the same paper; layout by association strength "
             "(observed ÷ expected co-occurrence), each node shows its 4 strongest links. Chemicals = used in the paper's own experiments "
             "(regex on full text + SI); strategies = authors' wording in title/abstract; conditions = step-1 check.",
             fontsize=8.5, color=MUTED, wrap=True)
    fig.savefig(os.path.join(OUT, "图1_共现网络_v2_含快充.png"), bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def heatmap(X, B, cat, conds):
    chems = [lab for lab, _, _ in CHEM] + [lab for lab, _ in STRAT]
    rows = []
    per = {"2016–2019": X["年份"] <= 2019, "2020–2022": X["年份"].between(2020, 2022), "2023–2026": X["年份"] >= 2023}
    for c in chems:
        u = B[c]
        r = {"item": c, "All papers": int(u.sum())}
        for k in conds:
            r[k] = int((u & B[k]).sum())
        for p, m in per.items():
            r[p] = 100 * (u & m).sum() / m.sum()
        rows.append(r)
    H = pd.DataFrame(rows).set_index("item")
    cols1 = ["All papers"] + conds
    cols2 = list(per)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 15), dpi=200, gridspec_kw={"width_ratios": [7, 3]})
    fig.patch.set_facecolor("#fcfcfb")
    for ax, cols, cmap, fmt, title in [(a1, cols1, "Blues", "{:.0f}", "Number of papers (darker = more studied; pale = gap; colour on log scale)"),
                                       (a2, cols2, "Greens", "{:.0f}%", "Share of papers using it, by period")]:
        V = H[cols].values.astype(float)
        norm = np.log1p(V) / np.log1p(V.max()) if ax is a1 else V / V.max()
        ax.imshow(norm, cmap=cmap, aspect="auto", vmin=0, vmax=1)
        for i in range(V.shape[0]):
            for j in range(V.shape[1]):
                ax.text(j, i, fmt.format(V[i, j]), ha="center", va="center", fontsize=8.5,
                        color="#ffffff" if norm[i, j] > 0.62 else TEXT)
        ax.set_xticks(range(len(cols)))
        ax.set_xticklabels([c.replace(" (", "\n(") for c in cols], fontsize=9, color=TEXT, rotation=0)
        ax.xaxis.tick_top()
        ax.set_yticks(range(len(H)))
        ax.set_yticklabels(H.index if ax is a1 else [""] * len(H), fontsize=9.5, color=TEXT)
        if ax is a1:  # 类别用标签旁的色块表示，文字保持深色
            ax.tick_params(axis="y", pad=16)
            for k, lab in enumerate(H.index):
                ax.scatter(-0.62, k, marker="s", s=38, color=COL[cat[lab]], clip_on=False, zorder=5)
            ax.set_xlim(-0.5, len(cols) - 0.5)  # 色块画在框外，不撑出空白列
        ax.set_title(title, fontsize=11, color=TEXT, pad=38, loc="left")
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_xticks(np.arange(-.5, len(cols), 1), minor=True)
        ax.set_yticks(np.arange(-.5, len(H), 1), minor=True)
        ax.grid(which="minor", color="#fcfcfb", linewidth=2)
        ax.tick_params(which="both", length=0)
    handles = [plt.Line2D([], [], marker="s", ls="", color=c, markersize=9, label=l) for l, c in CATS[:6]]
    fig.legend(handles=handles, loc="lower left", frameon=False, fontsize=9, ncol=3, labelcolor=MUTED, bbox_to_anchor=(0.01, -0.005))
    fig.suptitle("Where the Li–S liquid-electrolyte literature is thin: chemistry × test condition (667 papers)", fontsize=13, color=TEXT, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.03, 1, 0.98))
    fig.savefig(os.path.join(OUT, "图2_空白热图_v2_含快充.png"), bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    H.to_csv(os.path.join(OUT, "图2_数据_v2_含快充.csv"), encoding="utf-8-sig")


if __name__ == "__main__":
    X, B, cat, conds = build()
    network(B, cat)
    heatmap(X, B, cat, conds)
    print("saved to", OUT)
