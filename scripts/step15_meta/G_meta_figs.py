"""step15 G：05 页的图（11-06 用户要求：像 Figures 页那样的网络、桑基、热图，表现“整体交织”的 meta；图上文字英文；配方一律用分子描述符、按数值）。
读 F_pooled 的结果（meta_v3_全部测量_313篇_2026-11-06/汇总.json）、D_site 的网站数据（矛盾单元与判定）；图写到网站 图/。
  图 M1 数据流桑基：313 篇 → 四类性能 → 每个测量提供的是同测试 / 同篇跨测试 / 只有篇间的信息（宽度 = 测量数）；
  图 M2 证据网络：6 条描述符轴（大节点，成员描述符为卫星）→ 四类性能；连线 = 去重叠联合模型的同测试效应；轴之间橙色虚线 = 成员跨轴相关 |ρ| ≥ 0.5；
  图 M3 论文—轴网络：论文连到它在同一测试里改过的轴；红线 = 该篇方向与汇总相反；论文颜色 = 读原文的矛盾原因；
  图 M4 三层效应热图：22 个描述符（按轴排）× 四类性能 × 同测试 / 篇间；
  图 M5 矛盾归因桑基：性能 → 改动涉及的描述符轴 → 原因 → 判定；
  图 M6 同一电解液跨实验室：沿用 D_site 的图（文件名改为 M6）。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 G_meta_figs.py
"""
import sys
import json
import math
import shutil
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import D_site as D
import F_pooled as F

V3 = json.loads((F.OUT / "汇总.json").read_text(encoding="utf-8"))
W = json.loads((D.OUT / "网站数据.json").read_text(encoding="utf-8"))
FIG = D.SITE_FIG
CL = F.CLASSES
EN = D.EN_CLASS
AX = V3["轴"]
AXN = list(AX)
ACOL = dict(zip(AXN, D.REASON_COLORS))
LAB = F.LAB
BLUE, RED, GREY = D.BLUE, "#d03b3b", "#b7c2c4"


def write(fig, name):
    fig.write_html(FIG / name, include_plotlyjs="directory", full_html=True, config={"displaylogo": False})


def lnx(e):
    return math.log(e["倍数_每1SD"])


# ---------------- M1 数据流桑基 ----------------
def fig_flow(M):
    import plotly.graph_objects as go
    allM = json.loads((F.IN / "测量表.json").read_text(encoding="utf-8"))
    nodes = ["313 papers · main layer"] + [f"{EN[c]}" for c in CL] + \
            ["Same test, formulation varied", "Same paper, across tests", "Between papers only", "Not near room temperature"]
    idx = {n: i for i, n in enumerate(nodes)}
    tot = Counter()
    src, tgt, val, col, hov = [], [], [], [], []
    for c in CL:
        a = [r for r in allM if r["类别"] == c]
        m = [r for r in M if r["类别"] == c]
        src.append(0); tgt.append(idx[EN[c]]); val.append(len(a)); col.append("rgba(23,45,50,0.25)")
        hov.append(f"{EN[c]}: {len(a)} measurements from {len({r['论文'] for r in a})} papers")
        bt, bp = defaultdict(set), defaultdict(set)
        for r in m:
            key = r["recipe"]
            bt[(r["论文"], r["测试"])].add(key); bp[r["论文"]].add(key)
        kinds = Counter()
        for r in m:
            if len(bt[(r["论文"], r["测试"])]) > 1:
                kinds["Same test, formulation varied"] += 1
            elif len(bp[r["论文"]]) > 1:
                kinds["Same paper, across tests"] += 1
            else:
                kinds["Between papers only"] += 1
        kinds["Not near room temperature"] = len(a) - len(m)
        tot.update(kinds); tot[EN[c]] = len(a); tot["313 papers · main layer"] += len(a)
        for k, colr in (("Same test, formulation varied", "rgba(42,120,214,0.55)"), ("Same paper, across tests", "rgba(159,179,200,0.6)"),
                        ("Between papers only", "rgba(235,104,52,0.45)"), ("Not near room temperature", "rgba(200,200,200,0.5)")):
            if kinds[k]:
                src.append(idx[EN[c]]); tgt.append(idx[k]); val.append(kinds[k]); col.append(colr)
                hov.append(f"{EN[c]} → {k}: {kinds[k]} measurements")
    ncol = [D.INK] + [D.INK] * 4 + [BLUE, D.MUTED, D.ORANGE, "#c9c9c9"]
    fig = go.Figure(go.Sankey(arrangement="snap", node=dict(label=[f"{n} · {tot[n]}" for n in nodes], color=ncol, pad=18, thickness=18, line=dict(width=0)),
                              link=dict(source=src, target=tgt, value=val, color=col, customdata=hov, hovertemplate="%{customdata}<extra></extra>")))
    D.layout(fig, "How the pooled analysis is fed · width = measurements · blue = information that is free of lab differences (same test)", 520)
    write(fig, "图M1_数据流桑基.html")
    return dict(tot)


