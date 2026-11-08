"""step13s：结果网站（英文，单页、标签切换；版式参照用户提供的 electrolyte-atlas.html，11-04 用户要求）。

输出：网站/index.html（数据嵌在页面里）＋ 网站/图/ 下的交互图。双击 index.html 或项目根目录的 双击打开结果网站.bat 即可打开。
提取结果里的自由文字（取值点、物性描述）本身是中文，按原样显示并注明；其余界面、图、说明、核对结论为英文。
04 · Modelling（11-05 用户要求）：243 篇、313 篇建模迭代的方法（描述符）、结果与不采纳理由，数据读各轮结果文件
（表述试跑243篇_2026-11-04/试跑建模结果.json、物性对比/，改动模型_313篇_2026-11-05/考试结果.json、选定配置.json、诊断.json）；
其余标签页仍是 30 篇试跑。
"""
from __future__ import annotations

import html
import json
import math
import re

from step13_common import COMP, OUT, ROOT, in_analysis, read_json
import sys as _sys
_sys.path.insert(0, str(ROOT / "scripts" / "step15_meta"))
from site_meta import leak_note, meta_panel  # 11-06：05 · Meta & attribution（图由 step15_meta/D_site.py figs 先画好）
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


# ---------- 04 modelling（11-05 用户要求：各轮方法、描述符、结果、不采纳理由）----------
M243 = ROOT / "output" / "表述试跑243篇_2026-11-04"
M313 = ROOT / "output" / "改动模型_313篇_2026-11-05"
C243 = {"放电容量类": "First-cycle capacity", "衰减类": "Capacity retention", "库仑效率类·全电池": "Full-cell CE", "库仑效率类·Li‖Cu": "Li‖Cu CE"}
C14 = {"首圈容量": "First-cycle capacity", "每圈衰减率": "Capacity fade per cycle", "全电池CE": "Full-cell CE (cycling)", "LiCu_CE": "Li‖Cu CE (cycling)"}
C14TO243 = {"首圈容量": "放电容量类", "每圈衰减率": "衰减类", "全电池CE": "库仑效率类·全电池", "LiCu_CE": "库仑效率类·Li‖Cu"}
M14 = {"零": "predict no difference", "Huber": "Huber regression", "HGB浅": "gradient boosting (shallow)", "HGB深": "gradient boosting (deep)",
       "RF": "random forest", "ET": "extra trees", "kNN5": "5-nearest neighbours", "SVR": "support vector regression",
       "集成": "ensemble (ridge + random forest + shallow GB)"}
FAM = [("只有物性/结构", False, "Physical / structural descriptors, no conditions"),
       ("只有物性/结构", True, "Physical / structural descriptors + conditions"),
       ("物性/结构＋组分身份", True, "Physical / structural + component identity + conditions"),
       ("只有组分身份", True, "Component identity + conditions")]
ROUNDS = [("r1", "Round 1", "Physical / structural descriptor sets × every model, with and without test conditions"),
          ("r2", "Round 2", "Add component presence (COMP); try mirror augmentation, equal weight per paper and a winsorised training target"),
          ("r3多任务", "Round 3", "Multi-task: three or four classes trained together with a class indicator"),
          ("r4", "Round 4", "Add component amounts (AMT) and presence × condition (COMP×COND); ridge strength grid and an ensemble")]
GROUPS_EN = [
    ("ER", "12", "Formulation-level elemental ratios after Kim et al. (PNAS 2023), solvent + main salt only: solvent O in three bins "
                 "(non-fluorinated, β-fluorinated ether, α-fluorinated ether), aO, aC, sC, aF, sF, F/C, O/C, F/O, InOr"),
    ("RD5", "5", "RDKit descriptors weighted by solvent mole fraction: ether O, rings, rotatable bonds, carbonate groups, thioether / polysulfide S"),
    ("ADD", "8", "LiNO₃ (M), mediator, other additives, main salt (M), anion F per litre, anion sulfonyl per litre, iodine-containing, organosulfur"),
    ("SOLV", "20", "Solvent-weighted functional groups and properties: ether O, α/β-fluorinated ether O, carbonate, carbonyl, sulfone, nitrile, amide, "
                   "thioether S, F and C atoms, rings, rotatable bonds, TPSA, molecular weight; fractions of fluorinated, organosulfur, hydrocarbon, "
                   "cyclic-ether and carbonate molecules"),
    ("STATE", "3", "Solvation state computed from composition: ln(coordinating sites per Li⁺), diluent mole fraction, total Li⁺ concentration"),
    ("COMP", "{v}", "Presence of each component that appears in at least two development-set papers"),
    ("AMT", "{v}", "Amount of each of those components (mol per litre of solvent), where the composition can be converted"),
    ("COMP×COND", "2 × {v}", "Presence × reference ln E/S, and presence × reference sulfur loading"),
    ("Conditions", "7 / 4", "Li–S classes: ln E/S, S loading, cathode S content, ln rate, temperature, pouch, ln cycle number. "
                            "Li‖Cu: ln current density, ln plating capacity, ln cycle number, temperature")]


def f2(x) -> str:
    return "—" if x is None else f"{x:+.2f}"


def m14(k: str) -> str:
    return f"ridge α = {k[len('岭回归a'):]}" if k.startswith("岭回归a") else M14.get(k, k)


def cfg14(b: dict) -> str:
    """一个配置的英文简述：描述符组 · 模型 · 训练技巧。"""
    tricks = [n for k, n in (("镜像", "mirror"), ("每篇等权", "equal weight per paper"), ("截尾", "winsorised")) if b.get(k)]
    return f"{b['描述符'].replace('COMPxCOND', 'COMP×COND')} · {m14(b['模型'])}" + (f" · {', '.join(tricks)}" if tricks else "")


def change_en(x: dict) -> str:
    """同一改动的例子：只“去”不“加”的改写成“加”、效应取反，读起来顺。效应 > 0 = 实验侧更好。"""
    if not x["加"] and x["去"]:
        lab, lo, hi = "adds " + ", ".join(x["去"]), -x["效应最大"], -x["效应最小"]
    else:
        lab = " · ".join(p for p in ("adds " + ", ".join(x["加"]) if x["加"] else "", "removes " + ", ".join(x["去"]) if x["去"] else "") if p)
        lo, hi = x["效应最小"], x["效应最大"]
    return f"{lab}: {x['论文数']} papers, {x['配对数']} pairs, effect {lo:+.2f} to {hi:+.2f}"


