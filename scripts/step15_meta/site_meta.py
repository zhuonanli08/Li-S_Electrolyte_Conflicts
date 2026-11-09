"""结果网站“05 · Meta 分析与矛盾归因”标签页（11-06 用户要求：结论、方法、表格等文字用中文，图用英文；文字结论用表格和文字地图，不另画图）。
11-08 起 meta_panel 改为新版（用户定：主线只要“矛盾是什么、怎么找到的、原因”，只放漏斗图 fig00_funnel，其余文字；原因用 step20 的跨论文机制证据）；
11-06 版改名 meta_panel_v1 留作历史，下面关于数据来源的说明指的是 v1。
由 scripts/step13s_site.py 调用。数据：
  meta v3（F_pooled.py，全部测量、用户的分子结构描述符、同测试/跨测试/篇间分解、按数据去重叠）→ output/meta_v3_全部测量_313篇_2026-11-06/；
  矛盾单元与读原文判定、标准醚跨论文离散、预测记分卡（D_site.py compute）→ output/meta网站_313篇_2026-11-06/网站数据.json；
  可信度检验（E_credibility.py）→ output/可信度检验_313篇_2026-11-06/汇总.json。图由 G_meta_figs.py 先画到网站 图/。
"""
import html
import json
import math
from pathlib import Path
from collections import Counter

import numpy as np

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
DATA = ROOT / "output" / "meta网站_313篇_2026-11-06" / "网站数据.json"
V3F = ROOT / "output" / "meta_v3_全部测量_313篇_2026-11-06"
CREDF = ROOT / "output" / "可信度检验_313篇_2026-11-06" / "汇总.json"
CLASSES = ["首圈容量", "每圈衰减率", "全电池CE", "LiCu_CE"]
CN = {"首圈容量": "首圈容量", "每圈衰减率": "每圈衰减率", "全电池CE": "全电池 CE", "LiCu_CE": "Li‖Cu CE"}
DCN = {"eo": "非氟醚氧", "eo_a": "α 氟化醚氧", "eo_b": "β 氟化醚氧", "carbonate": "碳酸酯", "carbonyl": "羰基", "sulfone": "砜/亚砜", "nitrile": "腈",
       "amide": "酰胺/脲", "thio": "硫醚/多硫 S", "fat": "溶剂 F 原子数", "ring": "溶剂环数", "rotb": "可旋转键数", "tpsa": "TPSA", "mw": "溶剂分子量",
       "ffrac": "含氟溶剂比例", "lnsites": "每个 Li⁺ 的配位位点（对数）", "dil": "稀释剂摩尔比例", "li": "Li⁺ 总浓度", "salt": "主盐浓度",
       "anF": "阴离子 F（每升）", "anSO2": "阴离子磺酰（每升）", "lino3": "LiNO₃ 浓度"}
REASON_CN = {"Test conditions differ": "测试条件或取值点不同", "Another change mixed in": "混了别的改动", "Reference unusually weak or strong": "参照很弱或很强",
             "No defined direction, or sides swapped": "改动没有统一方向，或实验/对照标反", "Data or grouping error": "数据或归组错误",
             "Metric artefact or within noise": "指标被放大，或差别在噪声内", "Genuine effect": "真实效应"}
REASON = [("Test conditions differ", ("条件不同", "取值点不同")), ("Another change mixed in", ("混了别的改动",)),
          ("Reference unusually weak or strong", ("参照很弱或很强",)), ("No defined direction, or sides swapped", ("改动方向不同", "实验/对照方向标反")),
          ("Data or grouping error", ("归组或提取问题",)), ("Metric artefact or within noise", ("指标放大", "指标问题", "差异小于噪声")),
          ("Genuine effect", ("真实大效应", "真实机制差异", "符合描述符趋势"))]
REASON_EXPLAIN = {"Test conditions differ": "两边不在同一条件下测（低温、极贫液、取值的圈数不同），倍数被条件放大或反转",
                  "Another change mixed in": "除了这个改动，同时还换了正极、隔膜、主盐、LiNO₃ 或面容量",
                  "Reference unusually weak or strong": "参照本身特别差（不含硝酸盐、单一弱溶剂化溶剂、已短路）或特别好，倍数随之放大",
                  "No defined direction, or sides swapped": "同一组里有人加浓、有人稀释，本来就没有统一方向；或实验与对照标反",
                  "Data or grouping error": "提取或归组出错：用量为 0 的组分、溶剂记错、范围外的电池混进来",
                  "Metric artefact or within noise": "CE 接近 100% 时损失比被放大，或圈数太少，或差别小于测量噪声",
                  "Genuine effect": "数值属实：要么是真实的大效应，要么是化学机制本身不同（P108 非晶 S/C 在碳酸酯中更稳，P231 溶剂化离子液体）"}
PREFER = ["P232", "P333", "P115", "P633", "P088", "P295", "P321", "P012", "P121", "P386", "P108", "P231"]
VERD = {"✅": "原文证实", "🔶": "线索（部分可解释）", "⚠️": "数据或归组问题", "❌": "不成立"}
TYPE_CN = {"方向相反": "方向相反", "幅度异常": "幅度差 3 倍以上"}


def e(x):
    return html.escape(str(x))


def reason_of(cat):
    first = (cat or "").split("；")[0]
    return next((en for en, keys in REASON if any(k in first for k in keys)), "Genuine effect")


def f(x, d=2):
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"


