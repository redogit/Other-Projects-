# P-vs-NP MLIR Meta, Temporal, and Recursive Reification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add proposal-only temporal/spiking frontier ranking and finite recursive meta-level reification while enforcing `LEVEL_UP != AUTHORITY_UP` and preserving all lower-level exactness/evidence boundaries.

**Architecture:** `pnp.temporal` attaches dynamical observations only to frontier edges and may rank proposals; it cannot emit verdicts or admission. `pnp.meta` reifies a finite lower-level carrier/transform graph as a higher-level carrier with a declared `realized_level = k`, bounded reification budget, stable identity, provenance, and explicit lowering/recovery route.

**Tech Stack:** LLVM/MLIR 23.1.1, C++/TableGen/ODS, Python 3.12 deterministic reference models, lit/FileCheck.

**Spec:** `docs/superpowers/specs/2026-09-14-pnp-mlir-infinite-level-carrier-wave-design.md`

## Global Constraints

- Requires completed foundation, exact-transform, and wave/decision stages.
- Temporal signals are proposal pressure only: `TEMPORAL_SIGNAL != SAT_AUTHORITY`.
- DTC-inspired simulation must never be labeled a physical discrete time crystal.
- Temporal coupling inherits existing carrier/xref adjacency; it does not invent an authoritative topology.
- Every meta run has finite `realized_level = k` and finite reification budget.
- Recursive reification past the declared level/budget must fail explicitly.
- `LEVEL_UP != AUTHORITY_UP` and `VIEWPOINT_CHANGE != TASK_CHANGE` are verifier-enforced design rules.
- A reified graph cannot change the obligation/evidence semantics of its source graph.

---

## File Structure

Create:

```text
P versus NP Repair Lab/mlir/include/pnp/
  TemporalDialect.td
  TemporalOps.td
  MetaDialect.td
  MetaOps.td
P versus NP Repair Lab/mlir/lib/
  Temporal/TemporalDialect.cpp
  Temporal/TemporalOps.cpp
  Meta/MetaDialect.cpp
  Meta/MetaOps.cpp
  Transforms/TemporalRank.cpp
  Transforms/Reify.cpp
  Transforms/Crystallize.cpp
P versus NP Repair Lab/mlir/python/
  temporal_reference.py
  meta_reference.py
P versus NP Repair Lab/mlir/test/
  temporal/edge-state.mlir
  temporal/rank-frontier.mlir
  temporal/topology-inheritance.mlir
  meta/reify-l1-l2.mlir
  meta/level-budget.mlir
  meta/crystallize.mlir
  negative/temporal-cannot-verdict.mlir
  negative/temporal-cannot-admit.mlir
  negative/level-up-cannot-change-obligation.mlir
  negative/meta-budget-exhaustion.mlir
  python/test_temporal_reference.py
  python/test_meta_reference.py
```

---

### Task 1: Define proposal-only temporal IR

**Interfaces:**
- `pnp.temporal.attach_edge_state`
- `pnp.temporal.spike`
- `pnp.temporal.measure_phase`
- `pnp.temporal.measure_locking`
- `pnp.temporal.rank_frontier`

- [ ] **Step 1: Write failing round-trip test**

```mlir
%t = "pnp.temporal.attach_edge_state"(%edge) <{
  phase = 0.25 : f64,
  amplitude = 1.0 : f64,
  rigidity = 0.9 : f64,
  persistence = 8 : i64,
  model = "DTC_INSPIRED_SIMULATION"
}> : (!pnp.xref.edge) -> !pnp.temporal.state
```

- [ ] **Step 2: Write negative type test: temporal op cannot return `!pnp.core.verdict`**

Expected: verifier/type registration makes such an op form impossible or rejects it deterministically.

- [ ] **Step 3: Define types/ops and register dialect**

Required edge-state fields: target xref ID, declared model kind, measurement provenance, optional phase/frequency/amplitude/rigidity/persistence/perturbation-response values.

- [ ] **Step 4: Add negative `temporal -> wave.admit` test**

