from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest
from urllib.parse import parse_qs, urlsplit


HERE = Path(__file__).resolve().parent
TOOLS = HERE / "tools"
sys.path.insert(0, str(TOOLS))

try:
    module = importlib.import_module("fkdb_adapter_zotero")
    bridge = importlib.import_module("fkdb_local_tool_bridge")
    registry_module = importlib.import_module("fkdb_local_adapters")
except ModuleNotFoundError:
    module = None
    bridge = None
    registry_module = None


class ZoteroFixtureHandler(BaseHTTPRequestHandler):
    requests = []
    mode = "normal"

    def log_message(self, format, *args):
        return

    def do_POST(self):
        type(self).requests.append(("POST", self.path))
        self.send_response(405)
        self.end_headers()

    def do_GET(self):
        type(self).requests.append(("GET", self.path))
        if type(self).mode == "redirect" and self.path.startswith("/api/users/0/items"):
            self.send_response(302)
            self.send_header("Location", "http://8.8.8.8/not-loopback")
            self.end_headers()
            return

        if self.path == "/api/":
            body = b'{"version":"7"}'
        elif self.path.startswith("/api/users/0/items?"):
            body = json.dumps(
                [
                    {
                        "key": "ITEMAAA1",
                        "version": 3,
                        "data": {
                            "key": "ITEMAAA1",
                            "itemType": "journalArticle",
                            "title": "First",
                            "citationKey": "Alpha2026",
                        },
                    },
                    {
                        "key": "ITEMBBB2",
                        "version": 4,
                        "data": {
                            "key": "ITEMBBB2",
                            "itemType": "book",
                            "title": "Second",
                        },
                    },
                ]
            ).encode("utf-8")
        else:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class FixtureServer:
    def __init__(self, *, mode="normal"):
        ZoteroFixtureHandler.requests = []
        ZoteroFixtureHandler.mode = mode
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), ZoteroFixtureHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def start(self):
        self.thread.start()
        return self

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


@unittest.skipIf(
    module is None or bridge is None or registry_module is None,
    "Zotero adapter not implemented",
)
class FkdbZoteroAdapterTests(unittest.TestCase):
    def make_policy(self, root: Path | None = None, *, max_files=8, max_bytes=65536):
        roots = [] if root is None else [str(root)]
        return bridge.BridgePolicy.from_dict(
            {
                "schema": "fkdb/local-tool-policy/v1",
                "network_policy": "LOOPBACK_ONLY",
                "read_roots": roots,
                "write_roots": [],
                "processes": [],
                "max_import_bytes": 65536,
                "max_request_bytes": 65536,
                "environment_allowlist": [],
                "adapter_max_files": max_files,
                "adapter_max_bytes": max_bytes,
                "adapters": [{"tool_id": "zotero", "enabled": True}],
            }
        )

    def registry(self, adapter):
        registry = registry_module.LocalAdapterRegistry()
        registry.register(adapter)
        return registry

    def unused_loopback_url(self):
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        return f"http://127.0.0.1:{port}"

    def test_unavailable_local_api_is_unavailable(self):
        adapter = module.ZoteroAdapter(base_url=self.unused_loopback_url(), timeout=0.2)
        policy = self.make_policy()
        descriptor = self.registry(adapter).descriptors(policy)[0]
        self.assertEqual(descriptor["state"], "UNAVAILABLE")
        self.assertIn("ZOTERO_LOCAL_API_UNAVAILABLE", descriptor["unresolved_requirements"])

    def test_read_only_local_api_search_preserves_item_keys_and_bounds_query(self):
        fixture = FixtureServer().start()
        self.addCleanup(fixture.close)
        adapter = module.ZoteroAdapter(base_url=fixture.base_url, timeout=1.0)
        policy = self.make_policy(max_files=1)
        descriptor = self.registry(adapter).descriptors(policy)[0]
        self.assertEqual(descriptor["state"], "AVAILABLE")

        result = self.registry(adapter).collect(
            "zotero",
            {
                "root": None,
                "options": {
                    "mode": "local-api",
                    "query": "Hodge cycles",
                    "limit": 50,
                },
            },
            policy,
        )
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(len(result["carriers"]), 1)
        self.assertIn("ZOTERO_RESULT_LIMIT_REACHED", result["remainder"])
        carrier = result["carriers"][0]
        self.assertEqual(carrier["source_identity"], "zotero:item:ITEMAAA1")
        self.assertEqual(carrier["provenance"]["zotero_item_key"], "ITEMAAA1")
        self.assertEqual(carrier["provenance"]["citation_key"], "Alpha2026")
        self.assertEqual(carrier["authority_scope"], "ZOTERO_LOCAL_LIBRARY_METADATA_ONLY")

        methods = [method for method, _ in ZoteroFixtureHandler.requests]
        self.assertEqual(set(methods), {"GET"})
        paths = [path for _, path in ZoteroFixtureHandler.requests]
        self.assertTrue(any(path == "/api/" for path in paths))
        search = next(path for path in paths if path.startswith("/api/users/0/items?"))
        query = parse_qs(urlsplit(search).query)
        self.assertEqual(query["q"], ["Hodge cycles"])
        self.assertEqual(query["limit"], ["1"])
        self.assertFalse(any("fulltext" in path or "/file/" in path for path in paths))

    def test_redirect_to_non_loopback_is_rejected(self):
        fixture = FixtureServer(mode="redirect").start()
        self.addCleanup(fixture.close)
        adapter = module.ZoteroAdapter(base_url=fixture.base_url, timeout=1.0)
        policy = self.make_policy()
        with self.assertRaises(PermissionError):
            self.registry(adapter).collect(
                "zotero",
                {
                    "root": None,
                    "options": {"mode": "local-api", "query": "x", "limit": 1},
                },
                policy,
            )

    def test_portable_bib_ris_and_json_are_raw_source_carriers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = {
                "refs.bib": "@article{x,title={X}}\n",
                "refs.ris": "TY  - JOUR\nTI  - X\nER  - \n",
                "refs.json": '[{"id":"x","type":"article-journal"}]\n',
            }
            for name, content in fixtures.items():
                (root / name).write_bytes(content.encode("utf-8"))

            adapter = module.ZoteroAdapter(base_url=self.unused_loopback_url(), timeout=0.1)
            policy = self.make_policy(root)
            registry = self.registry(adapter)
            for name, expected in fixtures.items():
                with self.subTest(name=name):
                    result = registry.collect(
                        "zotero",
                        {
                            "root": str(root),
                            "options": {"mode": "portable", "path": name},
                        },
                        policy,
                    )
                    self.assertEqual(result["status"], "COLLECTED")
                    self.assertEqual(result["carriers"][0]["payload"], expected)
                    self.assertEqual(
                        result["carriers"][0]["authority_scope"],
                        "ZOTERO_PORTABLE_ARTIFACT_ONLY",
                    )
                    self.assertIn(
                        result["carriers"][0]["payload_type"],
                        ("application/x-bibtex", "application/x-research-info-systems", "application/json"),
                    )


class FkdbZoteroAdapterRedContractTests(unittest.TestCase):
    def test_zotero_adapter_module_exists(self):
        self.assertIsNotNone(
            module,
            "fkdb_adapter_zotero module must exist before local Zotero can be collected",
        )


if __name__ == "__main__":
    unittest.main()
