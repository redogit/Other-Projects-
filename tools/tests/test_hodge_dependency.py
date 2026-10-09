"""Dependency boundary tests use real Git repositories, with no network access."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "hodge_dependency.py"


class HodgeDependencyTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(), "canonical dependency resolver is missing")
        spec = importlib.util.spec_from_file_location("hodge_dependency", MODULE)
        self.dependency = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.dependency)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.checkout = self.root / "relocated canonical checkout"
        self.checkout.mkdir()
        self.path = self.checkout / "research/span-lab/evidence/frozen.json"
        self.path.parent.mkdir(parents=True)
        self.raw = b'{"authority":"candidate-test-only","source":{"actions":[1,2]}}\n'
        self.path.write_bytes(self.raw)
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=Dependency Test", "-c", "user.email=test@example.invalid",
                 "commit", "-qm", "frozen canonical source")
        self.revision = self.git("rev-parse", "HEAD")
        self.lock = self.root / "hodge.lock.json"
        self.lock.write_text(json.dumps({
            "schema": "hodge-dependency/v1", "repository": "redogit/hodge",
            "revision": self.revision,
            "artifacts": {"issue43_bridge_calibration": {
                "path": "research/span-lab/evidence/frozen.json",
                "sha256": hashlib.sha256(self.raw).hexdigest(),
            }},
        }))
        self.addCleanup(patch.stopall)
        patch.object(self.dependency, "LOCK_PATH", self.lock).start()
        patch.object(self.dependency, "DEFAULT_CHECKOUT", self.root / "absent").start()
        patch.dict(os.environ, {"HODGE_REPOSITORY_ROOT": str(self.checkout)}).start()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.checkout), *args],
                                       text=True).strip()

    def test_relocated_checkout_preserves_exact_bytes_without_former_path(self):
        result = self.dependency.resolve_artifact("issue43_bridge_calibration")
        self.assertEqual(result, self.path)
        self.assertEqual(result.read_bytes(), self.raw)
        self.assertFalse((self.root / "Hodge Span Lab").exists())

    def test_missing_checkout_fails_with_explicit_fetch_instruction(self):
        with patch.dict(os.environ, {"HODGE_REPOSITORY_ROOT": str(self.root / "missing")}):
            with self.assertRaisesRegex(self.dependency.DependencyError, "hodge_dependency.py fetch"):
                self.dependency.resolve_artifact("issue43_bridge_calibration")

    def test_modified_artifact_at_correct_commit_is_rejected(self):
        self.path.write_bytes(self.raw + b" ")
        with self.assertRaisesRegex(self.dependency.DependencyError, "SHA-256"):
            self.dependency.resolve_artifact("issue43_bridge_calibration")

    def test_missing_artifact_is_rejected_without_old_path_fallback(self):
        self.path.unlink()
        old = self.root / "Hodge Span Lab/evidence/frozen.json"
        old.parent.mkdir(parents=True)
        old.write_bytes(self.raw)
        with self.assertRaisesRegex(self.dependency.DependencyError, "missing"):
            self.dependency.resolve_artifact("issue43_bridge_calibration")

    def test_same_bytes_at_unpinned_revision_are_rejected(self):
        self.git("-c", "user.name=Dependency Test", "-c", "user.email=test@example.invalid",
                 "commit", "--allow-empty", "-qm", "different revision")
        with self.assertRaisesRegex(self.dependency.DependencyError, "revision"):
            self.dependency.resolve_artifact("issue43_bridge_calibration")

    def test_unknown_artifact_is_rejected(self):
        with self.assertRaisesRegex(self.dependency.DependencyError, "Unknown artifact"):
            self.dependency.resolve_artifact("not-in-lock")

    def test_lock_path_escape_is_rejected(self):
        lock = json.loads(self.lock.read_text())
        lock["artifacts"]["issue43_bridge_calibration"]["path"] = "../escaped.json"
        self.lock.write_text(json.dumps(lock))
        with self.assertRaisesRegex(self.dependency.DependencyError, "relative path"):
            self.dependency.resolve_artifact("issue43_bridge_calibration")

    def test_symlink_escape_is_rejected(self):
        outside = self.root / "outside.json"
        outside.write_bytes(self.raw)
        self.path.unlink()
        self.path.symlink_to(outside)
        with self.assertRaisesRegex(self.dependency.DependencyError, "outside"):
            self.dependency.resolve_artifact("issue43_bridge_calibration")

    def test_fetch_reuses_verified_checkout_without_network(self):
        with patch.object(self.dependency, "_run_git", wraps=self.dependency._run_git) as git:
            self.assertEqual(self.dependency.fetch_dependency(), self.checkout)
        self.assertFalse(any("fetch" in call.args[1:] for call in git.call_args_list))

    def test_explicit_fetch_materializes_only_the_locked_revision(self):
        destination = self.root / "dependency-cache"
        with patch.dict(os.environ, {"HODGE_REPOSITORY_ROOT": str(destination)}), \
                patch.object(self.dependency, "FETCH_URL", str(self.checkout)):
            self.assertEqual(self.dependency.fetch_dependency(), destination)
            self.assertEqual(self.dependency.resolve_artifact("issue43_bridge_calibration").read_bytes(), self.raw)
        self.assertEqual(subprocess.check_output(
            ["git", "-C", str(destination), "rev-parse", "HEAD"], text=True).strip(), self.revision)

    def test_fetch_does_not_overwrite_modified_existing_artifact(self):
        altered = b"altered frozen evidence"
        self.path.write_bytes(altered)
        with self.assertRaisesRegex(self.dependency.DependencyError, "SHA-256"):
            self.dependency.fetch_dependency()
        self.assertEqual(self.path.read_bytes(), altered)

    def test_failed_fetch_leaves_no_partially_admitted_checkout(self):
        destination = self.root / "dependency-cache"
        with patch.dict(os.environ, {"HODGE_REPOSITORY_ROOT": str(destination)}), \
                patch.object(self.dependency, "FETCH_URL", str(self.root / "missing-origin")):
            with self.assertRaises(self.dependency.DependencyError):
                self.dependency.fetch_dependency()
        self.assertFalse(destination.exists())

    def test_fetch_integrity_failure_leaves_no_admitted_checkout(self):
        destination = self.root / "dependency-cache"
        lock = json.loads(self.lock.read_text())
        lock["artifacts"]["issue43_bridge_calibration"]["sha256"] = "0" * 64
        self.lock.write_text(json.dumps(lock))
        with patch.dict(os.environ, {"HODGE_REPOSITORY_ROOT": str(destination)}), \
                patch.object(self.dependency, "FETCH_URL", str(self.checkout)):
            with self.assertRaisesRegex(self.dependency.DependencyError, "SHA-256"):
                self.dependency.fetch_dependency()
        self.assertFalse(destination.exists())

    def test_malformed_lock_types_fail_with_dependency_diagnostic(self):
        original = json.loads(self.lock.read_text())
        malformed = [None, [], {**original, "revision": 7},
                     {**original, "artifacts": {"fixture": None}},
                     {**original, "artifacts": {"fixture": {"path": 7, "sha256": "0" * 64}}},
                     {**original, "artifacts": {"fixture": {"path": "safe", "sha256": 7}}}]
        for value in malformed:
            with self.subTest(lock=value):
                self.lock.write_text(json.dumps(value))
                with self.assertRaises(self.dependency.DependencyError):
                    self.dependency.resolve_artifact("issue43_bridge_calibration")


if __name__ == "__main__":
    unittest.main()
