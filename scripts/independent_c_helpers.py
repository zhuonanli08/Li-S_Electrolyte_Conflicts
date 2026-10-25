import json
from pathlib import Path
ROOT=Path('output/GPT_v4_调试集53篇_2026-10-24')
MF=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
def ev(s): return s.replace(',',' ').split() if isinstance(s,str) else s
def init(pid,si=True):
 return dict(paper_id=pid,doi=next(x['doi'] for x in MF if x['id']==pid),formulations=[],control_id=None,control_type='其他',gradients=[],properties=[],tests=[],mechanisms=[],design_claims=[],figure_requests=[],gaps=[],source_review=dict(main=True,si=si,notes='完整通读正文及可用SI索引；未读旧提取或参考答案。'))
def form(p,id,raw,cs,e):
 p['formulations'].append(dict(id=id,name=id,components=[dict(name=c[0],role=c[1],amount=c[2],unit=c[3]) for c in cs],raw_formula=raw,evidence_ids=ev(e)))
def grad(p,name,order,values,axis,e):
 p['gradients'].append(dict(name=name,order=order,values=values,solvation_axis=axis,evidence_ids=ev(e)))
def prop(p,name,values,direction,method,system,e):
 p['properties'].append(dict(name=name,values=values,direction=direction,method=method,system=system,evidence_ids=ev(e)))
def test(p,id,name,cell,cond,forms,e):
 t=dict(id=id,name=name,cell=cell,conditions=dict(sulfur_loading='未报告',ES='未报告',ES_unit='未报告',Li_thickness='未报告',rate='未报告',formation='未报告',temperature='未报告',LiNO3='未报告',one_C='未报告',**{}),formulations=forms,evidence_ids=ev(e),results=[])
 t['conditions'].update(cond); p['tests'].append(t); return t
def result(t,metric,A,B,va,vb,unit,point,basis,direction,e,reason='',same=True):
 t['results'].append(dict(id=t['id']+'R'+str(len(t['results'])+1),metric=metric,A=A,B=B,value_A=va,value_B=vb,unit=unit,point=point,basis=basis,direction_text=direction,same_conditions=same,evidence_ids=ev(e),reason=reason))
def mech(p,summary,A,B,property,cats,typ,e,tests,side):
 p['mechanisms'].append(dict(id='M'+str(len(p['mechanisms'])+1),summary=summary,A=A,B=B,property=property,categories=cats,source_type=typ,evidence_ids=ev(e),test_ids=tests,side=side))
def claim(p,summary,e): p['design_claims'].append(dict(summary=summary,evidence_ids=ev(e)))
def fig(p,t,f,part,metric,A,B,point,e,reason):
 p['figure_requests'].append(dict(test_id=t,figure=f,part=part,metric=metric,A=A,B=B,target_point=point,anchor_quote_ids=ev(e),reason=reason))
def save(p):
 dst=ROOT/'independent_predictions'/f"{p['paper_id']}.json"; dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists(): raise Exception('Frozen file exists '+str(dst))
 ids={s['id'] for s in json.loads((ROOT/'sources'/f"{p['paper_id']}.json").read_text(encoding='utf-8'))}
 def check(o):
  if isinstance(o,list):
   for x in o: check(x)
  elif isinstance(o,dict):
   for k,v in o.items():
    if k in ['evidence_ids','anchor_quote_ids']:
     for x in v:
      if x not in ids: raise Exception('Invalid evidence '+x)
    check(v)
 check(p)
 dst.write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
 print(p['paper_id'],len(p['tests']),sum(len(t['results']) for t in p['tests']),len(p['mechanisms']),len(p['figure_requests']))

