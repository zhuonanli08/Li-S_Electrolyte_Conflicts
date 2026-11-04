"""step13s：结果网站（英文，单页、标签切换；版式参照用户提供的 electrolyte-atlas.html，11-04 用户要求）。

输出：网站/index.html（数据嵌在页面里）＋ 网站/图/ 下的交互图。双击 index.html 或项目根目录的 双击打开结果网站.bat 即可打开。
提取结果里的自由文字（取值点、物性描述）本身是中文，按原样显示并注明；其余界面、图、说明、核对结论为英文。
"""
from __future__ import annotations

import html
import json
import math

from step13_common import COMP, OUT, in_analysis, read_json
from step13_i18n import (BASIS, BATT, CAT, CSTATE, CTYPE, DIR, MODEL, PROP, SRC, STAGE, STD, STDKEY, STDSET,
                         recipe_en, statement_en, t)

SITE = OUT / "网站"
TESTKIND = {"全电池性能": "Full-cell performance", "机理电池": "Mechanistic cell", "表面表征": "Surface characterisation", "溶液性质": "Solution property",
            "对称电池": "Symmetric cell", "模拟": "Simulation", "锂铜效率": "Li‖Cu efficiency", "其他": "Other", "浸泡": "Soaking"}
CELL = {"扣式": "coin", "软包": "pouch", "其他": "other"}

CSS = """
:root{--ink:#172d32;--muted:#62777a;--bg:#f1f5f3;--paper:#fff;--line:#dbe5e1;--green:#007e70;--mint:#d8f3e9;--amber:#8b601a;--purple:#7159a7;--red:#a5423d}
*{box-sizing:border-box}body{margin:0;background:var(--bg);font:15px/1.55 'Segoe UI',Arial,sans-serif;color:var(--ink)}
button,input,select{font:inherit}button{cursor:pointer}a{color:var(--green)}
header{padding:22px 5%;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line);background:#fff}
.brand{font-size:17px;font-weight:750;letter-spacing:-.4px}.mark{display:inline-grid;place-items:center;background:var(--ink);color:#a8f2d7;width:34px;height:34px;border-radius:10px;margin-right:12px}
.meta{font-size:12px;color:var(--muted);letter-spacing:1px}main{max-width:1420px;margin:auto;padding:38px 5% 60px}
.hero{display:grid;grid-template-columns:1.5fr 1fr;gap:35px;align-items:center}.eyebrow{color:var(--green);font-size:11px;font-weight:750;letter-spacing:2px;text-transform:uppercase}
h1{font-size:clamp(36px,4.4vw,60px);line-height:1.06;letter-spacing:-2.5px;font-weight:650;margin:13px 0 18px}h1 span{color:var(--green)}
p{margin:8px 0;color:var(--muted)}.hero p{max-width:560px}
.pipeline{background:#e3ece7;border:1px solid #d3e1d8;border-radius:22px;padding:26px}.pipeline svg{width:100%;height:130px}
.flow{display:flex;justify-content:space-between;font-size:11px;font-weight:600;color:var(--muted)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);margin:30px 0 25px;gap:14px}.stat{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px 22px}
.stat strong{font-size:29px;letter-spacing:-1px;font-weight:650}.stat small{display:block;color:var(--muted);font-size:12px}
.stat .bar{height:4px;background:var(--line);margin-top:12px;border-radius:5px}.stat .bar i{display:block;height:100%;background:var(--green);border-radius:5px}
nav{display:flex;gap:6px;border-bottom:1px solid var(--line);margin-bottom:25px;overflow-x:auto}
nav button{background:none;border:0;padding:14px 17px;color:var(--muted);white-space:nowrap;border-bottom:3px solid transparent}
nav button[aria-selected=true]{color:var(--ink);border-color:var(--green);font-weight:700}.panel[hidden]{display:none}
.section-head{display:flex;justify-content:space-between;align-items:center;gap:20px;margin:6px 0 18px}
h2{font-size:25px;font-weight:650;letter-spacing:-.7px;margin:0}h3{font-size:18px;margin:10px 0 6px;line-height:1.3}
.note{font-size:12px;color:var(--muted)}.toolbar{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0 12px}
input{flex:1;min-width:200px;border:1px solid var(--line);border-radius:9px;padding:11px 15px;background:#fff;color:var(--ink)}
select{background:#fff;border:1px solid var(--line);border-radius:9px;padding:10px 13px;color:var(--ink)}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}.chips button{background:#fff;border:1px solid var(--line);border-radius:20px;padding:6px 12px;color:var(--muted);font-size:12px}
.chips button[aria-pressed=true]{background:var(--ink);color:#fff;border-color:var(--ink)}
.result-line{display:flex;justify-content:space-between;margin:10px 0;font-size:12px;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px;min-width:0}.card[hidden]{display:none}
.card-top{display:flex;justify-content:space-between;align-items:center;gap:6px}.card p{font-size:13px}
.badge{display:inline-block;border-radius:5px;padding:3px 7px;font-size:10px;font-weight:700;letter-spacing:.2px;background:var(--mint);color:#00614e}
.badge.trial{background:#fff0d7;color:var(--amber)}.badge.planned{background:#eee7f7;color:var(--purple)}.badge.no{background:#eceff0;color:#53656a}.badge.bad{background:#fbe3e1;color:var(--red)}
details{border-top:1px solid var(--line);margin-top:14px;padding-top:10px;font-size:12px}summary{cursor:pointer;font-weight:600;color:var(--ink)}
.detail{color:var(--muted);margin-top:10px;font-size:13px}.detail b{color:var(--ink)}
code,.formula{display:block;overflow-wrap:anywhere;white-space:pre-wrap;background:#f2f6f4;border-radius:6px;padding:10px;margin:8px 0;font:12px/1.6 Consolas,monospace;color:#24594e}
.callout{border-left:3px solid var(--green);padding:10px 15px;background:#e6efeb;margin:20px 0;font-size:13px;color:#46625d}
.callout.warn{border-color:#d08c2e;background:#fbf2e3;color:#6d4f1d}
.two{display:grid;grid-template-columns:1.25fr 1fr;gap:22px}.sheet{background:white;border:1px solid var(--line);border-radius:18px;padding:24px;min-width:0}
.step{display:grid;grid-template-columns:34px 1fr;gap:12px;margin:14px 0}.num{display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:var(--mint);font-size:11px;font-weight:700}
.step p{font-size:13px;margin:2px 0}.table-wrap{overflow:auto;background:#fff;border:1px solid var(--line);border-radius:14px}
table{width:100%;border-collapse:collapse;font-size:13px}td,th{text-align:left;padding:9px 11px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-size:11px;letter-spacing:.3px;background:#f7faf9;position:sticky;top:0;cursor:pointer;z-index:1}
tr.sel td{background:#eef8f3}tr.click{cursor:pointer}tr.click:hover td{background:#f5faf8}tr.detailrow td{background:#f7faf9;white-space:pre-wrap;font-size:12.5px;color:#36504c}
.fig{width:100%;border:1px solid var(--line);border-radius:14px;background:#fff;display:block}
.sides{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}.side{background:#f7faf9;border-radius:10px;padding:12px;font-size:12px;min-width:0}
.side b{display:block;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.quote{font:12px/1.55 Georgia,serif;color:#36504c;white-space:pre-wrap;overflow-wrap:anywhere}.mono{font-family:Consolas,monospace;font-size:12px;overflow-wrap:anywhere}
.footer{margin-top:40px;padding-top:20px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:15px;font-size:11px;color:var(--muted)}
:focus-visible{outline:3px solid #edb34b;outline-offset:3px}button:hover{filter:brightness(.95)}
@media(max-width:900px){.hero,.two,.sides{grid-template-columns:1fr}.pipeline{display:none}.grid,.grid2{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}}
"""

