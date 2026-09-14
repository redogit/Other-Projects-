from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from math import ceil, log2

from core import (
    AssemblySpec,
    CostVector,
    EmergentEffectCertificate,
    FailureKind,
    ObligationSpec,
    PartSpec,
    StepPhase,
    VerificationResult,
)

TARGETS = frozenset((3, 7))
INITIAL_WORLDS = (0, 4)
OBSERVATIONS = (0, 1, 2, 3, 0, 1, 2, 3)


def _hidden_transition(world: int, action: int) -> int:
    if type(world) is not int or not 0 <= world < 8:
        raise ValueError("world outside hidden-mode domain")
    if type(action) is not int or not 0 <= action < 4:
        raise ValueError("action outside hidden-mode domain")
    mode, physical = divmod(world, 4)
    if action == 0:
        nxt = (2 if mode else 1) if physical == 0 else physical
    elif action == 1:
        nxt = 0 if physical in (1, 2) else physical
    elif action == 2:
        nxt = (1 if mode else 3) if physical == 0 else physical
    else:
        nxt = (3 if mode else 1) if physical == 0 else physical
    return 4 * mode + nxt


@dataclass(frozen=True)
class TableController:
    actions: tuple[tuple[int, int, int, int], ...]
    updates: tuple[tuple[int, int, int, int], ...]
    start: int = 0

    def __post_init__(self):
        if not self.actions or len(self.actions) != len(self.updates):
            raise ValueError("controller tables must be matching and nonempty")
        if not 0 <= self.start < len(self.actions):
            raise ValueError("invalid controller start")
        for row in self.actions:
            if len(row) != 4 or any(type(a) is not int or not 0 <= a < 4 for a in row):
                raise ValueError("action row must cover four observations")
        for row in self.updates:
            if len(row) != 4 or any(type(q) is not int or not 0 <= q < len(self.actions) for q in row):
                raise ValueError("update row must stay within controller memory")

    @property
    def states(self):
        return len(self.actions)

    def choice(self, memory: int, observation: int):
        return self.actions[memory][observation], self.updates[memory][observation]


@dataclass(frozen=True)
class CandidateAssembly:
    spec: AssemblySpec
    parts: tuple[PartSpec, ...]
    controller: TableController
    uses_observation: bool
    dedicated_probe_steps: int

    @property
    def stable_id(self):
        return self.spec.stable_id

    @property
    def obligation_id(self):
        return self.spec.obligation_id


def hidden_mode_obligation() -> ObligationSpec:
    return ObligationSpec(
        stable_id="pass08.hidden_mode_reach",
        version=1,
        subject="Pass 08 eight-world hidden-mode witness",
        bounds=(("actions", 4), ("hidden_worlds", 8), ("initial_worlds", 2)),
        required_capabilities=("transition", "decide"),
        protected_invariants=("mode is hidden and unchanged", "target physical state 3 remains absorbing"),
        success_condition="sure reach target physical state 3 from both allowed initial hidden worlds",
        allowed_initial=INITIAL_WORLDS,
        allowed_actions=(0, 1, 2, 3),
        observable_information=("physical observation when an observe part is present",),
        permissions=("actions 0..3 only",),
        temporal_semantics="finite path reachability; execution stops once target is reached",
        step_timing=(
            StepPhase.PRE_ACTION,
            StepPhase.TRANSITION,
            StepPhase.OBSERVATION,
            StepPhase.KNOWLEDGE_UPDATE,
            StepPhase.MONITOR_UPDATE,
            StepPhase.MEMORY_UPDATE,
        ),
        exact_regime=True,
        evidence_threshold="complete execution over both allowed hidden initial worlds",
        unresolved_remainder=("does not establish global optimality outside this finite witness",),
        cost_dimensions=(
            "component_count", "coupling_count", "memory_bits", "observation_classes",
            "dedicated_probe_steps", "worst_case_steps", "verification_cases",
        ),
    )


def _part(stable_id, provides, requires=(), inputs=(), outputs=(), state=()):
    return PartSpec(
        stable_id=stable_id, version=1, provides=tuple(provides), requires=tuple(requires),
        input_ports=tuple(inputs), output_ports=tuple(outputs), state_carried=tuple(state),
        assumptions=("Pass 08 hidden-mode witness only",), bounds=(("worlds", 8),), side_effects=(),
        external_dependencies=(), cost=CostVector.from_mapping({"component_count": 1}),
        evidence_refs=("SPrime Search/decision-field/partial-observation/evidence/SUMMARY.json",),
        known_failures=(), replaceability_boundary="same hidden-mode obligation only",
    )


