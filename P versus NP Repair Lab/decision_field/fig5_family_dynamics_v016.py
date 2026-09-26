from __future__ import annotations

"""FIG-5 v0.16 deterministic family dynamics.

Purpose
-------
Freeze the scientific family constructor only.  This module deliberately does
NOT choose the five FIG-5 block seeds, materialize the 30-row manifest, run the
Davis-Putnam generator, call the independent oracle, or admit any row.

The constructor implements the FIG-5 fallback family rule:

    same block seed + same common hash stream + same generator law; only n varies.

No Python PRNG semantics are relied upon.  SHA-256 is the only stream primitive.
"""

from dataclasses import dataclass, asdict
import argparse
import hashlib
import json
from typing import Iterable, Sequence

FAMILY_VERSION = "FIG5-common-stream-3cnf/v0.16"
WIDTH = 3
# Exact rational density inherited as an explicit design choice from the
# retained v0.10 anchor's 35 canonical clauses / 10 active variables.
DENSITY_NUMERATOR = 7
DENSITY_DENOMINATOR = 2
MIN_N = 3


def _sha256_bytes(*parts: object) -> bytes:
    h = hashlib.sha256()
    for part in parts:
        b = str(part).encode("utf-8")
        h.update(len(b).to_bytes(4, "big"))
        h.update(b)
    return h.digest()


def _sha256_hex(*parts: object) -> str:
    return hashlib.sha256(b"".join(
        len(str(p).encode("utf-8")).to_bytes(4, "big") + str(p).encode("utf-8")
        for p in parts
    )).hexdigest()


def canonical_clause(clause: Iterable[int]) -> tuple[int, ...]:
    s = {int(x) for x in clause}
    if 0 in s:
        raise ValueError("literal 0 is invalid")
    if any(-x in s for x in s):
        raise ValueError("tautological clause is forbidden")
    return tuple(sorted(s, key=lambda z: (abs(z), z < 0)))


def canonical_formula(clauses: Iterable[Iterable[int]]) -> tuple[tuple[int, ...], ...]:
    cs = {canonical_clause(c) for c in clauses}
    return tuple(sorted(cs, key=lambda c: (len(c), c)))


def target_clause_count(n: int) -> int:
    """Round 7n/2 to nearest integer, half upward, using integer arithmetic."""
    _validate_n(n)
    num = DENSITY_NUMERATOR * n
    q, r = divmod(num, DENSITY_DENOMINATOR)
    return q + (1 if 2 * r >= DENSITY_DENOMINATOR else 0)


def _validate_n(n: int) -> None:
    if not isinstance(n, int) or n < MIN_N:
        raise ValueError(f"n must be an integer >= {MIN_N}")


def _uniform_index(seed: str, n: int, namespace: str, item: int, slot: int, retry: int = 0) -> int:
    """Deterministic rejection-sampled index in [0,n), avoiding modulo bias."""
    _validate_n(n)
    counter = retry
    modulus = 1 << 64
    limit = modulus - (modulus % n)
    while True:
        d = _sha256_bytes(FAMILY_VERSION, seed, namespace, item, slot, counter)
        value = int.from_bytes(d[:8], "big")
        if value < limit:
            return value % n
        counter += 1


def _bit(seed: str, namespace: str, item: int, slot: int) -> int:
    return _sha256_bytes(FAMILY_VERSION, seed, namespace, item, slot)[0] & 1


def _permutation(seed: str, n: int) -> list[int]:
    """Hash-keyed carrier permutation used only to guarantee active-variable coverage."""
    _validate_n(n)
    keyed = []
    for v in range(1, n + 1):
        keyed.append((_sha256_bytes(FAMILY_VERSION, seed, "coverage-order", v), v))
    keyed.sort(key=lambda x: (x[0], x[1]))
    return [v for _, v in keyed]


def _coverage_clauses(seed: str, n: int) -> list[tuple[int, ...]]:
    """Small deterministic activation scaffold so Var(F)=1..n exactly."""
    order = _permutation(seed, n)
    out: list[tuple[int, ...]] = []
    group = 0
    for start in range(0, n, WIDTH):
        vars_ = order[start:start + WIDTH]
        if len(vars_) < WIDTH:
            # Deterministically pad from the same permutation without repeats.
            for v in order:
                if v not in vars_:
                    vars_.append(v)
                if len(vars_) == WIDTH:
                    break
        lits = []
        for slot, v in enumerate(vars_):
            sign = 1 if _bit(seed, "coverage-sign", group, slot) else -1
            lits.append(sign * v)
        out.append(canonical_clause(lits))
        group += 1
    return out


def _stream_clause(seed: str, n: int, candidate_index: int) -> tuple[int, ...]:
    # Select variable identity first; sign is a carrier attribute applied only
    # after the three distinct absolute variables are fixed.
    selected_vars: list[int] = []
    for slot in range(WIDTH):
        retry = 0
        while True:
            v = 1 + _uniform_index(seed, n, "stream-var", candidate_index, slot, retry)
            if v not in selected_vars:
                selected_vars.append(v)
                break
            retry += 1

    literals: list[int] = []
    for slot, v in enumerate(selected_vars):
        sign = 1 if _bit(seed, "stream-sign", candidate_index, slot) else -1
        literals.append(sign * v)
    return canonical_clause(literals)


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
    density_numerator: int
    density_denominator: int
    target_clause_count: int
    coverage_clause_count: int
    stream_candidates_consumed: int
    duplicate_candidates_rejected: int
    active_variable_count: int
    formula_digest: str


