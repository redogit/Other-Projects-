# Decision-Field BOM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an additive, capability-based bill-of-materials layer that can express the existing Pass 06–08 decision-field stack and search verified substitute assemblies without rewriting prior scientific artifacts.

**Architecture:** The BOM is split into an operational plane and evidence/transport sidecars. Immutable specs describe obligations, parts, assemblies, costs, and emergent-effect certificates; adapters wrap existing Pass 06–08 implementations; a deterministic search enumerates compatible capability covers and typed wiring, verifies candidates under the same obligation, and returns a Pareto frontier. The first experiment compares a deliberately separated probe construction with a fused consequential/diagnostic construction for the existing hidden-mode witness.

**Tech Stack:** Python 3.10+ standard library; existing Pass 06–08 Python modules; existing C++17 audit helpers where reused; GitHub Actions for exact-commit CI.

**Spec:** `docs/superpowers/specs/2026-09-14-decision-field-bom-design.md`

## Global Constraints

- Do not modify or rewrite Pass 06–08 scientific evidence files.
- Operational capabilities are `transition`, `observe`, `infer`, `monitor`, `decide`, `remember`, and `schedule`.
- `encode` and `verify` are evidence/transport sidecars; `verify` never satisfies its own evidence requirement.
- A part may claim only intrinsic capabilities exposed by its interface.
- System-level diagnostic or informational properties must be recorded as verified emergent effects.
- Construction dependency cycles are invalid; runtime temporal feedback is allowed through declared phase boundaries.
- Step timing must distinguish pre-action information, transition, observation, knowledge update, monitor update, and policy-memory update.
- Candidate assemblies are compared by a declared cost vector and Pareto dominance; there is no default scalar score.
- A replacement may be promoted only under the same versioned `ObligationSpec` and obligation-specific verifier.
- Failure states are first-class: `INCOMPATIBLE`, `UNSATISFIED`, `UNRESOLVED`, `DOMINATED`, `OUT_OF_BOUND`, `VERIFIER_DISAGREEMENT`.
- Search order and scientific output serialization must be deterministic.
- The first milestone must express both the existing Pass 08 reference assembly and the fused diagnostic/consequential alternative under the same BOM contracts.

---

## File Structure

Create this additive subtree:

```text
SPrime Search/decision-field/bom/
  README.md
  core.py
  catalog.py
  adapters.py
  search.py
  experiment.py
  audit.py
  tests/
    test_core.py
    test_catalog_adapters.py
    test_search.py
    test_experiment.py
  evidence/
    SUMMARY.json
    FRONTIER.json
    VERIFICATION.json
```

Modify only:

```text
.github/workflows/sprime-decision-field-check.yml
```

Responsibilities:

- `core.py`: immutable contracts, validation, canonical serialization, failure/result records, cost vectors, emergent-effect certificates.
- `catalog.py`: append-only in-memory registry with deterministic iteration and stable version lookup.
- `adapters.py`: wrappers around Pass 06–08 implementations; no copied scientific logic.
- `search.py`: capability cover enumeration, construction dependency validation, typed wiring compatibility, deterministic candidate generation, Pareto frontier.
- `experiment.py`: hidden-mode obligation, baseline/fused candidate definitions, obligation-specific verifier, measured costs.
- `audit.py`: independent small-domain oracles, regression checks against Pass 08, deterministic evidence writer.
- tests: focused unit/regression tests; each task adds only tests needed for that task.

---

### Task 1: Immutable BOM contracts and validation

**Files:**
- Create: `SPrime Search/decision-field/bom/core.py`
- Create: `SPrime Search/decision-field/bom/tests/test_core.py`

