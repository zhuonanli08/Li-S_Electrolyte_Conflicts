"""网站 07 页的矛盾图（11-08 用户同意）：只放与三个无定论问题有关的图，图英文、悬停英文。

图 7a–7c 说法地图（每个问题一张）：一个点 = 一篇论文的一条机制说法（step20 选出的那条）。横轴 = 发表年份（缺的按编号推断，标 ~）；
  上下两条带 = 两派立场（来自 step20 读原文的判断，不来自向量）；带内上下位置 = 文字向量（step21，bge-small-zh）的第一主成分，话题相近的说法高度相近；
  灰线 = 两派之间话题最相近的说法（每条说法连到对方派里最相近的一条，只画相似度 ≥ 两派之间相似度 75 分位的）；中线 = 相关但不站队（C）。
  实心 = 作者结论，空心 = 作者推测或转述；★ = 发现这个矛盾的反例论文。
图 7d、7e 方向图（问题 1、2）：一个点 = 一对同测试比较（计票时的一票）；横轴 = 描述符差（A − B），纵轴 = 性能变化（A 相对 B，ln，正 = 变好；
  CE 用损失比的倒数，衰减用每圈衰减率之比的倒数）；与共识同向的落在两个“agree”象限，反例落在另两个象限，按读原文结果上色。
图 7f 交叉图（问题 3）：左 = P112 盐浓度 × LiNO₃；右 = 313 篇里只改主盐浓度的 Li‖Cu CE 比较，按低盐一侧（参照）含不含 LiNO₃ 上色。
输入：step17/18/20/21 的输出、两两比较表述 v2、配方组成（经 step16）。输出：网站 图/ 下 图7a…图7f_*.html，汇总写 output/说法地图_313篇_2026-11-08/图07汇总.json。
初步；立场与读原文结果是 AI 辅助，用户尚未逐项人工确认。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/fig07_tension_figures.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "step15_meta"))
import step17_tension_trial as T
import step16_pairwise_statements as P16
import D_site as D

O = ROOT / "output"
VEC = O / "说法地图_313篇_2026-11-08" / "说法向量.json"
PAIRS = O / "两两比较表述_313篇_v2_2026-11-07" / "比较表述.json"
JUD = [O / "张力判定_313篇_2026-11-07" / "判定_v2.json", O / "张力判定_313篇_2026-11-07" / "判定_v2_弱.json"]
FIG = D.SITE_FIG
INK, MUTED = D.INK, "#9fb3c8"
SIDE_COL = {"A": "#2a78d6", "B": "#eb6834", "C": "#8a8984"}
RESULT = {"比较不对等": ("Unequal comparison", "#eb6834"), "数据问题": ("Data issue", "#eda100"), "待定": ("Pending", "#e87ba4"),
          "已知条件": ("Already-known condition", "#6250d6"), "真张力候选": ("Genuine-tension candidate", "#172d32")}
SRC_EN = {"本文结论": "author's conclusion", "本文结论（与他文一致）": "author's conclusion (agrees with others)",
          "本文推测": "author's speculation", "转述他文或通用说法": "citing others / general statement"}
Q = {  # 问题 → (标题, A 派英文, B 派英文, 反例论文)
    "T1": ("Open question 1 · Should the diluent decompose?",
           "Diluent / fluorinated solvent itself decomposes to LiF<br>→ good for the Li anode",
           "LiF mainly comes from the anion;<br>the diluent should stay intact", ["P381", "P371"]),
    "T3": ("Open question 2 · How much LiNO₃ is best?",
           "LiNO₃ is consumed on Li and runs out<br>→ more is better",
           "LiNO₃ is reduced irreversibly on the cathode (≲1.7 V)<br>→ too much hurts", ["P111"]),
    "T4": ("Open question 3 · High salt and LiNO₃: substitutes or complements?",
           "The Li anode can be stabilised<br>without LiNO₃ (weak solvation, F, organic SEI)",
           "LiNO₃ protection cannot be replaced", ["P112"]),
}
summary = {}


def write(fig, name):
    fig.write_html(FIG / name, include_plotlyjs="directory", full_html=True, config={"displaylogo": False})
    pv = __import__("os").environ.get("FIG_PREVIEW_DIR")  # 设了就另存图 JSON，供 textvec 环境导出 PNG 目测（只用于检查排版）
    if pv:
        Path(pv).mkdir(parents=True, exist_ok=True)
        def plain(o):  # numpy 数组转普通列表（plotly 7 的 JSON 会把数组编码成 bdata，旧版读不出）
            if isinstance(o, dict):
                return {k: plain(v) for k, v in o.items()}
            if isinstance(o, (list, tuple)):
                return [plain(v) for v in o]
            if isinstance(o, np.ndarray):
                return plain(o.tolist())
            if isinstance(o, np.generic):
                return o.item()
            return o
        (Path(pv) / (Path(name).stem + ".json")).write_text(json.dumps(plain(fig.to_dict()), ensure_ascii=False), encoding="utf-8")


# ---------------- 说法地图 ----------------
def claim_map(t, letter):
    import plotly.graph_objects as go
    title, la, lb, cex = Q[t]
    C = [c for c in json.loads(VEC.read_text(encoding="utf-8"))["说法"] if c["问题"] == t]
    V = np.array([c["向量"] for c in C])
    Vc = V - V.mean(0)
    pc1 = np.linalg.svd(Vc, full_matrices=False)[2][0]
    off = Vc @ pc1
    off = off / (np.abs(off).max() or 1)
    band = {"A": 1.0, "B": -1.0, "C": 0.0}
    # 同一年的点左右错开，避免重叠
    xs = np.array([c["年份"] for c in C], float)
    for y in set(xs):
        ii = [i for i in range(len(C)) if xs[i] == y]
        for k, i in enumerate(sorted(ii, key=lambda i: (C[i]["立场"], off[i]))):
            xs[i] = y + (k - (len(ii) - 1) / 2) * 0.16
    ys = np.array([band[c["立场"]] + (0.38 if c["立场"] != "C" else 0.18) * off[i] for i, c in enumerate(C)])
    S = V @ V.T
    A_ = [i for i, c in enumerate(C) if c["立场"] == "A"]
    B_ = [i for i, c in enumerate(C) if c["立场"] == "B"]
    cross = np.array([S[i, j] for i in A_ for j in B_])
    th = float(np.percentile(cross, 75)) if len(cross) else 1.0
    # 11-08：每条说法连到对方派里最相近的一条，且对方也把它排在前两名、相似度 ≥ 75 分位（避免一条泛泛的说法连出一大把线）
    links = set()
    for a_, b_ in ((A_, B_), (B_, A_)):
        for i in a_:
            if not b_:
                continue
            j = max(b_, key=lambda j: S[i, j])
            top2 = sorted(a_, key=lambda k: -S[j, k])[:2]
            if S[i, j] >= th and i in top2:
                links.add((min(i, j), max(i, j)))
    fig = go.Figure()
    for i, j in sorted(links):
        fig.add_trace(go.Scatter(x=[xs[i], xs[j]], y=[ys[i], ys[j]], mode="lines", showlegend=False, hoverinfo="skip",
                                 line=dict(color="#b8b7b2", width=1 + 4 * (S[i, j] - th) / max(1e-6, cross.max() - th)), opacity=0.7))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color="#b8b7b2", width=3),
                             name="same topic, opposite sides (text similarity)"))
    for s in "ABC":
        for concl in (True, False):
            ii = [i for i, c in enumerate(C) if c["立场"] == s and c["论文"] not in cex and (c["来源类型"] in ("本文结论", "本文结论（与他文一致）")) == concl]
            if not ii:
                continue
            col = SIDE_COL[s]
            fig.add_trace(go.Scatter(
                x=xs[ii], y=ys[ii], mode="markers+text", text=[C[i]["论文"] for i in ii], textposition="top center",
                textfont=dict(size=10, color=INK), showlegend=False,
                marker=dict(size=13 if s != "C" else 10, symbol="circle" if s != "C" else "diamond",
                            color=col if concl else "white", line=dict(color=col, width=2)),
                hovertext=[f"<b>{C[i]['论文']}</b> · {'~' if C[i]['年份是推断'] else ''}{C[i]['年份']} · mechanism {C[i]['机制']}<br>"
                           f"{SRC_EN.get(C[i]['来源类型'], C[i]['来源类型'])}" for i in ii], hoverinfo="text"))
    ii = [i for i, c in enumerate(C) if c["论文"] in cex]
    if ii:
        fig.add_trace(go.Scatter(x=xs[ii], y=ys[ii], mode="markers+text", text=[f"<b>{C[i]['论文']}</b>" for i in ii], textposition="bottom center",
                                 textfont=dict(size=11, color=INK), name="counterexample paper that revealed the tension",
                                 marker=dict(size=22, symbol="star", color=[SIDE_COL[C[i]["立场"]] for i in ii], line=dict(color=INK, width=1.5)),
                                 hovertext=[f"<b>{C[i]['论文']}</b> · {C[i]['年份']} · mechanism {C[i]['机制']}" for i in ii], hoverinfo="text"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(size=11, color="#52514e"), name="filled = author's conclusion"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(size=11, color="white", line=dict(color="#52514e", width=2)),
                             name="open = speculation / citing others"))
    x0, x1 = xs.min() - 0.8, xs.max() + 0.8
    for s, y, lab in (("A", 1.0, la), ("B", -1.0, lb)):
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y - 0.5, y1=y + 0.5, fillcolor=SIDE_COL[s], opacity=0.06, line_width=0, layer="below")
        n = sum(c["立场"] == s for c in C)
        fig.add_annotation(xref="paper", x=-0.01, y=y, xanchor="right", yanchor="middle", showarrow=False, align="right",
                           text=f"<b>{lab}</b><br>({n} papers)", font=dict(size=11.5, color=SIDE_COL[s]))
    if any(c["立场"] == "C" for c in C):
        fig.add_annotation(xref="paper", x=-0.01, y=0.0, xanchor="right", showarrow=False, align="right",
                           text="related,<br>not taking a side", font=dict(size=10.5, color="#8a8984"))
    fig.update_yaxes(visible=False, range=[-1.6, 1.6])
    fig.update_xaxes(title="Publication year (~ = inferred from paper order)", range=[x0, x1], dtick=1, showgrid=True, gridcolor="#eeeeea")
    D.layout(fig, f"Fig. 7{letter} · Claim map · {title}", 560, legend=dict(orientation="h", y=-0.22, font=dict(size=11)),
             margin=dict(l=300, r=20, t=60, b=110))
    name = f"图7{letter}_说法地图_{t}.html"
    write(fig, name)
    yrs = {s: sorted(c["年份"] for c in C if c["立场"] == s) for s in "AB"}
    summary[name] = {"说法": len(C), "灰线": len(links), "灰线门槛（余弦）": round(th, 3),
                     "年份中位数": {s: (float(np.median(v)) if v else None) for s, v in yrs.items()},
                     "2022 年及以后": {s: sum(y >= 2022 for y in v) for s, v in yrs.items()}}
    return name


# ---------------- 方向图 ----------------
def judged():
    out = {}
    for f in JUD:
        for r in json.loads(f.read_text(encoding="utf-8")):
            for p in r["相反的对"]:
                out[p.split()[0]] = r["真假"]
    return out


def direction(letter, dkey, cls, xlab, ylab, title, cex):
    import plotly.graph_objects as go
    R = json.loads(PAIRS.read_text(encoding="utf-8"))
    res = judged()
    maj = None
    pts = []
    for r in R:
        if r["类别"] != cls or r["比较类型"] != T.SAME:
            continue
        x = next((y for y in r["描述符"] if y["描述符"] == dkey), None)
        if not x:
            continue
        dx, ef = x["A"] - x["B"], T.effect(r)
        pts.append((r, dx, ef))
    votes = [math.copysign(1, dx) * ef for _, dx, ef in pts]
    good, bad = sum(v > T.T for v in votes), sum(v < -T.T for v in votes)
    maj = 1 if good >= bad else -1
    fig = go.Figure()
    xm = max(abs(dx) for _, dx, _ in pts) * 1.08
    ym = max(abs(ef) for _, _, ef in pts) * 1.08
    for sx, sy, agree in ((1, 1, maj > 0), (-1, -1, maj > 0), (1, -1, maj < 0), (-1, 1, maj < 0)):
        fig.add_shape(type="rect", x0=0, x1=sx * xm, y0=0, y1=sy * ym, line_width=0, layer="below",
                      fillcolor="#2a78d6" if agree else "#d03b3b", opacity=0.05)
        fig.add_annotation(x=sx * xm * 0.97, y=sy * ym * 0.97, xanchor="right" if sx > 0 else "left", yanchor="top" if sy > 0 else "bottom",
                           text="agrees with consensus" if agree else "counterexample", showarrow=False, font=dict(size=11, color="#52514e"))
    groups = {}
    for r, dx, ef in pts:
        v = math.copysign(1, dx) * ef * maj
        k = "Agrees with consensus" if v > T.T else "Within ±5% (not counted)" if v >= -T.T else RESULT.get(res.get(r["编号"]), ("Counterexample, not read", "#d03b3b"))[0]
        groups.setdefault(k, []).append((r, dx, ef))
    order = ["Agrees with consensus", "Within ±5% (not counted)"] + [v[0] for v in RESULT.values()] + ["Counterexample, not read"]
    colr = {"Agrees with consensus": MUTED, "Within ±5% (not counted)": "#d9d8d2", **{v[0]: v[1] for v in RESULT.values()}, "Counterexample, not read": "#d03b3b"}
    for k in order:
        if k not in groups:
            continue
        g = groups[k]
        star = k == "Genuine-tension candidate"
        fig.add_trace(go.Scatter(
            x=[dx for _, dx, _ in g], y=[ef for _, _, ef in g], mode="markers+text" if star else "markers", name=f"{k} ({len(g)})",
            text=[r["论文"] for r, _, _ in g] if star else None, textposition="top center", textfont=dict(size=11, color=INK),
            marker=dict(size=18 if star else 9, symbol="star" if star else "circle", color=colr[k], line=dict(color="white" if not star else INK, width=1)),
            hovertext=[f"<b>{r['论文']}</b> · {r['编号']}<br>A: {r['A']['配方名']}<br>B: {r['B']['配方名']}<br>Δ = {dx:+.3g} · "
                       f"{r['性能']['值A']} vs {r['性能']['值B']}" for r, dx, _ in g], hoverinfo="text"))
    fig.add_hline(y=0, line_color="#8a8984", line_width=1)
    fig.add_vline(x=0, line_color="#8a8984", line_width=1)
    fig.update_xaxes(title=xlab, range=[-xm, xm], zeroline=False)
    fig.update_yaxes(title=ylab, range=[-ym, ym], zeroline=False)
    D.layout(fig, f"Fig. 7{letter} · {title} · {len(pts)} same-test comparisons ({good} better : {bad} worse) · each point = one vote",
             560, legend=dict(orientation="v", x=1.01, y=1, font=dict(size=11)), margin=dict(l=60, r=20, t=60, b=50))
    name = f"图7{letter}_方向图.html"
    write(fig, name)
    summary[name] = {"比较": len(pts), "好": good, "差": bad, "各组": {k: len(v) for k, v in groups.items()}}
    return name


# ---------------- 交叉图（问题 3） ----------------
def has_lino3(p, rid):
    c = P16.comps(p, rid) if rid is not None else None
    if not c:
        return None
    i = c.get("LiNO3")
    if i is None:
        return False
    v = i.get("数值")
    return not (isinstance(v, (int, float)) and v == 0)


def cross(letter):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    R = json.loads(PAIRS.read_text(encoding="utf-8"))
    val = {}
    for r in R:
        if r["论文"] == "P112" and r["类别"] == "LiCu_CE":
            for s, k in (("A", "值A"), ("B", "值B")):
                val[r[s]["配方名"]] = r["性能"][k]
    p112 = {("1 M", False): val["1 M LiTFSI DOL/DME"], ("4 M", False): val["4 M LiTFSI DOL/DME"],
            ("1 M", True): val["1 M LiTFSI DOL/DME +0.5 M LiNO3"], ("4 M", True): val["4 M LiTFSI DOL/DME +0.5 M LiNO3"]}
    pts = []
    for r in R:
        if r["类别"] != "LiCu_CE" or r["比较类型"] != T.SAME:
            continue
        ds = {x["描述符"]: x for x in r["描述符"]}
        if "salt" not in ds or len(r.get("作者改动的组分") or []) != 1:
            continue
        x = ds["salt"]
        up = 1 if x["A"] > x["B"] else -1
        lo, hi = (r["B"], r["A"]) if up > 0 else (r["A"], r["B"])
        pts.append({"论文": r["论文"], "编号": r["编号"], "fold": math.log(max(x["A"], x["B"]) / min(x["A"], x["B"])), "效应": up * T.effect(r),
                    "LiNO3": has_lino3(r["论文"], lo["recipe"]), "lo": lo["配方名"], "hi": hi["配方名"],
                    "v": (r["性能"]["值B"], r["性能"]["值A"]) if up > 0 else (r["性能"]["值A"], r["性能"]["值B"])})
    fig = make_subplots(rows=1, cols=2, column_widths=[0.4, 0.6], horizontal_spacing=0.12,
                        subplot_titles=("P112: salt concentration × LiNO₃ (Li‖Cu CE)", "All salt-only comparisons (Li‖Cu CE, same test)"))
    for lino, col, nm in ((False, "#eb6834", "without LiNO₃"), (True, "#2a78d6", "with 0.5 M LiNO₃")):
        fig.add_trace(go.Scatter(x=["1 M", "4 M"], y=[p112[("1 M", lino)], p112[("4 M", lino)]], mode="lines+markers+text", name=f"P112 {nm}",
                                 text=[f"{p112[('1 M', lino)]}%", f"{p112[('4 M', lino)]}%"], textposition="top center",
                                 line=dict(color=col, width=3), marker=dict(size=11, color=col), legendgroup=nm), row=1, col=1)
    for lino, col, nm in ((False, "#eb6834", "reference without LiNO₃"), (True, "#2a78d6", "reference with LiNO₃"), (None, "#8a8984", "LiNO₃ unknown")):
        g = [p for p in pts if p["LiNO3"] is lino]
        if not g:
            continue
        fig.add_trace(go.Scatter(x=[p["fold"] for p in g], y=[p["效应"] for p in g], mode="markers+text", name=f"{nm} ({len(g)})",
                                 text=[p["论文"] for p in g], textposition="middle right", textfont=dict(size=10, color=INK),
                                 marker=dict(size=11, color=col, line=dict(color="white", width=1)),
                                 hovertext=[f"<b>{p['论文']}</b> · {p['编号']}<br>{p['lo']} → {p['hi']}<br>CE {p['v'][0]} → {p['v'][1]} %" for p in g],
                                 hoverinfo="text"), row=1, col=2)
    fig.add_hline(y=0, line_color="#8a8984", line_width=1, row=1, col=2)
    fig.update_yaxes(title="Li‖Cu CE (%)", row=1, col=1)
    fig.update_xaxes(title="Salt concentration", row=1, col=1)
    fig.update_xaxes(title="Salt increase, ln(high / low)", row=1, col=2)
    fig.update_yaxes(title="CE change (ln of loss ratio, + = better)", row=1, col=2)
    D.layout(fig, f"Fig. 7{letter} · Open question 3 · does LiNO₃ make the salt-concentration benefit disappear?", 520,
             legend=dict(orientation="h", y=-0.25, font=dict(size=11)), margin=dict(l=60, r=20, t=80, b=110))
    name = f"图7{letter}_交叉图.html"
    write(fig, name)
    by = {k: [round(p["效应"], 2) for p in pts if p["LiNO3"] is v] for k, v in (("参照无 LiNO3", False), ("参照有 LiNO3", True), ("不明", None))}
    summary[name] = {"P112": {f"{k[0]}{' +LiNO3' if k[1] else ''}": v for k, v in p112.items()}, "只改盐浓度的比较": len(pts),
                     "效应": by, "篇": {k: sorted({p["论文"] for p in pts if p["LiNO3"] is v}) for k, v in (("参照无 LiNO3", False), ("参照有 LiNO3", True))}}
    return name


def main():
    names = [claim_map("T1", "a"), claim_map("T3", "b"), claim_map("T4", "c"),
             direction("d", "ffrac", "LiCu_CE", "Δ fluorinated-solvent fraction (A − B)", "Li‖Cu CE change, A vs B (ln of loss ratio, + = better)",
                       "Open question 1 · fluorinated-solvent fraction vs Li‖Cu CE", ["P381", "P371"]),
             direction("e", "lino3", "每圈衰减率", "Δ LiNO₃ concentration, M (A − B)", "Fade change, A vs B (ln of fade-rate ratio, + = slower fade)",
                       "Open question 2 · LiNO₃ concentration vs fade per cycle", ["P111"]),
             cross("f")]
    (O / "说法地图_313篇_2026-11-08" / "图07汇总.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
