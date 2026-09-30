from copy import deepcopy
from pathlib import Path
import unittest

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from rmapl_runtime import run_program


HERE = Path(__file__).resolve().parent
PROGRAM_PATH = HERE / "examples" / "independent_browser_transport.rmapl"

EMPTY_URL = {
    "raw": "",
    "scheme": "",
    "authority": "",
    "path": "",
    "canonical": "",
    "kind": "",
    "pageId": "",
    "networkRequired": False,
}


def local_url(page_id):
    return {
        "raw": f"rmapl://local/{page_id}",
        "scheme": "rmapl",
        "authority": "local",
        "path": f"/{page_id}",
        "canonical": f"rmapl://local/{page_id}",
        "kind": "local",
        "pageId": page_id,
        "networkRequired": False,
    }


def browser_omega(href="http://example.com/"):
    page = f'<h1>NET</h1><a href="{href}">GO</a>'
    return make_omega(
        native_type="independent-browser-transport/v0",
        native_identity="fixture:independent-browser-transport:1",
        source_refs=("inline:network-link-fixture",),
        state={
            "source": page,
            "resources": {
                "pages": [
                    {
                        "id": "page1",
                        "url": "rmapl://local/page1",
                        "source": page,
                    },
                ]
            },
            "navigation": {
                "currentPage": "page1",
                "currentUrl": local_url("page1"),
                "pendingHref": "",
                "pendingUrl": deepcopy(EMPTY_URL),
                "history": [],
                "focusIndex": -1,
                "focusedHref": "",
            },
            "input": {
                "pointer": {"x": 0, "y": 0},
                "keyboard": "",
                "lastHit": "",
            },
            "network": {
                "host": "",
                "port": 0,
                "request": [],
                "response": [],
                "maxResponseBytes": 262144,
                "transport": "idle",
            },
            "html": {"tokens": []},
            "dom": {"nodes": []},
            "layout": {"boxes": []},
            "hitMap": [],
            "camera": {
                "width": 160,
                "height": 64,
                "pixels": [],
                "verified": False,
                "admitted": False,
                "blackPixels": 0,
                "pgm": [],
            },
        },
        path=(),
        frame={"obligation": "build-request-before-native-byte-transport"},
        invariants=("sourceRefs", "claim-ceiling"),
        observations=(),
        residuals=(
            {"kind": "html-tokenization-pending", "detail": "fixture"},
        ),
        decision_field={"goal": "bounded-http-request-handoff"},
        provenance=(
            {"kind": "fixture", "ref": "independent-browser-transport"},
        ),
        evidence=(),
        claim_ceiling=(
            "HTTP_REQUEST_BUILD != TCP_TRANSPORT",
            "TCP_TRANSPORT != HTTP_RESPONSE_PARSE",
            "RAW_RESPONSE_BYTES != DOCUMENT_ADMISSION",
            "HTTPS_URL != TLS_IMPLEMENTED",
            "SOFTWARE_VERIFICATION != SECURITY_CERTIFICATION",
        ),
        resource_bounds={"maxCandidates": 1, "maxSteps": 11},
        domain_remainder={
            "unsupported": [
                "tls",
                "http-response-parsing",
                "redirects",
                "cookies",
                "cache",
                "compression",
                "chunked-transfer-decoding",
            ]
        },
    )


def pointer_input(omega, x, y):
    construction = deepcopy(omega["construction"])
    construction["state"]["input"]["pointer"] = {"x": x, "y": y}
    construction["state"]["input"]["lastHit"] = ""
    construction["residuals"] = [
        {"kind": "pointer-activation-pending", "detail": "synthetic-click"}
    ]
    return make_omega(**construction)


class IndependentBrowserTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = parse_rmapl(PROGRAM_PATH.read_text(encoding="utf-8"))
        cls.registry = native_registry(cls.program)

    def test_request_builder_is_rmapl_native(self):
        self.assertEqual(
            {spec.operator for spec in self.program.repairs},
            set(self.registry),
        )
        self.assertIn("browser_http_request_build", self.registry)

    def test_http_link_stops_at_preserved_tcp_handoff(self):
        first = run_program(self.program, browser_omega(), self.registry)
        self.assertEqual(first["stopReason"], "SUCCESS")
        self.assertEqual(first["generation"]["executedCount"], 8)

        clicked = pointer_input(first["branches"][0]["omega"], 5, 23)
        result = run_program(
            self.program,
            clicked,
            self.registry,
            stop_residual_kinds=(
                "tcp-exchange-pending",
                "tls-transport-pending",
            ),
        )

        self.assertEqual(result["stopReason"], "OUTER_CONTROLLER_BOUND")
        self.assertEqual(result["generation"]["executedCount"], 3)
        self.assertEqual(len(result["branches"]), 1)

        omega = result["branches"][0]["omega"]
        network = omega["state"]["network"]
        self.assertEqual(network["host"], "example.com")
        self.assertEqual(network["port"], 80)
        self.assertEqual(network["response"], [])
        self.assertEqual(network["maxResponseBytes"], 262144)
        self.assertEqual(network["transport"], "tcp-pending")
        self.assertEqual(
            bytes(network["request"]).decode("ascii"),
            "GET / HTTP/1.0\r\n"
            "Host: example.com\r\n"
            "Connection: close\r\n"
            "Accept: text/html\r\n"
            "User-Agent: RMAPL-Independent/0\r\n"
            "\r\n",
        )
        self.assertEqual(
            omega["residuals"],
            [{"kind": "tcp-exchange-pending", "detail": "raw-http-request-ready"}],
        )

    def test_http_path_is_owned_by_url_object(self):
        first = run_program(
            self.program,
            browser_omega("http://example.com/docs/start"),
            self.registry,
        )
        clicked = pointer_input(first["branches"][0]["omega"], 5, 23)
        result = run_program(
            self.program,
            clicked,
            self.registry,
            stop_residual_kinds=("tcp-exchange-pending",),
        )
        request = bytes(
            result["branches"][0]["omega"]["state"]["network"]["request"]
        ).decode("ascii")
        self.assertTrue(request.startswith("GET /docs/start HTTP/1.0\r\n"))
        self.assertIn("\r\nHost: example.com\r\n", request)

    def test_https_stops_at_separate_tls_boundary(self):
        first = run_program(
            self.program,
            browser_omega("https://example.com/secure"),
            self.registry,
        )
        clicked = pointer_input(first["branches"][0]["omega"], 5, 23)
        result = run_program(
            self.program,
            clicked,
            self.registry,
            stop_residual_kinds=(
                "tcp-exchange-pending",
                "tls-transport-pending",
            ),
        )

        self.assertEqual(result["stopReason"], "OUTER_CONTROLLER_BOUND")
        omega = result["branches"][0]["omega"]
        network = omega["state"]["network"]
        self.assertEqual(network["host"], "example.com")
        self.assertEqual(network["port"], 443)
        self.assertEqual(network["request"], [])
        self.assertEqual(network["transport"], "tls-required")
        self.assertEqual(
            omega["residuals"],
            [{
                "kind": "tls-transport-pending",
                "detail": "https-requires-unimplemented-tls",
            }],
        )


if __name__ == "__main__":
    unittest.main()
