"""step15 D：结果网站“Meta & attribution”页的数据与图（11-06 用户要求：先确认用了全部数据、一张图展示多重信息又易读，再上网站）。

数据：第 0 步 v2（meta共同准备_313篇_v2_2026-11-06：修了归因读原文发现的问题），全部 313 篇（开发＋考试）。两次考试已做完，
展示用的效应估计用全部论文；考试成绩仍是 v1 上事先登记、只算一次的那一次（记分卡里照原样列出）。
内容（都用方案 A 的两步估计：岭回归扣条件差 → 论文随机效应；跨温度 >10 °C 的比较不用）：
  ① 数据流：每类论文、测量、三种比较的数量与剔除原因；
  ② 同一电解液跨实验室的差别 vs 同一测试里换电解液的差别（标准醚各篇平均值；同测试比较）；
  ③ 16 个描述符 × 4 类性能的效应热图（方案 A 全部数据；悬停给区间、q、方向稳定折数、方案 B 是否同向）；
  ④ 权衡图（横轴容量，纵轴衰减率 / Li‖Cu CE；形状 = 机制组，实心 = 至少一项 q < 0.1）；
  ⑤ 按组成定义统一方向后的改动倍数（全部比较 vs 只同测试；悬停给篇数、同向比例、留一篇误差）；
  ⑥ 矛盾候选的原因（读原文判定，归 7 类）；
  ⑦ 预测检验记分卡（读各方案已有的开发集与考试结果文件，不重算）。
用法：python -X utf8 D_site.py compute   （算数，写 output/meta网站_313篇_2026-11-06/网站数据.json；列出还没读原文的矛盾候选）
      python -X utf8 D_site.py figs      （画图到网站 图/ 目录）
"""
import sys
import json
import math
import copy
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import A_meta as A
import B_normalize as B
import C_attribution as C
from mm import fit_mixed, bh

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
V2 = ROOT / "output" / "meta共同准备_313篇_v2_2026-11-06"
OUT = ROOT / "output" / "meta网站_313篇_2026-11-06"
SITE_FIG = ROOT / "output" / "表述与矛盾试跑_F版30篇_2026-11-04" / "网站" / "图"
A.IN = V2
B.IN = V2
CLASSES = A.CLASSES
EN_CLASS = {"首圈容量": "Initial capacity", "每圈衰减率": "Fade per cycle", "全电池CE": "Full-cell CE", "LiCu_CE": "Li‖Cu CE"}
EN_Y = {"首圈容量": "capacity ratio", "每圈衰减率": "1 / fade-rate ratio", "全电池CE": "1 / CE-loss ratio", "LiCu_CE": "1 / CE-loss ratio"}
EN_DESC = {"ln_配位位点每Li": "Coordinating sites per Li⁺ (ln)", "ln_Li总浓度": "Li⁺ concentration (ln)", "稀释剂摩尔比例": "Diluent mole fraction",
           "醚氧数": "Ether O per solvent", "sO_β氟化醚": "β-fluorinated ether O", "sO_α氟化醚": "α-fluorinated ether O",
           "溶剂_含氟分子比例": "Fluorinated-solvent fraction", "F/O": "F/O ratio", "aF": "Anion F (aF)", "LiNO3_M": "LiNO₃ (M)",
           "有机硫": "Organosulfur", "介体": "Redox mediator", "含碘": "Iodide", "溶剂_环醚比例": "Cyclic-ether fraction",
           "溶剂_碳酸酯比例": "Carbonate fraction", "可旋转键数": "Rotatable bonds"}
EN_GROUP = {"G1 溶剂化/配位": "Solvation", "G2 氟化": "Fluorination", "G3 阴离子": "Anion", "G4 添加剂": "Additive", "G5 溶剂骨架": "Backbone"}
EN_ORIENT = {"改浓度/配比": "Salt concentration up", "高浓": "Salt concentration up (HCE)", "换溶剂（其他）": "More coordinating solvent",
             "加/换氟化醚": "More fluorinated solvent", "局部高浓": "More diluent (LHCE)", "LiNO₃ 用量": "More LiNO₃",
             "加有机硫": "Add organosulfur", "加介体": "Add redox mediator"}
