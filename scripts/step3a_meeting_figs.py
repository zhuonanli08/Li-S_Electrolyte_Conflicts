"""组会用图（方案 3 阶段性结果）：读 output/第一阶段_证据表.xlsx 与机制判别表.json，输出 PNG + SVG 到 output/图/组会/

图1 证据分布：E/S 档 × 锂量档（主层，格内 = 论文数 / 比较数）
图2 各指标胜方（按论文计，主层，只计胜方可判的比较）
图3 配对指纹：同一篇、同一对配方、同一条件下各指标哪边赢
图4 案例：S33 氟化度梯度（CE 与寿命）；S32 E-baseline vs 1.0M-DMFN（含 HUGS 库存）
图5 机制判别表：10 个案例 × 候选机制的证据状态
"""
import json
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch, Rectangle
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX = os.path.join(ROOT, "output", "第一阶段_证据表.xlsx")
JDIR = os.path.join(ROOT, "output", "第一阶段_证据表", "json")
MECH = os.path.join(ROOT, "output", "第一阶段_证据表", "机制判别表.json")
OUT = os.path.join(ROOT, "output", "图", "组会")
os.makedirs(OUT, exist_ok=True)

for f in ("msyh.ttc", "msyhbd.ttc"):
    p = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", f)
    if os.path.exists(p):
        font_manager.fontManager.addfont(p)
plt.rcParams.update({"font.family": "Microsoft YaHei", "axes.unicode_minus": False, "font.size": 10,
                     "svg.fonttype": "none", "axes.spines.top": False, "axes.spines.right": False})

C_STRONG, C_WEAK, C_SMALL, C_UNK, C_MIX = "#E07B39", "#3B75AF", "#BDBDBD", "#F2F2F2", "#9C6ADE"
C_A, C_B = "#2E9C6A", "#B5487E"

m = pd.read_excel(XLSX, sheet_name="主表")
ac = pd.read_excel(XLSX, sheet_name="优势一致性")
main = m[m["A6 主层（本行）"] == "是"].copy()
npap, nrand = m["A2 论文号"].nunique(), m.loc[m["A5 抽样来源"].astype(str).str.startswith(("随机", "补抽")), "A2 论文号"].nunique()
FOOT = (f"样本：{npap} 篇（随机 {nrand} 篇，其余按入选标签或定向精读选入，非随机）；只计主层（液态电解液、硫碳正极）。"
        "数据为 AI 辅助提取与复核，尚未逐项人工确认。")

GROUP = {"首圈容量": "首圈容量 / 能量", "能量密度": "首圈容量 / 能量", "倍率容量": "倍率容量", "过电位或动力学": "过电位 / 动力学",
         "阻抗": "阻抗", "平均放电容量": "平均放电容量", "指定圈数放电容量": "指定圈数放电容量", "循环保持率或寿命": "保持率 / 寿命",
         "全电池库仑效率": "全电池 CE", "多硫化物溶解或穿梭": "穿梭", "自放电（容量损失）": "自放电", "自放电（容量变化）": "自放电",
         "其他": "其他（库存、Li2S 沉积等）"}
COLS = ["首圈容量 / 能量", "倍率容量", "过电位 / 动力学", "阻抗", "平均放电容量", "指定圈数放电容量", "保持率 / 寿命",
        "全电池 CE", "穿梭", "自放电", "其他（库存、Li2S 沉积等）"]
BLOCKS = [("初始性能 / 动力学", 0, 4), ("随循环累积", 4, 7), ("副反应 / 损耗", 7, 10), ("", 10, 11)]
main["组"] = main["D1 指标"].map(GROUP)


def save(fig, name):
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def footnote(fig, y=0.0, extra=""):
    fig.text(0.01, y, FOOT + (("\n" + extra) if extra else ""), fontsize=7.5, color="#555555", ha="left", va="top")


