from copy import deepcopy
from pathlib import Path
import unittest

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from rmapl_runtime import run_program


HERE = Path(__file__).resolve().parent
PROGRAM_PATH = HERE / "examples" / "independent_browser_keyboard.rmapl"

PAGE1 = '<h1>ONE</h1><a href="page2">NEXT</a>'
PAGE2 = '<h1>TWO</h1><p>DONE</p>'


def browser_omega():
    return make_omega(
        native_type="independent-browser-keyboard/v0",
        native_identity="fixture:independent-browser-keyboard:1",
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
        frame={"obligation": "keyboard-link-navigation"},
        invariants=("sourceRefs", "claim-ceiling"),
        observations=(),
        residuals=(
            {"kind": "html-tokenization-pending", "detail": "fixture"},
        ),
        decision_field={"goal": "keyboard-select-and-activate-link"},
        provenance=(
            {"kind": "fixture", "ref": "independent-browser-keyboard"},
        ),
        evidence=(),
        claim_ceiling=(
            "KEYBOARD_LINK_ACTIVATION != COMPLETE_KEYBOARD_UI",
            "LOCAL_PAGE_NAVIGATION != NETWORK_BROWSING",
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
                "text-input",
                "scrolling",
                "full-html-error-recovery",
            ]
        },
    )


def keyboard_input(omega, key):
    construction = deepcopy(omega["construction"])
    construction["state"]["input"]["keyboard"] = key
    construction["state"]["input"]["lastHit"] = ""
    construction["residuals"] = [
        {"kind": "keyboard-activation-pending", "detail": "synthetic-key"}
    ]
    return make_omega(**construction)


class IndependentBrowserKeyboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = parse_rmapl(PROGRAM_PATH.read_text(encoding="utf-8"))
        cls.registry = native_registry(cls.program)

    def test_keyboard_apply_target_is_rmapl_native(self):
        self.assertEqual(
            {spec.operator for spec in self.program.repairs},
            set(self.registry),
        )
        self.assertIn("browser_keyboard_activate", self.registry)

    def test_tab_focuses_first_link_without_rerender(self):
        first = run_program(self.program, browser_omega(), self.registry)
        self.assertEqual(first["stopReason"], "SUCCESS")
        self.assertEqual(first["generation"]["executedCount"], 8)

        tab = run_program(
            self.program,
            keyboard_input(first["branches"][0]["omega"], "TAB"),
            self.registry,
        )
        self.assertEqual(tab["stopReason"], "SUCCESS")
        self.assertEqual(tab["generation"]["executedCount"], 1)

        state = tab["branches"][0]["omega"]["state"]
        self.assertEqual(state["navigation"]["focusIndex"], 0)
        self.assertEqual(state["navigation"]["focusedHref"], "page2")
        self.assertEqual(state["input"]["lastHit"], "page2")
        self.assertEqual(state["navigation"]["currentPage"], "page1")
        self.assertTrue(state["camera"]["verified"])
        self.assertTrue(state["camera"]["admitted"])

    def test_enter_activates_focused_link_and_rerenders(self):
        first = run_program(self.program, browser_omega(), self.registry)
        tab = run_program(
            self.program,
            keyboard_input(first["branches"][0]["omega"], "TAB"),
            self.registry,
        )
        enter = run_program(
            self.program,
            keyboard_input(tab["branches"][0]["omega"], "ENTER"),
            self.registry,
        )

        self.assertEqual(enter["stopReason"], "SUCCESS")
        self.assertEqual(enter["generation"]["executedCount"], 10)
        state = enter["branches"][0]["omega"]["state"]

        self.assertEqual(state["navigation"]["currentPage"], "page2")
        self.assertEqual(state["navigation"]["history"], ["page1"])
        self.assertEqual(state["navigation"]["focusIndex"], -1)
        self.assertEqual(state["navigation"]["focusedHref"], "")
        self.assertEqual(state["input"]["lastHit"], "page2")
        self.assertEqual(state["source"], PAGE2)
        self.assertTrue(state["camera"]["verified"])
        self.assertTrue(state["camera"]["admitted"])

    def test_enter_without_focus_does_not_navigate(self):
        first = run_program(self.program, browser_omega(), self.registry)
        enter = run_program(
            self.program,
            keyboard_input(first["branches"][0]["omega"], "ENTER"),
            self.registry,
        )

        self.assertEqual(enter["stopReason"], "NO_ADMISSIBLE_PROGRESS")
        self.assertEqual(enter["generation"]["executedCount"], 1)
        self.assertEqual(enter["branches"], [])


if __name__ == "__main__":
    unittest.main()