**Interfaces:**
- Produces:
  - `Capability` string constants.
  - `StepPhase` enum values: `PRE_ACTION`, `TRANSITION`, `OBSERVATION`, `KNOWLEDGE_UPDATE`, `MONITOR_UPDATE`, `MEMORY_UPDATE`.
  - `FailureKind` enum values matching the global constraints.
  - `CostVector(items: tuple[tuple[str, int], ...])` with `dominates(other) -> bool`.
  - `ObligationSpec` frozen dataclass.
  - `PartSpec` frozen dataclass.
  - `AssemblySpec` frozen dataclass.
  - `EmergentEffectCertificate` frozen dataclass.
  - `VerificationResult` frozen dataclass.
  - `canonical_json(value) -> str` for deterministic evidence serialization.

- [ ] **Step 1: Write failing validation and Pareto tests**

Create `tests/test_core.py` with exact tests:

```python
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import (
    AssemblySpec,
    CostVector,
    EmergentEffectCertificate,
    FailureKind,
    ObligationSpec,
    PartSpec,
    StepPhase,
    VerificationResult,
    canonical_json,
)


class CoreTests(unittest.TestCase):
    def test_cost_vector_pareto_dominance(self):
        a = CostVector.from_mapping({"memory_bits": 1, "probe_steps": 0})
        b = CostVector.from_mapping({"memory_bits": 1, "probe_steps": 1})
        c = CostVector.from_mapping({"memory_bits": 0, "probe_steps": 2})
        self.assertTrue(a.dominates(b))
        self.assertFalse(b.dominates(a))
        self.assertFalse(a.dominates(c))
        self.assertFalse(c.dominates(a))

    def test_cost_vectors_require_same_declared_dimensions(self):
        a = CostVector.from_mapping({"memory_bits": 1})
        b = CostVector.from_mapping({"probe_steps": 1})
        with self.assertRaises(ValueError):
            a.dominates(b)

    def test_obligation_requires_explicit_step_timing(self):
        with self.assertRaises(ValueError):
            ObligationSpec(
                stable_id="o", version=1, subject="synthetic",
                bounds=(("worlds", 2),), required_capabilities=("transition",),
                protected_invariants=(), success_condition="sure_reach",
                allowed_initial=(0, 1), allowed_actions=(0, 1),
                observable_information=("physical",), permissions=("observe",),
                temporal_semantics="path", step_timing=(), exact_regime=True,
                evidence_threshold="exhaustive", unresolved_remainder=(),
                cost_dimensions=("memory_bits",),
            )

    def test_part_rejects_self_construction_dependency(self):
        with self.assertRaises(ValueError):
            PartSpec(
                stable_id="p", version=1,
                provides=("transition",), requires=("transition",),
                input_ports=(("state", "WorldState"),),
                output_ports=(("next", "WorldState"),),
                state_carried=(), assumptions=(), bounds=(), side_effects=(),
                external_dependencies=(), cost=CostVector.from_mapping({"memory_bits": 0}),
                evidence_refs=(), known_failures=(), replaceability_boundary="same obligation",
            )

    def test_emergent_effect_requires_assembly_and_verifier_evidence(self):
        with self.assertRaises(ValueError):
            EmergentEffectCertificate(
                stable_id="e", version=1, assembly_id="", obligation_id="o",
                effect="DISTINGUISHES(mode0,mode1)", verifier_ref="", evidence_refs=(),
            )

    def test_canonical_json_is_key_and_sequence_stable(self):
        left = {"b": 2, "a": [3, 1]}
        right = {"a": [3, 1], "b": 2}
        self.assertEqual(canonical_json(left), canonical_json(right))
        self.assertEqual(json.loads(canonical_json(left)), left)

    def test_failure_kinds_are_closed(self):
        self.assertEqual(
            {x.value for x in FailureKind},
            {"INCOMPATIBLE", "UNSATISFIED", "UNRESOLVED", "DOMINATED", "OUT_OF_BOUND", "VERIFIER_DISAGREEMENT"},
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python -m unittest discover -s "SPrime Search/decision-field/bom/tests" -p 'test_core.py' -v
```

Expected: import failure because `core.py` does not yet exist.

- [ ] **Step 3: Implement minimal immutable contracts**

Create `core.py` with frozen dataclasses, strict tuple-based fields, deterministic sorting, and explicit validation. Required implementation shape:

