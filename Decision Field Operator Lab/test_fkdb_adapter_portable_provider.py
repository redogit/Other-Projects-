from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
TOOLS=HERE/"tools"
sys.path.insert(0,str(TOOLS))

from fkdb_adapter_portable_provider import PortableProviderAdapter
from fkdb_local_adapters import LocalAdapterRegistry
from fkdb_local_tool_bridge import BridgePolicy


POLICIES={
    "scispace":"RESEARCH_DISCOVERY_ONLY",
    "consensus":"RESEARCH_SYNTHESIS_ONLY",
    "exa":"SEARCH_DISCOVERY_ONLY",
    "linear":"PROJECT_WORKFLOW_ONLY",
}


class PortableProviderTests(unittest.TestCase):
    def policy(self,root,max_files=8,max_bytes=65536):
        return BridgePolicy.from_dict({
            "schema":"fkdb/local-tool-policy/v1","network_policy":"LOOPBACK_ONLY",
            "read_roots":[str(root)],"write_roots":[],"processes":[],
            "max_import_bytes":65536,"max_request_bytes":65536,
            "environment_allowlist":[],"adapter_max_files":max_files,
            "adapter_max_bytes":max_bytes,
            "adapters":[{"tool_id":p,"enabled":True} for p in POLICIES],
        })

    def registry(self):
        r=LocalAdapterRegistry()
        for provider,scope in POLICIES.items():
            r.register(PortableProviderAdapter(provider,scope))
        return r

    def write(self,root,provider,records):
        path=root/f"{provider}.json"
        path.write_text(json.dumps({
            "schema":"fkdb/portable-provider/v1",
            "provider":provider,
            "exported_at":"2026-10-08T00:00:00Z",
            "records":records,
        }),encoding="utf-8")
        return path

    def test_all_provider_authority_scopes_and_raw_records_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for provider,scope in POLICIES.items():
                path=self.write(root,provider,[{
                    "external_id":provider+"-1","title":"Title",
                    "query":"q","rank":1,"status":"done",
                }])
                result=self.registry().collect(provider,{
                    "root":str(root),
                    "options":{"path":path.name},
                },self.policy(root))
                self.assertEqual(result["status"],"COLLECTED")
                self.assertEqual(len(result["carriers"]),1)
                carrier=result["carriers"][0]
                self.assertEqual(carrier["authority_scope"],scope)
                self.assertEqual(carrier["provenance"]["provider"],provider)
                raw=json.loads(carrier["payload"])
                self.assertEqual(raw["external_id"],provider+"-1")
                self.assertEqual(raw["rank"],1)
                self.assertEqual(raw["status"],"done")
                self.assertEqual(carrier["evidence_status"],"PORTABLE_PROVIDER_RECORD_UNVERIFIED")

    def test_provider_spoofing_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            path=self.write(root,"exa",[{"external_id":"1"}])
            with self.assertRaisesRegex(ValueError,"provider"):
                self.registry().collect("scispace",{
                    "root":str(root),"options":{"path":path.name}
                },self.policy(root))

    def test_wrong_schema_and_malformed_record_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            path=root/"exa.json"
            path.write_text(json.dumps({
                "schema":"fkdb/portable-provider/v99",
                "provider":"exa","exported_at":"x","records":[{}],
            }),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"schema"):
                self.registry().collect("exa",{
                    "root":str(root),"options":{"path":path.name}
                },self.policy(root))

            path.write_text(json.dumps({
                "schema":"fkdb/portable-provider/v1",
                "provider":"exa","exported_at":"x","records":[42,{"external_id":"ok"}],
            }),encoding="utf-8")
            result=self.registry().collect("exa",{
                "root":str(root),"options":{"path":path.name}
            },self.policy(root))
            self.assertEqual(result["status"],"PARTIAL")
            self.assertIn("PORTABLE_PROVIDER_MALFORMED_RECORD:0",result["remainder"])
            self.assertEqual(len(result["carriers"]),1)

    def test_record_and_byte_bounds_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            path=self.write(root,"linear",[{"external_id":str(i),"text":"x"*20} for i in range(20)])
            result=self.registry().collect("linear",{
                "root":str(root),"options":{"path":path.name,"max_records":2}
            },self.policy(root))
            self.assertEqual(result["status"],"PARTIAL")
            self.assertEqual(len(result["carriers"]),2)
            self.assertIn("PORTABLE_PROVIDER_RECORD_LIMIT_REACHED",result["remainder"])

    def test_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root=Path(tmp); ext=Path(outside)/"exa.json"
            self.write(Path(outside),"exa",[{"external_id":"1"}])
            with self.assertRaises(PermissionError):
                self.registry().collect("exa",{
                    "root":str(root),"options":{"path":str(ext)}
                },self.policy(root))


if __name__=="__main__":
    unittest.main()
