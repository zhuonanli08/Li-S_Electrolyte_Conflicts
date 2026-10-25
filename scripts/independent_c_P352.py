from independent_c_helpers import *
p=init('P352');p['control_id']='DOL:DME-control';p['control_type']='常规醚基准（DOL/DME + LiTFSI + LiNO3）'
form(p,'DOL:DME-control','DOL:DME 1:1 w/w；LiTFSI和LiNO3各1 mol kgsolvent−1',[['DOL','溶剂化溶剂','1','质量份'],['DME','溶剂化溶剂','1','质量份'],['LiTFSI','盐','1','mol kgsolvent−1'],['LiNO3','添加剂','1','mol kgsolvent−1']],'M0073')
for v in ['5','10','15']:
 form(p,'TE-'+v+'%','TEGDME中LiTFSI和LiNO3各1 mol kgsolvent−1；按初始溶液质量额外加入'+v+' wt% DOL',[['TEGDME','溶剂化溶剂','基液',''],['LiTFSI','盐','1','mol kgsolvent−1，添加DOL前'],['LiNO3','添加剂','1','mol kgsolvent−1，添加DOL前'],['DOL','溶剂化溶剂',v,'wt%相对初始溶液质量']],'M0029 M0030 M0031 M0037')
fs=['TE-5%','TE-10%','TE-15%']
grad(p,'DOL加入量',fs,['5','10','15 wt%相对初始溶液'],'TE-5至TE-15作者推测离子缔合增加；未直接定量溶剂化强度','M0030 M0107')
prop(p,'Li+溶剂化/离子缔合',{'TE-5%':'较低离子缔合','TE-10%':'较高','TE-15%':'较高'},'FTIR强度提示更多离子对，属于作者推测','FTIR','电解液','M0107')
prop(p,'离子电导率（25 °C）',dict.fromkeys(fs,'near 1.5×10−3 S cm−1'),'相近','EIS','SS||SS','M0097')
prop(p,'离子电导率（−3 °C）',dict(zip(fs,['8×10−4','6×10−4','7×10−4'])),'S cm−1；非单调','EIS','SS||SS','M0098')
prop(p,'离子电导率（约50 °C）',dict(zip(fs,['2×10−3','2×10−3','approaching 3×10−3'])),'S cm−1；TE-15较高','EIS','SS||SS','M0097')
prop(p,'Li+迁移数',dict(zip(fs,['0.55','0.53','0.50'])),'随DOL增加下降','Bruce–Vincent–Evans','Li||Li','M0116')
prop(p,'离子运动活化能',dict(zip(fs,['5.1×10−2','7.6×10−2','8.5×10−2'])),'eV；随DOL增加升高','Arrhenius拟合电导率','电解液','M0100')
prop(p,'黏度',dict(zip(fs,['高','中','低'])),'增加DOL降低黏度，未给溶液实测数','作者描述','电解液','M0173 M0177 M0188 M0189')
t=test(p,'T1','静置Li界面阻抗','Li||Li',{'rate':'EIS 500 kHz–100 mHz,10 mV','LiNO3':'基液1 mol kgsolvent−1'},fs,'M0047 M0110')
for id,a,b in zip(fs,['85','84','50'],['154','129','86']):
 result(t,'界面电阻',id,None,a,None,'Ω','初始','numeric','不判','M0110')
 result(t,'界面电阻',id,None,b,None,'Ω','18天','numeric','不判','M0110')
t=test(p,'T2','Li沉积剥离','Li||Li T-cell',{'rate':'0.1 mA cm−2','LiNO3':'基液1 mol kgsolvent−1'},fs,'M0046 M0122 M0124 M0126')
for id,v in zip(fs,['27','23','20']):result(t,'过电位',id,None,v,None,'mV','第8天开始','numeric','不判','M0124')
result(t,'过电位','全梯度',None,'∼30',None,'mV','后半段稳定','numeric','不判','M0126 M0132')
t=test(p,'T3','电化学稳定窗','Li||SPC',{'rate':'0.1 mV s−1','LiNO3':'基液1 mol kgsolvent−1'},fs,'M0048 M0051 M0052 M0120')
for id,v in zip(fs,['4.41','4.38','4.37']):result(t,'阳极稳定电位',id,None,v,None,'V vs Li+/Li','30 μA判据','numeric','不判','M0114 M0120')
common={'one_C':'1675 mA g−1','LiNO3':'1 mol kgsolvent−1','voltage':'1.7–2.8 V'}
for tid,rate,initial,steady,final,ce in [('T4','C/5','810','about 610','500','>99'),('T5','C/3','703','about 530','436','>97')]:
 t=test(p,tid,'常规电解液固定倍率循环','S:MWCNTs||Li CR2032',{**common,'sulfur_loading':'2.2–2.3 mg cm−2','ES':'10','ES_unit':'μL mg−1','rate':rate},['DOL:DME-control'],'M0076 M0158 M0159')
 for metric,v,pt,u in [('放电容量',initial,'首圈','mAh g−1'),('放电容量',steady,'稳定阶段','mAh g−1'),('放电容量',final,'200圈','mAh g−1'),('库仑效率',ce,'整个测试','%')]:result(t,metric,'DOL:DME-control',None,v,None,u,pt,'numeric','不判','M0158' if tid=='T4' else 'M0159')
