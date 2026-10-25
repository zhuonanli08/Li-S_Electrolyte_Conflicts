from agent_b_common import *
p=paper('P163','BE','高浓度母液')
form(p,'BE','6 M LiFSI/DME',[('LiFSI','盐',6,'M'),('DME','溶剂',None,None)],'M0046')
for f,n in [('HE2',2),('HE5',5)]:form(p,f,f'BE:TFTFE=1:{n}',[('BE','母液',1,'体积比'),('TFTFE','稀释剂',n,'体积比')],'M0049 M0087')
form(p,'DME2','2 M LiFSI/DME（光谱对照）',[('LiFSI','盐',2,'M'),('DME','溶剂',None,None)],'M0095')
grad(p,'TFTFE稀释梯度',['BE','HE2','HE5'],[0,2,5],'TFTFE不参与Li+溶剂化，保持局部配位','M0099 M0100 M0101')
for n,v,d,u in [('黏度',[107.72,11.34,6.20],'递减','mPa s'),('电导率',[11.53,4.59,2.41],'递减','mS cm-1')]:prop(p,n,dict(zip(['BE','HE2','HE5'],v)),d,'SI Table S6','23°C；'+u,'S0011 S0048')
prop(p,'Li–OFSI配位百分比',{'BE':58.82,'HE2':61.54},'近似保持','AIMD','百分比','S0048')
prop(p,'Li–ODME配位百分比',{'BE':41.18,'HE2':38.46},'近似保持','AIMD','百分比','S0048')
prop(p,'Li–OTFTFE配位百分比',{'HE2':0},'不参与','AIMD','百分比','S0048')
c=dict(LiNO3='无',one_C='1671 mA gS-1',temperature='未报告')
t=test(p,'S@PAN富锂半电池',['BE','HE2','HE5'],'M0142 M0145 M0147 M0148 M0149 S0024 S0025',cell='S@PAN||过量Li',sulfur_loading='2 mgS cm-2',ES=5,ES_unit='μL mgS-1',rate='0.2 C',formation='前7圈0.1 C',**c)
for point,a,b,ids in [('首圈',1498,952,'M0145 M0148'),('10圈',603,407,'M0147 M0149'),('50圈',598,386,'M0147 M0149')]:result(t,'放电容量','HE2','BE',a,b,'mAh gS-1',point,ids)
result(t,'放电容量','HE5','BE/HE2','显著更低','更高',None,'首圈及后续','S0025',basis='qualitative',direction='变坏',reason='过度稀释例外')
for es,vals,ids in [(3,[1365,696,509],'M0154'),(2,[1226,597,439],'M0155 M0156')]:
 tt=test(p,f'S@PAN限锂全电池E/S={es}',['HE2'],'M0152 M0153 '+ids,cell='S@PAN||预镀Cu上Li，N/P=2',sulfur_loading='3 mgS cm-2',ES=es,ES_unit='μL mgS-1',rate='0.05 C',**c)
 for point,v in zip(['首圈','10圈','50圈'],vals):result(tt,'放电容量','HE2',None,v,None,'mAh gS-1',point,ids)
 fig(p,tt,'Fig.4f','放电容量','HE2',None,'100圈',ids)
