"""step13h：结构描述符版关联图（11-05 用户定，取代 step13d 的图 1–3）。

用户要求：共现网络、弦图、聚类里与配方有关的部分不用组分名/化学类别，改用分子结构描述符；聚类与热图分开画。
用户定：用 313 篇；热图画“描述符 × 物性/条件/性能”的相关；性能档按“相对本篇对照”（不用归一化值，归一化模型 R²≈0）。

数据：output/表述试跑313篇_2026-11-05/表述.json（分析集 in_analysis；主层 = Li‖S 硫碳正极 ＋ Li‖Cu 单列，11-05 用户定“不是硫碳就不要”；
     首圈 CE 不进 CE 类，同 step14；疑似重复组每组只计一次），output/组分结构表_试跑313篇_2026-11-05/（配方组成、描述符、组分表）。
配方结构描述符（每个配方一组，口径同 step13g xdata.struct / feats3.state）：
  溶剂结构（RDKit，按溶剂摩尔分数加权；没有摩尔分数用体积分数近似，都没有则等权，逐配方记权重来源）：不含氟醚氧、α/β 氟化醚氧、碳酸酯、
  羰基、砜/亚砜、腈、酰胺/脲、硫醚/多硫 S、F 原子、环、可旋转键、TPSA、分子量、含氟分子比例；
  元素比例（Kim PNAS 2023，配方组成.json）：sO 三档、aC、F/O、InOr；
  溶剂化状态：ln（每个 Li⁺ 的可配位位点数）、稀释剂摩尔比例、Li⁺ 总浓度；
  盐与添加剂：主盐 M、阴离子 F/每升、阴离子磺酰/每升、LiNO₃ M。
共现与弦图的节点：一半以上配方为 0 的描述符记“有”（>0），其余按配方三等分记“低/高”（中档不画，减少杂乱）；
  用严格不等号，很多配方取同一值（标准醚电解液）使两个切点重合时，低/高 = 比这个常见值低/高。
性能档（相对本篇对照）：同篇、同测试、同指标、同阶段、同圈数里和对照比，效应 > ln1.05 记“好于对照”，< −ln1.05 记“差于对照”，其余“相近”。
  效应：容量等取对数比（越小越好的指标取反），CE 用损失比 −ln[(100−CE)/(100−CE对照)]（同 step13e.effect）。
热图：行 = 描述符；列分三块——物性（配方实测值，跨配方）、条件（配方所测条件中位数，跨配方，显示“什么设计在什么条件下测”）、
  相对对照的性能（篇内配对：Δ描述符 = 配方 − 对照，对效应，每个“论文×配方×对照×类别”取中位数）；格子 = Spearman ρ，n < 15 不显示。
聚类：只用分子结构描述符（溶剂结构 15 个 ＋ 元素比例 6 个，缺任一则该配方不进聚类）；按秩转正态分数再标准化（少数极端配方不主导）
  → Ward 层次聚类；簇数在 3–8 中取轮廓系数最高、且每簇 ≥ 10 个配方的；二维展示用 PCA；
  下方表格给每簇的特征描述符、平均用量（盐、LiNO₃、稀释剂、Li⁺，不参与聚类）与相对对照的性能分布。
输出：网站图写到 30 篇网站的 图/ 文件夹（结果网站只有这一个）；数据与汇总写到 output/表述试跑313篇_2026-11-05/结构描述符图/。
用法（papertrail 环境）：python -X utf8 step13h_descriptor_figures.py
"""
from __future__ import annotations

import itertools
import json
import math
import re
from collections import Counter, defaultdict

import numpy as np

import step13d_figures as F13
from step13_common import ROOT, in_analysis
from step13_i18n import BIN, PROP, t as tr

S313 = ROOT / "output" / "表述试跑313篇_2026-11-05"
C313 = ROOT / "output" / "组分结构表_试跑313篇_2026-11-05"
OUTD = S313 / "结构描述符图"
OUTD.mkdir(exist_ok=True)
FIG = F13.FIG
LABEL_EN = "Preliminary · 313 papers · main layer (Li‖S sulfur–carbon, Li‖Cu) · AI-assisted"
TITLE_NOTE = f"<span style='font-size:12px;color:#62777a'>{LABEL_EN} · association, not causation</span>"
PROP_SKIP = {"其他（未归类）"}  # 没有具体含义的物性类别，不画
FONT = F13.FONT
SMALL = math.log(1.05)
rj = lambda p: json.loads(p.read_text(encoding="utf-8"))

# ---------------- 描述符定义 ----------------
FAMS = {"Solvent structure": "#007e70", "Elemental ratio": "#2f6db5", "Solvation state": "#7159a7", "Salt & additive": "#c2504a"}
DESCS = [  # 键, 英文名, 族
    ("eo", "Ether O (non-F)", "Solvent structure"), ("eo_a", "α-F ether O", "Solvent structure"), ("eo_b", "β-F ether O", "Solvent structure"),
    ("carbonate", "Carbonate", "Solvent structure"), ("carbonyl", "Carbonyl", "Solvent structure"), ("sulfone", "Sulfone/sulfoxide", "Solvent structure"),
    ("nitrile", "Nitrile", "Solvent structure"), ("amide", "Amide/urea", "Solvent structure"), ("thio", "Thioether/polysulfide S", "Solvent structure"),
    ("fat", "F atoms per solvent", "Solvent structure"), ("ring", "Rings per solvent", "Solvent structure"), ("rotb", "Rotatable bonds", "Solvent structure"),
    ("tpsa", "TPSA", "Solvent structure"), ("mw", "Solvent MW", "Solvent structure"), ("ffrac", "Fluorinated-solvent fraction", "Solvent structure"),
    ("sO_n", "sO non-F", "Elemental ratio"), ("sO_b", "sO β-F ether", "Elemental ratio"), ("sO_a", "sO α-F ether", "Elemental ratio"),
    ("aC", "aC", "Elemental ratio"), ("FO", "F/O", "Elemental ratio"), ("InOr", "InOr", "Elemental ratio"),
    ("lnsites", "Coordinating sites per Li⁺ (ln)", "Solvation state"), ("dil", "Diluent mole fraction", "Solvation state"), ("li", "Total Li⁺ (M)", "Solvation state"),
    ("salt", "Main salt (M)", "Salt & additive"), ("anF", "Anion F per litre", "Salt & additive"), ("anSO2", "Anion sulfonyl per litre", "Salt & additive"),
    ("lino3", "LiNO₃ (M)", "Salt & additive")]
