"""Typed evidence-to-claim checks. These detect declared mismatches, not truth.

Source classification and transfer judgments still require reading the source.
No keyword ban, novelty score, or automatic scientific endorsement is used.
"""
import re
from experiment_design_workflow import obj,require

S=lambda n=400:{'type':'string','maxLength':n}
A=lambda item,n=8,minimum=0:{'type':'array','items':item,'maxItems':n,'minItems':minimum}
E=lambda *values:{'type':'string','enum':list(values)}
SOURCE=obj({'id':S(20),'source_id':S(20),'anchor_quote':S(1400),
 'read_level':E('primary_excerpt','upstream_summary','metadata'),
 'system':S(160),'components':A(S(60)),'changed_components':A(S(60)),'changed_conditions':A(S(60)),
 'component_roles':A(obj({'name':S(60),'role':E('solvent','supporting_salt','additive','active_species','solid_component','unknown')})),
 'material':S(100),'actual_comparison':S(400),'covariates_and_unknowns':S(300),
 'measured_quantity':S(80),'observation':S(400),
 'interpreted_quantity':S(80),'author_interpretation':S(400)})
CLAIM=obj({'id':S(20),'basis_id':S(20),'statement':S(350),
 'level':E('observation','author_interpretation','project_hypothesis'),
 'quantity':S(80),'system':S(160),'components':A(S(60)),'material':S(100),
 'attribution':E('specific_components','specified_conditions','formulation_comparison','unresolved'),
 'actor_components':A(S(60)),'actor_conditions':A(S(60)),'use':E('question_basis','mechanism_hypothesis','intervention_basis'),
 'essential':{'type':'boolean'},'basis_status':E('source_supported','reasoned_transfer','unsubstantiated'),
 'inference_step':S(400)})
CHECK=obj({'claim_id':S(20),'verdict':E('question_only','intervention_supported','insufficient'),
 'reason':S(350)})
SOURCE_CHECK=obj({'source_record_id':S(20),'observation_separated_from_interpretation':{'type':'boolean'},
 'component_and_system_scope_supported':{'type':'boolean'},'reason':S(350)})
INTERVENTION=obj({'changed_components':A(S(60)),'changed_conditions':A(S(60)),
 'material':S(100),'system':S(160),'intended_quantity':S(80)})
CONTRACT_RULES='''
初始分支只形成带引文的科学草案；下列source_records/claims约束用于补证后的重组及方案审查。
来源卡是事实登记，author_interpretation只写作者解释，项目限制写covariates_and_unknowns。主张的quantity/system/material是来源卡标识的引用：直接转述时原样复用，不翻译或改写；跨对象或新量只能作为明确推断。一个来源卡混含多个测量时，先按需要的实验/量拆卡，不能用相似词归一化隐藏物理量差异。字符串未对上仅表示待核链接，不是科学反证。
source_records只为候选实际使用的依据建卡，不为所有背景关系重复建卡，优先完整覆盖所有候选引用。basis_id必须是本次source_records内一个真实id，不能填主张id或用加号拼接；多个来源的综合推断以一个主来源挂接，其他依据写inference_step和evidence_refs。
components/changed_components/actor_components只写具体化学组分的相同名称，例如LiTFSI，不能写LiTFSI浓度、倍率或压实。用量/比例及数值写actual_comparison；非组分干预（压实、倍率、浸润时间等）写changed_conditions，主张的actor_conditions与之对应，归因specified_conditions。不能因现有字段不适合而把结构塞成化学组分。两个列表无对应变化时填空数组。
每个科学主张用claims连接source_records。source_records分别写实际改变的具体组分/材料/结构、共同变化、直接测量及作者解释；锚点必须逐字出现在输入证据中，摘要仍标摘要。quantity用简短、稳定的物理量标识，不把实测信号、吸附程度、速率、总库存归为同一量。
claims明确观察、作者解释或项目假说，目标材料、组分及体系和来源分开。整体配方比较可作为整体比较报告，不能无依据指定某一分子机制；机制不明记unresolved。吸附程度不同不证明脱附速率改变，表面EDS不证明总硫库存/通量，SEM覆膜不直接证明孔道锁定。同一篇不同实验须拆成不同source_record。
假说可以未证实；但承载实验判别的组分干预必须有依据。区分“欲检验的机制是否成立”和“选定组分变化是否能产生所声称的干预”。跨材料/溶剂/初始体系迁移列明inference_step；仅写项目建议、先预试、可逆性未知，不能算干预依据。无依据的参数矩阵不以探索性名义放行；保留问题并退回补证/重构。
审查先逐source_checks回原文检查源记录的组分/体系、观察与作者解释是否分开，不能只信任生成者填的标签；再逐条support_checks检查推断。不能将作者推断改称实测。程序只检查声明与来源的关系，字段写对不证明语义或新颖性。
'''

