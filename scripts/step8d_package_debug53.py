"""Build review tables and an honest status report for the development corpus."""
import json, re, collections, math
from step8a_prepare_debug53 import ROOT, OUT, save
from step8c_build_v4_debug53 import Locate, direction, numeric

def text(x):
    if x is None:return ''
    if isinstance(x,(list,dict)):return json.dumps(x,ensure_ascii=False)
    return str(x)

def known(x):return x is not None and str(x) not in ['', '未报告','原文未写','未独立核对']

def quote_text(q):
    if isinstance(q,dict):return q.get('原句','')
    if isinstance(q,list):return '\n'.join(quote_text(v) for v in q)
    return q or ''

def condition(t):
    fs=[]
    for k in ['电池','硫载量','E/S','锂厚','倍率','温度','LiNO₃']:
        if known(t.get(k)):fs.append(k+'='+text(t[k]))
    return '；'.join(fs)

def v4_pairs(t,r,base):
    if '比较A' in r:
        yield r['比较A'],r['比较B'],r.get('方向','不判'),r.get('判定依据',''),r.get('数值',{}).get(r['比较A']),r.get('数值',{}).get(r['比较B'])
        return
    vals=r.get('数值') or {}
    if r.get('来源')=='读图' and not str(r.get('锚点','')).startswith('通过'):
        yield '',base or '', '不判', '既有读图无锚点',None,None
        return
    done=set()
    if base in vals:
        for a,va in vals.items():
            if a==base:continue
            reasons=[]
            for key in ['硫载量','E/S','锂厚','倍率','温度']:
                v=t.get(key)
                if isinstance(v,dict) and a in v and base in v and v[a]!=v[base]:reasons.append(key+'不同')
            if r.get('跨图'):reasons.append('跨图且未确认同批')
            if reasons:d,why='不判','；'.join(reasons)
            elif '≈' in str(va)+str(vals[base]) or '<' in str(va)+str(vals[base]) or '>' in str(va)+str(vals[base]):d,why='未重算','区间/近似值沿用表样，见记录'
            else:d,why=direction(va,vals[base],r['指标'],r.get('取值点',''),True,'','原句定位通过')
            yield a,base,d,why,va,vals[base];done.add((a,base))
    qs=r.get('作者定性',[])
    if not isinstance(qs,list):qs=[]
    for q in qs:
        if (q.get('A'),q.get('B')) in done:continue
        if q.get('说法不一'):d='不判'
        else:
            smaller=any(k in r['指标'] for k in ['过电位','阻抗','衰减率','自放电','穿梭电流'])
            dr=q.get('方向','')
            d='差异小' if dr=='差异小' else ('变好' if (dr=='↓' if smaller else dr=='↑') else '变坏') if dr in ['↑','↓'] else '不判'
        yield q.get('A',''),q.get('B',''),d,'沿用表样作者定性'+('；说法不一' if q.get('说法不一') else ''),None,None

