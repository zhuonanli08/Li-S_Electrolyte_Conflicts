import json,itertools
from pathlib import Path
R=Path('output/GPT_v4_调试集53篇_2026-10-24/figures')
def finish(pid,notes,terminal=None):
 d=R/pid;t=json.loads((d/'tasks.json').read_text(encoding='utf-8'));detail=[];review=[]
 for a in t:
  p=d/f"{a['编号']}_results.json";res=json.loads(p.read_text(encoding='utf-8'));good=res['status'].startswith('锚点通过');fn=f"核对_{a['编号']}.png"
  res.update(metric=a.get('metric','放电容量'),unit=a.get('unit','mAh g−1'),reader='step8h_c_read_figures.py',request_index=a['request_index'],visual_verified=good)
  if 'request_indices'in a:res['request_indices']=a['request_indices']
  p.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
  detail.append({'file':fn if (d/fn).exists() else None,'task_id':a['编号'],'status':'verified_partial_points' if good else 'unread_final','reason':res.get('reason',res['status']),'accepted_points':{k:[c for c,ok in s.get('points_repeat_consistent',{}).items() if ok and s.get('usable')] for k,s in res.get('series',{}).items()}})
  for ix in a.get('request_indices',[a['request_index']]):review.append({'request_index':ix,'status':'read_partial' if good else 'unread_final','task_id':a['编号'],'result_file':p.name,'metric':res['metric'],'unit':res['unit'],'reason':res.get('reason',res['status']),'evidence_ids':a.get('shared_test_anchor_evidence',[])})
 review.extend(terminal or [])
 vr={'paper_id':pid,'reviewer':'extract_c','date':'2026-10-27','reviewed_overlays':[x['file'] for x in detail if x['file'] and x['status']=='verified_partial_points'],'overlay_details':detail,'notes':notes,'result':'逐图终态已保存；仅使用复核通过的稳定点','scoring_use':'读图补充单独保存，不修改冻结预测或首轮文本评分。'}
 for name,v in [('visual_review.json',vr),('request_review.json',review)]:
  p=d/name;assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
 print(pid,'saved',len(t),'plots',sum(len(v) for x in detail for v in x['accepted_points'].values()),'points')
if __name__=='__main__':
 finish('S19',['Fig5d倍率分段：3/9/15/21/27/35圈分别0.1/0.2/0.3/0.5/1/返回0.1 C，颜色与配方对应已核。','Fig5c上部CE与下部容量分开；90圈E-DD已停止、E-EDD边界取值不稳，留空。','SI原始拆图缺黑色轴字，改用PDF300dpi渲染读S30/S31，未对原位图放大插值。','S30初始1097和70圈76%、S31初始1107和100圈848锚点均通过。'])
 finish('S20',['Fig3a只读下方实心容量点，倍率映射见任务point_conditions；0.1C首圈两组接近，其他倍率不受首圈方向影响。','Fig3d首次发现末段DD的CE落进容量区域，修正一次单独排除CE后，400圈容量只来自下方曲线。','Fig6a灰轴用axis_threshold200仅改善几何识别；170圈851.7与118圈365.7锚点均通过。','图6a含0.03C化成，未把图示首点与0.05C首容量808.4强行对应；DD170圈无曲线留空。'])
 for pid in ['P109','P149','P211','S33','S39','S40','S51']:
  p=R/pid/'tasks.json';t=json.loads(p.read_text(encoding='utf-8'))
  for a in t:
   ids=[c['配方编号'] for c in a['曲线']];a['comparison_pairs']=[list(x) for x in itertools.combinations(ids,2)]
  p.write_text(json.dumps(t,ensure_ascii=False,indent=2),encoding='utf-8')
