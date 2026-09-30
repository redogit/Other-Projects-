from copy import deepcopy
from pathlib import Path
import unittest

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from rmapl_runtime import run_program
from test_independent_browser_url import browser_omega as url_browser_omega, EMPTY_URL, local_url


HERE = Path(__file__).resolve().parent
HTTP_PATH = HERE / "examples" / "independent_browser_http.rmapl"
URL_PATH = HERE / "examples" / "independent_browser_url.rmapl"


def network_url(scheme="http", host="127.0.0.1", path="/test"):
    return {
        "raw": f"{scheme}://{host}{path}",
        "scheme": scheme,
        "authority": host,
        "path": path,
        "canonical": f"{scheme}://{host}{path}",
        "kind": "network",
        "pageId": "",
        "networkRequired": True,
    }


def with_network_state(omega, *, pending_url=None, residual="network-transport-pending"):
    construction = deepcopy(omega["construction"])
    state = construction["state"]
    state["navigation"]["pendingUrl"] = deepcopy(pending_url or network_url())
    state["network"] = {
        "request": {
            "host": "",
            "port": 0,
            "bytes": [],
            "maxResponseBytes": 0,
        },
        "responseBytes": [],
        "response": {
            "status": 0,
            "bodyBytes": [],
        },
    }
    construction["residuals"] = [{"kind": residual, "detail": "synthetic"}]
    return make_omega(**construction)


def inject_response(omega, raw: bytes):
    construction = deepcopy(omega["construction"])
    construction["state"]["network"]["responseBytes"] = list(raw)
    construction["residuals"] = [
        {"kind": "http-response-parse-pending", "detail": "native-transport-complete"}
    ]
    return make_omega(**construction)


class IndependentBrowserHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http_program = parse_rmapl(HTTP_PATH.read_text(encoding="utf-8"))
        cls.http_registry = native_registry(cls.http_program)
        cls.url_program = parse_rmapl(URL_PATH.read_text(encoding="utf-8"))
        cls.url_registry = native_registry(cls.url_program)

    def test_http_profile_owns_declared_apply_targets(self):
        self.assertEqual(
            {spec.operator for spec in self.http_program.repairs},
            set(self.http_registry),
        )
        self.assertIn("browser_http_plan", self.http_registry)
        self.assertIn("browser_http_response_admit", self.http_registry)

    def test_http_request_is_built_by_rmapl_exactly(self):
        omega = with_network_state(url_browser_omega())
        result = run_program(self.http_program, omega, self.http_registry)
        self.assertEqual(len(result["branches"]), 1)
        branch = result["branches"][0]
        self.assertTrue(branch["admitted"])

        state = branch["omega"]["state"]
        request = state["network"]["request"]
        self.assertEqual(request["host"], "127.0.0.1")
        self.assertEqual(request["port"], 80)
        self.assertEqual(request["maxResponseBytes"], 262144)
        self.assertEqual(
            bytes(request["bytes"]),
            (
                b"GET /test HTTP/1.1\r\n"
                b"Host: 127.0.0.1\r\n"
                b"Connection: close\r\n"
                b"Accept: text/html\r\n"
                b"User-Agent: RMAPL-Independent/0\r\n"
                b"\r\n"
            ),
        )
        self.assertEqual(
            branch["omega"]["residuals"],
            [{"kind": "native-http-transport-pending", "detail": "rmapl-request-ready"}],
        )

    def test_https_stops_at_explicit_tls_boundary(self):
        omega = with_network_state(
            url_browser_omega(),
            pending_url=network_url("https", "example.com", "/docs"),
        )
        proposal = self.http_registry["browser_http_plan"](omega)
        candidate = proposal["omega"]
        self.assertEqual(candidate["state"]["network"]["request"]["bytes"], [])
        self.assertEqual(
            candidate["residuals"],
            [{"kind": "tls-transport-pending", "detail": "https-requires-native-tls-carrier"}],
        )

    def test_http_200_response_is_admitted_as_new_document_then_renders(self):
        planned = self.http_registry["browser_http_plan"](
            with_network_state(url_browser_omega())
        )["omega"]
        raw = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/html\r\n"
            b"Connection: close\r\n"
            b"\r\n"
            b"<h1>FETCHED</h1>"
        )
        parsed = self.http_registry["browser_http_response_admit"](
            inject_response(planned, raw)
        )["omega"]

        state = parsed["state"]
        self.assertEqual(state["source"], "<h1>FETCHED</h1>")
        self.assertEqual(state["navigation"]["history"], ["rmapl://local/page1"])
        self.assertEqual(state["navigation"]["currentUrl"], network_url())
        self.assertEqual(state["navigation"]["pendingUrl"], EMPTY_URL)
        self.assertEqual(state["navigation"]["currentPage"], "")
        self.assertEqual(state["network"]["response"]["status"], 200)
        self.assertEqual(
            bytes(state["network"]["response"]["bodyBytes"]),
            b"<h1>FETCHED</h1>",
        )
        self.assertEqual(
            parsed["residuals"],
            [{"kind": "html-tokenization-pending", "detail": "http-response-admitted"}],
        )

        rendered = run_program(self.url_program, parsed, self.url_registry)
        self.assertEqual(rendered["stopReason"], "SUCCESS")
        final = rendered["branches"][0]["omega"]
        self.assertEqual(final["state"]["dom"]["nodes"][1]["tag"], "h1")
        self.assertEqual(final["state"]["dom"]["nodes"][2]["text"], "FETCHED")
        self.assertTrue(final["state"]["camera"]["verified"])
        self.assertTrue(final["state"]["camera"]["admitted"])

    def test_non_200_and_missing_header_delimiter_fail_closed(self):
        planned = self.http_registry["browser_http_plan"](
            with_network_state(url_browser_omega())
        )["omega"]
        bad_responses = (
            b"HTTP/1.1 404 Not Found\r\n\r\n<h1>NO</h1>",
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n<h1>NO</h1>",
        )
        for raw in bad_responses:
            with self.subTest(raw=raw):
                candidate = self.http_registry["browser_http_response_admit"](
                    inject_response(planned, raw)
                )["omega"]
                self.assertEqual(
                    candidate["residuals"],
                    [{
                        "kind": "http-response-invalid",
                        "detail": "requires-http11-200-header-delimiter-utf8-body",
                    }],
                )
                self.assertNotEqual(candidate["state"]["source"], "<h1>NO</h1>")


if __name__ == "__main__":
    unittest.main()
