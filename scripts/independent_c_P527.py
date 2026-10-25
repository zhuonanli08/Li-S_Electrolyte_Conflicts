from independent_c_helpers import *
p=init('P527')
form(p,'DOL/DME','1M LiTFSI DOL/DME1:1 +2wt%LiNO3',[('LiTFSI','salt',1,'M'),('DOL','solvent',1,'volume ratio'),('DME','solvent',1,'volume ratio'),('LiNO3','additive',2,'wt%')],'M0063 S0018')
for n in [4,6,8,10]:
 form(p,'H'+str(n),f'1 M LiTFSI, HMPA {n} vol% in DOL, 2 wt% LiNO3',[('LiTFSI','salt',1,'M'),('HMPA','cosolvent',n,'vol%'),('DOL','solvent','余量',''),('LiNO3','additive',2,'wt%')],'M0061 M0062 S0019 S0020')
A='H6';B='DOL/DME';p['control_id']=B;p['control_type']='常规醚基电解液'
grad(p,'HMPA体积分数',['H4','H6','H8','H10'],[4,6,8,10],'未直接建立连续溶剂化轴；强配位HMPA含量','M0061 M0062')
prop(p,'离子电导率',{'H6':4.51},'随HMPA先升后降，6vol%最大','EIS','mS cm−1','M0067 M0071 S0034 S0035 S0036')
prop(p,'Li+迁移数',{'H6':0.88},'随HMPA先升后降，6vol%最大','恒电位极化/EIS','Li||Li','M0067 M0071 S0047 S0049 S0050')
prop(p,'Li+传输活化能',{A:14.1,B:19.3},'H6降低','变温电导Arrhenius','kJ mol−1','M0068 S0039')
prop(p,'Li+溶剂化',{A:'HMPA内层强配位、游离HMPA少',B:'较弱DME配位、更多游离DME'},'H6增强','MD/Raman','实际电解液','M0077 M0079 M0080 M0082 M0083 M0091')
prop(p,'CIP+AGG比例',{A:83.7,B:78.5},'H6增加','Raman','%','M0089')
prop(p,'多硫化物溶解/穿梭',{A:'更低'},'H6降低','可视电池/漏电流','放电过程','M0175 M0176 M0177 M0184')
C={'LiNO3':'2 wt%','electrolyte_volume':'40 µL'}
def T(id,name,cell,c,e):
 return test(p,id,name,cell,dict(C,**c),[A,B],e)
t=T('T1','锂对称倍率','Li||Li',{'rate':'0.5,1,2,5 mA cm−2；1 mAh cm−2'},'M0095 M0096 S0040 S0042')
result(t,'极化','H6',B,'所有倍率更低',None,None,'0.5–5 mA cm−2','qualitative','变好','M0096')
t=T('T2','1mA锂对称循环','Li||Li',{'rate':'1 mA cm−2；1 mAh cm−2'},'M0099 M0100 M0101 S0043')
result(t,'稳定极化',A,B,'ca.0.05','最大0.11','V','初始后至600h','numeric','不判','M0100 M0101','稳定值与对照最大值不是相同时间统计')
result(t,'初始极化',A,None,'ca.0.14',None,'V','initial','numeric','不判','M0100')
result(t,'极化稳定性',A,B,'稳定至600h','明显波动',None,'循环','qualitative','变好','M0100 M0101')
t=T('T3','5mA锂对称循环','Li||Li',{'rate':'5 mA cm−2；1 mAh cm−2'},'M0102 M0226 S0043')
result(t,'极化',A,B,'~0.06','最大~0.25','V','600h循环','numeric','不判','M0102 M0226','对照最大值，非同一时间点')
result(t,'极化稳定性',A,B,'较低且稳定',None,None,'600h','qualitative','变好','M0102 M0226')
t=T('T4','锂界面动力学','Li||Li',{'rate':'LSV0.1 mV s−1；EIS'},'M0097 M0141 M0149 M0154 S0044')
for metric,va,vb,u,pt,e in [('交换电流密度',.22,.12,'mA cm−2','LSV','M0097'),('Rs',3.9,4.0,'Ω','before cycling','M0141'),('Rct',93.6,138.0,'Ω','before cycling','M0141'),('RE-SEI',11.0,17.4,'Ω','10 cycles','M0154 M0149'),('RSEI-Li',16.1,23.9,'Ω','10 cycles','M0154 M0149')]:
 result(t,metric,A,B,va,vb,u,pt,'numeric','不判',e)
t=T('T5','Li-S界面','S@RGO||Li',{'rate':'0.1 C','one_C':'1675 mA g−1'},'M0164 M0166 M0170 S0052')
for m,va,vb,pt,e in [('Rct',29.0,55.5,'before cycling','M0164'),('电解液/电极阻抗',15.2,34.7,'10 cycles','M0170'),('SEI/Li阻抗',16.5,22.2,'10 cycles','M0170')]:
 result(t,m,A,B,va,vb,'Ω',pt,'numeric','不判',e)
