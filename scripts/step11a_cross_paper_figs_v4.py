"""
step11a：用 v4 四篇表样（S11、S21、S33、S39）演示“跨文献比较”的三类图（组会用）。

只读、不改：
  output/论断式提取表样_v4_2026-10-24/论断式提取表样_v4_S11_S21_S33_S39.xlsx
    - 明细-配方：尺子值（每个主盐 Li⁺ 分到的配位溶剂分子数，step6h 算好的）
    - 明细-方向：每个比较、每个测试的方向（已按 v4 固定规则处理过“不判”）
  output/论断式提取表样_v4_2026-10-24/json/*.json
    - 测试条件（E/S、LiNO₃）、性质（溶解度）、机制（过程大类、方向、原句来源）

输出：output/云端_2026-10-25_组会图_跨文献v4表样/
  图1_尺子总览、图2_条件方向地图、图3a_机制在尺子上、图3b_两侧短板说了测了（PNG + SVG）

四篇只演示分析形式，不是结论；AI 辅助提取，用户未逐项人工确认。
"""
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.ticker import NullFormatter
import openpyxl

# ---------- 参数（改图时改这里） ----------
ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "output" / "论断式提取表样_v4_2026-10-24"
XLSX = V4 / "论断式提取表样_v4_S11_S21_S33_S39.xlsx"
OUT = ROOT / "output" / "云端_2026-10-25_组会图_跨文献v4表样"
PAPERS = ["S11", "S21", "S33", "S39"]
OPTIMUM = {"S11": "E20", "S21": "T60", "S33": "TFTFE", "S39": "F4"}   # 作者最优配方
CONTROL = {"S11": "E0", "S21": "T0", "S33": "DME", "S39": "DD"}       # 主对照
SHAPE = {"S11": "o", "S21": "s", "S33": "^", "S39": "D"}
C_GOOD, C_BAD, C_SAME, C_NA = "#2b6cb0", "#dd6b20", "#a0aec0", "#718096"
C_MIX = "#805ad5"
RULER_LIM = (13.0, 3.2)        # 尺子横轴：左强右弱
DPI = 200
FOOT = "样本：v4 表样 4 篇（S11、S21、S33、S39，挑选的表样，非随机）。只演示跨文献比较的形式，不是结论；AI 辅助提取，用户尚未逐项人工确认。"

plt.rcParams["font.family"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["svg.fonttype"] = "none"


# ---------- 读数据 ----------
def read_sheet(name):
    ws = openpyxl.load_workbook(XLSX, read_only=True)[name]
    rows = list(ws.iter_rows(values_only=True))
    head = rows[0]
    return [dict(zip(head, r)) for r in rows[1:] if any(c is not None for c in r)]


def ruler_value(text):
    m = re.match(r"^\s*([\d.]+)（粗算）", str(text or ""))
    return float(m.group(1)) if m else None


FORM = read_sheet("明细-配方")
DIRS = read_sheet("明细-方向")
J = {p: json.loads((V4 / "json" / f"{p}.json").read_text(encoding="utf-8")) for p in PAPERS}
RULER = {(r["文献"], r["代号"]): ruler_value(r["每个主盐 Li⁺ 分到的配位溶剂分子数 🧮"]) for r in FORM}


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.png", dpi=DPI, bbox_inches="tight")
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)
    print("写出", OUT / f"{name}.png")


# ---------- 图1 尺子总览 ----------
ROW_TITLE = {
    "S11": "S11  DOL/DME + TTE 稀释剂｜LiTFSI 1 M｜LiNO₃ 2 wt%",
    "S21": "S21  DME/THF + 邻二甲苯稀释剂｜LiTFSI 1 M｜不含 LiNO₃",
    "S33": "S33  DME + 氟化醚共溶剂｜LiFSI｜含 LiNO₃",
    "S39": "S39  DOL + DME / F4DEE / TTE｜LiTFSI 1 M｜LiNO₃ 0.2 M",
}
OFF_RULER = {
    "S11": "Em（软包用 medium，成分未写）",
    "S21": "T50、T70、T80（DME/THF 比例只在图片表 S2）",
    "S33": "全部 5 个配方：DME 对照单位小写 m 不换算；\nETFE、BTFE、TFTFE★、TFOFE 配位能力不明",
    "S39": "F4★（F4DEE 配位能力不明；只计 DOL 为 11.4）",
}


def solubility(p):
    for prop in J[p]["性质"]:
        if prop["性质"] == "多硫化物溶解度" and "数值" in prop:
            return prop["数值"], prop["单位"], prop["对象"]
    return {}, "", ""


