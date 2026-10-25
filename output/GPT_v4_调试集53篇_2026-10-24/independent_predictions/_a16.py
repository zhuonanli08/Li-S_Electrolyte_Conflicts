from _author_a import *
p=paper('S16');p['control_id']='DD';p['control_type']='常规醚溶剂自配高LiNO3基准：0.5M LiTFSI+0.8M LiNO3'
form(p,'DD','DD',[('DOL','溶剂化溶剂',1,'体积份'),('DME','溶剂化溶剂',1,'体积份'),('LiTFSI','盐',.5,'M'),('LiNO3','添加剂',.8,'M')],'0.5M LiTFSI+0.8M LiNO3 DOL/DME 1:1','S0034')
for solvent in ['HMPA','TPPO','DMSO','DMF']:
 form(p,'DD_'+solvent,'DD_'+solvent,[('DOL/DME','溶剂化溶剂','1:1','v/v in base'),(solvent,'溶剂化溶剂',8,'vol% added to base'),('LiTFSI','盐',.5,'M in base'),('LiNO3','添加剂',.8,'M in base')],'8vol% '+solvent+' mixed with prepared DD electrolyte','S0034 S0035')
for n in [2,4,5,6,10,12,15,20]:form(p,f'HMPA{n}',f'DD_HMPA-{n}%',[('DD','基液',None,None),('HMPA','溶剂化溶剂',n,'vol%')],f'HMPA {n}%; characterization/specific test as cited','M0036 M0081 S0103 S0184 S0221')
for n in [6,8,10]:form(p,f'alt{n}',f'S19 HMPA-{n}%',[('DOL/DME','溶剂化溶剂','1:1','v/v'),('HMPA','溶剂化溶剂',n,'vol%'),('LiTFSI','盐',1,'M'),('LiNO3','添加剂',.4,'M')],f'1M LiTFSI+0.4M LiNO3; {n}% HMPA','S0221 S0223')
grad(p,'HMPA含量',['DD','HMPA2','HMPA4','DD_HMPA','HMPA10','HMPA12','HMPA15','HMPA20'],[0,2,4,8,10,12,15,20],'Li+配位HMPA增加；高比例不再完全局限内层','M0036 S0103 S0183')
grad(p,'共溶剂种类',['DD','DD_HMPA','DD_TPPO','DD_DMSO','DD_DMF'],['none','HMPA','TPPO','DMSO','DMF'],'种类比较，无单一溶剂化强弱全序','S0034 S0035')
prop(p,'Li+溶剂化',{'DD':'第一层约4.5 O来自DME/DOL','DD_HMPA':'约0.5 O HMPA+2.5 O DME/DOL及TFSI，HMPA局限第一层'},'HMPA参与内层，外层DOL/DME/TFSI','AIMD、7Li NMR、Raman','无LiPS工作电解液','M0041 M0042 M0043 M0050')
prop(p,'LiPS物种/自由基稳定性',{'DD':'无可检测自由基','DD_HMPA':'24h保留最高[S3]自由基','DD_TPPO/DD_DMSO/DD_DMF':'24h几乎无自由基'},'HMPA最高长时稳定性','UV-vis','0.5mM Li2S6盐自由混合溶剂；非饱和溶解度','M0075 M0076 M0077 S0120 S0125 S0126')
fs=['DD_HMPA','DD','DD_TPPO','DD_DMF','DD_DMSO'];tc=test(p,'Li2S恒电位沉积','Li‖Li2S6/CP',fs,'S0044 S0068 S0071 S0072 S0073',rate='2.02 V',formation='0.05C预放至2.07V',temperature='25°C',LiNO3='0.8M',electrolyte_volume='20μL catholyte+20μL无LiPS电解液')
for f,v in zip(fs[1:],[353,518,402,201]):result(tc,'Li2S沉积容量','DD_HMPA',f,618,v,'mAh gsulfur−1','恒电位积分','M0111 M0112 M0118')
tl=test(p,'锂沉积剥离效率','Li‖Cu',fs,'S0053 S0054 M0127 M0128 M0129',rate='0.5 mA cm−2/1mAh cm−2',LiNO3='0.8M基液');result(tl,'平均CE','DD_HMPA/DD_TPPO','DD','>98.7',98.4,'%','A400圈，B280圈','M0127 M0129',same=False);result(tl,'平均CE','DD_DMSO',None,95,None,'%','120圈','M0128',same=None);result(tl,'CE','DD_DMF',None,'30–60',None,'%','循环','M0128',same=None);result(tl,'循环寿命','DD_HMPA/DD_TPPO','DD',400,280,'cycles','无明显衰减','M0127 M0129')
ts=test(p,'对称锂','Li‖Li',['DD_HMPA','DD','HMPA10','HMPA12','HMPA15'],'S0175 S0177 S0184',rate='1mA cm−2/1mAh cm−2',LiNO3='0.8M基液');result(ts,'不短路时间','DD_HMPA','DD',500,130,'h','短路/测试结束','M0139 S0179');result(ts,'高HMPA含量趋势','HMPA10/12/15','DD_HMPA','含量越高寿命越短',None,None,'循环','S0180',basis='qualitative',direction='变坏')
tsc=test(p,'高HMPA锂效率','Li‖Cu',['HMPA10','HMPA12','HMPA15'],'S0177 S0180',rate='0.5mA cm−2/1mAh cm−2（按LiCu通用方法）');result(tsc,'CE','全梯度',None,'随HMPA增加降低',None,None,'循环','S0180',basis='qualitative',same=None)
tests=[]
for load,es,rate,init,end,cycles,ev in [(3.2,10,.1,1094,799,100,'M0165 M0175'),(3.5,5,.05,1213,860,70,'M0172 M0176'),(5.5,4,.1,864,None,65,'M0177 M0182 M0191')]:
 t=test(p,f'载量{load} E/S{es}循环','Li‖S CR2032',fs if load!=5.5 else fs[:2],ev+' S0046 S0047 S0049',sulfur_loading=f'{load} mg cm−2',ES=es,ES_unit='μL mg−1',rate=str(rate)+' C',temperature='25°C',LiNO3='0.8M基液');tests.append(t);result(t,'初始容量','DD_HMPA',None,init,None,'mAh gsulfur−1','首圈',ev,same=None)
 if end:result(t,'循环容量','DD_HMPA',None,end,None,'mAh gsulfur−1',f'{cycles}圈',ev,same=None)
 else:result(t,'容量保持率','DD_HMPA',None,85.4,None,'%',f'{cycles}圈',ev,same=None)
 result(t,'循环稳定性','DD_HMPA','DD','更好',None,None,'循环',ev,basis='qualitative',direction='变好');fig(p,t,{3.2:'5a',3.5:'5c',5.5:'5e'}[load],'main','同圈容量','DD_HMPA','DD','首圈及末圈',ev)
