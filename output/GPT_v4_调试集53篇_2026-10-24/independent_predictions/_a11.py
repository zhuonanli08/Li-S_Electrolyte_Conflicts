from _author_a import *
p=paper('S11');p['control_id']='0HFE';p['control_type']='常规醚基准（无LiNO3机理测试另列）';fs=['0HFE','10HFE','20HFE','30HFE'];names=['strong','mid-strong','mid-weak','weak']
for n,k,name in zip([0,10,20,30],fs,names):form(p,k,name,[('DOL/DME','溶剂化溶剂','1:1','v/v'),('HFE','弱或非溶剂化溶剂',n,'vol%'),('LiTFSI','盐',1,'M'),('LiNO3','添加剂',2,'wt%（无硝酸锂测试除外）')],f'DOL/DME 1:1 mixed with {n}% HFE; 1 M LiTFSI, 2wt% LiNO3','S0005 M0060')
form(p,'medium','pouch medium（具体HFE档原文未写）',[],'medium solvation structure','M0191 S0117')
grad(p,'HFE体积分数',fs,[0,10,20,30],'LiPS外层溶剂化由强到弱；内层近似不变','M0037 M0045 M0046 M0060')
prop(p,'Li2S8溶解度',dict(zip(fs,[4.3,2.9,2.6,1.8])),'逐级下降','溶解试验','M[S] Li2S8','M0037 S0109')
prop(p,'LiPS内外层溶剂化',{f:'内层DME配位数相同；外层HFE随含量增加' for f in fs},'HFE不进入内层；外层DME/DOL减少','MD、7Li-NMR','模拟1 M[S]，NMR0.5 M[S] Li2S8','M0041 M0045 M0046 M0048 M0050 S0066')
an=dict(sulfur_loading='1.3 mg cm−2',Li_thickness='600 μm',temperature='室温',LiNO3='无',electrolyte_volume='25 μL')
t1=test(p,'穿梭电流','Li‖S coin',fs,'S0012 S0013 S0014 S0015 S0016',rate='充至2.90 V；2.40→2.34 V每档1h',**an);result(t1,'穿梭电流','全梯度',None,'随HFE升高依次下降',None,None,'2.34–2.40 V','M0066',basis='qualitative',same=None)
t2=test(p,'无LiNO3循环CE','Li‖S coin',fs,'S0012 S0013 S0017',rate='0.1 C',one_C='1672 mA g−1',**an)
for i in range(1,4):result(t2,'首圈CE',fs[i],fs[0],[38.2,45.4,67.1,81.8][i],38.2,'%','首圈','M0068')
tcv=test(p,'LiPS总反应动力学CV','Li‖Li2S8/CP',fs,'S0018 S0019',Li_thickness='600 μm',rate='0.5 mV s−1；1.70–2.80 V',LiNO3='2wt%（制备基液）',electrolyte_volume='25 μL',LiPS='1.0 M[S] Li2S8')
for metric,vals,ev in [('R1还原峰',[2.02,2.01,1.97,1.78],'M0098'),('R2还原峰',[2.30,2.25,2.18,2.16],'M0099'),('O氧化峰',[2.45,2.47,2.50,2.53],'M0100')]:
 for i in range(1,4):result(tcv,metric,fs[i],fs[0],vals[i],vals[0],'V','CV',ev)
