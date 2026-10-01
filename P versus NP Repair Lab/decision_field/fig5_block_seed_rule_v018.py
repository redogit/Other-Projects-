from __future__ import annotations

"""FIG-5 v0.18 five-block seed derivation rule.

This module freezes only the rule that defines the five future official block
seeds. It deliberately does NOT evaluate/materialize those five official seed
values, construct any FIG-5 formula, materialize the 30-row manifest, run the
active solver, call the verifier, or admit any row.

The official seed values are logically fixed by this rule, but this file's
self-test uses a TEST-ONLY namespace and never invokes derive_block_seed() on a
valid official block id.
"""

import argparse
import hashlib
import json

SEED_RULE_VERSION = "FIG5-block-seed/v0.18"
OFFICIAL_NAMESPACE = "FIG5/BLOCK-SEED/v0.18"
TEST_NAMESPACE = "FIG5/TEST-ONLY-BLOCK-SEED/v0.18"
EXPERIMENT_ID = "FIG-5"
BLOCK_COUNT = 5

CONSTRUCTOR_VERSION = "FIG5-clause-priority-3cnf/v0.17"
CONSTRUCTOR_SOURCE_SHA256 = "9b9f274513bb83e61643a7bcf515553888a354c625cb2e7ac7c4e5648200c4dd"
NSTAR_BINDING_RECEIPT_SHA256 = "682bbcf6ed83e6d3f3264b7ca41257e60c64dc56b4c0fc331057808a845d440d"
DELTA_BINDING_WITNESS_SHA256 = "2b1b2d04819f262ab5d8d8fd654a5c550a3978fa8bd8d75a9737322aacb5df09"


def _encode_part(part: object) -> bytes:
    if isinstance(part, bytes):
        return part
    return str(part).encode("utf-8")


def _sha256_hex(*parts: object) -> str:
    h = hashlib.sha256()
    for part in parts:
        b = _encode_part(part)
        h.update(len(b).to_bytes(4, "big"))
        h.update(b)
    return h.hexdigest()


def _validate_block_id(block_id: int) -> None:
    if not isinstance(block_id, int) or isinstance(block_id, bool) or not 0 <= block_id < BLOCK_COUNT:
        raise ValueError(f"block_id must be an integer in [0,{BLOCK_COUNT - 1}]")


def _derive_seed(namespace: str, block_id: int) -> str:
    if not isinstance(namespace, str) or not namespace:
        raise ValueError("namespace must be a non-empty string")
    _validate_block_id(block_id)
    return _sha256_hex(
        namespace,
        EXPERIMENT_ID,
        CONSTRUCTOR_VERSION,
        CONSTRUCTOR_SOURCE_SHA256,
        NSTAR_BINDING_RECEIPT_SHA256,
        DELTA_BINDING_WITNESS_SHA256,
        block_id,
    )


def derive_block_seed(block_id: int) -> str:
    """Derive one official block seed. Do not call until the manifest-materialization rung opens."""
    return _derive_seed(OFFICIAL_NAMESPACE, block_id)


