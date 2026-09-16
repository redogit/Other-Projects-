#!/usr/bin/env python3
"""Generate and audit the bounded GSFL v0.1 proverbial fixture corpus."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import gsfl
import gsfl_proverbs as proverbs

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence" / "PROVERBIAL_RESULTS.json"


def build_corpus():
    synthetic = list(proverbs.generate_synthetic_fixtures(seed=20260916, count=12))
    traditional = [
        proverbs.traditional_fixture(
            "many-hands",
            "Many hands make light work.",
            "common English-language saying; exact origin not established by this fixture",
        ),
        proverbs.traditional_fixture(
            "stitch-in-time",
            "A stitch in time saves nine.",
            "common English-language saying; exact origin not established by this fixture",
        ),
    ]
    return tuple(traditional + synthetic)


def build_summary() -> dict:
    corpus = build_corpus()
    first = proverbs.audit_corpus(corpus)
    second = proverbs.audit_corpus(build_corpus())
    first_bytes = gsfl.canonical_json(first).encode("utf-8")
    second_bytes = gsfl.canonical_json(second).encode("utf-8")
    if first_bytes != second_bytes:
        raise AssertionError("proverbial corpus audit is not byte-deterministic")

    all_rotation_checks = [
        check
        for fixture in first["fixture_audits"]
        for check in fixture["semantic_rotation_checks"]
    ]
    checks = {
        "repeat_audit_byte_identical": first_bytes == second_bytes,
        "fixture_count_14": first["fixture_count"] == 14,
        "synthetic_count_12": first["source_status_counts"].get("SYNTHETIC") == 12,
        "traditional_count_2": first["source_status_counts"].get("TRADITIONAL_OR_COMMON") == 2,
        "no_universal_meaning_claim": first["universal_meaning_claim"] is False,
        "all_fixture_surfaces_semantically_admitted": all(row["admitted"] for row in all_rotation_checks),
        "required_machine_human_confound_present": any(
            row["id"] == "MACHINE_PARAPHRASE_AS_HUMAN_UNDERSTANDING"
            for row in first["confounds"]
        ),
        "required_cultural_confound_present": any(
            row["id"] == "CULTURAL_FLATTENING" for row in first["confounds"]
        ),
        "required_provenance_confound_present": any(
            row["id"] == "ATTRIBUTION_UNCERTAINTY" for row in first["confounds"]
        ),
        "multiple_readings_corollary_present": any(
            row["id"] == "MULTIPLE_READINGS_REMAIN_DISTINCT" for row in first["corollaries"]
        ),
    }
    if not all(checks.values()):
        failed = [key for key, value in checks.items() if not value]
        raise AssertionError("proverbial audit checks failed: " + ", ".join(failed))

    return {
        "artifact": "GSFL-v0.1-proverbial-fixture-audit",
        "profile": "human-machine-cooperation",
        "generator_seed": 20260916,
        "checks": checks,
        "corollaries": first["corollaries"],
        "confounds": first["confounds"],
        "observations": first["observations"],
        "source_status_counts": first["source_status_counts"],
        "fixture_count": first["fixture_count"],
        "corpus_sha256": hashlib.sha256(first_bytes).hexdigest(),
        "claim_ceiling": first["claim_ceiling"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit GSFL v0.1 proverbial fixtures")
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
            raise SystemExit("frozen proverbial evidence is missing")
        if EVIDENCE.read_text(encoding="utf-8") != payload:
            raise SystemExit("fresh proverbial audit does not match evidence/PROVERBIAL_RESULTS.json")
    if not (args.write or args.out or args.check):
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
