"""Source-only root extraction: S32 main through conclusion and complete SI."""
from step8a_prepare_debug53 import OUT,save
import json
P='S32';D={'paper_id':P,'doi':'10.1002/adma.202503365','formulations':[],'control_id':'E-baseline','control_type':'常规DME/DOL+LiTFSI+2 wt.% LiNO3','gradients':[],'properties':[],'tests':[],'mechanisms':[],'design_claims':[],'figure_requests':[],'gaps':[],'source_review':{'main':True,'si':True,'notes':'root逐段读取正文至M0199、全部SI；源文独立提取，无旧参考输入。SI Word页号0仅为索引占位。'}}
def c(n,r,a,u):return dict(name=n,role=r,amount=a,unit=u)
F=['0.6M-DMFN','0.8M-DMFN','1.0M-DMFN','1.2M-DMFN'];ALL=['E-baseline']+F
D['formulations'].append({'id':'E-baseline','name':'E-baseline','components':[c('DME','溶剂化溶剂',1,'体积份'),c('DOL','弱溶剂化溶剂',1,'体积份'),c('LiTFSI','盐',1,'m（正文原单位）'),c('LiNO3','添加剂',2,'wt.%')],'raw_formula':'1 m LiTFSI in DME/DOL 1:1 v/v + 2 wt.% LiNO3','evidence_ids':['M0049']})
for concentration,f in zip([0.6,0.8,1.0,1.2],F):D['formulations'].append({'id':f,'name':f,'components':[c('DME','溶剂化溶剂',2,'体积份'),c('2-MeTHF','弱溶剂化溶剂',1,'体积份'),c('TFEO','非溶剂化稀释剂',1,'体积份'),c('LiTFSI','盐',concentration,'m（正文原单位；代号含M）'),c('LiNO3','添加剂',2,'wt.%')],'raw_formula':f'{concentration} m LiTFSI / DME:2-MeTHF:TFEO=2:1:1 v/v + 2 wt.% LiNO3','evidence_ids':['M0048','M0053','S0095']})
D['gradients']=[{'name':'DMFN主盐浓度','order':F,'values':[0.6,0.8,1.0,1.2],'solvation_axis':'CIP/AGG随盐增加；LiPS颜色似随盐增而溶解降低，但CHNS显示0.8档最低且不宜据此算Li2S6浓度；不能把这两者强合并为单调溶剂化','evidence_ids':['M0065','M0081','M0085','S0104','S0106']},{'name':'纯溶剂种类','order':['DME','DOL','2-MeTHF','TFEO'],'values':None,'solvation_axis':'Li2S6溶解/溶剂化由强到弱；这是性质实验，不是完整电池配方梯度','evidence_ids':['M0038','M0039','S0076','S0077']}]
def prop(name,values,direction,method,system,ev):D['properties'].append(dict(name=name,values=values,direction=direction,method=method,system=system,evidence_ids=ev))
prop('Li+溶剂化',{},'DME主配位；DMFN的CIP/AGG随盐增加，TFEO不配位；2-MeTHF协调明显','Raman、CMD RDF/CN','五种完整电解液',['M0063','M0064','M0065','M0066','M0069','M0070','M0071','M0072','M0073','M0077'])
prop('LiPS溶剂化/团簇',{},'Li2S6浓度低时各组接近；高时DMFN团簇更密、Li-S第一壳层增强，baseline仍能继续溶解','CMD','60/120/180个Li2S6分子模拟体系',['S0118','S0120','S0121','S0122','S0127','S0128','S0129','S0130','S0131','S0134','S0135','S0136'])
prop('LiPS溶解度',{'DME/DOL溶剂':'0.83 M（SI 1:1；正文写2:1和m）','DME/2-MeTHF/TFEO 2:1:1':'0.38 M（SI）'},'DMFN溶剂体系更低；实际含盐电解液应低于0.38 M但未定量','CHNS元素分析+溶剂样品换算；UV-vis/颜色','溶剂混合物的值，不是实际完整电解液浓度',['M0085','M0086','S0106','S0107','S0111','S0112','S0113','S0114','S0115','S0206'])
prop('总硫含量',{'E-baseline':'15.472 ±0.320','0.6M-DMFN':'12.499 ±0.712','0.8M-DMFN':'10.012 (+0.652,1.882)','1.0M-DMFN':'12.281 ±0.554','1.2M-DMFN':'13.486 ±0.029'},'单位wt.%；0.8最低，不能把总硫直接当LiPS，因为LiTFSI也含硫','CHNS','饱和Li2S6电解液',['S0103','S0104','S0105','S0106','S0205'])
prop('离子电导率',{'DMFN':'约6–7 mS cm−1','1.0M-DMFN':'6.77 mS cm−1'},'DMFN约baseline一半；DMFN中1.0最高','电导率温度系列','25 °C数值；另测−20至60 °C每5 °C',['M0051','M0052','M0053','S0079'])
prop('黏度',{},'0.6M-DMFN与baseline近重合，其余随盐浓度升高而增加','黏度温度系列','0–60 °C',['M0058','S0080'])
prop('Li+迁移数',{},'未报告','未报告','未报告',[])
prop('S8溶解/电极浸泡',{},'baseline三天显黄，1.0M-DMFN七个月无明显变化','颜色/浸泡','1 mL电解液+S电极',['M0087','S0097','S0098','S0117'])
base={'sulfur_loading':'4 mg cm−2（SI）；正文另称4 mAh cm−2容量载量','ES':8,'ES_unit':'μL mgS−1','Li_thickness':'250 μm','rate':'未报告','formation':'2圈C/20，1.8–2.8 V','temperature':'25 °C','LiNO3':'2 wt.%','one_C':'未报告（扣电）','voltage_window':'1.7–2.8 V'}
def test(name,cell,conditions,ev,forms=None):
 t={'id':P+f'-T{len(D["tests"])+1}','name':name,'cell':cell,'conditions':{k:'未报告' for k in base},'formulations':forms or ALL,'evidence_ids':ev,'results':[]};t['conditions'].update(conditions);D['tests'].append(t);return t
