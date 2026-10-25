from independent_c_helpers import *
p=init('P354');p['control_id']='3M';p['control_type']='不含LiNO3的自配对照：3 M LiFSI/DME'
for id,n,r in [('3M','3','2.2'),('3.6M','3.6','2'),('4M','4','1.4')]:
 form(p,id,n+' M LiFSI/DME；LiFSI:DME=1:'+r,[['LiFSI','盐',n,'M'],['DME','溶剂化溶剂',r,'摩尔份/1份LiFSI']],'M0056 M0162')
form(p,'HFE','3 M LiFSI DME/HFE 1:1 vol；LiFSI:DME:HFE=1:1.2:0.83',[['LiFSI','盐','3','M'],['DME','溶剂化溶剂','1.2','摩尔份/1份LiFSI'],['HFE','弱或非溶剂化溶剂','0.83','摩尔份/1份LiFSI']],'M0057 M0058 M0059')
fs=['3M','3.6M','4M','HFE']
grad(p,'LiFSI浓度',['3M','3.6M','4M'],['3','3.6','4 M'],'自由DME随盐浓度升高减少；3.6/4 M近乎全部配位','M0149 M0162')
grad(p,'HFE替代部分DME',['3M','HFE'],['DME','DME/HFE 1:1 vol'],'自由DME减少、局部盐浓度增加','M0057 M0174')
prop(p,'离子电导率',dict(zip(fs,['6.75','5.94','5.10','2.74'])),'mS cm−1；逐渐降低','阻抗仪25 °C','电解液','M0045 M0162')
prop(p,'黏度',dict(zip(fs,['40.2','49.9','62.4','31.3'])),'mPa s；升盐增黏，HFE降低','黏度仪25 °C','电解液','M0045 M0162')
prop(p,'多硫化物溶解度',dict(zip(fs,['高','较低','较低','较低'])),'提高盐浓度或HFE抑制溶解，未定量','混合液颜色','电解液:0.2 M Li2S8/DME=3:1（非原液体系）','M0150 M0151 M0152 M0176')
prop(p,'Li+溶剂化',{'3M':'存在未配位DME','3.6M':'近乎全部DME配位','4M':'近乎全部DME配位','HFE':'自由DME减少'},'定性','引文配位论述及组成解释','电解液','M0123 M0149 M0174')
base={'Li_thickness':'200 μm','LiNO3':'未添加','one_C':'1672 mA g−1','electrolyte_volume':'52.0 μL'}
for tid,host,loading in [('T1','Cmicro-S','1.0'),('T2','Cmicro-meso-S','1.2'),('T3','Cmeso-S','1.4')]:
 t=test(p,tid,'不同碳宿主循环，按载量拆分',host+'||Li',{**base,'sulfur_loading':loading+' mg cm−2','rate':'未报告（Fig.3正文无明确倍率）'},['3M'],'S0016 S0018 M0063 M0068 M0072 M0120 M0121 M0122 M0127')
 if tid=='T1':
  for met,v,u,pt in [('容量','1121','mAh g−1','2圈'),('容量','934.5','mAh g−1','50圈'),('容量保持率','83.4','%','50/2圈'),('平均CE','99.4','%','50圈测试')]:result(t,met,'3M',None,v,None,u,pt,'numeric','不判','M0120 M0121')
 elif tid=='T3':result(t,'循环失败','3M',None,'14',None,'cycles','充电无法达到截止电位','numeric','不判','M0122 M0127 M0134')
cond={**base,'sulfur_loading':'1.2 mg cm−2'}
t=test(p,'T4','浓度梯度0.1C循环','Cmicro-meso-S||Li',{**cond,'rate':'0.1 C'},['3M','3.6M','4M'],'M0161 S0018 M0063 M0068 M0072')
for id,a,b,c,ce in [('3.6M','1578.8','82.3','5.21','90.8'),('4M','1475.4','161.6','11.0','92.6')]:
 for met,v,u,pt in [('容量',a,'mAh g−1','2圈'),('容量',b,'mAh g−1','50圈'),('保持率',c,'%','50/2圈'),('平均CE',ce,'%','50圈测试')]:result(t,met,id,None,v,None,u,pt,'numeric','不判','M0156 M0157')
result(t,'循环容量衰减','3.6M','3M','更显著','基准',None,'0.1C','qualitative','变坏','M0155')
t=test(p,'T5','浓度梯度低电流循环','Cmicro-meso-S||Li',{**cond,'rate':'0.02 C'},['3M','3.6M','4M'],'M0161 M0166 M0167')
for id in ['3.6M','4M']:
 result(t,'放电容量',id,'3M','较高','较低',None,'0.02C','qualitative','变好','M0167')
 result(t,'库仑效率',id,'3M','提高','基准',None,'0.02C','qualitative','变好','M0166')
