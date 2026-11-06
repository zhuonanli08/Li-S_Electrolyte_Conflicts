"""step15 E：可信度检验（11-06 用户同意“试试”：借鉴已发表的文献数据分析，检查我们的结论站不站得住）。

① 外部对照：Kim 等 2023（PNAS 120:e2214357120）用 150 个 Li‖Cu CE 数据拟合的线性模型（正文 Model Verification and Analysis 节）
   LCE = −4.481 sO + 0.052 F/O + 0.188 InOr − 13.460 aC + 2.112，LCE = −log10(1 − CE)。
   特征定义与本项目 step12d 相同（sO = 溶剂带来的 O ÷ 全部原子，aC = 阴离子带来的 C ÷ 全部原子，F/O，InOr = 除 C、H、Li 外的原子 ÷ C），
   取自 表述.json 的 元素比例。用它预测我们每个 Li‖Cu 篇内比较两边的差，和实测差比较。我们的 y = −ln(100 − CE%)，所以 Δy = ln10 × ΔLCE。
   指标：符号一致率（按比较、按论文等权；对照基线 = “新电解液总是更好”）、Spearman、校准斜率（论文随机截距；1 = 完全吻合）。
   Kim 的数据有一部分来自文献，可能和我们的论文重叠（他们 SI 表 S1 未核对），所以这是“方向是否一致”的对照，不是严格独立验证。
   另：4 个特征各自在我们篇内比较里的方向是否与 Kim 系数同号；每个 Li⁺ 配位位点数与 sO 的相关。
② 联合模型：Li‖Cu 的配位位点、Li⁺ 浓度、含氟溶剂比例放进同一个模型（同一批比较），与单独估比较，报 VIF；
   再把配位位点换成 sO（Kim 认为氟的作用可能被溶剂含氧量吸收）；再加稀释剂比例、LiNO₃。容量：配位位点、Li⁺ 浓度、碳酸酯比例。
   估计方法与方案 A 相同：岭回归扣条件差 → 论文随机截距；跨温度 > 10 °C 的比较不用；用全部 313 篇（同网站 05 页）。
③ 报告完整度（借鉴 Bird 等 2024，ACS Mater. Lett. 6:5363）：主层测试（Li‖S＋硫碳正极）与 Li‖Cu 测试，各条件字段
   “写明且可用 / 写了但没解析出 / 没写（含按默认值补的）”的比例，按测试和按论文；论文 × 字段热图按编号（年份顺序）排。
只读第 0 步 v2 与 表述.json；结果写到 output/可信度检验_313篇_2026-11-06/（汇总.json、图/）。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 E_credibility.py
"""
import sys
import json
import math
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
import A_meta as A
import C_attribution as C
import D_site as D
from mm import boot_by_paper, bh

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
OUT = ROOT / "output" / "可信度检验_313篇_2026-11-06"
FIG = OUT / "图"
LN10 = math.log(10)
KIM = {"sO": -4.481, "F/O": 0.052, "InOr": 0.188, "aC": -13.460}
KIM0 = 2.112
CN = {"ln_配位位点每Li": "每个 Li⁺ 的配位位点（对数）", "ln_Li总浓度": "Li⁺ 浓度（对数）", "溶剂_含氟分子比例": "含氟溶剂比例",
      "稀释剂摩尔比例": "稀释剂比例", "LiNO3_M": "LiNO₃ 浓度", "溶剂_碳酸酯比例": "碳酸酯比例", "sO": "溶剂含氧比例 sO",
      "F/O": "F/O", "InOr": "无机/有机 InOr", "aC": "阴离子含碳比例 aC"}
CLS_CN = {"首圈容量": "首圈容量", "LiCu_CE": "Li‖Cu CE"}


def jdump(path, obj):
    def conv(o):
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=conv), encoding="utf-8")