Admission must still require `pnp.evidence.result<PASS>` tied to an exact verifier.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/include/pnp/Temporal"* "P versus NP Repair Lab/mlir/lib/Temporal" "P versus NP Repair Lab/mlir/test/temporal" "P versus NP Repair Lab/mlir/test/negative/temporal"*
git commit -m "feat(pnp-mlir): add proposal-only temporal dialect"
```

---

### Task 2: Implement deterministic temporal reference model over topology edges

**Files:**
- Create: `python/temporal_reference.py`
- Create: `test/python/test_temporal_reference.py`

**Interfaces:**
- `step(phases: dict[str,float], adjacency: dict[str,tuple[str,...]], drive: dict, coupling: float) -> dict[str,float]`
- `rank(signatures: dict[str,dict]) -> list[str]`

- [ ] **Step 1: Write adjacency-locality test**

```python
def test_non_adjacent_edge_does_not_couple():
    phases = {"ab": 0.0, "bc": 1.0, "xy": 2.0}
    adjacency = {"ab": ("bc",), "bc": ("ab",), "xy": ()}
    out = step(phases, adjacency, {"omega": 0.1}, 0.2)
    isolated = step({"xy": 2.0}, {"xy": ()}, {"omega": 0.1}, 0.2)
    assert out["xy"] == isolated["xy"]
```

- [ ] **Step 2: Implement a bounded deterministic oscillator update**

Use an explicitly documented discrete update, e.g. phase modulo `2*pi`, and fixed lexical iteration order. This is a DTC-inspired computational probe, not a physical DTC model claim.

- [ ] **Step 3: Add deterministic ranking test**

Ranking may use a declared tuple such as `(unresolved_flag, -rigidity, -persistence, edge_id)`; it must remain proposal-only.

- [ ] **Step 4: Add topology mutation counterprobe**

Changing adjacency while keeping all edge-local measurements fixed must be detectable in the next-state/ranking record when coupling is nonzero.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/python/temporal_reference.py" "P versus NP Repair Lab/mlir/test/python/test_temporal_reference.py"
git commit -m "test(pnp-mlir): add deterministic temporal topology reference"
```

---

### Task 3: Implement `--pnp-temporal-rank-frontier`

**Files:**
- Create: `lib/Transforms/TemporalRank.cpp`
- Create: `test/temporal/rank-frontier.mlir`
- Create: `test/temporal/topology-inheritance.mlir`

**Interfaces:**
- Pass consumes admitted wavefront + xref adjacency + temporal states.
- Pass writes a proposal-priority attribute/order only; it must not modify evidence status or verdicts.

- [ ] **Step 1: Write a failing rank test matching the Python reference**

- [ ] **Step 2: Implement ranking with stable edge-ID tie break**

- [ ] **Step 3: Add before/after assertions that evidence/verdict attributes are byte-identical**

- [ ] **Step 4: Compare pass ordering to `temporal_reference.rank`**

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/lib/Transforms/TemporalRank.cpp" "P versus NP Repair Lab/mlir/test/temporal"
git commit -m "feat(pnp-mlir): rank frontier with proposal-only temporal signals"
```

---

### Task 4: Define finite meta-level reification

**Interfaces:**
- `!pnp.meta.graph_carrier<level>`
- `pnp.meta.reify`
- `pnp.meta.lower_level`
- `pnp.meta.search`
- `pnp.meta.crystallize`

- [ ] **Step 1: Write failing L1->L2 reification round-trip**

```mlir
%g = "pnp.meta.reify"(%region) <{
  source_level = 1 : i64,
  realized_level = 2 : i64,
  max_level = 3 : i64,
  obligation = "sat",
  source_digest = "..."
}> : (!pnp.wave.region) -> !pnp.meta.graph_carrier<2>
```

- [ ] **Step 2: Add verifier tests**

Require `realized_level == source_level + 1`, `realized_level <= max_level`, same obligation ID, stable source digest, and explicit lowering/recovery route.

- [ ] **Step 3: Implement `lower_level` identity/recovery contract**

A reified carrier must reproduce the lower-level graph identity/provenance manifest; it need not reproduce pointer addresses or incidental printer formatting.

- [ ] **Step 4: Add negative obligation-change test**

Attempt to reify source obligation `sat` as `hodge` or another obligation; expected verifier failure `LEVEL_UP cannot change obligation`.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/include/pnp/Meta"* "P versus NP Repair Lab/mlir/lib/Meta" "P versus NP Repair Lab/mlir/test/meta" "P versus NP Repair Lab/mlir/test/negative/level-up-cannot-change-obligation.mlir"
git commit -m "feat(pnp-mlir): add finite recursive meta reification"
```

---

### Task 5: Enforce recursive level and work budgets

**Files:**
- Create: `python/meta_reference.py`
- Create: `test/python/test_meta_reference.py`
- Create: `negative/meta-budget-exhaustion.mlir`

**Interfaces:**
- `next_level(current: int, max_level: int, work_used: int, work_budget: int) -> int | None`

- [ ] **Step 1: Write boundary tests**

