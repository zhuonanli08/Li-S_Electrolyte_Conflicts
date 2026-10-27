from agent_b_review_common import Review
r=Review('S25')
r.many('T1 T2 T3 T4 T5 T6 T7 T8 T9 T10 T11 T12 T14 T15 T16 T17','TP','逐项核正文与SI，配方0.2M LiNO3、LiPS浓度、形成步骤/高温/载量匹配；锂厚和图上未列温度不猜。')
r.u('T13','FP','高载量倍率组3.5mg应依统一方法先C/30放电和C/20化成，formation未报告遗漏。','S0018 M0192')
r.fn('测试及条件','T13补C/30初次放电及C/20形成','S0018 M0192','高载量通用方法没有排除倍率测试。')
r.many('T1-R1 T1-R2 T1-R3 T3-R2 T5-R4 T6-R2 T7-R1 T7-R2 T8-R1 T8-R2 T13-R3 T14-R4 T17-R1 T17-R2','TP','原文明确作者定性，MSE整体/最优MtBE、动力学相反指标及电极形貌均语义吻合。')
r.many('T2-R1 T14-R2 T14-R3','TP','同条件CE原数正确，差1.5/41.2/5.2百分点；只记录数值差，不用5%或好坏阈值。')
r.many('T5-R1 T5-R2 T5-R3 T6-R1 T10-R2 T10-R3 T11-R1 T11-R2 T13-R1 T14-R1','TP','同测试精确数对与指标正确，程序5%派生方向合理。')
r.u('T4-R1','FP','原文两电流均为约数∼0.013/∼0.047，提取丢近似号并走精确5%判向；应保留作者抑制穿梭定性。','M0122 M0123')
r.fn('方向','MtBE穿梭电流约0.013低于DD约0.047，作者明确抑制穿梭','M0122 M0123','修正近似性，不应伪作精确阈值数对。')
r.many('T3-R1 T13-R2','SKIP_ABSTENTION','界限/近似数不强行5%判断，作者有明确优越趋势另列。')
r.many('T9-R1 T10-R1 T12-R1 T12-R2 T12-R3 T15-R1 T16-R1','SKIP_NONSCORING','物相演化没有普适优劣，其他为单组容量无方向对照。')
r.many('M1 M2 M3 M4 M5 M6 M7','TP','七条因果实质均由本篇支持；M3–6推测程度保留，M7正负极相同氧化硫物种作用相反已涵盖。')
r.fn('方向','Aurbach筛选MtBE的CE最高，优于其余MSE；LiLi寿命>600h优于DD400h','M0095 M0097','T2仅MtBE/DD数值、T3寿命不判，遗漏作者明示梯度和界限寿命定性。')
r.fn('方向','MtBE各倍率容量都更高更稳定，返回C/5仍明显较高；除C/2成核下凹外过电位相近','M0180 M0181 M0182 M0183','T13仅C/2精确容量和成核变坏，遗漏其他倍率定性及多数过电位相近。')
r.fn('方向','75%DoD前MtBE浓差极化通常稍大，与25%峰值较低/末期较低并存','M0134 M0135 M0137','预测仅峰值和末期改善，遗漏方向随DOD变化的例外。')
r.fn('机制','45°C下DD更高LiPS溶解、更快迁移及Li反应引发严重穿梭，使化成充电达不到2.8V','M0186 M0194','一般M2降低穿梭未覆盖温度触发、化成无法达到截止电压的独有因果。')
r.fn('机制','DD正极氧化硫副产物可能来自电解液分解/硫反应或电极串扰，拖慢离子扩散','M0229 M0230 M0231','M7只概括减少有害氧化物，漏其来源与电解液消耗/串扰路径。')
r.d['reference_errors']=[dict(reference_id='comparisons[6]/[9]',reason='905.6及809.2来自末容量/保持率倒推并非原句，必须标明公式与舍入；不视作漏掉原文数。',evidence_ids=['M0173','M0174','M0177']),dict(reference_id='comparisons[18]',reason='穿梭电流原文为近似值，不能将0.013/0.047记为精确数。',evidence_ids=['M0122','M0123'])]
r.d['suggested_corrections']=['T4近似电流恢复约号并保留作者定性；S24的CV25°C等温度应仅由对应测试来源确认，不无依据外推。','T1-R3拆保留MSE总体活化能相近与MtBE最低，当前摘要已有两层信息不另扣分。']
r.d['figure_triage']=[dict(request_index=1,status='out_of_scope',reason='活化能/交换电流不在本轮缺失循环容量读图范围。',evidence_ids=['M0079','M0090']),dict(request_index=2,status='out_of_scope',reason='LiNi CE不在本轮图读取范围。',evidence_ids=['M0095']),dict(request_index=3,status='out_of_scope',reason='纯活化能不在本轮图读取范围。',evidence_ids=['M0151']),dict(request_index=4,status='eligible',reason='同倍率C/2 781/700及返回C/5约850/<700可核。',evidence_ids=['M0180','M0181','M0182'])]
r.finish()