DLAB = {k: l for k, l, _ in DESCS}
DFAM = {k: f for k, _, f in DESCS}
AL, BE = "α氟化醚氧数（相邻CF₂/CF₃）", "β氟化醚氧数（隔一个碳为CF₂/CF₃，不含α）"
RD = {"carbonate": "碳酸酯基数", "carbonyl": "羰基数", "sulfone": "砜/亚砜基数", "nitrile": "腈基数", "amide": "酰胺/脲基数", "thio": "硫醚/多硫链S原子数",
      "fat": "F原子数", "ring": "环数", "rotb": "可旋转键数", "tpsa": "TPSA", "mw": "分子量"}
ER = {"sO_n": "sO_不含氟", "sO_b": "sO_β氟化醚", "sO_a": "sO_α氟化醚", "aC": "aC", "FO": "F/O", "InOr": "InOr"}

DESC = rj(C313 / "描述符.json")
DWHOLE = {d["组分"]: d for d in DESC if d["对象"] == "整体"}
DANION = {d["组分"]: d for d in DESC if d["对象"] == "阴离子"}
CTAB = {c["id"]: c for c in rj(C313 / "组分表.json")}
COMPREC = {(r["论文"], r["配方"]): r for r in rj(C313 / "配方组成.json")}


def sites(cid):
    """可配位位点（同 feats3.sites）：不含氟醚氧 ＋ 羰基 ＋ 砜/亚砜 ＋ P=O ＋ 腈。"""
    d = DWHOLE[cid]
    eo = max((d.get("醚氧数") or 0) - (d.get(AL) or 0) - (d.get(BE) or 0), 0)
    return eo + (d.get("羰基数") or 0) + (d.get("砜/亚砜基数") or 0) + (d.get("P=O数") or 0) + (d.get("腈基数") or 0)


def descriptors(pid, rid):
    """一个配方的结构描述符（缺的记 None，不填 0）与溶剂权重来源。"""
    r = COMPREC.get((pid, rid))
    out = dict.fromkeys(DLAB)
    if not r:
        return out, "无配方组成"
    comps = [i["组分"] for i in r["组分"]]
    solv = [c for c in comps if CTAB.get(c, {}).get("类别") in ("溶剂", "溶剂/添加剂") and c in DWHOLE]
    xf, vf = r.get("摩尔分数") or {}, r.get("体积分数") or {}
    how = "无溶剂结构"
    if solv:
        if all(c in xf for c in solv):
            w, how = np.array([xf[c] for c in solv], float), "摩尔分数"
        elif all(c in vf for c in solv):
            w, how = np.array([vf[c] for c in solv], float), "体积分数近似"
        else:
            w, how = np.ones(len(solv)), "等权（用量缺）"
        w = w / w.sum()
        g = lambda c, col: DWHOLE[c].get(col) or 0
        out["eo"] = float(sum(wi * max(g(c, "醚氧数") - g(c, AL) - g(c, BE), 0) for wi, c in zip(w, solv)))
        out["eo_a"] = float(sum(wi * g(c, AL) for wi, c in zip(w, solv)))
        out["eo_b"] = float(sum(wi * g(c, BE) for wi, c in zip(w, solv)))
        for k, col in RD.items():
            out[k] = float(sum(wi * g(c, col) for wi, c in zip(w, solv)))
        out["ffrac"] = float(sum(wi for wi, c in zip(w, solv) if g(c, "F原子数") > 0))
    e = (r.get("元素比例") or {})
    if e.get("状态") == "可算":
        for k, col in ER.items():
            out[k] = e["比例"].get(col)
    # 溶剂化状态（同 feats3.state）：需要全部溶剂的每升物质的量
    n = r.get("每升溶剂物质的量_mol") or {}
    if solv and all(c in n for c in solv):
        li = sum(m for c, m in n.items() if "锂盐" in CTAB.get(c, {}).get("类别", "") or c == "LiNO3")
        tot = sum(n[c] for c in solv)
        coord = sum(n[c] * sites(c) for c in solv)
        if li > 0 and coord > 0:
            out["lnsites"] = math.log(coord / li)
        out["dil"] = sum(n[c] for c in solv if sites(c) == 0) / tot if tot else None
        out["li"] = li or None
    salt_M, aF, aSO2 = 0.0, 0.0, 0.0
    for i in r["组分"]:
        c = i["组分"]
        if CTAB.get(c, {}).get("类别") == "锂盐" and i["单位类别"] == "摩尔浓度" and i["数值"]:
            salt_M += i["数值"]
            an = DANION.get(c, {})
            aF += i["数值"] * (an.get("F原子数") or 0)
            aSO2 += i["数值"] * (an.get("磺酰基数（磺酰亚胺/磺酸根等，不含砜）") or 0)
    if salt_M:
        out["salt"], out["anF"], out["anSO2"] = salt_M, aF, aSO2
    lino3 = next((i for i in r["组分"] if i["组分"] == "LiNO3"), None)
    out["lino3"] = 0.0 if lino3 is None else (lino3["数值"] if lino3["单位类别"] == "摩尔浓度" else None)
    return out, how


