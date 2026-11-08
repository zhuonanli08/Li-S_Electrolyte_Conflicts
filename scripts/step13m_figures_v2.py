"""step13m：Figures 页 v2（11-06 用户要求：描述符按数值画——放坐标轴、颜色或大小，不切 low/high；聚类从分子结构层面做，参照 SES AI 的 Molecular Universe / 电解液基因组）。
先用 rdkit 环境跑 step13m_fp.py 生成指纹。图上文字英文。图写到网站 图/，数据写到 output/表述试跑313篇_2026-11-05/结构描述符图/v2/。
  图 1  描述符相关网络（取代图 1a/1b 的低/高共现网络）：节点 = 22 个结构描述符（颜色 = meta v3 的轴，大小 = 有该结构的配方数），线 = 跨配方 Spearman |ρ| ≥ 0.3；
  图 2  配方空间（取代图 1b）：每个点 = 同测试里换上的新配方，横轴每个 Li⁺ 的配位位点，纵轴可切换，颜色 = 相对本篇对照的性能（ln 倍数），四类性能四个小图；
  图 3  平行坐标（取代图 2a/2b 弦图）：每条线 = 同测试里换上的新配方，竖轴 = 描述符数值 → 条件 → 相对对照的性能，可在轴上拖选；
  图 6a 分子宇宙：313 篇用到的 263 个组分，距离 = ½ Morgan 指纹（r = 2）Jaccard ＋ ½ 官能团组成（描述符表，log 后标准化的欧氏距离，按 95 分位缩到 0–1）→ t-SNE；
         家族 = HDBSCAN，HDBSCAN 没归入的并入最相似的已归类分子所在家族（11-06 用户要求不留未归类）；颜色可切换：结构家族 / 角色 / 使用的论文数；
  图 6b 配方基因组：行 = 配方（按官能团组成层次聚类），列 = 官能团与盐描述符，颜色 = 该列内的百分位，悬停给原值。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/step13m_figures_v2.py
"""
import sys
import json
import math
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
from scipy import stats

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "step15_meta"))
import step13h_descriptor_figures as H
import F_pooled as F
import D_site as D

OUTD = ROOT / "output" / "表述试跑313篇_2026-11-05" / "结构描述符图" / "v2"
FIG = D.SITE_FIG
C313 = ROOT / "output" / "组分结构表_试跑313篇_2026-11-05"
V3 = json.loads((F.OUT / "汇总.json").read_text(encoding="utf-8"))
AXCOL = dict(zip(V3["轴"], D.REASON_COLORS))
LAB = F.LAB
EN = D.EN_CLASS
summary = {}


def write(fig, name):
    fig.write_html(FIG / name, include_plotlyjs="directory", full_html=True, config={"displaylogo": False})


