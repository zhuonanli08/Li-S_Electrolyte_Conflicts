"""S28 source-only extraction; scientific main and SI read by root."""
from step8a_prepare_debug53 import OUT, save
P='S28'
D=dict(paper_id=P,doi='10.1021/acsenergylett.6c00790',formulations=[],control_id='DD',control_type='DME/DOL常规电解液及十种双溶剂筛选',gradients=[],properties=[],tests=[],mechanisms=[],design_claims=[],figure_requests=[],gaps=[],source_review={'main':True,'si':True,'notes':'独立读正文M0001–M0199和SI科学内容S0001–S0332，后段为参考文献。未读旧提取结果。75种候选溶剂不是75种实际电池配方。'})
def c(n,r,a,u):return dict(name=n,role=r,amount=a,unit=u)
pairs=[('DMSO','CSA'),('DMSO','DME'),('DMSO','MeTHF'),('DMSO','TTE'),('CSA','DME'),('CSA','MeTHF'),('CSA','TTE'),('DME','MeTHF'),('DME','TTE'),('MeTHF','TTE')]
forms=['/'.join(p) for p in pairs]+['DD']; A='CSA/MeTHF'
for s1,s2 in pairs:
 nitrate=s2!='TTE'
 D['formulations'].append(dict(id=f'{s1}/{s2}',name=f'{s1}/{s2}',components=[c('LiTFSI','盐',1,'摩尔份'),c(s1,'主溶剂',4,'摩尔份'),c(s2,'共溶剂',6,'摩尔份')]+([c('LiNO3','添加剂',.2,'摩尔份')] if nitrate else []),raw_formula=f'LiTFSI:{s1}:{s2}'+(':LiNO3=1:4:6:0.2' if nitrate else '=1:4:6，无LiNO3'),evidence_ids=['S0034','S0035','S0320']))
D['formulations'].append(dict(id='DD',name='DD',components=[c('DME','溶剂',1,'体积份'),c('DOL','溶剂',1,'体积份'),c('LiTFSI','盐',1,'M'),c('LiNO3','添加剂',.2,'M')],raw_formula='1 M LiTFSI + 0.2 M LiNO3 / DME:DOL=1:1 v/v',evidence_ids=['S0036','S0320']))
D['formulations'].append(dict(id='TFBA/DOL',name='TFBA/DOL',components=[c('LiTFSI','盐',1,'摩尔份'),c('TFBA','主溶剂',4,'摩尔份'),c('DOL','共溶剂',6,'摩尔份'),c('LiNO3','添加剂',.2,'摩尔份')],raw_formula='LiTFSI:TFBA:DOL:LiNO3=1:4:6:0.2',evidence_ids=['S0038']))
for x in [0,2,4,6]:
 D['formulations'].append(dict(id=f'CSA-x{x}',name=f'CSA优化x={x}',components=[c('LiTFSI','盐',1,'摩尔份'),c('CSA','主溶剂',x,'摩尔份'),c('MeTHF','共溶剂',6,'摩尔份')],raw_formula=f'LiTFSI:CSA:MeTHF=1:{x}:6；该优化段LiNO3未明确',evidence_ids=['S0145','S0146']))
for fid,solvents,ev in [('EC/DEC',[('EC',1),('DEC',1)],'S0127'),('pyridine',[('pyridine',None)],'S0131')]:
 D['formulations'].append(dict(id=fid,name=fid,components=[c('LiTFSI','盐',1,'M')]+[c(n,'溶剂',v,'体积份' if v else '纯溶剂') for n,v in solvents],raw_formula=f'1 M LiTFSI in {fid}'+(' 1:1 v/v' if fid=='EC/DEC' else '')+'；LiNO3未报告',evidence_ids=[ev]))
