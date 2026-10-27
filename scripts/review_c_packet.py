import json,sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
R=Path('output/GPT_v4_调试集53篇_2026-10-24')
pid=sys.argv[1]; mode=sys.argv[2] if len(sys.argv)>2 else 'pred'
p=json.loads((R/'independent_predictions'/f'{pid}.json').read_text(encoding='utf-8'))
m=next(x for x in json.loads((R/'manifest.json').read_text(encoding='utf-8')) if x['id']==pid)
src=json.loads((R/'sources'/f'{pid}.json').read_text(encoding='utf-8'))
if mode=='short':
 for t in p['tests']:
  print('T',t['id'],t['name'],json.dumps(t['conditions'],ensure_ascii=False))
  for v in t['results']:print('R',*[v.get(k) for k in ['id','metric','A','B','value_A','value_B','unit','point','direction_text','same_conditions','evidence_ids']])
 for v in p['mechanisms']:print('M',v['id'],v['summary'],v['source_type'],v['evidence_ids'])
 print('FIG',json.dumps(p.get('figure_requests'),ensure_ascii=False))
elif mode=='pred':
 for t in p['tests']:
  print('TEST',t['id'],t['name'],json.dumps(t['conditions'],ensure_ascii=False),t['formulations'],'E',t['evidence_ids'])
  for r in t['results']: print('RESULT',json.dumps(r,ensure_ascii=False,separators=(',',':')))
 for x in p['mechanisms']:print('MECH',json.dumps(x,ensure_ascii=False,separators=(',',':')))
 print('GAPS',p.get('gaps'))
elif mode=='ref':
 ref=json.loads(Path(m['reference']).read_text(encoding='utf-8'))
 for k in ('conditions','mechanisms'): 
  if k in ref: print(k,json.dumps(ref[k],ensure_ascii=False,separators=(',',':')))
 for i,c in enumerate(ref.get('comparisons',[]),1):
  print('REF'+str(i),json.dumps({k:c.get(k) for k in ['A','B','cond','metric','val_A','val_B','point','obs_dir','author_judgement','quote','reason_quote','reasons']},ensure_ascii=False,separators=(',',':')))
elif mode=='src':
 lo=int(sys.argv[3]);hi=int(sys.argv[4]);part=sys.argv[5] if len(sys.argv)>5 else 'main'
 for x in src:
  if x['part']==part and lo<=int(x['id'][1:])<=hi: print(x['id'],x['text'])
elif mode=='num':
 data=json.loads((R/'validation/numeric_directions.json').read_text(encoding='utf-8'))
 if isinstance(data,list):print(json.dumps([x for x in data if x.get('paper_id')==pid],ensure_ascii=False))
 else: print(json.dumps(data.get(pid,{}) if pid in data else data,ensure_ascii=False)[:1000])