def fig1():
    fig = plt.figure(figsize=(15, 8))
    ax = fig.add_axes([0.25, 0.25, 0.47, 0.62])
    ax2 = fig.add_axes([0.74, 0.25, 0.25, 0.62])
    ys = {p: 3 - i for i, p in enumerate(PAPERS)}
    ax.axvspan(9.8, 8.4, ymin=0.47, ymax=0.97, color="#fefcbf", zorder=0)
    ax.text(9.1, 3.62, "S11 与 S21 唯一重叠段 9.8–8.4（S21 在这段没有中间档）", ha="center", va="bottom", fontsize=8.5, color="#744210")
    for p in PAPERS:
        y = ys[p]
        pts = [(r["代号"], RULER[(p, r["代号"])]) for r in FORM if r["文献"] == p and RULER[(p, r["代号"])] is not None]
        pts.sort(key=lambda t: -t[1])
        sol, unit, obj = solubility(p)
        title = ROW_TITLE[p].replace("｜", "\n", 1) + (f"\n溶解度：{obj}，{unit}" if sol else "")
        ax.text(RULER_LIM[0] + 0.25, y, title, ha="right", va="center", fontsize=9, color="#2d3748")
        if pts:
            xs = [x for _, x in pts]
            ax.plot([max(xs), min(xs)], [y, y], color="#cbd5e0", lw=3, zorder=1)
        else:
            ax.text(8.1, y, "放不上尺子（见右栏）", ha="center", va="center", fontsize=10, color=C_NA,
                    bbox=dict(boxstyle="round", fc="#f7fafc", ec="#cbd5e0"))
        for k, (code, x) in enumerate(pts):
            is_opt, is_ctl = code == OPTIMUM[p], code == CONTROL[p]
            mk, ms = ("*", 17) if is_opt else (("s", 9) if is_ctl else ("o", 7))
            fc = "#e53e3e" if is_opt else ("#2d3748" if is_ctl else "white")
            ax.plot(x, y, marker=mk, ms=ms, mfc=fc, mec="#2d3748", zorder=3)
            lab = code + ("（对照）" if is_ctl else "（另一对照）" if code == "DD" and p == "S21" else "（最优）" if is_opt else "")
            lab += f" {x:.1f}" + (f"\n溶解度 {sol[code]:g}" if code in sol else "")
            up = k % 2 == 0
            ax.text(x, y + (0.17 if up else -0.17), lab, ha="center", va="bottom" if up else "top", fontsize=8,
                    color="#2d3748", linespacing=1.1)
    ax.set_xlim(*RULER_LIM)
    ax.set_ylim(-0.6, 3.8)
    ax.set_yticks([])
    for s_ in ("left", "right", "top"):
        ax.spines[s_].set_visible(False)
    ax.set_xlabel("← 强溶剂化        每个主盐 Li⁺ 分到的配位溶剂分子数（配方 + 手册粗算）        弱溶剂化 →", fontsize=10)
    ax2.axis("off")
    ax2.set_xlim(0, 1)
    ax2.set_ylim(-0.6, 3.8)
    ax2.text(0, 3.65, "放不上尺子的配方（只在篇内比）", fontsize=10, weight="bold", color="#4a5568")
    for p in PAPERS:
        ax2.text(0, ys[p], f"{p}：{OFF_RULER[p]}", fontsize=8.5, va="center", color="#4a5568")
    leg = [Line2D([], [], marker="s", ls="", mfc="#2d3748", mec="#2d3748", ms=8, label="对照"),
           Line2D([], [], marker="*", ls="", mfc="#e53e3e", mec="#2d3748", ms=14, label="作者最优"),
           Line2D([], [], marker="o", ls="", mfc="white", mec="#2d3748", ms=7, label="其他梯度档")]
    ax2.legend(handles=leg, loc="upper left", bbox_to_anchor=(0, 0.1), frameon=False, fontsize=9)
    fig.text(0.03, 0.95, "图1  各篇配方放到同一把尺子上：“强 / 弱溶剂化”跨篇可比吗？最优落在哪一段？", fontsize=14, weight="bold")
    fig.text(0.03, 0.09, "看点：① S11 的最弱档（8.4）还在 S21 对照（9.8）附近——各篇的“弱溶剂化”不在同一段，档位名不能跨篇比。\n"
             "② 两篇能放上尺子的最优点位置不同（S11 9.6、S21 4.0），稀释剂、LiNO₃、测试条件也都不同；全库后看最优是否随这些条件移动。\n"
             "③ S39 DD → TT 尺子只从 12.0 到 11.4，溶解度却从 1.0 降到 0.22 M：尺子只代表 Li⁺ 一侧，多硫化物一侧看实测溶解度。④ 4 篇里 S33 整篇、S39 最优配方放不上尺子。",
             fontsize=9, color="#2d3748", linespacing=1.5)
    fig.text(0.03, 0.025, FOOT, fontsize=7.5, color="#718096")
    save(fig, "图1_尺子总览")


