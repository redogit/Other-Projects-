from pathlib import Path
import json
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
TOOLS = HERE / "tools"
sys.path.insert(0, str(TOOLS))

from fkdb_index import load_index, search_index  # noqa: E402
from interact_fkdb import bounded_result_text, write_index_result  # noqa: E402


class FkdbResultProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_index()

    def test_single_match_keeps_bounded_title(self):
        result = search_index("Independent Browser", self.data)
        display, remainder = bounded_result_text(result)
        self.assertEqual(display, "INDEPENDENT BROWSER")
        self.assertNotIn("DISPLAY_TRUNCATED", remainder)

    def test_long_failure_title_truncates_only_display(self):
        result = search_index("display failure", self.data)
        display, remainder = bounded_result_text(result)
        self.assertLessEqual(len(display), 25)
        self.assertIn("DISPLAY_TRUNCATED", remainder)
        self.assertEqual(result["candidates"][0]["title"], "FKDB DISPLAY BOUND FAILURE")

    def test_no_match_and_unresolved_are_distinct(self):
        no_match = search_index("MISSING THING", self.data)
        unresolved = search_index("♥", self.data)
        self.assertEqual(bounded_result_text(no_match)[0], "NO LOCAL MATCH")
        self.assertEqual(bounded_result_text(unresolved)[0], "UNRESOLVED QUERY")

    def test_single_match_creates_source_and_recovery_inspection(self):
        result = search_index("Independent Browser", self.data)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = write_index_result(root, result)

            result_html = page.read_text(encoding="utf-8")
            self.assertIn('<a href="source">SOURCE</a>', result_html)
            self.assertIn('<a href="recovery">RECOVERY</a>', result_html)

            source = root / "source.html"
            recovery = root / "recovery.html"
            self.assertTrue(source.is_file())
            self.assertTrue(recovery.is_file())
            self.assertIn("<h1>SOURCE</h1>", source.read_text(encoding="utf-8"))
            self.assertIn("GITHUB SOURCE", source.read_text(encoding="utf-8"))
            self.assertIn(
                "DIRECT PREDECESSOR OF",
                source.read_text(encoding="utf-8"),
            )
            self.assertIn("<h1>RECOVERY</h1>", recovery.read_text(encoding="utf-8"))
            self.assertIn(
                "READ PREDECESSOR SOURCES",
                recovery.read_text(encoding="utf-8"),
            )

            sidecar = json.loads((root / "index_result.json").read_text(encoding="utf-8"))
            self.assertEqual(
                sidecar["candidates"][0]["recovery_path"],
                result["candidates"][0]["recovery_path"],
            )
            self.assertEqual(
                sidecar["surface_projection"]["source"]["provenance_relation"],
                "DIRECT PREDECESSOR OF",
            )

    def test_multiple_candidates_do_not_create_false_inspection_target(self):
        result = search_index("history decay", self.data)
        self.assertGreater(result["candidate_count"], 1)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = write_index_result(root, result)
            html = page.read_text(encoding="utf-8")
            self.assertIn("MULTIPLE CANDIDATES", html)
            self.assertNotIn('href="source"', html)
            self.assertNotIn('href="recovery"', html)
            self.assertFalse((root / "source.html").exists())
            self.assertFalse((root / "recovery.html").exists())

    def test_sidecar_retains_full_result_when_page_is_bounded(self):
        result = search_index("display failure", self.data)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = write_index_result(root, result)
            self.assertTrue(page.is_file())
            self.assertIn("<h1>RESULT</h1>", page.read_text(encoding="utf-8"))
            sidecar = root / "index_result.json"
            self.assertTrue(sidecar.is_file())
            raw = sidecar.read_text(encoding="utf-8")
            self.assertIn("FKDB DISPLAY BOUND FAILURE", raw)
            self.assertIn("DISPLAY_TRUNCATED", raw)


if __name__ == "__main__":
    unittest.main()
