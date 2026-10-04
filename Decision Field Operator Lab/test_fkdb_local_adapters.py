from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib import error, request


HERE = Path(__file__).resolve().parent
TOOLS = HERE / "tools"
sys.path.insert(0, str(TOOLS))

try:
    adapters = importlib.import_module("fkdb_local_adapters")
except ModuleNotFoundError:
    adapters = None

try:
    bridge = importlib.import_module("fkdb_local_tool_bridge")
except ModuleNotFoundError:
    bridge = None


def carrier(carrier_id: str = "adapter-fixture-1", payload: str = "LOCAL") -> dict:
    return {
        "schema": "fkdb/tool-carrier/v1",
        "carrier_id": carrier_id,
        "tool_id": "fixture-adapter",
        "tool_version": "1",
        "adapter_kind": "LOCAL_FILE",
        "locality": "LOCAL_FILE",
        "source_identity": "fixture:adapter:1",
        "source_version": "1",
        "retrieved_at": "2026-10-04T21:30:00Z",
        "payload_type": "text/plain",
        "payload": payload,
        "content_hash": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "provenance": {"provider": "fixture", "source": "unit-test"},
        "authority_scope": "TEST_ONLY",
        "evidence_status": "UNVERIFIED_FIXTURE",
        "obligation": "TEST_LOCAL_ADAPTER",
        "relations": [],
        "cost": {"units": 1},
        "loss": [],
        "remainder": [],
        "recovery_path": "recreate fixture",
    }


class FixtureAdapter:
    tool_id = "fixture-adapter"

    def descriptor(self, context):
        return {
            "tool_id": self.tool_id,
            "locality": "LOCAL_FILE",
            "state": "AVAILABLE",
            "capabilities": ["COLLECT"],
            "unresolved_requirements": [],
        }

    def collect(self, request_value, context):
        return {
            "status": "COLLECTED",
            "carriers": [carrier()],
            "remainder": [],
            "cost": {"files_scanned": 1, "bytes_read": len(b"LOCAL")},
        }


class EscapeAdapter(FixtureAdapter):
    tool_id = "escape-adapter"

    def collect(self, request_value, context):
        outside = Path(request_value["options"]["outside"])
        context.resolve_read_path(outside)
        raise AssertionError("outside path must not be admitted")


class PartialAdapter(FixtureAdapter):
    tool_id = "partial-adapter"

    def collect(self, request_value, context):
        return {
            "status": "PARTIAL",
            "carriers": [carrier("partial-carrier")],
            "remainder": ["ADAPTER_FILE_LIMIT_REACHED"],
            "cost": {
                "files_scanned": context.max_files,
                "bytes_read": context.max_bytes,
            },
        }


class InvalidCarrierAdapter(FixtureAdapter):
    tool_id = "invalid-carrier"

    def collect(self, request_value, context):
        value = carrier("invalid")
        value["content_hash"] = "0" * 64
        return {
            "status": "COLLECTED",
            "carriers": [value],
            "remainder": [],
            "cost": {"files_scanned": 1, "bytes_read": 1},
        }