```python
def test_level_budget_stops_exactly_at_bound():
    assert next_level(2, 3, 4, 10) == 3
    assert next_level(3, 3, 4, 10) is None
    assert next_level(2, 4, 10, 10) is None
```

- [ ] **Step 2: Implement explicit exhaustion result**

Return/emit `BOUND` or `UNRESOLVED` according to the meta operation’s declared contract; never recurse silently.

- [ ] **Step 3: Add MLIR budget-exhaustion verifier/pass test**

- [ ] **Step 4: Add large requested-level counterprobe**

Request `max_level = 10^9` with work budget 2; verify only the allowed finite levels materialize and the run records budget exhaustion.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/python/meta_reference.py" "P versus NP Repair Lab/mlir/test/python/test_meta_reference.py" "P versus NP Repair Lab/mlir/test/negative/meta-budget-exhaustion.mlir"
git commit -m "test(pnp-mlir): bound recursive reification"
```

---

### Task 6: Crystallize only verified reusable transforms

**Files:**
- Create: `lib/Transforms/Crystallize.cpp`
- Create: `test/meta/crystallize.mlir`

**Interfaces:**
- `pnp.meta.crystallize` consumes a finite transform sequence plus verification results and emits a reusable macro/pass descriptor.

- [ ] **Step 1: Write failing unique-admission test**

One verified transform sequence -> crystallization allowed.

- [ ] **Step 2: Write zero/multiple survivor tests**

Zero verified candidates -> `REJECT_FRACTURE`; multiple equally admitted candidates -> `REJECT_AMBIGUOUS`. Do not arbitrarily choose one.

- [ ] **Step 3: Implement verifier and macro identity**

Macro ID must bind source sequence digests, obligation, finite bounds, verifier IDs, and cost record.

- [ ] **Step 4: Add replay test**

Applying the crystallized macro on its declared finite domain must match replaying its underlying verified transform sequence.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/lib/Transforms/Crystallize.cpp" "P versus NP Repair Lab/mlir/test/meta/crystallize.mlir"
git commit -m "feat(pnp-mlir): crystallize uniquely verified transform sequences"
```

---

### Task 7: Full L0->Lk integration and regression gate

**Files:**
- Create: `test/meta/end-to-end-levels.mlir`
- Extend: `.github/workflows/pnp-decision-field-check.yml`
- Update: `P versus NP Repair Lab/mlir/README.md`

- [ ] **Step 1: Construct a bounded end-to-end fixture**

Source CNF -> explicit carrier -> exact transform/xref -> verified wave -> decision field -> optional temporal ranking -> admitted transform -> meta reification to `k=2` -> lowering back to source graph identity.

- [ ] **Step 2: Assert standing firewalls**

Check exact strings/statuses for:

```text
TEMPORAL_SIGNAL != PROOF
LEVEL_UP != AUTHORITY_UP
VIEWPOINT_CHANGE != TASK_CHANGE
UNKNOWN != 0
```

as enforceable behavior/tests, not merely comments.

- [ ] **Step 3: Run all prior parity/exact/wave tests**

- [ ] **Step 4: Add CI job `pnp-mlir-meta-temporal` gated after earlier jobs**

- [ ] **Step 5: Update README with realized-level and temporal-model reporting rules**

- [ ] **Step 6: Commit**

```bash
git add "P versus NP Repair Lab/mlir/test/meta/end-to-end-levels.mlir" .github/workflows/pnp-decision-field-check.yml "P versus NP Repair Lab/mlir/README.md"
git commit -m "ci(pnp-mlir): gate recursive meta and temporal layers"
```

---

## Final Rewrite Exit Gate

The MLIR successor is eligible to become the primary active implementation only when:

1. All foundation parity tests pass.
2. Exact transforms pass independent finite exactness checks.
3. Wave admission rejects unverified carriers.
4. Decision policy parity passes current frozen cases.
5. Temporal ranking cannot alter verdict/evidence authority.
6. Reification is finite, budgeted, obligation-preserving, and reversible to a source-identity record.
7. Crystallization requires unique verified admission.
8. Existing failed/negative evidence remains preserved.
9. All named cost channels remain explicit.
10. Exact-head CI passes twice on the same commit with byte-identical deterministic scientific outputs.
11. Only then may legacy execution code be demoted to reference/oracle status; it is not deleted as historical evidence.

## Self-Review Notes

- Covers spec Stages 6-8 and the L∞ safety rule.
- Temporal dynamics are intentionally modest and proposal-only; no physical-DTC or complexity-speedup claim is encoded.
- Recursive `L∞` means extensibility, while every realized execution is finite and explicitly budgeted.