def norm(s):return re.sub(r'\s+',' ',s).strip()

def validate_sources(records,evidence):
    sources={e['id']:e for e in evidence};ids=[r['id'] for r in records]
    require(len(ids)==len(set(ids)),'Duplicate source record')
    for r in records:
        require(r['source_id'] in sources,'Unknown source record citation')
        origin=sources[r['source_id']]
        if r['read_level']=='primary_excerpt':
            require(origin.get('kind') in ('primary_text_and_SI_excerpts','primary_targeted_excerpts') or origin.get('primary_verified') is True,
                    'Summary/metadata/unverified web text cannot be promoted to primary evidence')
        quote=norm(r['anchor_quote'])
        require(bool(quote) and quote in norm(origin['text']),'Source anchor absent from evidence')
        require(set(r['changed_components'])<=set(r['components']),'Changed component absent from source composition')
        role_names=[x['name'] for x in r['component_roles']]
        require(set(role_names)==set(r['components']) and len(role_names)==len(set(role_names)),'Missing/duplicate component roles')
        require(r['system'].strip() and r['material'].strip(),'Unspecified source system/material')

def inspect_claim(claim,records):
    """Return explicit mismatch codes; never infer semantic support from prose."""
    by_id={r['id']:r for r in records};issues=[]
    if claim['basis_id'] not in by_id:return ['missing_basis']
    r=by_id[claim['basis_id']]
    same=(claim['system']==r['system'] and claim['material']==r['material'] and set(claim['components'])<=set(r['components']))
    expected=r['measured_quantity'] if claim['level']=='observation' else r['interpreted_quantity']
    if claim['level']!='project_hypothesis':
        if claim['quantity']!=expected:issues.append('observation_inference_or_quantity_jump')
        if not same:issues.append('context_transfer_as_source_fact')
    elif not claim['inference_step'].strip():issues.append('hypothesis_missing_inference_step')
    if claim['basis_status']=='source_supported' and (not same or claim['quantity'] not in (r['measured_quantity'],r['interpreted_quantity'])):
        issues.append('unsupported_direct_support_label')
    if claim['attribution']=='specific_components':
        if not claim['actor_components'] or not set(claim['actor_components'])<=set(r['changed_components']):
            issues.append('component_attribution_not_supported_by_comparison')
    if claim['attribution']=='specified_conditions':
        if not claim.get('actor_conditions') or not set(claim['actor_conditions'])<=set(r.get('changed_conditions',[])):
            issues.append('condition_attribution_not_supported_by_comparison')
    if claim['basis_status']=='reasoned_transfer' and not claim['inference_step'].strip():issues.append('transfer_without_reason')
    return issues

def validate_claims(claims,records):
    ids=[c['id'] for c in claims];require(len(ids)==len(set(ids)),'Duplicate claim ID')
    for c in claims:
        issues=inspect_claim(c,records)
        require(not issues,f"Claim {c['id']}: {','.join(issues)}")

