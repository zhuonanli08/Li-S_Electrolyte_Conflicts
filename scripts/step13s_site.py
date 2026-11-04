"""step13s：把 step13a–13e 的结果做成本地静态网站（11-04 用户定：所有结果用网站展示）。

输出：网站/index.html、表述表.html、别名表.html、条件表.html、图.html、矛盾候选.html、style.css
数据直接嵌在页面里，双击 index.html 用浏览器打开即可，不需要联网或服务器。
"""
from __future__ import annotations

import html
import json

from step13_common import LABEL, OUT, read_json

SITE = OUT / "网站"
SITE.mkdir(exist_ok=True)
PAGES = [("index.html", "总览"), ("表述表.html", "表述表"), ("别名表.html", "指标与物性别名"), ("条件表.html", "测试条件"),
         ("图.html", "四张图"), ("矛盾候选.html", "矛盾候选")]

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
    flow = [("提取结果", "规则处理版 30 篇：1054 条比较结果、214 条物性记录", ""),
            ("① 名称统一", f"205 种指标名 → 四类性能 {a['四类标准指标种数']} 个标准指标；物性 {a['物性原名种数']} 种名 → {a['标准物性种数']} 类", ""),
            ("② 测试条件", f"{b['性能测试数']} 个性能测试；正极硫含量 55 条正极文字逐条核定", ""),
            ("③ 表述", f"{c['表述条数']} 条表述（{c['配方数']} 个配方）", ""),
            ("④ 四张图", "共现网络、弦图、聚类热图、文字向量图", ""),
            ("⑤ 矛盾候选", f"方向相反 {e['方向相反候选']} 条（核对后均 ❌）；数值相差大 {e['数值相差大候选']} 条", ""),
            ("⑥ 打分模型与归一化", "尚未做：等你看完①–⑤再定", "todo")]
    fl = '<span class="arrow">→</span>'.join(f'<div class="step {cls}"><b>{h}</b><br>{t}</div>' for h, t, cls in flow)
    kpi = lambda k, v: f'<div class="kpi"><b>{v}</b>{k}</div>'
    body = f"""
<div class="warn"><b>先看这一条：</b>这里的结果<b>都还没有归一化到标准条件</b>（归一化是第⑥步打分模型的工作）。
“方向相反”比的是同一篇里两个配方的比值，篇内条件相同，不受影响；“数值相差大”是跨篇比原始数值，现在只是“配方相同、已知条件相近”时的初筛，正式版本要等归一化之后重做。图 3 里的性能“原值”也不能直接横向比较。</div>
<h2>流程</h2><div class="flow">{fl}</div>
<h2>关键数字</h2>
{kpi("条表述", c['表述条数'])}{kpi("篇论文", c['论文数'])}{kpi("个配方", c['配方数'])}{kpi("条有物性的表述", c['有物性的表述'])}
{kpi("条可算元素比例", c['元素比例可算的表述'])}{kpi("个性能测试", b['性能测试数'])}{kpi("条方向相反候选", e['方向相反候选'])}{kpi("条数值相差大候选", e['数值相差大候选'])}
<h2>四类性能各有多少条表述</h2><p>{'；'.join(f'{k} {v} 条' for k, v in c['按性能类别'].items())}。</p>
<h2>一条表述长什么样</h2><div class="note mono">{html.escape(sts[0]['表述文字'])}</div>
<p>一个性能数值生成一条表述，由四部分组成：<b>配方</b>（原文用量＋配方级元素比例）、<b>物性</b>（只用同一篇对这个配方报告的值，没报告写“未报告”）、
<b>测试条件</b>、<b>性能</b>。机制不写进表述文字，只在后台保留编号（表述表里点开一行可以看到）。</p>
<h2>这次试跑的主要发现</h2>
<ul>
<li>30 篇里<b>同一种改动在两篇以上出现的只有 4 种</b>（DMTS 增加、LiNO₃ 增加、LiNO₃ 增加且 LiTFSI 减少、换成标准醚电解液），各篇方向都一致，所以没有真正的“方向相反”。放宽到“主改动部分相同”出了 2 条，读原文后都不是同一种改动（判 ❌）。要找到方向相反的矛盾，需要更多论文。</li>
<li>标准醚电解液（LiTFSI＋DOL/DME＋LiNO₃）在 16 篇里出现。配方和已知条件都相近的跨篇对有 {e['配方与条件都配上的跨篇对（不论差距）']} 对，首圈容量最多差 1.39 倍（约 900 到 1250 mAh g⁻¹），没有到 1.5 倍阈值。这个离散程度就是归一化要处理的“同一电解液在不同实验室的差别”。</li>
<li>条件缺失多：E/S 有值的表述 {c['条件有值的表述数']['E/S']}/{c['表述条数']}，锂厚 {c['条件有值的表述数']['锂厚']}，N/P 只有 {c['条件有值的表述数']['N/P']}。</li>
<li>正极硫含量：脚本正则解析与读原文核定只有 29/55 一致，全量时不能直接用正则结果。</li>
<li>同一个数值被提取进同篇两个测试的情况有 19 组（如 P034 的 2485 mAh g⁻¹），已标“疑似重复组”，统计时每组只计一次。</li>
</ul>
<h2>文件</h2><p class="mono">output/表述与矛盾试跑_F版30篇_2026-11-04/：表述表.xlsx、别名表与复核表.xlsx、条件表.xlsx、矛盾候选复核表.xlsx，以及同名 JSON。脚本 scripts/step13a–13e、step13s。</p>
"""
    page("index.html", "总览", body)

    # ---------------- 表述表 ----------------
    cols = ["编号", "论文", "测试", "配方", "对照", "性能类别", "标准指标", "数值", "单位", "阶段", "圈数", "E/S", "硫载量", "正极含硫", "倍率", "温度", "电池形式", "电池类型", "物性项数", "归类"]
    cv = lambda s, f: s["条件"][f]["值"] if s["条件"][f]["值"] is not None else ""
    rows = [[s["表述编号"], s["论文"], s["测试"], s["配方"], "是" if s["是否对照"] else "", s["性能类别"], s["标准指标"], s["数值原文"], s["单位"],
             s["阶段"], s["圈数"] or "", cv(s, "ES"), cv(s, "sulfur_loading"), cv(s, "S_content"), cv(s, "rate"), cv(s, "temperature"),
             cv(s, "cell_format"), s["电池类型"], len(s["物性"]), s["归类状态"]] for s in sts]
    details = [f"<b>表述：</b>{s['表述文字']}\n\n<b>原文句子：</b>\n{s['原句']}\n\n<b>后台链接</b>（不进表述）：机制 {', '.join(s['机制链接']) or '无'}；支撑测量 {', '.join(s['支撑测量链接']) or '无'}"
               + (f"\n<b>疑似重复组：</b>{s['疑似重复组']}" if s.get("疑似重复组") else "")
               + (f"\n<b>归类说明：</b>{s['归类原因']}" if s["归类原因"] else "") for s in sts]
    body = f"""<div class="note">共 {len(sts)} 条。可按论文、性能类别、标准指标筛选，点表头排序，点一行展开完整表述、原文句子和后台机制编号。条件为空表示原文没写或算不出（Excel 里写了原因）。数值是原文值，未归一化。</div>
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
             "四种颜色的点分别是组分、物性、条件档（如“E/S≤5（贫液）”）、性能档（同一指标同一阶段里三等分，好/中/差）。线 = 两者同时出现在多少条表述里（只画 ≥10 条的）。性能档是原值三等分，未归一化，只看分布，不比优劣。"),
            ("图2a_配方物性弦图.png", "图2a 弦图：配方 × 物性",
             "左边一圈是组分化学类别，右边是物性类别；弦表示“含这类组分的配方报告了这项物性”（按配方计）。能看出哪些体系的物性测得多、哪些是空白。"),
            ("图2b_四部分弦图.png", "图2b 弦图：配方 × 物性 × 测试条件 × 性能",
             "四组弧：组分类别（蓝）、物性（橙）、测试条件（绿，只选贫液、高载量、软包、薄锂等关键档）、性能类别（红）。弦宽 = 两者同时出现的表述数（只画 ≥15 条的）。"),
            ("图3_四部分聚类热图.html", "图3 聚类热图：配方 × 物性 × 条件 × 性能",
             "每行一个配方（共 52 个，需能算元素比例且有性能值），列分四块，用竖线隔开。颜色是标准化后的值（红高蓝低），灰 = 未报告。行顺序按层次聚类排列。注意：性能“原值”未归一化，跨篇不能直接比；“篇内相对对照”两列是同篇比值，可以比。"),
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

    # ---------------- 矛盾候选 ----------------
    dirc = [x for x in cands if x["类型"] == "方向相反"]
    blocks = []
    for x in dirc:
        ex = lambda lst: "<br>".join(html.escape(f"{p['测试']}：{p['A']}（{p['A值']}） vs {p['B']}（{p['B值']}），{p['标准指标']}，{p['取值点']} → {p['方向']}") for p in lst)
        blocks.append(f"""<h3>{x['候选编号']}　<span class="tag">{x['匹配']}</span> {html.escape(x['签名'])}｜{x['性能类别']}｜判定 {x['判定'] or '未核对'}</h3>