tr=test(p,'倍率','Li‖S CR2032',fs,'S0213 S0214 S0217 S0219',rate='0.1/0.2/0.5/1/2/2.5/3 C',LiNO3='0.8M基液')
for r,v in zip([.1,.2,.5,1,2,2.5,3],[1227,1034,976,930,889,830,776]):result(tr,'倍率容量','DD_HMPA',None,v,None,'mAh gsulfur−1',str(r)+' C','S0214',same=None)
result(tr,'倍率表现','DD_HMPA','DD/DD_TPPO/DD_DMF/DD_DMSO','更高',None,None,'倍率','S0214 S0218 S0219 S0220',basis='qualitative',direction='变好')
talt=test(p,'另盐浓度HMPA梯度循环','Li‖S',['alt6','alt8','alt10'],'S0221 S0222 S0223',LiNO3='0.4 M');result(talt,'容量保持率','alt10','alt6/alt8','更高',None,None,'循环','S0224',basis='qualitative',direction='变好');fig(p,talt,'S19a','si','各档首圈/末圈容量','alt10','alt6','首圈/末圈','',reason='正文无可核数锚点，仅图未读')
talt2=test(p,'另盐浓度HMPA梯度倍率','Li‖S',['alt6','alt8','alt10'],'S0221 S0222 S0223',LiNO3='0.4M',rate='含2.5C');result(talt2,'倍率容量','alt10',None,130,None,'mAh g−1','2.5C','S0225',same=None);result(talt2,'倍率表现','alt10','alt6/alt8','更差',None,None,'倍率','S0225',basis='qualitative',direction='变坏')
tli=test(p,'Li2S正极','Li‖Li2S/CP',fs,'S0056 S0057 S0234 S0235',rate='0.05C',formation='初充至4.0V后1.7–2.6V',electrolyte_volume='20μL');result(tli,'容量','DD_HMPA','其他配方','更高',None,None,'第2圈','S0235',basis='qualitative',direction='变好')
te=test(p,'CV/EIS动力学','Li‖S',fs,'S0051 S0055 S0201 S0206',rate='CV 0.1/0.2/0.5mV s−1；EIS10mV');result(te,'CV峰电流','DD_HMPA','DD','更高',None,None,'CV','S0203',basis='qualitative',direction='变好');result(te,'阻抗','DD_HMPA','DD/其他HSE','更低',None,None,'首放后和首充后','S0209 S0210',basis='qualitative',direction='变好')
tp=test(p,'2.71Ah软包','Li‖S pouch',fs[:2],'M0184 M0185 S0088 S0089 S0090',sulfur_loading='4.6 mg cm−2单侧（双面9.2）',ES=4,ES_unit='μL mg−1',Li_thickness='125 μm（双侧整体，原文）',rate='0.1C',temperature='25°C',LiNO3='0.8M基液');result(tp,'容量','DD_HMPA',None,2.71,None,'Ah','首圈','M0185',same=None);result(tp,'能量密度','DD_HMPA',None,307,None,'Wh kg−1','整包18.96g','M0185',same=None);result(tp,'容量保持率','DD_HMPA',None,86.7,None,'%','20圈','M0185',same=None);result(tp,'循环表现','DD_HMPA','DD','高容量且稳定','低容量且快速衰减',None,'循环','M0185',basis='qualitative',direction='变好');fig(p,tp,'6d','main','首圈与同圈容量','DD_HMPA','DD','首圈、第20圈','M0185')
for summary,A,B,pr,cat,ev,tt,src,side in [
 ('氢键将HMPA限于第一层，降低其与锂接触副反应','DD_HMPA','DD_DMF/DD_DMSO','Li+核壳溶剂化',['负极锂'],'M0051 M0055 M0188',[tl,ts],'本文结论','其他'),
 ('HMPA-Li[S3]复合物减少自由基碰撞，延长寿命并促进硫反应','DD_HMPA','DD','LiPS/自由基溶剂化',['正极反应'],'M0093 M0094 M0095 M0096',tests,'本文推测','其他'),
 ('自由基化学作用阻止Li2S过早覆盖电极和钝化','DD_HMPA','DD','自由基反应',['正极反应'],'M0115',[tc],'本文推测','弱侧'),
 ('DMSO对Li2S强溶剂化提高成核势垒，沉积容量最低','DD_DMSO','DD_HMPA','Li2S溶剂化',['正极反应'],'M0118 M0123',[tc],'本文结论（与他文一致）','强侧'),
 ('HMPA溶剂化增加TFSI参与，SEI富LiF/Li3N并抑制DOL/DME分解','DD_HMPA','DD','Li+溶剂化',['负极锂','电解液消耗'],'M0147 M0148 M0149',[tl],'本文推测','其他'),
 ('过多HMPA可能不再限于第一层，加剧对锂反应','HMPA10/12/15','DD_HMPA','Li+溶剂化',['负极锂'],'S0180 S0181 S0182 S0183 S0184',[ts,tsc],'本文推测','强侧'),
 ('高HMPA提高保持率但高亲电子给体性造成去溶剂化困难、倍率变差','alt10','alt6/alt8','Li+去溶剂化',['正极反应'],'S0224 S0225 S0226',[talt,talt2],'本文推测','强侧'),
 ('TPPO高黏度降低高倍率容量','DD_TPPO','DD_HMPA','黏度',['正极反应'],'S0218',[tr],'本文结论','其他'),
 ('快速自由基介导硫反应抑制LiPS穿梭','DD_HMPA','DD','自由基反应',['多硫化物穿梭'],'M0169',tests,'本文结论','其他')]:mech(p,summary,A,B,pr,cat,ev,tt,source=src,side=side)
claim(p,'适量HMPA核壳结构同时稳定自由基与锂负极，兼顾贫液硫利用率和循环','M0186 M0187 M0188 M0189 M0190')
p['gaps']=['未报告实测LiPS饱和溶解度、离子电导率、迁移数。','盐先配成基液再加8%溶剂；不把基液浓度直接当最终浓度。','SI S19使用不同盐浓度，拆测试和配方。','多数扣电锂厚/1C定义未报告。','S22正文说明0.1C而图标签0.05C，与图5c0.05C冲突。']
save(p)