```python
from dataclasses import dataclass
from enum import Enum
import json

OPERATIONAL_CAPABILITIES = frozenset({
    "transition", "observe", "infer", "monitor", "decide", "remember", "schedule"
})
SIDECARS = frozenset({"encode", "verify"})

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

@dataclass(frozen=True)
class CostVector:
    items: tuple[tuple[str, int], ...]

    @classmethod
    def from_mapping(cls, values):
        if not values or any(type(v) is not int or v < 0 for v in values.values()):
            raise ValueError("costs must be nonnegative integers")
        return cls(tuple(sorted(values.items())))

    def dominates(self, other):
        if tuple(k for k, _ in self.items) != tuple(k for k, _ in other.items):
            raise ValueError("cost dimensions differ")
        le = all(a <= b for (_, a), (_, b) in zip(self.items, other.items))
        lt = any(a < b for (_, a), (_, b) in zip(self.items, other.items))
        return le and lt
```

Implement each spec `__post_init__` to reject empty stable ids, versions below 1, unknown intrinsic capability names, empty timing for temporal obligations, duplicate ports, negative bounds/costs, and self construction-dependencies. `PartSpec.provides` may contain operational capabilities plus sidecars, but `verify` must be marked sidecar-only and cannot appear in an obligation's `required_capabilities`.

`canonical_json` must use:

```python
def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
```

- [ ] **Step 4: Run core tests**

Run the command from Step 2.

Expected: all `CoreTests` pass.

- [ ] **Step 5: Commit Task 1**

```bash
git add "SPrime Search/decision-field/bom/core.py" \
        "SPrime Search/decision-field/bom/tests/test_core.py"
git commit -m "Add immutable decision-field BOM contracts"
```

---

### Task 2: Append-only catalog and Pass 06–08 adapters

**Files:**
- Create: `SPrime Search/decision-field/bom/catalog.py`
- Create: `SPrime Search/decision-field/bom/adapters.py`
- Create: `SPrime Search/decision-field/bom/tests/test_catalog_adapters.py`

**Interfaces:**
- Consumes: Task 1 contracts.
- Produces:
  - `PartCatalog.register(spec, factory)`; duplicate `(stable_id, version)` rejected.
  - `PartCatalog.get(stable_id, version)`.
  - `PartCatalog.ordered_specs()` deterministic by `(stable_id, version)`.
  - `reference_catalog() -> PartCatalog`.
  - adapter factories for T4 transition, Pass 08 observation partition, bit-set inference, reach monitor, observation controller, and Pass 07 scheduler.
  - `reference_hidden_mode_assembly(obligation) -> AssemblySpec`.

- [ ] **Step 1: Write failing catalog/adapters tests**

Create tests that load the existing modules by file path rather than copying logic:

```python
class CatalogAdapterTests(unittest.TestCase):
    def test_catalog_is_append_only_and_ordered(self):
        catalog = PartCatalog()
        p2 = make_part("z", 1, ("transition",))
        p1 = make_part("a", 1, ("observe",))
        catalog.register(p2, lambda: object())
        catalog.register(p1, lambda: object())
        self.assertEqual([p.stable_id for p in catalog.ordered_specs()], ["a", "z"])
        with self.assertRaises(ValueError):
            catalog.register(p1, lambda: object())

    def test_reference_catalog_wraps_existing_implementations(self):
        catalog = reference_catalog()
        ids = {(p.stable_id, p.version) for p in catalog.ordered_specs()}
        self.assertIn(("pass08.observation_partition", 1), ids)
        self.assertIn(("pass08.bitset_belief", 1), ids)
        self.assertIn(("pass08.reach_monitor", 1), ids)
        self.assertIn(("pass08.observation_controller", 1), ids)
        self.assertIn(("pass07.moore_scheduler", 1), ids)
        self.assertIn(("pass06.t4_transition", 1), ids)

    def test_adapters_do_not_mutate_reference_sources(self):
        before = source_hashes()
        catalog = reference_catalog()
        for spec in catalog.ordered_specs():
            catalog.factory(spec.stable_id, spec.version)
        self.assertEqual(source_hashes(), before)
```

