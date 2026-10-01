from __future__ import annotations

"""FIG-5 v0.17 deterministic clause-priority family constructor.

Purpose
-------
Freeze only the scientific family constructor. This module deliberately does
NOT derive the five official FIG-5 block seeds, materialize the 30-row manifest,
run Davis-Putnam, call the independent oracle, or admit any row.

The constructor assigns one n-independent deterministic priority to every
canonical non-tautological width-3 clause under an external block seed. For a
requested n in the frozen FIG-5 ladder, it enumerates the complete eligible
clause universe over variables 1..n and selects the target number of
lowest-priority clauses.

This removes modulo projection, duplicate-retry loops, coverage scaffolds, and
unbounded candidate generation from v0.16 while preserving a common random
ranking across n.
"""

from dataclasses import dataclass, asdict
from itertools import combinations, product
import argparse
import hashlib
import json
from typing import Iterable, Sequence

FAMILY_VERSION = "FIG5-clause-priority-3cnf/v0.17"
PRIORITY_NAMESPACE = "FIG5/CLAUSE-PRIORITY/v0.17"
WIDTH = 3
TARGET_DENSITY_NUMERATOR = 7
TARGET_DENSITY_DENOMINATOR = 2
ALLOWED_N = (8, 9, 10, 11, 12, 13)
ALLOWED_N_SET = frozenset(ALLOWED_N)


class StructuralPreconditionFailure(RuntimeError):
    """Frozen constructor produced a formula that violates a preregistered structural precondition."""


def _encode_part(part: object) -> bytes:
    if isinstance(part, bytes):
        return part
    return str(part).encode("utf-8")


def _sha256_bytes(*parts: object) -> bytes:
    h = hashlib.sha256()
    for part in parts:
        b = _encode_part(part)
        h.update(len(b).to_bytes(4, "big"))
        h.update(b)
    return h.digest()


def canonical_clause(clause: Iterable[int]) -> tuple[int, ...]:
    values = [int(x) for x in clause]
    if len(values) != WIDTH:
        raise ValueError(f"clause must contain exactly {WIDTH} literals")
    if any(x == 0 for x in values):
        raise ValueError("literal 0 is invalid")
    if len({abs(x) for x in values}) != WIDTH:
        raise ValueError("clause must use three distinct variable identities")
    return tuple(sorted(values, key=lambda z: (abs(z), z < 0)))


def canonical_formula(clauses: Iterable[Iterable[int]]) -> tuple[tuple[int, ...], ...]:
    normalized = [canonical_clause(c) for c in clauses]
    if len(set(normalized)) != len(normalized):
        raise ValueError("duplicate canonical clause")
    return tuple(sorted(normalized))