# ---------------- M2 证据网络 ----------------
def axis_positions():
    n = len(AXN)
    hub = {a: (math.cos(math.pi / 2 - 2 * math.pi * i / n), math.sin(math.pi / 2 - 2 * math.pi * i / n)) for i, a in enumerate(AXN)}
    sat = {}
    for a, (x, y) in hub.items():
        mem = AX[a]["成员"]
        base = math.atan2(y, x)
        step = 0.42 if len(mem) > 3 else 0.8
        for k, d in enumerate(mem):
            ang = base + (k - (len(mem) - 1) / 2) * step
            sat[d] = (x + 0.30 * math.cos(ang), y + 0.30 * math.sin(ang))
    perf = {"LiCu_CE": (-0.54, 0.0), "全电池CE": (-0.18, 0.0), "每圈衰减率": (0.18, 0.0), "首圈容量": (0.54, 0.0)}  # 顺序让主要连线最短、不穿过别的方块
    return hub, sat, perf


PERF2 = {"首圈容量": "Initial<br>capacity", "每圈衰减率": "Fade per<br>cycle", "全电池CE": "Full-cell<br>CE", "LiCu_CE": "Li‖Cu<br>CE"}


def fig_network():
    import plotly.graph_objects as go
    hub, sat, perf = axis_positions()
    fig = go.Figure()
    ov = V3["重叠"]
    # 轴之间的重叠：成员跨轴 |ρ| ≥ 0.5
    cross = defaultdict(list)
    for pr in ov["|ρ|≥0.5 的对"]:
        a, b = F.AXIS_OF.get(pr["a"]), F.AXIS_OF.get(pr["b"])
        if a and b and a != b:
            cross[tuple(sorted((a, b)))].append(pr)
    for (a, b), prs in cross.items():
        (x0, y0), (x1, y1) = hub[a], hub[b]
        txt = "<br>".join(f"{LAB[p['a']]} ~ {LAB[p['b']]}: ρ = {p['ρ']:+.2f}" for p in prs)
        fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines", line=dict(color=D.ORANGE, width=2, dash="dash"), opacity=0.8,
                                 hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=[(x0 + x1) / 2], y=[(y0 + y1) / 2], mode="markers", marker=dict(size=12, color=D.ORANGE, opacity=0.01), showlegend=False,
                                 hovertext=f"<b>Overlap between axes</b><br>{txt}", hoverinfo="text"))
    # 轴 → 性能：联合模型同测试效应；联合模型没放进的轴用单描述符结果（细虚线）
    for c in CL:
        j = V3["去重叠联合"][c]
        for a in AXN:
            rep = AX[a]["代表"]
            if not rep:
                continue
            if rep in j["代表"]:
                e = j["结果"][rep]["同测试"]; src = f"joint model ({j['测量']} measurements / {j['论文']} papers)"
                sig = e["p"] < 0.05; joint = True
            else:
                s = V3["单描述符"][c].get(rep, {})
                if s.get("状态") != "已估计":
                    continue
                e = s["同测试"]; src = "single-descriptor model (not separable from other axes here)"
                sig = e.get("q", 1) < 0.1; joint = False
            m = lnx(e)
            if not sig and abs(m) < 0.15:
                continue
            (x0, y0), (x1, y1) = hub[a], perf[c]
            colr = BLUE if m > 0 else RED
            fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines", hoverinfo="skip", showlegend=False,
                                     line=dict(color=colr, width=(1.5 + 11 * min(abs(m), 1.0)) if sig and joint else 2.5 if sig else 1.5,
                                               dash="solid" if sig and joint else "dot" if not sig else "dash"),
                                     opacity=0.85 if sig else 0.35))
            fig.add_trace(go.Scatter(x=[x0 * 0.45 + x1 * 0.55], y=[y0 * 0.45 + y1 * 0.55], mode="markers", marker=dict(size=14, opacity=0.01),
                                     showlegend=False, hoverinfo="text",
                                     hovertext=f"<b>{a} → {EN[c]}</b><br>representative: {LAB[rep]}<br>same-test effect ×{e['倍数_每1SD']:.2f} per SD "
                                               f"(95% CI ×{e['区间'][0]:.2f}–×{e['区间'][1]:.2f})<br>{src}" + ("" if sig else "<br>not significant")))
    # 卫星：成员描述符
    for a in AXN:
        for d in AX[a]["成员"]:
            (x0, y0), (x1, y1) = hub[a], sat[d]
            fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines", line=dict(color=ACOL[a], width=1.2), opacity=0.6, hoverinfo="skip", showlegend=False))
    for a in AXN:
        mem = AX[a]["成员"]
        hov = []
        for d in mem:
            rows = []
            for c in CL:
                s = V3["单描述符"][c].get(d, {})
                if s.get("状态") == "已估计":
                    t = s["同测试"]
                    rows.append(f"{EN[c]}: ×{t['倍数_每1SD']:.2f}{' *' if t['q'] < 0.1 else ''} (same test, {s['同测试有变化的论文']} papers)")
            hov.append(f"<b>{LAB[d]}</b> · {a}<br>" + ("<br>".join(rows) if rows else "too few papers vary it") + "<br>* q < 0.1")
        side = ["middle right" if sat[d][0] > hub[a][0] + 0.03 else "middle left" if sat[d][0] < hub[a][0] - 0.03 else "top center" for d in mem]
        fig.add_trace(go.Scatter(x=[sat[d][0] for d in mem], y=[sat[d][1] for d in mem], mode="markers+text", text=[LAB[d] for d in mem],
                                 textposition=side, textfont=dict(size=10, color="#5b6f72"),
                                 marker=dict(size=9, color=ACOL[a], line=dict(width=1, color="white")), hovertext=hov, hoverinfo="text", showlegend=False))
    fig.add_trace(go.Scatter(x=[hub[a][0] for a in AXN], y=[hub[a][1] for a in AXN], mode="markers+text", text=[f"<b>{a}</b>" for a in AXN],
                             textposition="top center", textfont=dict(size=12, color=D.INK),
                             marker=dict(size=30, color=[ACOL[a] for a in AXN], line=dict(width=2, color="white")),
                             hovertext=[f"<b>{a}</b><br>members: {', '.join(LAB[d] for d in AX[a]['成员'])}<br>representative: "
                                        f"{LAB[AX[a]['代表']] if AX[a]['代表'] else '—'}" for a in AXN], hoverinfo="text", showlegend=False))
    fig.add_trace(go.Scatter(x=[perf[c][0] for c in CL], y=[perf[c][1] for c in CL], mode="markers+text", text=[PERF2[c] for c in CL],
                             textposition="middle center", textfont=dict(size=11, color="white"), marker=dict(size=64, color=D.INK, symbol="square"),
                             hovertext=[f"{EN[c]}: {V3['覆盖'][c]['测量']} measurements, {V3['覆盖'][c]['论文']} papers" for c in CL], hoverinfo="text", showlegend=False))
    for lab, colr, dash in (("better (solid = joint model, p < 0.05)", BLUE, "solid"), ("worse", RED, "solid"),
                            ("significant alone, not separable", BLUE, "dash"), ("overlap between axes (|ρ| ≥ 0.5)", D.ORANGE, "dash")):
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color=colr, width=3, dash=dash), name=lab))
    fig.update_xaxes(visible=False, range=[-1.75, 1.75]); fig.update_yaxes(visible=False, range=[-1.45, 1.45], scaleanchor="x")
    D.layout(fig, "Meta evidence network · 6 descriptor axes (data-defined, |ρ| ≥ 0.5) → 4 metrics · line width = same-test effect per SD", 860,
             legend=dict(orientation="h", y=-0.02, x=0))
    write(fig, "图M2_证据网络.html")


