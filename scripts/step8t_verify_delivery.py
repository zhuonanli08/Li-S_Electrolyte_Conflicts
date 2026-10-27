"""End-to-end delivery checks against frozen inputs and accepted figure sources."""
import collections,hashlib,json
from step8a_prepare_debug53 import OUT,save
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    frozen=read(OUT/'prediction_freeze.json');assert len(frozen)==53
    for pid,rec in frozen.items():
        assert hashlib.sha256((OUT/rec['path']).read_bytes()).hexdigest()==rec['sha256'],pid
        review=read(OUT/'cross_reviews'/f'{pid}.json')
        assert review['prediction_sha256']==rec['sha256'],pid
    metrics=read(OUT/'cross_review_metrics.json')
    assert metrics['reviewed_papers']==53 and not metrics['review_errors'] and not metrics['unresolved_units']
    ledger=read(OUT/'cross_review_rows.json');counts=collections.Counter((x['category'],x['verdict']) for x in ledger)
    for cat,m in metrics['metrics_for_reviewed_papers']['categories'].items():
        for v in ['TP','FP','FN']:assert counts[cat,v]==m[v],(cat,v)
    points=read(OUT/'figure_supplement_points.json');directions=read(OUT/'figure_supplement_directions.json')
    lookup={};tasks={};sources={}
    for p in points:
        pid,tid=p['paper_id'],p['figure_task'];key=(pid,tid,p['formulation'],p['point']);assert key not in lookup
        lookup[key]=p['value']
        if pid not in tasks:tasks[pid]={x['编号']:x for x in read(OUT/'figures'/pid/'tasks.json')}
        if (pid,tid) not in sources:sources[pid,tid]=read(OUT/'figures'/pid/(tid+'_results.json'))
        s=sources[pid,tid]['series'][p['formulation']]
        assert s['usable'] and s['points_repeat_consistent'][p['point']] and s['points'][p['point']]==p['value'],key
        anchors=[a for z in sources[pid,tid]['series'].values() for a in z.get('anchors',[])]
        assert anchors and all(a['pass'] for a in anchors),key
        assert p['unit']==tasks[pid][tid].get('unit','mAh g−1'),key
    seen=set()
    for d in directions:
        pid=d['paper_id'];source_tasks=d.get('source_tasks',[d['figure_task']])
        key=(pid,tuple(source_tasks),tuple(sorted((d['A'],d['B']))),d['point']);assert key not in seen,key;seen.add(key)
        for side in ['A','B']:
            candidates=[lookup.get((pid,t,d[side],d['point'])) for t in source_tasks]
            assert d['value_'+side] in candidates,(key,side)
        assert all(tasks[pid][t].get('allow_comparison') is not False for t in source_tasks),key
        if d['same_conditions'] is not True:assert d['calculation']['direction']=='不判',key
    # Real cases that previously leaked unequal conditions into numerical directions.
    assert not any(d['paper_id'] in {'P212','P149'} for d in directions)
    assert not any(d['paper_id']=='S09' and d['figure_task'] in {'S09_F5A','S09_F5E'} for d in directions)
    assert not any(d['paper_id']=='S18' and d['figure_task'] in {'S18_F6B','S18_FS57','S18_FS58'} for d in directions)
    assert not any(d['paper_id']=='P624' and d['figure_task']=='P624_FS35' for d in directions)
    for d in directions:
        if (d['paper_id']=='S33' and 'DME' in [d['A'],d['B']]) or d['paper_id']=='S28':
            assert d['calculation']['direction']=='不判',d
    figures=read(OUT/'figure_status.json');assert len(figures['requests'])==149
    report={'frozen_predictions_unchanged':53,'reviews_hash_matched':53,'text_score_ledger_matches':True,
      'unresolved_text_units':0,'accepted_points_checked':len(points),'comparisons_checked':len(directions),
      'condition_regressions_passed':True,'figure_summary':figures['summary'],'all_figure_requests_complete':figures['summary']['all_complete']}
    save(OUT/'validation/final_delivery_checks.json',report)
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