def canonical_clause_bytes(clause: Sequence[int]) -> bytes:
    c = canonical_clause(clause)
    return json.dumps(list(c), separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _validate_n(n: int) -> None:
    if not isinstance(n, int) or isinstance(n, bool) or n not in ALLOWED_N_SET:
        raise ValueError(f"n must be one of the frozen FIG-5 levels {list(ALLOWED_N)}")


def target_clause_count(n: int) -> int:
    """Round target density 7n/2 to nearest integer, half upward, exactly."""
    _validate_n(n)
    numerator = TARGET_DENSITY_NUMERATOR * n
    q, r = divmod(numerator, TARGET_DENSITY_DENOMINATOR)
    return q + (1 if 2 * r >= TARGET_DENSITY_DENOMINATOR else 0)


def realized_density(n: int) -> tuple[int, int]:
    """Return exact realized density as (clause_count, n), not as the target 7/2 label."""
    return target_clause_count(n), n


def clause_universe(n: int) -> tuple[tuple[int, ...], ...]:
    """Complete canonical non-tautological width-3 universe over variables 1..n."""
    _validate_n(n)
    clauses: list[tuple[int, ...]] = []
    for a, b, c in combinations(range(1, n + 1), WIDTH):
        for signs in product((-1, 1), repeat=WIDTH):
            clauses.append(canonical_clause((signs[0] * a, signs[1] * b, signs[2] * c)))
    return tuple(clauses)


def clause_priority(block_seed: str, clause: Sequence[int]) -> bytes:
    if not isinstance(block_seed, str) or not block_seed:
        raise ValueError("block_seed must be a non-empty string")
    return _sha256_bytes(PRIORITY_NAMESPACE, block_seed, canonical_clause_bytes(clause))


def formula_digest(clauses: Sequence[Sequence[int]]) -> str:
    cs = canonical_formula(clauses)
    payload = json.dumps([list(c) for c in cs], separators=(",", ":"), ensure_ascii=True)
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
    """Generate one test/future FIG-5 family member without solver/verifier feedback."""
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
        digest = clause_priority(block_seed, clause)
        serial = canonical_clause_bytes(clause)
        ranked.append((digest, serial, clause))
        digest_counts[digest] = digest_counts.get(digest, 0) + 1

    ranked.sort(key=lambda item: (item[0], item[1]))
    selected = [item[2] for item in ranked[:target]]
    formula = canonical_formula(selected)

    active = {abs(lit) for clause in formula for lit in clause}
    expected = set(range(1, n + 1))
    if active != expected:
        missing = sorted(expected - active)
        raise StructuralPreconditionFailure(
            f"frozen seed failed exact active support at n={n}; missing={missing}"
        )

    collision_count = sum(count - 1 for count in digest_counts.values() if count > 1)
    rnum, rden = realized_density(n)
    trace = GenerationTrace(
        family_version=FAMILY_VERSION,
        block_seed=block_seed,
        n=n,
        width=WIDTH,
        target_density_numerator=TARGET_DENSITY_NUMERATOR,
        target_density_denominator=TARGET_DENSITY_DENOMINATOR,
        target_clause_count=target,
        realized_density_numerator=rnum,
        realized_density_denominator=rden,
        eligible_clause_universe_size=len(universe),
        active_variable_count=len(active),
        priority_hash_collision_count=collision_count,
        formula_digest=formula_digest(formula),
    )
    return formula, trace


def describe_contract() -> dict:
    return {
        "family_version": FAMILY_VERSION,
        "construction": "finite_clause_universe_bottom_priority",
        "changing_degree_within_block": "n only",
        "allowed_n": list(ALLOWED_N),
        "block_seed_rule": "EXTERNAL_INPUT_NOT_FROZEN_HERE",
        "width": WIDTH,
        "target_density_parameter": f"{TARGET_DENSITY_NUMERATOR}/{TARGET_DENSITY_DENOMINATOR}",
        "clause_count_law": "round_half_up((7/2)*n)",
        "realized_density_rule": "target_clause_count(n)/n; odd n is not exactly 7/2",
        "active_variable_coverage": "required exact 1..n; failure is fail-closed, never repaired",
        "common_random_object": "n-independent SHA-256 priority for each canonical eligible clause",
        "priority_namespace": PRIORITY_NAMESPACE,
        "selection": "lowest target_clause_count(n) priorities; digest bytes then canonical clause bytes tie-break",
        "generation_feedback": "NONE_FROM_SOLVER_OR_VERIFIER",
        "termination": "finite enumeration and finite sort only; no unbounded candidate/retry loop",
        "nested": False,
        "reason_not_nested": "newly eligible clauses may outrank old clauses; common priority is preserved but membership may change",
        "boundaries": [
            "CONSTRUCTOR_FROZEN != BLOCK_SEED_RULE_FROZEN",
            "SOFTWARE_SELF_TEST != FAMILY_EXECUTION",
            "FAMILY_GENERATION != VERIFY != ADMIT",
            "TARGET_DENSITY_PARAMETER != REALIZED_DENSITY_AT_ODD_N",
            "COMMON_PRIORITY != NESTED_MEMBERSHIP",
            "ANCHOR_SIZE_CENTER != ANCHOR_FORMULA_MEMBER",
            "P ?= NP = OPEN",
        ],
    }


def self_test(stress_seed_count: int = 256) -> dict:
    # No official FIG-5 block seeds are derived here.
    test_seed = "TEST-ONLY-NOT-A-FIG5-BLOCK"
    traces = []

    # Contract description must itself execute.
    description = describe_contract()
    assert description["family_version"] == FAMILY_VERSION

    # Frozen level domain closes the v0.16 n=3 nontermination hole.
    for bad_n in (3, 4, 7, 14, 100):
        try:
            generate_formula(test_seed, bad_n)
        except ValueError:
            pass
        else:
            raise AssertionError(f"out-of-domain n unexpectedly accepted: {bad_n}")

    # Determinism, width, support, count, and finite universe law.
    for n in ALLOWED_N:
        f1, t1 = generate_formula(test_seed, n)
        f2, t2 = generate_formula(test_seed, n)
        assert f1 == f2
        assert asdict(t1) == asdict(t2)
        assert len(f1) == target_clause_count(n)
        assert {abs(lit) for c in f1 for lit in c} == set(range(1, n + 1))
        assert all(len(c) == WIDTH and len({abs(x) for x in c}) == WIDTH for c in f1)
        assert t1.eligible_clause_universe_size == 8 * (n * (n - 1) * (n - 2) // 6)
        traces.append(asdict(t1))

    # Same seed, same clause: priority is invariant across n because n is not an input.
    witness_clause = canonical_clause((1, -2, 3))
    priority_once = clause_priority(test_seed, witness_clause)
    for n in ALLOWED_N:
        assert set(map(abs, witness_clause)).issubset(set(range(1, n + 1)))
        assert clause_priority(test_seed, witness_clause) == priority_once

    # Different external seed changes at least one formula.
    a, _ = generate_formula("TEST-SEED-A", 10)
    b, _ = generate_formula("TEST-SEED-B", 10)
    assert a != b

    # Bounded synthetic stress only. Any support failure is evidence against the candidate constructor.
    structural_failures: list[dict] = []
    max_priority_collisions = 0
    for seed_index in range(stress_seed_count):
        seed = f"STRESS-ONLY-NOT-FIG5-{seed_index:04d}"
        for n in ALLOWED_N:
            try:
                _, trace = generate_formula(seed, n)
                max_priority_collisions = max(max_priority_collisions, trace.priority_hash_collision_count)
            except StructuralPreconditionFailure as exc:
                structural_failures.append({"seed_index": seed_index, "n": n, "error": str(exc)})

    assert not structural_failures, structural_failures[:10]

    return {
        "status": "PASS",
        "tests": {
            "allowed_levels": list(ALLOWED_N),
            "describe_contract_executes": True,
            "closed_n_domain": True,
            "determinism": True,
            "exact_active_variable_coverage": True,
            "all_clauses_width_3_distinct_variables": True,
            "target_clause_count_law": True,
            "finite_clause_universe_size": True,
            "same_clause_priority_invariant_across_n": True,
            "seed_changes_output": True,
            "stress_test_seed_count": stress_seed_count,
            "stress_formula_count": stress_seed_count * len(ALLOWED_N),
            "stress_structural_failures": len(structural_failures),
            "max_sha256_priority_collisions_observed": max_priority_collisions,
        },
        "traces": traces,
        "claim_ceiling": [
            "SOFTWARE_SELF_TEST != FIG5_FAMILY_EXECUTION",
            "SYNTHETIC_STRESS != OFFICIAL_SEED_VALIDITY",
            "CONSTRUCTOR_FROZEN != BLOCK_SEED_RULE_FROZEN",
            "GENERATE != VERIFY != ADMIT",
            "P ?= NP = OPEN",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--describe", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--stress-seeds", type=int, default=256)
    ap.add_argument("--test-formula", type=int, metavar="N",
                    help="emit a TEST-ONLY formula at N; not an official FIG-5 block")
    args = ap.parse_args()

    if args.describe:
        print(json.dumps(describe_contract(), indent=2, sort_keys=True))
    if args.self_test:
        print(json.dumps(self_test(args.stress_seeds), indent=2, sort_keys=True))
    if args.test_formula is not None:
        f, t = generate_formula("TEST-ONLY-NOT-A-FIG5-BLOCK", args.test_formula)
        print(json.dumps({"trace": asdict(t), "clauses": [list(c) for c in f]}, indent=2, sort_keys=True))
    if not (args.describe or args.self_test or args.test_formula is not None):
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
