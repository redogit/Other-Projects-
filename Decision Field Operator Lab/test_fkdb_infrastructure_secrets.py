from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tools"))

from fkdb_adapter_railway import RailwayAdapter
from fkdb_adapter_supabase import SupabaseAdapter
from fkdb_cross_carrier import admit_tool_carriers, build_external_index_records
from fkdb_index import load_index, overlay_external_records
from fkdb_local_adapters import LocalAdapterRegistry
from fkdb_local_tool_bridge import BridgePolicy
from fkdb_tool_carrier import load_tool_bundle, validate_tool_carrier


SYNTHETIC_SECRET = '{"fixture_secret":"SYNTHETIC_FORBIDDEN_PAYLOAD"}\n'
VALID_SNAPSHOT = '{"state":"fixture","message":"credential names are not payload scanning"}\n'


def local_carrier(tool_id: str, source: str) -> dict:
    digest = hashlib.sha256(SYNTHETIC_SECRET.encode("utf-8")).hexdigest()
    return {
        "schema": "fkdb/tool-carrier/v1",
        "carrier_id": tool_id + "-retained-fixture",
        "tool_id": tool_id,
        "tool_version": "fixture-v1",
        "adapter_kind": "LOCAL_FILE",
        "locality": "LOCAL_FILE",
        "source_identity": source,
        "source_version": digest,
        "retrieved_at": "2026-10-10T00:00:00Z",
        "payload_type": "application/json",
        "payload": SYNTHETIC_SECRET,
        "content_hash": digest,
        "provenance": {"provider": tool_id, "source_identity": source},
        "authority_scope": "LOCAL_ARTIFACT_ONLY",
        "evidence_status": "SYNTHETIC_FIXTURE_ONLY",
        "obligation": "TEST_RETAINED_CARRIER_ADMISSION",
        "relations": [],
        "cost": {"bytes_read": len(SYNTHETIC_SECRET.encode("utf-8"))},
        "loss": [],
        "remainder": [],
        "recovery_path": "recreate synthetic fixture",
    }


def retained_admission_record(tool_id: str, source: str) -> dict:
    carrier = local_carrier(tool_id, source)
    return {
        "source_carrier_id": carrier["carrier_id"],
        **{field: carrier[field] for field in (
            "tool_id", "source_identity", "source_version", "authority_scope",
            "evidence_status", "recovery_path", "relations", "payload_type", "payload", "provenance",
        )},
        "evidence_promoted": False,
    }


def retained_external_record(tool_id: str, source: str) -> dict:
    return {
        "id": "EXT-" + tool_id + "-retained-fixture",
        "title": source, "kind": "EXTERNAL_TOOL_CARRIER", "state": "IMPORTED",
        "domain": "CROSS_CARRIER", "carrier": "TOOL_CARRIER", "source_refs": [source],
        "provenance": {
            "relation": "IMPORTED_FROM_TOOL_CARRIER", "target": tool_id + "-retained-fixture",
            "status": "SOURCE_PRESERVED", "tool_id": tool_id, "authority_scope": "LOCAL_ARTIFACT_ONLY",
        },
        "evidence_status": "SYNTHETIC_FIXTURE_ONLY", "recovery_path": "recreate synthetic fixture",
        "recovery_display": "INSPECT IMPORTED SOURCE", "relations": [], "terms": ["SYNTHETIC", "FORBIDDEN"],
    }


