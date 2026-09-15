import json
import sys
import unittest
from pathlib import Path

MLIR_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MLIR_ROOT / "python"))

from check_parity import compare, validate_sidecar
from emit_legacy_mlir import build_sidecar, emit_case


class CheckParityTests(unittest.TestCase):
    def test_selected_variable_mismatch_is_load_bearing(self):
        expected = {"status": "UNKNOWN", "selected_variable": 3}
        got = {"status": "UNKNOWN", "selected_variable": 2}
        self.assertEqual(
            compare(expected, got),
            ["selected_variable: expected 3, got 2"],
        )

    def test_incidental_seconds_are_not_compared(self):
        expected = {"status": "SAT", "seconds_total": 1.0, "states_evaluated": 3}
        got = {"status": "SAT", "seconds_total": 999.0, "states_evaluated": 3}
        self.assertEqual(compare(expected, got), [])

    def test_corrupted_mlir_digest_is_rejected(self):
        sidecar = {
            "schema": "pnp-mlir-parity-sidecar-v1",
            "mlir_sha256": "0" * 64,
            "scientific": {"case": "x", "status": "UNSAT"},
        }
        with self.assertRaisesRegex(ValueError, "MLIR digest mismatch"):
            validate_sidecar("module {}\n", sidecar)

    def test_all_frozen_aggregate_cases_roundtrip_through_bound_sidecar(self):
        manifest = json.loads(
            (MLIR_ROOT / "evidence" / "parity-v1" / "manifest.json").read_text()
        )
        seen = []
        for record in manifest["records"]:
            for case in record["scientific"]["cases"]:
                text = emit_case(case)
                sidecar = build_sidecar(text, case)
                reconstructed = validate_sidecar(text, sidecar)
                self.assertEqual(compare(case, reconstructed), [])
                seen.append((record["scientific"]["experiment"], case["case"]))
        self.assertEqual(len(seen), 6)

    def test_deliberate_frozen_case_corruption_is_detected(self):
        expected = {"case": "compiler_0", "status": "UNSAT", "states_evaluated": 7}
        corrupted = dict(expected, states_evaluated=8)
        self.assertEqual(
            compare(expected, corrupted),
            ["states_evaluated: expected 7, got 8"],
        )


if __name__ == "__main__":
    unittest.main()
