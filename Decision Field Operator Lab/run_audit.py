#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import builder

ROOT = Path(__file__).resolve().parent
COMMITTED_RESULTS = ROOT / "evidence" / "RESULTS.json"


def summary() -> dict:
    audit = builder.bounded_audit()
    fixtures = audit["balance"]["fixtures"]
    return {
        "schema": "decision-field-operator-lab/results-v1",
        "boolean": audit["boolean"],
        "compass": audit["compass"],
        "negative_controls": audit["negative_controls"],
        "admission_statuses": {
            name: record["status"]
            for name, record in audit["admission_protocol"].items()
        },
        "equal_gain_loss_control": audit["equal_gain_loss_control"],
        "balance_winners": {
            name: record["winner"]
            for name, record in fixtures.items()
            if isinstance(record, dict) and "winner" in record
        },
    }


def assert_contract() -> None:
    audit = builder.bounded_audit()
    compass = audit["compass"]
    if audit["boolean"]["operator_count"] != 16:
        raise AssertionError("binary Boolean operator census must be 16")
    if not audit["boolean"]["all_masks_present"] or not audit["boolean"]["all_certificates_verified"]:
        raise AssertionError("Boolean census/certificates incomplete")
    if audit["boolean"]["max_nand_gate_count"] != 5:
        raise AssertionError("declared NAND calibration maximum changed")
    if audit["negative_controls"]["xnor_reachable_within_four_nand_gates"]:
        raise AssertionError("XNOR four-gate negative control failed")
    if compass["heading_count"] != 80:
        raise AssertionError("4D compass census must be 80")
    if compass["support_counts"] != {1: 8, 2: 24, 3: 32, 4: 16}:
        raise AssertionError("4D compass support split changed")
    if compass["support_counts"] != compass["independent_orbit_counts"]:
        raise AssertionError("independent orbit construction disagrees")
    if not compass["coverage_verified"] or not compass["opposites_verified"]:
        raise AssertionError("compass coverage/opposite check failed")
    control = audit["equal_gain_loss_control"]
    if not (control["signed"] == 0.0 and control["magnitude"] == 2 and not control["representation_only"]):
        raise AssertionError("equal gain/loss must remain nonzero change")
    winners = summary()["balance_winners"]
    expected = {
        "exclusive_change": "XOR",
        "agreement": "XNOR",
        "intersection": "AND",
        "coverage": "OR",
        "endpoint_preserving_symmetric": "AND",
    }
    if winners != expected:
        raise AssertionError(f"balance fixtures changed: {winners!r}")


def write_full(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "AUDIT.json").write_text(
        json.dumps(builder.bounded_audit(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "OPERATOR_TABLE.json").write_text(
        json.dumps(builder.periodic_table(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build/check bounded Decision Field Operator Lab evidence.")
    parser.add_argument("--check", action="store_true", help="Verify the finite contract and committed concise results.")
    parser.add_argument("--out", type=Path, help="Write full AUDIT.json and OPERATOR_TABLE.json to this directory.")
    args = parser.parse_args()

    assert_contract()

    if args.check:
        committed = json.loads(COMMITTED_RESULTS.read_text(encoding="utf-8"))
        fresh = json.loads(json.dumps(summary()))
        if committed != fresh:
            raise SystemExit("committed RESULTS.json is stale")

    if args.out:
        write_full(args.out)

    result = summary()
    print(
        "PASS operator-field audit: "
        f"{result['boolean']['operator_count']} Boolean operators, "
        f"max NAND gates {result['boolean']['max_nand_gate_count']}, "
        f"{result['compass']['heading_count']} compass headings, "
        "4 symmetry templates, XNOR four-gate negative control preserved."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
