from independent_c_helpers import *
p=init('P548')
for id,sol,c,n,e in [('E2','2FPy',1,'饱和','M0047 S0047'),('E3','3FPy',1,.2,'M0047'),('Ether','DME/DOL',1,.2,'S0045 S0077'),('E2-2.5','2FPy',2.5,0,'S0077'),('E3-2.5','3FPy',2.5,0,'S0077')]:
 form(p,id,f'{c} M LiTFSI/{n} LiNO3/{sol}',[('LiTFSI','salt',c,'M'),(sol,'solvent','纯溶剂' if sol!='DME/DOL' else '比例未写',''),('LiNO3','additive',n,'M' if isinstance(n,(int,float)) else '')],e)
for id in ['Py','2FPy','3FPy','4FPy','DME/DOL']:
 form(p,id,'模型溶剂：'+id,[(id,'model solvent','模型','')],'M0041 M0063 S0004 S0006')
p['control_id']='Ether';p['control_type']='常规醚基电解液；室温主比较E2/E3'
grad(p,'氟吡啶Li亲和力',['3FPy','4FPy','2FPy'],{'3FPy':9.6,'4FPy':23.9,'2FPy':55.1},'Li+配位强度由弱到强；CID相对Py碎片丰度','M0030 M0041 M0093')
prop(p,'Li+配位强度',{'2FPy':'高于4FPy和3FPy','Py':'高于氟吡啶'},'2FPy>4FPy>3FPy','ESI/MS CID','50mM LiTFSI，Py/其他溶剂1:1摩尔比；非实际电池配方','M0027 M0028 M0041 S0028')
prop(p,'多硫化物溶解度指标',{'Py':1834,'DME/DOL':451.5,'2FPy':459.7,'3FPy':2134},'3FPy>Py>2FPy>DME/DOL','ICP-OES','无LiTFSI的1M Li2S6混合物上清Li+浓度mM，不是Li2S6摩尔浓度','M0081 S0083 S0084')
prop(p,'加1M LiTFSI后多硫化物溶解',{'2FPy':'显著降低','3FPy':'略降低','Py':'升高','DME/DOL':'升高'},'溶剂依赖非统一趋势','HPLC','1M Li2S6加盐前后','M0082 M0084 M0085 S0082 S0086')
prop(p,'S8溶解度',{'2FPy':12.47,'3FPy':21.38},'3FPy较高','HPLC','无盐纯溶剂，mM','M0083 S0014 S0015 S0087 S0088')
prop(p,'多硫化物化学相容性',{'2FPy':'与多硫化物反应，产生Py-S/Py-S2','3FPy':'室温稳定'},'2FPy发生反应','ESI/MS/HPLC','15mM Li2S6','M0068 M0069 M0070 M0071 M0072 M0074 M0078')
C={'sulfur_loading':'~1.6 mg cm−2 (theoretical)','ES':'~5','ES_unit':'µL mg−1（原文E/S around5，8µL）','formation':'静置12h；未说明活化','voltage':'1.7–3.0 V','LiNO3':'E2饱和/E3与Ether0.2M'}
def T(id,n,c,forms,e): return test(p,id,n,'S/CMK3||Li CR2032',dict(C,**c),forms,e+' S0029 S0035 S0036 S0037 S0038')
t=T('T1','室温0.05C循环',{'temperature':'room temperature','rate':'0.05 C'},['E2','E3'],'M0036 M0048 M0049 M0050')
result(t,'容量保持率','E2','E3','50–60','50–60','%','50 cycles','numeric','差异小','M0036','原文共同区间，不是各自精确值')
t=T('T2','室温第二圈曲线',{'temperature':'room temperature','rate':'0.05 C'},['E2','E3'],'M0039 M0044 M0048 M0076')
result(t,'高放电平台长度','E3','E2','更长',None,None,'second cycle','qualitative','不判','M0039')
result(t,'低放电平台长度','E3','E2','更短',None,None,'second cycle','qualitative','不判','M0039')
result(t,'高压新放电平台','E2',None,'2.4–2.6',None,'V','随循环逐渐出现','numeric','不判','M0076')
t=T('T3','室温倍率',{'temperature':'room temperature','rate':'0.02,0.04,0.1,0.2,0.5,1 C；各10圈后0.1C至160圈'},['E2','E3'],'M0037 S0053 S0054')
result(t,'高倍率性能','E2','E3','更好',None,None,'高倍率','qualitative','变好','M0037')
t=T('T4','电池CV',{'temperature':'room temperature','rate':'0.1 mV s−1','voltage':'1.5–3.2 V'},['E2','E3'],'M0046 M0047 S0042')
result(t,'硫氧化还原行为','E2','E3','不同',None,None,'CV','figure_only','不判','M0038 M0046','无文字定量；不目测')
t=test(p,'T5','溶解S8三电极CV','glassy carbon/Li reference/Li counter',{'temperature':'room temperature','rate':'10 mV s−1','voltage':'1.5–3.2 V','sulfur_loading':'4 mM dissolved S8','LiNO3':'按配方'},['E2','E3','Ether'],'S0043 S0044 S0045 S0046 S0047 S0050 S0051')
result(t,'硫氧化还原','E3','Ether',None,None,None,'CV','figure_only','不判','S0050','仅图，无文字方向和数值')
t=T('T6','60°C循环',{'temperature':'60 °C','rate':'0.05 C','LiNO3':'E2-2.5/E3-2.5无；E2饱和；E3/Ether0.2M'},['E2-2.5','E3-2.5','E2','E3','Ether'],'M0086 M0087 M0088 S0077')
result(t,'穿梭/过充','E2-2.5',None,'严重',None,None,'60°C','qualitative','不判','M0086')
result(t,'穿梭/过充','E3-2.5',None,'严重',None,None,'60°C','qualitative','不判','M0086')
result(t,'穿梭','E3','E3-2.5','明显缓解','严重',None,'60°C','qualitative','变好','M0086 M0087','LiTFSI浓度亦1M vs2.5M，不能单归因LiNO3')
result(t,'过充','E2',None,'严重',None,None,'60°C，饱和LiNO3','qualitative','不判','M0088')
result(t,'容量保持','E3',None,'仍不理想',None,None,'60°C','qualitative','不判','M0087')
t=T('T7','0°C循环',{'temperature':'0 °C','rate':'0.05 C'},['E2','E3','Ether'],'M0090 M0091 S0078')
result(t,'放电容量','E3','Ether',300,'>750','mAh g−1','25 cycles','numeric','变坏','M0090 M0091')
result(t,'放电容量','E2','Ether',550,'>750','mAh g−1','25 cycles','numeric','变坏','M0090 M0091')
result(t,'放电容量','E3','E2',300,550,'mAh g−1','25 cycles','numeric','变坏','M0090')
for summary,A,B,pr,cats,typ,e,ts,side in [
('邻位F可能协同N配位使2FPy与Li+作用强于3FPy，与按计算DN推定顺序不一致','2FPy','3FPy','Li+溶剂化',[],'本文推测','M0028 M0029 M0030 M0032 M0033 M0034 M0093',[],'强侧'),
('Py稳定S3自由基使平衡偏短链；3FPy稳定长链多硫化物','Py','3FPy','多硫化物溶剂化',['正极反应'],'本文推测','M0054 M0056 M0059 M0060',['T2'],'其他'),
('2FPy发生多硫化物亲核取代形成有机硫，可能导致循环后出现高压放电平台','E2','E3','化学相容性',['正极反应','电解液消耗'],'本文推测','M0073 M0074 M0076 M0077',['T1','T2'],'强侧'),
('3FPy间位氟电子效应及不同反应活性使其室温不与多硫化物反应','E3','E2','化学相容性',['电解液消耗'],'本文结论','M0078 M0094',['T1','T2'],'弱侧'),
('LiNO3在高温稳定锂SEI并抑制穿梭；2FPy中LiNO3低溶解度限制作用','E3','E2','LiNO3/SEI',['负极锂','多硫化物穿梭'],'本文结论','M0086 M0087 M0088 M0089',['T6'],'其他'),
('前人将3FPy室温高载贫液性能归于高多硫化物溶解与LiF丰富SEI','E3',None,'溶解/SEI',['正极反应','负极锂'],'转述他文或通用说法','M0012 M0013',[],'强侧')]:
 mech(p,summary,A,B,pr,cats,typ,e,ts,side)
claim(p,'氟吡啶电解液需同时考虑化学相容性及温度，单独DN不能解释Li配位或溶解行为','M0085 M0093 M0094 M0095 M0096 M0097')
p['gaps']=['无锂半电池实测；文献LiF机理不得当作本文锂实验结论。','E2与E3添加LiNO3浓度不同；高温有/无LiNO3对比同时改变LiTFSI浓度。','Li厚度及1C定义未写；DME/DOL比例未明确。','室温倍率及CV等仅图示数值未目测；冷温25圈数值正文完整无需读图。','ICP报告的是上清Li+浓度，未冒充Li2S6浓度；2FPy化学反应使物种分布额外复杂。']
save(p)