# ---------------- 物性解析（同 feats3：电导率换算到 mS/cm，黏度 cP，超出合理范围的不用） ----------------
def _num(t):
    m = re.match(r"(\d+(?:\.\d+)?)(?:\s*[×x]\s*10\s*-\s*(\d+))?", t)
    return float(m.group(1)) * (10 ** -int(m.group(2)) if m.group(2) else 1) if m else None


def first_value(t):
    t = t.replace("−", "-").replace("–", "-").replace("℃", "°C")
    m = re.search(r"(?:25\s*°\s*C|室温|RT|room temperature)[^0-9]{0,10}(\d+(?:\.\d+)?(?:\s*[×x]\s*10\s*-\s*\d+)?)", t, re.I)
    if m:
        return _num(m.group(1)), t
    for m in re.finditer(r"(\d+(?:\.\d+)?(?:\s*[×x]\s*10\s*-\s*\d+)?)", t):
        if not re.match(r"\s*°", t[m.end():]):
            return _num(m.group(1)), t
    return None, t


def parse_cond(t):
    v, t = first_value(t)
    if v is None:
        return None
    if re.search(r"[µμ]S", t):
        v /= 1000
    elif re.search(r"(?<![mµμ])S\s*/?\s*cm", t) and not re.search(r"mS", t):
        v *= 1000
    return v if 0.001 <= v <= 100 else None


def parse_visc(t):
    if not re.search(r"cP|mPa|centipoise", t, re.I) and "°" not in t:
        return None
    v, _ = first_value(t)
    return v if v is not None and 0.1 <= v <= 5000 else None


def parse_tli(t):
    v, _ = first_value(t)
    return v if v is not None and 0 < v < 1 else None


PROPS = [("ln conductivity", "离子电导率", parse_cond, True), ("ln viscosity", "黏度", parse_visc, True), ("Li⁺ transference no.", "Li⁺迁移数", parse_tli, False)]


def effect(std, a, b, higher_better):
    """A 相对 B 的效应，> 0 表示 A 更好（同 step13e.effect）。"""
    if a is None or b is None:
        return None
    if "CE" in std and "圈数" not in std:
        if a >= 100 or b >= 100:
            return None
        return -math.log((100 - a) / (100 - b))
    if a <= 0 or b <= 0:
        return None
    e = math.log(a / b)
    return e if higher_better is not False else -e


def pclass(s):
    if s["性能类别"] == "库仑效率类":
        return "CE · Li‖Cu" if s["电池类型"] == "Li‖Cu" else "CE · full cell"
    return {"放电容量类": "Discharge capacity", "衰减类": "Capacity fade"}.get(s["性能类别"], s["性能类别"])


