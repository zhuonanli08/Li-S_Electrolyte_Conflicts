from independent_c_helpers import *
p=init('P432',False);p['control_id']='DME';p['control_type']='不含LiNO3的自配对照；DME及TMU各有无陷阱'
for sol in ['DME','TMU']:
 for tr in ['','Emim','BmPyr','DMPO','PotBN']:
  cs=[['LiTFSI','盐','1','M'],[sol,'溶剂化溶剂','1','体积份'],['DOL','溶剂化溶剂','1','体积份']]
  if tr:cs.append([tr,'添加剂','0.78','mmol nitrone/iminium per mL electrolyte'])
  form(p,sol+('-'+tr if tr else ''),'1 M LiTFSI '+sol+'/DOL 1:1 v/v; trap '+tr,cs,'M0041 M0050 M0069 M0070 M0099')
grad(p,'溶剂',['TMU','TEGDME（光谱）','DME','TFEE（光谱）'],['TMU','TEGDME','DME','TFEE'],'自由基稳定/浓度由高到低，不等同于Li+配位数','M0088 M0089 M0095')
prop(p,'Li+溶剂化',{'TMU':'TFSI低频，与TEGDME近似','DME':'中','TFEE（光谱）':'最高频、氟屏蔽配位'},'TFSI峰位TFEE>DME>TEGDME≈TMU','Raman','OCV电解液；TEGDME/TFEE配方不详','M0093 M0094 M0095')
prop(p,'多硫化物/自由基',{'TMU':'S3自由基最高','TEGDME（光谱）':'次高','DME':'低','TFEE（光谱）':'未见'},'TMU>TEGDME>DME>>TFEE','Raman 532 cm−1','OCV电解液','M0087 M0088 M0089')
prop(p,'ex situ捕获',{'Emim':'蓝→透明','BmPyr':'蓝→黄','PotBN':'蓝→黄','DMPO':'蓝→浅蓝绿'},'只适用于离体溶液','Raman及颜色','0.2 mM Li2S6/DMA；另一句2 mM，冲突','M0102 M0103 M0109')
base={'Li_thickness':'125 μm','LiNO3':'未添加','temperature':'室温'}
for i,sol in enumerate(['DME','TMU'],1):
 fs=[sol]+[sol+'-'+x for x in ['Emim','BmPyr','DMPO','PotBN']]
 grad(p,sol+'中陷阱',fs,['无','Emim','BmPyr','DMPO','PotBN'],'种类梯度，非单调溶剂化','M0069 M0070')
 t=test(p,'T'+str(i),'operando Raman容量','C/S||Li石英窗',{**base,'ES':'38–40','ES_unit':'μL mgS−1','rate':'C/20','electrolyte_volume':'ca.200 μL','voltage':'1.8–2.8 V'},fs,'M0054 M0066 M0068 M0071 M0072')
 for tr in ['Emim','BmPyr']:result(t,'首平台容量',sol+'-'+tr,sol,'降低','基准',None,'operando首圈','qualitative','变坏','M0129')
 if sol=='DME':
  for tr in ['DMPO','PotBN']:result(t,'第二平台容量',sol+'-'+tr,sol,'降低','基准',None,'operando首圈','qualitative','变坏','M0122 M0123')
  result(t,'穿梭',sol+'-BmPyr',sol,'降低','基准',None,'operando','qualitative','变好','M0122')
 else:prop(p,'operando S3自由基峰面积',{'TMU-BmPyr':'ca.1/6 of TMU'},'降低','Raman','operando','M0127')
