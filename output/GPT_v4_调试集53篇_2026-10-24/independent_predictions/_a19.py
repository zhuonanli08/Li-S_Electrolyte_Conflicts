from _author_a import *
p=paper('S19');p['control_id']='E-DD';p['control_type']='1 M LiTFSI + 0.4 M LiNO3 in DOL/DME；另设DMEU高给体对照'
for k,co in [('E-DD',None),('E-EDD','DMEU'),('E-PDD','DMPU')]:
 cs=[('LiTFSI','盐',1,'M'),('LiNO3','添加剂',0.4,'M'),('DOL','溶剂',4 if co else 1,'体积份'),('DME','溶剂',4 if co else 1,'体积份')]
 if co:cs.append((co,'溶剂',2,'体积份'))
 form(p,k,k,cs,'1.0 M LiTFSI + 0.4 M LiNO3; '+('DOL/DME 1:1' if not co else co+'/DOL/DME 2:4:4')+' v/v','S0016 M0081')
grad(p,'环状脲溶剂对照',['E-DD','E-EDD','E-PDD'],['无脲','五元DMEU','六元DMPU'],'Li+和LiPS内层配位增强；DD混合壳层→EDD混合壳层→DMPU主导','M0055 M0058 M0059 M0060 M0067 M0071')
prop(p,'离子电导率',{'E-PDD':11.3,'E-EDD':10.3,'E-DD':8.5},'PDD>EDD>DD','离子电导测量，mS cm−1','工作电解液','S0087')
prop(p,'Li2S溶解度',{'E-PDD':0.55,'E-EDD':0.25,'E-DD':'极低'},'PDD>EDD>DD','溶解测试，mM','PDD/EDD/DD溶剂；非完整工作配方','S0100 S0103 S0105 S0109')
prop(p,'LiPS溶剂化结构',{'E-PDD':'DMPU主导内层，DOL/DME外层','E-EDD':'DMEU/DME混合内层，部分DMEU自由','E-DD':'DME/DOL内层'},'PDD内层高DN配位更强','Raman/NMR/MD','0.1 M Li2S6；MD另含1 M LiTFSI','M0062 M0063 M0066 M0067 M0070 M0071 M0072 S0054')
fs=['E-PDD','E-EDD','E-DD']
t=test(p,'Li对称循环','Li‖Li',fs,'S0035 S0036 S0037 S0038 M0081 M0103',rate='1 mA cm−2; 1 mAh cm−2',LiNO3='0.4 M',formation='Li预保护人工SEI，方法引用前文',electrolyte_volume='40 μL')
for b,v in [('E-EDD',800),('E-DD',1000)]:result(t,'稳定循环时间','E-PDD',b,'>1400',v,'h','极化显著上升前','M0081 M0082 M0083 M0084')
for b in fs[1:]:result(t,'Li表面','E-PDD',b,'光滑均匀','裂纹/多孔苔藓状',None,'400 h','M0085 M0086',basis='qualitative',direction='变好')
tl=test(p,'Tafel交换电流','Li‖Li',fs,'S0039 M0087',rate='−0.2~0.2 V; 0.5 mV s−1',LiNO3='0.4 M')
for b,v in [('E-EDD',0.42),('E-DD',0.12)]:result(tl,'交换电流密度','E-PDD',b,0.52,v,'mA cm−2','Tafel','M0087')
td=test(p,'Li2S沉积','Li‖Li2S8',fs,'S0022 S0023 S0024 S0092 S0093 S0094',rate='0.112 mA至2.12 V，2.05 V恒电位至<0.01 mA',LiNO3='方法S0023未写；结果S0092写0.4 M',catholyte='0.2 M Li2S8')
for b,v in [('E-EDD',408),('E-DD',365)]:result(td,'Li2S沉积容量','E-PDD',b,543,v,'mAh g−1','恒电位终点','S0099')
for b,v in [('E-EDD','3DP岛状颗粒'),('E-DD','2DI致密膜')]:result(td,'Li2S形貌','E-PDD',b,'3DI多孔3D',v,None,'沉积后','S0100 S0102 S0103 S0105',basis='qualitative',direction='变好')
tu=test(p,'Li2S溶解','Li‖Li2S8',fs,'S0026 S0120 S0121',rate='放电至1.7 V；0.112 mA充至2.35 V，2.35 V 20 h')
for b in fs[1:]:result(tu,'Li2S溶解容量','E-PDD',b,956,None,'mAh g−1','20 h','S0121',basis='qualitative',direction='变好')
fig(p,tu,'S19','si','Li2S溶解容量','E-PDD','E-EDD/E-DD','20 h','S0026 S0120 S0121')
c=dict(sulfur_loading='约1.4 mg cm−2',ES=19,ES_unit='μL mgS−1',LiNO3='0.4 M',formation='Li预保护人工SEI',one_C='1675 mA g−1',voltage='1.7–2.8 V')
t01=test(p,'Li2S6低倍率循环','Li‖Li2S6 coin',fs,'S0029 S0035 S0039 S0042 M0094 M0095',rate='0.1 C',**c)
for b,v,low in [('E-EDD',1164,785),('E-DD',964,577)]:
 result(t01,'初始容量','E-PDD',b,1403,v,'mAh g−1','初始','M0094');result(t01,'低平台容量','E-PDD',b,937,low,'mAh g−1','初始','M0097');result(t01,'循环寿命','E-PDD',b,'135圈仍1079 mAh g−1','130圈内失效',None,'循环','M0095',basis='qualitative',direction='变好')
