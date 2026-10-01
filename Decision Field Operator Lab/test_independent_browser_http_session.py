from copy import deepcopy
from pathlib import Path
import unittest

from rmapl import parse_rmapl
from rmapl_native import native_registry

from tools.interact_independent_browser import (
    HTTP_OUTER_STOP_KINDS,
    HTTP_PROGRAM_PATH,
    URL_OUTER_STOP_KINDS,
    URL_PROGRAM_PATH,
    drive_browser,
    execute_to_boundary,
    initial_omega,
    pointer_omega,
    residual_kind,
    response_omega,
)


PAGE_HTTP = '<h1>ONE</h1><a href="http://example.com/test">NET</a>'
PAGE_HTTPS = '<h1>ONE</h1><a href="https://example.com/test">TLS</a>'


def pages(source):
    return [{
        "id": "page1",
        "url": "rmapl://local/page1",
        "source": source,
    }]


class LiveHttpSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url_program = parse_rmapl(URL_PROGRAM_PATH.read_text(encoding="utf-8"))
        cls.url_registry = native_registry(cls.url_program)
        cls.http_program = parse_rmapl(HTTP_PROGRAM_PATH.read_text(encoding="utf-8"))
        cls.http_registry = native_registry(cls.http_program)

    def drive(self, omega, transport=None, tls_transport=None):
        return drive_browser(
            omega,
            url_program=self.url_program,
            url_registry=self.url_registry,
            http_program=self.http_program,
            http_registry=self.http_registry,
            transport=transport,
            tls_transport=tls_transport,
            max_transitions=64,
        )

    def test_initial_render_completes_inside_one_host_routing_turn(self):
        initial, status = drive_browser(
            initial_omega(pages(PAGE_HTTP), "page1"),
            url_program=self.url_program,
            url_registry=self.url_registry,
            http_program=self.http_program,
            http_registry=self.http_registry,
            max_transitions=1,
        )
        self.assertEqual(status, "presentable")
        self.assertTrue(initial["state"]["camera"]["verified"])
        self.assertTrue(initial["state"]["camera"]["admitted"])

    def test_cross_program_and_native_seams_use_outer_controller_bound(self):
        initial, status = self.drive(initial_omega(pages(PAGE_HTTP), "page1"))
        self.assertEqual(status, "presentable")

        url_handoff, url_result = execute_to_boundary(
            self.url_program,
            self.url_registry,
            pointer_omega(initial, 5, 23),
            stop_residual_kinds=URL_OUTER_STOP_KINDS,
        )
        self.assertIsNotNone(url_handoff)
        self.assertEqual(url_result["stopReason"], "OUTER_CONTROLLER_BOUND")
        self.assertNotIn("RESOURCE_BOUND", url_result["stopFacts"])
        self.assertEqual(url_result["generation"]["stepsExecuted"], 2)
        self.assertEqual(residual_kind(url_handoff), "network-transport-pending")

        http_handoff, http_result = execute_to_boundary(
            self.http_program,
            self.http_registry,
            url_handoff,
            stop_residual_kinds=HTTP_OUTER_STOP_KINDS,
        )
        self.assertIsNotNone(http_handoff)
        self.assertEqual(http_result["stopReason"], "OUTER_CONTROLLER_BOUND")
        self.assertNotIn("RESOURCE_BOUND", http_result["stopFacts"])
        self.assertEqual(http_result["generation"]["stepsExecuted"], 1)
        self.assertEqual(residual_kind(http_handoff), "native-http-transport-pending")

        returned = response_omega(
            http_handoff,
            (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/html\r\n"
                b"Connection: close\r\n"
                b"\r\n"
                b"<h1>FETCHED</h1>"
            ),
        )
        render_handoff, response_result = execute_to_boundary(
            self.http_program,
            self.http_registry,
            returned,
            stop_residual_kinds=HTTP_OUTER_STOP_KINDS,
        )
        self.assertIsNotNone(render_handoff)
        self.assertEqual(response_result["stopReason"], "OUTER_CONTROLLER_BOUND")
        self.assertNotIn("RESOURCE_BOUND", response_result["stopFacts"])
        self.assertEqual(response_result["generation"]["stepsExecuted"], 1)
        self.assertEqual(residual_kind(render_handoff), "html-tokenization-pending")

    def test_network_link_fetches_admits_and_rerenders_through_rmapl(self):
        initial, status = self.drive(initial_omega(pages(PAGE_HTTP), "page1"))
        self.assertEqual(status, "presentable")
        self.assertEqual(
            initial["state"]["hitMap"],
            [{"x": 4, "y": 22, "width": 18, "height": 7, "href": "http://example.com/test"}],
        )

        calls = []

        def transport(omega):
            request = omega["state"]["network"]["request"]
            calls.append({
                "host": request["host"],
                "port": request["port"],
                "bytes": bytes(request["bytes"]),
                "max": request["maxResponseBytes"],
            })
            return (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/html\r\n"
                b"Connection: close\r\n"
                b"\r\n"
                b"<h1>FETCHED</h1>"
            )

        final, status = self.drive(pointer_omega(initial, 5, 23), transport)
        self.assertEqual(status, "presentable")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["host"], "example.com")
        self.assertEqual(calls[0]["port"], 80)
        self.assertEqual(calls[0]["max"], 262144)
        self.assertEqual(
            calls[0]["bytes"],
            (
                b"GET /test HTTP/1.1\r\n"
                b"Host: example.com\r\n"
                b"Connection: close\r\n"
                b"Accept: text/html\r\n"
                b"User-Agent: RMAPL-Independent/0\r\n"
                b"\r\n"
            ),
        )

        state = final["state"]
        self.assertEqual(state["navigation"]["currentPage"], "")
        self.assertEqual(
            state["navigation"]["currentUrl"]["canonical"],
            "http://example.com/test",
        )
        self.assertEqual(
            state["navigation"]["history"],
            ["rmapl://local/page1"],
        )
        self.assertEqual(state["source"], "<h1>FETCHED</h1>")
        self.assertEqual(state["network"]["response"]["status"], 200)
        self.assertEqual(state["dom"]["nodes"][1]["tag"], "h1")
        self.assertEqual(state["dom"]["nodes"][2]["text"], "FETCHED")
        self.assertTrue(state["camera"]["verified"])
        self.assertTrue(state["camera"]["admitted"])
        self.assertEqual(final["residuals"], [])

    def test_network_link_without_carrier_stops_before_transport(self):
        initial, status = self.drive(initial_omega(pages(PAGE_HTTP), "page1"))
        self.assertEqual(status, "presentable")

        proposed, status = self.drive(pointer_omega(initial, 5, 23), None)
        self.assertEqual(status, "http-carrier-missing")
        self.assertEqual(residual_kind(proposed), "native-http-transport-pending")
        self.assertEqual(
            proposed["state"]["navigation"]["pendingUrl"]["canonical"],
            "http://example.com/test",
        )
        self.assertEqual(
            proposed["state"]["network"]["request"]["host"],
            "example.com",
        )
        # The host has not replaced the last admitted page with unverified data.
        self.assertEqual(proposed["state"]["source"], PAGE_HTTP)
        self.assertTrue(proposed["state"]["camera"]["verified"])
        self.assertTrue(proposed["state"]["camera"]["admitted"])

    def test_https_uses_only_tls_carrier_then_admits_and_rerenders(self):
        initial, status = self.drive(initial_omega(pages(PAGE_HTTPS), "page1"))
        self.assertEqual(status, "presentable")
        http_calls = []
        tls_calls = []

        def http_transport(_omega):
            http_calls.append(True)
            return b"should-not-run"

        def tls_transport(omega):
            request = omega["state"]["network"]["request"]
            tls_calls.append({
                "host": request["host"],
                "port": request["port"],
                "bytes": bytes(request["bytes"]),
            })
            return (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/html\r\n"
                b"Connection: close\r\n"
                b"\r\n"
                b"<h1>SECURE</h1>"
            )

        final, status = self.drive(
            pointer_omega(initial, 5, 23),
            http_transport,
            tls_transport,
        )
        self.assertEqual(status, "presentable")
        self.assertEqual(http_calls, [])
        self.assertEqual(len(tls_calls), 1)
        self.assertEqual(tls_calls[0]["host"], "example.com")
        self.assertEqual(tls_calls[0]["port"], 443)
        self.assertEqual(
            tls_calls[0]["bytes"],
            (
                b"GET /test HTTP/1.1\r\n"
                b"Host: example.com\r\n"
                b"Connection: close\r\n"
                b"Accept: text/html\r\n"
                b"User-Agent: RMAPL-Independent/0\r\n"
                b"\r\n"
            ),
        )
        self.assertEqual(
            final["state"]["navigation"]["currentUrl"]["canonical"],
            "https://example.com/test",
        )
        self.assertEqual(final["state"]["source"], "<h1>SECURE</h1>")
        self.assertEqual(final["state"]["dom"]["nodes"][2]["text"], "SECURE")
        self.assertTrue(final["state"]["camera"]["verified"])
        self.assertTrue(final["state"]["camera"]["admitted"])

    def test_https_without_tls_carrier_stops_before_encrypted_transport(self):
        initial, status = self.drive(initial_omega(pages(PAGE_HTTPS), "page1"))
        self.assertEqual(status, "presentable")

        proposed, status = self.drive(pointer_omega(initial, 5, 23))
        self.assertEqual(status, "tls-carrier-missing")
        self.assertEqual(residual_kind(proposed), "native-tls-transport-pending")
        self.assertEqual(
            proposed["state"]["navigation"]["pendingUrl"]["canonical"],
            "https://example.com/test",
        )
        self.assertEqual(proposed["state"]["network"]["request"]["port"], 443)
        self.assertEqual(proposed["state"]["source"], PAGE_HTTPS)
        self.assertTrue(proposed["state"]["camera"]["verified"])
        self.assertTrue(proposed["state"]["camera"]["admitted"])

    def test_bad_http_response_does_not_replace_last_visual_state(self):
        initial, status = self.drive(initial_omega(pages(PAGE_HTTP), "page1"))
        self.assertEqual(status, "presentable")

        def transport(_omega):
            return b"HTTP/1.1 404 Not Found\r\n\r\n<h1>NO</h1>"

        proposed, status = self.drive(pointer_omega(initial, 5, 23), transport)
        self.assertTrue(status.startswith("no-admitted-transition:"))
        self.assertEqual(proposed["state"]["source"], PAGE_HTTP)
        self.assertTrue(proposed["state"]["camera"]["verified"])
        self.assertTrue(proposed["state"]["camera"]["admitted"])

    def assert_admitted_view_unchanged(self, initial, proposed):
        for key in ("source", "dom", "layout", "hitMap", "camera"):
            self.assertEqual(proposed["state"][key], initial["state"][key], key)
        for key in ("currentPage", "currentUrl", "history"):
            self.assertEqual(proposed["state"]["navigation"][key],
                             initial["state"]["navigation"][key], key)

    def test_tls_failure_preserves_view_and_never_substitutes_http(self):
        initial, status = self.drive(initial_omega(pages(PAGE_HTTPS), "page1"))
        self.assertEqual(status, "presentable")
        frozen = deepcopy(initial)
        for failure in (RuntimeError("certificate rejected"), OSError("carrier failed")):
            with self.subTest(failure=type(failure).__name__):
                calls = []

                def http_transport(_omega):
                    calls.append("http")
                    return b"HTTP/1.1 200 OK\r\n\r\n<h1>DOWNGRADE</h1>"

                def tls_transport(_omega):
                    calls.append("tls")
                    raise failure

                proposed, status = self.drive(pointer_omega(initial, 5, 23),
                                              http_transport, tls_transport)
                self.assertTrue(status.startswith("tls-carrier-failed:"), status)
                self.assertEqual(calls, ["tls"])
                self.assertEqual(residual_kind(proposed), "native-tls-transport-pending")
                self.assertEqual(proposed["state"]["network"]["responseBytes"], [])
                self.assert_admitted_view_unchanged(initial, proposed)
                self.assertEqual(initial, frozen)

    def test_decrypted_bytes_still_require_response_admission(self):
        initial, status = self.drive(initial_omega(pages(PAGE_HTTPS), "page1"))
        self.assertEqual(status, "presentable")
        for payload in (b"HTTP/1.1 404 Not Found\r\n\r\n<h1>NO</h1>",
                        b"HTTP/1.1 200 OK\r\n<h1>MISSING DELIMITER</h1>"):
            with self.subTest(payload=payload):
                calls = []

                def http_transport(_omega):
                    calls.append("http")
                    return b"HTTP/1.1 200 OK\r\n\r\n<h1>DOWNGRADE</h1>"

                def tls_transport(_omega):
                    calls.append("tls")
                    return payload

                proposed, status = self.drive(pointer_omega(initial, 5, 23),
                                              http_transport, tls_transport)
                self.assertTrue(status.startswith("no-admitted-transition:"), status)
                self.assertEqual(calls, ["tls"])
                self.assertEqual(residual_kind(proposed), "http-response-invalid")
                self.assertEqual(bytes(proposed["state"]["network"]["responseBytes"]), payload)
                self.assert_admitted_view_unchanged(initial, proposed)


if __name__ == "__main__":
    unittest.main()