# ---------- 图1 ----------
ES = ["贫液(≤5)", "中等(5–15]", "富液(>15)", "未知"]
LI = ["薄", "中", "厚", "未报告"]
LI_LAB = {"薄": "薄锂\n（≤50 µm 或 N/P≤3）", "中": "中", "厚": "厚", "未报告": "锂量未报告"}
cnt_r = main.pivot_table(index="C17 E/S 档", columns="C17 锂量档", values="A1 行号", aggfunc="count").reindex(index=ES, columns=LI)
cnt_p = main.pivot_table(index="C17 E/S 档", columns="C17 锂量档", values="A2 论文号", aggfunc=pd.Series.nunique).reindex(index=ES, columns=LI)
fig, ax = plt.subplots(figsize=(7.2, 4.6))
im = ax.imshow(cnt_p.fillna(0).values, cmap="Blues", vmin=0, vmax=max(8, cnt_p.max().max()))
for i, e in enumerate(ES):
    for j, l in enumerate(LI):
        p, r = cnt_p.loc[e, l], cnt_r.loc[e, l]
        if pd.notna(p) and p > 0:
            top = main[(main["C17 E/S 档"] == e) & (main["C17 锂量档"] == l)]["A2 论文号"].value_counts()
            note = f"\n（{top.index[0]} 占 {top.iloc[0]}）" if top.iloc[0] / r >= 0.5 and p > 1 else ""
            ax.text(j, i, f"{int(p)} 篇 / {int(r)} 条{note}", ha="center", va="center", fontsize=9,
                    color="white" if p >= 5 else "#222222")
        else:
            ax.text(j, i, "—", ha="center", va="center", color="#999999")
ax.set_xticks(range(len(LI)), [LI_LAB[x] for x in LI])
ax.set_yticks(range(len(ES)), ES)
ax.set_xlabel("锂量档"); ax.set_ylabel("E/S 档（µL/mg）")
ax.set_title(f"图1  证据分布：主层 {len(main)} 条比较、{main['A2 论文号'].nunique()} 篇", loc="left", fontsize=12)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_xticks([x - 0.5 for x in range(1, len(LI))], minor=True); ax.set_yticks([y - 0.5 for y in range(1, len(ES))], minor=True)
ax.grid(which="minor", color="white", linewidth=2); ax.tick_params(which="minor", length=0)
nun = (main["C17 锂量档"] == "未报告").mean()
footnote(fig, -0.02, f"格内：论文数 / 比较条数（一篇可落入多格）；颜色深浅按论文数。锂量未报告的比较占 {nun:.0%}。")
save(fig, "图1_证据分布")

# ---------- 图2 ----------
dec = main[main["D6 胜方"].isin(["强者胜", "弱者胜"])]
per = dec.groupby(["组", "A2 论文号"])["D6 胜方"].agg(lambda s: "强" if set(s) == {"强者胜"} else ("弱" if set(s) == {"弱者胜"} else "混"))
tab = per.reset_index().pivot_table(index="组", columns="D6 胜方", aggfunc="size", fill_value=0).reindex(COLS).fillna(0)
for c in ("强", "弱", "混"):
    if c not in tab:
        tab[c] = 0
undec = {g: len(set(main[main["组"] == g]["A2 论文号"]) - set(dec[dec["组"] == g]["A2 论文号"])) for g in COLS}
fig, ax = plt.subplots(figsize=(8.2, 5.4))
y = list(range(len(COLS)))[::-1]
ax.barh(y, -tab["强"], color=C_STRONG, height=0.62, label="强溶剂化一侧胜")
ax.barh(y, tab["弱"], color=C_WEAK, height=0.62, label="弱溶剂化一侧胜")
for yi, g in zip(y, COLS):
    s, w, x = int(tab.loc[g, "强"]), int(tab.loc[g, "弱"]), int(tab.loc[g, "混"])
    if s:
        ax.text(-s - 0.15, yi, str(s), ha="right", va="center", fontsize=9, color=C_STRONG)
    if w:
        ax.text(w + 0.15, yi, str(w), ha="left", va="center", fontsize=9, color=C_WEAK)
    side = []
    if x:
        side.append(f"两侧都有 {x}")
    if undec[g]:
        side.append(f"胜方未判 {undec[g]}")
    ax.text(10.6, yi, "；".join(side), ha="left", va="center", fontsize=8, color="#777777")
