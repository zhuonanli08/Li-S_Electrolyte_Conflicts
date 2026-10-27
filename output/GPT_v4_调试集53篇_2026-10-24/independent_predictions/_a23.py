from _author_a import *
p=paper('S23');p['control_id']='BL';p['control_type']='1 M LiTFSI + 0.2 M LiNO3 DOL/DME 1:1'
for n in [0,5,10,20,50]:
 k='BL' if n==0 else 'BL+'+str(n)
 form(p,k,k,[('DOL','溶剂',(100-n)/2,'vol.%'),('DME','溶剂',(100-n)/2,'vol.%'),('LIB 1200ET','弱溶剂化共溶剂',n,'vol.%'),('LiTFSI','盐',1,'M'),('LiNO3','添加剂',0.2,'M')],f'1200ET {n} vol.%; 其余DOL/DME1:1；1M LiTFSI+0.2M LiNO3','S0015 S0016')
fs=['BL+20','BL'];gs=['BL','BL+10','BL+20','BL+50']
grad(p,'1200ET体积分数',['BL','BL+5','BL+10','BL+20','BL+50'],[0,5,10,20,50],'Li+–溶剂减弱、Li+–阴离子及LiPS配位增强；高LiPS浓度缓冲该效应','S0015 S0016 M0064 M0080 M0082 M0097')
prop(p,'CIP/AGG比例',{'BL':11.98,'BL+50':24.5},'随1200ET上升','Raman拟合，%','不含Li2S6电解液','M0062 M0063 M0064')
prop(p,'LiPS溶解/聚集',{'BL+20':'溶解态减少，先聚集后动态再平衡','BL+50':'0.25M Li2S6时可能沉淀/胶体'},'弱溶剂化降低自由LiPS；非单调NMR受浓度影响','NMR/UV-vis/H-cell','0.25M与0.5M Li2S6分开','M0083 M0084 M0085 M0094 M0096 M0103 M0108 M0113 M0114')
prop(p,'离子电导',{'BL+50':'明显降低'},'1200ET过多降低电导','电导仪','0/5/10/20/50%','M0124 S0124')
tg=test(p,'GITT放充电极化','Li‖S coin',gs,'M0140 M0141 M0154 M0155 M0156 M0162 S0033 S0087 S0088',sulfur_loading='3.8 mg cm−2',ES=8,ES_unit='μL mgS−1',Li_thickness='600 μm',rate='C/20 15 min，静置6 h',LiNO3='0.2 M',voltage='1.6–2.8 V')
for k,total,oa in [('BL+10',133,45),('BL+20',160,45),('BL+50',214,73)]:
 result(tg,'总放电极化',k,'BL',total,119,'mV','约20%DoD最大值','M0154');result(tg,'欧姆+活化极化',k,'BL',oa,37,'mV','约20%DoD','M0155')
result(tg,'浓差极化','BL+50','BL',141,82,'mV','约20%DoD','M0156');result(tg,'充电热力学曲线/极化','BL+20/BL+50','BL','差异小','差异小',None,'充电','M0162',basis='qualitative',direction='差异小')
te=test(p,'LiPS电荷转移能垒','Li2S6对称',gs,'M0164 M0167 M0168 M0169 S0022 S0049 S0089 S0091',temperature='0/10/20/25/30/40/50/60 °C',LiNO3='0.2 M',catholyte='0.25 M Li2S6；每侧20 μL')
for k,v in [('BL+10',51.71),('BL+20',51.80),('BL+50',52.30)]:result(te,'电荷转移活化能',k,'BL',v,50.96,'kJ mol−1','Arrhenius拟合','M0168 M0169')
tv=test(p,'LiPS CV扩散拟合','Li‖Li2S6',gs,'M0173 M0175 M0198 S0047 S0048 S0097 S0133 S0134',rate='0.1/0.2/0.3/0.5/1 mV s−1',LiNO3='0.2 M',catholyte='0.25 M Li2S6；40 μL+负极5 μL无LiPS电解液')
for k,v in [('BL+10',5.35),('BL+20',5.11),('BL+50',4.77)]:result(tv,'R2峰Randles–Sevcik斜率绝对值',k,'BL',v,5.76,None,'R2拟合','M0175')
result(tv,'R1/O斜率','BL+20','BL','基本不变','基本不变',None,'拟合','M0176',basis='qualitative',direction='差异小')
tls=[]
for ps,current in [(False,0.5),(True,0.5),(True,1)]:
 ev='M0184 M0185 M0188 M0189 M0190' if not ps else 'M0193 M0194 M0204' if current==0.5 else 'M0205 S0138 S0139'
 t=test(p,f'Li对称 {current} '+('有Li2S6' if ps else '无Li2S6'),'Li‖Li',fs,ev+' S0043 S0044 S0099 S0100 S0101',rate=f'{current} mA cm−2; {current} mAh cm−2',LiNO3='0.2 M',catholyte='0.25 M Li2S6' if ps else '无Li2S6',electrolyte_volume='每侧20 μL');tls.append(t)
 if not ps:
  result(t,'终点过电位',*fs,42,46,'mV','测试末期','M0189');result(t,'早期极化/稳定性',*fs,'较低较稳定','高且波动',None,'初始至稳定段','M0185 M0186 M0187',basis='qualitative',direction='变好');result(t,'末期RSEI',*fs,'几乎相同','几乎相同',None,'最终EIS','M0190',basis='qualitative',direction='差异小')
 elif current==0.5:result(t,'过电位',*fs,10,13,'mV','半周期末','M0194');result(t,'RSEI',*fs,'各圈更小',None,None,'各圈','M0204',basis='qualitative',direction='变好')
 else:result(t,'过电位',*fs,23,36,'mV','10–108 h稳定段','M0205');result(t,'过电位',*fs,51,148,'mV','最终半周期末','M0205')