EN_PAIR = {"同测试、不同配方": "same test", "跨测试、不同配方": "across tests", "同配方、换条件": "same formulation, new conditions"}
# 读原文判定的归类 → 网站 7 类（第一个写的归类是主要原因）
REASON = [("Test conditions differ", ("条件不同", "取值点不同")), ("Another change mixed in", ("混了别的改动",)),
          ("Reference unusually weak or strong", ("参照很弱或很强",)), ("No defined direction, or sides swapped", ("改动方向不同", "实验/对照方向标反")),
          ("Data or grouping error", ("归组或提取问题",)), ("Metric artefact or within noise", ("指标放大", "指标问题", "差异小于噪声")),
          ("Genuine effect", ("真实大效应", "真实机制差异", "符合描述符趋势"))]
NOTE = "初步、未裁定；AI 辅助，用户尚未逐项人工确认"


def reason_of(cat):
    first = cat.split("；")[0]
    for en, keys in REASON:
        if any(k in first for k in keys):
            return en
    return "Other"


def jdump(path, obj):
    def conv(o):
        if isinstance(o, (np.floating, np.integer, np.bool_)):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=conv), encoding="utf-8")


# ---------------- 计算 ----------------
def compute():
    OUT.mkdir(parents=True, exist_ok=True)
    P, M, drop = A.load()
    for q in P:
        q["划分"] = "开发"  # 展示用全部论文：A 的函数只认“开发”
    Mall = copy.deepcopy(M)
    for r in Mall:
        r["划分"] = "开发"
    summ0 = json.loads((V2 / "汇总.json").read_text(encoding="utf-8"))
    std_ether = {(r["论文"], r["表述"]): float(r["标准醚"]) for r in M}
    ST = {s["表述编号"]: s for s in json.loads(C.STF.read_text(encoding="utf-8"))}
    judge = json.loads(C.JUDGE.read_text(encoding="utf-8")) if C.JUDGE.exists() else {}
    res = {"说明": NOTE, "数据": "第 0 步 v2，全部 313 篇（开发＋考试）", "数据流": {}, "实验室差异": {}, "描述符": {}, "改动倍数": [],
           "矛盾候选": [], "调节因素": [], "方案B方向": {}}
    BM, _ = B.load()
    for cls in CLASSES:
        Pc = [q for q in P if q["类别"] == cls]
        Mc = [r for r in M if r["类别"] == cls]
        res["数据流"][cls] = {"测量点": len(Mc), "测量论文": len({r["论文"] for r in Mc}), "比较": dict(Counter(q["配对类型"] for q in Pc)),
                            "比较论文": len({q["论文"] for q in Pc}), "跨温度剔除": drop[cls], "测量剔除": summ0["剔除计数"].get(cls, {}),
                            "标记": summ0["标记计数"].get(cls, {})}
        # ② 实验室差异
        by = defaultdict(list)
        for r in Mc:
            if r["标准醚"]:
                by[r["论文"]].append(r["y"])
        se = {p: float(np.mean(v)) for p, v in by.items()}
        med = float(np.median(list(se.values()))) if se else None
        st = [q for q in Pc if q["配对类型"] == "同测试、不同配方"]
        res["实验室差异"][cls] = {"标准醚各篇": [{"论文": p, "相对中位数_ln": v - med} for p, v in sorted(se.items())],
                              "同测试换电解液": [{"论文": q["论文"], "实验": q["实验配方"], "参照": q["参照配方"], "dy": q["dy"]} for q in st]}
        # ③ 描述符（A 两步估计，全部数据）
        g1 = A.stage1(Pc, cls)
        res["描述符"][cls] = A.screen(Pc, Mall, cls, g1)
        # 方案 B 方向（交叉随机效应，全部数据）
        R = [r for r in BM if r["类别"] == cls]
        g = B.G().fit(R, cls)
        ystd = np.array([r["y"] for r in R]) - g(R)[0]
        res["方案B方向"][cls] = {e["描述符"]: (math.log(e["倍数_每1SD"]) if e.get("状态") == "已估计" else None) for e in B.screen_b(R, ystd, cls)}
        # ⑤ 改动倍数、⑥ 矛盾候选、调节因素
        groups = defaultdict(list)
        for q in Pc:
            if q["配对类型"] != "同配方、换条件":
                groups[q["主改动"]].append(q)
        res["改动倍数"] += C.c5(groups, cls, g1)
        res["矛盾候选"] += C.c3(groups, cls, g1, std_ether, ST)
        res["调节因素"] += C.c1(Pc, cls, g1, std_ether)[0]
        print(f"{cls}: 测量 {len(Mc)}，比较 {len(Pc)}（{res['数据流'][cls]['比较论文']} 篇）", flush=True)
    units = {}
    for r in res["矛盾候选"]:
        units.setdefault(f"{r['类别']}|{r['主改动']}|{r['论文']}", []).append(r)
    res["矛盾单元"] = {k: {"类型": v[0]["类型"], "本组合并倍数": v[0]["本组合并倍数"], "本篇平均倍数": v[0]["本篇平均倍数"], "比较": len(v),
                         "判定": judge.get(k)} for k, v in units.items()}
    todo = [k for k in units if k not in judge]
    gone = [k for k in judge if k not in units]
    res["未判"] = todo
    res["记分卡"] = scorecard()
    res["v1 判过但 v2 不再是候选"] = gone
    KEEP = ("类别", "主改动", "论文", "类型", "本组合并倍数", "本篇平均倍数", "这一比较倍数", "实验表述", "参照表述", "配对类型", "全部改动", "标记")
    res["矛盾候选"] = [{k: r[k] for k in KEEP} for r in res["矛盾候选"]]  # 入库的版本不带原文句子（版权；仓库公开）
    jdump(OUT / "网站数据.json", res)
    jdump(OUT / "待读矛盾候选.json", {k: units[k] for k in todo})
    print(f"\n矛盾单元 {len(units)}，已判 {len(units) - len(todo)}，待读 {len(todo)}；v1 判过、v2 不再是候选 {len(gone)}")
    for k in todo:
        print("  待读", k)
    for k in gone:
        print("  不再是候选", k)


