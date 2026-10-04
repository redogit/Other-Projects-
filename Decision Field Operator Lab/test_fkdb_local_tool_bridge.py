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
POLICY_PATH = HERE / "fkdb" / "tools" / "local-tool-policy.json"
sys.path.insert(0, str(TOOLS))

try:
    bridge = importlib.import_module("fkdb_local_tool_bridge")
except ModuleNotFoundError:
    bridge = None


def carrier(payload: str = "LOCAL") -> dict:
    return {
        "schema": "fkdb/tool-carrier/v1",
        "carrier_id": "bridge-fixture-1",
        "tool_id": "bridge-fixture",
        "tool_version": "1",
        "adapter_kind": "PORTABLE_IMPORT",
        "locality": "LOCALHOST",
        "source_identity": "fixture:bridge:1",
        "source_version": "1",
        "retrieved_at": "2026-10-04T16:40:00Z",
        "payload_type": "text/plain",
        "payload": payload,
        "content_hash": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "provenance": {"provider": "fixture", "source": "unit-test"},
        "authority_scope": "TEST_ONLY",
        "evidence_status": "UNVERIFIED_FIXTURE",
        "obligation": "TEST_LOCAL_BRIDGE",
        "relations": [],
        "cost": {"units": 1},
        "loss": [],
        "remainder": [],
        "recovery_path": "recreate fixture",
    }


