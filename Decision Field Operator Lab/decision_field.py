from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Iterable, Protocol, Sequence, TypeVar

X = TypeVar("X")
R = TypeVar("R")
E = TypeVar("E")
G = TypeVar("G")
U = TypeVar("U")
ResultT = TypeVar("ResultT")


@dataclass(frozen=True)
class Evidence:
    kind: str
    detail: str
    certificate: Any = None
    claim_ceiling: str = "BOUNDED"


@dataclass(frozen=True)
class DecisionField(Generic[X, R, E, G, U]):
    possibilities: X
    relations: R
    evidence: tuple[E, ...]
    goal: G
    unresolved: U
    observer: Any = None
    history: tuple[str, ...] = ()


@dataclass(frozen=True, order=True)
class GravityScore:
    terminal: int = 0
    irreversible_fact: int = 0
    factorization: int = 0
    exact_rank_gain: int = 0
    kernel_reduction: int = 0
    heuristic_gain: float = 0.0
    negative_cost: float = 0.0


@dataclass(frozen=True)
class Probe:
    operator_name: str
    score: GravityScore
    exact_progress: bool
    payload: Any = None


class Operator(Protocol[X, R, E, G, U]):
    name: str

    def precondition(self, field: DecisionField[X, R, E, G, U]) -> bool:
        ...

    def probe(self, field: DecisionField[X, R, E, G, U]) -> Probe:
        ...

    def apply(
        self, field: DecisionField[X, R, E, G, U], probe: Probe
    ) -> DecisionField[X, R, E, G, U] | Sequence[DecisionField[X, R, E, G, U]]:
        ...


NormalizeFn = Callable[[DecisionField[X, R, E, G, U]], DecisionField[X, R, E, G, U]]
GoalFn = Callable[[DecisionField[X, R, E, G, U]], ResultT | None]
ImpossibleFn = Callable[[DecisionField[X, R, E, G, U]], ResultT | None]
LearnFn = Callable[[DecisionField[X, R, E, G, U]], DecisionField[X, R, E, G, U]]
BranchFn = Callable[[DecisionField[X, R, E, G, U]], Sequence[DecisionField[X, R, E, G, U]]]
CombineFn = Callable[[Sequence[ResultT]], ResultT]


@dataclass
class DecisionFieldSolver(Generic[X, R, E, G, U, ResultT]):
    operators: Sequence[Operator[X, R, E, G, U]]
    normalize: NormalizeFn[X, R, E, G, U]
    goal_result: GoalFn[X, R, E, G, U, ResultT]
    impossible_result: ImpossibleFn[X, R, E, G, U, ResultT]
    learn: LearnFn[X, R, E, G, U]
    branch: BranchFn[X, R, E, G, U]
    combine: CombineFn[ResultT]
    canonical_key: Callable[[DecisionField[X, R, E, G, U]], Any] | None = None
    memo: dict[Any, ResultT] = field(default_factory=dict)

    def solve(self, field: DecisionField[X, R, E, G, U]) -> ResultT:
        current = self._close(field)

        terminal = self.goal_result(current)
        if terminal is not None:
            return terminal

        impossible = self.impossible_result(current)
        if impossible is not None:
            return impossible

        key = self.canonical_key(current) if self.canonical_key else None
        if key is not None and key in self.memo:
            return self.memo[key]

        while True:
            probes = [
                (op, op.probe(current))
                for op in self.operators
                if op.precondition(current)
            ]
            progressive = [(op, p) for op, p in probes if p.exact_progress]

            if not progressive:
                break

            op, best = max(progressive, key=lambda item: item[1].score)
            outcome = op.apply(current, best)

            if isinstance(outcome, Sequence) and not isinstance(outcome, DecisionField):
                results = [self.solve(child) for child in outcome]
                result = self.combine(results)
                if key is not None:
                    self.memo[key] = result
                return result

            current = self._close(outcome)  # type: ignore[arg-type]

            terminal = self.goal_result(current)
            if terminal is not None:
                if key is not None:
                    self.memo[key] = terminal
                return terminal

            impossible = self.impossible_result(current)
            if impossible is not None:
                if key is not None:
                    self.memo[key] = impossible
                return impossible

        children = self.branch(current)
        if not children:
            impossible = self.impossible_result(current)
            if impossible is None:
                raise RuntimeError(
                    "No progressive operator, no exact branch, and no terminal certificate."
                )
            result = impossible
        else:
            result = self.combine([self.solve(child) for child in children])

        if key is not None:
            self.memo[key] = result
        return result

    def _close(
        self, field: DecisionField[X, R, E, G, U]
    ) -> DecisionField[X, R, E, G, U]:
        previous = None
        current = field
        while current != previous:
            previous = current
            current = self.normalize(current)
            current = self.learn(current)
        return current


def consequentially_equivalent(
    left: Any,
    right: Any,
    tests: Iterable[Callable[[Any], Any]],
) -> bool:
    """Task-local equivalence: all admitted consequential tests agree."""
    return all(test(left) == test(right) for test in tests)
