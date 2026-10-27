from review_c_build import Review
r=Review('S44')
r.group('t1 t2 t3 t4 t5 t6 t7 t8 t9 t11','TP','载量/E/S/锂厚及各自电压窗口、倍率、形成/静置条件与正文SI一致；T3载量未明、T11正文图注冲突均保留。',['M0095','M0096','M0100','M0101','M0102','M0103','M0108','M0113','M0242','M0283','S0011','S0013','S0015'])
r.unit('t10','FP','LiCu稳定性扫描方法明确60µL电解液，预测未记；扫描范围/速率准确。',['M0092','M0093','M0094'])
r.group('t12 t13','SKIP_NONSCORING','同DD电解液只改变正极rGO量，非电解液比较目标；实验记录可保留。',['M0175','M0176','M0178'])
r.group('t1r1 t1r2 t1r3 t2r1 t2r2 t2r3 t2r4 t3r1 t3r2 t3r3 t4r1 t4r2 t5r1 t5r2 t6r1 t6r2 t6r3','SKIP_NONSCORING','原数/约数与所引原文一致，均为单配方记录，无A/B方向不能计方向TP。')
r.unit('t2r5','SKIP_ABSTENTION','两电解液电压窗口与LiNO3条件不同，明确same_conditions=false，不作严格同条件判向合理。',['M0101','M0234'])
r.group('t7r1 t7r2 t7r3 t7r4 t7r5 t8r1 t8r2 t8r3 t8r4 t8r5 t9r1 t9r2 t9r3 t9r4 t9r5','SKIP_ABSTENTION','SI表S2三天数组逐项准确；两体系电压窗口/LiNO3不同，程序不强判方向。',['S0019','M0101'])
r.unit('t10r1','SKIP_NONSCORING','双方稳定至0.5V为界限观测，不是已测完整稳定窗口，也非完整数值优劣比较。',['M0220'])
r.unit('t11r1','SKIP_ABSTENTION','作者称短期行为相近，但20/25圈及C/5/C/10来源冲突已保留，不强判。',['M0242','M0243','M0283','S0011'])
r.group('t12r1 t12r2 t13r1','SKIP_NONSCORING','数值912/687、CE99.7/99.2和倍率趋势准确，正极rGO梯度非电解液方向目标。',['M0177','M0179'])
r.group('m1 m3 m4 m6 m7 m8 m9','TP','本文关于高载量溶解、DOL部分溶解、OCTO抑穿梭、润湿、物种路径、SEI及进一步锂保护的论断有原文支持；推测标记保留。')
r.unit('m2','SKIP_NONSCORING','原记录明确标为转述/通用LiNO3耗尽说法，不能算本文独有机制；本研究具体33圈后过电位解释另补。',['M0189','M0190'])
r.unit('m5','SKIP_NONSCORING','Li迁移受限→电导率低仅为性质来源，没有四类反应过程，移性质。',['M0208','M0209'])
r.miss('测试及条件','LiCu稳定性测试需记录60µL电解液、Celgard2500。',['M0092'])
r.miss('机制','本研究DD在33圈后LiNO3耗尽、锂失保护导致过电位增大；DO首圈至100圈极化近似稳定说明穿梭有效降低。',['M0241'],['comparisons.4'])
r.miss('机制','DD中苔藓锂显示不均匀沉积，LiPS腐蚀可能导致早期失效。',['M0246','M0276'])
r.out['reference_errors']=[dict(reference_id='comparisons.1-8',reason='旧参考把不同电压窗口或添加剂的跨体系结果直接判好坏，按现方案需保留条件差异；自放电也不能默认同条件。',evidence_ids=['M0101','M0074','M0075'])]
r.out['suggested_corrections']=['T10 metric应写扫描中稳定至0.5V的观测界限，不称完整稳定窗口。','rGO正极EIS/CV/循环机制非电解液对象，放补充背景，不计电解液漏项。','作者DO/DD跨窗口的容量与自放电方向可保留为作者描述，不能做严格同条件数值输出。']
r.out['figure_triage']=[dict(request_index=i,status='out_of_scope',reason='虽有同测试容量/寿命锚点，但本请求是单配方补终点，且DD/DO或宽窄窗口条件不同，不属于同条件电解液缺容量侧/梯度档。',evidence_ids=['M0101','M0233','M0274','M0277','M0280']) for i in range(1,5)]
r.save('完整读取正文M0001–M0300和SI S0001–S0019，核旧参考8比较3条件；13测试及全部结果/9机制逐项处理，单组值与跨窗口数值不充作方向TP。正极rGO梯度标非评分。')
