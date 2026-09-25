#!/usr/bin/env python3
"""Provenance-first Compass/Hodge query API. Standard library only."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, sqlite3, sys
from fractions import Fraction
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

SCHEMA="hodge-compass-api/v1"; HOST="127.0.0.1"; PORT=8765; DB=".hodge-compass/index.sqlite3"
BOUNDARIES=[
 "RELATION != IDENTITY",
 "NORMAL_OCCURRENCE + WORK_OCCURRENCE != INDEPENDENT_CORROBORATION",
 "METHOD_TRANSFER != EVIDENCE_TRANSFER",
 "OBSERVABLE_REMAINDER != ALGEBRAIC_REALIZATION",
 "PROJECTION != FULL_STATE",
 "NONZERO_TARGET_COEFFICIENT != FULL_HODGE_PROOF",
 "FAILED_ANSATZ != NONALGEBRAIC_CLASS",
]
W114={"semantic_object_id":"hodge:w114:alpha:1-7-78-79-86-91","alpha":[1,7,78,79,86,91],
 "jacobian_monomial":{"x1":6,"x2":77,"x3":78,"x4":85,"x5":90},"jacobian_degree":336,
 "factorization_obligation":"AB = BA = Q I exactly",
 "success_criterion":"coeff_M_W114(T(A,B) mod (x0^113,...,x5^113)) != 0",
 "issue":"https://github.com/redogit/conscience64/issues/99",
 "claim_ceiling":"NONZERO_TARGET_COEFFICIENT != FULL_HODGE_PROOF"}

def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def sha(x): return hashlib.sha256(canon(x).encode()).hexdigest()
def frac(x):
    if isinstance(x,bool) or isinstance(x,float): raise TypeError("use exact int or rational string; floats rejected")
    if isinstance(x,(int,str)): return Fraction(x)
    raise TypeError("not an exact rational")
def ftxt(x): return str(x.numerator) if x.denominator==1 else f"{x.numerator}/{x.denominator}"
def rank(rows):
    if not rows:return 0
    a=[r[:] for r in rows]; n=len(a[0]); r=0
    if any(len(x)!=n for x in a): raise ValueError("ragged matrix")
    for c in range(n):
        p=next((i for i in range(r,len(a)) if a[i][c]),None)
        if p is None: continue
        a[r],a[p]=a[p],a[r]; q=a[r][c]; a[r]=[x/q for x in a[r]]
        for i in range(len(a)):
            if i!=r and a[i][c]:
                q=a[i][c]; a[i]=[x-q*y for x,y in zip(a[i],a[r])]
        r+=1
        if r==len(a): break
    return r

def observe(p):
    if set(p)-{"object_id","ground_truth","baseline","observers"}: raise ValueError("unsupported field")
    g=[frac(x) for x in p.get("ground_truth",[])]; b=[frac(x) for x in p.get("baseline",[])]
    if not g or len(g)!=len(b) or len(g)>64: raise ValueError("state dimensions must match and be 1..64")
    rows=[]; out=[]
    obs=p.get("observers")
    if not isinstance(obs,list) or not 1<=len(obs)<=64: raise ValueError("observers must be list 1..64")
    for o in obs:
        if set(o)!={"id","matrix"}: raise ValueError("observer requires id,matrix")
        m=[[frac(x) for x in row] for row in o["matrix"]]
        if not m or any(len(row)!=len(g) for row in m): raise ValueError("observer dimension mismatch")
        rows+=m
        og=[sum((x*y for x,y in zip(row,g)),Fraction()) for row in m]
        ob=[sum((x*y for x,y in zip(row,b)),Fraction()) for row in m]
        d=[x-y for x,y in zip(og,ob)]
        out.append({"observer_id":o["id"],"observed":[ftxt(x) for x in og],"expected":[ftxt(x) for x in ob],
                    "residual":[ftxt(x) for x in d],"sees_remainder":any(d)})
    rr=rank(rows)
    return {"schema":"hodge-compass-observer-remainder/v1","object_id":p.get("object_id","controlled:anonymous"),
            "hidden_remainder":[ftxt(x-y) for x,y in zip(g,b)],"remainder_nonzero":g!=b,
            "observer_results":out,"combined_observer_rank":rr,"collective_blind_dimension":len(g)-rr,
            "collectively_detected":any(x["sees_remainder"] for x in out),"boundaries":BOUNDARIES}

exact_observer_remainder = observe

class Index:
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.path,timeout=30,check_same_thread=False); self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL"); self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS objects(id TEXT PRIMARY KEY,kind TEXT,domain TEXT,title TEXT,claim_ceiling TEXT,payload TEXT,sha TEXT);
        CREATE TABLE IF NOT EXISTS occurrences(id TEXT PRIMARY KEY,object_id TEXT,surface TEXT,source_ref TEXT,authority TEXT,status TEXT,text TEXT,provenance TEXT,sha TEXT);
        CREATE INDEX IF NOT EXISTS occ_obj ON occurrences(object_id); CREATE INDEX IF NOT EXISTS occ_surface ON occurrences(surface);
        CREATE TABLE IF NOT EXISTS relations(id TEXT PRIMARY KEY,source_id TEXT,target_id TEXT,type TEXT,permission TEXT,evidence_transfer TEXT,provenance TEXT,sha TEXT);
        CREATE INDEX IF NOT EXISTS rel_s ON relations(source_id); CREATE INDEX IF NOT EXISTS rel_t ON relations(target_id);
        """)
        try:
            self.db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(occurrence_id UNINDEXED,object_id UNINDEXED,domain UNINDEXED,surface UNINDEXED,title,text)"); self.fts=True
        except sqlite3.OperationalError:self.fts=False
        self.db.commit()
    def close(self):self.db.close()
    def relation(self,s,rel):
        t=rel["target_object_id"]; typ=rel["type"]; perm=rel.get("permission","ALLOW"); ev=rel.get("evidence_transfer","DENY"); prov=rel.get("provenance",[])
        if perm not in {"ALLOW","DENY","UNKNOWN"} or ev not in {"ALLOW","DENY"}: raise ValueError("bad relation gate")
        body={"source_object_id":s,"target_object_id":t,"type":typ,"permission":perm,"evidence_transfer":ev,"provenance":prov}
        rid=rel.get("relation_id",f"rel:{sha(body)}")
        self.db.execute("INSERT OR REPLACE INTO relations VALUES(?,?,?,?,?,?,?,?)",(rid,s,t,typ,perm,ev,canon(prov),sha(body)))
        return rid
    def ingest(self,r):
        need={"semantic_object_id","kind","domain","title","claim_ceiling","occurrence"}
        if need-set(r): raise ValueError(f"missing {sorted(need-set(r))}")
        sid=r["semantic_object_id"]; obj={k:r[k] for k in ["semantic_object_id","kind","domain","title","claim_ceiling"]}
        self.db.execute("INSERT OR REPLACE INTO objects VALUES(?,?,?,?,?,?,?)",(sid,r["kind"],r["domain"],r["title"],r["claim_ceiling"],canon(obj),sha(obj)))
        o=r["occurrence"]; prov=o.get("provenance",[])
        body={"semantic_object_id":sid,"surface":o["surface"],"source_ref":o["source_ref"],"authority":o["authority"],"status":o["status"],"text":o["text"],"provenance":prov}
        oid=o.get("occurrence_id",f"occ:{sha(body)}")
        self.db.execute("INSERT OR REPLACE INTO occurrences VALUES(?,?,?,?,?,?,?,?,?)",(oid,sid,o["surface"],o["source_ref"],o["authority"],o["status"],o["text"],canon(prov),sha(body)))
        if self.fts:
            self.db.execute("DELETE FROM fts WHERE occurrence_id=?",(oid,)); self.db.execute("INSERT INTO fts VALUES(?,?,?,?,?,?)",(oid,sid,r["domain"],o["surface"],r["title"],o["text"]))
        for rel in r.get("relations",[]): self.relation(sid,rel)
        self.db.commit(); return {"semantic_object_id":sid,"occurrence_id":oid,"object_sha256":sha(obj),"occurrence_sha256":sha(body)}
    def get(self,sid):
        o=self.db.execute("SELECT * FROM objects WHERE id=?",(sid,)).fetchone()
        if not o:return None
        d=dict(o); d["payload"]=json.loads(d.pop("payload")); d["occurrences"]=[dict(x) for x in self.db.execute("SELECT * FROM occurrences WHERE object_id=?",(sid,))]; d["relations"]=[dict(x) for x in self.db.execute("SELECT * FROM relations WHERE source_id=? OR target_id=?",(sid,sid))]
        return d
    get_object = get
    def search(self,p):
        q=str(p.get("q","")).strip(); limit=int(p.get("limit",20)); surf=p.get("surface"); dom=p.get("domain"); sid=p.get("semantic_object_id")
        if not 1<=limit<=200: raise ValueError("limit 1..200")
        a=[]
        if q and self.fts:
            s="SELECT occurrence_id,object_id AS semantic_object_id,domain,surface,title,text,bm25(fts) score FROM fts WHERE fts MATCH ?"; a=[q]
            if surf:s+=" AND surface=?";a+=[surf]
            if dom:s+=" AND domain=?";a+=[dom]
            if sid:s+=" AND object_id=?";a+=[sid]
            s+=" ORDER BY score LIMIT ?";a+=[limit]; return [dict(x) for x in self.db.execute(s,a)]
        s="SELECT x.id occurrence_id,x.object_id AS semantic_object_id,o.domain,x.surface,o.title,x.text,0 score FROM occurrences x JOIN objects o ON o.id=x.object_id WHERE 1=1"
        if q:s+=" AND (o.title LIKE ? OR x.text LIKE ?)";a += [f"%{q}%",f"%{q}%"]
        if surf:s+=" AND x.surface=?";a+=[surf]
        if dom:s+=" AND o.domain=?";a+=[dom]
        if sid:s+=" AND x.object_id=?";a+=[sid]
        s+=" LIMIT ?";a+=[limit]; return [dict(x) for x in self.db.execute(s,a)]
    def stats(self):
        return {"objects":self.db.execute("SELECT count(*) FROM objects").fetchone()[0],"occurrences":self.db.execute("SELECT count(*) FROM occurrences").fetchone()[0],"relations":self.db.execute("SELECT count(*) FROM relations").fetchone()[0],"fts5":self.fts}