ax.axvline(0, color="#333333", linewidth=0.8)
ax.set_yticks(y, COLS)
ax.set_xlim(-9.5, 10.5)
ax.set_xticks(range(-8, 11, 2), [str(abs(v)) for v in range(-8, 11, 2)])
ax.set_xlabel("论文数（同一篇、同一指标只计一次）")
for name, a, b in BLOCKS[:3]:
    top, bot = y[a] + 0.45, y[b - 1] - 0.45
    ax.annotate("", xy=(-9.4, top), xytext=(-9.4, bot), arrowprops=dict(arrowstyle="-", color="#999999", linewidth=1.2), annotation_clip=False)
    ax.text(-9.25, (top + bot) / 2, name, rotation=90, ha="left", va="center", fontsize=8, color="#777777")
    if b < len(COLS):
        ax.axhline(y[b - 1] - 0.5, color="#DDDDDD", linewidth=0.8)
ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, frameon=False, fontsize=9)
ax.set_title("图2  各指标由哪一侧胜出（按论文计）", loc="left", fontsize=12, pad=26)
footnote(fig, 0.0, "胜方 = 溶剂化强弱方向（来自同篇可比描述符）与观察方向合成；方向不明、差异小的不计入条形。"
                   "'两侧都有' = 同一篇里该指标既有强侧胜也有弱侧胜（通常是不同配方对或条件）。")
save(fig, "图2_各指标胜方")

# ---------- 图3 ----------
def names(pid):
    d = json.load(open(os.path.join(JDIR, f"{pid}.json"), encoding="utf-8"))["electrolytes"]
    out = {}
    for k, e in d.items():
        n = e["name"].split("（")[0].split("：")[0].strip()
        if len(n) > 18:
            n = e["solvent"].split(" ")[0]
        out[k] = n
    return out


NAMES = {p: names(p) for p in m["A2 论文号"].unique()}
NAMES["S51"].update({"I1": "1 M LiTFSI/IL", "I2": "2 M LiTFSI/IL", "I3": "3 M LiTFSI/IL"})
FLIP = {"A更好": "A更差", "A更差": "A更好"}


def eid(v):
    """主表 B1/B2 列为'编号：名称'，取编号"""
    return str(v).split("：")[0].strip()
ok = ac[(ac["主层"] == "是") & (ac["指标数"] >= 2) & ~ac["判定（初步）"].isin(["仅单一指标（不可判定）", "无可判定方向"])]
CAT_ORDER = ["随运行时间变化", "跨指标权衡", "同一指标取值点间方向不一（非容量）", "一致（弱者全胜）", "一致（强者全胜）", "一致（强弱未定）"]
known, unknown = [], []
for _, r in ok.iterrows():
    pid, (a, b), cond = r["论文"], [x.strip() for x in r["配方对（A / B）"].split("/")], r["条件"]
    rows = main[(main["A2 论文号"] == pid) & (main["A1 行号"].isin(
        [l.split("：")[0] for l in str(r["涉及行（指标｜取值点 → A 方向｜胜方）"]).split("\n")]))]
    if rows.empty:
        continue
    weak_side = None
    for _, x in rows.iterrows():
        if x["D6 胜方"] in ("强者胜", "弱者胜") and x["D4 观察方向"] in ("A更好", "A更差"):
            a_wins = x["D4 观察方向"] == "A更好"
            a_is_weak = (x["D6 胜方"] == "弱者胜") == a_wins
            weak_side = eid(x["B1 电解液A"]) if a_is_weak else eid(x["B2 电解液B"])
            break
    cells = defaultdict(set)
    for _, x in rows.iterrows():
        obs = x["D4 观察方向"] if eid(x["B1 电解液A"]) == a else FLIP.get(x["D4 观察方向"], x["D4 观察方向"])
        g = GROUP.get(x["D1 指标"])
        if g is None:
            continue
        if obs in ("A更好", "A更差"):
            if weak_side:
                cells[g].add("W" if (obs == "A更好") == (a == weak_side) else "S")
            else:
                cells[g].add("A" if obs == "A更好" else "B")
        elif obs == "差异小":
            cells[g].add("E")
        else:
            cells[g].add("U")
    cc = rows.iloc[0]
    es = cc["C17 E/S 档"].split("(")[0].replace("未知", "E/S 未知")
    ld = "载量未知" if cc["C17 载量档"] == "未知" else f"{cc['C17 载量档']} mg"
    li = "锂量未报告" if cc["C17 锂量档"] == "未报告" else f"{cc['C17 锂量档']}锂"
    hot = "·高温" if cc["C17 温度档"] == "高温" else ""
    tag = f"［{es}·{ld}·{li}{hot}］{cond}"
    nm = NAMES[pid]
    if weak_side:
        strong = b if weak_side == a else a
        lab = f"{pid}  {nm[weak_side]}（弱）vs {nm[strong]}  {tag}"
        known.append((CAT_ORDER.index(r["判定（初步）"]), pid, lab, r["判定（初步）"], cells))
    else:
        lab = f"{pid}  甲 {nm[a]} vs 乙 {nm[b]}  {tag}"
        unknown.append((CAT_ORDER.index(r["判定（初步）"]), pid, lab, r["判定（初步）"], cells))


