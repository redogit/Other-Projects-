import copy
import json
import unittest
from pathlib import Path

try:
    import gsfl_operator_projection as projection
except ImportError:
    projection = None

ROOT = Path(__file__).resolve().parent
PROFILE = ROOT / 'gsfl-operator-profile.json'
EXPECTED = [
    'OBSERVE','DISTINGUISH','GROUND','MAP','RELATE','COMPARE','ROTATE','PRESERVE',
    'COMPOSE','SPLIT','MERGE','COOPERATE','HANDOFF','TRACE_TOOL','TEACH_BACK',
    'VERIFY','RECONSTRUCT','REPAIR','FIT','SELECT','GENERATE_PROVERB_FIXTURE',
    'AUDIT_CONFOUNDS','DERIVE_COROLLARIES'
]

class GSFLProjectionTests(unittest.TestCase):
    def require(self):
        self.assertIsNotNone(projection, 'gsfl_operator_projection module must exist')
        self.assertTrue(PROFILE.is_file(), 'profile registry must exist')

    def test_profile_registers_all_operations_as_unique_operators(self):
        self.require()
        data = json.loads(PROFILE.read_text(encoding='utf-8'))
        ids = [row['id'] for row in data['operators']]
        self.assertEqual(EXPECTED, ids)
        self.assertEqual(len(ids), len(set(ids)))

    def test_projection_points_to_complete_bounded_source_without_mutating_it(self):
        self.require()
        data = projection.load_profile(PROFILE)
        self.assertEqual('COMPLETE_BOUNDED_V0_1', data['source_contract']['lifecycle'])
        self.assertEqual('cf9d5a35a39b1a7b92f30e24b2789f659e913f04', data['source_contract']['completion_merge'])
        self.assertEqual('PROJECTION_DOES_NOT_MUTATE_SOURCE_BASELINE', data['authority_model'])

    def test_canonical_overlaps_delegate_instead_of_conflicting(self):
        self.require()
        data = projection.load_profile(PROFILE)
        by_id = {row['id']: row for row in data['operators']}
        for op in ('DISTINGUISH','GROUND','REPAIR','SELECT'):
            self.assertEqual('DELEGATE_CANONICAL', by_id[op]['execution'])
            self.assertEqual(op, by_id[op]['delegate_to'])

    def test_shared_skill_and_agent_exist(self):
        self.require()
        data = projection.load_profile(PROFILE)
        self.assertTrue((ROOT / data['shared_skill']).is_file())
        self.assertTrue((ROOT / data['shared_agent']).is_file())
        for op in data['operators']:
            self.assertEqual(data['shared_skill'], op['skill'])
            self.assertEqual(data['shared_agent'], op['agent'])
            self.assertTrue(op['output'])

    def test_native_operator_does_not_mutate_input_envelope(self):
        self.require()
        envelope = {'payload': {'x': 1}, 'trace': []}
        before = copy.deepcopy(envelope)
        out = projection.apply_operator('OBSERVE', envelope, observation='x is present')
        self.assertEqual(before, envelope)
        self.assertEqual(['x is present'], out['payload']['observations'])
        self.assertEqual('OBSERVE', out['trace'][-1]['operator'])

    def test_rotation_preserves_source_meaning(self):
        self.require()
        envelope = {'payload': {'source_meaning': {'identity': 'same'}}, 'trace': []}
        out = projection.apply_operator('ROTATE', envelope, surface='same thing, clearer')
        self.assertEqual({'identity': 'same'}, out['payload']['source_meaning'])
        self.assertEqual('same thing, clearer', out['payload']['surface'])
        self.assertEqual('REPRESENTATION_ONLY', out['trace'][-1]['semantic_effect'])

    def test_fit_cannot_select_unadmitted_candidate_even_with_higher_score(self):
        self.require()
        envelope = {'payload': {'candidates': [
            {'id':'invalid','admitted':False,'score':1.0},
            {'id':'valid','admitted':True,'score':0.5},
        ]}, 'trace': []}
        out = projection.apply_operator('FIT', envelope)
        self.assertEqual('valid', out['payload']['fit_selection']['id'])

    def test_cooperation_and_tool_trace_remain_attributed(self):
        self.require()
        envelope = {'payload': {}, 'trace': []}
        out = projection.apply_operator('TRACE_TOOL', envelope, tool_id='semantic-audit', purpose='compare', provenance='GSFL v0.1')
        out = projection.apply_operator('COOPERATE', out, partner_id='human', action='review', detail='checked machine proposal')
        self.assertEqual('semantic-audit', out['payload']['tools'][0]['tool_id'])
        self.assertEqual('human', out['payload']['cooperation_steps'][0]['partner_id'])

    def test_proverb_operator_preserves_synthetic_provenance(self):
        self.require()
        out = projection.apply_operator('GENERATE_PROVERB_FIXTURE', {'payload': {}, 'trace': []}, source_text='Many windows can face one field.', context='calibration')
        fixture = out['payload']['proverb_fixture']
        self.assertEqual('SYNTHETIC', fixture['source_status'])
        self.assertFalse(fixture['claims_single_true_meaning'])

    def test_confound_audit_flags_truth_and_learning_shortcuts(self):
        self.require()
        env = {'payload': {'claims': {'fit_is_truth': True, 'output_proves_learning': True}}, 'trace': []}
        out = projection.apply_operator('AUDIT_CONFOUNDS', env)
        ids = {row['id'] for row in out['payload']['confounds']}
        self.assertIn('FIT_SCORE_AS_TRUTH', ids)
        self.assertIn('OUTPUT_AS_LEARNING_EVIDENCE', ids)

    def test_validate_profile_passes(self):
        self.require()
        data = projection.load_profile(PROFILE)
        report = projection.validate_profile(data)
        self.assertTrue(report['valid'])
        self.assertEqual(23, report['operator_count'])

if __name__ == '__main__':
    unittest.main()
