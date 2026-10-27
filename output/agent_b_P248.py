from agent_b_common import *
p=paper('P248','HCE','高浓度母液；另有LCE')
form(p,'LCE','1 M LiTFSI DME/DOL 1:1',[('LiTFSI','盐',1,'M'),('DME','溶剂',1,'体积比'),('DOL','溶剂',1,'体积比')],'M0032 S0007')
for f,tme,c in [('HCE',0,5.5),('LHCE',6,1.8)]:
 co=[('LiTFSI','盐',1,'摩尔比'),('DME','溶剂',1.5,'摩尔比'),('DOL','溶剂',1.5,'摩尔比')]
 if tme:co.append(('TME','稀释剂',tme,'摩尔比'))
 form(p,f,f'{f}，总盐浓度{c} M',co,'M0031 M0032 S0008 S0009')
grad(p,'自由溶剂/AGG结构',['LCE','HCE','LHCE'],['SSIP为主','CIP/AGG','更高AGG'],'AGG增加，自由溶剂减少','M0061 M0062 M0065 M0073 M0074 M0075')
prop(p,'S–N–S Raman峰位',{'LCE':742,'HCE':746,'LHCE':749},'升高表明更多TFSI参与Li配位','Raman','cm-1','M0061 M0062')
prop(p,'黏度/隔膜润湿',{'HCE':'高黏度不易铺展','LHCE':'低黏度快速铺展'},'LHCE改善','50 μL液滴隔膜观察','Celgard','M0115 M0116 M0117 M0118 M0119')
prop(p,'SEI',{'HCE':'少LiF及Li2CO3、寡聚物','LHCE':'更多LiF，Li2CO3消失'},'LHCE阴离子衍生无机膜增强','XPS','LiS50圈后Li表面','M0079 M0080 M0082 M0106')
t=test(p,'LiS长循环',['HCE','LHCE'],'M0124 M0125 M0126 M0127 M0130 M0131 M0132 S0010 S0011 S0014 S0022',sulfur_loading='约0.5 mg cm-2',rate='0.5 C',LiNO3='无',electrolyte_volume='约30 μL',cathode='S@KB含S71.2%，复合物/AB/PVDF80:10:10')
for metric,a,b,u,pt,ids in [('放电容量',554.68,463.69,'mAh g-1','400圈','M0125 M0130'),('容量保持率',60,48.62,'%','400圈','M0126 M0131'),('平均CE',97.73,96.52,'%','400圈','M0127 M0132')]:result(t,metric,'LHCE','HCE',a,b,u,pt,ids)
t2=test(p,'LiCu循环',['LCE','HCE','LHCE'],'M0034 M0035 M0036 M0037 M0039 M0040 M0067 S0010',cell='Li||Cu',rate='0.5 mA cm-2，1 mAh cm-2',LiNO3='无',electrolyte_volume='约60 μL')
for b,v in [('LCE',76),('HCE',82)]:result(t2,'首圈CE','LHCE',b,93.16,v,'%','首圈','M0034 M0035 M0039')
result(t2,'平均CE','LHCE',None,98.87,None,'%','120圈','M0040')
result(t2,'CE','LHCE',None,99.37,None,'%','100圈','M0039')
result(t2,'CE衰退','HCE','LCE','升至98.5后60圈下降','40圈后低于80','%','不同圈','M0034 M0036 M0037',basis='qualitative',same=False,reason='不同点仅保留各自趋势')
result(t2,'过电位','LHCE','LCE/HCE','更低并稳定','更高',None,'循环','M0053',basis='qualitative',direction='变好')
t3=test(p,'限锂累计损失',['LHCE','HCE','LCE'],'M0049 M0050 M0051 M0052',cell='预镀4 mAh cm-2 Li的Cu||Cu',rate='未报告',LiNO3='无',Li_inventory='3倍过量Li')
result(t3,'循环寿命','LHCE','HCE','>157',78,'圈','失效','M0051 M0052')
result(t3,'循环寿命','LHCE','LCE','>157',65,'圈','失效','M0051 M0052')
for excess,ce in [('4.0×',99.13),('0.5×',98.35)]:
 tt=test(p,'限锂效率'+excess,['LHCE'],'M0045 M0046 M0047 S0029',cell='Li||Cu（限Li方法）',LiNO3='无',Li_inventory=excess)
 result(tt,'CE','LHCE',None,ce,None,'%','限锂测量','M0046 M0047')
t6=test(p,'Li对称与EIS',['HCE','LHCE'],'M0110 M0111 M0112 S0030 S0031',cell='Li||Li',LiNO3='无',electrolyte_volume='约60 μL')
result(t6,'界面阻抗变化','LHCE','HCE','稳定','变化大',None,'1→100圈','M0111 M0112 S0031',basis='qualitative',direction='变好',reason='原文定性；电流条件未报告')
t7=test(p,'阳极氧化稳定性',['LHCE'],'M0121 M0122 S0019 S0024 S0033',cell='Li||SS',rate='LSV 1 mV s-1')
result(t7,'氧化稳定电压','LHCE',None,'4.5以下稳定',None,'V','LSV','M0122',basis='qualitative')
for sm,pr,cat,ids,ts in [
('降低自由溶剂抑制多硫化物溶解与穿梭。','自由溶剂','多硫化物穿梭','M0090',[t]),
('增加TFSI使盐优先还原，形成富LiF SEI。','阴离子配位','负极锂','M0138',[t2]),
('致密LiF/寡聚物SEI抑制枝晶并适应沉积剥离体积变化，提高循环表现。','SEI','负极锂','M0086',[t,t2]),
('SSIP为主弱Li配位造成松散SEI和不良锂形貌。','SSIP','负极锂','M0103',[t2]),
('LHCE的AGG主导结构形成更强SEI并促进均匀锂沉积。','AGG','负极锂','M0105',[t2]),
('LHCE界面阻抗稳定归因稳定SEI。','稳定SEI','负极锂','M0112',[t6]),
('HCE高黏度和较低离子传导限制活性材料利用率。','黏度/导电性','正极反应','M0128',[t]),
('加TME更高导电率和更低多硫化物溶解性提高利用率及容量保持。','传导/溶解','正极反应 多硫化物穿梭','M0133',[t]),
('致密SEI保护锂避免多硫化物持续腐蚀。','致密SEI','负极锂 多硫化物穿梭','M0134',[t])]:mech(p,sm,'LHCE','HCE/LCE',pr,cat,ids,ts)
p['gaps']=['E/S因电极面积未知不由30 μL及面载量推算；温度、锂厚度、1C定义未报告。','Li对称电流与限锂效率算法未见文本具体说明。','黏度/电导率缺数字，导电率提高为作者解释，不能当作数值测量。']
save(p)
