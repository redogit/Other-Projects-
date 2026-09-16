# P-vs-NP MLIR Wavefront and Decision Topology Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement verified carrier-wave traversal, edge-first freedoms, decision-field topology, and the existing consequence-aware selector as a bounded MLIR policy without changing claim authority.

**Architecture:** `pnp.wave` owns admitted carrier regions and frontier state; `pnp.decision` owns legal actions and their relations; `pnp.xref` supplies the carrier topology. Selection is vector/cost aware and must preserve the current selector’s bounded `UNKNOWN` behavior. Only independently verified transform edges may enter the admitted wavefront.

**Tech Stack:** LLVM/MLIR 23.1.1, C++/TableGen/ODS, Python 3.12 parity/control harnesses, existing SAT64 selector fixtures.

**Spec:** `docs/superpowers/specs/2026-09-14-pnp-mlir-infinite-level-carrier-wave-design.md`

## Global Constraints

- Requires completed foundation/parity and exact-transform stages.
- `verified region -> frontier -> decision field -> proposal -> exact verification -> admit/reject/unresolved` is the only admission path.
- Degrees of freedom live on frontier actions; there is no fixed 199-dimensional latent state.
- Topology precedes geometry/Compass metadata.
- `UNKNOWN` causes unresolved/expand behavior, never implicit falsehood.
- Existing `consequence_selector_k4.py` scientific behavior is a parity target, not automatically the best policy.
- No arbitrary scalar collapse of incomparable cost dimensions.

---

## File Structure

Create:

```text
P versus NP Repair Lab/mlir/include/pnp/
  WaveDialect.td
  WaveOps.td
  DecisionDialect.td
  DecisionOps.td
P versus NP Repair Lab/mlir/lib/
  Wave/WaveDialect.cpp
  Wave/WaveOps.cpp
  Decision/DecisionDialect.cpp
  Decision/DecisionOps.cpp
  Transforms/BuildFrontier.cpp
  Transforms/ConsequenceK4.cpp
P versus NP Repair Lab/mlir/python/
  wave_oracle.py
  decision_parity.py
P versus NP Repair Lab/mlir/test/
  wave/frontier.mlir
  wave/admission.mlir
  wave/reject-unresolved.mlir
  decision/actions.mlir
  decision/action-relations.mlir
  decision/consequence-k4.mlir
  negative/unverified-admit.mlir
  negative/unknown-is-not-unsat.mlir
  python/test_wave_oracle.py
  python/test_decision_parity.py
```

---

### Task 1: Define verified wave regions and frontier edges

**Interfaces:**
- `!pnp.wave.region`
- `!pnp.wave.frontier`
- `pnp.wave.seed`, `pnp.wave.frontier`, `pnp.wave.admit`, `pnp.wave.reject`, `pnp.wave.unresolved`

- [ ] **Step 1: Write a failing frontier parse/print test**

```mlir
%region = "pnp.wave.seed"(%src) : (!pnp.carrier<cnf>) -> !pnp.wave.region
%frontier = "pnp.wave.frontier"(%region) : (!pnp.wave.region) -> !pnp.wave.frontier
```

- [ ] **Step 2: Add a failing negative admission test**

Construct an xref with `evidence = UNVERIFIED` and attempt `pnp.wave.admit`; expected verifier failure.

- [ ] **Step 3: Implement types/ops and verifier rules**

`admit` requires a `pnp.evidence.result` bound to the same source/destination/obligation with `PASS` status. `reject` and `unresolved` preserve the proposed edge in history.