D['gradients']=[dict(name='CSA用量',order=[f'CSA-x{x}' for x in [0,2,4,6]],values=[0,2,4,6],solvation_axis='LiTFSI:CSA:MeTHF=1:x:6；x=0用于性质，x=2/4/6用于电池；x=4平衡、x=6出现游离CSA',evidence_ids=['S0145','S0146','S0148','S0157']),dict(name='溶剂化能力组合筛选',order=forms,values=None,solvation_axis='DMSO强、CSA中强、DME中、MeTHF弱、TTE不配位；十种两两组合不是单调的一维梯度',evidence_ids=['S0318','S0320'])]
def prop(name,values,direction,method,system,ev):D['properties'].append(dict(name=name,values=values,direction=direction,method=method,system=system,evidence_ids=ev))
prop('Li+溶剂化',{},'DMSO/CSA、CSA/DME、DME/MeTHF和DD均有竞争配位；CSA/MeTHF中CSA内壳层而MeTHF外层；TFBA/DOL中TFBA内层、DOL主要未配位','Raman/MD','各配方；不把Li+配位等同LiPS溶解',['M0060','M0061','M0062','M0063','M0064','S0286'])
prop('LiPS溶剂化',{},'CSA富内壳层，MeTHF富外层；DD两溶剂均参与。CSA/MeTHF有更大LiPS团簇','17O/7Li NMR、DOSY、MD、DLS','NMR含0.1 M Li2S6；MD 0.2 M Li2S6+1 M LiTFSI简化体系',['M0095','M0096','M0097','M0100','M0101','M0104','M0111','M0112','M0120','M0122'])
prop('LiPS溶解度',{'CSA':'约18 mol L−1','DME':'9 mol L−1','MeTHF':'0.6 mol L−1','DOL':'1 mol L−1'},'按硫原子浓度[S]报告，不能当Li2S6的摩尔浓度','饱和Li2S6溶液','纯溶剂；CSA:MeTHF 4:6的0.01 M Li2Sx均匀，而DD出现沉淀',['M0089','M0090','M0093','M0094'])
prop('Li+扩散系数',{'CSA/MeTHF':3.1e-10,'DD':6.3e-10},'m² s−1；CSA/MeTHF较低','DOSY','0.1 M Li2S6溶液',['M0120'])
prop('LiPS团簇半径',{'CSA/MeTHF':7.5,'DD':4.2},'nm；CSA/MeTHF更大','DLS','LiPS溶液',['M0122'])
prop('Li2S6扩散系数',{'CSA/MeTHF':2.3e-11,'DD':8.9e-11},'m² s−1；计算估计值','Stokes–Einstein关系','LiPS溶液',['M0124'])
for name,vals,unit in [('密度',[1.23,1.09,1.09,1.50,1.11,1.12,1.47,1.01,1.39,1.38,1.11],'g cm−3'),('黏度',[7.64,1.76,2.23,5.33,2.23,3.15,5.44,1.08,2.82,2.49,1.25],'mPa s'),('离子电导率',[2.57,9.40,9.44,2.56,6.17,3.60,1.42,6.39,2.37,.49,7.93],'mS cm−1')]:
 prop(name,dict(zip(forms,vals)),unit+'；各组合非单调','SI Table S11','25 °C，所有配方均无LiNO3；不直接套有硝酸锂电池配方',['S0321','S0322'])
prop('CSA用量与Li+配位',{'x2':'CSA 706.1 cm−1；MeTHF仍参与配位','x4':'CSA大致全配位，MeTHF主要游离','x6':'游离CSA 702.8 cm−1出现'},'加CSA逐步置换MeTHF配位，过量后游离','Raman','LiTFSI:CSA:MeTHF=1:x:6',['S0148'])
prop('Li+迁移数',{},'未报告','未报告','未报告',[])
base=dict(sulfur_loading='未报告',ES='未报告',ES_unit='μL mgS−1',Li_thickness='未明确（材料购有500和75 μm）',rate='未报告',formation='未报告',temperature='未报告',LiNO3='按配方；TTE组不含，其余0.2摩尔份/1摩尔LiTFSI，DD为0.2 M',one_C='未报告',voltage_window='未报告')
def test(name,cell,conds,ev,ff=None):
 t=dict(id=P+f'-T{len(D["tests"])+1}',name=name,cell=cell,conditions={**base,**conds},formulations=ff or [A,'DD'],evidence_ids=ev,results=[]);D['tests'].append(t);return t
