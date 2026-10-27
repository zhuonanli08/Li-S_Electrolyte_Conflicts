import json
from pathlib import Path
R=Path('output/GPT_v4_调试集53篇_2026-10-24/figures')
notes={
'P109':['图4左右分别为充电与放电容量，只读右侧放电容量。','自动纵轴首轮把小刻度当主刻度，已用7个主刻度像素纠正；网格逐一贴合标签，最大残差<2像素。','默认蓝/青色容差交叉，已收紧Lab容差25后分离；2.8 M约40圈达最大是峰值位置锚点，程序定位35圈、在半格10圈内。','L28第100圈空心标记无法稳定保留，不补数值；40圈七档均可核。'],
'P149':['a仅比较两条with CS容量曲线，移除上方CE；200圈黑/绿重叠不读，1000圈两条可稳定读取。','e的LS002容量只画至约44圈，h只至约40圈；不填请求的100/56圈对照，分别补同40/35圈。','h沿用e图例，正文图注再次确认相同两配方；红色样本取自已辨识红方形容量线，不取上方CE。','补充语义：图6b CV黑线图例为LS002，红线为TDE with CS，不能把两者当同隔膜条件；本轮未读该图，文本已保留same_conditions不判。'],
'P211':['图3a两条容量曲线位于下方，上方空心点是CE，已排除。','原文800–900 mAh/g over 100 cycles保留为区间锚点，无反造精确值。','50圈灰色对照被绿色曲线遮挡，不补；99圈两组可读，100圈压右边框，未外推。'],
'S33':['图4b五档图例、黑实心/彩色圆点对应正确，各寿命锚点通过；只保留稳定可分离的同圈点。','图7c/d纵轴为比能量Wh/kg，已纠正请求误写容量，按方案允许示例保留原单位，不换算容量。','图7c对照约107圈停止，135圈没有对照；图7d对照约15圈停止，80圈没有对照；读取共同循环。','图7c第50圈黑色被红线遮挡，留空；叠片首圈几何读取TFTFE405.6、DME450.7 Wh/kg，非模型目测。'],
'S39':['请求1和2合并同测试SI图S32容量轴；正文图5d为容量保持率，只用于语义与曲线对应，不当容量轴。','M0159 over 180 cycles保留为寿命下限锚点，程序末端198圈满足下限；不改写成精确180圈寿命。','10圈仅为共同循环读数，不称化成后首圈；55/100圈可比较三档。','180圈F4DEE红点被TTE青点遮挡；DME曲线已停止，留空，不作全组180圈比较。'],
'S40':['图1a/b分别为E/S=23/16；五档图例对应，纵轴容量mAh/g。','厚边框与首圈点扰动端点刻度，唯一修正采用清楚内部主刻度标定，网格检查通过。','M0056高E/S首容量above800只作边界锚点，分别由a的SL-LiTFSI及b的G3-LiTFSI核验，不扩展成各组全部>800。','重叠造成a的SL-LiClO4第99圈、b的G3-LiTFSI50/99圈和G3-LiTF首圈/50圈缺值，均保留空。'],
'S51':['原生200dpi图，没有插值伪提高分辨率；只读下方实心容量标记，上方空心CE剔除。','图例定位修正一次，IL1蓝方、IL2绿三角、IL3红圆对应；首圈1071和约950稳定容量锚点均通过。','50圈压右边框，补49圈三档共同循环；IL2首圈无法稳定取值，留空。']}
summary=[]
for pid,nt in notes.items():
 d=R/pid;tasks=json.loads((d/'tasks.json').read_text(encoding='utf-8'));requests=[];overlays=[];accepted=0
 for t in tasks:
  p=d/f"{t['编号']}_results.json";res=json.loads(p.read_text(encoding='utf-8'));res['metric']=t.get('metric','放电容量');res['unit']=t.get('unit','mAh g−1');res['reader']='step8h_c_read_figures.py' if pid not in ['P149','S51'] else 'step8h_read_figures.py';res['visual_verified']=True;res['request_index']=t['request_index']
  if 'request_indices' in t:res['request_indices']=t['request_indices']
  p.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
  assert res['status'].startswith('锚点通过'),(pid,res['status'])
  stable={fid:[pt for pt,ok in s['points_repeat_consistent'].items() if ok and s['usable']] for fid,s in res['series'].items()};accepted+=sum(map(len,stable.values()))
  overlays.append({'file':f"核对_{t['编号']}.png",'task_id':t['编号'],'status':'verified_partial_points','accepted_points':stable,'max_calibration_residual_px':max(res['calibration']['x'][2]+res['calibration']['y'][2])})
  for ix in t.get('request_indices',[t['request_index']]):requests.append({'request_index':ix,'status':'read_partial','task_id':t['编号'],'result_file':p.name,'metric':res['metric'],'unit':res['unit'],'reason':'锚点/几何/叠图检查通过；仅采用重复取值一致且未遮挡点，不外推缺失组。','evidence_ids':t['shared_test_anchor_evidence']})
 vr={'paper_id':pid,'reviewer':'extract_c','date':'2026-10-27','reviewed_overlays':overlays,'result':'通过部分点；缺失点保留空值','notes':nt,'scoring_use':'读图补充另存；不回写冻结预测或混入首轮文本评分。'}
 for name,obj in [('visual_review.json',vr),('request_review.json',requests)]:
  p=d/name;assert not p.exists(),str(p);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
 summary.append({'paper_id':pid,'requests':len(requests),'plots':len(tasks),'accepted_series_points':accepted})
p=R/'C_group_summary.json';assert not p.exists();p.write_text(json.dumps({'reviewer':'extract_c','papers':summary,'total_requests':sum(x['requests'] for x in summary),'total_plots':sum(x['plots'] for x in summary),'total_accepted_series_points':sum(x['accepted_series_points'] for x in summary),'notes':'每点须结合结果points_repeat_consistent与visual_review使用；未回写首轮冻结预测。'},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(summary,ensure_ascii=False));print('TOTAL',sum(x['accepted_series_points'] for x in summary))
