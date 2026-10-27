from agent_b_review_common import Review
r=Review('S23')
r.many('T1 T2 T4 T5 T6 T7 T8 T9 T10 T14 T15 T16 T17','TP','方法、组别和原文条件匹配；倍率电池类型未明，不从段落位置推定。LiCu/LiLi使用11.13mm不同Li片，厚度未明不强套15.8mm 600μm。')
r.u('T3','FP','15.8mm Li片为标准扣式600μm厚，T3漏记。','S0033 S0047')
r.fn('测试及条件','T3补Li厚600μm','S0033 S0047','同15.8mm标准Li片条件已给。')
for t in ['T11','T12']:
 r.u(t,'FP','高电流测试按同预处理协议，但formation空缺；有LiPS先0.1mA还原，随后各自预沉积/平均CE步骤。','S0102 S0105 S0106 S0107 S0108 S0110')
 r.fn('测试及条件',t+'补有LiPS预还原及对应预沉积/CE预处理','S0102 S0105 S0106 S0107 S0108 S0110','高电流并未取消同protocol。')
r.u('T13','FP','标准扣式穿梭测试遗漏已给的约4mg/cm2通用正极及600μm Li；E/S此组未明确可保留缺失。','S0029 S0033 S0111')
r.fn('测试及条件','T13补约4mg/cm2通用正极及600μm Li','S0029 S0033 S0111','标准扣式方法适用。')
r.many('T1-R1 T1-R2 T1-R3 T1-R4 T1-R5 T1-R6 T1-R7 T4-R1 T5-R1 T6-R1 T6-R2 T7-R2 T9-R1 T9-R2 T15-R7 T16-R2','TP','原文同条件精确数对正确，固定程序5%方向合理；T7稳定段两者约16mV且作者说相同，按定性相近可支持。')
r.many('T1-R8 T3-R4 T4-R2 T4-R3 T5-R2 T13-R1 T15-R5 T15-R6 T17-R6','TP','作者定性充电相近、R1/O斜率不变、早期Li极化/末期阻抗、穿梭、容量反转及软包衰减趋势均匹配。')
r.many('T8-R1 T10-R1 T12-R1','TP','同协议平均CE原数正确，分别差0.33/0.21/0.11百分点，仅计数值差，不按好坏或5%阈值。')
r.many('T2-R1 T2-R2 T2-R3 T3-R1 T3-R2 T3-R3 T7-R1 T7-R4 T9-R4 T14-R1 T14-R2 T15-R2 T16-R1','SKIP_ABSTENTION','当前程序未知指标或区间/界限值不判；有明确作者定性者另列补漏。')
for t,ids in [('T7-R3','M0232 M0233'),('T9-R3','M0237')]:
 r.u(t,'FP','程序将极化突增时间当极化幅值越低越好，错误输出变坏；突增延后表示稳定性改善，且部分数为约数。',ids)
 r.fn('方向',t+'应保留BL+20极化突增延后的作者定性改善',ids,'程序指标关键词混淆时间与幅值；原数本身已提。')
r.many('T15-R1 T15-R3 T15-R4 T17-R1 T17-R2 T17-R3 T17-R4 T17-R5','SKIP_NONSCORING','单配方容量/能量/CE没有A/B方向。')
r.many('M1 M2 M3 M4 M5 M6 M7','TP','本文因果说法获得正文及SI支持；M4/M6不确定性保留，M3有结论段相同实质论断，不因早期提出假说的位置扣分。')
r.fn('测试及条件','遗漏H型池LiPS扩散、LSV、恒电位Raman及软包空间XANES/循环后LiCu SEM测试','M0118 M0119 M0120 M0122 M0123 M0250 M0270 M0273 M0274 M0308 S0082 S0083','这些是实际独立实验与条件；M1/M6机制不能替代测试登记。')
r.fn('方向','活化能随1200ET增加变化较小，R2扩散拟合斜率逐渐下降','M0168 M0169 M0170 M0175','当前数值指标未定义，且作者明确区分电荷转移影响小和扩散变慢。')
r.fn('方向','无LiPS初期BL+20极化更低；有/无LiPS时CE开始下降均更迟，高电流也相同趋势','M0228 M0238 M0239 M0240','区间和圈数未输出作者定性，T11无结果。')
r.fn('方向','Raman中BL+20长链LiPS形成更晚且消失更早，硫还原更慢','M0257 M0258 M0264 M0265','DoD数只是未判单调数字，漏作者明确反应趋势。')
r.fn('方向','单层软包BL+20寿命>200圈优于BL168圈；C/2倍率容量>600优于BL<500','M0317 M0339','界限数不能当精确5%判断，但原文定性可提。')
r.fn('方向','有Li2S6相对无Li2S6降低LiLi/LiCu极化、延缓失效并提高平均CE；两种基底都成立','M0194 M0206 M0213 M0214 M0235 M0236 M0237 M0242 M0243','预测按有/无LiPS分组仅比较BL+20/BL，遗漏LiPS添加梯度本身。')
r.fn('方向','BL+20的H池扩散更慢、LSV氧化稳定性更高、LiCu沉积形貌更完整；BL100圈出现正极退化分峰','M0120 M0123 M0309 M0310 M0311 M0328','独立表征和性能定性未列结果。')
r.fn('机制','高1200ET受限溶剂化造成5–30%DoD热力学放电电位降低和液/准固转化障碍；BL长期正极结构退化损害硫利用','M0151 M0152 M0328','M2只分解动力学极化，M5只说明SEI重构，漏热力学/正极结构两条独有后果。')
r.d['reference_errors']=[dict(reference_id='C3/C4',reason='600μm明确给15.8mm标准扣式Li片；LiLi/LiCu使用11.13mm且未明厚，不宜无说明强套。',evidence_ids=['S0033','S0043','S0045']),dict(reference_id='comparisons[10]',reason='仅凭所在软包段落推定倍率电池为单层软包不充分，S34图注又称MLP；预测留类型不明合理。',evidence_ids=['M0338','S0161','S0163'])]
r.d['suggested_corrections']=['固定程序需区分极化突增时间和极化幅值；保持初轮FP，修正展示另行存档。','T7-R2的16mV及T7-R3、R4/T9-R4的时间圈数保留约号；CE英文缩写应按已批准规则仅记差。','所有扣式静置12h可补非评分操作备注，不当作形成循环；T16对应S34图注称MLP，保留来源冲突。']
r.d['figure_triage']=[dict(request_index=1,status='out_of_scope',reason='LiCu极化/失效时间不在循环容量图范围。',evidence_ids=['M0240']),dict(request_index=2,status='out_of_scope',reason='纯穿梭电流图不在本轮范围。',evidence_ids=['M0249']),dict(request_index=3,status='eligible',reason='同单层软包200圈527及BL168圈寿命可校验。',evidence_ids=['M0053','M0317']),dict(request_index=4,status='eligible',reason='同倍率C/2容量上下界及返回C/5精确值可核。',evidence_ids=['M0339','M0340']),dict(request_index=5,status='eligible',reason='Fig5f本组初始1.53Ah、末662.8及>50圈可核；S35是独立BL图，只能分别核后谨慎并列，不强同批数值。',evidence_ids=['M0345','M0348','M0349'])]
r.finish()
