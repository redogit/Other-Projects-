import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class AuditTests(unittest.TestCase):
    def test_two_dev_replays_have_identical_scientific_outputs(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            cmd = [sys.executable, str(ROOT / "audit.py"), "--skip-reference-check"]
            subprocess.run(cmd + ["--out", a], check=True, cwd=ROOT)
            subprocess.run(cmd + ["--out", b], check=True, cwd=ROOT)
            for name in ("SUMMARY.json", "FRONTIER.json"):
                self.assertEqual((pathlib.Path(a) / name).read_bytes(), (pathlib.Path(b) / name).read_bytes())
            summary = json.loads((pathlib.Path(a) / "SUMMARY.json").read_text())
            self.assertEqual(summary["pareto_frontier_ids"], ["openloop.312", "pass08.fused_commit"])
            self.assertEqual(summary["verified_count"], 3)
            self.assertEqual(summary["invalid_rejected_count"], 1)


if __name__ == "__main__":
    unittest.main()
