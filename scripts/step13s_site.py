"""step13s：把 step13a–13e 的结果做成本地静态网站（11-04 用户定：所有结果用网站展示）。

输出：网站/index.html、表述表.html、别名表.html、条件表.html、图.html、矛盾候选.html、style.css
数据直接嵌在页面里，双击 index.html 用浏览器打开即可，不需要联网或服务器。
"""
from __future__ import annotations

import html
import math
import json

from step13_common import LABEL, OUT, in_analysis, read_json

SITE = OUT / "网站"
SITE.mkdir(exist_ok=True)
PAGES = [("index.html", "总览"), ("表述表.html", "表述表"), ("别名表.html", "指标与物性别名"), ("条件表.html", "测试条件"),
         ("图.html", "四张图"), ("归一化.html", "归一化与跨篇比较"), ("矛盾候选.html", "矛盾候选")]

CSS = """
body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;margin:0;color:#222;background:#fafafa}
header{background:#1f3b57;color:#fff;padding:14px 28px}
header h1{margin:0;font-size:20px} header .sub{font-size:13px;opacity:.85;margin-top:4px}
nav{background:#e8eef4;padding:8px 28px;position:sticky;top:0;z-index:5;border-bottom:1px solid #cdd8e3}
nav a{margin-right:18px;color:#1f3b57;text-decoration:none;font-size:14px} nav a.on{font-weight:bold;border-bottom:2px solid #1f3b57}
main{padding:18px 28px;max-width:1500px}
h2{font-size:18px;border-left:4px solid #1f3b57;padding-left:8px;margin-top:28px}
.note{background:#fff8e1;border:1px solid #f0d58c;padding:10px 14px;border-radius:4px;font-size:14px;line-height:1.7}
.warn{background:#fdecea;border:1px solid #f3b7b0;padding:10px 14px;border-radius:4px;font-size:14px;line-height:1.7}
table{border-collapse:collapse;font-size:13px;background:#fff;width:100%}
th,td{border:1px solid #d6dde4;padding:4px 6px;vertical-align:top;text-align:left}
th{background:#eef3f8;position:sticky;top:38px;cursor:pointer}
td{white-space:nowrap;max-width:420px;overflow:hidden;text-overflow:ellipsis}
main div[id^="t"]{overflow-x:auto}
tr.detail td{background:#f7fafc;white-space:pre-wrap;font-size:12.5px;max-width:none}
.kpi{display:inline-block;background:#fff;border:1px solid #d6dde4;border-radius:6px;padding:10px 16px;margin:6px 10px 6px 0;min-width:120px}
.kpi b{display:block;font-size:22px;color:#1f3b57}
.flow{display:flex;flex-wrap:wrap;align-items:stretch;gap:6px;margin:10px 0}
.step{background:#fff;border:1px solid #9fb3c8;border-radius:6px;padding:8px 10px;width:170px;font-size:13px;line-height:1.5}
.step.todo{border-style:dashed;color:#777} .arrow{align-self:center;font-size:20px;color:#9fb3c8}
.filters{margin:8px 0 10px} .filters input,.filters select{margin-right:10px;padding:3px 6px;font-size:13px}
iframe{width:100%;border:1px solid #d6dde4;background:#fff} img.fig{max-width:900px;width:100%;border:1px solid #d6dde4;background:#fff}
.tag{display:inline-block;padding:0 6px;border-radius:3px;font-size:12px;background:#eef3f8;margin-right:4px}
.mono{font-family:Consolas,monospace;font-size:12px}
"""