def cellval(s):
    d = s - {"U", "E"}
    if len(d) > 1:
        return "M"
    if d:
        return d.pop()
    return "E" if "E" in s else ("U" if s else None)


COLOR = {"W": C_WEAK, "S": C_STRONG, "A": C_A, "B": C_B, "E": C_SMALL, "U": C_UNK, "M": C_MIX}
SHORT = {"随运行时间变化": "时间反转", "跨指标权衡": "跨指标权衡", "同一指标取值点间方向不一（非容量）": "同指标不一",
         "一致（弱者全胜）": "弱侧全胜", "一致（强者全胜）": "强侧全胜", "一致（强弱未定）": "一致"}
for lst in (known, unknown):
    lst.sort(key=lambda t: (t[0], int(t[1][1:])))
nk, nu = len(known), len(unknown)
for k, (lst, fname, title, legend, extra) in enumerate([
        (known, "图3a_配对指纹_强弱已知", "图3a  配对指纹：溶剂化强弱已知的配对（颜色按强 / 弱一侧）",
         [(C_WEAK, "弱溶剂化一侧更好"), (C_STRONG, "强溶剂化一侧更好")], ""),
        (unknown, "图3b_配对指纹_强弱未定", "图3b  配对指纹：强弱未定的配对（文中无可比描述符，颜色按甲 / 乙）",
         [(C_A, "甲更好"), (C_B, "乙更好")], "S28 的强弱只有文献 DN 代理（不可比），S40、S53 文中无描述符。")]):
    fig, ax = plt.subplots(figsize=(12.5, 0.33 * len(lst) + 2.4))
    for i, (_, pid, lab, cat, cells) in enumerate(lst):
        yy = len(lst) - 1 - i
        for j, col in enumerate(COLS):
            v = cellval(cells.get(col, set()))
            if v:
                ax.add_patch(Rectangle((j + 0.06, yy + 0.08), 0.88, 0.84, color=COLOR[v], linewidth=0))
            else:
                ax.add_patch(Rectangle((j + 0.06, yy + 0.08), 0.88, 0.84, facecolor="white", edgecolor="#EEEEEE", linewidth=0.6))
        ax.text(len(COLS) + 0.15, yy + 0.5, SHORT[cat], va="center", fontsize=8, color="#555555")
    ax.set_xlim(0, len(COLS) + 1.4); ax.set_ylim(0, max(1, len(lst)))
    ax.set_yticks([len(lst) - 1 - i + 0.5 for i in range(len(lst))], [t[2] for t in lst], fontsize=8)
    ax.xaxis.tick_top()
    ax.set_xticks([j + 0.5 for j in range(len(COLS))], COLS, rotation=35, ha="left", fontsize=8.5)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    for _, a_, b_ in BLOCKS[:3]:
        ax.axvline(b_, color="#888888", linewidth=0.8, linestyle=":")
    hand = [Patch(color=c, label=l) for c, l in legend] + [Patch(color=C_MIX, label="同格内方向相反"), Patch(color=C_SMALL, label="差异小"),
                                                           Patch(facecolor=C_UNK, edgecolor="#CCCCCC", label="方向不明"),
                                                           Patch(facecolor="white", edgecolor="#DDDDDD", label="未比较")]
    ax.legend(handles=hand, loc="upper left", bbox_to_anchor=(1.0, 1.0), frameon=False, fontsize=8)
    ax.set_title(title, loc="left", fontsize=12, pad=70)
    footnote(fig, 0.0, "只列主层、同一条件下 ≥2 个指标的配对；行末标签为优势一致性初步分类（时间反转 = 同一量放电容量在不同圈数的相对优势改变）；"
                       "［］内为 E/S 档、硫载量档、锂量档，末尾为该文条件编号。" + extra)
    save(fig, fname)

# ---------- 图4 ----------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.15, 1], "wspace": 0.35})
lab = ["DME\n（对照）", "DME-\nETFE", "DME-\nBTFE", "DME-\nTFTFE", "DME-\nTFOFE"]
ce = [95.42, 95.31, 96.19, 96.81, 97.18]
life = [36, 32, 131, 154, 31]
x = range(5)
bars = a1.bar(x, life, color=[C_STRONG, "#9DB9D5", "#6E98C4", C_WEAK, "#1F3F66"], width=0.6)
for xi, v in zip(x, life):
    a1.text(xi, v - 10, f"{v} 圈", ha="center", fontsize=9, color="white")