for ps in [False,True]:
 ev='M0235 M0236 M0237 M0239' if ps else 'M0228 M0230 M0232 M0233 M0238'
 t=test(p,'LiCu循环 '+('有Li2S6' if ps else '无Li2S6'),'Li‖Cu',fs,ev+' S0045 S0046 S0102 S0104 S0106',rate='0.5 mA cm−2;0.5 mAh cm−2',formation='0.5 mA cm−2 10 h预沉积；有LiPS先0.1 mA cm−2还原',LiNO3='0.2 M',catholyte='0.25 M Li2S6' if ps else '无Li2S6')
 result(t,'初期过电位',*fs,12 if ps else '21–37',16 if ps else '61–65','mV','region i',ev);result(t,'稳定段过电位',*fs,10 if ps else 16,13 if ps else 16,'mV','region ii',ev);result(t,'剥离极化突增时间',*fs,273 if ps else 180,258 if ps else 163,'h','region iii',ev);result(t,'CE开始下降圈数',*fs,142 if ps else 133,129 if ps else 95,'cycles','CE衰减',ev)
 tce=test(p,'改良平均CE '+('有Li2S6' if ps else '无Li2S6'),'Li‖Cu',fs,'M0242 M0243 S0107 S0108 S0109 S0110',rate='0.5 mA cm−2;0.5 mAh cm−2',formation='0.1 mA cm−2沉积剥离各5h；再预沉积5h/15次1h循环/终剥离1V',LiNO3='0.2 M',catholyte='0.25 M Li2S6' if ps else '无Li2S6');result(tce,'平均CE',*fs,98.27 if ps else 97.90,98.06 if ps else 97.57,'%','15圈改良法','M0242 M0243')
