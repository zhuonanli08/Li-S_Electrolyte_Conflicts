import json,hashlib
from pathlib import Path
R=Path('output/GPT_v4_调试集53篇_2026-10-24')
class Review:
 def __init__(self,pid):
  self.pid=pid; path=R/'independent_predictions'/f'{pid}.json';self.p=json.loads(path.read_text(encoding='utf-8'));self.expected={};self.done={}
  for t in self.p['tests']:
   self.expected['T/'+t['id']]=('测试及条件',t)
   for v in t['results']:self.expected['T/'+t['id']+'/'+v['id']]=('方向',v)
  for v in self.p['mechanisms']:self.expected['M/'+v['id']]=('机制',v)
  self.out=dict(paper_id=pid,reviewer='extract_c',prediction_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),all_prediction_units_reviewed=True,reference_and_source_reviewed=True,coverage_notes='',units=[],missing=[],reference_errors=[],unresolved=[],suggested_corrections=[])
 def unit(self,key,verdict,reason,ev=None,ref=None,new=False):
  if key.startswith('t'):
   bits=key[1:].split('r');t=f'{self.pid}-T{bits[0]}';key='T/'+t+('/'+t+'-R'+bits[1] if len(bits)>1 else '')
  elif key.startswith('m'):key='M/'+self.pid+'-M'+key[1:]
  assert key in self.expected,key;assert key not in self.done,key
  cat,v=self.expected[key];self.done[key]=dict(id=key,category=cat,verdict=verdict,reason=reason,evidence_ids=ev or v.get('evidence_ids',[]),reference_ids=ref or [],new_correct=new)
 def group(self,keys,verdict,reason,ev=None,ref=None,new=False):
  for k in keys.split():self.unit(k,verdict,reason,ev,ref,new)
 def miss(self,cat,desc,ev,ref=None,reason='原文独有目标未被冻结预测覆盖'):
  self.out['missing'].append(dict(id='FN'+str(len(self.out['missing'])+1),category=cat,description=desc,evidence_ids=ev,reference_ids=ref or [],reason=reason))
 def save(self,notes):
  assert set(self.expected)==set(self.done),set(self.expected)-set(self.done)
  self.out['coverage_notes']=notes;self.out['units']=[self.done[k] for k in self.expected]
  dst=R/'cross_reviews'/f'{self.pid}.json';assert not dst.exists(),str(dst);dst.parent.mkdir(exist_ok=True)
  dst.write_text(json.dumps(self.out,ensure_ascii=False,indent=2),encoding='utf-8')
  from collections import Counter
  print(self.pid,len(self.done),Counter(v['verdict'] for v in self.done.values()),'missing',len(self.out['missing']))
