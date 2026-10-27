import json
from pathlib import Path
R=Path('output/GPT_v4_调试集53篇_2026-10-24/figures')
def col(fid,box,anchors=[],kind='color',**kw):return {'配方编号':fid,'图例原文':fid,'类型':kind,'图例框':box,'anchors':anchors,**kw}
def base(pid,num,test,req,img,crop,x,y,w,cycles,excl,curves,ev,**kw):
 return {'编号':num,'test_id':test,'request_index':req,'图':str((R/pid/img).resolve()),'子图':crop,'x刻度':x,'y刻度':y,'标记宽':w,'取圈':cycles,'排除':excl,'曲线':curves,'shared_test_anchor':True,'shared_test_anchor_evidence':ev,'comparison_pairs':[['E-PDD','E-EDD'],['E-PDD','E-DD']],**kw}
def save(pid,t):
 p=R/pid/'tasks.json';assert not p.exists();p.write_text(json.dumps(t,ensure_ascii=False,indent=2),encoding='utf-8')
g=lambda:[col('E-PDD',[135,236,220,255]),col('E-EDD',[135,268,225,288]),col('E-DD',None,kind='gray',gray_range=[80,180])]
t=[]
c=g();c[0]['anchors']=[{'cycle':3,'value':1313,'evidence_id':'M0112'},{'cycle':27,'value':1004,'evidence_id':'M0112'}]
t.append(base('S19','S19_F5d','S19-T6',2,'main/p6_xref269.png',[970,420,1500,830],[0,10,20,30],[0,400,800,1200,1600],9,[3,9,15,21,27,35],[[130,233,230,326],[250,65,435,145],[340,165,380,185]],c,['M0111','M0112'],x_tick_pixels=[118,208,298,388],y_tick_pixels=[332,262,192,121,50],point_conditions={'3':'0.1 C','9':'0.2 C','15':'0.3 C','21':'0.5 C','27':'1 C','35':'返回0.1 C'}))
c=[col('E-PDD',[397,131,520,151],[{'cycle':1,'value':1106,'evidence_id':'M0115'},{'type':'retention','cycle':90,'initial_cycle':1,'ratio':.92,'evidence_id':'M0115'}]),col('E-EDD',[397,181,520,205]),col('E-DD',None,kind='gray',gray_range=[80,175])]
t.append(base('S19','S19_F5c','S19-T8',4,'main/p6_xref269.png',[0,415,900,835],[0,30,60,90],[0,400,800,1200,1600],13,[1,80,90],[[0,0,900,115],[395,128,530,151],[395,178,530,205],[395,249,530,285],[140,291,365,332],[560,290,760,330],[705,137,765,165],[708,185,765,215]],c,['M0115','S0148'],x_tick_pixels=[128,343,560,775],y_tick_pixels=[336,273,211,148,86]))
c=[col('E-PDD',[657,180,770,207],[{'cycle':1,'value':1097,'evidence_id':'M0116'},{'type':'retention','cycle':70,'initial_cycle':1,'ratio':.76,'evidence_id':'M0116'}]),col('E-EDD',[657,255,770,282]),col('E-DD',None,kind='gray',gray_range=[70,185])]
t.append(base('S19','S19_FS30','S19-T9',5,'si/p25_render300.png',[360,1300,1500,1830],[0,20,40,60],[0,400,800,1200,1600],15,[1,60,69],[[0,0,1140,145],[655,180,780,209],[650,255,790,282],[652,320,780,348],[900,185,985,225],[900,267,985,311],[900,374,985,408],[235,372,580,409]],c,['M0116','S0149'],x_tick_pixels=[212,435,658,880],y_tick_pixels=[417,341,265,189,113],notes='原生拆图缺黑色坐标文字，改PDF300dpi渲染还原，未插值原位图。'))
c=[col('E-PDD',[740,173,850,199],[{'cycle':1,'value':1107,'evidence_id':'M0120'},{'cycle':100,'value':848,'evidence_id':'M0120'}]),col('E-EDD',[756,234,857,260]),col('E-DD',None,kind='gray',gray_range=[70,185])]
t.append(base('S19','S19_FS31','S19-T12',6,'si/p25_render300.png',[370,2280,1510,2770],[0,20,40,60,80,100],[0,400,800,1200,1600],15,[1,50,99],[[0,0,1140,115],[738,170,860,200],[755,232,865,260],[775,304,850,334],[875,171,955,201],[875,237,955,268],[880,312,955,346],[210,345,850,390]],c,['M0120','S0150'],x_tick_pixels=[214,366,518,670,822,974],y_tick_pixels=[397,314,230,147,64],notes='原生拆图缺坐标，改PDF300dpi渲染；只读容量实心圆。'))
save('S19',t)