def _transition_part():
    return _part(
        "pass08.hidden_transition", ("transition",),
        inputs=(("state", "WorldState"), ("action", "Action")),
        outputs=(("next", "WorldState"),),
    )


def _observation_part():
    return _part(
        "pass08.physical_observation", ("observe",),
        inputs=(("state", "WorldState"),), outputs=(("observation", "Observation"),),
    )


def _simulate(controller: TableController, uses_observation: bool):
    traces = []
    worst = 0
    for start in INITIAL_WORLDS:
        world, memory, steps = start, controller.start, 0
        trace = []
        seen = set()
        while world not in TARGETS:
            key = (world, memory)
            if key in seen:
                return False, (), 0
            seen.add(key)
            observation = OBSERVATIONS[world] if uses_observation else 0
            action, next_memory = controller.choice(memory, observation)
            next_world = _hidden_transition(world, action)
            trace.append((world, memory, observation if uses_observation else -1, action, next_world, next_memory))
            world, memory = next_world, next_memory
            steps += 1
            if steps > 8 * controller.states + 2:
                return False, (), 0
        worst = max(worst, steps)
        traces.append(tuple(trace))
    return True, tuple(traces), worst


def _trace_refs(traces):
    refs = []
    for trace in traces:
        raw = json.dumps(trace, separators=(",", ":")).encode("utf-8")
        refs.append("trace:" + hashlib.sha256(raw).hexdigest())
    return tuple(refs)


def _assembly(obligation, stable_id, parts, wiring, controller, *, uses_observation, dedicated_probe_steps):
    ok, traces, worst = _simulate(controller, uses_observation)
    memory_bits = 0 if controller.states <= 1 else ceil(log2(controller.states))
    cost = CostVector.from_mapping({
        "component_count": len(parts),
        "coupling_count": len(wiring),
        "memory_bits": memory_bits,
        "observation_classes": 4 if uses_observation else 0,
        "dedicated_probe_steps": dedicated_probe_steps,
        "worst_case_steps": worst if ok else 8 * controller.states + 2,
        "verification_cases": len(INITIAL_WORLDS),
    })
    covered = tuple(sorted(set().union(*(set(part.provides) for part in parts)) & {
        "transition", "observe", "infer", "monitor", "decide", "remember", "schedule"
    }))
    spec = AssemblySpec(
        stable_id=stable_id, version=1, obligation_id=obligation.stable_id, obligation_version=obligation.version,
        parts=tuple((p.stable_id, p.version) for p in parts), wiring=tuple(wiring),
        covered_capabilities=covered, unresolved_gaps=(), cost=cost,
        evidence_refs=("SPrime Search/decision-field/partial-observation/evidence/SUMMARY.json",),
        search_provenance=("decision-field BOM milestone 1",),
    )
    return CandidateAssembly(spec, tuple(parts), controller, uses_observation, dedicated_probe_steps)


def reference_probe_parts(obligation=None):
    obligation = hidden_mode_obligation() if obligation is None else obligation
    transition = _transition_part(); observe = _observation_part()
    protocol = _part(
        "synthetic.probe_protocol", ("schedule", "remember"), requires=("observe",),
        inputs=(("observation", "Observation"),), outputs=(("phase", "PolicyMemory"),), state=("PolicyMemory",),
    )
    decider = _part(
        "synthetic.commit_decider", ("decide",), requires=("observe", "schedule"),
        inputs=(("observation", "Observation"), ("phase", "PolicyMemory")), outputs=(("action", "Action"),),
    )
    controller = TableController(
        actions=((0, 1, 1, 0), (2, 0, 0, 0), (3, 0, 0, 0)),
        updates=((0, 1, 2, 0), (1, 1, 1, 1), (2, 2, 2, 2)),
    )
    wiring = (
        (transition.stable_id, "next", observe.stable_id, "state"),
        (observe.stable_id, "observation", protocol.stable_id, "observation"),
        (observe.stable_id, "observation", decider.stable_id, "observation"),
        (protocol.stable_id, "phase", decider.stable_id, "phase"),
        (decider.stable_id, "action", transition.stable_id, "action"),
    )
    return _assembly(obligation, "synthetic.probe_baseline", (transition, observe, protocol, decider), wiring, controller, uses_observation=True, dedicated_probe_steps=1)