JS = r"""
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
function esc(x){return x===null||x===undefined?'':String(x).replace(/&/g,'&amp;').replace(/</g,'&lt;')}
$$('nav button').forEach(b=>b.onclick=()=>{
  $$('nav button').forEach(x=>x.setAttribute('aria-selected',x===b));
  $$('.panel').forEach(p=>p.hidden=p.id!==b.dataset.panel);
  $$('#'+b.dataset.panel+' iframe[data-src]').forEach(f=>{if(!f.getAttribute('src'))f.src=f.dataset.src});
  history.replaceState(null,'','#'+b.dataset.panel);
});
function table(id,cols,rows,opt){
  opt=opt||{}; const el=document.getElementById(id); const st={sort:null,asc:true}; const f={};
  const tb=document.createElement('div'); tb.className='toolbar';
  const q=document.createElement('input'); q.type='search'; q.placeholder=opt.placeholder||'Search…'; tb.appendChild(q);
  (opt.selects||[]).forEach(c=>{const s=document.createElement('select'); const v=[...new Set(rows.map(r=>r[c]))].filter(x=>x!==''&&x!==null).sort();
    s.innerHTML='<option value="">All · '+cols[c]+'</option>'+v.map(x=>'<option>'+esc(x)+'</option>').join(''); s.onchange=()=>{f[c]=s.value;draw()}; tb.appendChild(s)});
  const rl=document.createElement('div'); rl.className='result-line'; const cnt=document.createElement('span'); rl.appendChild(cnt);
  const hint=document.createElement('span'); hint.textContent=opt.detail?'Click a row to expand · click a header to sort':'Click a header to sort'; rl.appendChild(hint);
  const wrap=document.createElement('div'); wrap.className='table-wrap'; wrap.style.maxHeight=(opt.height||560)+'px';
  const tbl=document.createElement('table'); wrap.appendChild(tbl); el.append(tb,rl,wrap); q.oninput=draw;
  function draw(){const qq=q.value.trim().toLowerCase();
    let rs=rows.map((r,i)=>[r,i]).filter(([r])=>Object.entries(f).every(([c,v])=>!v||String(r[c])===v)&&(!qq||JSON.stringify(r).toLowerCase().includes(qq)));
    if(st.sort!==null)rs.sort((a,b)=>{const x=a[0][st.sort],y=b[0][st.sort],nx=parseFloat(x),ny=parseFloat(y);
      const r=(!isNaN(nx)&&!isNaN(ny))?nx-ny:String(x).localeCompare(String(y));return st.asc?r:-r});
    cnt.textContent=rs.length+' of '+rows.length+' rows';
    let h='<tr>'+cols.map((c,i)=>'<th data-i="'+i+'">'+c+'</th>').join('')+'</tr>';
    rs.forEach(([r,i])=>{h+='<tr data-k="'+i+'" class="'+(opt.detail?'click':'')+'">'+r.map(v=>'<td>'+esc(v)+'</td>').join('')+'</tr>'});
    tbl.innerHTML=h;
    tbl.querySelectorAll('th').forEach(th=>th.onclick=()=>{const i=+th.dataset.i;st.asc=st.sort===i?!st.asc:true;st.sort=i;draw()});
    if(opt.detail)tbl.querySelectorAll('tr[data-k]').forEach(tr=>tr.onclick=()=>{const n=tr.nextElementSibling;
      if(n&&n.classList.contains('detailrow')){n.remove();return}
      const d=document.createElement('tr');d.className='detailrow';d.innerHTML='<td colspan="'+cols.length+'">'+opt.detail(+tr.dataset.k)+'</td>';tr.after(d)});}
  draw();
}
$$('#ctype button').forEach(b=>b.onclick=()=>{$$('#ctype button').forEach(x=>x.setAttribute('aria-pressed',x===b));
  $$('.cand').forEach(c=>c.hidden=!(b.dataset.t==='all'||c.dataset.t===b.dataset.t))});
"""


