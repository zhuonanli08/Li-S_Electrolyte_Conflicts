from independent_c_helpers import *
p=init('P413');p['control_id']='organic';p['control_type']='常规醚基准（DOL/DME + LiTFSI + LiNO3）'
form(p,'organic','1 M LiTFSI +0.1 M LiNO3 in DOL:DME 1:1 vol',[['LiTFSI','盐','1','M'],['LiNO3','添加剂','0.1','M'],['DOL','溶剂化溶剂','1','体积份'],['DME','溶剂化溶剂','1','体积份']],'M0170 S0012')
ils=['PP14-TFSI','DEME-TFSI','TBMA-TFSI','BMIM-PF6','BMIM-CF3SO3','BMIM-MeSO4']
for x in ils:
 form(p,x+'-25','IL:已配organic=25:75 vol%',[ [x,'添加剂（离子液体）','25','vol%'],['organic','基液','75','vol%']],'M0172 M0174 M0184 S0014')
for x in ils[:2]:form(p,x+'-50','IL:已配organic=50:50 vol%',[ [x,'添加剂（离子液体）','50','vol%'],['organic','基液','50','vol%']],'S0013 S0020')
grad(p,'IL种类（由预测Li2S8溶解度高到低）',[x+'-25' for x in ['BMIM-MeSO4','BMIM-CF3SO3','BMIM-PF6','DEME-TFSI','PP14-TFSI','TBMA-TFSI']],['182635','847','1.29','0.38','0.20','0.04 mol/mol'],'COSMO-RS纯IL溶解度，非实测混合电解液Li+溶剂化','M0184')
for x in ils[:2]:grad(p,x+'体积分数',['organic',x+'-25',x+'-50'],['0','25','50 vol%'],'用量梯度，溶剂化排序未测','M0171 S0013 S0020')
prop(p,'预测Li2S8溶解度',dict(zip([x+'-25' for x in ils],['0.20','0.38','0.04','1.29','847','182635'])),'mol/mol；只能定性筛选，极端数不可解释为饱和浓度','COSMO-RS 25 °C','纯IL而非25%IL混合电解液；无限稀释活度系数倒数','M0087 M0184 M0212 M0213')
prop(p,'预测黏度',dict(zip([x+'-25' for x in ils],['65','54','107','223','56','146'])),'mPa s','COSMO-RS 25 °C','纯IL而非电池混合电解液','M0184')
c={'sulfur_loading':'approximately 2 mg cm−2','ES':'13','ES_unit':'mL g−1','Li_thickness':'170 μm','rate':'0.1 C','LiNO3':'有机母液0.1 M；与IL混合后被稀释','one_C':'按1675 mAh g−1理论容量'}
fs=['organic']+[x+'-25' for x in ils]
t=test(p,'T1','六IL种类长循环','S/CB||Li CR2032',c,fs,'M0173 S0005 S0011 S0015 S0016 S0021')
for a in ils[:2]:
 for b in ils[2:4]:result(t,'循环容量/性能',a+'-25',b+'-25','最好','中等',None,'50圈及100圈','qualitative','变好','M0181 M0187 M0191')
for x in ils[4:]:result(t,'循环容量',x+'-25',None,'almost zero',None,None,'循环期间','qualitative','不判','M0188')
result(t,'容量','PP14-TFSI-25','organic','较高','基准',None,'循环初期','qualitative','变好','M0192')
result(t,'容量','PP14-TFSI-25','organic','相近','相近',None,'循环末期','qualitative','差异小','M0192')
result(t,'库仑效率','全梯度',None,None,None,'%','100圈Figure S6b','figure_only','不判','S0021','CE只有图；不在允许读图类型内')
for i,x in enumerate(ils[:2],2):
 t=test(p,'T'+str(i),'IL用量梯度','S/CB||Li CR2032',c,['organic',x+'-25',x+'-50'],'S0013 S0020')
 result(t,'容量',x+'-25',x+'-50',None,None,'mAh g−1','Figure S5a','figure_only','不判','S0020','无文字数值或明确方向')
t=test(p,'T4','E/S低档循环','S/CB||Li CR2032',{**c,'ES':'8'},['PP14-TFSI-25'],'S0013 S0020')
result(t,'容量','PP14-TFSI-25',None,None,None,'mAh g−1','Figure S5b','figure_only','不判','S0020','不与E/S13直接判优劣')
for su,a,b,pr,cats,typ,e,ts,side in [
('高黏度可限制PS移动抑制穿梭，同时妨碍Li+扩散','全梯度',None,'黏度',['多硫化物穿梭','正极反应'],'本文结论','M0180',['T1'],'其他'),
('高溶解度BMIM-CF3SO3即使低黏度也性能差，作者据此认为溶解度更关键','BMIM-CF3SO3-25','PP14-TFSI-25','预测PS溶解度高',['多硫化物穿梭'],'本文结论','M0188 M0189 M0190',['T1'],'强侧'),
('极低和极高PS溶解度分别造成反应迟缓与正极硫流失','全梯度',None,'PS溶解度过低或过高',['正极反应','多硫化物穿梭'],'转述他文或通用说法','M0218',[],'其他'),
('低PS溶解度但高黏度TBMA-TFSI/BMIM-PF6仅中等表现','TBMA-TFSI-25/BMIM-PF6-25','PP14-TFSI-25/DEME-TFSI-25','溶解度与黏度',[],'本文结论','M0187',['T1'],'其他')]:
 mech(p,su,a,b,pr,cats,typ,e,ts,side)
claim(p,'筛选需要适度低PS溶解度及低黏度；650个预测候选尚未实际电池验证','M0220 M0263 M0264 M0270 M0204')
for tid,f,a,b in [('T1','Figure 3/S6a','全梯度','organic'),('T2','Figure S5a','PP14-TFSI-25','PP14-TFSI-50'),('T3','Figure S5a','DEME-TFSI-25','DEME-TFSI-50'),('T4','Figure S5b','PP14-TFSI-25',None)]:
 fig(p,tid,f,'main/si' if tid=='T1' else 'si','容量',a,b,'首圈及50/100圈','','正文无同测试数值锚点，按规则仅图未读')
p['gaps']=['全部电池数值只在图上，未提供可核数值锚点，不目测填数','COSMO-RS属性针对纯IL且是预测，不作为混合电解液实测性质','引用Park等溶解度/容量不并入本文实测结果','未报告电池温度、化成；无Li半电池、Li+溶剂化或迁移数实测']
save(p)

