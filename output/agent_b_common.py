import json,pathlib
BASE=pathlib.Path('output/GPT_v4_调试集53篇_2026-10-24')
META={v['id']:{k:v[k] for k in ('id','doi','stem','title')} for v in json.loads((BASE/'manifest.json').read_text(encoding='utf8'))}
OUT=BASE/'independent_predictions'; OUT.mkdir(exist_ok=True)
def ev(x): return x.split() if isinstance(x,str) else x
def paper(pid,control,ctype,si=True):
 return dict(paper_id=pid,doi=META[pid]['doi'],formulations=[],control_id=control,control_type=ctype,gradients=[],properties=[],tests=[],mechanisms=[],design_claims=[],figure_requests=[],gaps=[],source_review={'main':True,'si':si,'notes':'正文与可得SI按原始索引复核；参考文献不作为本文实验。数值仅原文，图不目测。'})
def form(p,i,name,components,ids,raw=None):
 p['formulations'].append(dict(id=i,name=name,components=[dict(name=n,role=r,amount=a,unit=u) for n,r,a,u in components],raw_formula=raw or name,evidence_ids=ev(ids)))
def grad(p,n,order,values,axis,ids):p['gradients'].append(dict(name=n,order=order,values=values,solvation_axis=axis,evidence_ids=ev(ids)))
def prop(p,n,values,direction,method,system,ids):p['properties'].append(dict(name=n,values=values,direction=direction,method=method,system=system,evidence_ids=ev(ids)))
def test(p,n,forms,ids,cell='Li||S 扣式',**cond):
 i=f"{p['paper_id']}-T{len(p['tests'])+1}"; c={k:'未报告' for k in ['sulfur_loading','ES','ES_unit','Li_thickness','rate','formation','temperature','LiNO3','one_C']};c.update(cond)
 t=dict(id=i,name=n,cell=cell,conditions=c,formulations=forms,evidence_ids=ev(ids),results=[]);p['tests'].append(t);return t

def result(t,metric,A,B,va,vb,unit,point,ids,basis='numeric',direction='不判',same=True,reason='数值方向待程序复算'):
 t['results'].append(dict(id=t['id']+'-R'+str(len(t['results'])+1),metric=metric,A=A,B=B,value_A=va,value_B=vb,unit=unit,point=point,basis=basis,direction_text=direction,same_conditions=same,evidence_ids=ev(ids),reason=reason))
def mech(p,summary,A,B,property,cats,ids,tests=[],side='其他',source='本文结论'):
 p['mechanisms'].append(dict(id=p['paper_id']+'-M'+str(len(p['mechanisms'])+1),summary=summary,A=A,B=B,property=property,categories=cats.split(),source_type=source,evidence_ids=ev(ids),test_ids=[x['id'] if isinstance(x,dict) else x for x in tests],side=side))
def fig(p,t,figure,metric,A,B,point,ids,part='main',reason='原文无可直接抄录数值；需几何读图并核对同测试锚点，无锚点整图不用'):
 p['figure_requests'].append(dict(test_id=t['id'],figure=figure,part=part,metric=metric,A=A,B=B,target_point=point,anchor_quote_ids=ev(ids),reason=reason))
def save(p):
 src={x['id'] for x in json.loads((BASE/'sources'/f"{p['paper_id']}.json").read_text(encoding='utf8'))}
 def walk(o):
  if isinstance(o,dict):
   for k,v in o.items():
    if k in ('evidence_ids','anchor_quote_ids'):
     assert all(z in src for z in v),(p['paper_id'],v)
    else:walk(v)
  elif isinstance(o,list):
   for z in o:walk(z)
 walk(p)
 with (OUT/(p['paper_id']+'.json')).open('x',encoding='utf8') as f:json.dump(p,f,ensure_ascii=False,indent=2)
 print(p['paper_id'],len(p['tests']),sum(len(t['results']) for t in p['tests']),len(p['mechanisms']),len(p['figure_requests']))