# ---------------- 记分卡（读已有结果文件，不重算） ----------------
def scorecard():
    o = ROOT / "output"
    rd = lambda p: json.loads(p.read_text(encoding="utf-8"))
    s14 = rd(o / "改动模型_313篇_2026-11-05" / "考试结果.json")["类别"]
    s14d = rd(o / "改动模型_去圈数_313篇_2026-11-06" / "考试结果.json")["类别"]["每圈衰减率"]
    cfg14 = rd(o / "改动模型_313篇_2026-11-05" / "选定配置.json")
    cfg14d = rd(o / "改动模型_去圈数_313篇_2026-11-06" / "选定配置.json")["每圈衰减率"]
    a_dev = rd(o / "方案A_meta回归_313篇_2026-11-06" / "A5_开发集验证.json")["结果"]
    a_ex = rd(o / "方案A_meta回归_313篇_2026-11-06" / "考试结果.json")["类别"]
    a_reg = rd(o / "方案A_meta回归_313篇_2026-11-06" / "预先登记.json")["A4选中描述符"]
    b_dev = rd(o / "方案B_归一化_313篇_2026-11-06" / "B4_开发集验证.json")["锚点预测"]
    b_ex = rd(o / "方案B_归一化_313篇_2026-11-06" / "考试结果.json")["类别"]
    rows = []
    for c in CLASSES:
        if c == "每圈衰减率":
            s = {"开发": cfg14d["开发集R2"], "考试": s14d["总体"], "区间": s14d["总体95%区间"], "备注": "re-examined after removing the cycle-count leak (2nd use of the test set); 1st result 0.32 included the leak"}
        else:
            s = {"开发": cfg14[c]["开发集R2"], "考试": s14[c]["总体"], "区间": s14[c]["总体95%区间"],
                 "备注": "selected from a stale record (on current data this configuration scores −0.54 on the dev set)" if c == "全电池CE" else ""}
        a_ok = lambda ev: ev.get("A4−只用条件 篇内排序一致率差 95%区间") and ev["A4−只用条件 篇内排序一致率差 95%区间"][0] is not None and ev["A4−只用条件 篇内排序一致率差 95%区间"][0] > 0
        b = lambda ev: (ev.get("完整", {}).get("均方误差"), ev.get("与锚点相同", {}).get("均方误差"), ev.get("完整−与锚点相同 均方误差差 95%区间"))
        rows.append({"类别": c, "改动模型": s,
                     "方案A": {"描述符": a_reg[c], "开发": [a_dev[c]["A4"]["篇内排序一致率"], a_dev[c]["只用条件"]["篇内排序一致率"]],
                              "考试": [a_ex[c]["A4"]["篇内排序一致率"], a_ex[c]["只用条件"]["篇内排序一致率"]],
                              "开发通过": bool(a_reg[c]) and bool(a_ok(a_dev[c])), "考试通过": bool(a_reg[c]) and bool(a_ok(a_ex[c]))},
                     "方案B": {"开发": b(b_dev[c]), "考试": b(b_ex[c]),
                              "开发通过": bool(b(b_dev[c])[2] and b(b_dev[c])[2][1] is not None and b(b_dev[c])[2][1] < 0),
                              "考试通过": bool(b(b_ex[c])[2] and b(b_ex[c])[2][1] is not None and b(b_ex[c])[2][1] < 0)}})
    return rows