def r(t,metric,A,B,va=None,vb=None,unit=None,point='未报告',ev=(),basis='numeric',direction='不判',same=True,reason='数值方向待程序复算'):
 t['results'].append({'id':t['id']+f'-R{len(t["results"])+1}','metric':metric,'A':A,'B':B,'value_A':va,'value_B':vb,'unit':unit,'point':point,'basis':basis,'direction_text':direction,'same_conditions':same,'evidence_ids':list(ev),'reason':reason})
t1=test('改进Aurbach平均锂效率','Li‖Cu CR2032',{'Li_thickness':'250 μm（方法通用锂片）','temperature':'25 °C','LiNO3':'2 wt.%','rate':'未报告电流密度；QT 5 mAh cm−2、QC 1 mAh cm−2、n=10','electrolyte_amount':'75 μL'},['M0059','M0060','M0061','S0020','S0028','S0029','S0030','S0033'])
r(t1,'平均库仑效率','1.0M-DMFN','E-baseline',99.66,99.19,'%','Aurbach平均',['M0060','M0061'])
for f in F:r(t1,'平均CE作者定性',f,'E-baseline',point='各DMFN优于baseline',ev=['M0062'],basis='qualitative',direction='变好',reason='作者定性另存，数值CE只记百分点差')
t2=test('充电倍率系列','Li‖S CR2032',{**base,'rate':'充电C/10、C/5至1C；固定放电倍率未报告'},['M0089','M0092','M0093','M0094','M0095','M0112','M0113','S0020','S0030'])
for f in F:r(t2,'充电倍率容量',f,'E-baseline',point='充电C/5至1C档',ev=['M0094','M0095'],basis='qualitative',direction='差异小',reason='各配方在这些充电倍率下容量重合；早期C/10不并入')
t3=test('放电倍率系列','Li‖S CR2032',{**base,'rate':'放电C/10、C/5、C/3、C/2、1C（文本明确档）；固定充电倍率未报告'},['M0089','M0096','M0097','M0098','M0099','M0101','M0112','M0113','S0149'])
r(t3,'放电倍率容量','0.6M-DMFN','E-baseline',point='C/2',ev=['M0097'],basis='qualitative',direction='变好',reason='除0.6组外其余C/2骤降，0.6至1C才骤降')
for f in F:r(t3,'放电倍率能力',f,'E-baseline',point='≤C/3',ev=['M0101'],basis='qualitative',direction='差异小',reason='作者定性相似')
t4=test('C/5长循环及化成','Li‖S CR2032',{**base,'rate':'C/5'},['M0089','M0090','M0102','M0103','M0106','M0112','M0113','S0020','S0030','S0031','S0151'])
for f in F:
 r(t4,'化成首圈高平台容量',f,'E-baseline',point='第一化成圈C/20，不是化成后C/5首圈',ev=['M0090','M0091','M0112'],basis='qualitative',direction='变坏',reason='只描述化成平台，不能当后续首圈容量')
 r(t4,'循环稳定性',f,'E-baseline',point='C/5循环',ev=['M0103','M0105','M0106'],basis='qualitative',direction='变好',reason='作者定性')
 r(t4,'循环极化',f,'E-baseline',point='250圈内',ev=['M0105','M0106'],basis='qualitative',direction='变好',reason='作者定性')
