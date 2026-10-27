from agent_b_common import *
p=paper('S37','DME1','1 M LiTFSI/DME')
for f,s,c in [('DME1','DME',1),('DME2','DME',2),('DME4','DME',4),('G4','G4',1),('THF','THF',1),('DMSO','DMSO',1)]:form(p,f,f'{c} M LiTFSI/{s}',[('LiTFSI','盐',c,'M'),(s,'溶剂',None,None)],'M0055 M0162 S0008')
form(p,'DD','1 M LiTFSI DOL/DME',[('LiTFSI','盐',1,'M'),('DOL','溶剂',None,'混合比例正文未写'),('DME','溶剂',None,'混合比例正文未写')],'M0055 S0007')
for f,a,b in [('DT64',6,4),('DT11',1,1),('DT46',4,6),('DT14',1,4)]:form(p,f,f'1 M LiTFSI DME/TTE {a}:{b}',[('LiTFSI','盐',1,'M（图总说明）'),('DME','溶剂',a,'体积比'),('TTE','稀释剂',b,'体积比')],'M0055 M0061 S0006 S0007')
form(p,'MTBE','MTBE弱溶剂化样',[('LiTFSI','盐','未明确','M'),('MTBE','溶剂',None,None)],'S0006')
grad(p,'同溶剂浓度',['DME1','DME2','DME4'],[1,2,4],'浓度增加→更正Li溶剂化自由能→更弱溶剂化','M0046 M0047')
grad(p,'TTE稀释',['DME1','DT64','DT11','DT46','DT14'],[0,'4/10','1/2','6/10','4/5'],'TTE增加→溶剂化变弱','M0048 M0050 S0006')
grad(p,'醚供体溶剂',['DD','DME1','G4'],['DOL/DME','DME','G4'],'DOL到DME到G4变强；DD为混合不等于纯DOL','M0051')
prop(p,'相对Li+溶剂化自由能',{'DME4':'更正更弱','DME1':'更负更强'},'浓度、稀释剂共同调节','非对称电解液LiH电池电位','以1 M LiFSI DEC为参考；含浓度化学势，不是无限稀释自由能','M0039 M0040 M0180 M0181 M0182')
prop(p,'Li2S6溶解度',{'弱溶剂化':'较低','强溶剂化':'较高'},'随溶剂化变弱降低','UV-vis','饱和溶液；G4因自由基物种排除','M0097 M0098 M0099')
prop(p,'Li+聚簇与扩散',{'DME1':'更多未聚簇Li，更高扩散','DT11':'更多聚簇、较低扩散'},'强溶剂化促进解离','MD和DOSY-NMR','0.1 M Li2S6模型，非1 M盐电池电解液','M0082 M0085 M0087 M0088')
fs=['DME1','DME2','DME4','G4','THF','DD','DT64','DT11','DT46']
c=dict(sulfur_loading='1–2 mg cm-2',ES='15（原文单位倒置mg μL-1）',ES_unit='原文mg μL-1，疑为μL mg-1，未静默修正',Li_thickness='约500 μm',LiNO3='无',temperature='空调室，无温控箱',one_C='1675 mA gS-1',voltage='1.7–2.8 V')
t=test(p,'低倍率平台热力学',fs+['DMSO'],'M0061 M0062 M0064 M0067 M0068 M0169 M0171 M0172 M0174 S0007 S0008',rate='C/20',formation='前两圈',**c)
result(t,'第一平台电压','弱溶剂化','强溶剂化','较低','较高',None,'C/20平台平均','M0064 M0067',basis='qualitative',direction='变坏',reason='按电压高低；不等同总能量方向')
result(t,'第二平台电压','弱溶剂化','强溶剂化','较高','较低',None,'C/20平台平均','M0064 M0067',basis='qualitative',direction='变好')
t2=test(p,'LiS 150圈循环',fs,'M0112 M0114 M0121 M0128 M0169 M0171 M0172 M0173 S0018',rate='C/5',formation='2圈C/20+3圈C/10',**c)
result(t2,'平均库仑效率','弱溶剂化','强溶剂化','较高','较低',None,'150圈平均','M0112 M0128',basis='qualitative',direction='变好')
result(t2,'初始放电容量','弱溶剂化','强溶剂化','较高','较低',None,'初始','M0114 M0128',basis='qualitative',direction='变好',reason='仅所研究中等至强溶剂化范围')
result(t2,'容量保持率','中等溶剂化','强/更弱溶剂化','在−10至−12 kJ mol-1处最高','较低',None,'循环','M0121',basis='qualitative',direction='变好',reason='非单调；不能说越弱循环越好')
fig(p,t2,'Supplementary Fig.11','放电容量',fs,None,'150圈','M0128 S0018',part='si',reason='无可抄逐配方数值，150圈是横轴锚点；有效几何读图须满足数值锚点条件')
t3=test(p,'动力学倍率极化',fs,'M0118 M0119 S0017',rate='0.05 C和0.2 C差',**c)
result(t3,'第二平台过电位','弱溶剂化','强溶剂化','更高','更低',None,'0.05 C与0.2 C平台差','M0119',basis='qualitative',direction='变坏')
t4=test(p,'极弱溶剂化放电',['DT14','MTBE'],'M0044 M0122 S0006',rate='未报告',**c)
result(t4,'放电容量','DT14/MTBE','中等强溶剂化','极低','较高',None,'放电','S0006',basis='qualitative',direction='变坏',same=None,reason='SI图注无完整测试条件，不做严格配方同条件判向')
for withps in [False,True]:
 tt=test(p,'改良Aurbach '+('饱和LiPS' if withps else '无LiPS'),fs,'M0127 M0132 M0133 M0134 M0165 M0175 S0021 S0022',cell='Li||Cu/20 μm薄Li',Li_thickness='工作Cu上20 μm',LiNO3='无',rate='0.5 mA cm-2',formation='5 mAh cm-2镀/剥至1 V形成；5 mAh cm-2储库；10圈1 mAh cm-2；终剥至1 V',LiPS='饱和Li2S6' if withps else '无')
 result(tt,'Li金属CE','弱溶剂化','强溶剂化','较高','较低',None,'改良Aurbach','M0133 M0134',basis='qualitative',direction='变好')
 result(tt,'可测性','DME1/DME2/G4',None,'CE太低不能纳入图',None,None,'改良Aurbach','M0132',basis='qualitative',reason='低于方法可可靠测量范围，不能填0')
 if withps:result(tt,'LiPS引起CE变化','饱和LiPS','无LiPS','整体低约3%',None,'百分点（原文about3%）','改良Aurbach','M0134',basis='qualitative',direction='变坏',reason='同配方有无LiPS的整体趋势')
