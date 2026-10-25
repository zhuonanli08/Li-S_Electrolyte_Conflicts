from independent_c_helpers import *
p=init('P525')
form(p,'CE','1.0 M LiTFSI, DOL/DME 1:1 v/v, 2 wt% LiNO3',[('LiTFSI','salt',1,'M'),('DOL','solvent',1,'volume ratio'),('DME','solvent',1,'volume ratio'),('LiNO3','additive',2,'wt%')],'M0036')
form(p,'STE','1.0 M LiTFSI, MPE/DOL/DME 4:3:3 v/v/v, 2 wt% LiNO3',[('LiTFSI','salt',1,'M'),('methyl propyl ether (MPE)','solvent',4,'volume ratio'),('DOL','solvent',3,'volume ratio'),('DME','solvent',3,'volume ratio'),('LiNO3','additive',2,'wt%')],'M0036 M0040')
p['control_id']='CE';p['control_type']='常规醚基电解液'
grad(p,'MPE比例筛选',['CE','STE'],{'CE':'0 vol%','STE':'40 vol%','其他浓度':'仅图S1，未转录'},'Li+溶剂化减弱','M0053 S0059')
for n,vals,d,m,e in [('黏度',{'STE':'低于CE'},'STE降低','流变/MD','M0050 M0051 M0052 M0054 M0055 S0020'),('润湿/接触角',{'STE':'接触角更低、渗透更好'},'STE润湿增强','接触角','M0056 M0057 S0061'),('Li+溶剂化',{'CE':'更强','STE':'Li-TFSI配位增加、溶剂配位减弱'},'STE减弱','MD/Raman','M0070 M0071 M0073 M0086 M0087 M0088 M0089 M0090'),('多硫化物溶解度',{'STE':'Li2S8/Li2S4峰降低'},'STE降低','UV-vis','M0085 S0063'),('Li+去溶剂化势垒',{'STE':'降低'},'STE降低','MD/变温EIS','M0113 M0114 M0115 M0117 S0071 S0072'),('电荷转移阻抗',{'STE':'低于CE'},'STE降低','EIS','M0141 S0081')]:
 prop(p,n,vals,d,m,'CE/STE',e)
prop(p,'7Li NMR化学位移',{'CE':'−0.060','STE':'−0.035'},'向高频移动','7Li NMR','Li2S8模型体系；主文与SI配方表述不同','M0091 M0092 S0019')
t=test(p,'T1','Li沉积剥离效率','Li||Cu',{'LiNO3':'2 wt%'},['CE','STE'],'M0121 S0074')
result(t,'库仑效率','STE','CE',98.5,None,'%','over 300 cycles','numeric','不判','M0121','对照无文字数值')
result(t,'过电位','STE','CE','更低',None,None,'循环','qualitative','变好','M0121')
for i,cur,e in [(2,'0.32 mA cm−2 / 0.32 mAh cm−2','S0077'),(3,'1 mA cm−2 / 1 mAh cm−2','S0077 S0078')]:
 t=test(p,'T'+str(i),'锂对称循环','Li||Li',{'rate':cur,'LiNO3':'2 wt%'},['CE','STE'],e+' M0126 M0127')
 result(t,'极化/稳定性','STE','CE','更低且稳定','不稳定',None,'循环','qualitative','变好','M0126 M0127')
