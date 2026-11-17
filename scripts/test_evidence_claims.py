import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import evidence_claims as ec
import inspiration_design as w

class ClaimTests(unittest.TestCase):
    def setUp(self):
        self.source={'id':'R1','source_id':'E1','anchor_quote':'measured absorbance after contact',
          'read_level':'primary_excerpt','system':'Li2S8 solution','components':['DMSO','DOL','DME'],
          'changed_components':['DMSO','DOL','DME'],'material':'TiX','actual_comparison':'solvent comparison',
          'component_roles':[{'name':n,'role':'solvent'} for n in ('DMSO','DOL','DME')],
          'covariates_and_unknowns':'speciation','measured_quantity':'UV_absorbance','observation':'absorbance differs',
          'interpreted_quantity':'adsorption_extent','author_interpretation':'binding competition'}
        self.claim={'id':'C1','basis_id':'R1','statement':'adsorption differs','level':'author_interpretation',
          'quantity':'adsorption_extent','system':'Li2S8 solution','components':['DMSO','DOL','DME'],
          'material':'TiX','attribution':'formulation_comparison','actor_components':[],
          'use':'question_basis','essential':False,'basis_status':'source_supported','inference_step':''}
        self.evidence=[{'id':'E1','kind':'primary_targeted_excerpts','text':'The paper measured absorbance after contact with solids.'}]
        self.source_checks=[{'source_record_id':'R1','observation_separated_from_interpretation':True,
                             'component_and_system_scope_supported':True,'reason':'checked source text'}]

    def test_observed_signal_does_not_become_author_mechanism(self):
        c={**self.claim,'level':'observation'}
        self.assertIn('observation_inference_or_quantity_jump',ec.inspect_claim(c,[self.source]))

    def test_extent_cannot_become_desorption_rate(self):
        c={**self.claim,'quantity':'desorption_rate'}
        self.assertIn('observation_inference_or_quantity_jump',ec.inspect_claim(c,[self.source]))

    def test_material_solvent_and_initial_system_transfer_are_not_direct(self):
        for change in ({'material':'LTO'},{'components':['TEGDME','DME']},{'system':'S initial cell'}):
            with self.subTest(change=change):
                c={**self.claim,**change}
                self.assertIn('context_transfer_as_source_fact',ec.inspect_claim(c,[self.source]))

    def test_component_causation_requires_actual_changed_component(self):
        c={**self.claim,'attribution':'specific_components','actor_components':['LiFSI']}
        self.assertIn('component_attribution_not_supported_by_comparison',ec.inspect_claim(c,[self.source]))

    def test_structure_condition_does_not_have_to_masquerade_as_chemical(self):
        r={**self.source,'changed_components':[],'changed_conditions':['compaction']}
        c={**self.claim,'attribution':'specified_conditions','actor_conditions':['compaction']}
        ec.validate_sources([r],self.evidence)
        self.assertEqual(ec.inspect_claim(c,[r]),[])
        self.assertIn('condition_attribution_not_supported_by_comparison',
                      ec.inspect_claim({**c,'actor_conditions':['rest_time']},[r]))

    def test_present_but_fixed_component_cannot_support_new_intervention(self):
        r={**self.source,'changed_components':['DMSO']}
        c={**self.claim,'use':'intervention_basis','essential':True}
        packet={'prior':{'selected_question':{'claims':[c]},'criticism':{'source_checks':self.source_checks,
            'assessments':[{'support_checks':[{'claim_id':'C1','verdict':'intervention_supported'}]}]}},'source_records':[r]}
        target={'changed_components':['DME'],'changed_conditions':[],'material':c['material'],
                'system':c['system'],'intended_quantity':c['quantity']}
        with self.assertRaisesRegex(ValueError,'beyond its reviewed dependency'):
            ec.validate_stage('revise_design',{'experiments':[{'basis_claim_ids':['C1'],'intervention_target':target}]},packet)

    def test_hypothesis_can_survive_but_unsupported_intervention_is_held(self):
        c={**self.claim,'level':'project_hypothesis','quantity':'desorption_rate','material':'LTO',
           'basis_status':'unsubstantiated','inference_step':'analogy, untested','use':'intervention_basis','essential':True}
        ec.validate_claims([c],[self.source])
        result=ec.design_readiness({'claims':[c]},[self.source],[{'claim_id':'C1','verdict':'intervention_supported'}],self.source_checks)
        self.assertFalse(result['ready_for_design']);self.assertTrue(result['hypothesis_retained'])

    def test_reasoned_transfer_with_review_can_support_intervention(self):
        c={**self.claim,'level':'project_hypothesis','material':'related material',
           'basis_status':'reasoned_transfer','inference_step':'explicit transferable binding mechanism, scoped uncertainty',
           'use':'intervention_basis','essential':True}
        result=ec.design_readiness({'claims':[c]},[self.source],[{'claim_id':'C1','verdict':'intervention_supported'}],self.source_checks)
        self.assertTrue(result['ready_for_design']);self.assertFalse(result['scientific_truth_certified'])
        bad=[{**self.source_checks[0],'observation_separated_from_interpretation':False}]
        self.assertFalse(ec.design_readiness({'claims':[c]},[self.source],[{'claim_id':'C1','verdict':'intervention_supported'}],bad)['ready_for_design'])

    def test_supported_formulation_does_not_validate_unqualified_measurement(self):
        c={**self.claim,'use':'intervention_basis','essential':True}
        checks=[{'claim_id':'C1','verdict':'intervention_supported'}]
        readout={k:True for k in ('predictions_distinguishable','measurement_supported','critical_condition_supported','routine_feasible')}
        self.assertTrue(ec.design_readiness({'claims':[c]},[self.source],checks,self.source_checks,readout,True)['ready_for_design'])
        for key in readout:
            with self.subTest(key=key):
                gate=ec.design_readiness({'claims':[c]},[self.source],checks,self.source_checks,{**readout,key:False},True)
                self.assertFalse(gate['ready_for_design']);self.assertTrue(gate['hypothesis_retained'])

    def test_inventory_and_pore_mechanism_cannot_replace_measurements(self):
        for measured,claimed in [('surface_EDS','total_sulfur_inventory'),('SEM_film','pore_connectivity')]:
            r={**self.source,'measured_quantity':measured}
            c={**self.claim,'level':'observation','quantity':claimed}
            self.assertIn('observation_inference_or_quantity_jump',ec.inspect_claim(c,[r]))

    def test_quote_must_exist_and_all_claims_must_be_reviewed(self):
        with self.assertRaisesRegex(ValueError,'anchor absent'):
            ec.validate_sources([{**self.source,'anchor_quote':'fabricated quote'}],self.evidence)
        with self.assertRaisesRegex(ValueError,'support review'):
            ec.validate_stage('critic',{'assessments':[{'question_id':'N1','support_checks':[]}],'source_checks':self.source_checks},
                              {'prior':{'questions':[{'id':'N1','claims':[self.claim]}],'source_records':[self.source]}})

    def test_summary_cannot_be_relabelled_as_primary(self):
        with self.assertRaisesRegex(ValueError,'cannot be promoted'):
            ec.validate_sources([self.source],[{**self.evidence[0],'kind':'complete_upstream_summary'}])

    def test_invalid_claim_rejected_before_acceptance_hook_returns(self):
        w.configure()
        result={'scope_id':'X','source_records':[self.source],
                'branches':[{'claims':[{**self.claim,'quantity':'desorption_rate'}]}]}
        with self.assertRaisesRegex(ValueError,'quantity_jump'):
            w.io.check_result(result,'branches',{'scope':{'scope_id':'X'},'evidence':self.evidence})

    def test_design_preflight_skips_model_and_emits_no_matrix(self):
        c={**self.claim,'level':'project_hypothesis','quantity':'desorption_rate','material':'LTO',
           'basis_status':'unsubstantiated','inference_step':'not established','use':'intervention_basis','essential':True}
        with tempfile.TemporaryDirectory() as td:
            run=Path(td)
            w.write(run/'stages/recombine/result.json',{'questions':[{'id':'N1','question':'hypothesis','claims':[c]}],'source_records':[self.source]})
            w.write(run/'stages/critic/result.json',{'design_target':'N1','assessments':[{'question_id':'N1','support_checks':[{'claim_id':'C1','verdict':'insufficient'}]}]})
            with patch.object(w,'verify'),patch.object(w,'combine_evidence',return_value=(self.evidence,[])),patch.object(w,'call') as model:
                result=w.design(run)
            model.assert_not_called();self.assertEqual(result['result']['experiments'],[])
            self.assertEqual(w.read(run/'state.json')['phase'],'design_held')

    def test_plan_cannot_borrow_citation_then_change_solvent(self):
        c={**self.claim,'use':'intervention_basis','essential':True}
        packet={'prior':{'selected_question':{'claims':[c]},'criticism':{'source_checks':self.source_checks,
                 'assessments':[{'support_checks':[{'claim_id':'C1','verdict':'intervention_supported'}]}]}},'source_records':[self.source]}
        target={'changed_components':['DMSO'],'system':c['system'],'material':c['material'],'intended_quantity':c['quantity']}
        result={'experiments':[{'basis_claim_ids':['C1'],'intervention_target':target}]}
        ec.validate_stage('revise_design',result,packet)
        result['experiments'][0]['intervention_target']={**target,'changed_components':['TEGDME']}
        with self.assertRaisesRegex(ValueError,'beyond its reviewed dependency'):
            ec.validate_stage('revise_design',result,packet)

if __name__=='__main__':unittest.main()
