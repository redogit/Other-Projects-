from pathlib import Path
import unittest

from rmapl import parse_rmapl
from rmapl_native import native_registry

from tools.interact_independent_browser import (
    HTTP_PROGRAM_PATH,
    URL_PROGRAM_PATH,
    drive_browser,
    initial_omega,
    pointer_omega,
    residual_kind,
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

    def drive(self, omega, transport=None):
        return drive_browser(
            omega,
            url_program=self.url_program,
            url_registry=self.url_registry,
            http_program=self.http_program,
            http_registry=self.http_registry,
            transport=transport,
            max_transitions=64,
        )

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

    def test_https_never_calls_plaintext_http_transport(self):
        initial, status = self.drive(initial_omega(pages(PAGE_HTTPS), "page1"))
        self.assertEqual(status, "presentable")
        calls = []

        def transport(_omega):
            calls.append(True)
            return b"should-not-run"

        proposed, status = self.drive(pointer_omega(initial, 5, 23), transport)
        self.assertEqual(status, "tls-transport-pending")
        self.assertEqual(residual_kind(proposed), "tls-transport-pending")
        self.assertEqual(calls, [])
        self.assertEqual(
            proposed["state"]["navigation"]["pendingUrl"]["canonical"],
            "https://example.com/test",
        )
        self.assertEqual(proposed["state"]["source"], PAGE_HTTPS)

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


if __name__ == "__main__":
    unittest.main()
