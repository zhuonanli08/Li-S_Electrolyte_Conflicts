from review_c_build import Review,R
import json,re
r=Review('S40')
r.group('t1 t2 t3 t4 t5 t6 t7','TP','E/S23/16/9/6、载硫、170µmLi、0.1C/电压/OCV16h及CV条件吻合；室温不填25℃。',['M0148','M0152','M0153','M0154','M0155','M0156','M0158','M0160','M0162'])
r.group('t8 t9','FP','遗漏SI明确的20µL/cm²电解液和S:Li2S=7:1饱和长链LiPS条件。',['S0020','S0021','S0025','S0026','S0027'],['conditions.C5'])
r.group('t1r1 t2r1 t2r2 t3r1 t4r1','UNRESOLVED','almost all E/S概括不能确认每个E/S和配方的一律方向，已有低E/S例外，待图核。',['M0057','M0060','M0065'])
r.group('t1r2 t3r2 t4r2','TP','除16外SL-LiClO4容量最低，结合循环判断支持G3-LiTFSI更好。',['M0057','M0063'])
r.group('t1r3 t2r3 t3r3 t4r3','TP','原文明示所有E/S中SL CE约90%，高于G3；作者定性不套5%。',['M0062'],['comparisons.3'])
r.group('t1r4 t3r4 t4r4','TP','正确保留E/S16例外，其他SL-LiClO4容量最低。',['M0063'])
r.unit('t4r5','TP','E/S6时G3-LiTF容量及保持率最高，虽CE低。',['M0065','M0168'],['comparisons.8','comparisons.9','comparisons.15','comparisons.16'])
r.unit('t4r6','TP','E/S6 SL-LiTFSI优于G3-LiTFSI明示。',['M0061'],['comparisons.1'])
r.unit('t4r7','TP','SL-LiTFSI各圈硫利用率最高明示，不混为总容量。',['M0127'],['comparisons.6'])
r.unit('t4r8','SKIP_NONSCORING','低/高平台容量比未定义优劣，不能当总容量。',['M0129'])
src=json.loads((R/'sources/S40.json').read_text(encoding='utf-8'));s=next(x['text'] for x in src if x['id']=='S0029');gs=re.split(r'(SL-LiTFSI|SL-LiTF|SL-LiClO4|G3-LiTFSI|G3-LiTF) ',s)[1:];table={}
for name,block in zip(gs[0::2],gs[1::2]):
 nums=block.split();assert len(nums)==30
 for j in range(0,30,5):table[(name.replace('-','_'),int(nums[j]))]=[float(x) for x in nums[j+1:j+5]]
for v in r.p['tests'][4]['results']:
 cyc=int(re.search(r'\d+',v['point']).group());col=['R1','R2','R3','RTotal'].index(v['metric']);assert float(v['value_A'])==table[(v['A'],cyc)][col];assert float(v['value_B'])==table[(v['B'],cyc)][col]
 r.unit('t5r'+v['id'].split('-R')[1],'SKIP_ABSTENTION','SI表S1按配方/圈数/列逐项核对原数准确；固定程序R1/R2/R3/RTotal偏好未定义，保持不判，不扩评分。',['S0029','M0086'])
r.group('t6r1 t7r1','TP','对应E/S的CV原文明确SL动力学比G3有利。',['M0114','M0120'])
r.unit('t8r1','TP','储存及循环支持SL更稳定SEI为作者定性结论。',['M0147'],['comparisons.13'])
r.group('m1 m2 m3 m4 m5 m6 m7','TP','该因果判断或解释与所引原文及上下文一致，保留推测/结论。')
r.unit('m8','SKIP_DUPLICATE','同M7的SL更稳定SEI/锂界面，增加对称测试证据不另计说法。',['M0145','M0147'])
for cat,desc,ev,ref in [
('测试及条件','对称储存/循环20µL/cm²、饱和长链LiPS(S:Li2S7:1)，循环面积5cm²。',['S0020','S0021','S0025','S0026','S0027'],['conditions.C5']),
('方向','前10圈SL-LiTFSI和SL-LiTF容量最高；G3-LiTF初期较低，与后期反转分开。',['M0096','M0104'],['comparisons.2','comparisons.7','comparisons.14']),
('方向','各E/S SL-LiTF对G3-LiTF的CE更高；只录了LiTFSI对比。',['M0062'],['comparisons.10']),
('方向','LiTFSI两溶剂初容量对E/S近似不变；其他SL盐随E/S增大容量降低，G3相反，属跨条件趋势。',['M0070','M0071','M0075'],[]),
('方向','E/S6对9一般电压滞后更大，需标跨条件。',['M0113'],[]),
('机制','低E/S LiTFSI可能增黏降电导加剧穿梭，解释G3-LiTFSI低E/S恶化。',['M0059','M0060'],['comparisons.16']),
('机制','G3较低且波动大的CE指示更强穿梭。',['M0062'],['comparisons.3','comparisons.10']),
('机制','高E/S下SL第一平台弱/消失表明长链LiPS形成受阻。',['M0077','M0078'],[]),
('机制','SL-LiClO4最低膜阻抗可能与LiPS溶解动力学有关。',['M0101'],[]),
('机制','锂表面不均匀可使电流分布和电极传导性质改变。',['M0133'],[])]:r.miss(cat,desc,ev,ref)
r.out['reference_errors']=[dict(reference_id='conditions.C1-C4',reason='室温不等于确认25℃。',evidence_ids=['M0155'])]
r.out['unresolved']=['5个almost all分派到指定E/S的方向待图核。']
r.out['suggested_corrections']=['96条阻抗配对正确，程序未定义命名偏好，不扩评分；可补物理名称。','T5补EIS频段/振幅与30min静置。']
r.out['figure_triage']=[dict(request_index=i,status='eligible' if i<=2 else 'no_numeric_capacity_anchor',reason='高E/S首容量>800可先核是否对应本图，边界锚点适用性待图核。' if i<=2 else '本E/S只有定性与条件，无容量/寿命/保持率数字锚点。',evidence_ids=['M0056','M0072'] if i<=2 else ['M0065','M0072']) for i in range(1,5)]
r.save('完整读正文M0001–M0178、SI S0001–S0031、旧参考19比较5条件；9测试118结果8机制全部审，96阻抗值对表格精确校验。图请求只筛不读数。')