def r(t,metric,a,b,va=None,vb=None,unit=None,point='未报告',ev=(),basis='numeric',direction='不判',same=True,reason='数值方向待程序复算'):
 t['results'].append(dict(id=t['id']+f'-R{len(t["results"])+1}',metric=metric,A=a,B=b,value_A=va,value_B=vb,unit=unit,point=point,basis=basis,direction_text=direction,same_conditions=same,evidence_ids=list(ev),reason=reason))
# The S12 row order differs from S10: use explicit formulation keys.
screen={'DMSO/CSA':[1575,206,52,11,588,86.2,505],'DMSO/DME':[70,540,18,12,623,39.2,513],'DMSO/MeTHF':[78,508,12,29,585,89.5,510],'DMSO/TTE':[81,480,8,32,333,87.2,445],'CSA/DME':[72,572,54,30,626,91.5,731],'CSA/TTE':[1561,434,1,142,695,98.8,666],'DME/MeTHF':[12,1700,17,25,531,99.1,737],'CSA/MeTHF':[32,1200,5,15,699,99.9,913],'DME/TTE':[28,1443,1,148,494,99.3,478],'MeTHF/TTE':[39,1217,1,None,0,98.6,460],'DD':[10,1200,42,42,570,98.9,754]}
li_tests=[];dep_tests=[];cyc_tests=[]
for nitrate in [True,False]:
 ff=[f for f in forms if ('TTE' not in f)==nitrate]
 no3='0.2摩尔份/1摩尔LiTFSI；DD为0.2 M/1 M LiTFSI（绝对浓度未统一）' if nitrate else '无'
 suffix='（含LiNO3）' if nitrate else '（无LiNO3）'
 t=test('双溶剂筛选：锂对称寿命/极化'+suffix,'Li‖Li',dict(rate='0.5 mA cm−2 / 0.5 mAh cm−2',electrolyte_amount='40 μL',LiNO3=no3),['S0080','S0081','M0068','S0324','S0326'],ff);li_tests.append(t)
 for f in ff:
  b='DD' if nitrate and f!='DD' else None
  for metric,col,unit,point in [('极化电压',0,'mV','400 h附近；短寿命组统计口径见表S12'),('循环寿命',1,'h','Table S12')]:r(t,metric,f,b,screen[f][col],screen[b][col] if b else None,unit,point,['S0326'],same=True if b else None,reason='同硝酸锂/盐摩尔比，完整配方比较' if b else '单组；不跨LiNO3条件配对')
 t=test('双溶剂筛选：恒流Li2S成核/沉积'+suffix,'Li‖Li2S6',dict(sulfur_loading='1.4 mg cm−2',rate='0.2 C',electrolyte_amount='20 μL（低载硫通用方法）',LiNO3=no3),['M0078','S0059','S0060','S0072','S0325','S0326'],ff);dep_tests.append(t)
 for f in ff:
  b='DD' if nitrate and f!='DD' else None
  for metric,col,unit in [('Li2S成核过电位',3,'mV'),('Li2S沉积容量',4,'mAh g−1')]:r(t,metric,f,b,screen[f][col],screen[b][col] if b else None,unit,'恒流0.2 C；不是2.05 V恒电位',['S0326'],same=True if b else None,reason='表S12；无成核数据保留null，不当0')
 t=test('双溶剂筛选：100圈平均性能'+suffix,'Li‖Li2S6',dict(sulfur_loading='1.4 mg cm−2',rate='0.2 C',electrolyte_amount='20 μL（通用方法）',LiNO3=no3),['M0081','S0059','S0060','S0247','S0326'],ff);cyc_tests.append(t)
 for f in ff:
  b='DD' if nitrate and f!='DD' else None
  for metric,col,unit in [('平均库仑效率',5,'%'),('平均容量',6,'mAh g−1')]:r(t,metric,f,b,screen[f][col],screen[b][col] if b else None,unit,'100圈平均，不是第100圈',['S0326','M0081'],same=True if b else None,reason='CE只计百分点差；均为平均值')