# ---------- 图2 条件—方向地图 ----------
def metric_cat(name, es):
    if name.startswith(("首圈容量", "首圈能量")):
        return "首圈容量 / 能量"
    if name.startswith("倍率容量"):
        return "倍率容量"
    if name.startswith("过电位"):
        return "过电位"
    if name.startswith("阻抗"):
        return "阻抗（循环后）"
    if name.startswith(("库仑效率",)):
        return "锂负极（Li‖Cu/Ni/Li）" if es is None else "Li‖S 库仑效率"
    if name.startswith(("穿梭", "自放电")):
        return "穿梭 / 自放电"
    if name.startswith(("寿命", "容量保持", "衰减", "指定圈数")):
        return "锂负极（Li‖Cu/Ni/Li）" if es is None else "寿命 / 保持率"
    return None


CATS = ["首圈容量 / 能量", "倍率容量", "过电位", "阻抗（循环后）", "Li‖S 库仑效率", "寿命 / 保持率", "穿梭 / 自放电", "锂负极（Li‖Cu/Ni/Li）"]


def test_es(t):
    es = t.get("E/S")
    if isinstance(es, (int, float)):
        return float(es)
    if isinstance(es, str) and re.fullmatch(r"[\d.]+", es.strip()):
        return float(es)
    if isinstance(es, dict):            # A、B 的 E/S 不同（S21 T8），画在均值处，方向本来就是“不判”
        return sum(es.values()) / len(es)
    return None


def has_lino3(t):
    s = json.dumps(t.get("LiNO₃"), ensure_ascii=False)
    return not ("不含" in s or "去掉" in s or "都不" in s)


def direction(s):
    s = str(s)
    if s.startswith("变好"):
        return "good"
    if s.startswith("变坏"):
        return "bad"
    if s.startswith("差异小"):
        return "same"
    if s.startswith("不判"):
        return "na"
    return None


def fig2_points():
    pts = {}
    for r in DIRS:
        p = r["文献"]
        if r["类型"] != "表现":
            continue
        a, b = [x.strip() for x in r["比较"].split("vs")]
        # 只取作者最优 vs 主对照；S11 软包只有 Em/E30 vs E0，取 Em（medium，🔶 对应哪档原文未写）
        tcode = r["测试"].split()[0]
        if not ((a == OPTIMUM[p] and b == CONTROL[p]) or (p == "S11" and tcode == "T5" and a == "Em")):
            continue
        t = next(t for t in J[p]["测试"] if t["编号"] == tcode)
        es = test_es(t)
        cat = metric_cat(r["指标（取值点）"], es)
        d = direction(r["方向"])
        if cat is None or d is None:
            continue
        key = (p, tcode, cat)
        e = pts.setdefault(key, {"dirs": set(), "es": es, "lino3": has_lino3(t), "test": r["测试"],
                                 "qual": False, "fig": False})
        e["dirs"].add(d)
        e["qual"] |= "作者定性" in str(r["方向"])
        e["fig"] |= "读图" in str(r["出处"])
    return pts


