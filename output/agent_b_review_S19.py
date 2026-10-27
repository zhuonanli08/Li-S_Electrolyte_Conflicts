from agent_b_review_common import Review
r=Review('S19')
r.many('T1 T3 T4 T5 T6 T7 T8 T9 T10 T12 T13 T14','TP','正文与SI测试条件相符；锂厚度仅采购材料给400/50μm未分配到各扣式组，不猜。1C定义仅GITT段出现，CNT/S组留未报告可接受。')
for t in ['T2','T11','T15']:
 r.u(t,'FP','SI统一说明LMA先预保护形成人工SEI，本项formation误作未报告。','S0035')
 r.fn('测试及条件',t+'应保留Li金属预保护人工SEI步骤','S0035','统一电化学方法已明示，非由前文具体配方推测。')
r.many('T1-R1 T1-R2','SKIP_ABSTENTION','>1400与约800/1000不是精确成对标量，程序未判；原文仍有明确稳定性定性。')
r.many('T1-R3 T1-R4 T3-R3 T3-R4 T4-R1 T4-R2 T5-R3 T5-R6 T6-R1 T6-R2 T6-R3 T6-R4 T6-R5 T6-R6 T6-R7 T6-R8 T6-R9 T6-R10 T7-R1 T7-R2','TP','原文明确同测试形貌、溶解容量、循环稳定性或倍率容量优于对应对照，作者定性与A/B一致。')
r.many('T2-R1 T2-R2 T10-R1 T10-R2','SKIP_ABSTENTION','精确数对已存，但当前固定程序未定义该指标单调性；没有输出原文的定性方向。')
r.many('T3-R1 T3-R2 T5-R1 T5-R2 T5-R4 T5-R5 T11-R1 T11-R2 T13-R2','TP','同条件精确容量/穿梭电流/保持率数对准确，固定程序派生方向符合5%规则。')
r.many('T5-R7 T8-R1 T8-R2 T9-R1 T9-R2 T12-R1 T12-R2 T13-R1 T14-R1 T14-R2 T14-R3 T15-R1 T15-R2 T15-R3','SKIP_NONSCORING','单配方单组值，不是A/B方向断言；原文明确对比而另缺的方向单列FN。')
r.many('M1 M2 M3 M4 M5 M6','TP','本篇正文/SI支持所述因果链；按因果说法整体匹配，分类或引用位置不另扣分。')
r.fn('测试及条件','遗漏Li||Li2S6 GITT及不同放充电阶段EIS/SEM测试','S0043 S0045 S0091 S0093 S0122 S0129 S0132','0.1C、15min放电/1h静置及各阶段阻抗均实际测试；T3仅CA不能替代。')
r.fn('方向','Li对称：PDD稳定超过1400h优于EDD约800h、DD约1000h；EDD较DD差','M0081 M0082 M0083 M0084','保留原文寿命定性，不能将界限自动当精确数；第三对照关系亦漏。')
r.fn('方向','PDD交换电流0.52高于EDD0.42与DD0.12，传输动力学更快','M0087','当前未输出作者明确方向，建议程序指标扩充后复核。')
r.fn('方向','PDD穿梭常数0.039低于EDD0.079与DD0.128，穿梭受抑制','S0139','数值已提但当前方向未输出；不要仅因模型待复算扣分，具体缺在程序指标识别。')
r.fn('方向','1C循环PDD明显优于EDD/DD；2.1mg CNT/S组100圈容量及极化更优','M0116 M0120 M0121','预测相应T9/T12仅存单组数值，漏作者明确同组比较。')
r.fn('方向','1C下PDD仍有明显低平台容量，而DD严重极化/低平台容量很低','M0113','倍率总容量已覆盖，低平台极化差异为独立指标。')
r.fn('方向','不同反应阶段PDD保持低阻抗，EDD中等阻抗、DD提前钝化','S0125 S0126 S0127 S0130 S0133','遗漏分阶段阻抗观察，不能仅用沉积形貌替代。')
r.fn('机制','多孔Li2S结构促进充电时固体Li2S向液态LiPSs及S的可逆转化','S0121 S0128','M1主要覆盖放电沉积/硫利用，未提充电逆向转化的独有论断。')
r.d['reference_errors']=[dict(reference_id='comparisons[6:9]',reason='Li对称1400为下界、800/1000为约数，不可视作精确寿命或以5%数值阈值强判；作者定性仍成立。',evidence_ids=['M0081','M0083','M0084'])]
r.d['suggested_corrections']=['T1-R1/R2的800、1000补近似符号；M0089原文称-3.1低于-3.7属于文字算术错误，机制结论应依反应自由能较不负/反应性较低解释，预测未照抄错误。','建议为穿梭常数、交换电流密度补固定程序指标语义；冻结数值本身正确。']
r.d['figure_triage']=[dict(request_index=1,status='out_of_scope',reason='Li2S恒电位溶解容量不属当前循环容量缺侧/梯度读图范围；956可作锚点但本轮不读。',evidence_ids=['S0121']),dict(request_index=2,status='eligible',reason='同倍率测试PDD五档容量可校验。',evidence_ids=['M0112']),dict(request_index=3,status='no_numeric_capacity_anchor',reason='仅50圈后SEM取样与循环图题，未提供该0.3C循环容量、保持率或稳定寿命数字。',evidence_ids=['M0100','S0144','S0145']),dict(request_index=4,status='eligible',reason='同0.5C组1106容量、90圈92%可校验。',evidence_ids=['M0115']),dict(request_index=5,status='eligible',reason='同1C组1097容量、70圈76%可校验。',evidence_ids=['M0116']),dict(request_index=6,status='eligible',reason='同CNT/S组初始1107及100圈848可校验。',evidence_ids=['M0120'])]
r.finish()