t=test(p,'T4','锂对称倍率','Li||Li',{'rate':'3 mA cm−2','LiNO3':'2 wt%'},['CE','STE'],'M0128 S0079')
result(t,'短路','STE','CE','正常','短路',None,'3 mA cm−2','qualitative','变好','M0128')
t=test(p,'T5','Li2S沉积','carbon paper||Li',{'rate':'先恒流至2.06 V，再恒压2.05 V至<1e−5 A','electrolyte':'正极20 µL 0.2 M Li2S6；负极20 µL CE/STE'},['CE','STE'],'S0010 S0011 S0012 M0157 M0158 M0159')
result(t,'沉积动力学/形貌','STE','CE','更快3D','较慢2D',None,'Li2S沉积','qualitative','变好','M0157 M0158 M0159 S0084')
t=test(p,'T6','CV硫反应','HCG/S||Li',{'rate':'0.1–0.5 mV s−1','voltage':'1.7–2.8 V','LiNO3':'2 wt%'},['CE','STE'],'M0149 M0150 M0151 S0006 S0082 S0083')
result(t,'极化','STE','CE','更低',None,None,'CV','qualitative','变好','M0150')
result(t,'Li+扩散系数','STE','CE','更高',None,None,'Randles–Sevcik','qualitative','变好','M0155 M0156')
t=test(p,'T7','室温倍率','HCG/S||Li',{'rate':'0.2–5 C','LiNO3':'2 wt%'},['CE','STE'],'M0160 M0161 M0164')
result(t,'倍率性能','STE','CE','更好',None,None,'0.2–5 C','qualitative','变好','M0160')
result(t,'容量恢复','STE',None,'恢复',None,None,'返回0.5 C','qualitative','不判','M0161')
t=test(p,'T8','0.5C循环','HCG/S||Li',{'rate':'0.5 C','LiNO3':'2 wt%'},['CE','STE'],'M0169 S0085 S0086')
result(t,'容量保持','STE','CE','更高',None,None,'长期循环','qualitative','变好','M0169')
result(t,'容量','STE',None,1067,None,'mAh g−1','0.5 C；表S4本工作行','numeric','不判','S0108','表中汇总值，不能假定具体循环点')
t=test(p,'T9','5C循环','HCG/S||Li',{'rate':'5 C','sulfur_loading':'1.1 mg cm−2','ES':15,'ES_unit':'µL mg−1','LiNO3':'2 wt%'},['CE','STE'],'M0165 M0170 S0108')
result(t,'容量保持','STE','CE','较稳定','快速衰减',None,'5 C','qualitative','变好','M0170')
result(t,'高倍率容量','STE',None,944,None,'mAh g−1','5 C；表S4本工作行','numeric','不判','S0108','具体循环点未写')
result(t,'单圈衰减','STE',None,0.095,None,'%','500 cycles at 5 C','numeric','不判','S0108')
fig(p,'T9','Fig.5c','main','放电容量','STE','CE','同一循环点，优先500圈','M0165 M0170 S0108','表S4提供本工作5C容量/循环锚；需先确认944对应点，无法匹配则不读数')
t=test(p,'T10','贫液软包','HCG/S||Li pouch',{'sulfur_loading':'5.2 mg cm−2','ES':5,'ES_unit':'µL mg−1','Li_thickness':'50 µm','LiNO3':'2 wt%'},['STE'],'M0166 M0173 M0174 M0175 S0051 S0052 S0053 S0054 S0055')
result(t,'放电容量','STE',None,1070,None,'mAh g−1','initial','numeric','不判','M0173 S0055')
result(t,'放电容量','STE',None,770,None,'mAh g−1','80 cycles','numeric','不判','M0175')
result(t,'比能量','STE',None,318.8,None,'Wh kg−1','不含包装和极耳','numeric','不判','M0174 S0054')
t=test(p,'T11','低温倍率','HCG/S||Li',{'temperature':'−30 °C','rate':'最高3 C','LiNO3':'2 wt%'},['CE','STE'],'M0179 M0180 M0181 M0182 M0183 S0093 S0094')
result(t,'可工作倍率','STE','CE','3 C','1 C时停滞',None,'−30 °C','qualitative','变好','M0179')
t=test(p,'T12','低温循环','HCG/S||Li',{'temperature':'−30 °C','rate':'0.5 C','sulfur_loading':'1.1 mg cm−2','ES':25,'ES_unit':'µL mg−1','LiNO3':'2 wt%'},['CE','STE'],'M0167 M0184')
result(t,'循环容量','STE','CE','可运行100圈','容量明显降低',None,'100 cycles','qualitative','变好','M0184')
fig(p,'T12','Fig.5e','main','放电容量','STE','CE','100 cycles','M0184','正文只给循环数没有同点容量锚；不可无锚读整图')
for args in [
('MPE减少配位氧和螯合效应，弱化Li+溶剂化并降低脱溶剂化能垒，从而改善硫反应动力学','Li+溶剂化',['正极反应'],'M0068 M0070 M0071 M0113 M0114 M0115 M0117',['T5','T6','T7'],'弱侧'),
('短碳链MPE降低空间位阻，使Li更容易接近多硫化物单体；抑制溶解仍可加速硫转化','空间位阻/多硫化物溶解度',['正极反应'],'M0137 M0138 M0139 M0189',['T5','T6'],'弱侧'),
('低黏度改善传质与硫反应；CE在60% DOD因多硫化物堆积和迟缓传质阻抗突升','黏度',['正极反应'],'M0054 M0055 M0146',['T6','T7'],'弱侧'),
('MPE在多硫化物外溶剂化壳层形成抗还原保护，减少多硫化物与Li寄生反应','多硫化物溶剂化',['负极锂'],'M0083 M0093 M0094 M0118',['T1','T2','T3'],'弱侧'),
('均匀Li扩散和浓度分布降低极化并促进平滑沉积','传质',['负极锂'],'M0123 M0124 M0134',['T1','T2','T3','T4'],'其他'),
('LiF/Li3N致密SEI抑制锂腐蚀、死锂和电解液消耗','SEI',['负极锂','电解液消耗'],'M0204 M0205 M0206 M0207',['T1','T9'],'其他'),
('STE中S信号几乎消失被归因为减少多硫化物穿梭及与Li副反应','多硫化物行为',['多硫化物穿梭','负极锂'],'M0210 M0211',['T9'],'弱侧'),
('STE减少正极厚重副产物和电解液分解','界面稳定性',['正极反应','电解液消耗'],'M0191 M0192 M0199 M0200 M0201 M0202',['T9'],'其他'),
('低温改善来自弱溶剂化降低脱溶剂化和降低位阻促进硫反应','Li+溶剂化/位阻',['正极反应'],'M0180 M0181 M0182 M0183 M0212 M0213 M0214 M0215',['T11','T12'],'弱侧')]:
 summary,pr,cats,e,ts,side=args;mech(p,summary,'STE','CE',pr,cats,'本文结论',e,ts,side)
claim(p,'协同弱化溶剂化与降低位阻，而非仅压低多硫化物溶解，实现高倍率、贫液软包与低温运行','M0212 M0213 M0214 M0215')
p['gaps']=['除软包外Li厚度、一般活化、1C定义未见明确文字；不同图的E/S不外推。','MPE浓度筛选图S1其他梯度值未提供文字，不能补猜。','SI表S1将MPE写为methyl butyl ether，与主文methyl propyl ether不一致。','NMR主文描述纯溶剂混合物，SI写0.2M Li2S8在CE/STE，按模型条件不合并。','表S4本工作容量1067/944未注明具体循环点；不跨图配对。','锂半电池电流条件仅明确写出部分；COMSOL参数不是实验条件。']
save(p)