# ---------------- 图（plotly，英文，离线；配色经 palette_check 校验） ----------------
XMIN, XMAX, TICKS = 0.05, 30.0, [0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20]
BLUE, ORANGE, MUTED, INK = "#2a78d6", "#eb6834", "#9fb3c8", "#172d32"
REASON_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]  # 7 色相邻校验通过；对比度偏低，图上直接标数字
SYMBOLS = {"Solvation": "circle", "Fluorination": "diamond", "Anion": "square", "Additive": "triangle-up", "Backbone": "x"}
FONT = dict(family="Segoe UI, Arial, sans-serif", size=12, color=INK)
PALE = 0.3  # 不显著格子的颜色只取 30% 强度
DIVERGE = [[0, "#d03b3b"], [0.5, "#f0efec"], [1, "#2a78d6"]]  # 默认发散对：红（变差）— 灰 — 蓝（变好）


def layout(fig, title, height, **kw):
    kw.setdefault("margin", dict(l=20, r=20, t=70, b=40))
    fig.update_layout(title=dict(text=title, x=0.01, xanchor="left", font=dict(size=15)), template="plotly_white", height=height, font=FONT,
                      hoverlabel=dict(bgcolor="white", font_size=12), **kw)


def write(fig, name):
    fig.write_html(SITE_FIG / name, include_plotlyjs="directory", full_html=True, config={"displaylogo": False})


def fig_spread(d):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.06, subplot_titles=[EN_CLASS[c] for c in CLASSES])
    rng = np.random.default_rng(1)
    for i, c in enumerate(CLASSES, 1):
        se = d["实验室差异"][c]["标准醚各篇"]; st = d["实验室差异"][c]["同测试换电解液"]
        for k, (lab, vals, col, hov, yv) in enumerate((
                ("Same electrolyte (standard ether), different papers", [math.exp(x["相对中位数_ln"]) for x in se], BLUE,
                 [f"{x['论文']}: ×{math.exp(x['相对中位数_ln']):.2f} vs. the median paper" for x in se], 1),
                ("Electrolyte changed, same test in one paper", [math.exp(x["dy"]) for x in st], ORANGE,
                 [f"{x['论文']} {x['实验']} vs {x['参照']}: ×{math.exp(x['dy']):.2f}" for x in st], 0))):
            if not vals:
                continue
            lo, hi = np.percentile(vals, [10, 90])
            xs = [min(max(v, XMIN), XMAX) for v in vals]  # 超出范围的画在边上（三角形），悬停给真实值
            sym = ["triangle-right" if v > XMAX else "triangle-left" if v < XMIN else "circle" for v in vals]
            fig.add_trace(go.Scatter(x=xs, y=yv + rng.uniform(-0.18, 0.18, len(vals)), mode="markers", name=lab, legendgroup=lab, showlegend=i == 1,
                                     marker=dict(size=8, color=col, opacity=0.75, symbol=sym, line=dict(width=1, color="white")), text=hov, hoverinfo="text"),
                          row=i, col=1)
            fig.add_shape(type="line", x0=max(lo, XMIN), x1=min(hi, XMAX), y0=yv + 0.34, y1=yv + 0.34, line=dict(color=col, width=3), row=i, col=1)
            fig.add_annotation(xref="paper", x=1.0, y=yv, text=f"middle 80%: ×{lo:.2f}–×{hi:.2f}<br>n = {len(vals)}", showarrow=False, xanchor="left",
                               align="left", font=dict(size=11, color=INK), yref=f"y{'' if i == 1 else i}")
        fig.update_yaxes(showticklabels=False, range=[-0.6, 1.7], row=i, col=1)
    fig.update_xaxes(type="log", range=[math.log10(XMIN), math.log10(XMAX)], tickvals=TICKS, ticktext=[f"×{t:g}" for t in TICKS])
    fig.update_xaxes(title_text="Performance relative to the comparison (×, log scale; 1 = no difference; triangles = beyond the axis)", row=4, col=1)
    for i in range(1, 5):
        fig.add_vline(x=1, line=dict(color="#8a9a9c", width=1), row=i, col=1)
    layout(fig, "Lab-to-lab spread of one electrolyte vs. the effect of changing the electrolyte", 940,
           legend=dict(orientation="h", y=1.075, x=0), margin=dict(l=20, r=170, t=110, b=40))
    write(fig, "图M1_实验室差异与电解液效应.html")


