from _author_a import *
p=paper('S15');p['control_id']='LiTFSI';p['control_type']='其他：DIPS弱溶剂化自配对照，5 wt% LiNO3'
for f,salts in [('LiTFSI',[('LiTFSI','盐',1,'M')]),('LiFSI',[('LiFSI','盐',.8,'M'),('LiTFSI','盐',.2,'M')])]:form(p,f,f,[('DME','溶剂化溶剂',1,'摩尔份'),('DOL','溶剂化溶剂',.75,'摩尔份'),('DIPS','弱或非溶剂化溶剂',.25,'摩尔份'),('LiNO3','添加剂',5,'wt%')]+salts,'DME/DOL/DIPS=1:0.75:0.25 mol/mol/mol','S0009 S0056 S0057')
grad(p,'盐种类',['LiTFSI','LiFSI'],['1M LiTFSI','0.8M LiFSI+0.2M LiTFSI'],'作者未给可验证强弱排序；LiFSI用于改善界面转移','S0056 S0057 M0145')
base=dict(sulfur_loading='4.0 mgS cm−2',Li_thickness='50 μm',ES_unit='μL mg−1',LiNO3='5 wt%',one_C='1672 mA g−1')
gitts=[]
for es in [12,8,6,5,4.5]:
 t=test(p,f'GITT E/S={es}','Li‖S CR2032',['LiTFSI'],'M0052 S0013 S0014 S0017',ES=es,rate='0.1 C放/充6min，静置60min',**base);gitts.append(t)
 if es in [12,6,4.5]:
  vals={12:[25,60,7],6:[44,None,None],4.5:[185,78,38]}[es]
  for metric,v in zip(['活化极化','浓差极化','欧姆极化'],vals):
   if v is not None:result(t,metric,'LiTFSI',None,v,None,'mV','Li2S成核阶段','M0081 M0082 M0084',same=None)
 if es in [6,4.5]:result(t,'总动力学极化','LiTFSI',None,96 if es==6 else 300,None,'mV','Li2S成核','M0061',same=None)
tl=test(p,'负极极化分离','Li‖Li CR2025',['LiTFSI'],'M0066 M0068 S0021 S0024 S0029',Li_thickness='50 μm',rate='0.72 mA cm−2/3.60 mAh cm−2',LiPS='0/1/4 M[S]',electrolyte_volume='40 μL',LiNO3='5 wt%');result(tl,'扣除欧姆后的负极动力学极化','LiTFSI',None,'<16',None,'mV','第3圈、所有LiPS浓度','M0068 S0029',same=None)
for concentration in [2,4,6]:
 t=test(p,f'Li2S沉积 {concentration} M[S]','Li‖Li2S8/CP',['LiTFSI'],'S0047 S0048 S0049 S0054 S0055',Li_thickness='600 μm',rate='2.10 V积分',formation='2.30/2.25/2.20/2.15 V各10h；2.10/2.05 V各50h',LiPS=f'{concentration} M[S]',electrolyte_volume={2:'75 μL',4:'37.5 μL',6:'25 μL'}[concentration]);result(t,'Li2S沉积容量','LiTFSI',None,{2:124,4:97,6:73}[concentration],None,'mAh g−1','2.10V','M0129 M0135',same=None)