for sm,pr,cat,ids,src in [
('强溶剂化稳定LiPS并降低其自由能，使第一平台更高。','LiPS自由能','正极反应','M0074 M0076 M0077','本文推测'),
('强溶剂化LiPS低自由能降低到Li2S的自由能差，使第二平台更低。','LiPS自由能','正极反应','M0079','本文推测'),
('低LiPS溶解性减轻向锂穿梭，提高全电池CE。','溶解性','多硫化物穿梭','M0113','本文结论（与他文一致）'),
('穿梭使硫在负极变为不溶Li2S/Li2S2或自放电，降低初始容量。','活性硫损失','多硫化物穿梭 负极锂','M0116','本文推测'),
('弱溶剂化极化较大可能因LiPS浓度不足，缺少加速电荷转移的氧化还原媒介。','LiPS媒介','正极反应','M0120','本文推测'),
('不含LiNO3时LiPS可能不能稳定锂，反而有害。','LiPS与添加剂','负极锂','M0136','本文推测'),
('LiPS可能促进成核而非生长，增加小核面积及副反应。','锂成核','负极锂','M0142','本文推测'),
('LiPS可能改变溶剂化能，使高表面积锂形貌更有利。','界面能','负极锂','M0146','本文推测'),
('添加TTE时SEI更富无机、F和S。','SEI','负极锂','M0148','本文结论（与他文一致）'),
('加入LiPS后SEI更富S，可能源于LiPS分解。','LiPS分解','负极锂','M0149','本文推测')]:mech(p,sm,'弱侧','强侧',pr,cat,ids,[t,t2],source=src)
p['gaps']=['大多数所有配方数字仅图，无原句数值，保留定性趋势并避免目测。','本文E/S单位mg μL-1反写，未猜改。','DOL/DME比例正文未列；图仅称DOL-DME。','LiPS模型MD/NMR与LiTFSI电池配方不同。','极弱DT14和MTBE图注无完整盐浓度/条件；MTBE盐浓度未猜。','LiNO3全部无，本文结论不可外推其协同成膜体系。']
save(p)
