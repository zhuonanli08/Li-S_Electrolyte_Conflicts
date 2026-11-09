"""step13s：结果网站（单页、标签切换；11-06 起文字中文、图英文；版式参照用户提供的 electrolyte-atlas.html，11-04 用户要求）。

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


# 11-06 用户要求全站文字中文（图仍英文）：翻译层改为直接显示提取出来的中文原文
def t(d, k, default=None):
    return k if k not in (None, "") else (default if default is not None else "—")


def statement_en(s, comp=None):
    return s["表述文字"]


def recipe_en(comp, fallback=""):
    return fallback or "（配方未记录）"

SITE = OUT / "网站"
TESTKIND = {}
CELL = {"扣式": "扣式", "软包": "软包", "其他": "其他"}
CTYPE_CN = {"NORM": "同一配方，归一化后仍差得远", "LOPO": "论文自己的结论 vs 不用这篇训练的模型的预测", "SAME": "同一个改动，结果方向相反",
            "FLIP": "同一对配方，换了条件后方向翻转", "DESC": "描述符变化方向相同，结果方向相反"}

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
  const q=document.createElement('input'); q.type='search'; q.placeholder=opt.placeholder||'搜索…'; tb.appendChild(q);
  (opt.selects||[]).forEach(c=>{const s=document.createElement('select'); const v=[...new Set(rows.map(r=>r[c]))].filter(x=>x!==''&&x!==null).sort();
    s.innerHTML='<option value="">全部 · '+cols[c]+'</option>'+v.map(x=>'<option>'+esc(x)+'</option>').join(''); s.onchange=()=>{f[c]=s.value;draw()}; tb.appendChild(s)});
  const rl=document.createElement('div'); rl.className='result-line'; const cnt=document.createElement('span'); rl.appendChild(cnt);
  const hint=document.createElement('span'); hint.textContent=opt.detail?'点击一行展开 · 点击表头排序':'点击表头排序'; rl.appendChild(hint);
  const wrap=document.createElement('div'); wrap.className='table-wrap'; wrap.style.maxHeight=(opt.height||560)+'px';
  const tbl=document.createElement('table'); wrap.appendChild(tbl); el.append(tb,rl,wrap); q.oninput=draw;
  function draw(){const qq=q.value.trim().toLowerCase();
    let rs=rows.map((r,i)=>[r,i]).filter(([r])=>Object.entries(f).every(([c,v])=>!v||String(r[c])===v)&&(!qq||JSON.stringify(r).toLowerCase().includes(qq)));
    if(st.sort!==null)rs.sort((a,b)=>{const x=a[0][st.sort],y=b[0][st.sort],nx=parseFloat(x),ny=parseFloat(y);
      const r=(!isNaN(nx)&&!isNaN(ny))?nx-ny:String(x).localeCompare(String(y));return st.asc?r:-r});
    cnt.textContent='显示 '+rs.length+' / '+rows.length+' 行';
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
    """“放电容量类×5；衰减类×2”这类计数串，中文原样显示。"""
    return s or ""


def pct(r):
    if r is None:
        return ""
    return f"≈ ±{round((math.exp(r) - 1) * 100)}%" if r < 10 else "发散"


def pair_en(p: dict | None) -> str:
    """一对比较的中文说明（函数名沿用）。"""
    if not p:
        return ""
    if p.get("翻转"):
        a, b, va, vb, d = p["B"], p["A"], p["B值"], p["A值"], {"变好": "变坏", "变坏": "变好"}.get(p["方向"], p["方向"])
    else:
        a, b, va, vb, d = p["A"], p["B"], p["A值"], p["B值"], p["方向"]
    return (f"{p['论文']} {p['测试']} · {a}（{va}）对 {b}（{vb}）\n{p['标准指标']} · 取值点（提取原文）：{p['取值点']}\n"
            f"→ {a} 比 {b} {d}（依据：{p['依据'] or '—'}）\n改动：{' '.join(p['完整签名']) or '—'}")


def verdict_badge(v: str) -> str:
    cls = {"✅": "", "🔶": "trial", "⚠️": "bad", "❌": "no"}.get(v, "planned")
    lab = {"✅": "✅ 原文证实", "🔶": "🔶 由未对齐的因素解释", "⚠️": "⚠️ 提取问题", "❌": "❌ 不是矛盾"}.get(v, "未核对")
    return f'<span class="badge {cls}">{lab}</span>'


# ---------- 04 modelling（11-05 用户要求：各轮方法、描述符、结果、不采纳理由；11-06 改中文）----------
M243 = ROOT / "output" / "表述试跑243篇_2026-11-04"
M313 = ROOT / "output" / "改动模型_313篇_2026-11-05"
C243 = {"放电容量类": "首圈容量", "衰减类": "容量保持", "库仑效率类·全电池": "全电池 CE", "库仑效率类·Li‖Cu": "Li‖Cu CE"}
C14 = {"首圈容量": "首圈容量", "每圈衰减率": "每圈衰减率", "全电池CE": "全电池 CE（循环）", "LiCu_CE": "Li‖Cu CE（循环）"}
C14TO243 = {"首圈容量": "放电容量类", "每圈衰减率": "衰减类", "全电池CE": "库仑效率类·全电池", "LiCu_CE": "库仑效率类·Li‖Cu"}
M14 = {"零": "预测没差别", "Huber": "Huber 回归", "HGB浅": "梯度提升（浅）", "HGB深": "梯度提升（深）", "RF": "随机森林", "ET": "极端随机树",
       "kNN5": "5 近邻", "SVR": "支持向量回归", "集成": "集成（岭回归＋随机森林＋浅梯度提升）"}
FAM = [("只有物性/结构", False, "物性/结构描述符，不加条件"),
       ("只有物性/结构", True, "物性/结构描述符＋条件"),
       ("物性/结构＋组分身份", True, "物性/结构＋组分身份＋条件"),
       ("只有组分身份", True, "组分身份＋条件")]
ROUNDS = [("r1", "第 1 轮", "物性/结构描述符组 × 所有模型，加或不加测试条件"),
          ("r2", "第 2 轮", "加组分有无（COMP）；试镜像增广、每篇等权、截尾训练目标"),
          ("r3多任务", "第 3 轮", "多任务：三类或四类一起训练，加类别指示"),
          ("r4", "第 4 轮", "加组分用量（AMT）和有无 × 条件（COMP×COND）；岭回归强度网格与集成")]
GROUPS_EN = [
    ("ER", "12", "配方层面的元素比例（照 Kim 等 PNAS 2023，只算溶剂和主盐）：溶剂 O 分三档（不含氟、β 氟化醚、α 氟化醚）、aO、aC、sC、aF、sF、F/C、O/C、F/O、InOr"),
    ("RD5", "5", "按溶剂摩尔分数加权的 RDKit 描述符：醚氧、环数、可旋转键、碳酸酯基、硫醚/多硫 S"),
    ("ADD", "8", "LiNO₃（M）、介体、其他添加剂、主盐（M）、每升阴离子 F、每升阴离子磺酰、含碘、有机硫"),
    ("SOLV", "20", "按溶剂加权的官能团与性质：醚氧、α/β 氟化醚氧、碳酸酯、羰基、砜、腈、酰胺、硫醚 S、F 与 C 原子、环、可旋转键、TPSA、分子量；"
                   "含氟、有机硫、烃、环醚、碳酸酯分子的比例"),
    ("STATE", "3", "由组成算出的溶剂化状态：ln（每个 Li⁺ 的配位位点）、稀释剂摩尔比例、Li⁺ 总浓度"),
    ("COMP", "{v}", "在至少两篇开发集论文里出现的每个组分的有无"),
    ("AMT", "{v}", "这些组分的用量（每升溶剂的摩尔数），组成能换算时才有"),
    ("COMP×COND", "2 × {v}", "有无 × 参照 ln E/S，有无 × 参照硫载量"),
    ("条件", "7 / 4", "Li–S 各类：ln E/S、硫载量、正极含硫、ln 倍率、温度、软包、ln 圈数。Li‖Cu：ln 电流密度、ln 沉积容量、ln 圈数、温度")]


def f2(x) -> str:
    return "—" if x is None else f"{x:+.2f}"


def m14(k: str) -> str:
    return f"岭回归 α = {k[len('岭回归a'):]}" if k.startswith("岭回归a") else M14.get(k, k)


def cfg14(b: dict) -> str:
    """一个配置的简述：描述符组 · 模型 · 训练技巧。"""
    tricks = [k for k in ("镜像", "每篇等权", "截尾") if b.get(k)]
    return f"{b['描述符'].replace('COMPxCOND', 'COMP×COND')} · {m14(b['模型'])}" + (f" · {'、'.join(tricks)}" if tricks else "")


def change_en(x: dict) -> str:
    """同一改动的例子：只“去”不“加”的改写成“加”、效应取反，读起来顺。效应 > 0 = 实验侧更好。"""
    if not x["加"] and x["去"]:
        lab, lo, hi = "加 " + "、".join(x["去"]), -x["效应最大"], -x["效应最小"]
    else:
        lab = " · ".join(p for p in ("加 " + "、".join(x["加"]) if x["加"] else "", "去掉 " + "、".join(x["去"]) if x["去"] else "") if p)
        lo, hi = x["效应最小"], x["效应最大"]
    return f"{lab}：{x['论文数']} 篇、{x['配对数']} 对，效应 {lo:+.2f} 到 {hi:+.2f}"


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
    leak_html = (f"<div class='callout warn'><b>每圈衰减率的圈数泄漏（11-05 深夜发现，本页复核）。</b>第 4 次迭代把 ln（圈数）留在了每圈衰减率的输入里，"
                 f"违反了你 11-05 定的规则。只用两边 ln（圈数）之差，就能解释开发集配对 R² {lk['总体']['只用Δln圈数R2']:.2f}——跨测试配对 "
                 f"{lk['跨测试、不同配方']['只用Δln圈数R2']:.2f}，同测试配对（两边圈数相同）{lk['同测试、不同配方']['只用Δln圈数R2']:.2f}。"
                 f"每圈衰减率 = 总损失 ÷ 圈数，圈数本身泄露了一部分答案。下面每圈衰减率的结果（开发集、考试集、加条件后的提升）因此都不能当作可迁移的证据。"
                 f"其他三类同样的检查 R² ≤ {lk_other:.2f}。"
                 + (f"<br><b>去掉圈数重跑（另一会话，11-06；考试集第二次使用）。</b>选定配置 "
                    f"{e(cfg14(rr['配置']['每圈衰减率']))}，开发集 R² {f2(rr['配置']['每圈衰减率']['开发集R2'])}；考试集 R² <b>{f2(rr['类别']['每圈衰减率']['总体'])}</b>"
                    f"（95% 区间 {f2(rr['类别']['每圈衰减率']['总体95%区间'][0])}～{f2(rr['类别']['每圈衰减率']['总体95%区间'][1])}），同测试配对 "
                    f"{f2(rr['类别']['每圈衰减率']['同测试、不同配方'])}，圈数相差 ≤ 5 倍的配对 {f2(rr['类别']['每圈衰减率']['圈数相差≤5倍']['R2'])}。"
                    "去掉泄漏后，每圈衰减率同样不能跨论文迁移。文件：<span class='mono'>output/改动模型_去圈数_313篇_2026-11-06/</span>。"
                    if rr else "去掉圈数的重跑正在另一会话进行。") + "</div>")
    fam = lambda c, f, cond: cmp_[c]["按描述符与条件"].get(f"{f}｜{'加条件' if cond else '不加条件'}")

    # 第 1–3 次迭代（30 篇、243 篇）
    sel1 = {n: next(m for m in r["模型比较"] if m["模型"] == r["主模型"]) for n, r in nres.items() if n in C243}
    it1 = "<br>".join(f"{C243[n]} {f2(m['V1篇内R2'])} <span class='note'>（{e(t(MODEL, m['模型']))}）</span>" for n, m in sel1.items())
    v3best = lambda r: max(x["R2"] for x in r["模型V3"].values())
    it2 = "<br>".join(f"{C243[n]} {f2(v3best(m243[n]))} <span class='note'>（猜没差别 {f2(m243[n]['基线']['猜没差别']['R2'])} · "
                      f"猜其他论文平均提升 {f2(m243[n]['基线']['猜其他论文平均提升']['R2'])}）</span>" for n in C243)
    pairs2 = " · ".join(f"{C243[n]} {m243[n]['V3配对']}" for n in C243)

    def pbest(d):
        res = d["结果"]
        base = max(x["R2"] for k, x in res.items() if k.startswith("对照"))
        k, x = max(((k, x) for k, x in res.items() if not k.startswith("对照")), key=lambda kv: kv[1]["R2"])
        add, _, mdl = k.partition("｜")
        return base, x["R2"], f"{add}，{t(MODEL, mdl)}"
    it3 = "<br>".join(f"{C243[n]} {f2(pbest(d)[0])} → {f2(pbest(d)[1])} <span class='note'>（{e(pbest(d)[2])}）</span>" for n, d in p243.items())
    imp = [q["按论文留出R2"] for d in p243.values() for q in d.get("补值小模型质量", {}).values() if q.get("按论文留出R2") is not None]
    imp_txt = f"{min(imp):+.2f} 到 {max(imp):+.2f}（{len(imp)} 个中 {sum(x < 0 for x in imp)} 个小于 0）"
    imp_n = [q["配方"] for d in p243.values() for q in d.get("补值小模型质量", {}).values() if q.get("配方")]
    np3 = [d["V3配对"] for d in p243.values() if d.get("V3配对")]
    star = lambda c: "*" if chk[c]["选定时用了过期记录"] else ""
    it4 = "<br>".join(f"{C14[c]} {f2(chk[c]['现行数据上按规则应选']['总体'])} → {f2(exam['类别'][c]['总体'])}{star(c)}" for c in C14)
    n_exam = sum(exam["类别"][c]["n"] for c in C14)
    itrows = [
        ("1", "11-04 · 30 篇（F 版试跑）",
         "用一个共同的打分函数把每篇归一化到同一标准条件。V1：留出一篇，给它的篇内差别打分",
         "sO 三档、aC、F/O、InOr、LiNO₃、主盐、其他添加剂 ＋ E/S、硫载量、正极含硫、倍率、温度、软包、圈数",
         "岭回归、线性混合模型、梯度提升、单调梯度提升、随机森林、高斯过程",
         "V1 R²（选定模型）：<br>" + it1, "配方效应不能迁移到没见过的论文；03 页的排名只作示意"),
        ("2", "11-04 · 243 篇",
         f"V3：留出唯一直接比较某一对配方的那篇，再用其他论文和描述符推这对的差距（配对数：{pairs2}）",
         "13 个元素比例 ＋ 5 个 RDKit（醚氧、环、可旋转键、碳酸酯基、硫醚/多硫 S）＋ LiNO₃、添加剂/介体 ＋ 测试条件（含截止电压）",
         "同样六种模型", "V3 R²（六种里最好，括号内为基线）：<br>" + it2,
         "不比两条基线好；整类留出（氟化溶剂、有机硫）时失败"),
        ("3", "11-04 · 243 篇", "同 2 的 V3，物性层逐个加（每类 3 种模型 × 6 组特征 = 18 次）",
         "2 ＋ <b>A</b> 由组成算的溶剂化状态 · <b>B</b> 分子性质（实际只有配位原子的 Gasteiger 电荷）· "
         "<b>C</b> 同篇实测的电导率/黏度 · <b>D</b> 用“组成 → 物性”模型补出的物性",
         "岭回归、单调梯度提升、随机森林", "V3 R²，对照 → 加物性后最好：<br>" + it3,
         f"容量和保持率没有提升；CE 的提升是 18 次里挑最好的，只有 {min(np3)}–{max(np3)} 对，在噪声范围内；补值模型 {imp_txt}"),
        ("4", "11-05 · 313 篇",
         f"改动模型：篇内所有比较（含跨条件配对）。开发集 {dg['开发集']['配对']} 对、{dg['开发集']['论文']} 篇（按论文分组 5 折交叉验证）；"
         f"另留 {n_exam_papers} 篇的 {n_exam} 对作考试集，只算一次",
         "描述符组 ER、RD5、ADD、SOLV、STATE、COMP、AMT、COMP×COND ＋ 条件（见下）",
         "岭回归（α 0.3–100）、Huber、梯度提升、随机森林、极端随机树、kNN、SVR、集成；多任务",
         "开发集最好 R² → 考试集 R²：<br>" + it4,
         "只有每圈衰减率在考试集上大于 0——95% 区间跨 0，而且圈数泄漏了答案（见上方提示）"),
    ]
    it_html = "".join("<tr>" + "".join(f"<td>{x}</td>" for x in r) + "</tr>" for r in itrows)

    # 第 4 次迭代细节
    g_html = "".join(f"<tr><td><b>{g}</b></td><td>{n.format(v=v)}</td><td>{d}</td></tr>" for g, n, d in GROUPS_EN)
    r_html = "".join(f"<tr><td><b>{lab}</b></td><td>{dg['各轮配置数'].get(k, 0)}</td><td>{e(what)}</td>"
                     f"<td class='mono'>{e(', '.join(x.replace('COMPxCOND', 'COMP×COND') for x in dg['各轮内容'][k]['描述符组']))}</td>"
                     f"<td>{e('、'.join(m14(x) for x in dg['各轮内容'][k]['模型']))}</td></tr>" for k, lab, what in ROUNDS)
    st_vals = [x.get("同测试、不同配方") for c in C14 for f, cond, _ in FAM for x in [fam(c, f, cond)] if x and x.get("同测试、不同配方") is not None]

    def famcell(x):
        return "<td>—</td>" if not x else f"<td><b>{f2(x['总体'])}</b><br><span class='note'>同测试 {f2(x.get('同测试、不同配方'))}</span></td>"
    f_html = "".join(f"<tr><td>{e(lab)}</td>{''.join(famcell(fam(c, f, cond)) for c in C14)}</tr>" for f, cond, lab in FAM)
    f_html += "<tr><td>预测没差别（参照）</td>" + "".join(f"<td>{f2(cmp_[c]['零基线']['总体'])}</td>" for c in C14) + "</tr>"
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
        ("镜像增广（同时用 A − B 和 B − A 训练）", "开 / 关", lambda c: onoff(c, "镜像")),
        ("每篇等权", "开 / 关", lambda c: onoff(c, "每篇等权")),
        ("训练目标截尾 5–95%（第 2 轮）", "开 / 关", lambda c: onoff(c, "截尾")),
        ("多任务 · ER+RD5+ADD+SOLV", "联合 / 单类", lambda c: mt(c, "ER+RD5+ADD+SOLV")),
        ("多任务 · ER+RD5+ADD+SOLV+COMP", "联合 / 单类", lambda c: mt(c, "ER+RD5+ADD+SOLV+COMP")),
        ("加溶剂化状态 STATE（第 1 轮）", "加 / 不加", stt)))
    trick_d = [cmp_[c]["训练技巧"][f]["开"]["总体"] - cmp_[c]["训练技巧"][f]["关"]["总体"] for c in C14 for f in ("镜像", "每篇等权", "截尾")]
    mt_d = [x["多任务"]["总体"] - x["单类"]["总体"] for c in C14 for x in cmp_[c]["多任务"].values()]
    st_d = [abs(cmp_[c]["溶剂化状态STATE"]["加之后"]["总体"] - cmp_[c]["溶剂化状态STATE"]["加之前"]["总体"]) for c in C14]

    ex_html = ""
    for c in C14:
        s, r, k = exam["配置"][c], exam["类别"][c], chk[c]
        tag = " <span class='badge bad'>过期记录*</span>" if k["选定时用了过期记录"] else " <span class='badge bad'>圈数泄漏</span>" if c == "每圈衰减率" else ""
        ex_html += (f"<tr><td>{C14[c]}</td><td>{e(cfg14(s))}</td><td>{f2(s['开发集R2'])}{tag}</td><td>{r['n']} · {r['论文']}</td>"
                    f"<td><b>{f2(r['总体'])}</b></td><td>{f2(r['总体95%区间'][0])}～{f2(r['总体95%区间'][1])}</td>"
                    f"<td>{f2(r['同测试、不同配方'])}</td><td>{f2(r['跨测试、不同配方'])}</td><td>{f2(r['同配方、换条件'])}</td></tr>")
    stale = []
    for c in C14:
        k = chk[c]
        if k["选定时用了过期记录"]:
            right = k["现行数据上按规则应选"]
            stale.append(
                f"<b>*{C14[c]}。</b>选定配置依据的是剔除首圈 CE 之前算的记录（{k['选定时所用记录']['n']} 对，而现行是 {dg['开发集']['各类配对'][c]} 对）。"
                f"同一配置在现行数据上是 {f2(k['同一配置在现行数据上']['开发集R2'])}；按规则正确选，应选 {e(cfg14(right))}（{f2(right['总体'])}）。"
                f"所以考试集的 {f2(exam['类别'][c]['总体'])} 属于本不该选的配置。用正确配置重考等于第二次看考试集，由你决定。"
                f"结论不变：现行数据上没有单类配置的开发集 R² 超过 {f2(right['总体'])}。")
    stale_html = (f"<div class='callout warn'><b>11-05 晚发现的选择错误。</b>迭代记录里有 {dg['过期记录']['条数']} 条第 2 轮记录是在剔除首圈 CE 之前的数据上算的，"
                  f"与现行数据上重跑的同一配置重复。本页的比较只用现行数据上的 {dg['现行数据上的配置数']} 条记录。<br>{'<br>'.join(stale)}</div>") if stale else ""

    # 同一改动跨篇一致性
    co_html = ""
    for c in C14:
        x = cons[c]
        top = change_en(x["例子"][0]) if x["例子"] else "—"
        co_html += (f"<tr><td>{C14[c]}</td><td>{x['不同配方配对']}</td><td>{x['只改用量配对']}</td><td>{x['不同改动种数']}</td>"
                    f"<td>{x['在≥2篇出现的改动种数']} <span class='note'>（{x['在≥2篇出现的改动覆盖配对']} 对 · {x['覆盖比例']:.0%}）</span></td>"
                    f"<td>{f2(x['留一篇查表R2'])} · {x['方向一致率']:.0%} <span class='note'>（n = {x['查表配对数']}）</span></td>"
                    f"<td><b>{f2(x['只靠改动身份的上限R2'])}</b></td><td>{f2(ceil243.get(C14TO243[c]))}</td><td>{e(top)}</td></tr>")
    cl = [cons[c]["只靠改动身份的上限R2"] for c in C14]
    cv = [cons[c]["覆盖比例"] for c in C14]
    c243 = list(ceil243.values())
    fade, fade_r = exam["类别"]["每圈衰减率"], exam["类别"]["每圈衰减率"]["总体95%区间"]
    phys = "；".join(f"{C14[c].split('（')[0]} {f2(fam(c, '只有物性/结构', True)['总体'])} 对 {f2(fam(c, '只有组分身份', True)['总体'])}" for c in C14)

    rej = [
        ("圈数作为每圈衰减率的输入", "bad", "泄漏 · 已去掉并重考" if rr else "泄漏 · 去掉后重跑中",
         f"只用 Δln（圈数）就解释开发集配对 R² {lk['总体']['只用Δln圈数R2']:.2f}（跨测试配对 {lk['跨测试、不同配方']['只用Δln圈数R2']:.2f}）"
         + (f"；去掉后考试集 R² {f2(rr['类别']['每圈衰减率']['总体'])}" if rr else ""),
         "违反你 11-05 定的规则：每圈衰减率 = 总损失 ÷ 圈数，圈数泄露了一部分答案。重跑结果：output/改动模型_去圈数_313篇_2026-11-06/（另一会话）。"),
        ("目标 R² &gt; 0.8（11-05 定）", "bad", "达不到 · 新目标待你定",
         f"只靠改动身份的上限 {min(cl):+.2f} 到 {max(cl):+.2f}（313 篇）、{min(c243):+.2f} 到 {max(c243):+.2f}（243 篇）；"
         f"考试集最好 R² {f2(fade['总体'])}，还被圈数泄漏抬高",
         "同一个改动在不同论文里效应不同，只知道“改了什么”的模型不可能两边都对。建议的替代目标：已证实的矛盾里，测试条件能解释的比例。"),
        ("通过归一化做跨论文排名（03 页）", "bad", "不能用", "第 2–4 次迭代 V3 都失败",
         "方案 §8.7：V3 失败则不能跨论文给配方排名。03 页的排名只作为 30 篇的示意。"),
        ("物性/结构描述符作预测输入", "trial", "预测不采用 · 保留用于解释",
         f"开发集 R²，物性/结构＋条件 对 组分身份＋条件：{phys}。加溶剂化状态后 R² 最多变 {max(st_d):.2f}",
         "它们本身是配方的函数，只有抓到组分身份抓不到的机制时才会增加信息，这里没有看到。它们仍是解释矛盾用的语言。"),
        ("实测电导率/黏度（C 层）", "no", "不采用",
         "只有 35–60% 的建模数据报告；两者都有的只有 25 篇的 55 个配方（243 篇试跑）；没有超出噪声的提升", "太稀疏，无法训练。"),
        ("由组成补出的物性（D 层）", "bad", "否决",
         f"补值模型按整篇留出 R² {imp_txt}；每个模型只用 {min(imp_n)}–{max(imp_n)} 个配方训练",
         "补出来的值本身就不可预测。"),
        ("PubChem 分子性质（B 层）", "no", "拿不到",
         "110 个溶剂里介电常数 0 个、黏度 22 个；DME、DOL、EC、TTE 都缺；只试了 Gasteiger 电荷这一个替代量",
         "需要手册值（DN、介电常数）或方案 §7.17a 的 DFT/MD 特征。"),
        ("镜像增广 · 每篇等权 · 截尾目标", "no", "没有稳定提升",
         f"开减关：{min(trick_d):+.2f} 到 {max(trick_d):+.2f}，不同类别正负不一", "只在选择规则恰好选中时使用。"),
        ("多任务训练", "no", "没有稳定提升", f"联合减单类：{min(mt_d):+.2f} 到 {max(mt_d):+.2f}",
         "四类性能之间共享的信号不够，互相借不到力。"),
        ("截止电压作为输入", "no", "去掉（你 11-05 定）",
         "要求有它时，每个 Li–S 类别只剩 4–9 个条件齐全的篇内配对；不要求时 26–30 个",
         "报告很少。它的作用（低于约 1.6 V 时 LiNO₃ 还原贡献容量）在解释矛盾时处理，如 SAME001。"),
        ("CE 类里的首圈 CE", "trial", "第 4 次迭代已去掉 · 待你确认",
         "P017 内部首圈 CE 就从 8.8% 到 79.9%，跨测试配对还会拿它去配第 100 圈的 CE",
         "它测的是首圈不可逆损失（SEI 形成、LiNO₃ 还原），不是循环效率。"),
        ("低于 10 mAh g⁻¹ 的容量（P344，1.51）", "no", "去掉", "提取时单位出错", "—"),
        ("选定的全电池 CE 配置", "bad", "选择错误 · 是否重考待你定", "取自过期记录，见考试集一节", "全电池 CE 的结论（不能迁移）不变。"),
        ("预测性能绝对值", "planned", "没试 · 不算进展", "—",
         "R² 会很高，因为 E/S、载量、倍率决定了大部分绝对水平——这是条件和论文效应，不是电解液效应。只适合用来衡量条件能解释多少。"),
        ("NORM 和 LOPO 两条矛盾规则", "trial", "建议暂停 · 待你定", "都依赖归一化模型，而它的 R² ≈ 0",
         "SAME、FLIP、DESC 只需要方向，保留。"),
        ("表述的文本向量（MatSciBERT）", "trial", "建议推迟 · 待你定", "表述是由结构化字段按模板生成的",
         "直接比对字段更精确也更好核查；向量更适合作者自由书写的机制论断（Q2）。"),
        ("更多数据：读图补数、剩余 222 篇", "planned", "可选 · 需要提取费用", "论文多约 70%；很多对照侧的数值只在图里",
         "能增加配对和重复改动，但消除不了论文之间的不一致。"),
        ("DFT/MD 描述符（方案 §7.17a）", "planned", "已计划，用于解释而不是提高 R²", "尚未计算",
         "同一个改动在每篇论文里算出的值都一样，所以解释不了它为什么在不同论文里效应不同；可以在归因里解释机制。"),
    ]
    rj_html = "".join(f"<tr><td><b>{a}</b></td><td><span class='badge {cls}'>{s}</span></td><td>{ev}</td><td>{why}</td></tr>" for a, cls, s, ev, why in rej)
    cards = (f"<div class='card'><span class='badge bad'>考试集 · 最好的一类 · 有泄漏</span><h3 style='font-size:29px;margin:10px 0 4px'>{f2(fade['总体'])}</h3>"
             f"<p>每圈衰减率 · 95% 区间 {f2(fade_r[0])}～{f2(fade_r[1])} · {fade['论文']} 篇的 {fade['n']} 对 · 被圈数泄漏抬高"
             + (f"；去掉泄漏重考：<b>{f2(rr['类别']['每圈衰减率']['总体'])}</b>" if rr else "") + "。其他三类："
             f"{'、'.join(f2(exam['类别'][c]['总体']) + star(c) for c in C14 if c != '每圈衰减率')}。</p></div>"
             f"<div class='card'><span class='badge'>搜索过的配置</span><h3 style='font-size:29px;margin:10px 0 4px'>{dg['现行数据上的配置数']}</h3>"
             f"<p>在现行的 313 篇数据上分四轮完成；此前在 243 篇上每类试过 6 种模型（第 2 次迭代）和 18 组特征（第 3 次迭代）。</p></div>"
             f"<div class='card'><span class='badge bad'>在 ≥ 2 篇里出现的改动</span><h3 style='font-size:29px;margin:10px 0 4px'>{min(cv):.0%}–{max(cv):.0%}</h3>"
             f"<p>（占换配方配对的比例）。就算某个改动重复出现，只知道它是什么，最多解释 R² {min(cl):+.2f} 到 {max(cl):+.2f}。</p></div>")
    lift = lambda c: f"{f2(no_c(c))} 到 {f2(wi_c(c))}"
    reading = (f"<b>怎么读。</b>（1）同一测试里换电解液，跨论文预测不了：每一族描述符在同测试配对上的 R² 都在 "
               f"{min(st_vals):+.2f} 到 {max(st_vals):+.2f} 之间。（2）测试条件只对 Li‖Cu CE 有用，加上后开发集 R² 从 {lift('LiCu_CE')}。"
               f"每圈衰减率的提升更大（{lift('每圈衰减率')}），但几乎全来自泄漏答案的圈数。"
               "（3）物性和结构描述符并不比“知道有哪些组分”好。（4）大多数改动只在一篇论文里出现，重复出现的效应也不一致。"
               "所以只靠文字提取的文献数据，不管用什么模型，R² &gt; 0.8 都达不到。")
    steps = [("找候选", "在 313 篇的表述上找：SAME（同一改动、结果相反）、FLIP（同一对配方、条件让方向翻转）、DESC（描述符方向相同、结果相反）。都不需要模型。"),
             ("核对原文", "每个候选都对照原文、贴原句：✅ 🔶 ⚠️ ❌。"),
             ("归因 · 条件", "比较两边的测试条件：E/S、载量、正极含硫、倍率、温度、锂片厚度。条件不同是同一改动看起来不一样的最简单原因，所以先查。"),
             ("归因 · 机制", "条件解释不了的，调出每条表述关联的机制论断和支撑测量：哪些一致、哪些冲突、哪些常被声称却没人测。"),
             ("DFT/MD", "剩下的交给第一批 DFT/MD 计算（先算 TTE 和 LiNO₃，方案 §7.17a）。")]
    st_html = "".join(f"<div class='step'><span class='num'>{i}</span><div><b>{a}</b><p>{e(b)}</p></div></div>" for i, (a, b) in enumerate(steps, 1))
    th = lambda cols: "<tr>" + "".join(f"<th>{x}</th>" for x in cols) + "</tr>"
    cls4 = [C14[c] for c in C14]
    return f"""<section id="modelling" class="panel" hidden><div class="section-head"><h2>电解液改动的效果能不能跨论文预测？</h2>
