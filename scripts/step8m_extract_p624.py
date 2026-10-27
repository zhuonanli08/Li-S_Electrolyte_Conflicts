"""Root's source-only extraction after reading P624 main M1-M254 and all SI."""
import json
from step8a_prepare_debug53 import OUT,save

PID='P624';d={'paper_id':PID,'doi':'10.1016/j.ensm.2026.105072','formulations':[],
 'control_id':'control_unknown','control_type':'作者without DMTMSA对照；SI同时列单盐blank和双盐LiFSI，正文未明确所用者',
 'gradients':[],'properties':[],'tests':[],'mechanisms':[],'design_claims':[],'figure_requests':[],
 'gaps':[],'source_review':{'main':True,'si':True,'notes':'root独立阅读全文科学内容M0001-M0243及SI S0001-S0106；参考文献不作为本文证据。未读取旧提取。SI索引来自Word文本，page=0不是实际页码。'}}
def comp(n,role,a,u):return {'name':n,'role':role,'amount':a,'unit':u}
def f(i,n,components,raw,ev):d['formulations'].append({'id':i,'name':n,'components':components,'raw_formula':raw,'evidence_ids':ev})
sol=[comp('DOL','溶剂化溶剂',1,'体积份'),comp('DME','溶剂化溶剂',1,'体积份')]
f('blank','blank electrolyte',sol+[comp('LiTFSI','盐',1.0,'M'),comp('LiNO3','添加剂',0.3,'M')],'1 M LiTFSI + 0.3 M LiNO3 / DOL:DME=1:1 v/v',['S0005'])
f('FSI','LiFSI electrolyte',sol+[comp('LiTFSI','盐',0.5,'M'),comp('LiFSI','盐',0.5,'M'),comp('LiNO3','添加剂',0.3,'M')],'0.5 M LiTFSI + 0.5 M LiFSI + 0.3 M LiNO3 / DOL:DME=1:1 v/v',['S0005'])
f('D10','DMTMSA electrolyte',[comp('DOL','溶剂化溶剂',4.5,'体积份'),comp('DME','溶剂化溶剂',4.5,'体积份'),comp('DMTMSA','动态溶剂化溶剂',1,'体积份'),comp('LiTFSI','盐',0.5,'M'),comp('LiFSI','盐',0.5,'M'),comp('LiNO3','添加剂',0.3,'M')],'DOL:DME:DMTMSA=4.5:4.5:1 v/v；双盐各0.5 M，LiNO3 0.3 M',['S0005'])
f('D20','20vol% DMTMSA',[comp('DMTMSA','动态溶剂化溶剂',20,'vol%')],'仅正文明确20vol%；其余组分用量未报告，不从10%组外推',['M0049','S0052','S0053'])
f('control_unknown','without DMTMSA 对照',[comp('DMTMSA','动态溶剂化溶剂',0,'vol%')],'具体为blank或FSI电解液未明确，保留盐组成待核',['S0005','M0214'])
f('D10_N0','无LiNO3 DMTMSA',[comp('DMTMSA','动态溶剂化溶剂',10,'vol%'),comp('LiNO3','添加剂',0,'M')],'无LiNO3；其余盐组成未对本组明确',['M0085','M0100','M0214'])
f('control_N0','无LiNO3无DMTMSA',[comp('DMTMSA','动态溶剂化溶剂',0,'vol%'),comp('LiNO3','添加剂',0,'M')],'无LiNO3，无DMTMSA；盐组成未明确',['M0085','M0100'])
f('amide10','10% N,N-Dimethyltrifluoroacetamide',[comp('N,N-Dimethyltrifluoroacetamide','添加剂/溶剂',10,'%（原文未标基准）')],'10%酰胺；其余成分未报告',['S0047'])
for i,name,dd in [('CP0','Li2S8 catholyte without DMTMSA',0),('CP10','Li2S8 catholyte with DMTMSA',10)]:
 f(i,name,[comp('Li2S8','活性物',100,'mmol/L'),comp('LiTFSI','盐',1,'M'),comp('DMTMSA','动态溶剂化溶剂',dd,'vol%')],'20 μL catholyte；Li侧10 μL blank，LiNO3在catholyte未说明',['S0018'])
