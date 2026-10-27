import json
from pathlib import Path

B=Path('output/GPT_v4_调试集53篇_2026-10-24')
def save(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read(p): return json.loads(p.read_text(encoding='utf-8'))

reviews=[
 (1,'out_of_scope',None,'纯梯度CE/最低电压不属本轮循环容量补读。'),
 (2,'read','S18_F6B','实心容量方块、顶部空心CE和下方插图已分开。首圈1269锚点通过；收窄取点宽度后报告实际图面第1、14、159圈，避免失效转折处相邻圈及CE污染；缺失PP后期容量留空。'),
 (3,'out_of_scope',None,'纯梯度CE/最低电压不属本轮循环容量补读。'),
 (4,'read','S18_FS57','重新渲染SI页后轴线及图例可核；TiN寿命120圈锚点读得119.9圈通过，共享于同测试独立辨色的PP容量曲线。报告第1、7、8、119圈，PP后期缺失留空；CE已屏蔽。'),
 (5,'out_of_scope',None,'纯梯度CE/最低电压不属本轮循环容量补读。'),
 (6,'partial','S18_FS58','重新渲染后容量曲线与CE已核验分开；正文114稳定圈锚点与程序曲线末端120圈差6圈，小于横轴半格15圈，但图尾含失效阶段，不能把末端120改写为114。仅报告失效前第1、23、24、113圈；PP后期留空。该锚点的阶段边界不完全一致，保留此限制供汇总筛选。'),
 (7,'read','S18_FS60B','S60B循环容量实心粉色方块与CE分开；100圈寿命锚点读得101.1圈通过。报告图面第1、20、99圈；S60A另一次首放电1343不得替代B面板首圈。'),
 (8,'unread','S18_FS61B','首次图例框误取相邻蓝色能量密度点，已在视觉核验时拒绝。修正为真实浅粉色容量标记后，固定颜色过滤器无法识别，最终结果为仅图未读且无数值；旧核对图属于已否决尝试，不可使用。'),
 (9,'unread','S18_FS62B','真实浅粉色容量标记无法通过固定颜色过滤器，结果为仅图未读。蓝色方块为能量密度，不能代替容量；未目测补数。'),
 (10,'unread','S18_FS63','重新渲染仍无法从真实浅粉色容量标记取得有效颜色，结果为仅图未读。蓝色能量密度点已排除，1403容量锚点无法核验，未目测补数。'),
]
req=read(B/'independent_predictions/S18.json')['figure_requests']
save(B/'figures/S18/request_review.json',[dict(request_index=i,status=status,task_id=tid,reason=reason,evidence_ids=req[i-1]['anchor_quote_ids']) for i,status,tid,reason in reviews])
save(B/'figures/S18/visual_review.json',dict(paper_id='S18',reviewer='extract_b',date='2026-10-27',
 reviewed_overlays=['核对_S18_F6B.png','核对_S18_FS57.png','核对_S18_FS58.png','核对_S18_FS60B.png'],
 result='Fig6B、S57、S58、S60B的轴刻度、图例配色及容量实心方块已核验，顶部CE及插图已排除。S58正文114稳定圈与含失效尾部的曲线末端120圈属于近似边界，仅保留第113圈及以前的目标值并注明限制。S61B首轮误取蓝色能量点的核对图已否决；修正后最终结果无容量值。S62B和S63也因浅粉色容量点无法通过固定过滤器而保留仅图未读。',
 invalidated_overlays=[dict(file='核对_S18_FS61B.png',reason='首次误取蓝色能量密度点；最终_results.json已替换为仅图未读，此旧图不得参与数据汇总。')],
 scoring_use='读图补充独立，不回写冻结预测或初轮文本评分。'))

pairs={
 'S10_F4a':[['LiBr','LiTFSI'],['LiSCN','LiTFSI'],['LiSCN','LiBr']],
 'S10_F4d':[['LiBr','LiTFSI'],['LiSCN','LiTFSI'],['LiSCN','LiBr']],
 'S10_F4e':[['LiBr','LiTFSI'],['LiSCN','LiTFSI'],['LiSCN','LiBr']],
 'S11_F5A':[['10HFE','0HFE'],['30HFE','0HFE'],['30HFE','10HFE']],
 'S11_F5C':[['10HFE','0HFE'],['30HFE','0HFE'],['30HFE','10HFE']],
 'S11_F6B':[],
 'S15_FS39':[['LiFSI','LiTFSI']], 'S15_F4b':[['LiFSI','LiTFSI']], 'S15_F4e':[],
 'S16_F5a':[['DD_HMPA','DD'],['DD_DMSO','DD'],['DD_HMPA','DD_DMSO']],
 'S16_F5c':[['DD_HMPA','DD_DMSO']], 'S16_F5e':[['DD_HMPA','DD']], 'S16_F6d':[['DD_HMPA','DD']],
 'S18_F6B':[['DIPS35+TiN','DIPS35+PP']], 'S18_FS57':[['DIPE35+TiN','DIPE35+PP']], 'S18_FS58':[['HME35+TiN','HME35+PP']],
 'S18_FS60B':[], 'S18_FS61B':[], 'S18_FS62B':[], 'S18_FS63':[]
}
for pid in ['S10','S11','S15','S16','S18']:
 path=B/'figures'/pid/'tasks.json'; tasks=read(path)
 for t in tasks:
  t['metric']='同圈容量' if t['编号']=='S16_F6d' else '同圈比容量'
  t['unit']='Ah' if t['编号']=='S16_F6d' else 'mAh g−1'
  t['comparison_pairs']=pairs[t['编号']]
 save(path,tasks)

summary=[]
for pid in ['S10','S11','S15','S16','S18']:
 fd=B/'figures'/pid;tasks=read(fd/'tasks.json');rv=read(fd/'request_review.json');v=read(fd/'visual_review.json')
 n=len(read(B/'independent_predictions'/f'{pid}.json')['figure_requests'])
 assert sorted(r['request_index'] for r in rv)==list(range(1,n+1)),pid
 assert len({t['编号'] for t in tasks})==len(tasks),pid
 for f in v['reviewed_overlays']: assert (fd/(f['file'] if isinstance(f,dict) else f)).exists(),f
 usable=failed=points=0
 for t in tasks:
  d=read(fd/(t['编号']+'_results.json'))
  ok=any(s.get('usable') for s in d.get('series',{}).values())
  usable+=int(ok);failed+=int(not ok)
  for s in d.get('series',{}).values():
   if s.get('usable'):points+=sum(v is not None and s['points_repeat_consistent'].get(k,False) for k,v in s['points'].items())
 summary.append(dict(paper_id=pid,requests=n,tasks=len(tasks),usable_figures=usable,failed_figures=failed,usable_points=points,statuses={s:sum(x['status']==s for x in rv) for s in sorted({x['status'] for x in rv})}))
save(B/'figures/agent_b_completion.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