tsh=test('各组合LiPS穿梭电流筛选','Li‖Li2S6',dict(sulfur_loading='1.4 mg cm−2',LiNO3='所有组均不含LiNO3',rate='充至2.9 V；2.90、2.60、2.45、2.43、2.40、2.39、2.38、2.37、2.36、2.35、2.34、2.25、2.20 V各恒压1 h'),['S0085','S0086','S0087','S0088','S0326'],forms)
for f in forms:r(tsh,'平均穿梭电流密度',f,'DD' if f!='DD' else None,screen[f][2],42 if f!='DD' else None,'μA cm−2','各稳态电位平均',['S0326'],same=True if f!='DD' else None,reason='该测试所有配方去除LiNO3')
topt=test('CSA用量优化循环','Li‖Li2S6',dict(sulfur_loading='1.4 mg cm−2（通用Li2S6电极）',rate='0.1 C',formation='先活化，未明确圈数',LiNO3='该优化段未明确'),['S0157','S0158','S0159','S0160','S0161'],['CSA-x2','CSA-x4','CSA-x6'])
for f,vs in [('CSA-x2',[1181,84,98.4]),('CSA-x4',[1274,93,99.4]),('CSA-x6',[1305,72,86.6])]:
 for (metric,unit,point),va,vb in zip([('放电容量','mAh g−1','活化后首圈'),('容量保持率','%','60圈'),('平均库仑效率','%','60圈循环')],vs,[1181,84,98.4]):r(topt,metric,f,'CSA-x2' if f!='CSA-x2' else None,va,vb if f!='CSA-x2' else None,unit,point,['S0157','S0158','S0159','S0160','S0161'],same=True if f!='CSA-x2' else None,reason='列出2/4/6各档；x=0无电池结果')
