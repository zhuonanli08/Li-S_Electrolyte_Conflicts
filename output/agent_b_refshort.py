import json,pathlib,sys
sys.stdout.reconfigure(encoding='utf8')
B=pathlib.Path('output/GPT_v4_调试集53篇_2026-10-24');pid=sys.argv[1]
m=next(x for x in json.loads((B/'manifest.json').read_text('utf8')) if x['id']==pid)
d=json.loads(pathlib.Path(m['reference']).read_text('utf8'))
for k,v in d.get('conditions',{}).items(): print('COND',k,json.dumps({a:b for a,b in v.items() if b is not None and a not in ['quote','revise','review','S_content_composite','diameter_mm','area_cm2','porosity']},ensure_ascii=False,separators=(',',':')))
for i,v in enumerate(d.get('comparisons',[])):print('CMP',i,json.dumps({a:b for a,b in v.items() if a in ['A','B','cond','metric','val_A','val_B','unit','point','obs_dir','author_judgement','reason_quote','quote','comparable_point','note']},ensure_ascii=False,separators=(',',':')))
p=json.loads((B/'independent_predictions'/f'{pid}.json').read_text('utf8'))
for i,f in enumerate(p.get('figure_requests',[]),1):print('FIG',i,json.dumps(f,ensure_ascii=False,separators=(',',':')))
