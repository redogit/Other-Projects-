#!/usr/bin/env python3
"""Bounded structural check for the RMAL bidirectional response successor.

This deliberately does not impersonate RMALC.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "RMAL_BIDIRECTIONAL_HANDOFF_RESPONSE.rmal"
EVIDENCE = ROOT / "evidence" / "RMAL_BIDIRECTIONAL_HANDOFF_RESPONSE_2026-09-20.json"

ALLOWED_PREFIXES = (
    "MODULE ", "EXPORT ", "CONST ", "CONTEXT ", "RELATION ", "PRESERVE ",
    "ALLOW ", "CLAIM ", "EVIDENCE ", "COUNTERPROBE ", "VERIFY ", "CONTINUE",
)

REQUIRED_TEXT = (
    "MODULE bidirectional_handoff_response_protocol",
    'CONST validation_state = "NOT_RMALC_REVALIDATED"',
    "CONTEXT BidirectionalResponse authority=TARGET_LOCAL",
    "RELATION RespondsTo",
    "RELATION Counterproposes",
    "PRESERVE provenance request_identity prior_response target_authority privacy uncertainty unresolved_remainder way_back",
    "CLAIM ValidationState STATUS DECLARED",
    "EVIDENCE PredecessorCarrier TYPE VERIFIED_COMPUTATION LINEAGE cooperative_implementation_protocol",
    'COUNTERPROBE "Attempt response without request identity must fail at target policy gate"',
    'VERIFY "Response preserves target-local authority prior decision provenance and way back"',
)

def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    assert lines, "RMAL response carrier is empty"
    for line in lines:
        assert line.startswith(ALLOWED_PREFIXES), f"unsupported RMAL surface line: {line}"
    for required in REQUIRED_TEXT:
        assert required in text, f"missing required carrier declaration: {required}"

    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert data["schema"] == "rmal/bidirectional-handoff-response-carrier/v1"
    assert data["predecessor"]["merge_anchor"] == "f93f056a33d5fad0f29b763a0d49c6b79eb18d49"
    validation = data["successor_validation"]
    assert validation["rmalc_check"] == "NOT_REVALIDATED"
    assert validation["rmalc_compile"] == "NOT_REVALIDATED"
    assert validation["rmalc_audit"] == "NOT_REVALIDATED"
    assert data["semantics"]["cross_write_default"] == "DENY"
    assert data["semantics"]["evidence_transfer_default"] == "DENY"
    assert set(data["semantics"]["statuses"]) == {
        "ACCEPTED", "REJECTED", "NEEDS_EVIDENCE", "UNRESOLVED"
    }
    boundaries = set(data["boundaries"])
    for boundary in {
        "REQUEST != COMMAND",
        "RESPONSE != AUTHORITY_TRANSFER",
        "CONTROLLED_SURFACE_CHECK != RMALC_COMPILE",
        "AUTHORED_CARRIER != GENERIC_RESPONSE_RUNTIME",
    }:
        assert boundary in boundaries

    print(
        "PASS RMAL bidirectional response successor: controlled predecessor surface; "
        "fresh RMALC check/compile/audit intentionally NOT_REVALIDATED"
    )

if __name__ == "__main__":
    main()