def load():
    P, M, _ = A.load()
    for q in P:
        q["划分"] = "开发"  # 同网站 05 页：两次考试已做完，展示用全部论文
    for r in M:
        r["划分"] = "开发"
    ST = {s["表述编号"]: s for s in json.loads(C.STF.read_text(encoding="utf-8"))}
    for r in M:  # Kim 的 4 个特征补进测量表描述符
        er = ST[r["表述"]].get("元素比例") or {}
        for k in KIM:
            r["描述符"][k] = er.get(k)
    for q in P:
        e, f = ST[q["实验"]].get("元素比例") or {}, ST[q["参照"]].get("元素比例") or {}
        for k in KIM:
            if q["配对类型"] == "同配方、换条件":
                q["Δ描述符"][k] = 0.0
            else:
                q["Δ描述符"][k] = e[k] - f[k] if e.get(k) is not None and f.get(k) is not None else None
        ok = all(e.get(k) is not None for k in KIM) and all(f.get(k) is not None for k in KIM)
        q["Kim预测Δy"] = LN10 * sum(c * (e[k] - f[k]) for k, c in KIM.items()) if ok else None
    return P, M, ST


# ---------------- ① Kim 外部对照 ----------------
def kim_check(P, M):
    cls = "LiCu_CE"
    Pc = [q for q in P if q["类别"] == cls]
    g1 = A.stage1(Pc, cls)
    res = {"说明": "Kim 等 2023 线性模型预测篇内两边之差 vs 我们的实测差（Δy = −ln(100−CE%) 之差 = ln10 × ΔLCE）"}
    for name, sel in (("同测试", lambda q: q["配对类型"] == "同测试、不同配方"),
                      ("全部不同配方（扣条件差）", lambda q: q["配对类型"] != "同配方、换条件")):
        R = [q for q in Pc if sel(q) and q["Kim预测Δy"] is not None]
        if not R:
            continue
        pred = np.array([q["Kim预测Δy"] for q in R])
        obs = A.dys(R) - (A.offset(g1, R, cls) if name.startswith("全部") else 0.0)
        pap = np.array(A.papers(R))
        keep = np.abs(pred) > 0.05  # Kim 预测几乎没差别的不算符号
        idx_by = defaultdict(list)
        for i, p in enumerate(pap):
            idx_by[p].append(i)

        def agree(ps, base=False):
            hit = []
            for p in ps:
                ii = [i for i in idx_by[p] if keep[i] and obs[i] != 0]
                if ii:
                    s = np.sign(np.ones(len(ii))) if base else np.sign(pred[ii])
                    hit.append(float(np.mean(s == np.sign(obs[ii]))))
            return float(np.mean(hit)) if hit else None

        def rho(ps):
            ii = [i for p in ps for i in idx_by[p]]
            return stats.spearmanr(pred[ii], obs[ii])[0] if len(set(pred[ii])) > 2 else None

        ii = [i for i in range(len(R)) if keep[i] and obs[i] != 0]
        fit = A.mixed(R, obs, [pred], ["Kim预测Δy"])
        j = fit["names"].index("Kim预测Δy")
        b, se = float(fit["b"][j]), float(fit["se"][j])
        res[name] = {"比较": len(R), "论文": len(set(pap)), "算符号的比较": len(ii),
                     "符号一致率_按比较": float(np.mean(np.sign(pred[ii]) == np.sign(obs[ii]))),
                     "符号一致率_论文等权": agree(sorted(idx_by)), "区间": boot_by_paper(agree, list(pap)),
                     "基线_新电解液总是更好_论文等权": agree(sorted(idx_by), True),
                     "基线区间": boot_by_paper(lambda ps: agree(ps, True), list(pap)),
                     "Kim预测为正的比例": float(np.mean(pred[ii] > 0)), "实测为正的比例": float(np.mean(obs[ii] > 0)),
                     "Spearman": float(stats.spearmanr(pred, obs)[0]), "Spearman区间": boot_by_paper(rho, list(pap)),
                     "校准斜率": b, "校准斜率区间": [b - 1.96 * se, b + 1.96 * se], "校准斜率p": float(fit["p"][j]), "方法": fit["方法"],
                     "点": [{"论文": q["论文"], "实验": q["实验配方"], "参照": q["参照配方"], "Kim预测": float(pred[i]), "实测": float(obs[i])}
                           for i, q in enumerate(R)]}
    # 4 个特征各自的篇内方向（方案 A 的单描述符筛查写法）
    feat = []
    for k, c in KIM.items():
        R = [q for q in Pc if q["Δ描述符"][k] is not None]
        nzp = {q["论文"] for q in R if abs(q["Δ描述符"][k]) > 1e-9}
        ya = A.dys(R) - A.offset(g1, R, cls)
        fit = A.mixed(R, ya, [A.diffrec(R), A.dd(R, k)], ["不同配方", "Δ" + k])
        j = fit["names"].index("Δ" + k)
        sd = A.sd_desc(M, cls, k)
        b, se = float(fit["b"][j]), float(fit["se"][j])
        feat.append({"特征": k, "Kim系数": c, "我们的β": b, "p": float(fit["p"][j]), "倍数_每1SD": math.exp(b * sd),
                     "倍数区间": [math.exp((b - 1.96 * se) * sd), math.exp((b + 1.96 * se) * sd)], "Δ≠0的论文": len(nzp),
                     "与Kim同号": bool(np.sign(b) == np.sign(c))})
    for f, qq in zip(feat, bh([f["p"] for f in feat])):  # 4 个特征的 BH 校正
        f["q"] = float(qq)
    res["四个特征各自的方向"] = feat
    # 配位位点数与 sO 的相关（按配方去重）
    seen = {}
    for r in M:
        d = r["描述符"]
        if d.get("ln_配位位点每Li") is not None and d.get("sO") is not None:
            seen[(r["论文"], r["recipe"], r["类别"] == cls)] = (d["ln_配位位点每Li"], d["sO"], r["类别"] == cls)
    for lab, flt in (("Li‖Cu 配方", lambda v: v[2]), ("全部配方", lambda v: True)):
        v = [x for x in seen.values() if flt(x)]
        res[f"配位位点与sO相关_{lab}"] = {"配方": len(v), "Spearman": float(stats.spearmanr([a for a, _, _ in v], [b for _, b, _ in v])[0])}
    return res