d['gradients']=[{'name':'DMTMSA用量','order':['control_unknown','D10','D20'],'values':[0,10,20],'solvation_axis':'简单电解液Li+溶剂化随DMTMSA增加而减弱；LiPS不能用统一强弱序：长链弱化、短链增强；其他含量档只在图中，尚未齐全','evidence_ids':['M0049','M0052','M0055','S0101','S0103','S0104']},
 {'name':'盐阴离子种类（性质实验）','order':['LiTFSI','LiFSI'],'values':None,'solvation_axis':'FSI-对DMTMSA诱导极化更强，Li2S4溶解度更高；不是已证实完整电池配方梯度','evidence_ids':['S0065','S0066','S0067','S0068']}]
def prop(name,values,direction,method,system,ev):d['properties'].append(dict(name=name,values=values,direction=direction,method=method,system=system,evidence_ids=ev))
prop('Li+溶剂化',{'D10':'DMTMSA主要在第二壳层约3.2 Å；DOL/DME第一壳层约1.8 Å，CN降低；TFSI靠近Li+'},'DMTMSA添加越多总体Li+配位减弱','1H/7Li/19F NMR、MD RDF/CN','不含LiPS的简单电解液',['M0041','M0043','M0047','M0049','M0052'])
prop('多硫化物溶剂化',{'DMTMSA':'Sn2-电荷密度诱导极化；Li2S4诱导强于Li2S8'},'相对DOL/DME：长链减弱，短链增强，不是单一强弱方向','17O/13C/7Li NMR、FTIR、Raman及计算','纯DMTMSA与Li2S4/Li2S8模型溶液',['M0036','M0037','M0053','M0055','M0059','M0060','M0062','M0063','M0064','M0066','M0074','M0076'])
prop('多硫化物溶解度',{'长链Li2Sn n>4':'降低超过50%','短链Li2Sn n≤4':'提升一个数量级'},'Li2S8降低、Li2S4增加','不同浓度溶液的沉淀及颜色深浅观察','简化溶剂溶液，不等同实际双盐电解液精确浓度',['M0057','M0058','M0228','S0042','S0054','S0055','S0056'])
prop('Li2S溶解度',{},'DMTMSA高于DOL/DME','溶解对照','溶剂模型体系',['M0198','M0199','M0200','S0096'])
prop('离子电导率',{},'添加DMTMSA降低但仍较高','电导测试，数值仅图S26','实际电解液',['M0129','M0130','S0087'])
prop('Li+迁移数',{},'添加DMTMSA提高','图S26，方法参数未写','电解液/电池',['M0131','S0088'])
prop('LiPS表观扩散',{},'DMTMSA组更高，第二还原阶段尤明显','CV峰电流与扫描速度平方根拟合','Li-S电池',['M0121','M0122','M0123','S0082','S0083'])
prop('黏度',{},'未报告','未报告','未报告',[])
prop('盐阴离子影响Li2S4溶解度',{},'均因同离子效应降低；加LiFSI后仍高于加LiTFSI','颜色对比与1H/19F NMR','DMTMSA+Li2S4简化溶液',['S0065','S0066','S0067','S0068'])
def test(name,cell,cond,ev,forms=None):
 t={'id':f'{PID}-T{len(d["tests"])+1}','name':name,'cell':cell,'conditions':{k:'未报告' for k in ['sulfur_loading','ES','ES_unit','Li_thickness','rate','formation','temperature','LiNO3','one_C']},'formulations':forms or ['D10','control_unknown'],'evidence_ids':ev,'results':[]};t['conditions'].update(cond);d['tests'].append(t);return t
def result(t,metric,va=None,vb=None,unit=None,point='未报告',ev=(),basis='numeric',direction='不判',same=None,A=None,B=None,reason='对照盐组成未明确；不把可能的双因素改变强当单一溶剂效应'):
 r={'id':t['id']+f'-R{len(t["results"])+1}','metric':metric,'A':A or t['formulations'][0],'B':B if B is not None else (t['formulations'][1] if len(t['formulations'])>1 else None),'value_A':va,'value_B':vb,'unit':unit,'point':point,'basis':basis,'direction_text':direction,'same_conditions':same,'evidence_ids':list(ev),'reason':reason};t['results'].append(r)
