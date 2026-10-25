"""Score independently adjudicated v4 units, refusing incomplete annotations.

Input JSON: {independent_prediction:true, reference_adjudicated:true,
 coverage_complete:true, categories:{name:{reference_ids:[],prediction_ids:[],
 matches:[{reference_id:...,prediction_id:...}]}}}.
Unmatched reference units are FN; unmatched predicted units are FP only after
explicit coverage_complete certification. One-to-one matching is mandatory.
"""
import argparse,json
from pathlib import Path

def score(data):
    gates=['independent_prediction','reference_adjudicated','coverage_complete']
    missing=[k for k in gates if data.get(k) is not True]
    if missing:return {'status':'未计算','reasons':missing,'precision':None,'recall':None}
    out={};total=[0,0,0]
    if not data.get('categories'):raise ValueError('No evaluation categories')
    for name,c in data['categories'].items():
        r,p=c['reference_ids'],c['prediction_ids'];pairs=c.get('matches',[])
        if len(set(r))!=len(r) or len(set(p))!=len(p):raise ValueError('Duplicate unit IDs')
        mr=[x['reference_id'] for x in pairs];mp=[x['prediction_id'] for x in pairs]
        if len(set(mr))!=len(mr) or len(set(mp))!=len(mp):raise ValueError('Matching must be one-to-one')
        if not set(mr)<=set(r) or not set(mp)<=set(p):raise ValueError('Unknown matched unit')
        tp=len(pairs);fp=len(p)-tp;fn=len(r)-tp
        out[name]={'TP':tp,'FP':fp,'FN':fn,'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None}
        total=[a+b for a,b in zip(total,[tp,fp,fn])]
    tp,fp,fn=total
    return {'status':'已计算（仅对已裁定范围）','categories':out,'micro':{'TP':tp,'FP':fp,'FN':fn,'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None}}

def selftest():
    d={'independent_prediction':True,'reference_adjudicated':True,'coverage_complete':True,'categories':{'方向':{'reference_ids':['r1','r2'],'prediction_ids':['p1','p2','p3'],'matches':[{'reference_id':'r1','prediction_id':'p1'}]}}}
    s=score(d)['micro'];assert (s['TP'],s['FP'],s['FN'])==(1,2,1) and s['recall']==.5 and s['precision']==1/3
    d['independent_prediction']=False;assert score(d)['precision'] is None
    d['independent_prediction']=True;d['categories']['方向']['matches'].append({'reference_id':'r1','prediction_id':'p2'})
    try:score(d)
    except ValueError:pass
    else:raise AssertionError('duplicate matching accepted')
    print('评分公式、参考泄漏拦截和一对一匹配检查通过')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input');ap.add_argument('--output');ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
    if a.self_test:selftest()
    elif a.input:
        result=score(json.loads(Path(a.input).read_text(encoding='utf-8')))
        if a.output:Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False))
    else:ap.error('Provide --input or --self-test')
