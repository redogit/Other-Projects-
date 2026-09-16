import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BRIDGE_PATH = ROOT / 'bridge.py'
if BRIDGE_PATH.exists():
    spec = importlib.util.spec_from_file_location('hodge_bridge', BRIDGE_PATH)
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
else:
    bridge = None


def require_bridge():
    if bridge is None:
        raise AssertionError('bridge.py must exist and load')
    return bridge


def source(actions):
    return {
        'schema': 's1-deformation-source/v0',
        'source_record_id': 'fixture-s1-record',
        'initial_state': 's3-sample',
        'mirror_id': 'mirror:s3-sample',
        'shell': 's3-sample',
        'operator_version': "S'1-Ops v0",
        'actions': copy.deepcopy(actions),
    }


def hodge_template():
    return {
        'schema': 'hodge-span/v1',
        'ambient_dimension': 3,
        'basis': 'Synthetic e1,e2,e3; not a cohomology computation',
        'cycle_vectors': [[1, 0, 0], [2, 0, 0], [0, 1, 0]],
        'target_vectors': [[1, 1, 0], [0, 0, 1]],
    }


def identity_map():
    return {
        'schema': 's1-hodge-linear-map/v0',
        'source_basis': ['xw', 'yw', 'zw'],
        'target_basis': 'Synthetic e1,e2,e3; not a cohomology computation',
        'matrix': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        'interpretation': 'Synthetic calibration identity map only; not a geometric Hodge map.',
    }


class BridgeTests(unittest.TestCase):
    def test_bridge_module_exists(self):
        self.assertTrue(BRIDGE_PATH.exists())

    def test_signature_compresses_net_plane_counts_but_preserves_full_chronology(self):
        b = require_bridge()
        actions = [
            {'plane': 'zw', 'degrees': 1},
            {'plane': 'xw', 'degrees': 1},
            {'plane': 'zw', 'degrees': -1},
        ]
        original = source(actions)
        result = b.execute_bridge(original, identity_map(), hodge_template())
        self.assertEqual(result['source']['signature_basis'], ['xw', 'yw', 'zw'])
        self.assertEqual(result['source']['signature_vector'], ['1', '0', '0'])
        self.assertEqual(result['source']['actions'], actions)
        self.assertEqual(original, source(actions), 'bridge must not mutate source input')

    def test_synthetic_zw_calibration_yields_exact_missing_direction_certificate(self):
        b = require_bridge()
        result = b.execute_bridge(
            source([{'plane': 'zw', 'degrees': 1}]),
            identity_map(),
            hodge_template(),
        )
        self.assertEqual(result['schema'], 'hodge-deformation-bridge-result/v0')
        self.assertEqual(result['bridge']['candidate_vector'], ['0', '0', '1'])
        self.assertEqual(result['consequence']['tested_target_count'], 1)
        self.assertFalse(result['consequence']['target_span_contained'])
        self.assertEqual(result['consequence']['target_directions_outside_supplied_cycle_span'], 1)
        certs = result['consequence']['separation_certificates']
        self.assertEqual(len(certs), 1)
        self.assertEqual(certs[0]['target_index'], 0)
        self.assertNotEqual(certs[0]['target_pairing'], '0')
        self.assertIn('synthetic', result['claim_ceiling'].lower())
        self.assertIn('hodge conjecture', result['claim_ceiling'].lower())

    def test_bridge_replaces_template_targets_with_exactly_one_derived_candidate(self):
        b = require_bridge()
        result = b.execute_bridge(
            source([{'plane': 'zw', 'degrees': 1}]),
            identity_map(),
            hodge_template(),
        )
        self.assertEqual(result['hodge_input']['target_vectors'], [['0', '0', '1']])
        self.assertEqual(result['hodge_input']['cycle_vectors'], [['1', '0', '0'], ['2', '0', '0'], ['0', '1', '0']])

    def test_basis_mismatch_fails_closed(self):
        b = require_bridge()
        m = identity_map()
        m['target_basis'] = 'different basis'
        with self.assertRaisesRegex(ValueError, 'basis'):
            b.execute_bridge(source([{'plane': 'zw', 'degrees': 1}]), m, hodge_template())

    def test_invalid_deformation_move_fails_closed(self):
        b = require_bridge()
        for bad in [
            {'plane': 'xy', 'degrees': 1},
            {'plane': 'xw', 'degrees': 2},
            {'plane': 'xw', 'degrees': 0.5},
        ]:
            with self.subTest(bad=bad):
                with self.assertRaises((ValueError, TypeError)):
                    b.execute_bridge(source([bad]), identity_map(), hodge_template())

    def test_mapping_requires_exact_rational_entries_and_correct_dimensions(self):
        b = require_bridge()
        floating = identity_map()
        floating['matrix'][0][0] = 0.5
        with self.assertRaisesRegex(ValueError, 'exact|rational|float'):
            b.execute_bridge(source([{'plane': 'zw', 'degrees': 1}]), floating, hodge_template())

        wrong = identity_map()
        wrong['matrix'] = [[1, 0], [0, 1], [0, 0]]
        with self.assertRaisesRegex(ValueError, 'matrix|dimension'):
            b.execute_bridge(source([{'plane': 'zw', 'degrees': 1}]), wrong, hodge_template())

    def test_bridge_is_deterministic_and_provenance_hashed(self):
        b = require_bridge()
        s = source([{'plane': 'zw', 'degrees': 1}])
        m = identity_map()
        h = hodge_template()
        one = b.execute_bridge(s, m, h)
        two = b.execute_bridge(copy.deepcopy(s), copy.deepcopy(m), copy.deepcopy(h))
        self.assertEqual(one, two)
        for key in ['source_sha256', 'map_sha256', 'hodge_template_sha256']:
            self.assertRegex(one['provenance'][key], r'^[0-9a-f]{64}$')

    def test_no_hodge_class_or_proof_authority_is_promoted(self):
        b = require_bridge()
        result = b.execute_bridge(
            source([{'plane': 'zw', 'degrees': 1}]),
            identity_map(),
            hodge_template(),
        )
        text = json.dumps(result).lower()
        self.assertEqual(result['authority'], 'candidate-test-only')
        self.assertNotIn('proved hodge', text)
        self.assertNotIn('is_hodge_class', text)
        self.assertNotIn('algebraic_cycle_proved', text)
        self.assertIn('candidate direction', result['claim_ceiling'].lower())


if __name__ == '__main__':
    unittest.main()
