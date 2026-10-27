import json, pathlib, hashlib, collections
BASE=pathlib.Path(__file__).resolve().parents[1]
REV=BASE/'cross_reviews'
AUDIT=REV/'reference_revision_audit'/'condition_consistency_2026-10-27'
AUDIT.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def counts(d):return dict(collections.Counter(u['verdict'] for u in d['units']))
targets={
 'P149':['T/P149-T2/P149-T2-R2','T/P149-T3/P149-T3-R1','T/P149-T4/P149-T4-R1'],
 'S28':[f'T/S28-T{n}/S28-T{n}-R{i}' for n in [1,2,3] for i in range(1,13)]+['T/S28-T9/S28-T9-R1','T/S28-T10/S28-T10-R1'],
 'P212':['T/P212-T4/P212-T4-R13']
}
pred_hash={pid:sha(BASE/'independent_predictions'/f'{pid}.json') for pid in ['P149','S28','P212','P624']}
report={'date':'2026-10-27','reviewer':'extract_a','scope':'仅纠正参考复核中与已确证LiNO3差异/不可确认相同条件相关的方向裁定；作者原文定性保留。冻结预测与固定程序均不改。','papers':[]}
for pid,ids in targets.items():
 p=REV/f'{pid}.json';raw=p.read_bytes();d=read(p);by={u['id']:u for u in d['units']};before=counts(d)
 backup=AUDIT/f'{pid}_before.json';assert not backup.exists(),str(backup);backup.write_bytes(raw)
 changes=[]
 for uid in ids:
  u=by[uid];old=json.loads(json.dumps(u,ensure_ascii=False))
  if pid=='P149':
   assert u['verdict']=='TP',uid
   reason='原数抄录保留；TDE的LiNO3约0.025（原文m），LS002为1 wt%，已明确不同。预测same_conditions=true使固定程序输出容量/保持率方向，违反本轮严格条件口径，应不判。参考原TP未检查该条件，现纠正为FP；不把数值正确等同方向正确。'
   ev=['M0043','M0044','M0169','M0170'];u['verdict']='FP'
  elif pid=='S28':
   assert u['verdict']=='TP',uid
   reason='原数及A/B抄录保留，但该配方LiNO3为每1摩尔LiTFSI配0.2摩尔份，DD为0.2 M；不能仅凭同为0.2确认绝对添加剂条件相同。预测same_conditions=true导致固定程序判数值方向（CE为同条件百分点差），严格规程应不判。参考原TP忽略已记录的口径差异，现纠正FP。所有组无LiNO3的T7和内部同配方用量口径的比较不受本项修正。'
   ev=['S0034','S0035','S0036'];u['verdict']='FP'
  else:
   assert u['verdict']=='FP',uid
   reason='M0040直接给出DEGDME_HCE比TREGDME_HCE的CV峰更平滑、极化更低。按当前口径，作者本篇定性比较可保留，不能仅因LiNO3不同将正确转述扣为方向FP；不强化为单因素因果或同条件数值比较。same_conditions标记不当仍由T/P212-T4条件FP及更正说明承担。'
   ev=['M0040','M0012'];u['verdict']='TP'
  u['reason']=reason;u['evidence_ids']=list(dict.fromkeys(u.get('evidence_ids',[])+ev));u['new_correct']=False
  changes.append({'unit_id':uid,'before':old,'after_verdict':u['verdict'],'after_reason':reason})
 d.setdefault('reference_errors',[]).append({'reference_id':'cross_review_condition_consistency_2026-10-27','reason':f'本次参考裁定一致性纠正，受影响units共{len(ids)}项；预测与固定数值程序保持冻结。详细前值与修正保存在reference_revision_audit/condition_consistency_2026-10-27。','evidence_ids':ev})
 d.setdefault('suggested_corrections',[]).append({'target_ids':ids,'correction':'数值比较须将不同或不能确认相同LiNO3用量的same_conditions改为false/null，保留原数；作者定性可单独保留并说明混杂。','evidence_ids':ev})
 d.setdefault('reference_revision_history',[]).append({'date':'2026-10-27','reviewer':'extract_a','audit_file':str((AUDIT/'report.json').relative_to(BASE)),'affected_units':ids,'counts_before':before,'counts_after':counts(d),'missing_before_after':len(d.get('missing',[]))})
 save(p,d);report['papers'].append({'paper_id':pid,'counts_before':before,'counts_after':counts(d),'missing_count_unchanged':len(d.get('missing',[])),'changes':changes})
report['papers'].append({'paper_id':'P624','action':'checked_no_change','reason':'所有配对数值均已same_conditions=null/false并判SKIP_ABSTENTION；单组CE为SKIP_NONSCORING，作者定性TP未当数值TP。'})
assert pred_hash=={pid:sha(BASE/'independent_predictions'/f'{pid}.json') for pid in pred_hash}
report['prediction_hashes_unchanged']=pred_hash
save(AUDIT/'report.json',report)
print(json.dumps([{k:v for k,v in p.items() if k!='changes'} for p in report['papers']],ensure_ascii=False))
