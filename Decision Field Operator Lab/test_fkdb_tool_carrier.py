from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
TOOLS = HERE / "tools"
SCHEMAS = HERE / "fkdb" / "tools"
sys.path.insert(0, str(TOOLS))

try:
    carrier_module = importlib.import_module("fkdb_tool_carrier")
except ModuleNotFoundError:
    carrier_module = None


def valid_carrier(payload: str = "HELLO") -> dict:
    raw = payload.encode("utf-8")
    return {
        "schema": "fkdb/tool-carrier/v1",
        "carrier_id": "carrier-1",
        "tool_id": "fixture",
        "tool_version": "1.0",
        "adapter_kind": "PORTABLE_IMPORT",
        "locality": "PORTABLE_IMPORT",
        "source_identity": "fixture:item:1",
        "source_version": "1",
        "retrieved_at": "2026-10-04T16:30:00Z",
        "payload_type": "text/plain",
        "payload": payload,
        "content_hash": hashlib.sha256(raw).hexdigest(),
        "provenance": {
            "provider": "fixture",
            "source": "unit-test",
        },
        "authority_scope": "TEST_ONLY",
        "evidence_status": "UNVERIFIED_FIXTURE",
        "obligation": "TEST_TOOL_CARRIER",
        "relations": [],
        "cost": {"units": 1},
        "loss": [],
        "remainder": [],
        "recovery_path": "recreate fixture",
    }


@unittest.skipIf(carrier_module is None, "fkdb_tool_carrier module not implemented")
class FkdbToolCarrierBehaviorTests(unittest.TestCase):
    def test_valid_carrier_round_trips_canonically(self):
        carrier = valid_carrier()
        validated = carrier_module.validate_tool_carrier(
            carrier, max_payload_bytes=1024
        )
        encoded_a = carrier_module.canonical_carrier_bytes(validated)
        encoded_b = carrier_module.canonical_carrier_bytes(validated)
        self.assertEqual(encoded_a, encoded_b)
        self.assertEqual(
            carrier_module.sha256_hex(carrier["payload"].encode("utf-8")),
            carrier["content_hash"],
        )

    def test_missing_provenance_evidence_or_recovery_is_rejected(self):
        for field in ("provenance", "evidence_status", "recovery_path"):
            with self.subTest(field=field):
                carrier = valid_carrier()
                del carrier[field]
                with self.assertRaises(ValueError):
                    carrier_module.validate_tool_carrier(
                        carrier, max_payload_bytes=1024
                    )

    def test_hash_mismatch_is_rejected(self):
        carrier = valid_carrier()
        carrier["content_hash"] = "0" * 64
        with self.assertRaises(ValueError):
            carrier_module.validate_tool_carrier(carrier, max_payload_bytes=1024)

    def test_payload_size_limit_is_rejected(self):
        with self.assertRaises(ValueError):
            carrier_module.validate_tool_carrier(
                valid_carrier("TOO LARGE"), max_payload_bytes=3
            )

    def test_unknown_locality_is_rejected(self):
        carrier = valid_carrier()
        carrier["locality"] = "MAGIC_REMOTE"
        with self.assertRaises(ValueError):
            carrier_module.validate_tool_carrier(carrier, max_payload_bytes=1024)

    def test_bundle_rejects_duplicate_ids_and_size_overflow(self):
        c1 = valid_carrier("ONE")
        c2 = valid_carrier("TWO")
        c2["content_hash"] = hashlib.sha256(b"TWO").hexdigest()
        bundle = {
            "schema": "fkdb/tool-bundle/v1",
            "manifest": {"bundle_id": "bundle-1"},
            "carriers": [c1, c2],
            "attachments": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bundle.json"
            path.write_text(json.dumps(bundle), encoding="utf-8")
            with self.assertRaises(ValueError):
                carrier_module.load_tool_bundle(path, max_bundle_bytes=100000)
            with self.assertRaises(ValueError):
                carrier_module.load_tool_bundle(path, max_bundle_bytes=4)

    def test_wrong_bundle_schema_is_rejected(self):
        bundle = {
            "schema": "fkdb/tool-bundle/v999",
            "manifest": {"bundle_id": "bad"},
            "carriers": [],
            "attachments": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bundle.json"
            path.write_text(json.dumps(bundle), encoding="utf-8")
            with self.assertRaises(ValueError):
                carrier_module.load_tool_bundle(path, max_bundle_bytes=10000)


class FkdbToolCarrierRedContractTests(unittest.TestCase):
    def test_module_and_interchange_schemas_exist(self):
        self.assertIsNotNone(
            carrier_module,
            "fkdb_tool_carrier module must exist before ToolCarrier can be admitted",
        )
        self.assertTrue((SCHEMAS / "tool-carrier.schema.json").is_file())
        self.assertTrue((SCHEMAS / "tool-bundle.schema.json").is_file())


if __name__ == "__main__":
    unittest.main()