<span class="badge bad">目标 R² &gt; 0.8 未达到</span></div>
<p>同一篇论文里比较的两个配方，用其他论文训练的模型，根据配方和测试条件预测它们的性能差多少。从 30 篇到 313 篇共四次迭代。
每次验证都整篇留出，因为同一篇论文的配方共用正极、工艺和实验室。R² = 1 表示完全正确；0 相当于“预测没差别”；小于 0 比这还差。</p>
<p class="note">数据：30 篇（第 1 次）、243 篇（第 2–3 次）、313 篇（第 4 次）· 初步、AI 辅助，用户尚未逐项人工确认 · 标“待你定”的事项等你决定</p>
{leak_html}
<div class="grid" style="margin-top:16px">{cards}</div>
<div class="callout warn">{reading}</div>
<h3 style="margin-top:26px">四次迭代一览</h3>
<div class="table-wrap"><table>{th(["#", "时间 · 数据", "问题 · 验证方式", "输入", "模型", "最好结果（R²）", "结论"])}{it_html}</table></div>
<p class="note">* 依据过期记录选出，见下面考试集一节。</p>
<div class="section-head" style="margin-top:32px"><h2>第 4 次迭代细节</h2><span class="note">313 篇 · 改动模型 · 共记录 {dg['迭代配置总数']} 条，其中 {dg['现行数据上的配置数']} 条在现行数据上</span></div>
<div class="two"><div class="sheet"><div class="eyebrow">描述符组</div>
<div class="table-wrap"><table>{th(["组", "特征数", "内容"])}{g_html}</table></div>
<p class="note">每个配方特征以“实验 − 参照”加参照值进入；条件同样。目标：ln 容量之差、−ln 每圈衰减率之差或 −ln(100 − CE) 之差，正值表示实验侧更好。
配对类型：同测试换配方 · 跨测试换配方 · 同配方换条件。</p></div>
<div class="sheet"><div class="eyebrow">搜索轮次</div>
<div class="table-wrap"><table>{th(["轮次", "配置数", "改了什么", "描述符组", "模型"])}{r_html}</table></div>
<p class="note">考试前定好的选择规则：每类取按论文分组 5 折开发集 R² 最高、单类训练的配置。从很多配置里挑最好的，会让开发集分数偏乐观。</p></div></div>
<h3 style="margin-top:26px">描述符 vs 测试条件 · 开发集</h3>
<p class="note">每格是最好配置的结果。小字：同测试换配方配对上的 R²，即纯粹的电解液效应。每圈衰减率加条件的数值含圈数泄漏。</p>
<div class="table-wrap"><table>{th(["输入"] + cls4)}{f_html}</table></div>
<h3 style="margin-top:22px">训练技巧与多任务 · 开发集</h3>
<div class="table-wrap"><table>{th(["变体", "显示方式"] + cls4)}{t_html}</table></div>
<h3 style="margin-top:22px">考试集 · 只算一次</h3>
<div class="table-wrap"><table>{th(["类别", "选定配置", "选定时开发集 R²", "考试配对 · 论文", "考试集 R²", "95% 区间", "同测试", "跨测试", "换条件"])}{ex_html}</table></div>
{stale_html}
<div class="section-head" style="margin-top:32px"><h2>为什么 R² &gt; 0.8 达不到</h2><span class="note">只用开发集 · 没看考试集论文</span></div>
<p>一个“改动”就是一边有、另一边没有的东西（加 X 和去掉 X 算同一个改动的两个方向）。如果加 TTE 在一篇里变好、在另一篇里变差，
只知道“加了 TTE”的模型对两篇只能给出同一个预测，至少错一篇。重复改动内部剩下的方差，就是任何这类模型的上限。</p>
<div class="table-wrap"><table>{th(["类别", "换配方配对", "只改用量", "不同改动种数", "在 ≥ 2 篇出现", "用其他论文查表：R² · 方向",
                                    "只靠改动身份的上限", "上限（243 篇）", "重复最多的改动（ln 效应，+ = 更好）"])}{co_html}</table></div>
