import json
from pathlib import Path
R=Path('output/GPT_v4_调试集53篇_2026-10-24/figures')
def put(pid,t):
 p=R/pid/'tasks.json';assert not p.exists();p.write_text(json.dumps(t,ensure_ascii=False,indent=2),encoding='utf-8')
def task(pid,id,test,req,img,crop,x,y,w,cycles,excl,curves,ev):return {'编号':id,'test_id':test,'request_index':req,'图':str((R/pid/img).resolve()),'子图':crop,'x刻度':x,'y刻度':y,'标记宽':w,'取圈':cycles,'排除':excl,'曲线':curves,'shared_test_anchor':True,'shared_test_anchor_evidence':ev}
def c(fid,label,box=None,anchors=[],kind='color',**kw):
 d={'配方编号':fid,'图例原文':label,'类型':kind,'anchors':anchors,**kw}
 if box:d['图例框']=box
 return d
curves=[]
for fid,label,y in [('L01','0.1 M 红方',79),('L05','0.5 M 蓝三角',125),('L1','1.0 M 黑菱',171),('L15','1.5 M 绿方',217),('L2','2.0 M 紫方',264),('L24','2.4 M 青圆',310),('L28','2.8 M 品红方',356)]:
 a=[{'type':'maximum_cycle','cycles':list(range(2,111)),'value':40,'evidence_id':'M0094'}] if fid=='L28' else []
 curves.append(c(fid,label,[685,y-7,705,y+7],a,kind='black' if fid=='L1' else 'color'))
put('P109',[task('P109','P109_F4','P109-T1',1,'main/p6_render300.png',[1250,300,2300,1250],list(range(1,202,20)),list(range(0,1201,200)),9,[40,100],[[640,50,900,380]],curves,['M0094','M0134'])])
put('P211',[task('P211','P211_F3a','P211-T1',1,'main/p4_xref146.png',[0,0,750,625],list(range(0,101,20)),[0,400,800,1200,1600],13,[50,99],[[0,0,750,155],[260,360,600,430],[160,470,610,530]],[c('RTN','0.8 M LiTFSI + 0.2 M NH4TFA 绿六角',[180,503,197,520],[{'type':'value_range','cycle':99,'range':[800,900],'evidence_id':'M0123'}]),c('RT0','1 M LiTFSI 灰六角',kind='gray',gray_range=[20,130])],['M0123'])])
curves=[]
for fid,label,y,life in [('DME','DME 黑实圆',255,36),('ETFE','DME-ETFE 金圆',291,32),('BTFE','DME-BTFE 橙圆',328,131),('TFTFE','DME-TFTFE 红圆',364,154),('TFOFE','DME-TFOFE 紫圆',401,31)]:
 curves.append(c(fid,label,[208,y-5,217,y+5],[{'type':'lifetime','value':life,'evidence_id':'M0172'}],kind='black' if fid=='DME' else 'color'))
put('S33',[task('S33','S33_F4b','S33-T1',1,'main/p9_xref196.png',[0,475,830,988],[0,40,80,120,160],[0,300,600,900,1200],9,[10,30,100],[[195,237,700,414]],curves,['M0172'])])
put('S39',[task('S39','S39_FS32','S39-T1',1,'si/p36_render300.png',[280,330,1850,1080],list(range(0,201,20)),list(range(0,1201,200)),15,[10,55,100,180],[[0,0,1570,205],[1040,440,1340,590],[370,430,820,590]],[c('DOL_DME','DOL/DME 灰实圆',kind='gray',gray_range=[20,140]),c('DOL_F4DEE','DOL/F4DEE 红实圆',[1071,512,1090,530],[{'type':'minimum_lifetime','value':180,'evidence_id':'M0159'}]),c('DOL_TTE','DOL/TTE 青实圆',[1071,559,1090,575])],['M0148','M0159','S0078'])])
# Fig.1a and b; same-test lower-bound anchor is kept as a lower bound.
ss=[]
for req,crop in [(1,[0,0,1030,650]),(2,[1030,0,2029,650])]:
 curves=[]
 for fid,label,j in [('SL_LiTFSI','SL-LiTFSI 金圆',0),('SL_LiTF','SL-LiTF 深红圆',1),('SL_LiClO4','SL-LiClO4 绿圆',2),('G3_LiTFSI','G3-LiTFSI 紫圆',3),('G3_LiTF','G3-LiTF 蓝圆',4)]:
  xx=785 if req==1 else 810;yy=(82 if req==1 else 87)+25*j
  a=[{'type':'minimum_value','cycle':1,'value':800,'evidence_id':'M0056'}] if fid==('SL_LiTFSI' if req==1 else 'G3_LiTFSI') else []
  curves.append(c(fid,label,[xx-7,yy-7,xx+7,yy+7],a))
 ss.append(task('S40',f'S40_F1{chr(96+req)}',f'S40-T{req}',req,'main/p3_xref91.png',crop,list(range(0,101,10)),list(range(0,901,100)),13,[1,50,99],[[735 if req==1 else 770,60,990,200]],curves,['M0056','M0072']))
put('S40',ss)
