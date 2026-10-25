from _author_a import *
p=paper('S18');p['control_id']='DD';p['control_type']='常规醚基准：1M LiTFSI DOL/DME+2wt% LiNO3'
form(p,'DD','DOL/DME',[('DOL','溶剂化溶剂',1,'体积份'),('DME','溶剂化溶剂',1,'体积份'),('LiTFSI','盐',1,'M'),('LiNO3','添加剂',2,'wt%（表征无此添加剂）')],'DOL/DME 1:1','S0005 S0010')
for w in ['DIPS','DIPE','HME']:
 ns=[10,20,30,35,40]+([50] if w=='HME' else [])
 for n in ns:form(p,f'{w}{n}',f'{n}% {w}',[('DOL/DME','溶剂化溶剂','1:1','v/v'),(w,'弱或非溶剂化溶剂',n,'vol%'),('LiTFSI','盐',1,'M'),('LiNO3','添加剂',2,'wt%（表征无此添加剂）')],f'{n}% {w}+DOL/DME 1:1','S0005 S0010 S0164 S0211 S0213 S0215 M0176 M0193')
 grad(p,w+'含量',['DD']+[f'{w}{n}' for n in ns],[0]+ns,'约20%后WSS进入LiPS内层、溶剂化能力急降','M0069 M0093 M0125 M0126 M0127')
form(p,'DIPS-pouch','DIPS软包电解液',[('DIPS','弱或非溶剂化溶剂',None,'比例原文未写'),('DOL','溶剂化溶剂',None,None),('DME','溶剂化溶剂',None,None),('LiTFSI','盐',1,'M'),('LiNO3','添加剂',5,'wt%')],'DIPS/DOL/DME+1 M LiTFSI+5wt% LiNO3','S0067')
prop(p,'Li+溶剂化',{},'低WSS主要外层，超过20%进入内层并增强Li+-TFSI相互作用','Raman','1M LiTFSI；无LiNO3','M0102 M0104 S0179 S0182 S0184')
prop(p,'LiPS内层WSS配位比例',{'DIPS10':'0（低于10%）','DIPS20':5.67,'DIPS40':18.7},'两阶段增加','Raman分峰、7Li-NMR','1M[S] Li2S6+1M LiTFSI，无LiNO3；%','M0106 M0107 M0121 M0122')
prop(p,'ESP（作者NMR标定DN）',{'DD':16.6,'DIPS20':16.5,'DIPS40':15.6},'约20%后急降','23Na-NMR，10mM NaTFSI探针','1M LiTFSI溶液；kcal mol−1','M0090 M0091 M0094')
base=dict(sulfur_loading='4.0 mgS cm−2',Li_thickness='600 μm',rate='0.1C',LiNO3='2wt%',one_C='1672 mA g−1',electrolyte_volume='45 μL')
for w in ['DIPS','DIPE','HME']:
 fs=['DD']+[f'{w}{n}' for n in [10,20,30,35,40]]+(['HME50'] if w=='HME' else [])
 t=test(p,w+'梯度电压与CE','Li‖S CR2032',fs,'S0049 S0050 S0051 M0036 M0037',**base);result(t,'CE',w+'40','DD','~99','~91','%','第2圈；正文概括三系列','M0036 S0051');result(t,'最低放电电压',w+'40','DD','<1.80','~2.05','V','两平台之间','M0037');fig(p,t,'1C','main','梯度CE及最低电压',w+'40','DD','各含量档位第2圈','M0036 M0037',reason='仅梯度档位图请求；非长循环容量图，根代理判断范围')
 tg=test(p,w+'梯度GITT','Li‖S CR2032',fs,'S0049 S0050 S0052',**{**base,'rate':'0.1C 15min，静置60min'},formation='0.05C 2圈')
 result(tg,'活化极化趋势','全梯度',None,'约20%前小增，之后急升',None,None,'约300mAh g−1极化峰','M0066 M0069 M0070',basis='qualitative',same=None)
 if w=='DIPE':
  result(tg,'活化极化','DIPE20','DD',50.1,22.8,'mV','极化峰','M0080');result(tg,'活化极化','DIPE40','DD',314,22.8,'mV','极化峰','M0080 M0081')
 ts=test(p,w+'液液转化','CNT‖CNT Li2S6对称 CR2032',fs,'S0007 S0026 S0028 S0029 S0031',temperature='0/10/20/25/30/40°C',LiNO3='无',LiPS='1M[S]',electrolyte_volume='40μL')
 if w=='DIPS':result(ts,'电荷转移阻抗','DIPS40','DD',248,93.4,'Ω','室温','M0145');result(ts,'活化能增量','DIPS40','DIPS20',5.2,None,'kJ mol−1','20%→40%；0→20%增1.5','M0148',same=None)
 else:result(ts,'界面转移活化能趋势','全梯度',None,'约20%后显著增大',None,None,'Arrhenius','M0148 M0149 M0150',basis='qualitative',same=None)
 tcat=test(p,w+'35%催化GITT','Li‖S CR2032',[w+'35'],'M0174 M0175 M0176 S0047 S0052 S0273',**{**base,'rate':'0.1C GITT'},catalyst='TiN 0.5mg cm−2隔膜 vs PP')
 if w=='DIPS':result(tcat,'最大活化极化',w+'35+TiN',w+'35+PP',20,98.1,'mV','峰值','M0176',same=False,reason='同电解液改变隔膜催化剂');result(tcat,'浓差极化',w+'35+TiN',w+'35+PP','~50','~50','mV','峰值','M0176',same=False)
 else:result(tcat,'活化极化',w+'35+TiN',w+'35+PP','降低',None,None,'GITT','M0175',basis='qualitative',same=False,reason='改变催化剂')
 tcy=test(p,w+'35%催化长循环','Li‖S CR2032',[w+'35'],'S0054 S0056 M0178',**{**base,'Li_thickness':'50 μm'},formation='0.05C 2圈',catalyst='TiN隔膜 vs PP')
 life={'DIPS':(160,15),'DIPE':(120,8),'HME':(114,24)}[w];result(tcy,'循环寿命',w+'35+TiN',w+'35+PP',*life,'cycles','稳定循环/失败','M0179 M0180' if w=='DIPS' else 'M0193',same=False,reason='催化剂改变，不单归因电解液');
 if w=='DIPS':result(tcy,'初始容量',w+'35+TiN',None,1269,None,'mAh g−1','0.1C','M0179',same=None)
 fig(p,tcy,{'DIPS':'6B','DIPE':'S57','HME':'S58'}[w],'main' if w=='DIPS' else 'si','首圈及同圈容量',w+'35+TiN',w+'35+PP','首圈及对照失效前一圈','M0179 M0180' if w=='DIPS' else 'M0193')