def j(x) -> str:
    return json.dumps(x, ensure_ascii=False).replace("</", "<\\/")


def e(x) -> str:
    return html.escape("" if x is None else str(x))


def tr_counts(s: str, m: dict) -> str:
    """把“放电容量类×5；衰减类×2”这类计数串翻成英文。"""
    if not s:
        return ""
    out = []
    for part in s.split("；"):
        k, _, n = part.rpartition("×")
        out.append(f"{t(m, k)} ×{n}" if k else t(m, part))
    return "; ".join(out)


def pct(r):
    if r is None:
        return ""
    return f"≈ ±{round((math.exp(r) - 1) * 100)}%" if r < 10 else "diverged"


def pair_en(p: dict | None) -> str:
    if not p:
        return ""
    if p.get("翻转"):
        a, b, va, vb, d = p["B"], p["A"], p["B值"], p["A值"], {"变好": "变坏", "变坏": "变好"}.get(p["方向"], p["方向"])
    else:
        a, b, va, vb, d = p["A"], p["B"], p["A值"], p["B值"], p["方向"]
    return (f"{p['论文']} {p['测试']} · {a} ({va}) vs {b} ({vb})\n{t(STD, p['标准指标'])} · point (as extracted): {p['取值点']}\n"
            f"→ {a} {t(DIR, d)} than {b} ({t(BASIS, p['依据'])})\nchange: {' '.join(p['完整签名']) or '—'}")


def verdict_badge(v: str) -> str:
    cls = {"✅": "", "🔶": "trial", "⚠️": "bad", "❌": "no"}.get(v, "planned")
    lab = {"✅": "✅ Confirmed", "🔶": "🔶 Explained by an unaligned factor", "⚠️": "⚠️ Extraction issue", "❌": "❌ Not a contradiction"}.get(v, "Not reviewed")
    return f'<span class="badge {cls}">{lab}</span>'


