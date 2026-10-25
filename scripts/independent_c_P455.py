from independent_c_helpers import *
p=init('P455');p['control_id']='H';p['control_type']='常规醚基准（DOL/DME + LiTFSI + LiNO3）'
spec={'H':('1','0.25',None),'L1':('0.1','0.075',None),'L3':('0.3','0.075',None),'L':('0.05','0.025',None),'LTF':('0.05','0.025','0.015'),'N':(None,'0.375',None),'HTF':('0.55','0.27','0.16')}
for id,(a,b,c) in spec.items():
 cs=[['DOL','溶剂化溶剂','1','体积份'],['DME','溶剂化溶剂','1','体积份'],['LiNO3','盐/添加剂',b,'M']]
 if a:cs.append(['LiTFSI','盐',a,'M'])
 if c:cs.append(['LiTF','盐',c,'M'])
 form(p,id,str(spec[id])+' M salts in DOL/DME 1:1 v/v',cs,'M0056 M0077 M0241 M0265 S0025 S0031')
for x in ['DMI','HMPA','DMA']:form(p,x,'1 M LiTFSI +0.25 M LiNO3 in 100% '+x,[[x,'溶剂化溶剂','100','%'],['LiTFSI','盐','1','M'],['LiNO3','添加剂','0.25','M']],'S0017')
grad(p,'Li盐浓度',['H','L3','L1','L'],[spec[x] for x in ['H','L3','L1','L']],'减少游离Li+；不等于减弱溶剂本征配位','M0241 S0031')
grad(p,'低浓度添加LiTF',['L','LTF'],['0','0.015 M LiTF'],'难解离阴离子增加；作者认为减少Li+参与PS聚集','M0232 M0238')
prop(p,'Li扩散系数（高PS浓度）',{'H':'1.25×10−10','L':'2.4×10−10','LTF':'2.55×10−10'},'m2 s−1；LiTF只略增','7Li DOSY','5 M sulfur/polysulfide solution，静置后上清，非无PS电解液','M0254 M0257 S0023 M0307 M0309 M0311')
prop(p,'Li扩散系数（低PS浓度）',{'H':'2.82×10−10','L':'7.2×10−10（另一句7.23）','LTF':'8.72×10−10'},'m2 s−1','7Li DOSY','正文未明确对应低浓度档；SI有0.5/1.66/5 M','M0246 M0250 M0251 S0023')
prop(p,'PS溶液沉淀稳定性',{'H':'降温无放热峰','L':'降温出现骤增放热峰'},'高Li盐使PS溶液更抗沉淀','DSC','TEGDME替代DOL/DME；8 molS L−1名义Li2S8','M0204 M0205 M0206 M0211')
base={'sulfur_loading':'~3.5 mg cm−2','ES':'2.5','ES_unit':'μL mgS−1（依方法，摘要质量比不混）','Li_thickness':'600 μm','rate':'0.05 C','temperature':'室温','one_C':'1675 mA g−1','LiNO3':'随配方'}
t=test(p,'T1','常规首圈低倍率放电','S/C45/PVDF||Li',{**base,'rate':'0.025 C'},['H'],'M0047 M0056 M0290')
result(t,'第二平台电压','H',None,'持续压低',None,None,'首圈','qualitative','不判','M0057')
t=test(p,'T2','operando EIS浓度比较','S/C45/PVDF||Li',{**base,'formation':'每放电15 min静置10 min再EIS'},['H','L1'],'M0069 M0077 M0078 S0010 M0294')
result(t,'Rct','L1','H','<500','>2000','Ω','operando全过程量级','numeric','不判','M0088')
result(t,'Re峰值','L1',None,'~100',None,'Ω','峰值','numeric','不判','M0084')
result(t,'第二平台稳定性','L1','H','电压稳定','继续下降',None,'第二平台','qualitative','变好','M0092 M0093')
for n,id,load,en in [('I','H','3.89','1462'),('II','H','3.89','1513'),('III','LTF','3.49','1906'),('IV','L3','3.83','2164'),('V','N','3.65','2293'),('VI','L3','3.63','2041'),('VII','L3','3.49','2062'),('VIII','N','3.63','2086'),('IX','L1','3.32','2108'),('X','N','3.63','2024')]:
 t=test(p,'EIS-'+n,'不同电解液EIS单样本'+n,'S/C45/PVDF||Li',{**base,'sulfur_loading':load+' mg cm−2','formation':'每放电15 min静置10 min再EIS'},[id],'S0010 S0030 S0031 M0294')
 result(t,'活性硫质量基能量密度',id,None,en,None,'Wh kgS−1','首放电','numeric','不判','S0030 S0031','各样本硫载量不同，跨样本不判')
