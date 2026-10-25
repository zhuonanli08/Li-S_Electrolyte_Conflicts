from _author_a import *
p=paper('S09');p['control_id']='DDN';p['control_type']='常规醚基准（DDN）；另有无LiNO3的DD'
for f in ['DEE','F3DEE','F4DEE','F4DMB','F5DEE','F6DEE']:
 form(p,f,f,[('LiTFSI','盐',1.2 if f!='F6DEE' else '<1.2（饱和）','M'),(f,'溶剂化溶剂',None,'单溶剂')],'1.2 M LiTFSI in '+f if f!='F6DEE' else 'saturated LiTFSI in F6DEE','M0250 M0251')
for f in ['DD','DDN']:
 cs=[('DOL','溶剂化溶剂',None,'比例原文未写'),('DME','溶剂化溶剂',None,'比例原文未写'),('LiTFSI','盐',1,'M')]
 if f=='DDN':cs.append(('LiNO3','添加剂',1,'wt%'))
 form(p,f,f,cs,'1M LiTFSI DOL/DME'+(' +1wt% LiNO3' if f=='DDN' else ''),'M0252 S0029')
order=['DD','DEE','F3DEE','F4DEE','F4DMB','F5DEE','F6DEE']
grad(p,'溶剂氟化种类梯度',order,['DD','DEE','3F','4F-DEE','4F-DMB','5F','6F'],'LiPS溶解度逐级降低；F4DMB为不同骨架','M0081 M0083 M0091')
prop(p,'LiPS溶解度',{'DD':'1100（引自他文）','DEE':'~200','F4DEE':140,'F4DMB':70,'F5DEE':'<50','F6DEE':37},'DD>DEE>F3DEE>F4DEE>F4DMB>F5DEE>F6DEE','ICP-OES','纯溶剂Li2S6饱和，mM [S]；DD来自ref10','M0054 M0091 M0092 M0108 M0118 M0142 M0143')
prop(p,'LiPS溶剂化团簇',{'F3DEE':'小','F4DEE':'增大','F4DMB':'再增大','F5DEE':'最大'},'大团簇频次F3DEE<F4DEE<F4DMB<F5DEE','MD','Li2S6/溶剂，不等于含盐工作电解液','M0097 M0098 M0099')
prop(p,'表观离子电导率',{},'DD>DEE>F3DEE≈F4DEE>F5DEE>F4DMB>F6DEE','有隔膜电导测量','RT及60°C','M0104 S0011')
base=dict(sulfur_loading='1–2 mg cm−2；SI具体RT系列1.2–2.8、60°C系列1.2–1.5 mg cm−2',ES=15,ES_unit='μL mg−1',one_C='1675 mAh g−1',LiNO3='DDN 1 wt%；其余无')
t1=test(p,'室温0.05C首放电','Li‖S coin',order[:-1],'M0105 M0175 M0290 M0298 S0018',rate='0.05 C',temperature='RT',**base)
result(t1,'首放电容量','F4DEE','DEE',1160,634,'mAh g−1','0.05 C','M0106 M0107');result(t1,'首放电容量','F4DEE','F5DEE',1160,441,'mAh g−1','0.05 C','M0106 M0108');result(t1,'充电容量','DEE',None,2001,None,'mAh g−1','0.05 C','M0107',same=None)
t2=test(p,'室温50圈循环','Li‖S coin',order[:-1],'M0109 M0162 M0164 M0175 M0298 S0018',rate='0.2 C',formation='0.05 C 2圈+0.1 C 3圈',temperature='RT',**base);result(t2,'50圈平均放电容量','F4DEE',None,651,None,'mAh g−1','含化成的前50圈','M0112 M0164',same=None);result(t2,'平均库仑效率','F4DEE',None,97.6,None,'%','50圈','M0112',same=None);result(t2,'容量保持稳定性','F4DMB/F5DEE','F3DEE/F4DEE','更稳定',None,None,'50圈归一化容量','M0114',basis='qualitative',direction='变好');fig(p,t2,'3B','main','各档0.2C首圈和第50圈容量','F4DEE','DD','化成后首圈、第50圈','M0112',reason='651为50圈均值，须程序核均值作锚点，无法核则不读。')
t3=test(p,'60°C 0.05C首放电','Li‖S coin',order,'M0117 M0118 M0120 M0175 M0298',rate='0.05 C',temperature='60 °C',**base);result(t3,'首放电容量','F4DMB','F6DEE',1563,842,'mAh g−1','首圈','M0118 M0120');result(t3,'首放电容量','DD/DEE',None,'>1200',None,'mAh g−1','首圈','M0117',same=None);result(t3,'充至截止电压','DD/DEE','F6DEE','不能','可以',None,'首次充电','M0117 M0118',basis='qualitative',direction='变坏')
t4=test(p,'60°C 50圈循环','Li‖S coin',['DDN']+order[2:],'M0127 M0128 M0172 M0175 M0298 S0025',rate='0.2 C',formation='0.05 C 2圈+0.1 C 3圈',temperature='60 °C',**base);result(t4,'50圈平均放电容量','F4DMB','DDN',1050,647,'mAh g−1','含化成前50圈','M0131 M0172');result(t4,'50圈平均放电容量','F4DMB','F5DEE',1050,679,'mAh g−1','前50圈','M0131 M0133');result(t4,'平均库仑效率','F4DMB/F5DEE/F6DEE',None,'>98.6',None,'%','50圈','M0135',same=None);fig(p,t4,'3G','main','0.2C首圈及第50圈各档容量','F4DMB','DDN','化成后首圈、第50圈','M0131 M0133',reason='文字锚点为50圈均值；需核均值，不能直接当首圈锚点。')
t5=test(p,'60°C倍率','Li‖S coin',['F4DMB'],'S0027 M0146 M0290 M0298',rate='0.1/0.2/0.4/0.8 C',temperature='60 °C',**base)
for r,v in zip([.1,.2,.4,.8],[1339.4,1070,721.3,438]):result(t5,'倍率容量','F4DMB',None,v,None,'mAh g−1',str(r)+' C','M0146',same=None)
t6=test(p,'Aurbach锂效率','Li‖Cu',order,'M0148 M0193 M0300',rate='0.5 mA cm−2；1 mAh cm−2',temperature='60 °C',formation='9预循环；5 mAh cm−2化成及锂库；10次剥镀');result(t6,'平均锂库仑效率','F3DEE','DD',90.83,96.93,'%','重复Aurbach测量平均','M0149 M0152');result(t6,'平均锂库仑效率','F4DEE/F4DMB/F5DEE','DD','>98',96.93,'%','Aurbach','M0149 M0150');result(t6,'锂效率排序','全梯度',None,'F3DEE<DEE<DD<F6DEE<F4DEE≈F4DMB≈F5DEE',None,None,'Aurbach','M0151',basis='qualitative',same=None)
t7=test(p,'长周期锂效率','Li‖Cu',['F4DMB'],'M0153 M0197 M0299',rate='0.5 mA cm−2；1 mAh cm−2',temperature='60 °C');result(t7,'平均CE','F4DMB',None,97.88,None,'%','200圈','M0153',same=None)
t8=test(p,'饱和LiPS下锂效率','Li‖Cu',['F4DMB','DD'],'M0154 M0155 M0156 S0030 M0299',rate='0.5 mA cm−2；1 mAh cm−2',temperature='60 °C',LiPS='各自饱和');result(t8,'CE','F4DMB','DD','>97',23.7,'%','A100圈平均，B首圈','M0155 M0156',same=False,reason='统计口径不同，不直接比较');result(t8,'循环寿命','F4DMB','DD',100,'<15','cycles','稳定/失效','M0155 M0156')
for name,scontent,ev in [('贫液63%S',63,'M0184 M0185 M0186 M0187'),('贫液67.5%S镍碳花',67.5,'M0188 M0190 M0191 M0202 M0238')]:
 t=test(p,name,'Li‖S coin',['F4DMB','DDN'],ev+' M0290 M0298',sulfur_loading='1–2 mg cm−2（一般方法；该组未独立给数）',ES=5,ES_unit='μL mg−1',rate='0.2 C',formation='0.05 C 2圈+0.1 C 3圈',temperature='60 °C',LiNO3='DDN 1wt%；F4DMB无',one_C='1675 mAh g−1',sulfur_content=str(scontent)+' wt%')
 if scontent==63:
  t9=t;result(t,'平均CE','F4DMB','DDN',99.58,92.07,'%','50圈','M0185 M0186');result(t,'容量保持率','F4DMB','DDN',92.9,75.3,'%','第50圈，相对0.2C首圈','M0187');result(t,'0.2C首圈容量','F4DMB',None,936.5,None,'mAh g−1','化成后首圈','M0187',same=None);fig(p,t,'5A','main','对照首圈/同圈容量','F4DMB','DDN','0.2C首圈、第50圈','M0187')
 else:
  t10=t;result(t,'0.2C首圈容量','F4DMB',None,1054,None,'mAh g−1','化成后首圈','M0191',same=None);result(t,'容量保持率','F4DMB',None,47.4,None,'%','150圈','M0191',same=None);result(t,'平均CE','F4DMB','DDN',99.89,70.6,'%','A150圈；B30圈内','M0190 M0202',same=False);result(t,'稳定循环寿命','F4DMB','DDN',150,'<30','cycles','循环','M0190 M0202');fig(p,t,'5E','main','0.2C首圈和第30圈容量','F4DMB','DDN','化成后首圈、第30圈','M0191')