TABLE_JS = """
function makeTable(id, cols, rows, opts){
  opts = opts || {};
  const el = document.getElementById(id);
  const state = {sort:null, asc:true};
  const filt = {};
  const box = document.createElement('div'); box.className='filters';
  const q = document.createElement('input'); q.placeholder='全文搜索…'; q.size=30; box.appendChild(q);
  (opts.selects||[]).forEach(c=>{
    const s=document.createElement('select'); const vals=[...new Set(rows.map(r=>r[c]))].sort();
    s.innerHTML='<option value="">'+cols[c]+'：全部</option>'+vals.map(v=>'<option>'+v+'</option>').join('');
    s.onchange=()=>{filt[c]=s.value; draw();}; box.appendChild(s);
  });
  const cnt=document.createElement('span'); box.appendChild(cnt);
  el.appendChild(box);
  const t=document.createElement('table'); el.appendChild(t);
  q.oninput=draw;
  function draw(){
    const qq=q.value.trim();
    let rs=rows.filter(r=>Object.entries(filt).every(([c,v])=>!v||String(r[c])===v) && (!qq || JSON.stringify(r).includes(qq)));
    if(state.sort!==null){rs=[...rs].sort((a,b)=>{const x=a[state.sort],y=b[state.sort];
      const nx=parseFloat(x),ny=parseFloat(y); const r=(!isNaN(nx)&&!isNaN(ny))?nx-ny:String(x).localeCompare(String(y),'zh');return state.asc?r:-r;});}
    cnt.textContent='显示 '+rs.length+' / '+rows.length+' 行'+(opts.detail?'（点一行看全文）':'');
    let h='<tr>'+cols.map((c,i)=>'<th data-i="'+i+'">'+c+'</th>').join('')+'</tr>';
    rs.slice(0, opts.limit||2000).forEach((r,k)=>{h+='<tr data-k="'+rows.indexOf(r)+'">'+cols.map((c,i)=>'<td>'+(r[i]===null||r[i]===undefined?'':String(r[i]).replace(/</g,'&lt;'))+'</td>').join('')+'</tr>';});
    t.innerHTML=h;
    t.querySelectorAll('th').forEach(th=>th.onclick=()=>{const i=+th.dataset.i; state.asc=(state.sort===i)?!state.asc:true; state.sort=i; draw();});
    if(opts.detail) t.querySelectorAll('tr[data-k]').forEach(tr=>tr.onclick=()=>{
      if(tr.nextSibling && tr.nextSibling.classList && tr.nextSibling.classList.contains('detail')){tr.nextSibling.remove();return;}
      const d=document.createElement('tr'); d.className='detail'; d.innerHTML='<td colspan="'+cols.length+'">'+opts.detail(+tr.dataset.k).replace(/</g,'&lt;').replace(/&lt;b>/g,'<b>').replace(/&lt;\\/b>/g,'</b>')+'</td>'; tr.after(d);});
  }
  draw();
}
"""


