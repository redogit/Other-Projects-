#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shlex
from pathlib import Path

SCHEMA="rmaos/minigx-ir/v1"
SUPPORTED_FAMILIES={"STATE","FIELD","OBSERVER","CONTROL","GEOMETRY","POINT","RELATION","SIGNAL","FEEDBACK","POST","TRACE","GAME"}
SUPPORTED_RELATIONS={"FEEDS","MODULATES","FEEDBACK_TO"}
SUPPORTED_OPS={
"W114_CENTER","W114_FIELD","OBSERVER_CHANNELS","TRANSFORM_SET","FRACTAL_BRANCHES","GPU_POINTS",
"COGNATE_LINKS","PULSE_OSCILLATOR","FRAME_FEEDBACK","BLOOM_TONEMAP","TRACE_TAP","RECENTER","ROBUST_SCORE"
}

def fields(tokens,start):
    if (len(tokens)-start)%2: raise ValueError("key/value fields must be paired")
    out={}
    for i in range(start,len(tokens),2):
        key=tokens[i]
        if key in out: raise ValueError(f"duplicate field {key}")
        out[key]=tokens[i+1]
    return out

def parse_params(text):
    out={}
    if not text:return out
    for piece in text.split(";"):
        if not piece:continue
        if "=" not in piece:raise ValueError(f"bad PARAMS piece: {piece}")
        k,v=piece.split("=",1)
        if not k:raise ValueError("empty PARAMS key")
        if k in out:raise ValueError(f"duplicate PARAMS key {k}")
        out[k]=v
    return out

def parse(path:Path):
    raw_bytes=path.read_bytes()
    module=surface=target=None;nodes={};edges=[];edge_keys=set();claims=[];claim_ids=set()
    def set_once(name,current,value):
        if current is not None: raise ValueError(f"duplicate {name}")
        return value
    for lineno,raw in enumerate(raw_bytes.decode("utf-8").splitlines(),1):
        line=raw.strip()
        if not line or line.startswith("#"):continue
        tok=shlex.split(line,comments=True,posix=True)
        if not tok:continue
        try:
            if tok[0]=="MODULE":
                if len(tok)!=2: raise ValueError("MODULE requires exactly one value")
                module=set_once("MODULE",module,tok[1])
            elif tok[0]=="SURFACE":
                if len(tok)!=2: raise ValueError("SURFACE requires exactly one value")
                surface=set_once("SURFACE",surface,tok[1])
            elif tok[0]=="TARGET":
                if len(tok)!=2: raise ValueError("TARGET requires exactly one value")
                target=set_once("TARGET",target,tok[1])
            elif tok[0]=="ENTITY":
                if len(tok)<4: raise ValueError("malformed ENTITY")
                ident=tok[1];f=fields(tok,2)
                if f.get("KIND")!="MINIGX_NODE":continue
                family=f.get("FAMILY","");op=f.get("OP","")
                if family not in SUPPORTED_FAMILIES:raise ValueError(f"unsupported FAMILY {family}")
                if op not in SUPPORTED_OPS:raise ValueError(f"unsupported OP {op}")
                if ident in nodes:raise ValueError(f"duplicate node {ident}")
                try: stage=int(f.get("STAGE","0"))
                except ValueError as exc: raise ValueError("STAGE must be an integer") from exc
                if stage<0:raise ValueError("STAGE must be >= 0")
                nodes[ident]={"id":ident,"family":family,"op":op,"stage":stage,"params":parse_params(f.get("PARAMS",""))}
            elif tok[0]=="RELATE":
                if len(tok)<6 or tok[2]!="AS" or tok[4]!="TO":raise ValueError("malformed RELATE")
                src,rel,dst=tok[1],tok[3],tok[5];f=fields(tok,6) if len(tok)>6 else {}
                if rel not in SUPPORTED_RELATIONS:raise ValueError(f"unsupported relation {rel}")
                edge={"src":src,"relation":rel,"dst":dst,"port":f.get("PORT","")}
                key=(edge["src"],edge["relation"],edge["dst"],edge["port"])
                if key in edge_keys:raise ValueError(f"duplicate edge {key}")
                edge_keys.add(key);edges.append(edge)
            elif tok[0]=="CLAIM":
                if len(tok)<4:raise ValueError("malformed CLAIM")
                ident=tok[1];f=fields(tok,2)
                if ident in claim_ids:raise ValueError(f"duplicate claim {ident}")
                claim_ids.add(ident);claims.append({"id":ident,"kind":f.get("KIND",""),"status":f.get("STATUS",""),"text":f.get("TEXT","")})
            else:raise ValueError(f"unsupported form {tok[0]}")
        except Exception as e:raise ValueError(f"{path}:{lineno}: {e}") from e
    if not module or surface!="minigx" or target!="android.opengl_es_3_1":
        raise ValueError("MODULE/SURFACE minigx/TARGET android.opengl_es_3_1 required")
    if not nodes:raise ValueError("no MiniGX nodes")
    for e in edges:
        if e["src"] not in nodes or e["dst"] not in nodes:raise ValueError(f"edge endpoint missing: {e}")
        if e["relation"]=="FEEDBACK_TO" and nodes[e["src"]]["family"]!="FEEDBACK":
            raise ValueError(f"FEEDBACK_TO source must have FAMILY FEEDBACK: {e['src']}")
    provenance={"source_file":path.name,"source_sha256":"sha256:"+hashlib.sha256(raw_bytes).hexdigest()}
    return module,target,nodes,edges,claims,provenance