t11=test(p,'高载量薄锂','Li‖S coin',['F4DMB'],'M0204 M0207 S0037 M0298',sulfur_loading='5.3 mg cm−2',ES=7,ES_unit='μL mg−1',Li_thickness='40 μm',rate='0.1 C',formation='0.05 C',temperature='60 °C',one_C='1675 mAh g−1');result(t11,'化成容量','F4DMB',None,1309,None,'mAh g−1','0.05 C','M0207',same=None);result(t11,'平均CE','F4DMB',None,96,None,'%','20圈0.1 C','M0207',same=None);fig(p,t11,'S15','si','0.1C首圈及末圈容量','F4DMB',None,'首圈、第20圈','M0207',reason='锚点在0.05 C化成，需确认图有该点才能核；勿当0.1 C首圈。')
t12=test(p,'薄锂软包','Li‖S pouch',['F4DMB','DDN'],'M0208 M0209 S0039 M0298',sulfur_loading='4 mg cm−2',Li_thickness='40 μm',rate='0.05 C',temperature='60 °C',one_C='1675 mAh g−1');result(t12,'放电容量','F4DMB','DDN',1175,977.4,'mAh g−1','0.05 C','M0209');result(t12,'CE','F4DMB','DDN',95.3,87.7,'%','0.05 C','M0209')
for es in [5,15]:
 t=test(p,f'30天日历老化 E/S={es}','Li‖S coin',['F4DMB','DDN'],'M0220 M0221 M0229 M0263 M0264 M0266',ES=es,ES_unit='μL mg−1',rate='0.1 C',formation='4圈后第5圈全充静置',temperature='循环60°C；静置RT',LiNO3='DDN 1wt%；F4DMB无',one_C='1675 mAh g−1')
 result(t,'静置后容量变化','F4DMB','DDN',4.3 if es==15 else 6.0,-16 if es==15 else -7.4,'%','30天后第5圈相对第4圈','M0229' if es==15 else 'M0222 M0223');
 if es==5: result(t,'重复电池平均容量变化','F4DMB',None,'4.6±1.3',None,'%','30天','M0225',same=None)
