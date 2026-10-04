from pathlib import Path
import json
import re
import unittest


HERE = Path(__file__).resolve().parent
PAGES = HERE / "fkdb" / "pages"
MANIFEST = PAGES / "manifest.json"
HREF = re.compile(r'href="([^"]+)"')


class FkdbManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_direct_successor_identity(self):
        self.assertEqual(self.data["schema"], "fkdb/page-manifest/v1")
        self.assertEqual(self.data["project"], "FKDB")
        self.assertEqual(self.data["lineage"]["kind"], "DIRECT_SUCCESSOR")
        self.assertEqual(self.data["lineage"]["predecessor"], "Independent Browser")

    def test_query_progression_is_explicit(self):
        self.assertEqual(
            self.data["query_progression"],
            ["NEED", "HISTORY", "DECAY", "RECOVER", "RELATE", "RETURN"],
        )

    def test_every_page_has_recovery_metadata(self):
        ids = set()
        for page in self.data["pages"]:
            self.assertTrue(page["id"])
            self.assertNotIn(page["id"], ids)
            ids.add(page["id"])
            self.assertTrue(page["title"])
            self.assertTrue(page["role"])
            self.assertTrue(page["purpose"])
            self.assertTrue(page["provenance"])
            self.assertTrue(page["recovery_path"])
            self.assertEqual(page["state"], "ACTIVE")
            self.assertTrue((PAGES / page["file"]).is_file())
        self.assertIn(self.data["start_page"], ids)

    def test_declared_relations_match_navigable_links(self):
        ids = {page["id"] for page in self.data["pages"]}
        for page in self.data["pages"]:
            source = (PAGES / page["file"]).read_text(encoding="utf-8")
            hrefs = HREF.findall(source)
            self.assertEqual(hrefs, page["relations"])
            self.assertTrue(set(hrefs).issubset(ids))

    def test_claim_ceiling_blocks_silent_promotion(self):
        ceilings = set(self.data["claim_ceiling"])
        self.assertIn("PAGE_MANIFEST != KNOWLEDGE", ceilings)
        self.assertIn("RELATION != EVIDENCE_TRANSFER", ceilings)
        self.assertIn("RECOVERED_PAGE != RECOVERED_MEANING", ceilings)


if __name__ == "__main__":
    unittest.main()
