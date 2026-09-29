from __future__ import annotations

"""FIG-5 v0.25 deterministic width-4, density-4 family constructor.

This is the constructor-only half of the preregistered one-degree probe.  It
changes clause width from the v0.24 width-3 baseline to width 4 while retaining
the density-4 target, n ladder, and bottom-priority ranking method.  Width-
specific family and priority identities are new on purpose; the priority
algorithm is unchanged.

No official seed is derived here.  No official formula is materialized here.
No solver, truth verifier, admission rule, or analysis is invoked here.
"""

import argparse
from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib
from itertools import combinations, product
import json
import math
from typing import Iterable, Sequence


FAMILY_VERSION = "FIG5-clause-priority-4cnf-density4/v0.25"
PRIORITY_NAMESPACE = "FIG5/CLAUSE-PRIORITY/4CNF/v0.25"
WIDTH = 4
TARGET_DENSITY_NUMERATOR = 4
TARGET_DENSITY_DENOMINATOR = 1
ALLOWED_N = (8, 9, 10, 11, 12, 13)
ALLOWED_N_SET = frozenset(ALLOWED_N)


class StructuralPreconditionFailure(RuntimeError):
    """The frozen constructor violated a preregistered structural condition."""


def _encode_part(part: object) -> bytes:
    if isinstance(part, bytes):
        return part
    return str(part).encode("utf-8")


def _update_hash_part(digest: object, part: object) -> None:
    encoded = _encode_part(part)
    digest.update(len(encoded).to_bytes(4, "big"))
    digest.update(encoded)


def _sha256_bytes(*parts: object) -> bytes:
    digest = hashlib.sha256()
    for part in parts:
        _update_hash_part(digest, part)
    return digest.digest()


def _priority_prefix(block_seed: str) -> object:
    digest = hashlib.sha256()
    _update_hash_part(digest, PRIORITY_NAMESPACE)
    _update_hash_part(digest, block_seed)
    return digest


def canonical_clause(clause: Iterable[int]) -> tuple[int, ...]:
    values = [int(value) for value in clause]
    if len(values) != WIDTH:
        raise ValueError(f"clause must contain exactly {WIDTH} literals")
    if any(value == 0 for value in values):
        raise ValueError("literal 0 is invalid")
    if len({abs(value) for value in values}) != WIDTH:
        raise ValueError(f"clause must use {WIDTH} distinct variable identities")
    return tuple(sorted(values, key=lambda value: (abs(value), value < 0)))


def canonical_formula(clauses: Iterable[Iterable[int]]) -> tuple[tuple[int, ...], ...]:
    normalized = [canonical_clause(clause) for clause in clauses]
    if len(set(normalized)) != len(normalized):
        raise ValueError("duplicate canonical clause")
    return tuple(sorted(normalized))


@lru_cache(maxsize=None)
def _canonical_clause_bytes_tuple(normalized: tuple[int, ...]) -> bytes:
    return json.dumps(list(normalized), separators=(",", ":"), ensure_ascii=True).encode("ascii")


def canonical_clause_bytes(clause: Sequence[int]) -> bytes:
    return _canonical_clause_bytes_tuple(canonical_clause(clause))


def _validate_n(n: int) -> None:
    if not isinstance(n, int) or isinstance(n, bool) or n not in ALLOWED_N_SET:
        raise ValueError(f"n must be one of the frozen FIG-5 levels {list(ALLOWED_N)}")


def target_clause_count(n: int) -> int:
    """Return the exact frozen density-4 target clause count, 4n."""
    _validate_n(n)
    numerator = TARGET_DENSITY_NUMERATOR * n
    quotient, remainder = divmod(numerator, TARGET_DENSITY_DENOMINATOR)
    return quotient + (1 if 2 * remainder >= TARGET_DENSITY_DENOMINATOR else 0)


def realized_density(n: int) -> tuple[int, int]:
    """Return the exact realized density numerator and denominator."""
    return target_clause_count(n), n