# ---------------- ② 联合模型 ----------------
def vif(X):
    out = []
    for i in range(X.shape[1]):
        y, Z = X[:, i], np.column_stack([np.ones(len(X)), np.delete(X, i, axis=1)])
        beta, *_ = np.linalg.lstsq(Z, y, rcond=None)
        r2 = 1 - np.sum((y - Z @ beta) ** 2) / np.sum((y - y.mean()) ** 2)
        out.append(float(1 / (1 - r2)) if r2 < 1 else float("inf"))
    return out


def joint(P, M):
    sets = {"LiCu_CE": [("主模型：位点＋浓度＋含氟", ["ln_配位位点每Li", "ln_Li总浓度", "溶剂_含氟分子比例"]),
                        ("位点换成 sO", ["sO", "ln_Li总浓度", "溶剂_含氟分子比例"]),
                        ("再加稀释剂、LiNO₃", ["ln_配位位点每Li", "ln_Li总浓度", "溶剂_含氟分子比例", "稀释剂摩尔比例", "LiNO3_M"])],
            "首圈容量": [("主模型：位点＋浓度＋碳酸酯", ["ln_配位位点每Li", "ln_Li总浓度", "溶剂_碳酸酯比例"])]}
    res = {}
    for cls, models in sets.items():
        Pc = [q for q in P if q["类别"] == cls]
        g1 = A.stage1(Pc, cls)
        out = []
        for title, ds in models:
            R = [q for q in Pc if all(q["Δ描述符"][d] is not None for d in ds)]
            ya = A.dys(R) - A.offset(g1, R, cls)
            fit = A.mixed(R, ya, [A.diffrec(R)] + [A.dd(R, d) for d in ds], ["不同配方"] + ["Δ" + d for d in ds])
            Xd = np.column_stack([A.dd(R, d) for d in ds])
            diff = A.diffrec(R) > 0
            v = vif(Xd[diff])
            rows = []
            for d, vv in zip(ds, v):
                sd = A.sd_desc(M, cls, d)
                one = A.mixed(R, ya, [A.diffrec(R), A.dd(R, d)], ["不同配方", "Δ" + d])  # 同一批比较上单独估
                cell = {}
                for lab, f in (("联合", fit), ("单独", one)):
                    if "Δ" + d not in f["names"]:
                        cell[lab] = None; continue
                    j = f["names"].index("Δ" + d)
                    b, se = float(f["b"][j]), float(f["se"][j])
                    cell[lab] = {"倍数_每1SD": math.exp(b * sd), "区间": [math.exp((b - 1.96 * se) * sd), math.exp((b + 1.96 * se) * sd)],
                                 "p": float(f["p"][j])}
                nzp = len({q["论文"] for q in R if abs(q["Δ描述符"][d]) > 1e-9})
                rows.append({"描述符": d, "VIF": vv, "描述符标准差": sd, "Δ≠0的论文": nzp, **cell})
            cor = np.corrcoef(Xd[diff].T).tolist() if Xd[diff].shape[0] > 2 else None
            out.append({"模型": title, "比较": len(R), "论文": len({q['论文'] for q in R}), "方法": fit["方法"], "结果": rows,
                        "Δ描述符相关矩阵_不同配方": cor, "描述符": ds})
        res[cls] = out
    return res


