from agent_b_common import *
p=paper('P149','LS002','常规DOL/DME电解液')
form(p,'LS002','1 M LiTFSI DOL/DME +1 wt% LiNO3',[('LiTFSI','盐',1,'M'),('DOL','溶剂',1,'体积比'),('DME','溶剂',1,'体积比'),('LiNO3','添加剂',1,'wt%')],'M0044 M0169')
form(p,'DME2','2 M LiTFSI DME +0.1 M LiNO3',[('LiTFSI','盐',2,'M'),('DME','溶剂',1,'溶剂'),('LiNO3','添加剂',.1,'M')],'M0041 M0170')
form(p,'TDE','TTE:2 M LiTFSI/DME=4:1',[('LiTFSI','盐','约0.4','M'),('DME','溶剂',1,'体积比'),('TTE','稀释剂',4,'体积比'),('LiNO3','添加剂','约0.025','M')],'M0037 M0043 M0170')
form(p,'TDE0','TDE无LiNO3',[('LiTFSI','盐','约0.4','M'),('DME','溶剂',1,'体积比'),('TTE','稀释剂',4,'体积比')],'S0047 S0049')
for c in [.5,1,1.5,4,5,6]:form(p,'D'+str(c),f'{c} M LiTFSI/DME（Raman样）',[('LiTFSI','盐',c,'M'),('DME','溶剂',None,None)],'M0059 S0009')
grad(p,'DME盐浓度Raman',['D0.5','D1','D1.5','DME2','D4','D5','D6'],[.5,1,1.5,2,4,5,6],'Li–O相互作用增强','M0046 M0059 S0009')
prop(p,'黏度',{'TDE':1.091,'DME2':'更高','LS002':'更高'},'TDE较低','黏度','25 °C','M0044 M0059')
prop(p,'电导率',{'TDE':.990,'DME2':'稍高','LS002':'稍高'},'TDE稍低','SS||SS EIS','室温；mS cm-1','M0052 M0191')
prop(p,'Li迁移数',{'TDE':'约0.4842'},None,'Bruce–Vincent–Evans','Li||Li','M0054 M0192 M0193')
prop(p,'Li+溶剂化与离子对',{'TDE':'TTE几乎不结合Li+；接触离子对','DME2':'自由TFSI峰'},'加TTE增强DME/Li/TFSI相互作用','Raman','电解液','M0047 M0049 M0050 M0051')
prop(p,'多硫化物溶解性',{'TDE':'较低','LS002':'较高'},'TDE降低','透明电池+UV–Vis','0.1 C至1.8 V','M0063 M0064 M0065 M0066')
c=dict(sulfur_loading='约1.2 mg cm-2',rate='0.5 C',temperature='ambient',LiNO3='TDE约0.025 M；LS002 1 wt%',one_C='1675 mA gS-1（理论容量定义）',voltage='1.8–2.8 V')
t=test(p,'裸硫普通隔膜循环',['TDE','LS002'],'M0109 M0111 M0112 M0172 M0174',separator='无碳涂层',**c)
result(t,'放电容量','TDE','LS002','约200','较高','mAh g-1','0.5 C','M0111',basis='qualitative',direction='变坏',reason='原文定性比较')
result(t,'循环稳定性','TDE','LS002','900圈几乎不变',None,None,'900圈','M0112',basis='qualitative',reason='只有TDE稳定性描述')
t2=test(p,'裸硫碳涂层隔膜循环',['TDE','LS002'],'M0114 M0115 M0118 M0121 M0122 M0134',separator='10 μm碳涂层CS',**c)
result(t2,'首圈放电容量','TDE','LS002',903,'稍高','mAh g-1','首圈','M0115 M0118',basis='qualitative',direction='变坏',reason='LS002无原文数值')
result(t2,'容量保持率','TDE','LS002',49.4,23.7,'%','1000圈','M0122')
result(t2,'容量保持率','TDE',None,83.6,None,'%','200圈','M0160')
fig(p,t2,'Fig.6a','放电容量','TDE','LS002','200/1000圈','M0115 M0122 M0160')
t3=test(p,'高温碳涂层隔膜循环',['TDE','LS002'],'M0134 M0145 M0146 M0147',separator='CS',**dict(c,temperature='60 °C',rate='0.1 C'))
result(t3,'首圈放电容量','TDE','LS002',1557,1671.5,'mAh g-1','首圈','M0146 M0147')
result(t3,'放电容量','TDE','LS002',870,'迅速下降','mAh g-1','100圈','M0146 M0147',basis='qualitative',reason='对照无100圈数值')
fig(p,t3,'Fig.6e','放电容量','TDE','LS002','100圈','M0146 M0147')
t4=test(p,'高载硫碳涂层隔膜循环',['TDE','LS002'],'M0135 M0154 M0155 M0156',separator='CS',**dict(c,sulfur_loading='约4 / >4 mg cm-2',temperature='25 °C',rate='0.02 C'))
result(t4,'首圈放电容量','TDE','LS002',1187,1223.9,'mAh g-1','首圈','M0155 M0156')
result(t4,'放电容量','TDE',None,806,None,'mAh g-1','56圈','M0155')
result(t4,'放电容量','TDE',None,820,None,'mAh g-1','42圈（SI表）','S0027')
result(t4,'库仑效率','TDE','LS002','>97','约80.6–93.8','%','循环范围','M0155 M0156',basis='qualitative',direction='变好',reason='范围而非同圈数值')
fig(p,t4,'Fig.6h','放电容量','TDE','LS002','56圈','M0155 M0156')
t5=test(p,'倍率能力',['TDE'],'M0143 M0144',separator='CS',**dict(c,sulfur_loading='1 mg cm-2（倍率换算处）',rate='至4 C后回0.5 C'))
result(t5,'放电容量','TDE',None,350,None,'mAh g-1','4 C','M0143')
result(t5,'恢复容量','TDE',None,'约900',None,'mAh g-1','恢复0.5 C','M0144')
t6=test(p,'自放电静置',['TDE','LS002'],'M0140 M0141 S0014',separator='CS',**dict(c,rate='充至2.8 V后静置72 h'))
result(t6,'静置开路电压','TDE','LS002','约2.3，稳定','2.35降至2.15','V','72 h','M0140 M0141',basis='qualitative',direction='变好',reason='对照末值不是容量')
t7=test(p,'CV',['TDE','LS002'],'M0131 M0188 M0189',separator='TDE配CS；对照隔膜措辞不完整',**dict(c,rate='0.1 mV s-1'))
result(t7,'峰间距','TDE','LS002',.239,'较大','V','CV','M0131',basis='qualitative',direction='变好',same=None,reason='对照CS条件须图核实')
t8=test(p,'EIS随循环',['TDE'],'M0132 M0133 M0138',separator='CS',**c)
result(t8,'阻抗','TDE',None,'第二圈最高，后降低并稳定至600圈',None,None,'2–600圈','M0133',basis='qualitative',reason='单配方时间演化')
t9=test(p,'Li对称低电流',['TDE','LS002'],'M0010 M0069 M0086',cell='Li||Li',rate='1 mA cm-2 / 1 mAh cm-2',temperature='室温',LiNO3=c['LiNO3'])
result(t9,'稳定时间','TDE','LS002','>2500','>2500','h','恒流循环','M0069')
result(t9,'过电位','TDE','LS002','<10','更高','mV','2500 h内','M0010 M0069',basis='qualitative',direction='变好',reason='对照无数值')
t10=test(p,'Li对称高电流',['TDE','LS002'],'M0068 M0086',cell='Li||Li',rate='2.5 mA cm-2 / 5 mAh cm-2')
result(t10,'过电位','TDE','LS002','归属不明30或>50','归属不明30或>50','mV','Fig.3a–c','M0068',basis='qualitative',same=None,reason='原句两次写LS002，不能自行修正归属')
t11=test(p,'LiCu效率',['TDE','LS002'],'M0070 M0071 M0075 M0076 M0077',cell='Li||Cu',rate='0.1 mA cm-2 / 0.1 mAh cm-2')
result(t11,'平均库仑效率','TDE','LS002',95.1,'波动且快速降低','%','10–45圈','M0075 M0076',basis='qualitative',direction='变好',reason='对照无数字')
result(t11,'极化电压','TDE',None,'1.0621→0.0406',None,'V','首圈→40圈','M0077',basis='numeric',reason='单配方时间变化，不作配方比较')
t12=test(p,'无硝酸锂Li对称',['TDE0'],'S0047 S0049',cell='Li||Li',LiNO3='无')
result(t12,'电压稳定性','TDE0',None,'稳定几乎不变',None,None,'循环过程','S0049',basis='qualitative')
t13=test(p,'60度Li对称',['TDE','LS002'],'S0057 S0058 S0059',cell='Li||Li',temperature='60 °C')
result(t13,'过电位','60 °C','室温','更低','较高',None,'Li对称循环','S0059',basis='qualitative',same=False,reason='跨温度比较，不作配方方向')
for sm,pr,cat,ids,ts,src in [
('TDE低多硫化物溶剂化能力降低硫利用率。','多硫化物溶剂化','正极反应','M0111',[t],'本文结论（与他文一致）'),
('加CS后更快多硫化物反应动力学提高容量。','反应动力学','正极反应','M0116',[t2],'本文结论'),
('加速高阶到不溶低阶多硫化物转化避免电解液饱和，维持溶解能力并提高利用率。','转化/饱和','正极反应','M0117',[t2],'本文结论'),
('LS002过量溶解多硫化物穿过碳涂层到锂负极，造成快速衰减。','高溶解性','多硫化物穿梭 负极锂','M0123',[t2],'本文结论'),
('TDE弱溶解性结合碳涂层进一步抑制穿梭。','弱溶解性','多硫化物穿梭','M0124',[t2],'本文结论'),
('TDE帮助形成无枝晶锂界面，提高电池稳定性。','锂界面','负极锂','M0125',[t2],'本文结论'),
('TDE减低多硫化物溶解性，抑制自放电。','溶解性','多硫化物穿梭','M0142',[t6],'本文结论'),
('高温常规电解液与锂更易反应，持续耗液及严重穿梭造成快速容量下降。','高温反应','负极锂 电解液消耗 多硫化物穿梭','M0150',[t3],'本文结论'),
('TDE分解形成刚柔结合富LiF SEI，抑制形貌不稳定。','SEI','负极锂','M0092',[t9],'本文结论（与他文一致）'),
('致密锂沉积减少死锂并改善锂负极长期稳定性。','致密沉积','负极锂','M0098',[t9],'本文结论'),
('LS002多孔破碎锂表面放大界面副反应，导致不稳SEI及持续电解液消耗。','锂表面','负极锂 电解液消耗','M0079',[t9],'本文结论'),
('HOMO/LUMO与浸泡后XPS证实TTE参与SEI形成。','TTE成膜','负极锂','S0046',[t9],'本文结论'),
('少量硝酸锂分解可导致初期电压变化。','添加剂分解','负极锂','S0053',[t9],'本文推测'),
('LiNO3初期还原产物以及可能的Li3N快离子导体降低界面阻抗。','含氮SEI','负极锂','S0054',[t9],'本文推测')]:mech(p,sm,'TDE','LS002',pr,cat,ids,ts,source=src)
p['design_claims']=[{'summary':'80%以上TTE阻燃但导电率随TTE增大降低，选4:1折中。','evidence_ids':['M0043']}]
p['gaps']=['E/S、电解液注液量、锂厚度未报告。','M0068将两种高电流过电位都归LS002，保留歧义。','SI表S1把DME/TTE体积比写4:1，与正文制备相反，采用正文TTE:DME=4:1。','LiNO3稀释计算0.1/5=0.02 M，与作者约0.025 M有差异；保留作者数值。','TTE体积分数阻燃梯度仅图中，未列全量。']
save(p)