def module(root,rel,name):
    p=Path(root)/rel
    if not p.exists():raise FileNotFoundError(p)
    sys.path.insert(0,str(p.parent)); sp=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
def span(root,p): return module(root,"Hodge Span Lab/span.py","hc_span").analyze(p)
def bridge(root,p):
    module(root,"Hodge Span Lab/span.py","span"); m=module(root,"Hodge Span Lab/bridge.py","hc_bridge")
    if set(p)!={"source","map","hodge_template"}:raise ValueError("bridge requires source,map,hodge_template")
    return m.execute_bridge(p["source"],p["map"],p["hodge_template"])

def source_catalog(root):
    p=Path(root)/"Hodge Compass API/source_catalog.json"
    if not p.exists(): raise FileNotFoundError(p)
    return json.loads(p.read_text(encoding="utf-8"))

def source_search(root,p):
    cat=source_catalog(root); q=str(p.get("q","")).lower(); repo=p.get("repo"); role=p.get("role"); limit=int(p.get("limit",100))
    if not 1<=limit<=500: raise ValueError("limit 1..500")
    out=[]
    for x in cat.get("sources",[]):
        if q and q not in x.get("path","").lower(): continue
        if repo and repo!=x.get("repo"): continue
        if role and role!=x.get("role"): continue
        out.append(x)
        if len(out)>=limit: break
    return {"catalog_sha256":sha(cat),"generated_from":cat.get("generated_from"),"count":len(out),"results":out,"boundaries":cat.get("boundaries",[])}