def fig2():
    pts = fig2_points()
    # 同一篇里 E/S 相同的不同测试横向错开（对数轴上乘一个小系数），免得叠在一起
    xpos = {}
    for p in PAPERS:
        groups = {}
        for (pp, tcode, _), e in pts.items():
            if pp == p:
                groups.setdefault(e["es"], set()).add(tcode)
        for es, tests in groups.items():
            tests = sorted(tests, key=lambda t: int(t[1:]))
            for i, t in enumerate(tests):
                k = i - (len(tests) - 1) / 2
                strip = {"S11": 0.6, "S21": 0.95, "S33": 1.3, "S39": 1.65}[p]     # 无 E/S 栏里每篇占一个位置
                xpos[(p, t)] = strip + 0.2 * k if es is None else es * 1.05 ** k
    fig = plt.figure(figsize=(15, 9))
    ax = fig.add_axes([0.17, 0.26, 0.62, 0.64])
    axr = fig.add_axes([0.81, 0.26, 0.12, 0.64], sharey=ax)
    yc = {c: len(CATS) - 1 - i for i, c in enumerate(CATS)}
    off = {"S11": 0.27, "S21": 0.09, "S33": -0.09, "S39": -0.27}
    for a in (ax, axr):
        for c, y in yc.items():
            a.axhline(y + 0.5, color="#edf2f7", lw=1, zorder=0)
    by_test = {}
    for (p, tcode, cat), e in pts.items():
        d = "mix" if len(e["dirs"]) > 1 else next(iter(e["dirs"]))
        col = {"good": C_GOOD, "bad": C_BAD, "same": C_SAME, "na": C_NA, "mix": C_MIX}[d]
        y = yc[cat] + off[p]
        a = axr if e["es"] is None else ax
        x = xpos[(p, tcode)]
        if d == "na":
            a.plot(x, y, marker="x", ms=9, mew=2, color=C_NA, zorder=3)
        else:
            a.plot(x, y, marker=SHAPE[p], ms=10, mfc=col if e["lino3"] else "white", mec=col, mew=2, zorder=3)
        tag = tcode + ("·读图" if e["fig"] else "")
        a.text(x * 1.012 if a is ax else x + 0.05, y + 0.13, tag, fontsize=6.8, va="bottom", ha="left", color="#4a5568")
        if a is ax and d in ("good", "bad"):
            by_test.setdefault((p, tcode), []).append((x, y, d))
    # 同一测试里既有变好又有变坏 → 竖虚线连起来（同测试内权衡）
    for (p, tcode), lst in by_test.items():
        if {"good", "bad"} <= {d for _, _, d in lst}:
            ys_ = [y for _, y, _ in lst]
            x = lst[0][0]
            ax.plot([x, x], [min(ys_), max(ys_)], ls=(0, (3, 2)), color="#e53e3e", lw=1.3, zorder=2)
    ax.set_xscale("log")
    ax.set_xlim(1.7, 19)
    ax.set_xticks([2, 3, 5, 10, 15])
    ax.set_xticklabels(["2", "3", "5", "10", "15"])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("E/S（µL mg⁻¹，测试条件本身是统一标准；越往左越贫液）", fontsize=10)
    ax.set_yticks(list(yc.values()))
    ax.set_yticklabels(list(yc.keys()), fontsize=10)
    ax.set_ylim(-0.6, len(CATS) - 0.4)
    axr.set_xlim(0.35, 1.95)
    axr.set_xticks([])
    axr.set_xlabel("无 E/S\n（半电池 / 对称电池）", fontsize=9)
    plt.setp(axr.get_yticklabels(), visible=False)
    axr.tick_params(left=False)
    leg = [Line2D([], [], marker="s", ls="", mfc=C_GOOD, mec=C_GOOD, ms=9, label="作者最优比对照变好"),
           Line2D([], [], marker="s", ls="", mfc=C_BAD, mec=C_BAD, ms=9, label="变坏"),
           Line2D([], [], marker="s", ls="", mfc=C_SAME, mec=C_SAME, ms=9, label="差异小"),
           Line2D([], [], marker="x", ls="", color=C_NA, mew=2, ms=9, label="不判（按 v4 规则）"),
           Line2D([], [], marker="s", ls="", mfc="white", mec="#4a5568", mew=2, ms=9, label="空心 = 测试不含 LiNO₃"),
           Line2D([], [], ls=(0, (3, 2)), color="#e53e3e", label="同一测试内权衡")]
    leg += [Line2D([], [], marker=SHAPE[p], ls="", mfc="#4a5568", mec="#4a5568", ms=8, label=f"{p}（最优 {OPTIMUM[p]} vs {CONTROL[p]}）") for p in PAPERS]
    ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.55, -0.09), ncol=5, frameon=False, fontsize=8.5)
    fig.text(0.17, 0.95, "图2  作者最优配方相对对照的优势，在什么条件下出现、在什么条件下变坏？（一个点 = 一篇论文的一个测试）", fontsize=14, weight="bold")
    fig.text(0.17, 0.045, "（点旁 T1、T2… 是该篇的测试编号，形状区分论文）\n看点：① 首圈容量 / 能量、倍率、过电位三行：含 LiNO₃ 的测试里（实心），作者最优配方没有一次比对照好（变坏或差异小，S11、S33、S39）；\n"
             "这三行变好的点只来自 S21 不含 LiNO₃ 的测试（空心，对照也不含）——“打破权衡”是真兼顾还是对照偏弱，全库要按对照类型分开看。\n"
             "② 寿命、库仑效率、穿梭、锂负极几行没有变坏的点。③ 同一测试内的权衡（红虚线）出现在 E/S 2.0（S33 叠片软包）、5（S33 扣式）、6.1（S11）。",
             fontsize=8.8, color="#2d3748")
    fig.text(0.17, 0.005, FOOT + " S11-T5 为软包 medium vs E0（medium 对应哪档原文未写）。", fontsize=7.5, color="#718096")
    save(fig, "图2_条件方向地图")