- [ ] **Step 4: Run tests**

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/include/pnp/Wave"* "P versus NP Repair Lab/mlir/lib/Wave" "P versus NP Repair Lab/mlir/test/wave" "P versus NP Repair Lab/mlir/test/negative/unverified-admit.mlir"
git commit -m "feat(pnp-mlir): add verified carrier-wave regions"
```

---

### Task 2: Build frontier topology from typed cross-references

**Files:**
- Create: `lib/Transforms/BuildFrontier.cpp`
- Create: `python/wave_oracle.py`
- Create: `test/python/test_wave_oracle.py`

**Interfaces:**
- `build_frontier(admitted_ids: set[str], edges: list[dict]) -> list[dict]`
- MLIR pass: `--pnp-build-frontier`

- [ ] **Step 1: Write the independent topology oracle test**

```python
def test_frontier_contains_only_outgoing_unadmitted_edges():
    edges = [
        {"src": "A", "dst": "B", "id": "ab"},
        {"src": "B", "dst": "C", "id": "bc"},
        {"src": "A", "dst": "A", "id": "aa"},
    ]
    assert [e["id"] for e in build_frontier({"A"}, edges)] == ["ab"]
```

- [ ] **Step 2: Implement oracle with stable lexical ordering**

- [ ] **Step 3: Write failing MLIR pass test against the same topology**

- [ ] **Step 4: Implement the pass and compare emitted frontier IDs to the oracle**

- [ ] **Step 5: Add duplicate-derivation test**

Two different xrefs may target the same carrier ID; both derivation edges remain distinct in the frontier until admission/merging policy handles them.

- [ ] **Step 6: Commit**

```bash
git add "P versus NP Repair Lab/mlir/lib/Transforms/BuildFrontier.cpp" "P versus NP Repair Lab/mlir/python/wave_oracle.py" "P versus NP Repair Lab/mlir/test"
git commit -m "feat(pnp-mlir): derive edge-first carrier frontiers"
```

---

### Task 3: Define decision actions and action topology

**Interfaces:**
- `!pnp.decision.field`, `!pnp.decision.action`, `!pnp.decision.plan`
- `pnp.decision.available`, `compose`, `select`, `branch`, `rollback`
- action relation attribute values: `ENABLES`, `BLOCKS`, `INDEPENDENT`, `MUST_PRECEDE`, `REVERSIBLE_PAIR`, `COUPLED`, `EQUIV_FOR`

- [ ] **Step 1: Write failing action-field tests**

Each action record must include operation, target edge ID, precondition status, predicted consequence record, named cost vector, evidence state, recovery/reversibility, authority, and expected remainder.

- [ ] **Step 2: Add QIT metadata round-trip test**

```mlir
{direction = "@", resolution = "0.[S']", orientation = "+1"}
```

and verify `UNKNOWN` orientation stays a symbolic token distinct from `0`.

- [ ] **Step 3: Implement ODS types/ops/verifiers**

Reject missing target, unnamed cost vectors, and action relations that reference absent action IDs.

- [ ] **Step 4: Add action-topology tests**

Ensure `MUST_PRECEDE` cycles are reported as unresolved planning constraints rather than silently reordered; `INDEPENDENT` actions may be composed only when their typed targets do not conflict.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/include/pnp/Decision"* "P versus NP Repair Lab/mlir/lib/Decision" "P versus NP Repair Lab/mlir/test/decision"
git commit -m "feat(pnp-mlir): add typed decision-field topology"
```

---

### Task 4: Port the consequence-aware K4 policy as a parity-preserving pass

**Files:**
- Create: `lib/Transforms/ConsequenceK4.cpp`
- Create: `python/decision_parity.py`
- Create: `test/python/test_decision_parity.py`
- Create: `test/decision/consequence-k4.mlir`

**Interfaces:**
- Pass `--pnp-select-consequence-k4`
- Policy inputs: candidate actions carrying occurrence count and verified branch-probe burden vectors.
- Policy output: exactly one selected action or `UNRESOLVED` when no legal action exists.

- [ ] **Step 1: Encode the current ordering rule in a Python oracle**

```python
def choose(planned):
    return sorted(
        planned,
        key=lambda x: (
            tuple(x["worst_burden"]),
            x["combined_unknown_component"],
            -x["occurrence_count"],
            x["variable"],
        ),
    )[0]
```

Use exact field semantics from the current selector; do not use known SAT/UNSAT labels in planning.

- [ ] **Step 2: Write frozen-case parity tests**

Assert the selected variable and shortlist match the legacy parity manifest for all currently frozen cases.

- [ ] **Step 3: Implement the MLIR policy pass**