def tbl(head, rows, cls=""):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<div class='table-wrap {cls}'><table><tr>{h}</tr>{b}</table></div>"


def leak_note() -> str:
    """插在 04 · Modelling 页开头的更正说明。"""
    return ('<div class="callout warn"><b>更正（11-06）</b>：本页每圈衰减率的结果（考试集 R² 0.32）含有泄漏——圈数进了模型，而跨论文看圈数本身就跟结果走'
            '（好电池测得久；报告的总损失不管测多少圈都在 9%–59%）。去掉圈数后开发集最好 0.23，按原规则重考（考试集第二次使用）R² <b>0.14（−0.24～0.35）</b>。'
            '另外全电池 CE 的选定配置取自一条过期记录。记分卡见 <a href="#meta" onclick="$(\'nav button[data-panel=meta]\').click();return false">05 页</a>。</div>')


EVF = ROOT / "output" / "机制证据_313篇_2026-11-08" / "机制证据.json"
JUDF = ROOT / "output" / "张力判定_313篇_2026-11-07"
# 11-08 用户定：主线只要“矛盾是什么、怎么找到的、产生矛盾的原因”；meta 部分只放漏斗图，其余用文字。下面三条无定论问题的标题与“还不知道的”由 Claude 写
QUESTIONS = [
    ("T1", "问题 1 · 稀释剂该不该分解？——加氟不一定越多越好",
     "P381 作者：氟化降低 LUMO，TTE 还原不稳定，分解出的有机副产物抵消了 LiF 的好处（有表征）。P371 作者推测：部分氟化的 F3DEE 反应活性高。"
     "另有 P263（氟苯）、P350（F4EO2）用低氟组分替换 TTE 也不差，读原文后记为待定。",
     "富 LiF 的 SEI 里，LiF 主要来自稀释剂分解还是阴离子分解？稀释剂分解对锂负极是利是弊？这和氟化的程度、位置有什么关系"
     "（P371 里 F3DEE 最差、F4DEE 最好）？"),
    ("T3", "问题 2 · LiNO₃ 加多少最好？",
     "P111 作者自己说这与“LiNO₃ 持续被消耗、越多寿命越长”的通常预期相反；作者认为 0.5 M 是保留 GO 结构与不过度消耗活性硫之间的平衡，"
     "但没有解释 1.0 M 为什么变差。体系是离子液体＋GO 正极，条件特殊。另外，“LiNO₃ 越多衰减越慢”这条多数规律去掉特殊组分后已没有共识。",
     "最佳用量由什么决定——放电截止电压、电解液用量、循环圈数？P111 作者推测与充电倍率有关，未验证。"),
    ("T4", "问题 3 · 高盐浓度和 LiNO₃ 是替代还是互补？",
     "P112 作者推测两者分工互补：LiNO₃ 负责在两极成膜，高盐抑制多硫化物溶解、从而少消耗 LiNO₃（作者推测）。",
     "313 篇里没有一篇把盐浓度和 LiNO₃ 交叉测过，只有 P112。两者对 CE 的作用是重叠（有了一个就不需要另一个），还是对寿命各有贡献？"
     "需要盐浓度 × LiNO₃ 用量的交叉实验，同时测 CE 和循环寿命。"),
]


