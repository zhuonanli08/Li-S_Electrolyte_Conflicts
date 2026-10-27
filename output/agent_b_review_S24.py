from agent_b_review_common import Review
r=Review('S24')
r.many('T1 T3 T4 T5 T6 T7 T8 T9 T10 T11 T12 T13 T14 T15 T16','TP','本文方法/图注已核，active material loading 4mg不能不加说明当作各组硫载量；未写倍率/添加剂/锂厚正确保留缺失。')
r.u('T2','FP','25°C仅明确用于恒流充放电及电导，CV未报告温度；本项将其确定为25°C缺依据。','M0173 M0175')
r.fn('测试及条件','T2 CV温度应未报告','M0173 M0175','不将恒流平台条件无依据转给CV。')
r.many('T1-R1 T1-R2 T2-R1 T2-R2','SKIP_ABSTENTION','峰/平台电位不是普适单调优劣，程序保持不判；需保留第一段下降、第二段上升的描述而非统一好坏。')
r.u('T1-R3','SKIP_NONSCORING','平台数2/1是反应路径特征，非性能好坏方向。')
r.many('T2-R3 T4-R2 T5-R1 T7-R1 T8-R1 T13-R1 T13-R2 T14-R1 T14-R2 T14-R3 T15-R1','SKIP_NONSCORING','缺另一配方数值且没有输出定性方向的单组报告，不计方向TP。')
r.many('T3-R1 T3-R2 T11-R1 T12-R1 T16-R1','TP','原文明确MAN过电位更低、低孔隙容量较高、相对AN锂相容性增强。')
r.u('T4-R1','TP','5C容量416/187来自同倍率测试，程序变好正确。')
r.u('T6-R1','FP','MAN1043来自Fig5a，DD1147.5是SI能量密度计算所用容量，未证实同批对照；却same_conditions=true并派生变坏。','M0099 S0033')
r.many('T9-R1 T10-R1','SKIP_ABSTENTION','80/72%孔隙率未给对照数值或明确作者比较，保留不判。')
r.many('M1 M2 M3 M4','TP','四条因果说法均由本文结果/结论支持；G2慢固态转化并非只引言背景，M0071结果明确支持。')
r.fn('测试及条件','遗漏原位Raman正极及隔膜/电解液硫物种演化实验','M0079 M0087 M0089 M0090 M0091 M0093 M0094 M0159 M0160 M0161','机制有利用数据，但独立实验及取样对象未登记。')
r.fn('方向','MAN最佳倍率、G2最差，1C下G2仅85且低于DD/MAN','M0074 M0075 M0076 M0077','T4只MAN/DD5C明确对比，G2仅单组数，漏作者全三配方排序。')
r.fn('方向','E/S低于5时DD容量骤减而MAN保持相近高容量；3和2μL/mg时MAN优于DD','M0099 M0100','T7/T8只有单侧数值没有输出作者明示定性。')
r.fn('方向','MAN的E/S10→2容量基本保持，孔隙率80/72/63容量相近而52%有所降低','M0099 M0103','原文称analogous/regular并给完整梯度原数，但预测未形成梯度内比较。')
r.fn('方向','原位Raman中MAN的电解液LiPS信号显著弱于DD','M0095 M0096','独立同实验定性观察未提结果，M2机制不替代。')
r.d['reference_errors']=[dict(reference_id='C1-C4',reason='active material loading并未明确等于硫载量，4mg应标歧义，不宜确定所有E/S组硫4mg。',evidence_ids=['M0131']),dict(reference_id='C8',reason='167mA/g明确，1C=1675未见本文说明，不可倒推为作者定义。',evidence_ids=['M0174'])]
r.d['suggested_corrections']=['T6-R1解除跨来源同条件数值对，需图5b同图读数验证；1147.5可保留原出处作为能量计算参数。','T2温度不由恒流25°C直接继承；M0131载量歧义保留备注。']
r.d['figure_triage']=[]
for i in range(1,12):
 r.d['figure_triage'].append(dict(request_index=i,status='eligible',reason=('同倍率416/187和G2 85可核，按各自倍率配对。' if i==1 else '同E/S梯度MAN1038/1043/1070/1094可核；重复面板可一次读取覆盖各档。' if i<=5 else '同孔隙梯度MAN1066/1060/1063/958可核；重复面板可一次读取覆盖各档。' if i<=9 else '同循环初始907与50圈72%可核。' if i==10 else '同软包1.13Ah/954及760可核，但高倍率电流原文截断需图注确认。'),evidence_ids=(['M0075','M0077'] if i==1 else ['M0099'] if i<=5 else ['M0103'] if i<=9 else ['M0110'] if i==10 else ['M0113','M0114','M0115'])))
r.finish()
