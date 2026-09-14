from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
import json
from typing import Any


class Capability:
    TRANSITION = "transition"
    OBSERVE = "observe"
    INFER = "infer"
    MONITOR = "monitor"
    DECIDE = "decide"
    REMEMBER = "remember"
    SCHEDULE = "schedule"
    ENCODE = "encode"
    VERIFY = "verify"


OPERATIONAL_CAPABILITIES = frozenset({
    Capability.TRANSITION,
    Capability.OBSERVE,
    Capability.INFER,
    Capability.MONITOR,
    Capability.DECIDE,
    Capability.REMEMBER,
    Capability.SCHEDULE,
})
SIDECARS = frozenset({Capability.ENCODE, Capability.VERIFY})
ALL_CAPABILITIES = OPERATIONAL_CAPABILITIES | SIDECARS


class StepPhase(str, Enum):
    PRE_ACTION = "PRE_ACTION"
    TRANSITION = "TRANSITION"
    OBSERVATION = "OBSERVATION"
    KNOWLEDGE_UPDATE = "KNOWLEDGE_UPDATE"
    MONITOR_UPDATE = "MONITOR_UPDATE"
    MEMORY_UPDATE = "MEMORY_UPDATE"


class FailureKind(str, Enum):
    INCOMPATIBLE = "INCOMPATIBLE"
    UNSATISFIED = "UNSATISFIED"
    UNRESOLVED = "UNRESOLVED"
    DOMINATED = "DOMINATED"
    OUT_OF_BOUND = "OUT_OF_BOUND"
    VERIFIER_DISAGREEMENT = "VERIFIER_DISAGREEMENT"


def _nonempty_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")


def _validate_pairs(items: tuple[tuple[str, Any], ...], label: str, *, int_values: bool = False) -> None:
    seen: set[str] = set()
    for key, value in items:
        _nonempty_text(key, f"{label} key")
        if key in seen:
            raise ValueError(f"duplicate {label} key: {key}")
        seen.add(key)
        if int_values and (type(value) is not int or value < 0):
            raise ValueError(f"{label} values must be nonnegative integers")


@dataclass(frozen=True)
class CostVector:
    items: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        _validate_pairs(self.items, "cost", int_values=True)
        if tuple(sorted(self.items)) != self.items:
            raise ValueError("cost items must be canonically sorted")
        if not self.items:
            raise ValueError("cost vector cannot be empty")

    @classmethod
    def from_mapping(cls, values: dict[str, int]) -> "CostVector":
        if not isinstance(values, dict):
            raise ValueError("cost mapping must be a dict")
        return cls(tuple(sorted(values.items())))

    def dimensions(self) -> tuple[str, ...]:
        return tuple(key for key, _ in self.items)

    def as_dict(self) -> dict[str, int]:
        return dict(self.items)

    def dominates(self, other: "CostVector") -> bool:
        if not isinstance(other, CostVector):
            raise ValueError("can only compare CostVector")
        if self.dimensions() != other.dimensions():
            raise ValueError("cost dimensions differ")
        le = all(a <= b for (_, a), (_, b) in zip(self.items, other.items))
        lt = any(a < b for (_, a), (_, b) in zip(self.items, other.items))
        return le and lt


@dataclass(frozen=True)
class ObligationSpec:
    stable_id: str
    version: int
    subject: str
    bounds: tuple[tuple[str, int], ...]
    required_capabilities: tuple[str, ...]
    protected_invariants: tuple[str, ...]
    success_condition: str
    allowed_initial: tuple[int, ...]
    allowed_actions: tuple[int, ...]
    observable_information: tuple[str, ...]
    permissions: tuple[str, ...]
    temporal_semantics: str
    step_timing: tuple[StepPhase, ...]
    exact_regime: bool
    evidence_threshold: str
    unresolved_remainder: tuple[str, ...]
    cost_dimensions: tuple[str, ...]

    def __post_init__(self) -> None:
        _nonempty_text(self.stable_id, "obligation id")
        if type(self.version) is not int or self.version < 1:
            raise ValueError("obligation version must be >= 1")
        _nonempty_text(self.subject, "subject")
        _validate_pairs(self.bounds, "bound", int_values=True)
        if not self.required_capabilities:
            raise ValueError("obligation must require at least one operational capability")
        unknown = set(self.required_capabilities) - OPERATIONAL_CAPABILITIES
        if unknown:
            raise ValueError(f"unknown or non-operational required capabilities: {sorted(unknown)}")
        if len(set(self.required_capabilities)) != len(self.required_capabilities):
            raise ValueError("duplicate required capability")
        _nonempty_text(self.success_condition, "success condition")
        _nonempty_text(self.temporal_semantics, "temporal semantics")
        if not self.step_timing:
            raise ValueError("temporal obligations require explicit step timing")
        if any(not isinstance(phase, StepPhase) for phase in self.step_timing):
            raise ValueError("step timing entries must be StepPhase values")
        if len(set(self.step_timing)) != len(self.step_timing):
            raise ValueError("step timing cannot repeat phases")
        if type(self.exact_regime) is not bool:
            raise ValueError("exact_regime must be bool")
        _nonempty_text(self.evidence_threshold, "evidence threshold")
        if not self.cost_dimensions or len(set(self.cost_dimensions)) != len(self.cost_dimensions):
            raise ValueError("cost dimensions must be nonempty and unique")
        for dim in self.cost_dimensions:
            _nonempty_text(dim, "cost dimension")