t=test(p,'T6','可视放电','S@RGO||Li visible',{'LiNO3':'2wt%','electrolyte_volume':'10 mL'},[A,B],'M0173 M0174 M0175 S0058')
result(t,'放电容量',A,B,966.6,420.0,'mAh g−1','可视放电','numeric','变好','M0174')
result(t,'电解液变色',A,B,'轻微且仅初期','明显黄绿色',None,'放电','qualitative','不判','M0175 M0176')
t=T('T7','穿梭漏电流','S@RGO||Li',{'formation':'1.7–2.7 V初始放充；放至1.7 V','rate':'2.2,2.35,2.4,2.5,2.6 V各恒压20h'},'M0184 S0055 S0056')
result(t,'漏电流',A,B,.57,1.4,'mA g−1','2.35 V稳定电流','numeric','变好','M0184')
t=T('T8','硫反应CV','S@RGO||Li',{'rate':'0.1–0.5 mV s−1'},'M0191 M0199 M0201 M0203 S0082 S0083')
result(t,'氧化还原峰电流',A,B,'更强',None,None,'CV','qualitative','变好','M0199 M0200')
for peak,va,vb in [('C','2.66e−8','9.60e−9'),('D','8.36e−8','3.78e−8')]:
 result(t,'Li扩散系数',A,B,va,vb,'cm2 s−1','peak '+peak,'numeric','变好','M0203')
t=T('T9','0.1C充放电','S@RGO||Li',{'rate':'0.1 C','one_C':'1675 mA g−1'},'M0205 M0207 M0208 M0211 M0212 S0052')
for m,va,vb,u,pt,e in [('比容量',1374.9,1043.9,'mAh g−1','0.1C','M0207'),('低/高平台容量比',2.21,2.06,None,'2.12/2.29 V','M0208'),('Li2S成核过电位',21,34,'mV','放电','M0211'),('Li2S分解过电位',60,91,'mV','充电','M0212')]:
 result(t,m,A,B,va,vb,u,pt,'numeric','不判',e)
t=T('T10','Li-S倍率','S@RGO||Li',{'rate':'0.1–2 C','one_C':'1675 mA g−1'},'M0214 M0215 M0216 M0217 S0052')
result(t,'比容量',A,B,606.4,181.5,'mAh g−1','2 C','numeric','变好','M0216')
result(t,'比容量',A,None,1110.4,None,'mAh g−1','initial 0.1 C','numeric','不判','M0217')
result(t,'比容量',A,None,939.2,None,'mAh g−1','return 0.1 C','numeric','不判','M0217')
result(t,'倍率容量',A,B,'各倍率更高',None,None,'0.1–2 C','qualitative','变好','M0215')
t=T('T11','Li-S循环','S@RGO||Li',{'rate':'0.2 C','formation':'0.1 C 3 cycles','one_C':'1675 mA g−1'},'M0195 M0218 M0219 M0220 S0052')
result(t,'比容量',A,B,1101.0,882.4,'mAh g−1','initial 0.2C','numeric','变好','M0219')
result(t,'比容量',A,B,619.6,295.6,'mAh g−1','300 cycles','numeric','变好','M0220','引言与结论对照写295.2；此处保留结果段295.6')
for summary,pr,cats,typ,e,ts,side in [
('HMPA强配位使其进入Li+内壳，减少游离分子并抑制多硫化物溶解/穿梭','Li+溶剂化',['多硫化物穿梭'],'本文结论','M0080 M0083 M0091 M0224',['T6','T7','T11'],'强侧'),
('HMPA中LiTFSI溶解度低，通过同离子效应预计降低多硫化物溶解','盐溶解度',['多硫化物穿梭'],'本文推测','M0043 M0044 M0045',['T6','T7'],'其他'),
('更紧凑Li+溶剂化半径促进传输，但过量HMPA提高黏度降低电导和迁移数','Li+溶剂化/黏度',['正极反应','负极锂'],'本文结论','M0070 M0071 M0077 M0078 M0098',['T1','T4'],'强侧'),
('更多CIP/AGG促进TFSI还原生成LiF丰富SEI，均匀Li沉积并抑制枝晶','阴离子配位',['负极锂'],'本文结论','M0119 M0120 M0122 M0124 M0125 M0225',['T1','T2','T3'],'其他'),
('致密LiF丰富SEI阻止Li/电解液副反应与电解液消耗','SEI',['负极锂','电解液消耗'],'本文结论','M0126 M0127 M0128 M0137',['T2','T3'],'其他'),
('HMPA高DN预计促进Li2S溶解与均匀沉积，保持孔隙并缓解正极钝化','高DN/沉积',['正极反应'],'本文结论（与他文一致）','M0158 M0159 M0160 M0161 M0162',['T5','T9'],'强侧'),
('多孔正极与LiF丰富SEI降低Li-S界面阻抗','界面结构',['正极反应','负极锂'],'本文结论','M0170 M0171',['T5'],'其他'),
('HMPA溶剂化结构可能促进多硫化物/Li2S互转，降低成核和分解过电位','Li+溶剂化',['正极反应'],'本文推测','M0209 M0211 M0212 M0213',['T9'],'强侧'),
('抑制穿梭解释长期循环改善','多硫化物行为',['多硫化物穿梭'],'本文结论','M0222',['T11'],'强侧')]:
 mech(p,summary,A,B,pr,cats,typ,e,ts,side)
claim(p,'用高Li亲和力且低盐/多硫化物溶解度的HMPA兼顾传输、锂保护及穿梭抑制','M0032 M0033 M0034 M0035 M0036 M0223 M0224 M0225')
fig(p,'property-gradient','Fig.2c,d','main','电导率及Li迁移数','H4/H6/H8/H10',B,'各浓度','M0067','6vol%最大4.51mS/cm及0.88为锚，补其他梯度值')
p['gaps']=['硫载量、Li厚度、E/S和实验温度未报告；40µL不能换算E/S。','300圈对照容量结果段M0220为295.6，M0038/M0227为295.2 mAh g−1，未擅自统一。','Li对称稳定极化和对照最大极化统计口径不同，不作同点数值比较。']
save(p)