Add a functional test using a known Pass 08 `POSystem` case: the transition adapter's next state, observation adapter's label, and bit-set inference adapter's successor beliefs must equal direct calls into `partial.py` for the same fixture.

- [ ] **Step 2: Run tests and verify failure**

```bash
python -m unittest discover -s "SPrime Search/decision-field/bom/tests" -p 'test_catalog_adapters.py' -v
```

Expected: import failure for `catalog`/`adapters`.

- [ ] **Step 3: Implement catalog and adapters**

`catalog.py` stores only immutable specs and callable factories. No factory executes during registration.

`adapters.py` must load existing modules using `importlib.util.spec_from_file_location`, with paths resolved relative to the BOM directory:

```python
DECISION_FIELD = Path(__file__).resolve().parent.parent
PASS08 = DECISION_FIELD / "partial-observation" / "partial.py"
PASS07 = DECISION_FIELD / "schedule" / "schedule.py"
PASS06 = DECISION_FIELD / "field.py"
```

Do not import scientific evidence JSON as executable authority. Adapter `PartSpec.evidence_refs` points to existing evidence paths, but behavior comes from the existing code modules.

Create small wrapper objects with explicit methods such as:

```python
class T4TransitionAdapter:
    def __init__(self, rank: int): ...
    def next_state(self, state: int, context: int) -> int: ...

class ObservationAdapter:
    def __init__(self, labels: tuple[int, ...]): ...
    def observe(self, world: int) -> int: ...

class BitsetInferenceAdapter:
    def successors(self, system, belief: int, action: int) -> tuple[int, ...]: ...
```

- [ ] **Step 4: Run catalog/adapter tests plus Pass 08 audit smoke**

```bash
python -m unittest discover -s "SPrime Search/decision-field/bom/tests" -p 'test_catalog_adapters.py' -v
python "SPrime Search/decision-field/partial-observation/audit.py" --out /tmp/pass08-bom-regression
```

Expected: tests pass and Pass 08 audit exits 0.

- [ ] **Step 5: Commit Task 2**

```bash
git add "SPrime Search/decision-field/bom/catalog.py" \
        "SPrime Search/decision-field/bom/adapters.py" \
        "SPrime Search/decision-field/bom/tests/test_catalog_adapters.py"
git commit -m "Wrap decision-field research as BOM reference parts"
```

---

### Task 3: Deterministic assembly search and Pareto frontier

**Files:**
- Create: `SPrime Search/decision-field/bom/search.py`
- Create: `SPrime Search/decision-field/bom/tests/test_search.py`

**Interfaces:**
- Consumes: `ObligationSpec`, `PartSpec`, `AssemblySpec`, `CostVector`, `PartCatalog`.
- Produces:
  - `construction_order(parts) -> tuple[PartSpec, ...]` or raises `ValueError` on construction dependency cycle.
  - `candidate_part_sets(obligation, catalog) -> tuple[tuple[PartSpec, ...], ...]`.
  - `compatible_wirings(obligation, parts) -> tuple[tuple[tuple[str, str, str, str], ...], ...]` using `(producer_id, producer_port, consumer_id, consumer_port)` edges.
  - `pareto_frontier(assemblies) -> tuple[AssemblySpec, ...]`.

- [ ] **Step 1: Write exhaustive small-domain search tests**

Use a four-capability toy catalog and compare `candidate_part_sets` against a direct brute-force subset oracle for every nonempty required-capability subset. Include:

```python
def test_multi_capability_part_can_replace_two_single_parts(self):
    # fused provides transition+observe; singles provide one each
    # both covers must appear before dominance filtering


def test_construction_cycle_rejected_but_runtime_feedback_not_encoded_as_dependency(self):
    # p requires q and q requires p -> rejected
    # transition/observe temporal feedback is represented by ports/phases, not requires-cycle


def test_pareto_frontier_exact(self):
    # compare result to direct pairwise dominance oracle
```