@dataclass(frozen=True)
class PartSpec:
    stable_id: str
    version: int
    provides: tuple[str, ...]
    requires: tuple[str, ...]
    input_ports: tuple[tuple[str, str], ...]
    output_ports: tuple[tuple[str, str], ...]
    state_carried: tuple[str, ...]
    assumptions: tuple[str, ...]
    bounds: tuple[tuple[str, int], ...]
    side_effects: tuple[str, ...]
    external_dependencies: tuple[str, ...]
    cost: CostVector
    evidence_refs: tuple[str, ...]
    known_failures: tuple[str, ...]
    replaceability_boundary: str

    def __post_init__(self) -> None:
        _nonempty_text(self.stable_id, "part id")
        if type(self.version) is not int or self.version < 1:
            raise ValueError("part version must be >= 1")
        if not self.provides:
            raise ValueError("part must provide at least one capability")
        unknown = set(self.provides) | set(self.requires)
        unknown -= ALL_CAPABILITIES
        if unknown:
            raise ValueError(f"unknown capabilities: {sorted(unknown)}")
        if len(set(self.provides)) != len(self.provides) or len(set(self.requires)) != len(self.requires):
            raise ValueError("capability lists cannot contain duplicates")
        overlap = set(self.provides) & set(self.requires)
        if overlap:
            raise ValueError(f"self construction dependency: {sorted(overlap)}")
        _validate_pairs(self.input_ports, "input port")
        _validate_pairs(self.output_ports, "output port")
        _validate_pairs(self.bounds, "bound", int_values=True)
        _nonempty_text(self.replaceability_boundary, "replaceability boundary")


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    failure_kind: FailureKind | None
    detail: str
    evidence_refs: tuple[str, ...] = ()
    metrics: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        if type(self.passed) is not bool:
            raise ValueError("passed must be bool")
        _nonempty_text(self.detail, "verification detail")
        if self.passed and self.failure_kind is not None:
            raise ValueError("passing result cannot have failure kind")
        if not self.passed and self.failure_kind is None:
            raise ValueError("failing result requires failure kind")
        _validate_pairs(self.metrics, "metric", int_values=True)

    @classmethod
    def pass_result(cls, detail: str, *, evidence_refs: tuple[str, ...] = (), metrics: tuple[tuple[str, int], ...] = ()) -> "VerificationResult":
        return cls(True, None, detail, evidence_refs, tuple(sorted(metrics)))

    @classmethod
    def fail(cls, kind: FailureKind, detail: str, *, evidence_refs: tuple[str, ...] = (), metrics: tuple[tuple[str, int], ...] = ()) -> "VerificationResult":
        return cls(False, kind, detail, evidence_refs, tuple(sorted(metrics)))


@dataclass(frozen=True)
class AssemblySpec:
    stable_id: str
    version: int
    obligation_id: str
    obligation_version: int
    parts: tuple[tuple[str, int], ...]
    wiring: tuple[tuple[str, str, str, str], ...]
    covered_capabilities: tuple[str, ...]
    unresolved_gaps: tuple[str, ...]
    cost: CostVector
    verification: VerificationResult | None = None
    evidence_refs: tuple[str, ...] = ()
    search_provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _nonempty_text(self.stable_id, "assembly id")
        _nonempty_text(self.obligation_id, "obligation id")
        if type(self.version) is not int or self.version < 1 or type(self.obligation_version) is not int or self.obligation_version < 1:
            raise ValueError("versions must be >= 1")
        if not self.parts:
            raise ValueError("assembly requires at least one part")
        if len(set(self.parts)) != len(self.parts):
            raise ValueError("assembly cannot contain duplicate part versions")
        unknown = set(self.covered_capabilities) - OPERATIONAL_CAPABILITIES
        if unknown:
            raise ValueError(f"assembly covered capabilities must be operational: {sorted(unknown)}")


@dataclass(frozen=True)
class EmergentEffectCertificate:
    stable_id: str
    version: int
    assembly_id: str
    obligation_id: str
    effect: str
    verifier_ref: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for value, label in ((self.stable_id, "effect id"), (self.assembly_id, "assembly id"), (self.obligation_id, "obligation id"), (self.effect, "effect"), (self.verifier_ref, "verifier ref")):
            _nonempty_text(value, label)
        if type(self.version) is not int or self.version < 1:
            raise ValueError("effect version must be >= 1")
        if not self.evidence_refs:
            raise ValueError("emergent effect requires evidence references")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {k: _jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
