from copy import deepcopy
from pathlib import Path
import unittest

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from rmapl_runtime import run_program


HERE = Path(__file__).resolve().parent
PROGRAM_PATH = HERE / "examples" / "independent_browser_keyboard.rmapl"
PAGES_DIR = HERE / "fkdb" / "pages"


def load_page(page_id: str) -> str:
    return (PAGES_DIR / f"{page_id}.html").read_text(encoding="utf-8")


def fkdb_omega():
    page_ids = ("fkdb", "history", "decay", "recover", "relate", "tools", "lineage")
    pages = [{"id": page_id, "source": load_page(page_id)} for page_id in page_ids]
    home = pages[0]["source"]
    return make_omega(
        native_type="fkdb-local-surface/v0",
        native_identity="fixture:fkdb-direct-successor:2",
        source_refs=tuple(f"fkdb-page:{page['id']}" for page in pages),
        state={
            "source": home,
            "resources": {"pages": pages},
            "navigation": {
                "currentPage": "fkdb",
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
        frame={"obligation": "fkdb-human-reconnectable-local-navigation"},
        invariants=("sourceRefs", "claim-ceiling"),
        observations=(),
        residuals=(
            {"kind": "html-tokenization-pending", "detail": "fkdb-bootstrap"},
        ),
        decision_field={"goal": "browse-fkdb-progression"},
        provenance=(
            {"kind": "direct-successor", "ref": "Independent Browser -> FKDB"},
        ),
        evidence=(),
        claim_ceiling=(
            "DIRECT_SUCCESSOR != RETROACTIVE_RENAME",
            "LOCAL_FKDB_SURFACE != COMPLETE_KNOWLEDGE_RECOVERY",
            "SOFTWARE_VERIFICATION != SEMANTIC_TRUTH",
        ),
        resource_bounds={"maxCandidates": 1, "maxSteps": 10},
        domain_remainder={
            "unsupported": [
                "semantic-free-text-query",
                "dynamic-history-index",
                "cross-carrier-live-search",
                "scrolling",
            ]
        },
    )


def keyboard_input(omega, key):
    construction = deepcopy(omega["construction"])
    construction["state"]["input"]["keyboard"] = key
    construction["state"]["input"]["lastHit"] = ""
    construction["residuals"] = [
        {"kind": "keyboard-activation-pending", "detail": "fkdb-key"}
    ]
    return make_omega(**construction)


class FkdbLocalSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = parse_rmapl(PROGRAM_PATH.read_text(encoding="utf-8"))
        cls.registry = native_registry(cls.program)

    def run_one(self, omega):
        result = run_program(self.program, omega, self.registry)
        self.assertEqual(len(result["branches"]), 1)
        self.assertTrue(result["branches"][0]["admitted"])
        return result["branches"][0]["omega"], result

    def activate_first_link(self, omega, expected_href):
        focused, _ = self.run_one(keyboard_input(omega, "TAB"))
        self.assertEqual(focused["state"]["navigation"]["focusedHref"], expected_href)
        activated, result = self.run_one(keyboard_input(focused, "ENTER"))
        self.assertEqual(result["stopReason"], "SUCCESS")
        self.assertEqual(activated["state"]["navigation"]["currentPage"], expected_href)
        self.assertTrue(activated["state"]["camera"]["verified"])
        self.assertTrue(activated["state"]["camera"]["admitted"])
        return activated

    def test_home_renders_progression_entry_and_lineage(self):
        home, result = self.run_one(fkdb_omega())
        self.assertEqual(result["stopReason"], "SUCCESS")
        self.assertEqual(home["state"]["navigation"]["currentPage"], "fkdb")
        self.assertEqual(
            [hit["href"] for hit in home["state"]["hitMap"]],
            ["history", "tools", "lineage"],
        )
        self.assertTrue(home["state"]["camera"]["verified"])
        self.assertTrue(home["state"]["camera"]["admitted"])
        self.assertGreater(home["state"]["camera"]["blackPixels"], 0)

    def test_keyboard_walks_decay_recovery_progression_and_returns(self):
        current, _ = self.run_one(fkdb_omega())
        for page_id in ("history", "decay", "recover", "relate", "fkdb"):
            current = self.activate_first_link(current, page_id)

        self.assertEqual(current["state"]["navigation"]["currentPage"], "fkdb")
        self.assertEqual(
            current["state"]["navigation"]["history"],
            ["fkdb", "history", "decay", "recover", "relate"],
        )
        self.assertEqual(
            [hit["href"] for hit in current["state"]["hitMap"]],
            ["history", "lineage"],
        )
    def test_keyboard_opens_tools_surface_and_returns(self):
        home, _ = self.run_one(fkdb_omega())
        first_focus, _ = self.run_one(keyboard_input(home, "TAB"))
        self.assertEqual(first_focus["state"]["navigation"]["focusedHref"], "history")
        second_focus, _ = self.run_one(keyboard_input(first_focus, "TAB"))
        self.assertEqual(second_focus["state"]["navigation"]["focusedHref"], "tools")
        tools, _ = self.run_one(keyboard_input(second_focus, "ENTER"))
        self.assertEqual(tools["state"]["navigation"]["currentPage"], "tools")
        self.assertEqual(
            [hit["href"] for hit in tools["state"]["hitMap"]],
            ["fkdb"],
        )
        returned = self.activate_first_link(tools, "fkdb")
        self.assertEqual(returned["state"]["navigation"]["currentPage"], "fkdb")


if __name__ == "__main__":
    unittest.main()