Add a test that an obligation requiring `verify` as operational capability is rejected before search.

- [ ] **Step 2: Run and verify failure**

```bash
python -m unittest discover -s "SPrime Search/decision-field/bom/tests" -p 'test_search.py' -v
```

Expected: import failure for `search.py`.

- [ ] **Step 3: Implement deterministic search**

Use `itertools.combinations` over catalog specs sorted by stable id/version. Keep the initial search finite and explicit; do not add heuristic pruning before correctness is established.

Construction dependencies are capabilities required at build/configuration time. Build a directed graph from provider candidates to requiring parts only after a concrete provider has been selected; reject cycles with Kahn topological sort.

Port compatibility requires exact semantic type strings in milestone 1. No implicit coercion. Adapters must be explicit catalog parts in later milestones.

Pareto frontier implementation:

```python
def pareto_frontier(assemblies):
    ordered = sorted(assemblies, key=lambda a: (a.cost.items, a.stable_id))
    return tuple(
        a for a in ordered
        if not any(b is not a and b.cost.dominates(a.cost) for b in ordered)
    )
```

Reject duplicate assembly ids and cost-dimension mismatches.

- [ ] **Step 4: Run exhaustive search tests**

Run Step 2 command.

Expected: all tests pass.

- [ ] **Step 5: Commit Task 3**

```bash
git add "SPrime Search/decision-field/bom/search.py" \
        "SPrime Search/decision-field/bom/tests/test_search.py"
git commit -m "Add deterministic BOM assembly search"
```

---

### Task 4: Obligation verifier and emergent-effect certificates

**Files:**
- Modify: `SPrime Search/decision-field/bom/core.py`
- Create: `SPrime Search/decision-field/bom/experiment.py`
- Create: `SPrime Search/decision-field/bom/tests/test_experiment.py`

**Interfaces:**
- Consumes: Tasks 1–3 and Pass 08 adapters.
- Produces:
  - `hidden_mode_obligation() -> ObligationSpec`.
  - `verify_hidden_mode(assembly, executable_parts) -> VerificationResult`.
  - `certify_effect(result, effect) -> EmergentEffectCertificate` only for PASS results.
  - `reference_probe_parts()` and `fused_commit_parts()` candidate sets.
  - `measure_hidden_mode_cost(...) -> CostVector` with dimensions exactly:
    `component_count`, `coupling_count`, `memory_bits`, `observation_classes`, `dedicated_probe_steps`, `worst_case_steps`, `verification_cases`.

- [ ] **Step 1: Write failing verifier/effect tests**

Required tests:

```python
class ExperimentTests(unittest.TestCase):
    def test_same_obligation_used_for_reference_and_fused_candidates(self):
        obligation = hidden_mode_obligation()
        self.assertEqual(reference_probe_parts(obligation).obligation_id, obligation.stable_id)
        self.assertEqual(fused_commit_parts(obligation).obligation_id, obligation.stable_id)

    def test_failed_assembly_cannot_receive_emergent_effect_certificate(self):
        failed = VerificationResult.fail(FailureKind.UNSATISFIED, "missed hidden mode")
        with self.assertRaises(ValueError):
            certify_effect(failed, "DISTINGUISHES(mode0,mode1)")

    def test_fused_diagnostic_value_is_system_effect_not_part_capability(self):
        candidate = fused_commit_parts(hidden_mode_obligation())
        self.assertFalse(any("infer" in p.provides and p.stable_id == "fused.commit_action" for p in candidate.parts))
        result = verify_hidden_mode(candidate, candidate.executables)
        self.assertTrue(result.passed)
        cert = certify_effect(result, "DISTINGUISHES(mode0,mode1)")
        self.assertEqual(cert.assembly_id, candidate.stable_id)
```

Add a deliberate cheap invalid assembly lacking monitor/history and assert `UNSATISFIED`, not `DOMINATED`.

