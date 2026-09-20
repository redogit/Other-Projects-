import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from run_rmapl_omega_stress import (
    DEFAULT_SEED,
    STRESS_SCHEMA,
    build_stress_report,
    canonical_stress_text,
)

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "run_rmapl_omega_stress.py"
EVIDENCE = HERE / "evidence" / "RMAPL_OMEGA_STRESS_RESULTS.json"

EXPECTED_CASES = {
    "omegaCanonical": 2048,
    "parserMutation": 1536,
    "runtimeMatrix": 1024,
    "adapterAuthority": 512,
    "rmalResponseBoundary": 256,
}
EXPECTED_CHECKS = {
    "omegaCanonicalDeterministic": True,
    "omegaIdentitySensitive": True,
    "omegaTamperRejected": True,
    "parserMalformedRejected": True,
    "parserValidDeterministic": True,
    "runtimeDeterministic": True,
    "runtimeEvidenceBound": True,
    "runtimeMutationRejected": True,
    "runtimeQuotientSeparated": True,
    "runtimeCycleBounded": True,
    "adapterNoEvidenceAmplification": True,
    "adapterAuthorityCeilings": True,
    "rmalResponseBoundaryPreserved": True,
}


class RmaplOmegaStressTests(unittest.TestCase):
    def test_stress_report_is_deterministic_and_exercises_declared_case_counts(self):
        first = build_stress_report()
        second = build_stress_report()
        self.assertEqual(canonical_stress_text(first), canonical_stress_text(second))
        self.assertEqual(first["schema"], STRESS_SCHEMA)
        self.assertEqual(first["schema"], "rmapl-omega-stress/v0")
        self.assertEqual(first["seed"], DEFAULT_SEED)
        self.assertEqual(first["families"], EXPECTED_CASES)
        self.assertEqual(first["totalCases"], sum(EXPECTED_CASES.values()))
        self.assertEqual(first["checks"], EXPECTED_CHECKS)
        self.assertEqual(first["failures"], [])
        self.assertRegex(first["digestSha256"], r"^[0-9a-f]{64}$")
        self.assertIs(first["scientificValidation"], False)

    def test_stress_scale_multiplies_case_counts_without_changing_boundaries(self):
        report = build_stress_report(scale=2)
        self.assertEqual(
            report["families"],
            {name: count * 2 for name, count in EXPECTED_CASES.items()},
        )
        self.assertEqual(report["totalCases"], 2 * sum(EXPECTED_CASES.values()))
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(report["claimCeiling"], build_stress_report()["claimCeiling"])

    def test_frozen_stress_evidence_matches_current_report_byte_for_byte(self):
        actual = canonical_stress_text(build_stress_report())
        if not EVIDENCE.exists():
            self.fail("FROZEN_STRESS_EVIDENCE_MISSING\n" + actual)
        expected = EVIDENCE.read_text(encoding="utf-8")
        self.assertEqual(expected, actual)

    def test_cli_repeat_output_is_byte_identical_and_check_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            subprocess.run(
                [sys.executable, str(SCRIPT), "--out", str(first)],
                check=True,
            )
            subprocess.run(
                [sys.executable, str(SCRIPT), "--out", str(second)],
                check=True,
            )
            self.assertEqual(first.read_bytes(), second.read_bytes())

        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS RMAPL Omega stress", completed.stdout)

    def test_stress_evidence_keeps_rmal_response_successor_bounded(self):
        report = build_stress_report()
        boundary = report["rmalResponseBoundary"]
        self.assertEqual(boundary["rmalcCheck"], "NOT_REVALIDATED")
        self.assertEqual(boundary["rmalcCompile"], "NOT_REVALIDATED")
        self.assertEqual(boundary["rmalcAudit"], "NOT_REVALIDATED")
        self.assertIs(boundary["genericRuntime"], False)
        self.assertIn(
            "AUTHORED_CARRIER != GENERIC_RESPONSE_RUNTIME",
            boundary["boundaries"],
        )


if __name__ == "__main__":
    unittest.main()
