#!/usr/bin/env python3
"""Deterministic bounded audit for the GSFL v0 reference implementation."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import gsfl

ROOT = Path(__file__).resolve().parent
EXAMPLE = ROOT / "examples" / "n_observer_accessibility.gsfl"
EVIDENCE = ROOT / "evidence" / "RESULTS.json"


def build_summary() -> dict:
    program = EXAMPLE.read_text(encoding="utf-8")
    first = gsfl.execute(program)
    second = gsfl.execute(program)
    first_bytes = gsfl.canonical_json(first).encode("utf-8")
    second_bytes = gsfl.canonical_json(second).encode("utf-8")
    if first_bytes != second_bytes:
        raise AssertionError("GSFL execution is not byte-deterministic")

    evaluations = {row["candidate_id"]: row for row in first["evaluations"]}
    required = {
        "technical": (gsfl.VALID_ROTATION, True),
        "human": (gsfl.VALID_ROTATION, True),
        "attractive-mutation": (gsfl.MUTATION, False),
        "invariant-decay": (gsfl.SEMANTIC_DECAY, False),
        "lossy-summary": (gsfl.VALID_ROTATION, False),
    }
    checks: dict[str, bool] = {
        "selected_human_surface": first["selected_candidate"] == "human",
        "repeat_execution_byte_identical": first_bytes == second_bytes,
        "source_world_state_preserved": first["source_meaning"]["world_state"] == "unchanged",
        "n_cardinality_preserved": first["source_meaning"]["cardinality"] == "N",
    }
    for candidate_id, (classification, admitted) in required.items():
        row = evaluations[candidate_id]
        checks[f"{candidate_id}_classification"] = row["classification"] == classification
        checks[f"{candidate_id}_admission"] = row["admitted"] is admitted

    if not all(checks.values()):
        failed = [key for key, value in checks.items() if not value]
        raise AssertionError("audit checks failed: " + ", ".join(failed))

    return {
        "artifact": "GSFL-v0-bounded-audit",
        "gsfl_version": 0,
        "example": "examples/n_observer_accessibility.gsfl",
        "selected_candidate": first["selected_candidate"],
        "candidate_count": len(first["evaluations"]),
        "admitted_candidates": sorted(row["candidate_id"] for row in first["evaluations"] if row["admitted"]),
        "classifications": {candidate_id: evaluations[candidate_id]["classification"] for candidate_id in sorted(evaluations)},
        "checks": checks,
        "execution_sha256": hashlib.sha256(first_bytes).hexdigest(),
        "claim_ceiling": [
            "bounded reference implementation only",
            "declared metrics are task-relative surrogates, not universal human cognition measures",
            "exact reconstruction in v0 is a machine-checkable surrogate, not participant comprehension evidence",
            "software verification does not establish universal semantic equivalence",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit GSFL v0")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="compare fresh audit to committed evidence")
    group.add_argument("--write", action="store_true", help="replace committed bounded evidence")
    parser.add_argument("--out", type=Path, help="optionally write fresh summary elsewhere")
    args = parser.parse_args()

    summary = build_summary()
    payload = gsfl.canonical_json(summary)

    if args.write:
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(payload, encoding="utf-8")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    if args.check:
        if not EVIDENCE.exists():
            raise SystemExit("frozen evidence is missing")
        expected = EVIDENCE.read_text(encoding="utf-8")
        if expected != payload:
            raise SystemExit("fresh audit does not match evidence/RESULTS.json")
    if not args.write and not args.out and not args.check:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
