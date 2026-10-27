from agent_b_common import *
p=paper('S33','DME','纯DME对照；传统DD仅失效诊断')
form(p,'DD','传统1 m LiTFSI+0.2 m LiNO3 DME/DOL',[('LiTFSI','盐',1,'m'),('LiNO3','添加剂',.2,'m'),('DME','溶剂',1,'体积比'),('DOL','溶剂',1,'体积比')],'M0038')
form(p,'DME','0.75 m LiFSI+0.4 m LiNO3 DME',[('LiFSI','盐',.75,'m'),('LiNO3','添加剂',.4,'m'),('DME','溶剂',None,None)],'M0075 M0267')
fs=['DME','ETFE','BTFE','TFTFE','TFOFE']
for f in fs[1:]:form(p,f,'DME-'+f,[('LiFSI','盐',1.9,'摩尔比'),('LiNO3','添加剂',1,'摩尔比'),('DME','溶剂',18.5,'摩尔比'),(f,'氟醚共溶剂',3.8,'摩尔比')],'M0066 M0074 M0266')
grad(p,'Li+与LiPS溶剂化由强至弱',fs,['强','中等','中等','中等','弱'],'氟化程度提高，H–F相互作用增强，DME配位减少阴离子配位增加','M0072 M0078 M0090 M0123')
prop(p,'Li2S4最大溶解度',dict(zip(fs,['最高','依次下降','依次下降','依次下降','最低'])),'DME>ETFE>BTFE>TFTFE>TFOFE','UV-vis','0.5 m Li2S4上清液','M0115 M0116 M0117')
prop(p,'Li+配位',{'DME':'更多DME','TFOFE':'更多FSI/NO3，更少DME'},'随氟化增强阴离子配位','7LiNMR/Raman/MD','电解液','M0078 M0082 M0090 M0091')
prop(p,'电导率',{'DME':'最高','ETFE':'≈BTFE','BTFE':'≈ETFE','TFTFE':'较低','TFOFE':'最低'},'DME>ETFE≈BTFE>TFTFE>TFOFE','电导率','无LiPS','M0084')
prop(p,'Li+扩散系数',{'DME':'最高','TFOFE':'最低'},'与溶剂化能力正相关','7Li DOSY NMR','电解液','M0086')
c=dict(sulfur_loading='3.8 mgS cm-2',ES=5,ES_unit='μL mgS-1',Li_thickness='40 μm',rate='0.15 C',formation='四形成圈；方法明确前2圈0.05 C、随后0.1 C',temperature='未报告',LiNO3='DME0.4 m；FE配方摩尔比1',one_C='未直接定义',voltage='1.8–2.7 V')
t=test(p,'贫液扣式循环',fs,'M0124 M0171 M0172 M0280 M0281 M0282 M0283 M0286',**c)
for f,v in [('ETFE',32),('BTFE',131),('TFTFE',154),('TFOFE',31)]:result(t,'70%容量保持寿命',f,'DME',v,36,'圈','70%保持阈值','M0172')
for f in ['ETFE','BTFE','TFTFE']:result(t,'形成后首次放电容量',f,'DME','相近','相近',None,'四形成圈后首圈','M0124 M0125',basis='qualitative',direction='差异小')
result(t,'形成后放电容量','TFOFE','DME','低20%',None,'相对差','四形成圈后首圈','M0129',basis='qualitative',direction='变坏')
result(t,'放电过电位','TFOFE','DME','高0.8',None,'V差值','四形成圈后首圈','M0129',basis='qualitative',direction='变坏',reason='按原文0.8 V保留，可能需原图核验但不自行改')
result(t,'第二平台前容量','TFOFE','其他配方',166,'约240','mAh gS-1','四形成圈后首放','M0130')
fig(p,t,'Fig.4b','放电容量',fs,None,'各70%保持寿命点','M0172')
t2=test(p,'穿梭电流',fs,'M0133 M0134 M0140 M0142',**dict(c,rate='95%充电后开路条件检测'))
result(t2,'穿梭电流','TFOFE','ETFE/BTFE/TFTFE','略高','较低',None,'95%充电','M0134 M0140 M0142',basis='qualitative',direction='变坏',reason='最低溶解度并非最低穿梭电流')
result(t2,'穿梭电流','各FE','DME','较低','最高',None,'95%充电','M0134 M0140',basis='qualitative',direction='变好')
t3=test(p,'operando XRD',fs,'M0148 M0149 M0151 M0153 M0157 M0158 M0285',**dict(c,rate='0.1 C'))
for f,appear,disappear in [('DME',785,310),('TFTFE',606,360),('TFOFE',458,413)]:
 result(t3,'Li2S出现对应放电容量',f,None,appear,None,'mAh gS-1','首次出现','M0149',reason='相变时点，不等于总容量')
 result(t3,'Li2S消失对应充电容量',f,None,disappear,None,'mAh gS-1','峰消失','M0151',reason='相变时点，不等于总容量')
