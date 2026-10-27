from _review_a import *
r=Review('P591','核对正文方法、全Results/Discussion和Conclusion、SI全文及旧参考。LiNO3剂量差按项目固定规则拆条件，定性和数值分开；E/S保留作者7.7及总30µL，不自行消除原文口径差。')
for t in ['T2','T3','T4','T6','T7','T8','T10','T11','T14']:
 r.unit('T/'+t,'TP','测试与对应图文一致；E/S作者值及实际加液量同时保留，初始/第三圈原文冲突已注明。')
for t in ['T1','T5','T9','T12']:
 r.unit('T/'+t,'FP','遗漏明确通用条件：五电解液均3wt% LiNO3；全部电池电化学测试室温。当前测试把其中一项或两项写未报告。',['M0052','M0053','M0054','M0073'])
 r.miss('测试及条件',t+'校正为3wt% LiNO3、室温；其余原已提取条件保留。',['M0052','M0053','M0054','M0073'],'原条件遗漏有来源支持的重要条件。')
r.unit('T/T13','FP','Mix3wt%与LowMix2wt% LiNO3条件混在一组，不能按同条件比较；并把倍率和0.5C循环合并。',['M0136','M0301','M0302','M0303','S0030'])
for desc in ['Mix：0.5C、3wt% LiNO3，约2.3mg/cm²、作者E/S7.7、总30µL、室温。','LowMix：0.5C、2wt% LiNO3，其他通用条件同所述但单独分组。','Mix与LowMix的倍率测试：倍率阶梯文本未给，按各自3wt%/2wt% LiNO3分条件保存。']:
 r.miss('测试及条件',desc,['M0136','M0301','M0302','M0303','S0030'],'T13未按不同硝酸锂剂量/测试拆分。')
for k in ['T/T1/T1R'+str(i) for i in range(1,5)]+['T/T2/T2R'+str(i) for i in range(1,4)]+['T/T3/T3R'+str(i) for i in range(1,4)]+['T/T4/T4R1','T/T5/T5R5','T/T6/T6R5','T/T6/T6R6','T/T7/T7R2','T/T10/T10R2']:
 r.unit(k,'TP','作者明确比较支持定性；保留其余四组/低浓度组的对照范围，不扩成数值。')
for k in ['T/T5/T5R'+str(i) for i in range(1,5)]:
 r.unit(k,'TP','同一Li2S沉积测试原数匹配；固定程序前三种差异较大，Mix/Se仅3.95%应差异小。')
for k in ['T/T4/T4R2']+['T/T6/T6R'+str(i) for i in [1,2,3,4,7]]+['T/T7/T7R1']+['T/T8/T8R1','T/T8/T8R2']+['T/T9/T9R'+str(i) for i in range(1,4)]+['T/T10/T10R1','T/T10/T10R3','T/T11/T11R1','T/T11/T11R2']+['T/T12/T12R'+str(i) for i in range(1,6)]:
 r.unit(k,'SKIP_NONSCORING','单组数值/时间演变或单组作者观察，未构成比较方向，不计方向TP。')
r.unit('T/T13/T13R1','FP','1103/745原数可核，但3wt%/2wt% LiNO3不同，same_conditions=true及程序变好违反本项目同条件规则。',['M0136','M0302'])
r.unit('T/T13/T13R2','TP','作者直接称Mix倍率/循环更优，可保留定性但需标LiNO3等多因素混杂、same_conditions=false，不能据此强化单因素因果。')
r.unit('T/T14/T14R1','SKIP_ABSTENTION','只有图、未读值且不判；保留请求证据，不计方向命中。')
for m in ['M1','M4','M5','M6','M7','M8','M9','M10']:
 r.unit('M/'+m,'TP','原文相应因果/例外明确，推测语气已保留；M7原位成核和循环后表面证据支持同一钝化控制论断。')
r.unit('M/M2','SKIP_NONSCORING','Te位阻/分子作用→黏度/自由溶剂→Li2S4溶解度为性质来源，未直接涉及四过程，移性质。')
r.unit('M/M3','SKIP_NONSCORING','配位螯合→Li迁移/电导为纯电解液性质来源，移性质并保留may推测，不计机制FP。')
r.miss('方向','0.2Se与0.2Te各自比0.2空白提高LiPS对称CV峰电流/氧化还原动力学。',['M0191'],'只提Mix对各组，遗漏单添加剂相对低盐空白的作者定性。')
r.miss('机制','排除无电化学过程下添加剂与单质硫自发反应，催化作用发生于电化学驱动PS转化。',['M0176','M0177','M0178'],'独有排除性因果遗漏。')
r.miss('机制','Mix添加剂自身容量小，完整电池高容量主要源于PS协同催化而非添加剂自身贡献。',['M0279','M0280','M0281'],'独有排除性因果遗漏，单组添加剂容量数据不能代替这一判断。')
r.d['reference_errors']=[{'description':'旧参考说方向需读图，但正文已有Mix较其余组容量/倍率更高、0.5C相对Se极化更大及1C极化更小的定性。','evidence_ids':['M0262','M0264','M0266','M0271','M0283']}]
r.d['suggested_corrections']=[{'description':'T13先分LiNO3剂量；禁止1103/745数值判向，作者定性注明混杂。T1/T5/T9/T12补通用明确条件。M2/M3移性质。','evidence_ids':['M0052','M0053','M0054','M0073','M0136','M0302','M0303']}]
r.d['figure_triage']=[{'request_index':1,'status':'eligible','reason':'Fig5a同0.5C/2.3mg有1103初始、985@100、89.3%锚可补同条件对照。','evidence_ids':['M0258','M0259','M0291']},{'request_index':2,'status':'out_of_scope','reason':'Mix与LowMix硝酸锂3wt%/2wt%不同，不是本方案允许的同条件容量补读配对；已有作者定性可保留。','evidence_ids':['M0053','M0136','M0302','S0030']}]
r.save()