t=test(p,'T6','HFE对比循环','Cmicro-meso-S||Li',{**cond,'rate':'未报告（Fig.5正文未明确；不可默认为0.1C）'},['3M','HFE'],'M0177 M0178 M0179 M0190')
for met,a,b,u,pt in [('容量','1347.7','1462.9','mAh g−1','2圈'),('容量','830.4','732.3','mAh g−1','50圈'),('保持率','61.6','50.0','%','50/2圈'),('平均CE','98.5','97.1','%','50圈测试')]:result(t,met,'HFE','3M',a,b,u,pt,'numeric','不判','M0178 M0179')
t=test(p,'T7','HFE倍率','Cmicro-meso-S||Li',{**cond,'rate':'各档仅图，文字明确2 C'},['3M','HFE'],'M0193 M0005 M0181')
result(t,'倍率容量','HFE',None,'943',None,'mAh g−1','2 C','numeric','不判','M0005')
result(t,'高倍率表现','HFE','3M','更优','基准',None,'Fig.5c','qualitative','变好','M0181')
t=test(p,'T8','高载量软包循环','Cmicro-meso-S||Li双侧锂软包',{'sulfur_loading':'16.8 mg cm−2','ES':'7.2','ES_unit':'μL mg−1','LiNO3':'未添加','one_C':'1672 mA g−1'},['3M','HFE'],'S0067 S0071 S0072 S0073 S0074 S0075')
result(t,'循环可持续性','HFE','3M','稳定50圈','首圈无法充至截止电压',None,'全测试','qualitative','变好','S0077 S0078 S0079')
for met,v,u,pt in [('放电容量','1203.7','mAh g−1','2圈'),('放电容量','787.3','mAh g−1','50圈'),('平均CE','98.6','%','50圈')]:result(t,met,'HFE',None,v,None,u,pt,'numeric','不判','S0079 S0080')
for su,a,b,pr,cats,typ,e,ts,side in [
('3M中未配位DME及少量介孔使LiPS溶出，造成容量衰减','3M',None,'自由DME',['多硫化物穿梭'],'本文结论','M0144',['T2'],'强侧'),
('3.6/4M中DME近乎全部配位，抑制LiPS溶解并消除高电位平台','全梯度',None,'自由DME减少',['正极反应','多硫化物穿梭'],'本文结论','M0149',['T4'],'强侧'),
('高黏度低电导造成正极电流不均，并传递至负极使CE下降','全梯度',None,'高黏度低电导',['正极反应','负极锂'],'本文结论','M0158 M0164 M0165',['T4'],'其他'),
('0.02C减轻不均匀电流分布，盐浓度提高反而改善CE','全梯度',None,'电流分布',['负极锂'],'本文结论','M0166',['T5'],'其他'),
('HFE减少自由DME以抑制LiPS溶解','HFE','3M','自由DME减少',['多硫化物穿梭'],'本文结论','M0174 M0175',['T6'],'强侧'),
('HFE减黏缓解不均匀电流分布，改善循环','HFE','3M','黏度降低',['正极反应','负极锂'],'本文结论','M0180',['T6'],'其他'),
('HFE降低黏度改善高倍率','HFE','3M','黏度降低',['正极反应'],'本文结论','M0181',['T7'],'其他'),
('HFE抑制FSI−在Li表面分解，形成更薄SEI','HFE','3M','FSI分解较少',['负极锂','电解液消耗'],'本文结论','M0200',['T6'],'其他'),
('本文低HFE量导致LiF少，与他文高HFE促进FSI分解富LiF结论不同','HFE',None,'HFE比例与阴离子分解',['负极锂','电解液消耗'],'本文结论','M0201 M0202 M0203',[],'其他'),
('高载量条件性能提升归于HFE降低黏度','HFE','3M','黏度降低',['正极反应'],'本文结论','S0081 S0082',['T8'],'其他')]:
 mech(p,su,a,b,pr,cats,typ,e,ts,side)
claim(p,'微介孔碳和3 M LiFSI DME/HFE结合，同时减少LiPS溶出、黏度并改善沉积/薄SEI','M0204 M0212')
for tid,f,e,pt in [('T4','Figure 4b','M0156','2及50圈'),('T5','Figure 4c','','首圈及50圈'),('T6','Figure 5b','M0178','首圈'),('T7','Figure 5c','M0005','各倍率档'),('T8','Figure S10c','S0079','首圈')]:
 fig(p,tid,f,'si' if 'S' in f else 'main','容量','全梯度',None,pt,e,'补齐文字缺失的同测试容量；无数值锚点图整图不得使用')
p['gaps']=['无Li||Cu或Li||Li半电池，Li表征来自Li-S循环后','不同碳宿主载量不同，不作同条件优劣比较','标准Li-S循环倍率部分仅图；电池温度/化成及软包锂厚未报告','正文称HFE稀释，但配方最终仍3M；严格照最终摩尔比存储，非简单往3M母液加HFE']
save(p)

