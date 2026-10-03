"""Fail-closed lowering for browser_local_navigate."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from typing import Any
HERE=Path(__file__).resolve().parent; LAB=HERE.parent
if str(LAB) not in sys.path: sys.path.insert(0,str(LAB))
from rmapl import OperatorSpec,parse_rmapl

ALLOWED={"CLONE","GET","LEN","CONST","LABEL","LT","JUMP_IF_FALSE","INDEX","EQ","APPEND","SET","OMEGA_REBUILD","RETURN","ADD","JUMP"}
LABELS={"loop","next","missing"}
class I:
 def __init__(self,op,args): self.op=op; self.args=tuple(args)
 def __eq__(self,o): return isinstance(o,I) and self.op==o.op and self.args==o.args
 def __repr__(self): return f"I({self.op!r},{self.args!r})"

def ins(op):
 out=[]
 for line in op.instructions:
  name,sep,payload=line.partition(" ")
  if name not in ALLOWED: raise ValueError(f"unsupported local-navigation opcode {name!r}")
  if not sep: raise ValueError(f"{name} missing args")
  a=json.loads(payload)
  if not isinstance(a,list): raise ValueError("instruction args must be list")
  out.append(I(name,a))
 return tuple(out)

def require(xs,w):
 if w not in xs: raise ValueError(f"missing local-navigation instruction {w}")

def validate(source:str):
 p=parse_rmapl(source); m={o.operator_id:o for o in p.operators}; o=m["browser_local_navigate"]; xs=ins(o)
 got={x.args[0] for x in xs if x.op=="LABEL"}
 if got!=LABELS: raise ValueError(f"local-navigation labels changed: {sorted(got)}")
 for w in (
  I("GET",["target","$candidate","construction.state.navigation.pendingHref"]),
  I("GET",["pages","$candidate","construction.state.resources.pages"]),
  I("LEN",["n","$pages"]),I("INDEX",["page","$pages","$i"]),I("GET",["id","$page","id"]),
  I("EQ",["match","$id","$target"]),I("GET",["source","$page","source"]),
  I("GET",["current_url","$candidate","construction.state.navigation.currentUrl.canonical"]),
  I("APPEND",["$candidate","construction.state.navigation.history","$current_url"]),
  I("SET",["$candidate","construction.state.navigation.currentPage","$target"]),
  I("GET",["pending_url","$candidate","construction.state.navigation.pendingUrl"]),
  I("SET",["$candidate","construction.state.navigation.currentUrl","$pending_url"]),
  I("SET",["$candidate","construction.state.source","$source"]),
 ): require(xs,w)
 for path in (
  "construction.state.navigation.pendingHref","construction.state.navigation.pendingUrl",
  "construction.state.navigation.focusIndex","construction.state.navigation.focusedHref",
  "construction.state.html.tokens","construction.state.dom.nodes","construction.state.layout.boxes",
  "construction.state.hitMap","construction.state.camera.pixels","construction.state.camera.pgm",
  "construction.state.camera.verified","construction.state.camera.admitted",
  "construction.state.camera.blackPixels","construction.residuals"
 ):
  if not any(x.op=="SET" and len(x.args)==3 and x.args[0]=="$candidate" and x.args[1]==path for x in xs):
   raise ValueError(f"local-navigation reset surface changed: {path}")
 c={x.args[0]:x.args[1] for x in xs if x.op=="CONST" and len(x.args)==2}
 if c.get("next_residual")!=[{"kind":"html-tokenization-pending","detail":"local-navigation"}]: raise ValueError("success residual changed")
 if c.get("missing_residual")!=[{"kind":"navigation-target-missing","detail":"local-page-not-found"}]: raise ValueError("missing residual changed")
 if c.get("minus_one")!=-1 or c.get("empty")!=[] or c.get("false") is not False or c.get("zero")!=0: raise ValueError("reset constants changed")
 returns=[x for x in xs if x.op=="RETURN"]
 if I("RETURN",["$candidate","local-navigation"]) not in returns or I("RETURN",["$candidate","navigation-target-missing"]) not in returns: raise ValueError("navigation consequences changed")
 return c["next_residual"][0],c["missing_residual"][0]

def q(s): return json.dumps(s)
def render(module,success,missing,fixtures):
 L=[
  "# GENERATED FILE — DO NOT EDIT BY HAND","# Lowered from browser_local_navigate","# Lowering family: rmapl-rmal-local-navigation-lowering/v1","",
  f"MODULE {module};","",
  'CONTEXT RMAPL_LOCAL_NAV_PORT status="GENERATED" authority="LOCAL" evidence_transfer="DENY"',
  'BOUNDARY RMAPL_LOCAL_NAV_PORT CLAIM_CEILING BOUNDED_GENERATED_PORT REASON "RMAL owns local navigation policy; native callbacks expose resource fields only"',"",
  "fn navigate_local() {",
  "    let target = BrowserNavTarget();","    let n = BrowserPageCount();","    let current_url = BrowserCurrentUrlCanonical();",
  "    let i = 0;",'    let page_id = "";','    let source = "";',
  "    while i < n {","        SET page_id = BrowserPageId(i);","        if page_id == target {","            SET source = BrowserPageSource(i);",
  f'            let ack = BrowserLocalNavResult(true, target, source, current_url, true, true, true, true, {q(success["kind"])}, {q(success["detail"])}, "local-navigation");',
  '            REQUIRE ack == "local-navigation:ACK";',"            return \"local-navigation\";","        }","        SET i = i + 1;","    }",
  f'    let miss = BrowserLocalNavResult(false, target, "", current_url, false, false, false, false, {q(missing["kind"])}, {q(missing["detail"])}, "navigation-target-missing");',
  '    REQUIRE miss == "navigation-target-missing:ACK";','    return "navigation-target-missing";',"}",""
 ]
 exp={"navigate_first":"local-navigation","navigate_third":"local-navigation","missing":"navigation-target-missing"}
 for f in fixtures:
  L.append(f"REQUIRE BrowserLocalNavSelect({q(f)}) == {q(f+':ACK')};");L.append(f"REQUIRE navigate_local() == {q(exp[f])};")
 L+=["",'print "RMAL_LOCAL_NAVIGATION_PASS";',"STOP;",""]; return "\n".join(L)

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--profile",type=Path,required=True);g=ap.add_mutually_exclusive_group(required=True);g.add_argument("--check",action="store_true");g.add_argument("--write",action="store_true");a=ap.parse_args()
 p=json.loads(a.profile.read_text()); 
 if p.get("schema")!="rmapl-rmal-local-navigation-lowering/v1": raise ValueError("bad local navigation schema")
 src=(a.profile.parent/p["source"]).resolve().read_text();success,missing=validate(src);out=(a.profile.parent/p["output"]).resolve();text=render(p["module"],success,missing,p["fixtures"])
 if a.write: out.write_text(text);print(f"WROTE {out}");return 0
 if out.read_text()!=text: print("LOWERING DRIFT: local navigation RMAL mismatch.",file=sys.stderr);return 1
 print("RMAPL_RMAL_LOCAL_NAVIGATION_LOWERING_CHECK PASS");return 0
if __name__=="__main__": raise SystemExit(main())
