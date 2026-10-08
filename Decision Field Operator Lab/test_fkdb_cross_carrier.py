from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
TOOLS=HERE/"tools"
sys.path.insert(0,str(TOOLS))

from fkdb_cross_carrier import admit_tool_carriers, build_external_index_records


def carrier(cid,tool,source,payload,authority,subject=None,claim=None):
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"))
    digest=hashlib.sha256(raw.encode()).hexdigest()
    provenance={"provider":tool}
    if subject is not None: provenance["subject_key"]=subject
    if claim is not None: provenance["claim_value"]=claim
    return {
        "schema":"fkdb/tool-carrier/v1","carrier_id":cid,"tool_id":tool,
        "tool_version":"1","adapter_kind":"PORTABLE_IMPORT","locality":"PORTABLE_IMPORT",
        "source_identity":source,"source_version":digest,
        "retrieved_at":"2026-10-08T00:00:00Z","payload_type":"application/json",
        "payload":raw,"content_hash":digest,"provenance":provenance,
        "authority_scope":authority,"evidence_status":"PORTABLE_PROVIDER_RECORD_UNVERIFIED",
        "obligation":"IMPORT","relations":[],"cost":{"bytes_read":len(raw)},
        "loss":[],"remainder":[],"recovery_path":"re-read source",
    }


class CrossCarrierTests(unittest.TestCase):
    def test_admission_preserves_provider_authority_and_source_identity(self):
        c=carrier("c1","exa","exa.json#1",{"title":"A"},"SEARCH_DISCOVERY_ONLY")
        result=admit_tool_carriers([c])
        self.assertEqual(result["status"],"ADMITTED")
        rec=result["records"][0]
        self.assertEqual(rec["source_carrier_id"],"c1")
        self.assertEqual(rec["source_identity"],"exa.json#1")
        self.assertEqual(rec["authority_scope"],"SEARCH_DISCOVERY_ONLY")
        self.assertEqual(rec["evidence_status"],"PORTABLE_PROVIDER_RECORD_UNVERIFIED")
        self.assertFalse(rec["evidence_promoted"])

    def test_duplicate_carrier_id_is_rejected(self):
        c=carrier("c1","exa","x",{},"SEARCH_DISCOVERY_ONLY")
        with self.assertRaisesRegex(ValueError,"duplicate carrier_id"):
            admit_tool_carriers([c,c])

    def test_contradictions_require_same_explicit_subject_and_different_claim(self):
        a=carrier("a","consensus","a",{},"RESEARCH_SYNTHESIS_ONLY","paper:1","supports")
        b=carrier("b","scispace","b",{},"RESEARCH_DISCOVERY_ONLY","paper:1","rejects")
        c=carrier("c","exa","c",{},"SEARCH_DISCOVERY_ONLY","paper:2","rejects")
        result=admit_tool_carriers([a,b,c])
        self.assertEqual(result["status"],"ADMITTED_WITH_CONTRADICTIONS")
        self.assertEqual(len(result["contradictions"]),1)
        pair=set(result["contradictions"][0]["carrier_ids"])
        self.assertEqual(pair,{"a","b"})
        self.assertIn("CONTRADICTION_REQUIRES_INSPECTION",result["remainder"])

    def test_no_subject_key_means_no_inferred_contradiction(self):
        a=carrier("a","consensus","a",{},"RESEARCH_SYNTHESIS_ONLY",claim="yes")
        b=carrier("b","scispace","b",{},"RESEARCH_DISCOVERY_ONLY",claim="no")
        result=admit_tool_carriers([a,b])
        self.assertEqual(result["contradictions"],[])

    def test_external_records_are_separate_from_static_index_and_queryable_terms_are_bounded(self):
        c=carrier("c1","linear","linear.json#ISS-1",{"title":"Fix browser","labels":["fkdb"]},"PROJECT_WORKFLOW_ONLY")
        admitted=admit_tool_carriers([c])
        records=build_external_index_records(admitted["records"],max_terms=8)
        self.assertEqual(len(records),1)
        rec=records[0]
        self.assertTrue(rec["id"].startswith("EXT-"))
        self.assertEqual(rec["kind"],"EXTERNAL_TOOL_CARRIER")
        self.assertLessEqual(len(rec["terms"]),8)
        self.assertEqual(rec["provenance"]["relation"],"IMPORTED_FROM_TOOL_CARRIER")
        self.assertEqual(rec["evidence_status"],"PORTABLE_PROVIDER_RECORD_UNVERIFIED")


if __name__=="__main__":
    unittest.main()
