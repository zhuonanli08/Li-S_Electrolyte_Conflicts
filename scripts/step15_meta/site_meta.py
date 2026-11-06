"""结果网站“05 · Meta & attribution”标签页（11-06 用户要求）：读 D_site.py 写的 网站数据.json，生成页面 HTML 与表格 JS。
由 scripts/step13s_site.py 调用；图由 D_site.py figs 预先画到网站 图/ 目录。界面英文；读原文笔记是中文，照原样显示并注明。
"""
import html
import json
import math
from pathlib import Path

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
DATA = ROOT / "output" / "meta网站_313篇_2026-11-06" / "网站数据.json"
CLASSES = ["首圈容量", "每圈衰减率", "全电池CE", "LiCu_CE"]
EN_CLASS = {"首圈容量": "Initial capacity", "每圈衰减率": "Fade per cycle", "全电池CE": "Full-cell CE", "LiCu_CE": "Li‖Cu CE"}
EN_PAIR = {"同测试、不同配方": "same test", "跨测试、不同配方": "across tests", "同配方、换条件": "same formulation, new conditions"}
EN_CHANGE = {"改浓度/配比": "Concentration / ratio", "高浓": "High concentration", "局部高浓": "Localised high concentration",
             "换溶剂（其他）": "Solvent swap (other)", "加/换氟化醚": "Add / swap fluorinated ether", "LiNO₃ 用量": "LiNO₃ amount",
             "加有机硫": "Add organosulfur", "加介体": "Add redox mediator", "加含碘添加剂": "Add iodide", "加其他添加剂": "Add other additive",
             "换主盐": "Salt swap", "组成不明": "Composition unknown"}
EN_DROP = {"非主层": "outside main layer (SPAN, Li₂S, no Li anode…)", "非同条件结果": "flagged “not same conditions” at extraction",
           "结果被限制剔除": "excluded by field restrictions", "论文不可用": "paper unusable for performance", "<10 或 >1675": "capacity < 10 or > 1675 mAh g⁻¹",
           "引用他文数据": "values quoted from other papers (P293)", "非电解液比较": "not an electrolyte comparison (P143, P272, P371)"}
REASON = [("Test conditions differ", ("条件不同", "取值点不同")), ("Another change mixed in", ("混了别的改动",)),
          ("Reference unusually weak or strong", ("参照很弱或很强",)), ("No defined direction, or sides swapped", ("改动方向不同", "实验/对照方向标反")),
          ("Data or grouping error", ("归组或提取问题",)), ("Metric artefact or within noise", ("指标放大", "指标问题", "差异小于噪声")),
          ("Genuine effect", ("真实大效应", "真实机制差异", "符合描述符趋势"))]
EN_DESC = {"ln_配位位点每Li": "coordinating sites per Li⁺", "ln_Li总浓度": "Li⁺ concentration", "溶剂_含氟分子比例": "fluorinated-solvent fraction",
           "LiNO3_M": "LiNO₃", "稀释剂摩尔比例": "diluent fraction", "aF": "anion F", "醚氧数": "ether O", "F/O": "F/O"}
VERD = {"✅": "clear", "🔶": "lead", "⚠️": "data issue", "❌": "not found"}


def e(x):
    return html.escape(str(x))


def reason_of(cat):
    first = cat.split("；")[0]
    return next((en for en, keys in REASON if any(k in first for k in keys)), "Other")


def f(x, d=2):
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"


def leak_note() -> str:
    """插在 04 · Modelling 页开头的更正说明。"""
    return ('<div class="callout warn"><b>Correction (6 Nov).</b> The fade-per-cycle result on this page (test-set R² 0.32) included a leak: the number of '
            'cycles entered the model, and across papers it tracks the outcome (stable cells are cycled longer; reported total loss is 9–59% whatever the cycle count). '
            'Without cycle count the dev-set best drops to 0.23 and the re-examined test-set R² is <b>0.14 (−0.24 to 0.35)</b>; the test set was used for the second time. '
            'Separately, the full-cell CE configuration was picked from a stale record. See <a href="#meta" onclick="$(\'nav button[data-panel=meta]\').click();return false">'
            '05 · Meta &amp; attribution</a> for the score card.</div>')