class InfrastructureSecretExclusionTests(unittest.TestCase):
    def make_policy(self, root: Path) -> BridgePolicy:
        return BridgePolicy.from_dict({
            "schema": "fkdb/local-tool-policy/v1",
            "network_policy": "LOOPBACK_ONLY",
            "read_roots": [str(root)],
            "write_roots": [],
            "processes": [],
            "max_import_bytes": 65536,
            "max_request_bytes": 65536,
            "environment_allowlist": [],
            "adapter_max_files": 64,
            "adapter_max_bytes": 65536,
            "adapters": [
                {"tool_id": "supabase", "enabled": True},
                {"tool_id": "railway", "enabled": True},
            ],
        })

    def collect(self, root: Path, adapter, *, snapshots=()):
        registry = LocalAdapterRegistry()
        registry.register(adapter)
        return registry.collect(
            adapter.tool_id,
            {"root": str(root), "options": {"snapshot_paths": list(snapshots)}},
            self.make_policy(root),
        )

    def write(self, root: Path, relative: str, payload: str = SYNTHETIC_SECRET):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload.encode("utf-8"))
        return path

    @contextmanager
    def forbid_reads(self, paths):
        forbidden = {path.resolve() for path in paths}
        original = Path.read_bytes
        reads = []

        def guarded(path):
            resolved = path.resolve()
            self.assertNotIn(
                resolved, forbidden,
                "collector attempted to read a forbidden synthetic payload",
            )
            reads.append(resolved)
            return original(path)

        with patch.object(Path, "read_bytes", guarded):
            yield reads

    def assert_only_valid_artifacts(self, result, valid_sources):
        self.assertEqual(result["status"], "COLLECTED")
        carriers = result["carriers"]
        self.assertEqual({c["source_identity"] for c in carriers}, set(valid_sources))
        self.assertTrue(all("SYNTHETIC_FORBIDDEN_PAYLOAD" not in c["payload"] for c in carriers))
        records = build_external_index_records(admit_tool_carriers(carriers)["records"])
        self.assertEqual({r["source_refs"][0] for r in records}, set(valid_sources))
        self.assertTrue(all("SYNTHETIC" not in r["terms"] for r in records))

    def test_railway_original_explicit_snapshot_failures_are_excluded_before_read(self):
        for relative in (".env.json", "service_role.json", "secrets.txt"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                forbidden = self.write(root, relative)
                valid = self.write(root, "artifacts/deploy.json", VALID_SNAPSHOT)
                with self.forbid_reads([forbidden]) as reads:
                    result = self.collect(root, RailwayAdapter(), snapshots=[relative, "artifacts/deploy.json"])
                self.assertEqual(reads, [valid.resolve()])
                self.assert_only_valid_artifacts(result, ["artifacts/deploy.json"])
                self.assertEqual(result["cost"], {"files_scanned": 1, "bytes_read": len(VALID_SNAPSHOT.encode("utf-8"))})

    def test_supabase_original_nested_secret_failure_is_excluded_before_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            forbidden = self.write(root, "supabase/functions/secrets/credentials.json")
            valid = self.write(root, "supabase/config.toml", "project_id = 'fixture'\n")
            with self.forbid_reads([forbidden]) as reads:
                result = self.collect(root, SupabaseAdapter())
            self.assertEqual(reads, [valid.resolve()])
            self.assert_only_valid_artifacts(result, ["supabase/config.toml"])

    def test_original_forbidden_paths_never_become_validated_carriers_or_index_records(self):
        cases = (
            (RailwayAdapter(), (".env.json", "service_role.json", "secrets.txt"), "artifacts/deploy.json"),
            (SupabaseAdapter(), ("supabase/functions/secrets/credentials.json",), "supabase/config.toml"),
        )
        for adapter, forbidden_sources, valid_source in cases:
            with self.subTest(tool_id=adapter.tool_id), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                for source in forbidden_sources:
                    self.write(root, source)
                self.write(root, valid_source, VALID_SNAPSHOT)
                result = self.collect(root, adapter, snapshots=[*forbidden_sources, valid_source])
                records = build_external_index_records(admit_tool_carriers(result["carriers"])["records"])
                self.assertEqual(
                    {record["source_refs"][0] for record in records}, {valid_source},
                    "forbidden original paths reached validated carriers and index projection",
                )
                self.assert_only_valid_artifacts(result, [valid_source])

    def test_supabase_nested_case_and_filename_variants_are_excluded_before_read(self):
        forbidden_sources = (
            "supabase/functions/SeCrEtS/index.ts",
            "supabase/functions/CREDENTIALS/deno.json",
            "supabase/functions/hello/.ENV.production.json",
            "supabase/functions/hello/service-role.json",
            "supabase/functions/hello/serviceRole.json",
            "supabase/functions/hello/private_key.json",
            "supabase/migrations/20260101000000_credentials.sql",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            forbidden = [self.write(root, source) for source in forbidden_sources]
            self.write(root, "supabase/config.toml", "project_id = 'fixture'\n")
            self.write(root, "supabase/functions/hello/index.ts", "Deno.serve(() => new Response('ok'));\n")
            with self.forbid_reads(forbidden):
                result = self.collect(root, SupabaseAdapter())
            self.assert_only_valid_artifacts(result, ["supabase/config.toml", "supabase/functions/hello/index.ts"])

    def test_railway_nested_case_and_private_key_variants_are_excluded_before_read(self):
        forbidden_sources = (
            "artifacts/SeCrEtS/deploy.json",
            "artifacts/.credentials/deploy.ndjson",
            "artifacts/service.role.json",
            "artifacts/ServiceRole.json",
            "artifacts/private-key.json",
            "artifacts/id_ed25519.txt",
            "artifacts/deploy.json:SeCrEtS.txt",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            forbidden = [self.write(root, source) for source in forbidden_sources]
            self.write(root, "artifacts/deploy.log", "ordinary deployment fixture\n")
            with self.forbid_reads(forbidden):
                result = self.collect(root, RailwayAdapter(), snapshots=[*forbidden_sources, "artifacts/deploy.log"])
            self.assert_only_valid_artifacts(result, ["artifacts/deploy.log"])

    def test_prefixed_and_camel_secret_filenames_preserve_prior_exclusion(self):
        names = ("topsecret.json", "secretFile.json", "mysecrets.json", "myCredentials.json")
        for adapter, directory, valid_source in (
            (SupabaseAdapter(), "supabase/functions/hello", "supabase/config.toml"),
            (RailwayAdapter(), "artifacts", "Dockerfile"),
        ):
            with self.subTest(tool_id=adapter.tool_id), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                forbidden_sources = [directory + "/" + name for name in names]
                forbidden = [self.write(root, source) for source in forbidden_sources]
                self.write(root, valid_source, "ordinary fixture\n")
                with self.forbid_reads(forbidden):
                    result = self.collect(root, adapter, snapshots=forbidden_sources)
                self.assert_only_valid_artifacts(result, [valid_source])

    def make_symlink(self, link: Path, target: Path):
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")

    def test_railway_checks_secret_sensitive_symlink_alias_and_target_before_read(self):
        for alias, target in ((".env.json", "artifacts/ordinary.json"), ("artifacts/alias.json", "artifacts/secrets/deploy.json")):
            with self.subTest(alias=alias), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                target_path = self.write(root, target)
                self.make_symlink(root / alias, target_path)
                self.write(root, "Dockerfile", "FROM scratch\n")
                with self.forbid_reads([target_path]):
                    result = self.collect(root, RailwayAdapter(), snapshots=[alias])
                self.assert_only_valid_artifacts(result, ["Dockerfile"])

    def test_supabase_checks_secret_sensitive_symlink_alias_and_target_before_read(self):
        for alias, target in (
            ("supabase/functions/.env.json", "artifacts/ordinary.json"),
            ("supabase/functions/hello/alias.json", "artifacts/secrets/deploy.json"),
            ("supabase/seed.sql", "artifacts/credentials/seed.sql"),
        ):
            with self.subTest(alias=alias), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                target_path = self.write(root, target)
                self.make_symlink(root / alias, target_path)
                self.write(root, "supabase/config.toml", "project_id = 'fixture'\n")
                with self.forbid_reads([target_path]):
                    result = self.collect(root, SupabaseAdapter())
                self.assert_only_valid_artifacts(result, ["supabase/config.toml"])

    def test_railway_fixed_artifact_symlink_target_is_screened_before_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            forbidden = self.write(root, "private-key/deploy.txt")
            self.make_symlink(root / "Dockerfile", forbidden)
            self.write(root, ".railway/railway.ts", "export default { services: {} };\n")
            with self.forbid_reads([forbidden]):
                result = self.collect(root, RailwayAdapter())
            self.assert_only_valid_artifacts(result, [".railway/railway.ts"])

    def test_sensitive_ambient_parent_does_not_exclude_valid_project_artifacts(self):
        with tempfile.TemporaryDirectory(prefix="fkdb-secrets-credentials-") as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            self.write(root, "supabase/config.toml", "project_id = 'fixture'\n")
            self.write(root, "supabase/seed.sql", "select 1;\n")
            self.write(root, "supabase/migrations/20260101000000_init.sql", "select 1;\n")
            self.write(root, "supabase/functions/hello/deno.json", '{"imports":{}}\n')
            self.write(root, ".railway/railway.ts", "export default {};\n")
            self.write(root, "Dockerfile", "FROM scratch\n")
            self.write(root, "railway.json", '{"build":{}}\n')
            self.write(root, "artifacts/deploy.json", VALID_SNAPSHOT)
            self.assert_only_valid_artifacts(self.collect(root, SupabaseAdapter()), [
                "supabase/config.toml", "supabase/seed.sql",
                "supabase/migrations/20260101000000_init.sql", "supabase/functions/hello/deno.json",
            ])
            self.assert_only_valid_artifacts(self.collect(root, RailwayAdapter(), snapshots=["artifacts/deploy.json"]), [
                ".railway/railway.ts", "Dockerfile", "railway.json", "artifacts/deploy.json",
            ])

    def test_retained_forbidden_local_carriers_are_rejected_by_shared_validator(self):
        sources = (
            ".env.json", "service_role.json", "service-role.json", "serviceRole.json",
            "secrets.txt", "supabase/functions/SeCrEtS/credentials.json",
            "supabase\\functions\\CREDENTIALS\\index.ts", "private-key.json",
            "artifacts/client.PEM", "artifacts/id_rsa", "artifacts/.credentials/deploy.json",
            "artifacts/client.pem:export.txt", "artifacts/client.KEY:snapshot.json",
            "artifacts/CREDENTIALS. /deploy.json",
            "topsecret.json", "secretFile.json", "mysecrets.json", "myCredentials.json",
            "artifacts/deploy.json:secrets.txt", "artifacts/deploy.json:credentials.json",
        )
        for tool_id in ("supabase", "railway"):
            for source in sources:
                with self.subTest(tool_id=tool_id, source=source):
                    with self.assertRaisesRegex(ValueError, "secret-sensitive"):
                        validate_tool_carrier(local_carrier(tool_id, source), max_payload_bytes=65536)

    def test_retained_provenance_identity_cannot_hide_a_forbidden_source(self):
        for tool_id in ("supabase", "railway"):
            with self.subTest(tool_id=tool_id):
                carrier = local_carrier(tool_id, "artifacts/deploy.json")
                carrier["provenance"]["source_identity"] = "artifacts/secrets/deploy.json"
                with self.assertRaisesRegex(ValueError, "secret-sensitive"):
                    validate_tool_carrier(carrier, max_payload_bytes=65536)

    def test_declared_provider_origin_cannot_be_hidden_by_a_changed_tool_id(self):
        for provider in ("supabase", "railway"):
            for boundary in ("validator", "projection", "overlay"):
                with self.subTest(provider=provider, boundary=boundary):
                    if boundary == "validator":
                        record = local_carrier(provider, "secrets.txt")
                        record["tool_id"] = "fixture"
                        operation = lambda: validate_tool_carrier(record, max_payload_bytes=65536)
                    elif boundary == "projection":
                        record = retained_admission_record(provider, "secrets.txt")
                        record["tool_id"] = "fixture"
                        operation = lambda: build_external_index_records([record])
                    else:
                        record = retained_external_record(provider, "secrets.txt")
                        del record["provenance"]["tool_id"]
                        record["provenance"]["provider"] = provider
                        operation = lambda: overlay_external_records(load_index(), [record])
                    with self.assertRaisesRegex(ValueError, "secret-sensitive"):
                        operation()

    def test_ordinary_stream_names_remain_admissible(self):
        for tool_id in ("supabase", "railway"):
            with self.subTest(tool_id=tool_id):
                carrier = local_carrier(tool_id, "artifacts/deploy.json:export.txt")
                self.assertEqual(validate_tool_carrier(carrier, max_payload_bytes=65536), carrier)

    def test_retained_forbidden_bundle_import_is_rejected(self):
        for tool_id, source in (("railway", ".env.json"), ("supabase", "supabase/functions/secrets/credentials.json")):
            with self.subTest(tool_id=tool_id), tempfile.TemporaryDirectory() as tmp:
                bundle_path = Path(tmp) / "retained-bundle.json"
                bundle_path.write_text(json.dumps({
                    "schema": "fkdb/tool-bundle/v1", "manifest": {"bundle_id": "retained-fixture"},
                    "carriers": [local_carrier(tool_id, source)], "attachments": [],
                }), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "secret-sensitive"):
                    load_tool_bundle(bundle_path, max_bundle_bytes=65536)

    def test_relabelled_retained_sources_cannot_bypass_validation_or_bundle_import(self):
        for tool_id in ("supabase", "railway"):
            for boundary in ("validator", "bundle"):
                with self.subTest(tool_id=tool_id, boundary=boundary), tempfile.TemporaryDirectory() as tmp:
                    carrier = local_carrier(tool_id, ".env.json")
                    carrier["adapter_kind"] = carrier["locality"] = "PORTABLE_IMPORT"
                    if boundary == "validator":
                        with self.assertRaisesRegex(ValueError, "secret-sensitive"):
                            validate_tool_carrier(carrier, max_payload_bytes=65536)
                    else:
                        bundle_path = Path(tmp) / "relabelled-bundle.json"
                        bundle_path.write_text(json.dumps({
                            "schema": "fkdb/tool-bundle/v1", "manifest": {"bundle_id": "relabelled-fixture"},
                            "carriers": [carrier], "attachments": [],
                        }), encoding="utf-8")
                        with self.assertRaisesRegex(ValueError, "secret-sensitive"):
                            load_tool_bundle(bundle_path, max_bundle_bytes=65536)

    def test_retained_forbidden_carriers_cannot_reach_plan_e_index_admission(self):
        for tool_id, source in (("railway", "service_role.json"), ("supabase", "supabase/functions/secrets/credentials.json")):
            with self.subTest(tool_id=tool_id):
                with self.assertRaisesRegex(ValueError, "secret-sensitive"):
                    admit_tool_carriers([local_carrier(tool_id, source)])
                valid = local_carrier(tool_id, "artifacts/deploy.json")
                valid["payload"] = VALID_SNAPSHOT
                valid["content_hash"] = hashlib.sha256(VALID_SNAPSHOT.encode("utf-8")).hexdigest()
                records = build_external_index_records(admit_tool_carriers([valid])["records"])
                self.assertEqual(len(records), 1)
                self.assertEqual(records[0]["source_refs"], ["artifacts/deploy.json"])

    def test_retained_admission_records_cannot_bypass_index_projection(self):
        for tool_id in ("supabase", "railway"):
            for identity_field in ("source_identity", "provenance"):
                with self.subTest(tool_id=tool_id, identity_field=identity_field):
                    record = retained_admission_record(tool_id, "artifacts/deploy.json")
                    if identity_field == "provenance":
                        record["provenance"]["source_identity"] = "SeCrEtS/deploy.json"
                    else:
                        record[identity_field] = "SeCrEtS/deploy.json"
                    with self.assertRaisesRegex(ValueError, "secret-sensitive"):
                        build_external_index_records([record])
            records = build_external_index_records([retained_admission_record(tool_id, "artifacts/deploy.json")])
            self.assertEqual(records[0]["source_refs"], ["artifacts/deploy.json"])

    def test_retained_external_records_cannot_bypass_index_overlay(self):
        canonical = load_index()
        original_count = len(canonical["records"])
        for tool_id in ("supabase", "railway"):
            for identity_field in ("source_refs", "source_identity", "provenance"):
                with self.subTest(tool_id=tool_id, identity_field=identity_field):
                    record = retained_external_record(tool_id, "artifacts/deploy.json")
                    if identity_field == "source_refs":
                        record["source_refs"].append("SeCrEtS/deploy.json")
                    elif identity_field == "provenance":
                        record["provenance"]["source_identity"] = "SeCrEtS/deploy.json"
                    else:
                        record[identity_field] = "SeCrEtS/deploy.json"
                    with self.assertRaisesRegex(ValueError, "secret-sensitive"):
                        overlay_external_records(canonical, [record])
            overlaid = overlay_external_records(canonical, [retained_external_record(tool_id, "artifacts/deploy.json")])
            self.assertEqual(len(overlaid["records"]), original_count + 1)
            self.assertEqual(len(canonical["records"]), original_count)

    def test_registry_rejects_a_bypassed_forbidden_carrier(self):
        class BypassedRailwayAdapter:
            tool_id = "railway"

            def descriptor(self, context):
                return {"tool_id": self.tool_id}

            def collect(self, request, context):
                return {
                    "status": "COLLECTED", "carriers": [local_carrier(self.tool_id, "secrets.txt")],
                    "remainder": [], "cost": {"files_scanned": 1, "bytes_read": len(SYNTHETIC_SECRET)},
                }

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "secret-sensitive"):
                self.collect(Path(tmp), BypassedRailwayAdapter())


if __name__ == "__main__":
    unittest.main()
