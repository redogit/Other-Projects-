from copy import deepcopy
from pathlib import Path
import unittest

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from rmapl_runtime import run_program


HERE = Path(__file__).resolve().parent
PROGRAM_PATH = HERE / "examples" / "independent_browser_url.rmapl"

PAGE1 = '<h1>ONE</h1><a href="rmapl://local/page2">NEXT</a>'
PAGE2 = '<h1>TWO</h1><p>DONE</p>'

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


def browser_omega():
    return make_omega(
        native_type="independent-browser-url/v0",
        native_identity="fixture:independent-browser-url:1",
        source_refs=("url:rmapl://local/page1", "url:rmapl://local/page2"),
        state={
            "source": PAGE1,
            "resources": {
                "pages": [
                    {
                        "id": "page1",
                        "url": "rmapl://local/page1",
                        "source": PAGE1,
                    },
                    {
                        "id": "page2",
                        "url": "rmapl://local/page2",
                        "source": PAGE2,
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
        frame={"obligation": "typed-url-resolution-before-navigation"},
        invariants=("sourceRefs", "claim-ceiling"),
        observations=(),
        residuals=(
            {"kind": "html-tokenization-pending", "detail": "fixture"},
        ),
        decision_field={"goal": "canonical-url-gated-navigation"},
        provenance=(
            {"kind": "fixture", "ref": "independent-browser-url"},
        ),
        evidence=(),
        claim_ceiling=(
            "URL_PARSE_RESOLVE != NETWORK_FETCH",
            "BOUNDED_URL_SUBSET != RFC3986_CONFORMANCE",
            "LOCAL_PAGE_NAVIGATION != NETWORK_BROWSING",
            "SOFTWARE_VERIFICATION != SECURITY_CERTIFICATION",
        ),
        resource_bounds={"maxCandidates": 1, "maxSteps": 11},
        domain_remainder={
            "unsupported": [
                "dns",
                "tcp",
                "tls",
                "http",
                "query",
                "fragment",
                "userinfo",
                "ports",
                "percent-decoding",
                "dot-segment-normalization",
                "unicode-hostnames",
            ]
        },
    )


def with_residual(omega, residual, **navigation_changes):
    construction = deepcopy(omega["construction"])
    construction["state"]["navigation"].update(navigation_changes)
    construction["residuals"] = [{"kind": residual, "detail": "synthetic"}]
    return make_omega(**construction)


def pointer_input(omega, x, y):
    construction = deepcopy(omega["construction"])
    construction["state"]["input"]["pointer"] = {"x": x, "y": y}
    construction["state"]["input"]["lastHit"] = ""
    construction["residuals"] = [
        {"kind": "pointer-activation-pending", "detail": "synthetic-click"}
    ]
    return make_omega(**construction)


class IndependentBrowserUrlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = parse_rmapl(PROGRAM_PATH.read_text(encoding="utf-8"))
        cls.registry = native_registry(cls.program)

    def test_url_resolver_is_rmapl_native(self):
        self.assertEqual(
            {spec.operator for spec in self.program.repairs},
            set(self.registry),
        )
        self.assertIn("browser_url_resolve", self.registry)

    def test_initial_absolute_local_link_builds_url_bearing_hit_map(self):
        result = run_program(self.program, browser_omega(), self.registry)
        self.assertEqual(result["stopReason"], "SUCCESS")
        self.assertEqual(result["generation"]["executedCount"], 8)
        state = result["branches"][0]["omega"]["state"]

        self.assertEqual(state["navigation"]["currentUrl"], local_url("page1"))
        self.assertEqual(
            state["hitMap"],
            [{
                "x": 4,
                "y": 22,
                "width": 24,
                "height": 7,
                "href": "rmapl://local/page2",
            }],
        )

    def test_absolute_local_click_resolves_then_navigates_and_rerenders(self):
        first = run_program(self.program, browser_omega(), self.registry)
        clicked = pointer_input(first["branches"][0]["omega"], 5, 23)
        second = run_program(self.program, clicked, self.registry)

        self.assertEqual(second["stopReason"], "SUCCESS")
        self.assertEqual(second["generation"]["executedCount"], 11)
        state = second["branches"][0]["omega"]["state"]

        self.assertEqual(state["navigation"]["currentPage"], "page2")
        self.assertEqual(state["navigation"]["currentUrl"], local_url("page2"))
        self.assertEqual(
            state["navigation"]["history"],
            ["rmapl://local/page1"],
        )
        self.assertEqual(state["navigation"]["pendingHref"], "")
        self.assertEqual(state["navigation"]["pendingUrl"], EMPTY_URL)
        self.assertEqual(state["source"], PAGE2)
        self.assertTrue(state["camera"]["verified"])
        self.assertTrue(state["camera"]["admitted"])

    def test_relative_local_href_gets_canonical_identity(self):
        rendered = run_program(self.program, browser_omega(), self.registry)
        omega = with_residual(
            rendered["branches"][0]["omega"],
            "url-resolution-pending",
            pendingHref="page2",
            pendingUrl=deepcopy(EMPTY_URL),
        )
        proposal = self.registry["browser_url_resolve"](omega)
        candidate = proposal["omega"]

        self.assertEqual(candidate["state"]["navigation"]["pendingHref"], "page2")
        self.assertEqual(
            candidate["state"]["navigation"]["pendingUrl"],
            local_url("page2") | {"raw": "page2"},
        )
        self.assertEqual(
            candidate["residuals"],
            [{"kind": "local-navigation-pending", "detail": "url-resolved-local"}],
        )

    def test_https_url_is_parsed_but_not_promoted_to_fetch(self):
        rendered = run_program(self.program, browser_omega(), self.registry)
        omega = with_residual(
            rendered["branches"][0]["omega"],
            "url-resolution-pending",
            pendingHref="https://example.com/docs",
            pendingUrl=deepcopy(EMPTY_URL),
        )
        proposal = self.registry["browser_url_resolve"](omega)
        candidate = proposal["omega"]
        pending = candidate["state"]["navigation"]["pendingUrl"]

        self.assertEqual(
            pending,
            {
                "raw": "https://example.com/docs",
                "scheme": "https",
                "authority": "example.com",
                "path": "/docs",
                "canonical": "https://example.com/docs",
                "kind": "network",
                "pageId": "",
                "networkRequired": True,
            },
        )
        self.assertEqual(
            candidate["residuals"],
            [{
                "kind": "network-transport-pending",
                "detail": "url-resolved-network-unavailable",
            }],
        )

    def test_network_url_without_path_canonicalizes_slash(self):
        rendered = run_program(self.program, browser_omega(), self.registry)
        omega = with_residual(
            rendered["branches"][0]["omega"],
            "url-resolution-pending",
            pendingHref="http://example.com",
            pendingUrl=deepcopy(EMPTY_URL),
        )
        candidate = self.registry["browser_url_resolve"](omega)["omega"]
        pending = candidate["state"]["navigation"]["pendingUrl"]
        self.assertEqual(pending["scheme"], "http")
        self.assertEqual(pending["authority"], "example.com")
        self.assertEqual(pending["path"], "/")
        self.assertEqual(pending["canonical"], "http://example.com/")
        self.assertTrue(pending["networkRequired"])

    def test_query_and_fragment_fail_closed_in_bounded_profile(self):
        rendered = run_program(self.program, browser_omega(), self.registry)
        for href in (
            "https://example.com/a?x=1",
            "https://example.com/a#frag",
            "page2?x=1",
            "rmapl://local/page2#frag",
        ):
            with self.subTest(href=href):
                omega = with_residual(
                    rendered["branches"][0]["omega"],
                    "url-resolution-pending",
                    pendingHref=href,
                    pendingUrl=deepcopy(EMPTY_URL),
                )
                candidate = self.registry["browser_url_resolve"](omega)["omega"]
                self.assertEqual(
                    candidate["residuals"],
                    [{"kind": "url-invalid", "detail": "unsupported-or-malformed-url"}],
                )


if __name__ == "__main__":
    unittest.main()
