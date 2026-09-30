from copy import deepcopy
from pathlib import Path
import unittest

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from rmapl_runtime import run_program
from test_independent_browser_native import browser_omega


HERE = Path(__file__).resolve().parent
RENDER_PATH = HERE / "examples" / "independent_browser_native.rmapl"
INTERACTION_PATH = HERE / "examples" / "independent_browser_interaction.rmapl"


def rebuild(omega, *, state=None, residuals=None):
    construction = deepcopy(omega["construction"])
    if state is not None:
        construction["state"] = state
    if residuals is not None:
        construction["residuals"] = residuals
    return make_omega(**construction)


def initial_page():
    source = '<a href="page2">NEXT</a>'
    omega = browser_omega(source)
    state = deepcopy(omega["state"])
    state["documents"] = {
        "page1": source,
        "page2": "<h1>DONE</h1>",
    }
    state["location"] = "page1"
    return rebuild(omega, state=state)


class IndependentBrowserInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.render_program = parse_rmapl(RENDER_PATH.read_text(encoding="utf-8"))
        cls.interaction_program = parse_rmapl(
            INTERACTION_PATH.read_text(encoding="utf-8")
        )

    def rendered_page1(self):
        result = run_program(
            self.render_program,
            initial_page(),
            native_registry(self.render_program),
        )
        self.assertEqual(result["stopReason"], "SUCCESS")
        return result["branches"][0]["omega"]

    def with_click(self, omega, x, y):
        state = deepcopy(omega["state"])
        state["input"] = {"clickX": x, "clickY": y, "consumed": False}
        return rebuild(
            omega,
            state=state,
            residuals=(
                {"kind": "pointer-input-pending", "detail": "test-click"},
            ),
        )

    def test_click_inside_link_navigates_then_rerenders(self):
        page1 = self.rendered_page1()
        self.assertEqual(
            page1["state"]["hitMap"],
            [{"x": 4, "y": 4, "width": 24, "height": 7, "href": "page2"}],
        )

        interaction = run_program(
            self.interaction_program,
            self.with_click(page1, 5, 5),
            native_registry(self.interaction_program),
        )
        self.assertEqual(interaction["generation"]["executedCount"], 1)
        self.assertEqual(len(interaction["branches"]), 1)
        navigated = interaction["branches"][0]["omega"]

        self.assertTrue(interaction["branches"][0]["admitted"])
        self.assertEqual(navigated["state"]["location"], "page2")
        self.assertEqual(navigated["state"]["history"], ["page1"])
        self.assertEqual(navigated["state"]["source"], "<h1>DONE</h1>")
        self.assertTrue(navigated["state"]["input"]["consumed"])
        self.assertEqual(
            navigated["residuals"],
            [{"kind": "html-tokenization-pending", "detail": "local-navigation"}],
        )
        self.assertEqual(navigated["state"]["hitMap"], [])
        self.assertEqual(navigated["state"]["camera"]["pixels"], [])
        self.assertFalse(navigated["state"]["camera"]["admitted"])

        rerender = run_program(
            self.render_program,
            navigated,
            native_registry(self.render_program),
        )
        self.assertEqual(rerender["stopReason"], "SUCCESS")
        final = rerender["branches"][0]["omega"]
        self.assertEqual(final["state"]["location"], "page2")
        self.assertEqual(final["state"]["history"], ["page1"])
        self.assertEqual(final["state"]["dom"]["nodes"][1]["tag"], "h1")
        self.assertEqual(final["state"]["dom"]["nodes"][2]["text"], "DONE")
        self.assertTrue(final["state"]["camera"]["verified"])
        self.assertTrue(final["state"]["camera"]["admitted"])

    def test_click_outside_hit_map_preserves_document_and_location(self):
        page1 = self.rendered_page1()
        source_before = page1["state"]["source"]
        location_before = page1["state"]["location"]

        interaction = run_program(
            self.interaction_program,
            self.with_click(page1, 100, 50),
            native_registry(self.interaction_program),
        )
        self.assertEqual(interaction["stopReason"], "SUCCESS")
        self.assertEqual(len(interaction["branches"]), 1)
        miss = interaction["branches"][0]["omega"]

        self.assertEqual(miss["state"]["source"], source_before)
        self.assertEqual(miss["state"]["location"], location_before)
        self.assertEqual(miss["state"]["history"], [])
        self.assertTrue(miss["state"]["input"]["consumed"])
        self.assertEqual(miss["residuals"], [])


if __name__ == "__main__":
    unittest.main()