common={'Li_thickness':'450 μm（通用扣电方法）','temperature':'室温','one_C':'1675 mA gS−1','voltage_window':'1.7–2.6 V'}
t1=test('无LiNO3穿梭电流','Li‖S CR2025',{**common,'LiNO3':'0','rate':'恒流充至2.90 V，再阶梯恒压放电2.60/2.45/2.43/2.40/2.39/2.38/2.37/2.36/2.35/2.34/2.25/2.20 V'},['M0085','M0100','S0015','S0016'],['D10_N0','control_N0']);result(t1,'穿梭电流',None,'接近0.5','mA','不同恒压点',['M0100'],basis='qualitative',direction='变好')
t2=test('无LiNO3完整充放电','Li‖S CR2025',{**common,'LiNO3':'0'},['M0086','M0101','M0103'],['D10_N0','control_N0']);result(t2,'过充/完整充电',point='充放电曲线',ev=['M0101'],basis='qualitative',direction='变好');result(t2,'第一放电平台容量',point='第一平台',ev=['M0103'],basis='qualitative',direction='变好')
t3=test('循环后正负极保留与腐蚀表征','Li‖S CR2025',{**common,'LiNO3':'0.3 M（通用配方）'},['M0104','M0106','S0069','S0070','S0076','S0077','S0078','S0079']);result(t3,'正极活性物残余量','对照2倍',None,None,'50圈',['M0104'],basis='qualitative',direction='变好');result(t3,'锂金属质量损失','较对照减少约70%',None,None,'50圈',['M0104'],basis='qualitative',direction='变好');result(t3,'锂表面腐蚀',point='100圈',ev=['M0106'],basis='qualitative',direction='变好')
t4=test('Li-S多扫描速率CV','Li‖S CR2025',{**common,'rate':'0.1–0.4 mV s−1扫描；图3c为0.4','LiNO3':'0.3 M（通用配方）'},['M0087','M0119','M0120','M0121','S0022']);result(t4,'氧化还原极化',point='0.4 mV/s CV',ev=['M0119'],basis='qualitative',direction='变好');result(t4,'峰电流响应',point='CV',ev=['M0120'],basis='qualitative',direction='变好')
t5=test('Li2S6对称电池CV','碳纸‖碳纸',{'rate':'50 mV s−1','Li2S6_concentration':'两组相同，具体值未报告'},['M0124','S0084']);result(t5,'氧化还原响应电流',point='50 mV/s',ev=['M0124'],basis='qualitative',direction='变好')
t6=test('PITT放电','Li‖S CR2025',{**common,'LiNO3':'0.3 M（通用配方）'},['M0125','M0126','S0085']);result(t6,'还原起始电位',point='PITT',ev=['M0125'],basis='qualitative',direction='变好');result(t6,'响应电流',point='PITT',ev=['M0126'],basis='qualitative',direction='变好')
t7=test('OCV EIS及DRT','Li‖S CR2025',{**common,'LiNO3':'0.3 M（通用配方）','rate':'100 kHz–0.01 Hz，10 mV扰动，开路电位'},['M0127','M0128','M0129','M0130','S0021','S0086']);
for metric,ev,di in [('SEI阻抗',['M0128'],'变好'),('电荷转移阻抗',['M0128'],'变好'),('浓差极化阻抗',['M0128'],'变好'),('欧姆阻抗',['M0129'],'变坏'),('总阻抗',['M0130'],'变好')]:result(t7,metric,point='OCV/DRT',ev=ev,basis='qualitative',direction=di)
t8=test('变温EIS活化能拟合','Li‖S CR2025',{**common,'temperature':'35–60 °C温度系列，单档温度未逐个报告','LiNO3':'0.3 M（通用配方）','rate':'EIS 100 kHz–0.01 Hz，10 mV'},['M0133','M0134','S0021','S0089','S0090']);result(t8,'SEI离子输运活化能',43.60,46.24,'kJ mol−1','Arrhenius拟合',['M0134']);result(t8,'电荷转移活化能',40.49,44.28,'kJ mol−1','Arrhenius拟合',['M0134'])
t9=test('原位Raman放电','带石英窗Li‖S',{**common,'sulfur_loading':'1.0 mg cm−2','rate':'0.5 C','electrolyte_amount':'100 μL','LiNO3':'0.3 M（通用配方）','ES':'未报告（不能套用普通扣电20 μL/mg）'},['S0030','S0031','S0032','M0144','M0145','M0146']);result(t9,'LiPS出现电位',2.35,2.25,'V','放电',['M0144','M0145']);result(t9,'LiPS转化完全程度',point='放电末期，DMTMSA在2.00 V几乎无LiPS信号',ev=['M0144','M0145','M0146'],basis='qualitative',direction='变好');result(t9,'放电比容量',point='原位Raman对应放电',ev=['M0146'],basis='qualitative',direction='变好')
t10=test('GITT充放电分解极化','Li‖S CR2025',{**common,'rate':'每次充/放电15 min后休息2 h；电流倍率未报告','LiNO3':'0.3 M（通用配方）'},['M0161','M0167','M0168','M0171','M0174','S0092','S0093','S0098']);result(t10,'浓差极化',point='DOD 0–0.3',ev=['M0168'],basis='qualitative',direction='差异小');result(t10,'浓差极化',point='DOD约0.3后',ev=['M0171'],basis='qualitative',direction='变好');result(t10,'活化极化',point='放电，尤其DOD>0.3',ev=['M0174','M0176','M0177'],basis='qualitative',direction='变好');result(t10,'充电活化/浓差极化',point='充电',ev=['M0208'],basis='qualitative',direction='变好')
t11=test('Li2S沉积容量与成核','Li‖碳纸',{'temperature':'25 °C','rate':'0.05 C预放电至2.07 V；恒压正文图注2.06 V，SI方法2.02 V，冲突未决','electrolyte_amount':'负极侧10 μL blank；正极侧20 μL含100 mmol/L Li2S8及1 M LiTFSI','LiNO3':'负极侧blank含0.3 M；正极侧未写'},['S0018','S0019','S0020','M0156','M0158','M0185','M0191'],['CP10','CP0']);result(t11,'Li2S沉积容量',345.3,207.6,'mAh g−1','恒压沉积积分',['M0191'],reason='正文图注2.06 V与SI2.02 V冲突；同一测试作者两组值保留，不强判数值方向');result(t11,'沉积形貌/成核模式',point='恒压沉积',ev=['M0185','M0190'],basis='qualitative',direction='不判',reason='A逐步3D、B瞬时2D/3D混合，形貌原话不自动换成好坏')
t12=test('低温循环','Li‖S CR2025',{**common,'temperature':'−20 °C','rate':'0.05 C','LiNO3':'0.3 M（通用配方）'},['M0214','M0215','M0216','M0231']);result(t12,'循环容量',700,200,'mAh g−1','A运行超过100圈，B取值圈未写',['M0215','M0216'],same=False,reason='两组文字未给齐同圈口径');result(t12,'循环极化',point='−20 °C循环',ev=['M0216'],basis='qualitative',direction='变好')
t13=test('高载量DMTMSA循环','Li‖S CR2025',{**common,'sulfur_loading':'4 mg cm−2','ES':5,'ES_unit':'μL mgS−1','rate':'0.2 C','LiNO3':'0.3 M'},['S0005','S0009','S0010','M0217','M0218','M0232'],['D10']);result(t13,'首圈放电容量',1006.2,None,'mAh g−1','首圈',['M0218'],reason='单组；对照用0.1 C，不能配对');result(t13,'放电容量','>843.5',None,'mAh g−1','150圈',['M0218'],reason='单组');result(t13,'每圈容量衰减率',0.107,None,'%/cycle','150圈平均',['M0218'],reason='单组')
t14=test('高载量对照循环','Li‖S CR2025',{**common,'sulfur_loading':'4 mg cm−2','ES':5,'ES_unit':'μL mgS−1','rate':'0.1 C','LiNO3':'0.3 M（通用配方）'},['M0217','M0219','M0220','M0232'],['control_unknown']);result(t14,'首圈放电容量',775.5,None,'mAh g−1','首圈',['M0219'],reason='单组；DMTMSA用0.2 C，条件不同');result(t14,'放电容量',691.1,None,'mAh g−1','75圈',['M0220'],reason='单组')
for rate,cap in [(0.3,923.95),(0.4,903.9),(0.5,885.74)]:
 t=test(f'DMTMSA倍率 {rate} C','Li‖S CR2025',{**common,'rate':f'{rate} C','sulfur_loading':'未报告（倍率组未明确与4 mg组相同）','LiNO3':'0.3 M'},['M0221','M0222','M0234','M0235'],['D10']);result(t,'倍率容量',cap,None,'mAh g−1',f'{rate} C',['M0221'],reason='单组倍率容量，不跨不同倍率判配方好坏')
