import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from run_rmapl_omega_audit import build_audit, canonical_audit_text

ROOT = Path(__file__).parent.parent
EVIDENCE = Path(__file__).parent / "evidence" / "RMAPL_OMEGA_RESULTS.json"
SCRIPT = Path(__file__).parent / "run_rmapl_omega_audit.py"

EXPECTED_CHECKS = {
    "omegaStrict": True,
    "decisionFieldRoundTrip": True,
    "s1ChronologyDistinct": True,
    "typedEvidenceNoAmplification": True,
    "lossyQuotientExplicit": True,
    "paretoBranchPreserved": True,
    "cycleBounded": True,
    "hodgeCeilingPreserved": True,
    "suggestionAuthorityPreserved": True,
}


class RmaplOmegaAuditTests(unittest.TestCase):
    def test_audit_is_deterministic_and_bounded(self):
        first = build_audit()
        second = build_audit()
        self.assertEqual(canonical_audit_text(first), canonical_audit_text(second))
        self.assertEqual(first["schema"], "rmapl-omega-audit/v0")
        self.assertIs(first["scientificValidation"], False)
        self.assertEqual(first["checks"], EXPECTED_CHECKS)

    def test_frozen_evidence_matches_current_audit_byte_for_byte(self):
        expected = EVIDENCE.read_text(encoding="utf-8")
        self.assertEqual(expected, canonical_audit_text(build_audit()))

    def test_cli_check_and_repeat_output(self):
        with tempfile.TemporaryDirectory() as directory:
            a = Path(directory) / "a.json"
            b = Path(directory) / "b.json"
            subprocess.run([sys.executable, str(SCRIPT), "--out", str(a)], check=True)
            subprocess.run([sys.executable, str(SCRIPT), "--out", str(b)], check=True)
            self.assertEqual(a.read_bytes(), b.read_bytes())
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS RMAPL Omega audit", completed.stdout)


if __name__ == "__main__":
    unittest.main()
