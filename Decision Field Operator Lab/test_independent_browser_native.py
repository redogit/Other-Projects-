from pathlib import Path
import unittest

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from rmapl_runtime import run_program


HERE = Path(__file__).resolve().parent
PROGRAM_PATH = HERE / "examples" / "independent_browser_native.rmapl"


def browser_omega(source="<h1>HI</h1><p>WEB</p>"):
    return make_omega(
        native_type="independent-browser/v0",
        native_identity="fixture:independent-browser:1",
        source_refs=("inline:fixture",),
        state={
            "source": source,
            "html": {"tokens": []},
            "dom": {"nodes": []},
            "layout": {"boxes": []},
            "camera": {
                "width": 160,
                "height": 64,
                "pixels": [],
                "verified": False,
                "admitted": False,
                "blackPixels": 0,
            },
        },
        path=(),
        frame={"obligation": "render-bounded-html-to-owned-framebuffer"},
        invariants=("sourceRefs", "claim-ceiling"),
        observations=(),
        residuals=(
            {"kind": "html-tokenization-pending", "detail": "fixture"},
        ),
        decision_field={"goal": "admitted-independent-frame"},
        provenance=(
            {"kind": "fixture", "ref": "independent-browser-native"},
        ),
        evidence=(),
        claim_ceiling=(
            "BOUNDED_HTML_SUBSET != GENERAL_WEB_COMPATIBILITY",
            "MONO8_FRAMEBUFFER != OS_WINDOW_PRESENTATION",
            "SOFTWARE_VERIFICATION != SECURITY_CERTIFICATION",
        ),
        resource_bounds={"maxCandidates": 1, "maxSteps": 6},
        domain_remainder={
            "unsupported": [
                "network",
                "tls",
                "css",
                "javascript",
                "images",
                "forms",
                "unicode-non-ascii-tokenization",
                "html-error-recovery",
                "os-window-presentation",
            ]
        },
    )


class IndependentBrowserNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = parse_rmapl(PROGRAM_PATH.read_text(encoding="utf-8"))

    def test_all_browser_apply_targets_are_rmapl_native(self):
        registry = native_registry(self.program)
        self.assertEqual(
            set(registry),
            {
                "browser_html_tokenize",
                "browser_dom_build",
                "browser_layout",
                "browser_raster",
                "browser_frame_verify",
                "browser_frame_admit",
            },
        )
        self.assertEqual(
            {spec.operator for spec in self.program.repairs},
            set(registry),
        )

    def test_bounded_html_reaches_verified_admitted_owned_framebuffer(self):
        result = run_program(
            self.program,
            browser_omega(),
            native_registry(self.program),
        )

        self.assertEqual(result["stopReason"], "SUCCESS")
        self.assertEqual(result["generation"]["executedCount"], 6)
        self.assertEqual(len(result["branches"]), 1)

        branch = result["branches"][0]
        self.assertTrue(branch["admitted"])
        self.assertEqual(branch["classification"], "EXACT_REPAIR")

        omega = branch["omega"]
        state = omega["state"]
        self.assertEqual(omega["residuals"], [])

        self.assertEqual(
            state["html"]["tokens"],
            [
                {"kind": "start", "name": "h1", "value": ""},
                {"kind": "text", "name": "", "value": "HI"},
                {"kind": "end", "name": "h1", "value": ""},
                {"kind": "start", "name": "p", "value": ""},
                {"kind": "text", "name": "", "value": "WEB"},
                {"kind": "end", "name": "p", "value": ""},
            ],
        )

        nodes = state["dom"]["nodes"]
        self.assertEqual(len(nodes), 5)
        self.assertEqual(nodes[1]["tag"], "h1")
        self.assertEqual(nodes[2]["text"], "HI")
        self.assertEqual(nodes[2]["parent"], 1)
        self.assertEqual(nodes[3]["tag"], "p")
        self.assertEqual(nodes[4]["text"], "WEB")
        self.assertEqual(nodes[4]["parent"], 3)

        boxes = state["layout"]["boxes"]
        self.assertEqual(len(boxes), 2)
        self.assertEqual(
            boxes[0],
            {"x": 4, "y": 4, "width": 24, "height": 14, "scale": 2, "text": "HI"},
        )
        self.assertEqual(
            boxes[1],
            {"x": 4, "y": 22, "width": 18, "height": 7, "scale": 1, "text": "WEB"},
        )

        camera = state["camera"]
        self.assertEqual(camera["width"], 160)
        self.assertEqual(camera["height"], 64)
        self.assertEqual(len(camera["pixels"]), 160 * 64)
        self.assertTrue(camera["verified"])
        self.assertTrue(camera["admitted"])
        self.assertGreater(camera["blackPixels"], 0)

        # H glyph, row 0 / column 0 at x=4,y=4 with scale=2.
        self.assertEqual(camera["pixels"][4 * 160 + 4], 0)
        self.assertEqual(camera["pixels"][0], 255)

    def test_unterminated_tag_is_preserved_as_explicit_residual(self):
        result = run_program(
            self.program,
            browser_omega("<h1"),
            native_registry(self.program),
        )
        self.assertEqual(result["stopReason"], "NO_ADMISSIBLE_PROGRESS")
        self.assertEqual(result["generation"]["executedCount"], 1)
        # The runtime intentionally exposes no later admitted branch when the
        # next residual has no matching repair. The execution count proves the
        # tokenizer ran and did not silently continue to DOM/layout/raster.
        self.assertEqual(result["branches"], [])


if __name__ == "__main__":
    unittest.main()