def fused_commit_parts(obligation=None):
    obligation = hidden_mode_obligation() if obligation is None else obligation
    transition = _transition_part(); observe = _observation_part()
    fused = _part(
        "fused.commit_action", ("decide", "remember"), requires=("observe",),
        inputs=(("observation", "Observation"), ("memory", "PolicyMemory")),
        outputs=(("action", "Action"), ("memory", "PolicyMemory")), state=("PolicyMemory",),
    )
    controller = TableController(
        actions=((3, 1, 0, 0), (2, 0, 0, 0)),
        updates=((0, 1, 0, 0), (0, 0, 0, 0)),
    )
    wiring = (
        (transition.stable_id, "next", observe.stable_id, "state"),
        (observe.stable_id, "observation", fused.stable_id, "observation"),
        (fused.stable_id, "action", transition.stable_id, "action"),
    )
    return _assembly(obligation, "pass08.fused_commit", (transition, observe, fused), wiring, controller, uses_observation=True, dedicated_probe_steps=0)


def open_loop_parts(obligation=None):
    obligation = hidden_mode_obligation() if obligation is None else obligation
    transition = _transition_part()
    scheduler = _part(
        "openloop.312_scheduler", ("decide", "schedule", "remember"),
        outputs=(("action", "Action"),), state=("PolicyMemory",),
    )
    controller = TableController(
        actions=((3, 3, 3, 3), (1, 1, 1, 1), (2, 2, 2, 2)),
        updates=((1, 1, 1, 1), (2, 2, 2, 2), (2, 2, 2, 2)),
    )
    wiring = ((scheduler.stable_id, "action", transition.stable_id, "action"),)
    return _assembly(obligation, "openloop.312", (transition, scheduler), wiring, controller, uses_observation=False, dedicated_probe_steps=0)


def invalid_cheap_parts(obligation=None):
    obligation = hidden_mode_obligation() if obligation is None else obligation
    transition = _transition_part()
    decider = _part("invalid.always_zero", ("decide",), outputs=(("action", "Action"),))
    controller = TableController(actions=((0, 0, 0, 0),), updates=((0, 0, 0, 0),))
    wiring = ((decider.stable_id, "action", transition.stable_id, "action"),)
    return _assembly(obligation, "invalid.always_zero", (transition, decider), wiring, controller, uses_observation=False, dedicated_probe_steps=0)


def verify_hidden_mode(candidate: CandidateAssembly) -> VerificationResult:
    obligation = hidden_mode_obligation()
    if candidate.spec.obligation_id != obligation.stable_id or candidate.spec.obligation_version != obligation.version:
        return VerificationResult.fail(FailureKind.INCOMPATIBLE, "candidate uses a different obligation")
    provided = set().union(*(set(part.provides) for part in candidate.parts))
    if not set(obligation.required_capabilities) <= provided:
        return VerificationResult.fail(FailureKind.INCOMPATIBLE, "required capability missing")
    for part in candidate.parts:
        if not set(part.requires) <= provided:
            return VerificationResult.fail(FailureKind.INCOMPATIBLE, f"unsatisfied part dependency: {part.stable_id}")
    ok, traces, worst = _simulate(candidate.controller, candidate.uses_observation)
    if not ok:
        return VerificationResult.fail(
            FailureKind.UNSATISFIED,
            "candidate does not reach target from every allowed hidden initial world",
            metrics=(("verification_cases", len(INITIAL_WORLDS)),),
        )
    first_observations = []
    for trace in traces:
        if trace:
            first_observations.append(OBSERVATIONS[trace[0][4]] if candidate.uses_observation else -1)
    distinguished = int(candidate.uses_observation and len(set(first_observations)) == len(INITIAL_WORLDS))
    return VerificationResult.pass_result(
        "candidate reaches target from every allowed hidden initial world",
        evidence_refs=_trace_refs(traces),
        metrics=(("distinguished_initial_modes", distinguished), ("verification_cases", len(INITIAL_WORLDS)), ("worst_case_steps", worst)),
    )


def certify_effect(result: VerificationResult, effect: str, assembly_id: str) -> EmergentEffectCertificate:
    if not result.passed:
        raise ValueError("cannot certify emergent effect from failed verification")
    if effect.startswith("DISTINGUISHES") and dict(result.metrics).get("distinguished_initial_modes") != 1:
        raise ValueError("verification did not establish the requested distinction")
    return EmergentEffectCertificate(
        stable_id=f"effect.{assembly_id}.distinguishes_hidden_mode",
        version=1,
        assembly_id=assembly_id,
        obligation_id=hidden_mode_obligation().stable_id,
        effect=effect,
        verifier_ref="bom.verify_hidden_mode/v1",
        evidence_refs=result.evidence_refs,
    )
