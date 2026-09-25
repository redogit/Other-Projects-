from pathlib import Path
import tempfile
import unittest
import hodge_compass_api as api

class APITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.idx=api.Index(Path(self.tmp.name)/"x.sqlite")
    def tearDown(self):
        self.idx.close(); self.tmp.cleanup()
    def record(self,surface,text="same object"):
        return {
            "semantic_object_id":"obj:compass-hodge","kind":"thread","domain":"hodge",
            "title":"Compass Hodge","claim_ceiling":"METHOD_ONLY",
            "occurrence":{"surface":surface,"source_ref":f"{surface}:1","authority":"lineage",
                          "status":"CURRENT","text":text,"provenance":[surface]},
            "relations":[{"target_object_id":"hodge:w114","type":"RELATES_TO",
                          "permission":"ALLOW","provenance":[surface]}]}
    def test_normal_work_are_two_occurrences_one_object(self):
        a=self.idx.ingest(self.record("normal")); b=self.idx.ingest(self.record("work"))
        self.assertNotEqual(a["occurrence_id"],b["occurrence_id"])
        obj=self.idx.get_object("obj:compass-hodge")
        self.assertEqual(len(obj["occurrences"]),2)
        self.assertTrue(all(r["evidence_transfer"]=="DENY" for r in obj["relations"]))
    def test_search(self):
        self.idx.ingest(self.record("normal","W114 alpha target and Compass remainder"))
        self.assertEqual(self.idx.search({"q":"W114","limit":10})[0]["semantic_object_id"],"obj:compass-hodge")
    def test_exact_observer_remainder(self):
        out=api.exact_observer_remainder({
            "ground_truth":["1","2","3","5"],"baseline":["1","2","3","0"],
            "observers":[
                {"id":"xyz","matrix":[[1,0,0,0],[0,1,0,0],[0,0,1,0]]},
                {"id":"w","matrix":[[0,0,0,1]]}]})
        self.assertFalse(out["observer_results"][0]["sees_remainder"])
        self.assertTrue(out["observer_results"][1]["sees_remainder"])
        self.assertEqual(out["combined_observer_rank"],4)
        self.assertEqual(out["collective_blind_dimension"],0)
    def test_float_rejected(self):
        with self.assertRaises(TypeError):
            api.exact_observer_remainder({"ground_truth":[1.0],"baseline":[0],
                                          "observers":[{"id":"x","matrix":[[1]]}]})
    def test_w114_contract(self):
        self.assertEqual(api.W114["alpha"],[1,7,78,79,86,91])
        self.assertEqual(api.W114["jacobian_degree"],336)
        self.assertIn("FULL_HODGE_PROOF",api.W114["claim_ceiling"])
    def test_source_catalog_is_revision_pinned_and_searchable(self):
        root=Path(__file__).resolve().parents[1]
        out=api.source_search(root,{"q":"W114","limit":200})
        self.assertTrue(out["generated_from"]["conscience64"]["sha"])
        self.assertTrue(any("w114" in x["path"].lower() for x in out["results"]))
        full=api.source_search(root,{"limit":500})
        self.assertGreaterEqual(full["count"],100)

if __name__=="__main__": unittest.main()