def main():
    mf=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    supp=json.loads((OUT/'GPT机制补提.json').read_text(encoding='utf-8'))
    new=collections.defaultdict(list)
    tables={k:[] for k in ['一句话结论','要你看','明细-配方','明细-测试','明细-方向','明细-机制','明细-性质梯度','程序核对记录']}
    for pid,sid,summary,cats,src in supp:
        ss=json.loads((OUT/'sources'/f'{pid}.json').read_text(encoding='utf-8'))
        s=next(x for x in ss if x['id']==sid)
        item={'编号':f'G{len(new[pid])+1:02}','证据编号':sid,'概括':summary,'原句':s['text'],'部分':s['part'],'页':s['page'],
              '来源':src,'过程大类':cats,'记录来源':'本轮 GPT 阅读原文候选句后补提；用户未逐项确认',
              '比较范围':'原句所指体系；未强行指定 A/B','落到':[]}
        new[pid].append(item)
    for m in mf:
        pid=m['id'];d=json.loads((OUT/'v4_records'/f'{pid}.json').read_text(encoding='utf-8'));loc=Locate(pid)
        d['本轮GPT机制']=new[pid]
        save(OUT/'v4_records'/f'{pid}.json',d)
        forms=d.get('配方',[]);fmap={f['代号']:f.get('作者原名',f['代号']) for f in forms}
        perf=[]
        for f in forms:
            tables['明细-配方'].append([pid,f['代号'],f.get('作者原名',''),text(f.get('组分',[])),f.get('配方原文记载',''),quote_text(f.get('原句','')),f.get('状态','沿用 v4 表样'),m['doi']])
        for t in d.get('测试',[]):
            tables['明细-测试'].append([pid,t['编号'],t.get('名称',''),t.get('电池',''),text(t.get('硫载量')),text(t.get('E/S')),t.get('E/S单位',''),text(t.get('锂厚')),text(t.get('倍率')),text(t.get('化成')),text(t.get('温度')),text(t.get('LiNO₃')),text(t.get('配方',[])),quote_text(t.get('条件原句','')),t.get('状态','沿用 v4 表样'),m['doi']])
            vals=[]
            for ri,r in enumerate(t.get('结果',[]),1):
                pairs=list(v4_pairs(t,r,d.get('对照')))
                if not pairs:pairs=[('','','未形成配对','原记录无可比配对',None,None)]
                for a,b,dr,why,va,vb in pairs:
                    tables['明细-方向'].append([pid,t['编号'],r.get('编号',f'R{ri:03}'),a,b,r['指标'],r.get('取值点',''),text(va),text(vb),r.get('单位',''),dr,why,quote_text(r.get('原句','')),text(r.get('位置',r.get('图',''))),m['doi']])
                    vals.append(f'{a}/{b} {r["指标"]}：{dr}')
            # All pair-level directions are in the detail table. Avoid an
            # unreadable cell: the conclusion explicitly points to that table.
            ds=[]
            for v in vals:
                if v not in ds:ds.append(v)
            perf.append(t['编号']+' '+condition(t)+'；'+('、'.join(ds) if len(ds)<=4 else '、'.join(ds[:4])+f'；其余 {len(ds)-4} 项见明细-方向'))
        for p in d.get('性质',[]):tables['明细-性质梯度'].append([pid,'性质',p.get('性质',''),text(p),m['doi']])
        for g in d.get('梯度',[]):tables['明细-性质梯度'].append([pid,'梯度',g.get('名称',''),text(g),m['doi']])
        if not d.get('梯度'):tables['明细-性质梯度'].append([pid,'梯度','未完成全档位核对','不能把未迁移的梯度当作论文没有梯度',m['doi']])
        for z in new[pid]:
            tables['明细-机制'].append([pid,z['编号'],z['概括'],'、'.join(z['过程大类']) or '原句未明确落入四类',z['来源'],z['原句'],z['部分'],z['页'],z['证据编号'],'未完成与测试/比较的逐条挂接',m['doi']])
        props='；'.join(p.get('性质','')+':'+text(p.get('数值',p.get('原记载',p.get('方向','未报告')))) for p in d.get('性质',[]))
        conclusion='对照与配方：'+('对照 '+str(d.get('对照'))+'；' if d.get('对照') else '对照类型待核；')+'、'.join(k+'='+v for k,v in fmap.items())
        conclusion+='\n性质：'+(props or '性质未完整补提')
        conclusion+='\n表现：\n'+'\n'.join(perf)
        conclusion+='\n机制：'+'；'.join(z['概括'] for z in new[pid])
        tables['一句话结论'].append([pid,m['doi'],'既有 v4 + GPT 机制补提' if pid in ['S11','S21','S33','S39'] else '旧记录迁移 + GPT 机制补提',conclusion,'；'.join(d['缺口']),'',''])
        # Gap rows are explicit; they are not presented as proven author errors.
        if pid not in ['S11','S21','S33','S39']:tables['要你看'].append([pid,'v4 补提未完成','旧条件组尚未完整拆分；梯度档位、配方角色和机制挂接待补提','当前为可追溯初版，不是验收通过的数据','',''])
        if not m['si_chars']:tables['要你看'].append([pid,'本地无 SI 文本','本地文献索引 si_file 为空','需要确认期刊是否提供 SI；不能填成已检查','',''])
    audit=json.loads((OUT/'程序核对记录.json').read_text(encoding='utf-8'))
    for x in audit:
        locations='；'.join(f"{z['部分']} p{z['页']} {z['证据编号']}" for z in x['定位'])
        tables['程序核对记录'].append([x['文献'],x['测试'],x['指标'],x['核对状态'],x['原句'],locations,x['注意']])
        if x['核对状态'] in ['原句未完整定位','缺原句']:
            tables['要你看'].append([x['文献'],'原句缺口',x['测试']+' '+x['指标'],x['核对状态'],x['原句'],''])
    for z in new.values():
        for x in z:assert x['原句'] and x['证据编号']
    stats=json.loads((OUT/'迁移统计.json').read_text(encoding='utf-8'))
    stats.update({'papers':53,'gpt_mechanisms':len(supp),'mechanism_papers':len(new),'pair_rows':len(tables['明细-方向']),
       'missing_si':[m['id'] for m in mf if not m['si_chars']],'precision':None,'recall':None,'complete':False,
       'scoring_blockers':['本轮测试和性能记录复用了旧参考，不能作为独立预测与同一参考评分',
        '49 篇旧格式尚未完成 v4 的全部测试拆分、梯度、配方角色及机制挂接',
        '53 篇尚无按 v4 单位完整裁定的 TP/FP/FN，机制参考不完整',
        '本轮没有执行完整读图流程，5 条已通过锚点的读图来自既有表样']})
    save(OUT/'review_tables.json',tables);save(OUT/'评估结果.json',stats)
    cfg=json.loads((OUT/'run_config.json').read_text(encoding='utf-8'))
    cfg.update({'mode':'当前对话 GPT 处理；复用旧记录并补提机制；不调用外部 API',
                'evaluation_status':'不能作为独立提取评分；召回率和精确率未计算','complete':False})
    save(OUT/'run_config.json',cfg)
    report=f'''# 53 篇调试集处理记录（未完成验收）

日期：2026-10-24。现行依据：课题方案 §5.7 v4、§14.1a。按用户选择在当前 GPT 对话处理，没有调用 GPT/Qwen 外部 API。

## 已做的工作

- 53 篇 DOI 无重复：23 篇深入证据 + 30 篇试提。留出 6 篇未纳入。P014、P039 虽后被排除，仍按既定调试集保留；S37 不在原 669 篇库中。
- 正文文本 53/53；SI 文本 49/53。缺缓存且本地索引未列 SI：S53、P212、P296、P432。未假定它们一定存在补充材料。
- 复用整理 {stats['tests']} 个旧测试组、{stats['results']} 条结果记录。四篇既有 v4 表样直接保留；49 篇进行了结构迁移，尚未完成全部 v4 语义补提。表中的“测试组”不等于已经审核的 v4 同条件测试。
- 本轮 GPT 从正文/SI 候选原句补提 {len(supp)} 条机制或解释，覆盖 53 篇，全部附证据编号、来源页和英文原文。候选句由关键词筛选后阅读，未覆盖全文所有句子，不能宣称机制无遗漏。用户未逐项人工确认。
- 原句核对：489 条文本引句定位通过；1 条未完整定位（S40 表格行）；5 条原记录无引句。另有 6 条既有读图记录：5 条记载锚点通过，1 条无锚点不使用。本轮没有重新读图。
- 新结果写入本目录，旧 JSON、Excel、人工填写格没有覆盖。

## 召回率和精确率

**未计算，不能用 100% 或引句命中率代替。** 本轮性能和测试数据来自既有参考的复用，对其再评分会发生参考泄漏；本轮新增机制也没有覆盖 53 篇的完整 v4 人工参考。没有独立预测和逐项裁定的 TP、FP、FN，目前不具备有效分母。

按方案，计数单位分别是：一个测试及条件、一个比较中的一个指标方向、一条机制说法。每一类分别统计后再给微平均；错误取值替换真实事实时同时记 1 FP 和 1 FN；未报告或不适用不能当正确负例加入。新提取中参考未覆盖的说法必须回原文裁定，不能一律算 FP。

- 精确率 = TP / (TP + FP)。
- 召回率 = TP / (TP + FN)。
- 分母为零或裁定不完整时返回“未计算”，不填 0。
- 调试集结果即使以后完成评分，也不能当独立 30 篇测试集准确率。

## 尚未完成

1. 49 篇按 v4 完成配方逐组分、全梯度、同条件测试拆分、机制到测试的挂接及必要的读图。当前各篇 JSON 的“缺口”保留这些事项。
2. 固定一份与参考分开的完整 GPT 提取结果；保留预测原始快照，再根据原文裁定参考缺项、错提和漏提。
3. 按三类单位建立一对一匹配清单，形成 TP/FP/FN 后运行评分。评分程序已提供，但未虚构裁定记录。

本次是可追溯初版与机制补提，不是“53 篇独立批量提取及评估已经完成”。
'''
    (OUT/'处理报告.md').write_text(report,encoding='utf-8')
    print(json.dumps(stats,ensure_ascii=False))

if __name__=='__main__':main()
