import json,pathlib,sys
sys.stdout.reconfigure(encoding="utf-8"); B=pathlib.Path('output/GPT_v4_调试集53篇_2026-10-24')
id=sys.argv[1]; mode=sys.argv[2]; p=json.loads((B/'independent_predictions'/f'{id}.json').read_text('utf8'))
if mode=='pred':
 for t in p['tests']:
  print('TEST',t['id'],t['name'],t['conditions'],t['evidence_ids'])
  for r in t['results']:print('RES',r['id'],r['metric'],r['A'],r['B'],r['value_A'],r['value_B'],r['point'],r['direction_text'],r['same_conditions'],r['evidence_ids'])
 for m in p['mechanisms']:print('MECH',m['id'],m['summary'],m['source_type'],m['categories'],m['evidence_ids'])
 for d in json.loads((B/'validation/numeric_directions.json').read_text('utf8')):
  if d['paper_id']==id:print('DIR',d['unit'],d['direction'],d['reason'])
elif mode=='ref':
 meta=next(x for x in json.loads((B/'manifest.json').read_text('utf8')) if x['id']==id)
 d=json.loads(pathlib.Path(meta['reference']).read_text('utf8'))
 for k,v in d.items():
  if k in ['paper','electrolytes','descriptors']:continue
  print('REF',k,json.dumps(v,ensure_ascii=False,separators=(',',':')))
elif mode=='src':
 lo=sys.argv[3];hi=sys.argv[4]
 for x in json.loads((B/'sources'/f'{id}.json').read_text('utf8')):
  if lo<=x['id']<=hi:print(x['id'],x['text'])