r(t4,'容量保持率','1.0M-DMFN',None,81.3,None,'%','300圈',['M0103'],same=None,reason='单组；首圈后同批配对另一侧尚缺')
r(t4,'放电容量','1.0M-DMFN',None,604,None,'mAh g−1','300圈',['M0103'],same=None,reason='单组')
r(t4,'循环寿命','1.0M-DMFN','E-baseline','约2倍',None,None,'作者结论',['M0194'],basis='qualitative',direction='变好',reason='未给对照相同失效阈值，不反造150圈')
t5=test('C/10长循环','Li‖S CR2032',{**base,'rate':'C/10'},['M0117','M0118','S0152','S0153','S0154','S0155'])
for f in F:r(t5,'循环稳定性',f,'E-baseline',point='C/10，详图S16',ev=['M0117','M0118'],basis='qualitative',direction='变好',reason='仅作者总体说明此倍率结果；数值只在图')
t6=test('28周充满态日历/自放电','Li‖S CR2032',{**base,'rate':'C/10充至2.8 V；休息168 h后C/10放至1.7 V，重复28周','formation':'2圈C/20；正文另写先1圈C/10作为参考'},['M0124','M0125','M0126','M0127','M0128','M0129','M0113','S0032'])
for f in F:
 r(t6,'容量损失',f,'E-baseline','≈8',34.2,'%','第1周后',['M0125','M0128'],reason='近似值保留，不擅自按精确数计算')
 r(t6,'自放电抑制/电压稳定性',f,'E-baseline',point='28个一周周期',ev=['M0127','M0129'],basis='qualitative',direction='变好',reason='作者定性')
