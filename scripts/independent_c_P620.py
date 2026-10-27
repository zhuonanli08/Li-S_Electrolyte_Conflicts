from independent_c_helpers import *
p=init('P620')
form(p,'ELDD','1M LiTFSI in DME/DOL1:1v/v',[('LiTFSI','salt',1,'M'),('DME','solvent',1,'volume ratio'),('DOL','solvent',1,'volume ratio')],'M0059')
form(p,'ELC14','1M LiTFSI in C14',[('LiTFSI','salt',1,'M'),('1,1,1-trifluoro-2-(2-methoxyethoxy)ethane (C14)','solvent','neat','')],'M0060')
for solv in ['DME','C14']:
 for c in [0,.5,1]:
  form(p,solv+str(c),f'{c}M LiTFSI in {solv} spectroscopy model',[('LiTFSI','salt',c,'M'),(solv,'model solvent','neat','')],'M0102 M0103 M0137')
p['control_id']='ELDD';p['control_type']='常规醚基；正文1:1DME/DOL与图注DME表述冲突'
grad(p,'光谱盐浓度',['DME0','DME0.5','DME1','C140','C140.5','C141'],[0,.5,1,0,.5,1],'Rc随盐改变；C14各浓度较低','M0103 M0127 M0131')
prop(p,'Li+螯合/构象',{'ELC14':'更难形成cis/gauche配位，较弱','ELDD':'DME容易变构象螯合'},'C14弱','FTIR/Raman Rc','纯DME/C14模型，勿当DME/DOL量化','M0110 M0115 M0116 M0126 M0131 M0132 M0133')
prop(p,'LiPS溶解/配位',{'C140':'黄色悬液、很低','DME0':'透明红棕、高'},'C14低','照片/FTIR','0.1/0.2M名义Li2Sx纯溶剂','M0177 M0178 M0179 M0183 M0184 M0185 M0186 M0218 M0219')
prop(p,'离子电导率',{'ELC14':.111,'ELDD':1.277},'C14低一数量级以上','正文引用TableS1','S m−1','M0164')
prop(p,'Li迁移数',{'ELC14':.599},'C14较高；对照未给实测数','PFG-NMR自扩散比','电解液','M0062 M0064 M0167')
prop(p,'黏度/密度',{'ELC14':'均高于ELDD'},'C14更高','TableS1正文描述','电解液；SI表不可检索','M0151 M0164')
C={'sulfur_loading':'1.15 mg cm−2','ES':'flooded，具体未报','ES_unit':'未报告','Li_thickness':'未报告','LiNO3':'未添加','one_C':'1672 mA g−1','electrode_area':'1.13 cm2'}
t=test(p,'T1','初始放充','mesoporous C/S||Li',dict(C,rate:='') if False else dict(C,rate='.1 C',voltage='1.0–3.0 V'),['ELC14','ELDD'],'M0072 M0073 M0074 M0134 M0139 M0141 M0143 M0272')
result(t,'放电容量','ELC14','ELDD',1000,1200,'mAh g−1','初始机理分析','numeric','变坏','M0272','作者近似量；对照充电不收敛不能比较完整循环保持')
result(t,'可逆充电/穿梭','ELC14','ELDD','可正常完成','~2.3V无限充电',None,'0.1C','qualitative','变好','M0141 M0142 M0143 M0144 M0162 M0163')
t=test(p,'T2','C14循环','mesoporous C/S||Li',dict(C,rate='.1 C，Fig2；S3是否同倍率需核图'),['ELC14'],'M0139 M0161 M0171')
result(t,'容量趋势','ELC14',None,'逐渐衰减',None,None,'50cycles','qualitative','不判','M0171')
result(t,'库仑效率','ELC14',None,'approximately106',None,'% (charge/discharge)','稳定阶段','numeric','不判','M0161 M0171 M0172','作者定义与通常放/充相反，不能直接越高越好')
t=test(p,'T3','C14倍率','mesoporous C/S||Li',C,['ELC14'],'M0161 M0166')
result(t,'倍率可逆容量','ELC14',None,'升倍率仍保持显著容量',None,None,'FigS3','qualitative','不判','M0166','具体倍率/数值在图，未目测')
for sm,A,B,pr,cats,ty,e,ts,side in [
('CF3吸电子使表面电荷离域，位阻限制cis螯合，阻止LiPS中Li+被抽取电离，减少溶出与穿梭','ELC14','ELDD','LiPS溶剂化/电离',['多硫化物穿梭'],'本文结论','M0197 M0198 M0199 M0266 M0267 M0268 M0269 M0287',['T1','T2'],'弱侧'),
('抑制LiPS溶解使反应中间态更少，dQdV更尖锐、反应更均一','ELC14','ELDD','LiPS溶解',['正极反应'],'本文结论','M0157 M0158 M0159 M0160',['T1'],'弱侧'),
('高Li迁移数缓和浓差极化，补偿低总体电导，支持倍率','ELC14','ELDD','Li迁移数',['正极反应'],'本文结论','M0164 M0165 M0166 M0167 M0169 M0170',['T3'],'其他'),
('强烈限制溶解迫使迟缓固相转化，结合残余穿梭或氧化分解，可能造成容量衰减','ELC14',None,'LiPS溶解/副反应',['正极反应','多硫化物穿梭','电解液消耗'],'本文推测','M0171 M0172 M0173 M0174',['T2'],'弱侧'),
('低LiPS溶出减少跨界迁移和锂表面寄生沉积，锂侧硫浓度低','ELC14','ELDD','LiPS溶解',['多硫化物穿梭','负极锂'],'本文结论','M0240 M0241 M0247 M0248',['T1'],'弱侧'),
('C14正极50%DOD无ELDD纳米沉淀，体现较少电解液盐分解','ELC14','ELDD','界面稳定性',['正极反应','电解液消耗'],'本文结论','M0205 M0206 M0207',['T1'],'其他'),
('颗粒内部未反应硫及表面优先反应限制两体系的实际容量','ELC14','ELDD','体相可及性',['正极反应'],'本文结论','M0270 M0271 M0272',['T1'],'其他'),
('抑制溶解减少持续电解液消耗，理论上支持未来降低E/S','ELC14','ELDD','LiPS溶解',['电解液消耗'],'本文推测','M0152 M0153 M0154',[],'弱侧')]:
 mech(p,sm,A,B,pr,cats,ty,e,ts,side)
claim(p,'分子电荷离域/构象限制抑制LiPS电离，同时保持1M LiTFSI溶解与适合加工沸点','M0047 M0287 M0288')
fig(p,'T2','FigS3(a)','si','循环容量','ELC14',None,'初始与50圈','M0272 M0171','需验证1000容量锚可匹配SI同批；不匹配则不可补整图')
p['gaps']=['SI文本仅9条，表S1和多数图为图像；未目测，黏度/密度数值未获。','ELDD配制为DME/DOL1:1，Fig2注只写DME；不能擅自统一。','循环CE按charge/discharge定义，106%提示副反应，禁止作为常规高CE优点。','无Li半电池测试；Li侧XPS来自全电池。','洪液具体体积/E-S、Li厚度、活化、倍率程序未文字报告。']
p['source_review']['notes']='完整通读正文及全部SI文本索引；SI仅可检索9条，多数图表是图片，留缺口；未读旧提取或参考答案。'
save(p)