t=test(p,'T6','常规电解液高载量循环','S:MWCNTs||Li CR2032',{**common,'sulfur_loading':'5.2 mg cm−2','ES':'6','ES_unit':'μL mg−1','rate':'C/10'},['DOL:DME-control'],'M0076 M0167 M0169 M0170')
for v,pt in [('803','首圈'),('531','第5圈'),('350–400','稳态至200圈')]:result(t,'放电容量','DOL:DME-control',None,v,None,'mAh g−1',pt,'numeric','不判','M0169 M0170')
result(t,'库仑效率','DOL:DME-control',None,'>97',None,'%','全程','numeric','不判','M0170')
t=test(p,'T7','常规电解液倍率','S:MWCNTs||Li CR2032',{**common,'sulfur_loading':'2.2 mg cm−2','ES':'10','ES_unit':'μL mg−1','rate':'C/10,C/8,C/5,C/3,C/2,回C/10，每档5圈','voltage':'C/10–C/3:1.8–2.8 V；C/2:1.7–2.8 V'},['DOL:DME-control'],'M0077 M0078 M0155 M0156')
for pt,v in [('初始C/10','1100'),('稳态C/10','976'),('C/8','915'),('C/5','833'),('C/3','720'),('C/2','163'),('回C/10','922')]:result(t,'倍率容量','DOL:DME-control',None,v,None,'mAh g−1',pt,'numeric','不判','M0155 M0156')
t=test(p,'T8','TE系列固定倍率循环','S:MWCNTs||Li CR2032',{**common,'sulfur_loading':'1.7–2.1 mg cm−2；配方逐项载量未明确','ES':'15','ES_unit':'μL mg−1','rate':'C/5'},fs,'M0082 M0161 M0162')
for id,v in zip(fs,['140','220','270']):result(t,'初始放电容量',id,None,v,None,'mAh g−1','初始阶段起点','numeric','不判','M0175')
for id,v in zip(fs,['360','530','570']):result(t,'活化后放电容量',id,None,v,None,'mAh g−1','初始阶段增长终点，圈数未明','numeric','不判','M0175')
result(t,'放电容量','TE-10%',None,'406',None,'mAh g−1','130圈','numeric','不判','M0183')
result(t,'失活后放电容量','TE-5%',None,'below 100',None,'mAh g−1','117圈后','numeric','不判','M0181')
result(t,'末点放电容量','TE-15%',None,'250',None,'mAh g−1','末点，圈数文字未给','numeric','不判','M0182')
result(t,'库仑效率','TE-5%',None,'82',None,'%','转化失活阶段','numeric','不判','M0184')
result(t,'库仑效率','TE-10%','TE-15%','>96','>96','%','整个测试','numeric','不判','M0184')
t=test(p,'T9','TE系列倍率','S:MWCNTs||Li CR2032',{**common,'sulfur_loading':'∼2.0 mg cm−2','ES':'15','ES_unit':'μL mg−1','rate':'C/20,C/10,C/8,C/5,C/3,C/2,回C/20，每档5圈','voltage':'C/20–C/8:1.8–2.8 V；C/5–C/2:1.7–2.8 V'},fs,'M0083 M0084 S0088 S0089 S0090 S0091')
for j,pt in enumerate(['C/20','C/10','C/8','C/5']):
 for id,vals in [('TE-5%',['900','760','670','150']),('TE-10%',['880','735','610','around 500']),('TE-15%',['920','810','725','640'])]:result(t,'倍率容量',id,None,vals[j],None,'mAh g−1',pt+'稳态','numeric','不判','M0199 M0200')
result(t,'倍率容量','TE-15%',None,'130',None,'mAh g−1','C/3最大值','numeric','不判','M0201')
result(t,'转化反应','全梯度',None,'失活',None,None,'C/2','qualitative','不判','M0201')
for su,e,cats,typ,ts in [
('更多DOL降低黏度并促进长链向短链多硫化物的液固转化','M0173',['正极反应'],'本文结论',['T8']),
('容量起伏可能来自TEGDME/DOL/共溶剂及Li2Sx的复杂相互作用','M0185',['正极反应'],'本文推测',['T8']),
('TE-10最长寿命伴随最大容量起伏，提示10 wt% DOL改变多硫化物溶剂化与物种','M0186',['正极反应'],'本文推测',['T8']),
('TE-5高黏度限制容量和循环寿命，尽管glyme支持有效Li+交换','M0188',['正极反应'],'本文结论',['T8']),
('TE-15低黏度带来较高容量，但DOL持续耗损可能形成不均匀且过多SEI而缩短寿命','M0189',['负极锂','电解液消耗'],'本文推测',['T8']),
('DOL浓度增加改善转化动力学，但高倍率仍受黏度限制','M0202',['正极反应'],'本文结论',['T9']),
('TE-15初期更高极化可能源于较多DOL在Li上反应形成SEI','M0123',['负极锂'],'本文推测',['T2']),
('第7天后部分SEI溶解降低Li极化','M0124',['负极锂'],'本文结论',['T2'])]:
 mech(p,su,'全梯度',None,'DOL比例、黏度、溶剂化与成膜',cats,typ,e,ts,'其他')
claim(p,'TE-10%为容量与寿命最有希望的折中，但容量波动仍待改善','M0194 M0218')
fig(p,'T8','Figure 5d','main','同圈容量及寿命','全梯度',None,'第1圈/100/117/130圈','M0175 M0181 M0182 M0183','同圈比较补齐；载量范围未逐配方明确，保持条件标记')
p['gaps']=['正文M0180称Ea下降，与M0100实测Ea上升矛盾；不采纳该方向','SI Figure S3d数值与正文第8天电位不同，图中多系列排版未明确配对；保留正文数','常规对照与TE系列E/S和载量不同，不跨测试判性能','无直接多硫化物定量溶解度；锂厚/化成/电池温度未报告']
save(p)

