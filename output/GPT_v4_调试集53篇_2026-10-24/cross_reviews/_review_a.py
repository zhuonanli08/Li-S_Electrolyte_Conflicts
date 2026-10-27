import json,pathlib,hashlib,sys
BASE=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def packet(pid,mode='all',start=0,end=99999):
 p=read(BASE/'independent_predictions'/f'{pid}.json')
 if mode=='compact':
  print('PRED',pid)
  for t in p['tests']:
   print(t['id'],t['name'],t['cell'],json.dumps(t['conditions'],ensure_ascii=False,separators=(',',':')),t['evidence_ids'])
   for r in t['results']:print(r['id'],r['metric'],r['A'],r['B'],r['value_A'],r['value_B'],r['unit'],r['point'],r['basis'],r['direction_text'],r['same_conditions'],','.join(r['evidence_ids']))
  for m in p['mechanisms']:print(m['id'],m['summary'],m['source_type'],','.join(m['evidence_ids']))
  print('FIG',p.get('figure_requests',[]))
  m=next(x for x in read(BASE/'manifest.json') if x['id']==pid);old=read(m['reference'])
  print('REFCOND',old.get('条件'));print('REF',old.get('比较'));print('REFNOTE',old.get('备注'))
  print('NUM',[(n['unit'],n['direction']) for n in read(BASE/'validation/numeric_directions.json') if n['paper_id']==pid])
  for s in read(BASE/'sources'/f'{pid}.json'):
   if any(w in s['text'] for w in ['Results','Experimental','Conclusion','References']):print('HEAD',s['id'],s['text'][:110])
 if mode in ('all','pred'):
  print('PRED',pid)
  for t in p['tests']:
   print('TEST',t['id'],t['name'],t['cell'],json.dumps(t['conditions'],ensure_ascii=False),t['formulations'],t['evidence_ids'])
   for r in t['results']:print('RESULT',r)
  for m in p['mechanisms']:print('MECH',m)
  print('GAPS',p.get('gaps'))
  print('NUMERIC',[n for n in read(BASE/'validation/numeric_directions.json') if n['paper_id']==pid])
 if mode in ('all','ref'):
  m=next(x for x in read(BASE/'manifest.json') if x['id']==pid)
  print('REFERENCE',json.dumps(read(m['reference']),ensure_ascii=False,separators=(',',':')))
 if mode in ('all','src'):
  s=read(BASE/'sources'/f'{pid}.json')
  for i,x in enumerate(s):
   if start<=i<end:print(x['id'],x['part'],x['text'])
class Review:
 def __init__(self,pid,notes):
  self.pid=pid;self.p=read(BASE/'independent_predictions'/f'{pid}.json');self.sources={s['id']:s for s in read(BASE/'sources'/f'{pid}.json')};self.units={}
  self.d=dict(paper_id=pid,reviewer='GPT-extract_a-cross-review',prediction_sha256=hashlib.sha256((BASE/'independent_predictions'/f'{pid}.json').read_bytes()).hexdigest(),all_prediction_units_reviewed=True,reference_and_source_reviewed=True,coverage_notes=notes,units=[],missing=[],reference_errors=[],unresolved=[],suggested_corrections=[])
 def unit(self,key,verdict,reason,ev=None,refs=None,new=False):
  assert key not in self.units,key
  if key.startswith('M/'):
   item=next(m for m in self.p['mechanisms'] if m['id']==key[2:]);cat='机制'
  else:
   z=key.split('/');t=next(t for t in self.p['tests'] if t['id']==z[1]);item=t if len(z)==2 else next(r for r in t['results'] if r['id']==z[2]);cat='测试及条件' if len(z)==2 else '方向'
  ev=item.get('evidence_ids',[]) if ev is None else ev
  self.units[key]=dict(id=key,category=cat,verdict=verdict,reason=reason,evidence_ids=ev,reference_ids=refs or [],new_correct=new)
 def miss(self,cat,desc,ev,reason,refs=None):self.d['missing'].append(dict(id='FN'+str(len(self.d['missing'])+1),category=cat,description=desc,evidence_ids=ev,reference_ids=refs or [],reason=reason))
 def save(self):
  expected=[]
  for t in self.p['tests']:
   expected.append('T/'+t['id']);expected.extend('T/'+t['id']+'/'+r['id'] for r in t['results'])
  expected.extend('M/'+m['id'] for m in self.p['mechanisms'])
  assert set(expected)==set(self.units),(set(expected)-set(self.units),set(self.units)-set(expected))
  self.d['units']=[self.units[k] for k in expected]
  for x in self.d['units']+self.d['missing']:
   assert all(e in self.sources for e in x['evidence_ids']),x
  out=BASE/'cross_reviews'/f'{self.pid}.json';assert not out.exists(),out
  out.write_text(json.dumps(self.d,ensure_ascii=False,indent=2),encoding='utf-8');print('SAVED',self.pid,len(expected),'missing',len(self.d['missing']))
if __name__=='__main__':packet(*sys.argv[1:3],*[int(x) for x in sys.argv[3:]])
