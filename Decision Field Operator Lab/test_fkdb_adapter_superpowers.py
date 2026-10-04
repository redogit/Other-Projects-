from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
TOOLS = HERE / "tools"
sys.path.insert(0, str(TOOLS))

try:
    module = importlib.import_module("fkdb_adapter_superpowers")
    bridge = importlib.import_module("fkdb_local_tool_bridge")
    registry_module = importlib.import_module("fkdb_local_adapters")
except ModuleNotFoundError:
    module = None
    bridge = None
    registry_module = None


@unittest.skipIf(
    module is None or bridge is None or registry_module is None,
    "Superpowers adapter not implemented",
)
class FkdbSuperpowersAdapterTests(unittest.TestCase):
    def make_policy(self, root: Path, *, max_files=16, max_bytes=65536):
        return bridge.BridgePolicy.from_dict(
            {
                "schema": "fkdb/local-tool-policy/v1",
                "network_policy": "LOOPBACK_ONLY",
                "read_roots": [str(root)],
                "write_roots": [],
                "processes": [],
                "max_import_bytes": 65536,
                "max_request_bytes": 65536,
                "environment_allowlist": [],
                "adapter_max_files": max_files,
                "adapter_max_bytes": max_bytes,
                "adapters": [{"tool_id": "superpowers", "enabled": True}],
            }
        )

    def registry(self):
        registry = registry_module.LocalAdapterRegistry()
        registry.register(module.SuperpowersAdapter())
        return registry

    def test_missing_superpowers_tree_is_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy = self.make_policy(root)
            descriptor = self.registry().descriptors(policy)[0]
            self.assertEqual(descriptor["state"], "UNAVAILABLE")
            result = self.registry().collect(
                "superpowers", {"root": str(root), "options": {}}, policy
            )
            self.assertEqual(result["status"], "UNAVAILABLE")
            self.assertIn("SUPERPOWERS_ARTIFACTS_NOT_FOUND", result["remainder"])

    def test_specs_plans_and_progress_are_distinguished_and_ordered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs = root / "docs" / "superpowers" / "specs"
            plans = root / "docs" / "superpowers" / "plans"
            specs.mkdir(parents=True)
            plans.mkdir(parents=True)
            (specs / "b.md").write_text("# Spec B\n", encoding="utf-8")
            (specs / "a.md").write_text("# Spec A\n", encoding="utf-8")
            (plans / "z-plan.md").write_text("# Plan Z\n", encoding="utf-8")
            (plans / "z-plan-progress.md").write_text("# Progress\n", encoding="utf-8")

            policy = self.make_policy(root)
            result = self.registry().collect(
                "superpowers", {"root": str(root), "options": {}}, policy
            )
            self.assertEqual(result["status"], "COLLECTED")
            self.assertEqual(
                [c["source_identity"] for c in result["carriers"]],
                [
                    "docs/superpowers/plans/z-plan-progress.md",
                    "docs/superpowers/plans/z-plan.md",
                    "docs/superpowers/specs/a.md",
                    "docs/superpowers/specs/b.md",
                ],
            )
            kinds = [c["provenance"]["artifact_kind"] for c in result["carriers"]]
            self.assertEqual(kinds, ["progress", "plan", "spec", "spec"])
            self.assertTrue(
                all(c["authority_scope"] == "WORKFLOW_ARTIFACT_ONLY" for c in result["carriers"])
            )
            self.assertTrue(
                all(
                    c["evidence_status"] == "WORKFLOW_STATE_NOT_CLAIM_VERIFICATION"
                    for c in result["carriers"]
                )
            )

    def test_content_is_preserved_raw_and_hash_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs = root / "docs" / "superpowers" / "specs"
            specs.mkdir(parents=True)
            content = "# Approved design\nThis file says approved.\n"
            (specs / "approved.md").write_text(content, encoding="utf-8")
            policy = self.make_policy(root)
            result = self.registry().collect(
                "superpowers", {"root": str(root), "options": {}}, policy
            )
            carrier = result["carriers"][0]
            self.assertEqual(carrier["payload"], content)
            self.assertNotIn("approval", carrier)
            self.assertNotIn("verified", carrier["evidence_status"].lower())

    def test_symlinked_superpowers_tree_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            outside_root = Path(outside)
            (outside_root / "specs").mkdir()
            (outside_root / "specs" / "x.md").write_text("# X", encoding="utf-8")
            docs = root / "docs"
            docs.mkdir()
            link = docs / "superpowers"
            try:
                link.symlink_to(outside_root, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            policy = self.make_policy(root)
            with self.assertRaises(PermissionError):
                self.registry().collect(
                    "superpowers", {"root": str(root), "options": {}}, policy
                )

    def test_file_and_byte_limits_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs = root / "docs" / "superpowers" / "specs"
            specs.mkdir(parents=True)
            for name in ("a.md", "b.md", "c.md"):
                (specs / name).write_text("# " + name + "\n", encoding="utf-8")
            policy = self.make_policy(root, max_files=2)
            result = self.registry().collect(
                "superpowers", {"root": str(root), "options": {}}, policy
            )
            self.assertEqual(result["status"], "PARTIAL")
            self.assertEqual(len(result["carriers"]), 2)
            self.assertIn("SUPERPOWERS_FILE_LIMIT_REACHED", result["remainder"])

            policy = self.make_policy(root, max_bytes=2)
            result = self.registry().collect(
                "superpowers", {"root": str(root), "options": {}}, policy
            )
            self.assertEqual(result["status"], "PARTIAL")
            self.assertEqual(result["carriers"], [])
            self.assertIn("SUPERPOWERS_BYTE_LIMIT_REACHED", result["remainder"])


class FkdbSuperpowersAdapterRedContractTests(unittest.TestCase):
    def test_superpowers_adapter_module_exists(self):
        self.assertIsNotNone(
            module,
            "fkdb_adapter_superpowers module must exist before workflow artifacts can be collected",
        )


if __name__ == "__main__":
    unittest.main()