t4=test(p,'CMK3/S富锂电池',['HE2'],'M0165 M0166 M0167 S0026',cell='CMK3/S||Li',sulfur_loading='2 mgS cm-2',ES=5,ES_unit='μL mgS-1',**c)
for metric,v,unit,pt in [('放电容量',1519,'mAh gS-1','首圈'),('库仑效率',86,'%','首圈'),('放电容量',907,'mAh gS-1','10圈'),('容量衰减率',4,'%/圈','循环')]:result(t4,metric,'HE2',None,v,None,unit,pt,'M0166 M0167')
t5=test(p,'VS2+ZnS/Li2S/graphene混合正极全电池',['HE2'],'M0166 M0177 M0178 M0182 M0183 M0190 M0195',cell='混合正极||限Li，N/P=2',sulfur_loading='活性物7.8 mgAM cm-2，VS2计入AM',ES=2,ES_unit='μL mgS-1（仅Li2S中硫）；E/AM=0.96 μL mgAM-1',formation='先充电Li2S脱锂',**c)
for metric,v,unit,pt in [('首充容量',421,'mAh gAM-1','首充'),('放电容量',528,'mAh gAM-1','首放'),('面容量',4.12,'mAh cm-2','首放'),('能量密度',483,'Wh kg-1（两极+电解液）','首放'),('容量保持率',82,'%','14圈')]:result(t5,metric,'HE2',None,v,None,unit,pt,'M0178 M0182 M0183 M0195')
result(t5,'寿命/充电异常','HE2',None,'14圈后噪声与过充',None,None,'14圈后','M0195',basis='qualitative')
t6=test(p,'VS2独立正极',['HE2'],'S0028 S0029 S0030',cell='VS2||Li',**c)
result(t6,'循环测试','HE2',None,'至100圈；容量仅图',None,None,'100圈','S0030',basis='figure_only',reason='无数字锚点，不读图')
t7=test(p,'LiCu低电流',['HE2','BE'],'M0071 M0077 M0113 M0114 M0115 M0116 M0119 M0127',cell='Li||Cu',rate='0.5 mA cm-2；1 mAh cm-2',formation='10圈0.01–1.0 V扫；0.05 mA cm-2',separator='HE2 Celgard2400；BE Celgard3501',LiNO3='无')
for metric,a,b,unit in [('首圈CE',96.3,93.7,'%'),('首镀过电位',-35,-54,'mV'),('首剥过电位',27,45,'mV')]:result(t7,metric,'HE2','BE',a,b,unit,'首圈','M0116 M0119',same=False,reason='隔膜不同，配方因果不单独判')
result(t7,'平均CE','HE2',None,99.4,None,'%','350圈','M0127')
result(t7,'CE异常','BE',None,'多圈超过100%',None,None,'包括26圈','M0120 M0122',basis='qualitative',reason='不可把过100%判优')
t8=test(p,'LiCu高电流',['HE2'],'M0124 M0125 M0126 M0127 M0157',cell='Li||Cu',rate='2 mA cm-2；1 mAh cm-2',LiNO3='无')
result(t8,'平均CE','HE2',None,99.3,None,'%','350圈','M0127')
result(t8,'CE','HE2',None,98.7,None,'%','30圈','M0126')
result(t8,'过电位','HE2',None,'190→130',None,'mV','首圈→30圈','M0125')
t9=test(p,'Li对称阶梯电流',['HE2','BE'],'M0071 M0078 M0079 M0128 M0129 M0130',cell='Li||Li',rate='0.5→1→2→0.5 mA cm-2各20圈，1 mAh cm-2',separator='HE2 2400；BE 3501',LiNO3='无')
result(t9,'过电位','HE2','BE',15,31,'mV','0.5 mA cm-2','M0129',same=False,reason='隔膜不同')
for sm,pr,cat,ids,ts,src in [
('TFTFE添加保持盐配位结构，不参与Li+溶剂化。','溶剂化保持','', 'M0100 M0101',[t],'本文结论'),
('HE2更佳润湿可能解释其比BE更高初始容量。','润湿','正极反应','M0148',[t],'本文推测'),
('HE5过度稀释可能减少Li+与硫接触，损害循环。','过度稀释','正极反应','M0151',[t],'本文推测'),
('首圈不可逆容量可能与CEI形成和S–S断裂有关。','CEI/断键','正极反应','M0146',[t],'本文推测'),
('TFTFE优先脱氟部分贡献更强LiF峰。','含氟SEI','负极锂','M0141',[t7],'本文结论（与他文一致）'),
('TFTFE促进富LiF SEI形成，使锂表现高可逆效率。','富LiF SEI','负极锂','M0210',[t7],'本文结论'),
('BE超100%效率可能由此前隔绝锂重新与集流体接通。','死锂再连接','负极锂','M0121',[t7],'本文推测'),
('混合正极失效可能由贫液中浓多硫化物驱动穿梭和电解液耗尽。','浓多硫化物','多硫化物穿梭 电解液消耗','M0196',[t5],'本文推测'),
('TFTFE空间上缩窄离子有效路径，降低Li+及多硫化物迁移。','离子通道','正极反应 多硫化物穿梭','M0207',[t],'本文结论'),
('稀释剂可能帮助减轻多硫化物穿梭。','稀释/迁移','多硫化物穿梭','M0208',[t],'本文推测'),
('TFTFE改善碳硫复合正极润湿，在贫液下促进电解液吸收。','润湿','正极反应','M0211',[t],'本文结论')]:mech(p,sm,'HE2','BE',pr,cat,ids,ts,source=src)
p['gaps']=['LiCu及Li对称BE/HE2使用不同隔膜，比较不满足同条件。','正文OCR μL常显示mL；SI S0026和表头明确μL mg-1。','锂厚度未给；0.38 mm是合成Li2S使用原料，不作为电池厚度。','S@PAN、CMK3/S及混合正极机制/循环应分开；混合正极14圈后失效。','HE5容量仅SI图且无数值锚点，保留原文定性下降。']
save(p)
