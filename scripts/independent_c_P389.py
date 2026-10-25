from independent_c_helpers import *
p=init('P389');p['control_id']='DOL/DME';p['control_type']='常规醚基准（DOL/DME + LiTFSI + LiNO3）'
form(p,'DOL/DME','1.0 M LiTFSI +2.0 wt% LiNO3 in DOL/DME 1:1 vol',[['LiTFSI','盐','1.0','M'],['LiNO3','添加剂','2.0','wt%'],['DOL','溶剂化溶剂','1','体积份'],['DME','溶剂化溶剂','1','体积份']],'M0035 S0011')
for x in ['HME','DIPS','HFE','DIPE']:
 form(p,x+'-EPSE','1.0 M LiTFSI +2.0 wt% LiNO3 in DOL/DME/'+x+' 37.5/37.5/25 vol',[['LiTFSI','盐','1.0','M'],['LiNO3','添加剂','2.0','wt%'],['DOL','溶剂化溶剂','37.5','vol%'],['DME','溶剂化溶剂','37.5','vol%'],[x,'弱或非溶剂化溶剂','25','vol%']],'M0034 M0035 M0071 S0012 S0013')
grad(p,'外壳溶剂种类',['HME-EPSE','DIPS-EPSE','HFE-EPSE','DIPE-EPSE'],['HME','DIPS','HFE','DIPE'],'溶剂化强弱未定量排序；等25 vol%对照','M0071 M0072')
prop(p,'多硫化物溶剂化',{'DOL/DME':'内外层均为DOL/DME','HME-EPSE':'内层DME/DOL；HME位于外层约7.8 Å'},'HME构建纳米异质双层壳，内层维持溶解','MD','0.25 M Li2S8模型；无LiTFSI和LiNO3，区别于电池电解液','M0035 M0036 M0037 M0039 M0050 M0052 M0053 S0036')
fs=['DOL/DME','HME-EPSE','DIPS-EPSE','HFE-EPSE','DIPE-EPSE']
c={'sulfur_loading':'4.4 mgS cm−2','ES':'6.6','ES_unit':'μL mgS−1','Li_thickness':'50 μm','LiNO3':'2.0 wt%','temperature':'25 °C','one_C':'1672 mA g−1','formation':'0.05 C 2圈'}
t=test(p,'T1','实际条件倍率','CNT/S||Li coin',{**c,'rate':'0.1,0.2,0.3 C，每档5圈'},fs,'M0055 S0017 S0019 S0020 S0021')
vals={'DOL/DME':['1049','942','915'],'HME-EPSE':['1040','919','869'],'DIPS-EPSE':['948','840','777'],'HFE-EPSE':['929','<800','<200'],'DIPE-EPSE':['753','<800','<200']}
for i,r in enumerate(['0.1','0.2','0.3']):
 for a in fs[1:]:result(t,'倍率容量',a,'DOL/DME',vals[a][i],vals['DOL/DME'][i],'mAh g−1',r+' C','numeric','不判','M0056 M0067 M0072 M0073 M0074 M0075')
for a,vs in [('HME-EPSE',['24.5',None,'75.7']),('DIPS-EPSE',['43.5','97.7','172.4']),('HFE-EPSE',['101.3','284.8',None]),('DIPE-EPSE',['155.6','237.7',None])]:
 for i,v in enumerate(vs):
  if v:result(t,'Li2S成核过电位ΔE',a,None,v,None,'mV',['0.1 C','0.2 C','0.3 C'][i],'numeric','不判','M0078 M0079 M0080')