# ---------------- M3 论文—轴网络 ----------------
def fig_papers(M):
    import plotly.graph_objects as go
    import networkx as nx
    hub, _, _ = axis_positions()
    judge = {k: u.get("判定") for k, u in W["矛盾单元"].items() if u.get("判定")}
    reason_p = {}
    for k, j in judge.items():
        reason_p.setdefault(k.split("|")[2], D.reason_of(j.get("归类", "")))
    rc = dict(zip([r for r, _ in D.REASON], D.REASON_COLORS))
    # 汇总方向：联合模型同测试 p < 0.05，否则单描述符 q < 0.1
    pooled = {}
    for c in CL:
        j = V3["去重叠联合"][c]
        for a in AXN:
            rep = AX[a]["代表"]
            if not rep:
                continue
            if rep in j["代表"] and j["结果"][rep]["同测试"]["p"] < 0.05:
                pooled[(c, a)] = np.sign(j["结果"][rep]["同测试"]["β"])
            else:
                s = V3["单描述符"][c].get(rep, {})
                if s.get("状态") == "已估计" and s["同测试"]["q"] < 0.1:
                    pooled[(c, a)] = np.sign(s["同测试"]["β"])
    # 每篇论文、每条轴：同一测试里换配方的方向
    edges = defaultdict(list); nmeas = Counter()
    by = defaultdict(list)
    for r in M:
        by[(r["类别"], r["论文"], r["测试"])].append(r); nmeas[r["论文"]] += 1
    for (c, p, t), rows in by.items():
        if len({r["recipe"] for r in rows}) < 2:
            continue
        y = np.array([r["y"] for r in rows])
        for a in AXN:
            rep = AX[a]["代表"]
            if not rep:
                continue
            x = np.array([r["D"].get(rep) if r["D"].get(rep) is not None else np.nan for r in rows])
            ok = ~np.isnan(x)
            if ok.sum() < 2 or np.std(x[ok]) < 1e-9:
                continue
            cov = float(np.mean((x[ok] - x[ok].mean()) * (y[ok] - y[ok].mean())))
            edges[(p, a)].append(np.sign(cov) * pooled[(c, a)] if (c, a) in pooled and cov != 0 else None)
    G = nx.Graph()
    for (p, a) in edges:
        G.add_edge(p, a)
    pos = nx.spring_layout(G, pos={a: np.array(hub[a]) * 1.1 for a in AXN}, fixed=AXN, k=0.12, iterations=300, seed=5)
    fig = go.Figure()
    kinds = {"agree": ("#9fb3c8", "same direction as the pooled effect"), "opposite": (RED, "against the pooled effect"),
             "mixed": ("#eda100", "mixed"), "none": ("#dedbd4", "no pooled direction for this axis")}
    def kind(v):
        v = [x for x in v if x is not None]
        return "none" if not v else "agree" if np.mean(v) > 0.33 else "opposite" if np.mean(v) < -0.33 else "mixed"
    cnt = Counter(kind(v) for v in edges.values())
    for k, (colr, lab) in kinds.items():
        xs, ys = [], []
        for (p, a), v in edges.items():
            if kind(v) == k:
                xs += [pos[p][0], pos[a][0], None]; ys += [pos[p][1], pos[a][1], None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=colr, width=1.8 if k == "opposite" else 0.9),
                                 opacity=0.9 if k == "opposite" else 0.55, name=f"{lab} ({cnt[k]})", hoverinfo="skip"))
    papers = sorted({p for p, _ in edges})
    for lab in [None] + [r for r, _ in D.REASON]:
        ps = [p for p in papers if reason_p.get(p) == lab]
        if not ps:
            continue
        fig.add_trace(go.Scatter(x=[pos[p][0] for p in ps], y=[pos[p][1] for p in ps], mode="markers",
                                 name="Paper" if lab is None else f"Paper · contradiction read: {lab}",
                                 marker=dict(size=[5 + 1.3 * math.sqrt(nmeas[p]) for p in ps], color="#c9d3d6" if lab is None else rc[lab],
                                             line=dict(width=0.7, color="white")),
                                 hovertext=[f"<b>{p}</b> · {nmeas[p]} measurements<br>axes varied in the same test: "
                                            + ", ".join(f"{a} ({kind(edges[(p, a)])})" for a in AXN if (p, a) in edges)
                                            + ("" if lab is None else f"<br>contradiction read: {lab}") for p in ps], hoverinfo="text"))
    fig.add_trace(go.Scatter(x=[pos[a][0] for a in AXN if a in pos], y=[pos[a][1] for a in AXN if a in pos], mode="markers+text",
                             text=[f"<b>{a}</b>" for a in AXN if a in pos], textposition="top center", textfont=dict(size=12, color=D.INK),
                             marker=dict(size=28, color=[ACOL[a] for a in AXN if a in pos], symbol="diamond", line=dict(width=2, color=D.INK)),
                             name="Descriptor axis", hoverinfo="text",
                             hovertext=[f"<b>{a}</b><br>{sum(1 for (p, b) in edges if b == a)} papers vary it within a test" for a in AXN if a in pos]))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False, scaleanchor="x")
    D.layout(fig, f"Paper–axis network · {len(papers)} papers linked to the descriptor axes they changed within one test · red = that paper runs against the pooled effect",
             900, legend=dict(orientation="v", x=1.01, y=1))
    write(fig, "图M3_论文与描述符轴网络.html")
    return {"论文": len(papers), "连线": dict(cnt)}


