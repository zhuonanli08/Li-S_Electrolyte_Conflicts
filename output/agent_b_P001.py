from agent_b_common import *
p=paper('P001','T1','常规醚基准（DOL/DME + LiTFSI + LiNO3）')
for i,s,n in [('T1','LiTFSI',1),('T3','LiTFSI',3),('F3','LiFSI',3)]:
 cp=[('DOL','溶剂化溶剂',1,'体积份'),('DME','溶剂化溶剂',1,'体积份'),(s,'盐',n,'M')];cp+= [('LiNO3','添加剂',0.2,'M')] if i=='T1' else [];form(p,i,i,cp,'M0038 M0050 M0170')
grad(p,'盐种类',['T3','F3'],['LiTFSI','LiFSI'],'TFSI聚集程度高；不强行等同LiPS溶剂化强弱','M0124 M0132');grad(p,'LiTFSI浓度',['T1','T3'],[1,3],'高盐溶剂可用量减少；LiNO3也变化','M0036 M0050')
prop(p,'黏度/cP',{'T3':25.9,'F3':9.24},'T3>F3','原文物性表','25°C','S0012');prop(p,'电导率（原表单位mS）',{'T3':2.81,'F3':14.82},'F3>T3','原文物性表','25°C；表未写cm-1','S0012')
prop(p,'LiPS溶解度',{'T3':'高于F3','F3':'较低'},'F3<T3；浓电解液低于稀','饱和Li2S8外观','DOL/DME','M0117 M0144 S0024')
prop(p,'Li+溶剂化/聚集',{'T1':'主要DME配位','T3':'Li-DME-阴离子聚集','F3':'较低聚集程度'},'T3聚集高于F3','17O NMR','室温电解液','M0123 M0124 M0132')
prop(p,'自扩散系数排序',{'T3':'D_Li≈D_TFSI≈D_DME','F3':'D_FSI>D_DME≥D_Li'},'FSI阴离子移动更快','PFG NMR','0–50°C','M0138 M0139 M0181')
c=dict(sulfur_loading='about 1 mg cm-2',ES='未报告（60 μL/池）',Li_thickness='0.45 mm',rate='0.2 C',one_C='1.0 mA cm-2')
t=test(p,'浓盐LiS循环',['T3','F3'],'M0038 M0158 M0168 M0171 M0172 M0173',cell='Li||S/MWCNT CR2032',LiNO3='无',**c)
result(t,'保持率','T3',None,71.9,None,'%','200圈','M0039');result(t,'寿命','F3',None,33,None,'cycles','循环终点（EIS称35圈）','M0039');result(t,'CE','T3',None,101,None,'%','初始','M0040');result(t,'CE','T3',None,96.6,None,'%','200圈','M0040')
result(t,'CE','F3','T3','略高','较低',None,'循环','M0041',basis='qualitative',direction='不判',reason='CE>100%由副反应产生，不能简单更高=更好');result(t,'极化','T3','F3','更高','较低',None,'循环电压','M0048',basis='qualitative',direction='变坏')
fig(p,t,'Fig.1a','首圈及同圈容量','T3','F3','首圈、25或33圈','M0039')
tb=test(p,'常规电解液循环',['T1'],'M0050 S0015 M0173',cell='Li||S/MWCNT CR2032',LiNO3='0.2 M',**c)
result(tb,'衰减/CE','T1','T3','衰减更快且CE更低','较好',None,'不同图的作者定性','M0052',basis='qualitative',same=None,reason='图S1与图1不同批次未明，保留作者定性不判');fig(p,tb,'Fig.S1','首圈及终点容量','T1',None,'首圈、200圈',[],part='si')
te=test(p,'循环EIS',['T3','F3'],'M0111 M0174',**c)
result(te,'阻抗随循环','T3','F3','随循环下降','前5圈下降后增加至35圈失效',None,'循环','M0112 M0113',basis='qualitative',direction='变好')
for withps in [True,False]:
 tl=test(p,'LiCu锂效率'+('含饱和Li2S8' if withps else '无LiPS'),['T3','F3'],'M0115 S0023',cell='Li||Cu，'+('Li2S8饱和浓电解液' if withps else '无LiPS浓电解液'))
 if withps:result(tl,'CE稳定性','T3','F3','稳定','大幅波动',None,'沉积剥离','M0116',basis='qualitative',direction='变好')
for s,ids,pr,cats,source,tt in [('TFSI高黏度低电导导致更高极化','M0049','黏度/电导','正极反应','本文结论',[t]),('LiTFSI形成可逆硫化锂，LiFSI生成不可逆硫酸盐导致循环差','M0083','盐阴离子反应','负极锂','本文结论',[t]),('LiFSI不可逆放电产物不能充电分解，CE可能超过100%','M0085','盐阴离子反应','负极锂','本文结论',[t]),('FSI不可逆产物使钝化膜更厚','M0087','盐阴离子反应','负极锂','本文结论',[t]),('FSI电池电阻升高与绝缘硫酸盐钝化层快速生长一致','M0114','界面钝化','负极锂','本文结论',[te]),('FSI中更低LiPS溶解度可能导致盐在LiPS上升时析出','M0117','LiPS溶解度','正极反应','本文推测',[t]),('FSI扩散快与较低极化一致','M0140','阴离子扩散','正极反应','本文结论',[t]),('FSI扩散快可能促进锂表面分解形成更多硫酸盐','M0141','阴离子扩散','负极锂','本文推测',[t]),('FSI连续分解导致绝缘硫酸盐钝化层快速增厚','M0147','阴离子反应','负极锂','本文结论',[t])]:mech(p,s,'F3','T3',pr,cats,ids,tt,source=source)
p['design_claims']=[dict(summary='设计需同时考虑阴离子种类与浓度',evidence_ids=['M0153'])];p['gaps']=['LiCu条件和数值未报告；循环温度与化成未报告。LiPS溶剂化未单独测。高浓度对常规对照涉及LiNO3改变与跨图，保留定性不算同批数值方向。']
save(p)