<table><tr><th>论文甲（变好）{x['论文甲']}</th><th>论文乙（变坏）{x['论文乙']}</th></tr>
<tr><td>{ex(x['甲例'])}</td><td>{ex(x['乙例'])}</td></tr></table>
<p><b>核对：</b>{html.escape(x['核对说明'])}<br><b>依据句子：</b>{'、'.join(x['依据句子'])}<br><b>可能原因：</b>{html.escape(x['可能原因'])}<br><b>机制线索：</b>{html.escape(x['机制线索'])}</p>""")
    matched = []
    try:
        import openpyxl
        wb = openpyxl.load_workbook(OUT / "矛盾候选复核表.xlsx", read_only=True)
        ws = wb["配上的跨篇对（未到阈值）"]
        matched = [list(r) for r in ws.iter_rows(min_row=2, values_only=True)]
    except Exception:
        pass
    body = f"""<div class="note"><b>两种候选</b>（方案 §8.7）：① 方向相反 = 两篇做了同一种改动，同一类性能一篇变好、一篇变坏；② 数值相差大 = 不同论文、配方和条件都相近，性能相差 ≥1.5 倍（CE 损失比 ≥2 倍）。
判定：✅ 原文支持、条件已对齐，值得解释；🔶 数值无误但有未对齐的条件或定义差异；⚠️ 提取或归类有问题；❌ 不构成矛盾。</div>
<h2>① 方向相反：{len(dirc)} 条</h2>
<p>篇内有方向的配对 {e['篇内有方向的配对']} 对（数值 {e['配对依据'].get('数值', 0)}、作者定性 {e['配对依据'].get('定性', 0)}）。改动用“主改动签名”表示（+X 加入、−X 去掉、X↑/X↓ 用量增减；加共溶剂时 DME、DOL 比例的被动变化不算）。
严格按主改动相同配对：0 条（同一种改动在两篇以上出现的只有 4 种，方向都一致）。放宽到主改动部分相同：</p>
{''.join(blocks)}
<h2>② 数值相差大：{e['数值相差大候选']} 条</h2>
<div class="warn">这一种是跨篇比原始数值，<b>需要先归一化到标准条件才是正式结果</b>。现在只是“配方相同、已知条件相近”时的初筛：E/S、载量相差 ≤1.5 倍，含硫相差 ≤10 个百分点，倍率 ≤2 倍，温度 ≤10 °C，电池形式相同；条件没报告的控制不住。
第⑥步做完后，改成“归一化后仍差得远”重新找。</div>
<p>配方和条件都配上的跨篇对共 {e['配方与条件都配上的跨篇对（不论差距）']} 对，全是标准醚电解液的首圈硫比容量，最大差 1.39 倍，没到阈值：</p>
<div id="tm"></div>"""
    cm = ["标准指标", "阶段", "倍数", "甲", "乙", "配方差异", "条件说明"]
    page("矛盾候选.html", "矛盾候选", body, f"makeTable('tm',{j(cm)},{j(matched)},{{}});")
    print("网站页面：", [p for p, _ in PAGES])


if __name__ == "__main__":
    main()