r(t6,'28周容量损失','DMFN（正文未指具体档）','E-baseline',5.9,23.5,'%','28周',['M0196'],same=None,reason='DMFN具体档位未明确，不配给1.0档')
t7=test('1 Ah软包C/10循环及化成','Li‖S pouch',{'sulfur_loading':'4 mg cm−2','ES':'≈5.2','ES_unit':'μL mgS−1','Li_thickness':'100 μm','rate':'C/10','formation':'2圈C/20，1.8–2.6 V','temperature':'25 °C','LiNO3':'2 wt.%','one_C':'1000 mA cm−2（SI原文单位疑误，未自行改）','voltage_window':'1.7–2.6 V','pressure':'25 psi固定间距夹具'},['S0026','S0033','S0034','S0035','S0156','S0157','S0158','S0159','S0160','S0161'],['0.8M-DMFN','E-baseline'])
r(t7,'化成比能量','0.8M-DMFN','E-baseline',290,310,'Wh kg−1','C/20；不含软包封装重量',['S0161'])
r(t7,'循环稳定性','0.8M-DMFN','E-baseline',point='C/10，baseline40圈后过电位大',ev=['M0119'],basis='qualitative',direction='变好',reason='作者定性')
r(t7,'循环过电位','0.8M-DMFN','E-baseline',point='40圈后',ev=['M0119'],basis='qualitative',direction='变好',reason='作者定性')
t8=test('100圈后HUG库存','Li‖S CR2032',{**base,'rate':'C/5'},['M0134','M0136','M0137','M0147','S0020','S0030'],['1.0M-DMFN','E-baseline'])
r(t8,'不可逆活性硫损失','1.0M-DMFN','E-baseline',23.1,45.3,'%','100圈后',['M0136'])
r(t8,'剩余可逆硫中LiPS比例','1.0M-DMFN','E-baseline',36.7,92.6,'%','100圈后',['M0137'],reason='物种分布本身不自动判好坏')
r(t8,'剩余可逆硫中S8比例','1.0M-DMFN','E-baseline',63.3,7.4,'%','100圈后',['M0137'],reason='物种分布本身不自动判好坏')
r(t8,'金属锂保持','1.0M-DMFN','E-baseline',point='100圈后',ev=['M0134'],basis='qualitative',direction='变好',reason='作者明确不可逆Li消耗更少')
# Postmortem results belong to the same C/5 protocol; retain values and source without creating a new cycling condition.
r(t4,'锂反应层厚度','1.0M-DMFN','E-baseline','175–190','209–350','μm','300圈后',['M0152','M0153'],reason='区间；厚度不直接当循环优劣')
r(t4,'锂腐蚀/沉积形貌','1.0M-DMFN','E-baseline',point='300圈后',ev=['M0141','M0142','M0150'],basis='qualitative',direction='变好',reason='作者定性')
r(t4,'正极结构保持','1.0M-DMFN','E-baseline',point='300圈后',ev=['M0161','M0162','M0164','M0171'],basis='qualitative',direction='变好',reason='作者定性')
def m(summary,pr,cat,ev,tests,side='其他',st='本文结论'):
 D['mechanisms'].append({'id':P+f'-M{len(D["mechanisms"])+1}','summary':summary,'A':'DMFN全梯度','B':'E-baseline','property':pr,'categories':cat,'source_type':st,'evidence_source_types':{e:st for e in ev},'evidence_ids':ev,'test_ids':[t['id'] for t in tests],'side':side})
