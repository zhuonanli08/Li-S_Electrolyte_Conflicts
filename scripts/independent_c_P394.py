from independent_c_helpers import *
p=init('P394');p['control_id']='base';p['control_type']='不含LiNO3的自配对照：DOL/TEGDME+LiTFSI'
form(p,'base','1 M LiTFSI in DOL/TEGDME 1:1 v/v',[['LiTFSI','盐','1','M'],['DOL','溶剂化溶剂','1','体积份'],['TEGDME','溶剂化溶剂','1','体积份']],'M0164')
form(p,'hybrid','[S222][TFSI]:base=1:3 v/v；主盐随加入IL稀释，原文未给最终浓度',[['[S222][TFSI]','添加剂（离子液体）','1','体积份'],['base','基液','3','体积份']],'M0165')
grad(p,'加入离子液体',['base','hybrid'],['0','IL:base=1:3 v/v'],'非Li+溶剂化强弱梯度；作用主要为LiPS结合/界面','M0164 M0165')
prop(p,'离子电导率',{'base':'0.7至1 mS cm−1','hybrid':'1.1至2.45 mS cm−1'},'hybrid较高，随10至70 °C增加','EIS','浸电解液Celgard2320夹于钢电极','M0038 M0039 M0040')
prop(p,'多硫化物相互作用',{'hybrid':'短链Li2S/Li2S2比长链结合更强；Li2S6/Li2S8有局部结合回升'},'不收不同方法的DFT能量数值','DFT B3LYP','孤立IL分子与LiPS复合物，不是实测溶解度','M0113 M0115 M0119')
c={'LiNO3':'未添加','temperature':'室温'}
t=test(p,'T1','储存自放电','S/MWCNT||Li CR2032',c,['base','hybrid'],'M0041 M0042 M0043 M0162')
result(t,'OCV','base',None,'2.54→2.43',None,'V','18天储存','numeric','不判','M0042')
result(t,'OCV','hybrid',None,'2.58',None,'V','第7天起维持','numeric','不判','M0043')
result(t,'自放电','hybrid','base','较低','较高',None,'储存','qualitative','变好','M0043 M0044')
result(t,'bulk电阻','hybrid',None,'~4.2',None,'Ω','第12天后','numeric','不判','M0053','原文近似符号编码异常')
t=test(p,'T2','CV','S/MWCNT||Li CR2032',{**c,'rate':'0.1 mV s−1','voltage':'结果段1.5–3.0 V，方法1.0–3.0 V'},['base','hybrid'],'M0055 M0059 M0174')
result(t,'氧化还原峰差ΔEp','hybrid','base','0.08','0.24','V','前两圈','numeric','不判','M0061')
t=test(p,'T3','首圈恒流','S/MWCNT||Li CR2032',{**c,'rate':'0.1 C','voltage':'1.5–3.0 V'},['base','hybrid'],'M0062 M0173')
result(t,'首圈比容量','hybrid',None,'1200',None,'mAh g−1','首圈（未明确充/放）','numeric','不判','M0063')
result(t,'充放电极化','hybrid','base','较小','较大',None,'首圈','qualitative','变好','M0064 M0070')
t=test(p,'T4','Li界面储存阻抗','Li||Li',c,['base','hybrid'],'M0076 M0077 M0079')
result(t,'界面电阻稳定性','hybrid','base','第3天后较低且近乎恒定','持续变化',None,'储存','qualitative','变好','M0079')
t=test(p,'T5','Li沉积剥离','Li||Li',{**c,'rate':'0.1 mA cm−2，充放各60 min'},['base','hybrid'],'M0081 M0082')
result(t,'过电位','hybrid','base','~0.006','~0.013','V','恒流剥离沉积','numeric','不判','M0083','原文近似符号编码异常')
result(t,'稳定持续时间','hybrid',None,'200',None,'h','仍恒定过电位','numeric','不判','M0084')
t=test(p,'T6','首圈原位EIS','S/MWCNT||Li CR2032',{**c,'rate':'0.1 C；EIS 200 kHz–100 mHz'},['base','hybrid'],'M0086 M0091 M0172')
result(t,'电荷转移电阻','hybrid','base','首圈充放近恒定','放电显著增加',None,'首圈不同电位','qualitative','变好','M0092 M0093')
for su,pr,cats,typ,e,ts in [
('IL稳定CEI降低自放电','界面稳定',['正极反应','多硫化物穿梭'],'本文结论','M0043',['T1']),
('IL抑制多硫化物溶解和自放电','LiPS溶解',['多硫化物穿梭'],'本文结论（与他文一致）','M0044',['T1']),
('TFSI与Li2S结合延长Li-S键、降低活化能，因此减小充电过电位','LiPS结合',['正极反应'],'本文结论（与他文一致）','M0071 M0072 M0073',['T3']),
('稳定SEI使Li沉积剥离200小时保持恒定过电位','SEI稳定',['负极锂'],'本文结论','M0084',['T5']),
('对照Rct增加可能来自不溶多硫化物在Li表面沉积','LiPS溶解/沉积',['负极锂','多硫化物穿梭'],'本文推测','M0094 M0095',['T6']),
('Li2S相关FTIR信号减弱提示稳定SEI和穿梭受控','SEI稳定',['负极锂','多硫化物穿梭'],'本文结论（与他文一致）','M0103 M0104',['T6']),
('IL溶解正极Li2S/Li2S2钝化沉积，可能提高活性硫利用率并减少衰减','短链LiPS结合',['正极反应'],'本文推测','M0156',['T3']),
('较短高电位平台又被作者推测与较强穿梭有关，和全文抑穿梭说法存在张力','穿梭',['多硫化物穿梭'],'本文推测','M0070',['T3'])]:
 mech(p,su,'hybrid','base',pr,cats,typ,e,ts,'其他')
claim(p,'IL添加剂同时改善界面并与LiPS作用；本文只测试Li-S首圈，寿命提升未实际长循环验证','M0151 M0152 M0153 M0156 M0086')
p['gaps']=['未报告硫载量/E/S/锂厚/1C定义/化成','无Li-S长循环保持率和Li||Cu CE；Figure6电压曲线不属于允许读图两类，容量对照仅图未读','未测Li+溶剂化、迁移数、黏度或LiPS定量溶解度；不能将DFT结合强当实测溶解度','CV电压范围方法与结果冲突；原文M0070强穿梭说法与主要结论不一致']
save(p)