class Handler(BaseHTTPRequestHandler):
    def sendj(self,n,x):
        b=json.dumps(x,sort_keys=True,ensure_ascii=False).encode(); self.send_response(n); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def body(self):
        n=int(self.headers.get("Content-Length",0));
        if n>4_000_000:raise ValueError("body too large")
        return json.loads(self.rfile.read(n) or b"{}")
    def do_GET(self):
        try:
            p=unquote(urlparse(self.path).path)
            if p=="/v1/health":return self.sendj(200,{"schema":SCHEMA,"status":"ok","stats":self.server.idx.stats(),"boundaries":BOUNDARIES})
            if p=="/v1/hodge/w114":return self.sendj(200,{**W114,"boundaries":BOUNDARIES})
            if p=="/v1/hodge/sources":return self.sendj(200,source_search(self.server.root,{"limit":500}))
            if p.startswith("/v1/objects/"):
                x=self.server.idx.get(p[len("/v1/objects/"):]);return self.sendj(200 if x else 404,x or {"error":"not found"})
            return self.sendj(404,{"error":"not found"})
        except Exception as e:return self.sendj(400,{"error":type(e).__name__,"message":str(e)})
    def do_POST(self):
        try:
            p=unquote(urlparse(self.path).path); b=self.body()
            if p=="/v1/records":
                rr=b if isinstance(b,list) else [b]
                if len(rr)>1000:raise ValueError("max 1000 records")
                return self.sendj(200,{"results":[self.server.idx.ingest(x) for x in rr]})
            if p=="/v1/search":return self.sendj(200,{"results":self.server.idx.search(b)})
            if p=="/v1/hodge/span":return self.sendj(200,span(self.server.root,b))
            if p=="/v1/hodge/bridge":return self.sendj(200,bridge(self.server.root,b))
            if p=="/v1/hodge/sources/search":return self.sendj(200,source_search(self.server.root,b))
            if p=="/v1/observer/remainder":return self.sendj(200,observe(b))
            return self.sendj(404,{"error":"not found"})
        except Exception as e:return self.sendj(400,{"error":type(e).__name__,"message":str(e)})
    def log_message(self,*a):
        if not self.server.quiet:super().log_message(*a)

