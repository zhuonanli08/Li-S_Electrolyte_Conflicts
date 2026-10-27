import sys,json,hashlib
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
r=Path('output/GPT_v4_调试集53篇_2026-10-24');ids='S33 S37 S39 S40 S44 S51 S53 P014 P039 P095 P109 P149 P163 P211 P248 P271'.split();total=Counter();f=Counter();bad=[]
for pid in ids:
 ppath=r/'independent_predictions'/f'{pid}.json';p=json.loads(ppath.read_text(encoding='utf-8'));x=json.loads((r/'cross_reviews'/f'{pid}.json').read_text(encoding='utf-8'));s={z['id'] for z in json.loads((r/'sources'/f'{pid}.json').read_text(encoding='utf-8'))}
 expected=['T/'+t['id'] for t in p['tests']]+['T/'+t['id']+'/'+v['id'] for t in p['tests'] for v in t['results']]+['M/'+m['id'] for m in p['mechanisms']];actual=[v['id'] for v in x['units']]
 if set(actual)!=set(expected) or len(actual)!=len(expected):bad.append((pid,'units'))
 if x['prediction_sha256']!=hashlib.sha256(ppath.read_bytes()).hexdigest():bad.append((pid,'hash'))
 for group in ['units','missing','reference_errors','figure_triage']:
  for row in x.get(group,[]):
   for ev in row.get('evidence_ids',[]):
    if ev not in s:bad.append((pid,group,ev))
 c=Counter(v['verdict'] for v in x['units']);total.update(c);f.update(v['status'] for v in x.get('figure_triage',[]));print(pid,len(actual),dict(c),'FN',len(x['missing']))
print('TOTAL',dict(total),'FIG',dict(f),'BAD',bad)
