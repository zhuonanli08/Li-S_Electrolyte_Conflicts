"""step13d：表述分析四张图（初步，30 篇）。11-04 用户定：图不限于配方字段，可做配方＋物性＋条件＋性能的组合。

图1 共现网络：1a 配方组分共现；1b 组分＋物性＋条件档＋性能档（按表述共现）
图2 弦图：2a 组分化学类别 ↔ 物性类别；2b 组分类别、物性、条件、性能四组之间
图3 聚类图：每个配方一行，列分四块（配方描述符｜物性｜条件｜性能），层次聚类排序
图4 文字向量图：整条表述文字 → TF-IDF 字符 n-gram → SVD → UMAP 二维
输出：网站/图/*.html（plotly，交互）、网站/图/*.svg/png（弦图，matplotlib），step13d_汇总.json
图形表示关联，不证明因果；疑似重复组每组只计一次。
"""
from __future__ import annotations

import itertools
import math
import re
from collections import Counter, defaultdict

import numpy as np

from step13_common import COMP, LABEL, OUT, in_analysis, read_json, write_json
from step13_i18n import BATT, BIN, CAT, CHEM, PROP, ROLE, statement_en, t as tr

FIG = OUT / "网站" / "图"
FIG.mkdir(parents=True, exist_ok=True)
LABEL_EN = "Preliminary · 30 papers (F-version, rule-processed)"
TITLE_NOTE = f"<span style='font-size:12px;color:#62777a'>{LABEL_EN} · association, not causation</span>"
FONT = dict(family="Segoe UI, Arial, sans-serif", color="#172d32")
TYPE_COLOR = {"Component": "#007e70", "Property": "#d08c2e", "Condition": "#7159a7", "Performance": "#c2504a"}


def dedup(sts):
    seen, out = set(), []
    for s in sts:
        g = s.get("疑似重复组")
        if g and g in seen:
            continue
        seen.add(g)
        out.append(s)
    return out


def cond_bins(s) -> list[str]:
    c = s["条件"]
    v = lambda f: c[f]["值"]
    out = []
    if v("ES") is not None:
        out.append("E/S≤5（贫液）" if v("ES") <= 5 else "E/S 5–10" if v("ES") <= 10 else "E/S>10（富液）")
    if v("sulfur_loading") is not None:
        x = v("sulfur_loading")
        out.append("硫载量<2" if x < 2 else "硫载量2–4" if x < 4 else "硫载量≥4（高载量）")
    if v("S_content") is not None:
        x = v("S_content")
        out.append("正极含硫<50%" if x < 50 else "正极含硫50–65%" if x < 65 else "正极含硫≥65%")
    if v("rate") is not None:
        x = v("rate")
        out.append("倍率≤0.2C" if x <= 0.2 else "倍率0.2–1C" if x < 1 else "倍率≥1C")
    if v("temperature") is not None:
        x = v("temperature")
        out.append("温度≤0°C" if x <= 0 else "温度>40°C" if x > 40 else "常温")
    if v("Li_thickness") is not None:
        out.append("锂≤50μm（薄锂）" if v("Li_thickness") <= 50 else "锂>50μm")
    if v("cell_format"):
        out.append(v("cell_format"))
    return out


def perf_levels(sts, norm_map) -> dict[str, str]:
    """性能档：用归一化到普遍条件后的值（step13f），同一类内三等分，给“性能类别·好/中/差”。没有归一化值的表述不分档。"""
    grp = defaultdict(list)
    for s in sts:
        x = norm_map.get(s["表述编号"])
        if x and not x.get("普遍条件_外推"):
            grp[x["类别"]].append((s, x["普遍条件_y"]))
    out = {}
    for k, lst in grp.items():
        if len(lst) < 6:
            continue
        lo, hi = np.quantile([v for _, v in lst], [1 / 3, 2 / 3])
        for s, v in lst:
            lvl = "好" if v > hi else "差" if v < lo else "中"
            out[s["表述编号"]] = f"{tr(CAT, k)} · {dict(好='good', 中='mid', 差='poor')[lvl]}"
    return out