- [ ] **Step 2: Run and verify failure**

```bash
python -m unittest discover -s "SPrime Search/decision-field/bom/tests" -p 'test_experiment.py' -v
```

Expected: missing experiment symbols.

- [ ] **Step 3: Implement hidden-mode obligation and verifier**

Reuse the existing Pass 08 hidden-mode transition/observation semantics exactly; do not create a different scientific target. Encode explicit phase order in the obligation:

```python
step_timing=(
    StepPhase.PRE_ACTION,
    StepPhase.TRANSITION,
    StepPhase.OBSERVATION,
    StepPhase.KNOWLEDGE_UPDATE,
    StepPhase.MONITOR_UPDATE,
    StepPhase.MEMORY_UPDATE,
)
```

The verifier must enumerate every allowed initial hidden world and execute until either success or a repeated full operational state `(world, knowledge, monitor, memory)` is detected. Record per-case trace hashes, worst-case step count, and exact failures.

The fused commit action must claim `transition`; its diagnostic effect is certified only after full assembly execution shows distinguishability under the declared observation and inference parts.

The synthetic dedicated-probe baseline must be explicitly labeled synthetic and must not be described as historical Pass 08 architecture.

- [ ] **Step 4: Run verifier tests and direct Pass 08 hidden-mode regression**

```bash
python -m unittest discover -s "SPrime Search/decision-field/bom/tests" -p 'test_experiment.py' -v
python "SPrime Search/decision-field/partial-observation/audit.py" --out /tmp/pass08-bom-regression-2
```

Expected: tests pass; Pass 08 audit exits 0.

- [ ] **Step 5: Commit Task 4**

```bash
git add "SPrime Search/decision-field/bom/core.py" \
        "SPrime Search/decision-field/bom/experiment.py" \
        "SPrime Search/decision-field/bom/tests/test_experiment.py"
git commit -m "Add obligation-scoped BOM verification"
```

---

### Task 5: End-to-end substitution search and evidence outputs

**Files:**
- Create: `SPrime Search/decision-field/bom/audit.py`
- Create: `SPrime Search/decision-field/bom/README.md`
- Create generated-on-audit evidence files under `SPrime Search/decision-field/bom/evidence/`.

**Interfaces:**
- Consumes: all previous tasks.
- Produces deterministic `SUMMARY.json`, `FRONTIER.json`, and `VERIFICATION.json`.

- [ ] **Step 1: Add audit assertions before evidence writing**

`audit.py` must perform, in this order:

1. Run all BOM unit tests in-process or as a subprocess and require success.
2. Build the reference catalog.
3. Validate every catalog spec.
4. Compare capability-cover results on a small synthetic catalog against a brute-force subset oracle.
5. Compare Pareto frontier against a direct pairwise oracle.
6. Build both hidden-mode candidate families under one `ObligationSpec`.
7. Verify every candidate on the complete finite witness domain.
8. Require deliberately invalid cheap candidates to fail.
9. Require at least one verified emergent effect for the fused construction.
10. Require the fused construction to be no worse on every declared dimension used for the regression claim and strictly better in at least `component_count` or `dedicated_probe_steps`; if not, record the negative result and fail the expected-regression assertion rather than rewriting the cost model.
11. Hash Pass 06–08 source/evidence files before and after and require no mutation.

- [ ] **Step 2: Implement canonical evidence documents**

`SUMMARY.json` must include:

```json
{
  "status": "PASS_BOUNDED",
  "obligation_id": "...",
  "candidate_count": 0,
  "verified_count": 0,
  "invalid_rejected_count": 0,
  "emergent_effect_certificates": [],
  "reference_assembly": "...",
  "pareto_frontier_ids": [],
  "claim_ceiling": "obligation-relative finite BOM substitution only"
}
```

Populate exact values at runtime; the shown zeros/empty lists are schema examples only and must never be committed as evidence.

`FRONTIER.json` contains complete assembly ids, part ids/versions, exact cost vectors, verifier status, and emergent effect ids.

