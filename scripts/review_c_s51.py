from review_c_build import Review
r=Review('S51')
r.group('t1 t2 t3 t4 t5','TP','载硫~1、无添加剂、各倍率/静置/CV及对称Li化成条件与原文一致；原文1C异常单位明确保留，E/S/锂厚未虚填。',['M0062','M0064','M0066','M0067','M0103','M0105','M0114','M0182','M0183'])
r.group('t1r1 t1r2 t1r6 t2r1','SKIP_NONSCORING','1071、约950、0.51及92%单组记录准确，无A/B不能方向计TP。')
r.group('t1r3 t1r4','TP','2M首容量最高、1M最低、3M中等，两个定性比较吻合。',['M0110','M0112','M0113'],['comparisons.4','comparisons.5'])
r.unit('t1r5','TP','3M循环稳定性和CE较1M改善有正文结论支持。',['M0110','M0122','M0196'],['comparisons.8','comparisons.12'])
r.group('t3r1 t3r2','TP','30天OCV保持率96.4/92.7和96.8/96.4准确，程序<5%判差异小；不可与电压降损失口径混同。',['S0014'])
r.group('t3r3 t3r4 t3r5','SKIP_NONSCORING','同配方30天/初始OCV值准确，但不是不同配方方向比较。',['S0014'])
r.unit('t4r1','TP','作者明确1M30天阻抗波动、高盐更稳定，定性界面稳定改善成立。',['M0185','M0186','M0187'],['comparisons.13'])
r.group('m1 m3 m4 m6 m7 m9','TP','各独立因果论断由原句支持，M4/M6推测正确，M9引用他文并应用解释本文形貌。')
r.unit('m2','SKIP_NONSCORING','载流子数量/迁移→电导/传输只是性质因果，未连到正极/穿梭/锂/消耗，移性质。',['M0101'])
r.unit('m5','SKIP_DUPLICATE','高盐极化使初容量下降与M4黏度/电导动力学解释属于同一性能因果链。',['M0117','M0123'])
r.unit('m8','SKIP_DUPLICATE','与M1同为黏度和同离子效应抑LiPS溶解扩散。',['M0099','M0163'])
r.unit('m10','SKIP_DUPLICATE','与M6高盐减少副反应形成稳定SEI同一说法，EIS为补充验证。',['M0135','M0187'])
r.miss('方向','3M较2M循环更稳定：2M虽初容量最高但快速衰减，3M50圈稳定约950。',['M0112','M0113'],['comparisons.7'])
r.miss('方向','3M第二圈0.51V为最大电压滞后，较1M/2M极化更大；单组0.51没有输出作者比较。',['M0119','M0129'],['comparisons.10','comparisons.11'])
r.miss('机制','高盐HOMO升高促进正极氧化，帮助形成正极保护膜。',['M0132','M0133'])
r.miss('机制','高盐正极膜来自TFSI分解及其诱导的AMIm聚合，具体成膜路径尚未提。',['M0155','M0159','M0160','M0161'])
r.out['reference_errors']=[dict(reference_id='comparisons.1-3',reason='旧参考名为容量损失却实际用OCV电压降mV；不是容量损失，需标推算并与OCV保持率区别。',evidence_ids=['M0106','M0108','S0014']),dict(reference_id='conditions.C2',reason='1C=1672是旧参考自行改原文1.672，不能无标注作为直接值。',evidence_ids=['M0067'])]
r.out['suggested_corrections']=['T1-R5循环稳定和CE可拆开，两个原文判断均支持但不人为加倍计分。','补T2电压窗口可关联通用1.6–2.8V方法。']
r.out['figure_triage']=[dict(request_index=1,status='eligible',reason='同测试IL3初容量1071、50圈约950可核，补梯度缺容量侧。',evidence_ids=['M0113']),dict(request_index=2,status='out_of_scope',reason='100圈92%为有效锚点，但仅IL3单配方0.1C，非缺配方对照/梯度档。',evidence_ids=['M0114','M0115'])]
r.save('正文M0001–M0197与SI S0001–S0014完整核读，旧参考13比较3条件逐项核；5测试13结果10机制全部评，剔除单组/性质/重复计分。')