# ---------------- 图 1 描述符相关网络 ----------------
def fig_corr(M):
    import plotly.graph_objects as go
    import networkx as nx
    ov = V3["重叠"]
    ks, R = ov["描述符"], np.array(ov["相关矩阵"])
    F_ = {}
    for r in M:
        F_[(r["论文"], r["recipe"])] = r["D"]
    nz = {k: sum(1 for v in F_.values() if v.get(k) not in (None, 0, 0.0)) for k in ks}
    order = [d for ax in V3["轴"] for d in V3["轴"][ax]["成员"] if d in ks]
    pos = {d: (math.cos(math.pi / 2 - 2 * math.pi * i / len(order)), math.sin(math.pi / 2 - 2 * math.pi * i / len(order))) for i, d in enumerate(order)}

    def arc(p0, p1, n=24):  # 经过圆心附近的二次贝塞尔弧线
        t = np.linspace(0, 1, n)[:, None]
        c = np.array([0.0, 0.0]) * 0.6 + (np.array(p0) + np.array(p1)) / 2 * 0.4
        return ((1 - t) ** 2 * np.array(p0) + 2 * (1 - t) * t * c + t ** 2 * np.array(p1)).T
    fig = go.Figure()
    for i, a in enumerate(ks):
        for j in range(i + 1, len(ks)):
            r = R[i, j]
            if abs(r) < 0.3:
                continue
            b = ks[j]
            xs, ys = arc(pos[a], pos[b])
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(width=1 + 9 * (abs(r) - 0.3), color=D.BLUE if r > 0 else "#d03b3b"),
                                     opacity=0.35 + 0.6 * (abs(r) - 0.3), hoverinfo="skip", showlegend=False))
            fig.add_trace(go.Scatter(x=[xs[12]], y=[ys[12]], mode="markers", marker=dict(size=10, opacity=0.01), showlegend=False,
                                     hovertext=f"{LAB[a]} ~ {LAB[b]}: ρ = {r:+.2f}", hoverinfo="text"))
    for ax in V3["轴"]:
        ds = [d for d in V3["轴"][ax]["成员"] if d in pos]
        if not ds:
            continue
        fig.add_trace(go.Scatter(x=[pos[d][0] for d in ds], y=[pos[d][1] for d in ds], mode="markers+text", name=ax, text=[LAB[d] for d in ds],
                                 textposition=["middle right" if pos[d][0] > 0.05 else "middle left" if pos[d][0] < -0.05 else ("top center" if pos[d][1] > 0 else "bottom center") for d in ds],
                                 textfont=dict(size=10.5, color=D.INK),
                                 marker=dict(size=[9 + 2.2 * math.sqrt(nz[d]) for d in ds], color=AXCOL[ax], line=dict(width=1.5, color="white")),
                                 hovertext=[f"<b>{LAB[d]}</b> ({ax})<br>non-zero in {nz[d]} of {len(F_)} formulations" for d in ds], hoverinfo="text"))
    for lab, col in (("positive ρ", D.BLUE), ("negative ρ", "#d03b3b")):
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color=col, width=4), name=lab))
    fig.update_xaxes(visible=False, range=[-1.9, 1.9]); fig.update_yaxes(visible=False, scaleanchor="x", range=[-1.2, 1.2])
    D.layout(fig, f"Fig. 1 · How the 22 structural descriptors move together · {len(F_)} formulations · line = Spearman |ρ| ≥ 0.3 (width = strength) · "
                  "node size = formulations having the structure · colour = descriptor axis", 820, legend=dict(orientation="h", y=-0.03))
    write(fig, "图1_描述符相关网络.html")


# ---------------- 同测试换配方：新配方的描述符与相对对照的性能 ----------------
def same_test_points():
    P = json.loads((F.IN / "比较表.json").read_text(encoding="utf-8"))
    ST = {s["表述编号"]: s for s in json.loads(D.C.STF.read_text(encoding="utf-8"))}
    pts = []
    for q in P:
        if q["配对类型"] != "同测试、不同配方":
            continue
        t = (q.get("参照条件") or {}).get("温度")
        if t is not None and not (F.T_LO <= t <= F.T_HI):
            continue
        s = ST[q["实验"]]
        h, _ = H.descriptors(s["论文"], s["recipe"])
        h["lino3"] = (q.get("参照描述符") or {}).get("LiNO3_M")
        if h["lino3"] is not None and q["Δ描述符"].get("LiNO3_M") is not None:
            h["lino3"] = h["lino3"] + q["Δ描述符"]["LiNO3_M"]
        pts.append({"类别": q["类别"], "论文": q["论文"], "实验": q["实验配方"], "参照": q["参照配方"], "dy": q["dy"], "D": h, "条件": q.get("参照条件") or {}})
    return pts


YOPT = ["salt", "ffrac", "eo", "rotb", "carbonate", "lino3"]


# 11-08 用户：配方空间颜色大小不好看 → 改为一张图：每个点 = 一个有性能数据的配方，横轴 = 每个 Li⁺ 的配位位点（溶剂化强弱），
# 纵轴 = 主盐浓度（对数），颜色 = 溶剂类别（按描述符判定，规则见 solvent_class），点一样大；类别名标在该类点群的中位位置
SOLV = [("Ether", "#2a78d6"), ("Fluorinated (localized high-conc. / fluorinated solvent)", "#eb6834"), ("Carbonate", "#1baf7a"),
        ("Sulfone / sulfoxide", "#eda100"), ("Amide / nitrile (high donor)", "#e87ba4"), ("Organosulfur solvent", "#6250d6"), ("Other", "#9fb3c8")]


