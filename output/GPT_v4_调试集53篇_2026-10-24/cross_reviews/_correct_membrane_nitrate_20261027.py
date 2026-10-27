import json,pathlib,hashlib,collections
B=pathlib.Path(__file__).resolve().parents[1];R=B/'cross_reviews';A=R/'reference_revision_audit'/'membrane_nitrate_2026-10-27';A.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ph={pid:sha(B/'independent_predictions'/f'{pid}.json') for pid in ['P337','P548']}
p=R/'P337.json';d=read(p);backup=A/'P337_before.json';assert not backup.exists();backup.write_bytes(p.read_bytes());before=dict(collections.Counter(u['verdict'] for u in d['units']));by={u['id']:u for u in d['units']};changes=[]
for uid in ['T/T1/T1R1','T/T1/T1R2','T/T6/T6R3']:
 u=by[uid];old=json.loads(json.dumps(u));assert u['verdict']=='TP';u['verdict']='FP';u['new_correct']=False
 if uid.startswith('T/T1/'):
  u['reason']='FN-SEI含2 wt%基础电解液并另配LiNO3载量约1.2 mg cm−2的LNO-SRF；R-SEI/F-SEI不含膜。S0001–S0003、M0054明确额外LiNO3来源差异，不能把该CE配对作为same_conditions=true的同条件百分点差TP。原数保留，不套5%阈值；作者最高CE的定性可另保留，不将本数值单位自动改算定性。'
 else:
  u['reason']='T6常规高载量FN-SEI另配含LiNO3的LNO-SRF，R-SEI无膜。M0160调膜使总LiNO3相等仅属于FigureS13/T5特设试验，不能无依据扩展给T6。25圈220/360 mV原数保留，但预测same_conditions=true导致程序数值判向，应不判，原TP修正为FP。'
 u['evidence_ids']=list(dict.fromkeys(u.get('evidence_ids',[])+['S0001','S0002','S0003','M0054','M0160']))
 changes.append({'unit_id':uid,'before':old,'after_verdict':'FP','after_reason':u['reason']})
u=by['T/T6/T6R1'];assert u['verdict']=='TP';u['adjudicated_basis']='author_qualitative';u['reason']='保留TP仅因M0173直接写nearly identical的作者定性，符合作者原话可保留口径；约1250/约1250不作精确5%数值比较。FN额外缓释膜使LiNO3总量未与R确认相等，same_conditions应改false/null并明示混杂，不据数值相同判TP。'
u=by['T/T1/T1R3'];assert u['verdict']=='TP';u['reason']+=' 定点复核：FN-SEI与N-SEI均为2 wt%并均配同载量LNO-SRF，没有已确证额外LiNO3量差异；不以未报告字段自动认定条件不等。'
after=dict(collections.Counter(u['verdict'] for u in d['units']))
d.setdefault('reference_errors',[]).append({'reference_id':'cross_review_membrane_nitrate_2026-10-27','reason':'原复核忽略FN/R及FN/F的额外LiNO3缓释膜差异，误将T1R1、T1R2、T6R3计数值方向TP；等总LiNO3特设试验仅T5。T6R1仅以作者nearly identical定性保留。','evidence_ids':['S0001','S0002','S0003','M0054','M0160','M0173']})
d.setdefault('reference_revision_history',[]).append({'date':'2026-10-27','reviewer':'extract_a','audit_file':str((A/'report.json').relative_to(B)),'affected_units':[x['unit_id'] for x in changes],'counts_before':before,'counts_after':after,'missing_before_after':len(d.get('missing',[]))})
save(p,d)
report={'date':'2026-10-27','reviewer':'extract_a','P337':{'counts_before':before,'counts_after':after,'missing_count_unchanged':len(d.get('missing',[])),'changes':changes,'retained':['T/T1/T1R3：两组均2 wt%+LNO-SRF，无确证不同','T/T5/T5R1：作者调膜使总LiNO3相同','T/T6/T6R1：M0173明确作者nearly identical定性，非精确数值方向']},'P548':{'action':'checked_no_change','retained':['T/T1/T1R1：M0036明确comparable capacity retention作者定性；E2/E3混杂在原review已标','T/T7/T7R1：A=E3、B=Ether，均0.2 M LiNO3；M0090/M0091亦直接比较低温容量'],'evidence_ids':['M0036','M0047','M0090','M0091','S0077']}}
assert ph=={pid:sha(B/'independent_predictions'/f'{pid}.json') for pid in ph};report['prediction_hashes_unchanged']=ph;save(A/'report.json',report)
print(json.dumps({'P337_before':before,'P337_after':after,'FN_unchanged':len(d.get('missing',[])),'P548':'unchanged'},ensure_ascii=False))