def meta_panel():
    # 11-09 用户：漏斗图说明分三段（是什么 / 怎么读 / 说明了什么）
    """05 页（11-08 版）：漏斗图＋三条无定论问题（矛盾是什么、怎么找到的、两方原因、还不知道的）＋已有解释的反例。"""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from fig00_funnel import numbers
    n = numbers()
    ev = json.loads(EVF.read_text(encoding="utf-8"))

    def plist(v):
        return "、".join(v) if v else "—"

    cards = []
    for t, title, author, unknown in QUESTIONS:
        x = ev[t]
        side = {k[0]: v for k, v in x["各立场论文"].items()}
        rows = [["矛盾是什么", e(x["矛盾是什么"])],
                ["怎么找到的", e(x["怎么找到的"])],
                ["反例论文的作者怎么说", e(author)],
                [f"其他论文 · 一方（{len(side['A'])} 篇）", f"{e(x['立场']['A'])}<br><span class='note'>{plist(side['A'])}</span>"],
                [f"其他论文 · 另一方（{len(side['B'])} 篇）", f"{e(x['立场']['B'])}<br><span class='note'>{plist(side['B'])}</span>"],
                ["还不知道的", f"<b>{e(unknown)}</b>"]]
        b = "".join(f"<tr><td style='white-space:nowrap;width:13em'><b>{k}</b></td><td>{v}</td></tr>" for k, v in rows)
        cards.append(f"<div class='card' style='grid-column:1/-1'><h3 style='margin-top:0'>{e(title)}</h3>"
                     f"<div class='table-wrap'><table>{b}</table></div></div>")
    t2 = ev["T2"]
    k2 = {k[0]: v for k, v in t2["各立场论文"].items()}
    explained = tbl(["读原文后", "条数", "意思", "例子"], [
        ["比较不对等", n["unequal"], "这对比较同时还改了别的（盐浓度、LiNO₃、成膜溶剂等），或参照特别弱、特别强",
         "P112：4 M 醚对 1 M 碳酸酯，CE 95.3% 对 91.6%；盐浓度也变了，同为 1 M 时醚反而更差（80.0%）"],
        ["数据问题", n["data"], "提取或归组出错，或差别在测量误差内", "P386：CE 99.71% 对 99.68%"],
        ["已知条件", n["known"], "看起来和共识相反，但文献已经解释清楚",
         f"P108：非晶 S/C 正极里碳酸酯比醚好（20 圈 94.8% 对 72.7%）——{len(k2['A'])} 篇论文说碳酸酯能不能用取决于正极"
         f"（限域/短链硫、SPAN 走固-固转化）：{plist(k2['A'])}"],
        ["待定", n["pending"], "读原文后还说不清", "P295：LiFSI 超过 1 M 后 CE 下降，但只差 0.5 个百分点"],
        ["真张力候选", n["real"], "读原文后仍和共识相反，且有机制上的理由", "见上面问题 1、2"]])
    steps = tbl(["步骤", "做了什么"], [
        ["① 两两比较", f"同一篇论文里，两个配方在同一个测试里比一次，记下结构描述符和性能是变高、变低还是相近（性能相差 < 5%、描述符 < 1% 算相近）。共 {n['pairs']:,} 对，同测试 {n['same']} 对。"],
        ["② 计票", f"每对比较给每个变了的描述符投一票；≥ 5 篇、且多数占比 ≥ 2/3 才算共识。{n['rules']} 条“描述符 → 性能”规律里 {n['consensus']} 条有共识。"],
        ["③ 找反例和交叉设计", f"和共识相反的比较叫反例（{n['cex']} 个，{n['cex_papers']} 篇）；同一篇里两样东西交叉着变的叫交叉设计，可以看协同作用（只有 {', '.join(n['cross'])}）。"],
        ["④ 读原文", "逐条读反例两边的原句、对照说明和作者机制，分成比较不对等、数据问题、已知条件、待定、真张力候选。"],
        ["⑤ 跨论文找原因", "在 313 篇已提取的 7477 条机制说法里，按关键词找出与每条矛盾有关的，分成两方，列出各方论文。"]])
    sec = f"""<section id="meta" class="panel" hidden><div class="section-head"><h2>Meta 分析：找到了哪些矛盾、为什么</h2><span class="note">{n['papers']}/535 篇 ·
初步，AI 辅助，用户尚未逐项人工确认</span></div>
<div class="callout"><b>一句话</b>：从 {n['papers']} 篇论文的 {n['pairs']:,} 对比较里数票找共识，再找和共识相反的反例、读原文排除比较方式造成的，
最后剩下 <b>{n['questions']} 个文献里没有定论的问题</b>：稀释剂该不该分解、LiNO₃ 加多少最好、高盐和 LiNO₃ 是替代还是互补。</div>
<div class="card" style="margin-top:18px"><h3 style="margin-top:0">工作流漏斗图</h3>
<p><b>是什么</b>　从 {n['papers']} 篇提取结果到 {n['questions']} 个无定论问题的筛选流程，每一层是一步。</p>
<p><b>怎么读</b>　从上往下读：每层写这一步剩下多少，计数单位逐层不同（论文、比较、规律、反例），条的宽度只是示意、不按比例。右侧上方 = 读原文后有解释、被排除的反例分几类；右侧下方 = 问题 3 来自同篇交叉设计（{', '.join(n['cross'])}），不是来自反例。</p>
<p><b>说明了什么</b>　自动计票把 {n['pairs']:,} 对比较压缩成 {n['cex']} 个需要人读的反例；其中 {n['unequal'] + n['data'] + n['known']} 个读原文后有解释（{n['unequal']} 个是比较不对等：同时改了别的东西，或参照特别弱、特别强），说明文献里大多数“看起来矛盾”是比较方式造成的；剩下 {n['real'] + n['pending']} 个解释不了（{n['real']} 个真张力候选、{n['pending']} 个待定），由此提炼出 {n['questions']} 个无定论问题。读原文与归类为 AI 辅助，尚未逐项人工确认。</p>
<a href="图/fig0_funnel.png" target="_blank"><img class="fig" src="图/fig0_funnel.png" alt="工作流漏斗图" style="width:100%"></a></div>
<h3 style="margin-top:26px">矛盾是怎么找到的</h3>{steps}
<h3 style="margin-top:26px">找到的矛盾和原因</h3><div class="grid2">{''.join(cards)}</div>
<h3 style="margin-top:26px">其余反例：读原文后已有解释</h3>{explained}
<div class="callout warn" style="margin-top:18px"><b>meta 分析能做到哪一步</b>：“矛盾是什么、怎么找到的”靠计票（最简单的一种 meta 分析）和读原文；
“为什么”只能做一半——11-06 用调节因素检验（换了什么条件结论会反过来）试过 126 次，经多重比较校正后没有一个成立：每个问题只有几篇论文、条件又各不相同。
所以上面的原因是作者的解释和其他论文的说法，还没有被验证；验证留给后面的实验或计算。</div>
<div class="callout">脚本：<span class="mono">scripts/step16–20</span>（两两比较、计票、读原文判定、协同作用、跨论文机制证据）、<span class="mono">scripts/fig00_funnel.py</span>。
原文句子不在公开网页上展示。</div>
</section>"""
    return sec, ""