def solvent_class(d):
    g = lambda k: d.get(k) or 0
    if g("ffrac") >= 0.2:
        return SOLV[1][0]
    if g("carbonate") >= 0.3:
        return "Carbonate"
    if g("sulfone") >= 0.3:
        return "Sulfone / sulfoxide"
    if g("amide") >= 0.3 or g("nitrile") >= 0.3:
        return "Amide / nitrile (high donor)"
    if g("thio") >= 0.3:
        return "Organosulfur solvent"
    if g("eo") >= 0.5:
        return "Ether"
    return "Other"


def fig_space(M):
    import plotly.graph_objects as go
    F_ = {}
    for r in M:
        F_.setdefault((r["论文"], r["recipe"]), r["D"])
    pts = [(k, d) for k, d in F_.items() if d.get("lnsites") is not None and (d.get("salt") or 0) > 0]
    fig = go.Figure()
    out, big = {}, None
    for g, col in SOLV:
        ii = [(k, d) for k, d in pts if solvent_class(d) == g]
        if not ii:
            continue
        out[g] = len(ii)
        cell = {}  # 位置相同（四舍五入后）的配方合成一个点，大小 = 配方数
        for k, d in ii:
            cell.setdefault((round(d["lnsites"], 2), round(math.log10(d["salt"]), 2)), []).append((k, d))
        xs = [v[0][1]["lnsites"] for v in cell.values()]
        ys = [v[0][1]["salt"] for v in cell.values()]
        ns = [len(v) for v in cell.values()]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", name=f"{g} ({len(ii)})",
                                 marker=dict(size=[7 + 3.2 * math.sqrt(n - 1) for n in ns], color=col, opacity=0.75, line=dict(width=0.8, color="white")),
                                 hovertext=[f"<b>{n} formulation{'s' if n > 1 else ''}</b> · {g}<br>sites per Li⁺ (ln) {v[0][1]['lnsites']:.2f} · salt {v[0][1]['salt']:.2f} M<br>"
                                            + ", ".join(f"{k[0]}" for k, _ in v[:8]) + (" …" if n > 8 else "") for v, n in zip(cell.values(), ns)],
                                 hoverinfo="text"))
        m = max(zip(ns, xs, ys))
        if big is None or m[0] > big[0]:
            big = m + (g,)
    if big:
        fig.add_annotation(x=big[1], y=math.log10(big[2]), text=f"<b>{big[0]} formulations</b> at one spot<br>(typical 1 M ether electrolyte)",
                           showarrow=True, arrowhead=0, ax=90, ay=-70, font=dict(size=11, color=D.INK), bgcolor="rgba(255,255,255,0.85)")
    fig.update_xaxes(title_text="Coordinating sites per Li⁺ (ln) — weaker solvation ←  → stronger solvation", showgrid=True, gridcolor="#eeeeea")
    fig.update_yaxes(title_text="Main lithium-salt concentration (M, log scale)", type="log", showgrid=True, gridcolor="#eeeeea")
    D.layout(fig, f"Fig. 2 · Formulation space · {len(pts)} formulations with performance data (313 papers) · colour = solvent class (from descriptors)",
             640, legend=dict(orientation="v", x=1.01, y=1, font=dict(size=11), title=dict(text="Solvent class (formulations)")),
             margin=dict(l=60, r=20, t=70, b=60), plot_bgcolor="white")
    write(fig, "图2_配方空间.html")
    return {"配方": len(pts), "按溶剂类别": out}