# ---------------- ③ 报告完整度 ----------------
OKS = {"✅", "🔶", "⚠️"}
PARTIAL = {"有文字未解析", "冲突或多值", "缺浆料配比", "缺复合物含硫", "本配方未单列"}
FIELDS = {"主层": [("ES", "E/S"), ("sulfur_loading", "硫面载量"), ("S_content", "正极含硫量"), ("rate", "倍率"), ("temperature", "温度"),
                  ("cell_format", "电池形式"), ("Li_thickness", "锂片厚度"), ("NP", "N/P 比")],
          "Li‖Cu": [("current", "电流密度"), ("Li_Cu_capacity", "沉积面容量"), ("temperature", "温度"), ("cell_format", "电池形式"),
                    ("Li_thickness", "锂片厚度")]}


def level(c):
    if not c or c.get("状态") in (None, "未报告") or c.get("默认"):
        return 0  # 没写，或按默认值补（如温度按室温 25 °C）
    return 2 if c["状态"] in OKS else 1 if c["状态"] in PARTIAL else 0


def completeness(ST):
    import common as CM
    bad = CM.BAD_PAPERS
    res = {}
    for layer, fields in FIELDS.items():
        tests = defaultdict(dict)
        for s in ST.values():
            if s["论文"] in bad:
                continue
            if layer == "主层" and not (s["电池类型"] == "Li‖S" and s["正极类型"] == "硫碳类"):
                continue
            if layer == "Li‖Cu" and s["电池类型"] != "Li‖Cu":
                continue
            t = tests[(s["论文"], s["测试"])]
            for f, _ in fields:
                t[f] = max(t.get(f, 0), level(s["条件"].get(f)))
        papers = sorted({p for p, _ in tests})
        by_paper = {p: {f: [t[f] for (pp, _), t in tests.items() if pp == p] for f, _ in fields} for p in papers}
        summ = []
        for f, lab in fields:
            lv = [t[f] for t in tests.values()]
            summ.append({"字段": f, "中文": lab, "测试数": len(lv),
                         "写明且可用_测试": sum(x == 2 for x in lv) / len(lv), "写了没解析出_测试": sum(x == 1 for x in lv) / len(lv),
                         "没写_测试": sum(x == 0 for x in lv) / len(lv),
                         "至少一个测试写明的论文": sum(max(by_paper[p][f]) >= 1 for p in papers) / len(papers)})
        # 按编号三等分（编号按发表年份排）
        third = np.array_split(np.array(papers), 3)
        trend = [{"段": f"{seg[0]}–{seg[-1]}", "论文": len(seg),
                  **{f: float(np.mean([max(by_paper[p][f]) >= 1 for p in seg])) for f, _ in fields}} for seg in third]
        res[layer] = {"测试": len(tests), "论文": len(papers), "字段": summ, "按编号三段": trend,
                      "热图": {"论文": papers, "字段": [lab for _, lab in fields],
                             "写明比例": [[float(np.mean([x >= 1 for x in by_paper[p][f]])) for f, _ in fields] for p in papers],
                             "可用比例": [[float(np.mean([x == 2 for x in by_paper[p][f]])) for f, _ in fields] for p in papers],
                             "测试数": [len(by_paper[p][fields[0][0]]) for p in papers]}}
    return res


