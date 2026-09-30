from copy import deepcopy
from pathlib import Path
import unittest

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from rmapl_runtime import run_program


HERE = Path(__file__).resolve().parent
PROGRAM_PATH = HERE / "examples" / "independent_browser_navigation.rmapl"

PAGE1 = '<h1>ONE</h1><a href="page2">NEXT</a>'
PAGE2 = '<h1>TWO</h1><p>DONE</p>'


def browser_omega():
    return make_omega(
        native_type="independent-browser-navigation/v0",
        native_identity="fixture:independent-browser-navigation:1",
        source_refs=("inline:page1", "inline:page2"),
        state={
            "source": PAGE1,
            "resources": {
                "pages": [
                    {"id": "page1", "source": PAGE1},
                    {"id": "page2", "source": PAGE2},
                ]
            },
            "navigation": {
                "currentPage": "page1",
                "pendingHref": "",
                "history": [],
            },
            "input": {
                "pointer": {"x": 0, "y": 0},
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
        frame={"obligation": "render-and-navigate-bounded-local-pages"},
        invariants=("sourceRefs", "claim-ceiling"),
        observations=(),
        residuals=(
            {"kind": "html-tokenization-pending", "detail": "fixture"},
        ),
        decision_field={"goal": "verified-local-navigation"},
        provenance=(
            {"kind": "fixture", "ref": "independent-browser-navigation"},
        ),
        evidence=(),
        claim_ceiling=(
            "LOCAL_PAGE_NAVIGATION != NETWORK_BROWSING",
            "BOUNDED_HREF_SUBSET != HTML5_ATTRIBUTE_PARSER",
            "SOFTWARE_VERIFICATION != SECURITY_CERTIFICATION",
        ),
        resource_bounds={"maxCandidates": 1, "maxSteps": 10},
        domain_remainder={
            "unsupported": [
                "network",
                "tls",
                "css",
                "javascript",
                "images",
                "forms",
                "keyboard-input",
                "scrolling",
                "full-html-error-recovery",
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


class IndependentBrowserNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = parse_rmapl(PROGRAM_PATH.read_text(encoding="utf-8"))
        cls.registry = native_registry(cls.program)

    def test_navigation_profile_owns_every_apply_target(self):
        self.assertEqual(
            {spec.operator for spec in self.program.repairs},
            set(self.registry),
        )
        self.assertIn("browser_pointer_activate", self.registry)
        self.assertIn("browser_local_navigate", self.registry)
        self.assertIn("browser_hit_map", self.registry)

    def test_anchor_builds_hit_map_without_navigation(self):
        result = run_program(self.program, browser_omega(), self.registry)
        self.assertEqual(result["stopReason"], "SUCCESS")
        self.assertEqual(result["generation"]["executedCount"], 8)
        self.assertEqual(len(result["branches"]), 1)

        state = result["branches"][0]["omega"]["state"]
        self.assertEqual(state["navigation"]["currentPage"], "page1")
        self.assertEqual(state["navigation"]["history"], [])

        self.assertEqual(
            state["html"]["tokens"],
            [
                {"kind": "start", "name": "h1", "value": ""},
                {"kind": "text", "name": "", "value": "ONE"},
                {"kind": "end", "name": "h1", "value": ""},
                {"kind": "start", "name": "a", "value": "page2"},
                {"kind": "text", "name": "", "value": "NEXT"},
                {"kind": "end", "name": "a", "value": ""},
            ],
        )

        self.assertEqual(
            state["hitMap"],
            [{"x": 4, "y": 22, "width": 24, "height": 7, "href": "page2"}],
        )
        self.assertEqual(state["layout"]["boxes"][1]["href"], "page2")
        self.assertTrue(state["camera"]["verified"])
        self.assertTrue(state["camera"]["admitted"])

    def test_pointer_hit_navigates_and_rerenders_second_page(self):
        first = run_program(self.program, browser_omega(), self.registry)
        first_omega = first["branches"][0]["omega"]

        # Link rectangle is x=[4,28), y=[22,29).
        clicked = pointer_input(first_omega, 5, 23)
        second = run_program(self.program, clicked, self.registry)

        self.assertEqual(second["stopReason"], "SUCCESS")
        self.assertEqual(second["generation"]["executedCount"], 10)
        self.assertEqual(len(second["branches"]), 1)

        state = second["branches"][0]["omega"]["state"]
        self.assertEqual(state["navigation"]["currentPage"], "page2")
        self.assertEqual(state["navigation"]["pendingHref"], "")
        self.assertEqual(state["navigation"]["history"], ["page1"])
        self.assertEqual(state["input"]["lastHit"], "page2")
        self.assertEqual(state["source"], PAGE2)
        self.assertEqual(state["hitMap"], [])

        self.assertEqual(
            state["html"]["tokens"],
            [
                {"kind": "start", "name": "h1", "value": ""},
                {"kind": "text", "name": "", "value": "TWO"},
                {"kind": "end", "name": "h1", "value": ""},
                {"kind": "start", "name": "p", "value": ""},
                {"kind": "text", "name": "", "value": "DONE"},
                {"kind": "end", "name": "p", "value": ""},
            ],
        )
        self.assertTrue(state["camera"]["verified"])
        self.assertTrue(state["camera"]["admitted"])
        self.assertGreater(state["camera"]["blackPixels"], 0)

    def test_click_outside_link_does_not_navigate(self):
        first = run_program(self.program, browser_omega(), self.registry)
        clicked = pointer_input(first["branches"][0]["omega"], 100, 50)
        second = run_program(self.program, clicked, self.registry)

        self.assertEqual(second["stopReason"], "NO_ADMISSIBLE_PROGRESS")
        self.assertEqual(second["generation"]["executedCount"], 1)
        self.assertEqual(second["branches"], [])


if __name__ == "__main__":
    unittest.main()
