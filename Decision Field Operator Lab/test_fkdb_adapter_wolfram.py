from __future__ import annotations

import base64
import hashlib
import importlib
from pathlib import Path
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
TOOLS = HERE / "tools"
sys.path.insert(0, str(TOOLS))

try:
    module = importlib.import_module("fkdb_adapter_wolfram")
    bridge = importlib.import_module("fkdb_local_tool_bridge")
    registry_module = importlib.import_module("fkdb_local_adapters")
except ModuleNotFoundError:
    module = None
    bridge = None
    registry_module = None


@unittest.skipIf(
    module is None or bridge is None or registry_module is None,
    "Wolfram adapter not implemented",
)
class FkdbWolframAdapterTests(unittest.TestCase):
    def make_policy(self, root: Path, *, max_bytes=65536):
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
                "adapter_max_files": 8,
                "adapter_max_bytes": max_bytes,
                "adapters": [{"tool_id": "wolfram", "enabled": True}],
            }
        )

    def registry(self, adapter):
        registry = registry_module.LocalAdapterRegistry()
        registry.register(adapter)
        return registry

    def test_text_wolfram_artifact_is_collected_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "Expand[(x+y)^2]\n"
            (root / "probe.wl").write_bytes(content.encode("utf-8"))
            adapter = module.WolframAdapter(which_fn=lambda _: None)
            policy = self.make_policy(root)
            result = self.registry(adapter).collect(
                "wolfram",
                {
                    "root": str(root),
                    "options": {"mode": "artifact", "path": "probe.wl"},
                },
                policy,
            )
            self.assertEqual(result["status"], "COLLECTED")
            carrier = result["carriers"][0]
            self.assertEqual(carrier["payload"], content)
            self.assertEqual(carrier["source_version"], hashlib.sha256(content.encode()).hexdigest())
            self.assertEqual(carrier["authority_scope"], "WOLFRAM_ARTIFACT_ONLY")
            self.assertEqual(carrier["evidence_status"], "ARTIFACT_NOT_EXECUTED")

    def test_binary_notebook_bytes_are_preserved_as_base64_with_raw_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = b"NB\x00\xff\x10"
            (root / "probe.nb").write_bytes(raw)
            adapter = module.WolframAdapter(which_fn=lambda _: None)
            policy = self.make_policy(root)
            result = self.registry(adapter).collect(
                "wolfram",
                {
                    "root": str(root),
                    "options": {"mode": "artifact", "path": "probe.nb"},
                },
                policy,
            )
            carrier = result["carriers"][0]
            self.assertEqual(carrier["payload"]["encoding"], "base64")
            self.assertEqual(base64.b64decode(carrier["payload"]["bytes"]), raw)
            self.assertEqual(carrier["source_version"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(carrier["provenance"]["artifact_sha256"], hashlib.sha256(raw).hexdigest())

    def test_missing_executable_does_not_advertise_process_capability(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter = module.WolframAdapter(which_fn=lambda _: None)
            policy = self.make_policy(root)
            descriptor = self.registry(adapter).descriptors(policy)[0]
            self.assertNotIn("LOCAL_PROCESS", descriptor["capabilities"])
            self.assertNotIn("RUN", descriptor["capabilities"])

    def test_discovered_wolframscript_is_degraded_not_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter = module.WolframAdapter(
                which_fn=lambda name: "/opt/Wolfram/wolframscript"
                if name == "wolframscript"
                else None
            )
            policy = self.make_policy(root)
            descriptor = self.registry(adapter).descriptors(policy)[0]
            self.assertEqual(descriptor["state"], "DEGRADED")
            self.assertIn("LOCAL_PROCESS_PROBE", descriptor["capabilities"])
            self.assertNotIn("RUN", descriptor["capabilities"])
            self.assertIn(
                "PROCESS_ISOLATION_BACKEND_UNAVAILABLE",
                descriptor["unresolved_requirements"],
            )

    def test_unsupported_or_oversized_artifact_is_rejected_or_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "x.txt").write_text("x", encoding="utf-8")
            (root / "big.wl").write_bytes(b"A" * 32)
            adapter = module.WolframAdapter(which_fn=lambda _: None)
            policy = self.make_policy(root, max_bytes=8)
            with self.assertRaisesRegex(ValueError, "extension"):
                self.registry(adapter).collect(
                    "wolfram",
                    {
                        "root": str(root),
                        "options": {"mode": "artifact", "path": "x.txt"},
                    },
                    policy,
                )
            result = self.registry(adapter).collect(
                "wolfram",
                {
                    "root": str(root),
                    "options": {"mode": "artifact", "path": "big.wl"},
                },
                policy,
            )
            self.assertEqual(result["status"], "PARTIAL")
            self.assertIn("WOLFRAM_ARTIFACT_BYTE_LIMIT_REACHED", result["remainder"])


class FkdbWolframAdapterRedContractTests(unittest.TestCase):
    def test_wolfram_adapter_module_exists(self):
        self.assertIsNotNone(
            module,
            "fkdb_adapter_wolfram module must exist before Wolfram artifacts can be collected",
        )


if __name__ == "__main__":
    unittest.main()
