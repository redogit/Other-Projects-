"""Materialize a bounded HTTP/1.1 request planned by RMAPL.

This tool does not construct HTTP syntax itself. The request bytes are produced
by examples/independent_browser_http.rmapl. The host only provides a typed URL
record, runs the bounded RMAPL program, and writes the resulting bytes.

HOST_MATERIALIZATION != HTTP_SEMANTICS
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

LAB = Path(__file__).resolve().parents[1]
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from rmapl_runtime import run_program

PROGRAM_PATH = LAB / "examples" / "independent_browser_http.rmapl"


def omega_for(host: str, path: str, scheme: str = "http") -> dict:
    if scheme not in {"http", "https"}:
        raise ValueError("scheme must be http or https")
    canonical = f"{scheme}://{host}{path}"
    empty_url = {
        "raw": "",
        "scheme": "",
        "authority": "",
        "path": "",
        "canonical": "",
        "kind": "",
        "pageId": "",
        "networkRequired": False,
    }
    return make_omega(
        native_type="independent-browser-http/v0",
        native_identity="bootstrap:http-plan:1",
        source_refs=(canonical,),
        state={
            "source": "",
            "resources": {"pages": []},
            "navigation": {
                "currentPage": "",
                "currentUrl": {
                    "raw": "rmapl://local/bootstrap",
                    "scheme": "rmapl",
                    "authority": "local",
                    "path": "/bootstrap",
                    "canonical": "rmapl://local/bootstrap",
                    "kind": "local",
                    "pageId": "bootstrap",
                    "networkRequired": False,
                },
                "pendingHref": canonical,
                "pendingUrl": {
                    "raw": canonical,
                    "scheme": scheme,
                    "authority": host,
                    "path": path,
                    "canonical": canonical,
                    "kind": "network",
                    "pageId": "",
                    "networkRequired": True,
                },
                "history": [],
                "focusIndex": -1,
                "focusedHref": "",
            },
            "input": {
                "pointer": {"x": 0, "y": 0},
                "keyboard": "",
                "lastHit": "",
            },
            "network": {
                "request": {
                    "host": "",
                    "port": 0,
                    "bytes": [],
                    "maxResponseBytes": 0,
                },
                "responseBytes": [],
                "response": {"status": 0, "bodyBytes": []},
            },
            "html": {"tokens": []},
            "dom": {"nodes": []},
            "layout": {"boxes": []},
            "hitMap": [],
            "camera": {
                "width": 160,
                "height": 64,
                "pixels": [],
                "verified": False,
                "admitted": False,
                "blackPixels": 0,
                "pgm": [],
            },
        },
        path=(),
        frame={"obligation": "plan-bounded-http-request"},
        invariants=("sourceRefs", "claim-ceiling"),
        observations=(),
        residuals=(
            {"kind": "network-transport-pending", "detail": "bootstrap"},
        ),
        decision_field={"goal": "native-http-transport-request"},
        provenance=(
            {"kind": "bootstrap", "ref": "plan_independent_browser_http.py"},
        ),
        evidence=(),
        claim_ceiling=(
            "HTTP_REQUEST_PLAN != NETWORK_FETCH",
            "TLS_REQUEST_PLAN != TLS_HANDSHAKE",
            "HTTP11_CLOSE_PROFILE != GENERAL_HTTP",
            "SOFTWARE_VERIFICATION != SECURITY_CERTIFICATION",
        ),
        resource_bounds={"maxCandidates": 1, "maxSteps": 1},
        domain_remainder={
            "unsupported": [
                "redirects",
                "chunked-transfer",
                "compression",
                "cookies",
                "authentication",
            ]
        },
    )


def plan(host: str, path: str, scheme: str = "http") -> tuple[bytes, dict]:
    program = parse_rmapl(PROGRAM_PATH.read_text(encoding="utf-8"))
    result = run_program(program, omega_for(host, path, scheme), native_registry(program))
    if len(result["branches"]) != 1:
        raise RuntimeError(
            "RMAPL HTTP planner did not expose exactly one branch: "
            + json.dumps(
                {
                    "stopReason": result["stopReason"],
                    "stopFacts": result["stopFacts"],
                    "generation": result["generation"],
                },
                sort_keys=True,
            )
        )
    branch = result["branches"][0]
    if not branch["admitted"]:
        raise RuntimeError("RMAPL HTTP planner proposal was rejected")
    omega = branch["omega"]
    expected_residual = (
        {"kind": "native-http-transport-pending", "detail": "rmapl-request-ready"}
        if scheme == "http"
        else {"kind": "native-tls-transport-pending", "detail": "rmapl-tls-request-ready"}
    )
    if omega["residuals"] != [expected_residual]:
        raise RuntimeError("RMAPL request planner did not reach expected native transport seam")
    request = omega["state"]["network"]["request"]
    payload = bytes(request["bytes"])
    receipt = {
        "schema": "rmapl-network-request-receipt/v0",
        "scheme": scheme,
        "omegaId": omega["id"],
        "host": request["host"],
        "port": request["port"],
        "requestBytes": len(payload),
        "maxResponseBytes": request["maxResponseBytes"],
        "residual": omega["residuals"][0],
        "claimCeiling": list(omega["claimCeiling"]),
    }
    return payload, receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scheme", choices=("http", "https"), default="http")
    parser.add_argument("--host", required=True)
    parser.add_argument("--path", default="/")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.host or any(c.isspace() for c in args.host):
        raise SystemExit("host must be non-empty and contain no whitespace")
    if not args.path.startswith("/") or any(c.isspace() for c in args.path):
        raise SystemExit("path must start with / and contain no whitespace")
    payload, receipt = plan(args.host, args.path, args.scheme)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(payload)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
