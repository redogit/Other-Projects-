"""Deterministic adversarial stress audit for the bounded RMAPL/Omega runtime.

This harness deliberately uses only the Python standard library and public
project APIs.  It is broad bounded software verification, not exhaustive
verification, scientific validation, or RMALC validation.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any, Callable

from omega import canonical_json, make_omega, validate_omega
from omega_adapters import (
    project_dimensional_record,
    project_gsfl_record,
    project_hodge_bridge,
    project_s1_experience,
    project_suggestion_record,
)
from rmapl import parse_rmapl
from rmapl_runtime import run_program

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EVIDENCE_PATH = HERE / "evidence" / "RMAPL_OMEGA_STRESS_RESULTS.json"

STRESS_SCHEMA = "rmapl-omega-stress/v0"
DEFAULT_SEED = 20260920

_BASE_CASES = {
    "omegaCanonical": 2048,
    "parserMutation": 1536,
    "runtimeMatrix": 1024,
    "adapterAuthority": 512,
    "rmalResponseBoundary": 256,
}

CLAIM_CEILING = [
    "STRESS_PASS != PROOF",
    "FIXED_SEED_STRESS != EXHAUSTIVE_VERIFICATION",
    "RMAPL_PROFILE != RMAL_CORE_FRONTEND",
    "SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",
    "METHOD_TRANSFER != EVIDENCE_TRANSFER",
    "AUTHORED_CARRIER != GENERIC_RESPONSE_RUNTIME",
    "CONTROLLED_SURFACE_CHECK != RMALC_COMPILE",
]

_MAX_FAILURE_SAMPLES = 20


class _Tracker:
    def __init__(self) -> None:
        self._digests = {name: hashlib.sha256() for name in _BASE_CASES}
        self.failures: list[dict[str, Any]] = []

    def observe(self, family: str, case_index: int, payload: Any) -> None:
        encoded = canonical_json(
            {
                "family": family,
                "case": case_index,
                "payload": payload,
            }
        )
        self._digests[family].update(encoded.encode("utf-8"))

    def fail(self, family: str, case_index: int, check: str, detail: str) -> None:
        self.observe(
            family,
            case_index,
            {"check": check, "ok": False, "detail": detail},
        )
        if len(self.failures) < _MAX_FAILURE_SAMPLES:
            self.failures.append(
                {
                    "family": family,
                    "case": case_index,
                    "check": check,
                    "detail": detail,
                }
            )

    def family_digests(self) -> dict[str, str]:
        return {name: digest.hexdigest() for name, digest in sorted(self._digests.items())}


def canonical_stress_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _json_value(rng: random.Random, depth: int = 0) -> Any:
    scalar_kind = rng.randrange(6)
    if depth >= 3 or scalar_kind < 4:
        if scalar_kind == 0:
            return None
        if scalar_kind == 1:
            return bool(rng.randrange(2))
        if scalar_kind == 2:
            return rng.randint(-1_000_000, 1_000_000)
        if scalar_kind == 3:
            numerator = rng.randint(-1_000_000, 1_000_000)
            denominator = rng.randint(1, 10_000)
            return numerator / denominator
        if scalar_kind == 4:
            return f"s:{rng.randrange(1 << 30):08x}"
        return ""
    if scalar_kind == 4:
        return [_json_value(rng, depth + 1) for _ in range(rng.randrange(0, 5))]
    keys = [f"k{index}_{rng.randrange(1 << 16):04x}" for index in range(rng.randrange(0, 5))]
    return {key: _json_value(rng, depth + 1) for key in keys}


def _reordered(value: Any, rng: random.Random) -> Any:
    if isinstance(value, dict):
        items = [(key, _reordered(item, rng)) for key, item in value.items()]
        rng.shuffle(items)
        return {key: item for key, item in items}
    if isinstance(value, list):
        return [_reordered(item, rng) for item in value]
    return value


def _make_stress_omega(
    *,
    identity: str,
    state: Any,
    residual_kind: str = "stress-residual",
    evidence_kind: str = "software-verification",
    max_candidates: int = 8,
    max_steps: int = 1,
) -> dict[str, Any]:
    return make_omega(
        native_type="stress-synthetic/v0",
        native_identity=identity,
        source_refs=(identity,),
        state=state,
        path=(),
        frame={"obligation": "stress"},
        invariants=("state.protected", "claim-ceiling"),
        observations=(),
        residuals=({"kind": residual_kind, "detail": identity},),
        decision_field={"goal": "bounded-stress"},
        provenance=({"kind": "stress", "ref": identity},),
        evidence=(
            {
                "kind": evidence_kind,
                "detail": "stress fixture",
                "claimCeiling": "BOUNDED",
            },
        ),
        claim_ceiling=("SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",),
        resource_bounds={
            "maxCandidates": max_candidates,
            "maxSteps": max_steps,
        },
        domain_remainder={"native": "stress", "identity": identity},
    )


def _updated(omega: dict[str, Any], **changes: Any) -> dict[str, Any]:
    construction = dict(omega["construction"])
    construction.update(changes)
    return make_omega(**construction)


def _metrics(*, score: float = 1.0, loss: float = 0.0) -> dict[str, float]:
    return {
        "residualReduction": score,
        "invariantPreservation": score,
        "reconstructibility": score,
        "reversibility": score,
        "evidenceCoverage": score,
        "branchReduction": score,
        "provenanceCompleteness": score,
        "semanticLoss": loss,
        "ambiguityIntroduction": loss,
        "relationGrowth": loss,
        "runtimeCost": 0.0,
        "economicCost": 0.0,
        "unresolvedGrowth": loss,
        "irreversibleMutation": loss,
    }


def _proposal(
    omega: dict[str, Any],
    consequence: str,
    *,
    score: float = 1.0,
    loss: float = 0.0,
    reconstruction: str = "exact",
) -> dict[str, Any]:
    return {
        "omega": omega,
        "consequenceKey": consequence,
        "metrics": _metrics(score=score, loss=loss),
        "knowledgeDecay": {
            "loss": [],
            "introduction": [],
            "aliasing": [],
            "ambiguity": [],
            "provenanceGap": [],
            "reconstructionCost": 0,
            "oracleShift": [],
            "unresolvedGrowth": [],
        },
        "reconstruction": {"status": reconstruction},
    }


def _program(
    repair_blocks: list[tuple[str, str, list[str], list[str]]],
    *,
    residual_kind: str = "stress-residual",
    max_candidates: int = 8,
    max_steps: int = 1,
) -> Any:
    blocks = []
    for repair_id, operator, evidence, preserves in repair_blocks:
        blocks.append(
            "\n".join(
                [
                    f"REPAIR {repair_id}",
                    json.dumps(residual_kind),
                    "REQUIRES []",
                    f"TARGETS {json.dumps([residual_kind], separators=(',', ':'))}",
                    f"PRESERVES {json.dumps(preserves, separators=(',', ':'))}",
                    'MAY_MUTATE ["state.x","residuals"]',
                    'FORBIDS ["provenance","evidence"]',
                    f"APPLY {operator}",
                    f"EVIDENCE {json.dumps(evidence, separators=(',', ':'))}",
                    "COST 1",
                    "END",
                ]
            ).replace(f"REPAIR {repair_id}\n{json.dumps(residual_kind)}", f"REPAIR {repair_id}\nWHEN {json.dumps(residual_kind)}")
        )
    source = (
        "RMAPL 0\n"
        "PROGRAM stress-runtime\n"
        "LOAD fixture\n"
        f"BOUND maxCandidates={max_candidates}\n"
        f"BOUND maxSteps={max_steps}\n"
        + "\n".join(blocks)
        + "\nRUN\n"
    )
    return parse_rmapl(source)


def _valid_parser_program(case_index: int) -> str:
    return (
        "RMAPL 0\n"
        f"PROGRAM stress_{case_index}\n"
        "LOAD fixture\n"
        f"BOUND maxCandidates={(case_index % 7) + 1}\n"
        f"BOUND maxSteps={(case_index % 3) + 1}\n"
        f"REPAIR repair_{case_index}\n"
        'WHEN "stress-residual"\n'
        'REQUIRES ["source.available"]\n'
        'TARGETS ["stress-residual"]\n'
        'PRESERVES ["state.protected"]\n'
        'MAY_MUTATE ["state.x","residuals"]\n'
        'FORBIDS ["provenance","evidence"]\n'
        f"APPLY op_{case_index}\n"
        'EVIDENCE ["software-verification"]\n'
        f"COST {case_index % 11}\n"
        "END\n"
        "RUN\n"
    )


def _malformed_parser_program(valid: str, mutation_index: int) -> str:
    mode = mutation_index % 10
    if mode == 0:
        return valid.replace("RUN\n", "MAGIC nope\nRUN\n")
    if mode == 1:
        return valid.replace("COST ", "COST -", 1)
    if mode == 2:
        return valid.replace("BOUND maxCandidates=", "BOUND maxCandidates=NaN #", 1)
    if mode == 3:
        line = next(line for line in valid.splitlines() if line.startswith("BOUND maxSteps="))
        return valid.replace(line + "\n", line + "\n" + line + "\n", 1)
    if mode == 4:
        return valid.replace("END\nRUN\n", "RUN\n", 1)
    if mode == 5:
        return valid.replace(
            'REQUIRES ["source.available"]\nTARGETS ["stress-residual"]',
            'TARGETS ["stress-residual"]\nREQUIRES ["source.available"]',
            1,
        )
    if mode == 6:
        repair_line = next(line for line in valid.splitlines() if line.startswith("REPAIR "))
        duplicate = (
            repair_line
            + "\n"
            + 'WHEN "other"\n'
            + "REQUIRES []\n"
            + "TARGETS []\n"
            + "PRESERVES []\n"
            + "MAY_MUTATE []\n"
            + "FORBIDS []\n"
            + "APPLY duplicate_op\n"
            + "EVIDENCE []\n"
            + "COST 0\n"
            + "END\n"
        )
        return valid.replace("RUN\n", duplicate + "RUN\n", 1)
    if mode == 7:
        return valid + "BOUND after=1\n"
    if mode == 8:
        return valid.replace("PROGRAM stress_", "PROGRAM invalid id ", 1)
    return valid.replace(
        'EVIDENCE ["software-verification"]\n',
        "",
        1,
    )


def _run_omega_family(count: int, seed: int, tracker: _Tracker, checks: dict[str, bool]) -> None:
    rng = random.Random(seed ^ 0x0A11CE)
    for index in range(count):
        try:
            state = {
                "protected": index % 97,
                "payload": _json_value(rng),
                "nested": _json_value(rng),
            }
            reordered = _reordered(state, random.Random(seed + index))
            first = _make_stress_omega(identity=f"omega:{index}", state=state)
            second = _make_stress_omega(identity=f"omega:{index}", state=reordered)

            deterministic = first["id"] == second["id"] and canonical_json(first) == canonical_json(second)
            if not deterministic:
                checks["omegaCanonicalDeterministic"] = False
                tracker.fail("omegaCanonical", index, "omegaCanonicalDeterministic", "reordered equivalent input changed canonical identity")
                continue

            construction = dict(first["construction"])
            remainder = dict(construction["domain_remainder"])
            remainder["sensitivityNonce"] = index + 1
            construction["domain_remainder"] = remainder
            changed = make_omega(**construction)
            sensitive = changed["id"] != first["id"]
            if not sensitive:
                checks["omegaIdentitySensitive"] = False
                tracker.fail("omegaCanonical", index, "omegaIdentitySensitive", "changed domain remainder did not change Omega identity")
                continue

            tampered = dict(first)
            tampered["id"] = "0" * 64
            try:
                validate_omega(tampered)
            except ValueError:
                tamper_rejected = True
            else:
                tamper_rejected = False
            if not tamper_rejected:
                checks["omegaTamperRejected"] = False
                tracker.fail("omegaCanonical", index, "omegaTamperRejected", "tampered Omega id was accepted")
                continue

            tracker.observe(
                "omegaCanonical",
                index,
                {
                    "deterministic": True,
                    "sensitive": True,
                    "tamperRejected": True,
                    "id": first["id"],
                    "changedId": changed["id"],
                },
            )
        except Exception as exc:  # audit captures exact unexpected failures
            checks["omegaCanonicalDeterministic"] = False
            tracker.fail("omegaCanonical", index, "exception", f"{type(exc).__name__}: {exc}")


def _run_parser_family(count: int, seed: int, tracker: _Tracker, checks: dict[str, bool]) -> None:
    del seed  # deterministic corpus is indexed rather than random
    for index in range(count):
        try:
            valid = _valid_parser_program(index)
            first = parse_rmapl(valid)
            second = parse_rmapl(valid)
            deterministic = first == second
            if not deterministic:
                checks["parserValidDeterministic"] = False
                tracker.fail("parserMutation", index, "parserValidDeterministic", "same valid program parsed differently")
                continue

            malformed = _malformed_parser_program(valid, index)
            try:
                parse_rmapl(malformed)
            except ValueError:
                rejected = True
            else:
                rejected = False
            if not rejected:
                checks["parserMalformedRejected"] = False
                tracker.fail("parserMutation", index, "parserMalformedRejected", f"mutation mode {index % 10} was accepted")
                continue

            tracker.observe(
                "parserMutation",
                index,
                {
                    "validRepair": first.repairs[0].repair_id,
                    "mutationMode": index % 10,
                    "rejected": True,
                },
            )
        except Exception as exc:
            checks["parserMalformedRejected"] = False
            tracker.fail("parserMutation", index, "exception", f"{type(exc).__name__}: {exc}")


def _run_runtime_family(count: int, seed: int, tracker: _Tracker, checks: dict[str, bool]) -> None:
    rng = random.Random(seed ^ 0x5A17)
    for index in range(count):
        mode = index % 4
        try:
            protected = rng.randrange(1, 100_000)
            source = _make_stress_omega(
                identity=f"runtime:{index}",
                state={"x": 0, "protected": protected},
                max_candidates=4,
                max_steps=1,
            )

            if mode == 0:
                program = _program(
                    [("science", "science_op", ["scientific-validation"], ["state.protected"])]
                )

                def science_op(value: dict[str, Any]) -> dict[str, Any]:
                    return _proposal(_updated(value, residuals=[]), "done")

                registry = {"science_op": science_op}
                result_a = run_program(program, source, registry)
                result_b = run_program(program, source, registry)
                ok = (
                    canonical_json(result_a) == canonical_json(result_b)
                    and result_a["stopReason"] == "EVIDENCE_BOUND"
                    and result_a["generation"]["executedCount"] == 0
                )
                checks["runtimeDeterministic"] &= canonical_json(result_a) == canonical_json(result_b)
                checks["runtimeEvidenceBound"] &= ok
                if not ok:
                    tracker.fail("runtimeMatrix", index, "runtimeEvidenceBound", canonical_json(result_a))
                    continue

            elif mode == 1:
                program = _program(
                    [
                        ("good", "good_op", [], ["state.protected"]),
                        ("bad", "bad_op", [], ["state.protected"]),
                    ]
                )

                def good_op(value: dict[str, Any]) -> dict[str, Any]:
                    candidate = _updated(
                        value,
                        state={"x": 1, "protected": protected},
                        residuals=[],
                    )
                    return _proposal(candidate, "x=1", score=1)

                def bad_op(value: dict[str, Any]) -> dict[str, Any]:
                    candidate = _updated(
                        value,
                        state={"x": 1, "protected": protected + 1},
                        residuals=[],
                    )
                    return _proposal(candidate, "x=1", score=100)

                registry = {"good_op": good_op, "bad_op": bad_op}
                result_a = run_program(program, source, registry)
                result_b = run_program(program, source, registry)
                classes = {
                    (branch["candidateId"], branch["classification"], branch["admitted"])
                    for branch in result_a["branches"]
                }
                ok = (
                    canonical_json(result_a) == canonical_json(result_b)
                    and result_a["stopReason"] == "SUCCESS"
                    and ("good", "EXACT_REPAIR", True) in classes
                    and ("bad", "MUTATION", False) in classes
                    and result_a["generation"]["equivalenceClassCount"] == 2
                )
                checks["runtimeDeterministic"] &= canonical_json(result_a) == canonical_json(result_b)
                checks["runtimeMutationRejected"] &= ok
                checks["runtimeQuotientSeparated"] &= result_a["generation"]["equivalenceClassCount"] == 2
                if not ok:
                    tracker.fail("runtimeMatrix", index, "runtimeMutationRejected", canonical_json(result_a))
                    continue

            elif mode == 2:
                program = _program(
                    [
                        ("route_a", "route_a_op", [], ["state.protected"]),
                        ("route_b", "route_b_op", [], ["state.protected"]),
                    ]
                )

                def route_a_op(value: dict[str, Any]) -> dict[str, Any]:
                    return _proposal(
                        _updated(
                            value,
                            state={"x": 1, "protected": protected},
                            residuals=[],
                        ),
                        "same-consequence",
                    )

                def route_b_op(value: dict[str, Any]) -> dict[str, Any]:
                    return _proposal(
                        _updated(
                            value,
                            state={"x": 1, "protected": protected},
                            residuals=[],
                        ),
                        "same-consequence",
                    )

                registry = {"route_a_op": route_a_op, "route_b_op": route_b_op}
                result_a = run_program(program, source, registry)
                result_b = run_program(program, source, registry)
                branch = result_a["branches"][0] if result_a["branches"] else {}
                ok = (
                    canonical_json(result_a) == canonical_json(result_b)
                    and result_a["stopReason"] == "SUCCESS"
                    and result_a["generation"]["equivalenceClassCount"] == 1
                    and branch.get("sourceCandidateIds") == ["route_a", "route_b"]
                )
                checks["runtimeDeterministic"] &= canonical_json(result_a) == canonical_json(result_b)
                checks["runtimeQuotientSeparated"] &= ok
                if not ok:
                    tracker.fail("runtimeMatrix", index, "runtimeQuotientSeparated", canonical_json(result_a))
                    continue

            else:
                program = _program(
                    [("loop", "loop_op", [], ["state.protected"])],
                    max_steps=1,
                )

                def loop_op(value: dict[str, Any]) -> dict[str, Any]:
                    return _proposal(_updated(value), "same-state")

                registry = {"loop_op": loop_op}
                result_a = run_program(program, source, registry)
                result_b = run_program(program, source, registry)
                ok = (
                    canonical_json(result_a) == canonical_json(result_b)
                    and result_a["stopReason"] == "REPEATED_STATE_CYCLE"
                    and "REPEATED_STATE_CYCLE" in result_a["stopFacts"]
                    and "RESOURCE_BOUND" in result_a["stopFacts"]
                )
                checks["runtimeDeterministic"] &= canonical_json(result_a) == canonical_json(result_b)
                checks["runtimeCycleBounded"] &= ok
                if not ok:
                    tracker.fail("runtimeMatrix", index, "runtimeCycleBounded", canonical_json(result_a))
                    continue

            tracker.observe(
                "runtimeMatrix",
                index,
                {
                    "mode": mode,
                    "stopReason": result_a["stopReason"],
                    "branchClasses": [
                        [branch["candidateId"], branch["classification"], branch["admitted"]]
                        for branch in result_a["branches"]
                    ],
                    "generation": result_a["generation"],
                },
            )
        except Exception as exc:
            if mode == 0:
                checks["runtimeEvidenceBound"] = False
            elif mode == 1:
                checks["runtimeMutationRejected"] = False
            elif mode == 2:
                checks["runtimeQuotientSeparated"] = False
            else:
                checks["runtimeCycleBounded"] = False
            checks["runtimeDeterministic"] = False
            tracker.fail("runtimeMatrix", index, "exception", f"{type(exc).__name__}: {exc}")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_adapter_family(count: int, seed: int, tracker: _Tracker, checks: dict[str, bool]) -> None:
    rng = random.Random(seed ^ 0xADA7)
    hodge_native = _load_json(ROOT / "Hodge Span Lab" / "evidence" / "issue43_bridge_calibration_result.json")
    gsfl_native = _load_json(ROOT / "Generalized Semantic Fitting Language" / "evidence" / "RESULTS.json")

    for index in range(count):
        mode = index % 5
        try:
            if mode == 0:
                native = {
                    "schema": "s1-experience/v0",
                    "id": f"stress-s1-{index}",
                    "operatorVersion": "S'1-Ops v0",
                    "initialState": "fixture",
                    "mirrorId": "mirror:fixture",
                    "shell": "comparison",
                    "actions": [
                        {
                            "plane": ("xw", "yw", "zw")[index % 3],
                            "degrees": 1 if index % 2 == 0 else -1,
                        }
                    ],
                    "observer": {
                        "yaw": 0,
                        "pitch": 0,
                        "roll": 0,
                        "wPerspective": 0.35,
                    },
                    "provenance": {"source": "stress"},
                }
                omega = project_s1_experience(native)
                evidence_kinds = {item["kind"] for item in omega["evidence"]}
                no_amplification = "software-verification" not in evidence_kinds
                authority_ok = "SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION" in omega["claimCeiling"]

            elif mode == 1:
                native = {
                    "carrierVersion": "s1-transition-carrier/v0",
                    "kind": "generated" if index % 2 else "observed",
                    "move": {
                        "plane": ("xw", "yw", "zw")[index % 3],
                        "degrees": 1 if index % 2 == 0 else -1,
                    },
                    "prefix": [],
                    "contract": {
                        "initialState": "fixture",
                        "mirrorId": "mirror:fixture",
                        "shell": "comparison",
                        "observer": {},
                        "operatorVersion": "S'1-Ops v0",
                    },
                    "provenance": {
                        "datasetVersion": "s1-suggest-dataset/v0",
                        "modelVersion": "s1-suggest-transition/v0",
                        "sourceExperienceIds": [],
                        "strategy": "stress",
                    },
                    "authority": "suggestion-only",
                }
                omega = project_suggestion_record(native)
                evidence_kinds = {item["kind"] for item in omega["evidence"]}
                no_amplification = evidence_kinds == {"suggestion-only"}
                authority_ok = "SUGGESTION != EXPERIENCE_AUTHORITY" in omega["claimCeiling"]

            elif mode == 2:
                native = deepcopy(hodge_native)
                native["provenance"]["stress_nonce"] = index
                omega = project_hodge_bridge(native)
                evidence_kinds = {item["kind"] for item in omega["evidence"]}
                no_amplification = evidence_kinds == {"candidate-test-only"}
                authority_ok = (
                    native["claim_ceiling"] in omega["claimCeiling"]
                    and omega["path"] == native["source"]["actions"]
                )

            elif mode == 3:
                native = deepcopy(gsfl_native)
                omega = project_gsfl_record(native)
                evidence_kinds = {item["kind"] for item in omega["evidence"]}
                no_amplification = (
                    "software-verification" not in evidence_kinds
                    and "reported-software-verification" in evidence_kinds
                )
                authority_ok = "FIT != TRUTH" in omega["claimCeiling"]

            else:
                dropped_a = rng.randrange(-1000, 1001)
                dropped_b = dropped_a
                while dropped_b == dropped_a:
                    dropped_b = rng.randrange(-1000, 1001)
                native = {
                    "version": "s1-dimension-ladder/v0",
                    "boundary": "ADJACENT_DIMENSIONS_RELATED != ADJACENT_DIMENSIONS_IDENTICAL",
                    "ladder": [0, 1, 2, 3, 4],
                    "projectionLoss": {
                        "map": "drop coordinate 2",
                        "sourceA": [1, 2, dropped_a],
                        "sourceB": [1, 2, dropped_b],
                        "projectionA": [1, 2],
                        "projectionB": [1, 2],
                        "sameProjection": True,
                        "sourcePointsDistinct": True,
                    },
                    "claimCeiling": [
                        "finite Euclidean fixtures only",
                        "no universal dimensional law",
                    ],
                }
                omega = project_dimensional_record(native)
                evidence_kinds = {item["kind"] for item in omega["evidence"]}
                no_amplification = "software-verification" not in evidence_kinds
                observation = next(
                    item for item in omega["observations"]
                    if item["kind"] == "projection-loss"
                )
                authority_ok = (
                    observation["reconstructionAvailable"] is False
                    and observation["lost"] == "dropped-coordinate-distinction"
                )

            if not no_amplification:
                checks["adapterNoEvidenceAmplification"] = False
                tracker.fail("adapterAuthority", index, "adapterNoEvidenceAmplification", f"mode={mode}, evidence={sorted(evidence_kinds)}")
                continue
            if not authority_ok:
                checks["adapterAuthorityCeilings"] = False
                tracker.fail("adapterAuthority", index, "adapterAuthorityCeilings", f"mode={mode}, ceiling={omega['claimCeiling']}")
                continue

            tracker.observe(
                "adapterAuthority",
                index,
                {
                    "mode": mode,
                    "nativeType": omega["nativeType"],
                    "evidenceKinds": sorted(evidence_kinds),
                    "claimCeiling": omega["claimCeiling"],
                },
            )
        except Exception as exc:
            checks["adapterNoEvidenceAmplification"] = False
            checks["adapterAuthorityCeilings"] = False
            tracker.fail("adapterAuthority", index, "exception", f"{type(exc).__name__}: {exc}")


def _rmal_boundary_snapshot() -> dict[str, Any]:
    adapter = _load_json(ROOT / "BIDIRECTIONAL_HANDOFF_ADAPTER_2026-09-20.json")
    evidence = _load_json(ROOT / "evidence" / "RMAL_BIDIRECTIONAL_HANDOFF_RESPONSE_2026-09-20.json")
    validation = evidence["successor_validation"]
    return {
        "adapterStatus": adapter["outbound"]["status"],
        "controlledSurfaceCheck": adapter["outbound"]["controlled_surface_check"],
        "rmalcRevalidated": adapter["outbound"]["rmalc_revalidated"],
        "structuredRuntime": adapter["outbound"]["structured_response_packet_runtime"],
        "genericRuntime": adapter["outbound"]["generic_response_packet_runtime"],
        "rmalcCheck": validation["rmalc_check"],
        "rmalcCompile": validation["rmalc_compile"],
        "rmalcAudit": validation["rmalc_audit"],
        "claimCeiling": evidence["claim_ceiling"],
        "boundaries": sorted(evidence["boundaries"]),
    }


def _validate_rmal_boundary(snapshot: dict[str, Any]) -> bool:
    return (
        snapshot["rmalcRevalidated"] is False
        and snapshot["structuredRuntime"] is False
        and snapshot["genericRuntime"] is False
        and snapshot["rmalcCheck"] == "NOT_REVALIDATED"
        and snapshot["rmalcCompile"] == "NOT_REVALIDATED"
        and snapshot["rmalcAudit"] == "NOT_REVALIDATED"
        and "CONTROLLED_SURFACE_CHECK != RMALC_COMPILE" in snapshot["boundaries"]
        and "AUTHORED_CARRIER != GENERIC_RESPONSE_RUNTIME" in snapshot["boundaries"]
    )


def _run_rmal_boundary_family(count: int, seed: int, tracker: _Tracker, checks: dict[str, bool]) -> dict[str, Any]:
    rng = random.Random(seed ^ 0xB0A7D)
    snapshot = _rmal_boundary_snapshot()
    escalation_fields: list[tuple[str, Any]] = [
        ("rmalcRevalidated", True),
        ("structuredRuntime", True),
        ("genericRuntime", True),
        ("rmalcCheck", "PASS"),
        ("rmalcCompile", "PASS"),
        ("rmalcAudit", "PASS"),
    ]

    for index in range(count):
        try:
            original_ok = _validate_rmal_boundary(snapshot)
            field, forbidden = escalation_fields[rng.randrange(len(escalation_fields))]
            mutated = deepcopy(snapshot)
            mutated[field] = forbidden
            escalation_rejected = not _validate_rmal_boundary(mutated)
            ok = original_ok and escalation_rejected
            checks["rmalResponseBoundaryPreserved"] &= ok
            if not ok:
                tracker.fail(
                    "rmalResponseBoundary",
                    index,
                    "rmalResponseBoundaryPreserved",
                    f"field={field}, original_ok={original_ok}, escalation_rejected={escalation_rejected}",
                )
                continue
            tracker.observe(
                "rmalResponseBoundary",
                index,
                {
                    "field": field,
                    "forbidden": forbidden,
                    "originalAccepted": original_ok,
                    "escalationRejected": escalation_rejected,
                },
            )
        except Exception as exc:
            checks["rmalResponseBoundaryPreserved"] = False
            tracker.fail("rmalResponseBoundary", index, "exception", f"{type(exc).__name__}: {exc}")
    return snapshot


def build_stress_report(*, seed: int = DEFAULT_SEED, scale: int = 1) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("stress seed must be an integer")
    if type(scale) is not int or scale < 1 or scale > 8:
        raise ValueError("stress scale must be an integer from 1 through 8")

    families = {name: count * scale for name, count in _BASE_CASES.items()}
    checks = {
        "omegaCanonicalDeterministic": True,
        "omegaIdentitySensitive": True,
        "omegaTamperRejected": True,
        "parserMalformedRejected": True,
        "parserValidDeterministic": True,
        "runtimeDeterministic": True,
        "runtimeEvidenceBound": True,
        "runtimeMutationRejected": True,
        "runtimeQuotientSeparated": True,
        "runtimeCycleBounded": True,
        "adapterNoEvidenceAmplification": True,
        "adapterAuthorityCeilings": True,
        "rmalResponseBoundaryPreserved": True,
    }
    tracker = _Tracker()

    _run_omega_family(families["omegaCanonical"], seed, tracker, checks)
    _run_parser_family(families["parserMutation"], seed, tracker, checks)
    _run_runtime_family(families["runtimeMatrix"], seed, tracker, checks)
    _run_adapter_family(families["adapterAuthority"], seed, tracker, checks)
    boundary = _run_rmal_boundary_family(
        families["rmalResponseBoundary"],
        seed,
        tracker,
        checks,
    )

    family_digests = tracker.family_digests()
    digest_payload = {
        "seed": seed,
        "scale": scale,
        "families": families,
        "checks": checks,
        "familyDigests": family_digests,
        "failures": tracker.failures,
        "rmalResponseBoundary": boundary,
    }
    digest = hashlib.sha256(canonical_json(digest_payload).encode("utf-8")).hexdigest()

    return {
        "schema": STRESS_SCHEMA,
        "seed": seed,
        "scale": scale,
        "families": families,
        "totalCases": sum(families.values()),
        "checks": checks,
        "failures": tracker.failures,
        "familyDigests": family_digests,
        "digestSha256": digest,
        "scientificValidation": False,
        "rmalResponseBoundary": boundary,
        "claimCeiling": list(CLAIM_CEILING),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--scale", type=int, default=1)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.check and (args.seed != DEFAULT_SEED or args.scale != 1):
        parser.exit(2, "--check is only valid for the frozen default seed and scale\n")

    report = build_stress_report(seed=args.seed, scale=args.scale)
    if report["failures"] or not all(report["checks"].values()):
        failed_checks = sorted(name for name, value in report["checks"].items() if not value)
        parser.exit(
            1,
            f"RMAPL Omega stress failed: checks={failed_checks}, sampled_failures={len(report['failures'])}\n",
        )

    text = canonical_stress_text(report)
    if args.out:
        args.out.write_text(text, encoding="utf-8")

    if args.check:
        try:
            expected = EVIDENCE_PATH.read_text(encoding="utf-8")
        except OSError as exc:
            parser.exit(1, f"RMAPL Omega frozen stress evidence unavailable: {exc}\n")
        if expected != text:
            parser.exit(1, "RMAPL Omega frozen stress evidence does not match current stress report\n")
        print(
            f"PASS RMAPL Omega stress: {report['totalCases']} fixed-seed adversarial cases, "
            f"{len(report['checks'])}/{len(report['checks'])} checks"
        )
        return 0

    if not args.out:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