td=test('恒电位Li2S沉积','Li‖Li2S8',dict(rate='0.112 mA放至2.14 V，2.05 V恒压至<0.01 mA',electrolyte_amount='20 μL 0.2 M Li2S8正极液+20 μL普通电解液负极侧'),['S0053','S0054','S0055','S0056','S0197'])
r(td,'Li2S沉积容量',A,'DD',550,292,'mAh g−1','2.05 V恒电位',['S0197'])
r(td,'Li2S沉积形貌',A,'DD',point='3DP vs 2DI',ev=['S0203','S0204','S0207'],basis='qualitative',direction='变好',reason='作者明确3D促进利用/避免钝化；不是容量数值')
tdis=test('恒电位Li2S溶解','Li‖Li2S8',dict(rate='0.112 mA放至1.7 V后2.35 V恒压20 h/至<0.01 mA',electrolyte_amount='20 μL 0.2 M Li2S8正极液+20 μL普通电解液负极侧'),['S0057','S0211'])
r(tdis,'Li2S溶解容量',A,'DD',691,186,'mAh g−1','2.35 V',['S0211'])
tcv=test('CV与Tafel、扩散控制表征','Li‖S',dict(rate='0.05–0.3 mV s−1',voltage_window='1.7–2.8 V'),['S0077','S0078','S0214','S0216','S0218','S0219','S0223','S0224','S0230'])
for metric,point,ev in [('峰电流/极化','0.05 mV s−1',['S0216']),('Tafel反应动力学','R1/R2/O1；斜率更小',['S0219']),('扫描峰电流/峰偏移','0.05–0.3 mV s−1',['S0224','S0225']),('CV推算Li+扩散','Randles–Sevcik拟合；不是DOSY系数',['S0230'])]:r(tcv,metric,A,'DD',point=point,ev=ev,basis='qualitative',direction='变好',reason='作者定性；CV间接扩散和DOSY非同条件不能判矛盾')
tgitt=test('GITT极化分解','Li‖S',dict(sulfur_loading='4.5 mg cm−2',ES=4,rate='0.05 C；脉冲20 min/休息60 min',voltage_window='1.7–2.8 V'),['S0082','S0083','S0084','S0258','M0167','M0168','M0169','M0170','M0171'])
r(tgitt,'反应动力学/活化极化',A,'DD',point='DoD >25%液固转化段',ev=['M0168','M0169','M0170','M0171'],basis='qualitative',direction='变好',reason='DD活化极化占主导、CSA快速转化；欧姆项不是主因')
tstate=test('首圈不同SoC界面表征','Li‖Li2S6',dict(sulfur_loading='1.4 mg cm−2',rate='0.1 C',characterization='EIS 100 kHz–0.1 Hz、10 mV；DRT、SEM、S 2p XPS'),['S0073','S0234','S0236','S0238','S0241','S0242'])
r(tstate,'转化与界面可逆性',A,'DD',point='首圈不同SoC',ev=['S0241','S0242','S0243'],basis='qualitative',direction='变好',reason='作者SO3富集界面解释；组分强度不是定量容量')
tl=test('低载硫长循环','Li‖S',dict(sulfur_loading='1.1 mg cm−2',ES=16.7,rate='0.2 C'),['M0157','M0173','M0174','M0175'])
for metric,v,u,pnt in [('放电容量',1037,'mAh g−1','首圈'),('容量保持率',70,'%','300圈'),('平均库仑效率',99.8,'%','300圈'),('作者平均容量衰减率',.05,'%/圈','原文；与70%@300按首圈计算不一致')]:r(tl,metric,A,None,v,None,u,pnt,['M0173','M0174','M0175'],same=None,reason='单组文字值；保留内部不一致')
tm=test('3.0 mg贫液循环','Li‖S',dict(sulfur_loading='3.0 mg cm−2',ES=7.4,rate='0.1 C'),['M0158','M0176','M0177','M0178','S0265','S0329'])
for metric,v,u,pnt in [('放电容量',992,'mAh g−1','首圈'),('低平台极化',.232,'V','首圈'),('容量保持率',88,'%','130圈'),('平均库仑效率',99.5,'%','130圈')]:r(tm,metric,A,None,v,None,u,pnt,['M0176','M0177','M0178','S0329'],same=None,reason='单组数值不判配对方向')
r(tm,'循环极化/稳定性',A,'DD',point='130圈附近，DD后期极化增大',ev=['M0176','M0177','M0178'],basis='qualitative',direction='变好',reason='作者定性')
r(tm,'初始容量',A,'DD',point='首圈',ev=['M0176','M0177','M0178'],basis='qualitative',direction='变坏',reason='DD初始容量较高，不能用后期稳定性代替首圈方向')
th=test('6.3 mg高载硫贫液循环','Li‖S',dict(sulfur_loading='6.3 mg cm−2',ES=4.2,rate='0.05 C'),['M0179','M0180','M0181','S0267','S0329'],[A])
for metric,v,u,pnt in [('放电容量',1211,'mAh g−1','首圈'),('面积容量',7.6,'mAh cm−2','首圈'),('放电容量',909,'mAh g−1','50圈'),('容量保持率',67,'%','50圈；与909/1211约75%不一致')]:r(th,metric,A,None,v,None,u,pnt,['M0179','M0180','M0181','S0329'],same=None,reason='作者原值；不自行统一矛盾数值')
th2=test('8.6 mg高载硫贫液循环','Li‖S',dict(sulfur_loading='8.6 mg cm−2',ES=3.6,rate='0.05 C'),['M0182','M0183','S0269','S0329'],[A])
for metric,v,u,pnt in [('放电容量',1094,'mAh g−1','首圈'),('面积容量',9.4,'mAh cm−2','首圈'),('面积容量',7.7,'mAh cm−2','30圈'),('容量保持率',69,'%','30圈；与7.7/9.4约82%不一致')]:r(th2,metric,A,None,v,None,u,pnt,['M0182','M0183','S0329'],same=None,reason='原值保留，内部不一致列核查')
tp=test('3 Ah软包循环','Li‖S pouch',dict(sulfur_loading='8.2 mg cm−2（单面）',ES=2.9,ES_unit='g电解液/gS（方法）；表S14异写μL mg−1，未换算',Li_thickness='75 μm，每侧',rate='0.03 C',voltage_window='1.7–2.55 V',electrolyte_amount='8.0 g',total_mass='17.8 g，含封装'),['S0089','S0090','S0091','S0092','M0186','M0187','S0332'],[A])
for metric,v,u,pnt in [('放电容量',3.12,'Ah','首圈'),('比能量',369,'Wh kg−1','首圈，含封装'),('比能量',307,'Wh kg−1','15圈')]:r(tp,metric,A,None,v,None,u,pnt,['M0186','M0187'],same=None,reason='单组软包')
ttli=test('TFBA验证：锂对称循环','Li‖Li',dict(rate='0.5 mA cm−2 / 0.5 mAh cm−2',electrolyte_amount='40 μL（通用方法）',LiNO3='0.2摩尔份/1摩尔LiTFSI'),['S0080','S0081','S0291','S0292'],['TFBA/DOL'])
r(ttli,'循环寿命','TFBA/DOL',None,'>1000',None,'h','寿命下界',['S0292'],same=None,reason='下界单组')
tt=test('TFBA验证：Li–S循环','Li‖S',dict(sulfur_loading='2.3 mg cm−2',ES=7.7,rate='0.2 C',LiNO3='0.2摩尔份/1摩尔LiTFSI'),['S0293','S0296'],['TFBA/DOL'])
for metric,v,u,pnt in [('放电容量',1051,'mAh g−1','首圈'),('容量保持率',92,'%','100圈')]:r(tt,metric,'TFBA/DOL',None,v,None,u,pnt,['S0293'],same=None,reason='单组验证')
ttsh=test('TFBA验证：穿梭电流','Li‖Li2S6',dict(rate='不同恒电位充电',LiNO3='穿梭测试方法统一无LiNO3'),['S0087','S0287','S0289'],['TFBA/DOL'])
r(ttsh,'穿梭抑制','TFBA/DOL',None,point='S59',ev=['S0287'],basis='qualitative',same=None,reason='作者声称有效抑制，文字未指配对对照')
te=test('碳酸酯不可逆首放电','Li‖S',dict(LiNO3='未报告'),['S0127'],['EC/DEC'])
r(te,'首放电','EC/DEC',None,point='S13（条件不足）',ev=['S0127'],basis='qualitative',same=None,reason='电解液不适用演示，不伪造配对')
tpy=test('吡啶开路兼容性','Li‖S',dict(LiNO3='未报告',rate='开路电压'),['S0131','S0134'],['pyridine'])
r(tpy,'开路稳定性','pyridine',None,point='吡啶电解液；纯溶剂浸锂为另一性质实验',ev=['S0131','S0134'],basis='qualitative',same=None,reason='无同条件配对数值')
def m(summary,pr,cats,ev,ts,side='其他',st='本文结论',a=A,b='DD'):
 D['mechanisms'].append(dict(id=P+f'-M{len(D["mechanisms"])+1}',summary=summary,A=a,B=b,property=pr,categories=cats,source_type=st,evidence_source_types={e:st for e in ev},evidence_ids=ev,test_ids=[t['id'] for t in ts],side=side))
