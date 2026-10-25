"""S39 mechanism-sentence review: Claude / GPT / three Qwen settings, sentence level.

Union of every sentence each extractor hung on a mechanism, plus sentences none
of them hung but that should be recorded. Judgments (判定_AI辅助.json) are
AI-assisted and not confirmed by the user; this script only joins them with the
frozen predictions, checks every sentence id against the full text and counts.
Output: output/云端_2026-10-25_千问调试集53篇/S39_机制句复核/S39_机制句复核.xlsx
"""
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

sys.path.insert(0, str(Path(__file__).resolve().parent))
import step10a_qwen_debug53 as q

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

O = q.OUT
DEST = O / 'S39_机制句复核'
EXTRACTORS = {  # name: (frozen prediction, note)
    'Claude': (q.CLAUDE / 'independent_predictions' / 'S39.json', 'Claude 子代理，对话内提取'),
    'GPT': (q.s9.GPT / 'independent_predictions' / 'S39.json', 'GPT 子代理，对话内提取'),
    '千问Max关思考': (O / '设置对比' / 'Max_关思考' / 'S39_程序删一个多余括号_仅供对比.json',
                 '格式 3 轮未过；程序删一个多余括号后仅供对比，未冻结'),
    '千问27B开思考': (O / '设置对比' / '27B_开思考' / 'independent_predictions' / 'S39.json', 'API'),
    '千问27B关思考': (O / 'independent_predictions' / 'S39.json', 'API'),
}
CODES = {
    'A': '应记：本文机制说法（含排除性说法，如“电导率不是原因”）',
    'B': '应记：本文推测（may / likely 等）',
    '续接': '被切断的半句，与下一句同属一句；挂上不算错，不计数',
    'C': '口径待定：引言/背景转述、通用规律（带引文）',
    'E': '口径待定：只讲性质本身或性质来源（分子结构 → 溶剂化/溶解度），不涉及四类过程',
    'D': '不该记：纯数据、表征观察、方法、小标题、计算',
}
EXPECT = {'A': {'本文结论', '本文结论（与他文一致）'}, 'B': {'本文推测'}, 'C': {'转述他文或通用说法'}}
MIXED = {'M0097', 'M0115'}  # half citation, half own conclusion: source label not judged

