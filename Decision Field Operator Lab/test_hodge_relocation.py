"""The Hodge consumers retain frozen results from an alternate pinned checkout."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

from hodge_dependency import resolve_artifact


class HodgeRelocationTests(unittest.TestCase):
    def test_readers_accept_an_alternate_pinned_checkout(self):
        artifact = resolve_artifact("issue43_bridge_calibration")
        checkout = subprocess.run(
            ["git", "-C", str(artifact.parent), "rev-parse", "--show-toplevel"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        revision = subprocess.run(
            ["git", "-C", checkout, "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        with tempfile.TemporaryDirectory() as directory:
            relocated = Path(directory) / "hodge"
            subprocess.run(
                ["git", "clone", "--shared", "--no-checkout", checkout, str(relocated)],
                check=True, capture_output=True, text=True,
            )
            subprocess.run(
                ["git", "-C", str(relocated), "checkout", "--detach", revision],
                check=True, capture_output=True, text=True,
            )
            environment = {**os.environ, "HODGE_REPOSITORY_ROOT": str(relocated)}
            commands = (
                [sys.executable, str(HERE / "run_rmapl_omega_audit.py"), "--check"],
                [sys.executable, str(HERE / "run_rmapl_omega_stress.py"), "--check"],
                [
                    sys.executable, "-m", "unittest",
                    "test_omega_domain_adapters.OmegaDomainAdapterTests."
                    "test_hodge_frozen_bridge_preserves_candidate_authority_and_full_chronology",
                    "test_omega_domain_adapters.OmegaDomainAdapterTests."
                    "test_hodge_stronger_unknown_authority_fails_closed",
                ],
            )
            for command in commands:
                with self.subTest(reader=command[1:]):
                    completed = subprocess.run(
                        command, cwd=HERE, env=environment,
                        check=False, capture_output=True, text=True,
                    )
                    self.assertEqual(
                        completed.returncode, 0, completed.stdout + completed.stderr
                    )


if __name__ == "__main__":
    unittest.main()
