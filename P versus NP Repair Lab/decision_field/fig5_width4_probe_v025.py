from __future__ import annotations

"""Reproducible staged runner for the FIG-5 v0.25 width-4 probe.

Every command executes exactly one stage and emits one JSON object.  Later
stages consume sealed earlier-stage objects; they never call earlier or later
scientific stages implicitly.

    MATERIALIZE -> GENERATE -> VERIFY -> ADMIT -> ANALYZE

POSTHOC consumes the sealed chain but is explicitly non-promotable.  The
official seed derivation requires the preregistration commit, so official
seeds and rows cannot be materialized before preregistration is committed.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
from typing import Iterable, Sequence

import fig5_width4_family_v025 as family
from fig5_dp_mirror_v020 import (
    VERSION as SOLVER_VERSION,
    active_dp,
    brute_force_sat,
    execute_fixed_sequence,
    independent_dp160,
    permute_formula,
)


EXPERIMENT_ID = "FIG-5-v0.25-width4-density4"
OFFICIAL_SEED_NAMESPACE = "FIG5/BLOCK-SEED/v0.25-WIDTH4-DENSITY4"
TEST_SEED_NAMESPACE = "TEST-ONLY/FIG5/BLOCK-SEED/v0.25-WIDTH4-DENSITY4"
CONSTRUCTOR_SHA256 = "3c5b549b5b35e320894090f5408756bacbdc5965f1cd611893dd22d232f7327a"
SOLVER_SHA256 = "b6c6e5c360b2166e43e383c280d33f8f2c48b9a9a763212bc2ec467b62a628c5"
ACTIVE_CAP = 160
INDEPENDENT_DP_CAP = 160
NSTAR_RECEIPT_SHA256 = "682bbcf6ed83e6d3f3264b7ca41257e60c64dc56b4c0fc331057808a845d440d"
DELTA_WITNESS_SHA256 = "2b1b2d04819f262ab5d8d8fd654a5c550a3978fa8bd8d75a9737322aacb5df09"
PREDECESSOR_CLOSE_COMMIT = "8e24af67b75a7135f868afb0bed0d9b3e53067f2"
BLOCK_COUNT = 5
CALIBRATION_N = frozenset({8, 9, 10})
VALIDATION_N = frozenset({11, 12, 13})


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_hex(*parts: object) -> str:
    digest = hashlib.sha256()
    for part in parts:
        encoded = str(part).encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _validate_commit(commit: str) -> None:
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise ValueError("preregistration_commit must be 40 lowercase hexadecimal characters")


def derive_seed(namespace: str, preregistration_commit: str, block_id: int) -> str:
    """Derive one seed from preregistered provenance; never search or retry."""
    if not namespace:
        raise ValueError("namespace must be non-empty")
    _validate_commit(preregistration_commit)
    if not isinstance(block_id, int) or isinstance(block_id, bool) or not 0 <= block_id < BLOCK_COUNT:
        raise ValueError(f"block_id must be in 0..{BLOCK_COUNT - 1}")
    return _sha256_hex(
        namespace,
        EXPERIMENT_ID,
        CONSTRUCTOR_SHA256,
        SOLVER_SHA256,
        ACTIVE_CAP,
        NSTAR_RECEIPT_SHA256,
        DELTA_WITNESS_SHA256,
        PREDECESSOR_CLOSE_COMMIT,
        preregistration_commit,
        block_id,
    )


def _mean(values: Sequence[float]) -> float | None:
    return statistics.fmean(values) if values else None


def materialize_rows(
    seeds: Sequence[dict],
    n_levels: Sequence[int],
    provenance: dict,
) -> dict:
    """Materialize formulas only; no active or independent solver is invoked."""
    rows: list[dict] = []
    block_efficiency: list[dict] = []
    for seed_record in seeds:
        block_id = seed_record["block_id"]
        seed = seed_record["seed"]
        generated, efficiency = family.generate_block(seed, n_levels)
        block_efficiency.append({"block_id": block_id, **efficiency})
        for n in n_levels:
            formula, trace = generated[n]
            rows.append(
                {
                    "block_id": block_id,
                    "n": n,
                    "seed": seed,
                    "formula": [list(clause) for clause in formula],
                    "generation_trace": asdict(trace),
                }
            )

    adjacent_jaccards: list[float] = []
    old_clause_retentions: list[float] = []
    by_block: dict[int, list[dict]] = {}
    for row in rows:
        by_block.setdefault(row["block_id"], []).append(row)
    for block_rows in by_block.values():
        ordered = sorted(block_rows, key=lambda row: row["n"])
        for left, right in zip(ordered, ordered[1:]):
            old = {tuple(clause) for clause in left["formula"]}
            new = {tuple(clause) for clause in right["formula"]}
            adjacent_jaccards.append(len(old & new) / len(old | new))
            old_clause_retentions.append(len(old & new) / len(old))

    digests = [row["generation_trace"]["formula_digest"] for row in rows]
    support_failures = sum(
        row["generation_trace"]["active_variable_count"] != row["n"] for row in rows
    )
    priority_collisions = sum(
        row["generation_trace"]["priority_hash_collision_count"] for row in rows
    )
    return {
        "schema": "fig5-v025-width4-manifest/v1",
        "experiment_id": EXPERIMENT_ID,
        "stage": "MATERIALIZE",
        "status": "MATERIALIZED_NOT_EXECUTED",
        "provenance": provenance,
        "constructor": {
            "version": family.FAMILY_VERSION,
            "sha256": CONSTRUCTOR_SHA256,
            "width": family.WIDTH,
            "density": "4/1",
            "priority_namespace": family.PRIORITY_NAMESPACE,
        },
        "seeds": list(seeds),
        "rows": rows,
        "structural_qa": {
            "row_count": len(rows),
            "distinct_formula_digests": len(set(digests)),
            "support_failures": support_failures,
            "priority_collisions": priority_collisions,
            "mean_adjacent_jaccard": _mean(adjacent_jaccards),
            "mean_old_clause_retention": _mean(old_clause_retentions),
            "min_old_clause_retention": min(old_clause_retentions, default=None),
            "max_old_clause_retention": max(old_clause_retentions, default=None),
        },
        "generation_efficiency": {
            "blocks": block_efficiency,
            "total_priority_evaluations": sum(
                row["priority_evaluations"] for row in block_efficiency
            ),
            "total_sorts": sum(row["sort_count"] for row in block_efficiency),
            "method": "one maximum width-4 universe ranking per block; lower n levels are stable eligibility filters",
        },
        "generate_run": False,
        "verify_run": False,
        "admit_run": False,
        "boundaries": [
            "MATERIALIZE != GENERATE",
            "WIDTH4_IDENTITY != WIDTH3_IDENTITY",
            "GENERATE != VERIFY != ADMIT",
            "P ?= NP = OPEN",
        ],
    }


def official_manifest(preregistration_commit: str) -> dict:
    """Materialize the five official blocks after preregistration is committed."""
    _validate_commit(preregistration_commit)
    root = Path(__file__).resolve().parent
    constructor_path = root / "fig5_width4_family_v025.py"
    solver_path = root / "fig5_dp_mirror_v020.py"
    if file_sha256(constructor_path) != CONSTRUCTOR_SHA256:
        raise RuntimeError("constructor source hash does not match preregistration input")
    if file_sha256(solver_path) != SOLVER_SHA256:
        raise RuntimeError("active solver source hash does not match frozen v0.20 identity")

    seeds = [
        {
            "block_id": block_id,
            "seed": derive_seed(OFFICIAL_SEED_NAMESPACE, preregistration_commit, block_id),
        }
        for block_id in range(BLOCK_COUNT)
    ]
    if len({record["seed"] for record in seeds}) != BLOCK_COUNT:
        raise RuntimeError("official seed collision: STOP_NO_RETRY_NO_RESEED")
    return materialize_rows(
        seeds=seeds,
        n_levels=family.ALLOWED_N,
        provenance={
            "preregistration_commit": preregistration_commit,
            "predecessor_close_commit": PREDECESSOR_CLOSE_COMMIT,
            "seed_namespace": OFFICIAL_SEED_NAMESPACE,
            "seed_derivation": "SHA256(length-prefixed ordered inputs)",
            "seed_ordered_inputs": [
                "namespace",
                "experiment_id",
                "constructor_sha256",
                "active_solver_sha256",
                "active_cap",
                "nstar_receipt_sha256",
                "delta_witness_sha256",
                "predecessor_close_commit",
                "preregistration_commit",
                "block_id",
            ],
            "collision_policy": "STOP_NO_RETRY_NO_RESEED",
        },
    )


def _row_key(row: dict) -> tuple[int, int]:
    return int(row["block_id"]), int(row["n"])


def _rows_by_key(stage: dict) -> dict[tuple[int, int], dict]:
    keyed = {_row_key(row): row for row in stage["rows"]}
    if len(keyed) != len(stage["rows"]):
        raise ValueError(f"duplicate row identity in {stage.get('stage')}")
    return keyed


def _validate_manifest(manifest: dict) -> None:
    if manifest.get("stage") != "MATERIALIZE" or manifest.get("status") != "MATERIALIZED_NOT_EXECUTED":
        raise ValueError("expected a sealed MATERIALIZE object")
    if manifest.get("generate_run") or manifest.get("verify_run") or manifest.get("admit_run"):
        raise ValueError("manifest collapses stage firewall")
    rows_by_seed: dict[str, list[dict]] = {}
    for row in manifest["rows"]:
        rows_by_seed.setdefault(row["seed"], []).append(row)
    for seed, seed_rows in rows_by_seed.items():
        regenerated, _ = family.generate_block(seed, tuple(row["n"] for row in seed_rows))
        for row in seed_rows:
            formula, trace = regenerated[row["n"]]
            if [list(clause) for clause in formula] != row["formula"]:
                raise ValueError(f"formula reconstruction mismatch at {_row_key(row)}")
            if asdict(trace) != row["generation_trace"]:
                raise ValueError(f"generation trace mismatch at {_row_key(row)}")


def _effective_workers(requested: int | None, item_count: int) -> int:
    if requested is not None and requested < 1:
        raise ValueError("workers must be positive")
    available = os.cpu_count() or 1
    return min(requested or BLOCK_COUNT, BLOCK_COUNT, available, max(1, item_count))


def _ordered_map(function: object, items: list, workers: int | None) -> list:
    worker_count = _effective_workers(workers, len(items))
    if worker_count == 1 or len(items) <= 1:
        return [function(item) for item in items]
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        return list(executor.map(function, items))


def _generate_one(payload: tuple[dict, int]) -> dict:
    row, active_cap = payload
    return {
        "block_id": row["block_id"],
        "n": row["n"],
        "formula_digest": row["generation_trace"]["formula_digest"],
        "active": asdict(active_dp(row["formula"], cap=active_cap)),
    }


def run_generate(
    manifest: dict,
    active_cap: int = ACTIVE_CAP,
    workers: int | None = None,
) -> dict:
    """Execute only the frozen active solver."""
    _validate_manifest(manifest)
    rows = _ordered_map(
        _generate_one,
        [(row, active_cap) for row in manifest["rows"]],
        workers,
    )
    return {
        "schema": "fig5-v025-width4-generate/v1",
        "experiment_id": EXPERIMENT_ID,
        "stage": "GENERATE",
        "status": "GENERATE_SEALED_VERIFY_NOT_RUN",
        "manifest_canonical_sha256": canonical_sha256(manifest),
        "solver": {"version": SOLVER_VERSION, "sha256": SOLVER_SHA256, "cap": active_cap},
        "rows": rows,
        "verify_run": False,
        "admit_run": False,
        "boundaries": [
            "GENERATE != VERIFY != ADMIT",
            "ACTIVE_CAP_160 != ASYMPTOTIC_BOUND",
            "FIG5_RESULT != P_VS_NP_RESULT",
            "P ?= NP = OPEN",
        ],
    }


def _validate_generate(manifest: dict, generated: dict) -> None:
    _validate_manifest(manifest)
    if generated.get("stage") != "GENERATE" or generated.get("status") != "GENERATE_SEALED_VERIFY_NOT_RUN":
        raise ValueError("expected a sealed GENERATE object")
    if generated.get("verify_run") or generated.get("admit_run"):
        raise ValueError("GENERATE object collapses stage firewall")
    if generated.get("manifest_canonical_sha256") != canonical_sha256(manifest):
        raise ValueError("GENERATE input manifest hash mismatch")
    if set(_rows_by_key(generated)) != set(_rows_by_key(manifest)):
        raise ValueError("GENERATE row identities differ from manifest")


def _satisfies(formula: Sequence[Sequence[int]], witness: Sequence[int]) -> bool:
    assignment = {abs(literal): literal > 0 for literal in witness}
    return all(any(assignment[abs(literal)] == (literal > 0) for literal in clause) for clause in formula)


def _carrier_counterprobe(
    formula: list[list[int]],
    active: dict,
    original_truth: str,
) -> dict:
    variables = sorted({abs(literal) for clause in formula for literal in clause})
    mapping = {variable: variables[-index - 1] for index, variable in enumerate(variables)}
    sequence = active["elimination_sequence"]
    transported_sequence = [mapping[variable] for variable in sequence]
    transported_formula = permute_formula(formula, mapping)
    baseline = execute_fixed_sequence(formula, sequence, cap=ACTIVE_CAP)
    transported = execute_fixed_sequence(transported_formula, transported_sequence, cap=ACTIVE_CAP)
    exact_keys = (
        "status",
        "generated_resolvents",
        "dp_pair_pressure_sum",
        "peak_live_clauses",
        "unit_assignments",
        "ssr_steps",
    )
    mismatches = {
        key: [baseline[key], transported[key]]
        for key in exact_keys
        if baseline[key] != transported[key]
    }
    active_prefix_matches = (
        baseline["generated_resolvents"] == active["generated_resolvents"]
        and baseline["dp_pair_pressure_sum"] == active["dp_pair_pressure_sum"]
        and baseline["peak_live_clauses"] == active["peak_live_clauses"]
    )
    transported_truth = brute_force_sat(transported_formula)[0]
    passed = not mismatches and active_prefix_matches and original_truth == transported_truth
    return {
        "mapping": mapping,
        "transported_sequence": transported_sequence,
        "baseline_fixed_sequence": baseline,
        "transported_fixed_sequence": transported,
        "active_prefix_matches": active_prefix_matches,
        "original_truth": original_truth,
        "transported_truth": transported_truth,
        "mismatches": mismatches,
        "passed": passed,
    }


def _verify_one(payload: tuple[dict, dict, frozenset[int]]) -> dict:
    manifest_row, generate_row, validation_n = payload
    active = generate_row["active"]
    truth_status, witness, assignments_tested = brute_force_sat(manifest_row["formula"])
    witness_valid = witness is None or _satisfies(manifest_row["formula"], witness)
    unsat_complete = truth_status != "UNSAT" or assignments_tested == 2 ** manifest_row["n"]
    diagnostic = independent_dp160(manifest_row["formula"], cap=INDEPENDENT_DP_CAP)
    carrier = (
        _carrier_counterprobe(manifest_row["formula"], active, truth_status)
        if manifest_row["n"] in validation_n
        else None
    )
    return {
        "block_id": manifest_row["block_id"],
        "n": manifest_row["n"],
        "formula_digest": manifest_row["generation_trace"]["formula_digest"],
        "truth": {
            "status": truth_status,
            "witness": witness,
            "assignments_tested": assignments_tested,
            "certificate_valid": witness_valid and unsat_complete,
        },
        "independent_dp160": diagnostic,
        "active_truth_resolved_agree": (
            active["status"] == "UNKNOWN" or active["status"] == truth_status
        ),
        "dp160_truth_resolved_agree": (
            diagnostic["status"] == "UNKNOWN" or diagnostic["status"] == truth_status
        ),
        "carrier_counterprobe": carrier,
    }


def run_verify(
    manifest: dict,
    generated: dict,
    validation_n: frozenset[int] = VALIDATION_N,
    workers: int | None = None,
) -> dict:
    """Run independent truth, bounded DP diagnostic, and carrier probes only."""
    _validate_generate(manifest, generated)
    manifest_rows = _rows_by_key(manifest)
    generate_rows = _rows_by_key(generated)
    rows = _ordered_map(
        _verify_one,
        [
            (manifest_rows[key], generate_rows[key], validation_n)
            for key in sorted(manifest_rows)
        ],
        workers,
    )
    return {
        "schema": "fig5-v025-width4-verify/v1",
        "experiment_id": EXPERIMENT_ID,
        "stage": "VERIFY",
        "status": "VERIFY_SEALED_ADMIT_NOT_RUN",
        "manifest_canonical_sha256": canonical_sha256(manifest),
        "generate_canonical_sha256": canonical_sha256(generated),
        "admission_authority": "complete brute-force truth enumeration on n<=13",
        "independent_dp_role": "cap-160 diagnostic only",
        "carrier_scope_n": sorted(validation_n),
        "rows": rows,
        "admit_run": False,
        "boundaries": [
            "INDEPENDENT_DP160_DIAGNOSTIC != ADMISSION_AUTHORITY",
            "VERIFY != ADMIT",
            "WIDTH4_BOUNDED_PROBE != ASYMPTOTIC_TRANSFER",
            "FIG5_RESULT != P_VS_NP_RESULT",
            "P ?= NP = OPEN",
        ],
    }


def _validate_verify(manifest: dict, generated: dict, verified: dict) -> None:
    _validate_generate(manifest, generated)
    if verified.get("stage") != "VERIFY" or verified.get("status") != "VERIFY_SEALED_ADMIT_NOT_RUN":
        raise ValueError("expected a sealed VERIFY object")
    if verified.get("admit_run"):
        raise ValueError("VERIFY object collapses stage firewall")
    if verified.get("manifest_canonical_sha256") != canonical_sha256(manifest):
        raise ValueError("VERIFY input manifest hash mismatch")
    if verified.get("generate_canonical_sha256") != canonical_sha256(generated):
        raise ValueError("VERIFY input GENERATE hash mismatch")
    if set(_rows_by_key(verified)) != set(_rows_by_key(manifest)):
        raise ValueError("VERIFY row identities differ from manifest")


def run_admit(manifest: dict, generated: dict, verified: dict) -> dict:
    """Apply the frozen admission rule; do not estimate or score predictors."""
    _validate_verify(manifest, generated, verified)
    generate_rows = _rows_by_key(generated)
    verify_rows = _rows_by_key(verified)
    rows: list[dict] = []
    for key in sorted(generate_rows):
        active = generate_rows[key]["active"]
        verification = verify_rows[key]
        admitted = (
            active["status"] in {"SAT", "UNSAT"}
            and verification["truth"]["certificate_valid"]
            and active["status"] == verification["truth"]["status"]
            and verification["active_truth_resolved_agree"]
        )
        reason = "ACTIVE_RESOLVED_EQUALS_COMPLETE_TRUTH" if admitted else "ACTIVE_UNRESOLVED_OR_DISAGREES"
        rows.append(
            {
                "block_id": key[0],
                "n": key[1],
                "formula_digest": generate_rows[key]["formula_digest"],
                "admitted": admitted,
                "reason": reason,
            }
        )
    return {
        "schema": "fig5-v025-width4-admit/v1",
        "experiment_id": EXPERIMENT_ID,
        "stage": "ADMIT",
        "status": "ADMIT_SEALED_ANALYSIS_NOT_RUN",
        "manifest_canonical_sha256": canonical_sha256(manifest),
        "generate_canonical_sha256": canonical_sha256(generated),
        "verify_canonical_sha256": canonical_sha256(verified),
        "rule": "admit iff active status is resolved and equals complete brute-force truth; provenance is frozen",
        "rows": rows,
        "analysis_run": False,
        "boundaries": [
            "ADMIT != ANALYZE",
            "WIDTH4_RESULT_NOT_YET_KNOWN",
            "FIG5_RESULT != P_VS_NP_RESULT",
            "P ?= NP = OPEN",
        ],
    }


def _validate_admit(manifest: dict, generated: dict, verified: dict, admitted: dict) -> None:
    _validate_verify(manifest, generated, verified)
    if admitted.get("stage") != "ADMIT" or admitted.get("status") != "ADMIT_SEALED_ANALYSIS_NOT_RUN":
        raise ValueError("expected a sealed ADMIT object")
    if admitted.get("analysis_run"):
        raise ValueError("ADMIT object collapses stage firewall")
    expected_hashes = {
        "manifest_canonical_sha256": canonical_sha256(manifest),
        "generate_canonical_sha256": canonical_sha256(generated),
        "verify_canonical_sha256": canonical_sha256(verified),
    }
    for field, expected in expected_hashes.items():
        if admitted.get(field) != expected:
            raise ValueError(f"ADMIT input hash mismatch: {field}")


def _median_fraction(values: Iterable[Fraction]) -> Fraction:
    materialized = list(values)
    if not materialized:
        raise ValueError("cannot estimate from zero rows")
    return statistics.median(materialized)


def _error(observed: int, predicted: Fraction) -> float:
    return abs(math.log1p(observed) - math.log1p(float(predicted)))


def _fit(calibration_keys: Sequence[tuple[int, int]], generate_rows: dict, admit_rows: dict) -> dict:
    eligible = [key for key in calibration_keys if admit_rows[key]["admitted"]]
    eta_rows = [key for key in eligible if generate_rows[key]["active"]["dp_pair_pressure_sum"] > 0]
    eta = (
        _median_fraction(
            Fraction(
                generate_rows[key]["active"]["generated_resolvents"],
                generate_rows[key]["active"]["dp_pair_pressure_sum"],
            )
            for key in eta_rows
        )
        if eta_rows
        else None
    )
    a_hat = (
        _median_fraction(
            Fraction(generate_rows[key]["active"]["generated_resolvents"], key[1])
            for key in eligible
        )
        if eligible
        else None
    )
    b_hat = (
        _median_fraction(
            Fraction(generate_rows[key]["active"]["generated_resolvents"], key[1] ** 2)
            for key in eligible
        )
        if eligible
        else None
    )
    return {
        "eta_hat": eta,
        "a_hat": a_hat,
        "b_hat": b_hat,
        "admitted_calibration_rows": len(eligible),
        "eta_positive_rows": len(eta_rows),
    }


def _serialize_fraction(value: Fraction | None) -> dict:
    if value is None:
        return {"exact": None, "float": None}
    return {"exact": str(value), "float": float(value)}


def _evaluate_level(
    n: int,
    keys: Sequence[tuple[int, int]],
    fit: dict,
    generate_rows: dict,
    admit_rows: dict,
    expected_count: int,
) -> dict:
    admitted_keys = [key for key in keys if admit_rows[key]["admitted"]]
    if any(fit[name] is None for name in ("eta_hat", "a_hat", "b_hat")):
        return {
            "n": n,
            "expected_admitted_rows": expected_count,
            "admitted_rows": len(admitted_keys),
            "row_errors": [],
            "passes": False,
            "failure": "CALIBRATION_ESTIMATOR_UNAVAILABLE",
        }
    row_errors: list[dict] = []
    for key in admitted_keys:
        active = generate_rows[key]["active"]
        observed = active["generated_resolvents"]
        predictions = {
            "chi": fit["eta_hat"] * active["dp_pair_pressure_sum"],
            "n": fit["a_hat"] * n,
            "n2": fit["b_hat"] * n * n,
        }
        row_errors.append(
            {
                "block_id": key[0],
                "n": n,
                "observed_R": observed,
                "P_DP": active["dp_pair_pressure_sum"],
                "predicted": {name: _serialize_fraction(value) for name, value in predictions.items()},
                "errors": {name: _error(observed, value) for name, value in predictions.items()},
            }
        )
    if len(row_errors) != expected_count:
        return {
            "n": n,
            "expected_admitted_rows": expected_count,
            "admitted_rows": len(row_errors),
            "row_errors": row_errors,
            "passes": False,
            "failure": "EXACT_ADMITTED_ROW_COUNT_NOT_MET",
        }
    medians = {
        name: statistics.median(row["errors"][name] for row in row_errors)
        for name in ("chi", "n", "n2")
    }
    return {
        "n": n,
        "expected_admitted_rows": expected_count,
        "admitted_rows": len(row_errors),
        "row_errors": row_errors,
        "median_E_chi": medians["chi"],
        "median_E_n": medians["n"],
        "median_E_n2": medians["n2"],
        "margin_vs_n": medians["n"] - medians["chi"],
        "margin_vs_n2": medians["n2"] - medians["chi"],
        "passes": medians["chi"] < medians["n"] and medians["chi"] < medians["n2"],
    }


def run_analyze(manifest: dict, generated: dict, verified: dict, admitted: dict) -> dict:
    """Fit and evaluate exactly the frozen preregistered estimators and rule."""
    _validate_admit(manifest, generated, verified, admitted)
    generate_rows = _rows_by_key(generated)
    admit_rows = _rows_by_key(admitted)
    calibration_keys = sorted(key for key in generate_rows if key[1] in CALIBRATION_N)
    fit = _fit(calibration_keys, generate_rows, admit_rows)
    validation = {
        str(n): _evaluate_level(
            n,
            sorted(key for key in generate_rows if key[1] == n),
            fit,
            generate_rows,
            admit_rows,
            expected_count=BLOCK_COUNT,
        )
        for n in sorted(VALIDATION_N)
    }
    success = all(result["passes"] for result in validation.values())
    all_validation_admitted = all(result["admitted_rows"] == BLOCK_COUNT for result in validation.values())
    if success:
        status = "WIDTH4_DENSITY4_BOUNDED_STRUCTURAL_COLLAPSE"
    elif not all_validation_admitted:
        status = "WIDTH4_DENSITY4_INCONCLUSIVE_ADMISSION"
    else:
        status = "WIDTH4_DENSITY4_PREREGISTERED_RULE_NOT_MET"
    return {
        "schema": "fig5-v025-width4-analysis/v1",
        "experiment_id": EXPERIMENT_ID,
        "stage": "ANALYZE",
        "status": status,
        "success": success,
        "inputs": {
            "manifest_canonical_sha256": canonical_sha256(manifest),
            "generate_canonical_sha256": canonical_sha256(generated),
            "verify_canonical_sha256": canonical_sha256(verified),
            "admit_canonical_sha256": canonical_sha256(admitted),
        },
        "calibration": {
            "eta_hat": _serialize_fraction(fit["eta_hat"]),
            "a_hat": _serialize_fraction(fit["a_hat"]),
            "b_hat": _serialize_fraction(fit["b_hat"]),
            "admitted_calibration_rows": fit["admitted_calibration_rows"],
            "eta_positive_rows": fit["eta_positive_rows"],
        },
        "validation": validation,
        "success_rule": "at each n in {11,12,13}, exactly five rows admitted and median E_chi < median E_n and median E_n2",
        "boundaries": [
            "WIDTH4_BOUNDED_RESULT != ASYMPTOTIC_LAW",
            "SURVIVAL_FRACTION_TRANSFER != INDEPENDENT_COMPLEXITY_LAW",
            "FINITE_FOUR_PANEL_RESULT != GENERAL_WIDTH_INVARIANCE",
            "FIG5_RESULT != P_VS_NP_RESULT",
            "P ?= NP = OPEN",
        ],
    }


def _cap80_one(manifest_row: dict) -> dict:
    result = asdict(active_dp(manifest_row["formula"], cap=80))
    return {
        "block_id": manifest_row["block_id"],
        "n": manifest_row["n"],
        "status": result["status"],
        "generated_resolvents": result["generated_resolvents"],
        "cap_crossing_at": result["cap_crossing_at"],
    }


def run_posthoc(
    manifest: dict,
    generated: dict,
    verified: dict,
    admitted: dict,
    workers: int | None = None,
) -> dict:
    """Run bounded diagnostics that cannot alter the preregistered result."""
    _validate_admit(manifest, generated, verified, admitted)
    manifest_rows = _rows_by_key(manifest)
    generate_rows = _rows_by_key(generated)
    admit_rows = _rows_by_key(admitted)

    omissions: list[dict] = []
    for omitted_block in range(BLOCK_COUNT):
        calibration_keys = sorted(
            key for key in generate_rows if key[0] != omitted_block and key[1] in CALIBRATION_N
        )
        fit = _fit(calibration_keys, generate_rows, admit_rows)
        validation = {
            str(n): _evaluate_level(
                n,
                sorted(key for key in generate_rows if key[0] != omitted_block and key[1] == n),
                fit,
                generate_rows,
                admit_rows,
                expected_count=BLOCK_COUNT - 1,
            )
            for n in sorted(VALIDATION_N)
        }
        omissions.append(
            {
                "omitted_block": omitted_block,
                "calibration": {
                    "eta_hat": _serialize_fraction(fit["eta_hat"]),
                    "a_hat": _serialize_fraction(fit["a_hat"]),
                    "b_hat": _serialize_fraction(fit["b_hat"]),
                },
                "validation": validation,
                "passes_all_three_levels": all(row["passes"] for row in validation.values()),
            }
        )

    cap80_rows = _ordered_map(
        _cap80_one,
        [manifest_rows[key] for key in sorted(manifest_rows)],
        workers,
    )

    identity_rows = []
    for key in sorted(generate_rows):
        active = generate_rows[key]["active"]
        pair_pressure = active["dp_pair_pressure_sum"]
        generated_count = active["generated_resolvents"]
        identity_rows.append(
            {
                "block_id": key[0],
                "n": key[1],
                "P_DP": pair_pressure,
                "R": generated_count,
                "T_taut": pair_pressure - generated_count,
                "identity_holds": pair_pressure >= generated_count,
            }
        )

    return {
        "schema": "fig5-v025-width4-posthoc/v1",
        "experiment_id": EXPERIMENT_ID,
        "stage": "POSTHOC",
        "status": "NON_PROMOTABLE_DIAGNOSTIC",
        "inputs": {
            "manifest_canonical_sha256": canonical_sha256(manifest),
            "generate_canonical_sha256": canonical_sha256(generated),
            "verify_canonical_sha256": canonical_sha256(verified),
            "admit_canonical_sha256": canonical_sha256(admitted),
        },
        "leave_one_block_out": {
            "omissions": omissions,
            "all_three_levels_pass_for_every_omission": all(
                omission["passes_all_three_levels"] for omission in omissions
            ),
        },
        "cap80_counterfactual": {
            "rows": cap80_rows,
            "status_counts": {
                status: sum(row["status"] == status for row in cap80_rows)
                for status in ("SAT", "UNSAT", "UNKNOWN")
            },
        },
        "pair_pressure_identity": {
            "rows": identity_rows,
            "all_executed_prefixes_hold": all(row["identity_holds"] for row in identity_rows),
            "meaning": "P_DP = R + T_taut for executed parent-pair prefixes",
        },
        "boundaries": [
            "POSTHOC_DIAGNOSTIC != PREREGISTERED_EVIDENCE",
            "CAP80_COUNTERFACTUAL != COMPLEXITY_BOUND",
            "WIDTH4_BOUNDED_RESULT != GENERAL_WIDTH_INVARIANCE",
            "FIG5_RESULT != P_VS_NP_RESULT",
            "P ?= NP = OPEN",
        ],
    }


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _emit(value: dict) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="stage", required=True)

    manifest_parser = subparsers.add_parser("manifest")
    manifest_parser.add_argument("--preregistration-commit", required=True)

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--manifest", required=True)
    generate_parser.add_argument("--workers", type=int)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--manifest", required=True)
    verify_parser.add_argument("--generate", required=True)
    verify_parser.add_argument("--workers", type=int)

    admit_parser = subparsers.add_parser("admit")
    admit_parser.add_argument("--manifest", required=True)
    admit_parser.add_argument("--generate", required=True)
    admit_parser.add_argument("--verify", required=True)

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--manifest", required=True)
    analyze_parser.add_argument("--generate", required=True)
    analyze_parser.add_argument("--verify", required=True)
    analyze_parser.add_argument("--admit", required=True)

    posthoc_parser = subparsers.add_parser("posthoc")
    posthoc_parser.add_argument("--manifest", required=True)
    posthoc_parser.add_argument("--generate", required=True)
    posthoc_parser.add_argument("--verify", required=True)
    posthoc_parser.add_argument("--admit", required=True)
    posthoc_parser.add_argument("--workers", type=int)

    arguments = parser.parse_args()
    if arguments.stage == "manifest":
        result = official_manifest(arguments.preregistration_commit)
    elif arguments.stage == "generate":
        result = run_generate(_load(arguments.manifest), workers=arguments.workers)
    elif arguments.stage == "verify":
        result = run_verify(
            _load(arguments.manifest),
            _load(arguments.generate),
            workers=arguments.workers,
        )
    elif arguments.stage == "admit":
        result = run_admit(
            _load(arguments.manifest),
            _load(arguments.generate),
            _load(arguments.verify),
        )
    elif arguments.stage == "analyze":
        result = run_analyze(
            _load(arguments.manifest),
            _load(arguments.generate),
            _load(arguments.verify),
            _load(arguments.admit),
        )
    else:
        result = run_posthoc(
            _load(arguments.manifest),
            _load(arguments.generate),
            _load(arguments.verify),
            _load(arguments.admit),
            workers=arguments.workers,
        )
    _emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
