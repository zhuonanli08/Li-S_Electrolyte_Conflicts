from independent_c_helpers import *
p=init('P564')
for c in [.2,.5,.8,1.0]:
 form(p,'E'+str(c),f'{c}M LiTFSI+0.3M LiNO3 DOL/DME1:1',[('LiTFSI','salt',c,'M'),('LiNO3','additive',.3,'M'),('DOL','solvent',1,'volume ratio'),('DME','solvent',1,'volume ratio')],'S0013')
 form(p,'D'+str(c),f'{c}M LiTFSI DOL模型',[('LiTFSI','salt',c,'M'),('DOL','solvent','纯溶剂','')],'M0044')
 form(p,'F'+str(c),f'{c}M LiFSI DME模型',[('LiFSI','salt',c,'M'),('DME','solvent','纯溶剂','')],'M0048 S0076')
form(p,'EB','0.8M LiTFSI+0.2M LiBr+0.3M LiNO3 DOL/DME1:1',[('LiTFSI','salt',.8,'M'),('LiBr','salt',.2,'M'),('LiNO3','additive',.3,'M'),('DOL','solvent',1,'volume ratio'),('DME','solvent',1,'volume ratio')],'S0013')
for t,b in [(.8,.2),(.5,.5),(.2,.8),(0,1)]:
 form(p,'DB'+str(t),f'{t}M LiTFSI+{b}M LiBr DOL模型',[('LiTFSI','salt',t,'M'),('LiBr','salt',b,'M'),('DOL','solvent','纯溶剂','')],'M0189 M0190 M0191 M0197')
for x,y in [(10,0),(8,2),(7,3),(6,4),(5,5),(4,6),(3,7),(2,8),(0,10)]:
 form(p,f'C{x}',f'CS2:DOL={x}:{y}摩尔比模型',[('CS2','model solvent',x,'molar ratio'),('DOL','model solvent',y,'molar ratio')],'M0051 M0052')
for id,c,b in [('P1',1,0),('P08',.8,0),('PB',.8,.2)]:
 form(p,id,f'歧化实验{c}M LiTFSI/{b}M LiBr DOL/DME2:1',[('LiTFSI','salt',c,'M'),('LiBr','salt',b,'M'),('DOL','solvent',2,'volume ratio'),('DME','solvent',1,'volume ratio')],'M0138 M0140 M0221 S0123')
p['control_id']='E1.0';p['control_type']='1M常规醚基电解液'
grad(p,'LiTFSI浓度',['E0.2','E0.5','E0.8','E1.0'],[.2,.5,.8,1.0],'随盐增加未极化醚减少；S8溶解非线性','M0044 M0045 M0046 M0095')
grad(p,'DOL中LiTFSI/LiBr替换',['DB0','DB0.2','DB0.5','DB0.8','D1.0'],['0/1','0.2/0.8','0.5/0.5','0.8/0.2','1/0'],'LiBr缔合离子对弱极化；LiTFSI解离强极化','M0189 M0190 M0191 M0202 M0206')
grad(p,'CS2/DOL摩尔比例',['C0','C2','C3','C4','C5','C6','C7','C8','C10'],['0:10','2:8','3:7','4:6','5:5','6:4','7:3','8:2','10:0'],'S8溶剂化/溶解能非线性阈值','M0051 M0052 M0054')
prop(p,'S8溶解度',{'D0.2':4.3,'D0.5':4.0,'D0.8':3.7,'D1.0':1.0},'0.8至1M骤降','Raman','DOL模型，mg mL−1','M0044')
prop(p,'S8溶解度',{'C0':5.1,'C2':12,'C3':14,'C4':20,'C5':51,'C6':55,'C7':57,'C8':59,'C10':60.0},'4:6至5:5骤增','蒸干称重','CS2/DOL无盐模型，mg mL−1','M0051 M0052 S0214 S0215 S0216')
prop(p,'S8溶解度',{'DB0.8':3.65,'DB0.5':3.85,'DB0.2':4.1,'D0.8':3.70,'D0.5':4,'D0.2':4.3},'加LiBr变化小','Raman','DOL模型，mg mL−1','M0190 M0191')
prop(p,'LiNO3对S8溶解度',{'0.3M LiNO3':'无明显影响'},'变化小','Raman','不同LiTFSI浓度DOL模型','M0193 M0194')
prop(p,'离子电导率',{'E0.2':14.2,'E0.5':9.2,'E0.8':6.8,'E1.0':3.3},'原文随浓度升高下降','电导仪','mS m−1（原文单位照录）','M0111 S0017 S0106')
prop(p,'多硫化物浓度/溶解',{'P08':'前0–16h高于P1，16h后低于P1','PB':'高于P08且后期高于P1'},'时间依赖且与S8溶解趋势不同','歧化/UV-vis','DOL/DME2:1；60°C反应','M0144 M0145 M0173 M0224 M0226 S0122 S0123')
prop(p,'醚极化与盐缔合',{'D1.0':'LiTFSI解离/强极化DOL','DB0':'LiBr缔合/弱极化DOL'},'盐种类依赖','DFT/MD','模型','M0036 M0202 M0204 M0206 M0220')
C={'Li_thickness':'450 µm','temperature':'room temperature','one_C':'1675 mA g−1','LiNO3':'0.3 M','voltage':'1.7–2.8 V'}
def T(id,n,c,forms,e):
 return test(p,id,n,'S-PC||Li',dict(C,**c),forms,e+' S0025 S0026 S0030 S0031')