result(t3,'充电后S8形成','TFOFE','DME/TFTFE','充电918仍无S8峰','分别787/826时出现','mAh gS-1','充电过程','M0153 M0157',basis='qualitative',direction='变坏',reason='XRD相变证据，不能作总容量对比')
t4=test(p,'operando GEIS',fs,'M0160 S0068 S0069 S0070 S0071',**c)
result(t4,'界面及电荷转移阻抗','TFOFE','其他配方','明显更高','较低',None,'放电过程','M0160',basis='qualitative',direction='变坏')
t5=test(p,'LiNi Aurbach',fs,'M0166 M0167 M0277 M0278 M0279',cell='Li||Ni',Li_thickness='40 μm',rate='1 mA cm-2',formation='预镀1 mAh cm-2后10圈0.2 mAh cm-2，终剥离至1 V',electrolyte_volume='30 μL')
for f,v in [('ETFE',95.31),('BTFE',96.19),('TFTFE',96.81),('TFOFE',97.18)]:result(t5,'Aurbach CE',f,'DME',v,95.42,'%','10圈方法平均','M0167')
t6=test(p,'LiNi连续循环',fs,'M0168 M0169 S0075',cell='Li||Ni',rate='0.2 mA cm-2；0.2 mAh cm-2',electrolyte_volume='15 μL')
result(t6,'100圈平均CE','TFOFE>TFTFE>BTFE>ETFE','DME','顺序递减','最低',None,'100圈平均','M0169',basis='qualitative',direction='变好',reason='Aurbach与连续循环条件不同，不混用数值')
t7=test(p,'36圈后锂容量和耗液',['DME','ETFE','BTFE','TFTFE'],'M0208 M0209 M0210 M0214 M0215 M0216 M0295',cell='LiS循环后拆解；Li||SUS剥离/QNMR',**c)
for f,li,dme,fsi in [('ETFE',3.5,52,34),('BTFE',5.4,68,45),('TFTFE',7.2,70,73)]:
 result(t7,'剩余活性Li面容量',f,'DME',li,5.1,'mAh cm-2','36圈后','M0210')
 result(t7,'DME剩余比例',f,'DME',dme,56,'%','36圈后','M0215')
 result(t7,'FSI剩余比例',f,'DME',fsi,68,'%','36圈后','M0216')
result(t7,'共溶剂保留','ETFE',None,'几乎耗尽',None,None,'36圈后','M0228',basis='qualitative')
t8=test(p,'传统DD失效诊断',['DD'],'M0038 M0039 M0043 M0044 M0046 M0048 M0050 M0051',**dict(c,LiNO3='.2 m'))
result(t8,'失效圈数','DD',None,46,None,'圈','异常下平台','M0039')
result(t8,'剩余活性锂','DD',None,6.3,None,'mAh cm-2','46圈后（初始理论8）','M0043')
for n,v in [('DME分解',33),('DOL分解',49),('TFSI分解',2)]:result(t8,n,'DD',None,v,None,'%','46圈','M0046')
result(t8,'补液恢复','DD',None,'恢复',None,None,'失效电极+新电解液','M0050 M0051',basis='qualitative')
for typ,es,rate,formation,life,capA,capB,eneA,eneB in [('bi',3.5,'0.1 C','2圈0.025 C+2圈0.05 C',135,87,84.6,290,295),('stack',2,'0.05 C','2圈0.0125 C+1圈0.025 C',80,429,457,405,450)]:
 tt=test(p,typ+'软包',['TFTFE','DME'],'M0241 M0242 M0243 M0249 M0250 M0296 M0297 M0304 M0306 M0307 S0112',cell='Li||S '+typ+' pouch',**dict(c,sulfur_loading='2.5 mgS cm-2双面正极',ES=es,rate=rate,formation=formation))
 result(tt,'放电容量','TFTFE','DME',capA,capB,'mAh','SI表S2对应能量密度','S0112')
 result(tt,'能量密度','TFTFE','DME',eneA,eneB,'Wh kg-1','不含包装的各组件总质量','S0112')
 result(tt,'循环寿命','TFTFE','DME',life,'25%更短' if typ=='bi' else '<TFTFE的1/6','圈','70%保持' if typ=='bi' else '稳定运行','M0249' if typ=='bi' else 'M0250',basis='qualitative',direction='变好',reason='不反推对照圈数')
 fig(p,tt,'Fig.7c' if typ=='bi' else 'Fig.7d','放电容量','TFTFE','DME','135圈' if typ=='bi' else '80圈','M0249' if typ=='bi' else 'M0250')
