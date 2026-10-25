from independent_c_helpers import *
p=init('P337'); p['control_id']='R-SEI';p['control_type']='常规醚基准（DOL/DME + LiTFSI + LiNO3）'
for id,f,n in [('R-SEI',False,False),('F-SEI',True,False),('N-SEI',False,True),('FN-SEI',True,True)]:
 cs=[['LiTFSI','盐','1','M'],['DOL','溶剂化溶剂','4.5' if f else '1','体积份'],['DME','溶剂化溶剂','4.5' if f else '1','体积份'],['LiNO3','添加剂','2','wt%']]
 if f:cs.append(['TFTFE','弱或非溶剂化溶剂','1','体积份'])
 if n:cs.append(['LNO-SRF（LiNO3/Li-Nafion膜）','添加剂','LiNO3 loading about 1.2','mg cm−2'])
 form(p,id,'1 M LiTFSI DOL/DME'+('/TFTFE 4.5:4.5:1' if f else ' 1:1')+' +2 wt% LiNO3'+('；另配LNO-SRF' if n else ''),cs,'S0001 S0002 S0003 M0054 M0055')
grad(p,'TFTFE和LiNO3缓释膜二因素对照',['R-SEI','F-SEI','N-SEI','FN-SEI'],['无/无','有/无','无/有','有/有'],'不是单调溶剂化梯度','S0003')
prop(p,'LiNO3释放速度',{'N-SEI':'Li浓度7.14/7.56/8.22/8.82/10.05 g L−1','FN-SEI':'7.14/7.38/7.56/8.28/9.90 g L−1'},'TFTFE减慢释放；12/24/36/48/168 h','ICP-OES','LNO-SRF浸泡的1 M LiTFSI电解液','M0073 M0074 M0075 M0076')
prop(p,'Li+溶剂化',{'LiNO3浓度提高':'7Li化学位移降低；NO3−与Li+相互作用加强'},'NO3−进入配位环境','NMR','含不同LiNO3浓度的DOL/DME电解液','M0086 M0087 M0088 M0089')
forms=['R-SEI','F-SEI','N-SEI','FN-SEI']
base={'Li_thickness':'50 μm（SI）；长循环正文100 μm，冲突单列','rate':'1 mA cm−2, 1 mAh cm−2','LiNO3':'2 wt%；N/FN另有LNO-SRF','electrolyte_volume':'40 μL'}
t=test(p,'T1','Li||Cu平均CE','Li||Cu CR2032',base,forms,'S0006 S0007 S0008 S0014 M0125 M0126')
for b,v in [('R-SEI','98.46'),('F-SEI','99.02'),('N-SEI','99.17')]:result(t,'平均CE','FN-SEI',b,'99.63',v,'%','Figure 3e–h平均法','numeric','不判','M0129')
result(t,'成核过电位','FN-SEI',None,'46',None,'mV','沉积开始','numeric','不判','M0127')
result(t,'沉积过电位','FN-SEI',None,'24',None,'mV','沉积','numeric','不判','M0127')
t=test(p,'T2','Li||Cu持续循环','Li||Cu CR2032',base,forms,'S0006 S0007 S0014 M0145')
for b,v in [('R-SEI','25'),('F-SEI','98'),('N-SEI','135')]:result(t,'稳定循环数','FN-SEI',b,'over 400','within '+v,'cycles','CE快速下降前','numeric','不判','M0145')
t=test(p,'T3','Li||Li持续循环','Li||Li CR2032',{**base,'Li_thickness':'100 μm（正文）；SI通用50 μm，未消歧'},forms,'S0004 S0005 S0008 M0142 M0143 M0190')
for b,v in [('R-SEI','560'),('F-SEI','1054'),('N-SEI','1400')]:result(t,'稳定循环时间','FN-SEI',b,'up to 2000',v,'h','短路前','numeric','不判','M0142 M0143')
t=test(p,'T4','Li||Li界面动力学','Li||Li',{'Li_thickness':'50 μm','rate':'CV 0.1 mV s−1','LiNO3':'2 wt%；有无缓释膜'},forms,'S0004 S0009 S0010 S0011 S0012 S0013')
for b,v in [('R-SEI','0.22'),('F-SEI','0.56'),('N-SEI','0.91')]:result(t,'交换电流密度','FN-SEI',b,'1.58',v,'mA cm−2','Tafel拟合','numeric','不判','M0131')
for b,v in [('R-SEI','9.06'),('F-SEI','7.17'),('N-SEI','6.02')]:result(t,'界面Li+输运活化能','FN-SEI',b,'4.46',v,'kJ mol−1','变温EIS','numeric','不判','M0139')
li={'sulfur_loading':'5.0 mg cm−2','Li_thickness':'50 μm','ES':'5','ES_unit':'μL mgS−1','LiNO3':'2 wt%；FN另配缓释膜','voltage':'1.7–2.6 V'}
t=test(p,'T5','相等LiNO3总量Li-S循环','CNT/S||Li CR2032',{**li,'rate':'0.5 C','LiNO3':'调节膜载量使每电池LiNO3总量相同；具体总量未报告'},['FN-SEI','R-SEI'],'M0159 M0160 M0165 S0015 S0017')
result(t,'容量保持率','FN-SEI','R-SEI','80.6','61.3','%','100 cycles','numeric','不判','M0165')
t=test(p,'T6','高载量Li-S循环','CNT/S||Li CR2032',{**li,'rate':'0.1 C'},['FN-SEI','R-SEI'],'M0169 M0219 S0015 S0017 S0018')
result(t,'初始放电容量','FN-SEI','R-SEI','about 1250','about 1250','mAh g−1','初始圈','numeric','差异小','M0173')
result(t,'稳定循环寿命','FN-SEI','R-SEI','250','approximately 25','cycles','容量快速下降前','numeric','不判','M0174 M0175 M0219')
result(t,'极化电压','FN-SEI','R-SEI','220','360','mV','25圈后，依Fig. S15标题','numeric','不判','M0177 S0057')
result(t,'残余活性锂','FN-SEI','R-SEI','91.2','14.5','%','25 cycles','numeric','不判','M0196')
t=test(p,'T7','穿梭电流','CNT/S||Li CR2032',{**li,'rate':'0.1 C循环后多电位恒电位稳态电流'},['FN-SEI','R-SEI'],'M0170 S0019 S0020 S0021')
result(t,'穿梭电流','FN-SEI','R-SEI','close to 0','close to 0',None,'第1圈','qualitative','差异小','M0171')
result(t,'穿梭电流','FN-SEI','R-SEI','approximately five times lower','比较基准',None,'25圈','qualitative','变好','M0172')
t=test(p,'T8','Li-S软包循环','CNT/S||Li pouch',{'sulfur_loading':'6 mg cm−2','ES':'3','ES_unit':'μL mgS−1','Li_thickness':'50 μm','LiNO3':'2 wt%；FN缓释膜；Table S1未列TFTFE'},['FN-SEI'],'M0197 M0198 M0200 M0201 M0203 S0074')
result(t,'放电容量','FN-SEI',None,'1.67',None,'Ah','初始','numeric','不判','M0200')
result(t,'放电容量','FN-SEI',None,'1.55',None,'Ah','20 cycles','numeric','不判','M0201')
result(t,'全电池质量能量密度','FN-SEI',None,'about 300',None,'Wh kg−1','初始','numeric','不判','M0203')
t=test(p,'T9','Li-Nafion膜单独对照','Li||S及Li||Li（两图仅定性）',{'LiNO3':'未明确独立膜对照用量'},['R-SEI','Li-Nafion膜（非缓释膜）'],'M0144 M0179 S0051 S0058')
result(t,'Li沉积剥离极化','Li-Nafion膜（非缓释膜）','R-SEI','降低','基准',None,'Fig.S10','qualitative','变好','M0144')
result(t,'Li-S循环寿命','Li-Nafion膜（非缓释膜）','R-SEI','改善','基准',None,'Fig.S16','qualitative','变好','M0179')
for summary,e,cats,typ,ts in [
('TFTFE抑制LiNO3快速溶出，与聚合物封装共同持续补充NO3−，支持长循环牺牲成膜','M0081',['负极锂','电解液消耗'],'本文结论',['T2','T3','T6']),
('FN-SEI调节Li+沉积，抑制枝晶和死锂','M0119',['负极锂'],'本文结论',['T1','T3']),
('枝晶受抑降低反应表面积和副反应可能性','M0122',['负极锂'],'本文结论',['T2']),
('对照SEI无法有效阻止高表面积枝晶，副反应和死锂累积造成CE快速衰减','M0146',['负极锂'],'本文结论',['T2']),
('FN-SEI中更多LiF/Li3N/LiNxOy促进均匀沉积','M0147',['负极锂'],'本文结论',['T1','T3']),
('缓释膜补充循环消耗的LiNO3','M0148',['电解液消耗'],'本文结论',['T2','T6']),
('FN-SEI不影响硫氧化还原动力学','M0157 M0158',['正极反应'],'本文结论',[]),
('R-SEI电池25圈后因严重枝晶和LiNO3耗尽而容量快速下降、CE波动','M0174',['负极锂','电解液消耗'],'本文结论',['T6']),
('R-SEI严重钝化导致极化增加','M0178',['负极锂'],'本文结论',['T6']),
('Li-Nafion屏蔽LiPSs，PP骨架调控Li+流，单独用膜也改善寿命','M0179',['多硫化物穿梭','负极锂'],'本文结论',['T9']),
('FN-SEI屏蔽LiPSs、加快Li+迁移并抑制电子隧穿，因此改善Li CE并抑制穿梭','M0204',['多硫化物穿梭','负极锂'],'本文结论',['T1','T6','T7'])]:
 mech(p,summary,'FN-SEI','R-SEI','缓释LiNO3/F-N富集SEI',cats,typ,e,ts,'其他')
claim(p,'通过LiNO3封装和10 vol% TFTFE共同控制释放，实现持久F/N富集SEI','M0043 M0047 M0063 M0206')
for tid,f,pt,e in [('T5','Figure S13b','首圈及100圈','M0165'),('T6','Figure 5c','首圈及250圈','M0173 M0174 M0175'),('T8','Figure S20','首圈及20圈','M0200 M0201')]:
 fig(p,tid,f,'si' if 'S' in f else 'main','容量','FN-SEI','R-SEI' if tid!='T8' else None,pt,e,'补全文字缺失容量侧，仅锚点校验通过才使用')
p['gaps']=['Li||Li厚度正文100 μm与SI通用50 μm冲突，保留两者','Table S1软包电解液只写DOL/DME，未写TFTFE，与FN命名不一致','Li-Nafion单独对照仅定性；T9两个电池体系未合并数值比较','温度、化成、1C定义未报告；溶解度/电导率/黏度实测值未报告；模拟电导率不当实测']
save(p)