# ---------------- 图（中文；配色同网站 05 页） ----------------
def write(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    if not (FIG / "plotly.min.js").exists():  # 离线可看：和网站 图/ 用同一份 plotly.min.js
        (FIG / "plotly.min.js").write_bytes((D.SITE_FIG / "plotly.min.js").read_bytes())
    fig.write_html(FIG / name, include_plotlyjs="directory", full_html=True, config={"displaylogo": False})


def fig_kim(k):
    import plotly.graph_objects as go
    r = k["同测试"]
    pts = r["点"]
    fig = go.Figure()
    lim = max(3.0, max(abs(p["Kim预测"]) for p in pts) * 1.1)
    fig.add_shape(type="line", x0=-lim, x1=lim, y0=-lim, y1=lim, line=dict(color=D.MUTED, dash="dot"))
    for x0, x1, y0, y1 in ((0, lim, 0, 9), (-lim, 0, -9, 0)):
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1, fillcolor="#2a78d6", opacity=0.06, line_width=0, layer="below")
    fig.add_trace(go.Scatter(x=[p["Kim预测"] for p in pts], y=[max(-6, min(6, p["实测"])) for p in pts], mode="markers",
                             marker=dict(size=9, color=D.BLUE, opacity=0.7, line=dict(width=1, color="white")),
                             text=[f"{p['论文']} {p['实验']} 对 {p['参照']}<br>Kim 预测 CE 损失 ×{math.exp(-p['Kim预测']):.2f}<br>实测 ×{math.exp(-p['实测']):.2f}"
                                   for p in pts], hoverinfo="text", showlegend=False))
    fig.add_hline(y=0, line=dict(color="#8a9a9c", width=1)); fig.add_vline(x=0, line=dict(color="#8a9a9c", width=1))
    fig.update_xaxes(title_text="Kim 等 2023 模型预测的两边之差（Δ，正 = 新电解液 CE 更高）", range=[-lim, lim], zeroline=False)
    fig.update_yaxes(title_text="我们实测的两边之差（Δ，同一测试内）", range=[-6.3, 6.3], zeroline=False)
    D.layout(fig, f"外部对照：Kim 等 2023 的 Li‖Cu CE 模型能否预测我们的篇内比较 · 同测试 {r['比较']} 个比较 / {r['论文']} 篇 · "
                  f"符号一致 {r['符号一致率_论文等权']:.0%}（论文等权）· 浅蓝区 = 方向一致", 620)
    write(fig, "图E1_Kim模型外部对照.html")


