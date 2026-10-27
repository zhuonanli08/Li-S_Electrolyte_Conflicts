import json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
R=Path('output/GPT_v4_调试集53篇_2026-10-24/figures/S21');img=Image.open(R/'si/image14.png').convert('RGB');a=np.array(img);crop=[560,0,1188,430];a=a[crop[1]:crop[3],crop[0]:crop[2]];yvals=np.array([0,400,800,1200,1600]);ypix=np.array([377,299,221,143,65]);ca,cb=np.polyfit(ypix,yvals,1);res=np.abs(ypix-(yvals-cb)/ca).tolist();series={};im=Image.fromarray(a);dr=ImageDraw.Draw(im)
for y in ypix:dr.line([(143,int(y)),(546,int(y))],fill='orange')
for fid,x,label in [('0DTL',184,1003),('50DTL',264,1105),('60DTL',345,1412),('70DTL',426,1297),('80DTL',506,1284)]:
 color=np.median(a[320:340,x-4:x+5].reshape(-1,3),axis=0);m=(np.linalg.norm(a.astype(float)-color,axis=-1)<35)&(np.indices(a.shape[:2])[0]>=54)&(np.indices(a.shape[:2])[0]<375)
 points=[]
 for w in [9,11]:
  ys=np.nonzero(m[:,x-w//2:x+w//2+1].any(1))[0];points.append(round(float(ca*ys.min()+cb),1) if len(ys) else None)
 passed=all(v is not None for v in points) and abs(points[0]-points[1])<=200
 anchors=[]
 if fid in ['0DTL','60DTL']:
  target=1002 if fid=='0DTL' else 1371;anchors=[{'cycle':1,'value':target,'evidence_id':'M0136','read_value':points[0],'pass':points[0] is not None and abs(points[0]-target)<=200}]
 series[fid]={'legend':fid,'color':color.tolist(),'points':{'1':points[0]},'repeat_points':{'1':points[1]},'points_repeat_consistent':{'1':passed},'anchors':anchors,'usable':passed,'reason':'分类柱位置由标签对应；取柱顶，重复宽度核验','explicit_figure_label':label};dr.line([(x,54),(x,377)],fill='green')
shared=all(z['pass'] for s in series.values() for z in s['anchors']);assert shared and max(res)<2
im.save(R/'核对_S21_FS14b.png')
t={'编号':'S21_FS14b','test_id':'S21-T4','request_index':1,'图':str((R/'si/image14.png').resolve()),'子图':crop,'axis_type':'categorical_bar','x_categories':{'0DTL':184,'50DTL':264,'60DTL':345,'70DTL':426,'80DTL':506},'y刻度':yvals.tolist(),'y_tick_pixels':ypix.tolist(),'取圈':[1],'标记宽':9,'曲线':[{'配方编号':k,'图例原文':k} for k in series],'shared_test_anchor_evidence':['M0136','S0130'],'comparison_pairs':[['60DTL',x] for x in ['0DTL','50DTL','70DTL','80DTL']],'notes':'分类柱状容量图，x为类别，无虚构连续x刻度；y按5个已见数字刻度拟合。取柱顶而非像素中值。'}
r={'id':t['编号'],'test_id':t['test_id'],'source_image':t['图'],'status':'锚点通过；分类柱图柱顶读值','calibration':{'y':[float(ca),float(cb),res],'x_categories':t['x_categories']},'series':series,'shared_test_anchor_evidence':t['shared_test_anchor_evidence']}
(R/'S21_FS14b_results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
# Standard cycling panel S23 only; no cross-test anchor transfer to S20b.
c={'编号':'S21_FS23','test_id':'S21-T11','request_index':3,'图':str((R/'si/image23.png').resolve()),'子图':[0,0,1269,507],'x刻度':[0,100,200,300,400,500,600],'y刻度':[0,200,400,600,800,1000,1200],'标记宽':15,'取圈':[1,400,600],'排除':[[0,0,1269,105],[715,111,1090,183],[200,355,820,408]],'shared_test_anchor':True,'shared_test_anchor_evidence':['M0204','M0205','S0154'],'comparison_pairs':[['60DTL','0DTL']],'曲线':[{'配方编号':'60DTL','图例原文':'60DTL with 1 wt% LiNO3','类型':'color','图例框':[744,160,767,179],'anchors':[{'cycle':600,'value':639,'evidence_id':'M0205'}]},{'配方编号':'0DTL','图例原文':'0DTL with 1 wt% LiNO3','类型':'color','图例框':[744,122,767,141],'anchors':[]}],'notes':'只读S23同图；S20b没有独立数字锚点，不用S23数字代替。'}
(R/'tasks.json').write_text(json.dumps([t,c],ensure_ascii=False,indent=2),encoding='utf-8');(R/'tasks_cycling.json').write_text(json.dumps([c],ensure_ascii=False,indent=2),encoding='utf-8')
print({k:v['points'] for k,v in series.items()})
