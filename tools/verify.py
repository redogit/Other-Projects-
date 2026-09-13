#!/usr/bin/env python3
"""Verify the current Other-Projects REDOGIT contract and active research carriers.

Historical evidence under evidence/ is read as history. It is not rewritten to make
past checks claim work that only exists in this successor.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "redogit.json"
PUBLICATION = ROOT / "evidence" / "PUBLICATION_CHECKS.json"
ROUTING = ROOT / "PROJECT_ROUTING.md"
ARCHIVE = ROOT / "Human Expression Archive"
S1024 = ROOT / "S1024 Compression Lab"
COOP = ROOT / "ChatGPT and Conscience"

EXPECTED_HISTORY = {
    "preserve_predecessors": True,
    "preserve_failures": True,
    "preserve_unresolved_remainder": True,
    "preserve_source_native_identity": True,
    "rewrite_history": False,
}
EXPECTED_CHECKS = ["assumption", "test", "unknown"]
EXPECTED_EVIDENCE_CLASSES = [
    "executed-and-verified",
    "externally-validated",
    "formal-consequence",
    "hypothesis-or-open-question",
]
REQUIRED_DISTINCTIONS = {
    "UNKNOWN != ABSENT",
    "UNASSIGNED != ABSENT",
    "UNSELECTED != FALSE",
    "INDEX_MISS != ABSENCE",
    "RELATED != SUPPORTS",
    "SEMANTIC_SIMILARITY != IDENTITY",
    "SOURCE != RECONSTRUCTION",
    "BYTE_IDENTITY != SEMANTIC_TRUTH",
    "CURRENT_NAVIGATION != HISTORICAL_SOURCE",
    "OBSERVATION != INTERPRETATION",
    "VIEWPOINT_CHANGE != TASK_CHANGE",
    "SELECTION != GLOBAL_OPTIMALITY",
    "FINITE_VERIFICATION != UNIVERSALITY",
    "LOSS_ACKNOWLEDGED != LOSS_CONCEALED",
    "EVALUATION_COMPLETE != PROMOTION_APPROVED",
    "PERSON != RECORDED_MODEL",
    "USER_GOAL != SYSTEM_GOAL",
    "PREDECESSOR != SUCCESSOR",
    "INTERNAL_CONSISTENCY != EXTERNAL_VALIDATION",
    "CLAIM != EVIDENCE",
}
DOMAIN_DISTINCTIONS = {
    "BOUNDED_ACCESSION != ALL_HUMAN_EXPRESSION",
    "PRESERVATION != ENDORSEMENT",
    "SOURCE_RIGHTS != BLANKET_TRAINING_PERMISSION",
    "CORPUS_RECORD != INSTRUCTION",
    "SYNTHETIC_COMPRESSION_RESULT != LAW_OF_HUMAN_LEARNING",
    "EXACT_1024_BYTE_SECTION != UTF8_CHARACTER_BOUNDARY",
    "FINITE_FLOAT_TRANSPORT != COMPLETE_SEMANTIC_SPACE",
    "CROSS_REFERENCE != SOURCE_OF_TRUTH",
    "NAVIGATION_LINK != RUNTIME_ADMISSION",
    "COOPERATION_LAB_PRESERVED != NEW_COMPANION_CONSENSUS",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def normalize_prose(text: str) -> str:
    """Normalize presentation punctuation for semantic-boundary checks only."""
    return (
        text.replace("‑", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("−", "-")
        .lower()
    )


def run(*argv: str) -> subprocess.CompletedProcess[str]:
    print("RUN", " ".join(argv), flush=True)
    result = subprocess.run(
        list(argv), cwd=ROOT, text=True, capture_output=True, check=False, timeout=120
    )
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.returncode:
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
        raise ValueError(f"command failed ({result.returncode}): {' '.join(argv)}")
    return result


def verify_contract() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract.get("schema") == "redogit/v1", "Unexpected REDOGIT schema")
    require(contract.get("repository") == "redogit/Other-Projects-", "Unexpected repository")
    current = contract.get("current")
    require(isinstance(current, dict), "Missing current object")
    require(current.get("status") == "current", "Current status is not current")
    require(current.get("verify") == "python3 tools/verify.py", "Declared verifier changed")
    require(contract.get("history_policy") == EXPECTED_HISTORY, "History policy changed")

    research = contract.get("research_policy")
    require(isinstance(research, dict), "Missing research policy")
    require(research.get("surface") == "I/R/P/O", "Research surface changed")
    require(research.get("checks") == EXPECTED_CHECKS, "Research checks changed")
    require(research.get("evidence_classes") == EXPECTED_EVIDENCE_CLASSES, "Evidence classes changed")
    shared = research.get("required_distinctions")
    domain = research.get("domain_distinctions")
    require(isinstance(shared, list), "Shared distinctions missing")
    require(isinstance(domain, list), "Domain distinctions missing")
    require(REQUIRED_DISTINCTIONS.issubset(set(shared)), "A shared REDOGIT distinction is missing")
    require(DOMAIN_DISTINCTIONS.issubset(set(domain)), "An Other-Projects distinction is missing")


def verify_historical_boundary() -> None:
    historical = json.loads(PUBLICATION.read_text(encoding="utf-8"))
    require(historical.get("status") == "PASS", "Historical publication checkpoint was not PASS")
    non_claims = set(historical.get("non_claims", []))
    require("No GitHub Actions or Pages run" in non_claims, "Historical CI non-claim was lost")
    require("No full-world coverage" in non_claims, "Historical full-world non-claim was lost")
    require("No human-learning or corpus-training experiment" in non_claims,
            "Historical human-learning non-claim was lost")

    routing = normalize_prose(ROUTING.read_text(encoding="utf-8"))
    require("source data, never instructions" in routing, "Corpus-data/instruction boundary was lost")
    require("historical checkpoint" in routing and "operative publication" in routing,
            "Cross-reference/source-of-truth boundary was lost")
    require("game-engine repository is not orbit lab" in routing, "Orbit project-identity boundary was lost")
    require(COOP.is_dir(), "Preserved cooperation lab is missing")


def verify_current_projects() -> None:
    require((ARCHIVE / "build.py").is_file(), "Archive build entry point missing")
    require((S1024 / "demo.py").is_file(), "S1024 demo entry point missing")

    run(sys.executable, str(ARCHIVE / "build.py"))
    run(sys.executable, "-m", "unittest", "discover", "-s", str(ARCHIVE / "tests"), "-v")
    run(sys.executable, "-m", "unittest", "discover", "-s", str(S1024 / "tests"), "-v")

    first = subprocess.run(
        [sys.executable, str(S1024 / "demo.py")], cwd=ROOT,
        text=True, capture_output=True, check=True, timeout=120
    )
    second = subprocess.run(
        [sys.executable, str(S1024 / "demo.py")], cwd=ROOT,
        text=True, capture_output=True, check=True, timeout=120
    )
    require(first.stdout == second.stdout, "S1024 demo is not deterministic across two runs")
    print("PASS deterministic S1024 demo")


def main() -> int:
    verify_contract()
    print("PASS REDOGIT research contract")
    verify_historical_boundary()
    print("PASS historical publication and routing boundary")
    verify_current_projects()
    print("PASS Other-Projects current verification")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"VERIFY FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