def fig_parcoords(pts):
    import plotly.graph_objects as go
    CL = F.CLASSES
    dims_d = ["lnsites", "ffrac", "salt", "rotb", "lino3"]
    cond = {"首圈容量": [("ln_ES", "E/S (ln)"), ("载量", "S loading")], "每圈衰减率": [("ln_ES", "E/S (ln)"), ("载量", "S loading")],
            "全电池CE": [("ln_ES", "E/S (ln)"), ("载量", "S loading")], "LiCu_CE": [("ln_电流", "Current (ln)"), ("ln_沉积容量", "Capacity (ln)")]}
    fig = go.Figure()
    counts = {}
    for i, c in enumerate(CL):
        ps = [p for p in pts if p["类别"] == c and all(p["D"].get(k) is not None for k in dims_d)
              and all(p["条件"].get(k) is not None for k, _ in cond[c])]
        counts[c] = len(ps)
        dims = [dict(label=LAB[k].replace(" (ln)", ""), values=[p["D"][k] for p in ps]) for k in dims_d]
        dims += [dict(label=lab, values=[p["条件"][k] for p in ps]) for k, lab in cond[c]]
        dims += [dict(label="ln × vs own control", values=[max(-2, min(2, p["dy"])) for p in ps], range=[-2, 2])]
        fig.add_trace(go.Parcoords(line=dict(color=[max(-1.5, min(1.5, p["dy"])) for p in ps], colorscale=D.DIVERGE, cmin=-1.5, cmax=1.5, showscale=True,
                                             colorbar=dict(title="ln ×", tickvals=[-1.5, 0, 1.5], ticktext=["worse", "0", "better"])),
                                   dimensions=dims, visible=(i == 0), labelfont=dict(size=11), tickfont=dict(size=9)))
    buttons = [dict(label=f"{EN[c]} ({counts[c]})", method="update", args=[{"visible": [j == i for j in range(len(CL))]}]) for i, c in enumerate(CL)]
    fig.update_layout(updatemenus=[dict(buttons=buttons, direction="right", type="buttons", x=0, xanchor="left", y=1.06, yanchor="bottom")])
    D.layout(fig, "Fig. 3 · Parallel coordinates · each line = a new formulation vs its own control in the same test · descriptors → test conditions → result · "
                  "drag on any axis to filter", 660, margin=dict(l=60, r=40, t=150, b=40))
    write(fig, "图3_平行坐标.html")
    return counts


# ---------------- 图 6a 分子宇宙 ----------------
AL13, BE13 = "α氟化醚氧数（相邻CF₂/CF₃）", "β氟化醚氧数（隔一个碳为CF₂/CF₃，不含α）"
ROLE = {"溶剂": "Solvent", "溶剂/添加剂": "Solvent / additive", "锂盐": "Lithium salt", "锂盐/添加剂": "Lithium salt", "添加剂": "Additive",
        "添加剂（介体）": "Redox mediator", "氧化还原介体（原文称均相催化剂）": "Redox mediator", "其他盐/添加剂": "Other salt / additive",
        "硫物种": "Sulfur species", "离子": "Ion", "盐": "Other salt / additive"}


# 无定论问题 1 涉及的分子（step20 T1 的论文与反例 P381、P371、P263、P350 里用到的稀释剂/溶剂）：True = 含氟，False = 不含氟的对照
Q1_MOLS = {"TTE": True, "BTFE": True, "OFE": True, "TFEE": True, "TFTFE": True, "F3DEE": True, "F4DEE": True, "F5DEE": True,
           "DTFEG": True, "F4DMB": True, "FB": True, "F4EO2": True, "DBE": False, "DEE": False}


# 11-08：分子宇宙按化学大类上色（由组分表“化学类别”归并；顺序与颜色固定，取自作图规范的 8 色）
CHEM_GROUPS = [("Ether", "#2a78d6"), ("Fluorinated ether / solvent", "#eb6834"), ("Carbonate / ester", "#1baf7a"),
               ("Organosulfur / Se", "#eda100"), ("N-containing (amide, amine, N-ring, nitrile)", "#e87ba4"),
               ("Salt / ion", "#6250d6"), ("Polysulfide / sulfur", "#008300"), ("Other", "#9fb3c8")]


def chem_group(c):
    c = c or ""
    if c.endswith("盐") or c in ("阴离子", "阳离子", "卤化物", "金属卤化物", "多卤化物", "离子液体", "碘化物"):
        return "Salt / ion"
    if c.startswith("氟") or c in ("氟代芳烃", "氟代吡啶", "卤代烃"):
        return "Fluorinated ether / solvent"
    if any(k in c for k in ("醚", "缩醛")):
        return "Ether"
    if any(k in c for k in ("碳酸酯", "羧酸酯", "磷酸酯", "磺酸酯")) or c == "酯":
        return "Carbonate / ester"
    if c.startswith("有机硫") or c.startswith("有机硒") or c.startswith("有机碲") or c == "二硫化碳":
        return "Organosulfur / Se"
    if c.startswith("多硫化") or c == "硫":
        return "Polysulfide / sulfur"
    if c.endswith("盐") or c in ("阴离子", "阳离子", "卤化物", "金属卤化物", "多卤化物", "离子液体", "碘化物"):
        return "Salt / ion"
    if any(k in c for k in ("酰胺", "胺", "含氮杂环", "咪唑", "吡啶", "异噁唑", "吡咯", "腈", "酰亚胺", "磷腈")):
        return "N-containing (amide, amine, N-ring, nitrile)"
    return "Other"


