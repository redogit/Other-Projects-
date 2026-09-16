"""GSFL v0 reference implementation.

A small, deterministic surrogate for human-optimized semantic fitting.
It separates semantic state from surface representation, classifies changes,
checks declared invariants and exact reconstruction, and selects only admitted
rotations under a declared task-relative metric vector.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import shlex
from typing import Any, Iterable

VALID_ROTATION = "VALID_ROTATION"
MUTATION = "MUTATION"
SEMANTIC_DECAY = "SEMANTIC_DECAY"

_METRIC_NAMES = (
    "clarity",
    "usefulness",
    "recoverability",
    "cognitive_effort",
    "ambiguity",
    "semantic_loss",
)


@dataclass(frozen=True)
class SemanticObject:
    object_id: str
    meaning: dict[str, Any]
    invariants: tuple[str, ...]


@dataclass(frozen=True)
class Metrics:
    clarity: float
    usefulness: float
    recoverability: float
    cognitive_effort: float
    ambiguity: float
    semantic_loss: float

    def __post_init__(self) -> None:
        for name in _METRIC_NAMES:
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"metric {name} must be in [0, 1], got {value!r}")


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    meaning: dict[str, Any]
    surface: str
    metrics: Metrics
    reconstructed_meaning: dict[str, Any]


@dataclass(frozen=True)
class Evaluation:
    candidate_id: str
    classification: str
    invariants_preserved: bool
    reconstruction_pass: bool
    admitted: bool
    score: float
    changed_keys: tuple[str, ...] = ()
    failed_invariants: tuple[str, ...] = ()


def _changed_keys(left: dict[str, Any], right: dict[str, Any]) -> tuple[str, ...]:
    keys = set(left) | set(right)
    return tuple(sorted(k for k in keys if left.get(k, object()) != right.get(k, object())))


def _failed_invariants(source: SemanticObject, candidate: Candidate) -> tuple[str, ...]:
    failed = []
    for key in source.invariants:
        if key not in source.meaning or key not in candidate.meaning:
            failed.append(key)
            continue
        if source.meaning[key] != candidate.meaning[key]:
            failed.append(key)
    return tuple(sorted(failed))


def quality_score(metrics: Metrics) -> float:
    """Return the bounded v0 fit score.

    Benefit is multiplicative so a near-zero human-use dimension cannot be
    hidden by the others. Cost terms are additive and cannot divide by zero.
    This is a declared surrogate, not a universal cognitive metric.
    """

    benefit = metrics.clarity * metrics.usefulness * metrics.recoverability
    burden = 1.0 + metrics.cognitive_effort + metrics.ambiguity + metrics.semantic_loss
    return round(benefit / burden, 12)


def classify(source: SemanticObject, candidate: Candidate) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    changed = _changed_keys(source.meaning, candidate.meaning)
    failed = _failed_invariants(source, candidate)
    if failed:
        return SEMANTIC_DECAY, changed, failed
    if changed:
        return MUTATION, changed, failed
    return VALID_ROTATION, changed, failed


def evaluate_candidate(source: SemanticObject, candidate: Candidate) -> Evaluation:
    classification, changed, failed = classify(source, candidate)
    reconstruction_pass = candidate.reconstructed_meaning == source.meaning
    admitted = classification == VALID_ROTATION and reconstruction_pass
    return Evaluation(
        candidate_id=candidate.candidate_id,
        classification=classification,
        invariants_preserved=not failed,
        reconstruction_pass=reconstruction_pass,
        admitted=admitted,
        score=quality_score(candidate.metrics),
        changed_keys=changed,
        failed_invariants=failed,
    )


def fit(source: SemanticObject, candidates: Iterable[Candidate]) -> tuple[Candidate, list[Evaluation]]:
    candidates = list(candidates)
    if not candidates:
        raise ValueError("FIT requires at least one candidate")
    evaluations = [evaluate_candidate(source, candidate) for candidate in candidates]
    admitted = [
        (candidate, evaluation)
        for candidate, evaluation in zip(candidates, evaluations)
        if evaluation.admitted
    ]
    if not admitted:
        raise ValueError("FIT found no admitted invariant-preserving reconstructible rotations")
    selected, _ = sorted(admitted, key=lambda pair: (-pair[1].score, pair[0].candidate_id))[0]
    return selected, evaluations


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2, separators=(",", ": ")) + "\n"


def _parse_value(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _parse_assignment(text: str) -> tuple[str, Any]:
    if "=" not in text:
        raise ValueError(f"expected key=value, got {text!r}")
    key, value = text.split("=", 1)
    key = key.strip()
    if not key:
        raise ValueError("empty key")
    return key, _parse_value(value)


def parse(program: str) -> tuple[SemanticObject, list[Candidate]]:
    lines = []
    for raw in program.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)

    if not lines or lines[0] != "GSFL 0":
        raise ValueError("program must start with 'GSFL 0'")

    object_id: str | None = None
    meaning: dict[str, Any] = {}
    invariants: list[str] = []
    candidates: list[Candidate] = []
    candidate_ids: set[str] = set()
    current: dict[str, Any] | None = None
    saw_fit = False
    after_fit = False

    for line in lines[1:]:
        if after_fit:
            raise ValueError("FIT must be terminal")
        op, _, rest = line.partition(" ")
        op = op.upper()
        rest = rest.strip()

        if current is None:
            if op == "OBJECT":
                if object_id is not None:
                    raise ValueError("OBJECT may appear only once")
                if not rest:
                    raise ValueError("OBJECT requires an id")
                object_id = rest
            elif op == "MEANING":
                key, value = _parse_assignment(rest)
                if key in meaning:
                    raise ValueError(f"duplicate MEANING key {key!r}")
                meaning[key] = value
            elif op == "PRESERVE":
                if not rest:
                    raise ValueError("PRESERVE requires a key")
                invariants.append(rest)
            elif op == "ROTATE":
                if not rest:
                    raise ValueError("ROTATE requires a candidate id")
                if rest in candidate_ids:
                    raise ValueError(f"duplicate candidate id {rest!r}")
                candidate_ids.add(rest)
                current = {
                    "candidate_id": rest,
                    "meaning": dict(meaning),
                    "surface": "",
                    "metrics": {},
                    "reconstructed_meaning": {},
                }
            elif op == "FIT":
                if saw_fit:
                    raise ValueError("FIT may appear only once")
                saw_fit = True
                after_fit = True
            else:
                raise ValueError(f"unknown top-level operation {op!r}")
        else:
            if op == "SURFACE":
                current["surface"] = _parse_value(rest)
                if not isinstance(current["surface"], str):
                    raise ValueError("SURFACE must decode to a string")
            elif op == "SET":
                key, value = _parse_assignment(rest)
                current["meaning"][key] = value
            elif op == "DROP":
                if not rest:
                    raise ValueError("DROP requires a key")
                current["meaning"].pop(rest, None)
            elif op == "METRIC":
                for token in shlex.split(rest):
                    key, value = _parse_assignment(token)
                    if key not in _METRIC_NAMES:
                        raise ValueError(f"unknown metric {key!r}")
                    current["metrics"][key] = float(value)
            elif op == "RECONSTRUCT":
                key, value = _parse_assignment(rest)
                current["reconstructed_meaning"][key] = value
            elif op == "END":
                missing = [name for name in _METRIC_NAMES if name not in current["metrics"]]
                if missing:
                    raise ValueError(f"candidate {current['candidate_id']!r} missing metrics: {', '.join(missing)}")
                candidates.append(
                    Candidate(
                        candidate_id=current["candidate_id"],
                        meaning=dict(current["meaning"]),
                        surface=current["surface"],
                        metrics=Metrics(**current["metrics"]),
                        reconstructed_meaning=dict(current["reconstructed_meaning"]),
                    )
                )
                current = None
            else:
                raise ValueError(f"unknown candidate operation {op!r}")

    if current is not None:
        raise ValueError("unterminated ROTATE block")
    if object_id is None:
        raise ValueError("OBJECT is required")
    if not saw_fit:
        raise ValueError("FIT is required")
    for key in invariants:
        if key not in meaning:
            raise ValueError(f"PRESERVE refers to absent meaning key {key!r}")

    return SemanticObject(object_id, meaning, tuple(dict.fromkeys(invariants))), candidates


def execute(program: str) -> dict[str, Any]:
    source, candidates = parse(program)
    selected, evaluations = fit(source, candidates)
    return {
        "gsfl_version": 0,
        "object_id": source.object_id,
        "source_meaning": source.meaning,
        "invariants": list(source.invariants),
        "selected_candidate": selected.candidate_id,
        "selected_surface": selected.surface,
        "evaluations": [asdict(result) for result in evaluations],
    }