def topo(nodes,edges):
    indeg={n:0 for n in nodes};adj={n:[] for n in nodes}
    for e in edges:
        if e["relation"]=="FEEDBACK_TO":continue
        indeg[e["dst"]]+=1;adj[e["src"]].append(e["dst"])
    ready=sorted((nodes[n]["stage"],n) for n,d in indeg.items() if d==0);order=[]
    while ready:
        _,n=ready.pop(0);order.append(n)
        for m in sorted(adj[n]):
            indeg[m]-=1
            if indeg[m]==0:ready.append((nodes[m]["stage"],m));ready.sort()
    if len(order)!=len(nodes):raise ValueError(f"non-feedback cycle: {sorted(n for n,d in indeg.items() if d)}")
    return order

def canonical_ir(path):
    path=Path(path);module,target,nodes,edges,claims,provenance=parse(path);order=topo(nodes,edges)
    semantic={"schema":SCHEMA,"module":module,"target":target,
      "nodes":[nodes[k] for k in sorted(nodes)],
      "edges":sorted(edges,key=lambda e:(e["src"],e["relation"],e["dst"],e["port"])),
      "execution_order":order,"claims":sorted(claims,key=lambda c:c["id"]),
      "boundaries":{"surface_semantics":"SURFACE != SEMANTICS","compile_truth":"COMPILED != TRUE",
        "generate_verify_admit":"GENERATE != VERIFY != ADMIT","software_proof":"SOFTWARE_VERIFICATION != MATHEMATICAL_PROOF"}}
    blob=json.dumps(semantic,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return {**semantic,"digest":"sha256:"+hashlib.sha256(blob).hexdigest(),"provenance":provenance}

def java_source(ir):
    def q(s):return json.dumps(str(s))
    order=", ".join(q(x) for x in ir["execution_order"])
    return f'''package org.rmaos.mingx.generated;

public final class MiniGXGraph {{
    public static final String SCHEMA = {q(ir["schema"])};
    public static final String MODULE = {q(ir["module"])};
    public static final String DIGEST = {q(ir["digest"])};
    public static final int NODE_COUNT = {len(ir["nodes"])};
    public static final int EDGE_COUNT = {len(ir["edges"])};
    public static final String[] EXECUTION_ORDER = new String[]{{{order}}};
    private MiniGXGraph() {{}}
}}
'''

def main():
    ap=argparse.ArgumentParser();ap.add_argument("source");ap.add_argument("--out",required=True);ap.add_argument("--java");ap.add_argument("--check",action="store_true");ns=ap.parse_args()
    ir=canonical_ir(Path(ns.source));encoded=json.dumps(ir,indent=2,sort_keys=True,ensure_ascii=False)+"\n";out=Path(ns.out)
    if ns.check:
        if not out.exists() or out.read_text(encoding="utf-8")!=encoded:print("MINIGX_IR_MISMATCH");return 2
        if ns.java:
            jp=Path(ns.java)
            if not jp.exists() or jp.read_text(encoding="utf-8")!=java_source(ir):print("MINIGX_JAVA_MISMATCH");return 3
        print("MINIGX_GENERATED_MATCH");return 0
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(encoded,encoding="utf-8")
    if ns.java:
        jp=Path(ns.java);jp.parent.mkdir(parents=True,exist_ok=True);jp.write_text(java_source(ir),encoding="utf-8")
    print(ir["digest"]);return 0

if __name__=="__main__":raise SystemExit(main())
