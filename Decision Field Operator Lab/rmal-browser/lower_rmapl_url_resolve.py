"""Fail-closed lowering for browser_url_resolve.

The current RMAPL URL resolver is intentionally bounded; this lowerer admits
only that exact policy family and emits RMAL control flow using mechanical
byte/character callbacks because RMAL 3.1 has no byte-buffer value kind.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any

HERE=Path(__file__).resolve().parent
LAB=HERE.parent
if str(LAB) not in sys.path:
    sys.path.insert(0,str(LAB))

from rmapl import OperatorSpec, parse_rmapl

ALLOWED={
    "CLONE","GET","LEN","GT","JUMP_IF_FALSE","BYTES_UTF8","CONST","SET","GE",
    "BUF_GET","EQ","AND","JUMP","LABEL","LT","OR","BUF_NEW","BUF_SET",
    "TEXT_UTF8","CONCAT","ADD","OMEGA_REBUILD","RETURN"
}

REQUIRED_LABELS={
    "local_abs_loop","local_abs_done","local_abs_char","check_https","check_http",
    "network_authority","host_loop","host_done_no_path","host_done_with_path",
    "host_char","host_append","path_loop","path_append","network_finish","relative",
    "relative_loop","relative_done","relative_char","local_commit","invalid"
}

@dataclass(frozen=True)
class Instruction:
    opcode:str
    args:tuple[Any,...]


def parse_instruction(line:str)->Instruction:
    opcode,sep,payload=line.partition(" ")
    if opcode not in ALLOWED:
        raise ValueError(f"unsupported URL-lowering opcode {opcode!r}")
    if not sep:
        raise ValueError(f"{opcode} requires JSON arguments")
    args=json.loads(payload)
    if not isinstance(args,list):
        raise ValueError(f"{opcode} arguments must be a JSON array")
    return Instruction(opcode,tuple(args))


def find_operator(source:str,operator_id:str)->OperatorSpec:
    program=parse_rmapl(source)
    matches=[op for op in program.operators if op.operator_id==operator_id]
    if len(matches)!=1:
        raise ValueError(f"expected one {operator_id!r}, got {len(matches)}")
    return matches[0]


def require(ins:tuple[Instruction,...],wanted:Instruction)->None:
    if wanted not in ins:
        raise ValueError(f"missing URL-lowering instruction {wanted}")


def label_set(ins:tuple[Instruction,...])->set[str]:
    out=set()
    for item in ins:
        if item.opcode=="LABEL":
            if len(item.args)!=1 or not isinstance(item.args[0],str):
                raise ValueError("LABEL contract changed")
            out.add(item.args[0])
    return out


def lower(operator:OperatorSpec)->None:
    ins=tuple(parse_instruction(line) for line in operator.instructions)
    if label_set(ins)!=REQUIRED_LABELS:
        raise ValueError(
            f"URL labels changed: expected {sorted(REQUIRED_LABELS)}, got {sorted(label_set(ins))}"
        )
    require(ins,Instruction("GET",("raw","$candidate","construction.state.navigation.pendingHref")))
    require(ins,Instruction("LEN",("n","$raw")))
    require(ins,Instruction("BYTES_UTF8",("bytes","$raw")))

    # Prefix tests must remain literal and branch to the same families.
    for index,value in enumerate(b"rmapl://local/"):
        require(ins,Instruction("BUF_GET",("b","$bytes",index)))
        # Original variable names p0..p13.
        require(ins,Instruction("EQ",(f"p{index}","$b",value)))
    for index,value in enumerate(b"https://"):
        require(ins,Instruction("BUF_GET",("b","$bytes",index)))
        require(ins,Instruction("EQ",(f"h{index}","$b",value)))
    for index,value in enumerate(b"http://"):
        require(ins,Instruction("BUF_GET",("b","$bytes",index)))
        require(ins,Instruction("EQ",(f"t{index}","$b",value)))

    require(ins,Instruction("JUMP_IF_FALSE",("$is_local_abs","check_https")))
    require(ins,Instruction("JUMP_IF_FALSE",("$is_https","check_http")))
    require(ins,Instruction("JUMP_IF_FALSE",("$is_http","relative")))

    # Character policy: local ids reject : / ? # space; network host/path
    # reject ? # space. Require the literal byte tests to remain present.
    for value in (58,47,63,35,32):
        if not any(i.opcode=="EQ" and len(i.args)==3 and i.args[2]==value for i in ins):
            raise ValueError(f"local forbidden-byte test {value} disappeared")
    for value in (63,35,32):
        if not any(i.opcode=="EQ" and len(i.args)==3 and i.args[2]==value for i in ins):
            raise ValueError(f"network forbidden-byte test {value} disappeared")

    # Result surface must stay stable.
    for path in (
        "construction.state.navigation.pendingUrl",
        "construction.state.navigation.pendingHref",
        "construction.residuals",
    ):
        if not any(
            i.opcode=="SET" and len(i.args)==3 and i.args[0]=="$candidate" and i.args[1]==path
            for i in ins
        ):
            raise ValueError(f"URL result surface changed: missing SET {path}")

    constants={
        i.args[0]:i.args[1] for i in ins
        if i.opcode=="CONST" and len(i.args)==2 and isinstance(i.args[0],str)
    }
    if constants.get("prefix")!="rmapl://local/":
        raise ValueError("relative local canonical prefix changed")
    if constants.get("sep")!="://":
        raise ValueError("network canonical separator changed")
    if constants.get("local_residual") != [{"kind":"local-navigation-pending","detail":"url-resolved-local"}]:
        raise ValueError("local URL residual changed")
    if constants.get("network_residual") != [{"kind":"network-transport-pending","detail":"url-resolved-network-unavailable"}]:
        raise ValueError("network URL residual changed")
    if constants.get("invalid_residual") != [{"kind":"url-invalid","detail":"unsupported-or-malformed-url"}]:
        raise ValueError("invalid URL residual changed")

    returns=[i for i in ins if i.opcode=="RETURN"]
    expected={
        Instruction("RETURN",("$candidate","local-url-resolved")),
        Instruction("RETURN",("$candidate","network-url-resolved")),
        Instruction("RETURN",("$candidate","url-invalid")),
    }
    if len(returns)!=3 or any(item not in returns for item in expected):
        raise ValueError("URL return contract changed")


def q(value:str)->str:
    return json.dumps(value)


def render(profile:dict[str,Any])->str:
    module=profile["module"]

    def prefix_expr(prefix:bytes)->str:
        return " && ".join(
            f"BrowserUrlByte({i}) == {value}" for i,value in enumerate(prefix)
        )

    lines=[
        "# GENERATED FILE — DO NOT EDIT BY HAND",
        "# Lowered from examples/independent_browser_url.rmapl::browser_url_resolve",
        "# Lowering family: rmapl-rmal-url-resolve-lowering/v1",
        "",
        f"MODULE {module};",
        "",
        'CONTEXT RMAPL_URL_RESOLVE_PORT status="GENERATED" authority="LOCAL" evidence_transfer="DENY"',
        'BOUNDARY RMAPL_URL_RESOLVE_PORT CLAIM_CEILING BOUNDED_GENERATED_PORT REASON "RMAL owns URL policy; native callbacks expose input byte mechanics only"',
        "",
        "fn invalid_result(raw) {",
        '    let ack = BrowserUrlResult("", "", "", "", "", "", "", false, raw, "url-invalid", "unsupported-or-malformed-url", "url-invalid");',
        '    REQUIRE ack == "url-invalid:ACK";',
        '    return "url-invalid";',
        "}",
        "",
        "fn local_result(raw, page, canonical) {",
        '    let path = "/" + page;',
        '    let ack = BrowserUrlResult(raw, "rmapl", "local", path, canonical, "local", page, false, page, "local-navigation-pending", "url-resolved-local", "local-url-resolved");',
        '    REQUIRE ack == "local-url-resolved:ACK";',
        '    return "local-url-resolved";',
        "}",
        "",
        "fn network_result(raw, scheme, host, path) {",
        '    let canonical = scheme + "://" + host + path;',
        '    let ack = BrowserUrlResult(raw, scheme, host, path, canonical, "network", "", true, raw, "network-transport-pending", "url-resolved-network-unavailable", "network-url-resolved");',
        '    REQUIRE ack == "network-url-resolved:ACK";',
        '    return "network-url-resolved";',
        "}",
        "",
        "fn bad_local_byte(b) {",
        "    return b == 58 || b == 47 || b == 63 || b == 35 || b == 32;",
        "}",
        "",
        "fn bad_network_byte(b) {",
        "    return b == 63 || b == 35 || b == 32;",
        "}",
        "",
        "fn resolve_url() {",
        "    let raw = BrowserUrlRaw();",
        "    let n = BrowserUrlLength();",
        "    if n <= 0 { return invalid_result(raw); }",
        f"    if n >= 14 && {prefix_expr(b'rmapl://local/')} {{",
        '        let la_page = "";',
        "        let la_i = 14;",
        "        while la_i < n {",
        "            let la_b = BrowserUrlByte(la_i);",
        "            if bad_local_byte(la_b) { return invalid_result(raw); }",
        "            let la_ch = BrowserUrlChar(la_i);",
        '            if la_ch == "" { return invalid_result(raw); }',
        "            SET la_page = la_page + la_ch;",
        "            SET la_i = la_i + 1;",
        "        }",
        '        if la_page == "" { return invalid_result(raw); }',
        "        return local_result(raw, la_page, raw);",
        "    }",
        f"    if n >= 8 && {prefix_expr(b'https://')} {{",
        '        let https_scheme = "https";',
        "        let https_i = 8;",
        '        let https_host = "";',
        "        while https_i < n && BrowserUrlByte(https_i) != 47 {",
        "            let https_host_b = BrowserUrlByte(https_i);",
        "            if bad_network_byte(https_host_b) { return invalid_result(raw); }",
        "            let https_host_ch = BrowserUrlChar(https_i);",
        '            if https_host_ch == "" { return invalid_result(raw); }',
        "            SET https_host = https_host + https_host_ch;",
        "            SET https_i = https_i + 1;",
        "        }",
        '        if https_host == "" { return invalid_result(raw); }',
        '        let https_path = "/";',
        "        if https_i < n {",
        '            SET https_path = "";',
        "            while https_i < n {",
        "                let https_path_b = BrowserUrlByte(https_i);",
        "                if bad_network_byte(https_path_b) { return invalid_result(raw); }",
        "                let https_path_ch = BrowserUrlChar(https_i);",
        '                if https_path_ch == "" { return invalid_result(raw); }',
        "                SET https_path = https_path + https_path_ch;",
        "                SET https_i = https_i + 1;",
        "            }",
        "        }",
        "        return network_result(raw, https_scheme, https_host, https_path);",
        "    }",
        f"    if n >= 7 && {prefix_expr(b'http://')} {{",
        '        let http_scheme = "http";',
        "        let http_i = 7;",
        '        let http_host = "";',
        "        while http_i < n && BrowserUrlByte(http_i) != 47 {",
        "            let http_host_b = BrowserUrlByte(http_i);",
        "            if bad_network_byte(http_host_b) { return invalid_result(raw); }",
        "            let http_host_ch = BrowserUrlChar(http_i);",
        '            if http_host_ch == "" { return invalid_result(raw); }',
        "            SET http_host = http_host + http_host_ch;",
        "            SET http_i = http_i + 1;",
        "        }",
        '        if http_host == "" { return invalid_result(raw); }',
        '        let http_path = "/";',
        "        if http_i < n {",
        '            SET http_path = "";',
        "            while http_i < n {",
        "                let http_path_b = BrowserUrlByte(http_i);",
        "                if bad_network_byte(http_path_b) { return invalid_result(raw); }",
        "                let http_path_ch = BrowserUrlChar(http_i);",
        '                if http_path_ch == "" { return invalid_result(raw); }',
        "                SET http_path = http_path + http_path_ch;",
        "                SET http_i = http_i + 1;",
        "            }",
        "        }",
        "        return network_result(raw, http_scheme, http_host, http_path);",
        "    }",
        '    let rel_page = "";',
        "    let rel_i = 0;",
        "    while rel_i < n {",
        "        let rel_b = BrowserUrlByte(rel_i);",
        "        if bad_local_byte(rel_b) { return invalid_result(raw); }",
        "        let rel_ch = BrowserUrlChar(rel_i);",
        '        if rel_ch == "" { return invalid_result(raw); }',
        "        SET rel_page = rel_page + rel_ch;",
        "        SET rel_i = rel_i + 1;",
        "    }",
        '    if rel_page == "" { return invalid_result(raw); }',
        '    return local_result(raw, rel_page, "rmapl://local/" + rel_page);',
        "}",
        "",
    ]

    expected={
        "local_absolute":"local-url-resolved",
        "local_relative":"local-url-resolved",
        "https_path":"network-url-resolved",
        "http_root":"network-url-resolved",
        "invalid_query":"url-invalid",
        "invalid_empty_local":"url-invalid",
        "invalid_empty":"url-invalid",
    }
    for fixture in profile["fixtures"]:
        lines.append(f"REQUIRE BrowserUrlSelect({q(fixture)}) == {q(fixture + ':ACK')};")
        lines.append(f"REQUIRE resolve_url() == {q(expected[fixture])};")
    lines.extend(["",'print "RMAL_URL_RESOLVE_PASS";',"STOP;",""])
    return "\n".join(lines)


def load_profile(path:Path)->dict[str,Any]:
    profile=json.loads(path.read_text(encoding="utf-8"))
    if profile.get("schema")!="rmapl-rmal-url-resolve-lowering/v1":
        raise ValueError("unsupported URL lowering schema")
    return profile


def generated(profile_path:Path)->tuple[Path,str]:
    profile=load_profile(profile_path)
    source=(profile_path.parent/profile["source"]).resolve()
    output=(profile_path.parent/profile["output"]).resolve()
    operator=find_operator(source.read_text(encoding="utf-8"),profile["operator"])
    lower(operator)
    return output,render(profile)


def main()->int:
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
    if output.read_text(encoding="utf-8")!=expected:
        print("LOWERING DRIFT: URL RMAL does not match RMAPL source.",file=sys.stderr)
        return 1
    print("RMAPL_RMAL_URL_RESOLVE_LOWERING_CHECK PASS")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