a1.set_ylabel("Li‖S 寿命（容量保持 70% 的圈数）")
a1.set_xticks(list(x), lab, fontsize=9)
a1.set_ylim(0, 185)
a1b = a1.twinx()
a1b.plot(list(x), ce, "o-", color="#333333", linewidth=1.5)
for xi, v in zip(x, ce):
    a1b.text(xi, v + 0.12, f"{v:.2f}", ha="center", fontsize=8, color="#333333")
a1b.set_ylabel("Li‖Ni CE（%，Aurbach 法）")
a1b.set_ylim(94.5, 98.2)
a1b.spines["right"].set_visible(True); a1b.spines["top"].set_visible(False)
a1.annotate("Li+ 溶剂化能力 →  逐级减弱", xy=(0.02, -0.2), xycoords="axes fraction", fontsize=8.5, color="#555555")
a1.text(4, 60, "锂 CE 最高\n寿命最短", ha="center", fontsize=8.5, color="#1F3F66")
a1.set_title("（a）S33：氟化醚共溶剂梯度（E/S 5、40 µm 锂）", loc="left", fontsize=10)
items = [("Li‖Cu CE（%）", 99.19, 99.66), ("Li‖S 寿命（圈）*", 150, 300),
         ("第 100 圈正极硫保留（%，HUGS）", 54.7, 76.9), ("首周静置容量损失（%，越低越好）", 34.2, 8)]
for i, (nm, eb, dm) in enumerate(items):
    base = (len(items) - 1 - i) * 1.25
    mx = max(eb, dm)
    a2.barh(base + 0.2, eb / mx, height=0.36, color=C_STRONG)
    a2.barh(base - 0.2, dm / mx, height=0.36, color=C_WEAK)
    a2.text(eb / mx + 0.02, base + 0.2, f"{eb:g}", va="center", fontsize=8.5)
    a2.text(dm / mx + 0.02, base - 0.2, f"{dm:g}", va="center", fontsize=8.5)
    a2.text(0, base + 0.48, nm, va="bottom", fontsize=9)
a2.set_yticks([]); a2.set_ylim(-0.55, (len(items) - 1) * 1.25 + 0.85)
a2.set_xlim(0, 1.25); a2.set_xticks([])
a2.spines["bottom"].set_visible(False); a2.spines["left"].set_visible(False)
a2.text(0.0, -0.75, "首圈容量：E-baseline 更高（作者归因黏度低、润湿好；原文未给数值）", fontsize=8.5, color=C_STRONG)
a2.legend(handles=[Patch(color=C_STRONG, label="E-baseline（DME/DOL，强）"), Patch(color=C_WEAK, label="1.0M-DMFN（DME/2-MeTHF/TFEO，弱）")],
          loc="lower left", bbox_to_anchor=(0.0, 1.0), frameon=False, fontsize=8.5, ncol=1)
a2.set_title("（b）S32：初始容量 vs 持续性能与库存", loc="left", fontsize=10, pad=46)
fig.suptitle("图4  两个案例：初始优势与持续优势不在同一侧", x=0.01, ha="left", fontsize=12, y=1.04)
footnote(fig, -0.06, "数值取自原文（S33 Fig. 4；S32 正文与 Fig. 4）。*S32 E-baseline 寿命 150 圈由'寿命为基准两倍'反推，非原文直接给出；"
                     "静置损失 DMFN 为 0.6–1.2 M 各浓度的概括值（约 8%）。")
save(fig, "图4_案例")

