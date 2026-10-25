from agent_b_common import *
p=paper('P002','TFSI','不含LiNO3的自配对照')
for i,s in [('TFSI','LiTFSI'),('TDI','LiTDI'),('TFSI_add','LiTFSI'),('TDI_add','LiTDI')]:
 cp=[('DOL','溶剂化溶剂',1,'体积份'),('DME','溶剂化溶剂',1,'体积份'),(s,'盐',1,'M')];cp+= [('LiNO3','添加剂',0.2,'M'),('Li2S8','添加剂',0.04,'M')] if i.endswith('add') else [];form(p,i,i,cp,'M0130 M0080')
grad(p,'盐种类',['TFSI','TDI'],['LiTFSI','LiTDI'],'TDI引发更大LiPS聚集，非单一Li+溶剂化尺度','M0043 M0044 M0107')
for n,a,b,u in [('电导率',10.8,6.2,'mS cm-1'),('黏度',1.35,1.31,'cP'),('最大Li2S8溶解度','≈0.5',0.084,'M')]:prop(p,n+'/'+u,{'TFSI':a,'TDI':b},'原数值比较','电导仪/黏度计/过量溶解稀释','30°C；1M盐+DOL/DME','M0060 M0061 M0115 M0116 M0132')
prop(p,'LiPS聚集尺度',{'TDI':'加入0.05M Li2S8后rs,Li/rLi从10.13至12.06','TFSI':'10.16至10.42'},'TDI聚集更大','NMR扩散推得水动力半径','加入Li2S8前后','S0015 M0044')
prop(p,'Li+溶剂化',{'TDI':'主要DME','TFSI':'主要DME'},'DOL影响小','7Li/17O NMR','1M盐DOL/DME','M0022')
c=dict(sulfur_loading='<1 mg cm-2',Li_thickness='400 μm',rate='C/5',temperature='室温（数值未报告）',LiNO3='无',one_C='1675 mA g-1',voltage='1.5–2.8 V')
t=test(p,'薄正极循环及初始曲线',['TDI','TFSI'],'M0055 M0056 M0083 M0125 M0133 M0135',ES='S/E按配方优化；图标数值文本未给',ES_unit='gS/L E（倒数口径）',**c)
result(t,'初始容量','TDI','TFSI',995,1170,'mAh g-1','首圈','M0057',same=None,reason='各配方S/E单独优化；无法确认相等')
result(t,'保持率差','TDI','TFSI','25% higher',None,None,'100圈','M0070',basis='qualitative',same=None,reason='原文相对提高口径未给分母；不反算且S/E未确认相同')
result(t,'初始CE','TDI','TFSI','提高','较低',None,'首圈','M0071',basis='qualitative',same=None,reason='条件未确认相同')
fig(p,t,'Fig.2b','首圈/100圈容量','TDI','TFSI','同圈','M0057 M0070',reason='先读取各曲线S/E语义；S/E不同则不判。锚点需同测试。')
for se in [50,70]:
 tx=test(p,f'TDI S/E={se}循环',['TDI'],'M0068 S0014',ES=se,ES_unit='gS/L E（S/E，不是E/S）',**c)
 fig(p,tx,'Fig.S2b','容量/保持率','TDI',None,'首圈/100圈',[],part='si')
th=test(p,'厚正极无添加剂',['TFSI','TDI'],'M0075 M0076 M0077 M0084 M0127 M0133 M0135',**dict(c,sulfur_loading='≈3 mg cm-2',rate='C/2（2.4 mA cm-2）',formation='5圈C/10（0.5 mA cm-2）'),ES='未报告')
result(th,'放电容量','TDI','TFSI',300,300,'mAh g-1','厚正极测试（取值圈未指明）','M0077')
ta=test(p,'厚正极含LiPS和LiNO3',['TDI_add','TFSI_add'],'M0075 M0076 M0080 M0084 M0127 M0133 M0135',**dict(c,sulfur_loading='≈3 mg cm-2',rate='C/2（2.4 mA cm-2）',formation='5圈C/10（0.5 mA cm-2）',LiNO3='0.2 M'),ES='未报告')
result(ta,'化成初始容量','TDI_add','TFSI_add',1110,1140,'mAh g-1','初始C/10（非化成后首圈）','M0081');result(ta,'循环容量','TDI_add',None,570,None,'mAh g-1','300圈稳定','M0090');result(ta,'面容量','TDI_add',None,1.67,None,'mAh cm-2','300圈','M0093');result(ta,'CE','TDI_add',None,99,None,'%','稳定循环','M0091');result(ta,'CE','TFSI_add',None,'≈80',None,'%','150圈后','M0089');result(ta,'寿命/稳定性','TDI_add','TFSI_add','稳定300圈','150圈后快速衰减',None,'长期循环','M0089 M0090',basis='qualitative',direction='变好')
fig(p,ta,'Fig.3a','化成后C/2首圈及150/300圈容量','TDI_add','TFSI_add','C/2首圈/150/300圈','M0090 M0093')
for s,ids,pr,cats,source,side,tt in [('TDI较低初始硫利用率可能由于长链LiPS溶解度低','M0058 M0066','LiPS溶解度','正极反应','本文推测','弱侧',[t]),('减少电解液量和LiPS溶解度通过减少硫损失提高保持','M0069','LiPS溶解度/电解液量','正极反应 多硫化物穿梭','本文结论（与他文一致）','强侧',[t]),('较高LiPS溶解度使TFSI电解液更腐蚀、消耗LiNO3更快','M0082 M0087','LiPS溶解度','负极锂 电解液消耗','本文结论','强侧',[ta]),('TFSI中更多LiPS加快锂负极失效','M0088','LiPS溶解度','负极锂','本文结论','强侧',[ta]),('TDI低LiPS浓度降低LiNO3消耗，保持高CE','M0091','LiPS溶解度','电解液消耗','本文结论','强侧',[ta]),('少溶解与添加LiPS润湿协同，使厚正极充分输出并稳定','M0092','LiPS溶解度/预添加','正极反应','本文结论','其他',[ta]),('TDI减少LiPS溶解，抑制穿梭、硫损失和锂劣化','M0105','LiPS溶解度','正极反应 多硫化物穿梭 负极锂','本文结论','强侧',[ta]),('TDI配位改变LiPS歧化形成Li4S8二聚体降低溶解度','M0107','LiPS聚集','正极反应','本文结论','其他',[])]:mech(p,s,'TDI','TFSI',pr,cats,ids,tt,side,source)
p['design_claims']=[dict(summary='盐选择降低LiPS溶解度，并加少量LiPS与LiNO3改善厚电极性能',evidence_ids=['M0105','M0108'])]
p['gaps']=['S/E系列各档文本仅给50与70以及总范围15–100，完整档位需图语义。厚极E/S未给。Li2S8添加量正文0.04M/1%与总结0.1%有冲突，保留明确摩尔量。未报告锂半电池。']
save(p)