t18=test('3 Ah级软包','Li‖S pouch',{'sulfur_loading':'4 mg cm−2','ES':3,'ES_unit':'mL gS−1','rate':'0.05 C','temperature':'未报告','LiNO3':'0.3 M（DMTMSA通用配方）'},['M0223','M0224','S0005'],['D10']);result(t18,'首圈放电容量',1496.5,None,'mAh g−1','首圈',['M0224'],reason='单组');result(t18,'首圈能量密度',406.2,None,'Wh kg−1','首圈，整软包总质量口径',['M0224'],reason='单组')
t19=test('添加剂与锂相容性','Li‖Li',{'rate':'1 mA cm−2 / 1 mAh cm−2；30与60 h有0.1/0.5 mA电流切换（具体顺序未写）'},['S0044','S0045','S0047','S0048'],['D10','amide10']);result(t19,'稳定运行时长','>400','约200','h','对称电池',['S0047'],reason='近似/界限；添加剂之外基液未明确');result(t19,'锂对称循环稳定性',point='1 mA cm−2条件',ev=['S0047'],basis='qualitative',direction='变好')
t20=test('锂铜循环与用量筛选','Li‖Cu',{},['S0044','S0049','S0050']);result(t20,'稳定循环寿命','>400','<100','cycles','CE快速下降前',['S0050']);result(t20,'库仑效率','接近100',None,'%','DMTMSA稳定循环',['S0050'],reason='未提供对照同圈数值，不作百分点差');result(t20,'库仑效率稳定性',point='循环',ev=['S0049','S0050'],basis='qualitative',direction='变好')
t21=test('DMTMSA用量梯度倍率','Li‖S',{'rate':'不同倍率，具体档仅图','LiNO3':'未报告'},['S0101','S0103','S0104','S0105','S0106'],['control_unknown','D10','D20']);result(t21,'梯度倍率性能',point='不同DMTMSA浓度',ev=['S0103','S0104','S0105','S0106'],basis='qualitative',direction='不判',reason='过低/过高均不佳，适中最优；原文未明确倍率图的全部档位与最优百分数')
def mech(summary,prop,cats,ev,ts,side='其他',source='本文结论'):
 d['mechanisms'].append({'id':PID+f'-M{len(d["mechanisms"])+1}','summary':summary,'A':'D10','B':'control_unknown','property':prop,'categories':cats,'source_type':source,'evidence_source_types':{e:source for e in ev},'evidence_ids':ev,'test_ids':[x['id'] for x in ts],'side':side})