result(tcv,'R1峰电流','30HFE','0HFE',.35,.75,'mA cm−2','CV','M0103');result(tcv,'R2峰电流','30HFE','0HFE',.38,1.5,'mA cm−2','CV','M0103')
te=test(p,'液液转化EIS','CP‖CP对称Li2S6',fs,'S0020 S0021',rate='OCV 10mV；100kHz–0.1Hz',LiPS='1.0 M[S] Li2S6',electrolyte_volume='40 μL');result(te,'电荷转移阻抗','全梯度',None,'强到弱显著增大',None,None,'开路','M0108',basis='qualitative',same=None)
tn=test(p,'液固Li2S沉积','Li‖Li2S8/CP',fs,'S0018 S0022 S0023',Li_thickness='600 μm',rate='2.05 V',formation='0.117 mA放到2.06 V',LiPS='1.0 M[S] Li2S8',electrolyte_volume='25 μL')
for i,v in enumerate([98,89,71],1):result(tn,'Li2S沉积容量',fs[i],fs[0],v,161,'mAh g−1','恒电位积分','M0111')
common=dict(sulfur_loading='4.3 mg cm−2',Li_thickness='50 μm',ES=6.1,ES_unit='μL mg−1',LiNO3='2wt%',one_C='1672 mA g−1')
tg=test(p,'GITT极化分解','Li‖S coin',fs,'S0026 S0027 M0124 M0143',rate='0.1 C；放10min静置2h',**common);result(tg,'活化极化','30HFE','0HFE',223,38,'mV','308 mAh g−1','M0137');result(tg,'浓差极化','30HFE','0HFE',81,55,'mV','308 mAh g−1','M0137');result(tg,'活化极化','30HFE',None,362,None,'mV','336 mAh g−1','M0135',same=None)
tr=test(p,'倍率','Li‖S CR2032',fs,'S0033 S0034 S0035 M0145 M0154',rate='0.1/0.2/0.3/0.4/0.5 C',**common);result(tr,'倍率容量','0HFE','30HFE',1040,956,'mAh g−1','0.1 C','M0145 M0154');result(tr,'倍率容量','0HFE','30HFE',874,'<243','mAh g−1','0.5 C','M0145 M0154');result(tr,'各倍率容量','全梯度',None,'依次降低',None,None,'每档倍率','M0153 M0154',basis='qualitative',same=None);fig(p,tr,'5A','main','中间梯度倍率容量','10HFE','20HFE','0.1和0.5 C','M0145 M0154')
tcy=test(p,'长期循环','Li‖S CR2032',fs,'S0033 S0034 S0035 M0172',rate='0.1 C',**common)
for i,v in enumerate([889,887,778],1):result(tcy,'首圈容量',fs[i],fs[0],v,1013,'mAh g−1','0.1 C首圈','M0174 M0176 M0177 M0179')
for f,v,point,ev in [('0HFE',63.7,'60圈','M0177'),('10HFE',66.5,'122圈','M0176'),('20HFE',78.5,'146圈','M0174')]:result(tcy,'容量保持率',f,None,v,None,'%',point,ev,same=None)
result(tcy,'容量急降起点','30HFE','0HFE','30圈后','30圈后','cycles','容量急降','M0177 M0179',basis='qualitative',direction='差异小')
for f,v in zip(fs[:3],[38,65,106]):result(tcy,'CE降至90%圈数',f,None,v,None,'cycles','90% CE','M0173',same=None)
fig(p,tcy,'5C','main','同圈容量/寿命/交叉','20HFE','0HFE','首圈、第30、第60圈及终点','M0174 M0176 M0177 M0179')
tp=test(p,'软包','Li‖S pouch',['0HFE','medium','30HFE'],'M0189 M0190 S0037 S0038 S0040 S0041',sulfur_loading='7.4 mg cm−2单侧',Li_thickness='75 μm单侧',ES=3.5,ES_unit='g gS−1',rate='0.05 C',one_C='1000 mA g−1',LiNO3='2wt%（基液）');result(tp,'循环寿命','medium','0HFE',30,19,'cycles','正常循环','M0191 M0201');result(tp,'循环寿命','medium','30HFE',30,1,'cycles','正常循环','M0191 M0201');result(tp,'首圈能量密度','medium',None,338,None,'Wh kg−1','整包质量','M0191 S0119',same=None);result(tp,'放电容量','medium',None,999,None,'mAh g−1','20圈','M0203',same=None);fig(p,tp,'6B','main','各配方首圈/同圈容量','medium','0HFE','首圈、第19圈','M0191 M0201 M0203')
for summary,A,B,propname,cat,ev,ts,side,src in [
 ('弱外层溶剂化抑制LiPS与锂副反应及负极动力学，改善锂稳定性','30HFE','0HFE','LiPS外层溶剂化',['负极锂','多硫化物穿梭'],'M0066 M0093',[t1,t2],'强侧','本文结论'),
 ('HFE还原稳定且不参与SEI，性能差异主要来自溶剂化结构','全梯度',None,'LiPS溶剂化',['负极锂'],'M0090 M0091',[t2],'其他','本文结论'),
 ('弱溶剂化降低液液转化和Li2S沉积动力学','30HFE','0HFE','LiPS溶剂化',['正极反应'],'M0108 M0112',[te,tn],'弱侧','本文结论'),
 ('弱溶剂化的主要极化瓶颈为活化极化，可能来自Li2S成核沉积受阻','30HFE','0HFE','LiPS溶剂化',['正极反应'],'M0135 M0136 M0138',[tg],'弱侧','本文推测'),
 ('强溶剂化引起LiPS对锂快速副反应，耗尽锂库且积累失活锂导致极化和失效','0HFE','20HFE','LiPS溶剂化',['负极锂'],'M0178 M0184',[tcy],'强侧','本文结论'),
 ('弱溶剂化正极动力学慢导致容量骤降及第二平台消失','30HFE','20HFE','LiPS溶剂化',['正极反应'],'M0179 M0185',[tcy],'弱侧','本文结论'),
 ('中等溶剂化同时限制负极副反应并保留正极动力学','20HFE','0HFE/30HFE','LiPS溶剂化',['正极反应','负极锂'],'M0182',[tcy],'其他','本文结论'),
 ('软包弱档正极受阻，仅首圈正常；强档锂负极被破坏，medium平衡两侧','medium','0HFE/30HFE','LiPS溶剂化',['正极反应','负极锂'],'M0202 M0204 M0205',[tp],'其他','本文结论')]:mech(p,summary,A,B,propname,cat,ev,ts,source=src,side=side)
claim(p,'通过中等溶剂化平衡正负极动力学；扣电最优20%HFE，软包medium具体档未给','M0174 M0205 M0210')
p['gaps']=['软包medium对应HFE档原文未写，不映射为20%。','离子电导率、黏度、迁移数未报告。','各循环保持率终点不同，等待同圈读图。','无单独Li‖Cu或Li‖Li测试。']
save(p)
