"""Bootstrap runner for the RMAPL-only independent-browser render profile.

This file does not implement HTML parsing, DOM construction, layout, font
rasterization, or frame verification. Those operations live in
examples/independent_browser_native.rmapl. This runner only supplies the Omega
input, executes the bounded RMAPL runtime, and materializes the admitted P5
camera carrier as bytes.

BOOTSTRAP_HOST != BROWSER_IMPLEMENTATION
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

PROGRAM_PATH = LAB / "examples" / "independent_browser_native.rmapl"


def browser_omega(source: str) -> dict:
    return make_omega(
        native_type="independent-browser/v0",
        native_identity="bootstrap:independent-browser:1",
        source_refs=("bootstrap:inline-or-file",),
        state={
            "source": source,
            "html": {"tokens": []},
            "dom": {"nodes": []},
            "layout": {"boxes": []},
            "hitMap": [],
            "documents": {},
            "location": "bootstrap:inline",
            "history": [],
            "input": {"clickX": 0, "clickY": 0, "consumed": False},
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
        frame={"obligation": "render-bounded-html-to-owned-camera-stream"},
        invariants=("sourceRefs", "claim-ceiling"),
        observations=(),
        residuals=(
            {"kind": "html-tokenization-pending", "detail": "bootstrap"},
        ),
        decision_field={"goal": "admitted-independent-camera-stream"},
        provenance=(
            {"kind": "bootstrap-runner", "ref": "render_independent_browser.py"},
        ),
        evidence=(),
        claim_ceiling=(
            "BOUNDED_HTML_SUBSET != GENERAL_WEB_COMPATIBILITY",
            "P5_CAMERA_STREAM != OS_WINDOW_PRESENTATION",
            "RMAPL_BROWSER_LOGIC != SELF_HOSTED_RMAPL_RUNTIME",
            "SOFTWARE_VERIFICATION != SECURITY_CERTIFICATION",
        ),
        resource_bounds={"maxCandidates": 1, "maxSteps": 8},
        domain_remainder={
            "unsupported": [
                "network",
                "tls",
                "css",
                "javascript",
                "images",
                "forms",
                "unicode-non-ascii-tokenization",
                "html-error-recovery",
                "interactive-input",
            ]
        },
    )


def render(source: str) -> tuple[bytes, dict]:
    program = parse_rmapl(PROGRAM_PATH.read_text(encoding="utf-8"))
    result = run_program(program, browser_omega(source), native_registry(program))
    if result["stopReason"] != "SUCCESS" or len(result["branches"]) != 1:
        raise RuntimeError(
            "RMAPL browser did not produce one admitted success branch: "
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
    camera = branch["omega"]["state"]["camera"]
    if not branch["admitted"] or not camera["verified"] or not camera["admitted"]:
        raise RuntimeError("RMAPL browser frame was not verified and admitted")

    pgm = bytes(camera["pgm"])
    receipt = {
        "schema": "rmapl-independent-browser-camera-receipt/v0",
        "program": result["program"],
        "omegaId": branch["omega"]["id"],
        "width": camera["width"],
        "height": camera["height"],
        "blackPixels": camera["blackPixels"],
        "cameraBytes": len(pgm),
        "verified": camera["verified"],
        "admitted": camera["admitted"],
        "executedStages": result["generation"]["executedCount"],
        "claimCeiling": list(branch["omega"]["claimCeiling"]),
    }
    return pgm, receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--html")
    source.add_argument("--html-file", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.html is not None:
        source = args.html
    else:
        source = args.html_file.read_text(encoding="utf-8")

    pgm, receipt = render(source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(pgm)
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