`VERIFICATION.json` contains source hashes, reference-source before/after hashes, commands, Python version, deterministic-order assertion, and two-run evidence hash agreement field.

- [ ] **Step 3: Run audit twice into fresh directories**

```bash
python "SPrime Search/decision-field/bom/audit.py" --out /tmp/bom-run1
python "SPrime Search/decision-field/bom/audit.py" --out /tmp/bom-run2
cmp /tmp/bom-run1/SUMMARY.json /tmp/bom-run2/SUMMARY.json
cmp /tmp/bom-run1/FRONTIER.json /tmp/bom-run2/FRONTIER.json
```

Expected: both audits exit 0 and both comparisons are identical.

- [ ] **Step 4: Copy only canonical scientific evidence into the repo**

```bash
mkdir -p "SPrime Search/decision-field/bom/evidence"
cp /tmp/bom-run1/SUMMARY.json "SPrime Search/decision-field/bom/evidence/SUMMARY.json"
cp /tmp/bom-run1/FRONTIER.json "SPrime Search/decision-field/bom/evidence/FRONTIER.json"
cp /tmp/bom-run1/VERIFICATION.json "SPrime Search/decision-field/bom/evidence/VERIFICATION.json"
```

Update `VERIFICATION.json` with a `second_run_identical=true` record through an explicit audit argument or a separate deterministic finalization step; do not hand-edit scientific values.

- [ ] **Step 5: Write README with claim boundaries and run command**

README must state:

- BOM is an obligation-relative construction search tool, not a universal architecture optimizer.
- Pass 06–08 are reference assemblies and remain authoritative for their own evidence.
- emergent effects belong to verified assemblies, not component labels.
- the first probe-vs-fused baseline is synthetic except where it wraps the real Pass 08 hidden-mode witness.
- fewer components is not globally better; only declared Pareto dimensions count.

Run command:

```bash
python "SPrime Search/decision-field/bom/audit.py" --out /tmp/bom-fresh
```

- [ ] **Step 6: Commit Task 5**

```bash
git add "SPrime Search/decision-field/bom"
git commit -m "Add verified decision-field BOM substitution experiment"
```

---

### Task 6: Exact-commit CI integration

**Files:**
- Modify: `.github/workflows/sprime-decision-field-check.yml`

**Interfaces:**
- Consumes: BOM audit from Task 5.
- Produces: exact-commit CI replay with byte-stability checks against committed BOM evidence.

- [ ] **Step 1: Extend workflow path filters**

Ensure the workflow triggers on:

```yaml
- 'SPrime Search/decision-field/**'
- '.github/workflows/sprime-decision-field-check.yml'
```

The existing broad decision-field path already covers BOM; do not add redundant narrower paths.

- [ ] **Step 2: Add BOM replay step after Pass 07**

Add:

```yaml
- name: Re-run decision-field BOM twice
  shell: bash
  run: |
    set -euo pipefail
    rm -rf /tmp/bom-ci-1 /tmp/bom-ci-2
    python3 "SPrime Search/decision-field/bom/audit.py" --out /tmp/bom-ci-1
    python3 "SPrime Search/decision-field/bom/audit.py" --out /tmp/bom-ci-2
    cmp /tmp/bom-ci-1/SUMMARY.json /tmp/bom-ci-2/SUMMARY.json
    cmp /tmp/bom-ci-1/FRONTIER.json /tmp/bom-ci-2/FRONTIER.json
    python3 - <<'PY'
    import json
    from pathlib import Path
    committed = Path('SPrime Search/decision-field/bom/evidence')
    fresh = Path('/tmp/bom-ci-1')
    for name in ('SUMMARY.json','FRONTIER.json'):
        assert json.loads((committed/name).read_text()) == json.loads((fresh/name).read_text())
    print('PASS BOM scientific evidence replay')
    PY
```

Do not compare runtime timestamps or environment-specific fields byte-for-byte.

- [ ] **Step 3: Validate workflow syntax by reading the complete file and checking indentation**