for i,sol in enumerate(['DME','TMU'],3):
 fs=[sol]+[sol+'-'+x for x in ['Emim','BmPyr','DMPO','PotBN']]
 t=test(p,'T'+str(i),'扣电长循环','C/S||Li coin',{**base,'sulfur_loading':'2.5 mgS cm−2','ES':'24','ES_unit':'μL mgS−1','electrolyte_volume':'80 μL','rate':'C/10','voltage':'1.5–2.8 V','capacity_limit':'DME对照施加未报告值容量限制'},fs,'M0064 M0065 M0198 M0199')
 result(t,'容量',sol+'-BmPyr',sol,'降低','基准',None,'循环','qualitative','变坏' if sol=='TMU' else '不判','M0212','DME对照限容不同' if sol=='DME' else '',sol!='DME')
 result(t,'寿命',sol+'-BmPyr',None,'20–25',None,'cycles','失效','numeric','不判','M0212')
 if sol=='DME':
  result(t,'容量',sol+'-Emim',None,'前20圈持续下降后稳定',None,None,'循环','qualitative','不判','M0201 M0202')
  for tr in ['DMPO','PotBN']:result(t,'长期容量',sol+'-'+tr,sol,'降低','基准',None,'循环','qualitative','不判','M0207 M0208','对照限容不同',False)
 else:
  for met in ['容量','CE']:result(t,met,sol+'-Emim',sol,'提高','基准',None,'前40圈','qualitative','变好','M0203 M0204')
  result(t,'初始容量',sol+'-DMPO',sol,'提高，约30圈趋平','基准',None,'初始','qualitative','变好','M0208 M0209 M0210 M0211')
  for tr in ['DMPO','PotBN']:result(t,'CE',sol+'-'+tr,sol,'略提高','基准',None,'循环','qualitative','变好','M0209')
 result(t,'Li表面稳定',sol+'-BmPyr',sol,'致密/厚度不变','退化',None,'循环后','qualitative','变好','M0220 M0222 M0223 M0227')
for su,pr,cats,typ,e,ts in [
('无LiNO3导致穿梭和不完全充电','无LiNO3',['多硫化物穿梭'],'本文结论','M0099',['T1','T2']),
('DMPO/PotBN电池中反增自由基，与ex situ相反，推测不可逆电化学反应','陷阱稳定性',['正极反应','电解液消耗'],'本文推测','M0124 M0125',['T1','T2']),
('BmPyr捕获S3改变PS路径，降低容量并导致20–25圈失效','S3减少',['正极反应'],'本文结论','M0212',['T3','T4']),
('捕获S3可能抑制S3二价阴离子形成，减少第二平台容量','S3减少',['正极反应'],'本文推测','M0190 M0191',['T1','T2']),
('S3相关亚稳S3二价阴离子可能是充分利用硫的重要中间体','S3/PS物种',['正极反应'],'本文推测','M0197',['T1','T2']),
('Emim在DME/TMU表现不同，不能归于捕获，可能源于溶剂化或其他PS相互作用','Emim溶剂化',['正极反应'],'本文推测','M0206',['T3','T4']),
('BmPyr保护Li表面，因此其电池失效应源于PS形成变化','PS路径与负极解耦',['正极反应','负极锂'],'本文结论','M0227',['T3','T4']),
('确认PotBN在DME和DMPO在TMU中的分解','添加剂分解',['电解液消耗'],'本文结论','M0261',[]),
('DME自由基少，本文难以明确其容量和稳定性作用','自由基含量',['正极反应'],'本文结论（与他文一致）','M0216',[])]:
 mech(p,su,'全梯度',None,pr,cats,typ,e,ts,'其他')
claim(p,'稳定S3自由基可能有利；BmPyr虽损害硫转化却可作为负极SEI添加剂','M0012 M0265 M0269 M0272')
for tid,f in [('T3','Figure 5a'),('T4','Figure 5b')]:fig(p,tid,f,'main','容量','全梯度',None,'初始/20/25/40/100圈','M0212','仅BmPyr失效圈数锚点；其他曲线无可核数值不得读')
p['gaps']=['SI缺失，图S1–S17/表S1–S2无法核','DME原文名di-methyl ether，保留缩写','E/S扫描只明列11.6及18，其他档未取得','TEGDME/TFEE光谱配方未详；无Li半电池','未报告1C/化成/电导率/黏度/迁移数；ex situ浓度0.2/2 mM冲突']
save(p)