def ingest_manifest(idx,p):
    x=json.loads(Path(p).read_text()); rr=x.get("records",x) if isinstance(x,dict) else x
    return {"count":len(rr),"results":[idx.ingest(r) for r in rr]}
def main():
    a=argparse.ArgumentParser();a.add_argument("--db",default=DB);a.add_argument("--repo-root",default=".");s=a.add_subparsers(dest="cmd",required=True)
    sv=s.add_parser("serve");sv.add_argument("--host",default=HOST);sv.add_argument("--port",type=int,default=PORT);sv.add_argument("--quiet",action="store_true")
    ig=s.add_parser("ingest");ig.add_argument("manifest");q=s.add_parser("search");q.add_argument("query");q.add_argument("--domain");q.add_argument("--surface");q.add_argument("--limit",type=int,default=20)
    s.add_parser("stats");s.add_parser("w114");src=s.add_parser("sources");src.add_argument("--query",default="");src.add_argument("--repo");src.add_argument("--role");src.add_argument("--limit",type=int,default=100);x=a.parse_args()
    if x.cmd=="serve":
        idx=Index(x.db);h=ThreadingHTTPServer((x.host,x.port),Handler);h.idx=idx;h.root=Path(x.repo_root);h.quiet=x.quiet;print(json.dumps({"url":f"http://{x.host}:{x.port}","schema":SCHEMA}));
        try:h.serve_forever()
        finally:idx.close()
        return
    idx=Index(x.db)
    try:
        if x.cmd=="ingest":o=ingest_manifest(idx,x.manifest)
        elif x.cmd=="search":o=idx.search({"q":x.query,"domain":x.domain,"surface":x.surface,"limit":x.limit})
        elif x.cmd=="stats":o=idx.stats()
        elif x.cmd=="sources":o=source_search(x.repo_root,{"q":x.query,"repo":x.repo,"role":x.role,"limit":x.limit})
        else:o={**W114,"boundaries":BOUNDARIES}
        print(json.dumps(o,indent=2,sort_keys=True))
    finally:idx.close()
if __name__=="__main__":main()
