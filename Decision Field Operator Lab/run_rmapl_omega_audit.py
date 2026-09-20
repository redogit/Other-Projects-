"""Deterministic bounded audit for the RMAPL/Omega reference runtime."""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

from decision_field import DecisionField, Evidence
from omega import make_omega, validate_omega
from omega_adapters import (
    project_decision_field,
    project_dimensional_record,
    project_hodge_bridge,
    project_s1_experience,
    project_suggestion_record,
    reconstruct_decision_field,
)
from rmapl import parse_rmapl
from rmapl_runtime import (
    CandidateOutcome,
    ClaimSpec,
    KnowledgeDecay,
    admit_claim,
    pareto_frontier,
    run_program,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EVIDENCE_PATH = HERE / "evidence" / "RMAPL_OMEGA_RESULTS.json"

CLAIM_CEILING = [
    "RMAPL_PROFILE != RMAL_CORE_FRONTEND",
    "OMEGA_VIEW != NATIVE_OBJECT",
    "METHOD_TRANSFER != EVIDENCE_TRANSFER",
    "SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",
    "MAXIMAL_WITHIN_DECLARED_SCOPE != GLOBAL_COMPLETENESS",
]


def canonical_audit_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _omega(*, native_identity="audit:omega", state=None, residuals=(), max_steps=1):
    return make_omega(
        native_type="audit-synthetic/v0",
        native_identity=native_identity,
        source_refs=(native_identity,),
        state=state or {"x": 0, "protected": 7},
        path=(),
        frame={"obligation": "audit"},
        invariants=("state.protected",),
        observations=(),
        residuals=residuals,
        decision_field={"goal": "bounded-audit"},
        provenance=({"kind": "synthetic-audit"},),
        evidence=(
            {
                "kind": "software-verification",
                "detail": "synthetic audit fixture",
                "claimCeiling": "SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",
            },
        ),
        claim_ceiling=("SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",),
        resource_bounds={"maxCandidates": 8, "maxSteps": max_steps},
        domain_remainder={"native": "synthetic-audit"},
    )


def _updated(omega, *, state=None, residuals=None):
    construction = dict(omega["construction"])
    if state is not None:
        construction["state"] = state
    if residuals is not None:
        construction["residuals"] = residuals
    return make_omega(**construction)


def _runtime_metrics(**overrides):
    values = {
        "residualReduction": 1.0,
        "invariantPreservation": 1.0,
        "reconstructibility": 1.0,
        "reversibility": 1.0,
        "evidenceCoverage": 1.0,
        "branchReduction": 1.0,
        "provenanceCompleteness": 1.0,
        "semanticLoss": 0.0,
        "ambiguityIntroduction": 0.0,
        "relationGrowth": 0.0,
        "runtimeCost": 0.0,
        "economicCost": 0.0,
        "unresolvedGrowth": 0.0,
        "irreversibleMutation": 0.0,
    }
    values.update(overrides)
    return values


def _kd():
    return KnowledgeDecay()


def _candidate(candidate_id, omega, **metrics):
    return CandidateOutcome(
        candidate_id=candidate_id,
        omega=omega,
        consequence_key=candidate_id,
        classification="EXACT_REPAIR",
        admitted=True,
        metrics=_runtime_metrics(**metrics),
        knowledge_decay=_kd(),
        inspection={},
        source_candidate_ids=(candidate_id,),
    )


def _check_omega_strict():
    omega = _omega()
    if validate_omega(omega) != omega:
        return False
    try:
        validate_omega({**omega, "truthAuthority": "invented"})
    except ValueError:
        return True
    return False


def _check_decision_field_round_trip():
    field = DecisionField(
        possibilities=frozenset({0, 1, 2}),
        relations=({"kind": "excludes", "left": 0, "right": 2},),
        evidence=(Evidence("software-verification", "audit"),),
        goal=1,
        unresolved=frozenset({0, 2}),
        observer={"obligation": "select-1"},
        history=("seed",),
    )
    projected = project_decision_field(field, "audit:df", "audit:df")
    return reconstruct_decision_field(projected) == field


def _s1(actions, identity):
    return {
        "schema": "s1-experience/v0",
        "id": identity,
        "operatorVersion": "S'1-Ops v0",
        "initialState": "fixture",
        "mirrorId": "mirror:fixture",
        "shell": "comparison",
        "actions": actions,
        "observer": {"yaw": 0, "pitch": 0, "roll": 0, "wPerspective": 0.35},
        "provenance": {"source": "rmapl-omega-audit"},
    }


def _check_s1_chronology():
    a = project_s1_experience(
        _s1(
            [
                {"plane": "xw", "degrees": 1},
                {"plane": "yw", "degrees": 1},
            ],
            "audit:s1:a",
        )
    )
    b = project_s1_experience(
        _s1(
            [
                {"plane": "yw", "degrees": 1},
                {"plane": "xw", "degrees": 1},
            ],
            "audit:s1:b",
        )
    )
    return a["path"] != b["path"] and a["id"] != b["id"]


def _check_typed_evidence():
    claim = ClaimSpec("science", ("scientific-validation",), ())
    return (
        not admit_claim(claim, {"software-verification"})
        and admit_claim(claim, {"software-verification", "scientific-validation"})
    )


def _check_lossy_quotient():
    native = {
        "version": "s1-dimension-ladder/v0",
        "boundary": "ADJACENT_DIMENSIONS_RELATED != ADJACENT_DIMENSIONS_IDENTICAL",
        "ladder": [0, 1, 2, 3, 4],
        "projectionLoss": {
            "map": "drop coordinate 2",
            "sourceA": [1, 2, 3],
            "sourceB": [1, 2, 9],
            "projectionA": [1, 2],
            "projectionB": [1, 2],
            "sameProjection": True,
            "sourcePointsDistinct": True,
        },
        "claimCeiling": ["finite Euclidean fixtures only"],
    }
    omega = project_dimensional_record(native)
    observation = next(
        item for item in omega["observations"] if item["kind"] == "projection-loss"
    )
    return (
        observation["inducedEquivalence"] == "equal-projected-coordinates"
        and observation["lost"] == "dropped-coordinate-distinction"
        and observation["reconstructionAvailable"] is False
    )


def _check_pareto_branch():
    source = _omega(native_identity="audit:pareto")
    a = _candidate("a", source, residualReduction=2, semanticLoss=1)
    b = _candidate("b", source, residualReduction=1, semanticLoss=0)
    return [item.candidate_id for item in pareto_frontier((a, b))] == ["a", "b"]


def _check_cycle_bound():
    program = parse_rmapl(
        """RMAPL 0
PROGRAM audit-cycle
LOAD fixture
BOUND maxCandidates=1
BOUND maxSteps=1
REPAIR loop
WHEN "loop-residual"
REQUIRES []
TARGETS ["loop-residual"]
PRESERVES ["state.protected"]
MAY_MUTATE []
FORBIDS ["provenance","evidence"]
APPLY loop_op
EVIDENCE []
COST 0
END
RUN
"""
    )
    source = _omega(
        native_identity="audit:cycle",
        residuals=({"kind": "loop-residual", "detail": "fixture"},),
        max_steps=1,
    )

    def loop_op(value):
        return {
            "omega": _updated(value),
            "consequenceKey": "same",
            "metrics": _runtime_metrics(),
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
            "reconstruction": {"status": "exact"},
        }

    result = run_program(program, source, {"loop_op": loop_op})
    return (
        result["stopReason"] == "REPEATED_STATE_CYCLE"
        and "REPEATED_STATE_CYCLE" in result["stopFacts"]
        and "RESOURCE_BOUND" in result["stopFacts"]
    )


def _check_hodge_ceiling():
    native = json.loads(
        (ROOT / "Hodge Span Lab" / "evidence" / "issue43_bridge_calibration_result.json")
        .read_text(encoding="utf-8")
    )
    omega = project_hodge_bridge(native)
    return (
        omega["evidence"][0]["kind"] == "candidate-test-only"
        and native["claim_ceiling"] in omega["claimCeiling"]
        and omega["path"] == native["source"]["actions"]
    )


def _check_suggestion_authority():
    native = {
        "carrierVersion": "s1-transition-carrier/v0",
        "kind": "generated",
        "move": {"plane": "xw", "degrees": 1},
        "prefix": [],
        "contract": {
            "initialState": "fixture",
            "mirrorId": "mirror:fixture",
            "shell": "comparison",
            "observer": {"yaw": 0, "pitch": 0, "roll": 0, "wPerspective": 0.35},
            "operatorVersion": "S'1-Ops v0",
        },
        "provenance": {
            "datasetVersion": "s1-suggest-dataset/v0",
            "modelVersion": "s1-suggest-transition/v0",
            "sourceExperienceIds": [],
            "strategy": "deterministic-fallback/v0",
        },
        "authority": "suggestion-only",
    }
    omega = project_suggestion_record(native)
    return (
        omega["evidence"][0]["kind"] == "suggestion-only"
        and "SUGGESTION != EXPERIENCE_AUTHORITY" in omega["claimCeiling"]
    )


def build_audit():
    checks = {
        "omegaStrict": _check_omega_strict(),
        "decisionFieldRoundTrip": _check_decision_field_round_trip(),
        "s1ChronologyDistinct": _check_s1_chronology(),
        "typedEvidenceNoAmplification": _check_typed_evidence(),
        "lossyQuotientExplicit": _check_lossy_quotient(),
        "paretoBranchPreserved": _check_pareto_branch(),
        "cycleBounded": _check_cycle_bound(),
        "hodgeCeilingPreserved": _check_hodge_ceiling(),
        "suggestionAuthorityPreserved": _check_suggestion_authority(),
    }
    return {
        "schema": "rmapl-omega-audit/v0",
        "profile": "RMAPL 0",
        "omegaSchema": "rmapl-omega/v0",
        "scientificValidation": False,
        "checks": checks,
        "scope": {
            "adapterDomains": [
                "decision-field",
                "s1-experience",
                "dimensional-ladder",
                "suggestion",
                "hodge-bridge",
            ],
            "runtime": "bounded-conditional-repair-reference",
            "globalCompletenessClaim": False,
            "rmalCoreFrontendClaim": False,
        },
        "claimCeiling": list(CLAIM_CEILING),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    audit = build_audit()
    if not all(audit["checks"].values()):
        failed = sorted(key for key, value in audit["checks"].items() if not value)
        parser.exit(1, f"RMAPL Omega audit failed checks: {failed}\n")

    text = canonical_audit_text(audit)

    if args.out:
        args.out.write_text(text, encoding="utf-8")

    if args.check:
        try:
            expected = EVIDENCE_PATH.read_text(encoding="utf-8")
        except OSError as exc:
            parser.exit(1, f"RMAPL Omega frozen evidence unavailable: {exc}\n")
        if expected != text:
            parser.exit(1, "RMAPL Omega frozen evidence does not match current audit\n")
        print("PASS RMAPL Omega audit: 9/9 bounded checks")
        return 0

    if not args.out:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
