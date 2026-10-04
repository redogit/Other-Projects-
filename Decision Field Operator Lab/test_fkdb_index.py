from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
TOOLS = HERE / "tools"
sys.path.insert(0, str(TOOLS))

from fkdb_index import load_index, search_index  # noqa: E402


class FkdbIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_index()

    def test_independent_browser_recovers_predecessor(self):
        result = search_index("Independent Browser", self.data)
        self.assertEqual(result["raw_query"], "Independent Browser")
        self.assertEqual(result["normalized_tokens"], ["INDEPENDENT", "BROWSER"])
        self.assertEqual(result["status"], "MATCH")
        self.assertEqual([c["id"] for c in result["candidates"]], ["IB-001"])
        self.assertEqual(result["candidates"][0]["provenance"]["relation"], "DIRECT_PREDECESSOR_OF")

    def test_failure_is_retrievable_not_discarded(self):
        result = search_index("display failure", self.data)
        self.assertEqual(result["status"], "MATCH")
        self.assertEqual([c["id"] for c in result["candidates"]], ["FKDB-F6-001"])
        self.assertEqual(result["candidates"][0]["state"], "RETAINED")

    def test_multiple_candidates_remain_explicit(self):
        result = search_index("history decay", self.data)
        self.assertEqual(result["status"], "MATCH")
        self.assertGreaterEqual(result["candidate_count"], 2)
        self.assertIn("MULTIPLE_CANDIDATES_REMAIN", result["remainder"])

    def test_no_match_is_not_falsehood(self):
        result = search_index("MISSING THING", self.data)
        self.assertEqual(result["status"], "NO_MATCH")
        self.assertEqual(result["candidates"], [])
        self.assertIn("NO_LOCAL_BOUNDED_MATCH", result["remainder"])
        self.assertIn("LOCAL_INDEX != GLOBAL_HISTORY", result["claim_ceiling"])

    def test_unsupported_query_is_unresolved(self):
        result = search_index("♥", self.data)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertEqual(result["candidates"], [])
        self.assertIn("NO_SUPPORTED_QUERY_TOKENS", result["remainder"])

    def test_scan_cost_is_explicit(self):
        result = search_index("FKDB", self.data)
        self.assertEqual(result["scan_cost"]["records_scanned"], len(self.data["records"]))
        self.assertEqual(result["scan_cost"]["query_tokens"], 1)
        self.assertEqual(result["scan_cost"]["comparison_units"], len(self.data["records"]))


if __name__ == "__main__":
    unittest.main()