def fig_universe():
    import plotly.graph_objects as go
    import umap
    from sklearn.cluster import HDBSCAN
    from sklearn.metrics import silhouette_score
    fp = json.loads((OUTD / "指纹.json").read_text(encoding="utf-8"))["分子"]
    comp = {c["id"]: c for c in json.loads((C313 / "组分表.json").read_text(encoding="utf-8"))}
    ids = [m["id"] for m in fp]
    X = np.zeros((len(fp), 2048), bool)
    for i, m in enumerate(fp):
        X[i, m["bits"]] = True
    inter = X.astype(np.int32) @ X.T.astype(np.int32)
    cnt = X.sum(1)
    union = cnt[:, None] + cnt[None, :] - inter
    Dj = 1 - np.where(union > 0, inter / np.maximum(union, 1), 1.0)
    np.fill_diagonal(Dj, 0)
    Dfp = Dj.copy()
    # 11-06：小分子（LiI、S8、甲苯）指纹位数少，只看指纹不可靠 → 再加官能团组成距离（用户的描述符表），两者各占一半
    FG = ["O原子数", "N原子数", "S原子数", "F原子数", "Cl/Br/I原子数", "C原子数", "环数", "芳环数", "可旋转键数", "TPSA", "醚氧数", AL13, BE13, "羰基数",
          "碳酸酯基数", "酰胺/脲基数", "砜/亚砜基数", "磺酰基数（磺酰亚胺/磺酸根等，不含砜）", "P=O数", "腈基数", "胺/铵氮数（不含酰胺）", "硫醚/多硫链S原子数", "分子量"]
    V = np.array([[float(H.DWHOLE.get(i, {}).get(k) or 0) for k in FG] for i in ids])
    V = np.log1p(np.abs(V)); V = (V - V.mean(0)) / np.where(V.std(0) > 0, V.std(0), 1)
    De = np.sqrt(((V[:, None, :] - V[None, :, :]) ** 2).sum(-1)); De = np.minimum(De / np.percentile(De, 95), 1.0)
    Dj = 0.5 * Dfp + 0.5 * De
    np.fill_diagonal(Dj, 0)
    from sklearn.manifold import TSNE  # 11-06：UMAP 把氟化醚一族甩得很远、其余挤成一团，改用 t-SNE（布局更均匀；位置只表示相似，不表示距离的绝对大小）
    emb = TSNE(metric="precomputed", init="random", perplexity=20, random_state=42).fit_transform(Dj.copy())
    lab = HDBSCAN(min_cluster_size=5, min_samples=3, metric="precomputed").fit_predict(Dj.copy())  # 会原地改距离矩阵，传副本
    fams = sorted(set(lab) - {-1})
    sil_core = float(silhouette_score(Dj[lab >= 0][:, lab >= 0], lab[lab >= 0], metric="precomputed")) if len(fams) > 1 else None
    # 11-06 用户要求“未归类的解决一下”：HDBSCAN 没归入的分子并入与它最相似（Tanimoto 最高）的已归类分子所在的家族，记下相似度
    core = np.where(lab >= 0)[0]
    sim = np.ones(len(ids)); joined = np.zeros(len(ids), bool)
    for i in np.where(lab < 0)[0]:
        j = core[np.argmin(Dj[i, core])]
        lab[i] = lab[j]; sim[i] = 1 - Dj[i, j]; joined[i] = True
    sil = float(silhouette_score(Dj, lab, metric="precomputed")) if len(fams) > 1 else None
    def fam_name(k):
        ii = sorted([i for i in range(len(ids)) if lab[i] == k], key=lambda i: -(comp[ids[i]].get("论文数") or 0))
        return f"F{k + 1} · " + ", ".join(ids[i] for i in ii[:3]) + (" …" if len(ii) > 3 else "")
    names = {k: fam_name(k) for k in fams}
    npap = np.array([comp[i].get("论文数") or 1 for i in ids], float)
    # 11-08 用户：颜色大小不好看、分类依据看不出 → 颜色改为化学大类（由组分表“化学类别”归并，依据写在图例），大小差别缩小，标出常用分子名；
    # HDBSCAN 家族仍计算（只进汇总与悬停），不再作颜色
    size = 7 + 1.4 * np.sqrt(npap)
    cls = [chem_group(comp[i].get("化学类别")) for i in ids]
    hov = [f"<b>{comp[i].get('英文名') or comp[i].get('名称')}</b> ({i})<br>{comp[i].get('规范SMILES') or comp[i].get('smiles')}<br>"
           f"class: {cls[k]} ({comp[i].get('化学类别')}) · role: {ROLE.get(comp[i].get('类别'), comp[i].get('类别'))}<br>used in {int(npap[k])} papers"
           for k, i in enumerate(ids)]
    fig = go.Figure()
    groups = []
    for g, col in CHEM_GROUPS:
        ii = [k for k in range(len(ids)) if cls[k] == g]
        if not ii:
            continue
        fig.add_trace(go.Scatter(x=emb[ii, 0], y=emb[ii, 1], mode="markers", name=f"{g} ({len(ii)})",
                                 marker=dict(size=size[ii], color=col, line=dict(width=0.8, color="white"), opacity=0.9),
                                 hovertext=[hov[i] for i in ii], hoverinfo="text"))
        groups.append("cls")
    fig.add_trace(go.Scatter(x=emb[:, 0], y=emb[:, 1], mode="markers", name="papers using it", visible=False, showlegend=False,
                             marker=dict(size=size, color=np.log10(npap), colorscale=[[0, "#dde9f7"], [1, "#0d3f80"]], showscale=True,
                                         colorbar=dict(title="papers", tickvals=[0, 1, 2], ticktext=["1", "10", "100"]), line=dict(width=0.6, color="white")),
                             hovertext=hov, hoverinfo="text"))
    groups.append("use")
    # 11-08 用户同意：标出无定论问题 1（稀释剂该不该分解）涉及的分子——氟化醚/氟代溶剂 vs 不含氟的对照（DBE、DEE）
    q1 = [i for i in range(len(ids)) if ids[i] in Q1_MOLS]
    fig.add_trace(go.Scatter(x=emb[:, 0], y=emb[:, 1], mode="markers", name="other molecules", visible=False,
                             marker=dict(size=size, color="#e4e3de", line=dict(width=0.5, color="white")), hovertext=hov, hoverinfo="text"))
    groups.append("q1")
    for fl, col, nm in ((True, "#eb6834", "Open question 1 · fluorinated diluent / solvent"), (False, "#2a78d6", "Open question 1 · non-fluorinated counterpart")):
        ii = [i for i in q1 if Q1_MOLS[ids[i]] == fl]
        fig.add_trace(go.Scatter(x=emb[ii, 0], y=emb[ii, 1], mode="markers+text", name=nm, visible=False, text=[ids[i] for i in ii],
                                 textposition="top center", textfont=dict(size=10, color=D.INK),
                                 marker=dict(size=size[ii] + 6, color=col, symbol="star", line=dict(width=1, color=D.INK)),
                                 hovertext=[hov[i] for i in ii], hoverinfo="text"))
        groups.append("q1")
    for k in np.argsort(-npap)[:14]:  # 用得最多的 14 个分子直接标名
        fig.add_annotation(x=float(emb[k, 0]), y=float(emb[k, 1]), text=ids[k], showarrow=False, yshift=12, font=dict(size=10.5, color=D.INK))
    vis = lambda g: [x == g for x in groups]
    fig.update_layout(updatemenus=[dict(type="buttons", direction="right", x=0, xanchor="left", y=1.035, yanchor="bottom", buttons=[
        dict(label="Chemical class", method="update", args=[{"visible": vis("cls")}]),
        dict(label="How often it is used", method="update", args=[{"visible": vis("use")}]),
        dict(label="Open question 1 molecules", method="update", args=[{"visible": vis("q1")}])])])
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    D.layout(fig, f"Fig. 6a · Molecular universe · {len(ids)} molecules · position = structural similarity · colour = chemical class · size = papers", 760,
             legend=dict(orientation="v", x=1.01, y=1, font=dict(size=11), title=dict(text="Chemical class (molecules)")),
             margin=dict(l=20, r=20, t=120, b=20), plot_bgcolor="white")
    write(fig, "图6a_分子宇宙.html")
    fam_rows = [{"家族": names[k], "分子数": int((lab == k).sum()),
                 "例子": [comp[ids[i]].get("英文名") or comp[ids[i]].get("名称") for i in np.argsort(-npap) if lab[i] == k][:6]} for k in fams]
    return {"分子": len(ids), "家族": len(fams), "HDBSCAN 核心成员": int((~joined).sum()), "按最近邻并入": int(joined.sum()),
            "其中弱归属（相似度 < 0.5）": int((joined & (sim < 0.5)).sum()), "并入分子的相似度中位数": float(np.median(sim[joined])) if joined.any() else None,
            "轮廓系数_核心成员": sil_core, "轮廓系数_全部": sil, "家族表": fam_rows}


