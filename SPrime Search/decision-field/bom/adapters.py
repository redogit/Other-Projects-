from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

from catalog import PartCatalog
from core import CostVector, PartSpec

DEFAULT_DECISION_FIELD = Path(__file__).resolve().parent.parent


def _module(path: Path, name: str):
    if not path.is_file():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _root(root=None) -> Path:
    return DEFAULT_DECISION_FIELD if root is None else Path(root)


def source_hashes(root=None) -> dict[str, str]:
    base = _root(root)
    files = {
        "pass06.field": base / "field.py",
        "pass07.schedule": base / "schedule" / "schedule.py",
        "pass08.partial": base / "partial-observation" / "partial.py",
    }
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}


class T4TransitionAdapter:
    def __init__(self, rank: int, root=None):
        self.rank = rank
        self.module = _module(_root(root) / "field.py", f"bom_pass06_{id(self)}")

    def next_state(self, state: int, context: int) -> int:
        return self.module.get_next(self.rank, context, state)


class ObservationAdapter:
    def __init__(self, labels: tuple[int, ...]):
        if not labels or any(type(x) is not int or x < 0 for x in labels):
            raise ValueError("observation labels must be nonnegative integers")
        self.labels = tuple(labels)

    def observe(self, world: int) -> int:
        if type(world) is not int or not 0 <= world < len(self.labels):
            raise ValueError("world outside observation domain")
        return self.labels[world]


class BitsetInferenceAdapter:
    def successors(self, system, belief: int, action: int) -> tuple[int, ...]:
        return tuple(system.successors(belief, action))


class ReachMonitorAdapter:
    def __init__(self, target_mask: int):
        if type(target_mask) is not int or target_mask < 0:
            raise ValueError("target mask must be nonnegative integer")
        self.target_mask = target_mask

    def update(self, reached: bool, world: int) -> bool:
        if type(reached) is not bool or type(world) is not int or world < 0:
            raise ValueError("invalid monitor state")
        return reached or bool(self.target_mask & (1 << world))


class ObservationControllerAdapter:
    def __init__(self, controller):
        self.controller = controller

    def step(self, system, world: int, memory: int):
        return self.controller.step(system, world, memory)


class MooreSchedulerAdapter:
    def __init__(self, scheduler):
        self.scheduler = scheduler

    def step(self, rank: int, plant_state: int, memory: int):
        return self.scheduler.step(rank, plant_state, memory)


def _part(stable_id, provides, requires=(), inputs=(), outputs=(), *, state=(), evidence=()):
    return PartSpec(
        stable_id=stable_id,
        version=1,
        provides=tuple(provides),
        requires=tuple(requires),
        input_ports=tuple(inputs),
        output_ports=tuple(outputs),
        state_carried=tuple(state),
        assumptions=("finite deterministic decision-field reference adapter",),
        bounds=(),
        side_effects=(),
        external_dependencies=(),
        cost=CostVector.from_mapping({"component_count": 1}),
        evidence_refs=tuple(evidence),
        known_failures=(),
        replaceability_boundary="obligation-scoped behavioral replacement only",
    )


def reference_catalog(root=None) -> PartCatalog:
    base = _root(root)
    catalog = PartCatalog()
    catalog.register(
        _part("pass06.t4_transition", ("transition",), inputs=(("state", "WorldState"), ("action", "Action")), outputs=(("next", "WorldState"),), evidence=("SPrime Search/decision-field/evidence/SUMMARY.json",)),
        lambda rank, _base=base: T4TransitionAdapter(rank, _base),
    )
    catalog.register(
        _part("pass07.moore_scheduler", ("schedule", "remember"), inputs=(("state", "WorldState"),), outputs=(("action", "Action"),), state=("PolicyMemory",), evidence=("SPrime Search/decision-field/schedule/evidence/SUMMARY.json",)),
        lambda scheduler: MooreSchedulerAdapter(scheduler),
    )
    catalog.register(
        _part("pass08.observation_partition", ("observe",), inputs=(("state", "WorldState"),), outputs=(("observation", "Observation"),), evidence=("SPrime Search/decision-field/partial-observation/evidence/SUMMARY.json",)),
        lambda labels: ObservationAdapter(tuple(labels)),
    )
    catalog.register(
        _part("pass08.bitset_belief", ("infer",), requires=("transition", "observe"), inputs=(("knowledge", "KnowledgeState"), ("action", "Action"), ("observation", "Observation")), outputs=(("knowledge", "KnowledgeState"),), state=("KnowledgeState",), evidence=("SPrime Search/decision-field/partial-observation/evidence/SUMMARY.json",)),
        lambda: BitsetInferenceAdapter(),
    )
    catalog.register(
        _part("pass08.reach_monitor", ("monitor",), inputs=(("state", "WorldState"), ("monitor", "MonitorState")), outputs=(("monitor", "MonitorState"),), state=("MonitorState",), evidence=("SPrime Search/decision-field/partial-observation/evidence/SUMMARY.json",)),
        lambda target_mask: ReachMonitorAdapter(target_mask),
    )
    catalog.register(
        _part("pass08.observation_controller", ("decide", "remember"), requires=("observe",), inputs=(("observation", "Observation"), ("memory", "PolicyMemory")), outputs=(("action", "Action"), ("memory", "PolicyMemory")), state=("PolicyMemory",), evidence=("SPrime Search/decision-field/partial-observation/evidence/SUMMARY.json",)),
        lambda controller: ObservationControllerAdapter(controller),
    )
    return catalog
