"""Fail-closed lowering for browser_http_response_admit.

The generated RMAL owns HTTP admission policy. Native callbacks expose only
mechanical byte access required because RMAL 3.1 has no byte-buffer value kind.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from rmapl import OperatorSpec, parse_rmapl


ALLOWED = {
    "CLONE","GET","LEN","GE","JUMP_IF_FALSE","BUF_GET","EQ","AND","CONST",
    "SUB","LABEL","LT","ADD","GT","BUF_NEW","BUF_SET","TEXT_UTF8","APPEND",
    "SET","OMEGA_REBUILD","RETURN","JUMP"
}

REQUIRED_LABELS = {"scan_headers","copy_body","body_done","scan_next","invalid"}

REQUIRED_RESET_PATHS = {
    "construction.state.navigation.currentUrl",
    "construction.state.navigation.pendingUrl",
    "construction.state.navigation.pendingHref",
    "construction.state.navigation.currentPage",
    "construction.state.source",
    "construction.state.network.response.status",
    "construction.state.network.response.bodyBytes",
    "construction.state.html.tokens",
    "construction.state.dom.nodes",
    "construction.state.layout.boxes",
    "construction.state.hitMap",
    "construction.state.camera.pixels",
    "construction.state.camera.pgm",
    "construction.state.camera.verified",
    "construction.state.camera.admitted",
    "construction.state.camera.blackPixels",
    "construction.residuals",
}

STATUS_PREFIX = b"HTTP/1.1 200 "


@dataclass(frozen=True)
class Instruction:
    opcode: str
    args: tuple[Any, ...]


@dataclass(frozen=True)
class ResponsePlan:
    min_length: int
    scan_start: int
    status: int
    admitted_kind: str
    admitted_detail: str
    admitted_consequence: str
    invalid_kind: str
    invalid_detail: str
    invalid_consequence: str


def parse_instruction(line: str) -> Instruction:
    opcode, sep, payload = line.partition(" ")
    if opcode not in ALLOWED:
        raise ValueError(f"unsupported response-lowering opcode {opcode!r}")
    if not sep:
        raise ValueError(f"{opcode} requires JSON arguments")
    args = json.loads(payload)
    if not isinstance(args, list):
        raise ValueError(f"{opcode} arguments must be a JSON array")
    return Instruction(opcode, tuple(args))


def find_operator(source: str, operator_id: str) -> OperatorSpec:
    program = parse_rmapl(source)
    matches = [op for op in program.operators if op.operator_id == operator_id]
    if len(matches) != 1:
        raise ValueError(f"expected one {operator_id!r}, got {len(matches)}")
    return matches[0]


def labels(instructions: tuple[Instruction, ...]) -> set[str]:
    result=set()
    for ins in instructions:
        if ins.opcode=="LABEL":
            if len(ins.args)!=1 or not isinstance(ins.args[0],str):
                raise ValueError("LABEL must contain one string")
            result.add(ins.args[0])
    return result


def consts(instructions: tuple[Instruction, ...]) -> dict[str, Any]:
    out={}
    for ins in instructions:
        if ins.opcode=="CONST":
            if len(ins.args)!=2 or not isinstance(ins.args[0],str):
                raise ValueError("CONST must be [name,value]")
            out[ins.args[0]]=ins.args[1]
    return out


def require_instruction(instructions: tuple[Instruction,...], wanted: Instruction) -> None:
    if wanted not in instructions:
        raise ValueError(f"missing required instruction {wanted}")


def lower(operator: OperatorSpec) -> ResponsePlan:
    ins=tuple(parse_instruction(line) for line in operator.instructions)
    if labels(ins) != REQUIRED_LABELS:
        raise ValueError(f"response labels changed: {sorted(labels(ins))}")

    require_instruction(ins, Instruction("GET",("response","$candidate","construction.state.network.responseBytes")))
    require_instruction(ins, Instruction("LEN",("n","$response")))
    require_instruction(ins, Instruction("GE",("enough","$n",17)))
    require_instruction(ins, Instruction("CONST",("i",13)))
    require_instruction(ins, Instruction("SUB",("scan_limit","$n",3)))
    require_instruction(ins, Instruction("ADD",("body_start","$i",4)))
    require_instruction(ins, Instruction("SUB",("body_len","$n","$body_start")))
    require_instruction(ins, Instruction("GT",("body_ok","$body_len",0)))
    require_instruction(ins, Instruction("TEXT_UTF8",("html","$body")))

    # Verify literal status prefix byte checks in order.
    pairs=[]
    for insn in ins:
        if insn.opcode=="BUF_GET" and len(insn.args)==3 and insn.args[1]=="$response":
            dst,index=insn.args[0],insn.args[2]
            if isinstance(index,int) and 0 <= index < len(STATUS_PREFIX):
                pairs.append((dst,index))
    for index,expected in enumerate(STATUS_PREFIX):
        dst=f"s{index}"
        require_instruction(ins, Instruction("BUF_GET",("b","$response",index)) if index in {0,1,2,3,4,5,6,7,8,9,10,11,12} else Instruction("",()))
        require_instruction(ins, Instruction("EQ",(dst,"$b",expected)))

    # Verify CRLFCRLF scan.
    for dst,source,offset,value in (
        ("cr0","$b0",0,13),
        ("lf0","$b1",1,10),
        ("cr1","$b2",2,13),
        ("lf1","$b3",3,10),
    ):
        require_instruction(ins, Instruction("EQ",(dst,source,value)))

    written_paths={
        i.args[1] for i in ins
        if i.opcode=="SET" and len(i.args)==3 and i.args[0]=="$candidate" and isinstance(i.args[1],str)
    }
    missing=REQUIRED_RESET_PATHS-written_paths
    if missing:
        raise ValueError(f"response state-reset surface changed: missing {sorted(missing)}")

    c=consts(ins)
    admitted=c.get("next_residual")
    invalid=c.get("invalid_residual")
    if admitted != [{"kind":"html-tokenization-pending","detail":"http-response-admitted"}]:
        raise ValueError("admitted residual changed")
    if invalid != [{"kind":"http-response-invalid","detail":"requires-http11-200-header-delimiter-utf8-body"}]:
        raise ValueError("invalid residual changed")
    if c.get("status") != 200:
        raise ValueError("admitted status changed")

    returns=[i for i in ins if i.opcode=="RETURN"]
    if len(returns)!=2:
        raise ValueError("expected exactly two RETURN instructions")
    if returns[0] != Instruction("RETURN",("$candidate","http-response-admitted")):
        raise ValueError("admitted consequence changed")
    if returns[1] != Instruction("RETURN",("$candidate","http-response-invalid")):
        raise ValueError("invalid consequence changed")

    return ResponsePlan(
        min_length=17,
        scan_start=13,
        status=200,
        admitted_kind=admitted[0]["kind"],
        admitted_detail=admitted[0]["detail"],
        admitted_consequence="http-response-admitted",
        invalid_kind=invalid[0]["kind"],
        invalid_detail=invalid[0]["detail"],
        invalid_consequence="http-response-invalid",
    )


def q(text: str) -> str:
    return json.dumps(text)


def render(plan: ResponsePlan, profile: dict[str,Any]) -> str:
    module=profile["module"]
    fixtures=profile["fixtures"]
    prefix_checks=[]
    for i,b in enumerate(STATUS_PREFIX):
        prefix_checks.append(
            f"    if BrowserResponseByte({i}) != {b} {{ return invalid_result(); }}"
        )

    lines=[
        "# GENERATED FILE — DO NOT EDIT BY HAND",
        "# Lowered from examples/independent_browser_http.rmapl::browser_http_response_admit",
        "# Lowering family: rmapl-rmal-http-response-lowering/v1",
        "",
        f"MODULE {module};",
        "",
        'CONTEXT RMAPL_HTTP_RESPONSE_PORT status="GENERATED" authority="LOCAL" evidence_transfer="DENY"',
        'BOUNDARY RMAPL_HTTP_RESPONSE_PORT CLAIM_CEILING BOUNDED_GENERATED_PORT REASON "RMAL owns admission policy; native callbacks expose byte mechanics only"',
        "",
        "fn invalid_result() {",
        f"    let ack = BrowserResponseResult(false, 0, \"\", {q(plan.invalid_kind)}, {q(plan.invalid_detail)}, {q(plan.invalid_consequence)});",
        f"    REQUIRE ack == {q(plan.invalid_consequence + ':ACK')};",
        f"    return {q(plan.invalid_consequence)};",
        "}",
        "",
        "fn admit_response() {",
        "    let n = BrowserResponseLength();",
        f"    if n < {plan.min_length} {{ return invalid_result(); }}",
    ]
    lines.extend(prefix_checks)
    lines.extend([
        f"    let i = {plan.scan_start};",
        "    while i < n - 3 {",
        "        if BrowserResponseByte(i) == 13 && BrowserResponseByte(i + 1) == 10 && BrowserResponseByte(i + 2) == 13 && BrowserResponseByte(i + 3) == 10 {",
        "            let body_start = i + 4;",
        "            let body_len = n - body_start;",
        "            if body_len <= 0 { return invalid_result(); }",
        "            let html = BrowserResponseUtf8(body_start, body_len);",
        "            if html == \"\" { return invalid_result(); }",
        f"            let ack = BrowserResponseResult(true, {plan.status}, html, {q(plan.admitted_kind)}, {q(plan.admitted_detail)}, {q(plan.admitted_consequence)});",
        f"            REQUIRE ack == {q(plan.admitted_consequence + ':ACK')};",
        f"            return {q(plan.admitted_consequence)};",
        "        }",
        "        SET i = i + 1;",
        "    }",
        "    return invalid_result();",
        "}",
        "",
    ])
    expected={
        "valid":plan.admitted_consequence,
        "not_found":plan.invalid_consequence,
        "missing_delimiter":plan.invalid_consequence,
        "empty_body":plan.invalid_consequence,
    }
    for fixture in fixtures:
        lines.append(f"REQUIRE BrowserResponseSelect({q(fixture)}) == {q(fixture + ':ACK')};")
        lines.append(f"REQUIRE admit_response() == {q(expected[fixture])};")
    lines.extend([
        "",
        'print "RMAL_HTTP_RESPONSE_PASS";',
        "STOP;",
        "",
    ])
    return "\n".join(lines)


def load_profile(path: Path) -> dict[str,Any]:
    profile=json.loads(path.read_text(encoding="utf-8"))
    if profile.get("schema")!="rmapl-rmal-http-response-lowering/v1":
        raise ValueError("unsupported response lowering schema")
    return profile


def generated(profile_path: Path) -> tuple[Path,str]:
    profile=load_profile(profile_path)
    source=(profile_path.parent/profile["source"]).resolve()
    output=(profile_path.parent/profile["output"]).resolve()
    operator=find_operator(source.read_text(encoding="utf-8"),profile["operator"])
    return output,render(lower(operator),profile)


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--profile",type=Path,required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--write",action="store_true")
    args=parser.parse_args()
    output,expected=generated(args.profile.resolve())
    if args.write:
        output.write_text(expected,encoding="utf-8")
        print(f"WROTE {output}")
        return 0
    actual=output.read_text(encoding="utf-8")
    if actual!=expected:
        print("LOWERING DRIFT: HTTP response RMAL does not match RMAPL source.",file=sys.stderr)
        return 1
    print("RMAPL_RMAL_HTTP_RESPONSE_LOWERING_CHECK PASS")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