m('2-MeTHF/TFEO共溶剂改善与锂的稳定性，提高Li沉积剥离效率','共溶剂相容性',['负极锂'],['M0062','M0047'],[t1],st='本文结论（与他文一致）')
m('DMFN减少长链LiPS生成/溶解，降低化成高平台及总体初始容量','LiPS溶解度',['正极反应'],['M0090','M0091'],[t4],side='弱侧')
m('长链向短链LiPS转化是高倍率放电限速步，过电位使电池提前碰到截止电压','LiPS转化动力学',['正极反应'],['M0097','M0099'],[t3])
m('DMFN虽低电导高黏度使初期容量较低，但高Li效率、低LiPS溶解减少负极副反应、硫损失及串扰；保有约6–7 mS/cm电导使低于C/3倍率能力接近baseline','LiPS溶解与输运的权衡',['负极锂','多硫化物穿梭','正极反应'],['M0100','M0101'],[t1,t3,t4])
m('baseline低黏度与较好润湿使初始容量高，而DMFN改善循环稳定与CE','黏度/润湿',['正极反应'],['M0103'],[t4])
m('软包baseline额外充电容量来自副反应，导致低CE、过电位增长及失效','副反应',[],['M0119'],[t7])
m('高LiPS溶解及电极反应使S/LiPS迁移至锂负极，损失活性物、消耗电解液并使负极绝缘；DMFN低溶解和稳固双界面抑穿梭/自放电','LiPS溶解度与界面',['多硫化物穿梭','负极锂','电解液消耗'],['M0121','M0122','M0131','M0132'],[t6],side='强侧')
m('baseline中硫主要转成LiPS并不断溶解，造成持续副反应、硫损失、低CE与衰退；DMFN保留更多S8与活性硫','硫物种分布',['正极反应'],['M0136','M0137','M0138','M0139'],[t8])
m('抑制LiPS穿梭改善沉积锂形貌并减少腐蚀，解释DMFN较高LiCE与长循环稳定','LiPS穿梭',['多硫化物穿梭','负极锂'],['M0154','M0159'],[t1,t4])
m('TFEO与TFSI分解形成均匀富F、富阴离子/无机产物的SEI，保护锂负极免于循环腐蚀','SEI组成',['负极锂'],['M0155','M0156','M0158'],[t4],st='本文结论（与他文一致）')
m('DMFN促进无机富集的CEI，稳定正极结构并减少过度LiPS溶解/迁移；baseline有机CEI不稳定且硫颗粒剥离','CEI组成与LiPS溶解',['正极反应','多硫化物穿梭'],['M0164','M0171','M0172','M0173','M0174'],[t4])
m('DMFN保留α-S8的机制仍需原位研究，作者仅推测其可能反映硫可逆性/长期结构保持增强','硫晶型',['正极反应'],['M0182','M0183','M0190'],[t4,t6],st='本文推测')
D['design_claims']=[{'summary':'高/弱/不配位三种溶剂构成适度溶剂化体系；0.8M-DMFN容量较高、1.0M-DMFN的C/5稳定性最佳，容量与稳定性最优并非同档。','evidence_ids':['M0029','M0030','M0118','M0191','M0192']}]
def fig(t,f,metric,A,B,point,anchors,reason,part='main'):D['figure_requests'].append({'test_id':t['id'],'figure':f,'part':part,'metric':metric,'A':A,'B':B,'target_point':point,'anchor_quote_ids':anchors,'reason':reason})
fig(t4,'3d','同圈容量及梯度','DMFN全梯度','E-baseline','化成后C/5首圈及300圈',['M0103'],'1.0档300圈604有锚点；其他曲线需同测试锚点，不能全图默认通过')
fig(t3,'3c','倍率梯度容量','DMFN全梯度','E-baseline','C/3、C/2各档',[],'仅图，无明确数值锚点候选')
fig(t5,'S16','C/10循环容量','DMFN全梯度','E-baseline','首圈及末圈',[],'仅图，无明确数值锚点候选','si')
fig(t7,'S18b','软包循环容量侧','0.8M-DMFN','E-baseline','化成后C/10首圈与40圈',[],'C/20比能量不是C/10容量锚点，不能跨指标强核','si')
D['gaps']=['正文使用小写m、配方代号M，未给明确定义；保留原单位，不做摩尔数尺子换算。','正文溶剂DME-DOL比写2:1而SI与表写1:1，溶解度数值来自不含主盐的溶剂体系，不能当完整电解液值。','CHNS不能定量LiPS；颜色单调与CHNS最低0.8档结论不同，均保留。','软包SI给1C=1000 mA cm−2疑似单位错误，原样记录不默改。','化成C/20容量/能量与化成后C/5或C/10首圈不同，不混用。','SI所有图尚未几何读图；仅可按现有文字判方向。']
if __name__=='__main__':
 p=OUT/'independent_predictions'/f'{P}.json'
 if p.exists():raise SystemExit('Frozen prediction exists')
 save(p,D);print(json.dumps({'paper':P,'tests':len(D['tests']),'results':sum(len(t['results']) for t in D['tests']),'mechanisms':len(D['mechanisms'])},ensure_ascii=False))