# ---------- 图3a 机制在尺子上 ----------
PROCS = ["正极反应", "多硫化物穿梭", "负极锂", "电解液消耗"]
GOOD_WORDS = {"改善", "减轻", "减少"}
BAD_WORDS = {"变差", "加重", "加快", "劣化"}
STRONGER = {"更强", "更高"}
WEAKER = {"更弱", "更低"}
SOLV_NAMES = ("Li⁺ 溶剂化", "多硫化物溶剂化", "多硫化物溶解度")


def solv_kind(props):
    names = [x["名称"] for x in props]
    for n, k in (("多硫化物溶解度", "多硫化物溶解度"), ("多硫化物溶剂化", "多硫化物溶剂化"), ("Li⁺ 溶剂化", "Li⁺ 溶剂化")):
        if n in names:
            # S39 M1/M2 同时写 Li⁺ 与多硫化物溶剂化：记为“两者”
            if n == "多硫化物溶剂化" and "Li⁺ 溶剂化" in names:
                return "Li⁺ + 多硫化物溶剂化"
            return k
    return "其他（" + "、".join(names) + "）" if names else "未写"


def gradient_order(p):
    """本篇配方由强到弱的顺序：有梯度用梯度，没有用 Li⁺ 溶剂化的排序（S39）。"""
    if J[p].get("梯度"):
        return J[p]["梯度"][0]["顺序"]
    for prop in J[p]["性质"]:
        if prop["性质"] == "Li⁺ 溶剂化" and prop.get("排序含义") == "由强到弱":
            return prop["排序"]
    return None


def a_is_stronger(p, m):
    """只按 Li⁺ 溶剂化 / 多硫化物溶剂化 / 溶解度判 A、B 谁强；三项都没写时按本篇梯度顺序。"""
    dirs = [x["方向"] for x in m.get("性质", []) if x["名称"] in SOLV_NAMES]
    if any(d in STRONGER for d in dirs):
        return True
    if any(d in WEAKER for d in dirs):
        return False
    order = gradient_order(p)
    return order.index(m["A"]) < order.index(m["B"])


def claims():
    """把每条机制翻成“往溶剂化变弱的方向”：返回 (论文, 编号, 强端, 弱端, 过程, 变弱后 good/bad/same, 溶剂化种类, 有本文结论, 概括)。"""
    out = []
    for p in PAPERS:
        for m in J[p]["机制"]:
            a, b = m["A"], m["B"]
            props = m.get("性质", [])
            flip = a_is_stronger(p, m)    # 原文方向描述的是 A；A 是强端时，变弱方向要翻转
            strong, weak = (a, b) if flip else (b, a)
            # “全梯度”的说法覆盖整条梯度（S39 的 A/B 只写 F4、DD，梯度到 TT，TT 能放上尺子）
            if m.get("梯度段") == "全梯度":
                order = gradient_order(p)
                strong, weak = order[0], order[-1]
            for pr in m.get("过程", []):
                w = pr["方向"]
                if w in GOOD_WORDS:
                    eff = "good"
                elif w in BAD_WORDS:
                    eff = "bad"
                else:
                    eff = "same"
                if flip and eff != "same":
                    eff = "bad" if eff == "good" else "good"
                src_own = any(str(s.get("来源", "")).startswith("本文结论") for s in m.get("原句", []))
                out.append(dict(p=p, id=m["编号"], strong=strong, weak=weak, proc=pr["大类"], eff=eff,
                                kind=solv_kind(props), own=src_own, txt=m.get("概括", "")))
    return out