def describe_contract() -> dict:
    return {
        "seed_rule_version": SEED_RULE_VERSION,
        "official_namespace": OFFICIAL_NAMESPACE,
        "experiment_id": EXPERIMENT_ID,
        "block_ids": "integers 0..4",
        "block_count": BLOCK_COUNT,
        "derivation": "SHA256(length-prefixed ordered inputs)",
        "ordered_inputs": [
            "official_namespace",
            "experiment_id",
            "constructor_version",
            "constructor_source_sha256",
            "nstar_binding_receipt_sha256",
            "delta_binding_witness_sha256",
            "block_id",
        ],
        "constructor_version": CONSTRUCTOR_VERSION,
        "constructor_source_sha256": CONSTRUCTOR_SOURCE_SHA256,
        "nstar_binding_receipt_sha256": NSTAR_BINDING_RECEIPT_SHA256,
        "delta_binding_witness_sha256": DELTA_BINDING_WITNESS_SHA256,
        "materialization_preconditions": [
            "exact v0.17 constructor source bytes must SHA-256 to CONSTRUCTOR_SOURCE_SHA256",
            "derive exactly block ids 0..4 once each",
            "the five derived lowercase-hex seeds must be pairwise distinct; collision => STOP with no retry or reseed",
        ],
        "seed_representation": "64 lowercase hexadecimal characters representing the SHA-256 digest",
        "collision_policy": "STOP_NO_RETRY_NO_RESEED",
        "forbidden_inputs": [
            "generated formula content",
            "active solver output",
            "verifier/oracle output",
            "DP trace or resolvent count",
            "chi_DP or any measured metric",
            "calibration or validation result",
            "nonce/search/retry/acceptance criterion",
            "wall clock or environment entropy",
        ],
        "official_seed_values_materialized_here": False,
        "official_formula_rows_materialized_here": False,
        "boundaries": [
            "SEED_RULE_FROZEN != OFFICIAL_SEEDS_MATERIALIZED",
            "OFFICIAL_SEEDS_MATERIALIZED != 30_ROW_MANIFEST_MATERIALIZED",
            "BLOCK_SEED_RULE_FROZEN != FAMILY_VALIDITY",
            "GENERATE != VERIFY != ADMIT",
            "P ?= NP = OPEN",
        ],
    }


def self_test() -> dict:
    description = describe_contract()
    assert description["seed_rule_version"] == SEED_RULE_VERSION
    assert OFFICIAL_NAMESPACE != TEST_NAMESPACE

    for bad in (-1, 5, 6, 100, True):
        try:
            derive_block_seed(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid block id unexpectedly accepted: {bad!r}")

    test_seeds_a = [_derive_seed(TEST_NAMESPACE, i) for i in range(BLOCK_COUNT)]
    test_seeds_b = [_derive_seed(TEST_NAMESPACE, i) for i in range(BLOCK_COUNT)]
    assert test_seeds_a == test_seeds_b
    assert len(set(test_seeds_a)) == BLOCK_COUNT
    assert all(len(seed) == 64 and all(c in "0123456789abcdef" for c in seed) for seed in test_seeds_a)

    baseline = _sha256_hex(
        TEST_NAMESPACE,
        EXPERIMENT_ID,
        CONSTRUCTOR_VERSION,
        CONSTRUCTOR_SOURCE_SHA256,
        NSTAR_BINDING_RECEIPT_SHA256,
        DELTA_BINDING_WITNESS_SHA256,
        0,
    )
    changed = _sha256_hex(
        TEST_NAMESPACE,
        EXPERIMENT_ID,
        CONSTRUCTOR_VERSION,
        "0" * 64,
        NSTAR_BINDING_RECEIPT_SHA256,
        DELTA_BINDING_WITNESS_SHA256,
        0,
    )
    assert baseline != changed

    return {
        "status": "PASS",
        "tests": {
            "describe_contract_executes": True,
            "invalid_official_block_ids_rejected_without_seed_materialization": True,
            "test_namespace_determinism": True,
            "test_namespace_five_distinct_outputs": True,
            "hex_output_shape": True,
            "provenance_input_sensitivity_in_test_namespace": True,
            "official_seed_values_materialized": False,
        },
        "claim_ceiling": [
            "SEED_RULE_SELF_TEST != OFFICIAL_SEED_EVALUATION",
            "SEED_RULE_FROZEN != FAMILY_VALIDITY",
            "SEED_COLLISION != PERMISSION_TO_RESEED",
            "CONSTRUCTOR_SOURCE_HASH_MISMATCH != PERMISSION_TO_DERIVE",
            "OFFICIAL_SEEDS_NOT_MATERIALIZED",
            "GENERATE != VERIFY != ADMIT",
            "P ?= NP = OPEN",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--describe", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.describe:
        print(json.dumps(describe_contract(), indent=2, sort_keys=True))
    if args.self_test:
        print(json.dumps(self_test(), indent=2, sort_keys=True))
    if not (args.describe or args.self_test):
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
