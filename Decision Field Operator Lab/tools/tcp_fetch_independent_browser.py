"""Raw network handoff for the RMAPL independent browser.

RMAPL owns URL parsing and HTTP request construction.
win32_tcp_transport owns only DNS/TCP byte movement.
This bootstrap materializes the request and response files.

RAW_TCP_RESPONSE != HTTP_RESPONSE_PARSED
RAW_TCP_RESPONSE != DOCUMENT_ADMITTED
HTTPS_URL != TLS_IMPLEMENTED
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

LAB = Path(__file__).resolve().parents[1]
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from rmapl_runtime import run_program

PROGRAM_PATH = LAB / "examples" / "independent_browser_transport.rmapl"

EMPTY_URL = {
    "raw": "",
    "scheme": "",
    "authority": "",
    "path": "",
    "canonical": "",
    "kind": "",
    "pageId": "",
    "networkRequired": False,
}


def handoff_omega(url: str) -> dict:
    return make_omega(
        native_type="independent-browser-transport/v0",
        native_identity="bootstrap:raw-tcp-fetch:1",
        source_refs=(f"requested-url:{url}",),
        state={
            "navigation": {
                "currentPage": "",
                "currentUrl": dict(EMPTY_URL),
                "pendingHref": url,
                "pendingUrl": dict(EMPTY_URL),
                "history": [],
                "focusIndex": -1,
                "focusedHref": "",
            },
            "network": {
                "host": "",
                "port": 0,
                "request": [],
                "response": [],
                "maxResponseBytes": 262144,
                "transport": "idle",
            },
        },
        path=(),
        frame={"obligation": "url-to-raw-tcp-response"},
        invariants=("sourceRefs", "claim-ceiling"),
        observations=(),
        residuals=(
            {"kind": "url-resolution-pending", "detail": "bootstrap"},
        ),
        decision_field={"goal": "preserved-tcp-exchange-handoff"},
        provenance=(
            {"kind": "bootstrap", "ref": "tcp_fetch_independent_browser.py"},
        ),
        evidence=(),
        claim_ceiling=(
            "URL_PARSE_RESOLVE != NETWORK_FETCH",
            "HTTP_REQUEST_BUILD != TCP_TRANSPORT",
            "TCP_TRANSPORT != HTTP_RESPONSE_PARSE",
            "RAW_RESPONSE_BYTES != DOCUMENT_ADMISSION",
            "HTTPS_URL != TLS_IMPLEMENTED",
        ),
        resource_bounds={"maxCandidates": 1, "maxSteps": 2},
        domain_remainder={
            "unsupported": [
                "tls",
                "http-response-parsing",
                "redirects",
                "cookies",
                "cache",
                "compression",
                "chunked-transfer-decoding",
            ]
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--transport", type=Path, required=True)
    parser.add_argument("--out-response", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--work-dir", type=Path, default=Path(".rmapl-net"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.transport.is_file():
        raise FileNotFoundError(args.transport)

    program = parse_rmapl(PROGRAM_PATH.read_text(encoding="utf-8"))
    registry = native_registry(program)
    result = run_program(
        program,
        handoff_omega(args.url),
        registry,
        stop_residual_kinds=(
            "tcp-exchange-pending",
            "tls-transport-pending",
        ),
    )

    if result["stopReason"] != "OUTER_CONTROLLER_BOUND" or len(result["branches"]) != 1:
        raise RuntimeError(
            "RMAPL request pipeline did not reach one transport handoff: "
            + json.dumps(
                {
                    "stopReason": result["stopReason"],
                    "stopFacts": result["stopFacts"],
                    "generation": result["generation"],
                },
                sort_keys=True,
            )
        )

    omega = result["branches"][0]["omega"]
    residual_kinds = {item["kind"] for item in omega["residuals"]}
    if "tls-transport-pending" in residual_kinds:
        pending = omega["state"]["navigation"]["pendingUrl"]
        raise RuntimeError(
            "HTTPS was parsed but TLS is not implemented in this bounded slice: "
            + pending["canonical"]
        )
    if residual_kinds != {"tcp-exchange-pending"}:
        raise RuntimeError(f"unexpected transport residuals: {sorted(residual_kinds)}")

    network = omega["state"]["network"]
    request = bytes(network["request"])
    if not request:
        raise RuntimeError("RMAPL produced an empty TCP request carrier")

    args.work_dir.mkdir(parents=True, exist_ok=True)
    request_path = args.work_dir / "request.bin"
    response_path = args.work_dir / "response.bin"
    request_path.write_bytes(request)
    response_path.unlink(missing_ok=True)

    completed = subprocess.run(
        [
            str(args.transport),
            network["host"],
            str(network["port"]),
            str(request_path),
            str(response_path),
            str(network["maxResponseBytes"]),
        ],
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"native TCP carrier exited with code {completed.returncode}"
        )
    if not response_path.is_file():
        raise RuntimeError("native TCP carrier did not materialize a response")

    response = response_path.read_bytes()
    if not response:
        raise RuntimeError("native TCP carrier returned an empty response")

    args.out_response.parent.mkdir(parents=True, exist_ok=True)
    args.out_response.write_bytes(response)

    receipt = {
        "schema": "rmapl-independent-browser-raw-transport-receipt/v0",
        "requestedUrl": args.url,
        "resolvedUrl": omega["state"]["navigation"]["pendingUrl"],
        "host": network["host"],
        "port": network["port"],
        "requestBytes": len(request),
        "responseBytes": len(response),
        "maxResponseBytes": network["maxResponseBytes"],
        "rmaplStopReason": result["stopReason"],
        "transport": "winsock-tcp",
        "httpParsed": False,
        "documentAdmitted": False,
        "claimCeiling": list(omega["claimCeiling"]),
    }

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
