"""Differential evidence for browser_url_resolve.

Native RMAL owns URL policy. Python invokes the current RMAPL operator only as
an oracle and compares the complete pending-URL + residual contract.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import subprocess
import sys

LAB=Path(__file__).resolve().parents[1]
if str(LAB) not in sys.path:
    sys.path.insert(0,str(LAB))

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from tools.interact_independent_browser import initial_omega

PROGRAM_PATH=LAB/"examples"/"independent_browser_url.rmapl"

FIXTURES={
    "local_absolute":"rmapl://local/page2",
    "local_relative":"page2",
    "https_path":"https://example.com/docs",
    "http_root":"http://example.com",
    "invalid_query":"https://example.com/a?b",
    "invalid_empty_local":"rmapl://local/",
    "invalid_empty":"",
}


def pages():
    return [
        {"id":"page1","url":"rmapl://local/page1","source":"<p>ONE</p>"},
        {"id":"page2","url":"rmapl://local/page2","source":"<p>TWO</p>"},
    ]


def candidate(raw:str)->dict:
    base=initial_omega(pages(),"page1")
    construction=deepcopy(base["construction"])
    construction["state"]["navigation"]["pendingHref"]=raw
    construction["residuals"]=[
        {"kind":"url-resolution-pending","detail":"differential-oracle"}
    ]
    return make_omega(**construction)


def parse_line(line:str)->dict[str,str]:
    fields={}
    for token in line.split()[1:]:
        key,value=token.split("=",1)
        fields[key]=value
    return fields


def oracle(operator,raw:str)->dict[str,object]:
    proposal=operator(candidate(raw))
    omega=proposal["omega"]
    nav=omega["state"]["navigation"]
    url=nav["pendingUrl"]
    residual=omega["residuals"][0]
    return {
        "raw":url["raw"].encode("utf-8"),
        "scheme":url["scheme"],
        "authority":url["authority"],
        "path":url["path"],
        "canonical":url["canonical"],
        "kind":url["kind"],
        "page":url["pageId"],
        "network":url["networkRequired"],
        "pending":nav["pendingHref"].encode("utf-8"),
        "residual":residual["kind"],
        "detail":residual["detail"],
        "consequence":proposal["consequenceKey"],
    }


def bt(v:bool)->str:
    return "true" if v else "false"


def main()->int:
    if len(sys.argv)!=3:
        raise SystemExit(
            "usage: verify_url_resolve_equivalence.py "
            "<browser_rmal_url_host> <browser_url_resolve.rmal>"
        )
    completed=subprocess.run(
        [sys.argv[1],sys.argv[2]],capture_output=True,text=True,check=True
    )
    actual={
        row["fixture"]:row
        for row in (
            parse_line(line) for line in completed.stdout.splitlines()
            if line.startswith("RMAL_URL ")
        )
    }
    if set(actual)!=set(FIXTURES):
        raise AssertionError(
            f"RMAL URL fixture set mismatch: {sorted(actual)}\n"+completed.stdout
        )

    program=parse_rmapl(PROGRAM_PATH.read_text(encoding="utf-8"))
    operator=native_registry(program)["browser_url_resolve"]

    for name,raw in FIXTURES.items():
        expected=oracle(operator,raw)
        row=actual[name]
        assert bytes.fromhex(row["raw_hex"])==expected["raw"],(name,row,expected)
        assert row["scheme"]==expected["scheme"],(name,row,expected)
        assert row["authority"]==expected["authority"],(name,row,expected)
        assert row["path"]==expected["path"],(name,row,expected)
        assert row["canonical"]==expected["canonical"],(name,row,expected)
        assert row["kind"]==expected["kind"],(name,row,expected)
        assert row["page"]==expected["page"],(name,row,expected)
        assert row["network"]==bt(bool(expected["network"])),(name,row,expected)
        assert bytes.fromhex(row["pending_hex"])==expected["pending"],(name,row,expected)
        assert row["residual"]==expected["residual"],(name,row,expected)
        assert row["detail"]==expected["detail"],(name,row,expected)
        assert row["consequence"]==expected["consequence"],(name,row,expected)

    receipt=f"RMAL_URL_RECEIPT fixtures={len(FIXTURES)} policy_in_rmal=true python_runtime_used=false"
    if receipt not in completed.stdout:
        raise AssertionError("native RMAL URL receipt missing")

    print("RMAPL_RMAL_URL_RESOLVE_EQUIVALENCE PASS")
    print("BYTE_MECHANICS_CALLBACKS != URL_POLICY")
    print("PYTHON_DIFFERENTIAL_ORACLE != RMAL_RUNTIME_DEPENDENCY")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
