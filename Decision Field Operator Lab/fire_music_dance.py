"""Dynamic FIRE + Music + Dance research-control carrier.

Method infrastructure only.  It schedules transformations, preserves failures,
tracks survivors, learns from prior outcomes, and keeps a way home.  It does
not turn a metaphor, schedule, relation, or software test into domain evidence.

Core cycle:
OBSERVE -> GO_LOWER -> EXPOSE -> FUEL -> BURN
-> ASH / SMOKE / EMBER -> SURVIVOR -> RECONSTITUTE
-> GO_HIGHER -> HOMEWARD -> REST/SLEEP -> REOBSERVE -> DELTA
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from enum import Enum
import hashlib
import json
import math
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "fire-music-dance-dynamic-field/v1"
METHOD_AUTHORITY = "method-only"

BOUNDARIES = (
    "GENERATE != VERIFY != ADMIT",
    "METHOD_TRANSFER != EVIDENCE_TRANSFER",
    "SOFTWARE_VERIFICATION != DOMAIN_PROOF",
    "RELATION != SUPPORT",
    "FAILED_REPRESENTATION != FAILED_OBJECT",
    "ATTACKABILITY != FALSITY",
    "MUSIC != TRUTH",
    "DANCE != TRUTH",
    "DELTA_ZERO_IS_LOCAL_NOT_GLOBAL",
    "UNKNOWN != ZERO",
    "OBJECT_IDENTITY_IS_INVARIANT",
    "COORDINATES_AND_CARRIERS_ARE_NEGOTIABLE",
)

ALL_WAYS = (
    "FORWARD", "BACKWARD", "UP", "DOWN", "SIDEWAYS", "INWARD",
    "OUTWARD", "AROUND", "THROUGH", "REVERSE", "BRANCH", "HOMEWARD",
)


class Triad(str, Enum):
    DARK = "DARK"
    MIDDLE = "MIDDLE"
    LIGHT = "LIGHT"


class FireStage(str, Enum):
    OBSERVE = "OBSERVE"
    GO_LOWER = "GO_LOWER"
    EXPOSE = "EXPOSE"
    FUEL = "FUEL"
    BURN = "BURN"
    SMOKE = "SMOKE"
    ASH = "ASH"
    EMBER = "EMBER"
    SURVIVOR = "SURVIVOR"
    RECONSTITUTE = "RECONSTITUTE"
    GO_HIGHER = "GO_HIGHER"
    HOMEWARD = "HOMEWARD"
    REST = "REST"
    SLEEP = "SLEEP"
    REOBSERVE = "REOBSERVE"
    CLOSED = "CLOSED"


class Verification(str, Enum):
    GENERATED = "GENERATED"
    VERIFIED_LOCAL = "VERIFIED_LOCAL"
    REFUTED_LOCAL = "REFUTED_LOCAL"
    UNRESOLVED = "UNRESOLVED"
    ADMITTED = "ADMITTED"


class DeltaStatus(str, Enum):
    DELTA_ZERO = "DELTA_ZERO"
    DELTA_NONZERO = "DELTA_NONZERO"
    UNKNOWN = "UNKNOWN"


class Outcome(str, Enum):
    ASH = "ASH"
    EMBER = "EMBER"
    SMOKE = "SMOKE"


@dataclass(frozen=True)
class Mutation:
    path: str
    before: Any
    after: Any
    operator: str = "SET"
    direction: str = "SIDEWAYS"

    def validate(self) -> None:
        if not self.path:
            raise ValueError("mutation path must be non-empty")
        if self.direction not in ALL_WAYS:
            raise ValueError(f"unsupported direction: {self.direction}")
        if self.before == self.after:
            raise ValueError("mutation must change exactly one value")


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    status: str
    observation: str
    evidence_refs: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.status not in {"PASS", "FAIL", "UNRESOLVED"}:
            raise ValueError(f"unsupported check status: {self.status}")
        if not self.check_id or not self.observation:
            raise ValueError("check_id and observation must be non-empty")


@dataclass(frozen=True)
class Delta:
    status: DeltaStatus
    changed_paths: tuple[str, ...]
    protected_violations: tuple[str, ...]
    unresolved: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class MusicPulse:
    index: int
    beat: int
    bar: int
    operator: str
    phase: str


@dataclass(frozen=True)
class DanceStep:
    index: int
    direction: str
    mutation: Mutation | None
    note: str = ""

    def validate(self) -> None:
        if self.direction not in ALL_WAYS:
            raise ValueError(f"unsupported dance direction: {self.direction}")
        if self.mutation is not None:
            self.mutation.validate()
            if self.mutation.direction != self.direction:
                raise ValueError("dance direction and mutation direction must agree")


@dataclass(frozen=True)
class Experience:
    signature: str
    operator: str
    direction: str
    outcome: Outcome
    candidate_id: str
    novelty_before: float


@dataclass(frozen=True)
class Candidate:
    object_id: str
    candidate_id: str
    parent_id: str | None
    stage: FireStage
    triad: Triad
    verification: Verification
    surface: Mapping[str, Any]
    knowledge: Mapping[str, Any]
    invariants: Mapping[str, Any]
    provenance: tuple[str, ...]
    evidence_refs: tuple[str, ...] = ()
    mutation: Mutation | None = None
    remainder: tuple[str, ...] = ()
    admitted: bool = False
    resting: bool = False


@dataclass
class ExperienceMemory:
    """Bounded control learning and habituation, never a truth score."""
    experiences: list[Experience] = field(default_factory=list)
    signature_counts: dict[str, int] = field(default_factory=dict)

    def novelty(self, signature: str) -> float:
        return 1.0 / (1.0 + self.signature_counts.get(signature, 0))

    def record(self, *, signature: str, operator: str, direction: str,
               outcome: Outcome, candidate_id: str) -> Experience:
        exp = Experience(
            signature, operator, direction, outcome, candidate_id,
            self.novelty(signature),
        )
        self.experiences.append(exp)
        self.signature_counts[signature] = self.signature_counts.get(signature, 0) + 1
        return exp

    def route_score(self, operator: str, direction: str) -> tuple[float, int, str, str]:
        rows = [e for e in self.experiences
                if e.operator == operator and e.direction == direction]
        ember = sum(e.outcome == Outcome.EMBER for e in rows)
        ash = sum(e.outcome == Outcome.ASH for e in rows)
        smoke = sum(e.outcome == Outcome.SMOKE for e in rows)
        return ((2.0 * ember) - ash - (0.25 * smoke), -len(rows), operator, direction)

    def recommend(self, routes: Iterable[tuple[str, str]]) -> tuple[str, str] | None:
        routes = tuple(routes)
        return None if not routes else max(routes, key=lambda row: self.route_score(*row))


@dataclass
class DynamicFireField:
    root: Candidate
    candidates: dict[str, Candidate] = field(default_factory=dict)
    ash: list[str] = field(default_factory=list)
    embers: list[str] = field(default_factory=list)
    survivors: list[str] = field(default_factory=list)
    memory: ExperienceMemory = field(default_factory=ExperienceMemory)
    trace: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.candidates.setdefault(self.root.candidate_id, self.root)
        self._assert_object_identity()

    @classmethod
    def create(cls, *, object_id: str, surface: Mapping[str, Any],
               invariants: Mapping[str, Any], provenance: Sequence[str],
               triad: Triad = Triad.MIDDLE) -> "DynamicFireField":
        if not object_id:
            raise ValueError("object_id must be non-empty")
        root_base = {
            "object_id": object_id,
            "surface": _normalize(surface),
            "invariants": _normalize(invariants),
            "provenance": tuple(provenance),
        }
        cid = _digest(root_base)
        root = Candidate(
            object_id=object_id,
            candidate_id=cid,
            parent_id=None,
            stage=FireStage.OBSERVE,
            triad=triad,
            verification=Verification.GENERATED,
            surface=deepcopy(root_base["surface"]),
            knowledge={},
            invariants=deepcopy(root_base["invariants"]),
            provenance=tuple(provenance),
        )
        return cls(root=root)

    def get(self, candidate_id: str) -> Candidate:
        return self.candidates[candidate_id]

    def generate(self, parent_id: str, mutation: Mutation | Sequence[Mutation], *,
                 triad: Triad | None = None, stage: FireStage = FireStage.FUEL,
                 provenance: Sequence[str] = (), allow_wide: bool = False) -> Candidate:
        parent = self.get(parent_id)
        if parent.resting:
            raise RuntimeError("cannot mutate a resting/sleeping candidate; wake it first")
        mutations = (mutation,) if isinstance(mutation, Mutation) else tuple(mutation)
        if not mutations:
            raise ValueError("at least one mutation is required")
        for item in mutations:
            item.validate()
        if len(mutations) != 1 and not allow_wide:
            raise ValueError("one-degree rule: exactly one mutation unless allow_wide=True")

        surface = deepcopy(parent.surface)
        for item in mutations:
            current = _get_path(surface, item.path)
            if current != item.before:
                raise ValueError(
                    f"mutation before-value mismatch for {item.path}: "
                    f"expected {item.before!r}, got {current!r}"
                )
            _set_path(surface, item.path, deepcopy(item.after))

        payload = {
            "schema": SCHEMA, "object_id": parent.object_id,
            "parent_id": parent.candidate_id, "surface": surface,
            "mutations": [asdict(m) for m in mutations],
            "triad": (triad or parent.triad).value,
            "wide": len(mutations) != 1,
        }
        cid = _digest(payload)
        child = Candidate(
            object_id=parent.object_id,
            candidate_id=cid,
            parent_id=parent.candidate_id,
            stage=stage,
            triad=triad or parent.triad,
            verification=Verification.GENERATED,
            surface=surface,
            knowledge=deepcopy(parent.knowledge),
            invariants=deepcopy(parent.invariants),
            provenance=tuple(parent.provenance) + tuple(provenance),
            mutation=mutations[0] if len(mutations) == 1 else None,
            remainder=tuple(parent.remainder),
        )
        self.candidates[cid] = child
        self._trace("GENERATE", child, {
            "mutations": [asdict(m) for m in mutations],
            "wide": len(mutations) != 1,
        })
        self._assert_object_identity()
        return child

    def burn(self, candidate_id: str, checks: Sequence[CheckResult]) -> Candidate:
        candidate = self.get(candidate_id)
        if not checks:
            raise ValueError("BURN requires at least one explicit check")
        for check in checks:
            check.validate()
        statuses = {c.status for c in checks}
        if "FAIL" in statuses:
            outcome, verification, stage = Outcome.ASH, Verification.REFUTED_LOCAL, FireStage.ASH
            self.ash.append(candidate_id)
        elif "UNRESOLVED" in statuses:
            outcome, verification, stage = Outcome.SMOKE, Verification.UNRESOLVED, FireStage.SMOKE
        else:
            outcome, verification, stage = Outcome.EMBER, Verification.VERIFIED_LOCAL, FireStage.EMBER
            self.embers.append(candidate_id)

        refs = tuple(ref for c in checks for ref in c.evidence_refs)
        remainder = tuple(c.observation for c in checks if c.status != "PASS")
        updated = replace(
            candidate, stage=stage, verification=verification,
            evidence_refs=tuple(candidate.evidence_refs) + refs,
            remainder=remainder,
        )
        self.candidates[candidate_id] = updated
        if updated.mutation is not None:
            self.memory.record(
                signature=mutation_signature(updated.mutation),
                operator=updated.mutation.operator,
                direction=updated.mutation.direction,
                outcome=outcome,
                candidate_id=candidate_id,
            )
        self._trace("BURN", updated, {
            "outcome": outcome.value,
            "checks": [asdict(c) for c in checks],
        })
        return updated

    def mark_survivor(self, candidate_id: str) -> Candidate:
        candidate = self.get(candidate_id)
        if candidate.verification != Verification.VERIFIED_LOCAL:
            raise ValueError("only locally verified EMBER candidates can become SURVIVOR")
        updated = replace(candidate, stage=FireStage.SURVIVOR)
        self.candidates[candidate_id] = updated
        if candidate_id not in self.survivors:
            self.survivors.append(candidate_id)
        self._trace("SURVIVOR", updated, {})
        return updated

    def admit(self, candidate_id: str, *, authority: str,
              evidence_refs: Sequence[str]) -> Candidate:
        candidate = self.get(candidate_id)
        if candidate.stage not in {
            FireStage.SURVIVOR, FireStage.RECONSTITUTE, FireStage.GO_HIGHER
        }:
            raise ValueError("candidate must survive verification before admission")
        if not authority:
            raise ValueError("admission requires explicit authority")
        if not evidence_refs:
            raise ValueError("admission requires evidence references")
        updated = replace(
            candidate,
            verification=Verification.ADMITTED,
            admitted=True,
            evidence_refs=tuple(candidate.evidence_refs) + tuple(evidence_refs),
            knowledge={**deepcopy(candidate.knowledge), "admission_authority": authority},
        )
        self.candidates[candidate_id] = updated
        self._trace("ADMIT", updated, {
            "authority": authority,
            "evidence_refs": list(evidence_refs),
        })
        return updated

    def reconstitute(self, survivor_id: str, *, knowledge_patch: Mapping[str, Any],
                     provenance: Sequence[str] = ()) -> Candidate:
        survivor = self.get(survivor_id)
        if survivor.stage != FireStage.SURVIVOR:
            raise ValueError("RECONSTITUTE requires a SURVIVOR")
        knowledge = {**deepcopy(survivor.knowledge), **_normalize(knowledge_patch)}
        cid = _digest({
            "object_id": survivor.object_id,
            "parent_id": survivor.candidate_id,
            "surface": survivor.surface,
            "knowledge": knowledge,
            "stage": FireStage.RECONSTITUTE.value,
        })
        rebuilt = replace(
            survivor,
            candidate_id=cid,
            parent_id=survivor.candidate_id,
            stage=FireStage.RECONSTITUTE,
            knowledge=knowledge,
            provenance=tuple(survivor.provenance) + tuple(provenance),
            mutation=None,
            admitted=False,
        )
        self.candidates[cid] = rebuilt
        self._trace("RECONSTITUTE", rebuilt, {
            "from": survivor_id,
            "knowledge_patch": _normalize(knowledge_patch),
        })
        self._assert_object_identity()
        return rebuilt

    def homeward(self, candidate_id: str) -> Candidate:
        candidate = self.get(candidate_id)
        cid = _digest({
            "object_id": self.root.object_id,
            "root_surface": self.root.surface,
            "knowledge": candidate.knowledge,
            "evidence_refs": candidate.evidence_refs,
            "from": candidate_id,
        })
        home = Candidate(
            object_id=self.root.object_id,
            candidate_id=cid,
            parent_id=candidate_id,
            stage=FireStage.HOMEWARD,
            triad=Triad.MIDDLE,
            verification=candidate.verification,
            surface=deepcopy(self.root.surface),
            knowledge=deepcopy(candidate.knowledge),
            invariants=deepcopy(self.root.invariants),
            provenance=tuple(candidate.provenance) + (f"HOMEWARD:{candidate_id}",),
            evidence_refs=tuple(candidate.evidence_refs),
            remainder=tuple(candidate.remainder),
            admitted=candidate.admitted,
        )
        self.candidates[cid] = home
        self._trace("HOMEWARD", home, {"from": candidate_id, "to_root_surface": True})
        self._assert_object_identity()
        return home

    def sleep(self, candidate_id: str) -> Candidate:
        candidate = self.get(candidate_id)
        updated = replace(candidate, stage=FireStage.SLEEP, resting=True)
        self.candidates[candidate_id] = updated
        self._trace("SLEEP", updated, {})
        return updated

    def wake(self, candidate_id: str, *, trigger: str) -> Candidate:
        candidate = self.get(candidate_id)
        if not candidate.resting:
            raise ValueError("candidate is not sleeping/resting")
        if not trigger:
            raise ValueError("wake requires a new observation/obligation trigger")
        updated = replace(
            candidate,
            stage=FireStage.REOBSERVE,
            resting=False,
            provenance=tuple(candidate.provenance) + (f"WAKE:{trigger}",),
        )
        self.candidates[candidate_id] = updated
        self._trace("WAKE", updated, {"trigger": trigger})
        return updated

    def compare(self, before_id: str, after_id: str, *,
                consequential_paths: Sequence[str],
                unresolved: Sequence[str] = ()) -> Delta:
        before, after = self.get(before_id), self.get(after_id)
        if before.object_id != after.object_id:
            raise ValueError("cannot compare different objects")
        unresolved = tuple(unresolved)
        changed, protected = [], []
        for path in consequential_paths:
            try:
                lhs, rhs = _get_path(before.surface, path), _get_path(after.surface, path)
            except (KeyError, TypeError):
                protected.append(path)
                continue
            if lhs != rhs:
                changed.append(path)
        protected.extend(_invariant_violations(after.surface, after.invariants))
        if unresolved or protected:
            status = DeltaStatus.UNKNOWN
            note = "comparison has unresolved observations or invariant/measurement gaps"
        elif changed:
            status = DeltaStatus.DELTA_NONZERO
            note = "consequential difference observed"
        else:
            status = DeltaStatus.DELTA_ZERO
            note = "no consequential difference in the declared tested scope"
        delta = Delta(
            status, tuple(changed), tuple(sorted(set(protected))), unresolved, note
        )
        self.trace.append({
            "op": "COMPARE",
            "before": before_id,
            "after": after_id,
            "delta": _normalize(asdict(delta)),
        })
        return delta

    def close_if_delta_zero(self, candidate_id: str, delta: Delta) -> Candidate:
        if delta.status != DeltaStatus.DELTA_ZERO:
            raise ValueError("NO_CHANGE is permitted only for DELTA_ZERO")
        candidate = self.get(candidate_id)
        updated = replace(candidate, stage=FireStage.CLOSED, resting=True)
        self.candidates[candidate_id] = updated
        self._trace("DELTA_ZERO_NO_CHANGE", updated, {"delta": _normalize(asdict(delta))})
        return updated

    def music(self, *, bpm: int = 120, bars: int = 2, beats_per_bar: int = 4,
              motif: Sequence[str] = ("OBSERVE", "BURN", "REOBSERVE", "REST")
              ) -> tuple[MusicPulse, ...]:
        if bpm <= 0 or bars <= 0 or beats_per_bar <= 0:
            raise ValueError("music parameters must be positive")
        if not motif:
            raise ValueError("music motif must not be empty")
        total = bars * beats_per_bar
        return tuple(
            MusicPulse(
                i, (i % beats_per_bar) + 1, (i // beats_per_bar) + 1,
                motif[i % len(motif)], f"{(60.0 / bpm) * i:.6f}s"
            )
            for i in range(total)
        )

    def dance(self, steps: Sequence[DanceStep]) -> tuple[DanceStep, ...]:
        if not steps:
            raise ValueError("dance requires at least one step")
        for expected, step in enumerate(steps):
            step.validate()
            if step.index != expected:
                raise ValueError("dance indices must be contiguous from zero")
        return tuple(steps)

    def recommend_route(self, routes: Iterable[tuple[str, str]]) -> tuple[str, str] | None:
        return self.memory.recommend(routes)

    def export(self) -> dict[str, Any]:
        return _normalize({
            "schema": SCHEMA,
            "authority": METHOD_AUTHORITY,
            "boundaries": BOUNDARIES,
            "allWays": ALL_WAYS,
            "root": asdict(self.root),
            "candidates": {
                key: asdict(value) for key, value in sorted(self.candidates.items())
            },
            "ash": self.ash,
            "embers": self.embers,
            "survivors": self.survivors,
            "memory": {
                "experiences": [asdict(e) for e in self.memory.experiences],
                "signatureCounts": self.memory.signature_counts,
            },
            "trace": self.trace,
        })

    def _trace(self, op: str, candidate: Candidate, extra: Mapping[str, Any]) -> None:
        self.trace.append(_normalize({
            "op": op,
            "candidate_id": candidate.candidate_id,
            "object_id": candidate.object_id,
            "stage": candidate.stage.value,
            "verification": candidate.verification.value,
            **dict(extra),
        }))

    def _assert_object_identity(self) -> None:
        ids = {candidate.object_id for candidate in self.candidates.values()}
        if ids != {self.root.object_id}:
            raise AssertionError("object identity changed across the dynamic field")


def mutation_signature(mutation: Mutation) -> str:
    mutation.validate()
    return _digest({
        "path": mutation.path,
        "operator": mutation.operator,
        "direction": mutation.direction,
        "before_type": type(mutation.before).__name__,
        "after_type": type(mutation.after).__name__,
    })


def opposites_bounds_transitions(value: float, *, lower: float,
                                 upper: float) -> dict[str, Any]:
    if any(isinstance(v, bool) or not isinstance(v, (int, float))
           for v in (value, lower, upper)):
        raise TypeError("value/lower/upper must be numeric")
    if not all(math.isfinite(float(v)) for v in (value, lower, upper)):
        raise ValueError("value/lower/upper must be finite")
    if lower > upper:
        raise ValueError("lower must be <= upper")
    if value < lower:
        regime = "BELOW"
    elif value > upper:
        regime = "ABOVE"
    elif value == lower == upper:
        regime = "AT_COLLAPSED_BOUND"
    elif value in {lower, upper}:
        regime = "AT_BOUND"
    else:
        regime = "BETWEEN"
    midpoint = (lower + upper) / 2.0
    return {
        "value": float(value),
        "opposite": float((2.0 * midpoint) - value),
        "lower": float(lower),
        "upper": float(upper),
        "midpoint": float(midpoint),
        "regime": regime,
    }


def _normalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _normalize(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite float not allowed")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def _digest(value: Any) -> str:
    blob = json.dumps(
        _normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _path_parts(path: str) -> tuple[str, ...]:
    parts = tuple(part for part in path.split(".") if part)
    if not parts:
        raise ValueError("path must contain at least one component")
    return parts


def _get_path(root: Mapping[str, Any], path: str) -> Any:
    current: Any = root
    for part in _path_parts(path):
        if not isinstance(current, Mapping) or part not in current:
            raise KeyError(path)
        current = current[part]
    return current


def _set_path(root: dict[str, Any], path: str, value: Any) -> None:
    parts = _path_parts(path)
    current: dict[str, Any] = root
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            raise KeyError(path)
        current = current[part]
    if parts[-1] not in current:
        raise KeyError(path)
    current[parts[-1]] = value


def _invariant_violations(surface: Mapping[str, Any],
                          invariants: Mapping[str, Any]) -> list[str]:
    violations = []
    for path, expected in invariants.items():
        try:
            actual = _get_path(surface, path)
        except KeyError:
            violations.append(path)
            continue
        if actual != expected:
            violations.append(path)
    return violations