def fig_joint(j):
    import plotly.graph_objects as go
    rows, xs, err, cols, syms, hov = [], [], [], [], [], []
    for cls, ms in j.items():
        for m in ms:
            for r in m["结果"]:
                for lab, col, sym in (("单独", D.MUTED, "circle-open"), ("联合", D.BLUE, "circle")):
                    e = r.get(lab)
                    if not e:
                        continue
                    rows.append(f"{CLS_CN[cls]} · {m['模型']} · {CN[r['描述符']]}")
                    xs.append(e["倍数_每1SD"]); err.append(e["区间"]); cols.append(col); syms.append(sym)
                    hov.append(f"{lab}估计 ×{e['倍数_每1SD']:.2f}（95% 区间 ×{e['区间'][0]:.2f}–×{e['区间'][1]:.2f}，p = {e['p']:.3f}）<br>VIF {r['VIF']:.2f}")
    fig = go.Figure()
    for lab, col, sym in (("单独估（同一批比较）", D.MUTED, "circle-open"), ("放进同一个模型", D.BLUE, "circle")):
        ii = [i for i, c in enumerate(cols) if c == col]
        fig.add_trace(go.Scatter(x=[xs[i] for i in ii], y=[rows[i] for i in ii], mode="markers", name=lab,
                                 marker=dict(size=10, color=col, symbol=sym, line=dict(width=2, color=col)),
                                 error_x=dict(type="data", symmetric=False, array=[err[i][1] - xs[i] for i in ii],
                                              arrayminus=[xs[i] - err[i][0] for i in ii], color=col, thickness=1.5),
                                 text=[hov[i] for i in ii], hoverinfo="text"))
    fig.add_vline(x=1, line=dict(color="#8a9a9c", width=1))
    tv = [0.2, 0.3, 0.5, 0.7, 1, 1.5, 2, 3, 5, 8]
    fig.update_xaxes(type="log", tickvals=tv, ticktext=[f"×{t:g}" for t in tv], title_text="描述符变 1 个标准差，性能变几倍（> 1 = 变好）")
    fig.update_yaxes(autorange="reversed")
    D.layout(fig, "联合模型：几个描述符放在一起估，各自的作用还在不在", 90 + 34 * len(set(rows)), legend=dict(orientation="h", y=1.06, x=0),
             margin=dict(l=20, r=20, t=100, b=50))
    write(fig, "图E2_描述符联合模型.html")


