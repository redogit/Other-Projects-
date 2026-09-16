#!/usr/bin/env python3
"""Deterministic bounded audit for the GSFL v0.1 cooperation profile."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import gsfl
import gsfl_coop as coop

ROOT = Path(__file__).resolve().parent
EXAMPLE = ROOT / "examples" / "n_observer_cooperation.gsfl"
EVIDENCE = ROOT / "evidence" / "COOPERATION_RESULTS.json"


def build_summary() -> dict:
    program = EXAMPLE.read_text(encoding="utf-8")
    first = coop.execute_cooperation(program)
    second = coop.execute_cooperation(program)
    first_bytes = gsfl.canonical_json(first).encode("utf-8")
    second_bytes = gsfl.canonical_json(second).encode("utf-8")
    if first_bytes != second_bytes:
        raise AssertionError("cooperation execution is not byte-deterministic")

    by_id = {row["candidate_id"]: row for row in first["evaluations"]}
    confound_ids = {row["id"] for row in first["confound_findings"]}
    corollary_ids = {row["id"] for row in first["corollaries"]}
    checks = {
        "repeat_execution_byte_identical": first_bytes == second_bytes,
        "selected_human_cooperative_surface": first["selected_candidate"] == "human-cooperative",
        "vocabulary_majority_passes": first["vocabulary_audit"]["passes"] is True,
        "vocabulary_ratio_over_half": first["vocabulary_audit"]["ratio"] > 0.5,
        "human_machine_ids_distinct": first["cooperation"]["human_partner"]["partner_id"] != first["cooperation"]["machine_partner"]["partner_id"],
        "tool_provenance_present": all(tool["provenance"] for tool in first["cooperation"]["tools"]),
        "attractive_mutation_rejected": by_id["attractive-mutation"]["classification"] == "MUTATION" and not by_id["attractive-mutation"]["admitted"],
        "in_context_weight_confound_present": "IN_CONTEXT_AS_WEIGHT_UPDATE" in confound_ids,
        "correlated_tool_confound_present": "CORRELATED_TOOLS_AS_INDEPENDENT_VERIFICATION" in confound_ids,
        "lexical_majority_confound_present": "LEXICAL_MAJORITY_AS_COMPREHENSION" in confound_ids,
        "understanding_separation_corollary_present": "UNDERSTANDING_REMAINS_SEPARATE" in corollary_ids,
        "tool_provenance_corollary_present": "TOOL_PROVENANCE_SEPARABLE" in corollary_ids,
    }
    if not all(checks.values()):
        failed = [key for key, value in checks.items() if not value]
        raise AssertionError("cooperation audit checks failed: " + ", ".join(failed))

    return {
        "artifact": "GSFL-v0.1-human-machine-cooperation-audit",
        "profile": "human-machine-cooperation",
        "example": "examples/n_observer_cooperation.gsfl",
        "selected_candidate": first["selected_candidate"],
        "checks": checks,
        "vocabulary_audit": first["vocabulary_audit"],
        "corollaries": first["corollaries"],
        "confound_findings": first["confound_findings"],
        "confound_registry": first["confound_registry"],
        "execution_sha256": hashlib.sha256(first_bytes).hexdigest(),
        "claim_ceiling": [
            "human approval is not human understanding or ground truth",
            "machine output or in-context adaptation is not persistent machine-learning evidence",
            "tool provenance does not grant tool authority",
            "lexical vocabulary majority is not comprehension evidence",
            "fit selection occurs only after v0 semantic admission",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit GSFL v0.1 human-machine cooperation")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    parser.add_argument("--out", type=Path)
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
            raise SystemExit("frozen cooperation evidence is missing")
        if EVIDENCE.read_text(encoding="utf-8") != payload:
            raise SystemExit("fresh cooperation audit does not match evidence/COOPERATION_RESULTS.json")
    if not (args.write or args.out or args.check):
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
