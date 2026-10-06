from __future__ import annotations

import importlib
from pathlib import Path
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
TOOLS = HERE / "tools"
sys.path.insert(0, str(TOOLS))

try:
    module = importlib.import_module("fkdb_adapter_railway")
    bridge = importlib.import_module("fkdb_local_tool_bridge")
    registry_module = importlib.import_module("fkdb_local_adapters")
except ModuleNotFoundError:
    module = None
    bridge = None
    registry_module = None


@unittest.skipIf(
    module is None or bridge is None or registry_module is None,
    "Railway adapter not implemented",
)
class FkdbRailwayAdapterTests(unittest.TestCase):
    def make_policy(self, root: Path, *, max_files=32, max_bytes=65536):
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
                "adapters": [{"tool_id": "railway", "enabled": True}],
            }
        )

    def registry(self):
        registry = registry_module.LocalAdapterRegistry()
        registry.register(module.RailwayAdapter())
        return registry

    def test_missing_railway_artifacts_are_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            descriptor = self.registry().descriptors(self.make_policy(root))[0]
            self.assertEqual(descriptor["state"], "UNAVAILABLE")
            self.assertIn(
                "RAILWAY_PROJECT_ARTIFACTS_NOT_FOUND",
                descriptor["unresolved_requirements"],
            )

    def test_current_iac_is_preserved_as_current_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            iac = root / ".railway"
            iac.mkdir()
            (iac / "railway.ts").write_text(
                "export default { services: {} }\n",
                encoding="utf-8",
            )
            result = self.registry().collect(
                "railway",
                {"root": str(root), "options": {}},
                self.make_policy(root),
            )
            self.assertEqual(result["status"], "COLLECTED")
            carrier = next(
                c for c in result["carriers"]
                if c["source_identity"] == ".railway/railway.ts"
            )
            self.assertEqual(
                carrier["provenance"]["artifact_kind"],
                "infrastructure-as-code",
            )
            self.assertEqual(
                carrier["provenance"]["railway_authority_status"],
                "CURRENT_IAC",
            )
            self.assertEqual(carrier["remainder"], [])
            self.assertEqual(
                carrier["evidence_status"],
                "DEPLOYMENT_ARTIFACT_NOT_LIVE_DEPLOYMENT_STATE",
            )

    def test_legacy_configs_are_retained_with_deprecation_and_cutoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "railway.json").write_text(
                '{"build":{"builder":"NIXPACKS"}}\n',
                encoding="utf-8",
            )
            (root / "railway.toml").write_text(
                '[build]\nbuilder = "NIXPACKS"\n',
                encoding="utf-8",
            )
            result = self.registry().collect(
                "railway",
                {"root": str(root), "options": {}},
                self.make_policy(root),
            )
            self.assertEqual(result["status"], "COLLECTED")
            legacy = [
                c for c in result["carriers"]
                if c["source_identity"] in {"railway.json", "railway.toml"}
            ]
            self.assertEqual(len(legacy), 2)
            for carrier in legacy:
                self.assertIn(
                    "RAILWAY_CONFIG_AS_CODE_DEPRECATED",
                    carrier["remainder"],
                )
                self.assertIn(
                    "RAILWAY_CONFIG_AS_CODE_CUTOFF_2026_12_01",
                    carrier["remainder"],
                )
                self.assertEqual(
                    carrier["provenance"]["railway_authority_status"],
                    "LEGACY_DEPRECATED_CONFIG",
                )

    def test_portable_log_snapshot_is_raw_artifact_not_live_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            logs = root / "artifacts"
            logs.mkdir()
            raw = "deploy snapshot line 1\nline 2\n"
            (logs / "deploy.log").write_bytes(raw.encode("utf-8"))
            result = self.registry().collect(
                "railway",
                {
                    "root": str(root),
                    "options": {
                        "snapshot_paths": ["artifacts/deploy.log"],
                    },
                },
                self.make_policy(root),
            )
            carrier = next(
                c for c in result["carriers"]
                if c["source_identity"] == "artifacts/deploy.log"
            )
            self.assertEqual(carrier["payload"], raw)
            self.assertEqual(
                carrier["provenance"]["artifact_kind"],
                "portable-deployment-snapshot",
            )
            self.assertFalse(carrier["provenance"]["live_state_observed"])

    def test_collection_order_bounds_and_symlink_confinement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
            (root / "nixpacks.toml").write_text("[phases]\n", encoding="utf-8")
            result = self.registry().collect(
                "railway",
                {"root": str(root), "options": {}},
                self.make_policy(root, max_files=1),
            )
            self.assertEqual(result["status"], "PARTIAL")
            self.assertIn("RAILWAY_FILE_LIMIT_REACHED", result["remainder"])
            self.assertEqual(result["cost"]["files_scanned"], 1)

        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            external = Path(outside) / "railway.ts"
            external.write_text("export default {}\n", encoding="utf-8")
            (root / ".railway").mkdir()
            link = root / ".railway" / "railway.ts"
            try:
                link.symlink_to(external)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            with self.assertRaises(PermissionError):
                self.registry().collect(
                    "railway",
                    {"root": str(root), "options": {}},
                    self.make_policy(root),
                )


class FkdbRailwayAdapterRedContractTests(unittest.TestCase):
    def test_railway_adapter_module_exists(self):
        self.assertIsNotNone(
            module,
            "fkdb_adapter_railway module must exist before Railway artifacts can be collected",
        )


if __name__ == "__main__":
    unittest.main()