def page(fname: str, title: str, body: str, extra_js: str = "") -> None:
    nav = "".join(f'<a href="{f}" class="{"on" if f == fname else ""}">{t}</a>' for f, t in PAGES)
    (SITE / fname).write_text(f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8"><title>{title}｜课题二表述与矛盾试跑</title>
<link rel="stylesheet" href="style.css"></head><body>
<header><h1>课题二 · 标准化表述与矛盾候选试跑</h1><div class="sub">{LABEL}｜2026-11-04｜AI 辅助生成与核对，用户尚未逐项人工确认</div></header>
<nav>{nav}</nav><main>{body}</main><script>{TABLE_JS}{extra_js}</script></body></html>""", encoding="utf-8")


def j(x) -> str:
    return json.dumps(x, ensure_ascii=False).replace("</", "<\\/")


def main() -> None:
    (SITE / "style.css").write_text(CSS, encoding="utf-8")
    a, b, c, d, e = (read_json(f"step13{x}_汇总.json") for x in "abcde")
    sts = read_json("表述.json")
    cands = read_json("矛盾候选.json")

    # ---------------- 总览 ----------------
    f = read_json("step13f_汇总.json")
    nres = read_json("归一化结果.json")
    finds = read_json("试跑发现.json") if (OUT / "试跑发现.json").exists() else {"发现": [], "待定": []}
    ncand = e["候选数"]
    judged = e["判定统计"]
    flow = [("提取结果", "规则处理版 30 篇：1054 条比较结果、214 条物性记录"),
            ("① 名称统一", f"205 种指标名 → 四类性能 {a['四类标准指标种数']} 个标准指标；物性 {a['物性原名种数']} 种名 → {a['标准物性种数']} 类"),
            ("② 测试条件", f"{b['性能测试数']} 个性能测试；正极硫含量 55 条逐条核定"),
            ("③ 表述", f"{c['表述条数']} 条表述（{c['配方数']} 个配方）"),
            ("④ 打分模型与归一化", "六种模型比较，四个性能模型（首圈放电容量、保持率、两种 CE）；换算到统一标准条件后跨篇比较"),
            ("⑤ 矛盾候选", "五种口径：" + "、".join(f"{k} {v}" for k, v in ncand.items())),
            ("⑥ 图与网站", "四张关联图＋三张归一化图")]
    fl = '<span class="arrow">→</span>'.join(f'<div class="step"><b>{h}</b><br>{t}</div>' for h, t in flow)
    kpi = lambda k, v: f'<div class="kpi"><b>{v}</b>{k}</div>'
    mrows = "".join(
        f"<tr><td>{n}</td><td>{v.get('论文', '')}</td><td>{v.get('数值', '')}</td><td>{v.get('主模型', v.get('跳过', ''))}</td>"
        f"<td>{v.get('主模型指标', {}).get('V1篇内R2', '')}</td><td>{v.get('主模型指标', {}).get('V1方向正确率', '')}</td>"
        f"<td>{v.get('主模型指标', {}).get('V2提升R2', '')}</td><td>{v.get('主模型指标', {}).get('越界率（非外推）', '')}</td>"
        f"<td>{v.get('标准醚基准', {}).get('普遍条件', '')}</td></tr>" for n, v in f["类别"].items())
    jrows = "".join(f"<tr><td>{t}</td><td>{ncand.get(t, 0)}</td><td>{'；'.join(f'{k} {n}' for k, n in judged.get(t, {}).items())}</td></tr>" for t in ncand)
    body = f"""
<div class="note"><b>这一版做了什么：</b>按你的要求做了归一化：用打分模型把每条实测值换算到同一套标准条件，再跨篇比较；然后在归一化之后重做了矛盾候选（五种口径），
图和网站都已更新。按你定的分析集，倍率容量不纳入、放电容量只看第一圈。30 篇只够跑通流程，模型验证结果偏弱，数字都标“初步”。验证细节见“归一化与跨篇比较”页第一节。</div>
<h2>流程</h2><div class="flow">{fl}</div>
<h2>关键数字</h2>
{kpi("条表述", c['表述条数'])}{kpi("篇论文", c['论文数'])}{kpi("个配方", c['配方数'])}{kpi("个性能测试", b['性能测试数'])}
{''.join(kpi(f'条 {k} 候选', v) for k, v in ncand.items())}
<h2>归一化模型（每类选出的主模型）</h2>
<table><tr><th>性能类别</th><th>论文</th><th>数值条数</th><th>主模型</th><th>V1 篇内 R²</th><th>V1 方向正确率</th><th>V2 提升 R²</th><th>物理越界率</th><th>标准醚基准（普遍条件）</th></tr>{mrows}</table>
<p>V1 = 对没见过的论文，同篇配方之间的差距算得准不准（R² 越接近 1 越好，0 = 和“不预测差距”一样）；V2 = 同一篇换到没见过的条件，能不能换算准（相对“用本篇其他测试平均值猜”的提升）。
物理越界率 = 归一化后容量超过硫理论容量 1672 mAh g⁻¹ 或保持率超过 100% 的比例。详见“归一化与跨篇比较”页。</p>
<h2>矛盾候选（归一化后重做）</h2>
<table><tr><th>口径</th><th>候选数</th><th>回原文核对结果</th></tr>{jrows}</table>
<p>NORM = 归一化后同一配方跨篇仍差很多；LOPO = 某篇的结论与其他论文合起来训练的模型相反；FLIP = 同篇同一对配方换条件后结论翻转；DESC = 跨篇设计方向相同（只改溶剂/主盐）但结论相反；SAME = 改动完全相同但结论相反。</p>
<h2>这次试跑的主要发现</h2><ul>{''.join(f'<li>{x}</li>' for x in finds.get('发现', []))}</ul>
<h2>需要你定的事</h2><ul>{''.join(f'<li>{x}</li>' for x in finds.get('待定', []))}</ul>
<h2>一条表述长什么样</h2><div class="note mono">{html.escape(sts[0]['表述文字'])}</div>
<h2>文件</h2><p class="mono">output/表述与矛盾试跑_F版30篇_2026-11-04/：表述表.xlsx、别名表与复核表.xlsx、条件表.xlsx、归一化与跨篇比较.xlsx、矛盾候选复核表.xlsx，以及同名 JSON。脚本 scripts/step13a–13f、step13s。</p>
"""
    page("index.html", "总览", body)

    # ---------------- 表述表 ----------------
    cols = ["编号", "论文", "测试", "配方", "对照", "性能类别", "标准指标", "数值", "单位", "阶段", "圈数", "E/S", "硫载量", "正极含硫", "倍率", "温度", "电池形式", "电池类型", "物性项数", "归类", "进入分析"]
    cv = lambda s, f: s["条件"][f]["值"] if s["条件"][f]["值"] is not None else ""
    rows = [[s["表述编号"], s["论文"], s["测试"], s["配方"], "是" if s["是否对照"] else "", s["性能类别"], s["标准指标"], s["数值原文"], s["单位"],
             s["阶段"], s["圈数"] or "", cv(s, "ES"), cv(s, "sulfur_loading"), cv(s, "S_content"), cv(s, "rate"), cv(s, "temperature"),
             cv(s, "cell_format"), s["电池类型"], len(s["物性"]), s["归类状态"], "是" if in_analysis(s["性能类别"], s["阶段"]) else "否"] for s in sts]
    details = [f"<b>表述：</b>{s['表述文字']}\n\n<b>原文句子：</b>\n{s['原句']}\n\n<b>后台链接</b>（不进表述）：机制 {', '.join(s['机制链接']) or '无'}；支撑测量 {', '.join(s['支撑测量链接']) or '无'}"
               + (f"\n<b>疑似重复组：</b>{s['疑似重复组']}" if s.get("疑似重复组") else "")
               + (f"\n<b>归类说明：</b>{s['归类原因']}" if s["归类原因"] else "") for s in sts]
    body = f"""<div class="note">共 {len(sts)} 条。可按论文、性能类别、标准指标筛选，点表头排序，点一行展开完整表述、原文句子和后台机制编号。“进入分析”= 否 的是倍率容量和非首圈放电容量（你定这次不纳入分析，表里保留）。条件为空表示原文没写或算不出（Excel 里写了原因）。数值是原文值，未归一化。</div>
<div id="t"></div>"""
    page("表述表.html", "表述表", body, f"const C={j(cols)},R={j(rows)},D={j(details)};makeTable('t',C,R,{{selects:[1,5,6,17],detail:k=>D[k]}});")

    # ---------------- 别名表 ----------------
    al = read_json("指标别名表.json")
    pal = read_json("物性别名表.json")
    c1 = ["原名", "单位", "测试类型", "电池类型", "性能类别", "标准指标", "条数", "有数值", "论文数", "状态", "原因"]
    r1 = [[x["原名"], x["单位"], x["测试类型"], x["电池类型"], x["性能类别"], x["标准指标"], x["条数"], x["有数值条数"], x["论文数"], x["状态"], x["原因"]] for x in al]
    c2 = ["标准物性", "原名", "取值数", "论文", "来源类型"]
    r2 = [[x["标准物性"], x["原名"], x["取值数"], "、".join(x["论文"]), x["来源类型"]] for x in pal]
    body = f"""<div class="note">四类性能：放电容量类、倍率容量类、衰减类、库仑效率类；其余测量（阻抗、过电位、对称电池时长等）记“不进四类”，不生成表述。
✅ 规则直接判定；🔶 有推定（容量基准由条件文字判断、保持率分母未写明等）；⚠️ 单位与指标不符，不生成表述。
写不清基准的容量单独放在“比放电容量（基准未写明）”，不并进硫比容量（方案 §8.7：定义不同的不合并）。</div>
<h2>指标别名表（{len(al)} 行）</h2><div id="t1"></div><h2>物性别名表（{len(pal)} 行）</h2>
<div class="note">“作者解释”“非电解液本体性质”（SEI、碳载体、电池内扩散系数等）两类不进表述；“文献转述”的值也不进。</div><div id="t2"></div>"""
    page("别名表.html", "指标与物性别名", body,
         f"makeTable('t1',{j(c1)},{j(r1)},{{selects:[4,9]}});makeTable('t2',{j(c2)},{j(r2)},{{selects:[0]}});")

    # ---------------- 条件表 ----------------
    ct = read_json("条件表.json")
    cath = read_json("正极硫含量解析.json")
    names = [("ES", "E/S"), ("sulfur_loading", "硫载量"), ("S_content", "正极含硫%"), ("Li_thickness", "锂厚μm"), ("NP", "N/P"),
             ("rate", "倍率C"), ("temperature", "温度°C"), ("cell_format", "电池形式")]
    c3 = ["论文", "测试", "测试名", "测试类型"] + [x for _, n in names for x in (n, n + "状态")]
    r3 = []
    for r in ct:
        line = [r["论文"], r["测试"], r["测试名"], r["测试类型"]]
        for f, _ in names:
            x = r["条件"].get(f, {})
            v = x.get("值")
            if v is None and x.get("按配方"):
                v = "；".join(f"{k}={y['值']}" for k, y in x["按配方"].items() if y.get("值") is not None)
            line += [v if v is not None else "", x.get("状态", "")]
        r3.append(line)
    c4 = ["论文", "条件编号", "原文", "解析值", "核定值", "核定状态", "核定说明", "解析与核定一致"]
    r4 = [[x["论文"], x["条件编号"], x["原文"], x["解析值"], x["核定值"], x["核定状态"], x["核定说明"], x["解析与核定一致"]] for x in cath]
    body = f"""<div class="note">只整理有四类性能数值的 {len(ct)} 个测试。状态：✅ 原文写明；🔶 有换算或推定（室温按 25 °C、按 Li₂S/SPAN/Se/S 换算硫等）；⚠️ 冲突或多值；未报告 = 原文没写。
表述里，取值点写明的倍率、温度、载量会覆盖这里的测试级条件。</div><div id="t3"></div>
<h2>正极硫含量（极片基准）核定</h2><div class="note">规则（方案 §8.7）：直接写极片含硫的直接用；复合物含硫 × 复合物在浆料中的占比；只有复合物含硫、没有浆料配比的记缺失。
脚本正则只对 29/55，所以每条都由 Claude 读原文核定，表述用核定值。</div><div id="t4"></div>"""
    page("条件表.html", "测试条件", body, f"makeTable('t3',{j(c3)},{j(r3)},{{selects:[0,3]}});makeTable('t4',{j(c4)},{j(r4)},{{selects:[0,5]}});")

    # ---------------- 图 ----------------
    figs = [("图1a_配方组分共现网络.html", "图1a 配方组分共现网络（只看配方）",
             "每个点是一个组分，点越大用到它的配方越多；两点之间的线表示它们出现在同一个配方里，线越粗次数越多。鼠标停在点或线上看数字，可拖动、缩放。"),
            ("图1b_四部分共现网络.html", "图1b 组分＋物性＋条件＋性能共现网络",
             "四种颜色的点分别是组分、物性、条件档（如“E/S≤5（贫液）”）、性能档（归一化到普遍条件后，同一类里三等分：好/中/差）。线 = 两者同时出现在多少条表述里（只画 ≥10 条的）。"),
            ("图2a_配方物性弦图.png", "图2a 弦图：配方 × 物性",
             "左边一圈是组分化学类别，右边是物性类别；弦表示“含这类组分的配方报告了这项物性”（按配方计）。能看出哪些体系的物性测得多、哪些是空白。"),
            ("图2b_四部分弦图.png", "图2b 弦图：配方 × 物性 × 测试条件 × 性能",
             "四组弧：组分类别（蓝）、物性（橙）、测试条件（绿，只选贫液、高载量、软包、薄锂等关键档）、性能类别（红）。弦宽 = 两者同时出现的表述数（只画 ≥15 条的）。"),
            ("图3_四部分聚类热图.html", "图3 聚类热图：配方 × 物性 × 条件 × 性能",
             "每行一个配方（需能算元素比例且有归一化性能值），列分四块，用竖线隔开。颜色是标准化后的值（红高蓝低），灰 = 未报告或外推。行顺序按层次聚类排列。性能列是归一化到普遍条件后的值，可以跨篇比较；“篇内相对对照”两列是同篇比值。"),
            ("图4_表述文字向量图.html", "图4 表述文字向量图",
             "把每条表述的完整文字变成向量（字符片段统计，不是语义模型），再压到二维；越近的点文字越像。右上角可切换按性能类别、论文、电池类型着色，鼠标停在点上看整条表述。")]
    parts = []
    for f, t, desc in figs:
        if f.endswith(".png"):
            parts.append(f'<h2>{t}</h2><p>{desc}</p><a href="图/{f.replace(".png", ".svg")}" target="_blank"><img class="fig" src="图/{f}"></a>')
        else:
            h = 1000 if "图3" in f else 800
            parts.append(f'<h2>{t}</h2><p>{desc}（<a href="图/{f}" target="_blank">新窗口打开</a>）</p><iframe src="图/{f}" height="{h}"></iframe>')
    body = f'<div class="note">四张图都标“{LABEL}”。图形只表示关联，不证明因果；疑似重复的表述每组只计一次。</div>' + "".join(parts)
    page("图.html", "四张图", body)

    # ---------------- 归一化与跨篇比较 ----------------
    basis = read_json("标准条件依据.json") if (OUT / "标准条件依据.json").exists() else {}
    pct = lambda r: (f"约 ±{round((math.exp(r) - 1) * 100)}%" if r < 10 else "发散") if r is not None else ""
    vrows = []
    for n, r in nres.items():
        for m in r["模型比较"]:
            hl = ' style="background:#eef6ee"' if m["模型"] == r["主模型"] else ""
            vrows.append(f"<tr{hl}><td>{n}</td><td>{m['模型']}{'（主模型）' if m['模型'] == r['主模型'] else ''}</td>"
                         f"<td>{m['V1篇内R2']}</td><td>{m['V1篇内RMSE(ln)']}（{pct(m['V1篇内RMSE(ln)'])}）</td><td>{m['V1方向正确率']}（{m['V1方向对数']} 对）</td>"
                         f"<td>{m['V2提升R2']}</td><td>{m.get('V2 RMSE(ln)')}（{pct(m.get('V2 RMSE(ln)'))}）</td><td>{m.get('V2基线RMSE(ln)')}</td>"
                         f"<td>{m['越界率（非外推）']}</td></tr>")
    v4rows = "".join(f"<tr><td>{n}</td><td>{r['主模型']}</td><td>{(r.get('V4') or {}).get('参与排名配方数', '—')}</td>"
                     f"<td>{(r.get('V4') or {}).get('名次相关_中位数', '—')}（{(r.get('V4') or {}).get('名次相关_2.5–97.5%', '')}）</td>"
                     f"<td>{(r.get('V4') or {}).get('前5重合率_平均', '—')}</td></tr>" for n, r in nres.items())
    std_rows = "".join(f"<tr><td>{n}</td><td>{sn}</td><td>{'；'.join(f'{k} {v}' for k, v in d.items())}</td><td>{r['标准醚基准'].get(sn)}</td></tr>"
                       for n, r in nres.items() for sn, d in r["标准条件"].items())
    brow = "".join(f"<tr><td>{k}</td><td>{v['按论文中位数']}（{v['论文数']} 篇）</td><td>{v['按表述中位数']}（{v['表述数']} 条）</td></tr>"
                   for k, v in basis.get("共同条件", {}).items())
    bcls = "".join(f"<tr><td>{k}</td><td>{v['倍率']['按论文中位数']}</td><td>{'；'.join(f'{a} {b}' for a, b in v['标准倍率覆盖（2 倍内条数/总数）'].items())}</td>"
                   f"<td>{v['圈数']['按论文中位数']}（{v['圈数']['论文数']} 篇）</td></tr>" for k, v in basis.get("按类", {}).items())
    adopt = "；".join(f"{k}：{v}" for k, v in basis.get("采用", {}).items())
    fr_cols = ["性能类别", "标准条件", "名次", "名次区间", "论文", "配方", "对照", "相对标准醚倍数", "归一化值", "归一化值区间", "外推", "配方文字"]
    fr_rows = [[x["类别"], x["标准条件"], x["名次"] or "", x["名次区间"] or "", x["论文"], x["配方"], "是" if x["是否对照"] else "",
                x["倍数"] if x["倍数"] is not None else x["损失倍数"], x["归一化值"], x["归一化值区间"], x["外推"], x["配方文字"]]
               for r in nres.values() for x in sorted(r["配方"], key=lambda z: (z["标准条件"], z["名次"] or 999))]
    nst = read_json("归一化_表述.json")
    st_cols = ["表述", "性能类别", "论文", "测试", "配方", "实测值", "普遍条件归一化值", "外推", "未换算条件", "标准醚"]
    st_rows = [[x["表述编号"], x["类别"], x["论文"], x["测试"], x["配方"], x["实测值"], x.get("普遍条件_归一化值"), x.get("普遍条件_外推", ""),
                x["未换算条件"], "是" if x["标准醚"] else ""] for x in nst]
    body = f"""<div class="note"><b>怎么做的：</b>同一篇论文里的正极、工艺、课题组对所有配方一样，先把“论文自身的影响”扣掉，只用同一篇内配方之间的差距，
训练一个所有配方共用的打分函数。输入是配方描述符（配方级元素比例 sO 三档、aC、F/O、InOr，LiNO₃ 浓度，主盐浓度，有无其他添加剂）和测试条件
（E/S、硫载量、正极含硫、倍率、温度、软包；保持率和 CE 另加圈数）。每类性能各一个模型：首圈放电容量、容量保持率、全电池 CE、Li‖Cu CE。
输出是配方在标准条件下相对标准醚电解液的增益（倍数）；每条实测值换算到标准条件：换算后的值 = 实测值 × 模型在标准条件下的预测 ÷ 模型在实测条件下的预测。
原文没报告的条件不换算；离标准条件太远的标“外推”，不进排名和矛盾候选。<br>
<b>分析集（你定的）：</b>倍率容量这次不纳入；放电容量只用第一圈。</div>

<h2>一、验证结果</h2>
<p><b>验证方法（方案 §8.7 的 V1–V5，加一项物理检查）：</b></p>
<table><tr><th>验证</th><th>怎么做</th><th>回答什么问题</th><th>这次做了吗</th></tr>
<tr><td>V1 按论文留出</td><td>每次拿掉一整篇论文，用其余论文训练，再预测这篇里各配方之间的差距（去掉这篇的平均水平后比较）</td><td>对没见过的论文，配方之间谁好谁差、差多少，能不能算准</td><td>做了</td></tr>
<tr><td>V2 按测试留出</td><td>同一篇里有多个测试（不同条件）的，每次拿掉一个测试，用这篇其他测试和其他论文训练，预测被拿掉测试的数值；和“直接用这篇其他测试的平均值猜”比</td><td>换到没见过的条件，换算准不准，即归一化本身可不可靠</td><td>做了</td></tr>
<tr><td>V3 留出唯一直接比较</td><td>某两个配方只在一篇里直接比过，拿掉这篇，看靠其他论文推出的差距对不对</td><td>能不能做跨文献排名</td><td>没做：30 篇里配方之间的共同连接太少，凑不出足够的例子；全量后做</td></tr>
<tr><td>V4 按论文重抽样</td><td>有放回地抽论文、重新训练若干次，看配方名次和全数据结果的相关、前 5 名重合多少</td><td>排名稳不稳</td><td>做了（见下表）</td></tr>
<tr><td>V5 实验验证</td><td>挑几个配方在实验室同条件实测</td><td>最终检验</td><td>放到最后</td></tr>
<tr><td>物理越界</td><td>归一化后硫比容量超过 1672 mAh g⁻¹（含有机硫共溶剂的除外）或保持率超过 100% 的比例</td><td>模型有没有离谱外推</td><td>做了，也用于选模型</td></tr></table>
<p><b>指标怎么读：</b>R² 越接近 1 越好，0 表示和“完全不预测差距”一样，负数表示比不预测还差。RMSE 是 ln 单位的平均误差，括号里换成大约的百分比误差
（RMSE 0.2 ≈ ±22%）。V1 方向正确率 = 同一测试里配方比对照“好还是差”猜对的比例（随便猜是 50%）。V2 提升 R² = 相对“用本篇其他测试平均值猜”的改进，>0 才说明条件换算有用。</p>
<p><b>选择规则（先定后跑）：</b>物理越界率 ≤5% 的模型里选 V2 提升 R² 最高的；没有 V2 时看 V1。六种模型：线性岭回归、线性混合模型、梯度提升、
单调约束梯度提升（物理常识：容量随倍率、载量下降，随 E/S 上升；保持率随圈数、载量下降）、随机森林、高斯过程。线性混合模型没有正则，特征多、论文少时数值发散。</p>
<table><tr><th>性能类别</th><th>模型</th><th>V1 篇内 R²</th><th>V1 RMSE</th><th>V1 方向正确率</th><th>V2 提升 R²</th><th>V2 RMSE</th><th>V2 基线 RMSE</th><th>越界率</th></tr>{''.join(vrows)}</table>
<h3>V4 名次稳定性（主模型，普遍条件）</h3>
<table><tr><th>性能类别</th><th>主模型</th><th>参与排名配方数</th><th>名次相关（中位数，95% 范围）</th><th>前 5 名平均重合率</th></tr>{v4rows}</table>
<div class="warn"><b>结论：</b>30 篇数据太少。V1 的 R² 在 0 附近，说明“配方特征 → 性能”这部分对没见过的论文基本学不到；V2 在首圈放电容量等类别有正的提升，说明条件换算部分有一定作用；
两种 CE 各只有 5 篇，结果只作流程演示。排名和 NORM、LOPO 候选都要带着这个可靠性看。方案里“标准醚基准性能的取法”还没定，这里暂用各篇标准醚电解液实测值归一化后的中位数。</div>
<iframe src="图/图5a_模型比较.html" height="600"></iframe>
<h3>主模型验证散点（横轴实测、纵轴预测，越靠近虚线越准）</h3><iframe src="图/图5b_主模型验证散点.html" height="840"></iframe>

<h2>二、标准条件与依据</h2>
<p>你定的是“全类统一一套”。具体数值按方案“数据最密的位置”的原则，用 30 篇数据定：每篇论文先取自己的中位数，再取各篇的中位数（每篇一票，避免测得多的论文主导）；倍率另看标准倍率 2 倍以内的数据有多少条。</p>
<table><tr><th>条件</th><th>按论文中位数</th><th>按表述中位数</th></tr>{brow}</table>
<table><tr><th>类别</th><th>倍率按论文中位数</th><th>标准倍率覆盖（2 倍内条数/总数）</th><th>圈数按论文中位数</th></tr>{bcls}</table>
<p><b>采用：</b>{adopt}</p>
<table><tr><th>性能类别</th><th>标准条件</th><th>取值</th><th>标准醚电解液基准</th></tr>{std_rows}</table>

<h2>三、跨篇比较</h2>
<h3>排名（森林图）</h3><p>每个点是一个配方相对标准醚电解液的 ln 倍数（>0 更好），横线是按论文重抽样的 95% 区间；区间重叠的名次可视为并列。灰色 = 外推，不进排名。右上角切换类别和标准条件。</p>
<iframe src="图/图6_归一化跨篇排名.html" height="900"></iframe>
<h3>同一种电解液在各篇：归一化前后</h3><p>标准醚电解液（LiTFSI＋DOL/DME＋LiNO₃）在多篇都出现。灰点是实测值，红点是换算到普遍条件后的值；换算后各篇还差很多的，差别不能用已记录的条件解释，就是 NORM 类矛盾候选。</p>
<iframe src="图/图7_标准醚跨篇归一化前后.html" height="900"></iframe>
<h3>配方排名表</h3><div id="tf"></div>
<h3>每条表述的归一化值</h3><div id="ts"></div>"""
    page("归一化.html", "归一化与跨篇比较", body,
         f"makeTable('tf',{j(fr_cols)},{j(fr_rows)},{{selects:[0,1]}});makeTable('ts',{j(st_cols)},{j(st_rows)},{{selects:[1,2]}});")

    # ---------------- 矛盾候选 ----------------
    tnames = {"NORM": "归一化后同配方跨篇差距大", "LOPO": "篇内结论与跨文献模型相反", "FLIP": "条件依赖翻转", "DESC": "设计方向相反（只改溶剂/主盐）", "SAME": "严格同一改动"}
    tdesc = {"NORM": "同一配方在不同论文中，各自换算到普遍条件后仍相差 ≥1.5 倍（CE 损失比 ≥2 倍）；外推的表述不算。",
             "LOPO": "某篇“配方比对照好/差”的实测方向，与不含这篇训练的模型预测方向相反（两边差距都 ≥10%）。只在主模型 V1 篇内 R² > 0 的类别做；模型本身较弱，这类只作线索。",
             "FLIP": "同一篇里同一对配方，在一种条件下 A 更好、换个条件（或圈数）后 B 更好。这类不需要归一化，直接反映“配方好坏取决于条件”。",
             "DESC": "跨篇，两篇的改动都只涉及溶剂和主盐（LiNO₃、添加剂不变），溶剂氧比例 sO 或 F/O 往同一方向变，结论一好一坏。",
             "SAME": "两篇的主改动完全相同（如都加入同一种共溶剂），结论一好一坏。"}
    secs = []
    for t, nm in tnames.items():
        lst = [x for x in cands if x["类型"] == t]
        blocks = []
        for x in lst:
            blocks.append(f"""<h3>{x['候选编号']}　{html.escape(x['摘要'])}　<span class="tag">{x['性能类别']}</span><span class="tag">判定 {x['判定'] or '未核对'}</span></h3>
<table><tr><th style="width:50%">甲：{x['论文甲']}</th><th>乙：{html.escape(str(x['论文乙']))}</th></tr>
<tr><td>{html.escape(x['甲例'])}</td><td>{html.escape(x['乙例'])}</td></tr>
<tr><td class="mono" style="white-space:pre-wrap">{html.escape(x['原句甲'])}</td><td class="mono" style="white-space:pre-wrap">{html.escape(x['原句乙'])}</td></tr></table>
<p><b>核对：</b>{html.escape(x['核对说明'] or '（未核对）')}<br><b>依据句子：</b>{'、'.join(x['依据句子'])}<br><b>可能原因：</b>{html.escape(x['可能原因'])}<br><b>机制线索：</b>{html.escape(x['机制线索'])}</p>""")
        secs.append(f"<h2>{t}｜{nm}：{len(lst)} 条</h2><p>{tdesc[t]}</p>" + ("".join(blocks) or "<p>（没有候选）</p>"))
    body = f"""<div class="note">归一化之后重做的矛盾候选，共五种口径。每条都由 Claude 回原文核对，贴原句。
判定：✅ 原文支持、确实值得解释的矛盾；🔶 数值无误，但有未对齐的条件或定义差异可能解释差别；⚠️ 提取或归类有问题；❌ 不构成矛盾。
{('未做 LOPO 的类别：' + '；'.join(e['未做 LOPO 的类别'])) if e['未做 LOPO 的类别'] else ''}</div>""" + "".join(secs)
    page("矛盾候选.html", "矛盾候选", body)
    print("网站页面：", [p for p, _ in PAGES])


if __name__ == "__main__":
    main()
