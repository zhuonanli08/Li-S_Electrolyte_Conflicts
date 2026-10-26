import json,pathlib,hashlib
B=pathlib.Path('output/GPT_v4_调试集53篇_2026-10-24')
class Review:
 def __init__(self,pid):
  self.pid=pid;raw=(B/'independent_predictions'/f'{pid}.json').read_bytes();self.p=json.loads(raw);self.ex={};self.rows={}
  for t in self.p['tests']:
   self.ex[t['id']]=('T/'+t['id'],'测试及条件',t)
   for r in t['results']:self.ex[r['id']]=('T/'+t['id']+'/'+r['id'],'方向',r)
  for m in self.p['mechanisms']:self.ex[m['id']]=('M/'+m['id'],'机制',m)
  self.d=dict(paper_id=pid,reviewer='extract_b',prediction_sha256=hashlib.sha256(raw).hexdigest(),all_prediction_units_reviewed=True,reference_and_source_reviewed=True,coverage_notes='逐项核对冻结预测、正文结果/讨论/结论、SI方法和相关图注及旧参考；机制按10-25说法口径；原模型不判与固定程序数值派生方向分开。未凭目测读图。',units=[],missing=[],reference_errors=[],unresolved=[],suggested_corrections=[])
 def u(self,short,verdict,reason,ids=None,refs=None,new=False):
  key=self.pid+'-'+short if not short.startswith(self.pid) else short;uid,cat,o=self.ex[key]
  assert uid not in self.rows
  self.rows[uid]=dict(id=uid,category=cat,verdict=verdict,reason=reason,evidence_ids=ids.split() if isinstance(ids,str) else (ids if ids is not None else o.get('evidence_ids',[])),reference_ids=refs or [],new_correct=new)
 def many(self,shorts,verdict,reason):
  for short in shorts.split():self.u(short,verdict,reason)
 def fn(self,cat,desc,ids,reason,refs=None):self.d['missing'].append(dict(id='FN'+str(len(self.d['missing'])+1),category=cat,description=desc,evidence_ids=ids.split(),reference_ids=refs or [],reason=reason))
 def finish(self):
  expected={x[0] for x in self.ex.values()};assert set(self.rows)==expected,(expected-set(self.rows))
  self.d['units']=list(self.rows.values());src={x['id'] for x in json.loads((B/'sources'/f'{self.pid}.json').read_text('utf8'))}
  for r in self.d['units']+self.d['missing']:assert set(r['evidence_ids'])<=src
  (B/'cross_reviews').mkdir(exist_ok=True)
  with (B/'cross_reviews'/f'{self.pid}.json').open('x',encoding='utf8') as f:json.dump(self.d,f,ensure_ascii=False,indent=2)
  print(self.pid,len(self.rows),'FN',len(self.d['missing']))