def meta_panel_v1():
    """11-06 版 05 页（meta v3、矛盾归因、记分卡），11-08 起不再使用，留作历史。"""
    d = json.loads(DATA.read_text(encoding="utf-8"))
    v3 = json.loads((V3F / "汇总.json").read_text(encoding="utf-8"))
    st = json.loads((V3F / "网站图统计.json").read_text(encoding="utf-8"))
    cr = json.loads(CREDF.read_text(encoding="utf-8"))
    S, J = v3["单描述符"], v3["去重叠联合"]

    def js(cls, k, lev="同测试"):  # 联合模型某代表的结果
        return J[cls]["结果"][k][lev]

    def ss(cls, k, lev="同测试"):  # 单描述符结果
        return S[cls][k][lev]

    def x(e_, ci=True):
        return f"×{e_['倍数_每1SD']:.2f}" + (f"（{e_['区间'][0]:.2f}–{e_['区间'][1]:.2f}）" if ci else "")

    def jn(cls):
        return f"{J[cls]['测量']} 个测量 / {J[cls]['论文']} 篇"

    flow = st["数据流"]
    sd = {c: float(np.std([y["相对中位数_ln"] for y in d["实验室差异"][c]["标准醚各篇"]], ddof=1)) for c in CLASSES}
    lo_c, hi_c = min(sd, key=sd.get), max(sd, key=sd.get)
    verd = Counter(s.get("判断") for c in S for s in S[c].values() if s.get("状态") == "已估计")
    nsig = sum(v for k, v in verd.items() if k and k.startswith("同测试显著") or k == "同测试与篇间同向且都显著")
    U = d["矛盾单元"]
    cats = Counter(reason_of((u.get("判定") or {}).get("归类")) for u in U.values())
    kim = cr["Kim外部对照"]["同测试"]; kim_f = {r["特征"]: r for r in cr["Kim外部对照"]["四个特征各自的方向"]}
    comp = {r["中文"]: r for r in cr["报告完整度"]["主层"]["字段"]}
    vif_max = max(v for c in CLASSES for v in (J[c]["VIF_同测试"] or {}).values())

    # ---------- 结论地图（文字树） ----------
    tree = [
        ("Li‖Cu CE", [
            ("溶剂化越弱（每个 Li⁺ 的配位位点越少），Li‖Cu CE 越高", f"联合模型同测试 {x(js('LiCu_CE', 'lnsites'))}/每 1 SD，{jn('LiCu_CE')}",
             "Kim 2023：溶剂含氧越低 CE 越高；Chu 2019：强溶剂化伤锂负极"),
            ("LiNO₃ 越多，Li‖Cu CE 越高", f"联合模型同测试 {x(js('LiCu_CE', 'lino3'))}；同测试里改过 LiNO₃ 的只有 {J['LiCu_CE']['同测试有变化的论文']['lino3']} 篇",
             "Aurbach 2009：LiNO₃ 参与锂负极成膜、抑制穿梭"),
            ("含氟溶剂、稀释剂、盐浓度单独看都提高 Li‖Cu CE，但和配位放在一起后作用消失——是同一个信号",
             f"单独：含氟溶剂比例 {x(ss('LiCu_CE', 'ffrac'), False)}、主盐浓度 {x(ss('LiCu_CE', 'salt'), False)}；联合：{x(js('LiCu_CE', 'ffrac'), False)}、{x(js('LiCu_CE', 'salt'), False)}（不显著）",
             "Qian 2015（高浓）、Yu 2020（氟化醚）：方向一致")]),
        ("全电池 CE", [
            ("溶剂化越弱，全电池 CE 越高", f"联合模型同测试 {x(js('全电池CE', 'lnsites'))}，{jn('全电池CE')}", "与 Li‖Cu 同向"),
            ("氟化/稀释单独看提高全电池 CE", f"稀释剂比例 {x(ss('全电池CE', 'dil'), False)}、溶剂 F 原子数 {x(ss('全电池CE', 'fat'), False)}（同测试变化的论文少，未能放进联合模型）", "—")]),
        ("每圈衰减率", [
            ("溶剂化越弱，衰减越慢", f"联合模型同测试 {x(js('每圈衰减率', 'lnsites'))}，{jn('每圈衰减率')}；篇间反向 {x(js('每圈衰减率', 'lnsites', '篇间'), False)}", "—"),
            ("圈数不作输入（圈数跟结果走，会泄漏）", "见 04 页更正", "—")]),
        ("首圈容量", [
            ("主盐浓度越高，首圈容量越低", f"联合模型同测试 {x(js('首圈容量', 'salt'))}，{jn('首圈容量')}；同测试里改过盐浓度的 {J['首圈容量']['同测试有变化的论文']['salt']} 篇", "—"),
            ("碳酸酯越多，容量越低", f"同测试 {x(ss('首圈容量', 'carbonate'), False)}、篇间 {x(ss('首圈容量', 'carbonate', '篇间'), False)}，但同测试里只有 {S['首圈容量']['carbonate']['同测试有变化的论文']} 篇",
             "Yim 2013：多硫化物与碳酸酯亲核反应；例外 P108 与 Xin 2012（限域小分子硫）一致"),
            ("更正：之前“配位位点越多容量越高”在室温同测试里不成立", f"同测试 {x(ss('首圈容量', 'lnsites'), False)}（q {S['首圈容量']['lnsites']['同测试']['q']:.2f}）；之前的 ×1.19 可能来自低温测试（P232 等）和跨测试比较",
             "Chu 2019 的“强溶剂化提高硫利用率”在本数据的室温同测试里没有得到支持")]),
        ("跨文献", [
            ("同一电解液在不同实验室之间的差别，比换电解液的差别还大", f"标准醚各篇平均值离散 ×/÷{math.exp(sd[lo_c]):.1f}（{CN[lo_c]}）到 ×/÷{math.exp(sd[hi_c]):.1f}（{CN[hi_c]}）",
             "Bird 2024、Yari 2025：同条件下结果差异大、报告不全"),
            ("所以篇间部分只作旁证", f"同测试显著的 {nsig} 格里，篇间同向且也显著 {verd['同测试与篇间同向且都显著']} 格、同向不显著 {verd['同测试显著、篇间同向']} 格、反向 {verd['同测试显著、篇间反向']} 格", "—"),
            ("文献里的“结论相反”多数来自比较方式，真正的机制矛盾很少", f"{len(U)} 组读原文：比较方式 {cats['Test conditions differ'] + cats['Another change mixed in'] + cats['Reference unusually weak or strong'] + cats['No defined direction, or sides swapped']} 组、数据错误 {cats['Data or grouping error']} 组、指标 {cats['Metric artefact or within noise']} 组、真实效应 {cats['Genuine effect']} 组",
             "—")])]
    tree_html = "".join(
        f"<details open style='border:0;margin:6px 0'><summary style='font-size:15px'>{e(k)}</summary><div style='margin-left:18px'>"
        + "".join(f"<details style='margin:4px 0'><summary style='font-weight:500;color:var(--ink)'>{e(c)}</summary>"
                  f"<div class='detail' style='margin-left:16px'><b>证据</b>：{e(ev)}<br><b>前人</b>：{e(pr)}</div></details>" for c, ev, pr in items)
        + "</div></details>" for k, items in tree)

    # ---------- 主要结论表 ----------
    concl = tbl(["结论", "证据（同测试，每 1 SD 的倍数，>1 = 变好）", "去重叠后", "前人结论", "是否一致"], [
        ["溶剂化越弱（每个 Li⁺ 配位位点越少）→ Li‖Cu CE、全电池 CE 越高，衰减越慢",
         f"Li‖Cu {x(js('LiCu_CE', 'lnsites'), False)}、全电池 CE {x(js('全电池CE', 'lnsites'), False)}、衰减 {x(js('每圈衰减率', 'lnsites'), False)}",
         "联合模型中仍显著", "Kim 2023（溶剂含氧低 → CE 高）；Chu 2019（强溶剂化伤锂负极）", "一致"],
        ["LiNO₃ → Li‖Cu CE 高", x(js('LiCu_CE', 'lino3')), "联合模型中仍显著", "Aurbach 2009", "一致（同测试只有 6 篇）"],
        ["含氟溶剂 / 稀释剂 / 盐浓度 → Li‖Cu CE 高", f"单独显著（{x(ss('LiCu_CE', 'ffrac'), False)}、{x(ss('LiCu_CE', 'dil'), False)}、{x(ss('LiCu_CE', 'salt'), False)}）",
         "与配位一起估后不显著：同一信号", "Qian 2015；Yu 2020", "方向一致，作用不独立"],
        ["主盐浓度高 → 首圈容量低", x(js('首圈容量', 'salt')), "联合模型中仍显著", "—", "—"],
        ["碳酸酯 → 首圈容量低", f"同测试 {x(ss('首圈容量', 'carbonate'), False)}、篇间 {x(ss('首圈容量', 'carbonate', '篇间'), False)}", "同测试仅 3 篇", "Yim 2013；例外 P108 与 Xin 2012 一致", "一致，篇数少"],
        ["配位位点多 → 首圈容量高（之前的结论）", f"室温同测试 {x(ss('首圈容量', 'lnsites'), False)}，不显著", "不成立", "Chu 2019（强溶剂化提高硫利用率）", "本数据未支持"],
        ["同一电解液跨实验室的差别 ≥ 换电解液的差别", f"×/÷{math.exp(sd[lo_c]):.1f}–×/÷{math.exp(sd[hi_c]):.1f}", "—", "Bird 2024；Yari 2025", "一致"]])

    # ---------- 方法表 ----------
    method = tbl(["步骤", "做法", "为什么这样做", "文献依据"], [
        ["1 数据", "313 篇 → 第 0 步 v2 测量表；四类性能分开分析。一个测量 = 一个配方在一个测试里的一个值；同一颗电池只计一次", "避免重复计数", "—"],
        ["2 室温", f"只用 15–35 °C 的测量（没写温度的按 25 °C），剔除 {flow['Not near room temperature']} 个", "低温会把差别放大几倍（P232、P321）", "Yari 等 2025 剔除非室温电池"],
        ["3 描述符", "用户的 22 个分子结构描述符：溶剂官能团（按溶剂摩尔分数加权）、溶剂化状态、盐与添加剂；Kim 的 6 个元素比例不进主分析，只作外部对照", "配方一律用分子结构表示", "Kim 等 2023（元素组成作特征）；基团贡献思路（Fredenslund 等 1975，UNIFAC）"],
        ["4 去重叠", f"跨配方 Spearman |ρ| ≥ 0.5 的描述符聚为同一条轴（平均连接），共 6 条；每条轴取一个代表放进同一个模型，VIF ≤ {vif_max:.1f}", "同一信号不重复计数（旧的 16 个描述符一起估时 VIF 最高 35.6）", "Thompson & Higgins 2002（meta 回归的共线与多重检验）"],
        ["5 效应量", "对数尺度：容量取 ln，衰减取 −ln，CE 取 −ln(100−CE)；写成“描述符变 1 个标准差，性能变几倍”", "不同指标可比，>1 一律表示变好", "Hedges、Gurevitch、Curtis 1999（对数响应比）；Kim 2023（LCE）"],
        ["6 模型", "多层模型：测试条件（E/S、载量、含硫、倍率、温度、软包；Li‖Cu 用电流、面容量、圈数、测试方法，缺的按中位数补）＋ 每个描述符拆成同测试、同篇跨测试、篇间三部分 ＋ 论文随机截距",
         "同测试部分条件完全相同、不受实验室影响，是主证据；篇间部分受实验室差异影响，只作旁证", "Mundlak 1978；Bell & Jones 2015；DerSimonian & Laird 1986（随机效应）；Ligorati 等 2026（电池衰减的 meta 回归）"],
        ["7 多重检验", "每类性能 22 个描述符的同测试 p 值做 BH 校正，q < 0.1 算显著", "控制假发现", "Benjamini & Hochberg 1995"],
        ["8 矛盾归因", f"与汇总方向相反、或差 3 倍以上的 {len(U)} 组，逐条读原句、对比说明与机制，归为 7 类", "分清化学矛盾和比较方式造成的矛盾", "Schmack 等 2019（用文献数据检验化学假设）"],
        ["9 可信度", "用 Kim 模型作外部对照；统计报告完整度；去掉有提取问题的论文重算", "检查与已发表结论是否一致、数据缺口在哪", "Kim 等 2023；Bird 等 2024"]])

    # ---------- 数据流表 ----------
    frows = []
    for c in CLASSES:
        cov = v3["覆盖"][c]
        frows.append([CN[c], f"{cov['测量']} / {cov['论文']}", v3["非室温剔除"].get(c, 0), jn(c), "、".join(DCN[k] for k in J[c]["代表"])])
    flow_tbl = tbl(["性能", "室温测量 / 论文", "剔除的非室温测量", "去重叠联合模型", "联合模型里的代表描述符"], frows)

    # ---------- 图 ----------
    figs = [("图M1_数据流桑基.html", 540, "图 M1 · 数据怎么进入分析",
             f"宽度 = 测量数。{flow['313 papers · main layer']} 个测量里，{flow['Same test, formulation varied']} 个所在的测试换过配方（蓝色，不受实验室差异影响的信息），"
             f"{flow['Same paper, across tests']} 个只能在同一篇的不同测试之间比，{flow['Between papers only']} 个来自只测了一个配方的论文，只能提供篇间信息。"),
            ("图M2_证据网络.html", 880, "图 M2 · 证据网络：描述符轴 → 性能",
             "大节点是按数据聚出的 6 条描述符轴，小节点是轴里的描述符；中间是四类性能。连线 = 去重叠联合模型的同测试效应：蓝色变好、红色变差，越粗作用越大；"
             "虚线 = 单独看显著但和其他轴分不开；橙色虚线 = 不同轴的描述符之间仍有 |ρ| ≥ 0.5 的重叠。悬停看倍数、区间和篇数。"),
            ("图M3_论文与描述符轴网络.html", 920, "图 M3 · 论文 × 描述符轴：文献横向比较",
             f"{st['论文—轴网络']['论文']} 篇论文连到它在同一个测试里改过的轴上。灰线 = 方向与汇总一致（{st['论文—轴网络']['连线'].get('agree', 0)} 条），"
             f"红线 = 与汇总相反（{st['论文—轴网络']['连线'].get('opposite', 0)} 条），浅色 = 这条轴在该性能上没有汇总方向。论文颜色 = 读原文判定的矛盾原因。"),
            ("图M4_三层效应热图.html", 820, "图 M4 · 每个描述符的两类证据",
             "行 = 22 个描述符（按轴排，★ 为轴的代表），列 = 四类性能 × 同测试 / 篇间。深色加粗 = 显著（同测试 q < 0.1；篇间 p < 0.05），浅色 = 只有方向。"
             "同一条轴里的几行颜色相近，就是重叠；同测试和篇间颜色相反，就是跨文献比较被实验室差异带偏。"),
            ("图M5_矛盾归因桑基.html", 660, "图 M5 · 看似矛盾的结论从哪来",
             f"{len(U)} 组看似矛盾：性能 → 改动涉及的描述符轴 → 读原文找到的原因 → 判定。宽度 = 组数，悬停看论文编号。"),
            ("图M6_同一电解液跨实验室.html", 960, "图 M6 · 同一电解液跨实验室 vs 换电解液",
             "蓝点：各篇的标准醚（约 1 M LiTFSI、DOL:DME 1:1）相对中位数论文的倍数；橙点：同一测试里换电解液的倍数。蓝色的分布和橙色一样宽甚至更宽。")]
    fc = "".join(f'<div class="card" style="grid-column:1/-1"><div class="card-top"><h3 style="margin:0">{t}</h3><a class="note" href="图/{fn}" target="_blank">新窗口打开 ↗</a></div>'
                 f'<p>{cap}</p><iframe class="fig" data-src="图/{fn}" height="{h}"></iframe></div>' for fn, h, t, cap in figs)

    # ---------- 矛盾结论表 ----------
    by = {}
    for k, u in U.items():
        by.setdefault(reason_of((u.get("判定") or {}).get("归类")), []).append(k)
    crow = []
    for en, _ in REASON:
        ks = by.get(en, [])
        pick = [k for p in PREFER for k in ks if k.endswith("|" + p)][:2] or ks[:2]
        ex = "<br>".join(f"<b>{e(k.split('|')[2])}</b>（{e(CN[k.split('|')[0]])} · {e(k.split('|')[1])}）：{e((U[k].get('判定') or {}).get('原因', ''))}" for k in pick)
        crow.append([REASON_CN[en], len(ks), REASON_EXPLAIN[en], ex])
    contra = tbl(["原因", "组数", "说明", "典型案例（读原文笔记）"], crow)

    # ---------- 前人对照 ----------
    prior = tbl(["前人结论", "出处", "本研究的结果", "是否一致"], [
        ["溶剂含氧越低（弱溶剂化），Li‖Cu CE 越高", "Kim 等 2023, PNAS 120:e2214357120",
         f"配位位点 → Li‖Cu {x(js('LiCu_CE', 'lnsites'), False)}（联合）；Kim 的 4 个特征在篇内比较里方向全部同号，sO ×{kim_f['sO']['倍数_每1SD']:.2f}（q {kim_f['sO']['q']:.3f}）", "一致"],
        ["高盐浓度提高锂沉积 CE（4 M LiFSI–DME 99.1%）", "Qian 等 2015, Nat. Commun. 6:6362", f"主盐浓度 → Li‖Cu 单独 {x(ss('LiCu_CE', 'salt'), False)}；联合后并入配位", "一致（与配位是同一信号）"],
        ["氟化醚溶剂提高锂金属 CE", "Yu 等 2020, Nat. Energy 5:526", f"含氟溶剂比例 → Li‖Cu 单独 {x(ss('LiCu_CE', 'ffrac'), False)}；联合 {x(js('LiCu_CE', 'ffrac'), False)} 不显著", "方向一致，作用不独立"],
        ["强溶剂化提高硫利用率、但伤锂负极", "Chu 等 2019, Nat. Commun. 10:188", f"伤锂负极一侧一致（配位位点多 → Li‖Cu、全电池 CE 差）；提高容量一侧在室温同测试里不成立（{x(ss('首圈容量', 'lnsites'), False)}）", "部分一致"],
        ["多硫化物与碳酸酯亲核反应，碳酸酯不适合常规锂硫", "Yim 等 2013, Electrochim. Acta 107:454", f"碳酸酯 → 首圈容量 同测试 {x(ss('首圈容量', 'carbonate'), False)}、篇间 {x(ss('首圈容量', 'carbonate', '篇间'), False)}", "一致，同测试仅 3 篇"],
        ["限域的小分子硫可在碳酸酯中工作", "Xin 等 2012, JACS 134:18510", "唯一的机制矛盾 P108（非晶 S/C 在碳酸酯中保持率更高）正是这种情况", "一致"],
        ["LiNO₃ 参与锂负极成膜、抑制穿梭", "Aurbach 等 2009, J. Electrochem. Soc. 156:A694", f"LiNO₃ → Li‖Cu {x(js('LiCu_CE', 'lino3'), False)}（联合）", "一致"]])

    # ---------- 可信度检验 ----------
    cred = tbl(["检查", "做法", "结果", "怎么理解"], [
        ["外部对照", "用 Kim 2023 的线性模型预测我们 Li‖Cu 同测试的篇内差",
         f"校准斜率 {kim['校准斜率']:.2f}（{kim['校准斜率区间'][0]:.2f}–{kim['校准斜率区间'][1]:.2f}），{kim['比较']} 个比较 / {kim['论文']} 篇；方向一致率 {kim['符号一致率_论文等权']:.0%}，“新电解液总是更好”基线 {kim['基线_新电解液总是更好_论文等权']:.0%}",
         "方向和幅度与 Kim 一致；但判断“谁更好”不比作者自己的选择强。Kim 的数据有一部分也来自文献，可能重叠"],
        ["描述符重叠", "按数据聚 6 条轴，每轴一个代表一起估", f"旧的 16 个描述符一起估 VIF 最高 35.6；现在 ≤ {vif_max:.1f}", "去重叠后站得住的只剩配位、LiNO₃、盐浓度（容量）"],
        ["同测试 vs 篇间", "每个描述符同时估同测试和篇间效应", f"同测试显著的 {nsig} 格：篇间同向且显著 {verd['同测试与篇间同向且都显著']}、同向不显著 {verd['同测试显著、篇间同向']}、反向 {verd['同测试显著、篇间反向']}",
         "直接拿不同论文的绝对值比，常被实验室差异带偏"],
        ["室温筛选", f"剔除 {flow['Not near room temperature']} 个非室温测量", "容量“配位位点多 → 容量高”不再成立", "之前的结论受低温测试影响，已更正"],
        ["提取问题", "去掉 6 篇有已知提取问题的论文（P012、P099、P321、P230、P264、P536）重算方案 A", "主要结论不变；Li‖Cu 稀释剂与 LiNO₃ 两格从 q = 0.100 降到 0.074", "这 6 处问题不影响主要结论，留到下次重建一起修"],
        ["报告完整度", "统计 221 篇 Li‖S 主层 900 个测试", f"没写的测试：E/S {comp['E/S']['没写_测试']:.0%}、温度 {comp['温度']['没写_测试']:.0%}、锂片厚度 {comp['锂片厚度']['没写_测试']:.0%}、N/P {comp['N/P 比']['没写_测试']:.0%}；正极含硫量 {comp['正极含硫量']['写了没解析出_测试']:.0%} 写了但没解析出",
         "条件缺失按中位数补，主要影响跨测试和篇间部分；同测试部分不受影响"]])

    # ---------- 记分卡 ----------
    sr = []
    for r in d["记分卡"]:
        c = r["类别"]; s_, a, b = r["改动模型"], r["方案A"], r["方案B"]
        ok = lambda v: '<span class="badge">超过基线</span>' if v else '<span class="badge no">未超过</span>'
        a_txt = (f"{'、'.join(DCN.get({'ln_配位位点每Li': 'lnsites', 'ln_Li总浓度': 'li', '溶剂_含氟分子比例': 'ffrac', 'LiNO3_M': 'lino3', '稀释剂摩尔比例': 'dil'}.get(y, ''), y) for y in a['描述符'])}"
                 f"<br>开发 {f(a['开发'][0])} 对 {f(a['开发'][1])} {ok(a['开发通过'])}<br>考试 {f(a['考试'][0])} 对 {f(a['考试'][1])} {ok(a['考试通过'])}" if a["描述符"] else "没有描述符通过筛选")
        b_txt = f"开发 MSE {f(b['开发'][0])} 对 {f(b['开发'][1])} {ok(b['开发通过'])}<br>考试 MSE {f(b['考试'][0])} 对 {f(b['考试'][1])} {ok(b['考试通过'])}"
        sr.append([CN[c], f"开发 {f(s_['开发'])} · 考试 <b>{f(s_['考试'])}</b>（{f(s_['区间'][0])}～{f(s_['区间'][1])}）", a_txt, b_txt])
    score = tbl(["性能", "改动模型（step14，篇内差的 R²）", "方案 A（篇内排序一致率：模型 对 只用条件；0.5 = 随机）", "方案 B（锚点预测 MSE：模型 对 “与锚点相同”）"], sr)

    # ---------- 读原文表 ----------
    cols = ["性能", "改动", "论文", "类型", "本组合并倍数", "本篇倍数", "判定", "主要原因", "读原文笔记", "依据"]
    rows = []
    for k, u in sorted(U.items()):
        c, g, p = k.split("|")
        j = u.get("判定") or {}
        rows.append([CN[c], g, p, TYPE_CN.get(u["类型"], u["类型"]), round(u["本组合并倍数"], 2), round(u["本篇平均倍数"], 2),
                     f"{j.get('判定', '')} {VERD.get(j.get('判定'), '')}", REASON_CN[reason_of(j.get("归类"))], j.get("原因", ""), j.get("依据", "")])

    sec = f"""<section id="meta" class="panel" hidden><div class="section-head"><h2>Meta 分析与矛盾归因</h2><span class="note">313 篇（开发＋考试集）· 第 0 步 v2 · 全部测量一起进多层模型 ·
初步、AI 辅助，用户尚未逐项人工确认</span></div>
<div class="callout"><b>一句话</b>：把 313 篇的全部测量放进同一个模型，只相信“同一个测试里换配方”带来的差别（不受实验室影响），再用分子结构描述符去重叠——
真正独立起作用的是<b>溶剂化强弱（每个 Li⁺ 的配位位点）</b>和 <b>LiNO₃</b>；含氟、稀释、盐浓度与溶剂化是同一个信号；文献里的“矛盾”多数来自比较方式。</div>
<h3 style="margin-top:22px">结论地图（点开逐层看证据和前人结论）</h3><div class="sheet">{tree_html}</div>
<h3 style="margin-top:26px">主要结论</h3>{concl}
<h3 style="margin-top:26px">分析方法</h3>{method}
<h3 style="margin-top:26px">用到的数据</h3>{flow_tbl}
<div class="grid2" style="margin-top:18px">{fc}</div>
<h3 style="margin-top:26px">矛盾结论：看似相反的结果是怎么来的</h3><p class="note">{len(U)} 组读原文后的分类（按第一原因计数）；完整笔记见本页最后的表。</p>{contra}
<h3 style="margin-top:26px">与前人结论对照</h3>{prior}
<h3 style="margin-top:26px">可信度检验</h3>{cred}
<h3 style="margin-top:26px">预测检验记分卡（事先登记、考试集只算一次）</h3><p class="note">开发集分数偏乐观：设置是在开发集上选的。</p>{score}
<div class="callout warn">没有一种方法在开发集和考试集上都超过基线——跨论文预测绝对性能目前做不到，所以本页只讲篇内方向和权衡。</div>
<h3 style="margin-top:26px">{len(U)} 组矛盾候选 · 读原文笔记</h3><p class="note">依据编号：M = 正文句子，S = SI 句子。原文句子不在公开网页上展示。</p><div id="tMetaAttr"></div>
<div class="callout">脚本：<span class="mono">scripts/step15_meta/</span>（common 第 0 步，F_pooled 全部测量模型，G_meta_figs 本页图，C_judgments 读原文判定，E_credibility 可信度检验）。
数据：<span class="mono">output/meta_v3_全部测量_313篇_2026-11-06/</span>、<span class="mono">output/meta网站_313篇_2026-11-06/网站数据.json</span>。</div>
</section>"""
    js = f"table('tMetaAttr',{json.dumps(cols, ensure_ascii=False)},{json.dumps(rows, ensure_ascii=False)},{{selects:[0,1,6,7],placeholder:'搜索论文、改动、原因…',height:600}});"
    return sec, js
