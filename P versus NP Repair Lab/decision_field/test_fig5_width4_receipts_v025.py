from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

import fig5_width4_probe_v025 as probe


ROOT = Path(__file__).resolve().parent


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def file_sha256(name: str) -> str:
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


class Width4ReceiptIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load("FIG5_V025_WIDTH4_MANIFEST.json")
        cls.generate = load("FIG5_V025_WIDTH4_GENERATE.json")
        cls.verify = load("FIG5_V025_WIDTH4_VERIFY.json")
        cls.admit = load("FIG5_V025_WIDTH4_ADMIT.json")
        cls.analysis = load("FIG5_V025_WIDTH4_ANALYSIS.json")
        cls.posthoc = load("FIG5_V025_WIDTH4_POSTHOC.json")
        cls.close = load("FIG5_V025_WIDTH4_CLOSE_RECEIPT.json")
        cls.prefreeze = load("FIG5_V025_WIDTH4_PREFREEZE_RECEIPT.json")
        cls.hardening = load("FIG5_V025_WIDTH4_VALIDATION_HARDENING_RECEIPT.json")

    def test_validation_hardening_source_and_receipt_hashes_are_exact(self) -> None:
        frozen = self.prefreeze["source_identities"]
        historical = self.hardening["historical_frozen_sources"]
        self.assertEqual(historical["constructor_sha256"], frozen["constructor_sha256"])
        self.assertEqual(historical["runner_sha256_at_prefreeze"], frozen["runner_sha256"])
        self.assertEqual(historical["active_solver_sha256"], frozen["solver_sha256"])
        self.assertEqual(historical["constructor_sha256"], file_sha256("fig5_width4_family_v025.py"))
        self.assertEqual(historical["active_solver_sha256"], file_sha256("fig5_dp_mirror_v020.py"))
        self.assertEqual(
            self.hardening["hardened_sources"]["runner_sha256"],
            file_sha256("fig5_width4_probe_v025.py"),
        )
        receipt_files = {
            "manifest_sha256": "FIG5_V025_WIDTH4_MANIFEST.json",
            "generate_sha256": "FIG5_V025_WIDTH4_GENERATE.json",
            "verify_sha256": "FIG5_V025_WIDTH4_VERIFY.json",
            "admit_sha256": "FIG5_V025_WIDTH4_ADMIT.json",
            "analysis_sha256": "FIG5_V025_WIDTH4_ANALYSIS.json",
            "posthoc_sha256": "FIG5_V025_WIDTH4_POSTHOC.json",
        }
        for field, filename in receipt_files.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.hardening["sealed_scientific_receipts"][field],
                    file_sha256(filename),
                )

    def test_stage_chain_hashes_are_exact(self) -> None:
        self.assertEqual(self.generate["manifest_canonical_sha256"], canonical_sha256(self.manifest))
        self.assertEqual(self.verify["manifest_canonical_sha256"], canonical_sha256(self.manifest))
        self.assertEqual(self.verify["generate_canonical_sha256"], canonical_sha256(self.generate))
        self.assertEqual(self.admit["manifest_canonical_sha256"], canonical_sha256(self.manifest))
        self.assertEqual(self.admit["generate_canonical_sha256"], canonical_sha256(self.generate))
        self.assertEqual(self.admit["verify_canonical_sha256"], canonical_sha256(self.verify))
        self.assertEqual(self.analysis["inputs"]["admit_canonical_sha256"], canonical_sha256(self.admit))
        self.assertEqual(self.posthoc["inputs"]["admit_canonical_sha256"], canonical_sha256(self.admit))

    def test_close_receipt_hashes_every_sealed_artifact(self) -> None:
        expected = {
            "prefreeze_sha256": "FIG5_V025_WIDTH4_PREFREEZE_RECEIPT.json",
            "preregistration_sha256": "FIG5_V025_WIDTH4_PREREGISTRATION.json",
            "manifest_sha256": "FIG5_V025_WIDTH4_MANIFEST.json",
            "generate_sha256": "FIG5_V025_WIDTH4_GENERATE.json",
            "verify_sha256": "FIG5_V025_WIDTH4_VERIFY.json",
            "admit_sha256": "FIG5_V025_WIDTH4_ADMIT.json",
            "analysis_sha256": "FIG5_V025_WIDTH4_ANALYSIS.json",
            "posthoc_sha256": "FIG5_V025_WIDTH4_POSTHOC.json",
        }
        for field, filename in expected.items():
            with self.subTest(field=field):
                self.assertEqual(self.close["file_receipts"][field], file_sha256(filename))

    def test_stage_firewall_remains_visible_in_sealed_objects(self) -> None:
        self.assertFalse(self.manifest["generate_run"])
        self.assertFalse(self.manifest["verify_run"])
        self.assertFalse(self.manifest["admit_run"])
        self.assertFalse(self.generate["verify_run"])
        self.assertFalse(self.generate["admit_run"])
        self.assertFalse(self.verify["admit_run"])
        self.assertFalse(self.admit["analysis_run"])

    def test_bounded_result_is_not_promoted(self) -> None:
        self.assertEqual(self.analysis["status"], "WIDTH4_DENSITY4_INCONCLUSIVE_ADMISSION")
        self.assertFalse(self.analysis["success"])
        self.assertEqual(self.close["status"], self.analysis["status"])
        self.assertFalse(self.close["success"])
        self.assertIn("FIG5_RESULT != P_VS_NP_RESULT", self.close["boundaries"])
        self.assertIn("P ?= NP = OPEN", self.close["boundaries"])
        self.assertEqual(self.close["admit"]["admitted_by_n"]["12"], 4)
        self.assertEqual(self.close["admit"]["admitted_by_n"]["13"], 1)

    def test_analysis_rejects_tampered_admission_flags(self) -> None:
        tampered = copy.deepcopy(self.admit)
        for row in tampered["rows"]:
            row["admitted"] = True
            row["reason"] = "ACTIVE_RESOLVED_EQUALS_COMPLETE_TRUTH"

        with self.assertRaisesRegex(ValueError, "ADMIT rows do not match frozen admission rule"):
            probe.run_analyze(self.manifest, self.generate, self.verify, tampered)


if __name__ == "__main__":
    unittest.main()
