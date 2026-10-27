from review_c_build import Review
r=Review('S39')
r.group('t1 t2 t4 t8 t9 t10 t11 t12','TP','Li-S/LiCu独立测试、倍率、载硫、E/S、锂厚和LiNO3梯度与方法及SI对应；高载硫/低E/S/软包分别建测试。')
r.group('t3 t5','FP','方法明确LiCu/LiCP每电池50µL电解液，预测未记录；LiCP另需明确0.1M Li2S6初始正极液。其余电流/步长正确。',['S0016','S0044'],['conditions.C1','conditions.C2'])
r.group('t6 t7','FP','同一LiCP装配方法中Li片200µm、50µL电解液已有来源，预测把锂厚写未报告并遗漏体积。',['S0009','S0043','S0044','S0045','S0046'])
r.unit('t1r1','SKIP_ABSTENTION','>180与55不是同容量保持阈值且含下界，程序不判；作者延寿定性可另补。',['M0149','M0159'],['comparisons.5'])
r.unit('t1r2','SKIP_ABSTENTION','循环首圈容量仅在图上；未挪用GITT容量，待图核。')
r.unit('t1r3','TP','TTE缓慢激活及过电位恢复、F4DEE充分反应有作者判断。',['M0146','M0157','S0264','S0265'])
r.group('t2r1 t2r2 t2r3','TP','100圈后Rct/RSEI/Rbulk对比有正文明确描述。',['M0160','M0161','M0162','M0163'],['comparisons.6','comparisons.7'])
r.unit('t3r1','SKIP_ABSTENTION','只有F4DEE98.25%，B缺失不能算精确CE差；作者highest定性未输出。',['M0070','M0071'],['comparisons.1'])
r.unit('t3r2','TP','均<20mV不构成精确比较，但作者明确similarly low，定性差异小成立。',['S0160','S0162'])
r.unit('t4r1','TP','图内文字93.30/92.23%配对准确，百分点差1.07，不套5%。',['S0130','S0131','S0138'])
r.unit('t4r2','TP','图内明确DOL/DME40圈内roll-over，较F4DEE衰退成立。',['S0138'])
r.group('t5r1 t5r2 t5r3','TP','首次GITT500/900、400/500、650/650原数配对准确，程序分别坏/坏/差异小。',['M0094','M0095'],['comparisons.2','comparisons.3'])
r.group('t5r4 t5r5 t5r6','TP','首次GITT跨配方过电位相似、IV段DME最高、V段容量相近为作者明示。',['M0097','M0100','M0109','M0110'])
r.unit('t6r1','TP','第二次GITT II段DME>F4DEE>TTE，F4DEE较DME低正确。',['S0213'])
r.group('t7r1 t7r2','TP','70%DOD的177.7/246.7/314.7mV与0.4/0.2/0.1M对应正确，较低浓差极化程序判好。',['M0127','M0134'])
r.group('t8r1 t8r2','TP','LiCS GITT中DME容量最高，F4DEE比TTE极化低，未混同循环。',['M0139','M0140','M0141'],['comparisons.4'])
r.group('t9r1 t9r2 t9r3 t9r4','TP','0.2M LiNO3容量及寿命优于0.1/0.36M为SI明确判断。',['S0250','S0251'])
r.group('m1 m2 m3 m4 m6 m7 m8 m9 m10 m13 m14 m15 m16','TP','因果说法与所引正文/SI及上下文一致；M15保留干涸推测。侧别/配方挂接或类别过标只需修正。')
r.unit('m5','SKIP_DUPLICATE','容量寿命权衡是M6/M7已述因果的概括。',['M0116','M0117','M0118'])
r.unit('m11','SKIP_DUPLICATE','总括重复M1/M4负极稳定与M8中等溶解度维持动力学。',['M0158'])
r.unit('m12','SKIP_DUPLICATE','与M9同为TTE低溶解度使容量/极化恶化，慢激活证据合并。',['M0147','M0157','S0265'])
for cat,desc,ev,ref in [
('测试及条件','LiCu Aurbach需记50µL电解液。',['S0016'],['conditions.C1']),
('测试及条件','各LiCP GITT需记50µL、200µmLi；首次/第二次含0.1M Li2S6，浓度系列逐档标。',['S0009','S0044','S0045','S0046'],['conditions.C2']),
('测试及条件','25天Li浸泡TGC：1mL 0.1M Li2S6，DOL/DME、F4DEE、TTE。',['S0036','S0170'],['conditions.C4']),
('方向','浸泡25天弱LiPS溶剂化的Li库存损失更低；M14机制已提，测试/结果未提。',['S0177','S0178'],['comparisons.8']),
('方向','作者定性F4DEE寿命长于DME；>180与55不作同阈值精确比。',['M0149','M0159'],['comparisons.5']),
('方向','Aurbach作者明确F4DEE CE最高98.25%；无对照数只能保留定性。',['M0070','M0071'],['comparisons.1']),
('方向','首次GITT III段TTE亦为650，与另两组相近。',['M0095'],[]),
('方向','第二GITT II段TTE容量低于F4DEE。',['S0213'],[]),
('方向','同溶剂更高LiPS浓度时GITT充电过电位也下降。',['M0123'],[]),
('方向','同溶剂提高LiPS浓度使GITT比容量下降。',['M0121'],[]),
('机制','强LiPS溶剂化使LiPS→S8氧化迟滞，加快LiNO3不可逆消耗，不利长循环。',['M0115'],[]),
('机制','CP初次缺S8故无stageI；充电产生S8使第二次出现stageI。',['S0186','S0188','S0197','S0198'],[]),
('机制','C/S绝缘S8/Li2S遮蔽位点引起极化；新鲜CP位点多可促进1.8V Li2S沉积。',['M0090','S0192','S0193','S0194','S0195'],[]),
('机制','第二次CP残留死Li2S绝缘钝化位点，阻碍stageIII还原并削弱平台。',['S0199','S0200','S0201'],[]),
('机制','较高LiPS浓度使比容量下降可能因CP表面反应位点有限。',['M0121'],[]),
('机制','相近低Li界面过电位说明界面动力学对锂剥镀差异贡献可忽略。',['S0158','S0162'],[])]:r.miss(cat,desc,ev,ref)
r.out['reference_errors']=[dict(reference_id='comparisons.4',reason='旧参考把LiCS GITT容量写为0.05C首圈，实际GITT0.42mA/cm²，不能混用。',evidence_ids=['S0049','M0139'])]
r.out['suggested_corrections']=['M8应为同溶剂LiPS浓度梯度，M9/12应指TTE；强弱侧别和挂接按属性修正。','T7应明确LiPS浓度是变量，其余条件相同。']
r.out['figure_triage']=[dict(request_index=i,status=('eligible' if i in [1,2] else 'no_numeric_capacity_anchor'),reason=('同循环55圈衰退/>180圈寿命可作方案允许数字锚点，需根代理核图。' if i in [1,2] else '本图仅载量/E/S等条件，无同测试容量/寿命/保持率文字数字锚点。'),evidence_ids=(['M0149','M0159'] if i in [1,2] else ['S0251'] if i==3 else ['S0273','S0274','S0276'])) for i in range(1,7)]
r.save('逐项复核12测试、所有结果、16机制；读取正文M0001–M0178、SI S0001–S0280（略参考），旧参考8比较及4条件，补SI独有遗漏。无目测图数，按同测试数字锚点筛6图请求。')