result(t01,'容量保持率','E-PDD',None,77,None,'%','135圈','M0095',same=None)
tr=test(p,'倍率性能','Li‖Li2S6 coin',fs,'M0111 M0112 M0113 S0146 S0039 S0029',rate='0.1/0.2/0.3/0.5/1 C',**c)
for rate,v in zip([0.1,0.2,0.3,0.5,1],[1313,1244,1203,1149,1004]):
 for b in fs[1:]:result(tr,'倍率容量','E-PDD',b,v,None,'mAh g−1',str(rate)+' C','M0112',basis='qualitative',direction='变好')
fig(p,tr,'5d','main','倍率容量','E-PDD','E-EDD/E-DD','0.1/0.2/0.3/0.5/1 C','M0111 M0112')
for rate,ev,figure,cap,ret,n in [(0.3,'S0144 M0100','S26',None,None,50),(0.5,'M0114 M0115 S0148','5c',1106,92,90),(1,'M0116 S0149','S30',1097,76,70)]:
 tx=test(p,'Li2S6循环 '+str(rate)+' C','Li‖Li2S6 coin',fs,ev+' S0039 S0029',rate=str(rate)+' C',**c)
 if cap:result(tx,'初始容量','E-PDD',None,cap,None,'mAh g−1','初始',ev,same=None);result(tx,'容量保持率','E-PDD',None,ret,None,'%',str(n)+'圈',ev,same=None)
 if rate==0.3:
  for b in fs[1:]:result(tx,'电极形貌','E-PDD',b,'均匀3D硫/平整Li','不均匀或2D硫/裂纹Li',None,'50圈','M0101 M0108 M0109',basis='qualitative',direction='变好')
 fig(p,tx,figure,'main' if figure=='5c' else 'si','同圈容量/保持率','E-PDD','E-EDD/E-DD',str(n)+'圈',ev)