ta=test(p,'界面转移活化能','Li‖Li2S8/CP三电极，Cu@Li参比',['LiTFSI'],'S0041 S0042 S0043 S0044 S0045',Li_thickness='600 μm',rate='0.5 mA放至Li2S成核后EIS',temperature='303/308/313/318/323 K',LiPS='2/4/6 M[S]',electrolyte_volume='70 μL（SI；正文称等硫量，冲突）');result(ta,'界面电荷转移活化能','6M[S]','2M[S]',193,150,'kJ mol−1','Li2S成核','M0109',same=False,reason='B=193−43；浓度变化非同条件')
tr=test(p,'E/S4.5倍率','Li‖S CR2032',['LiFSI','LiTFSI'],'S0057 S0058 S0059',ES=4.5,rate='0.1/0.2/0.3/0.2/0.1 C各3圈',formation='0.05 C 2圈',**base);result(tr,'容量','LiFSI','LiTFSI',980,800,'mAh g−1','0.1 C','M0142',reason='B=980−180');result(tr,'容量','LiFSI',None,798,None,'mAh g−1','0.3 C','M0140',same=None);result(tr,'最大可循环倍率','LiFSI','LiTFSI',.3,.1,'C','倍率','M0140 M0141');result(tr,'中值电压','LiFSI',None,1.90,None,'V','0.2 C','M0144',same=None);result(tr,'中值电压','LiFSI',None,1.82,None,'V','0.3 C','M0144',same=None)
tc=test(p,'E/S5循环','Li‖S CR2032',['LiFSI','LiTFSI'],'S0060 S0061 S0062',ES=5,rate='0.2 C',formation='0.05和0.1 C化成两圈（各两圈与合计原句不明确）',**base);result(tc,'首圈容量','LiFSI',None,984,None,'mAh g−1','0.2 C','M0149',same=None);result(tc,'寿命','LiFSI','LiTFSI',50,'立即失败','cycles','约60%初容量','M0148 M0149',basis='qualitative',direction='变好');fig(p,tc,'S39','si','化成后首圈及第50圈容量','LiFSI','LiTFSI','0.2C首圈和第50圈','M0149 S0130')
th=test(p,'7mg载量倍率及循环','Li‖S CR2032',['LiFSI','LiTFSI'],'S0063 S0065 S0066 S0067 S0068',sulfur_loading='7.0 mgS cm−2',Li_thickness='50 μm（沿用方法）',ES=5,ES_unit='μL mg−1',rate='0.1/0.15/0.2/0.25 C后0.1 C',formation='0.05 C 2圈',LiNO3='5wt%',one_C='1672 mA g−1');result(th,'最大倍率','LiFSI','LiTFSI',.25,.15,'C','倍率','M0151');result(th,'回0.1C稳定循环','LiFSI','LiTFSI',15,1,'cycles','倍率测试后','M0152');fig(p,th,'4b','main','同倍率容量','LiFSI','LiTFSI','0.1C首轮和回到0.1C','M0152')
pb=dict(Li_thickness='75 μm单侧',ES_unit='gele gS−1',LiNO3='5wt%',one_C='1000 mA g−1')
tp3=test(p,'3Ah软包倍率','Li‖S pouch',['LiFSI','LiTFSI'],'S0075 S0077 S0079 S0080',sulfur_loading='7.8 mgS cm−2单侧',ES=2.8,rate='放0.05/0.08/0.1/0.15 C；充0.025 C',formation='静置12h，首放0.025 C',**pb)
for r,v in zip([.025,.05,.08,.1,.15],[1219,1139,1099,1080,939]):result(tp3,'放电容量','LiFSI',None,v,None,'mAh g−1',str(r)+' C','M0155',same=None)
result(tp3,'倍率能力','LiFSI','LiTFSI','0.15C仍工作','0.05C迅速失败，较高倍率<200',None,'倍率','M0155 M0156',basis='qualitative',direction='变好')
tp5=test(p,'5Ah软包','Li‖S pouch',['LiFSI','LiTFSI'],'S0081 S0082',sulfur_loading='7.9 mgS cm−2单侧',ES=2.5,rate='0.05 C',formation='静置12h',**pb);result(tp5,'首放电容量','LiFSI','LiTFSI',1150,295,'mAh g−1','首圈','M0156',reason='B=1150−855');result(tp5,'能量密度','LiFSI',None,410,None,'Wh kg−1','整包','M0157 S0139',same=None)
tp8=test(p,'8Ah软包循环','Li‖S pouch',['LiFSI'],'S0083 S0084',sulfur_loading='7.5 mgS cm−2单侧',ES=2.8,rate='0.025 C',formation='静置12h',**pb);result(tp8,'首放电容量','LiFSI',None,1260,None,'mAh g−1','首圈','M0158',same=None);result(tp8,'能量密度','LiFSI',None,474,None,'Wh kg−1','首圈','M0158',same=None);result(tp8,'能量密度','LiFSI',None,412,None,'Wh kg−1','20圈','M0159',same=None);result(tp8,'CE','LiFSI',None,'~99',None,'%','20圈期间','M0159',same=None);fig(p,tp8,'4e','main','容量及寿命终点','LiFSI',None,'首圈、第20圈及终点','M0158 M0159')
for summary,ev,cat,ts,side in [
 ('弱溶剂化贫液的高极化主要来自正极，负极贡献小于5%','M0068 M0069',['正极反应'],gitts,'弱侧'),
 ('电解液减量使Li2S成核活化极化急增，界面转移成为关键瓶颈','M0088 M0110 M0111',['正极反应'],gitts+[ta],'弱侧'),
 ('浓度升高使Li2S由三维扩散控制转为二维表面反应控制，核小层薄，更快覆盖导电表面并降低容量','M0118 M0119 M0126 M0127 M0136',['正极反应'],p['tests'][6:9],'弱侧'),
 ('LiFSI提高贫液弱溶剂化体系的界面转移动力学，改善倍率与循环','M0145 M0161 M0165',['正极反应'],[tr,tc,th,tp3,tp5,tp8],'其他')]:mech(p,summary,'LiFSI' if side=='其他' else 'LiTFSI','LiTFSI' if side=='其他' else None,'LiPS溶剂化/界面反应',cat,ev,ts,side=side)
claim(p,'通过LiFSI盐调控LiPS溶剂化，加快贫液弱溶剂化体系硫反应','M0175 M0176')
p['gaps']=['全电池测试温度未报告；Li+溶剂化、LiPS溶解度、电导率、黏度、迁移数未给实测排序。','8Ah正文写20圈，SI比较表写25圈，保留图核对请求。','5Ah对照容量为1150−855反算；984与结论985差异保留主结果984。','活化能方法正文称等硫，SI70μL各浓度造成硫不同，未自行消除冲突。']
save(p)
