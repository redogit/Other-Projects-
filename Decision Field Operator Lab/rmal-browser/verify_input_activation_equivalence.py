"""Differential evidence for pointer + keyboard activation."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import subprocess,sys

LAB=Path(__file__).resolve().parents[1]
if str(LAB) not in sys.path: sys.path.insert(0,str(LAB))
from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from tools.interact_independent_browser import initial_omega

PROGRAM=LAB/"examples"/"independent_browser_url.rmapl"
HITS=[
 {"x":4,"y":4,"width":24,"height":7,"href":"page2"},
 {"x":40,"y":4,"width":30,"height":7,"href":"https://example.com"},
]
FIXTURES={
 "pointer_second":{"kind":"pointer","px":45,"py":5,"key":"","hits":HITS,"pending":"KEEP","last":"OLD","focus":1,"focused":"OLD_FOCUS"},
 "pointer_miss":{"kind":"pointer","px":100,"py":50,"key":"","hits":HITS,"pending":"KEEP","last":"OLD","focus":1,"focused":"OLD_FOCUS"},
 "tab_first":{"kind":"keyboard","px":0,"py":0,"key":"TAB","hits":HITS,"pending":"KEEP","last":"OLD","focus":-1,"focused":"OLD_FOCUS"},
 "tab_wrap":{"kind":"keyboard","px":0,"py":0,"key":"TAB","hits":HITS,"pending":"KEEP","last":"OLD","focus":1,"focused":"https://example.com"},
 "tab_no_hits":{"kind":"keyboard","px":0,"py":0,"key":"TAB","hits":[],"pending":"KEEP","last":"OLD","focus":-1,"focused":"OLD_FOCUS"},
 "enter_valid":{"kind":"keyboard","px":0,"py":0,"key":"ENTER","hits":HITS,"pending":"KEEP","last":"OLD","focus":1,"focused":"https://example.com"},
 "enter_invalid":{"kind":"keyboard","px":0,"py":0,"key":"ENTER","hits":HITS,"pending":"KEEP","last":"OLD","focus":-1,"focused":"OLD_FOCUS"},
 "unsupported":{"kind":"keyboard","px":0,"py":0,"key":"ESC","hits":HITS,"pending":"KEEP","last":"OLD","focus":0,"focused":"page2"},
}

def pages():
 return [{"id":"page1","url":"rmapl://local/page1","source":"<p>ONE</p>"},{"id":"page2","url":"rmapl://local/page2","source":"<p>TWO</p>"}]

def omega_for(f):
 base=initial_omega(pages(),"page1"); c=deepcopy(base["construction"]); s=c["state"]
 s["hitMap"]=deepcopy(f["hits"]);s["navigation"]["pendingHref"]=f["pending"];s["navigation"]["focusIndex"]=f["focus"];s["navigation"]["focusedHref"]=f["focused"]
 s["input"]["pointer"]={"x":f["px"],"y":f["py"]};s["input"]["keyboard"]=f["key"];s["input"]["lastHit"]=f["last"]
 c["residuals"]=[{"kind":"pointer-activation-pending" if f["kind"]=="pointer" else "keyboard-activation-pending","detail":"oracle"}]
 return make_omega(**c)

def oracle(registry,f):
 op=registry["browser_pointer_activate" if f["kind"]=="pointer" else "browser_keyboard_activate"]
 p=op(omega_for(f)); o=p["omega"];s=o["state"];res=o["residuals"]
 return {
  "pending":s["navigation"]["pendingHref"].encode(),"last":s["input"]["lastHit"].encode(),"focus":s["navigation"]["focusIndex"],
  "focused":s["navigation"]["focusedHref"].encode(),"has_residual":bool(res),
  "residual":res[0]["kind"] if res else "none","detail":res[0]["detail"] if res else "none","consequence":p["consequenceKey"]
 }

def parse(line):
 d={}
 for t in line.split()[1:]:
  k,v=t.split("=",1);d[k]=v
 return d

def main():
 if len(sys.argv)!=3: raise SystemExit("usage: verify_input_activation_equivalence.py <host> <rmal>")
 cp=subprocess.run([sys.argv[1],sys.argv[2]],capture_output=True,text=True,check=True)
 rows={x["fixture"]:x for x in (parse(l) for l in cp.stdout.splitlines() if l.startswith("RMAL_INPUT "))}
 if set(rows)!=set(FIXTURES): raise AssertionError((sorted(rows),cp.stdout))
 p=parse_rmapl(PROGRAM.read_text(encoding="utf-8"));reg=native_registry(p)
 for name,f in FIXTURES.items():
  e=oracle(reg,f);a=rows[name]
  assert bytes.fromhex(a["pending_hex"])==e["pending"],(name,a,e)
  assert bytes.fromhex(a["last_hex"])==e["last"],(name,a,e)
  assert int(a["focus"])==e["focus"],(name,a,e)
  assert bytes.fromhex(a["focused_hex"])==e["focused"],(name,a,e)
  assert a["has_residual"]==("true" if e["has_residual"] else "false"),(name,a,e)
  assert a["residual"]==e["residual"],(name,a,e)
  assert a["detail"]==e["detail"],(name,a,e)
  assert a["consequence"]==e["consequence"],(name,a,e)
 receipt=f"RMAL_INPUT_RECEIPT fixtures={len(FIXTURES)} policy_in_rmal=true python_runtime_used=false"
 if receipt not in cp.stdout: raise AssertionError("input receipt missing")
 print("RMAPL_RMAL_INPUT_ACTIVATION_EQUIVALENCE PASS")
 print("HIT_MAP_ACCESS_CALLBACKS != INPUT_POLICY")
 return 0
if __name__=="__main__": raise SystemExit(main())