for label,load,es,rate,formation,energy,life,cap,ev,figure in [('2Ah',7.4,3.8,100,25,356,100,2.22,'M0196 M0197 S0071 S0315','S60'),('5Ah',7.6,2.8,25,None,460,67,5.10,'M0198 M0199 S0072 S0315','S61'),('10Ah-565',8.2,2.6,20,10,565,26,9.56,'M0201 S0074 S0317','S62'),('10Ah-607',8.2,2.3,10,5,607,17,9.63,'M0202 M0203 S0075 S0317','S63')]:
 t=test(p,label+'软包','Li‖S+TiN pouch',['DIPS-pouch'],ev+' S0064 S0067',sulfur_loading=f'{load} mgS cm−2单侧',Li_thickness='75μm单侧',ES=es,ES_unit='gele gS−1',rate=f'{rate} mA gS−1',formation=f'{formation} mA gS−1' if formation else '未报告',LiNO3='5wt%',catalyst='TiN混入正极')
 result(t,'初始能量密度','DIPS-pouch',None,energy,None,'Wh kg−1','含包材和极耳',ev,same=None);result(t,'稳定循环寿命','DIPS-pouch',None,life,None,'cycles','循环',ev,same=None);result(t,'初始容量','DIPS-pouch',None,cap,None,'Ah','首圈',ev,same=None);fig(p,t,figure,'si','首圈及寿命末点容量','DIPS-pouch',None,'首圈与末圈',ev)
mech(p,'WSS增加抑制负极副反应但损害正极动力学','全梯度',None,'LiPS溶剂化',['负极锂','正极反应'],'M0034 M0036 M0037',p['tests'][:15],side='其他')
mech(p,'约20%转折来自WSS开始进入LiPS内层，直接配位使本征电荷转移慢和活化极化激增','全梯度',None,'LiPS内层溶剂化',['正极反应'],'M0125 M0127 M0150 M0165',p['tests'][:15],side='弱侧')
mech(p,'WSS配位提高LiPS自由基底物结合能并阻碍脱附与后续反应','全梯度',None,'LiPS配位',['正极反应'],'M0158 M0164',source='本文结论',side='弱侧')
mech(p,'高WSS虽利于负极保护，但过大的正极活化极化造成快速正极失效','35%WSS',None,'LiPS溶剂化',['负极锂','正极反应'],'M0167',p['tests'][:15],side='弱侧')
mech(p,'TiN催化独立调节正极界面转移，降低活化极化而保留弱溶剂化负极稳定性','TiN','PP','界面催化',['正极反应','负极锂'],'M0169 M0175 M0194',p['tests'],side='其他')
claim(p,'高WSS与催化剂协同：用弱溶剂化保护锂，再恢复正极转移以实现高能长寿命软包','M0206 M0209 M0211')
p['gaps']=['软包DIPS具体比例在可检索正文/SI未写，不默认35%。','图中5%、15%、25%等档位文字破损，未凭数字碎片猜配方；已保留明确出现的10/20/30/35/40及HME50。','未报告LiPS溶解度实测；电导率/黏度/迁移数未给。','无独立Li‖Cu或Li‖Li测试；催化剂比较不可单归因电解液。']
save(p)