mech('降低长链LiPS溶解抑穿梭，同时增溶Li2S4发挥内源氧化还原介导作用，加快还原/歧化并防长链积累','链长依赖的LiPS溶剂化与溶解度',['多硫化物穿梭','正极反应'],['M0095','M0096','M0097','M0098'],[t1,t2,t4,t5,t6])
mech('穿梭抑制减少活性物损失及LiPS腐蚀锂负极，改善容量保持与稳定性','长链LiPS溶解度下降',['多硫化物穿梭','负极锂'],['M0102','M0104','M0105','M0106','M0115'],[t1,t3])
mech('DMTMSA/TFSI优先分解生成LiF/Li3N/Li2O富集且稳定的SEI；对照有机SEI反复破裂重长，不能防电解液分解与锂腐蚀','界面反应及Li+溶剂化',['负极锂','电解液消耗'],['M0107','M0108','M0109','M0110','M0111','M0112','M0113','M0114','S0074','S0075'],[t3,t19,t20])
mech('坚固SEI使负极侧LiPS保持较高氧化态，仅发生较轻副反应','界面保护',['负极锂'],['M0116'],[t3])
mech('电导下降提高欧姆阻抗但并未显著阻碍整体输运；弱配位提高Li+迁移数、便利脱溶剂化且形成无机SEI，降低内阻和界面阻抗','Li+溶剂化与离子输运',['负极锂'],['M0129','M0130','M0131','M0132','M0134','M0135','M0136','M0137','M0138'],[t7,t8])
mech('Li2S4增溶提高液相介导，Li2S解离溶解暴露更多正极位点，促进离子输运和硫转化','短链LiPS/Li2S溶解度',['正极反应'],['M0141','M0142'],[t4,t9,t11])
mech('DMTMSA拉长Li2S4的S-S与Li-S键便于断键，促进Li2S4转化','Li2S4溶剂相互作用',['正极反应'],['M0147'],[t9])
mech('DMTMSA使Li2S6转Li2S4和Li2S形成更有利；DOL/DME中Li2S2能量过低阻碍转Li2S，降低硫利用及充电氧化速度','反应热力学',['正极反应'],['M0148','M0149','M0150','M0151'],[t9,t11])
mech('早期DOD 0–0.3的浓差极化受Li2S8扩散限制，两组差异很小；后段DMTMSA提高Li2S4溶解分散并促进3D生长而降低极化','链长依赖溶解与扩散',['正极反应'],['M0168','M0169','M0170','M0171'],[t10])
mech('高DOD时Li2S4耗尽降低介导活性，Li2S覆盖正极阻碍剩余还原，极化急增甚至提前终止放电','Li2S4供给和Li2S覆盖',['正极反应'],['M0172','M0180','M0181','M0182','M0183','M0196'],[t10],source='本文推测')
mech('DMTMSA加快硫转化，Li2S持续逐步3D生长；对照活性位被覆盖后从3D转2D沉积，活化极化增加','Li2S成核与形貌',['正极反应'],['M0178','M0179','M0185','M0186','M0187','M0188','M0189','M0190','M0191','M0192','M0193','M0194','M0195'],[t10,t11])
mech('Li2S在DMTMSA中较易溶解，生成物及时溶解并优先在既有Li2S表面再沉积，形成还原-溶解-沉积的3D生长','Li2S溶解度',['正极反应'],['M0198','M0199','M0200','M0201','M0202','M0203'],[t11])
mech('DMTMSA与Li2S强相互作用及Li-S键伸长促进充电氧化，减少正极残余Li2S与容量损失','Li2S相互作用',['正极反应'],['M0204','M0207','M0208','M0209','M0210'],[t4,t10])
mech('Li2S成核须生成新固相、解离是既有固相的界面氧化，两过程能垒不同解释解离过电位较低','相变路径差异',['正极反应'],['M0205','M0206'],[t11])
mech('DMTMSA含量过高使Li2S8溶解过低、趋向准固态转化，过度抑制液相介导而损害性能；需要适中含量','长链LiPS溶解度',['正极反应'],['S0103','S0104','S0105','S0106'],[t21],side='弱侧')
mech('DMTMSA中CF3吸电子削弱氧对Li+配位，有利于与锂金属的相容性','Li+溶剂化',['负极锂'],['M0042'],[t19,t20])
d['design_claims']=[{'summary':'以高极化率溶剂实现依链长/电荷密度自适应的溶剂化：长链弱溶、短链强溶，兼顾穿梭抑制与动力学；含量过高有反例，适中最优。','evidence_ids':['M0227','M0228','M0229','M0239','S0103','S0104','S0105','S0106']}]
d['figure_requests']=[{'test_id':t12['id'],'figure':'5a','part':'main','metric':'低温同圈容量','A':'D10','B':'control_unknown','target_point':'首圈及100圈（先核B口径）','anchor_quote_ids':['M0215','M0216'],'reason':'文字双方未给齐同圈；盐组成需先确认'},
 {'test_id':t21['id'],'figure':'S35（SI讨论误写S31，需核图）','part':'si','metric':'用量梯度倍率容量与档位','A':'全梯度','B':None,'target_point':'各DMTMSA含量相同倍率点','anchor_quote_ids':['M0221'],'reason':'需确认M0221同一倍率测试；不能直接跨图用锚点或猜全梯度'},
 {'test_id':t18['id'],'figure':'5g','part':'main','metric':'软包循环保持','A':'D10','B':None,'target_point':'首圈及末圈','anchor_quote_ids':['M0224'],'reason':'单组曲线，可读补缺侧但不自动构成A/B方向'}]