# ---------- 图5 ----------
mech = json.load(open(MECH, encoding="utf-8"))["rows"]
# 证据状态由人工从机制判别表各行'直接测到 / 间接或推断 / 竞争解释'归纳：●直接测到  ◐推断或间接  ○列为竞争解释但未测
CODE = {
    "M01": {"K1": ("◐", "CE、寿命反推"), "K3": ("○", "")},
    "M02": {"K1": ("◐", "CE 反推"), "K2": ("●", "GITT、Rct、Ea")},
    "M03": {"K1": ("◐", "负极 XANES、CE"), "K2": ("●", "GITT、Ea（早期）")},
    "M04": {"K3": ("◐", "E/S 加大寿命变长"), "X": ("●", "电压示短路")},
    "M05": {"K1": ("◐", "溶解度、60 °C CE")},
    "M06": {"K2": ("◐", "还原峰、放电曲线"), "K3": ("◐", "凝胶化推断")},
    "M07": {"K1": ("●", "第 40 圈剩余锂"), "K3": ("○", "")},
    "M08": {"X": ("◐", "对照不一（LiNO3 等）")},
    "M09": {"K1": ("◐", "化学浸泡 TGC"), "K3": ("◐", "Rbulk 剧增")},
    "M10": {"K1": ("●", "剩余锂 > 放电容量"), "K2": ("◐", "TFOFE 堵孔、Rct"), "K3": ("●", "QNMR + 补液恢复")},
}
JUDGE = {"M01": "不能", "M02": "不能", "M03": "部分", "M04": "部分（两条冲突）", "M05": "部分", "M06": "不能", "M07": "部分",
         "M08": "部分", "M09": "部分（倾向 K3）", "M10": "是（基准组）"}
KC = [("K1", "K1 不可逆库存损失\n（活性锂 / 硫）"), ("K2", "K2 可逆传输 /\n转化限制"), ("K3", "K3 电解液组成\n演化或耗竭"), ("X", "其他\n（短路、对照效应）")]
fig, ax = plt.subplots(figsize=(11.5, 5.6))
n = len(mech)
for i, r in enumerate(mech):
    yy = n - 1 - i
    for j, (k, _) in enumerate(KC):
        sym, txt = CODE.get(r["编号"], {}).get(k, ("", ""))
        fc = {"●": "#2F6F9F", "◐": "#A9C8E3", "○": "#FFFFFF"}.get(sym, "#FAFAFA")
        ax.add_patch(Rectangle((j + 0.04, yy + 0.08), 0.92, 0.84, facecolor=fc, edgecolor="#DDDDDD" if sym != "○" else "#2F6F9F",
                               linewidth=0.8, linestyle="-" if sym != "○" else "--"))
        if txt:
            ax.text(j + 0.5, yy + 0.5, txt, ha="center", va="center", fontsize=7.8, color="white" if sym == "●" else "#222222")
        elif sym == "○":
            ax.text(j + 0.5, yy + 0.5, "未测", ha="center", va="center", fontsize=7.8, color="#2F6F9F")
    ax.text(len(KC) + 0.1, yy + 0.5, JUDGE[r["编号"]], va="center", fontsize=8.5,
            color="#2F6F9F" if JUDGE[r["编号"]].startswith("是") else "#444444")
lab = [f"{r['编号']}  {r['论文（证据表行）'].split('（')[0]}  {r['一致性类型'].split('：')[0]}" for r in mech]
ax.set_yticks([n - 1 - i + 0.5 for i in range(n)], lab, fontsize=8.5)
ax.set_xticks([j + 0.5 for j in range(len(KC))] + [len(KC) + 0.55], [k[1] for k in KC] + ["文献能否\n先判"], fontsize=8.5)
ax.xaxis.tick_top()
ax.set_xlim(0, len(KC) + 1.2); ax.set_ylim(0, n)
for s in ax.spines.values():
    s.set_visible(False)
ax.tick_params(length=0)
ax.legend(handles=[Patch(facecolor="#2F6F9F", label="直接测到"), Patch(facecolor="#A9C8E3", label="间接 / 由表现反推"),
                   Patch(facecolor="white", edgecolor="#2F6F9F", linestyle="--", label="列为竞争解释，未测")],
          loc="upper left", bbox_to_anchor=(0.0, -0.01), ncol=3, frameon=False, fontsize=8.5)
ax.set_title("图5  机制判别表（草稿）：每个案例的候选机制有没有被直接测到", loc="left", fontsize=12, pad=46)
footnote(fig, 0.0, "草稿，未经人工复核。M06 为跨论文对比（S06 vs S16 / S19），M08 为'弱者全胜 / 强者全胜'反例组。"
                   "超出 10 行上限未列：S32（第 100 圈 HUGS 直接测硫、金属锂保留，K1 直接测到）、S37（趋势层，无配对行）。")
save(fig, "图5_机制判别表")
print("输出：", OUT, sorted(os.listdir(OUT)))
print("图3 行数：强弱已知", nk, "，强弱未定", nu)