def modelling_panel(nres: dict) -> str:
    m243 = json.loads((M243 / "试跑建模结果.json").read_text(encoding="utf-8"))["类别"]
    p243 = {k: json.loads((M243 / "物性对比" / f"物性对比_{k}.json").read_text(encoding="utf-8")) for k in C243}
    ceil243 = {m.group(1): float(m.group(2)) for m in
               re.finditer(r"## (.+?): .*?R² 上限）≈ ([-\d.]+)", (M243 / "物性对比" / "同种改动跨篇一致性.txt").read_text(encoding="utf-8"))}
    exam = json.loads((M313 / "考试结果.json").read_text(encoding="utf-8"))
    n_exam_papers = len(json.loads((M313 / "划分.json").read_text(encoding="utf-8"))["考试集论文"])
    dg = json.loads((M313 / "诊断.json").read_text(encoding="utf-8"))
    cons, cmp_, chk, v = dg["同一改动跨篇一致性"], dg["迭代记录对比"], dg["选定配置核对"], dg["组分词表大小"]
    lk = dg["圈数泄漏检查"]["每圈衰减率"]
    rrf = ROOT / "output" / "改动模型_去圈数_313篇_2026-11-06" / "考试结果.json"  # 另一会话 11-06 去圈数重考
    rr = json.loads(rrf.read_text(encoding="utf-8")) if rrf.exists() else None
    lk_other = max(dg["圈数泄漏检查"][c]["总体"]["只用Δln圈数R2"] for c in C14 if c != "每圈衰减率")
    leak_html = (f"<div class='callout warn'><b>Cycle-number leak in fade per cycle (found 5 Nov late evening; checked here).</b> Iteration 4 kept ln(cycle number) "
                 f"among the inputs for fade per cycle, against your 5 Nov rule. The difference in ln(cycle number) alone explains R² "
                 f"{lk['总体']['只用Δln圈数R2']:.2f} of the development pairs — {lk['跨测试、不同配方']['只用Δln圈数R2']:.2f} of cross-test pairs, "
                 f"{lk['同测试、不同配方']['只用Δln圈数R2']:.2f} of same-test pairs, where both sides share the cycle number. Per-cycle fade is the total loss divided "
                 f"by the cycle count, so the cycle count gives part of the answer away. The fade-per-cycle results below (development, exam, and the lift from "
                 f"adding conditions) are therefore not evidence that anything transfers. For the other classes the same check gives R² ≤ {lk_other:.2f}. "
                 + (f"<br><b>Re-run without cycle number (another session, 6 Nov; exam set used a second time).</b> Selected configuration "
                    f"{e(cfg14(rr['配置']['每圈衰减率']))}, development R² {f2(rr['配置']['每圈衰减率']['开发集R2'])}; exam R² <b>{f2(rr['类别']['每圈衰减率']['总体'])}</b> "
                    f"(95% interval {f2(rr['类别']['每圈衰减率']['总体95%区间'][0])} to {f2(rr['类别']['每圈衰减率']['总体95%区间'][1])}), same-test pairs "
                    f"{f2(rr['类别']['每圈衰减率']['同测试、不同配方'])}, pairs whose cycle numbers differ ≤ 5× {f2(rr['类别']['每圈衰减率']['圈数相差≤5倍']['R2'])}. "
                    "So without the leak, fade per cycle does not transfer either. Files: <span class='mono'>output/改动模型_去圈数_313篇_2026-11-06/</span>."
                    if rr else "A re-run without cycle number is in progress in another session.") + "</div>")
    fam = lambda c, f, cond: cmp_[c]["按描述符与条件"].get(f"{f}｜{'加条件' if cond else '不加条件'}")

    # 第 1–3 次迭代（30 篇、243 篇）
    sel1 = {n: next(m for m in r["模型比较"] if m["模型"] == r["主模型"]) for n, r in nres.items() if n in C243}
    it1 = "<br>".join(f"{C243[n]} {f2(m['V1篇内R2'])} <span class='note'>({e(t(MODEL, m['模型']))})</span>" for n, m in sel1.items())
    v3best = lambda r: max(x["R2"] for x in r["模型V3"].values())
    it2 = "<br>".join(f"{C243[n]} {f2(v3best(m243[n]))} <span class='note'>(no difference {f2(m243[n]['基线']['猜没差别']['R2'])} · "
                      f"other papers' mean gain {f2(m243[n]['基线']['猜其他论文平均提升']['R2'])})</span>" for n in C243)
    pairs2 = " · ".join(f"{C243[n]} {m243[n]['V3配对']}" for n in C243)

    def pbest(d):
        res = d["结果"]
        base = max(x["R2"] for k, x in res.items() if k.startswith("对照"))
        k, x = max(((k, x) for k, x in res.items() if not k.startswith("对照")), key=lambda kv: kv[1]["R2"])
        add, _, mdl = k.partition("｜")
        return base, x["R2"], f"{add}, {t(MODEL, mdl)}"
    it3 = "<br>".join(f"{C243[n]} {f2(pbest(d)[0])} → {f2(pbest(d)[1])} <span class='note'>({e(pbest(d)[2])})</span>" for n, d in p243.items())
    imp = [q["按论文留出R2"] for d in p243.values() for q in d.get("补值小模型质量", {}).values() if q.get("按论文留出R2") is not None]
    imp_txt = f"{min(imp):+.2f} to {max(imp):+.2f} ({sum(x < 0 for x in imp)} of {len(imp)} below zero)"
    imp_n = [q["配方"] for d in p243.values() for q in d.get("补值小模型质量", {}).values() if q.get("配方")]
    np3 = [d["V3配对"] for d in p243.values() if d.get("V3配对")]
    star = lambda c: "*" if chk[c]["选定时用了过期记录"] else ""
    it4 = "<br>".join(f"{C14[c]} {f2(chk[c]['现行数据上按规则应选']['总体'])} → {f2(exam['类别'][c]['总体'])}{star(c)}" for c in C14)
    n_exam = sum(exam["类别"][c]["n"] for c in C14)
    itrows = [
        ("1", "4 Nov · 30 papers (F-version pilot)",
         "Normalise every paper to one standard condition with a shared scoring function. V1: leave one paper out, score its within-paper differences",
         "sO in 3 bins, aC, F/O, InOr, LiNO₃, main salt, other additives + E/S, S loading, cathode S, rate, temperature, pouch, cycle number",
         "Ridge, linear mixed model, gradient boosting, monotone gradient boosting, random forest, Gaussian process",
         "V1 R², selected model:<br>" + it1, "The formulation effect does not transfer to unseen papers; the ranking in 03 is kept only as an illustration"),
        ("2", "4 Nov · 243 papers",
         f"V3: leave out the only paper that compares a pair directly, then infer that gap from other papers and the descriptors (pairs: {pairs2})",
         "13 elemental ratios + 5 RDKit (ether O, rings, rotatable bonds, carbonate groups, thioether / polysulfide S) + LiNO₃, additives / mediators "
         "+ test conditions including cut-off voltage",
         "Same six models", "V3 R², best of six (baselines):<br>" + it2,
         "No better than the two baselines; leaving out whole families (fluorinated solvents, organosulfur) fails"),
        ("3", "4 Nov · 243 papers", "V3 as in 2, adding property layers one at a time (3 models × 6 feature sets = 18 tries per class)",
         "2 + <b>A</b> solvation state from composition · <b>B</b> molecular properties (in practice only the Gasteiger charge of coordinating atoms) · "
         "<b>C</b> conductivity / viscosity measured by the same paper · <b>D</b> properties imputed by a composition → property model",
         "Ridge, monotone gradient boosting, random forest", "V3 R², control → best with additions:<br>" + it3,
         f"No gain for capacity or retention; the CE gains are the best of 18 tries on {min(np3)}–{max(np3)} pairs, within noise; "
         f"imputation models score {imp_txt}"),
        ("4", "5 Nov · 313 papers",
         f"Change model: every comparison inside a paper, including cross-condition pairs. {dg['开发集']['配对']} development pairs from "
         f"{dg['开发集']['论文']} papers (paper-grouped 5-fold CV); {n_exam} pairs from {n_exam_papers} papers held out and scored once",
         "Groups ER, RD5, ADD, SOLV, STATE, COMP, AMT, COMP×COND + conditions (see below)",
         "Ridge (α 0.3–100), Huber, gradient boosting, random forest, extra trees, kNN, SVR, ensemble; multi-task",
         "Best development R² → exam R²:<br>" + it4,
         "Only fade per cycle scores above zero on the exam set — its 95% interval crosses zero, and cycle number leaks the answer (see the warning above)"),
    ]
    it_html = "".join("<tr>" + "".join(f"<td>{x}</td>" for x in r) + "</tr>" for r in itrows)

    # 第 4 次迭代细节
    g_html = "".join(f"<tr><td><b>{g}</b></td><td>{n.format(v=v)}</td><td>{d}</td></tr>" for g, n, d in GROUPS_EN)
    r_html = "".join(f"<tr><td><b>{lab}</b></td><td>{dg['各轮配置数'].get(k, 0)}</td><td>{e(what)}</td>"
                     f"<td class='mono'>{e(', '.join(x.replace('COMPxCOND', 'COMP×COND') for x in dg['各轮内容'][k]['描述符组']))}</td>"
                     f"<td>{e(', '.join(m14(x) for x in dg['各轮内容'][k]['模型']))}</td></tr>" for k, lab, what in ROUNDS)
    st_vals = [x.get("同测试、不同配方") for c in C14 for f, cond, _ in FAM for x in [fam(c, f, cond)] if x and x.get("同测试、不同配方") is not None]

    def famcell(x):
        return "<td>—</td>" if not x else f"<td><b>{f2(x['总体'])}</b><br><span class='note'>same test {f2(x.get('同测试、不同配方'))}</span></td>"
    f_html = "".join(f"<tr><td>{e(lab)}</td>{''.join(famcell(fam(c, f, cond)) for c in C14)}</tr>" for f, cond, lab in FAM)
    f_html += "<tr><td>Predict no difference (reference)</td>" + "".join(f"<td>{f2(cmp_[c]['零基线']['总体'])}</td>" for c in C14) + "</tr>"
    no_c, wi_c = (lambda c: fam(c, "只有物性/结构", False)["总体"]), (lambda c: fam(c, "只有物性/结构", True)["总体"])

    def onoff(c, flag):
        x = cmp_[c]["训练技巧"][flag]
        return f"<td>{f2(x['开']['总体'])} / {f2(x['关']['总体'])}</td>"

    def mt(c, g):
        x = cmp_[c]["多任务"][g]
        return f"<td>{f2(x['多任务']['总体'])} / {f2(x['单类']['总体'])}</td>"

    def stt(c):
        x = cmp_[c]["溶剂化状态STATE"]
        return f"<td>{f2(x['加之后']['总体'])} / {f2(x['加之前']['总体'])}</td>"
    t_html = "".join(f"<tr><td>{lab}</td><td class='note'>{cmpw}</td>{''.join(fn(c) for c in C14)}</tr>" for lab, cmpw, fn in (
        ("Mirror augmentation (train on A − B and B − A)", "on / off", lambda c: onoff(c, "镜像")),
        ("Equal weight per paper", "on / off", lambda c: onoff(c, "每篇等权")),
        ("Winsorised training target, 5–95% (round 2)", "on / off", lambda c: onoff(c, "截尾")),
        ("Multi-task · ER+RD5+ADD+SOLV", "joint / single", lambda c: mt(c, "ER+RD5+ADD+SOLV")),
        ("Multi-task · ER+RD5+ADD+SOLV+COMP", "joint / single", lambda c: mt(c, "ER+RD5+ADD+SOLV+COMP")),
        ("Solvation state STATE added (round 1)", "with / without", stt)))
    trick_d = [cmp_[c]["训练技巧"][f]["开"]["总体"] - cmp_[c]["训练技巧"][f]["关"]["总体"] for c in C14 for f in ("镜像", "每篇等权", "截尾")]
    mt_d = [x["多任务"]["总体"] - x["单类"]["总体"] for c in C14 for x in cmp_[c]["多任务"].values()]
    st_d = [abs(cmp_[c]["溶剂化状态STATE"]["加之后"]["总体"] - cmp_[c]["溶剂化状态STATE"]["加之前"]["总体"]) for c in C14]

    ex_html = ""
    for c in C14:
        s, r, k = exam["配置"][c], exam["类别"][c], chk[c]
        tag = " <span class='badge bad'>stale record*</span>" if k["选定时用了过期记录"] else " <span class='badge bad'>cycle-number leak</span>" if c == "每圈衰减率" else ""
        ex_html += (f"<tr><td>{C14[c]}</td><td>{e(cfg14(s))}</td><td>{f2(s['开发集R2'])}{tag}</td><td>{r['n']} · {r['论文']}</td>"
                    f"<td><b>{f2(r['总体'])}</b></td><td>{f2(r['总体95%区间'][0])} to {f2(r['总体95%区间'][1])}</td>"
                    f"<td>{f2(r['同测试、不同配方'])}</td><td>{f2(r['跨测试、不同配方'])}</td><td>{f2(r['同配方、换条件'])}</td></tr>")
    stale = []
    for c in C14:
        k = chk[c]
        if k["选定时用了过期记录"]:
            right = k["现行数据上按规则应选"]
            stale.append(
                f"<b>*{C14[c]}.</b> The configuration was selected on a record computed before first-cycle CE was removed "
                f"({k['选定时所用记录']['n']} pairs instead of {dg['开发集']['各类配对'][c]}). On the current data the same configuration scores "
                f"{f2(k['同一配置在现行数据上']['开发集R2'])}; applied correctly, the selection rule picks {e(cfg14(right))} ({f2(right['总体'])}). "
                f"The exam score {f2(exam['类别'][c]['总体'])} therefore belongs to a configuration that should not have been chosen. "
                "Scoring the exam set again with the right configuration would be a second look at it, so that is left to your decision. "
                f"The conclusion does not change: on the current data no single-class configuration reaches a development R² above {f2(right['总体'])}.")
    stale_html = (f"<div class='callout warn'><b>Selection error found on 5 Nov (evening).</b> {dg['过期记录']['条数']} round-2 records in the log were computed "
                  f"on the data before first-cycle CE was removed; they duplicate configurations re-run on the current data. Comparisons on this page use only "
                  f"the {dg['现行数据上的配置数']} records on the current data.<br>{'<br>'.join(stale)}</div>") if stale else ""

    # 同一改动跨篇一致性
    co_html = ""
    for c in C14:
        x = cons[c]
        top = change_en(x["例子"][0]) if x["例子"] else "—"
        co_html += (f"<tr><td>{C14[c]}</td><td>{x['不同配方配对']}</td><td>{x['只改用量配对']}</td><td>{x['不同改动种数']}</td>"
                    f"<td>{x['在≥2篇出现的改动种数']} <span class='note'>({x['在≥2篇出现的改动覆盖配对']} pairs · {x['覆盖比例']:.0%})</span></td>"
                    f"<td>{f2(x['留一篇查表R2'])} · {x['方向一致率']:.0%} <span class='note'>(n = {x['查表配对数']})</span></td>"
                    f"<td><b>{f2(x['只靠改动身份的上限R2'])}</b></td><td>{f2(ceil243.get(C14TO243[c]))}</td><td>{e(top)}</td></tr>")
    cl = [cons[c]["只靠改动身份的上限R2"] for c in C14]
    cv = [cons[c]["覆盖比例"] for c in C14]
    c243 = list(ceil243.values())
    fade, fade_r = exam["类别"]["每圈衰减率"], exam["类别"]["每圈衰减率"]["总体95%区间"]
    phys = "; ".join(f"{C14[c].split(' (')[0]} {f2(fam(c, '只有物性/结构', True)['总体'])} vs {f2(fam(c, '只有组分身份', True)['总体'])}" for c in C14)

    rej = [
        ("Cycle number as an input for fade per cycle", "bad", "Leak · removed and re-examined" if rr else "Leak · re-run without it in progress",
         f"Δln(cycle number) alone explains R² {lk['总体']['只用Δln圈数R2']:.2f} of the development pairs "
         f"({lk['跨测试、不同配方']['只用Δln圈数R2']:.2f} of cross-test pairs)"
         + (f"; without it the exam R² is {f2(rr['类别']['每圈衰减率']['总体'])}" if rr else ""),
         "Against your 5 Nov rule: per-cycle fade = total loss ÷ cycle count, so the cycle count gives part of the answer away. "
         "Re-run: output/改动模型_去圈数_313篇_2026-11-06/ (another session)."),
        ("Target R² &gt; 0.8 (set 5 Nov)", "bad", "Out of reach · new target pending your decision",
         f"Identity-only ceiling {min(cl):+.2f} to {max(cl):+.2f} (313 papers) and {min(c243):+.2f} to {max(c243):+.2f} (243 papers); "
         f"best exam R² {f2(fade['总体'])}, inflated by the cycle-number leak",
         "The same change has different effects in different papers, so a model that only knows what changed cannot be right on both sides. "
         "Suggested replacement: the share of confirmed contradictions that test conditions explain."),
        ("Cross-paper ranking via normalisation (03)", "bad", "Not usable", "V3 fails in iterations 2–4",
         "Plan §8.7: if V3 fails, formulations cannot be ranked across papers. The ranking in 03 stays as a 30-paper illustration."),
        ("Physical / structural descriptors as predictors", "trial", "Not adopted for prediction · kept for explanation",
         f"Development R², physical / structural + conditions vs component identity + conditions: {phys}. Adding the solvation state changes R² by at most {max(st_d):.2f}",
         "They are functions of the formulation, so they add information only if they capture mechanism that identity misses — not seen here. "
         "They remain the language for explaining contradictions."),
        ("Measured conductivity / viscosity (layer C)", "no", "Not adopted",
         "Reported for 35–60% of the modelling data; both together for 55 formulations from 25 papers (243-paper run); no gain beyond noise", "Too sparse to train on."),
        ("Properties imputed from composition (layer D)", "bad", "Rejected",
         f"Imputation models score R² {imp_txt} when whole papers are left out; each was trained on {min(imp_n)}–{max(imp_n)} formulations",
         "The imputed values are themselves not predictive."),
        ("Molecular properties from PubChem (layer B)", "no", "Not available",
         "Dielectric constant for 0 of 110 solvents, viscosity for 22; DME, DOL, EC and TTE missing; only a Gasteiger-charge proxy was tested",
         "Needs handbook values (DN, dielectric constant) or the DFT/MD features of plan §7.17a."),
        ("Mirror augmentation · equal weight per paper · winsorised target", "no", "No consistent gain",
         f"On minus off: {min(trick_d):+.2f} to {max(trick_d):+.2f}; the sign changes between classes", "Used only where the selection rule happened to pick them."),
        ("Multi-task training", "no", "No consistent gain", f"Joint minus single-class: {min(mt_d):+.2f} to {max(mt_d):+.2f}",
         "The four classes do not share enough signal to borrow from each other."),
        ("Cut-off voltage as an input", "no", "Removed (your decision, 5 Nov)",
         "Requiring it left 4–9 condition-complete within-paper pairs per Li–S class; without it 26–30",
         "Rarely reported. Its effect (LiNO₃ reduction below ≈ 1.6 V adds capacity) is handled when explaining contradictions, as in SAME001."),
        ("First-cycle CE inside the CE classes", "trial", "Removed in iteration 4 · pending your confirmation",
         "First-cycle CE spans 8.8–79.9% within P017, and cross-test pairing would match it against cycle-100 CE",
         "It measures first-cycle irreversible loss (SEI formation, LiNO₃ reduction), not cycling efficiency."),
        ("Capacity below 10 mAh g⁻¹ (P344, 1.51)", "no", "Removed", "Unit error in the extraction", "—"),
        ("Selected full-cell CE configuration", "bad", "Selection error · exam re-score pending your decision",
         "Chosen from a stale record; see the exam section", "The conclusion for full-cell CE (no transfer) does not change."),
        ("Predicting absolute performance values", "planned", "Not tried · not counted as progress", "—",
         "R² would be high because E/S, loading and rate set most of the absolute level — a condition and paper effect, not an electrolyte effect. "
         "Useful only to measure how much the conditions explain."),
        ("NORM and LOPO contradiction rules", "trial", "Proposed pause · pending your decision", "Both rely on the normalisation model, whose R² ≈ 0",
         "SAME, FLIP and DESC need only directions and stay."),
        ("Text embeddings (MatSciBERT) for statements", "trial", "Proposed deferral · pending your decision",
         "Statements are generated from structured fields by a template",
         "Matching the fields directly is more precise and easier to check; embeddings suit the authors' free-text mechanism claims (Q2) better."),
        ("More data: values read from figures, the remaining 222 papers", "planned", "Option · costs extraction money",
         "About 70% more papers; many control-side values exist only in figures",
         "Adds pairs and repeated changes, but does not remove the paper-to-paper inconsistency."),
        ("DFT/MD descriptors (plan §7.17a)", "planned", "Planned, for explanation rather than R²", "Not yet computed",
         "A change gets the same computed values in every paper, so they cannot explain why its effect differs between papers; "
         "they can explain mechanisms inside an attribution."),
    ]
    rj_html = "".join(f"<tr><td><b>{a}</b></td><td><span class='badge {cls}'>{s}</span></td><td>{ev}</td><td>{why}</td></tr>" for a, cls, s, ev, why in rej)
    cards = (f"<div class='card'><span class='badge bad'>Exam set · best class · leaked</span><h3 style='font-size:29px;margin:10px 0 4px'>{f2(fade['总体'])}</h3>"
             f"<p>Capacity fade per cycle · 95% interval {f2(fade_r[0])} to {f2(fade_r[1])} · {fade['n']} pairs from {fade['论文']} papers · "
             f"inflated by the cycle-number leak"
             + (f"; re-examined without it: <b>{f2(rr['类别']['每圈衰减率']['总体'])}</b>" if rr else "") + ". Other classes: "
             f"{', '.join(f2(exam['类别'][c]['总体']) + star(c) for c in C14 if c != '每圈衰减率')}.</p></div>"
             f"<div class='card'><span class='badge'>Configurations searched</span><h3 style='font-size:29px;margin:10px 0 4px'>{dg['现行数据上的配置数']}</h3>"
             f"<p>On the current 313-paper data in four rounds, after 6 models (iteration 2) and 18 feature sets (iteration 3) per class on 243 papers.</p></div>"
             f"<div class='card'><span class='badge bad'>Changes seen in ≥ 2 papers</span><h3 style='font-size:29px;margin:10px 0 4px'>{min(cv):.0%}–{max(cv):.0%}</h3>"
             f"<p>of formulation-change pairs. Where a change does repeat, knowing it explains at most R² {min(cl):+.2f} to {max(cl):+.2f}.</p></div>")
    lift = lambda c: f"{f2(no_c(c))} to {f2(wi_c(c))}"
    reading = (f"<b>Reading.</b> (1) Swapping the electrolyte inside one test is not predictable across papers: the R² on same-test pairs stays between "
               f"{min(st_vals):+.2f} and {max(st_vals):+.2f} for every descriptor family. (2) Test conditions help only for Li‖Cu CE, where adding them lifts the "
               f"development R² from {lift('LiCu_CE')}. The larger lift for fade per cycle ({lift('每圈衰减率')}) comes almost entirely from the cycle number, "
               "which leaks the answer. "
               "(3) Physical and structural descriptors do no better than knowing which components are present. (4) Most changes appear in a single paper, "
               "and the ones that repeat do not have a consistent effect. R² &gt; 0.8 is therefore out of reach on text-only literature data, whatever the model.")
    steps = [("Find candidates", "On the 313-paper statements: SAME (identical change, opposite outcome), FLIP (same pair, condition flips the direction), "
                                 "DESC (same descriptor direction, opposite outcome). None needs a model."),
             ("Check the source", "Every candidate against the source text, with quotes: ✅ 🔶 ⚠️ ❌."),
             ("Attribution · conditions", "Compare the two sides' test conditions: E/S, loading, cathode S, rate, temperature, Li thickness. "
                                         "This comes first because a difference in conditions is the simplest reason for the same change to look different."),
             ("Attribution · mechanisms", "For what conditions cannot explain, pull the mechanism claims and supporting measurements linked to each statement: "
                                         "consensus, conflict, often claimed but not measured."),
             ("DFT/MD", "What remains goes to the first DFT/MD batch (TTE and LiNO₃ first, plan §7.17a).")]
    st_html = "".join(f"<div class='step'><span class='num'>{i}</span><div><b>{a}</b><p>{e(b)}</p></div></div>" for i, (a, b) in enumerate(steps, 1))
    th = lambda cols: "<tr>" + "".join(f"<th>{x}</th>" for x in cols) + "</tr>"
    cls4 = [C14[c] for c in C14]
    return f"""<section id="modelling" class="panel" hidden><div class="section-head"><h2>Can the effect of an electrolyte change be predicted across papers?</h2>
<span class="badge bad">Target R² &gt; 0.8 not reached</span></div>
<p>For two formulations compared in one paper, a model trained on other papers predicts how far apart their performance is, given the formulations and test conditions.
Four iterations, from 30 to 313 papers. Every validation leaves out whole papers, because formulations from one paper share a cathode, a process and a lab.
R² = 1 is perfect; 0 equals predicting no difference; below 0 is worse than that.</p>
<p class="note">Preliminary · AI-assisted, not yet confirmed item by item by the user · items marked “pending” await your decision · Statements, Normalisation and Contradictions still show the 30-paper pilot</p>
{leak_html}
<div class="grid" style="margin-top:16px">{cards}</div>
<div class="callout warn">{reading}</div>
<h3 style="margin-top:26px">Iterations at a glance</h3>
<div class="table-wrap"><table>{th(["#", "When · data", "Question · validation", "Inputs", "Models", "Best result (R²)", "Outcome"])}{it_html}</table></div>
<p class="note">* Selected from a stale record; see the exam section below.</p>
<div class="section-head" style="margin-top:32px"><h2>Iteration 4 in detail</h2><span class="note">313 papers · change model · {dg['迭代配置总数']} records logged, {dg['现行数据上的配置数']} on the current data</span></div>
<div class="two"><div class="sheet"><div class="eyebrow">Descriptor groups</div>
<div class="table-wrap"><table>{th(["Group", "Features", "Contents"])}{g_html}</table></div>
<p class="note">Each formulation feature enters as experiment − reference plus the reference value; conditions likewise. Target: difference in ln capacity, −ln fade per cycle
or −ln(100 − CE); positive means the experiment side is better. Pair types: same test, other formulation · other test, other formulation · same formulation, other condition.</p></div>
<div class="sheet"><div class="eyebrow">Search rounds</div>
<div class="table-wrap"><table>{th(["Round", "Configs", "What changed", "Descriptor sets", "Models"])}{r_html}</table></div>
<p class="note">Selection rule fixed before the exam: per class, the highest paper-grouped 5-fold development R², single-class training. Picking the best of many configurations makes development scores optimistic.</p></div></div>
<h3 style="margin-top:26px">Descriptors versus test conditions · development set</h3>
<p class="note">Best configuration per cell. Small print: R² on same-test, other-formulation pairs — the pure electrolyte effect.
Fade-per-cycle values with conditions include the cycle-number leak.</p>
<div class="table-wrap"><table>{th(["Inputs"] + cls4)}{f_html}</table></div>
<h3 style="margin-top:22px">Training tricks and multi-task · development set</h3>
<div class="table-wrap"><table>{th(["Variant", "Shown as"] + cls4)}{t_html}</table></div>
<h3 style="margin-top:22px">Exam set · scored once</h3>
<div class="table-wrap"><table>{th(["Class", "Selected configuration", "Dev R² at selection", "Exam pairs · papers", "Exam R²", "95% interval",
                                    "Same test", "Other test", "Condition change"])}{ex_html}</table></div>
{stale_html}
<div class="section-head" style="margin-top:32px"><h2>Why R² &gt; 0.8 is out of reach</h2><span class="note">Development set only · exam papers not read</span></div>
<p>A change is what one side has that the other lacks (adding X and removing X count as one change in two directions). If adding TTE helps in one paper and hurts in another,
a model that knows only “TTE was added” must give both the same prediction and is wrong on at least one. The share of variance left within repeated changes bounds what any such model can reach.</p>
<div class="table-wrap"><table>{th(["Class", "Formulation-change pairs", "Amount only", "Distinct changes", "Seen in ≥ 2 papers", "Lookup from other papers: R² · direction",
                                    "Identity-only ceiling", "Ceiling, 243-paper run", "Most repeated change (effect in ln units, + = better)"])}{co_html}</table></div>
<p class="note">Lookup: predict a pair from the mean effect of the same change in other papers. Ceiling: 1 − within-change variance / total variance, in-sample (optimistic).
Few repeated changes (1–3 per class), so these are rough estimates. ADD_TRIAL is the placeholder for additives whose structure was not verified,
so its “repeats” may be different additives.</p>
<div class="section-head" style="margin-top:32px"><h2>Not adopted, and why</h2></div>
<div class="table-wrap"><table>{th(["Item", "Status", "Evidence", "Reason"])}{rj_html}</table></div>
<div class="section-head" style="margin-top:32px"><h2>Proposed next step · contradiction analysis</h2><span class="badge planned">Awaiting your decision</span></div>
<div class="sheet">{st_html}</div>
<div class="callout">Files: <span class="mono">output/表述试跑243篇_2026-11-04/</span> 试跑建模结果.json, 物性对比/ ·
<span class="mono">output/改动模型_313篇_2026-11-05/</span> 选定配置.json, 考试结果.json, 迭代记录.jsonl, 诊断.json.
Scripts: <span class="mono">scripts/step13g_试跑243篇建模/</span>, <span class="mono">scripts/step14_改动模型/</span> (pairs, search, final, diagnose).</div></section>"""


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
<button role="tab" aria-selected="false" data-panel="normalise">03 · Normalisation</button><button role="tab" aria-selected="false" data-panel="modelling">04 · Modelling</button>
<button role="tab" aria-selected="false" data-panel="meta">05 · Meta &amp; attribution</button><button role="tab" aria-selected="false" data-panel="conflicts">06 · Contradictions</button>
<button role="tab" aria-selected="false" data-panel="figures">07 · Figures</button><button role="tab" aria-selected="false" data-panel="data">08 · Methods &amp; data</button></nav>"""

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
<div class="callout"><b>Update · 5 Nov 2026.</b> Modelling on 243 and 313 papers — methods, descriptors, results and what was not adopted — is in
<a href="#modelling" onclick="$('nav button[data-panel=modelling]').click();return false">04 · Modelling</a>. Figs. 1–4 in 06 · Figures now use 313 papers and molecular-structure descriptors, with clustering and the heat map drawn
separately. Statements, Normalisation and Contradictions still show the 30-paper pilot of 4 Nov.</div>
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
V2 is positive for first-cycle capacity (0.33) and retention (0.14), so the condition correction helps somewhat. CE has only 5 papers per type. The standard-ether baseline is a pilot choice pending your decision.
<br><b>Later runs (243 and 313 papers):</b> V3 fails as well, so the cross-paper ranking below remains an illustration — see 04 · Modelling.</div>
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

    modelling = modelling_panel(nres)
    _h = '<section id="modelling" class="panel" hidden>'
    modelling = modelling.replace(_h, _h + leak_note(), 1)  # 11-06 圈数泄漏更正
    meta, meta_js = meta_panel()

    # ---------- 05 contradictions ----------
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
    vd = json.loads((ROOT / "output" / "组会图_2026-11-08" / "第13页向量图数据.json").read_text(encoding="utf-8"))
NORM: only 3 cross-paper pairs share the same formulation and none differs by ≥1.5× after normalisation. LOPO runs only where the selected model's V1 R² &gt; 0; skipped: {e(skip)}. FLIP: none in this analysis set.</div>
<div class="chips" id="ctype">{chips}</div><div class="grid2">{''.join(cc)}</div></section>"""

    # ---------- 07 figures（11-06 用户要求：描述符按数值画、不切低/高档；聚类做到分子层面；文字中文、图英文。图由 step13m_figures_v2.py 画） ----------
    hs = json.loads((ROOT / "output" / "表述试跑313篇_2026-11-05" / "结构描述符图" / "step13h_汇总.json").read_text(encoding="utf-8"))
    v2 = json.loads((ROOT / "output" / "表述试跑313篇_2026-11-05" / "结构描述符图" / "v2" / "汇总.json").read_text(encoding="utf-8"))
    u, gnm, sp, pc = v2["分子宇宙"], v2["配方基因组"], v2["配方空间点数"], v2["平行坐标线数"]
    cn4 = {"首圈容量": "首圈容量", "每圈衰减率": "每圈衰减率", "全电池CE": "全电池 CE", "LiCu_CE": "Li‖Cu CE"}
    k3 = gnm["Ward 切成 k 簇时的簇大小"]["3"]
    # 11-08 用户定（按 zy 批注）：07 页 = 三个问题各一张“左数据、右机制”图（fig_questions.py）＋第 13 页文字向量地图（fig_p13_vectors.py）
    # ＋重画的配方空间、分子宇宙（step13m）＋说法地图（补充）；方向图、交叉图撤下（文件保留）
    s7 = json.loads((ROOT / "output" / "说法地图_313篇_2026-11-08" / "图07汇总.json").read_text(encoding="utf-8"))
    qd = json.loads((ROOT / "output" / "组会图_2026-11-08" / "组会图数据.json").read_text(encoding="utf-8"))
    cm = {t: s7[f"图7{l}_说法地图_{t}.html"] for t, l in (("T1", "a"), ("T3", "b"), ("T4", "c"))}
    # 11-08 晚第二版（用户：线太乱、要清晰并准确传达问题；分子宇宙、配方空间照 SES 画）：说明文字跟着 fig_questions.py、step23、step24 的新图改
    q1, q2, q3 = qd["q1"], qd["q2"], qd["q3"]
    s371 = q1["P371 系列（Taur，60 °C）"]
    fsp = json.loads((ROOT / "output" / "组会图_2026-11-08" / "配方空间汇总.json").read_text(encoding="utf-8"))
    mu = json.loads((ROOT / "output" / "分子宇宙_SES式_2026-11-08" / "汇总.json").read_text(encoding="utf-8"))
    hi = q3["高盐且含 LiNO3"]
    figs = [
        ("fig_q1.png", "问题 1 · 稀释剂该不该分解？",
         f"左：两篇反例各一条线。P371 在同一骨架（1,2-二乙氧基乙烷）上逐步加氟，Li‖Cu CE 依次为 "
         + " → ".join(f"{k} {v:.1f}%" for k, v in s371.items()) +
         f"，部分氟化的 F3DEE 最差（F6DEE 为饱和溶液，锂盐低于 1.2 M）；P381 在同一 LiFSI–TEP 体系里把稀释剂从不含氟的 DBE（{q1['P381（T01）DBE / TTE'][0]}%）"
         f"换成 TTE（{q1['P381（T01）DBE / TTE'][1]}%），CE 反而下降。多数结论写在标题：{q1['有含氟数变化的同测试比较的论文']} 篇里有 "
         f"{q1['每个比较都是含氟多 CE 高的论文']} 篇每个比较都是含氟越多 CE 越高。右：文献里 LiF 的两条来源说法——稀释剂自己分解（{len(q1['路线 1 论文'])} 篇）"
         f"与阴离子分解、稀释剂宜稳定（{len(q1['路线 2 论文'])} 篇，多为 2022 年以后），以及一句可检验的假设。", 0, True),
        ("fig_q2.png", "问题 2 · LiNO₃ 加多少最好？",
         f"左：只改 LiNO₃ 用量、测了至少 3 个浓度的两篇，纵轴 = 比本篇最低浓度时衰减慢了几倍：P139 到 0.5 M 一直在变好；P111 0.5 M 最好、1.0 M 比 0.1 M 还差，"
         f"是 0.5 M 以上唯一干净的剂量系列（P121 的 1.0 M 配方同时把 LiTFSI 从 1.1 M 降到 0.5 M，不算）。0.5 M 以下 {q2['其中变好']}/{q2['较高浓度 ≤ 0.5 M 的比较']} 个比较"
         f"（{q2['≤ 0.5 M 涉及论文']} 篇）多加变好。下方：{q2['有 LiNO3 数值的配方']} 个配方的用量分布，超过 0.6 M 的只有 {q2['高于 0.6 M 的配方']} 个。"
         "右：概念示意（不是拟合）——负极收益会饱和（0 线上方）、正极低电位还原的代价随用量增加（0 线下方），两者之和给出最佳用量；下方小条表示最佳用量随截止电压、电解液用量往哪边移。", 0, True),
        ("fig_q3.png", "问题 3 · 高盐和 LiNO₃ 是替代还是互补？",
         f"左：P112 是唯一把两者交叉测过的论文，柱高 = 每圈损失的锂（100 − CE）：只提盐（1 → 4 M）或只加 0.5 M LiNO₃ 都让锂损失大幅下降，两者一起并不比只加 LiNO₃ 更好。"
         f"中：313 篇里四种组合各有多少配方（方块面积），高盐（> 1 M）且含 LiNO₃ 只有 {hi[0]} 个配方、{len(hi[1])} 篇（是否含 LiNO₃ 看配方组分，不要求原文给出 M 用量）。"
         f"右：两种解释——同一个靶点、可以互相替代（{len(q3['替代一方'])} 篇），还是不同靶点、在锂硫全电池里叠加（{len(q3['互补一方'])} 篇＋P112 作者：高盐减少多硫化物溶解，LiNO₃ 消耗变慢），"
         "以及在锂硫全电池里区分两者的实验。", 0, True),
        ("fig_p13_vectors.png", "文字向量地图：矛盾的说法是邻居",
         "左：四组句子的向量相似度——立场相反、讲同一件事的两句话几乎重合（0.95–0.96），讲两件事的才远，说明文字向量按“讲什么”摆放、不按“支持还是反对”。"
         f"中：313 篇 {vd['画出的说法']:,} 条机制说法（bge-small-zh → UMAP），按说法里的关键词粗分话题上色（只作定位）：LiF / SEI / 锂负极 "
         f"{vd['话题计数（关键词粗分）']['LiF / SEI / Li anode']:,} 条、转化动力学与催化 {vd['话题计数（关键词粗分）']['conversion kinetics / catalysis']:,} 条、"
         f"多硫化物穿梭与溶解 {vd['话题计数（关键词粗分）']['polysulfide shuttle / dissolution']:,} 条等；P017 的 {vd['英文摘要未画（P017）']} 条英文摘要单独成簇，不画。"
         f"右：方框放大，{vd['放大区说法']:,} 条说法里 {vd['放大区 LiF/SEI/锂负极']:,} 条讲 LiF / SEI / 锂负极，读原文后在问题 1 上站队的有 {vd['问题 1 站队说法']} 条（蓝、橙），"
         "两派互相交错；P179（HFE 分解成 LiF 有利）与 P338（LiF 来自锂盐、HFE 分解不太可能）离得最近、结论相反。向量找“讲同一件事”的说法，立场由读原文判断。", 0, True),
        ("fig_formulation_space.png", "配方空间（数据概况）",
         f"版式照 SES AI 分子宇宙（白底，背景由浅蓝到红 = 配方由少到多，文字直接标在图上）。横轴 = 每个 Li⁺ 分到的配位位点（越往左溶剂化越弱：高浓、局部高浓电解液），"
         f"纵轴 = 锂盐浓度，都取对数；绿点 = 含 LiNO₃（大小 = 用量），绿圈 = 含 LiNO₃ 但原文没给 M 用量，灰点 = 不含，金黄描边 = 含含氟溶剂/稀释剂。{fsp['上图配方']} 个配方（{fsp['论文']} 篇）里 "
         f"{fsp['热点']['配方数']} 个挤在同一点（其中 {fsp['热点']['其中 DOL/DME+LiTFSI']} 个是 1 M LiTFSI 的 DOL/DME）；高盐区几乎全是灰点（问题 3），"
         "大绿点很少（问题 2），含氟配方在左侧溶剂化弱的一边（问题 1）。", 0, True),
        ("fig_molecular_universe.png", "分子宇宙（数据概况）",
         f"照 SES AI Molecular Universe 的做法：背景 = QM9 的 {mu['背景分子']:,} 个小分子（GDB-17 中所有不超过 9 个重原子的 C/N/O/F 稳定分子），"
         f"313 篇用到的 {mu['文献分子']} 个中性有机分子（绿）叠在上面，位置 = 结构相似度（Morgan 指纹、Jaccard 距离、UMAP）。左：全景，文献分子只落在几个角落。"
         f"右：近景，{mu['文献分子']} 个分子和各自最相近的 120 个 QM9 分子（共 {mu['近景背景分子']:,} 个）重新降维，文献分子分成链状醚与氟化醚、碳酸酯/酯/酰胺、"
         "环状碳酸酯、环醚、芳香与含硫硒添加剂几块；背景点 = 结构相近但 313 篇里没人用过的分子（蓝 = 附近少、红 = 附近多）；金黄 = 问题 1 的含氟稀释剂。"
         "位置只表示结构相近（UMAP 降维），横纵坐标本身没有单位和物理含义。锂盐、离子、多硫化物不在图中。", 0, True),
        ("图7a_说法地图_T1.html", "补充 · 说法地图（问题 1）",
         f"一个点 = 一篇论文的一条机制说法；横轴 = 发表年份，上下两带 = 两派立场（读原文判断）。“LiF 来自阴离子”一派 {cm['T1']['2022 年及以后']['B']} 篇在 2022 年以后。", 560, True),
        ("图7b_说法地图_T3.html", "补充 · 说法地图（问题 2）", "画法同上。", 560, True),
        ("图7c_说法地图_T4.html", "补充 · 说法地图（问题 3）", "画法同上。", 560, True)]
    fc = []
    for fn, title, desc, hgt, wide in figs:
        body = (f'<a href="图/{fn}" target="_blank"><img class="fig" src="图/{fn}" alt="{e(title)}" style="width:100%"></a>' if fn.endswith((".svg", ".png"))
                else f'<iframe class="fig" data-src="图/{fn}" height="{hgt}"></iframe>')
        sty = " style='grid-column:1/-1'" if wide else ""
        fc.append(f'<div class="card"{sty}><div class="card-top"><h3 style="margin:0">{title}</h3>'
                  f'<a class="note" href="图/{fn}" target="_blank">新窗口打开 ↗</a></div><p>{desc}</p>{body}</div>')
    figures = f"""<section id="figures" class="panel" hidden><div class="section-head"><h2>矛盾图</h2><span class="note">三个无定论问题各一张图（左数据、右机制）· 文字向量地图 · 配方空间、分子宇宙为数据概况 · 说法地图为补充 ·
313 篇 · 立场与读原文结果为 AI 辅助，用户尚未逐项人工确认 · 图上文字为英文</span></div>
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
               + meta_js +
               "const hh=location.hash.slice(1);if(hh&&$('nav button[data-panel=\"'+hh+'\"]'))$('nav button[data-panel=\"'+hh+'\"]').click();")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Li–S Statement Atlas · Pilot</title><style>{CSS}</style></head><body>
<header><div class="brand"><span class="mark">S</span>Li–S Statement Atlas</div><div class="meta">LI–S ELECTROLYTE CONFLICTS / 04 NOV 2026 / PILOT · MODELLING UPDATED 05 NOV · META &amp; ATTRIBUTION 06 NOV</div></header>
<main>{hero}{overview}{statements}{norm}{modelling}{meta}{conflicts}{figures}{data}
<div class="footer"><span>Preliminary · 30 papers (F-version, rule-processed) · AI-assisted, not yet confirmed item by item by the user</span><span>Opens offline · no network needed</span></div></main>
<script>const D={j(det)};{JS}{js_data}</script></body></html>"""
    (SITE / "index.html").write_text(page, encoding="utf-8")
    for old in ("表述表.html", "别名表.html", "条件表.html", "图.html", "归一化.html", "矛盾候选.html", "style.css"):
        if (SITE / old).exists():
            (SITE / old).unlink()  # 旧的中文多页版本，已并入单页
    print("网站：index.html（单页，英文）")


if __name__ == "__main__":
    main()
