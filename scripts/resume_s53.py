"""S53 extraction and validation; reuse the established evidence calculations."""
import json
import re
from pathlib import Path
import step2d_build_evidence as b

root = Path(b.ROOT)
out = root / 'output/第一阶段_证据表'
text = (root / 'output/text_cache/10.1016_j.jpowsour.2024.236109.main.txt').read_text(encoding='utf-8')
flat = re.sub(r'\s+', ' ', text)
def quote(start, end):
    i = flat.index(start)
    j = flat.index(end, i) + len(end)
    return flat[i:j]

p = {'paper': {'pool_id':'S53','doi':'10.1016/j.jpowsour.2024.236109',
    'ref':'Zheng D. et al., Journal of Power Sources 2025, 630, 236109',
    'corr':'Deyang Qu（University of Wisconsin Milwaukee）',
    'source':'补抽(强/适中×常规)第1位','main_layer':True,
    'group_note':'随机补抽。精读正文 6 页；本地无 SI，Table S1 峰面积未核。抽样层标签不等于已验证的溶剂化强弱。没有可比溶剂化描述符；黏度不用于溶剂化排序。添加 LiNO3 同时把 LiTFSI 从 1.5 M 改为 1.0 M。只录正文明确支持的电解液配对；HPLC 为静态化学反应支持证据，不等同于循环中穿梭通量。'},
    'electrolytes':{},'descriptors':[], 'conditions':{},'comparisons':[]}
eq = quote('The polysulfide solutions used in this work were', '1.0 M LiTFSi/SL with 0.5 M LiNO3.')
for key, solvent, nitrate in [('DD','DME/DOL (1:1；比例基准未写)',False),('SL','SL（环丁砜）',False),('DDN','DME/DOL (1:1；比例基准未写)',True),('SLN','SL（环丁砜）',True)]:
    salt = '1.0 M LiTFSI' if nitrate else '1.5 M LiTFSI'
    p['electrolytes'][key] = dict(name=salt+(' + 0.5 M LiNO3 ' if nitrate else '（无 LiNO3） ')+solvent,
        solvent=solvent,salt=salt,salt_anion='TFSI',diluent='无',lino3='0.5 M' if nitrate else '无',
        lino3_value=0.5 if nitrate else 0,lino3_unit='M',additive='无',label_author='sulfolane electrolyte' if key.startswith('SL') else 'DME/DOL electrolyte',
        label='其他' if key.startswith('SL') else '常规',quote=eq)
base = dict(cathode_type='硫碳',cathode_material='S8/CMK3；S:CMK3:Super C-65:PVDF=60:20:10:10 wt%',
    S_loading=1.5,S_loading_src='直接（理论面载量约值）',S_content_composite=None,S_content_electrode=60,
    V_uL=15,diameter_mm=None,area_cm2=None,ES_reported=None,ES_unit='µL/mg',Li_um=None,
    NP_author=None,NP_author_basis=None,cell='扣式 CR2032',cell_Ah=None,rate_author=0.05,rate_1C_def=None,
    rate_note='1.7–2.9 V；装配后静置 12 h；1C 定义未写',anode_pretreat='未写',porosity=None,
    quote=quote('The sulfur cathodes have a theoretical', 'battery testing system (Arbin BT2000).'))
for key,temp in [('C1',25),('C2',60)]:
    p['conditions'][key] = dict(base, desc=f'Li‖S 扣式；约 1.5 mg/cm²，15 µL，0.05 C，{temp} °C；正极直径和锂厚未写',temp_C=temp,
        temp_src='直接（Fig. 1 图注：室温约 25 °C）' if temp==25 else '直接')

def add(A,B,cond,metric,point,direction,q,loc,note='',va=None,vb=None,unit='定性（穿梭越少越好）',reasons=None,rq=''):
    p['comparisons'].append(dict(A=A,B=B,cond=cond,metric=metric,val_A=va,val_B=vb,unit=unit,point=point,
        val_src_A='直接' if va is not None else '未取数（正文定性）',val_src_B='直接' if vb is not None else '未取数（正文定性）',
        comparable_point=True,obs_dir=direction,author_judgement='作者提出黏度与 SEI 的竞争解释；未独立分离两者贡献',
        error_info='未报告',evidence_loc=loc,evidence_type='有数据',changed=['溶剂种类'] if (A,B)==('SL','DD') else ['盐浓度','LiNO₃'],
        reasons=reasons or ['穿梭'],reason_quote=rq,scope_claim='无',first_cap_A=None,first_cap_B=None,first_cap_note='',note=note,quote=q))
add('SL','DD','C1','多硫化物溶解或穿梭','室温充放电曲线；SL 观察至 200 圈','A更好',
    quote('As shown in Fig. 1(A), at room temperature,','despite not having the LiNO3 additive.'),'Fig. 1A–B；p2–3',
    '比较的是同温同倍率下穿梭现象；未将两个不同圈数的容量配成数值。正文称 SL 至 200 圈仍无显著穿梭，不等于容量保持率已知。',
    rq=quote('This high viscosity could be a reason','without LiNO3 additive.'))