t=test(p,'T2','无LiNO3穿梭电流','CNT/S||Li coin',{'sulfur_loading':'1.1 mgS cm−2','Li_thickness':'600 μm','ES':'>15','ES_unit':'μL mgS−1','LiNO3':'0','temperature':'25 °C','electrolyte_volume':'25 μL','rate':'充至2.90V后阶梯恒电位'},['DOL/DME','HME-EPSE'],'M0098 S0015 S0021 S0022')
result(t,'峰值穿梭电流','HME-EPSE','DOL/DME','0.055','0.122','mA cm−2','2.35 V','numeric','不判','M0084')
t=test(p,'T3','温和条件长循环','CNT/S||Li coin',{'sulfur_loading':'1.1 mgS cm−2','Li_thickness':'600 μm','ES':'>15','ES_unit':'μL mgS−1','LiNO3':'2.0 wt%','temperature':'25 °C','electrolyte_volume':'25 μL','rate':'0.5 C','formation':'0.1 C 2圈','one_C':'1672 mA g−1'},['DOL/DME','HME-EPSE'],'M0098 S0015 S0016 S0021')
result(t,'寿命','HME-EPSE','DOL/DME','280','less than half HME', 'cycles','容量降至初始60%','qualitative','变好','M0099','对照数值未反算')
result(t,'初始放电容量','HME-EPSE',None,'856',None,'mAh g−1','0.5C起始','numeric','不判','M0100')
result(t,'电池阻抗','HME-EPSE','DOL/DME','13.3','14.2','Ω','100圈','numeric','不判','M0101')
t=test(p,'T4','实际条件长循环','CNT/S||Li coin',{**c,'rate':'0.1 C','voltage':'1.7–2.6 V'},['DOL/DME','HME-EPSE'],'M0101 M0102 S0018')
for met,a,b,u,pt in [('初始容量','approximately 1010','approximately 1010','mAh g−1','初始'),('寿命','113','65','cycles','循环失效'),('放电容量','860','652','mAh g−1','69圈')]:result(t,met,'HME-EPSE','DOL/DME',a,b,u,pt,'numeric','不判','M0103 M0105 M0106 M0107')
result(t,'保持率','HME-EPSE',None,'85',None,'%','69圈/初始','numeric','不判','M0107')
result(t,'库仑效率','HME-EPSE',None,'95',None,'%','69圈','numeric','不判','M0107')
t=test(p,'T5','超高载量长循环','CNT/S||Li coin',{**c,'sulfur_loading':'9.9 mgS cm−2','ES':'7.0','rate':'0.1 C','electrolyte_volume':'90 μL'},['DOL/DME','HME-EPSE'],'M0108 M0109 S0017 S0063')
for met,a,b,u,pt in [('初始容量','737','826','mAh g−1','0.1C第1圈'),('放电容量','482','168','mAh g−1','40圈'),('保持率','65','20','%','40圈/初始')]:result(t,met,'HME-EPSE','DOL/DME',a,b,u,pt,'numeric','不判','M0110 M0111')
t=test(p,'T6','软包循环','CNT/S||Li pouch',{'sulfur_loading':'7.6 mgS cm−2（单面）','Li_thickness':'75 μm（单面）','ES':'3.0','ES_unit':'gele gS−1（质量基）','rate':'0.025 C','one_C':'1000 mA g−1','LiNO3':'2.0 wt%','voltage':'1.70–2.55 V'},['HME-EPSE'],'M0118 S0029 S0030 S0031 S0032 S0033')
for met,v,u,pt in [('容量','1275','mAh g−1','初始'),('能量密度','387','Wh kg−1','初始全电池质量'),('容量','748','mAh g−1','27圈'),('能量密度','217','Wh kg−1','27圈'),('容量保持率','58','%','27圈'),('能量保持率','56','%','27圈')]:result(t,met,'HME-EPSE',None,v,None,u,pt,'numeric','不判','M0119 M0121 M0122')
t=test(p,'T7','纯溶剂还原稳定性','碳涂层Cu||Li',{'rate':'0.5 mV s−1；0–2.00 V','LiNO3':'纯溶剂未加'},['纯HME','纯DOL','纯DME'],'M0028 M0029 M0030 S0042')
for b,v in [('纯DOL','6.700'),('纯DME','15.500')]:result(t,'还原峰电流','纯HME',b,'within 0.017',v,'μA cm−2','about 0.01V','numeric','不判','M0031 M0032')
for su,a,b,pr,cats,typ,e,ts,side in [
('HME外壳减慢LiPS与金属Li的寄生反应而延长寿命','HME-EPSE','DOL/DME','多硫化物双层溶剂化',['负极锂','多硫化物穿梭'],'本文结论','M0024',['T4'],'强侧'),
('HME弱配位在外层，内层DOL/DME保持LiPS溶解和转化','HME-EPSE','DOL/DME','多硫化物溶剂化',['正极反应'],'本文结论（与他文一致）','M0039 M0050',['T1'],'其他'),
('HFE/DIPE在0.2C发生较大成核极化导致容量下降','HFE-EPSE/DIPE-EPSE','HME-EPSE','成核动力学',['正极反应'],'本文结论','M0073',['T1'],'其他'),
('HFE/DIPE在0.3C极化使第二放电平台完全丧失','HFE-EPSE/DIPE-EPSE','HME-EPSE','成核动力学',['正极反应'],'本文结论','M0074',['T1'],'其他'),
('常规对照活性Li和电解液快速消耗导致65圈过充后迅速衰减','DOL/DME','HME-EPSE','寄生反应',['负极锂','电解液消耗'],'本文结论','M0106',['T4'],'其他'),
('HME减弱LiPS与Li反应，循环后Li沉积更致密均匀','HME-EPSE','DOL/DME','多硫化物反应性',['负极锂'],'本文结论','M0116',['T4'],'强侧'),
('HME软包保持两平台，表明贫液下硫转化动力学得到保持','HME-EPSE',None,'多硫化物溶剂化',['正极反应'],'本文结论','M0123',['T6'],'其他')]:
 mech(p,su,a,b,pr,cats,typ,e,ts,side)
claim(p,'HME-EPSE平衡正极转化与负极保护；超高载量初始容量仍低于对照，不能推广为任何条件容量均不损失','M0128 M0129 M0110')
fig(p,'T3','Figure S10a','si','初始及指定圈容量','HME-EPSE','DOL/DME','0.5 C第1圈/100圈/60%终点','M0099 M0100','对照初始和寿命只给定性')
fig(p,'T4','Figure 3c','main','同圈容量','HME-EPSE','DOL/DME','113圈及交叉圈','M0103 M0105 M0106 M0107','补同圈容量；Figure S12为平行样不跨批拼值')
p['gaps']=['MD体系只有Li2S8和溶剂，不能当实际含主盐电解液的Li+配位结果','未报告电导率/黏度/迁移数/定量溶解度及Li||Cu CE','软包1C定义1000与扣电1672不同；Table S1列体积单位而正文/SI方法为质量基，采用方法并标冲突','S16标题HFE与正文HME不符，不用该图额外推论']
save(p)