t=test(p,'T3','恒流低盐与LiTF','S/C45/PVDF||Li',base,['L','LTF'],'M0247 M0290')
result(t,'第二平台电压','LTF','L','well >2.0','<2.0','V','前两圈','numeric','不判','M0228 M0231 M0232')
result(t,'放电容量','LTF',None,'~850',None,'mAh g−1','0.05C，文首汇总','numeric','不判','M0043')
result(t,'放电容量','LTF','L','降低','基准',None,'恒流','qualitative','变坏','M0264')
t=test(p,'T4','高溶剂化溶剂对照','S/C45/PVDF||Li',base,['H','DMI','HMPA','DMA'],'S0017')
for x in ['DMI','HMPA','DMA']:result(t,'放电表现',x,'H','未明显改善/略差','基准',None,'首放电','qualitative','不判','M0217 M0218','作者定性保留不强行变坏')
t=test(p,'T5','E/S2.5高倍率','S/C45/PVDF||Li',{**base,'rate':'0.1 C'},['LTF'],'M0258 M0259')
result(t,'第二平台','LTF',None,'无法进入',None,None,'0.1C','qualitative','不判','M0259')
t=test(p,'T6','E/S3倍率','S/C45/PVDF||Li',{**base,'ES':'3','rate':'0.05/0.1/0.2 C','voltage':'截止1.5V'},['LTF'],'M0260 S0021')
result(t,'放电电压','LTF',None,'mostly >2.0',None,'V','0.1C','numeric','不判','M0261')
result(t,'第二平台','LTF',None,'无法进入',None,None,'0.2C','qualitative','不判','M0262')
t=test(p,'T7','短寿命循环','S/C45/PVDF||Li',base,['L','LTF'],'M0272 S0026 S0027')
result(t,'稳定寿命','LTF',None,'9',None,'cycles','第10圈穿梭严重失效','numeric','不判','M0272 S0027')
t=test(p,'T8','更高LiTF浓度','S/C45/PVDF||Li',base,['HTF'],'S0025')
result(t,'放电电压','HTF',None,'<2.0',None,'V','首圈以后下降','numeric','不判','M0267')
t=test(p,'T9','阴极LSV','S/C45/PVDF||Li',{**base,'rate':'0.2 mV s−1，OCV至1.65 V'},['H','L','LTF'],'S0019')
result(t,'还原峰','LTF','H','两峰清晰且峰电流提高','弱峰/无第二峰',None,'LSV','qualitative','变好','M0234 M0235 M0236 M0237')
for su,pr,cats,typ,e,ts in [
('高PS短暂存在造成持久负面效应，不能仅由当下高浓度解释长期低电压','高PS浓度',['正极反应'],'本文推测','M0066',['T1','T2']),
('RPSS为暂存PS的可逆质量库，可快速调节浓度而不依赖慢Li2S反应','RPSS沉淀再溶解',['正极反应'],'本文推测','M0193',['T2','T3']),
('不能形成RPSS的体系无法消除聚集/凝胶导致的长期过电位','RPSS不足',['正极反应'],'本文推测','M0194',['T2']),
('更强溶剂-PS/盐相互作用可能过度稳定团簇，对贫液不利','强溶剂化/团簇',['正极反应'],'本文推测','M0215 M0216',['T4']),
('难解离盐的Li已与阴离子配对，可能无法参与PS团簇形成','离子缔合',['正极反应'],'本文推测','M0224',['T3']),
('LiTF仅稍增扩散系数，主要性能收益被推测来自RPSS形成','RPSS非单纯扩散',['正极反应'],'本文推测','M0257',['T3']),
('少量LiNO3使Li较少钝化并易穿梭，限制寿命','LiNO3减少',['负极锂','多硫化物穿梭'],'本文推测','M0271',['T7']),
('低Li浓度可能损害离子导电，PS可部分补偿但高倍率和极端SOC难持久','低盐电导',['正极反应'],'本文推测','M0269 M0270',['T5','T6'])]:
 mech(p,su,'全梯度',None,pr,cats,typ,e,ts,'其他')
claim(p,'低Li浓度与难解离高DN阴离子协同促进RPSS，以提高贫液电压；仍有容量、倍率、寿命代价','M0264 M0268 M0272 M0280')
fig(p,'T7','Figure S14','si','循环容量','LTF','L','首圈/9/10圈','M0272 S0027','寿命锚点，补同测试容量')
p['gaps']=['SI图号与正文多处不一致，按SI真实标题定位','Table S1样本载量各异不判跨样本能量优劣','没有Li半电池；无实测迁移数/黏度/无PS电导率','RPSS是作者由EIS推断的机制，不当成直接物种鉴定；DOD图注顺序亦不一致']
save(p)

