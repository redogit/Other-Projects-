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
    module = importlib.import_module("fkdb_adapter_supabase")
    bridge = importlib.import_module("fkdb_local_tool_bridge")
    registry_module = importlib.import_module("fkdb_local_adapters")
except ModuleNotFoundError:
    module = None
    bridge = None
    registry_module = None


@unittest.skipIf(
    module is None or bridge is None or registry_module is None,
    "Supabase adapter not implemented",
)
class FkdbSupabaseAdapterTests(unittest.TestCase):
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
                "adapters": [{"tool_id": "supabase", "enabled": True}],
            }
        )

    def registry(self):
        registry = registry_module.LocalAdapterRegistry()
        registry.register(module.SupabaseAdapter())
        return registry

    def test_missing_supabase_project_is_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy = self.make_policy(root)
            descriptor = self.registry().descriptors(policy)[0]
            self.assertEqual(descriptor["state"], "UNAVAILABLE")
            self.assertIn(
                "SUPABASE_LOCAL_PROJECT_NOT_FOUND",
                descriptor["unresolved_requirements"],
            )

    def test_collects_config_migration_seed_and_function_artifacts_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            supabase = root / "supabase"
            (supabase / "migrations").mkdir(parents=True)
            (supabase / "functions" / "hello").mkdir(parents=True)
            (supabase / "config.toml").write_text(
                'project_id = "fixture"\n',
                encoding="utf-8",
            )
            (supabase / "migrations" / "20260101000000_init.sql").write_text(
                "create table t(id int);\n",
                encoding="utf-8",
            )
            (supabase / "seed.sql").write_text(
                "insert into t values (1);\n",
                encoding="utf-8",
            )
            (supabase / "functions" / "hello" / "index.ts").write_text(
                "Deno.serve(() => new Response('ok'))\n",
                encoding="utf-8",
            )
            (supabase / "functions" / "deno.json").write_text(
                '{"imports":{}}\n',
                encoding="utf-8",
            )

            policy = self.make_policy(root)
            result = self.registry().collect(
                "supabase",
                {"root": str(root), "options": {}},
                policy,
            )
            self.assertEqual(result["status"], "COLLECTED")
            identities = [c["source_identity"] for c in result["carriers"]]
            self.assertEqual(identities, sorted(identities))
            self.assertIn("supabase/config.toml", identities)
            self.assertIn(
                "supabase/migrations/20260101000000_init.sql",
                identities,
            )
            self.assertIn("supabase/seed.sql", identities)
            self.assertIn("supabase/functions/hello/index.ts", identities)
            kinds = {
                c["source_identity"]: c["provenance"]["artifact_kind"]
                for c in result["carriers"]
            }
            self.assertEqual(kinds["supabase/config.toml"], "config")
            self.assertEqual(
                kinds["supabase/migrations/20260101000000_init.sql"],
                "migration",
            )
            self.assertEqual(
                kinds["supabase/functions/hello/index.ts"],
                "edge-function",
            )
            for carrier in result["carriers"]:
                self.assertEqual(
                    carrier["authority_scope"],
                    "SUPABASE_LOCAL_PROJECT_ARTIFACT_ONLY",
                )
                self.assertEqual(
                    carrier["evidence_status"],
                    "CONFIG_OR_MIGRATION_NOT_APPLIED_STATE",
                )
                self.assertNotIn("APPLIED", carrier["provenance"].get("state", ""))

    def test_secret_like_files_are_not_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            supabase = root / "supabase"
            supabase.mkdir()
            (supabase / "config.toml").write_text("x=1\n", encoding="utf-8")
            (supabase / ".env").write_text("SERVICE_ROLE_KEY=secret\n", encoding="utf-8")
            (supabase / "service_role.key").write_text("secret\n", encoding="utf-8")
            policy = self.make_policy(root)
            result = self.registry().collect(
                "supabase",
                {"root": str(root), "options": {}},
                policy,
            )
            identities = [c["source_identity"] for c in result["carriers"]]
            self.assertNotIn("supabase/.env", identities)
            self.assertNotIn("supabase/service_role.key", identities)

    def test_symlinked_supabase_root_cannot_escape_allowed_root(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            external = Path(outside) / "supabase"
            external.mkdir()
            (external / "config.toml").write_text("x=1\n", encoding="utf-8")
            link = root / "supabase"
            try:
                link.symlink_to(external, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            policy = self.make_policy(root)
            with self.assertRaises(PermissionError):
                self.registry().collect(
                    "supabase",
                    {"root": str(root), "options": {}},
                    policy,
                )

    def test_collection_limits_return_partial_with_explicit_remainder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            supabase = root / "supabase"
            (supabase / "migrations").mkdir(parents=True)
            (supabase / "config.toml").write_text("x=1\n", encoding="utf-8")
            for i in range(4):
                (supabase / "migrations" / f"{i:014d}_x.sql").write_text(
                    "select 1;\n",
                    encoding="utf-8",
                )
            policy = self.make_policy(root, max_files=2)
            result = self.registry().collect(
                "supabase",
                {"root": str(root), "options": {}},
                policy,
            )
            self.assertEqual(result["status"], "PARTIAL")
            self.assertIn("SUPABASE_FILE_LIMIT_REACHED", result["remainder"])
            self.assertLessEqual(result["cost"]["files_scanned"], 2)


class FkdbSupabaseAdapterRedContractTests(unittest.TestCase):
    def test_supabase_adapter_module_exists(self):
        self.assertIsNotNone(
            module,
            "fkdb_adapter_supabase module must exist before Supabase artifacts can be collected",
        )


if __name__ == "__main__":
    unittest.main()