Run any existing repository workflow/schema check if present; otherwise use a YAML parser only if already available. Do not add a PyYAML dependency solely for this check.

- [ ] **Step 4: Commit Task 6**

```bash
git add .github/workflows/sprime-decision-field-check.yml
git commit -m "Run BOM audit in SPrime decision-field CI"
```

---

### Task 7: Final verification, reviewable PR, and promotion gate

**Files:**
- No new implementation files unless verification exposes a defect.
- Update plan checkboxes only if the project convention permits; scientific evidence remains generated by the audit.

**Interfaces:**
- Produces a reviewable PR whose claims are bounded to the verified milestone.

- [ ] **Step 1: Run the full local verification stack**

```bash
python -m unittest discover -s "SPrime Search/decision-field/bom/tests" -v
python "SPrime Search/decision-field/bom/audit.py" --out /tmp/bom-final
python "SPrime Search/decision-field/partial-observation/audit.py" --out /tmp/pass08-final-regression
python "SPrime Search/decision-field/schedule/audit.py" --out /tmp/pass07-final-regression
```

Expected: all exit 0.

- [ ] **Step 2: Verify no prior scientific artifact changed**

Compare the branch against its pre-BOM base and require changes to be limited to:

```text
docs/superpowers/specs/2026-09-14-decision-field-bom-design.md
docs/superpowers/plans/2026-09-14-decision-field-bom-implementation.md
SPrime Search/decision-field/bom/**
.github/workflows/sprime-decision-field-check.yml
```

Any Pass 06–08 evidence/content change is a blocker unless separately justified and reviewed.

- [ ] **Step 3: Open PR with exact claim ceiling**

PR body must report:

- reference assembly wrapped, not rewritten;
- number of catalog parts and candidate assemblies searched;
- verified/failed/dominated counts;
- exact Pareto frontier;
- fused-action emergent-effect certificate;
- synthetic status of the dedicated-probe baseline;
- two-run deterministic evidence result;
- no universal optimality/equivalence claim.

- [ ] **Step 4: Wait for exact-head CI result and inspect failing step if any**

A green local audit is not substituted for GitHub CI. If CI fails, classify as implementation defect, evidence mismatch, environment issue, or workflow issue before changing scientific claims.

- [ ] **Step 5: Merge only after exact-head CI is green and PR remains mergeable**

Use expected head SHA in the merge action. Read back `main` and confirm the merged commit contains the BOM subtree and workflow update.

---

## Plan Self-Review Record

### Spec coverage

- Capability-based BOM and multi-capability parts: Tasks 1, 3, 4.
- Operational/evidence plane separation: Tasks 1, 4, 5.
- Intrinsic capability vs emergent effect: Tasks 1 and 4.
- Obligation, part, assembly records: Task 1.
- Typed boundaries/adapters: Task 2.
- Append-only catalog: Task 2.
- Deterministic capability/dependency/wiring search: Task 3.
- Pareto frontier with no default scalar score: Task 3.
- First hidden-mode substitution experiment: Task 4.
- Replacement rule and failure handling: Tasks 1, 4, 5.
- Provenance/reproducibility: Tasks 5–7.
- Reference artifacts preserved: Tasks 2, 5, 7.
- CI promotion gate: Tasks 6–7.

### Placeholder scan

No `TBD`, `TODO`, “similar to”, or unspecified test/code steps remain. Evidence JSON zeros shown in Task 5 are explicitly schema examples and forbidden as committed evidence.

### Type consistency

- `CostVector`, `ObligationSpec`, `PartSpec`, `AssemblySpec`, `EmergentEffectCertificate`, and `VerificationResult` originate in Task 1 and are consumed unchanged later.
- Search uses immutable `PartSpec` and `AssemblySpec` records; verifier effects refer to assembly ids, not part ids.
- Runtime wiring uses semantic port type strings; build-time dependencies remain capability names.
- The hidden-mode verifier owns the full operational-state loop, so monitor state and controller memory remain distinct throughout.