m('碳酸酯受LiPS亲核攻击，损失活性硫并耗溶剂，使放电提前终止','LiPS/溶剂反应',['正极反应','电解液消耗'],['M0041','S0118','S0119'],[te],a='EC/DEC',b=None)
m('DMSO强溶剂化与本征腐蚀缩短锂寿命','溶剂化/锂相容性',['负极锂'],['M0071'],li_tests,side='强侧',a='DMSO组合',b=None)
m('CSA适度配位能力兼顾与锂负极相容性','Li+溶剂化',['负极锂'],['M0072'],li_tests)
m('含TTE体系低电导/高黏度导致不均匀锂沉积及枝晶','输运',['负极锂'],['M0073'],li_tests,a='TTE组合',b=None)
m('CSA/MeTHF梯度溶剂化形成大LiPS团簇，降低扩散与穿梭，减少负极腐蚀','LiPS溶剂化/团簇',['多硫化物穿梭','负极锂'],['M0120','M0122','M0124','M0154','M0155'],[tsh]+cyc_tests)
m('较大LiPS团簇可能促进三维Li2S生长','LiPS团簇',['正极反应'],['M0124'],[td],st='作者推测')
m('CSA主导内壳层促进三维Li2S沉积和快速硫转化','LiPS梯度溶剂化',['正极反应'],['M0133','M0134','M0135','S0197','S0204'],[td,tdis])
m('三维Li2S岛状沉积保留三相界面与离子输运、减轻表面钝化，从而提高硫利用；DD二维致密膜阻碍后续还原','Li2S生长形态',['正极反应'],['M0142','M0146','M0147','M0148','S0203','S0204','S0207'],[td,tstate])
m('SO3富集正极界面改善离子传导与4M转化可逆性；DD过早二维Li2S层遗留LiPS','正极界面化学',['正极反应'],['S0241','S0242','S0243'],[tstate])
m('DD穿梭LiPS腐蚀负极导致疏松苔藓状形貌；CSA体系高价硫物种界面与光滑锂表面对应较好保护','穿梭及负极界面',['负极锂','多硫化物穿梭'],['S0253','S0254','S0255','S0256','M0154','M0155'],cyc_tests)
m('欧姆极化不是贫液差异的主因','欧姆电阻',[],['M0167'],[tgitt])
m('DD液固转化阶段活化极化主导、反应慢；CSA稳定界面和快速转化令较深放电时浓差极化占比更大','液固转化/界面',['正极反应'],['M0168','M0169','M0170','M0171'],[tgitt])
m('过量CSA（x6）加重穿梭并使30圈后衰减，x4梯度配位平衡锂稳定与硫氧化还原','配比及溶剂化',['多硫化物穿梭','负极锂','正极反应'],['S0159','S0160','S0161','S0162'],[topt],side='强侧',a='CSA-x6',b='CSA-x4')
m('TFBA/DOL梯度溶剂化抑制多硫化物穿梭','梯度溶剂化',['多硫化物穿梭'],['S0286','S0287'],[ttsh,tt],a='TFBA/DOL',b=None)
m('吡啶等候选溶剂与锂发生副反应导致不适用；作者提出脱质子解释','锂兼容性',['负极锂'],['S0133','S0134'],[tpy],st='作者推测',a='pyridine/N-methylaniline',b=None)
D['design_claims']=[dict(summary='用七项电化学描述符筛选中强/弱溶剂组合；CSA/MeTHF兼顾抑穿梭、锂稳定和硫转化，TFBA/DOL验证设计可推广。强弱区分Li+配位、LiPS配位与溶解度。',evidence_ids=['M0189','M0190','S0294','S0326'])]
for t,fig,anchors,point in [(tl,'4d',['M0173','M0174'],'首圈和300圈'),(tm,'4e',['M0176','M0177'],'首圈和130圈')]:D['figure_requests'].append(dict(test_id=t['id'],figure=fig,part='main',metric='同条件缺失对照侧容量',A=A,B='DD',target_point=point,anchor_quote_ids=anchors,reason='正文仅CSA侧数值；须核实图号/同测试锚点，代码校准后才用，不由保持率反造对照'))
D['gaps']=['无LiNO3的性质表S11和穿梭测试不能直接套含LiNO3完整电池配方；TTE组无LiNO3，与含LiNO3组不自动配对。','DD与CSA组LiNO3/盐摩尔比相同但CSA绝对盐/添加剂浓度未给；保留潜在条件混杂。','优化x=0只见性质，电池有x=2/4/6；不把未说明LiNO3的优化x=4与正式CSA配方混同。','低载硫70%@300与平均衰减0.05%/圈不一致；6.3 mg的1211→909与67%不一致；8.6 mg的9.4→7.7与69%不一致。均保留作者原值。','软包E/S方法是质量比2.9 ge/gS，表S14写体积比2.9 μL mg−1；未自行用密度转换。','表S12短寿命体系寿命<400 h却仍给400 h附近极化统计，应核原图取点；保持原表数值。','75种候选溶剂仅性质筛选，不当实际电池配方；他文横向比较Table S13不纳入同批方向。']
target=OUT/'independent_predictions'/f'{P}.json'
if target.exists():raise SystemExit('Frozen prediction already exists; no overwrite')
save(target,D)
print(P,len(D['formulations']),len(D['tests']),sum(len(t['results']) for t in D['tests']),len(D['mechanisms']))