for sm,pr,cat,ids,src in [
('阴离子配位增强，提高锂负极稳定性。','阴离子配位','负极锂','M0170','本文结论'),
('TFOFE虽锂可逆性最高，弱溶剂化下正极可逆性决定循环稳定性。','弱溶剂化极限','正极反应','M0173','本文结论'),
('弱溶剂化导致严重LiPS聚集，贫液下过电位高、容量低。','LiPS聚集','正极反应','M0163','本文结论'),
('TFOFE稳定低电荷密度单阴离子且LUMO更低，解释较高中穿梭电流。','物种/还原性','多硫化物穿梭 负极锂','M0143','本文结论'),
('这些单阴离子更易在锂上还原，而双阴离子比其他电解液组分更难还原。','多硫物种反应性','多硫化物穿梭 负极锂','M0144 M0147','本文结论'),
('弱溶剂化更偏固相转化，使Li2S更早结晶。','相变','正极反应','M0150','本文推测'),
('LiPS在正极和隔膜聚集造成高极化及氧化受阻，TFOFE充电后无S8。','聚集/氧化','正极反应','M0154','本文结论'),
('中等溶剂化更多阴离子进入Li溶剂化结构，促进无机富集SEI。','阴离子SEI','负极锂','M0188','本文推测'),
('中等溶剂化降低锂表面多硫/硫化锂信号，证明减少LiPS腐蚀。','腐蚀','负极锂 多硫化物穿梭','M0195','本文结论'),
('ETFE剩余锂异常低源于其高化学腐蚀。','ETFE稳定性','负极锂','M0211','本文结论'),
('TFTFE均匀锂沉积减少暴露面积，减少DME、FSI和共溶剂分解。','锂形貌','负极锂 电解液消耗','M0226','本文结论'),
('粗糙锂与多孔层捕获电解液会增加电解液分解。','多孔锂','负极锂 电解液消耗','M0052','本文推测'),
('重新注液恢复失效电池，确认溶剂耗尽为退化原因。','耗液','电解液消耗','M0051','本文结论'),
('DME中衰退前容量上升可能是LiPS溶出碳结构并在外表面反应。','溶出/反应位置','正极反应','M0178','本文推测')]:mech(p,sm,'TFTFE/弱侧','DME/强侧',pr,cat,ids,[t],source=src)
p['design_claims']=[{'summary':'中等溶剂化在硫氧化还原动力学与锂可逆性之间平衡，适合贫液长循环。','evidence_ids':['M0175']}]
p['gaps']=['M0254总结说H–F相互作用随氟化降低，与正文M0072等相反；采用正文多种实验一致次序并记录冲突。','bi-cell注液量正文336 μL与SI质量/密度及标称载硫面积不完全一致，不推算E/S，保留指定3.5。','能量密度405为不含包装组件总质量（SI表）；M0244称active materials不准确，包装估计后368见M0245。','四形成圈正文说明与方法后续0.1 C圈数省略，未强填。','多数溶剂化、输运、溶解度梯度只有图，原文无数字，保留顺序不目测。']
save(p)