def fig_heat(d):
    import plotly.graph_objects as go
    rows = [x for g in A.DESC.values() for x in g
            if any(next(e for e in d["描述符"][c] if e["描述符"] == x).get("标准化效应_ln") is not None for c in CLASSES)]
    z, text, hov = [], [], []
    for dsc in rows:
        zr, tr, hr = [], [], []
        for c in CLASSES:
            e = next(e for e in d["描述符"][c] if e["描述符"] == dsc)
            bdir = (d["方案B方向"].get(c) or {}).get(dsc)
            if e.get("状态") != "已估计" or e.get("标准化效应_ln") is None:
                zr.append(None); tr.append(""); hr.append(f"{EN_DESC[dsc]} · {EN_CLASS[c]}<br>not enough data ({e.get('Δ≠0 的论文', 0)} papers change it)")
                continue
            m = e["标准化效应_ln"]; sig = e["q"] is not None and e["q"] < 0.1
            zr.append(max(-0.6, min(0.6, m)) * (1 if sig else PALE))  # 颜色深浅 = 是否显著；格子里的数字是真实点估计
            tr.append(f"<b>×{math.exp(m):.2f}</b>" if sig else f"×{math.exp(m):.2f}")
            agree = "—" if bdir is None else ("same direction" if np.sign(bdir) == np.sign(m) else "opposite direction")
            hr.append(f"<b>{EN_DESC[dsc]} · {EN_CLASS[c]}</b><br>effect per 1 SD: ×{math.exp(m):.2f} "
                      f"(95% CI ×{e['倍数95%区间'][0]:.2f}–×{e['倍数95%区间'][1]:.2f})<br>q = {e['q']:.3f}{' · significant' if sig else ''}"
                      f"<br>papers where it changes: {e['Δ≠0 的论文']} · comparisons: {e['比较数']}<br>direction stable in {e['方向稳定']} folds"
                      f"<br>absolute-value check (plan B): {agree}")
        z.append(zr); text.append(tr); hov.append(hr)
    ylab = [f"{EN_GROUP[A.GROUP_OF[x]]} · {EN_DESC[x]}" for x in rows]
    fig = go.Figure(go.Heatmap(z=z, x=[EN_CLASS[c] for c in CLASSES], y=ylab, text=text, texttemplate="%{text}", hovertext=hov, hoverinfo="text",
                               colorscale=DIVERGE, zmid=0, zmin=-0.6, zmax=0.6, xgap=2, ygap=2,
                               colorbar=dict(title="ln × per SD", tickvals=[-0.5, 0, 0.5], ticktext=["worse", "0", "better"])))
    fig.update_yaxes(autorange="reversed")
    layout(fig, "Which molecular descriptors move which performance · strong colour + bold = significant (q < 0.1); pale = direction only; grey = not enough data", 700,
           plot_bgcolor="#e6ebea")
    write(fig, "图M2_描述符效应热图.html")


