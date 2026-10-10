from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from urllib import error, request

import test_fkdb_local_tool_bridge as bridge_harness
from test_fkdb_infrastructure_secrets import local_carrier


class InfrastructureSecretHttpImportTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(bridge_harness.bridge, "local bridge must be implemented")
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "index.html").write_text("<h1>synthetic fixture</h1>", encoding="utf-8")
        policy = bridge_harness.FkdbLocalToolBridgeBehaviorTests.make_policy(self, root)
        self.receipt = bridge_harness.bridge.run_bridge(
            bind="127.0.0.1", port=0, web_root=root, policy=policy
        )
        self.addCleanup(self.receipt.shutdown)

    def import_carrier(self, carrier):
        req = request.Request(
            self.receipt.origin + "/fkdb-tool-bridge/v1/import",
            data=json.dumps({"carrier": carrier}).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Origin": self.receipt.origin,
                "X-FKDB-Bridge-Token": self.receipt.token,
            },
        )
        try:
            response = request.urlopen(req, timeout=5)
        except error.HTTPError as denied:
            response = denied
        with response:
            return response.code, json.loads(response.read().decode("utf-8"))

    def test_retained_forbidden_infrastructure_local_files_are_denied_over_http(self):
        for tool_id in ("supabase", "railway"):
            for source in (".env.json", "supabase/functions/secrets/credentials.json"):
                with self.subTest(tool_id=tool_id, source=source):
                    status, body = self.import_carrier(local_carrier(tool_id, source))
                    self.assertEqual(
                        status, 400,
                        f"retained forbidden LOCAL_FILE carrier was {body.get('status')}",
                    )
                    self.assertEqual(body["status"], "DENIED")
                    self.assertIn("secret-sensitive", body["error"])
                    self.assertNotIn("carrier", body)
                    self.assertNotIn("SYNTHETIC_FORBIDDEN_PAYLOAD", json.dumps(body))

    def test_valid_infrastructure_local_file_counterparts_are_admitted_over_http(self):
        for tool_id, source in (
            ("supabase", "supabase/functions/hello/deno.json"),
            ("railway", "artifacts/deploy.json"),
        ):
            with self.subTest(tool_id=tool_id, source=source):
                # Use the same synthetic bytes: exclusion is based on source identity.
                carrier = local_carrier(tool_id, source)
                status, body = self.import_carrier(carrier)
                self.assertEqual(status, 200)
                self.assertEqual(body["schema"], "fkdb/local-tool-bridge-import/v1")
                self.assertEqual(body["status"], "ADMITTED")
                self.assertEqual(body["carrier"], carrier)
                self.assertEqual(body["remainder"], [])

    def test_relabelled_retained_sources_are_denied_over_http(self):
        for tool_id in ("supabase", "railway"):
            with self.subTest(tool_id=tool_id):
                carrier = local_carrier(tool_id, ".env.json")
                carrier["adapter_kind"] = carrier["locality"] = "PORTABLE_IMPORT"
                status, body = self.import_carrier(carrier)
                self.assertEqual(status, 400, "relabelled retained forbidden carrier was admitted")
                self.assertEqual(body["status"], "DENIED")
                self.assertIn("secret-sensitive", body["error"])
                self.assertNotIn("carrier", body)


if __name__ == "__main__":
    unittest.main()