def chord(groups, weights, title, fname, min_w=1, freq=None, unit="statements"):
    """弦图（改自 step13d.chord：画布加大，标签不压标题；数据说明用 313 篇）。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch, Wedge
    from matplotlib.path import Path as MPath
    plt.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    names = [(g, n, col) for g, ns, col in groups for n in ns]
    tot = Counter()
    for (a, b), w in weights.items():
        if w >= min_w:
            tot[a] += w
            tot[b] += w
    names = [x for x in names if tot[x[1]] > 0]
    gap, total = 2.0, sum(tot[n] for _, n, _ in names)
    span = 360 - gap * len(names) - 6 * len(groups)
    ang, start, cur_g = {}, 90.0, None
    for g, n, col in names:
        if g != cur_g:
            start -= 6
            cur_g = g
        width = span * tot[n] / total
        ang[n] = [start - width, start, start - width]
        start -= width + gap
    fig, ax = plt.subplots(figsize=(13, 13.6))
    ax.set_xlim(-2.05, 2.05)
    ax.set_ylim(-2.05, 2.05)
    ax.axis("off")
    color = {n: col for _, n, col in names}
    gidx = {n: i for i, (g, ns, _) in enumerate(groups) for n in ns}
    for g, n, col in names:
        a0, a1, _ = ang[n]
        ax.add_patch(Wedge((0, 0), 1.0, a0, a1, width=0.06, color=col))
        mid, rot = math.radians((a0 + a1) / 2), (a0 + a1) / 2
        ha = "left" if math.cos(mid) >= 0 else "right"
        if math.cos(mid) < 0:
            rot += 180
        ax.text(1.05 * math.cos(mid), 1.05 * math.sin(mid), f"{n.replace('⁺', '+')} ({(freq or tot)[n]})", rotation=rot, rotation_mode="anchor",
                ha=ha, va="center", fontsize=9)
    for (a, b), w in sorted(weights.items(), key=lambda x: -x[1]):
        if w < min_w or a not in ang or b not in ang:
            continue
        sa = span * w / total
        pa, pb = (ang[a][2], ang[a][2] + sa), (ang[b][2], ang[b][2] + sa)
        ang[a][2] += sa
        ang[b][2] += sa
        P = lambda t: (0.94 * math.cos(math.radians(t)), 0.94 * math.sin(math.radians(t)))
        verts = [P(pa[0]), P(pa[1]), (0, 0), P(pb[0]), P(pb[1]), (0, 0), P(pa[0]), P(pa[0])]
        codes = [MPath.MOVETO, MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts, codes), facecolor=color[a if gidx[a] <= gidx[b] else b], edgecolor="none", alpha=0.35))
    ax.legend(handles=[plt.Line2D([0], [0], color=col, lw=8, label=g) for g, _, col in groups], loc="lower left", fontsize=10, frameon=False)
    ax.set_title(f"{title}\n{LABEL_EN}\n(n) = number of {unit} containing the item; ribbon width = {unit} containing both (ribbons ≥{min_w}); association, not causation",
                 fontsize=11.5)
    fig.savefig(FIG / f"{fname}.svg", bbox_inches="tight")
    fig.savefig(FIG / f"{fname}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return {"弧": len(names), "弦": sum(1 for w in weights.values() if w >= min_w), "最小弦宽": min_w}


def network(nodes, edges, title, fname, min_w, layout, sectors=None, colors=None):
    """共现网络（改自 step13d.network_fig：分组扇区与颜色可配置）。"""
    import networkx as nx
    import plotly.graph_objects as go
    G = nx.Graph()
    for (a, b), w in edges.items():
        if w >= min_w and a in nodes and b in nodes:
            G.add_edge(a, b, weight=w)
    for n in list(G.nodes):
        G.nodes[n].update(nodes[n])
    if layout == "groups":
        pos, tpos = {}, {}
        for typ, (a0, a1) in sectors.items():
            ns = sorted([n for n in G if G.nodes[n]["类型"] == typ], key=lambda n: -G.nodes[n]["频次"])
            for k, n in enumerate(ns):
                ang = math.radians(a0 + (a1 - a0) * (k + 0.5) / max(len(ns), 1))
                pos[n] = (math.cos(ang), math.sin(ang))
                c = math.cos(ang)
                tpos[n] = "middle right" if c > 0.3 else "middle left" if c < -0.3 else ("top center" if math.sin(ang) > 0 else "bottom center")
    else:
        pos = nx.spring_layout(G, k=2.2 / math.sqrt(max(len(G), 1)), weight="weight", seed=3, iterations=400)
        tpos = {n: "top center" for n in G}
    wmax = max([d["weight"] for *_, d in G.edges(data=True)] or [1])
    fmax = max([G.nodes[n]["频次"] for n in G] or [1])
    size = lambda n: 8 + 22 * math.sqrt(G.nodes[n]["频次"] / fmax)  # 8–30 px，按最大频次缩放，节点不互相压住
    tr_ = []
    for a, b, d in G.edges(data=True):
        tr_.append(go.Scatter(x=[pos[a][0], pos[b][0]], y=[pos[a][1], pos[b][1]], mode="lines", hoverinfo="skip", showlegend=False,
                              line=dict(width=0.4 + 4 * d["weight"] / wmax, color="rgba(0,126,112,0.16)" if layout == "groups" else "rgba(110,120,120,0.30)")))
    tr_.append(go.Scatter(x=[(pos[a][0] + pos[b][0]) / 2 for a, b in G.edges], y=[(pos[a][1] + pos[b][1]) / 2 for a, b in G.edges], mode="markers",
                          marker=dict(size=6, opacity=0), hoverinfo="text", showlegend=False,
                          text=[f"{a} — {b}: {d['weight']}" for a, b, d in G.edges(data=True)]))
    for typ in (sectors or colors):
        ns = [n for n in G if G.nodes[n]["类型"] == typ]
        if not ns:
            continue
        tr_.append(go.Scatter(x=[pos[n][0] for n in ns], y=[pos[n][1] for n in ns], mode="markers+text", name=typ, text=ns,
                              textposition=[tpos[n] for n in ns], textfont=dict(size=10.5), hoverinfo="text",
                              hovertext=[f"{n}<br>{G.nodes[n]['说明']}" for n in ns],
                              marker=dict(size=[size(n) for n in ns], color=colors[typ], line=dict(width=1, color="white"))))
    fig = go.Figure(tr_)
    fig.update_layout(title=f"{title}<br>{TITLE_NOTE}", template="plotly_white", height=800, font=FONT, legend=dict(orientation="h", y=-0.03),
                      xaxis=dict(visible=False, range=[-1.9, 1.9] if layout == "groups" else None),
                      yaxis=dict(visible=False, range=[-1.35, 1.35] if layout == "groups" else None, scaleanchor="x" if layout == "groups" else None),
                      margin=dict(l=10, r=10, t=90, b=10))
    fig.write_html(FIG / fname, include_plotlyjs="directory", full_html=True)
    return {"节点": G.number_of_nodes(), "边": G.number_of_edges(), "最小边权": min_w}


def main() -> None:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from scipy.stats import spearmanr
    from scipy.cluster.hierarchy import fcluster, linkage
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score

    # ---------- 分析集 ----------
    raw = rj(S313 / "表述.json")
    main_layer = lambda s: (s["电池类型"] == "Li‖S" and s["正极类型"] == "硫碳类") or s["电池类型"] == "Li‖Cu"
    sts = [s for s in raw if in_analysis(s["性能类别"], s["阶段"]) and main_layer(s) and s["性能类别"] in ("放电容量类", "衰减类", "库仑效率类")
           and not (s["性能类别"] == "库仑效率类" and s["阶段"] == "首圈")]
    sts = F13.dedup(sts)
    summary = {"表述（分析集、主层、去重）": len(sts), "论文": len({s["论文"] for s in sts})}

    # ---------- 每个配方的描述符 ----------
    recs = sorted({(s["论文"], s["recipe"]) for s in sts if s["recipe"]})
    D, how = {}, Counter()
    for k in recs:
        D[k], h = descriptors(*k)
        how[h] += 1
    keys = [k for k, *_ in DESCS]
    X = np.array([[np.nan if D[r][k] is None else D[r][k] for k in keys] for r in recs], float)
    cover = {DLAB[k]: int(np.isfinite(X[:, j]).sum()) for j, k in enumerate(keys)}
    summary.update({"配方": len(recs), "溶剂权重来源": dict(how), "各描述符有值配方数": cover})

    # ---------- 节点：有 / 低 / 高 ----------
    kind, cuts = {}, {}
    for j, k in enumerate(keys):
        v = X[np.isfinite(X[:, j]), j]
        if len(v) < 30:
            continue
        if (v == 0).mean() > 0.5:
            kind[k] = "presence"
        else:
            kind[k] = "tertile"
            cuts[k] = tuple(np.quantile(v, [1 / 3, 2 / 3]))
    summary["节点规则"] = {DLAB[k]: ("有（>0）" if kind[k] == "presence" else f"三等分 {cuts[k][0]:.3g} / {cuts[k][1]:.3g}") for k in kind}

    def tokens(rec):
        out = []
        for k in kind:
            v = D[rec][k]
            if v is None:
                continue
            if kind[k] == "presence":
                if v > 0:
                    out.append(f"{DLAB[k]} · present")
            # 严格不等号：很多配方取同一个值（标准醚电解液）时两个切点相同，等于它的归中档，低/高 = 比这个常见值低/高
            elif v < cuts[k][0]:
                out.append(f"{DLAB[k]} · low")
            elif v > cuts[k][1]:
                out.append(f"{DLAB[k]} · high")
        return out
    tok_fam = {f"{DLAB[k]} · {x}": DFAM[k] for k in kind for x in ("present", "low", "high")}
    rtoks = {r: tokens(r) for r in recs}
    rpapers = defaultdict(set)
    for r in recs:
        for x in rtoks[r]:
            rpapers[x].add(r[0])

    # ---------- 相对本篇对照的性能 ----------
    ctrl = {}
    for s in sts:
        if s["是否对照"] and s["数值类型"] in ("精确", "约数"):
            ctrl.setdefault((s["论文"], s["测试"], s["标准指标"], s["阶段"], s["圈数"]), s)
    perf, pairs = {}, defaultdict(list)
    for s in sts:
        c = ctrl.get((s["论文"], s["测试"], s["标准指标"], s["阶段"], s["圈数"]))
        if s["是否对照"] or not c or s["数值类型"] not in ("精确", "约数") or not s["recipe"] or not c["recipe"] or c["recipe"] == s["recipe"]:
            continue
        e = effect(s["标准指标"], s["数值"], c["数值"], s.get("越大越好"))
        if e is None:
            continue
        perf[s["表述编号"]] = f"{pclass(s)} · {'better' if e > SMALL else 'worse' if e < -SMALL else 'similar'} vs control"
        pairs[(s["论文"], s["recipe"], c["recipe"], pclass(s))].append(e)
    summary["相对对照的表述"] = len(perf)
    summary["相对对照的配对（论文×配方×对照×类别）"] = {c: sum(1 for k in pairs if k[3] == c) for c in ("Discharge capacity", "Capacity fade", "CE · full cell", "CE · Li‖Cu")}

    # ---------- 图1a 结构描述符共现（按配方） ----------
    freq, edges = Counter(), Counter()
    for r in recs:
        ts = sorted(set(rtoks[r]))
        freq.update(ts)
        edges.update(itertools.combinations(ts, 2))
    min_w = max(10, round(0.05 * len(recs)))  # 连线 ≥ 5% 的配方
    nodes = {x: {"类型": tok_fam[x], "频次": n, "说明": f"{tok_fam[x]} · {n} formulations, {len(rpapers[x])} papers"} for x, n in freq.items()}
    summary["图1a"] = network(nodes, edges, "Fig. 1a · Structural-descriptor co-occurrence · one count per formulation",
                              "图1a_结构描述符共现网络.html", min_w, "spring", colors=FAMS)

    # ---------- 图1b 描述符 + 物性 + 条件档 + 性能档（按表述） ----------
    TYPES = {"Structure": "#007e70", "Property": "#d08c2e", "Condition": "#7159a7", "Performance": "#c2504a"}
    freq, edges = Counter(), Counter()
    stoks = []
    for s in sts:
        ts = [("Structure", x) for x in rtoks.get((s["论文"], s["recipe"]), [])]
        ts += [("Property", tr(PROP, k)) for k in s["物性"] if k not in PROP_SKIP]
        ts += [("Condition", tr(BIN, b)) for b in F13.cond_bins(s)]
        if s["表述编号"] in perf and "similar" not in perf[s["表述编号"]]:  # 只画“好于/差于对照”
            ts.append(("Performance", perf[s["表述编号"]]))
        ts = sorted(set(ts))
        stoks.append(ts)
        freq.update(ts)
    top = {g: [n for (gg, n), _ in sorted(((x, c) for x, c in freq.items() if x[0] == g), key=lambda z: -z[1])[:lim]]
           for g, lim in (("Structure", 16), ("Property", 10), ("Condition", 12), ("Performance", 8))}
    keep = {(g, n) for g, ns in top.items() for n in ns}
    for ts in stoks:
        ts = [x for x in ts if x in keep]
        for a, b in itertools.combinations(ts, 2):
            if a[0] != b[0]:
                edges[(a[1], b[1])] += 1
    nodes = {n: {"类型": g, "频次": freq[(g, n)], "说明": f"{g} · in {freq[(g, n)]} statements"} for g, n in keep}
    min_w = max(15, round(0.012 * len(sts)))
    summary["图1b"] = network(nodes, edges, "Fig. 1b · Structure + property + condition + performance (vs own control) · one count per statement",
                              "图1b_描述符物性条件性能共现网络.html", min_w, "groups",
                              sectors={"Property": (35, 145), "Structure": (152, 238), "Performance": (245, 305), "Condition": (-52, 28)}, colors=TYPES)

    # ---------- 图2a 描述符 ↔ 物性（按配方） ----------
    w, f2a, seen = Counter(), Counter(), set()
    rprops = defaultdict(set)
    for s in sts:
        rprops[(s["论文"], s["recipe"])] |= {tr(PROP, k) for k in s["物性"] if k not in PROP_SKIP}
    for r in recs:
        f2a.update(set(rtoks[r]))
        f2a.update(rprops[r])
        for a in set(rtoks[r]):
            for p in rprops[r]:
                w[(a, p)] += 1
    dtop = [x for x, _ in Counter(dict((x, n) for x, n in f2a.items() if x in tok_fam)).most_common(14)]
    ptop = [p for p, _ in Counter(dict((p, n) for p, n in f2a.items() if p not in tok_fam)).most_common(10)]
    w2 = Counter({k: v for k, v in w.items() if k[0] in dtop and k[1] in ptop})
    min2a = max(5, round(np.quantile(list(w2.values()), 0.4))) if w2 else 1
    summary["图2a"] = chord([("Structural descriptor", dtop, "#007e70"), ("Property reported", ptop, "#d08c2e")], w2,
                                "Fig. 2a · Structural descriptor × property reported (per formulation)", "图2a_描述符物性弦图", min_w=min2a, freq=f2a,
                                unit="formulations")

    # ---------- 图2b 描述符 ↔ 物性 ↔ 关键条件 ↔ 性能档（只用能和本篇对照比的表述，四部分才都有） ----------
    key_cond = re.compile(r"贫液|高载量|软包|薄锂|≤0|≥1C|富液|扣式")
    toks_of = []
    for s in sts:
        if s["表述编号"] not in perf:
            continue
        ts = {("D", x) for x in rtoks.get((s["论文"], s["recipe"]), [])}
        ts |= {("P", tr(PROP, k)) for k in s["物性"] if k not in PROP_SKIP}
        ts |= {("C", tr(BIN, b)) for b in F13.cond_bins(s) if key_cond.search(b)}
        ts.add(("R", perf[s["表述编号"]]))
        toks_of.append(ts)
    summary["图2b表述数"] = len(toks_of)
    gc = {g: Counter(n for ts in toks_of for gg, n in ts if gg == g) for g in "DPCR"}
    top = {"D": [n for n, _ in gc["D"].most_common(10)], "P": [n for n, _ in gc["P"].most_common(6)],
           "C": [n for n, _ in gc["C"].most_common(8)], "R": [n for n, _ in gc["R"].most_common(10)]}
    w = Counter()
    for ts in toks_of:
        ts = sorted(x for x in ts if x[1] in top[x[0]])
        for a, b in itertools.combinations(ts, 2):
            if a[0] != b[0]:
                w[(a[1], b[1])] += 1
    vals = sorted(w.values(), reverse=True)
    min2b = max(5, vals[min(len(vals) - 1, 160)]) if vals else 1
    summary["图2b"] = chord([("Structural descriptor", top["D"], "#007e70"), ("Property", top["P"], "#d08c2e"),
                                 ("Test condition", top["C"], "#7159a7"), ("Performance vs own control", top["R"], "#c2504a")], w,
                                f"Fig. 2b · Structure × property × condition × performance vs own control ({len(toks_of)} statements with a control to compare)",
                                "图2b_描述符四部分弦图",
                                min_w=min2b, freq={n: c for g in gc.values() for n, c in g.items()}, unit="statements")

    # ---------- 图3 聚类（只用分子结构描述符：溶剂结构 ＋ 元素比例；用量与溶剂化状态只在簇特征表里列出） ----------
    from scipy.stats import norm, rankdata
    cont = [j for j, k in enumerate(keys) if DFAM[k] in ("Solvent structure", "Elemental ratio") and np.nanstd(X[:, j]) > 0]
    ok = np.all(np.isfinite(X[:, cont]), axis=1)
    Xc = X[ok][:, cont]
    rc = [r for r, o in zip(recs, ok) if o]
    # 按秩转成正态分数再标准化：少数极端配方（大量氟化醚、碳酸酯）不至于主导距离
    Z = np.column_stack([norm.ppf((rankdata(col) - 0.5) / len(col)) for col in Xc.T])
    Z = (Z - Z.mean(0)) / Z.std(0)
    L = linkage(Z, "ward")
    MIN_SIZE = 10
    sil, sizes = {}, {}
    for k in range(3, 9):
        lb = fcluster(L, k, "maxclust")
        sil[k], sizes[k] = float(silhouette_score(Z, lb)), sorted(Counter(lb).values(), reverse=True)
    okk = [k for k in sil if min(sizes[k]) >= MIN_SIZE] or list(sil)
    kbest = max(okk, key=sil.get)  # 轮廓系数最高、且每簇 ≥ 10 个配方
    lab = fcluster(L, kbest, "maxclust")
    comp_cols = [(j, k) for j, k in enumerate(keys) if k in ("salt", "lino3", "dil", "li")]
    pca = PCA(2, random_state=0).fit(Z)
    P2 = pca.transform(Z)
    load = pca.components_
    axis_t = [f"PC{i + 1} ({pca.explained_variance_ratio_[i]:.0%}) · " + ", ".join(
        f"{'+' if load[i][j] > 0 else '−'}{DLAB[keys[cont[j]]]}" for j in np.argsort(-np.abs(load[i]))[:3]) for i in range(2)]
    rec_perf = defaultdict(Counter)
    for s in sts:
        if s["表述编号"] in perf:
            rec_perf[(s["论文"], s["recipe"])][perf[s["表述编号"]]] += 1
    fig = make_subplots(rows=2, cols=1, row_heights=[0.62, 0.38], vertical_spacing=0.06, specs=[[{"type": "xy"}], [{"type": "table"}]])
    pal = ["#007e70", "#c2504a", "#2f6db5", "#d08c2e", "#7159a7", "#5fb3a3", "#8b601a", "#9a86c4"]
    rows_t = []
    first = {}
    for s in sts:
        first.setdefault((s["论文"], s["recipe"]), s)
    for c in range(1, kbest + 1):
        m = lab == c
        txt = []
        for i in np.where(m)[0]:
            r = rc[i]
            s0 = first[r]
            top3 = sorted(range(len(cont)), key=lambda j: -abs(Z[i, j]))[:3]
            txt.append(f"{r[0]} {s0['配方']} · cluster {c}<br>" + "<br>".join(f"{DLAB[keys[cont[j]]]} = {Xc[i, j]:.3g}" for j in top3)
                       + f"<br><span style='color:#888'>components: {s0['配方文字'][:70]}</span>")
        fig.add_trace(go.Scatter(x=P2[m, 0], y=P2[m, 1], mode="markers", name=f"Cluster {c} ({m.sum()})", hovertext=txt, hoverinfo="text",
                                 marker=dict(size=6, color=pal[(c - 1) % len(pal)], opacity=0.75, line=dict(width=0.5, color="white"))), row=1, col=1)
        mz = Z[m].mean(0)
        feat = "; ".join(f"{DLAB[keys[cont[j]]]} {'high' if mz[j] > 0 else 'low'} ({mz[j]:+.1f}σ)" for j in np.argsort(-np.abs(mz))[:4])
        pc = Counter()
        for i in np.where(m)[0]:
            pc.update(rec_perf[rc[i]])
        ptxt = "; ".join(f"{cl}: {pc[f'{cl} · better vs control']}↑ {pc[f'{cl} · similar vs control']}≈ {pc[f'{cl} · worse vs control']}↓"
                         for cl in ("Discharge capacity", "Capacity fade", "CE · full cell", "CE · Li‖Cu")
                         if sum(pc[f"{cl} · {x} vs control"] for x in ("better", "similar", "worse")))
        idx = [recs.index(rc[i]) for i in np.where(m)[0]]
        ctxt = " · ".join(f"{DLAB[k]} {np.nanmean(X[idx, j]):.2g} (n={int(np.isfinite(X[idx, j]).sum())})" for j, k in comp_cols
                          if np.isfinite(X[idx, j]).any())
        rows_t.append([f"Cluster {c}", int(m.sum()), len({rc[i][0] for i in np.where(m)[0]}), feat, ctxt or "—", ptxt or "—"])
    fig.add_trace(go.Table(columnwidth=[55, 55, 45, 300, 220, 300],
                           header=dict(values=["Cluster", "Formulations", "Papers", "Distinguishing structure descriptors (mean z vs all)",
                                               "Composition, mean (not used for clustering)", "Statements vs own control (↑ better · ≈ similar · ↓ worse)"],
                                       fill_color="#f7faf9", align="left", font=dict(size=11, color="#62777a")),
                           cells=dict(values=list(map(list, zip(*rows_t))), align="left", font=dict(size=11), height=26, fill_color="white")), row=2, col=1)
    fig.update_xaxes(title_text=axis_t[0], row=1, col=1, zeroline=False)
    fig.update_yaxes(title_text=axis_t[1], row=1, col=1, zeroline=False)
    fig.update_layout(title=f"Fig. 3 · Clustering of formulations by molecular-structure descriptors only (rank-normal scores, Ward, k = {kbest}: best silhouette "
                            f"with every cluster ≥ {MIN_SIZE}) · PCA view<br>{TITLE_NOTE}",
                      template="plotly_white", height=960, font=FONT, margin=dict(l=60, r=20, t=100, b=10), legend=dict(orientation="h", y=1.02, x=0))
    fig.write_html(FIG / "图3_配方结构聚类.html", include_plotlyjs="directory")
    (OUTD / "图3_聚类结果.json").write_text(json.dumps([{"论文": r[0], "recipe": r[1], "簇": int(c), "PC1": float(p[0]), "PC2": float(p[1])}
                                                    for r, c, p in zip(rc, lab, P2)], ensure_ascii=False, indent=1), encoding="utf-8")
    summary["图3"] = {"聚类用描述符": [DLAB[keys[j]] for j in cont], "进入聚类的配方": len(rc), "论文": len({r[0] for r in rc}),
                     "轮廓系数": {str(k): round(v, 3) for k, v in sil.items()}, "各k簇大小": {str(k): v for k, v in sizes.items()},
                     "选k规则": f"轮廓系数最高、且每簇 ≥ {MIN_SIZE} 个配方", "簇数": kbest, "各簇配方数": {str(c): int((lab == c).sum()) for c in range(1, kbest + 1)},
                     "PCA解释方差": [round(float(x), 3) for x in pca.explained_variance_ratio_], "簇特征": rows_t}

    # ---------- 图4 热图：描述符 × 物性 / 条件 / 相对对照的性能（Spearman） ----------
    ridx = {r: i for i, r in enumerate(recs)}
    pv = defaultdict(lambda: defaultdict(list))
    cv = defaultdict(lambda: defaultdict(list))
    for s in sts:
        r = (s["论文"], s["recipe"])
        if r not in D:  # 没关联到配方的表述
            continue
        for lab_, zh, fn, lg in PROPS:
            for x in s["物性"].get(zh, []):
                if x["来源类型"] == "实测":
                    v = fn(str(x["值"]))
                    if v:
                        pv[r][lab_].append(math.log(v) if lg else v)
        for f, lab_ in (("ES", "E/S"), ("sulfur_loading", "S loading"), ("S_content", "Cathode S"), ("rate", "Rate"), ("temperature", "Temperature")):
            v = s["条件"][f]["值"]
            if v is not None:
                cv[r][lab_].append(v)
    cols = [("Property", p[0]) for p in PROPS] + [("Condition", c) for c in ("E/S", "S loading", "Cathode S", "Rate", "Temperature")] + \
           [("Performance vs own control", c) for c in ("Discharge capacity", "Capacity fade", "CE · full cell", "CE · Li‖Cu")]
    pair_items = {c: [(k, float(np.median(v))) for k, v in pairs.items() if k[3] == c] for c in ("Discharge capacity", "Capacity fade", "CE · full cell", "CE · Li‖Cu")}
    R = np.full((len(keys), len(cols)), np.nan)
    N = np.zeros((len(keys), len(cols)), int)
    NP = np.zeros((len(keys), len(cols)), int)
    for j, k in enumerate(keys):
        for c, (blk, name) in enumerate(cols):
            xs, ys, ps = [], [], set()
            if blk == "Property":
                for r, d in pv.items():
                    if name in d and D[r][k] is not None:
                        xs.append(D[r][k]); ys.append(float(np.median(d[name]))); ps.add(r[0])
            elif blk == "Condition":
                for r, d in cv.items():
                    if name in d and D[r][k] is not None:
                        xs.append(D[r][k]); ys.append(float(np.median(d[name]))); ps.add(r[0])
            else:
                for (pid, ra, rb, _), e in pair_items[name]:
                    a, b = D[(pid, ra)][k], D[(pid, rb)][k]  # 对照也在分析集里，D 里都有
                    if a is not None and b is not None:
                        xs.append(a - b); ys.append(e); ps.add(pid)
            N[j, c], NP[j, c] = len(xs), len(ps)
            if len(xs) >= 15 and np.std(xs) > 0 and np.std(ys) > 0:
                R[j, c] = spearmanr(xs, ys).statistic
    txt = [[("" if np.isnan(R[j, c]) else f"{R[j, c]:+.2f}") for c in range(len(cols))] for j in range(len(keys))]
    hov = [[f"{DLAB[keys[j]]} × {cols[c][1]}<br>ρ = {txt[j][c] or 'n < 15'}<br>n = {N[j, c]} ({'pairs' if cols[c][0].startswith('Perf') else 'formulations'}), "
            f"{NP[j, c]} papers" for c in range(len(cols))] for j in range(len(keys))]
    SHORT = {"ln conductivity": "Conductivity (ln)", "ln viscosity": "Viscosity (ln)", "Li⁺ transference no.": "Li⁺ transference",
             "Discharge capacity": "Capacity", "Capacity fade": "Fade", "CE · full cell": "CE full cell", "CE · Li‖Cu": "CE Li‖Cu"}
    xl = [SHORT.get(n, n) for _, n in cols]
    fig = go.Figure(go.Heatmap(z=R, x=xl, y=[f"{DLAB[k]}  [{DFAM[k]}]" for k in keys], zmin=-1, zmax=1, zmid=0,
                               colorscale="RdBu_r", text=txt, texttemplate="%{text}", textfont=dict(size=9), customdata=hov,
                               hovertemplate="%{customdata}<extra></extra>", colorbar=dict(title="Spearman ρ"), xgap=1, ygap=1))
    for c in range(1, len(cols)):
        if cols[c][0] != cols[c - 1][0]:
            fig.add_vline(x=c - 0.5, line=dict(color="black", width=2))
    for j in range(1, len(keys)):
        if DFAM[keys[j]] != DFAM[keys[j - 1]]:
            fig.add_hline(y=j - 0.5, line=dict(color="#62777a", width=1.5))
    blocks = {"Property": "Properties<br><span style='font-size:10px'>descriptor level vs value, across formulations</span>",
              "Condition": "Test conditions<br><span style='font-size:10px'>which designs are tested where</span>",
              "Performance vs own control": "Performance vs own control<br><span style='font-size:10px'>Δ descriptor (formulation − control) vs gain</span>"}
    for b, lab_ in blocks.items():
        idx = [c for c, (bb, _) in enumerate(cols) if bb == b]
        fig.add_annotation(x=(idx[0] + idx[-1]) / 2, y=1.0, xref="x", yref="paper", yanchor="bottom", text=f"<b>{lab_}</b>", showarrow=False,
                           font=dict(size=12, color="#172d32"))
    fig.update_layout(title=f"Fig. 4 · Heat map · structural descriptors × properties, test conditions and performance vs own control (Spearman ρ; blank = n < 15)<br>{TITLE_NOTE}",
                      template="plotly_white", height=1000, font=FONT, plot_bgcolor="#dfe7e3", xaxis=dict(side="bottom", tickangle=-30),
                      yaxis=dict(autorange="reversed"), margin=dict(l=280, r=20, t=150, b=90))
    fig.write_html(FIG / "图4_描述符相关热图.html", include_plotlyjs="directory")
    (OUTD / "图4_相关矩阵.json").write_text(json.dumps({"行": [DLAB[k] for k in keys], "列": [f"{b}｜{n}" for b, n in cols],
                                                     "rho": [[None if np.isnan(x) else round(float(x), 3) for x in row] for row in R],
                                                     "n": N.tolist(), "论文数": NP.tolist()}, ensure_ascii=False, indent=1), encoding="utf-8")
    strong = sorted(((abs(R[j, c]), DLAB[keys[j]], f"{cols[c][0]} · {cols[c][1]}", round(float(R[j, c]), 2), int(N[j, c]), int(NP[j, c]))
                     for j in range(len(keys)) for c in range(len(cols)) if np.isfinite(R[j, c])), reverse=True)
    summary["图4"] = {"有值格子": int(np.isfinite(R).sum()), "格子总数": int(R.size), "最强相关前12": [x[1:] for x in strong[:12]],
                     "性能块最强前8": [x[1:] for x in strong if x[2].startswith("Performance")][:8]}
    (OUTD / "step13h_汇总.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("各描述符有值配方数", "节点规则")}, ensure_ascii=False, indent=1)[:6000])


if __name__ == "__main__":
    main()