@lru_cache(maxsize=None)
def clause_universe(n: int) -> tuple[tuple[int, ...], ...]:
    """Return the complete canonical non-tautological width-4 universe."""
    _validate_n(n)
    clauses: list[tuple[int, ...]] = []
    for variables in combinations(range(1, n + 1), WIDTH):
        for signs in product((-1, 1), repeat=WIDTH):
            clauses.append(
                canonical_clause(sign * variable for sign, variable in zip(signs, variables))
            )
    return tuple(clauses)


def clause_priority(block_seed: str, clause: Sequence[int]) -> bytes:
    if not isinstance(block_seed, str) or not block_seed:
        raise ValueError("block_seed must be a non-empty string")
    digest = _priority_prefix(block_seed)
    _update_hash_part(digest, canonical_clause_bytes(clause))
    return digest.digest()


def formula_digest(clauses: Sequence[Sequence[int]]) -> str:
    normalized = canonical_formula(clauses)
    payload = json.dumps([list(clause) for clause in normalized], separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


@dataclass(frozen=True)
class GenerationTrace:
    family_version: str
    block_seed: str
    n: int
    width: int
    target_density_numerator: int
    target_density_denominator: int
    target_clause_count: int
    realized_density_numerator: int
    realized_density_denominator: int
    eligible_clause_universe_size: int
    active_variable_count: int
    priority_hash_collision_count: int
    formula_digest: str


def generate_formula(block_seed: str, n: int) -> tuple[tuple[tuple[int, ...], ...], GenerationTrace]:
    """Generate one member without solver, verifier, or admission feedback."""
    _validate_n(n)
    if not isinstance(block_seed, str) or not block_seed:
        raise ValueError("block_seed must be a non-empty string")

    universe = clause_universe(n)
    target = target_clause_count(n)
    if target > len(universe):
        raise StructuralPreconditionFailure("target clause count exceeds finite clause universe")

    ranked: list[tuple[bytes, bytes, tuple[int, ...]]] = []
    digest_counts: dict[bytes, int] = {}
    for clause in universe:
        priority = clause_priority(block_seed, clause)
        serialized = canonical_clause_bytes(clause)
        ranked.append((priority, serialized, clause))
        digest_counts[priority] = digest_counts.get(priority, 0) + 1

    ranked.sort(key=lambda item: (item[0], item[1]))
    formula = canonical_formula(item[2] for item in ranked[:target])

    active = {abs(literal) for clause in formula for literal in clause}
    expected = set(range(1, n + 1))
    if active != expected:
        raise StructuralPreconditionFailure(
            f"frozen seed failed exact active support at n={n}; missing={sorted(expected - active)}"
        )

    collision_count = sum(count - 1 for count in digest_counts.values() if count > 1)
    realized_numerator, realized_denominator = realized_density(n)
    trace = GenerationTrace(
        family_version=FAMILY_VERSION,
        block_seed=block_seed,
        n=n,
        width=WIDTH,
        target_density_numerator=TARGET_DENSITY_NUMERATOR,
        target_density_denominator=TARGET_DENSITY_DENOMINATOR,
        target_clause_count=target,
        realized_density_numerator=realized_numerator,
        realized_density_denominator=realized_denominator,
        eligible_clause_universe_size=len(universe),
        active_variable_count=len(active),
        priority_hash_collision_count=collision_count,
        formula_digest=formula_digest(formula),
    )
    return formula, trace


def generate_block(
    block_seed: str,
    n_levels: Sequence[int] = ALLOWED_N,
) -> tuple[dict[int, tuple[tuple[tuple[int, ...], ...], GenerationTrace]], dict]:
    """Generate a block with one priority pass and one sort over its maximum universe.

    Every lower-n universe is an eligibility subset of the maximum universe.
    Filtering a single globally ranked list therefore produces exactly the same
    bottom-priority formulas as ranking every lower universe independently.
    """
    if not isinstance(block_seed, str) or not block_seed:
        raise ValueError("block_seed must be a non-empty string")
    levels = tuple(sorted(set(n_levels)))
    if not levels:
        raise ValueError("n_levels must be non-empty")
    for n in levels:
        _validate_n(n)

    maximum_n = max(levels)
    universe = clause_universe(maximum_n)
    ranked: list[tuple[bytes, bytes, tuple[int, ...]]] = []
    priority_prefix = _priority_prefix(block_seed)
    for clause in universe:
        serialized = canonical_clause_bytes(clause)
        priority_hash = priority_prefix.copy()
        _update_hash_part(priority_hash, serialized)
        priority = priority_hash.digest()
        ranked.append((priority, serialized, clause))
    ranked.sort(key=lambda item: (item[0], item[1]))

    results: dict[int, tuple[tuple[tuple[int, ...], ...], GenerationTrace]] = {}
    for n in levels:
        target = target_clause_count(n)
        selected: list[tuple[int, ...]] = []
        for _, _, clause in ranked:
            if abs(clause[-1]) <= n:
                selected.append(clause)
                if len(selected) == target:
                    break
        if len(selected) != target:
            raise StructuralPreconditionFailure("target clause count exceeds finite clause universe")
        formula = canonical_formula(selected)
        active = {abs(literal) for clause in formula for literal in clause}
        expected = set(range(1, n + 1))
        if active != expected:
            raise StructuralPreconditionFailure(
                f"frozen seed failed exact active support at n={n}; missing={sorted(expected - active)}"
            )
        eligible_digest_counts: dict[bytes, int] = {}
        for priority, _, clause in ranked:
            if abs(clause[-1]) <= n:
                eligible_digest_counts[priority] = eligible_digest_counts.get(priority, 0) + 1
        collision_count = sum(
            count - 1 for count in eligible_digest_counts.values() if count > 1
        )
        realized_numerator, realized_denominator = realized_density(n)
        trace = GenerationTrace(
            family_version=FAMILY_VERSION,
            block_seed=block_seed,
            n=n,
            width=WIDTH,
            target_density_numerator=TARGET_DENSITY_NUMERATOR,
            target_density_denominator=TARGET_DENSITY_DENOMINATOR,
            target_clause_count=target,
            realized_density_numerator=realized_numerator,
            realized_density_denominator=realized_denominator,
            eligible_clause_universe_size=16 * math.comb(n, WIDTH),
            active_variable_count=len(active),
            priority_hash_collision_count=collision_count,
            formula_digest=formula_digest(formula),
        )
        results[n] = formula, trace

    return results, {
        "maximum_n": maximum_n,
        "priority_evaluations": len(universe),
        "sort_count": 1,
        "level_count": len(levels),
    }


def describe_contract() -> dict:
    return {
        "family_version": FAMILY_VERSION,
        "construction": "finite_clause_universe_bottom_priority",
        "changed_scientific_degree": "clause width 3 -> 4",
        "changing_degree_within_block": "n only",
        "allowed_n": list(ALLOWED_N),
        "block_seed_rule": "EXTERNAL_INPUT_NOT_FROZEN_HERE",
        "width": WIDTH,
        "target_density_parameter": f"{TARGET_DENSITY_NUMERATOR}/{TARGET_DENSITY_DENOMINATOR}",
        "clause_count_law": "4*n",
        "realized_density_rule": "target_clause_count(n)/n; exactly 4 for every allowed n",
        "active_variable_coverage": "required exact 1..n; failure is fail-closed, never repaired",
        "priority_method": "SHA256(length-prefixed namespace, block seed, canonical clause bytes)",
        "priority_namespace": PRIORITY_NAMESPACE,
        "selection": "lowest target_clause_count(n) priorities; digest bytes then canonical clause bytes tie-break",
        "generation_feedback": "NONE_FROM_SOLVER_OR_VERIFIER",
        "termination": "finite enumeration and finite sort only; no retry loop",
        "eligible_universe_size": "16*C(n,4)",
        "nested": False,
        "reason_not_nested": "newly eligible clauses may outrank old clauses",
        "boundaries": [
            "WIDTH4_IDENTITY != WIDTH3_IDENTITY",
            "RANKING_METHOD_FROZEN != PRIORITY_NAMESPACE_REUSED",
            "CONSTRUCTOR_FROZEN != OFFICIAL_SEEDS_MATERIALIZED",
            "SOFTWARE_SELF_TEST != OFFICIAL_FAMILY_EXECUTION",
            "GENERATE != VERIFY != ADMIT",
            "WIDTH4_BOUNDED_PROBE != ASYMPTOTIC_CLAIM",
            "FIG5_RESULT != P_VS_NP_RESULT",
            "P ?= NP = OPEN",
        ],
    }


def self_test(stress_seed_count: int = 256) -> dict:
    test_seed = "TEST-ONLY-WIDTH4-NOT-A-FIG5-BLOCK"
    traces: list[dict] = []

    for bad_n in (3, 4, 7, 14, 100, True):
        try:
            generate_formula(test_seed, bad_n)
        except ValueError:
            pass
        else:
            raise AssertionError(f"out-of-domain n unexpectedly accepted: {bad_n!r}")

    for n in ALLOWED_N:
        first_formula, first_trace = generate_formula(test_seed, n)
        second_formula, second_trace = generate_formula(test_seed, n)
        assert first_formula == second_formula
        assert asdict(first_trace) == asdict(second_trace)
        assert len(first_formula) == 4 * n
        assert first_trace.eligible_clause_universe_size == 16 * math.comb(n, WIDTH)
        assert {abs(literal) for clause in first_formula for literal in clause} == set(range(1, n + 1))
        assert all(len(clause) == WIDTH for clause in first_formula)
        traces.append(asdict(first_trace))

    witness = canonical_clause((1, -2, 3, -4))
    priority = clause_priority(test_seed, witness)
    assert all(clause_priority(test_seed, witness) == priority for _ in ALLOWED_N)

    first, _ = generate_formula("TEST-WIDTH4-SEED-A", 10)
    second, _ = generate_formula("TEST-WIDTH4-SEED-B", 10)
    assert first != second

    structural_failures: list[dict] = []
    max_priority_collisions = 0
    for seed_index in range(stress_seed_count):
        seed = f"STRESS-WIDTH4-NOT-FIG5-{seed_index:04d}"
        try:
            generated, _ = generate_block(seed, ALLOWED_N)
            for n, (_, trace) in generated.items():
                max_priority_collisions = max(max_priority_collisions, trace.priority_hash_collision_count)
        except StructuralPreconditionFailure as error:
            structural_failures.append({"seed_index": seed_index, "error": str(error)})
    assert not structural_failures, structural_failures[:10]

    return {
        "status": "PASS",
        "tests": {
            "allowed_levels": list(ALLOWED_N),
            "closed_n_domain": True,
            "determinism": True,
            "exact_active_variable_coverage": True,
            "all_clauses_width_4_distinct_variables": True,
            "target_clause_count_law_4n": True,
            "finite_clause_universe_size_16_choose_n4": True,
            "same_clause_priority_invariant_across_n": True,
            "seed_changes_output": True,
            "stress_test_seed_count": stress_seed_count,
            "stress_formula_count": stress_seed_count * len(ALLOWED_N),
            "batch_priority_evaluations_per_seed": 16 * math.comb(max(ALLOWED_N), WIDTH),
            "batch_sort_count_per_seed": 1,
            "stress_structural_failures": len(structural_failures),
            "max_sha256_priority_collisions_observed": max_priority_collisions,
        },
        "traces": traces,
        "claim_ceiling": [
            "SYNTHETIC_STRESS != OFFICIAL_SEED_VALIDITY",
            "SOFTWARE_SELF_TEST != OFFICIAL_FAMILY_EXECUTION",
            "GENERATE != VERIFY != ADMIT",
            "FIG5_RESULT != P_VS_NP_RESULT",
            "P ?= NP = OPEN",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--describe", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--stress-seeds", type=int, default=256)
    parser.add_argument("--test-formula", type=int, metavar="N")
    arguments = parser.parse_args()

    if arguments.describe:
        print(json.dumps(describe_contract(), indent=2, sort_keys=True))
    if arguments.self_test:
        print(json.dumps(self_test(arguments.stress_seeds), indent=2, sort_keys=True))
    if arguments.test_formula is not None:
        formula, trace = generate_formula(test_seed := "TEST-ONLY-WIDTH4-NOT-A-FIG5-BLOCK", arguments.test_formula)
        print(json.dumps({"test_seed": test_seed, "trace": asdict(trace), "clauses": formula}, indent=2, sort_keys=True))
    if not (arguments.describe or arguments.self_test or arguments.test_formula is not None):
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