def comp_ids(s, comp_rec) -> list[str]:
    r = comp_rec.get((s["论文"], s["recipe"]))
    return sorted({i["组分"] for i in r["组分"]}) if r else []


# ---------------- 图1 共现网络 ----------------
def network_fig(nodes: dict, edges: Counter, title: str, fname: str, min_w: int, seed=3, label_top: int | None = None,
                layout: str = "spring"):
    import networkx as nx
    import plotly.graph_objects as go
    G = nx.Graph()
    for (a, b), w in edges.items():
        if w >= min_w:
            G.add_edge(a, b, weight=w)
    for n in list(G.nodes):
        G.nodes[n].update(nodes[n])
    if layout == "groups":
        # 分组环形布局：每类节点占圆周的一段，同组按频次排开，标签朝外，避免挤在中间
        sectors = {"Property": (28, 152), "Component": (158, 238), "Performance": (244, 296), "Condition": (-58, 22)}
        pos, tpos = {}, {}
        for typ, (a0, a1) in sectors.items():
            ns = sorted([n for n in G if G.nodes[n]["类型"] == typ], key=lambda n: -G.nodes[n]["频次"])
            for k, n in enumerate(ns):
                ang = math.radians(a0 + (a1 - a0) * (k + 0.5) / max(len(ns), 1))
                pos[n] = (math.cos(ang), math.sin(ang))
                c = math.cos(ang)
                tpos[n] = "middle right" if c > 0.3 else "middle left" if c < -0.3 else ("top center" if math.sin(ang) > 0 else "bottom center")
    else:
        pos = nx.spring_layout(G, k=1.6 / math.sqrt(max(len(G), 1)), weight="weight", seed=seed, iterations=300)
        tpos = {n: "top center" for n in G}
    wmax = max([d["weight"] for *_, d in G.edges(data=True)] or [1])
    top_lab = set(sorted(G.nodes, key=lambda n: -G.nodes[n]["频次"])[:label_top]) if label_top else set(G.nodes)
    traces = []
    for a, b, d in G.edges(data=True):
        traces.append(go.Scatter(x=[pos[a][0], pos[b][0]], y=[pos[a][1], pos[b][1]], mode="lines", hoverinfo="skip",
                                 line=dict(width=(0.4 + 3 * d["weight"] / wmax) if layout == "groups" else (0.5 + 5 * d["weight"] / wmax),
                                           color="rgba(0,126,112,0.18)" if layout == "groups" else "rgba(120,120,120,0.35)"), showlegend=False))
    mx, my, mt = [], [], []
    for a, b, d in G.edges(data=True):
        mx.append((pos[a][0] + pos[b][0]) / 2)
        my.append((pos[a][1] + pos[b][1]) / 2)
        mt.append(f"{a} — {b}: {d['weight']}")
    traces.append(go.Scatter(x=mx, y=my, mode="markers", marker=dict(size=6, opacity=0), hoverinfo="text", text=mt, showlegend=False))
    for typ in sorted({G.nodes[n]["类型"] for n in G}):
        ns = [n for n in G if G.nodes[n]["类型"] == typ]
        traces.append(go.Scatter(
            x=[pos[n][0] for n in ns], y=[pos[n][1] for n in ns], mode="markers+text", name=typ,
            text=[n if (label_top is None or n in top_lab) else "" for n in ns], textposition=[tpos[n] for n in ns], textfont=dict(size=10.5),
            hovertext=[f"{n}<br>{G.nodes[n]['说明']}" for n in ns], hoverinfo="text",
            marker=dict(size=[(6 + 1.6 * math.sqrt(G.nodes[n]["频次"])) if layout == "groups" else (8 + 3.2 * math.sqrt(G.nodes[n]["频次"])) for n in ns],
                        color=G.nodes[ns[0]].get("颜色", TYPE_COLOR.get(typ, "#999")), line=dict(width=1, color="white"))))
    fig = go.Figure(traces)
    fig.update_layout(title=f"{title}<br>{TITLE_NOTE}", template="plotly_white", height=760,
                      xaxis=dict(visible=False, range=[-1.9, 1.9] if layout == "groups" else None),
                      yaxis=dict(visible=False, range=[-1.35, 1.35] if layout == "groups" else None, scaleanchor="x" if layout == "groups" else None),
                      legend=dict(orientation="h", y=-0.03),
                      margin=dict(l=10, r=10, t=80, b=10), font=FONT)
    fig.write_html(FIG / fname, include_plotlyjs="directory", full_html=True)
    return {"节点": G.number_of_nodes(), "边": G.number_of_edges(), "最小边权": min_w}