# ---------------- 图 6b 配方基因组 ----------------
GENE = ["eo", "eo_a", "eo_b", "fat", "ffrac", "dil", "carbonate", "carbonyl", "sulfone", "nitrile", "amide", "thio", "ring", "rotb", "mw", "tpsa",
        "salt", "anF", "anSO2", "lino3", "lnsites"]
CLUST = ["eo", "eo_a", "eo_b", "fat", "carbonate", "carbonyl", "sulfone", "nitrile", "amide", "thio", "ring", "rotb", "tpsa", "mw", "ffrac"]


def fig_genome(M):
    import plotly.graph_objects as go
    from scipy.cluster.hierarchy import linkage, leaves_list, fcluster
    Fm = {}
    for r in M:
        if all(r["D"].get(k) is not None for k in CLUST):
            Fm[(r["论文"], r["recipe"])] = r["D"]
    keys = list(Fm)
    Xc = np.array([[Fm[k][c] for c in CLUST] for k in keys], float)
    Z = (stats.rankdata(Xc, axis=0) - 0.5) / len(Xc)
    Z = stats.norm.ppf(Z)
    L = linkage(Z, "ward")
    order = leaves_list(L)
    keys = [keys[i] for i in order]
    pct = {}
    for c in GENE:
        v = np.array([Fm[k].get(c) if Fm[k].get(c) is not None else np.nan for k in keys], float)
        ok = ~np.isnan(v)
        p = np.full(len(v), np.nan)
        if ok.sum() and np.nanstd(v) > 0:
            p[ok] = (stats.rankdata(v[ok]) - 0.5) / ok.sum()
            p[ok & (v == 0)] = 0.0
        pct[c] = p
    zz = np.array([pct[c] for c in GENE]).T
    hov = [[f"{k[0]} · {k[1]}<br>{LAB[c]} = {Fm[k].get(c):.3g}" if Fm[k].get(c) is not None else f"{k[0]} · {k[1]}<br>{LAB[c]}: not computable"
            for c in GENE] for k in keys]
    fig = go.Figure(go.Heatmap(z=zz, x=[LAB[c] for c in GENE], y=[f"{k[0]}·{k[1]}" for k in keys], hovertext=hov, hoverinfo="text",
                               colorscale=[[0, "#f4f2ee"], [0.5, "#9fc1ea"], [1, "#0d3f80"]], zmin=0, zmax=1,
                               colorbar=dict(title="percentile in column", tickvals=[0, 0.5, 1], ticktext=["0 / absent", "median", "highest"])))
    fig.update_yaxes(showticklabels=False, title_text=f"{len(keys)} formulations (ordered by functional-group composition, Ward)")
    fig.update_xaxes(tickangle=-45, automargin=True)
    D.layout(fig, "Fig. 6b · Formulation genome · rows = formulations, columns = functional groups and salt descriptors (value as percentile within the column; grey = 0 or absent)",
             1150, margin=dict(l=40, r=20, t=70, b=190))
    write(fig, "图6b_配方基因组.html")
    top = {}
    for kk in (3, 6, 10):
        lab = fcluster(L, kk, "maxclust")
        top[kk] = sorted(Counter(lab).values(), reverse=True)
    return {"配方": len(keys), "Ward 切成 k 簇时的簇大小": top}


def main():
    OUTD.mkdir(parents=True, exist_ok=True)
    M, _ = F.load()
    fig_corr(M)
    pts = same_test_points()
    summary["配方空间"] = fig_space(M)
    summary["平行坐标线数"] = fig_parcoords(pts)
    summary["分子宇宙"] = fig_universe()
    summary["配方基因组"] = fig_genome(M)
    (OUTD / "汇总.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1)[:3000])


if __name__ == "__main__":
    main()