<p class="note">查表：用同一改动在其他论文里的平均效应预测这一对。上限：1 − 改动内方差 / 总方差，样本内计算（偏乐观）。
每类重复的改动只有 1–3 个，所以都是粗略估计。ADD_TRIAL 是结构未核实的添加剂的占位符，它的“重复”可能是不同的添加剂。</p>
<div class="section-head" style="margin-top:32px"><h2>不采纳的做法与原因</h2></div>
<div class="table-wrap"><table>{th(["事项", "状态", "证据", "原因"])}{rj_html}</table></div>
<div class="section-head" style="margin-top:32px"><h2>建议的下一步 · 矛盾分析</h2><span class="badge planned">等你决定</span></div>
<div class="sheet">{st_html}</div>
<div class="callout">文件：<span class="mono">output/表述试跑243篇_2026-11-04/</span> 试跑建模结果.json、物性对比/ ·
<span class="mono">output/改动模型_313篇_2026-11-05/</span> 选定配置.json、考试结果.json、迭代记录.jsonl、诊断.json。
脚本：<span class="mono">scripts/step13g_试跑243篇建模/</span>、<span class="mono">scripts/step14_改动模型/</span>（pairs、search、final、diagnose）。</div></section>"""


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
    vd = json.loads((ROOT / "output" / "组会图_2026-11-08" / "第13页向量图数据.json").read_text(encoding="utf-8"))
    # 11-08 夜（用户：“其它的问题也一起改了”“分子宇宙……再换其它的描述符试试”）：图注跟着改过的图更新，并加描述符版分子宇宙
    vk = vd["原始向量检验（step22b）"]
    md = json.loads((ROOT / "output" / "分子宇宙_描述符版_2026-11-08" / "汇总.json").read_text(encoding="utf-8"))
    use = mu["用量"]
    hi = q3["高盐且含 LiNO3"]
    # 11-09 用户：“每个图的文字标注部分整理下，1、是什么 2、怎么读图 3、说明佐证了哪些结论” → 每张图的说明分三段（读者：导师与组会）
    vk1, vfid, vrnd = vk["问题1"], vk["二维图保真"], vk["随机两条说法的余弦"]
    ax = md["轴的依据"]
    p371, p381 = q1["P371 系列（Taur，60 °C）"], q1["P381（T01）DBE / TTE"]
    ns = q2["≤ 0.5 M 去掉特殊组分后（变好/比较数）"]
    lo = {k: round(100 - v, 1) for k, v in q3["P112"].items()}
    fs = fsp["小图"]
    fe, ff, fsa, fl = fs["非氟醚氧"], fs["溶剂 F 原子数"], fs["主盐浓度"], fs["LiNO₃ 浓度"]
    sw = md["换溶剂箭头"]
    c1 = cm["T1"]
    figs = [
        ("fig_q1.png", "问题 1 · 稀释剂该不该分解？", (
            "问题 1“稀释剂该不该分解”的证据图。左：两篇反例论文各自的 Li‖Cu 库仑效率（CE）；右：文献里 LiF 从哪来的两种说法（示意），以及一个可检验的实验。",
            "左图横轴 = 每个溶剂/稀释剂分子含几个 F，纵轴 = Li‖Cu CE。每条线只比同一篇论文里的配方（同盐、同测试），两篇之间不比。"
            "红线 P371：同一骨架（1,2-二乙氧基乙烷）两端逐步加氟，60 °C、不含 LiNO₃；紫色虚线 P381：把整个稀释剂从 DBE 换成 TTE（换分子，不是逐步加氟），30 °C。"
            "左上标题写的是多数论文的结论。右图：上方两个框是 LiF 的两种来源，箭头指向锂负极表面的 SEI，框上方写着各有几篇论文持这种说法。",
            f"① “含氟越多 CE 越高”有例外：{q1['有含氟数变化的同测试比较的论文']} 篇有含氟数变化的论文里，{q1['每个比较都是含氟多 CE 高的论文']} 篇每个比较都符合；"
            f"P371 中一端不含氟的 F3DEE（{p371['F3DEE']:.1f}%）比不含氟的 DEE（{p371['DEE']:.1f}%）还差，同为部分氟化的 F4DEE、F5DEE 却最好，"
            f"说明关键可能是氟的位置和分布，而不只是有没有氟；P381 不含氟的 DBE（{p381[0]}%）反而比 TTE（{p381[1]}%）好。"
            f"② 文献对 LiF 的来源有分歧：{len(q1['路线 1 论文'])} 篇认为稀释剂自己分解出 LiF 有利，{len(q1['路线 2 论文'])} 篇认为 LiF 主要来自阴离子、稀释剂应保持稳定，"
            "后一派多在 2022 年以后。注意：P371 是 60 °C 的数据；右图是对文献说法的整理，不是本课题的验证结果。"), 0, True),
        ("fig_q2.png", "问题 2 · LiNO₃ 加多少最好？", (
            "问题 2“LiNO₃ 加多少最好”的证据图。左上：只改 LiNO₃ 用量、测了至少 3 个浓度的两篇论文；左下：所有配方的 LiNO₃ 用量分布；右：收益与代价的概念示意（不是拟合）。",
            "左上横轴 = LiNO₃ 浓度，纵轴 = 比该篇最低浓度时衰减慢了几倍（大于 1 更好，虚线 = 和最低浓度一样），灰底 = 0.5 M 以上。左下柱高 = 配方数。"
            "右图：蓝线 = 负极上的收益（随用量饱和），橙线 = 正极低电位还原的代价（随用量增加），黑线 = 两者之和，黑点 = 最佳用量；"
            "下方横条示意最佳用量随放电截止电压、电解液用量往哪边移。",
            f"① 0.5 M 以下多加有利：{q2['其中变好']}/{q2['较高浓度 ≤ 0.5 M 的比较']} 个比较（{q2['≤ 0.5 M 涉及论文']} 篇）衰减变慢，"
            f"去掉同时改了特殊组分的比较后仍是 {ns[0]}/{ns[1]}。"
            f"② 0.5 M 以上几乎没有数据：{q2['有 LiNO3 数值的配方']} 个有用量的配方里只有 {q2['高于 0.6 M 的配方']} 个超过 0.6 M；"
            "干净的剂量系列只有 P111，在 1.0 M 变差，而它的体系特殊（离子液体电解液、GO 正极）。所以“最佳用量在哪、由什么决定”现有文献回答不了，这就是无定论问题。"
            "右图是根据两派说法（各 6 篇）做的推论，需要实验检验。"), 0, True),
        ("fig_q3.png", "问题 3 · 高盐和 LiNO₃ 是替代还是互补？", (
            "问题 3“高盐和 LiNO₃ 是替代还是互补”的证据图。左：唯一把两者交叉测过的 P112，四个电解液每圈损失的锂；中：313 篇里“盐浓度 × 是否加 LiNO₃”四种组合各有多少配方；"
            "右：两种解释的示意，以及区分它们的实验。",
            "左图柱高 = 每圈损失的锂（100 − CE，越低越好），柱上“÷”是相对“1 M、不加 LiNO₃”降低的倍数。中图方块面积 = 配方数，红色 = 高盐（大于 1 M）且含 LiNO₃。"
            "右图左半“替代”：两者作用在同一处（负极 SEI），有一个就够；右半“互补”：各管一件事（LiNO₃ 成膜；高盐减少多硫化物溶解，让 LiNO₃ 消耗得慢）。",
            f"① 在 Li‖Cu 里，两者对负极的作用重叠：只加 LiNO₃ 每圈锂损失从 {lo['1 M']}% 降到 {lo['1 M +LiNO3']}%，只提盐降到 {lo['4 M']}%，"
            f"有了 LiNO₃ 再提盐没有额外收益（{lo['4 M +LiNO3']}%）。"
            f"② 两者在锂硫全电池里是否互补没有数据：{q3['有两个数值的配方']} 个配方里高盐加 LiNO₃ 只有 {hi[0]} 个（{len(hi[1])} 篇），交叉着测的只有 P112，"
            f"而 Li‖Cu 里没有多硫化物，回答不了这个问题。右图“替代”一方的 {len(q3['替代一方'])} 篇是间接证据（说不用 LiNO₃ 也能稳定负极），"
            "并没有直接比较高盐和 LiNO₃。"), 0, True),
        ("fig_p13_vectors.png", "文字向量地图：定位相关说法，再读原文辨别立场", (
            f"313 篇提取出的 {vd['画出的说法']:,} 条中文机制说法，用中文句向量模型（bge-small-zh）把每条说法变成一串数字，再压到二维（UMAP）。"
            "A = 全图；B = 问题 1 附近的放大；C = 四组示例句的相似度。",
            "一个点 = 一条说法，颜色 = 按关键词粗分的话题（LiF/SEI/锂负极、多硫化物穿梭、转化与催化等）。离得近 = 讲的事相近，但只看大块区域："
            f"二维图只保留了约 {vfid['原向量10近邻在二维图仍为10近邻']:.0%} 的近邻关系，近邻里 {vfid['10近邻来自同一篇论文']:.0%} 来自同一篇论文，所以小团常是一篇论文的几条说法。"
            "B 中蓝、橙 = 问题 1 读原文判定的两派（放大框是围着这些点画的）。"
            f"C 中条长 = 两句话的相似度（0–1），竖线 = 语料里随机两条说法的相似度中位数（{vrnd['中位数']:.2f}）。",
            f"① 向量能把同一话题的说法找到一起：问题 1 每条说法的 50 个最近邻里，同问题说法是随机的 {vk1['倍数']:.0f} 倍。"
            f"② 向量分不出立场：两派分不开（AUC {vk1['分立场AUC_两两']:.2f}，0.5 = 随机），立场相反的两句话相似度高达 0.95–0.96。"
            "所以向量只用来定位、检索相关说法，立场必须读原文判断。"), 0, True),
        ("fig_formulation_space.png", "配方比较：多数规律与反例（11-09 重做）", (
            "把计票画出来：四个小图各对应一个本项目已有的描述符——非氟醚氧、溶剂 F 原子数（问题 1），主盐浓度、LiNO₃（问题 3）。"
            "每个点 = 同一篇论文、同一个 Li‖Cu 测试里比较过的一对电解液，点数和计票完全一致。"
            "旧版“配方空间”的横轴（每个 Li⁺ 的配位位点）以盐浓度为分母、与纵轴重复；上午的箭头版线条交叉看不清，均已替换。",
            "横轴 = 这对配方里该描述符往共识方向变了多少（非氟醚氧画“减少”，其余画“增加”；主盐是倍数）；纵轴 = CE 的变化，用每圈锂损失之比表示，往上 = 损失更少。"
            "上半浅蓝 = 符合多数论文的结论（蓝点），下半浅红 = 反例（红点），灰带 = 相差 5% 以内。"
            "实心点 = 这对配方只改了这一类东西；空心点 = 同时还改了别的（盐、LiNO₃、溶剂或特殊组分），即“比较不对等”。"
            "只给问题论文的反例点标号：溶剂两图标 P371、P381，盐图标 P112。",
            f"① 多数规律成立：醚氧减少 CE 升高 {fe['共识一侧']} 对 {fe['反例']}（{fe['论文']} 篇），F 增加 CE 升高 {ff['共识一侧']} 对 {ff['反例']}（{ff['论文']} 篇），"
            f"提盐 {fsa['共识一侧']} 对 {fsa['反例']}（{fsa['论文']} 篇），加 LiNO₃ {fl['共识一侧']} 对 {fl['反例']}（{fl['论文']} 篇）。"
            f"② 反例多半是比较不对等：醚氧图的 {fe['反例']} 个反例里只有 {fe['反例中实心（只改了这一类）']} 个是实心，"
            f"盐图 {fsa['反例']} 个里只有 {fsa['反例中实心（只改了这一类）']} 个，LiNO₃ 图 {fl['反例']} 个全是空心。"
            f"③ 剩下的实心反例就是找到的矛盾：F 图里 P371（DEE 对 F3DEE）、P381（DBE 对 TTE）是问题 1，P263、P245 是读原文判为待定的；"
            "盐图里唯一的实心反例是 P112 “已加 0.5 M LiNO₃ 再把盐从 1 M 提到 4 M”（98.1% → 98.0%），正是问题 3。"), 0, True),
        ("fig_molecular_universe.png", "分子宇宙（数据概况）", (
            f"313 篇用到的 {mu['文献分子']} 个中性有机分子（溶剂、稀释剂、添加剂、介体），叠在 QM9 的 {mu['背景分子']:,} 个小分子"
            "（所有不超过 9 个重原子的 C/N/O/F 稳定分子）上，按结构相似度摆放（Morgan 指纹 + UMAP，照 SES AI 分子宇宙的做法）。"
            f"左 = 全景；右 = 近景（{mu['文献分子']} 个分子和各自最像的 400 个 QM9 分子，共 {mu['近景背景分子']:,} 个，重新降维）。锂盐、离子、多硫化物不在图中。",
            "离得近 = 结构片段相近；背景颜色 = 附近分子多少（蓝少、红多）；绿点 = 文献分子（近景里点大小 = 论文数），金黄 = 问题 1 的含氟稀释剂，方框 = 常用分子的结构式。"
            "坐标没有物理含义，簇与簇之间的距离也没有意义；背景没有按稳定性筛选。",
            "① 文献分子按结构分成几个家族：链醚与氟化醚、碳酸酯/酯/酰胺、环状碳酸酯、环醚、芳香与含硫/硒添加剂；问题 1 的含氟稀释剂同属链状氟化醚一族。"
            f"② 集中的是用量，不是种类：非氟醚占全部使用的 {use['非氟醚使用占比']:.0%}（DME {use['DME']} 篇、DOL {use['DOL']} 篇），"
            f"{mu['文献分子']} 个分子里 {use['只在1篇出现']} 个只出现在 1 篇。"
            "这张图说明不了分子性质或氟化程度（指纹只记结构片段有没有，不同链长的甘醇二甲醚会重合），背景空白也不等于值得试的候选。"), 0, True),
        ("fig_molecular_map.png", "分子宇宙 · 描述符版（11-08 新增）", (
            f"同样的文献分子（{md['文献溶剂/稀释剂']} 个溶剂和稀释剂）叠在 QM9 小分子上，但坐标换成本项目已有的两个结构描述符："
            "横轴 sO（溶剂氧原子 ÷ 全部原子），纵轴 InOr（除 C、H 外的原子 ÷ C 原子）。原版分子宇宙保留。",
            "往右 = 氧多、溶剂化强；往上 = 杂原子（尤其是氟）多。背景颜色 = 附近分子多少（蓝少、红多）；小分子的这两个比值只有几百种取值，"
            "背景画成平滑后的密度，只看区域、不看单点。绿点 = 文献分子、金黄 = 含氟，点大小 = 论文数，位置精确。"
            "箭头 = 同一篇、同一个 Li‖Cu 测试里只把一种溶剂换成另一种（其余都不变）的比较，一律指向共识方向（左上）那一侧："
            "蓝 = 箭头指向的溶剂 CE 更好，红 = 更差，线越粗变化越大；左下角列出全部红箭头。",
            f"① 这两个描述符在本项目数据里站得住：Li‖Cu 篇内比较 sO 越多 CE 越差（q = {ax['sO_q']:.2f}），InOr 越大 CE 越好（q = {ax['InOr_q']:.2f}），"
            f"与 Kim 2023 一致；计票里非氟醚氧越多越差（{ax['非氟醚氧'][1]:.0%}，{ax['非氟醚氧'][2]} 篇），F 原子数越多越好（{ax['F原子数'][1]:.0%}，{ax['F原子数'][2]} 篇）。"
            f"② 换溶剂的箭头在分子层面重现了这条规律：{len(sw['论文'])} 篇论文里 {sw['组数']} 组只换一种溶剂的比较，往左上走 {sw['好']} 组变好、{sw['差']} 组变差"
            f"（{sw['好'] / max(1, sw['好'] + sw['差']):.0%}）。"
            f"③ 变差的就是矛盾：{'、'.join(sorted({x['论文'] for x in sw['红']}))}，其中 P371（DEE → F3DEE）、P381（DBE → TTE）正是问题 1 的反例。"
            "④ 文献溶剂的分布：甘醇醚、环醚在中下部，碳酸酯在右侧，含氟醚在左上。"), 0, True),
        ("图7a_说法地图_T1.html", "补充 · 说法地图（问题 1）", (
            "问题 1 相关机制说法的时间线：一个点 = 一篇论文里的一条说法（从 313 篇已提取的 7,477 条机制里按关键词筛出，读后归派）。",
            "横轴 = 发表年份（~ = 按论文编号推断）；上、下两条带 = 读原文判定的两派，中间 = 相关但不站队；实心 = 作者的结论，空心 = 推测或转述；"
            "★ = 发现这个矛盾的反例论文。带内的高低和灰线来自文字向量，只表示两条说法讲的是同一件事，不代表引用或反驳关系。",
            f"“LiF 主要来自阴离子、稀释剂应保持稳定”一派 {len(q1['路线 2 论文'])} 篇里 {c1['2022 年及以后']['B']} 篇发表于 2022 年以后"
            f"（{c1['2022 年及以后']['B'] / len(q1['路线 2 论文']):.0%}），“稀释剂分解有利”一派 {len(q1['路线 1 论文'])} 篇里 {c1['2022 年及以后']['A']} 篇"
            f"（{c1['2022 年及以后']['A'] / len(q1['路线 1 论文']):.0%}），和整个语料差不多（有年份的论文里 2022 年以后约占 44%）：前一种看法是近几年才多起来的。"
            "说法按关键词筛选、只看摘要归派，可能有漏（向量检索在问题 1 附近还找到 3 篇关键词漏掉的相关论文）。"), 560, True),
        ("图7b_说法地图_T3.html", "补充 · 说法地图（问题 2）", (
            "问题 2（LiNO₃ 用量）相关机制说法的时间线，画法同问题 1。",
            "同问题 1：横轴年份，上下两带是两派，实心 = 结论、空心 = 推测或转述，★ = 反例论文 P111。",
            f"两派——“LiNO₃ 在负极被消耗、耗尽就失效，多加有利”和“LiNO₃ 在正极低电位不可逆还原，加多了有害”（各 6 篇）——都集中在 2017–2021 年"
            f"（两派年份中位数都在 2018–2019 年），2022 年以后只有 {cm['T3']['2022 年及以后']['A'] + cm['T3']['2022 年及以后']['B']} 篇；P083 两种说法都有。"
            "说明这个问题近几年没有人系统回答。"), 560, True),
        ("图7c_说法地图_T4.html", "补充 · 说法地图（问题 3）", (
            "问题 3（高盐与 LiNO₃）相关机制说法的时间线，画法同问题 1。",
            "同问题 1：横轴年份，上下两带是两派，实心 = 结论、空心 = 推测或转述，★ = 交叉设计论文 P112。",
            f"“不用 LiNO₃ 也能稳定负极（弱溶剂化、含氟、有机 SEI 等）”一派 {len(q3['替代一方'])} 篇，年份中位数 {cm['T4']['年份中位数']['A']:.0f} 年；"
            f"“LiNO₃ 的作用别的替代不了”一派 {len(q3['互补一方'])} 篇，中位数 {cm['T4']['年份中位数']['B']:.0f} 年。"
            "两派都没有直接比较高盐和 LiNO₃，直接证据只有 P112（星标）。"), 560, True)]
    LAB3 = ("是什么", "怎么读", "说明了什么")
    fc = []
    for fn, title, desc, hgt, wide in figs:
        body = (f'<a href="图/{fn}" target="_blank"><img class="fig" src="图/{fn}" alt="{e(title)}" style="width:100%"></a>' if fn.endswith((".svg", ".png"))
                else f'<iframe class="fig" data-src="图/{fn}" height="{hgt}"></iframe>')
        sty = " style='grid-column:1/-1'" if wide else ""
        fc.append(f'<div class="card"{sty}><div class="card-top"><h3 style="margin:0">{title}</h3>'
                  f'<a class="note" href="图/{fn}" target="_blank">新窗口打开 ↗</a></div>'
                  + "".join(f'<p><b>{lab}</b>　{txt}</p>' for lab, txt in zip(LAB3, desc)) + f'{body}</div>')
    figures = f"""<section id="figures" class="panel" hidden><div class="section-head"><h2>矛盾图</h2><span class="note">三个无定论问题各一张图（左数据、右机制）· 文字向量地图 · 配方空间、分子宇宙（原版＋描述符版）为数据概况 · 说法地图为补充 ·
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