for i,rate in enumerate([.05,.1,.15],1):
 t=T('T'+str(i),'浓度CV',{'rate':str(rate)+' mV s−1','ES':5,'ES_unit':'µL mg−1'},['E0.8','E1.0'],'M0094 M0100')
 if i==1:
  for m,a,b,u in [('ΔE1',154,230,'mV'),('ΔE2',424,506,'mV'),('Sact',50,41.7,'%'),('Suti',50,40,'%')]:
   result(t,m,'E0.8','E1.0',a,b,u,'0.05mV/s','numeric','不判','M0098 M0107 M0132')
 if i==2:
  for m,a,b,u in [('Tafel slope',238,700,'mV dec−1'),('Sact',45,32,'%'),('Suti',23,13,'%')]:
   result(t,m,'E0.8','E1.0',a,b,u,'0.1mV/s','numeric','不判','M0122 M0133')
  result(t,'还原峰数','E0.8','E1.0',2,1,None,'0.1mV/s','numeric','不判','M0114')
  result(t,'S8→Li2S8相对活化能','E0.8','E1.0','低37.24',None,'kJ mol−1','由Tafel推导','numeric','不判','M0124 S0181')
 if i==3:
  result(t,'第一还原峰电流','E0.8','E1.0',1.91,1.21,'mA','0.15mV/s','numeric','变好','M0125')
  result(t,'第二还原峰/利用','E0.8',None,'第二峰不能良好出现，Sact/Suti很低',None,None,'0.15mV/s','qualitative','不判','M0136 M0137')
t=T('T4','低浓度CV筛选',{'rate':'0.05 mV s−1','ES':5,'ES_unit':'µL mg−1'},['E0.2','E0.5','E0.8','E1.0'],'M0109 S0104')
for a in ['E0.2','E0.5']:
 result(t,'反应速率',a,'E1.0','提高但不如0.8M',None,None,'0.05mV/s','qualitative','变好','M0109')