def fig_tradeoff(d):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.09,
                        subplot_titles=["Capacity vs. fade per cycle", "Capacity vs. Li‖Cu CE"])
    shown = set()
    for col, cy in ((1, "每圈衰减率"), (2, "LiCu_CE")):
        for dsc in [x for g in A.DESC.values() for x in g]:
            ex = next(e for e in d["描述符"]["首圈容量"] if e["描述符"] == dsc)
            ey = next(e for e in d["描述符"][cy] if e["描述符"] == dsc)
            if ex.get("标准化效应_ln") is None or ey.get("标准化效应_ln") is None:
                continue
            x, y = ex["标准化效应_ln"], ey["标准化效应_ln"]
            sig = (ex["q"] or 1) < 0.1 or (ey["q"] or 1) < 0.1
            grp = EN_GROUP[A.GROUP_OF[dsc]]
            key = (grp, sig)
            fig.add_trace(go.Scatter(
                x=[x], y=[y], mode="markers+text" if sig else "markers", text=[EN_DESC[dsc]] if sig else None, textposition="top center",
                textfont=dict(size=11, color=INK),
                error_x=dict(type="data", array=[1.96 * ex["SE"] * ex["描述符标准差"]], color="#c9d3d6", thickness=1),
                error_y=dict(type="data", array=[1.96 * ey["SE"] * ey["描述符标准差"]], color="#c9d3d6", thickness=1),
                marker=dict(symbol=SYMBOLS[grp], size=11, color=BLUE if sig else MUTED, line=dict(width=1, color="white")),
                name=grp, showlegend=False,
                hovertext=f"<b>{EN_DESC[dsc]}</b> ({grp})<br>capacity ×{math.exp(x):.2f} per SD (q {ex['q']:.3f})<br>"
                          f"{EN_CLASS[cy]} ×{math.exp(y):.2f} per SD (q {ey['q']:.3f})", hoverinfo="text"), row=1, col=col)
            shown.add(key)
        fig.add_hline(y=0, line=dict(color="#8a9a9c", width=1), row=1, col=col)
        fig.add_vline(x=0, line=dict(color="#8a9a9c", width=1), row=1, col=col)
        fig.update_xaxes(title_text="Effect on initial capacity (ln × per SD)", zeroline=False, row=1, col=col)
        fig.update_yaxes(title_text=f"Effect on {EN_CLASS[cy]} (ln × per SD, up = better)", zeroline=False, row=1, col=col)
        for xa, ya, t in ((0.98, 0.98, "both better"), (0.02, 0.02, "both worse"), (0.02, 0.98, "trade-off"), (0.98, 0.02, "trade-off")):
            fig.add_annotation(xref=f"x{'' if col == 1 else 2} domain", yref=f"y{'' if col == 1 else 2} domain", x=xa, y=ya, text=t, showarrow=False,
                               xanchor="right" if xa > 0.5 else "left", yanchor="top" if ya > 0.5 else "bottom", font=dict(size=11, color="#62777a"))
    for grp, sym in SYMBOLS.items():  # 图例：形状 = 机制组；蓝色 = 至少一个轴显著
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=grp, marker=dict(symbol=sym, size=11, color=MUTED)), row=1, col=1)
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="significant (q < 0.1) on at least one axis", marker=dict(size=11, color=BLUE)), row=1, col=1)
    layout(fig, "Trade-off map: each point is one descriptor (shape = mechanism group; blue = significant for at least one axis)", 620,
           legend=dict(orientation="h", y=-0.18, x=0))
    write(fig, "图M3_权衡图.html")