def generate_formula(block_seed: str, n: int) -> tuple[tuple[tuple[int, ...], ...], GenerationTrace]:
    """Generate one FIG-5 family member without solver/verifier feedback."""
    _validate_n(n)
    if not isinstance(block_seed, str) or not block_seed:
        raise ValueError("block_seed must be a non-empty string")

    target = target_clause_count(n)
    clauses = list(_coverage_clauses(block_seed, n))
    seen = set(clauses)
    if len(seen) != len(clauses):
        # Extremely conservative: duplicates in the coverage scaffold are not silently repaired.
        raise RuntimeError("coverage scaffold collision; choose a different block seed")

    candidate_index = 0
    duplicates = 0
    while len(seen) < target:
        c = _stream_clause(block_seed, n, candidate_index)
        candidate_index += 1
        if c in seen:
            duplicates += 1
            continue
        seen.add(c)

    cs = canonical_formula(seen)
    active = {abs(l) for c in cs for l in c}
    expected = set(range(1, n + 1))
    if active != expected:
        raise AssertionError("constructor failed active-variable coverage invariant")
    if any(len(c) != WIDTH for c in cs):
        raise AssertionError("constructor violated frozen width")
    if len(cs) != target:
        raise AssertionError("constructor violated frozen clause-count law")

    trace = GenerationTrace(
        family_version=FAMILY_VERSION,
        block_seed=block_seed,
        n=n,
        width=WIDTH,
        density_numerator=DENSITY_NUMERATOR,
        density_denominator=DENSITY_DENOMINATOR,
        target_clause_count=target,
        coverage_clause_count=len(_coverage_clauses(block_seed, n)),
        stream_candidates_consumed=candidate_index,
        duplicate_candidates_rejected=duplicates,
        active_variable_count=len(active),
        formula_digest=formula_digest(cs),
    )
    return cs, trace


def describe_contract() -> dict:
    return {
        "family_version": FAMILY_VERSION,
        "construction": "fallback_common_hash_stream",
        "changing_degree_within_block": "n only",
        "block_seed_rule": "EXTERNAL_INPUT_NOT_FROZEN_HERE",
        "width": WIDTH,
        "clause_density": f"{DENSITY_NUMERATOR}/{DENSITY_DENOMATOR}",
        "clause_count_law": "round_half_up((7/2)*n)",
        "active_variable_coverage": "required exact 1..n",
        "stream": "SHA-256 domain-separated deterministic stream",
        "generation_feedback": "NONE_FROM_SOLVER_OR_VERIFIER",
        "nested": False,
        "reason_not_nested": "parity-extension nesting would hold the semantic core fixed and confound primary family growth with carrier growth",
        "boundaries": [
            "CONSTRUCTOR_FROZEN != BLOCK_SEED_RULE_FROZEN",
            "SOFTWARE_SELF_TEST != FAMILY_EXECUTION",
            "FAMILY_GENERATION != VERIFY != ADMIT",
            "ANCHOR_SIZE_CENTER != ANCHOR_FORMULA_MEMBER",
            "P ?= NP = OPEN",
        ],
    }


def self_test() -> dict:
    test_seed = "TEST-ONLY-NOT-A-FIG5-BLOCK"
    levels = [8, 9, 10, 11, 12, 13]
    traces = []

    # Determinism, width, exact active support, and density law.
    for n in levels:
        f1, t1 = generate_formula(test_seed, n)
        f2, t2 = generate_formula(test_seed, n)
        assert f1 == f2
        assert asdict(t1) == asdict(t2)
        assert len(f1) == target_clause_count(n)
        assert {abs(l) for c in f1 for l in c} == set(range(1, n + 1))
        assert all(len(c) == WIDTH for c in f1)
        traces.append(asdict(t1))

    # Same seed, changed n should actually change the family member.
    assert len({t["formula_digest"] for t in traces}) == len(levels)

    # Seed is a true external family coordinate: changing only seed changes output.
    a, _ = generate_formula("TEST-SEED-A", 10)
    b, _ = generate_formula("TEST-SEED-B", 10)
    assert a != b

    # Raw stream identity: a domain-separated entropy token is seed/position based,
    # not produced by solver outcomes.  It is deliberately independent of n.
    token_a = _sha256_hex(FAMILY_VERSION, test_seed, "raw-stream", 0)
    token_b = _sha256_hex(FAMILY_VERSION, test_seed, "raw-stream", 0)
    assert token_a == token_b

    return {
        "status": "PASS",
        "tests": {
            "levels_checked": levels,
            "determinism": True,
            "exact_active_variable_coverage": True,
            "all_clauses_width_3": True,
            "clause_count_law": True,
            "distinct_level_digests": True,
            "seed_changes_output": True,
            "raw_stream_reproducible": True,
        },
        "traces": traces,
        "claim_ceiling": "SOFTWARE_SELF_TEST != FIG5_FAMILY_EXECUTION",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--describe", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--test-formula", type=int, metavar="N",
                    help="emit a TEST-ONLY formula at N; not an official FIG-5 block")
    args = ap.parse_args()

    if args.describe:
        print(json.dumps(describe_contract(), indent=2, sort_keys=True))
    if args.self_test:
        print(json.dumps(self_test(), indent=2, sort_keys=True))
    if args.test_formula is not None:
        f, t = generate_formula("TEST-ONLY-NOT-A-FIG5-BLOCK", args.test_formula)
        print(json.dumps({"trace": asdict(t), "clauses": [list(c) for c in f]}, indent=2, sort_keys=True))
    if not (args.describe or args.self_test or args.test_formula is not None):
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