def fig3a():
    cl = claims()
    fig = plt.figure(figsize=(16, 8.6))
    ax = fig.add_axes([0.11, 0.24, 0.55, 0.66])
    ax2 = fig.add_axes([0.68, 0.24, 0.31, 0.66])
    yb = {pr: len(PROCS) - 1 - i for i, pr in enumerate(PROCS)}
    on, off = {pr: [] for pr in PROCS}, {pr: [] for pr in PROCS}
    for c in cl:
        x0, x1 = RULER.get((c["p"], c["strong"])), RULER.get((c["p"], c["weak"]))
        (on if x0 is not None and x1 is not None else off)[c["proc"]].append((c, x0, x1))
    for pr in PROCS:
        ax.axhline(yb[pr] - 0.5, color="#e2e8f0", lw=1)
        lst = on[pr]
        for k, (c, x0, x1) in enumerate(lst):
            y = yb[pr] + 0.33 - k * (0.66 / max(len(lst) - 1, 1)) if len(lst) > 1 else yb[pr]
            col = {"good": C_GOOD, "bad": C_BAD, "same": C_SAME}[c["eff"]]
            arr = FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=14, lw=2.4, color=col,
                                  linestyle="-" if c["own"] else "--", zorder=3)
            ax.add_patch(arr)
            ax.plot(x0, y, marker=SHAPE[c["p"]], ms=7, color=col, zorder=4)
            word = {"good": "变好", "bad": "变差", "same": "不变"}[c["eff"]]
            lab = f"{c['p']} {c['id']}：{word}｜{c['kind']}"
            if x1 < 6:      # 箭头伸到尺子右端时，标签放到起点左边，免得压进右栏
                ax.text(x0 + 0.15, y, lab, fontsize=8, va="center", ha="right", color="#2d3748")
            else:
                ax.text(x1 - 0.12, y, lab, fontsize=8, va="center", ha="left", color="#2d3748")
    # 重叠段的判定框（按 §8.3a）
    notes = [
        ("正极反应", 12.0, 8.4, "S11 vs S21：方向相反，但一个说多硫化物溶剂化、一个说 Li⁺ 溶剂化，\n且 S21 在重叠段 9.8–8.4 没有中间档 → 不判\n候选矛盾：S11 vs S39 M3（都说多硫化物溶剂化，段 12.0–11.4 重叠）\nS11 变差、S39 不变 → 再比 4 样：溶剂化种类同、对照类型同；\n测法不同（恒电位 Li₂S 沉积 vs 溶液正极 GITT）；配位溶剂不同只能粗比"),
        ("多硫化物穿梭", 9.8, 8.4, "S11、S21 方向一致，但一个说多硫化物溶剂化、一个说溶解度\n→ 不算共识（§8.3a：三种溶剂化不混）"),
        ("负极锂", 9.8, 8.4, "同上：方向一致，溶剂化种类不同 → 不算共识"),
    ]
    for pr, xa, xb, t in notes:
        ax.add_patch(Rectangle((xb, yb[pr] - 0.46), xa - xb, 0.92, fill=False, ec="#e53e3e", ls=(0, (4, 2)), lw=1.2, zorder=1))
    ax.set_xlim(*RULER_LIM)
    ax.set_ylim(-0.6, len(PROCS) - 0.4)
    ax.set_yticks(list(yb.values()))
    ax.set_yticklabels(PROCS, fontsize=11)
    ax.set_xlabel("← 强溶剂化        每个主盐 Li⁺ 分到的配位溶剂分子数        弱溶剂化 →\n（每条箭头 = 一条机制说法，从强端指向弱端；颜色 = 溶剂化变弱后该过程变好 / 变差）", fontsize=9.5)
    for s in ("right", "top"):
        ax.spines[s].set_visible(False)
    # 右栏：判定说明 + 放不上尺子的说法
    ax2.axis("off")
    ax2.set_xlim(0, 1)
    ax2.set_ylim(-0.6, len(PROCS) - 0.4)
    ax2.text(0, len(PROCS) - 0.45, "红框里怎么判（§8.3a）", fontsize=10, weight="bold", color="#c53030", va="top")
    yy = len(PROCS) - 0.75
    for pr, _, _, t in notes:
        ax2.text(0, yy, f"【{pr}】{t}", fontsize=7.6, va="top", color="#2d3748")
        yy -= 0.36 + 0.17 * t.count("\n")
    yy -= 0.05
    ax2.text(0, yy, "放不上尺子的说法（只做篇内汇总，不进矛盾判断）", fontsize=10, weight="bold", color="#4a5568", va="top")
    yy -= 0.25
    for pr in PROCS:
        for c, _, _ in off[pr]:
            word = {"good": "变好", "bad": "变差", "same": "不变"}[c["eff"]]
            col = {"good": C_GOOD, "bad": C_BAD, "same": C_SAME}[c["eff"]]
            ax2.text(0, yy, f"{c['p']} {c['id']}  {c['strong']}→{c['weak']}｜{pr}：{word}" + ("" if c["own"] else "（只有推测/转述）"),
                     fontsize=7.8, va="top", color=col)
            yy -= 0.17
    leg = [Line2D([], [], color=C_GOOD, lw=2.4, label="变弱后该过程变好"),
           Line2D([], [], color=C_BAD, lw=2.4, label="变弱后该过程变差"),
           Line2D([], [], color=C_SAME, lw=2.4, label="不变"),
           Line2D([], [], color="#4a5568", lw=2.4, ls="--", label="虚线 = 只有推测 / 转述原句"),
           Rectangle((0, 0), 1, 1, fill=False, ec="#e53e3e", ls="--", label="尺子同段、同一过程（要判）")]
    ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=3, frameon=False, fontsize=8.5)
    fig.text(0.11, 0.95, "图3a  各篇的机制说法放到同一把尺子上：同一段、同一过程，说法一致还是相反？", fontsize=14, weight="bold")
    fig.text(0.11, 0.035, "看点：4 篇里只有 S11、S21、S39 有能上尺子的说法；三个红框中两个因“说的是不同的溶剂化”不算共识，一个（S11 vs S39 正极反应）进入候选矛盾，下一步比测法。\n"
             "S33 整篇放不上尺子。全库后：红框数、候选矛盾的 4 样对比，直接生成共识 / 矛盾清单。", fontsize=8.8, color="#2d3748")
    fig.text(0.11, 0.005, FOOT, fontsize=7.5, color="#718096")
    save(fig, "图3a_机制在尺子上")


