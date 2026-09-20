"""Bounded conditional repair/fitting runtime for RMAPL v0.

The runtime is a reference execution model over Omega records.  It preserves
branches and provenance, uses claim-local evidence requirements, detects input
mutation, and stops with explicit bounded certificates.  It is not a universal
repair algorithm and does not amplify scientific authority.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, replace
import hashlib
import math
from typing import Any, Callable, Iterable, Mapping

from omega import canonical_json, make_inspection_record, validate_omega
from rmapl import FitterSpec, Program, RepairSpec


_MAXIMIZE = (
    "residualReduction",
    "invariantPreservation",
    "reconstructibility",
    "reversibility",
    "evidenceCoverage",
    "branchReduction",
    "provenanceCompleteness",
)
_MINIMIZE = (
    "semanticLoss",
    "ambiguityIntroduction",
    "relationGrowth",
    "runtimeCost",
    "economicCost",
    "unresolvedGrowth",
    "irreversibleMutation",
)
_METRIC_KEYS = _MAXIMIZE + _MINIMIZE

_STOP_PRECEDENCE = (
    "SUCCESS",
    "CERTIFIED_IMPOSSIBLE",
    "NO_ADMISSIBLE_PROGRESS",
    "REPEATED_STATE_CYCLE",
    "RESOURCE_BOUND",
    "EVIDENCE_BOUND",
    "OUTER_CONTROLLER_BOUND",
)


@dataclass(frozen=True)
class ClaimSpec:
    claim_id: str
    required_evidence: tuple[str, ...]
    forbidden_evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class KnowledgeDecay:
    loss: tuple[Any, ...] = ()
    introduction: tuple[Any, ...] = ()
    aliasing: tuple[Any, ...] = ()
    ambiguity: tuple[Any, ...] = ()
    provenance_gap: tuple[Any, ...] = ()
    reconstruction_cost: float = 0.0
    oracle_shift: tuple[Any, ...] = ()
    unresolved_growth: tuple[Any, ...] = ()


@dataclass(frozen=True)
class CandidateOutcome:
    candidate_id: str
    omega: dict[str, Any]
    consequence_key: str
    classification: str
    admitted: bool
    metrics: Mapping[str, float]
    knowledge_decay: KnowledgeDecay
    inspection: Mapping[str, Any]
    source_candidate_ids: tuple[str, ...]


def admit_claim(claim: ClaimSpec, evidence_kinds: Iterable[str]) -> bool:
    available = set(evidence_kinds)
    return set(claim.required_evidence) <= available and not (
        set(claim.forbidden_evidence) & available
    )


def _normalized_metrics(values: Mapping[str, Any], declared_cost: float = 0.0) -> dict[str, float]:
    if not isinstance(values, Mapping):
        raise TypeError("candidate metrics must be a mapping")
    if set(values) != set(_METRIC_KEYS):
        missing = sorted(set(_METRIC_KEYS) - set(values))
        extra = sorted(set(values) - set(_METRIC_KEYS))
        raise ValueError(f"candidate metrics mismatch: missing={missing}, extra={extra}")
    result: dict[str, float] = {}
    for key in _METRIC_KEYS:
        value = values[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"metric {key} must be numeric")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"metric {key} must be finite")
        result[key] = number
    result["runtimeCost"] = max(result["runtimeCost"], float(declared_cost))
    return result


def _dominates(left: CandidateOutcome, right: CandidateOutcome) -> bool:
    no_worse = all(left.metrics[key] >= right.metrics[key] for key in _MAXIMIZE)
    no_worse = no_worse and all(left.metrics[key] <= right.metrics[key] for key in _MINIMIZE)
    strictly = any(left.metrics[key] > right.metrics[key] for key in _MAXIMIZE)
    strictly = strictly or any(left.metrics[key] < right.metrics[key] for key in _MINIMIZE)
    return no_worse and strictly


def pareto_frontier(outcomes: Iterable[CandidateOutcome]) -> tuple[CandidateOutcome, ...]:
    ordered = tuple(sorted(outcomes, key=lambda item: item.candidate_id))
    frontier = []
    for candidate in ordered:
        if any(
            other.candidate_id != candidate.candidate_id and _dominates(other, candidate)
            for other in ordered
        ):
            continue
        frontier.append(candidate)
    return tuple(frontier)


def _knowledge_decay(value: Any) -> KnowledgeDecay:
    if isinstance(value, KnowledgeDecay):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("knowledgeDecay must be an object")
    allowed = {
        "loss",
        "introduction",
        "aliasing",
        "ambiguity",
        "provenanceGap",
        "reconstructionCost",
        "oracleShift",
        "unresolvedGrowth",
    }
    extra = set(value) - allowed
    if extra:
        raise ValueError(f"unsupported knowledgeDecay field(s): {sorted(extra)}")

    def seq(key: str) -> tuple[Any, ...]:
        raw = value.get(key, [])
        if not isinstance(raw, (list, tuple)):
            raise TypeError(f"knowledgeDecay {key} must be a list")
        return tuple(deepcopy(raw))

    cost = value.get("reconstructionCost", 0.0)
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(float(cost)) or float(cost) < 0:
        raise ValueError("knowledgeDecay reconstructionCost must be a non-negative finite number")
    return KnowledgeDecay(
        loss=seq("loss"),
        introduction=seq("introduction"),
        aliasing=seq("aliasing"),
        ambiguity=seq("ambiguity"),
        provenance_gap=seq("provenanceGap"),
        reconstruction_cost=float(cost),
        oracle_shift=seq("oracleShift"),
        unresolved_growth=seq("unresolvedGrowth"),
    )


def _evidence_kinds(omega: Mapping[str, Any]) -> set[str]:
    kinds = set()
    for record in omega.get("evidence", []):
        if isinstance(record, Mapping) and isinstance(record.get("kind"), str):
            kinds.add(record["kind"])
    return kinds


def _residual_kinds(omega: Mapping[str, Any]) -> set[str]:
    result = set()
    for record in omega.get("residuals", []):
        if isinstance(record, Mapping) and isinstance(record.get("kind"), str):
            result.add(record["kind"])
    return result


def _condition_tokens(omega: Mapping[str, Any]) -> set[str]:
    tokens = set(_evidence_kinds(omega))
    if omega.get("sourceRefs"):
        tokens.add("source.available")
    frame = omega.get("frame")
    if isinstance(frame, Mapping):
        conditions = frame.get("conditions", [])
        if isinstance(conditions, list):
            tokens.update(item for item in conditions if isinstance(item, str))
    for observation in omega.get("observations", []):
        if isinstance(observation, Mapping) and isinstance(observation.get("kind"), str):
            tokens.add(observation["kind"])
    return tokens


def _semantic_path(path: str) -> tuple[str, ...]:
    aliases = {
        "identity": ("nativeIdentity",),
        "claim-ceiling": ("claimCeiling",),
        "provenance": ("provenance",),
        "evidence": ("evidence",),
        "residuals": ("residuals",),
    }
    if path in aliases:
        return aliases[path]
    return tuple(path.split("."))


def _get_path(record: Any, path: str) -> Any:
    current = record
    for part in _semantic_path(path):
        if not isinstance(current, Mapping) or part not in current:
            return _MISSING
        current = current[part]
    return current


class _Missing:
    pass


_MISSING = _Missing()


def _changed_paths(original: Mapping[str, Any], candidate: Mapping[str, Any], paths: Iterable[str]) -> tuple[str, ...]:
    changed = []
    for path in paths:
        left = _get_path(original, path)
        right = _get_path(candidate, path)
        if left is _MISSING or right is _MISSING or canonical_json(left) != canonical_json(right):
            changed.append(path)
    return tuple(sorted(changed))


def _cycle_signature(omega: Mapping[str, Any], program: Program) -> str:
    payload = {
        "nativeIdentity": omega.get("nativeIdentity"),
        "sourceRefs": omega.get("sourceRefs"),
        "state": omega.get("state"),
        "residuals": omega.get("residuals"),
        "decisionField": omega.get("decisionField"),
        "claimCeiling": omega.get("claimCeiling"),
        "resourceBounds": omega.get("resourceBounds"),
        "program": program.program_id,
        "operators": sorted(
            [repair.operator for repair in program.repairs]
            + [fitter.operator for fitter in program.fitters]
        ),
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _bounds(program: Program, omega: Mapping[str, Any]) -> tuple[int, int]:
    source = dict(omega.get("resourceBounds", {}))
    source.update(program.bounds)

    def positive_int(name: str, default: int) -> int:
        raw = source.get(name, default)
        if type(raw) is not int or raw < 1:
            raise ValueError(f"{name} must be a positive integer")
        return raw

    return positive_int("maxCandidates", 32), positive_int("maxSteps", 1)


def _spec_id(spec: RepairSpec | FitterSpec) -> str:
    return spec.repair_id if isinstance(spec, RepairSpec) else spec.fitter_id


def _eligible_specs(
    program: Program,
    omega: Mapping[str, Any],
) -> tuple[list[RepairSpec | FitterSpec], list[RepairSpec | FitterSpec], int]:
    residuals = _residual_kinds(omega)
    conditions = _condition_tokens(omega)
    evidence = _evidence_kinds(omega)
    triggered: list[RepairSpec | FitterSpec] = []
    evidence_blocked: list[RepairSpec | FitterSpec] = []
    precondition_blocked = 0

    for spec in (*program.repairs, *program.fitters):
        if spec.trigger not in residuals:
            continue
        if not set(spec.requires) <= conditions:
            precondition_blocked += 1
            continue
        triggered.append(spec)
        if not set(spec.evidence) <= evidence:
            evidence_blocked.append(spec)

    eligible = [spec for spec in triggered if spec not in evidence_blocked]
    return eligible, evidence_blocked, precondition_blocked


def _proposal_outcome(
    *,
    spec: RepairSpec | FitterSpec,
    original: dict[str, Any],
    proposal: Mapping[str, Any],
) -> CandidateOutcome:
    if not isinstance(proposal, Mapping):
        raise TypeError("operator must return a proposal object")
    allowed = {"omega", "consequenceKey", "metrics", "knowledgeDecay", "reconstruction"}
    extra = set(proposal) - allowed
    if extra:
        raise ValueError(f"unsupported operator proposal field(s): {sorted(extra)}")
    candidate = validate_omega(proposal.get("omega"))
    consequence = proposal.get("consequenceKey")
    if not isinstance(consequence, str) or not consequence:
        raise ValueError("operator consequenceKey must be a non-empty string")
    reconstruction = proposal.get("reconstruction")
    if not isinstance(reconstruction, Mapping) or not isinstance(reconstruction.get("status"), str):
        raise ValueError("operator reconstruction status is required")

    preserves = spec.preserves
    forbidden = spec.forbids if isinstance(spec, RepairSpec) else ()
    changed_preserved = _changed_paths(original, candidate, preserves)
    changed_forbidden = _changed_paths(original, candidate, forbidden)

    if changed_preserved or changed_forbidden:
        classification = "MUTATION"
        admitted = False
    elif reconstruction["status"] == "exact":
        classification = "EXACT_REPAIR" if isinstance(spec, RepairSpec) else "VALID_REFIT"
        admitted = True
    elif reconstruction["status"] == "bounded":
        classification = "BOUNDED_REPAIR" if isinstance(spec, RepairSpec) else "LOSSY_REFIT"
        admitted = isinstance(spec, RepairSpec)
    else:
        classification = "FAILED"
        admitted = False

    decay = _knowledge_decay(proposal.get("knowledgeDecay", {}))
    metric_values = _normalized_metrics(proposal.get("metrics", {}), spec.cost)
    inspection = make_inspection_record(
        input_refs=original["sourceRefs"],
        native_contract=original["nativeType"],
        operator=_spec_id(spec),
        operator_version="RMAPL 0",
        condition=spec.trigger,
        trigger=spec.trigger,
        preconditions=list(spec.requires),
        obligation=original.get("frame"),
        expected={"targets": list(spec.targets) if isinstance(spec, RepairSpec) else []},
        actual={"classification": classification, "omegaId": candidate["id"]},
        residual_before=original["residuals"],
        residual_after=candidate["residuals"],
        preserved=[item for item in preserves if item not in changed_preserved],
        mutated=sorted(set(changed_preserved) | set(changed_forbidden)),
        lost=list(decay.loss),
        introduced=list(decay.introduction),
        reconstruction=dict(reconstruction),
        knowledge_decay={
            "loss": list(decay.loss),
            "introduction": list(decay.introduction),
            "aliasing": list(decay.aliasing),
            "ambiguity": list(decay.ambiguity),
            "provenanceGap": list(decay.provenance_gap),
            "reconstructionCost": decay.reconstruction_cost,
            "oracleShift": list(decay.oracle_shift),
            "unresolvedGrowth": list(decay.unresolved_growth),
        },
        evidence=original["evidence"],
        claim_ceiling=original["claimCeiling"],
        counterprobe={"status": "not-executed-by-operator", "required": True},
        provenance=original["provenance"],
        resource_bounds=original["resourceBounds"],
        resource_usage={"runtimeCost": metric_values["runtimeCost"]},
        unresolved=candidate["residuals"],
        next_decision=None,
        domain_remainder=candidate["domainRemainder"],
        gates=[
            {"name": "preserves", "status": "passed" if not changed_preserved else "failed"},
            {"name": "forbids", "status": "passed" if not changed_forbidden else "failed"},
            {"name": "reconstruction", "status": reconstruction["status"]},
        ],
    )
    return CandidateOutcome(
        candidate_id=_spec_id(spec),
        omega=candidate,
        consequence_key=consequence,
        classification=classification,
        admitted=admitted,
        metrics=metric_values,
        knowledge_decay=decay,
        inspection=inspection,
        source_candidate_ids=(_spec_id(spec),),
    )


def _execute_spec(
    spec: RepairSpec | FitterSpec,
    omega: dict[str, Any],
    registry: Mapping[str, Callable[[dict[str, Any]], Mapping[str, Any]]],
) -> CandidateOutcome:
    operator = registry.get(spec.operator)
    if operator is None:
        raise ValueError(f"operator registry is missing {spec.operator!r}")
    working = deepcopy(validate_omega(omega))
    before = canonical_json(working)
    proposal = operator(working)
    after = canonical_json(working)
    if after != before:
        raise ValueError(f"operator {spec.operator!r} mutated input Omega record")
    return _proposal_outcome(spec=spec, original=omega, proposal=proposal)


def _merge_equivalence_class(members: list[CandidateOutcome]) -> CandidateOutcome:
    members = sorted(members, key=lambda item: (not item.admitted, item.candidate_id))
    representative = members[0]
    ids = tuple(sorted({cid for item in members for cid in item.source_candidate_ids}))
    inspection = dict(representative.inspection)
    inspection["equivalentCandidateIds"] = list(ids)
    return replace(
        representative,
        source_candidate_ids=ids,
        inspection=inspection,
    )


def _quotient(outcomes: Iterable[CandidateOutcome]) -> tuple[CandidateOutcome, ...]:
    # Consequence equality alone is insufficient: a candidate that violates a
    # protected invariant is not equivalent to an admitted repair even when
    # both advertise the same downstream consequence.
    groups: dict[tuple[str, str, bool], list[CandidateOutcome]] = {}
    for outcome in outcomes:
        key = (outcome.consequence_key, outcome.classification, outcome.admitted)
        groups.setdefault(key, []).append(outcome)
    return tuple(
        _merge_equivalence_class(groups[key])
        for key in sorted(groups)
    )


def _outcome_dict(outcome: CandidateOutcome) -> dict[str, Any]:
    return {
        "candidateId": outcome.candidate_id,
        "sourceCandidateIds": list(outcome.source_candidate_ids),
        "omegaId": outcome.omega["id"],
        "consequenceKey": outcome.consequence_key,
        "classification": outcome.classification,
        "admitted": outcome.admitted,
        "metrics": dict(outcome.metrics),
        "knowledgeDecay": {
            "loss": list(outcome.knowledge_decay.loss),
            "introduction": list(outcome.knowledge_decay.introduction),
            "aliasing": list(outcome.knowledge_decay.aliasing),
            "ambiguity": list(outcome.knowledge_decay.ambiguity),
            "provenanceGap": list(outcome.knowledge_decay.provenance_gap),
            "reconstructionCost": outcome.knowledge_decay.reconstruction_cost,
            "oracleShift": list(outcome.knowledge_decay.oracle_shift),
            "unresolvedGrowth": list(outcome.knowledge_decay.unresolved_growth),
        },
        "inspection": dict(outcome.inspection),
        "omega": outcome.omega,
    }


def _stop_reason(facts: set[str]) -> str | None:
    return next((name for name in _STOP_PRECEDENCE if name in facts), None)


def run_program(
    program: Program,
    omega: dict[str, Any],
    registry: Mapping[str, Callable[[dict[str, Any]], Mapping[str, Any]]],
) -> dict[str, Any]:
    if not isinstance(program, Program):
        raise TypeError("program must be parsed RMAPL Program")
    current = [validate_omega(omega)]
    max_candidates, max_steps = _bounds(program, current[0])
    seen = {_cycle_signature(current[0], program)}

    generation = {
        "generationScope": "declared-trigger-precondition-evidence-bounds",
        "maxCandidates": max_candidates,
        "maxSteps": max_steps,
        "generatedCount": 0,
        "equivalenceClassCount": 0,
        "executedCount": 0,
        "prunedCount": 0,
        "evidenceBlockedCount": 0,
        "preconditionBlockedCount": 0,
        "truncationReason": None,
        "stepsExecuted": 0,
    }
    latest: tuple[CandidateOutcome, ...] = ()
    stop_facts: set[str] = set()

    for step in range(1, max_steps + 1):
        generation["stepsExecuted"] = step
        raw_outcomes: list[CandidateOutcome] = []
        evidence_blocked_this_step = 0
        triggered_this_step = 0

        for current_omega in current:
            eligible, evidence_blocked, precondition_blocked = _eligible_specs(program, current_omega)
            triggered_this_step += len(eligible) + len(evidence_blocked)
            generation["generatedCount"] += len(eligible) + len(evidence_blocked)
            generation["evidenceBlockedCount"] += len(evidence_blocked)
            generation["preconditionBlockedCount"] += precondition_blocked
            evidence_blocked_this_step += len(evidence_blocked)

            eligible = sorted(eligible, key=_spec_id)
            if len(eligible) > max_candidates:
                generation["prunedCount"] += len(eligible) - max_candidates
                generation["truncationReason"] = "maxCandidates"
                eligible = eligible[:max_candidates]

            for spec in eligible:
                raw_outcomes.append(_execute_spec(spec, current_omega, registry))
                generation["executedCount"] += 1

        if not raw_outcomes:
            if evidence_blocked_this_step and triggered_this_step:
                stop_facts.add("EVIDENCE_BOUND")
            else:
                stop_facts.add("NO_ADMISSIBLE_PROGRESS")
            latest = ()
            break

        quotiented = _quotient(raw_outcomes)
        generation["equivalenceClassCount"] += len(quotiented)

        # Rejected candidates remain inspectable, but they cannot dominate an
        # admissible repair/fitter in the planning frontier.
        admitted_candidates = tuple(item for item in quotiented if item.admitted)
        rejected_candidates = tuple(
            sorted(
                (item for item in quotiented if not item.admitted),
                key=lambda item: item.candidate_id,
            )
        )
        admitted_frontier = pareto_frontier(admitted_candidates)
        latest = admitted_frontier + rejected_candidates

        admitted = list(admitted_frontier)
        if any(not item.omega["residuals"] for item in admitted):
            stop_facts.add("SUCCESS")

        cycle_outcomes = [
            item for item in admitted
            if _cycle_signature(item.omega, program) in seen
        ]
        if cycle_outcomes:
            stop_facts.add("REPEATED_STATE_CYCLE")

        noncycle = [
            item for item in admitted
            if _cycle_signature(item.omega, program) not in seen
            and item.omega["residuals"]
        ]

        if not admitted and "SUCCESS" not in stop_facts:
            stop_facts.add("NO_ADMISSIBLE_PROGRESS")

        if step >= max_steps:
            stop_facts.add("RESOURCE_BOUND")

        if stop_facts & {
            "SUCCESS",
            "CERTIFIED_IMPOSSIBLE",
            "NO_ADMISSIBLE_PROGRESS",
            "REPEATED_STATE_CYCLE",
            "RESOURCE_BOUND",
            "EVIDENCE_BOUND",
            "OUTER_CONTROLLER_BOUND",
        }:
            break

        for item in noncycle:
            seen.add(_cycle_signature(item.omega, program))
        current = [item.omega for item in noncycle]
        if not current:
            stop_facts.add("NO_ADMISSIBLE_PROGRESS")
            break

    return {
        "schema": "rmapl-runtime-result/v0",
        "program": program.program_id,
        "initialOmegaId": validate_omega(omega)["id"],
        "generation": generation,
        "branches": [_outcome_dict(item) for item in latest],
        "stopFacts": [name for name in _STOP_PRECEDENCE if name in stop_facts],
        "stopReason": _stop_reason(stop_facts),
        "claimCeiling": [
            "MAXIMAL_WITHIN_DECLARED_SCOPE != GLOBAL_COMPLETENESS",
            "RMAPL_PROFILE != RMAL_CORE_FRONTEND",
            "METHOD_TRANSFER != EVIDENCE_TRANSFER",
        ],
    }
