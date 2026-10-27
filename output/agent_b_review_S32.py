from agent_b_review_common import Review
r=Review('S32')
r.many('T1 T2 T3 T4 T5 T6 T7 T8','TP','所有统一扣式/软包条件、形成步骤、温度、LiNO3及锂厚均与方法吻合；正文容量载量单位及软包1C疑误已明确保留。')
r.u('T1-R1','TP','99.66/99.19同Aurbach平均CE正确，差0.47百分点；不按5%好坏。')
r.many('T1-R2 T1-R3 T1-R4 T1-R5 T2-R1 T2-R2 T2-R3 T2-R4 T3-R1 T3-R2 T3-R3 T3-R4 T3-R5 T4-R1 T4-R2 T4-R3 T4-R4 T4-R5 T4-R6 T4-R7 T4-R8 T4-R9 T4-R10 T4-R11 T4-R12 T4-R15 T4-R17 T4-R18 T5-R1 T5-R2 T5-R3 T5-R4 T6-R2 T6-R4 T6-R6 T6-R8 T7-R2 T7-R3 T8-R4','TP','逐条原文支持各DMFN相对baseline的作者定性；首化成高平台不混作C/5首圈，倍率相近、循环/日历/电极改善及锂库存保持比较均匹配。')
r.many('T4-R13 T4-R14','SKIP_NONSCORING','单组容量/保持率不构成A/B方向。')
r.u('T4-R16','SKIP_ABSTENTION','反应层厚度区间不是精确单值，不据此统一性能判向；形貌改善另有TP。')
r.many('T6-R1 T6-R3 T6-R5 T6-R7','SKIP_ABSTENTION','约8%不能当精确数，整体自放电较小作者定性已由偶数结果覆盖。')
r.u('T6-R9','SKIP_ABSTENTION','5.9%具体DMFN档和baseline追加23.5%统计基准不完全明确，保留不判合理。')
r.many('T7-R1 T8-R1','SKIP_ABSTENTION','当前固定程序未定义比能量/不可逆活性硫损失的单调语义，没有派生方向；作者明确比较另列FN。')
r.many('T8-R2 T8-R3','SKIP_NONSCORING','剩余可逆硫的形态比例是物种库存表征，不可普适以高低直接判性能优劣；相关因果在机制。')
r.many('M1 M2 M3 M4 M5 M6 M7 M10 M11 M12','TP','正文/结论存在同义因果说法；M6未分类仅需修正，M12明确推测保留；不因引句位置或分类不全扣分。')
r.u('M8','SKIP_DUPLICATE','LiPS持续溶解引发副反应、硫损失和衰退与M4/M7同因果，HUG库存提供新证据而非新机制。')
r.u('M9','SKIP_DUPLICATE','抑穿梭减少Li腐蚀并改善循环与M4/M7同因果链，形貌/锂CE为相同链的观察，不重复计。')
r.fn('方向','DMFN盐浓度越高，首化成第一平台容量越低；C/5初始总容量低于baseline且循环CE更高','M0090 M0100 M0103','预测记录逐配方相对baseline高平台和循环稳定性，但缺浓度内趋势、化成后初始总容量及循环CE比较。')
r.fn('方向','DMFN内部0.8M容量最高，1.0M循环稳定性最好且LiCE最高','M0060 M0103 M0118','全部相对baseline已覆盖，内部最佳档位未输出。')
r.fn('方向','软包0.8M-DMFN化成比能量290低于baseline310；100圈后不可逆活性硫损失23.1低于45.3','S0161 S0162 M0136','原数正确但固定程序不识别；原文有明确lower/almost double作者定性待补。')
r.fn('测试及条件','遗漏日历/循环及首化成后硫电极XRD/PDF结构测试','M0175 M0181 M0182 M0183 M0184 M0188 S0174','T4形貌和T8库存不替代XRD/PDF及不同老化阶段。')
r.d['reference_errors']=[dict(reference_id='comparisons[5]',reason='baseline150圈由doubled反推不是原文，不能作为精确寿命；预测保留约两倍正确。',evidence_ids=['M0194']),dict(reference_id='comparisons[13]',reason='5.9%与追加23.5%的具体配方/统计基准有歧义，不能直接同条件5%方向。',evidence_ids=['M0196']),dict(reference_id='C5',reason='1C原文1000mA/cm2疑误需保留，不能未经确认改为质量比电流。',evidence_ids=['S0160'])]
r.d['suggested_corrections']=['M6补适用过程类别即可，不构成FP。','M8/M9因果重复合并到M4/M7，保留新HUG/形貌证据。','S18b软包图主代理处理；40圈后显著极化为同测试数字，可作为候选转折锚再核图，不要求容量精确锚。']
r.d['figure_triage']=[dict(request_index=1,status='eligible',reason='同C/5测试1M 300圈604/81.3%可核，读其余同图梯度容量。',evidence_ids=['M0103']),dict(request_index=2,status='no_numeric_capacity_anchor',reason='3c只有倍率档和突降描述，未给容量、保持率或稳定寿命数字。',evidence_ids=['M0097']),dict(request_index=3,status='no_numeric_capacity_anchor',reason='C/10独立循环图无容量/保持率/寿命数字锚。',evidence_ids=['M0117','S0152']),dict(request_index=4,status='eligible',reason='可用同测试baseline40圈后极化/稳定性转折作为候选数字核验；若图中转折不可明确校验则弃读，C/20能量不能替代C/10容量。主代理处理。',evidence_ids=['M0119'])]
r.finish()