for days,cycle in [(2,5),(7,9)]:
 t=test(p,f'{days}天静置','Li‖S coin',['F4DMB','DDN'],'S0049 S0050 S0051 S0055 S0060 S0061',ES=15,ES_unit='μL mg−1',rate='0.1 C',formation=f'第{cycle}圈全充静置',temperature='循环60°C；静置RT');result(t,'容量变化','F4DMB','DDN','恢复','损失',None,f'{days}天','S0060 S0061',basis='qualitative',direction='变好')
mech(p,'溶解度过低使LiPS供给不足、硫转化缓慢，极化增大且利用率降低','F6DEE','F4DMB','LiPS溶解度',['正极反应'],'M0124 M0133',[t3,t4],side='弱侧')
mech(p,'高溶解度DD/DEE穿梭严重，60°C无法正常充电','DD/DEE','F4DMB','LiPS溶解度',['多硫化物穿梭'],'M0117 M0170',[t3],side='强侧')
mech(p,'溶解度降低提高CE及保持率，来自穿梭抑制','全梯度',None,'LiPS溶解度',['多硫化物穿梭'],'M0114 M0134',[t2,t4],side='强侧')
mech(p,'F3DEE锂CE最低可能源于溶剂反应性高','F3DEE','DD','溶剂反应性',['负极锂'],'M0152',[t6],source='本文推测')
mech(p,'F4DMB无枝晶沉积及合适SEI解释高锂剥镀效率','F4DMB','DD','SEI及锂形貌',['负极锂'],'M0182',[t6,t7])
mech(p,'DDN贫液失效源自耗液或高黏度造成Li+传导失效或短路','DDN','F4DMB','电解液耗尽/黏度',['电解液消耗'],'M0203',[t10],source='本文结论（与他文一致）')
mech(p,'F4DMB抑制S/LiPS溶解迁移，降低长期静置自放电','F4DMB','DDN','S/LiPS溶解度',['多硫化物穿梭'],'M0216 M0217',p['tests'][12:])
mech(p,'静置形成少量Li2S作为后续成核种子，恢复容量','F4DMB','DDN','成核种子',['正极反应'],'M0218 M0219 M0223',p['tests'][12:])
claim(p,'中等溶解度兼顾硫转化与抑制穿梭；RT最优F4DEE，60°C最优F4DMB','M0240 M0243')
p['gaps']=['SI表格多为图片，未把表内引用文献数据当本文数据。','DD溶解度1100 mM引自他文。','DD/DDN中DOL:DME比例在索引文本未给；多数锂厚未给。','F6DEE盐浓度低于其他配方；配方比较同时变化盐浓度。','M0225重复均值与M0223单组结果分别记录；不可混用。']
save(p)