The pass may consume only action attributes and evidence already attached to the decision field.

- [ ] **Step 4: Run deliberate tie cases**

Verify lexical/variable tie-breaking is deterministic and matches the legacy rule.

- [ ] **Step 5: Preserve failed one-feedback-round policy as a separate named policy**

Do not overwrite its failure disposition; add a fixture recording that it remains a different pass/record.

- [ ] **Step 6: Commit**

```bash
git add "P versus NP Repair Lab/mlir/lib/Transforms/ConsequenceK4.cpp" "P versus NP Repair Lab/mlir/python/decision_parity.py" "P versus NP Repair Lab/mlir/test"
git commit -m "feat(pnp-mlir): port consequence-aware decision policy"
```

---

### Task 5: Implement bounded outward expansion semantics

**Files:**
- Extend: `WaveOps.td`, `WaveOps.cpp`
- Create: `test/wave/reject-unresolved.mlir`
- Create: `negative/unknown-is-not-unsat.mlir`

**Interfaces:**
- `pnp.wave.expand` consumes current region + unresolved frontier and produces a successor region descriptor without admitting unverified carriers.

- [ ] **Step 1: Write test: unresolved current frontier permits next-shell proposal generation**

- [ ] **Step 2: Write negative test: UNKNOWN cannot satisfy UNSAT termination**

Expected deterministic verifier error if a `#pnp.core.status<UNKNOWN>` is wired into an UNSAT-only termination op.

- [ ] **Step 3: Implement expand semantics**

Expansion adds legal adjacent proposal edges; it does not mark destinations admitted.

- [ ] **Step 4: Add resource-bound test**

When frontier/depth budget is exhausted, result must remain `BOUND` or `UNKNOWN` according to the declared source semantics, never inferred SAT/UNSAT.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/include/pnp/WaveOps.td" "P versus NP Repair Lab/mlir/lib/Wave" "P versus NP Repair Lab/mlir/test/wave" "P versus NP Repair Lab/mlir/test/negative/unknown-is-not-unsat.mlir"
git commit -m "feat(pnp-mlir): add bounded outward wave expansion"
```

---

### Task 6: End-to-end selector-wave parity

**Files:**
- Create: `test/parity/consequence-wave.mlir`
- Extend: `python/decision_parity.py`
- Modify: `.github/workflows/pnp-decision-field-check.yml`

- [ ] **Step 1: Build end-to-end fixtures from the frozen legacy cases**

For each case, emit source carrier -> verified probe carriers -> decision field -> selected branch -> wave outcome.

- [ ] **Step 2: Compare against legacy fields**

Required exact matches: status, shortlist, selected variable, state count, maximum depth, bounded termination reason, certificate lineage IDs.

- [ ] **Step 3: Add corruption counterprobe**

Mutate one burden vector or evidence ID; parity must fail.

- [ ] **Step 4: Add CI target `check-pnp-mlir-wave` after the foundation and exact-transform jobs**

- [ ] **Step 5: Run all three stage suites and existing P-vs-NP checks**

- [ ] **Step 6: Commit**

```bash
git add "P versus NP Repair Lab/mlir/test/parity/consequence-wave.mlir" "P versus NP Repair Lab/mlir/python/decision_parity.py" .github/workflows/pnp-decision-field-check.yml
git commit -m "ci(pnp-mlir): gate wave and decision parity"
```

---

## Stage Exit Gate

1. Unverified edges cannot enter admitted regions.
2. Frontier topology matches an independent oracle.
3. Decision actions are typed, costed, and topologically related.
4. K4 selection exactly matches frozen legacy cases.
5. `UNKNOWN` remains nonterminal for SAT/UNSAT unless a separate exact verifier resolves it.
6. Outward expansion respects explicit depth/frontier budgets.
7. Failed policies remain preserved as failures.
8. End-to-end wave parity and all earlier stage tests pass.

## Self-Review Notes

- Covers spec Stage 4 and the topology/edge-freedom/Decision Field portions of Stages 5-6.
- Temporal proposal dynamics and recursive meta-reification are intentionally deferred to the final plan.