@unittest.skipIf(adapters is None or bridge is None, "local adapter registry not implemented")
class FkdbLocalAdapterBehaviorTests(unittest.TestCase):
    def make_policy(self, root: Path, *, adapter_config=None):
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
                "adapter_max_files": 4,
                "adapter_max_bytes": 4096,
                "adapters": adapter_config or [],
            }
        )

    def test_registry_rejects_duplicate_adapter_ids(self):
        registry = adapters.LocalAdapterRegistry()
        registry.register(FixtureAdapter())
        with self.assertRaisesRegex(ValueError, "duplicate adapter"):
            registry.register(FixtureAdapter())

    def test_unknown_adapter_is_explicitly_unavailable(self):
        registry = adapters.LocalAdapterRegistry()
        with tempfile.TemporaryDirectory() as tmp:
            policy = self.make_policy(Path(tmp))
            result = registry.collect(
                "missing-adapter",
                {"root": str(Path(tmp)), "options": {}},
                policy,
            )
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertEqual(result["carriers"], [])
        self.assertIn("LOCAL_ADAPTER_UNAVAILABLE", result["remainder"])

    def test_collection_root_is_resolved_through_bridge_policy(self):
        registry = adapters.LocalAdapterRegistry()
        registry.register(EscapeAdapter())
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            policy = self.make_policy(Path(tmp))
            with self.assertRaises(PermissionError):
                registry.collect(
                    "escape-adapter",
                    {
                        "root": str(Path(tmp)),
                        "options": {"outside": str(Path(outside) / "x")},
                    },
                    policy,
                )

    def test_partial_result_preserves_explicit_limits_and_remainder(self):
        registry = adapters.LocalAdapterRegistry()
        registry.register(PartialAdapter())
        with tempfile.TemporaryDirectory() as tmp:
            policy = self.make_policy(Path(tmp))
            result = registry.collect(
                "partial-adapter",
                {"root": str(Path(tmp)), "options": {}},
                policy,
            )
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["cost"]["files_scanned"], 4)
        self.assertEqual(result["cost"]["bytes_read"], 4096)
        self.assertIn("ADAPTER_FILE_LIMIT_REACHED", result["remainder"])

    def test_result_carriers_are_validated_before_return(self):
        registry = adapters.LocalAdapterRegistry()
        registry.register(InvalidCarrierAdapter())
        with tempfile.TemporaryDirectory() as tmp:
            policy = self.make_policy(Path(tmp))
            with self.assertRaisesRegex(ValueError, "content_hash"):
                registry.collect(
                    "invalid-carrier",
                    {"root": str(Path(tmp)), "options": {}},
                    policy,
                )

    def test_default_production_policy_enables_no_adapters(self):
        policy_path = HERE / "fkdb" / "tools" / "local-tool-policy.json"
        value = json.loads(policy_path.read_text(encoding="utf-8"))
        self.assertEqual(value["adapters"], [])
        self.assertGreater(value["adapter_max_files"], 0)
        self.assertGreater(value["adapter_max_bytes"], 0)

    def test_collect_endpoint_requires_token_and_validates_carrier(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text("<h1>FKDB</h1>", encoding="utf-8")
            policy = self.make_policy(
                root,
                adapter_config=[{"tool_id": "fixture-adapter", "enabled": True}],
            )
            registry = adapters.LocalAdapterRegistry()
            registry.register(FixtureAdapter())
            receipt = bridge.run_bridge(
                bind="127.0.0.1",
                port=0,
                web_root=root,
                policy=policy,
                adapter_registry=registry,
            )
            self.addCleanup(receipt.shutdown)

            payload = json.dumps(
                {
                    "tool_id": "fixture-adapter",
                    "root": str(root),
                    "options": {},
                }
            ).encode("utf-8")

            unauthorized = request.Request(
                receipt.origin + "/fkdb-tool-bridge/v1/collect",
                data=payload,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Origin": receipt.origin,
                },
            )
            with self.assertRaises(error.HTTPError) as ctx:
                request.urlopen(unauthorized)
            self.assertEqual(ctx.exception.code, 403)

            admitted = request.Request(
                receipt.origin + "/fkdb-tool-bridge/v1/collect",
                data=payload,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Origin": receipt.origin,
                    "X-FKDB-Bridge-Token": receipt.token,
                },
            )
            result = json.loads(request.urlopen(admitted).read())
            self.assertEqual(result["schema"], "fkdb/local-tool-collection/v1")
            self.assertEqual(result["status"], "COLLECTED")
            self.assertEqual(result["carriers"][0]["carrier_id"], "adapter-fixture-1")


class FkdbLocalAdapterRedContractTests(unittest.TestCase):
    def test_adapter_module_exists(self):
        self.assertIsNotNone(
            adapters,
            "fkdb_local_adapters module must exist before Plan B collection can begin",
        )


if __name__ == "__main__":
    unittest.main()