# ---------- 图3b 两侧短板：说了 / 测了 ----------
# 测量对应到过程大类，是 Claude 的归类（AI 归类，待用户确认）；来源：各篇 JSON 的“机理测量”和直接测过程的测试。
# 每项： (在哪测：Li‖S / 简化, 测什么, 是否在失效电池里定量物质收支)
MEASURED = {
    ("S11", "正极反应"): [("简化", "Li₂S 恒电位沉积（Li|Li₂S₈）", False)],
    ("S11", "多硫化物穿梭"): [("Li‖S", "穿梭电流（不含 LiNO₃）", False)],
    ("S11", "负极锂"): [("简化", "SEI 中 S 含量 XPS（不含 LiNO₃）", False)],
    ("S21", "正极反应"): [("简化", "Li₂S 恒电位沉积（Li‖Li₂S₆）", False), ("Li‖S", "两段平台容量比 Q2/Q1", False)],
    ("S21", "多硫化物穿梭"): [("Li‖S", "静置 100 h 自放电（不含 LiNO₃）", False)],
    ("S21", "负极锂"): [("简化", "Li‖Li 对称电池", False)],
    ("S33", "多硫化物穿梭"): [("Li‖S", "开路穿梭电流", False)],
    ("S33", "负极锂"): [("Li‖S", "失效电池拆出测剩余活性锂", True), ("简化", "Li‖Ni CE", False)],
    ("S33", "电解液消耗"): [("Li‖S", "失效电池 DME、FSI⁻ 保留率 QNMR；补液后恢复", True)],
    ("S39", "正极反应"): [("Li‖S", "全电池 GITT", False), ("简化", "溶液正极 GITT", False)],
    ("S39", "负极锂"): [("简化", "Li‖Cu CE", False), ("Li‖S", "循环后 EIS 的 R_SEI", False)],
}


def wrap(t, n=20):
    import textwrap
    return "\n".join(textwrap.wrap(t, n))


