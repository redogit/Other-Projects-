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
    module = importlib.import_module("fkdb_adapter_mathbox")
except ModuleNotFoundError:
    module = None

try:
    bridge = importlib.import_module("fkdb_local_tool_bridge")
    registry_module = importlib.import_module("fkdb_local_adapters")
except ModuleNotFoundError:
    bridge = None
    registry_module = None


@unittest.skipIf(
    module is None or bridge is None or registry_module is None,
    "Mathbox adapter not implemented",
)
class FkdbMathboxAdapterTests(unittest.TestCase):
    def make_policy(self, root: Path, *, max_files=8, max_bytes=65536):
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
                "adapters": [{"tool_id": "mathbox", "enabled": True}],
            }
        )

    def registry(self):
        registry = registry_module.LocalAdapterRegistry()
        registry.register(module.MathboxAdapter())
        return registry

    def test_no_mathbox_is_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy = self.make_policy(root)
            descriptor = self.registry().descriptors(policy)[0]
            self.assertEqual(descriptor["tool_id"], "mathbox")
            self.assertEqual(descriptor["state"], "UNAVAILABLE")
            result = self.registry().collect(
                "mathbox", {"root": str(root), "options": {}}, policy
            )
            self.assertEqual(result["status"], "UNAVAILABLE")
            self.assertEqual(result["carriers"], [])
            self.assertIn("MATHBOX_LEDGER_NOT_FOUND", result["remainder"])

    def test_config_and_events_become_ordered_raw_json_carriers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = root / ".mathbox"
            events = ledger / "events"
            events.mkdir(parents=True)
            (ledger / "config.json").write_text(
                '{"schema_version":1,"projection":"recorded-evidence-v1"}\n',
                encoding="utf-8",
            )
            (events / "000002.json").write_text(
                '{"event_id":"E000002","type":"evidence"}\n',
                encoding="utf-8",
            )
            (events / "000001.json").write_text(
                '{"event_id":"E000001","type":"claim"}\n',
                encoding="utf-8",
            )

            policy = self.make_policy(root)
            result = self.registry().collect(
                "mathbox", {"root": str(root), "options": {}}, policy
            )
            self.assertEqual(result["status"], "COLLECTED")
            identities = [c["source_identity"] for c in result["carriers"]]
            self.assertEqual(
                identities,
                [
                    ".mathbox/config.json",
                    ".mathbox/events/000001.json",
                    ".mathbox/events/000002.json",
                ],
            )
            self.assertTrue(
                all(c["authority_scope"] == "MATHBOX_RECORDED_STATE_ONLY" for c in result["carriers"])
            )
            self.assertTrue(
                all(
                    c["evidence_status"] == "MECHANICAL_LEDGER_RECORD_NOT_PROOF_AUDIT"
                    for c in result["carriers"]
                )
            )
            self.assertEqual(result["remainder"], [])
            self.assertEqual(result["cost"]["files_scanned"], 3)
            self.assertGreater(result["cost"]["bytes_read"], 0)

    def test_invalid_json_is_explicit_remainder_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = root / ".mathbox"
            events = ledger / "events"
            events.mkdir(parents=True)
            (ledger / "config.json").write_text('{"schema_version":1}\n', encoding="utf-8")
            (events / "000001.json").write_text("{broken", encoding="utf-8")
            policy = self.make_policy(root)
            result = self.registry().collect(
                "mathbox", {"root": str(root), "options": {}}, policy
            )
            self.assertEqual(result["status"], "PARTIAL")
            self.assertEqual(len(result["carriers"]), 1)
            self.assertTrue(
                any(item.startswith("MATHBOX_INVALID_JSON:") for item in result["remainder"])
            )

    def test_symlinked_mathbox_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            outside_root = Path(outside)
            (outside_root / "config.json").write_text('{"schema_version":1}', encoding="utf-8")
            link = root / ".mathbox"
            try:
                link.symlink_to(outside_root, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            policy = self.make_policy(root)
            with self.assertRaises(PermissionError):
                self.registry().collect(
                    "mathbox", {"root": str(root), "options": {}}, policy
                )

    def test_file_limit_is_partial_and_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = root / ".mathbox"
            events = ledger / "events"
            events.mkdir(parents=True)
            (ledger / "config.json").write_text('{"schema_version":1}\n', encoding="utf-8")
            for i in range(1, 5):
                (events / f"{i:06d}.json").write_text(
                    json.dumps({"event_id": f"E{i:06d}", "type": "claim"}) + "\n",
                    encoding="utf-8",
                )
            policy = self.make_policy(root, max_files=2)
            result = self.registry().collect(
                "mathbox", {"root": str(root), "options": {}}, policy
            )
            self.assertEqual(result["status"], "PARTIAL")
            self.assertEqual(len(result["carriers"]), 2)
            self.assertEqual(result["cost"]["files_scanned"], 2)
            self.assertIn("MATHBOX_FILE_LIMIT_REACHED", result["remainder"])

    def test_mathbox_labels_are_not_promoted_to_proved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = root / ".mathbox"
            events = ledger / "events"
            events.mkdir(parents=True)
            (ledger / "config.json").write_text('{"schema_version":1}\n', encoding="utf-8")
            (events / "000001.json").write_text(
                '{"state":"proof-recorded","type":"evidence"}\n',
                encoding="utf-8",
            )
            policy = self.make_policy(root)
            result = self.registry().collect(
                "mathbox", {"root": str(root), "options": {}}, policy
            )
            serialized = json.dumps(result)
            self.assertNotIn('"proved"', serialized)
            self.assertIn("proof-recorded", serialized)


class FkdbMathboxAdapterRedContractTests(unittest.TestCase):
    def test_mathbox_adapter_module_exists(self):
        self.assertIsNotNone(
            module,
            "fkdb_adapter_mathbox module must exist before Mathbox can be collected",
        )


if __name__ == "__main__":
    unittest.main()
