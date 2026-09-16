import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BRIDGE_PATH = ROOT / 'bridge.py'
CALIBRATION_PATH = ROOT / 'bridge_calibration.json'
EVIDENCE_PATH = ROOT / 'evidence' / 'issue43_bridge_calibration_result.json'


class BridgeEvidenceTests(unittest.TestCase):
    def test_frozen_issue43_carrier_is_exact_cli_output(self):
        self.assertTrue(EVIDENCE_PATH.exists(), 'frozen issue-43 bridge carrier must exist')
        execution = subprocess.run(
            [sys.executable, str(BRIDGE_PATH), str(CALIBRATION_PATH)],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        frozen = EVIDENCE_PATH.read_text(encoding='utf-8')
        self.assertEqual(execution.stdout, frozen)
        result = json.loads(frozen)
        self.assertEqual(result['schema'], 'hodge-deformation-bridge-result/v0')
        self.assertEqual(result['authority'], 'candidate-test-only')
        self.assertEqual(result['source']['signature_vector'], ['0', '0', '1'])
        self.assertEqual(result['bridge']['candidate_vector'], ['0', '0', '1'])
        self.assertFalse(result['consequence']['target_span_contained'])
        self.assertEqual(result['consequence']['separation_certificates'][0]['annihilating_covector'], ['0', '0', '1'])
        self.assertEqual(result['consequence']['separation_certificates'][0]['target_pairing'], '1')


if __name__ == '__main__':
    unittest.main()