def meta_panel():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    flow = d["数据流"]
    # ---------- 数据流表 ----------
    fr = []
    for c in CLASSES:
        x = flow[c]
        drops = "; ".join(f"{EN_DROP.get(k, k)} {v}" for k, v in x["测量剔除"].items() if v)
        fr.append(f"<tr><td>{EN_CLASS[c]}</td><td>{x['测量论文']}</td><td>{x['测量点']}</td><td>{x['比较论文']}</td>"
                  f"<td>{x['比较'].get('同测试、不同配方', 0)}</td><td>{x['比较'].get('跨测试、不同配方', 0)}</td><td>{x['比较'].get('同配方、换条件', 0)}</td>"
                  f"<td>{x['跨温度剔除']}</td><td class='note'>{e(drops)}</td></tr>")
    flow_tbl = ("<div class='table-wrap'><table><tr><th>Performance</th><th>Papers</th><th>Measurements</th><th>Papers with ≥ 2</th><th>Same test</th>"
                "<th>Across tests</th><th>Same formulation, new conditions</th><th>Dropped: temperatures differ &gt; 10 °C</th><th>Measurements not used, and why</th></tr>"
                + "".join(fr) + "</table></div>")
    # ---------- 记分卡 ----------
    sr = []
    for r in d["记分卡"]:
        c = r["类别"]; s = r["改动模型"]; a = r["方案A"]; b = r["方案B"]
        badge = lambda ok: '<span class="badge">beats baseline</span>' if ok else '<span class="badge no">no</span>'
        a_txt = (f"{', '.join(EN_DESC.get(x, x) for x in a['描述符'])}<br>dev {f(a['开发'][0])} vs {f(a['开发'][1])} {badge(a['开发通过'])}<br>test {f(a['考试'][0])} vs {f(a['考试'][1])} {badge(a['考试通过'])}"
                 if a["描述符"] else "no descriptor passed the screening rule")
        b_txt = (f"dev MSE {f(b['开发'][0])} vs {f(b['开发'][1])} {badge(b['开发通过'])}<br>test MSE {f(b['考试'][0])} vs {f(b['考试'][1])} {badge(b['考试通过'])}")
        sr.append(f"<tr><td>{EN_CLASS[c]}</td><td>dev {f(s['开发'])} · test <b>{f(s['考试'])}</b> ({f(s['区间'][0])} to {f(s['区间'][1])})"
                  f"{'<br><span class=note>' + e(s['备注']) + '</span>' if s['备注'] else ''}</td><td>{a_txt}</td><td>{b_txt}</td></tr>")
    score = ("<div class='table-wrap'><table><tr><th>Performance</th><th>Change model (step 14 · R² of within-paper differences)</th>"
             "<th>Plan A · ranking within a paper (pair concordance: model vs. conditions only; 0.5 = chance)</th>"
             "<th>Plan B · anchor prediction (MSE: full model vs. “same as the anchor”)</th></tr>" + "".join(sr) + "</table></div>")
    # ---------- 读原文表 ----------
    U = d["矛盾单元"]
    cols = ["Performance", "Change", "Paper", "Type", "Pooled ×", "This paper ×", "Verdict", "Main reason", "Reading note (Chinese)", "Evidence"]
    rows = []
    for k, u in sorted(U.items()):
        c, g, p = k.split("|")
        j = u.get("判定") or {}
        rows.append([EN_CLASS[c], EN_CHANGE.get(g, g), p, {"方向相反": "opposite direction", "幅度异常": "> 3× off"}.get(u["类型"], u["类型"]),
                     round(u["本组合并倍数"], 2), round(u["本篇平均倍数"], 2), f"{j.get('判定', '')} {VERD.get(j.get('判定'), '')}",
                     reason_of(j.get("归类", "")), j.get("原因", ""), j.get("依据", "")])
    import numpy as np
    sd = {c: float(np.std([x["相对中位数_ln"] for x in d["实验室差异"][c]["标准醚各篇"]], ddof=1)) for c in CLASSES}
    spread = f"×/÷ {math.exp(min(sd.values())):.1f} ({EN_CLASS[min(sd, key=sd.get)]}) to ×/÷ {math.exp(max(sd.values())):.1f} ({EN_CLASS[max(sd, key=sd.get)]})"
    mods = d["调节因素"]
    best = min(mods, key=lambda m: m["置换p"])
    n_ok = sum(m["成立"] for m in mods)
    mod_txt = (f"across {len(mods)} moderator tests (paper-level permutation test, Benjamini–Hochberg) "
               + (f"{n_ok} survive" if n_ok else "none survives")
               + f"; the strongest lead is {EN_CLASS[best['类别']].lower()} · {EN_CHANGE.get(best['主改动'], best['主改动']).lower()} varying with "
               + f"{best['调节因素'].replace('条件:', '').replace('ln_ES', 'E/S').replace('载量', 'sulfur loading').replace('含硫', 'cathode S content').replace('ln_倍率', 'rate')} "
               + f"({best['论文']} papers, permutation p = {best['置换p']:.3f}, q = {best['q']:.2f})")
    nv = {v: sum(1 for u in U.values() if (u.get("判定") or {}).get("判定") == v) for v in ("✅", "🔶", "⚠️")}
    figs = [("图M1_实验室差异与电解液效应.html", 960, "Fig. M1 · One electrolyte across labs vs. changing the electrolyte within a test",
             "Blue: each paper’s standard ether (≈ 1 M LiTFSI, DOL:DME 1:1, any LiNO₃) relative to the median paper. Orange: each same-test comparison in which the "
             "electrolyte was changed. For every metric the blue band is about as wide as, or wider than, the orange one — the same electrolyte differs between labs "
             "as much as electrolytes differ within a lab. Absolute numbers from different papers therefore cannot be ranked directly."),
            ("图M2_描述符效应热图.html", 720, "Fig. M2 · Descriptor effects on the four metrics",
             "Each cell: the effect of moving one descriptor by one standard deviation, estimated only from within-paper differences (condition differences removed, "
             "paper effect as a random intercept). Strong colour and bold = significant after correcting for 16 tests (q &lt; 0.1); pale = direction only. Hover for the 95% "
             "interval, the number of papers in which the descriptor changes, fold stability and whether the absolute-value check (plan B) agrees."),
            ("图M3_权衡图.html", 640, "Fig. M3 · Trade-off map",
             "The same estimates placed on two axes. More coordinating sites per Li⁺ (more strongly solvating, more dilute) raises initial capacity but lowers Li‖Cu CE; "
             "a higher Li⁺ concentration does the opposite; a larger share of fluorinated solvent raises Li‖Cu CE without a visible capacity cost."),
            ("图M4_改动倍数.html", 960, "Fig. M4 · Pooled effect of each kind of change, direction aligned",
             "Comparisons are turned to one direction defined by composition alone (e.g. “more fluorinated solvent”), never by the outcome; blue = all within-paper "
             "comparisons, orange = same-test comparisons only. Multipliers are relative to each paper’s own reference: multiply by your own standard-ether value to get a number."),
            ("图M5_矛盾原因.html", 480, "Fig. M5 · Why papers seem to disagree",
             f"{len(U)} cases in which a paper’s result runs against the pooled direction of its group, or is more than 3× off it. Each was read against the source "
             f"sentences, the extraction’s comparison notes and linked mechanisms ({nv['✅']} clear, {nv['🔶']} lead, {nv['⚠️']} data issue). Most disagreements come from how "
             "the comparison was made, not from the chemistry.")]
    fc = "".join(f'<div class="card" style="grid-column:1/-1"><div class="card-top"><h3 style="margin:0">{t}</h3><a class="note" href="图/{fn}" target="_blank">open ↗</a></div>'
                 f'<p>{cap}</p><iframe class="fig" data-src="图/{fn}" height="{h}"></iframe></div>' for fn, h, t, cap in figs)
    sec = f"""<section id="meta" class="panel" hidden><div class="section-head"><h2>Meta-analysis &amp; attribution</h2><span class="note">313 papers (development + test set),
corrected data (v2) · within-paper comparisons · preliminary, AI-assisted, not yet confirmed item by item</span></div>
<div class="grid">
<div class="card"><span class="badge">Finding 1</span><h3>Labs differ more than electrolytes</h3><p>One standard ether varies {spread} between papers (SD of paper means) — as much as or more than a change of electrolyte within one test (Fig. M1). Results are reported as multipliers against each paper’s own reference; a specific value comes from your own standard ether × the multiplier.</p></div>
<div class="card"><span class="badge">Finding 2</span><h3>A solvation trade-off</h3><p>More coordinating sites per Li⁺ → higher initial capacity but lower Li‖Cu CE; higher Li⁺ concentration and more fluorinated solvent → higher Li‖Cu CE (Figs. M2–M3). No descriptor explains fade per cycle or full-cell CE.</p></div>
<div class="card"><span class="badge">Finding 3</span><h3>Most contradictions are comparison artefacts</h3><p>Of {len(U)} apparent contradictions read against the source, most trace to different test conditions, a second change mixed in, a weak or strong reference, undefined direction or data errors; genuine mechanism differences are rare (e.g. P108, amorphous sulfur in carbonate; P231, a solvate ionic liquid) (Fig. M5).</p></div>
</div>
<div class="callout"><b>How to read the multipliers.</b> Every effect is a within-paper ratio (capacity ratio; for fade and CE the inverse of the fade-rate or CE-loss ratio, so &gt; 1 always means better). Test-condition differences (E/S, sulfur loading and content, rate, pouch; for Li‖Cu current, capacity, protocol) are removed first with a ridge regression; cycle count is never used for fade (it tracks the outcome across papers). Comparisons whose two sides differ by more than 10 °C are left out.</div>
<h3 style="margin-top:22px">Data used</h3>{flow_tbl}
<div class="grid2" style="margin-top:18px">{fc}</div>
<h3 style="margin-top:26px">Did any model predict across papers?</h3><p class="note">Pre-registered criteria; each test-set result was computed once (the change model’s fade class twice, see note). Development scores are optimistic: settings were chosen on the development set.</p>{score}
<div class="callout warn">No approach beat its baseline on both the development and the test set. Conditions alone do not explain the disagreement between papers either: {mod_txt}.</div>
<h3 style="margin-top:26px">Contradiction candidates · reading notes</h3><p class="note">Reading notes and evidence IDs are in Chinese (Claude’s notes, written against the source sentences). Evidence IDs: M = main text, S = SI sentence.</p><div id="tMetaAttr"></div>
<div class="callout">Scripts: <span class="mono">scripts/step15_meta/</span> (common = data, A_meta, B_normalize, C_attribution, C_judgments, D_site). Data: <span class="mono">output/meta共同准备_313篇_v2_2026-11-06/</span>, <span class="mono">output/meta网站_313篇_2026-11-06/网站数据.json</span>. v2 fixes found while reading: components listed at 0 counted as absent; LiNO₃ change judged on the stated amount; “per-cycle retention” converted correctly (P052); high concentration also needs ≥ 3 mol L⁻¹ salt; non-electrolyte tests dropped.</div>
</section>"""
    js = f"table('tMetaAttr',{json.dumps(cols, ensure_ascii=False)},{json.dumps(rows, ensure_ascii=False)},{{selects:[0,1,6,7],placeholder:'Search paper, change, reason…',height:600}});"
    return sec, js
