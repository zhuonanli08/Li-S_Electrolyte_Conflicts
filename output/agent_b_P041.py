from agent_b_common import *
p=paper('P041','1-TFSI','不含LiNO3的自配对照')
fs=[]
for salt in ['TfO','FSI','TFSI','TDI']:
 for n in ([1] if salt=='TDI' else [1,3]):
  i=f'{n}-{salt}';fs.append(i);form(p,i,i,[('DOL','溶剂化溶剂',1,'体积份'),('DME','溶剂化溶剂',1,'体积份'),('Li'+salt,'盐',n,'M')],'M0013 M0020 S0029')
 form(p,'1-'+salt+'-PS','1-'+salt+'-PS',[('DOL','溶剂化溶剂',1,'体积份'),('DME','溶剂化溶剂',1,'体积份'),('Li'+salt,'盐',1,'M'),('Li2S8','表征溶质',0.12,'M')],'M0017 M0021')
for salt in ['TfO','FSI']:form(p,'4-'+salt,'4-'+salt,[('DOL','溶剂化溶剂',1,'体积份'),('DME','溶剂化溶剂',1,'体积份'),('Li'+salt,'盐',4,'M')],'S0046')
grad(p,'1M盐种类',['1-TDI','1-TFSI','1-FSI','1-TfO'],['LiTDI','LiTFSI','LiFSI','LiTfO'],'Li+-DME相互作用由强到弱；不等同阴离子缔合程度','M0048 M0121')
for salt in ['TfO','FSI','TFSI']:grad(p,salt+'浓度',[f'1-{salt}',f'3-{salt}'],[1,3],'浓度提高增加聚集；各阴离子迁移及LiPS亲和不同','M0050')
prop(p,'实测电导率/S cm-1',dict(zip(['1-FSI','1-TfO','1-TFSI','1-TDI'],['1.7×10−2','2.6×10−3','1.1×10−2','6.2×10−3'])),'FSI>TFSI>TDI>TfO','电导仪','30°C、1M盐','M0045')
prop(p,'Li+-DME溶剂化强度',{'1-TDI':'最强','1-TFSI':'次之','1-FSI':'次弱','1-TfO':'最弱'},'TDI>TFSI>FSI>TfO','17O NMR','1M电解液','M0048')
prop(p,'LiPS相互作用/溶解',{'1-TfO-PS':'强相互作用，促进解离','1-TDI-PS':'最弱相互作用，限制溶解'},'TfO与TDI不同','PFG NMR有效半径','0.12M Li2S8的1M电解液','M0103 M0104')
prop(p,'阴离子迁移',{'3-FSI':'相对更快','3-TFSI':'聚集中受限','3-TfO':'聚集中受限'},'FSI较快；TDI较低','17O/PFG NMR','0–50°C','M0062 M0063 M0136')
c=dict(sulfur_loading='approximately 1 mg cm-2',Li_thickness='0.45 mm',rate='0.2 C；1.5–3 V',one_C='1675 mA gS-1',LiNO3='配方未添加')
t=test(p,'盐种类/浓度LiS循环',fs,'M0025 M0030 M0031 S0012 S0060',cell='Li||S/MWCNT coin2320（原文）',**c)
result(t,'寿命','3-FSI',None,34,None,'cycles','突然失效','M0129');result(t,'长期容量','1-TDI','1-FSI','较好','较差',None,'长期循环','M0128 M0136',basis='qualitative',direction='变好');result(t,'长期容量','3-TfO','3-TFSI','低于迁移率预测','较好',None,'100圈','M0124 M0125',basis='qualitative',direction='不判',reason='原文偏离关联预测，不作为明确成对数值方向')
result(t,'衰减','3-TfO','1-TfO','更快','较慢',None,'33–100圈','M0127',basis='qualitative',direction='变坏')
fig(p,t,'Fig.S8a','1M四种盐各档容量','1-TDI/1-TfO/1-FSI','1-TFSI','首圈/33/100圈',[],part='si');fig(p,t,'Fig.S8b','3M三种盐各档容量','3-FSI/3-TfO','3-TFSI','首圈/33/100圈','M0129',part='si')
for s,ids,A,B,pr,cats,source,side in [('慢阴离子迁移有助稳定循环，但TfO虽慢仍表现差','M0078','全梯度',None,'阴离子迁移','负极锂','本文结论','其他'),('TfO较低迁移率并不足保证好性能','M0083','TfO','其他盐','阴离子迁移','正极反应','本文结论','其他'),('Li+/DME迁移与容量或衰减无线性关系','M0077','全梯度',None,'Li+迁移','正极反应','本文结论','其他'),('TDI对LiPS相互作用最弱，限制其溶解','M0104','1-TDI','1-TfO','LiPS溶解度','正极反应','本文结论','其他'),('TfO强LiPS作用可能增加正极活性物损失导致低容量','M0125','3-TfO','其他盐','LiPS溶解度','正极反应','本文推测','强侧'),('高浓度TfO促进LiPS损失，加速容量衰减','M0127','3-TfO','1-TfO','LiPS溶解度','正极反应','本文结论','强侧'),('3FSI突发失效可能因负极绝缘钝化层快速形成','M0129','3-FSI','3-TFSI','阴离子迁移','负极锂','本文推测','其他'),('FSI高迁移可能加强锂表面作用并加速有害SEI','M0134','FSI','其他盐','阴离子迁移','负极锂','本文推测','其他'),('TfO即使迁移低也能强作用LiPS并加快溶解','M0135','TfO','其他盐','LiPS相互作用','正极反应','本文结论','强侧'),('TDI较低迁移及弱LiPS作用使电池表现较好','M0136','TDI','其他盐','阴离子迁移/LiPS作用','正极反应 负极锂','本文结论','其他')]:mech(p,s,A,B,pr,cats,ids,[t],side,source)
p['design_claims']=[dict(summary='同时选低迁移率且弱LiPS相互作用阴离子，不能单看Li+-溶剂相互作用',evidence_ids=['M0149','M0121'])]
p['gaps']=['E/S、化成、循环温度未明确；无锂半电池。正文泛称1/3M四种盐，SI扩散系列及可确认配方未列3M TDI，因此不虚构其数据。图容量缺锚点时不用。文献列举黏度不当本篇实测数。']
save(p)
