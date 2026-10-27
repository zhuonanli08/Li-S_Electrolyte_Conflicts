"""Validate cross-review coverage and aggregate explicit AI adjudications."""
import collections,hashlib,json
from step8a_prepare_debug53 import OUT,save
from step8e_score_debug53 import score

CATS=['测试及条件','方向','机制']
VERDICTS={'TP','FP','UNRESOLVED','SKIP_ABSTENTION','SKIP_DUPLICATE','SKIP_NONSCORING'}

def expected_units(d):
    out={}
    for t in d.get('tests',[]):
        out['T/'+t['id']]='测试及条件'
        for r in t.get('results',[]):out['T/'+t['id']+'/'+r['id']]='方向'
    for m in d.get('mechanisms',[]):out['M/'+m['id']]='机制'
    return out

def main():
    mf=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    known={m['id'] for m in mf};rows=[];paperstats={};errors=[]
    cats={c:{'reference_ids':[],'prediction_ids':[],'matches':[]} for c in CATS}
    skipped=collections.Counter();unresolved=[]
    for p in sorted((OUT/'cross_reviews').glob('*.json')):
        d=json.loads(p.read_text(encoding='utf-8'));pid=d['paper_id']
        if pid not in known:raise ValueError('Unknown paper '+pid)
        predpath=OUT/'independent_predictions'/f'{pid}.json'
        raw=predpath.read_bytes();pred=json.loads(raw)
        if hashlib.sha256(raw).hexdigest()!=d.get('prediction_sha256'):raise ValueError('Review SHA mismatch '+pid)
        ex=expected_units(pred);u=d['units'];uids=[x['id'] for x in u]
        if len(set(uids))!=len(uids):raise ValueError('Duplicate review unit '+pid)
        if set(ex)!=set(uids):
            errors.append({'paper_id':pid,'missing_review_units':sorted(set(ex)-set(uids)),
                           'unknown_review_units':sorted(set(uids)-set(ex))});continue
        if not d.get('all_prediction_units_reviewed') or not d.get('reference_and_source_reviewed'):
            errors.append({'paper_id':pid,'reason':'review flags incomplete'});continue
        src={x['id'] for x in json.loads((OUT/'sources'/f'{pid}.json').read_text(encoding='utf-8'))}
        stats={c:collections.Counter() for c in CATS}
        for x in u:
            if x['category']!=ex[x['id']]:raise ValueError('Wrong category '+pid+' '+x['id'])
            v=x['verdict'];c=x['category'];uid=pid+'/'+x['id']
            if v not in VERDICTS:raise ValueError('Unknown verdict '+v)
            if not x.get('reason'):raise ValueError('Missing review rationale '+uid)
            if set(x.get('evidence_ids',[]))-src:raise ValueError('Unknown source evidence '+uid)
            stats[c][v]+=1
            if v=='TP':
                rid='R/'+uid;cats[c]['reference_ids'].append(rid);cats[c]['prediction_ids'].append(uid)
                cats[c]['matches'].append({'reference_id':rid,'prediction_id':uid})
            elif v=='FP':cats[c]['prediction_ids'].append(uid)
            elif v=='UNRESOLVED':unresolved.append({'paper_id':pid,**x})
            else:skipped[v]+=1
            rows.append({'paper_id':pid,**x})
        mids=[]
        for x in d.get('missing',[]):
            mid=x['id'];mids.append(mid);c=x['category']
            if c not in CATS:raise ValueError('Wrong FN category')
            if not x.get('evidence_ids') or set(x['evidence_ids'])-src:raise ValueError('Invalid FN evidence '+pid+'/'+mid)
            cats[c]['reference_ids'].append('FN/'+pid+'/'+mid);stats[c]['FN']+=1
            rows.append({'paper_id':pid,'id':mid,'category':c,'verdict':'FN',**x})
        if len(set(mids))!=len(mids):raise ValueError('Duplicate FN ID '+pid)
        paperstats[pid]={c:dict(v) for c,v in stats.items()}
    inp={'independent_prediction':True,'reference_adjudicated':True,'coverage_complete':not unresolved,'categories':cats}
    metrics=score(inp) if paperstats else {'status':'未计算','precision':None,'recall':None}
    result={'as_of':'2026-10-27','scope':'冻结文本预测与初轮数值程序；按10-25说法口径、AI交叉核对参考下的暂定调试指标；程序修正/读图补充另存，不是独立测试成绩',
            'reviewed_papers':len(paperstats),'expected_papers':len(mf),'unreviewed_papers':sorted(known-set(paperstats)),
            'all_53_text_reviews_complete':len(paperstats)==len(mf) and not errors and not unresolved,
            'reference_is_human_gold':False,'review_errors':errors,'unresolved_units':unresolved,
            'skipped_by_reason':dict(skipped),'paper_counts':paperstats,'metrics_for_reviewed_papers':metrics}
    save(OUT/'cross_review_scoring_input.json',inp);save(OUT/'cross_review_rows.json',rows)
    save(OUT/'cross_review_metrics.json',result)
    print(json.dumps({'reviewed_papers':len(paperstats),'review_errors':errors,'unresolved':len(unresolved),
                      'partial_metrics':metrics},ensure_ascii=False))

if __name__=='__main__':main()