# ---------------- 图2 弦图（matplotlib） ----------------
def chord(groups: list[tuple[str, list[str], str]], weights: Counter, title: str, fname: str, min_w=1, freq: dict | None = None,
          unit: str = "表述"):
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
    gap = 2.0
    total = sum(tot[n] for _, n, _ in names)
    span = 360 - gap * len(names) - 6 * len(groups)
    ang, start, cur_g = {}, 90.0, None
    for g, n, col in names:
        if g != cur_g:
            start -= 6
            cur_g = g
        width = span * tot[n] / total
        ang[n] = [start - width, start, start - width]  # [起, 止, 游标]
        start -= width + gap
    fig, ax = plt.subplots(figsize=(11, 11))
    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.45, 1.45)
    ax.axis("off")
    color = {n: col for _, n, col in names}
    gidx = {n: i for i, (g, ns, _) in enumerate(groups) for n in ns}
    for g, n, col in names:
        a0, a1, _ = ang[n]
        ax.add_patch(Wedge((0, 0), 1.0, a0, a1, width=0.06, color=col))
        mid = math.radians((a0 + a1) / 2)
        rot = (a0 + a1) / 2
        ha = "left" if math.cos(mid) >= 0 else "right"
        if math.cos(mid) < 0:
            rot += 180
        ax.text(1.05 * math.cos(mid), 1.05 * math.sin(mid), f"{n.replace('⁺', '+')} ({(freq or tot)[n]})", rotation=rot, rotation_mode="anchor",
                ha=ha, va="center", fontsize=8.5)
    for (a, b), w in sorted(weights.items(), key=lambda x: -x[1]):
        if w < min_w or a not in ang or b not in ang:
            continue
        sa = span * w / total
        pa = (ang[a][2], ang[a][2] + sa)
        pb = (ang[b][2], ang[b][2] + sa)
        ang[a][2] += sa
        ang[b][2] += sa
        P = lambda t: (0.94 * math.cos(math.radians(t)), 0.94 * math.sin(math.radians(t)))
        # 弦：A 弧段 → 经圆心的二次曲线 → B 弧段 → 经圆心回到 A
        verts = [P(pa[0]), P(pa[1]), (0, 0), P(pb[0]), P(pb[1]), (0, 0), P(pa[0]), P(pa[0])]
        codes = [MPath.MOVETO, MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts, codes), facecolor=color[a if gidx[a] <= gidx[b] else b], edgecolor="none", alpha=0.35))
    handles = [plt.Line2D([0], [0], color=col, lw=8, label=g) for g, _, col in groups]
    ax.legend(handles=handles, loc="lower left", fontsize=9, frameon=False)
    ax.set_title(f"{title}\n{LABEL_EN}\n(n) = number of {unit} containing the item; ribbon width = {unit} containing both (ribbons ≥{min_w}); association, not causation",
                 fontsize=11)
    fig.savefig(FIG / f"{fname}.svg", bbox_inches="tight")
    fig.savefig(FIG / f"{fname}.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    return {"弧": len(names), "弦": sum(1 for w in weights.values() if w >= min_w), "最小弦宽": min_w}


def main() -> None:
    import plotly.graph_objects as go
    sts_all = [s for s in read_json("表述.json") if in_analysis(s["性能类别"], s["阶段"])]  # 分析集：倍率容量不纳入，放电容量只看首圈
    sts = dedup(sts_all)
    comp_rec = {(r["论文"], r["配方"]): r for r in read_json("配方组成.json", COMP)}
    ctab = {c["id"]: c for c in read_json("组分表.json", COMP)}
    ccls = lambda cid: ctab.get(cid, {}).get("化学类别") or "未分类"
    ccat = lambda cid: ctab.get(cid, {}).get("类别") or "未分类"
    summary = {"表述（去重后）": len(sts), "去掉的疑似重复": len(sts_all) - len(sts)}
    nfile = OUT / "归一化_表述.json"
    nst = read_json("归一化_表述.json") if nfile.exists() else []
    norm_map = {x["表述编号"]: x for x in nst}
    plev = perf_levels(sts, norm_map)

    # ---- 1a 配方组分共现（以电池测试用到的 recipe 为单位） ----
    recipes = {(s["论文"], s["recipe"]) for s in sts if s["recipe"]}
    nodes, edges, freq, papers_of = {}, Counter(), Counter(), defaultdict(set)
    cat_color = {"Solvent": "#007e70", "Li salt": "#c2504a", "Additive": "#d08c2e", "Solvent/additive": "#5fb3a3",
                 "Additive (mediator)": "#7159a7", "Li salt/additive": "#e58e8a", "Other salt/additive": "#8b601a", "Redox mediator": "#9a86c4"}
    for key in recipes:
        r = comp_rec.get(key)
        if not r:
            continue
        cs = sorted({i["组分"] for i in r["组分"] if ccat(i["组分"]) not in ("硫物种", "离子")})
        for c in cs:
            freq[c] += 1
            papers_of[c].add(key[0])
        for a, b in itertools.combinations(cs, 2):
            edges[(a, b)] += 1
    for c in freq:
        nodes[c] = {"类型": tr(ROLE, ccat(c)), "频次": freq[c], "颜色": cat_color.get(tr(ROLE, ccat(c)), "#999"),
                    "说明": f"{ctab.get(c, {}).get('英文名', '')} · {tr(CHEM, ccls(c))} · {freq[c]} formulations, {len(papers_of[c])} papers"}
    summary["图1a"] = network_fig(nodes, edges, "Fig. 1a · Component co-occurrence",
                                  "图1a_配方组分共现网络.html", min_w=1)

    # ---- 1b 四部分共现（按表述） ----
    nodes, edges, freq = {}, Counter(), Counter()
    for s in sts:
        toks = []
        for c in comp_ids(s, comp_rec):
            if ccat(c) in ("硫物种", "离子"):
                continue
            toks.append(("Component", c))
        toks += [("Property", tr(PROP, k)) for k in s["物性"]]
        toks += [("Condition", tr(BIN, b)) for b in cond_bins(s)]
        if s["表述编号"] in plev:
            toks.append(("Performance", plev[s["表述编号"]]))
        toks = sorted(set(toks))
        for t in toks:
            freq[t] += 1
        for a, b in itertools.combinations(toks, 2):
            if a[0] == b[0] == "Component" or a[0] != b[0]:
                edges[(a[1], b[1])] += 1
    keep = {t for t, n in freq.items() if n >= 8}
    nodes = {t[1]: {"类型": t[0], "频次": n, "说明": f"{t[0]} · in {n} statements"} for t, n in freq.items() if t in keep}
    keepn = set(nodes)
    edges = Counter({k: v for k, v in edges.items() if k[0] in keepn and k[1] in keepn})
    summary["图1b"] = network_fig(nodes, edges, "Fig. 1b · Four-part co-occurrence",
                                  "图1b_四部分共现网络.html", min_w=10, layout="groups")

    # ---- 2a 组分化学类别 ↔ 物性（按配方计） ----
    w = Counter()
    seen = set()
    for s in sts:
        key = (s["论文"], s["recipe"])
        cls_set = {ccls(c) for c in comp_ids(s, comp_rec) if ccat(c) not in ("硫物种", "离子")}
        for k in s["物性"]:
            for cl in cls_set:
                if (key, cl, k) not in seen:
                    seen.add((key, cl, k))
                    w[(tr(CHEM, cl), tr(PROP, k))] += 1
    cls_names = [c for c, _ in Counter(c for c, _ in w.elements()).most_common(10)]
    prop_names = [p for p, _ in Counter(p for _, p in w.elements()).most_common(10)]
    w = Counter({k: v for k, v in w.items() if k[0] in cls_names and k[1] in prop_names})
    f2a = Counter()
    for key in {(s["论文"], s["recipe"]) for s in sts}:
        ss = next(s for s in sts if (s["论文"], s["recipe"]) == key)
        for cl in {ccls(c) for c in comp_ids(ss, comp_rec) if ccat(c) not in ("硫物种", "离子")}:
            f2a[tr(CHEM, cl)] += 1
        for k in ss["物性"]:
            f2a[tr(PROP, k)] += 1
    summary["图2a"] = chord([("Component chemical class", cls_names, "#007e70"), ("Property", prop_names, "#d08c2e")], w,
                           "Fig. 2a · Formulation × property: which component classes have which properties reported", "图2a_配方物性弦图", min_w=1,
                           freq=f2a, unit="formulations")

    # ---- 2b 四组：组分类别、物性、条件、性能类别（按表述） ----
    toks_of = []
    for s in sts:
        t = {("组分", tr(CHEM, ccls(c))) for c in comp_ids(s, comp_rec) if ccat(c) not in ("硫物种", "离子")}
        t |= {("物性", tr(PROP, k)) for k in s["物性"]}
        t |= {("条件", tr(BIN, b)) for b in cond_bins(s) if re.search(r"贫液|高载量|软包|薄锂|≤0|≥1C|富液|扣式", b)}
        t.add(("性能", tr(CAT, s["性能类别"])))
        toks_of.append(t)
    gc = {g: Counter(n for ts in toks_of for gg, n in ts if gg == g) for g in ("组分", "物性", "条件", "性能")}
    top = {"组分": [n for n, _ in gc["组分"].most_common(8)], "物性": [n for n, _ in gc["物性"].most_common(6)],
           "条件": [n for n, _ in gc["条件"].most_common(8)], "性能": [n for n, _ in gc["性能"].most_common()]}
    w = Counter()
    for ts in toks_of:
        ts = [x for x in ts if x[1] in top[x[0]]]
        for a, b in itertools.combinations(sorted(ts), 2):
            if a[0] != b[0]:
                w[(a[1], b[1])] += 1
    summary["图2b"] = chord([("Component class", top["组分"], "#007e70"), ("Property", top["物性"], "#d08c2e"),
                            ("Test condition", top["条件"], "#7159a7"), ("Performance class", top["性能"], "#c2504a")], w,
                           "Fig. 2b · Formulation × property × condition × performance: co-occurrence between the four groups", "图2b_四部分弦图", min_w=15,
                           freq={n: c for g in gc.values() for n, c in g.items()}, unit="statements")

    # ---- 图3 聚类图：每个配方一行 ----
    by_rec = defaultdict(list)
    for s in sts:
        by_rec[(s["论文"], s["配方"])].append(s)
    # 篇内相对对照：同篇同测试同指标同取值点，配方值 / 对照值 取对数
    ctrl = {}
    for s in sts:
        if s["是否对照"] and s["数值类型"] in ("精确", "约数"):
            ctrl[(s["论文"], s["测试"], s["标准指标"], s["阶段"], s["圈数"])] = s["数值"]

    def rel(lst, std):
        out = []
        for s in lst:
            c = ctrl.get((s["论文"], s["测试"], s["标准指标"], s["阶段"], s["圈数"]))
            if not s["是否对照"] and c and s["数值"] and s["标准指标"] == std and s["数值类型"] in ("精确", "约数") and c > 0 and s["数值"] > 0:
                out.append(math.log(s["数值"] / c))
        return float(np.median(out)) if out else None

    def med(lst, cname):
        """归一化到普遍条件后的中位数（不含外推表述）。"""
        v = [norm_map[s["表述编号"]]["普遍条件_归一化值"] for s in lst
             if s["表述编号"] in norm_map and norm_map[s["表述编号"]]["类别"] == cname and not norm_map[s["表述编号"]]["普遍条件_外推"]]
        return float(np.median(v)) if v else None

    def pnum(lst, k):
        v = [p["数值"] for s in lst for p in s["物性"].get(k, []) if p["数值"] is not None and p["来源类型"] == "实测"]
        return float(np.median(v)) if v else None

    def cmed(lst, f):
        v = [s["条件"][f]["值"] for s in lst if s["条件"][f]["值"] is not None]
        return float(np.median(v)) if v else None

    cols = [("Formulation", "sO"), ("Formulation", "aC"), ("Formulation", "F/O"), ("Formulation", "InOr"), ("Formulation", "LiNO₃ present"),
            ("Property", "Ionic conductivity"), ("Property", "Viscosity"), ("Property", "Li⁺ transference no."), ("Property", "No. of properties reported"),
            ("Condition", "E/S"), ("Condition", "S loading"), ("Condition", "Cathode S"), ("Condition", "Rate"), ("Condition", "T"), ("Condition", "Pouch share"),
            ("Performance", "1st-cycle capacity (normalised)"), ("Performance", "Retention (normalised)"), ("Performance", "Full-cell CE (normalised)"),
            ("Performance", "Li‖Cu CE (normalised)"), ("Performance", "vs own control · capacity (ln)"), ("Performance", "vs own control · retention (ln)")]
    rows, labels, hov = [], [], []
    for (pid, fid), lst in sorted(by_rec.items()):
        s0 = lst[0]
        r = s0["元素比例"] or {}
        if not r:
            continue
        vals = [r.get("sO"), r.get("aC"), r.get("F/O"), r.get("InOr"), 1.0 if s0["分块"]["LiNO3"] else 0.0,
                pnum(lst, "离子电导率"), pnum(lst, "黏度"), pnum(lst, "Li⁺迁移数"), float(len(s0["物性"])),
                cmed(lst, "ES"), cmed(lst, "sulfur_loading"), cmed(lst, "S_content"), cmed(lst, "rate"), cmed(lst, "temperature"),
                float(np.mean([s["条件"]["cell_format"]["值"] == "软包" for s in lst])),
                med(lst, "放电容量类"), med(lst, "衰减类"), med(lst, "库仑效率类·全电池"), med(lst, "库仑效率类·Li‖Cu"),
                rel(lst, "硫比放电容量"), rel(lst, "容量保持率")]
        perf_n = sum(v is not None for v in vals[15:])
        if perf_n == 0:
            continue
        rows.append(vals)
        labels.append(f"{pid}:{fid}{' (control)' if s0['是否对照'] else ''}")
        hov.append(s0["配方文字"][:80])
    X = np.array([[np.nan if v is None else v for v in r] for r in rows], dtype=float)
    mu, sd = np.nanmean(X, 0), np.nanstd(X, 0)
    sd[sd == 0] = 1
    Z = (X - mu) / sd
    Zf = np.where(np.isnan(Z), 0.0, Z)
    from scipy.cluster.hierarchy import fcluster, leaves_list, linkage
    L = linkage(Zf, "ward")
    order = leaves_list(L)
    clus = fcluster(L, 5, "maxclust")
    Zo, Xo = Z[order], X[order]
    lab_o = [labels[i] for i in order]
    text = [[("not reported" if np.isnan(Xo[i, j]) else f"{Xo[i, j]:.3g}") for j in range(len(cols))] for i in range(len(order))]
    hm = go.Heatmap(z=np.clip(Zo, -2.5, 2.5), x=[f"{a} · {b}" for a, b in cols], y=lab_o, colorscale="RdBu_r", zmid=0,
                    text=text, hovertemplate="%{y}<br>%{x}<br>value: %{text}<extra></extra>", colorbar=dict(title="z-score"),
                    xgap=1, ygap=0.5)
    fig = go.Figure(hm)
    for k, (a, b) in enumerate(cols):
        if k and cols[k - 1][0] != a:
            fig.add_vline(x=k - 0.5, line=dict(color="black", width=2))
    fig.update_layout(title=f"Fig. 3 · Clustered heat map · one row per formulation (grey = not reported or extrapolated)<br>{TITLE_NOTE}",
                      template="plotly_white", height=max(600, 14 * len(order) + 220), plot_bgcolor="#dfe7e3",
                      xaxis=dict(tickangle=-40, side="top"), yaxis=dict(autorange="reversed", tickfont=dict(size=9)),
                      margin=dict(l=170, r=20, t=210, b=20), font=FONT)
    fig.write_html(FIG / "图3_四部分聚类热图.html", include_plotlyjs="directory")
    summary["图3"] = {"配方行数": len(order), "列": [f"{a}｜{b}" for a, b in cols],
                     "各列有值的配方数": {f"{a}｜{b}": int((~np.isnan(X[:, j])).sum()) for j, (a, b) in enumerate(cols)},
                     "聚类数": 5, "各簇配方数": dict(Counter(int(c) for c in clus))}
    write_json("图3_聚类结果.json", [{"配方": labels[i], "簇": int(clus[i])} for i in range(len(labels))])

    # ---- 图4 文字向量图 ----
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer
    import umap
    en = {s["表述编号"]: statement_en(s, comp_rec.get((s["论文"], s["recipe"]))) for s in sts}
    docs = [re.sub(r"^\[Formulation\] \S+ \S+:", "[Formulation]", en[s["表述编号"]]) for s in sts]  # 去掉论文号与配方编号，免得按论文聚
    tf = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=2, sublinear_tf=True).fit_transform(docs)
    svd = TruncatedSVD(n_components=50, random_state=42).fit_transform(tf)
    emb = umap.UMAP(n_neighbors=15, min_dist=0.25, metric="cosine", random_state=42).fit_transform(svd)
    wrap = lambda t: "<br>".join(t[i:i + 60] for i in range(0, min(len(t), 420), 60))
    traces, vis_sets = [], []
    for key, getter in (("performance class", lambda s: tr(CAT, s["性能类别"])), ("paper", lambda s: s["论文"]),
                        ("cell type", lambda s: tr(BATT, s["电池类型"]))):
        cats = sorted({getter(s) for s in sts})
        idx0 = len(traces)
        for c in cats:
            ii = [i for i, s in enumerate(sts) if getter(s) == c]
            traces.append(go.Scattergl(x=emb[ii, 0], y=emb[ii, 1], mode="markers", name=str(c), visible=(key == "performance class"),
                                       marker=dict(size=7, opacity=0.8),
                                       text=[f"<b>{sts[i]['表述编号']}</b> {wrap(en[sts[i]['表述编号']])}" for i in ii],
                                       hoverinfo="text"))
        vis_sets.append((key, idx0, len(traces)))
    buttons = []
    for key, a, b in vis_sets:
        vis = [a <= i < b for i in range(len(traces))]
        buttons.append(dict(label=f"Colour by {key}", method="update", args=[{"visible": vis}]))
    fig = go.Figure(traces)
    fig.update_layout(title=f"Fig. 4 · Statement text map (TF-IDF character n-grams → UMAP)<br>{TITLE_NOTE}",
                      template="plotly_white", height=760, updatemenus=[dict(buttons=buttons, x=1.0, y=1.12, xanchor="right")],
                      xaxis=dict(title="UMAP-1"), yaxis=dict(title="UMAP-2"), font=FONT)
    fig.write_html(FIG / "图4_表述文字向量图.html", include_plotlyjs="directory")
    write_json("图4_坐标.json", [{"表述编号": s["表述编号"], "x": float(emb[i, 0]), "y": float(emb[i, 1])} for i, s in enumerate(sts)])
    summary["图4"] = {"表述数": len(sts), "方法": "TF-IDF(char_wb 2–4, min_df=2) → TruncatedSVD(50) → UMAP(n_neighbors=15, min_dist=0.25, cosine)",
                     "局限": "字符 n-gram 只反映字面相似，不是语义向量；相近的点多是同类配方/同类指标的表述"}
    write_json("step13d_汇总.json", summary)
    import json
    print(json.dumps(summary, ensure_ascii=False, indent=1)[:3000])


if __name__ == "__main__":
    main()