# ---------------- M4 三层效应热图 ----------------
def fig_heat():
    import plotly.graph_objects as go
    rows = [d for a in AXN for d in AX[a]["成员"]]
    cols = [(c, lev) for c in CL for lev in ("同测试", "篇间")]
    z, txt, hov = [], [], []
    for d in rows:
        zr, tr, hr = [], [], []
        for c, lev in cols:
            s = V3["单描述符"][c].get(d, {})
            if s.get("状态") != "已估计":
                zr.append(None); tr.append(""); hr.append(f"{LAB[d]} · {EN[c]}<br>too few papers vary it")
                continue
            e = s[lev]
            sig = (e.get("q", 1) < 0.1) if lev == "同测试" else e["p"] < 0.05
            m = lnx(e)
            zr.append(max(-1, min(1, m)) * (1 if sig else D.PALE))
            tr.append(f"<b>×{e['倍数_每1SD']:.2f}</b>" if sig else f"×{e['倍数_每1SD']:.2f}")
            hr.append(f"<b>{LAB[d]} · {EN[c]} · {'same test' if lev == '同测试' else 'between papers'}</b><br>×{e['倍数_每1SD']:.2f} per SD "
                      f"(95% CI ×{e['区间'][0]:.2f}–×{e['区间'][1]:.2f}), " + (f"q = {e['q']:.3f}" if lev == "同测试" else f"p = {e['p']:.3f}")
                      + f"<br>{s['测量']} measurements · {s['论文']} papers · varied within a test in {s['同测试有变化的论文']} papers"
                      + f"<br>verdict: {VERD_EN.get(s.get('判断'), s.get('判断'))}")
        z.append(zr); txt.append(tr); hov.append(hr)
    ylab = [f"{F.AXIS_OF[d]} · {LAB[d]}{' ★' if AX[F.AXIS_OF[d]]['代表'] == d else ''}" for d in rows]
    xlab = [f"{EN[c]}<br>{'same test' if lev == '同测试' else 'between papers'}" for c, lev in cols]
    fig = go.Figure(go.Heatmap(z=z, x=xlab, y=ylab, text=txt, texttemplate="%{text}", hovertext=hov, hoverinfo="text", colorscale=D.DIVERGE, zmid=0,
                               zmin=-1, zmax=1, xgap=2, ygap=2, colorbar=dict(title="ln × per SD", tickvals=[-0.8, 0, 0.8], ticktext=["worse", "0", "better"])))
    for i in range(1, len(CL)):
        fig.add_vline(x=2 * i - 0.5, line=dict(color="white", width=6))
    fig.update_yaxes(autorange="reversed")
    D.layout(fig, "Every descriptor, two kinds of evidence · strong colour + bold = significant (same test: q < 0.1; between papers: p < 0.05) · ★ = axis representative",
             130 + 30 * len(rows), plot_bgcolor="#e6ebea", margin=dict(l=20, r=20, t=70, b=60))
    write(fig, "图M4_三层效应热图.html")


