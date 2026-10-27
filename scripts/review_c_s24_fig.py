import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,'scripts');import step6e_figure_read_trial as old
R=Path('output/GPT_v4_调试集53篇_2026-10-24/figures/S24');TASKS=[]
def panel(num,test,req,fn,crop,yticks,ypix,positions,curves,excl,ev,unit='mAh g−1',metric='放电容量',xinfo=None,notes='',pairs=None):
 img=old.load(str(R/fn),crop);frame=old.v3.找坐标框(img);ypix=np.array(ypix,float);yticks=np.array(yticks,float);cy=np.polyfit(ypix,yticks,1);res=np.abs(ypix-(yticks-cy[1])/cy[0]).tolist();assert len(yticks)>=3 and max(res)<2
 half=float(min(np.diff(sorted(yticks)))/2);im=Image.fromarray(img);dr=ImageDraw.Draw(im);series={};prec=3 if unit=='Ah' else 1
 for y in ypix:dr.line([(frame[0],float(y)),(frame[1],float(y))],fill='orange')
 for key,x in positions.items():dr.line([(x,frame[2]),(x,frame[3])],fill='orange')
 for fid,box,anchors in curves:
  color=old.v3.取图例色(img,box);mask=old.series_mask(img,frame,'color',color,excl);values=[]
  for w in [13,15]:
   vals={}
   for point,x in positions.items():
    x=int(round(x));ys=np.nonzero(mask[:,max(0,x-w//2):x+w//2+1].any(1))[0];vals[str(point)]=None if not len(ys) else round(float(cy[0]*np.median(ys)+cy[1]),prec)
   values.append(vals)
  a=[]
  for anc in anchors:
   val=values[0].get(str(anc['point']));target=anc['value']
   if anc.get('type')=='retention':target=values[0].get(str(anc['initial_point']))*anc['ratio'] if values[0].get(str(anc['initial_point'])) is not None else None
   a.append({**anc,'expected_value':target,'read_value':val,'tolerance':half,'pass':val is not None and target is not None and abs(val-target)<=half})
  series[fid]={'legend':fid,'color':color.tolist(),'points':values[0],'repeat_points':values[1],'points_repeat_consistent':{p:v is not None and values[1][p] is not None and abs(v-values[1][p])<=half for p,v in values[0].items()},'anchors':a,'usable':False}
  yy,xx=np.nonzero(mask)
  for x,y in zip(xx[::5],yy[::5]):dr.point((int(x),int(y)),fill='green')
 given=[a for s in series.values() for a in s['anchors']];valid=bool(given) and all(a['pass'] for a in given)
 for s in series.values():s['usable']=valid and any(s['points_repeat_consistent'].values());s['reason']='同测试锚点和重复读取通过' if s['usable'] else '锚点或取值未通过'
 ok=all(s['usable'] for s in series.values())
 if not ok:
  for s in series.values():s['usable']=False
 t={'编号':num,'test_id':test,'request_index':req,'图':str((R/fn).resolve()),'子图':crop,'metric':metric,'unit':unit,'y刻度':yticks.tolist(),'y_tick_pixels':ypix.tolist(),'point_pixels':positions,'取圈':list(positions),'标记宽':13,'排除':excl,'曲线':[{'配方编号':fid,'图例原文':fid,'图例框':box,'anchors':anc} for fid,box,anc in curves],'shared_test_anchor':True,'shared_test_anchor_evidence':ev,'comparison_pairs':pairs or [],'axis_semantics':xinfo,'notes':notes}
 TASKS.append(t);result={'id':num,'test_id':test,'source_image':t['图'],'status':'锚点通过；仅使用points_repeat_consistent为true的点' if ok else '仅图未读：锚点或取值未通过','calibration':{'y':[float(cy[0]),float(cy[1]),res],'x_semantics':xinfo},'frame':[int(x) if x is not None else None for x in frame],'series':series,'shared_test_anchor_evidence':ev,'metric':metric,'unit':unit}
 for b in excl:dr.rectangle(b,outline='gray')
 im.save(R/f'核对_{num}.png');(R/f'{num}_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(num,result['status'],{k:s['points'] for k,s in series.items()})
# Fig3d logarithmic C-rate axis: calibrate the actual three labeled logarithmic ticks.
xvals=np.array([.1,1,10]);xp=np.array([219,447,675]);xa,xb=np.polyfit(xp,np.log10(xvals),1);rates=[.1,.3,.5,1,5];positions={str(v):float((np.log10(v)-xb)/xa) for v in rates}
panel('S24_F3d','S24-T4',1,'main/p4_xref107.png',[660,550,1359,1130],[0,200,400,600,800,1000,1200],[487,416,345,274,203,132,61],positions,[('MAN',[441,83,459,99],[{'point':5,'value':416,'evidence_id':'M0077'}]),('DD',[441,116,459,133],[{'point':5,'value':187,'evidence_id':'M0076'}]),('G2',[441,150,459,167],[{'point':1,'value':85,'evidence_id':'M0075'}])],[[415,74,670,174]],['M0075','M0076','M0077'],xinfo={'type':'log10','labels':xvals.tolist(),'tick_pixels':xp.tolist(),'calibration':[float(xa),float(xb)],'point_unit':'C'},notes='只在同一C-rate比较；x轴为对数，先用0.1/1/10三标定再求各倍率横坐标，未误用线性轴。',pairs=[['MAN','DD'],['MAN','G2']])
# Fig5b E/S labels are categorical equally spaced; each condition retains its own test ID.
for req,test,es,x,target in [(2,'S24-T5',10,215,1038),(3,'S24-T6',5,370,1043),(4,'S24-T7',3,526,1070),(5,'S24-T8',2,682,1094)]:
 panel(f'S24_F5b_ES{es}',test,req,'main/p6_xref145.png',[820,0,1583,610],list(range(0,1401,200)),[484,423,361,300,239,178,117,56],{str(es):x},[('MAN',[470,109,488,126],[{'point':es,'value':target,'evidence_id':'M0099'}]),('DD',[470,74,488,91],[])],[[442,64,735,129]],['M0099','M0100','M0154'],xinfo={'type':'categorical','condition':'E/S','unit':'μL mg−1','category':es,'pixel':x},notes='同E/S两配方点图；横坐标等距类别10/5/3/2，不把类别间距当连续数值线性拟合。',pairs=[['MAN','DD']])
# Fig5d porosity is a descending continuous axis; named target marker positions verified visually.
for req,test,po,x,target in [(6,'S24-T9',80,181,1066),(7,'S24-T10',72,323,1060),(8,'S24-T11',63,483,1063),(9,'S24-T12',52,679,958)]:
 panel(f'S24_F5d_P{po}',test,req,'main/p6_xref145.png',[820,610,1583,1210],list(range(0,1401,200)),[481,420,359,298,237,176,115,54],{str(po):x},[('MAN',[485,112,503,130],[{'point':po,'value':target,'evidence_id':'M0103'}]),('DD',[485,78,503,96],[])],[[458,69,742,132]],['M0103','M0154'],xinfo={'type':'descending_porosity','unit':'%','target':po,'pixel':x,'ticks':[80,75,70,65,60,55,50],'tick_pixels':[181,270,359,448,537,626,715]},notes='同孔隙率同图配对；分别独立测试，不与不同孔隙率点混比。',pairs=[['MAN','DD']])
# Single-formulation cycling panels: retain values, no synthetic A/B pair.
panel('S24_F5g','S24-T13',10,'main/p6_xref145.png',[0,1540,810,2118],list(range(0,1601,200)),[489,436,383,329,276,223,169,116,63],{'1':127.46,'25':426.5,'50':738},[('MAN',[330,279,380,305],[{'point':1,'value':907,'evidence_id':'M0110'},{'type':'retention','point':50,'initial_point':1,'ratio':.72,'value':None,'evidence_id':'M0110'}])],[],['M0110','M0155'],xinfo={'type':'linear_cycle','ticks':[0,10,20,30,40,50],'tick_pixels':[115,240,364,489,614,738]},notes='只读单配方严苛条件容量曲线，不构造对照方向。')
panel('S24_F5h','S24-T14',11,'main/p6_xref145.png',[820,1540,1583,2118],[0,.5,1,1.5,2],[486,380,274,168,61],{str(i):166+(i-1)*(556/9) for i in range(1,11)},[('MAN',[158,238,176,256],[{'point':1,'value':1.13,'evidence_id':'M0113'}])],[],['M0113','M0114','M0115','M0155'],unit='Ah',xinfo={'type':'linear_cycle','ticks':[1,2,3,4,5,6,7,8,9,10],'point_unit':'cycle'},notes='纵轴Ah，保留3位小数；图内明确1–2圈33.5 mA g−1，3–10圈50 mA g−1，补正正文高电流截断。单配方不同倍率不生成A/B。')
p=R/'tasks.json';assert not p.exists();p.write_text(json.dumps(TASKS,ensure_ascii=False,indent=2),encoding='utf-8')