def main() -> None:
    a, b, c, e13 = (read_json(f"step13{x}_汇总.json") for x in "abce")
    sts = read_json("表述.json")
    comp = {(r["论文"], r["配方"]): r for r in read_json("配方组成.json", COMP)}
    nres = read_json("归一化结果.json")
    cands = read_json("矛盾候选.json")
    finds = read_json("试跑发现.json")
    basis = read_json("标准条件依据.json")
    n_in = sum(in_analysis(s["性能类别"], s["阶段"]) for s in sts)
    vcount = {}
    for x in cands:
        vcount[x["判定"] or "—"] = vcount.get(x["判定"] or "—", 0) + 1
    vtxt = " · ".join(f"{k} {v}" for k, v in vcount.items()) or "none"

    # ---------- hero & stats ----------
    hero = f"""
<section class="hero"><div><div class="eyebrow">Pilot run · F-version extraction · 30 papers</div>
<h1>From papers to<br><span>comparable statements.</span></h1>
<p>Every reported performance value becomes one statement: the formulation, the properties reported by the same paper, the test conditions and the value.
Statements are normalised to one common test condition so that papers can be compared, then searched for contradictions that are checked against the source text.</p>
<p class="note">Preliminary · AI-assisted extraction and review, not yet confirmed item by item by the user.</p></div>
<div class="pipeline"><div class="eyebrow">Extract → State → Normalise → Contrast</div>
<svg viewBox="0 0 400 130" role="img" aria-label="Conceptual workflow, not data">
<g fill="#fff" stroke="#9fc4b8"><rect x="8" y="34" width="58" height="72" rx="6"/><rect x="16" y="26" width="58" height="72" rx="6"/></g>
<g stroke="#9fc4b8" stroke-width="3"><path d="M26 48h38M26 60h30M26 72h38M26 84h22"/></g>
<g stroke="#7faaa0" stroke-width="2" fill="none"><path d="M88 65h30M113 60l5 5-5 5M196 65h28M219 60l5 5-5 5M300 65h28M323 60l5 5-5 5"/></g>
<g fill="#007e70"><rect x="128" y="40" width="58" height="9" rx="4"/><rect x="128" y="56" width="44" height="9" rx="4" opacity=".7"/><rect x="128" y="72" width="52" height="9" rx="4" opacity=".5"/></g>
<g><circle cx="248" cy="40" r="5" fill="#9dc8b8"/><circle cx="262" cy="58" r="5" fill="#9dc8b8"/><circle cx="276" cy="50" r="5" fill="#007e70"/><circle cx="252" cy="80" r="5" fill="#9dc8b8"/><circle cx="284" cy="86" r="5" fill="#007e70"/><path d="M238 96L292 30" stroke="#7a6598" stroke-dasharray="4 4"/></g>
<g fill="none" stroke="#c2504a" stroke-width="2"><path d="M346 45l14 22-14 22M378 45l-14 22 14 22"/></g></svg>
<div class="flow"><span>Papers</span><span>Statements</span><span>Normalised</span><span>Conflicts</span></div>
<p class="note">Conceptual diagram · no data values</p></div></section>
<section class="stats">
<div class="stat"><strong>{c['表述条数']}</strong><small>Statements · {c['配方数']} formulations · {c['论文数']} papers</small><div class="bar"><i style="width:{100 * n_in / c['表述条数']:.1f}%"></i></div>
<small style="margin-top:8px">{n_in} in this analysis set</small></div>
<div class="stat"><strong>4</strong><small>Normalisation models · 6 model types compared</small><div class="bar"><i style="width:6%;background:#d08c2e"></i></div>
<small style="margin-top:8px">V1 within-paper R² ≈ 0 · see Normalisation</small></div>
<div class="stat"><strong>{len(cands)}</strong><small>Contradiction candidates · 5 rules</small><small style="margin-top:8px">{e(vtxt)}</small></div>
<div class="stat"><strong>{b['性能测试数']}</strong><small>Performance tests with parsed conditions</small><small style="margin-top:8px">cathode S content verified for 55 source texts</small></div>
</section>
<nav role="tablist">
<button role="tab" aria-selected="true" data-panel="overview">01 · Overview</button><button role="tab" aria-selected="false" data-panel="statements">02 · Statements</button>
<button role="tab" aria-selected="false" data-panel="normalise">03 · Normalisation</button><button role="tab" aria-selected="false" data-panel="conflicts">04 · Contradictions</button>
<button role="tab" aria-selected="false" data-panel="figures">05 · Figures</button><button role="tab" aria-selected="false" data-panel="data">06 · Methods &amp; data</button></nav>"""

    # ---------- 01 overview ----------
    fcards = "".join(f'<div class="card"><span class="badge {"trial" if k in (1, 2) else ""}">Finding {k + 1:02d}</span><p>{e(x)}</p></div>'
                     for k, x in enumerate(finds.get("findings_en", [])))
    pend = "".join(f"<li>{e(x)}</li>" for x in finds.get("pending_en", []))
    # 示例：进入分析、条件齐全、有物性的首圈放电容量表述
    full = lambda x: all(x["条件"][f]["值"] is not None for f in ("ES", "sulfur_loading", "S_content", "rate", "temperature"))
    good_prop = lambda x: any(p["来源类型"] == "实测" and p["数值"] is not None for k in ("离子电导率", "黏度") for p in x["物性"].get(k, []))
    known = lambda x: sum(x["条件"][f]["值"] is not None for f in ("ES", "sulfur_loading", "S_content", "rate", "temperature", "Li_thickness"))
    pool = [x for x in sts if in_analysis(x["性能类别"], x["阶段"]) and x["标准指标"] == "硫比放电容量" and good_prop(x)]
    s0 = max(pool, key=known) if pool else sts[0]
    overview = f"""<section id="overview" class="panel"><div class="section-head"><h2>What the pilot shows</h2>
<span class="note">Analysis set: rate capacity excluded · discharge capacity = first cycle only (your decision)</span></div>
<div class="grid">{fcards}</div>
<div class="callout warn"><b>Decisions still open</b><ul style="margin:6px 0 0 18px;padding:0">{pend}</ul></div>
<div class="two"><div class="sheet"><div class="eyebrow">How a statement is built · plan §8.7</div>
<div class="step"><span class="num">1</span><div><b>Formulation</b><p>Components with amounts as written in the paper, plus formulation-level elemental ratios (sO in three fluorination bins, aC, F/O, InOr).</p></div></div>
<div class="step"><span class="num">2</span><div><b>Properties</b><p>Only values the same paper reports for the same recipe; otherwise “not reported”. Nothing is filled in or inferred; names are unified first.</p></div></div>
<div class="step"><span class="num">3</span><div><b>Test conditions</b><p>E/S, sulfur loading, cathode sulfur content (electrode basis), Li thickness or N/P, rate, temperature, cell format and cycle number.</p></div></div>
<div class="step"><span class="num">4</span><div><b>Performance value</b><p>One value per statement, mapped to four performance classes. Mechanisms are not written into the statement; they stay linked by ID.</p></div></div></div>
<div class="sheet"><div class="eyebrow">Example statement</div><code>{e(statement_en(s0, comp.get((s0['论文'], s0['recipe']))))}</code>
<p class="note">Free-text fields copied from the extraction (sampling point, some property descriptions) are in Chinese and shown as recorded.</p></div></div></section>"""

    # ---------- 02 statements ----------
    cols = ["ID", "Paper", "Formulation", "Class", "Metric", "Value", "Unit", "Stage", "E/S", "S loading", "Cathode S %", "Rate C", "T °C", "Cell", "In analysis"]
    cv = lambda s, f: s["条件"][f]["值"] if s["条件"][f]["值"] is not None else ""
    rows, det = [], []
    for s in sts:
        rows.append([s["表述编号"], s["论文"], s["配方"] + (" (control)" if s["是否对照"] else ""), t(CAT, s["性能类别"]), t(STD, s["标准指标"]), s["数值原文"], s["单位"],
                     t(STAGE, s["阶段"]) + (f" {s['圈数']}" if s["阶段"] == "第 N 圈" else ""), cv(s, "ES"), cv(s, "sulfur_loading"), cv(s, "S_content"),
                     cv(s, "rate"), cv(s, "temperature"), CELL.get(cv(s, "cell_format"), ""), "yes" if in_analysis(s["性能类别"], s["阶段"]) else "no"])
        det.append(f"<b>Statement</b>\n{e(statement_en(s, comp.get((s['论文'], s['recipe']))))}\n\n<b>Source sentences</b>\n{e(s['原句'])}\n\n"
                   f"<b>Linked IDs (not part of the statement)</b> mechanisms: {e(', '.join(s['机制链接']) or '—')} · supporting measurements: {e(', '.join(s['支撑测量链接']) or '—')}"
                   + (f" · duplicate group {e(s['疑似重复组'])}" if s.get("疑似重复组") else ""))
    statements = f"""<section id="statements" class="panel" hidden><div class="section-head"><h2>{len(sts)} statements</h2>
<span class="note">One statement per reported performance value · values as reported (not normalised)</span></div>
<p>“In analysis = no” marks rate capacity and non-first-cycle discharge capacity, which this run leaves out of models, figures and contradiction search; they stay in the table.
Empty conditions mean the paper did not report them or they could not be derived.</p><div id="tStatements"></div></section>"""

    # ---------- 03 normalisation ----------
    vrows = "".join(
        f"<tr class='{'sel' if m['模型'] == r['主模型'] else ''}'><td>{e(t(CAT, n))}</td><td>{e(t(MODEL, m['模型']))}{' · <b>selected</b>' if m['模型'] == r['主模型'] else ''}</td>"
        f"<td>{m['V1篇内R2']}</td><td>{m['V1篇内RMSE(ln)']} <span class='note'>{pct(m['V1篇内RMSE(ln)'])}</span></td>"
        f"<td>{m['V1方向正确率']} <span class='note'>({m['V1方向对数']} pairs)</span></td><td>{m['V2提升R2']}</td>"
        f"<td>{m.get('V2 RMSE(ln)')} <span class='note'>{pct(m.get('V2 RMSE(ln)'))}</span></td><td>{m.get('V2基线RMSE(ln)')}</td><td>{m['越界率（非外推）']}</td></tr>"
        for n, r in nres.items() for m in r["模型比较"])
    v4 = "".join(f"<tr><td>{e(t(CAT, n))}</td><td>{e(t(MODEL, r['主模型']))}</td><td>{(r.get('V4') or {}).get('参与排名配方数', '—')}</td>"
                 f"<td>{(r.get('V4') or {}).get('名次相关_中位数', '—')} <span class='note'>{(r.get('V4') or {}).get('名次相关_2.5–97.5%', '')}</span></td>"
                 f"<td>{(r.get('V4') or {}).get('前5重合率_平均', '—')}</td></tr>" for n, r in nres.items())
    lab_common = {"E/S": "E/S (μL mg⁻¹)", "硫载量": "S loading (mg cm⁻²)", "正极含硫": "Cathode S (%)", "倍率": "Rate (C)", "温度": "Temperature (°C)"}
    brow = "".join(f"<tr><td>{lab_common.get(k, k)}</td><td>{v['按论文中位数']} <span class='note'>({v['论文数']} papers)</span></td>"
                   f"<td>{v['按表述中位数']} <span class='note'>({v['表述数']} statements)</span></td></tr>" for k, v in basis["共同条件"].items())
    bcls = "".join(f"<tr><td>{e(t(CAT, k.split('（')[0]))}{' (1st cycle)' if '首圈' in k else ''}</td><td>{v['倍率']['按论文中位数']}</td>"
                   f"<td>{' · '.join(f'{x}: {y}' for x, y in v['标准倍率覆盖（2 倍内条数/总数）'].items())}</td><td>{v['圈数']['按论文中位数']}</td></tr>"
                   for k, v in basis["按类"].items())
    std_rows = "".join(f"<tr><td>{e(t(CAT, n))}</td><td>{e(t(STDSET, sn))}</td><td>{e(' · '.join(f'{t(STDKEY, k)} {v}' for k, v in d.items()))}</td>"
                       f"<td>{r['标准醚基准'].get(sn)}</td></tr>" for n, r in nres.items() for sn, d in r["标准条件"].items())
    rec_en = {(s["论文"], s["配方"]): recipe_en(comp.get((s["论文"], s["recipe"])), s["配方文字"]) for s in sts}
    farmap = {"圈数": "cycles", "E/S": "E/S", "倍率": "rate", "载量": "loading", "电流": "current", "沉积容量": "plating capacity"}
    fr_cols = ["Class", "Condition", "Rank", "Rank interval", "Paper", "Formulation", "× vs std ether (CE: loss ×)", "Normalised value", "Interval", "Extrapolated", "Recipe"]
    fr_rows = [[t(CAT, x["类别"]), t(STDSET, x["标准条件"]), x["名次"] or "", x["名次区间"] or "", x["论文"], x["配方"] + (" (control)" if x["是否对照"] else ""),
                x["倍数"] if x["倍数"] is not None else x["损失倍数"], x["归一化值"], x["归一化值区间"],
                ", ".join(farmap.get(y, y) for y in x["外推"].split("；") if y) or "no", rec_en.get((x["论文"], x["配方"]), "")]
               for r in nres.values() for x in sorted(r["配方"], key=lambda z: (z["标准条件"], z["名次"] or 999))]
    norm = f"""<section id="normalise" class="panel" hidden><div class="section-head"><h2>Normalisation &amp; cross-paper comparison</h2><span class="badge trial">Preliminary · weak validation</span></div>
<div class="two"><div class="sheet"><div class="eyebrow">How it works</div><h3>One scoring function for all formulations</h3>
<p>Within one paper the cathode, process and lab are shared, so each paper's own level is removed and only within-paper differences train the model.
Inputs: formulation descriptors (sO in three bins, aC, F/O, InOr, LiNO₃ and main-salt concentration, other additives) and test conditions
(E/S, S loading, cathode S, rate, temperature, pouch; cycle number for retention and CE). One model per performance class; six model types compared.</p>
<div class="formula">y = f(formulation, condition) + paper effect + error
y_normalised = y + f(x, standard condition) − f(x, measured condition)
gain vs standard ether = exp[ f(formulation, std) − f(standard ether, std) ]
y = ln(value) for capacity and retention; y = −ln(100 − CE) for CE</div>
<p class="note">Conditions not reported in the paper are not converted. Statements far from the standard condition (cycles &gt;10×, E/S or rate &gt;2×, loading off by more than the standard value) are flagged as extrapolated and kept out of ranking and contradiction search.</p></div>
<div class="sheet"><div class="eyebrow">Validation methods · plan §8.7</div>
<div class="step"><span class="num">V1</span><div><b>Leave one paper out</b><p>Train without a paper, then predict the differences between its formulations. Can we rank formulations in an unseen paper? · done</p></div></div>
<div class="step"><span class="num">V2</span><div><b>Leave one test out</b><p>Hide one test condition of a paper and predict it; compared with guessing the paper's other-test mean. Is the condition correction reliable? · done</p></div></div>
<div class="step"><span class="num">V3</span><div><b>Leave out the only direct comparison</b><p>Can a pair compared in just one paper be inferred from the others? · not done: too few shared formulations in 30 papers</p></div></div>
<div class="step"><span class="num">V4</span><div><b>Resample papers</b><p>Retrain on bootstrap samples of papers; rank correlation and top-5 overlap. · done</p></div></div>
<div class="step"><span class="num">V5</span><div><b>Laboratory check</b><p>Measure selected formulations under the standard condition. · final step</p></div></div>
<p class="note">Plus a physical check: normalised S-specific capacity above 1672 mAh g⁻¹ (organosulfur co-solvents excepted) or retention above 100% counts as a violation.</p></div></div>
<h3 style="margin-top:28px">Validation results</h3>
<p class="note">R² near 1 is good; 0 equals “predict no difference”; negative is worse than that. RMSE is in ln units (0.2 ≈ ±22%; for CE it is the error in the per-cycle Li loss).
Direction = share of formulation-vs-control comparisons with the right sign (chance = 50%). Selection rule, fixed before running: among models with ≤5% physical violations, take the highest V2 skill.</p>
<div class="table-wrap"><table><tr><th>Class</th><th>Model</th><th>V1 R²</th><th>V1 RMSE</th><th>V1 direction</th><th>V2 skill R²</th><th>V2 RMSE</th><th>V2 baseline RMSE</th><th>Violations</th></tr>{vrows}</table></div>
<h3 style="margin-top:22px">V4 · ranking stability (selected model, common condition)</h3>
<div class="table-wrap"><table><tr><th>Class</th><th>Model</th><th>Formulations ranked</th><th>Rank correlation (median, 95% range)</th><th>Top-5 overlap</th></tr>{v4}</table></div>
<div class="callout warn"><b>Reading.</b> With 30 papers, V1 R² stays near zero: the formulation part of the model does not transfer to unseen papers, although the direction is often right (0.75 for first-cycle capacity, 0.87 for retention).
V2 is positive for first-cycle capacity (0.33) and retention (0.14), so the condition correction helps somewhat. CE has only 5 papers per type. The standard-ether baseline is a pilot choice pending your decision.</div>
<iframe class="fig" data-src="图/图5a_模型比较.html" height="600"></iframe>
<iframe class="fig" data-src="图/图5b_主模型验证散点.html" height="840" style="margin-top:14px"></iframe>
<div class="section-head" style="margin-top:32px"><h2>Standard condition</h2><span class="note">You chose one set for all classes; values follow the data-density rule</span></div>
<div class="two"><div class="sheet"><div class="eyebrow">Basis · one vote per paper</div><p>Each paper's own median first, then the median across papers, so data-rich papers do not dominate. For the rate, the share of data within 2× of a candidate value.</p>
<div class="table-wrap"><table><tr><th>Condition</th><th>Median across papers</th><th>Median across statements</th></tr>{brow}</table></div>
<div class="table-wrap" style="margin-top:12px"><table><tr><th>Class</th><th>Rate, paper median</th><th>Coverage within 2×</th><th>Cycle, paper median</th></tr>{bcls}</table></div></div>
<div class="sheet"><div class="eyebrow">Adopted</div><div class="table-wrap"><table><tr><th>Class</th><th>Set</th><th>Values</th><th>Std-ether baseline</th></tr>{std_rows}</table></div>
<p class="note">Common condition: E/S 10, S loading 1.5, cathode S 50%, 25 °C, coin, 0.2 C; retention at 200 cycles, full-cell CE at 100 cycles; Li‖Cu 0.5 mA cm⁻², 1 mAh cm⁻², 100 cycles.
Practical condition: E/S 5 and loading 4 (plan §7.8). To be recomputed on the full dataset.</p></div></div>
<div class="section-head" style="margin-top:32px"><h2>Cross-paper comparison</h2></div>
<iframe class="fig" data-src="图/图6_归一化跨篇排名.html" height="900"></iframe>
<iframe class="fig" data-src="图/图7_标准醚跨篇归一化前后.html" height="900" style="margin-top:14px"></iframe>
<h3 style="margin-top:22px">Ranking table</h3><div id="tRank"></div></section>"""

    # ---------- 04 contradictions ----------
    counts = {k: sum(x["类型"] == k for x in cands) for k in CTYPE}
    chips = f'<button data-t="all" aria-pressed="true">All · {len(cands)}</button>' + "".join(
        f'<button data-t="{k}" aria-pressed="false">{k} · {counts[k]}</button>' for k in CTYPE)
    rules = "".join(f"<tr><td><b>{k}</b></td><td>{e(v)}</td><td>{counts[k]}</td></tr>" for k, v in CTYPE.items())
    cc = []
    for x in cands:
        cc.append(f"""<div class="card cand" data-t="{x['类型']}"><div class="card-top"><span class="badge planned">{x['候选编号']} · {e(t(CTYPE, x['类型']))}</span>{verdict_badge(x['判定'])}</div>
<h3 style="margin-top:12px">{e(x.get('摘要_en') or x['摘要'])}</h3>
<div class="sides"><div class="side"><b>Paper A · {e(x['论文甲'])}</b><span class="mono" style="white-space:pre-wrap">{e(pair_en(x.get('甲对')) or x['甲例'])}</span></div>
<div class="side"><b>Paper B · {e(x['论文乙'])}</b><span class="mono" style="white-space:pre-wrap">{e(pair_en(x.get('乙对')) or x['乙例'])}</span></div></div>
<div class="detail"><b>Review.</b> {e(x.get('核对说明_en') or x['核对说明'] or 'not reviewed')}</div>
<div class="detail"><b>Likely cause.</b> {e(x.get('可能原因_en') or x['可能原因'])}<br><b>Mechanism clues.</b> {e(x.get('机制线索_en') or x['机制线索'])}<br><b>Evidence IDs.</b> {e(', '.join(x['依据句子']))}</div>
<details><summary>Source sentences</summary><div class="grid2" style="margin-top:10px"><div class="quote">{e(x['原句甲'])}</div><div class="quote">{e(x['原句乙'])}</div></div></details></div>""")
    skip = "; ".join(f"{t(CAT, s.split('（')[0])} (V1 R² = {s.split('= ')[-1].rstrip('）')})" for s in e13.get("未做 LOPO 的类别", []))
    conflicts = f"""<section id="conflicts" class="panel" hidden><div class="section-head"><h2>Contradiction candidates</h2><span class="note">Re-run after normalisation · every item checked against the source text</span></div>
<div class="table-wrap"><table><tr><th>Rule</th><th>What it looks for</th><th>Candidates</th></tr>{rules}</table></div>
<div class="callout"><b>Verdicts.</b> ✅ supported by the source and worth explaining · 🔶 values correct, but an unaligned factor or definition explains the gap · ⚠️ extraction or classification problem · ❌ not a contradiction.<br>
NORM: only 3 cross-paper pairs share the same formulation and none differs by ≥1.5× after normalisation. LOPO runs only where the selected model's V1 R² &gt; 0; skipped: {e(skip)}. FLIP: none in this analysis set.</div>
<div class="chips" id="ctype">{chips}</div><div class="grid2">{''.join(cc)}</div></section>"""

    # ---------- 05 figures ----------
    figs = [("图1a_配方组分共现网络.html", "Fig. 1a · Component co-occurrence", "Formulation only. Node size = formulations using the component; edge width = formulations containing both. Hover for counts; drag to zoom."),
            ("图1b_四部分共现网络.html", "Fig. 1b · Four-part co-occurrence", "Components, properties, condition tiers and performance tiers (tertiles of normalised values) appearing in the same statements; edges ≥10 statements."),
            ("图2a_配方物性弦图.svg", "Fig. 2a · Formulation × property chord", "Which component classes have which properties reported, counted per formulation; gaps show missing measurements."),
            ("图2b_四部分弦图.svg", "Fig. 2b · Four-group chord", "Component class, property, key test condition and performance class; ribbon width = statements containing both (≥15)."),
            ("图3_四部分聚类热图.html", "Fig. 3 · Clustered heat map", "One row per formulation; columns grouped into formulation, property, condition and normalised performance. Grey = not reported or extrapolated."),
            ("图4_表述文字向量图.html", "Fig. 4 · Statement text map", "English statements embedded with character n-grams and projected with UMAP; nearby points read alike. Switch colouring at top right.")]
    fc = []
    for fn, title, desc in figs:
        body = (f'<a href="图/{fn}" target="_blank"><img class="fig" src="图/{fn}" alt="{e(title)}"></a>' if fn.endswith(".svg")
                else f'<iframe class="fig" data-src="图/{fn}" height="{820 if "图3" in fn else 640}"></iframe>')
        fc.append(f'<div class="card"><div class="card-top"><h3 style="margin:0">{title}</h3><a class="note" href="图/{fn}" target="_blank">open ↗</a></div><p>{desc}</p>{body}</div>')
    figures = f"""<section id="figures" class="panel" hidden><div class="section-head"><h2>Association figures</h2><span class="note">Preliminary · 30 papers · association, not causation · duplicate statements counted once</span></div>
<div class="grid2">{''.join(fc)}</div></section>"""

    # ---------- 06 methods & data ----------
    al = read_json("指标别名表.json")
    a_cols = ["Metric as extracted", "Unit", "Test type", "Cell", "Class", "Standard metric", "Rows", "Numeric", "Papers", "Status"]
    a_rows = [[x["原名"], x["单位"], t(TESTKIND, x["测试类型"]), t(BATT, x["电池类型"]), tr_counts(x["性能类别"], CAT), tr_counts(x["标准指标"], STD),
               x["条数"], x["有数值条数"], x["论文数"], x["状态"]] for x in al]
    pal = read_json("物性别名表.json")
    p_cols = ["Standard property", "Name as extracted", "Values", "Papers", "Source type"]
    p_rows = [[t(PROP, x["标准物性"]), x["原名"], x["取值数"], ", ".join(x["论文"]), tr_counts(x["来源类型"], SRC)] for x in pal]
    ct = read_json("条件表.json")
    c_cols = ["Paper", "Test", "Type", "E/S", "S loading", "Cathode S %", "Li μm", "N/P", "Rate C", "T °C", "Cell"]

    def cval(r, f):
        x = r["条件"].get(f, {})
        v = x.get("值")
        if v is None and x.get("按配方"):
            v = "; ".join(f"{k}={y['值']}" for k, y in x["按配方"].items() if y.get("值") is not None)
        st = x.get("状态", "")
        return f"{v} {st if st in ('🔶', '⚠️') else ''}".strip() if v not in (None, "") else t(CSTATE, st, st)
    c_rows = [[r["论文"], r["测试"], t(TESTKIND, r["测试类型"])] + [cval(r, f) for f in ("ES", "sulfur_loading", "S_content", "Li_thickness", "NP", "rate", "temperature")]
              + [CELL.get(r["条件"].get("cell_format", {}).get("值"), "—")] for r in ct]
    cath = read_json("正极硫含量解析.json")
    s_cols = ["Paper", "Condition ID", "Source text (as extracted)", "Regex value", "Verified value", "State", "Parser agrees"]
    s_rows = [[x["论文"], x["条件编号"], x["原文"], x["解析值"], x["核定值"], t(CSTATE, x["核定状态"] or "", x["核定状态"] or ""),
               {True: "yes", False: "no"}.get(x["解析与核定一致"], "—")] for x in cath]
    data = f"""<section id="data" class="panel" hidden><div class="section-head"><h2>Methods &amp; data</h2><span class="note">Chinese text in these tables is copied from the extraction</span></div>
<div class="grid">
<div class="card"><span class="badge">Step 13a</span><h3>Metric &amp; property names</h3><p>205 metric spellings mapped to {a['四类标准指标种数']} standard metrics in four performance classes; {a['物性原名种数']} property names mapped to {a['标准物性种数']} categories.
Capacities with an unstated basis stay separate: definitions that differ are not merged.</p></div>
<div class="card"><span class="badge">Step 13b</span><h3>Test conditions</h3><p>{b['性能测试数']} performance tests. Cathode sulfur content (electrode basis) was verified by reading each of the 55 cathode descriptions; the regex parser agreed in only 29 cases, so verified values are used.</p></div>
<div class="card"><span class="badge">Step 13c</span><h3>Statements</h3><p>{c['表述条数']} statements; 19 groups where one value was extracted into two tests of the same paper are flagged and counted once in analyses.</p></div></div>
<h3 style="margin-top:26px">Metric aliases</h3><div id="tAlias"></div>
<h3 style="margin-top:26px">Property aliases</h3><div id="tProp"></div>
<h3 style="margin-top:26px">Test conditions</h3><p class="note">🔶 = converted or inferred (room temperature taken as 25 °C; Li₂S, SPAN or Se/S loading converted to sulfur); ⚠️ = conflicting or multiple values.</p><div id="tCond"></div>
<h3 style="margin-top:26px">Cathode sulfur content · verification</h3><div id="tCath"></div>
<div class="callout">Files: <span class="mono">output/表述与矛盾试跑_F版30篇_2026-11-04/</span> — 表述表.xlsx, 别名表与复核表.xlsx, 条件表.xlsx, 归一化与跨篇比较.xlsx, 矛盾候选复核表.xlsx (Chinese) and the matching JSON. Scripts: <span class="mono">scripts/step13a–13f, step13s</span>.</div></section>"""

    js_data = (f"table('tStatements',{j(cols)},{j(rows)},{{selects:[1,3,14],detail:k=>D[k],placeholder:'Search ID, paper, component, metric…',height:700}});"
               f"table('tRank',{j(fr_cols)},{j(fr_rows)},{{selects:[0,1]}});"
               f"table('tAlias',{j(a_cols)},{j(a_rows)},{{selects:[4]}});table('tProp',{j(p_cols)},{j(p_rows)},{{selects:[0]}});"
               f"table('tCond',{j(c_cols)},{j(c_rows)},{{selects:[0]}});table('tCath',{j(s_cols)},{j(s_rows)},{{selects:[5]}});"
               "const hh=location.hash.slice(1);if(hh&&$('nav button[data-panel=\"'+hh+'\"]'))$('nav button[data-panel=\"'+hh+'\"]').click();")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Li–S Statement Atlas · Pilot</title><style>{CSS}</style></head><body>
<header><div class="brand"><span class="mark">S</span>Li–S Statement Atlas</div><div class="meta">LI–S ELECTROLYTE CONFLICTS / 04 NOV 2026 / PILOT</div></header>
<main>{hero}{overview}{statements}{norm}{conflicts}{figures}{data}
<div class="footer"><span>Preliminary · 30 papers (F-version, rule-processed) · AI-assisted, not yet confirmed item by item by the user</span><span>Opens offline · no network needed</span></div></main>
<script>const D={j(det)};{JS}{js_data}</script></body></html>"""
    (SITE / "index.html").write_text(page, encoding="utf-8")
    for old in ("表述表.html", "别名表.html", "条件表.html", "图.html", "归一化.html", "矛盾候选.html", "style.css"):
        if (SITE / old).exists():
            (SITE / old).unlink()  # 旧的中文多页版本，已并入单页
    print("网站：index.html（单页，英文）")


if __name__ == "__main__":
    main()