VERD_EN = {"同测试不显著": "not significant within a test", "同测试与篇间同向且都显著": "same test and between papers agree, both significant",
           "同测试显著、篇间同向": "significant within a test; between papers same direction", "同测试显著、篇间反向": "significant within a test; between papers opposite"}
CHANGE_AXIS = {"改浓度/配比": "Salt amount", "高浓": "Salt amount", "换主盐": "Salt amount", "局部高浓": "Fluorination & dilution",
               "加/换氟化醚": "Fluorination & dilution", "换溶剂（其他）": "Coordination (ether O)", "LiNO₃ 用量": "LiNO₃",
               "加有机硫": "Other additives", "加介体": "Other additives", "加含碘添加剂": "Other additives", "加其他添加剂": "Other additives",
               "组成不明": "Composition unclear"}
M5_AXES = ["Coordination (ether O)", "Fluorination & dilution", "Salt amount", "LiNO₃", "Other additives", "Composition unclear"]
VERD_SHORT = {"✅": "Confirmed in source", "🔶": "Lead (partly explained)", "⚠️": "Data or grouping issue"}


# ---------------- M5 矛盾归因桑基 ----------------
def fig_contra():
    import plotly.graph_objects as go
    U = W["矛盾单元"]
    reasons = [r for r, _ in D.REASON]
    nodes = [EN[c] for c in CL] + [f"{a} " for a in M5_AXES] + reasons + list(VERD_SHORT.values())
    idx = {n: i for i, n in enumerate(nodes)}
    flows = Counter(); ex = defaultdict(list)
    for k, u in U.items():
        c, g, p = k.split("|")
        j = u.get("判定") or {}
        a = CHANGE_AXIS.get(g, "Other additives") + " "
        r = D.reason_of(j.get("归类", ""))
        r = r if r in idx else "Genuine effect"
        v = VERD_SHORT.get(j.get("判定"), "Data or grouping issue")
        for s, t in ((EN[c], a), (a, r), (r, v)):
            flows[(s, t)] += 1; ex[(s, t)].append(p)
    rc = dict(zip(reasons, D.REASON_COLORS))
    def lcol(s, t):
        h = rc.get(t) or rc.get(s) or ACOL.get(s.strip()) or "#9fb3c8"
        h = h.lstrip("#"); return f"rgba({int(h[:2], 16)},{int(h[2:4], 16)},{int(h[4:], 16)},0.45)"
    src = [idx[s] for s, _ in flows]; tgt = [idx[t] for _, t in flows]; val = list(flows.values())
    cd = [f"{s.strip()} → {t.strip()}: {n} cases<br>{', '.join(sorted(set(ex[(s, t)]))[:12])}" for (s, t), n in flows.items()]
    ncol = [D.INK] * 4 + [ACOL.get(a, "#6250d6" if a == "Other additives" else "#9aa6a8") for a in M5_AXES] + [rc[r] for r in reasons] + ["#1baf7a", "#eda100", "#d03b3b"]
    fig = go.Figure(go.Sankey(arrangement="snap", node=dict(label=[n.strip() for n in nodes], color=ncol, pad=14, thickness=16, line=dict(width=0)),
                              link=dict(source=src, target=tgt, value=val, color=[lcol(s, t) for s, t in flows], customdata=cd,
                                        hovertemplate="%{customdata}<extra></extra>")))
    D.layout(fig, f"Where the {len(U)} apparent contradictions come from · metric → descriptor axis of the change → reason found in the source → verdict", 640)
    write(fig, "图M5_矛盾归因桑基.html")


def main():
    M, _ = F.load()
    flow = fig_flow(M)
    fig_network()
    st = fig_papers(M)
    fig_heat()
    fig_contra()
    old = FIG / "图M1_实验室差异与电解液效应.html"
    if old.exists():
        shutil.copyfile(old, FIG / "图M6_同一电解液跨实验室.html")
    (F.OUT / "网站图统计.json").write_text(json.dumps({"论文—轴网络": st, "数据流": flow}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("论文—轴网络", st)


if __name__ == "__main__":
    main()
