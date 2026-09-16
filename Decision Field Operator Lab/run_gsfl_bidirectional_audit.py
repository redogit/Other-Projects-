#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import gsfl_bidirectional_cycle as cycle

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence" / "GSFL_BIDIRECTIONAL_RESULTS.json"


def fixture() -> dict:
    return {
        "payload": {
            "source_meaning": {"identity": "same", "purpose": "cooperative understanding"},
            "candidate_meaning": {"identity": "same", "purpose": "cooperative understanding"},
            "claims": {"fit_is_truth": True, "output_proves_learning": True},
            "candidates": [
                {"id": "human-admitted", "admitted": True, "score": 0.88},
                {"id": "attractive-rejected", "admitted": False, "score": 1.0},
            ],
        },
        "trace": [],
    }


def cycle_params() -> dict:
    return {
        "SEEK": {
            "OBSERVE": {"observation": "Outward exploration found a representation change without a declared source-meaning change."},
            "TRACE_TOOL": {
                "tool_id": "semantic-audit",
                "purpose": "trace outward comparison",
                "provenance": "GSFL v0.1 operator projection successor",
            },
        },
        "QUESTION": {
            "COMPARE": {"left": "source meaning", "right": "candidate surface"},
            "AUDIT_CONFOUNDS": {},
        },
        "REFRAME": {
            "MAP": {"source": "technical surface", "target": "human cooperative surface"},
            "ROTATE": {"surface": "Same meaning, reframed for cooperative human-machine use."},
            "RELATE": {"left": "human partner", "relation": "cooperates_with", "right": "machine partner"},
            "PRESERVE": {"keys": ["identity", "purpose"]},
        },
        "BUILD": {
            "COMPOSE": {"parts": ["observation", "distinction", "reframe", "verification"]},
            "VERIFY": {"checks": {"meaning_preserved": True, "provenance_present": True, "authority_not_transferred": True}},
            "HANDOFF": {"to": "human-partner", "reason": "bounded outward successor ready for inward reconciliation"},
        },
        "RETURN_INWARD": {
            "RECONSTRUCT": {"meaning": {"identity": "same", "purpose": "cooperative understanding"}},
            "TEACH_BACK": {"detail": "The preserved meaning can be restated after the outward build without claiming proof."},
            "DERIVE_COROLLARIES": {},
            "COMPARE": {
                "left": {"identity": "same", "purpose": "cooperative understanding"},
                "right": {"identity": "same", "purpose": "cooperative understanding"},
            },
            "PRESERVE": {"keys": ["identity", "purpose"]},
            "FIT": {},
        },
    }


def build_summary() -> dict:
    original = fixture()
    first = cycle.run_bidirectional_cycle(original, cycle_params=cycle_params())
    second = cycle.run_bidirectional_cycle(original, cycle_params=cycle_params())
    first_bytes = cycle.canonical_json(first).encode("utf-8")

    confound_ids = {row["id"] for row in first["payload"]["confounds"]}
    corollary_ids = {row["id"] for row in first["payload"]["corollaries"]}
    delegate_targets = {
        row.get("delegate_to")
        for row in first["payload"]["handoffs"]
        if row.get("delegate_to")
    }
    macro_phases = [row["phase"] for row in first["macro_trace"]]
    report = cycle.validate_macro_profile(cycle.load_macro_profile(), cycle.load_operator_profile())

    checks = {
        "profile_valid": report["valid"],
        "repeat_execution_byte_identical": cycle.canonical_json(first) == cycle.canonical_json(second),
        "input_envelope_unchanged": original == fixture(),
        "macro_order_exact": [row["macro"] for row in first["macro_trace"]] == ["SEEK", "QUESTION", "REFRAME", "BUILD", "RETURN_INWARD"],
        "outward_inward_phases_exact": macro_phases == ["OUTWARD", "OUTWARD", "OUTWARD", "OUTWARD", "INWARD"],
        "source_meaning_preserved": first["payload"]["source_meaning"] == original["payload"]["source_meaning"],
        "reconstruction_matches_source": first["payload"]["reconstruction"] == original["payload"]["source_meaning"],
        "declared_invariants_preserved": first["payload"]["preservation"]["passed"] is True,
        "bounded_verification_passed": first["payload"]["verification"]["passed"] is True,
        "fit_selected_admitted_candidate": first["payload"]["fit_selection"]["id"] == "human-admitted",
        "higher_scoring_rejected_candidate_not_selected": first["payload"]["fit_selection"]["id"] != "attractive-rejected",
        "canonical_delegates_present": delegate_targets == {"GROUND", "DISTINGUISH", "REPAIR", "SELECT"},
        "fit_truth_confound_detected": "FIT_SCORE_AS_TRUTH" in confound_ids,
        "output_learning_confound_detected": "OUTPUT_AS_LEARNING_EVIDENCE" in confound_ids,
        "tool_provenance_corollary_present": "TOOL_PROVENANCE_SEPARABLE" in corollary_ids,
        "source_lifecycle_preserved": first["cycle_summary"]["source_lifecycle"] == "COMPLETE_BOUNDED_V0_1",
    }
    if not all(checks.values()):
        failed = [key for key, value in checks.items() if not value]
        raise AssertionError("bidirectional macro audit checks failed: " + ", ".join(failed))

    profile = cycle.load_macro_profile()
    return {
        "artifact": "GSFL-v0.1-bidirectional-macro-cycle-audit",
        "profile_id": profile["profile_id"],
        "source_operator_projection_merge": profile["source_operator_projection_merge"],
        "source_gsfl_lifecycle": profile["source_gsfl_lifecycle"],
        "macro_count": report["macro_count"],
        "unique_operator_count": report["unique_operator_count"],
        "operator_invocation_count": sum(len(row["expansion"]) for row in first["macro_trace"]),
        "macro_order": [row["macro"] for row in first["macro_trace"]],
        "macro_phases": macro_phases,
        "selected_candidate": first["payload"]["fit_selection"]["id"],
        "checks": checks,
        "execution_sha256": hashlib.sha256(first_bytes).hexdigest(),
        "claim_ceiling": [
            "macro composition does not create primitive authority",
            "outward exploration is not validation",
            "inward coherence is not proof",
            "build is not truth",
            "operator execution does not transfer authority",
            "the completed GSFL v0.1 baseline remains unchanged by this successor",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the GSFL v0.1 bidirectional macro cycle")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    payload = cycle.canonical_json(build_summary())
    if args.write:
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(payload, encoding="utf-8")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    if args.check:
        if not EVIDENCE.exists():
            raise SystemExit("frozen bidirectional evidence is missing")
        if EVIDENCE.read_text(encoding="utf-8") != payload:
            raise SystemExit("fresh bidirectional audit does not match evidence/GSFL_BIDIRECTIONAL_RESULTS.json")
    if not (args.write or args.out or args.check):
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