d['gaps']=['without DMTMSA对照未明确是SI的blank单盐还是FSI双盐，不把该盐变化强行当仅DMTMSA变化。',
 '高载量DMTMSA为0.2 C、对照0.1 C，按图5b图注也确认为不同倍率；拆测试，不配对首圈和末圈。',
 'Li||CP恒压正文图4d/f为2.06 V，SI为2.02 V，保留冲突，不擅自选择。',
 '用量图未读，尚未确认全部浓度档；NMR明确0/10/20%，不能等同倍率图全部档位。',
 '普通扣电硫载量1/2/4 mg cm−2分别E/S约20/15/5 μL mg−1；除明示组外不填默认载量。',
 'SI原位Raman为1 mg cm−2和100 μL，不能误套普通扣电E/S20。软包锂厚未报告，不套450 μm扣电锂。',
 '图读与独立交叉复核未完成，本文首轮文本结果尚非人工金标准。']
if __name__=='__main__':
 p=OUT/'independent_predictions'/f'{PID}.json'
 if p.exists():raise SystemExit('Frozen prediction already exists; do not overwrite')
 save(p,d);print(json.dumps({'paper_id':PID,'tests':len(d['tests']),'results':sum(len(t['results']) for t in d['tests']),'mechanisms':len(d['mechanisms'])},ensure_ascii=False))