th=test(p,'高电流LiCu有LiPS','Li‖Cu',fs,'M0240 S0105 S0142',rate='1 mA cm−2;1 mAh cm−2',catholyte='0.25 M Li2S6',LiNO3='0.2 M');fig(p,th,'S22','si','极化/失效时间',*fs,'稳定段/末期','M0240 S0142')
tce=test(p,'高电流改良平均CE有LiPS','Li‖Cu',fs,'M0244 S0107 S0108 S0110 S0146',rate='1 mA cm−2;1 mAh cm−2',catholyte='0.25 M Li2S6',LiNO3='0.2 M');result(tce,'平均CE',*fs,97.51,97.40,'%','改良法','M0244 S0146')
tsh=test(p,'无LiNO3穿梭电流','Li‖S coin',gs,'M0249 S0018 S0111 S0112 S0113 S0114 S0150',rate='先2.10 V，2.15–2.40 V阶梯恒电位',LiNO3='无');result(tsh,'副反应/穿梭',*fs,'受抑制',None,None,'稳态阶梯','M0249',basis='qualitative',direction='变好');fig(p,tsh,'S25','si','穿梭电流','BL+20','BL','2.3/2.4 V同电位','M0249 S0150')
to=test(p,'原位Raman硫转化','光学Li‖S',fs,'M0249 M0250 M0256 M0257 M0258 M0264 M0265 S0054 S0055',sulfur_loading='4.2 mg cm−2',ES=6,ES_unit='μL mgS−1',rate='C/20',LiNO3='0.2 M');result(to,'长链LiPS峰出现DoD',*fs,21,8,'%','恒流放电','M0257 M0264');result(to,'长链LiPS峰消失DoD',*fs,50,70,'%','恒流放电','M0258 M0265')
tp=test(p,'单层软包循环','Li‖S SLP',fs,'M0051 M0053 M0317 M0321 M0322 M0327 S0037 S0042 S0157',sulfur_loading='3.7 mg cm−2',ES=6,ES_unit='μL mgS−1',Li_thickness='40 μm',rate='C/3',formation='C/15 3圈',LiNO3='0.2 M')
result(tp,'容量','BL+20',None,527,None,'mAh g−1','200圈','M0009 M0053',same=None);result(tp,'循环寿命',*fs,'>200',168,'cycles','BL失效','M0317');result(tp,'平均CE','BL+20',None,95.41,None,'%','200圈','M0317',same=None);result(tp,'末圈CE','BL+20',None,91.4,None,'%','200圈','M0317',same=None)
result(tp,'初始容量',*fs,'较低','较高',None,'初始','M0319 M0321',basis='qualitative',direction='变坏');result(tp,'后续容量',*fs,'逐渐恢复并超过BL',None,None,'循环中','M0322',basis='qualitative',direction='变好');result(tp,'dQ/dV极化',*fs,28.5,17.1,'mV','150圈前','M0327');fig(p,tp,'5a','main','容量交叉及同圈容量',*fs,'首圈、100、150圈','M0317 M0319 M0321 M0322')
tr=test(p,'倍率（修改1C定义）','Li‖S pouch',fs,'M0338 M0339 M0340 S0161',rate='C/30,C/10,C/7,C/5,C/4,C/3,C/2→C/5',one_C='1000 mA g−1',LiNO3='0.2 M');result(tr,'容量',*fs,'>600','<500','mAh g−1','C/2','M0339');result(tr,'返回容量',*fs,766,652,'mAh g−1','返回C/5','M0340');fig(p,tr,'S33','si','倍率容量',*fs,'各倍率同点','M0338 M0339 M0340 S0161')
tm=test(p,'Ah多层软包','Li‖S MLP 8层双面',fs,'M0343 M0345 M0348 M0349 M0350 S0037 S0042 S0164',sulfur_loading='3.5 mg cm−2',ES=4,ES_unit='μL mgS−1',Li_thickness='40 μm',rate='C/3',formation='C/15',LiNO3='0.2 M')
for met,v,u,pt in [('初始能量密度',358,'Wh kg−1','初始'),('初始容量',1.53,'Ah','初始'),('平均容量',732,'mAh g−1','常规循环'),('末容量',662.8,'mAh g−1','>50圈末'),('平均能量密度',262,'Wh kg−1','常规循环')]:result(tm,met,'BL+20',None,v,None,u,pt,'M0345 M0348',same=None)
result(tm,'容量衰减',*fs,'较慢','活化后更快',None,'>50圈','M0349',basis='qualitative',direction='变好');fig(p,tm,'5f/S35','main/si','同圈容量',*fs,'初始及50圈','M0345 M0348 M0349 S0164')
mech(p,'1200ET弱化Li+-溶剂，增强阴离子/LiPS配位与聚集，降低自由LiPS溶解及扩散','BL+20','BL','Li+与LiPS溶剂化',['多硫化物穿梭'],'M0100 M0120 M0127 M0128',[tsh],side='弱侧')
mech(p,'增多1200ET主要增加浓差极化；20%内活化动力学影响有限，50%额外增加活化和传质限制','BL+50','BL/BL+20','溶剂化/扩散',['正极反应'],'M0154 M0155 M0156 M0157 M0160 M0171 M0182',[tg,te,tv],side='弱侧')
mech(p,'Li2S6初期还原参与SEI构建，1200ET推动其与LiPS及盐阴离子反应，形成兼具LiF机械稳定和S4+离子传导的SEI','BL+20','BL','LiPS反应/SEI',['负极锂'],'M0224 M0225 M0245 M0248 M0314 M0315 M0353 M0354 M0355',tls+[tp,tm],side='弱侧')
mech(p,'无LiPS时1200ET分解生成LiF富集SEI可能减轻死锂与曲折输运','BL+20','BL','界面成分',['负极锂'],'M0216 M0217 M0218',[tls[0]],source='本文推测')
mech(p,'适当弱溶剂化初期SEI重构带来暂时容量损失与高极化，成熟后降低极化并提高长期稳定','BL+20','BL','SEI演化',['负极锂','正极反应'],'M0321 M0322 M0323 M0324',[tp],side='弱侧')
mech(p,'局部高电流区动力学主导，低电流区更显溶剂化控制；深循环SEI成熟降低早期空间差异','BL+20','BL','空间异质性',['负极锂'],'M0290 M0291 M0293 M0298 M0300 M0301 M0302 M0305',[tp],source='本文推测')
mech(p,'即使20%共溶剂，无LiPS对称电池长循环界面仍逐渐退化，最终极化趋同','BL+20','BL','长期SEI稳定',['负极锂'],'M0188 M0189 M0190',[tls[0]],side='弱侧')
claim(p,'用20%非配位共溶剂平衡有限SRR动力学代价与LiPS介导的稳定导离子SEI','M0182 M0183 M0356 M0357 M0358 M0362')
p['gaps']=['1200ET完整分子结构论文未给，仅专利引用，未联网补齐。','多数循环1C定义未明确，仅S33倍率明确1000 mA g−1，不外推。','S19图注说without Li2S6但曲线标记+PS且正文/S20为with，保留正文归类并记冲突。','S21图注1mA与图内/正文0.5mA冲突，采用正文和图内一致的0.5mA。','倍率图称pouch但SLP/MLP归属与S34标题不够明确，不填载量/E/S。','不将XANES可能S4+峰指定为已证实单一化合物。']
save(p)
