"""Track every requested figure and export only visually checked code readings."""
import collections,json
from pathlib import Path
from step8a_prepare_debug53 import OUT,save
from step8f_validate_independent import numeric_direction

def read(p,default):return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
def main():
    queue=[];directions=[];points=[];seen_points=set();seen_values=set()
    for pp in sorted((OUT/'independent_predictions').glob('*.json')):
        d=read(pp,{});pid=d['paper_id'];fd=OUT/'figures'/pid
        tasks=read(fd/'tasks.json',[]);review=read(OUT/'cross_reviews'/f'{pid}.json',{})
        triage={x['request_index']:x for x in review.get('figure_triage',[]) if 'request_index' in x}
        triage.update({x['request_index']:x for x in read(fd/'request_review.json',[])})
        visual=read(fd/'visual_review.json',{});approved={x.get('file') if isinstance(x,dict) else x for x in visual.get('reviewed_overlays',[])}
        accepted={x['file']:x.get('accepted_points') for x in visual.get('reviewed_overlays',[]) if isinstance(x,dict)}
        for ix,req in enumerate(d.get('figure_requests',[]),1):
            matched=[]
            for task in tasks:
                indices=task.get('request_indices') or ([task['request_index']] if task.get('request_index') else [])
                if indices and ix not in indices:continue
                if not indices and task.get('test_id')!=req.get('test_id'):continue
                result=read(fd/(task['编号']+'_results.json'),None)
                if result:matched.append((task,result,'核对_'+task['编号']+'.png' in approved))
            tr=triage.get(ix,{})
            terminal={'no_anchor','no_numeric_capacity_anchor','out_of_scope','conditions_differ','duplicate','unread','geometry_failed','anchor_failed','mapping_ambiguous'}
            if tr.get('status') in terminal:
                status=('仅图未读：' if tr['status'] in {'unread','geometry_failed','anchor_failed','mapping_ambiguous'} else '不采用：')+tr['status'];done=True
            elif matched:
                if all(not r.get('series') for _,r,_ in matched):status='仅图未读：程序几何失败';done=True
                elif all(v or not r.get('series') for _,r,v in matched):
                    status='已核验读图' if any(s.get('usable') for _,r,_ in matched for s in r.get('series',{}).values()) else '仅图未读：锚点或取值未通过'
                    done=True
                elif all(not r.get('series') for _,r,_ in matched):status='仅图未读：程序几何失败';done=True
                else:status='代码已运行，待图形核验';done=False
            else:status='待读图' if tr.get('status')=='eligible' else '待适用性/锚点核查';done=False
            row={'paper_id':pid,'request_index':ix,**req,'status':status,'complete':done,'triage':tr,
                 'result_files':[t['编号']+'_results.json' for t,_,_ in matched]}
            queue.append(row)
            if not matched or tr.get('status') in terminal:continue
            groups={}
            for task,result,ok in matched:
                if not ok:continue
                series={}
                visual_points=accepted.get('核对_'+task['编号']+'.png')
                for fid,s in result.get('series',{}).items():
                    if s.get('usable'):
                        series[fid]={k:v for k,v in s['points'].items() if s['points_repeat_consistent'].get(k) and (visual_points is None or k in visual_points.get(fid,[]))}
                        for point,value in series[fid].items():
                            key=(pid,task['编号'],fid,point)
                            if key in seen_values:continue
                            seen_values.add(key)
                            points.append({'paper_id':pid,'request_index':ix,'figure_task':task['编号'],'test_id':task.get('test_id'),
                              'formulation':fid,'point':point,'metric':task.get('metric','同圈容量'),'value':value,'unit':task.get('unit','mAh g−1'),
                              'anchors':[a for s2 in result.get('series',{}).values() for a in s2.get('anchors',[])],
                              'source_image':result.get('source_image'),'notes':task.get('comparison_prohibition_reason') or '已核验；只用于方向，不混入初轮评分'})
                if task.get('allow_comparison') is False:continue
                # Cross-panel comparisons require an explicit same-test group.
                group=(task.get('comparison_group',task['编号']),task.get('test_id'),task.get('metric','同圈容量'),task.get('unit','mAh g−1'))
                g=groups.setdefault(group,{'task':task,'series':{},'sources':[],'explicit_pairs':None})
                for fid,ps in series.items():
                    if fid in g['series'] and g['series'][fid]!=ps:raise ValueError('同组存在冲突系列：'+pid+' '+fid)
                    g['series'][fid]=ps
                g['sources'].append(task['编号'])
                if 'comparison_pairs' in task:
                    if g['explicit_pairs'] is None:g['explicit_pairs']=[]
                    g['explicit_pairs']+=task['comparison_pairs']
            for group,g in groups.items():
                task=g['task'];series=g['series'];task_label=' + '.join(g['sources'])
                def ids(value):
                    if isinstance(value,list):return value
                    if value in series:return [value]
                    return str(value or '').split('/')
                aa=ids(req.get('A'));bb=ids(req.get('B'))
                pairs=[(a,b) for a in aa for b in bb]
                if g['explicit_pairs'] is not None:
                    allowed={frozenset(x) for x in g['explicit_pairs']}
                    pairs=[p for p in pairs if frozenset(p) in allowed]+g['explicit_pairs']
                for a,b in dict.fromkeys(tuple(x) for x in pairs):
                    if a not in series or b not in series or a==b:continue
                    for point in sorted(set(series[a])&set(series[b]),key=float):
                        key=(pid,group[0],tuple(sorted((a,b))),point)
                        if key in seen_points:continue
                        seen_points.add(key)
                        decision=next((z for z in task.get('comparison_adjudications',[]) if {z['A'],z['B']}=={a,b}),{})
                        r={'metric':task.get('metric','同圈容量'),'basis':'numeric','same_conditions':decision.get('same_conditions',True),'A':a,'B':b,
                           'value_A':series[a][point],'value_B':series[b][point],'unit':task.get('unit','mAh g−1'),'point':point}
                        calc=numeric_direction({**r,'metric':'能量密度' if r['metric']=='比能量' else r['metric']})
                        if decision.get('reason'):calc['reason']=decision['reason']
                        directions.append({'paper_id':pid,'request_index':ix,'test_id':task.get('test_id',req['test_id']),'figure_task':task_label,'source_tasks':g['sources'],**r,
                                           'calculation':calc,'usage':'只补充方向，不混入冻结文本首轮评分'})
    stats={'requested':len(queue),'completed':sum(x['complete'] for x in queue),
           'pending':sum(not x['complete'] for x in queue),'status_counts':dict(collections.Counter(x['status'] for x in queue)),
           'accepted_series_points':len(points),'paired_comparisons':len(directions),
           'paired_direction_points':sum(x['calculation'].get('direction') in {'变好','变坏','差异小'} for x in directions),
           'comparisons_not_adjudicated':sum(x['calculation'].get('direction')=='不判' for x in directions),'all_complete':all(x['complete'] for x in queue)}
    save(OUT/'figure_status.json',{'summary':stats,'requests':queue});save(OUT/'figure_supplement_directions.json',directions)
    save(OUT/'figure_supplement_points.json',points)
    print(json.dumps(stats,ensure_ascii=False))
if __name__=='__main__':main()
