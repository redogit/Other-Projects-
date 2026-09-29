#!/usr/bin/env python3
"""Synthetic local benchmark for the Hodge Compass index. No network."""
from pathlib import Path
import argparse, importlib.util, statistics, tempfile, time

def load_api():
    p=Path(__file__).with_name("hodge_compass_api.py")
    s=importlib.util.spec_from_file_location("hodge_compass_api",p)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def main():
    a=argparse.ArgumentParser();a.add_argument("--records",type=int,default=3000);a.add_argument("--queries",type=int,default=200);x=a.parse_args()
    api=load_api(); n=x.records
    with tempfile.TemporaryDirectory() as d:
        idx=api.Index(Path(d)/"index.sqlite3"); records=[]
        for i in range(n):
            surface="normal" if i%2==0 else "work"; obj=i//2
            records.append({
              "semantic_object_id":f"hodge:bench:{obj}","kind":"thread","domain":"hodge",
              "title":f"W114 Compass residual {obj}","claim_ceiling":"METHOD_ONLY",
              "occurrence":{"surface":surface,"source_ref":f"{surface}:{i}","authority":"lineage",
                "status":"CURRENT","text":f"W114 alpha Compass remainder observer projection exact record {i}",
                "provenance":[surface]},"relations":[]})
        t=time.perf_counter()
        for j in range(0,n,1000): idx.ingest_many(records[j:j+1000])
        ingest=time.perf_counter()-t
        q=[]
        for _ in range(x.queries):
            t=time.perf_counter(); idx.search({"q":"W114 Compass remainder","limit":20}); q.append(time.perf_counter()-t)
        s=idx.stats();idx.close()
        print({
          "records":n,"objects":s["objects"],"fts5":s["fts5"],
          "ingest_seconds":round(ingest,4),"records_per_second":round(n/ingest,1),
          "search_p50_ms":round(statistics.median(q)*1000,4),
          "search_p95_ms":round(sorted(q)[max(0,int(.95*len(q))-1)]*1000,4)})

if __name__=="__main__":main()