@unittest.skipIf(bridge is None, "local bridge not implemented")
class FkdbLocalToolBridgeBehaviorTests(unittest.TestCase):
    def make_policy(self, root: Path, *, processes=None):
        return bridge.BridgePolicy.from_dict(
            {
                "schema": "fkdb/local-tool-policy/v1",
                "network_policy": "LOOPBACK_ONLY",
                "read_roots": [str(root)],
                "write_roots": [str(root)],
                "processes": processes or [],
                "max_import_bytes": 65536,
                "max_request_bytes": 65536,
                "environment_allowlist": [],
            }
        )

    def test_non_loopback_bind_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy = self.make_policy(Path(tmp))
            with self.assertRaises(ValueError):
                bridge.run_bridge(
                    bind="0.0.0.0",
                    port=0,
                    web_root=Path(tmp),
                    policy=policy,
                )

    def test_only_literal_loopback_urls_are_admitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy = self.make_policy(Path(tmp))
            self.assertEqual(
                policy.validate_loopback_url("http://127.0.0.1:8000/x"),
                "http://127.0.0.1:8000/x",
            )
            self.assertEqual(
                policy.validate_loopback_url("http://[::1]:8000/x"),
                "http://[::1]:8000/x",
            )
            for bad in (
                "http://localhost:8000/x",
                "http://localhost.evil.example/x",
                "http://192.168.1.2/x",
                "https://8.8.8.8/x",
            ):
                with self.subTest(url=bad), self.assertRaises(ValueError):
                    policy.validate_loopback_url(bad)

    def test_path_traversal_and_symlink_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            policy = self.make_policy(root)
            (root / "ok.txt").write_text("ok", encoding="utf-8")
            self.assertEqual(
                policy.resolve_allowed_path(root / "ok.txt", "READ"),
                (root / "ok.txt").resolve(),
            )
            with self.assertRaises(PermissionError):
                policy.resolve_allowed_path(root / ".." / Path(outside).name, "READ")

            link = root / "escape"
            try:
                link.symlink_to(Path(outside), target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable in this environment")
            with self.assertRaises(PermissionError):
                policy.resolve_allowed_path(link / "outside.txt", "READ")

    def test_process_is_deny_by_default_and_argv_is_not_shell_interpreted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = Path(sys.executable).resolve()
            script = root / "fixture.py"
            script.write_text("print('SAFE')\n", encoding="utf-8")

            denied = self.make_policy(root)
            with self.assertRaises(PermissionError):
                denied.validate_process(executable, [str(script)])

            allowed = self.make_policy(
                root,
                processes=[
                    {
                        "tool_id": "python-fixture",
                        "executable": str(executable),
                        "allowed_subcommands": [str(script.resolve())],
                        "working_roots": [str(root)],
                        "read_roots": [str(root)],
                        "write_roots": [],
                        "network_policy": "LOOPBACK_ONLY",
                        "time_limit": 5,
                        "memory_limit": 0,
                        "environment_allowlist": [],
                    }
                ],
            )
            grant = allowed.validate_process(
                executable, [str(script), "; echo PWNED"]
            )
            self.assertEqual(grant.executable, executable)
            self.assertEqual(grant.argv[-1], "; echo PWNED")
            self.assertFalse(grant.shell)

            with self.assertRaises(PermissionError):
                allowed.validate_process(
                    root / "python-substitute", [str(script)]
                )

    def test_bridge_token_origin_and_carrier_admission(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text("<h1>FKDB</h1>", encoding="utf-8")
            policy = self.make_policy(root)
            receipt = bridge.run_bridge(
                bind="127.0.0.1",
                port=0,
                web_root=root,
                policy=policy,
            )
            self.addCleanup(receipt.shutdown)

            self.assertNotIn(receipt.token, receipt.origin)
            status = json.loads(
                request.urlopen(receipt.origin + "/fkdb-tool-bridge/v1/status").read()
            )
            self.assertEqual(status["schema"], "fkdb/local-tool-bridge-status/v1")
            self.assertNotIn(receipt.token, json.dumps(status))

            body = json.dumps({"carrier": carrier()}).encode("utf-8")
            unauthorized = request.Request(
                receipt.origin + "/fkdb-tool-bridge/v1/import",
                data=body,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Origin": receipt.origin,
                },
            )
            with self.assertRaises(error.HTTPError) as ctx:
                request.urlopen(unauthorized)
            self.assertEqual(ctx.exception.code, 403)

            wrong_origin = request.Request(
                receipt.origin + "/fkdb-tool-bridge/v1/import",
                data=body,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Origin": "https://evil.example",
                    "X-FKDB-Bridge-Token": receipt.token,
                },
            )
            with self.assertRaises(error.HTTPError) as ctx:
                request.urlopen(wrong_origin)
            self.assertEqual(ctx.exception.code, 403)

            admitted = request.Request(
                receipt.origin + "/fkdb-tool-bridge/v1/import",
                data=body,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Origin": receipt.origin,
                    "X-FKDB-Bridge-Token": receipt.token,
                },
            )
            result = json.loads(request.urlopen(admitted).read())
            self.assertEqual(result["status"], "ADMITTED")
            self.assertEqual(result["carrier"]["carrier_id"], "bridge-fixture-1")

            invalid = carrier()
            invalid["content_hash"] = "0" * 64
            bad = request.Request(
                receipt.origin + "/fkdb-tool-bridge/v1/import",
                data=json.dumps({"carrier": invalid}).encode("utf-8"),
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Origin": receipt.origin,
                    "X-FKDB-Bridge-Token": receipt.token,
                },
            )
            with self.assertRaises(error.HTTPError) as ctx:
                request.urlopen(bad)
            self.assertEqual(ctx.exception.code, 400)

    def test_run_endpoint_executes_only_allowlisted_fixture_and_returns_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text("<h1>FKDB</h1>", encoding="utf-8")
            executable = Path(sys.executable).resolve()
            script = root / "fixture.py"
            script.write_text(
                "import sys\nprint('ARG=' + sys.argv[1])\n",
                encoding="utf-8",
            )
            policy = self.make_policy(
                root,
                processes=[
                    {
                        "tool_id": "python-fixture",
                        "executable": str(executable),
                        "allowed_subcommands": [str(script.resolve())],
                        "working_roots": [str(root)],
                        "read_roots": [str(root)],
                        "write_roots": [],
                        "network_policy": "LOOPBACK_ONLY",
                        "time_limit": 5,
                        "memory_limit": 0,
                        "environment_allowlist": [],
                    }
                ],
            )
            receipt = bridge.run_bridge(
                bind="127.0.0.1", port=0, web_root=root, policy=policy
            )
            self.addCleanup(receipt.shutdown)

            payload = {
                "executable": str(executable),
                "argv": [str(script), "; echo PWNED"],
                "obligation": "TEST_PROCESS_RECEIPT",
            }
            req = request.Request(
                receipt.origin + "/fkdb-tool-bridge/v1/run",
                data=json.dumps(payload).encode("utf-8"),
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Origin": receipt.origin,
                    "X-FKDB-Bridge-Token": receipt.token,
                },
            )
            result = json.loads(request.urlopen(req).read())
            carrier_result = result["carrier"]
            self.assertEqual(carrier_result["tool_id"], "python-fixture")
            self.assertEqual(carrier_result["locality"], "LOCAL_PROCESS")
            self.assertEqual(carrier_result["payload"]["exit_code"], 0)
            self.assertIn("ARG=; echo PWNED", carrier_result["payload"]["stdout"])
            self.assertEqual(carrier_result["obligation"], "TEST_PROCESS_RECEIPT")


class FkdbLocalToolBridgeRedContractTests(unittest.TestCase):
    def test_bridge_module_and_default_policy_exist(self):
        self.assertIsNotNone(
            bridge,
            "fkdb_local_tool_bridge module must exist before local tools can be exposed",
        )
        self.assertTrue(POLICY_PATH.is_file())


if __name__ == "__main__":
    unittest.main()
