from agent_b_common import *
p=paper('P211','RT0','室温常规配方；低温另有LT0')
for f,salt,add,amt,ratio,ids in [('RT0',1,None,0,[1,1],'M0036'),('RTN',.8,'NH4TFA',.2,[1,1],'M0036'),('LT0',.8,None,0,[85,15],'M0037'),('LTL',.5,'LiTFA',.3,[85,15],'M0037'),('LTN',.5,'NH4TFA',.3,[85,15],'M0037')]:
 co=[('LiTFSI','盐',salt,'M'),('LiNO3','添加剂',.2,'M'),('DOL','溶剂',ratio[0],'体积比'),('DME','溶剂',ratio[1],'体积比')]
 if add:co.append((add,'添加剂',amt,'M'))
 form(p,f,f,co,ids)
grad(p,'低温阳/阴离子竞争',['LT0','LTL','LTN'],['无TFA','LiTFA','NH4TFA'],'先增强阴离子竞争再加入NH4阳离子竞争；非纯单一变量','M0197 M0198 M0199')
prop(p,'多硫化锂配位',{'RTN':'Li与Sx配位减少，25°C NMR去屏蔽；−50°C仍存在混合簇','RT0':'低温纯锂多硫簇'},'NH4TFA改变而非完全消除聚簇','7Li NMR+DFT','模型0.2 M Li2S4±0.2 M NH4TFA，DME/dTHF=2:3','M0061 M0166 M0173 M0175 M0178 M0179 M0180')
c=dict(LiNO3='.2 M',one_C='1672 mA gS-1',temperature='室温',rate='C/10',formation='2圈C/20')
t=test(p,'室温富液扣式循环',['RTN','RT0'],'M0039 M0040 M0054 M0055 M0123 M0125',sulfur_loading='3.4 mg cm-2',ES=12,ES_unit='μL mgS-1',voltage='1.7–2.7 V',**c)
result(t,'放电容量/保持','RTN','RT0','800–900','800–900','mAh g-1','100圈内','M0123',basis='qualitative',direction='差异小',reason='原文表示循环相近，范围不是逐圈配对')
result(t,'放电过电位差','RTN','RT0','约低40',None,'mV','50圈电压曲线；低平台','M0101 M0125 M0126',basis='qualitative',direction='变好',reason='原文给差值而非两个绝对数值')
fig(p,t,'Fig.3a','放电容量','RTN','RT0','100圈','M0123')
t2=test(p,'贫液软包单循环',['RTN','RT0'],'M0045 M0046 M0051 M0056 M0129',cell='Li||S软包',sulfur_loading='RTN4.8；RT0 3.5 mg cm-2',ES=4.5,ES_unit='μL mgS-1',voltage='1.65–2.45 V',**dict(c,rate='C/20',formation='未报告'))
result(t2,'放电容量','RTN','RT0',930,250,'mAh g-1','单次循环','M0129',same=False,reason='载硫量4.8 vs3.5 mg cm-2；作者认为电解液主导但非同条件')
ts=[]
for temp,vol,improvements,ids in [(25,'1.7–2.7 V',[13,9],'M0200'),(0,'1.65–2.75 V',[26,15],'M0201'),(-20,'1.5–2.8 V',None,'M0204 M0205 M0207 M0208 M0209 M0210')]:
 tt=test(p,f'{temp}°C扣式单次充放电',['LTN','LTL','LT0'],'M0041 M0058 M0059 '+ids,sulfur_loading='3.1 mg cm-2',ES=13,ES_unit='μL mgS-1',voltage=vol,**dict(c,temperature=f'{temp} °C',rate='C/20',formation='每温度至少静置3 h'))
 ts.append(tt)
 if improvements:
  for b,v in zip(['LT0','LTL'],improvements):result(tt,'相对放电容量提高','LTN',b,v,None,'%','该温度单循环',ids,reason='原文相对提升，不反算绝对容量')
 else:
  result(tt,'放电平台/转化','LTN','LT0','四平台','无低电压平台',None,'−20°C','M0204 M0207',basis='qualitative',reason='非单一数值性能量')
  result(tt,'Li2S转换平台电位','LTN','LTL',1.9,1.7,'V','第三平台vs低平台','M0205 M0210',same=True,reason='平台对应物种解释仍不确定，方向不直接判')
for sm,ids,src in [
('NH4TFA与多硫化锂原位形成LiTFA及二铵多硫化物，抑制不利聚簇并增强溶液反应动力学。','M0227','本文结论'),
('NH4–Sx与Li–TFA结合竞争破坏Li–Sx聚簇骨架，增强溶液动力学。','M0228','本文结论'),
('NH4与Li两种不同聚簇驱动力相互竞争，可能共同抑制团簇形成。','M0159','本文推测'),
('另一可能是铵多硫化物团簇不占用Li载流子，因此减小对电荷转移的损害。','M0160','本文推测'),
('低温仍形成混合锂铵多硫团簇，且平均Li配位比纯锂多硫簇更有利。','M0185','本文结论'),
('竞争配位保持更有利解离的Li配位状态，为提升溶液电化学动力学提供基础。','M0187','本文结论'),
('−20°C四平台可能反映不同混合铵锂多硫物种的分阶段放电。','M0212','本文推测'),
('NH4替代阻碍聚簇、提高Li2S转化电位，体现于1.9 V第三平台。','M0217','本文结论'),
('较软NH4被DOL/DME更有效溶剂化，可能造成第二、第四平台电位损失。','M0218','本文推测')]:mech(p,sm,'LTN','LT0/LTL','竞争配位/聚簇','正极反应',ids,[t,t2]+ts,source=src)
p['gaps']=['没有锂半电池及负极稳定性独立数据。','贫液软包仅一圈，不能等同循环寿命。','第60圈后容量波动作者归因室温意外改变（M0100）。','25/0°C仅相对容量提升，−20°C无绝对容量数值，禁止自行反算/目测。','NMR模型溶剂及浓度不同于电池配方，properties明确标为模型。']
save(p)