add('SL','DD','C2','多硫化物溶解或穿梭','60 °C 充放电曲线（均无 LiNO3）','A更好',
    quote('Consequently, the polysulfide shuttle','even at elevated temperature.'),'Fig. 1C–D、2C/G；p2–3',
    '两种电解液都出现穿梭；SL 较轻不代表无穿梭。第 5 圈后约 10% 过充仅为 SL 单边数值，不构造配对效应量。')
add('SL','DD','C2','循环保持率或寿命','60 °C 持续循环能力／穿梭导致无法循环','A更好',
    quote('In the case of the Li-S battery with','shown in Fig. 1 (D).'),'Fig. 1C–D；p2',
    'DD 从开始即无法正常循环；不能把这一文字人为转成寿命 0 圈。SL 在 35 圈后失效；未统一容量阈值，不计算寿命比。',va=35,unit='圈（穿梭导致失效；非统一容量阈值）')
add('SLN','SL','C2','多硫化物溶解或穿梭','60 °C 充放电曲线（含／不含 LiNO3）','A更好',
    quote('For sulfolane electrolyte with LiNO3,','demonstrated by the study of SEI composition in DME/DOL electrolytes.'),'Fig. 1D/F、2G/H；p5',
    'LiTFSI 浓度与 LiNO3 同时变化，不能视为纯添加剂单因素；黏度更低但穿梭更少，反对仅用黏度解释全部现象。',reasons=['穿梭','负极 SEI'])
add('DDN','DD','C2','多硫化物溶解或穿梭','60 °C 充放电曲线（含／不含 LiNO3）','A更好',
    quote('In the case of the Li-S battery with DME/DOL','as shown in Fig. 1 (C).')+' … '+quote('Fig. 1(E) and (F) display','effect in both electrolytes.'),'Fig. 1C/E、2C/D；p2、p4',
    'LiTFSI 浓度与 LiNO3 同时变化，不能视为纯添加剂单因素。')
p['physical_properties'] = {'source':'Table 1；p4','property':'黏度','unit':'mPa·s','temperature_tolerance_C':1,
    'values_by_temperature_C':{'0':{'DD':4.98,'DDN':4.20,'SL':169.05,'SLN':151.05},'30':{'DD':2.41,'DDN':1.93,'SL':51.00,'SLN':43.55},'60':{'DD':1.54,'DDN':1.33,'SL':19.55,'SLN':15.90}},
    'flags':['DDN 在 60 °C 的 1.33 带脚注 a：测量超出正常扭矩范围','30 °C 黏度不能当作 25 °C 电池条件的实测值','该字段为补充物性存档，不进入溶剂化方向算法']}
for c in p['comparisons']:
    assert b.found(p['paper']['doi'],c['quote'])
    assert b.found(p['paper']['doi'],c['reason_quote'])
for obj in list(p['electrolytes'].values()) + list(p['conditions'].values()):
    assert b.found(p['paper']['doi'],obj['quote'])
(out/'json/S53.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
rows=b.build_rows()
new=[r for r in rows if r['_paper']=='S53']
assert len(new)==5 and all(r['F2 核验标记'] not in ['❌','⚠️'] for r in new)
assert all(r['B9 溶剂化方向']=='无法判断' for r in new)
print(json.dumps({'papers':len(set(r['_paper'] for r in rows)),'rows':len(rows),'S53':[(r['A1 行号'],r['F2 核验标记']) for r in new]},ensure_ascii=False))
ctrl=b.same_paper_controls(rows)
sampled=json.loads(Path(b.BASELINE).read_text(encoding='utf-8'))['spot_check']
pairs=b.build_pairs(rows)
diffs,targeted=b.compare_baseline(rows,pairs)
for r in rows:
    if r['A1 行号'] in sampled: r['F3 随机抽查（固定原 9 条）']='抽中，待核配方—条件对应'
    if r['A1 行号'] in targeted: r['F3b 定向复核（本轮修改涉及）']=targeted[r['A1 行号']]
cons,blocks=b.advantage_consistency(rows)
def matrix(records):
    keys=[k for k in records[0] if not k.startswith('_')]
    return [keys]+[[r.get(k) for k in keys] for r in records]
summary=[]
for title,block in b.summary_blocks(rows,pairs,ctrl,sampled,targeted)+[('7 字段与判定规则（10-18 第二轮评审已定 + 仍开放）',[[g] for g in b.GAPS]),("8 优势一致性（方案 3 §3；初步，明细见'优势一致性'页）",blocks)]:
    summary += [[title]]+block+[[]]
n=max(map(len,summary))
summary=[r+[None]*(n-len(r)) for r in summary]
payload={'主表':matrix(rows),'矛盾对':matrix(pairs),'汇总':summary,'优势一致性':matrix(cons),
    '新旧对照':matrix(diffs)}
(out/'s53_workbook_update.json').write_text(json.dumps(payload,ensure_ascii=False,default=str),encoding='utf-8')
