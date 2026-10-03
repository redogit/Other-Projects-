"""Fail-closed lowering for pointer + keyboard link activation."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any

HERE=Path(__file__).resolve().parent
LAB=HERE.parent
if str(LAB) not in sys.path: sys.path.insert(0,str(LAB))
from rmapl import OperatorSpec, parse_rmapl

ALLOWED={
 "CLONE","GET","LEN","CONST","LABEL","LT","JUMP_IF_FALSE","INDEX","GE","ADD",
 "AND","SET","OMEGA_REBUILD","RETURN","JUMP","EQ","GT","MOD"
}
PTR_LABELS={"loop","next","miss"}
KEY_LABELS={"check_enter","no_target","unsupported"}

class I:
    __slots__=("op","args")
    def __init__(self,op,args): self.op=op; self.args=tuple(args)
    def __eq__(self,o): return isinstance(o,I) and self.op==o.op and self.args==o.args
    def __repr__(self): return f"I({self.op!r},{self.args!r})"

def instructions(op:OperatorSpec)->tuple[I,...]:
    out=[]
    for line in op.instructions:
        name,sep,payload=line.partition(" ")
        if name not in ALLOWED: raise ValueError(f"unsupported input-lowering opcode {name!r}")
        if not sep: raise ValueError(f"{name} missing JSON arguments")
        args=json.loads(payload)
        if not isinstance(args,list): raise ValueError(f"{name} args must be list")
        out.append(I(name,args))
    return tuple(out)

def opmap(source:str)->dict[str,OperatorSpec]:
    p=parse_rmapl(source)
    return {o.operator_id:o for o in p.operators}

def labels(ins:tuple[I,...])->set[str]:
    return {x.args[0] for x in ins if x.op=="LABEL"}

def require(ins:tuple[I,...],wanted:I)->None:
    if wanted not in ins: raise ValueError(f"missing required instruction {wanted}")

def consts(ins:tuple[I,...])->dict[str,Any]:
    return {x.args[0]:x.args[1] for x in ins if x.op=="CONST" and len(x.args)==2}

def validate_pointer(op:OperatorSpec)->dict[str,Any]:
    ins=instructions(op)
    if labels(ins)!=PTR_LABELS: raise ValueError(f"pointer labels changed: {sorted(labels(ins))}")
    for wanted in (
        I("GET",["px","$candidate","construction.state.input.pointer.x"]),
        I("GET",["py","$candidate","construction.state.input.pointer.y"]),
        I("GET",["hits","$candidate","construction.state.hitMap"]),
        I("LEN",["n","$hits"]),
        I("GE",["x_ge","$px","$x"]),
        I("ADD",["x2","$x","$w"]),
        I("LT",["x_lt","$px","$x2"]),
        I("GE",["y_ge","$py","$y"]),
        I("ADD",["y2","$y","$h"]),
        I("LT",["y_lt","$py","$y2"]),
        I("AND",["inside","$in_x","$in_y"]),
        I("SET",["$candidate","construction.state.navigation.pendingHref","$href"]),
        I("SET",["$candidate","construction.state.input.lastHit","$href"]),
        I("SET",["$candidate","construction.state.input.lastHit","$empty_text"]),
    ): require(ins,wanted)
    c=consts(ins)
    if c.get("next_residual")!=[{"kind":"url-resolution-pending","detail":"pointer-hit"}]:
        raise ValueError("pointer hit residual changed")
    if c.get("miss_residual")!=[{"kind":"pointer-no-target","detail":"no-hit"}]:
        raise ValueError("pointer miss residual changed")
    returns=[x for x in ins if x.op=="RETURN"]
    if I("RETURN",["$candidate","pointer-hit"]) not in returns or I("RETURN",["$candidate","pointer-no-target"]) not in returns:
        raise ValueError("pointer consequences changed")
    return {"hit":c["next_residual"][0],"miss":c["miss_residual"][0]}

def validate_keyboard(op:OperatorSpec)->dict[str,Any]:
    ins=instructions(op)
    if labels(ins)!=KEY_LABELS: raise ValueError(f"keyboard labels changed: {sorted(labels(ins))}")
    for wanted in (
        I("GET",["key","$candidate","construction.state.input.keyboard"]),
        I("GET",["hits","$candidate","construction.state.hitMap"]),
        I("EQ",["is_tab","$key","TAB"]),
        I("EQ",["is_enter","$key","ENTER"]),
        I("MOD",["focus","$focus","$n"]),
        I("SET",["$candidate","construction.state.navigation.focusIndex","$focus"]),
        I("SET",["$candidate","construction.state.navigation.focusedHref","$href"]),
        I("SET",["$candidate","construction.state.navigation.pendingHref","$href"]),
        I("SET",["$candidate","construction.state.navigation.focusIndex","$minus_one"]),
        I("SET",["$candidate","construction.state.navigation.focusedHref","$empty_text"]),
    ): require(ins,wanted)
    c=consts(ins)
    if c.get("next_residual")!=[{"kind":"url-resolution-pending","detail":"keyboard-enter"}]:
        raise ValueError("keyboard enter residual changed")
    if c.get("no_target_residual")!=[{"kind":"keyboard-no-target","detail":"no-focused-link"}]:
        raise ValueError("keyboard no-target residual changed")
    if c.get("unsupported_residual")!=[{"kind":"keyboard-unsupported","detail":"unsupported-key"}]:
        raise ValueError("keyboard unsupported residual changed")
    if c.get("empty")!=[]: raise ValueError("keyboard TAB residual-clear contract changed")
    returns=[x for x in ins if x.op=="RETURN"]
    for consequence in ("keyboard-focus","keyboard-enter","keyboard-no-target","keyboard-unsupported"):
        if I("RETURN",["$candidate",consequence]) not in returns:
            raise ValueError(f"keyboard consequence {consequence!r} changed")
    return {
      "enter":c["next_residual"][0],
      "no_target":c["no_target_residual"][0],
      "unsupported":c["unsupported_residual"][0]
    }

def q(s:str)->str: return json.dumps(s)

def render(module:str,p:dict[str,Any],k:dict[str,Any],fixtures:list[str])->str:
    L=[
      "# GENERATED FILE — DO NOT EDIT BY HAND",
      "# Lowered from browser_pointer_activate + browser_keyboard_activate",
      "# Lowering family: rmapl-rmal-input-activation-lowering/v1","",
      f"MODULE {module};","",
      'CONTEXT RMAPL_INPUT_PORT status="GENERATED" authority="LOCAL" evidence_transfer="DENY"',
      'BOUNDARY RMAPL_INPUT_PORT CLAIM_CEILING BOUNDED_GENERATED_PORT REASON "RMAL owns input policy; native callbacks expose hit-map/input fields only"',"",
      "fn emit_result(pending, last_hit, focus, focused, has_residual, residual, detail, consequence) {",
      "    let ack = BrowserInputResult(pending, last_hit, focus, focused, has_residual, residual, detail, consequence);",
      '    REQUIRE ack == consequence + ":ACK";',
      "    return consequence;",
      "}","",
      "fn pointer_activate() {",
      "    let px = BrowserPointerX();",
      "    let py = BrowserPointerY();",
      "    let n = BrowserHitCount();",
      "    let pending = BrowserInitialPendingHref();",
      "    let focus = BrowserInitialFocusIndex();",
      "    let focused = BrowserInitialFocusedHref();",
      "    let i = 0;",
      "    let x = 0;",
      "    let y = 0;",
      "    let w = 0;",
      "    let h = 0;",
      '    let href = "";',
      "    while i < n {",
      "        SET x = BrowserHitX(i);",
      "        SET y = BrowserHitY(i);",
      "        SET w = BrowserHitWidth(i);",
      "        SET h = BrowserHitHeight(i);",
      "        if px >= x && px < x + w && py >= y && py < y + h {",
      "            SET href = BrowserHitHref(i);",
      f'            return emit_result(href, href, focus, focused, true, {q(p["hit"]["kind"])}, {q(p["hit"]["detail"])}, "pointer-hit");',
      "        }",
      "        SET i = i + 1;",
      "    }",
      f'    return emit_result(pending, "", focus, focused, true, {q(p["miss"]["kind"])}, {q(p["miss"]["detail"])}, "pointer-no-target");',
      "}","",
      "fn keyboard_activate() {",
      "    let key = BrowserKey();",
      "    let n = BrowserHitCount();",
      "    let pending = BrowserInitialPendingHref();",
      "    let last_hit = BrowserInitialLastHit();",
      "    let focus = BrowserInitialFocusIndex();",
      "    let focused = BrowserInitialFocusedHref();",
      '    let href = "";',
      '    if key == "TAB" {',
      f'        if n <= 0 {{ return emit_result(pending, last_hit, focus, focused, true, {q(k["no_target"]["kind"])}, {q(k["no_target"]["detail"])}, "keyboard-no-target"); }}',
      "        SET focus = (focus + 1) % n;",
      "        SET href = BrowserHitHref(focus);",
      '        return emit_result(pending, href, focus, href, false, "", "", "keyboard-focus");',
      "    }",
      '    if key == "ENTER" {',
      "        if focus >= 0 && focus < n {",
      "            SET href = BrowserHitHref(focus);",
      f'            return emit_result(href, href, -1, "", true, {q(k["enter"]["kind"])}, {q(k["enter"]["detail"])}, "keyboard-enter");',
      "        }",
      f'        return emit_result(pending, last_hit, focus, focused, true, {q(k["no_target"]["kind"])}, {q(k["no_target"]["detail"])}, "keyboard-no-target");',
      "    }",
      f'    return emit_result(pending, last_hit, focus, focused, true, {q(k["unsupported"]["kind"])}, {q(k["unsupported"]["detail"])}, "keyboard-unsupported");',
      "}",""
    ]
    expected={
      "pointer_second":"pointer-hit","pointer_miss":"pointer-no-target",
      "tab_first":"keyboard-focus","tab_wrap":"keyboard-focus","tab_no_hits":"keyboard-no-target",
      "enter_valid":"keyboard-enter","enter_invalid":"keyboard-no-target","unsupported":"keyboard-unsupported"
    }
    kind={name:("pointer" if name.startswith("pointer_") else "keyboard") for name in fixtures}
    for name in fixtures:
        L.append(f"REQUIRE BrowserInputSelect({q(name)}) == {q(name+':ACK')};")
        L.append(f"REQUIRE {kind[name]}_activate() == {q(expected[name])};")
    L+=["",'print "RMAL_INPUT_ACTIVATION_PASS";',"STOP;",""]
    return "\n".join(L)

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--profile",type=Path,required=True)
    m=ap.add_mutually_exclusive_group(required=True);m.add_argument("--check",action="store_true");m.add_argument("--write",action="store_true")
    args=ap.parse_args(); profile=json.loads(args.profile.read_text(encoding="utf-8"))
    if profile.get("schema")!="rmapl-rmal-input-activation-lowering/v1": raise ValueError("bad input lowering schema")
    source=(args.profile.parent/profile["source"]).resolve().read_text(encoding="utf-8")
    ops=opmap(source)
    p=validate_pointer(ops["browser_pointer_activate"]); k=validate_keyboard(ops["browser_keyboard_activate"])
    text=render(profile["module"],p,k,profile["fixtures"])
    out=(args.profile.parent/profile["output"]).resolve()
    if args.write: out.write_text(text,encoding="utf-8"); print(f"WROTE {out}"); return 0
    if out.read_text(encoding="utf-8")!=text:
        print("LOWERING DRIFT: input RMAL does not match RMAPL source.",file=sys.stderr);return 1
    print("RMAPL_RMAL_INPUT_ACTIVATION_LOWERING_CHECK PASS");return 0
if __name__=="__main__": raise SystemExit(main())
