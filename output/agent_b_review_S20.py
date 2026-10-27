from agent_b_review_common import Review
r=Review('S20')
r.many('T1 T2 T3 T4 T5 T7 T10','TP','方法和图注条件已匹配，正文/SI载量与E/S冲突有保留。T1梯度确为相同0.4M硝酸锂体系，字段应按配方展开。')
for t in ['T6','T8','T9','T11','T12','T13']:
 r.u(t,'FP','配方方法明确CD为0.4M LiNO3、DD为2wt.% LiNO3，本测试未记录；仅T7另明确无添加。','S0010 S0011 S0083')
 r.fn('测试及条件',t+'补CD40 0.4M LiNO3、DD 2wt.% LiNO3（有该组时）','S0010 S0011','同名配方已在方法定义，不能视作未报告。')
r.many('T1-R1 T2-R1 T2-R2 T2-R3 T2-R4 T2-R5 T2-R6 T2-R7 T3-R4 T5-R5 T9-R1 T10-R2 T11-R1 T13-R4','TP','作者明确描述梯度稳定性、倍率、阻抗、形貌、还原稳定性、Li腐蚀或初始容量相近，语义匹配。')
r.many('T3-R1 T3-R3 T5-R2 T5-R3 T5-R4','TP','精确同条件数对正确，固定程序方向符合5%规则。')
r.u('T3-R2','TP','同条件CE99.9/98.1及差1.8百分点准确；只记数值差，不按5%或好坏判定。')
r.many('T4-R1 T5-R1 T12-R1 T12-R2 T12-R3 T13-R1 T13-R2','SKIP_NONSCORING','单组数值，没有A/B方向。')
r.many('T6-R1 T7-R1 T8-R1 T12-R4 T12-R5 T13-R3','SKIP_ABSTENTION','跨条件或界限数不能强作精确数值方向；作者明确的定性另列补漏。')
r.many('T9-R2 T9-R3 T9-R4','SKIP_NONSCORING','XPS硫含量属于组成表征数值，不具有普适单调性能优劣；因果论断已在机制覆盖。')
r.u('T10-R1','SKIP_ABSTENTION','纯溶剂还原电流数对正确但程序未识别指标方向，原文稳定性排序可另列。')
r.many('M1 M2 M3 M4 M5','TP','本篇支持正极富DME动力学、CPME阻挡/保护锂、阴离子SEI及电解液消耗因果链；引句位置和分类不扣分。')
r.many('M6 M7','SKIP_NONSCORING','仅解释LiPS浓度/溶解度引发相分离及物理驱动力，未独立建立四类电化学过程后果；宜归溶剂化/相态性质。')
r.fn('方向','第一平台容量利用率相近，DD第二平台极化快且容量更低','M0088','仅提成核过电位，漏两平台容量的不同趋势。')
r.fn('方向','同CD体系更高载量/薄Li条件导致极化稍增、CE及容量下降','M0097 S0082','原文明示多条件联合比较；可以保留作者定性并标混杂，不能当单变量数值方向。')
r.fn('方向','无LiNO3下CD穿梭电流全窗口<0.05，显著低于DD峰0.26','M0100 M0101','有界数不作精确阈值判断，但作者定性未输出。')
r.fn('方向','CD LiCu稳循环超过100圈优于DD40圈；单层及多层软包寿命亦更长','M0112 M0163 M0164 M0170 M0171','相应结果均写不判，遗漏明示定性；寿命界限不能误精确化。')
r.fn('方向','纯溶剂还原稳定性CPME>DOL>DME，DOL相对DME更稳定','M0133 M0139 S0088','CPME比较已覆盖，DOL/DME剩余一对未输出作者方向。')
r.fn('方向','单层软包CD相对DD具有更缓慢极化增长及更高CE','M0163 M0164 M0165 M0169','不同时间点不算数值方向，但原文明确长期趋势应记录为作者定性。')
r.fn('方向','多层软包初始容量接近时CD因较低电解液密度具有更高能量密度','M0172','预测仅记容量相近和CD单组能量密度，未记作者明确能量比较。')
r.fn('机制','均匀导电SEI及LiPS溶解后较低粘度、较高电导共同降低CD总阻抗','M0091','M4主要论阴离子SEI抑制枝晶，遗漏溶液输运改善阻抗的额外因果。')
r.d['suggested_corrections']=['T1 LiNO3字段应CD0至CD40均0.4M，不应借DD 2wt.%替代CD0。','T6的跨载量/锂厚度比较可单列测试，以免与S12a低载量薄Li循环混在一起。','M6/M7转移到相分离性质解释；保留M7本文推测标签。']
r.d['reference_errors']=[dict(reference_id='C1',reason='SI明确2025型Li-S扣式，参考写2032；非固定评分条件，仅修正。',evidence_ids=['S0039']),dict(reference_id='C2',reason='参考E/S只取7遗漏SI方法6；预测保留两者较稳妥。',evidence_ids=['S0042','S0080'])]
r.d['figure_triage']=[dict(request_index=1,status='no_numeric_capacity_anchor',reason='S6仅单调改善，无该梯度测试容量/保持率/寿命数字。',evidence_ids=['M0081','S0075']),dict(request_index=2,status='eligible',reason='CD各倍率容量可校验。',evidence_ids=['M0084','M0085']),dict(request_index=3,status='eligible',reason='同0.5C组400圈76.7%可校验。',evidence_ids=['M0092']),dict(request_index=4,status='no_numeric_capacity_anchor',reason='S12a薄Li低载量重复组仅图注，无容量/保持率/寿命数；100圈是另一面板电压取样点。',evidence_ids=['S0081','S0082']),dict(request_index=5,status='out_of_scope',reason='LiCu CE不在本轮循环容量图读取范围。',evidence_ids=['S0084']),dict(request_index=6,status='eligible',reason='单层软包808.4初始、170圈851.7以及DD118圈365.7可校验。',evidence_ids=['M0163','M0164'])]
r.finish()