t=T('T5','原位Raman',{'rate':'1 C','sulfur_loading':'1.0 mg cm−2','electrolyte_volume':'200 µL'},['E0.8','E1.0'],'M0151 M0157 S0038')
result(t,'放电容量','E0.8','E1.0',928,746,'mAh g−1','原位1C放电','numeric','变好','M0157')
result(t,'S转化','E0.8','E1.0','更快更完全',None,None,'Raman放充','qualitative','变好','M0152 M0153 M0154 M0155 M0156 M0158 M0159 M0160 M0161 M0162')
t=test(p,'T6','Li2S沉积形貌','carbon paper||Li',{'electrolyte_volume':'10µL负极blank+20µL正极100mmol/L Li2S8 catholyte','LiNO3':'.3M blank'},['E0.8','E1.0'],'S0032 S0033 S0034 S0131 S0132')
result(t,'Li2S生长模式','E0.8','E1.0','3D岛/球状保留清洁表面','2D膜覆盖',None,'沉积','qualitative','不判','M0164 M0165 M0166 M0167 M0168')
for id,rate,e in [('T7',.05,'M0229 M0230 S0142'),('T8',.1,'M0231 M0232 M0233 S0142'),('T9',.15,'M0235 M0236 M0237')]:
 t=T(id,'LiBr作用CV',{'rate':str(rate)+' mV s−1','ES':5,'ES_unit':'µL mg−1'},['EB','E0.8'],e)
 if rate==.05: result(t,'CV曲线','EB','E0.8','相似',None,None,'0.05mV/s','qualitative','差异小','M0229 M0230')
 if rate==.1:
  result(t,'Pc2电流','EB','E0.8',4.86,3.12,'mA','0.1mV/s','numeric','变好','M0233')
  result(t,'Pc2正移','EB','E0.8','约80',None,'mV','0.1mV/s','numeric','不判','M0233')
  result(t,'Li2Sn→Li2S相对活化能','EB','E0.8','低60.92',None,'kJ mol−1','由Tafel推导','numeric','不判','S0181')
 if rate==.15: result(t,'还原峰数','EB','E0.8',2,1,None,'0.15mV/s','numeric','不判','M0236')
t=T('T10','倍率',{'rate':'0.05,0.1,0.2,0.5 C','sulfur_loading':'正文5.0；Fig5a4.61；SI通用4.5 mg cm−2','ES':10,'ES_unit':'µL mg−1'},['EB','E1.0'],'M0209 M0240 M0241 M0242 S0027')
for rate,cap in [(.05,1328.8),(.1,1030.4),(.2,955.5),(.5,607.9)]:
 result(t,'放电容量','EB','E1.0',cap,None,'mAh g−1',str(rate)+' C','numeric','不判','M0241','对照仅作者称更低')
result(t,'各倍率容量','EB','E1.0','更高',None,None,'倍率','qualitative','变好','M0242')
result(t,'极化','EB','E1.0','更低',None,None,'倍率','qualitative','变好','M0243')
t=T('T11','0.5C循环',{'rate':'.5 C','sulfur_loading':'2.18 mg cm−2','ES':10,'ES_unit':'µL mg−1'},['EB','E1.0'],'M0246 S0152')
result(t,'容量/循环时间','EB','E1.0','容量更高；循环时间约2.3倍',None,None,'循环','qualitative','变好','M0247')
result(t,'极化','EB','E1.0','更低',None,None,'循环','qualitative','变好','M0248')
t=T('T12','高载贫液循环',{'rate':'.2 C','formation':'首圈0.05 C','sulfur_loading':'4.25 mg cm−2','ES':5,'ES_unit':'µL mg−1'},['EB','E1.0'],'M0249 M0250 M0251 M0252')
for a,b,pt,e in [(1456,1251,'首圈0.05C','M0250'),(1104,219,'0.2C','M0251'),(883,None,'100cycles','M0252')]:
 result(t,'放电容量','EB','E1.0',a,b,'mAh g−1',pt,'numeric','不判',e)
result(t,'平均容量衰减','EB',None,.2,None,'%','100cycles','numeric','不判','M0252')
t=T('T13','极贫液循环',{'rate':'.1 C；另有0.05C','sulfur_loading':'6.2 mg cm−2','ES':3,'ES_unit':'µL mg−1'},['EB','E1.0'],'M0254 M0255 M0256 S0160')
result(t,'初始容量','EB',None,1129,None,'mAh g−1','0.1C','numeric','不判','M0255')
result(t,'容量','E1.0',None,171.6,None,'mAh g−1','0.05C','numeric','不判','M0256','不能与EB0.1C直接配对')
result(t,'稳定循环','EB',None,'over70',None,'cycles','0.1C','numeric','不判','M0255')
t=test(p,'T14','软包','S||Li pouch',{'sulfur_loading':'4.6 mg cm−2 单面','ES':3,'ES_unit':'µL mg−1','rate':'0.1 C','LiNO3':'.3 M','one_C':'1675 mA g−1'},['EB'],'M0257 M0258 S0167')
for m,v,u,pt,e in [('放电容量',1421,'mAh g−1','first cycle','M0258'),('总容量',10.77,'Ah','pouch','M0257'),('能量密度',554,'Wh kg−1','first cycle','M0258 S0167'),('循环数',54,'cycles','TableS1','S0167')]:
 result(t,m,'EB',None,v,None,u,pt,'numeric','不判',e)
