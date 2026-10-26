"""Package frozen GPT predictions and explicit reviews without changing either."""
import json,collections
from step8a_prepare_debug53 import OUT,save

def read(path,default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
def txt(v):
    if v is None:return '未报告'
    if isinstance(v,(dict,list)):return json.dumps(v,ensure_ascii=False)
    return str(v)
def main():
    manifest=read(OUT/'manifest.json'); rows=read(OUT/'cross_review_rows.json',[])
    reviews={(r['paper_id'],r['id']):r for r in rows}
    dirs={(r['paper_id'],r['unit']):r for r in read(OUT/'validation/numeric_directions.json',[])}
    metrics=read(OUT/'cross_review_metrics.json',{})
    tables={k:[] for k in ['conclusions','questions','tests','results','mechanisms','formulations','properties','figures','scores','checks']}
    headers={
      'conclusions':['文献','对照与梯度','性质','各测试表现','机制与主张','复核状态','DOI'],
      'questions':['文献','类别','单位','裁定','预测或漏项','核对理由','证据位置','整句原文','✍ 人工备注'],
      'tests':['文献','测试ID','测试名','电池','硫载量','E/S','E/S单位','锂厚','倍率','化成','温度','LiNO3','1C定义','其余条件','配方','AI裁定','证据位置','整句原文'],
      'results':['文献','测试ID','结果ID','指标','A','B','A值','B值','单位','取值点','依据','同条件','提取时方向文字','程序方向或百分点差','程序理由','AI裁定','证据位置','整句原文'],
      'mechanisms':['文献','说法ID','中文概括','A','B','性质','过程类别（原提取）','来源（原提取）','关联测试','短板侧','AI裁定','证据位置','整句原文'],
      'formulations':['文献','配方ID','配方名','原配方写法','组分','角色','用量','单位','对照类型','证据位置','整句原文'],
      'properties':['文献','类型','性质或梯度','数值或档位','方向或排序依据','测法','测量体系','证据位置','整句原文'],
      'figures':['文献','测试ID','图','正文或SI','所需指标','A','B','取值点','当前状态','锚点候选','请求理由'],
      'scores':['文献','类别','单位','裁定','核对理由','漏项描述','证据位置','整句原文'],
      'checks':['文献','单位','类型','详情']}
    counts=collections.Counter(); sources={}; descriptions={}
    def evidence(pid,ids):
        ss=sources[pid];loc=[];quotes=[]
        for eid in ids or []:
            if eid not in ss:loc.append(eid+'：无此索引');continue
            s=ss[eid];loc.append(f"{eid} {s['part']} p.{s['page']}");quotes.append(f"[{eid}] {s['text']}")
        return '\n'.join(loc),'\n'.join(quotes)
    for item in manifest:
        pid=item['id'];sources[pid]={s['id']:s for s in read(OUT/'sources'/f'{pid}.json',[])}
        d=read(OUT/'independent_predictions'/f'{pid}.json')
        if not d:
            tables['conclusions'].append([pid,'未完成独立提取','','','','待提取',item['doi']]);continue
        counts['papers']+=1
        def verdict(uid):return reviews.get((pid,uid),{}).get('verdict','待复核')
        fs=d.get('formulations',[]);props=d.get('properties',[]);gs=d.get('gradients',[])
        counts['formulations']+=len(fs);counts['tests']+=len(d.get('tests',[]));counts['mechanisms']+=len(d.get('mechanisms',[]))
        control=next((f for f in fs if f['id']==d.get('control_id')),None)
        summary_control='对照：'+(txt(control.get('raw_formula') or control.get('name')) if control else txt(d.get('control_id')))+'（'+txt(d.get('control_type'))+'）'
        summary_control+='\n梯度：'+('；'.join(txt(g.get('name'))+' '+txt(g.get('order'))+'；'+txt(g.get('solvation_axis')) for g in gs) or '未报告')
        summary_props='\n'.join(txt(p.get('name'))+'：'+txt(p.get('values') or p.get('direction')) for p in props) or '未报告'
        perf=[];mech=[]
        for f in fs:
            loc,quote=evidence(pid,f.get('evidence_ids',[]))
            for c in f.get('components',[]) or [{}]:
                tables['formulations'].append([pid,f.get('id'),f.get('name'),txt(f.get('raw_formula')),c.get('name'),c.get('role'),c.get('amount'),c.get('unit'),d.get('control_type'),loc,quote])
        for p in props:
            loc,q=evidence(pid,p.get('evidence_ids',[]));tables['properties'].append([pid,'性质',p.get('name'),txt(p.get('values')),p.get('direction'),p.get('method'),p.get('system'),loc,q])
        for g in gs:
            loc,q=evidence(pid,g.get('evidence_ids',[]));tables['properties'].append([pid,'梯度',g.get('name'),txt({'order':g.get('order'),'values':g.get('values')}),txt(g.get('solvation_axis')),None,None,loc,q])
        for t in d.get('tests',[]):
            tid=t['id'];cond=t.get('conditions',{});uid='T/'+tid
            keys=['sulfur_loading','ES','ES_unit','Li_thickness','rate','formation','temperature','LiNO3','one_C']
            loc,q=evidence(pid,t.get('evidence_ids',[]));descriptions[pid,uid]=t.get('name')+'；'+txt(cond)
            tables['tests'].append([pid,tid,t.get('name'),t.get('cell')]+[cond.get(k,'未报告') for k in keys]+[txt({k:v for k,v in cond.items() if k not in keys}),txt(t.get('formulations')),verdict(uid),loc,q])
            statements=collections.defaultdict(set)
            for r in t.get('results',[]):
                rid=uid+'/'+r['id'];dr=dirs.get((pid,rid),{});v=verdict(rid)
                counts['results']+=1
                derived=dr.get('direction')
                if dr.get('CE_difference_pp') is not None:derived='CE差 '+str(dr['CE_difference_pp'])+' 百分点'
                if derived is None and ('CE' in r.get('metric','') or '库仑' in r.get('metric','')):
                    a,b=r.get('value_A'),r.get('value_B')
                    if r.get('same_conditions') is True and all(isinstance(x,(int,float)) for x in [a,b]):derived='CE差 '+str(round(a-b,6))+' 百分点（不判好坏）'
                if not derived:derived='不判'
                loc,q=evidence(pid,r.get('evidence_ids',[]));descriptions[pid,rid]=txt(r)
                tables['results'].append([pid,tid,r['id'],r.get('metric'),r.get('A'),r.get('B'),r.get('value_A'),r.get('value_B'),r.get('unit'),r.get('point'),r.get('basis'),txt(r.get('same_conditions')),r.get('direction_text'),derived,dr.get('reason') or r.get('reason'),v,loc,q])
                final=(r.get('direction_text') if r.get('basis')=='qualitative' else derived) or '不判'
                label=r.get('metric','')+('（作者定性）' if r.get('basis')=='qualitative' else '')
                statements[label].add(final)
            cs=[]
            for k,label in [('sulfur_loading','硫'),('ES','E/S'),('Li_thickness','Li'),('rate','倍率'),('temperature','温度'),('LiNO3','LiNO3')]:
                if cond.get(k) not in [None,'未报告','N/A','不适用']:cs.append(label+' '+txt(cond[k])+(' '+txt(cond.get('ES_unit')) if k=='ES' else ''))
            rs='；'.join(k+'：'+('/'.join(sorted(v)) if len(v)==1 else '随比较/取值点不同，见④') for k,v in statements.items()) or '无配对方向'
            perf.append(tid+' '+t.get('name','')+' ['+ '；'.join(cs)+'] '+rs+('【测试待修正】' if verdict(uid)=='FP' else ''))
        for m in d.get('mechanisms',[]):
            uid='M/'+m['id'];loc,q=evidence(pid,m.get('evidence_ids',[]));descriptions[pid,uid]=m.get('summary')
            tables['mechanisms'].append([pid,m['id'],m.get('summary'),m.get('A'),m.get('B'),m.get('property'),txt(m.get('categories')),m.get('source_type'),txt(m.get('test_ids')),m.get('side'),verdict(uid),loc,q])
            mech.append(m['id']+' '+txt(m.get('side'))+'〔'+','.join(m.get('categories',[]))+'〕'+txt(m.get('summary'))+('【'+verdict(uid)+'】' if verdict(uid) in ['FP','SKIP_DUPLICATE','SKIP_NONSCORING'] else ''))
        mech+=['作者主张：'+txt(x.get('summary')) for x in d.get('design_claims',[])]
        checked=pid in metrics.get('paper_counts',{})
        tables['conclusions'].append([pid,summary_control,summary_props,'\n'.join(perf),'\n'.join(mech),'已AI核对，见②错漏项' if checked else '待AI复核',item['doi']])
        for req in d.get('figure_requests',[]):
            # A request is not a completed read. Keep unattempted work explicit.
            status='待逐图核查/读图'
            matches=[]
            for path in (OUT/'figures'/pid).glob('*_results.json'):
                fr=read(path,{})
                if fr.get('test_id')==req.get('test_id'):matches.append(fr.get('status','未完成'))
            if matches:status='；'.join(matches)
            elif not req.get('anchor_quote_ids'):status='未提供锚点候选，待核查原文'
            tables['figures'].append([pid,req.get('test_id'),req.get('figure'),req.get('part'),req.get('metric'),req.get('A'),req.get('B'),req.get('target_point'),status,txt(req.get('anchor_quote_ids')),req.get('reason')])
    for r in rows:
        pid=r['paper_id'];loc,q=evidence(pid,r.get('evidence_ids',[]))
        tables['scores'].append([pid,r['category'],r['id'],r['verdict'],r.get('reason'),r.get('description'),loc,q])
        if r['verdict'] in ['FP','FN','UNRESOLVED']:
            tables['questions'].append([pid,r['category'],r['id'],r['verdict'],r.get('description') or descriptions.get((pid,r['id']),''),r.get('reason'),loc,q,None])
    for i in read(OUT/'validation/issues.json',[]):tables['checks'].append([i['paper_id'],i['unit'],i['code'],txt(i['detail'])])
    for path in sorted((OUT/'cross_reviews').glob('*.json')):
        d=read(path)
        for kind in ['reference_errors','suggested_corrections']:
            for r in d.get(kind,[]):tables['checks'].append([d['paper_id'],r.get('unit') or r.get('reference_id'),kind,txt(r)])
    save(OUT/'delivery_tables.json',{'as_of':'2026-10-26','counts':dict(counts),'metrics':metrics,'headers':headers,'tables':tables})
    print(json.dumps({'counts':dict(counts),'sheet_rows':{k:len(v) for k,v in tables.items()}},ensure_ascii=False))

if __name__=='__main__':main()
