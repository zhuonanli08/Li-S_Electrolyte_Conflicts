import json, hashlib
from pathlib import Path
from collections import Counter

B=Path('output/GPT_v4_调试集53篇_2026-10-24')
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def score(r):
 c=Counter(x['verdict'] for x in r['units'])
 return {'TP':c['TP'],'FP':c['FP'],'FN':len(r['missing'])}

changes={
 'S09':{
  'units':['T/S09-T9/S09-T9-R1','T/S09-T9/S09-T9-R2'],
  'condition_evidence':['M0250','M0251','M0252','S0029'],
  'reason':'最终参考复核更正：F4DMB未加LiNO3，DDN含1 wt% LiNO3；冻结结果的same_conditions=true错误。原数值本身可保留，但本轮严格口径不允许据此产生同条件数值方向或同条件CE差值方向。原TP忽略添加剂条件，现改FP；作者明确的定性循环差异另计，不能用其替代该数值方向单元。',
  'missing':[{
   'category':'方向','description':'在各自原配方下，F4DMB表现稳定循环，而DDN在50圈内快速容量衰减；这是作者明确的定性循环比较。',
   'evidence_ids':['M0185','M0186','M0252','S0029'],'reference_ids':[],
   'reason':'T9只有同条件数值CE/保持率配对，未独立输出作者稳定性定性。正确目标须标明F4DMB无LiNO3、DDN含1 wt%的混杂，不作为同条件电解液单因素数值方向。'}]
 },
 'S20':{
  'units':['T/S20-T3/S20-T3-R1','T/S20-T3/S20-T3-R2','T/S20-T3/S20-T3-R3','T/S20-T5/S20-T5-R2','T/S20-T5/S20-T5-R3','T/S20-T5/S20-T5-R4'],
  'condition_evidence':['S0010','S0011'],
  'reason':'最终参考复核更正：CD40含0.4 M LiNO3，DD含2 wt% LiNO3；不是已证实等量添加剂条件。冻结结果的same_conditions=true错误，本轮不得产生同条件数值性能方向或同条件CE百分点方向。原TP只核数值而忽略条件，现改FP；保留原数值，作者明示定性另列，不能替代该数值方向单元。',
  'missing':[
   {'category':'方向','description':'作者对比CD40与DD的200圈循环，称CD40具有更高的容量保持率和CE。','evidence_ids':['M0086','M0087','S0010','S0011'],'reference_ids':[],'reason':'T3-R1/R2仅以同条件数值输出，未独立给出作者定性；须标CD40 0.4 M与DD 2 wt% LiNO3混杂，不另派生同条件数值方向。'},
   {'category':'方向','description':'作者以CD40较小的Li2S成核电位差说明其多硫化物转化动力学更快。','evidence_ids':['M0089','S0010','S0011'],'reference_ids':[],'reason':'T3-R3错误作同条件数值判向；该作者明确的成核电位差/动力学定性未被其他方向单元覆盖。须标不同LiNO3用量，仅保留作者配方整体比较。'},
   {'category':'方向','description':'作者明确比较CD40与DD的实用扣式循环，CD40循环容量与容量保持率更高。','evidence_ids':['M0094','M0095','S0010','S0011'],'reference_ids':[],'reason':'T5-R2/R3/R4均为错误同条件数值方向，T5-R5仅覆盖极化增长，未覆盖该作者容量/保持率定性；该目标需标LiNO3条件不同，不机械再列三个数值FN。'}
  ]
 }
}
ledger={'date':'2026-10-27','reviewer':'extract_b','purpose':'更正人工参考裁定遗漏的添加剂条件；预测及图补充不改，不重新评分图补充。','papers':[],'unchanged':[]}
for pid,change in changes.items():
 p=B/'cross_reviews'/f'{pid}.json';before=load(p);r=load(p)
 snapshot=B/'review_revision_history'/'before_condition_correction_b'/f'{pid}.json'
 if not snapshot.exists():save(snapshot,before)
 unit_changes=[]
 for u in r['units']:
  if u['id'] not in change['units']:continue
  assert u['verdict']=='TP', (pid,u['id'],u['verdict'])
  old=dict(u);u['verdict']='FP';u['reason']=change['reason']
  u['evidence_ids']=list(dict.fromkeys(u.get('evidence_ids',[])+change['condition_evidence']))
  u['new_correct']=False
  unit_changes.append({'id':u['id'],'old':old,'new':dict(u)})
 assert len(unit_changes)==len(change['units'])
 next_id=max([int(x['id'][2:]) for x in r['missing'] if x['id'].startswith('FN') and x['id'][2:].isdigit()]+[0])+1
 new_missing=[]
 for m in change['missing']:
  m={'id':f'FN{next_id}',**m};next_id+=1;r['missing'].append(m);new_missing.append(m)
 r['suggested_corrections'].append('2026-10-27条件终核：数值方向须核LiNO3用量，作者明确的定性可保留但需标不同添加剂条件；本次仅修正人工参考裁定，不改冻结预测。')
 r.setdefault('review_revision_history',[]).append({'date':'2026-10-27','reason':'人工参考遗漏LiNO3条件差异','TP_to_FP':change['units'],'added_missing':[m['id'] for m in new_missing],'details':'final_reference_corrections_b.json'})
 save(p,r)
 oldscore,newscore=score(before),score(r)
 ledger['papers'].append({'paper_id':pid,'before':oldscore,'after':newscore,'delta':{k:newscore[k]-oldscore[k] for k in oldscore},'units':unit_changes,'added_missing':new_missing})

# These were already correctly separated as author statements or abstentions.
for pid,notes in {
 'S16':'T/S16-T5/S16-T5-R3与T/S16-T7/S16-T7-R3均basis=qualitative，M0165/M0182作者明确比较稳定性，保留TP。8vol%加入基液引起最终LiNO3浓度不明须另标；原单配方数字仍SKIP_NONSCORING。',
 'S18':'T/S18-T5/S18-T5-R1、T/S18-T10/S18-T10-R1、T/S18-T15/S18-T15-R1已正确SKIP_ABSTENTION，冻结same_conditions=false；初轮文本无误，不变。',
 'S09':'T10-R3/R4原为SKIP_ABSTENTION；已有FN11覆盖作者寿命定性，不重加。',
 'S20':'已有倍率、阻抗、极化、形貌及初始容量相近的qualitative单位保留TP；原界限数字SKIP与已有作者定性FN保持。T7明确无LiNO3，两侧同条件，不受此修订影响。'
}.items():ledger['unchanged'].append({'paper_id':pid,'reason':notes,'delta':{'TP':0,'FP':0,'FN':0}})

ledger['total_delta']={k:sum(x['delta'][k] for x in ledger['papers']) for k in ['TP','FP','FN']}
for pid in ['S09','S16','S18','S20']:
 pred=B/'independent_predictions'/f'{pid}.json';r=load(B/'cross_reviews'/f'{pid}.json')
 assert hashlib.sha256(pred.read_bytes()).hexdigest()==r['prediction_sha256'],pid
 assert len({u['id'] for u in r['units']})==len(r['units']),pid
 assert len({u['id'] for u in r['missing']})==len(r['missing']),pid
save(B/'final_reference_corrections_b.json',ledger)
print(json.dumps({'delta':ledger['total_delta'],'papers':[{k:x[k] for k in ['paper_id','before','after','delta']} for x in ledger['papers']]},ensure_ascii=False,indent=2))