def fig_strategy(d):
    import plotly.graph_objects as go
    rows = [r for r in d["改动倍数"] if "合并倍数" in r.get("定向", {}) or "合并倍数" in r.get("定向＋只同测试", {})]
    rows.sort(key=lambda r: (CLASSES.index(r["类别"]), r["主改动"]))
    ylab = [f"{EN_CLASS[r['类别']]} · {EN_ORIENT.get(r['主改动'], r['主改动'])}" for r in rows]
    fig = go.Figure()
    for k, lab, col, off in (("定向", "All within-paper comparisons, direction aligned", BLUE, -0.17),
                             ("定向＋只同测试", "Same-test comparisons only", ORANGE, 0.17)):
        xs, lo, hi, ys, hov = [], [], [], [], []
        for j, r in enumerate(rows):
            v = r.get(k, {})
            if "合并倍数" not in v:
                continue
            xs.append(v["合并倍数"]); lo.append(v["合并倍数"] - v["95%区间"][0]); hi.append(v["95%区间"][1] - v["合并倍数"]); ys.append(j + off)
            raw = r.get("原始", {})
            rawtxt = (f"<br>before aligning direction: ×{raw['合并倍数']:.2f}, error {raw['留一篇误差_RMSE_ln']:.2f}" if "合并倍数" in raw else "")
            hov.append(f"<b>{ylab[j]}</b><br>{lab}<br>×{v['合并倍数']:.2f} (95% CI ×{v['95%区间'][0]:.2f}–×{v['95%区间'][1]:.2f})"
                       f"<br>{v['论文']} papers, {v['比较']} comparisons · {v['方向一致比例']:.0%} of papers agree in direction"
                       f"<br>leave-one-paper-out error {v['留一篇误差_RMSE_ln']:.2f} (ln){rawtxt}")
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", name=lab, marker=dict(size=10, color=col, line=dict(width=2, color="white")),
                                 error_x=dict(type="data", symmetric=False, array=hi, arrayminus=lo, color=col, thickness=1.6),
                                 hovertext=hov, hoverinfo="text"))
    for j, r in enumerate(rows):
        v = r.get("定向＋只同测试", {}) if "合并倍数" in r.get("定向＋只同测试", {}) else r.get("定向", {})
        fig.add_annotation(x=1, y=j, xref="paper", text=f"{v['论文']} papers · {v['方向一致比例']:.0%} agree", showarrow=False, xanchor="left",
                           font=dict(size=11, color="#62777a"))
    fig.add_vline(x=1, line=dict(color="#8a9a9c", width=1))
    fig.update_yaxes(tickvals=list(range(len(rows))), ticktext=ylab, autorange="reversed")
    fig.update_xaxes(type="log", tickvals=TICKS, ticktext=[f"×{t:g}" for t in TICKS],
                     title_text="Pooled multiplier vs. the paper's own reference (×, log; >1 = better; condition differences removed)")
    layout(fig, "Effect of each change after aligning its direction (by composition only)", 120 + 46 * len(rows),
           legend=dict(orientation="h", y=1.04, x=0), margin=dict(l=20, r=170, t=80, b=40))
    write(fig, "图M4_改动倍数.html")


def fig_reasons(d):
    import plotly.graph_objects as go
    U = d["矛盾单元"]
    cnt = {c: Counter() for c in CLASSES}
    who = defaultdict(list)
    verd = {c: Counter() for c in CLASSES}
    for k, u in U.items():
        c = k.split("|")[0]
        j = u.get("判定")
        if not j:
            continue
        r = reason_of(j["归类"])
        cnt[c][r] += 1
        who[(c, r)].append(k.split("|")[2])
        verd[c][j["判定"]] += 1
    fig = go.Figure()
    for (en, _), col in zip(REASON, REASON_COLORS):
        xs = [cnt[c][en] for c in CLASSES]
        fig.add_trace(go.Bar(y=[EN_CLASS[c] for c in CLASSES], x=xs, name=en, orientation="h", marker=dict(color=col, line=dict(color="white", width=2)),
                             text=[str(x) if x >= 2 else "" for x in xs], textposition="inside", insidetextanchor="middle",
                             hovertext=[f"<b>{en}</b><br>{EN_CLASS[c]}: {cnt[c][en]}<br>papers: {', '.join(sorted(set(who[(c, en)])))}" for c in CLASSES],
                             hoverinfo="text"))
    for c in CLASSES:
        n = sum(cnt[c].values())
        fig.add_annotation(x=n, y=EN_CLASS[c], text=f"  {n} read: {verd[c]['✅']} clear · {verd[c]['🔶']} lead · {verd[c]['⚠️']} data issue", showarrow=False, xanchor="left",
                           font=dict(size=11, color="#62777a"))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title_text="Contradiction candidates read against the source text (main reason of each)")
    layout(fig, "Why papers seem to disagree: a paper whose result runs against the pooled direction, or is >3× off it", 460,
           legend=dict(orientation="h", y=-0.25, x=0, traceorder="normal"), margin=dict(l=20, r=230, t=70, b=40))
    write(fig, "图M5_矛盾原因.html")


def figs():
    d = json.loads((OUT / "网站数据.json").read_text(encoding="utf-8"))
    fig_spread(d); fig_heat(d); fig_tradeoff(d); fig_strategy(d); fig_reasons(d)
    print("图已写到", SITE_FIG)


if __name__ == "__main__":
    if sys.argv[1:2] == ["compute"]:
        compute()
    elif sys.argv[1:2] == ["figs"]:
        figs()