ts=test(p,'穿梭常数','Li‖Li2S6 coin',fs,'S0045 S0137 S0139',rate='0.1 C',**c)
for b,v in [('E-EDD',0.079),('E-DD',0.128)]:result(ts,'穿梭常数','E-PDD',b,0.039,v,'h−1','充放电曲线计算','S0139')
tc=test(p,'无硝酸锂穿梭电流','Li‖Li2S6 coin',fs,'S0050 S0051 S0052 S0140 S0142',rate='2.9→2.2 V阶梯恒电位',LiNO3='无',sulfur_loading='约1.4 mg cm−2',ES=19,ES_unit='μL mgS−1')
for b,v in [('E-EDD',0.022),('E-DD',0.036)]:result(tc,'平均穿梭电流','E-PDD',b,0.017,v,'mA cm−2','阶梯均值','S0142')
for load,es,rate,cap,ret,n,ev,figure,b in [(2.1,12.8,0.1,1107,None,100,'M0119 M0120 M0121 S0150','S31','E-EDD/E-DD'),(4.4,5.0,0.1,876,82,80,'M0122 M0123 M0127 S0172','5e','E-DD'),(8.2,3.8,0.05,1024,91,25,'M0124 M0128 M0130 S0172','5f',None)]:
 tx=test(p,'CNT/S循环 '+str(load)+' mg cm−2','Li‖S coin',['E-PDD']+([] if b is None else b.split('/')),ev+' S0035',sulfur_loading=str(load)+' mg cm−2',ES=es,ES_unit='μL mgS−1',rate=str(rate)+' C',LiNO3='0.4 M',formation='Li预保护人工SEI')
 result(tx,'初始容量','E-PDD',None,cap,None,'mAh g−1','初始',ev,same=None)
 if ret:result(tx,'容量保持率','E-PDD',b,ret,23 if load==4.4 else None,'%',str(n)+'圈',ev,same=True if b else None)
 if load==2.1:result(tx,'循环容量','E-PDD',None,848,None,'mAh g−1','100圈',ev,same=None);fig(p,tx,figure,'si','同圈容量','E-PDD',b,'首圈、100圈',ev)
 if load==8.2:result(tx,'面容量','E-PDD',None,8.4,None,'mAh cm−2','初始',ev,same=None)
tp=test(p,'单层软包','Li‖S pouch',['E-PDD'],'M0131 M0132 M0133 S0154',sulfur_loading='4.6 mg cm−2',ES=4.4,ES_unit='μL mgS−1',Li_thickness='50 μm',rate='0.18 mA cm−2',LiNO3='0.4 M')
for met,v,u,pt in [('容量',877,'mAh g−1','初始'),('能量密度',238,'Wh kg−1','初始'),('容量保持率',80,'%','20圈')]:result(tp,met,'E-PDD',None,v,None,u,pt,'M0132 M0133',same=None)
mech(p,'DMPU主导内层稳定S3自由基并诱导多孔3D Li2S，促进硫利用；DMEU较低Li2S溶解导致渐进不均匀沉积，DD则提前膜状钝化','E-PDD','E-DD/E-EDD','LiPS溶剂化/Li2S溶解',['正极反应'],'M0098 S0100 S0102 S0103 S0105 S0114 S0117 S0118',[td,tu,t01,tr],side='强侧')
mech(p,'DMPU六元环较小环应变降低对Li的本征反应性','E-PDD','E-EDD','环结构',['负极锂','电解液消耗'],'M0089 M0090 M0137',[t],side='强侧')
mech(p,'强Li+配位减少自由DMPU，动力学上减少与锂接触及副反应；自由DMEU则持续消耗Li生成死锂','E-PDD','E-EDD','Li+溶剂化',['负极锂','电解液消耗'],'M0082 M0091 S0088',[t,t01],side='强侧')
mech(p,'高电导与快速Li+输运降低局部浓差并抑制枝晶','E-PDD','E-DD/E-EDD','离子传输',['负极锂'],'M0087 S0087',[t,tl],side='强侧')
mech(p,'DMPU加快LiPS转化缩短其迁往隔膜的时间；内层DMPU与外层DOL/DME包裹结构抑制随机迁移','E-PDD','E-DD/E-EDD','LiPS壳层',['多硫化物穿梭'],'M0099 S0142',[ts,tc],side='强侧')
mech(p,'E-DD在贫液条件下因穿梭LiPS与Li副反应及提前Li2S钝化而迅速衰减','E-DD','E-PDD','LiPS溶解/转化',['正极反应','多硫化物穿梭','负极锂'],'M0123',side='弱侧')
claim(p,'通过六元脲环结构及高DN主导内溶剂化，同时提升硫反应与锂兼容性','M0135 M0136 M0137 M0141')
p['gaps']=['Li均做文献引用的预保护，具体人工SEI配方未在本SI展开。','Li2S沉积方法仅列LiTFSI，结果说明列0.4 M LiNO3，保留不一致。','400 μm与50 μm锂均购入，但除软包明确50 μm外不将厚度自动分配各coin测试。','图S1的Li2S6饱和溶解度无文本数值；循环与倍率缺失对照数字已请求读图。']
save(p)