t=test(p,'T15','锂对称循环','Li||Li',{'LiNO3':'.3M'},['EB'],'M0260 M0261 S0162')
result(t,'稳定性','EB',None,'可稳定循环；作者称LiBr无明显影响',None,None,'长期循环','qualitative','不判','M0260 M0261','无明确对照及电流数值')
for sm,A,B,pr,cats,ty,e,ts,side in [
('降低LiTFSI增多未极化醚并提高S8溶解，建立液-液-固路径，长程电子传递促进正极反应','E0.8','E1.0','S8溶解/醚极化',['正极反应'],'本文结论','M0147 M0148 M0171',['T1','T2','T5'],'弱侧'),
('提高S8溶解加速早期歧化，但较高LiTFSI在后期提供更多Li+形成Li3S6+或极化醚来稳定多硫化物','P1','P08','多硫化物溶解',['正极反应'],'本文推测','M0143 M0144 M0145 M0146 M0173',[],'强侧'),
('0.8M高扫速仍反应不足，可能因多硫化物数量受限','E0.8',None,'多硫化物溶解',['正极反应'],'本文推测','M0136 M0137',['T3'],'弱侧'),
('LiBr缔合离子对弱极化醚，不损失S8溶解，同时通过偶极作用稳定Li2Sx进一步加速反应','EB','E0.8','盐缔合/多硫化物溶剂化',['正极反应'],'本文结论','M0206 M0207 M0220 M0224 M0226 M0227 M0238',['T7','T8','T9','T10','T12'],'其他'),
('0.8M促进3D Li2S生长，减少2D膜覆盖和钝化','E0.8','E1.0','Li2S沉积',['正极反应'],'本文结论（与他文一致）','M0164 M0165 M0166 M0167 M0168 M0171',['T6'],'弱侧'),
('贫液软包衰减可能来自Li金属腐蚀，循环后锂损伤提示保护不足','EB',None,'锂界面',['负极锂'],'本文推测','M0259 M0262 S0164',['T14'],'其他'),
('非线性S8溶解由溶剂-溶质作用跨越能量阈值决定，而介电常数不直接解释突变','D0.8','D1.0','S8溶剂化',[],'本文结论','M0037 M0091 M0092 M0195 M0267',[],'其他')]:
 mech(p,sm,A,B,pr,cats,ty,e,ts,side)
claim(p,'通过盐浓度/种类同时控制S8和Li2Sx溶解，改善贫液正极动力学','M0038 M0039 M0238 M0268')
fig(p,'T12','Fig.5c','main','放电容量','EB','E1.0','100cycles','M0252','EB883为同测试锚，补对照')
fig(p,'T13','Fig.5e / Fig.S32','main/si','放电容量','EB','E1.0','0.1C初始及共同循环点','M0255','EB1129@0.1C为锚，对照171.6@0.05C不可混用')
p['gaps']=['倍率载量正文5.0、图注4.61、SI通用4.5不一致；均保留。','结论写6.25mg/cm2 ES3容量1455，但结果正文6.2mg/cm2初始0.1C1129；未冒充同测试同点。','软包能量结果/表554，结论M0270写544Wh/kg；冻结优先结果段但保留冲突。','原文电导率mS m−1及解释相互不够一致，照抄不纠正。','Li对称电流/容量/时间及软包锂厚度未见文字。','SI S26标题为0.8M vsEB，与正文/其他图所述1M vsEB不同，未跨图整合数值。']
save(p)