def fig3b():
    cl = claims()
    rows = [("强溶剂化一侧的短板", pr) for pr in PROCS] + [("弱溶剂化一侧的短板", pr) for pr in PROCS]
    said = {}
    for c in cl:
        if c["id"] == "M2" and c["p"] == "S33":
            continue        # ETFE 自身腐蚀锂：作者归为溶剂本身，不是溶剂化强弱，单列在脚注
        if c["eff"] == "same":
            continue
        side = "强溶剂化一侧的短板" if c["eff"] == "good" else "弱溶剂化一侧的短板"
        e = said.setdefault((side, c["proc"], c["p"]), {"own": False, "ids": []})
        e["own"] |= c["own"]
        e["ids"].append(c["id"])
    fig = plt.figure(figsize=(16, 10))
    ax = fig.add_axes([0.02, 0.13, 0.96, 0.79])
    ax.axis("off")
    ncol = len(PAPERS) + 1
    x0, wlab = 0.0, 0.13
    wcol = (1 - wlab) / ncol
    # 有内容的行高一些，空行矮一些
    heights = [2.2 if any((sd, pr, p) in said for p in PAPERS) else 0.6 for sd, pr in rows]
    unit = 1 / (sum(heights) + 0.7)
    heads = ["", *PAPERS, "跨文献汇总"]
    for j, t in enumerate(heads):
        ax.text(x0 + (wlab + (j - 0.5) * wcol if j else wlab / 2), 1 - 0.35 * unit, t, ha="center", va="center", fontsize=11, weight="bold")
    ytop = 1 - 0.7 * unit
    ysplit = None
    for i, (side, pr) in enumerate(rows):
        hh = heights[i] * unit
        yc = ytop - hh / 2
        if i == 4:
            ysplit = ytop
        bg = "#fff5f5" if side.startswith("强") else "#ebf8ff"
        ax.add_patch(Rectangle((0, ytop - hh), 1, hh, color=bg, zorder=0))
        ax.plot([0, 1], [ytop - hh, ytop - hh], color="#edf2f7", lw=0.8)
        ax.text(0.005, yc, f"{side}\n  {pr}", va="center", fontsize=9.5)
        n_said, n_cell, n_mass = [], [], []
        for j, p in enumerate(PAPERS):
            xc = wlab + (j + 0.5) * wcol
            s_ = said.get((side, pr, p))
            ms = MEASURED.get((p, pr), [])
            if s_:
                n_said.append(p)
                lines = [("● 说了 " if s_["own"] else "○ 只推测/转述 ") + "、".join(s_["ids"])]
                if ms:
                    for where, what, mass in ms:
                        lines.append(wrap(f"测（{'Li‖S 电池' if where == 'Li‖S' else '简化体系/半电池'}）：{what}"))
                    if any(w == "Li‖S" for w, _, _ in ms):
                        n_cell.append(p)
                    if any(m for _, _, m in ms):
                        n_mass.append(p)
                else:
                    lines.append("测：无对应测量")
                ax.text(xc, yc, "\n".join(lines), ha="center", va="center", fontsize=7.6, color="#2d3748", linespacing=1.25)
            elif heights[i] > 1:
                ax.text(xc, yc, "—", ha="center", va="center", fontsize=8, color="#cbd5e0")
        xs = wlab + (len(PAPERS) + 0.5) * wcol
        if n_said:
            summ = (f"说了 {len(n_said)} 篇（{'、'.join(n_said)}）\n"
                    f"Li‖S 电池里有测量 {len(n_cell)} 篇" + (f"（{'、'.join(n_cell)}）" if n_cell else "") + "\n"
                    f"失效电池里定量收支 {len(n_mass)} 篇" + (f"（{'、'.join(n_mass)}）" if n_mass else ""))
            ax.text(xs, yc, summ, ha="center", va="center", fontsize=8.2, weight="bold", color="#2d3748", linespacing=1.3)
        else:
            ax.text(xs, yc, "4 篇都没说", ha="center", va="center", fontsize=8, color="#a0aec0")
        ytop -= hh
    ybot = ytop
    for j in range(ncol + 1):
        xx = wlab + j * wcol
        ax.plot([xx, xx], [ybot, 1 - 0.7 * unit], color="#e2e8f0", lw=1)
    ax.plot([0, 1], [1 - 0.7 * unit, 1 - 0.7 * unit], color="#a0aec0", lw=1)
    ax.plot([0, 1], [ysplit, ysplit], color="#a0aec0", lw=1.5)
    fig.text(0.02, 0.95, "图3b  两侧的短板：哪些论文说了、哪些论文测了？（→ 共识 / 矛盾 / 常说没测三张清单）", fontsize=14, weight="bold")
    fig.text(0.02, 0.065, "看点：① 强溶剂化一侧的短板说在负极锂：4 篇都说，但在失效电池里定量了剩余活性锂的只有 S33（其余是 XPS、对称电池、Li‖Cu、EIS）。"
             "电解液消耗也只有 S33 定量过（QNMR + 补液恢复），S39 只是推测。\n"
             "② 正极反应两侧都被说成短板（强的一侧 S21、S39；弱的一侧 4 篇）——与“最优在中间”一致，不是矛盾；弱的一侧 4 篇里 S33 没有对应测量，S11、S21 的 Li₂S 沉积在简化电池里测。\n"
             "③ 弱溶剂化一侧的穿梭、负极锂、电解液消耗，4 篇都没说。侧别由机制记录的方向自动换算；“测”把机理测量对应到过程大类是 Claude 的归类（待确认）。S33 M2（ETFE 自身腐蚀锂）不属于溶剂化强弱，未列入。",
             fontsize=8.8, color="#2d3748", linespacing=1.5)
    fig.text(0.02, 0.02, FOOT, fontsize=7.5, color="#718096")
    save(fig, "图3b_两侧短板说了测了")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3a()
    fig3b()