def fig_complete(c):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    for layer, name in (("主层", "图E3_报告完整度_锂硫.html"), ("Li‖Cu", "图E4_报告完整度_LiCu.html")):
        d = c[layer]; h = d["热图"]
        fig = make_subplots(rows=1, cols=2, column_widths=[0.70, 0.30], horizontal_spacing=0.10,
                            subplot_titles=["每篇论文：写明该字段的测试比例（行按编号＝发表年份顺序）", "全部测试"])
        hov = [[f"{p} · {fl}<br>写明 {v:.0%}，能解析出数值 {u:.0%}（{n} 个测试）" for fl, v, u in zip(h["字段"], vr, ur)]
               for p, vr, ur, n in zip(h["论文"], h["写明比例"], h["可用比例"], h["测试数"])]
        fig.add_trace(go.Heatmap(z=h["写明比例"], x=h["字段"], y=h["论文"], hovertext=hov, hoverinfo="text", xgap=1, ygap=0,
                                 colorscale=[[0, "#f0efec"], [1, D.BLUE]], zmin=0, zmax=1,
                                 colorbar=dict(title="写明比例", tickformat=".0%", orientation="h", x=0.32, y=-0.1, len=0.45, thickness=12)), row=1, col=1)
        f = d["字段"]
        for key, lab, col in (("写明且可用_测试", "写明且能解析出数值", D.BLUE), ("写了没解析出_测试", "写了但没解析出", "#9fc1ea"),
                              ("没写_测试", "没写（或按默认值补）", "#d9d6cf")):
            fig.add_trace(go.Bar(y=[x["中文"] for x in f], x=[x[key] for x in f], orientation="h", name=lab, marker_color=col,
                                 text=[f"{x[key]:.0%}" if x[key] >= 0.08 else "" for x in f], textposition="inside",
                                 hovertext=[f"{x['中文']}：{lab} {x[key]:.0%}（{x['测试数']} 个测试）；至少一个测试写明的论文 {x['至少一个测试写明的论文']:.0%}"
                                            for x in f], hoverinfo="text"), row=1, col=2)
        fig.update_layout(barmode="stack")
        fig.update_yaxes(autorange="reversed", showticklabels=False, row=1, col=1)
        fig.update_yaxes(autorange="reversed", row=1, col=2)
        fig.update_xaxes(tickformat=".0%", range=[0, 1], row=1, col=2)
        D.layout(fig, f"报告完整度 · {'Li‖S 主层（硫碳正极）' if layer == '主层' else 'Li‖Cu'}：{d['论文']} 篇、{d['测试']} 个测试", 760,
                 legend=dict(orientation="h", y=-0.08, x=0.7), margin=dict(l=20, r=20, t=90, b=70))
        write(fig, name)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    P, M, ST = load()
    k = kim_check(P, M)
    j = joint(P, M)
    c = completeness(ST)
    res = {"说明": "可信度检验（11-06）。初步、未裁定；AI 辅助，用户尚未逐项人工确认。", "数据": "第 0 步 v2，全部 313 篇；表述试跑313篇_2026-11-05",
           "Kim外部对照": k, "联合模型": j, "报告完整度": c}
    jdump(OUT / "汇总.json", res)
    fig_kim(k); fig_joint(j); fig_complete(c)
    # 屏幕摘要
    for name in ("同测试", "全部不同配方（扣条件差）"):
        r = k.get(name)
        if r:
            print(f"Kim {name}: {r['比较']} 比较/{r['论文']} 篇；符号一致 {r['符号一致率_论文等权']:.2f} {r['区间']}"
                  f"（基线 {r['基线_新电解液总是更好_论文等权']:.2f} {r['基线区间']}）；Spearman {r['Spearman']:.2f} {r['Spearman区间']}；"
                  f"斜率 {r['校准斜率']:.2f} {r['校准斜率区间']} p={r['校准斜率p']:.3g}；Kim 正 {r['Kim预测为正的比例']:.2f} 实测正 {r['实测为正的比例']:.2f}")
    for f in k["四个特征各自的方向"]:
        print(f"  {f['特征']}: Kim {f['Kim系数']:+.3f}，我们 ×{f['倍数_每1SD']:.2f} {['%.2f' % x for x in f['倍数区间']]} p={f['p']:.3g} q={f['q']:.3g}，同号 {f['与Kim同号']}，{f['Δ≠0的论文']} 篇")
    for lab in ("Li‖Cu 配方", "全部配方"):
        print("  位点与 sO", lab, k[f"配位位点与sO相关_{lab}"])
    for cls, ms in j.items():
        for m in ms:
            print(f"{cls} · {m['模型']}：{m['比较']} 比较/{m['论文']} 篇，{m['方法']}")
            for r in m["结果"]:
                s, u = r.get("单独"), r.get("联合")
                print(f"   {r['描述符']}: 单独 ×{s['倍数_每1SD']:.2f} p={s['p']:.3g} → 联合 ×{u['倍数_每1SD']:.2f} "
                      f"[{u['区间'][0]:.2f}, {u['区间'][1]:.2f}] p={u['p']:.3g}；VIF {r['VIF']:.2f}；{r['Δ≠0的论文']} 篇有变化")
    for layer, d in c.items():
        print(f"{layer}: {d['论文']} 篇 {d['测试']} 测试")
        for x in d["字段"]:
            print(f"   {x['中文']}: 可用 {x['写明且可用_测试']:.0%} 未解析 {x['写了没解析出_测试']:.0%} 没写 {x['没写_测试']:.0%}；论文≥1 {x['至少一个测试写明的论文']:.0%}")
        for t in d["按编号三段"]:
            print("   ", t)


if __name__ == "__main__":
    main()
