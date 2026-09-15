import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python"))

from emit_legacy_mlir import build_sidecar, emit_case


class EmitLegacyMLIRTests(unittest.TestCase):
    def test_unknown_remains_symbolic(self):
        text = emit_case({
            "case": "compiler_0",
            "status": "UNKNOWN",
            "planning_shortlist": [3, 1],
            "selected_variable": 3,
            "states_evaluated": 7,
            "maximum_depth": 2,
            "certificate_ids": ["node_0.json"],
            "costs": {"planning_row_operations": 3692},
            "provenance_digest": "abc123",
        })
        self.assertIn('#pnp_core.status<"UNKNOWN">', text)
        self.assertNotIn("status = 0", text)

    def test_emission_is_byte_deterministic(self):
        case = {
            "case": "compiler_1",
            "status": "SAT",
            "planning_shortlist": [2, 0],
            "selected_variable": 2,
            "states_evaluated": 3,
            "maximum_depth": 2,
            "certificate_ids": ["node_0.json", "node_1.json"],
            "costs": {"states_evaluated": 3, "planning_row_operations": 2312},
            "provenance_digest": "def456",
        }
        self.assertEqual(emit_case(case), emit_case(dict(reversed(list(case.items())))))

    def test_sidecar_binds_mlir_digest(self):
        text = emit_case({"case": "x", "status": "BOUND", "states_evaluated": 1})
        sidecar = build_sidecar(text, {"case": "x", "status": "BOUND"})
        self.assertEqual(sidecar["schema"], "pnp-mlir-parity-sidecar-v1")
        self.assertEqual(len(sidecar["mlir_sha256"]), 64)
        self.assertEqual(sidecar["scientific"]["status"], "BOUND")


if __name__ == "__main__":
    unittest.main()