def main():
    src = {s['id']: s for s in json.loads((O / 'sources' / 'S39.json').read_text(encoding='utf-8'))}
    J = json.loads((DEST / '判定_AI辅助.json').read_text(encoding='utf-8'))
    preds = {k: json.loads(p.read_text(encoding='utf-8')) for k, (p, _) in EXTRACTORS.items()}
    hung, design = {}, {}
    for k, d in preds.items():
        hung[k] = {}
        for m in d['mechanisms']:
            for e in m['evidence_ids']:
                hung[k].setdefault(e, m)
        design[k] = {e for x in d['design_claims'] for e in x['evidence_ids']}
    union = set().union(*[set(h) for h in hung.values()])
    missing = union - set(J)
    assert not missing, f'未判定的句子：{sorted(missing)}'
    assert all(e in src for e in J), '判定里有原文不存在的句子编号'
    rows = sorted(J, key=lambda e: (e[0] != 'M', e))

    def cell(k, e):
        code = J[e]['code']
        if e not in hung[k]:
            if code in ('A', 'B'):
                return '❌漏' + ('（挂在设计主张）' if e in design[k] else '')
            return ''
        st = hung[k][e]['source_type']
        mark = {'A': '✅', 'B': '✅', '续接': '✅', 'C': '🔶', 'E': '🔶', 'D': '❌错提'}[code]
        if code in EXPECT and e not in MIXED and st not in EXPECT[code]:
            mark += f'⚠️标“{st}”'
        return f'{mark} {hung[k][e]["id"]}'

    stats = {}
    need = [e for e in rows if J[e]['code'] in ('A', 'B')]
    need_main = [e for e in need if J[e]['where'] not in ('摘要', '引言末预告', '结论')]  # duplicates of body text
    for k in EXTRACTORS:
        h = hung[k]
        lab = [e for e in h if J[e]['code'] in EXPECT and e not in MIXED]
        stats[k] = {
            '机制条数': len(preds[k]['mechanisms']),
            '挂的原句': len(h),
            '应记句命中': sum(e in h for e in need),
            '应记句总数': len(need),
            '应记句命中（不计摘要/预告/结论）': sum(e in h for e in need_main),
            '应记句总数（不计摘要/预告/结论）': len(need_main),
            '口径待定句（C/E）': sum(J[e]['code'] in ('C', 'E') for e in h),
            '错提（D）': sum(J[e]['code'] == 'D' for e in h),
            '来源标注不符': sum(h[e]['source_type'] not in EXPECT[J[e]['code']] for e in lab),
            '来源可判句数': len(lab),
            '配方': len(preds[k]['formulations']), '测试': len(preds[k]['tests']),
            '结果': sum(len(t['results']) for t in preds[k]['tests']),
        }
        s = stats[k]
        s['应记句召回'] = round(s['应记句命中'] / s['应记句总数'], 3)
        s['应记句召回（不计摘要/预告/结论）'] = round(s['应记句命中（不计摘要/预告/结论）'] / len(need_main), 3)
        counted = s['挂的原句'] - sum(J[e]['code'] == '续接' for e in h)
        s['挂的句子里应记的比例'] = round(s['应记句命中'] / counted, 3) if counted else None
    nobody = [e for e in need if not any(e in hung[k] for k in EXTRACTORS)]

    wb = Workbook()
    wrap = Alignment(wrap_text=True, vertical='top')
    bold = Font(bold=True)
    head = PatternFill('solid', fgColor='DDEBF7')

    def sheet(title, header, data, widths):
        ws = wb.create_sheet(title)
        ws.append(header)
        for c in ws[1]:
            c.font, c.fill, c.alignment = bold, head, wrap
        for r in data:
            ws.append(r)
        for i, w in enumerate(widths):
            ws.column_dimensions[chr(65 + i)].width = w
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = wrap
        ws.freeze_panes = 'B2'
        return ws

    ws = wb.active
    ws.title = '说明'
    for line in [
        'S39 机制句复核：Claude / GPT / 千问三种设置（2026-10-25，云端）',
        'AI 辅助复核，用户尚未逐项人工确认。判定是 Claude 按规程 §5.7 逐句读原文给的建议，口径待定的几类要用户定。',
        '范围：五家挂在“机制”里的全部原句（并集 85 句）+ 五家都没挂、但应记的 9 句，共 94 句。只判“这句该不该作为机制原句”和“来源标注对不对”，不判机制概括、过程大类、强/弱侧写得对不对。',
        '只有 S39 一篇，是 Claude 提得最多的一篇，不能代表 53 篇。',
        '判定代码：',
        *[f'  {k}：{v}' for k, v in CODES.items()],
        '格子里的符号：✅ 应记且挂了；❌漏 应记没挂；❌错提 挂了不该记的句子；🔶 挂了口径待定的句子；⚠️ 来源标注与判定不符（M0097、M0115 半句转述半句本文结论，不判来源）。符号后是该家的机制编号。',
        '代码核对：94 个句子编号全部在 S39 原文里找到（✅）；五家挂的句子都已判定（脚本断言）。',
        '千问 Max 这一版格式 3 轮都没过（多一个括号），程序删掉括号后另存，仅供对比，未冻结。',
        '“挂的句子里应记的比例”= 应记句命中 ÷（挂的原句 − 续接半句）；口径待定的句子按“不算应记”计，用户定口径后会变。',
    ]:
        ws.append([line])
    ws.column_dimensions['A'].width = 150

    names = list(EXTRACTORS)
    keys = ['机制条数', '挂的原句', '应记句命中', '应记句总数', '应记句召回',
            '应记句命中（不计摘要/预告/结论）', '应记句总数（不计摘要/预告/结论）', '应记句召回（不计摘要/预告/结论）',
            '挂的句子里应记的比例',
            '口径待定句（C/E）', '错提（D）', '来源标注不符', '来源可判句数', '配方', '测试', '结果']
    sheet('汇总', ['指标'] + names, [[k] + [stats[n][k] for n in names] for k in keys] +
          [['说明'] + [EXTRACTORS[n][1] for n in names]], [26] + [18] * len(names))

    data = []
    for e in rows:
        s = src[e]
        data.append([e, f"{'正文' if s['part'] == 'main' else 'SI'} p{s['page']}", J[e]['where'],
                     s['text'], J[e]['code'], J[e]['reason']] + [cell(k, e) for k in names])
    sheet('逐句复核', ['句号', '位置', '段落', '原句', '判定', '理由'] + names, data,
          [8, 9, 11, 80, 6, 40] + [16] * len(names))

    issues = [
        ['口径', '引言/背景转述（C）要不要记', '规程说“只靠转述句支撑的说法照记、标转述”，但没说引言背景是否要穷尽。五家做法不一：Claude 记了 6 句、千问 Max 记 1 句、其他 0 句',
         'M0010、M0011、M0015、M0067、S0169', '建议：引言背景不记；正文里作者拿别人的结论支撑自己解释的句子照记、标转述'],
        ['口径', '性质来源句（E）要不要记', '分子结构 → 溶剂化/溶解度的解释，不涉及四类过程。千问 27B 开思考挂了 9 句，其他家 0–1 句',
         'M0043–M0045、S0093–S0101、S0227', '建议：不进“机制”；有需要时放进“性质”的 method/备注'],
        ['口径', '摘要、引言末预告、结论里重复的说法要不要每句都记', '同一说法在摘要、引言末、正文、结论各说一遍。千问三种设置都挂了引言末预告（M0023–M0026），Claude 挂了摘要，五家都没挂结论 M0167–M0170',
         'M0003–M0005、M0021–M0026、M0158、M0167–M0170', '建议：同一说法只记正文那一句；正文没有的才用摘要/结论句'],
        ['口径', '排除性说法（“电导率不是原因”“界面动力学可忽略”）算不算', '规程允许“只讲电导率时过程大类为空”，本表按应记算。五家都漏得多',
         'M0021、M0088、M0100、S0119、S0120、S0154、S0156、S0162、S0212', '建议：算，是判断两侧短板的关键证据'],
        ['口径', '一句一条还是多句一条', '规程“一句整句原文一条”。千问 27B 开思考把 46 句塞进 11 条，GPT 一句一条但只挂 16 句，Claude 47 条挂 55 句',
         '—', '建议：保留一句一条；同一说法跨两句时可挂连续 2 句'],
        ['漏提', '五家都没挂的应记句', '这几句至少一家应该挂上',
         '、'.join(nobody), '说明召回率是按这 94 句算的，原文里可能还有五家和本表都漏的'],
    ]
    for k in names:
        h = hung[k]
        bad = [e for e in h if J[e]['code'] == 'D']
        if bad:
            issues.append(['错提', f'{k} 挂了不该记的句子', '纯数据/方法/小标题/计算', '、'.join(sorted(bad)), ''])
        mis = [f"{e}（标“{h[e]['source_type']}”，应为{'/'.join(EXPECT[J[e]['code']])}）"
               for e in h if J[e]['code'] in EXPECT and e not in MIXED and h[e]['source_type'] not in EXPECT[J[e]['code']]]
        if mis:
            issues.append(['来源', f'{k} 来源标注与判定不符', '', '；'.join(mis), ''])
    sheet('问题汇总（要你定）', ['类型', '问题', '现状', '例句', '建议（AI 辅助，待用户定）'], issues, [8, 30, 60, 50, 50])

    DEST.mkdir(parents=True, exist_ok=True)
    out = DEST / 'S39_机制句复核.xlsx'
    wb.save(out)
    (DEST / '汇总.json').write_text(json.dumps({'stats': stats, 'nobody': nobody}, ensure_ascii=False, indent=1),
                                   encoding='utf-8')
    print(out)
    for n in names:
        print(n, stats[n])
    print('五家都没挂的应记句', nobody)

if __name__ == '__main__':
    main()