def design_readiness(candidate,records,checks,source_checks=(),readout_check=None,require_readout=False):
    """A hypothesis may survive while its specific intervention is held."""
    claims=candidate.get('claims',[]);review={x['claim_id']:x for x in checks}
    reasons=[];by_id={r['id']:r for r in records};source_review={r['source_record_id']:r for r in source_checks}
    required=[c for c in claims if c['essential'] and c['use']=='intervention_basis']
    if not required:reasons.append('missing_explicit_intervention_basis')
    if require_readout:
        for key in ('predictions_distinguishable','measurement_supported','critical_condition_supported','routine_feasible'):
            if not (readout_check or {}).get(key):reasons.append('core_readout:'+key)
    for c in claims:
        reasons += [f"{c['id']}:{x}" for x in inspect_claim(c,records)]
    for c in required:
        r=by_id.get(c['basis_id'],{})
        if c['basis_status']=='unsubstantiated':reasons.append(c['id']+':unsubstantiated_intervention')
        if c['attribution']=='unresolved':reasons.append(c['id']+':unresolved_intervention_attribution')
        if r.get('read_level')!='primary_excerpt':reasons.append(c['id']+':intervention_requires_primary_evidence')
        if review.get(c['id'],{}).get('verdict')!='intervention_supported':reasons.append(c['id']+':intervention_not_supported_in_review')
        sr=source_review.get(c['basis_id'],{})
        if not (sr.get('observation_separated_from_interpretation') and sr.get('component_and_system_scope_supported')):
            reasons.append(c['id']+':source_classification_not_verified')
    return {'ready_for_design':not reasons,'reasons':list(dict.fromkeys(reasons)),
            'linkage_checks_are_not_scientific_refutations':True,
            'hypothesis_retained':True,'scientific_truth_certified':False}

def validate_stage(stage,result,packet):
    if stage in ('branches','recombine'):
        records=result['source_records'];validate_sources(records,packet['evidence'])
        items=result['branches'] if stage=='branches' else result['questions']
        for item in items:
            require(item['claims'],'Candidate lacks evidence-linked claims')
            validate_claims(item['claims'],records)
    elif stage=='critic':
        questions={q['id']:q for q in packet['prior']['questions']}
        expected_sources={r['id'] for r in packet['prior']['source_records']}
        got_sources=[r['source_record_id'] for r in result['source_checks']]
        require(set(got_sources)==expected_sources and len(got_sources)==len(expected_sources),'Missing/duplicate source classification review')
        for assessment in result['assessments']:
            expected={c['id'] for c in questions[assessment['question_id']]['claims']}
            checks=assessment['support_checks'];got=[c['claim_id'] for c in checks]
            require(set(got)==expected and len(got)==len(expected),'Missing/duplicate claim support review')
    elif stage=='revise_design':
        q=packet['prior']['selected_question'];checks=packet['prior']['criticism']['assessments'][0]['support_checks']
        readiness=design_readiness(q,packet['source_records'],checks,packet['prior']['criticism']['source_checks'],
            readout_check=packet['prior']['criticism']['assessments'][0].get('readout_check'),require_readout='core_readout' in q)
        require(readiness['ready_for_design'] or not result['experiments'],'Unsupported intervention cannot carry experiment matrix')
        eligible={c['id']:c for c in q['claims'] if c['use']=='intervention_basis' and c['basis_status']!='unsubstantiated'}
        for exp in result['experiments']:
            require(bool(exp['basis_claim_ids']) and set(exp['basis_claim_ids'])<=set(eligible),'Experiment lacks supported intervention dependency')
            target=exp['intervention_target']
            require(target['changed_components'] or target.get('changed_conditions'),'Experiment has no declared intervention')
            sources={r['id']:r for r in packet['source_records']}
            matches=[eligible[i] for i in exp['basis_claim_ids'] if eligible[i]['material']==target['material'] and
                     eligible[i]['system']==target['system'] and eligible[i]['quantity']==target['intended_quantity'] and
                     set(target['changed_components'])<=set(eligible[i]['actor_components'] or sources[eligible[i]['basis_id']]['changed_components']) and
                     set(target.get('changed_conditions',[]))<=set(eligible[i].get('actor_conditions',[]))]
            require(bool(matches),'Experiment changes components/material/system/process beyond its reviewed dependency')
