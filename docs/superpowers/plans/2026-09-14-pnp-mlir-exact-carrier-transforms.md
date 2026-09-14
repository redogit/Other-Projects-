# P-vs-NP MLIR Exact Carrier Transform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement exact MLIR-native restriction, existential projection, decomposition, and carrier-change operations with independent finite verification and explicit cost/provenance records.

**Architecture:** Build on the foundation/parity stage. `pnp.rel` owns exact relational transformations; `pnp.xref` records typed lineage without certifying it; `pnp.evidence` verifies transform claims. Every transform must preserve its declared obligation and expose build/representation/query/verification costs separately.

**Tech Stack:** LLVM/MLIR 23.1.1, C++/TableGen/ODS, Python 3.12 finite reference oracles, lit/FileCheck.

**Spec:** `docs/superpowers/specs/2026-09-14-pnp-mlir-infinite-level-carrier-wave-design.md`

## Global Constraints

- Requires the completed foundation/parity stage.
- Exact transforms may not use temporal proposal signals.
- A cross-reference is lineage, not evidence.
- Compact representation does not imply cheap emptiness/query cost.
- Branching state growth and projection relation growth must remain separately observable.
- All finite exactness tests use independent reference encodings where practical.
- `pnp.rel.project_exists` must implement existential semantics exactly on its declared finite carrier, not heuristic elimination.
- Every transform records named cost dimensions and unresolved remainder.

---

## File Structure

Create:

```text
P versus NP Repair Lab/mlir/include/pnp/
  RelDialect.td
  RelOps.td
  XRefDialect.td
  XRefOps.td
P versus NP Repair Lab/mlir/lib/
  Rel/RelDialect.cpp
  Rel/RelOps.cpp
  XRef/XRefDialect.cpp
  XRef/XRefOps.cpp
  Transforms/Restrict.cpp
  Transforms/ProjectExists.cpp
  Transforms/Decompose.cpp
  Transforms/CarrierChange.cpp
P versus NP Repair Lab/mlir/python/
  relation_oracle.py
  verify_transform.py
P versus NP Repair Lab/mlir/test/
  transforms/restrict.mlir
  transforms/project-exists.mlir
  transforms/decompose.mlir
  transforms/carrier-change.mlir
  transforms/branch-vs-project-growth.mlir
  xref/lineage.mlir
  negative/xref-is-not-evidence.mlir
  python/test_relation_oracle.py
  python/test_verify_transform.py
```

---

### Task 1: Add `pnp.rel` and `pnp.xref` dialect surfaces

**Files:** create the dialect/ops files above and register them in `RegisterDialects.cpp`.

**Interfaces:**
- `pnp.rel.restrict : carrier -> carrier`
- `pnp.rel.project_exists : carrier -> carrier`
- `pnp.rel.decompose : carrier -> variadic carrier`
- `pnp.rel.change_carrier : carrier -> carrier`
- `pnp.xref.link : (source, destination) -> !pnp.xref.edge`

- [ ] **Step 1: Write failing parse/print tests**

```mlir
%p = "pnp.rel.project_exists"(%src) <{hidden = array<i64: 2, 4>, obligation = "sat"}> : (!pnp.carrier<cnf>) -> !pnp.carrier<boundary_relation>
%x = "pnp.xref.link"(%src, %p) <{transform = "project_exists", evidence = "UNVERIFIED"}> : (!pnp.carrier<cnf>, !pnp.carrier<boundary_relation>) -> !pnp.xref.edge
```

- [ ] **Step 2: Run `check-pnp-mlir` and confirm unknown dialect/op failures**

- [ ] **Step 3: Define ODS operations and verifiers**

Verifier rules:
- `project_exists.hidden` must be unique, nonnegative coordinate indices.
- source/destination carrier kinds must be legal for the named transform.
- `xref.link` must contain source/destination stable IDs and transform kind.
- `xref.link` may carry `evidence = UNVERIFIED|VERIFIED|REJECTED`, but creating the link never changes it to VERIFIED.

- [ ] **Step 4: Register both dialects and rerun tests**

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/include/pnp" "P versus NP Repair Lab/mlir/lib/Rel" "P versus NP Repair Lab/mlir/lib/XRef" "P versus NP Repair Lab/mlir/test/xref"
git commit -m "feat(pnp-mlir): add relational and cross-reference dialects"
```

---

### Task 2: Implement independent finite relation oracle

**Files:**
- Create: `mlir/python/relation_oracle.py`
- Create: `mlir/test/python/test_relation_oracle.py`

**Interfaces:**
- `restrict(rows: set[int], n: int, var: int, value: int) -> tuple[set[int], int]`
- `project_exists(rows: set[int], n: int, hidden: tuple[int, ...]) -> tuple[set[int], tuple[int, ...]]`

- [ ] **Step 1: Write exhaustive two-variable oracle tests**

```python
def test_project_exists_truth_table():
    # relation x0 XOR x1 = 1 -> projecting x1 leaves both x0 values
    rows = {0b01, 0b10}
    projected, kept = project_exists(rows, 2, (1,))
    assert kept == (0,)
    assert projected == {0, 1}
```

- [ ] **Step 2: Run and observe failure**

- [ ] **Step 3: Implement bit-exact finite semantics**

Projection must deduplicate equal retained tuples and never infer SAT/UNSAT beyond the represented relation.

- [ ] **Step 4: Exhaust all relations through n=3**

For each `n <= 3`, enumerate all subsets of `{0,...,2^n-1}` and compare restrict/project against direct existential truth evaluation.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/python/relation_oracle.py" "P versus NP Repair Lab/mlir/test/python/test_relation_oracle.py"
git commit -m "test(pnp-mlir): add independent finite relation oracle"
```

---

### Task 3: Implement `restrict` and `project_exists`

**Files:**
- Create: `lib/Transforms/Restrict.cpp`
- Create: `lib/Transforms/ProjectExists.cpp`
- Create: `test/transforms/restrict.mlir`
- Create: `test/transforms/project-exists.mlir`

**Interfaces:**
- Passes: `--pnp-apply-restrict`, `--pnp-project-exists` operating on explicit finite relation carriers first.

- [ ] **Step 1: Write failing MLIR transform tests with explicit relation rows**

Use a carrier attribute such as `rows = array<i64: ...>` only for bounded explicit-relation test carriers.

- [ ] **Step 2: Build and confirm pass-not-registered failure**

- [ ] **Step 3: Implement minimal exact transforms**

For `project_exists`, compute retained-coordinate row keys exactly and emit a new `boundary_relation` carrier plus a `pnp.xref.link` with `evidence = "UNVERIFIED"`.

- [ ] **Step 4: Add Python-vs-C++ exhaustive parity harness through n=3**

`verify_transform.py` runs the pass, parses emitted rows, and compares to `relation_oracle.py`.

- [ ] **Step 5: Add empty/full relation counterexamples**

Check projection of empty relation remains empty; projection of full relation remains full on retained coordinates.

- [ ] **Step 6: Commit**

```bash
git add "P versus NP Repair Lab/mlir/lib/Transforms/Restrict.cpp" \
        "P versus NP Repair Lab/mlir/lib/Transforms/ProjectExists.cpp" \
        "P versus NP Repair Lab/mlir/test/transforms" \
        "P versus NP Repair Lab/mlir/python/verify_transform.py"
git commit -m "feat(pnp-mlir): add exact restriction and existential projection"
```

---

### Task 4: Add exact decomposition and carrier-change gates

**Files:**
- Create: `lib/Transforms/Decompose.cpp`
- Create: `lib/Transforms/CarrierChange.cpp`
- Create tests listed above.

**Interfaces:**
- `decompose` only splits when independence is proved by variable-incidence partition for the explicit finite/CNF test surface.
- `change_carrier` requires a named converter and produces `UNVERIFIED` xref until evidence verification runs.

- [ ] **Step 1: Write a failing independent-components test**

Use two constraints over disjoint variable sets and expect two carriers.

- [ ] **Step 2: Write a failing false-decomposition counterprobe**

Use two constraints sharing one variable and assert the pass leaves one carrier or rejects the requested split.

- [ ] **Step 3: Implement component detection from declared incidence**

Do not infer independence from textual naming or cost heuristics.

- [ ] **Step 4: Implement one certified carrier-change calibration**

Initial calibration: affine XOR relation represented as explicit rows -> `gf2` carrier only when Gaussian-form equations reconstruct exactly the same relation on the bounded domain.

- [ ] **Step 5: Verify both directions against the finite oracle**

- [ ] **Step 6: Commit**

```bash
git add "P versus NP Repair Lab/mlir/lib/Transforms/Decompose.cpp" \
        "P versus NP Repair Lab/mlir/lib/Transforms/CarrierChange.cpp" \
        "P versus NP Repair Lab/mlir/test/transforms/decompose.mlir" \
        "P versus NP Repair Lab/mlir/test/transforms/carrier-change.mlir"
git commit -m "feat(pnp-mlir): add exact decomposition and carrier change"
```

---

### Task 5: Separate transform truth from transform evidence

**Files:**
- Create: `mlir/python/verify_transform.py`
- Extend: `EvidenceOps.td`, `EvidenceDialect.cpp`
- Create: `negative/xref-is-not-evidence.mlir`

**Interfaces:**
- `pnp.evidence.verify_exact` consumes source, destination, and xref and produces `!pnp.evidence.result`.
- `pnp.wave.admit` does not exist yet, so no transform is promoted by this plan.

- [ ] **Step 1: Write a negative test where a correct-looking xref lacks a certificate**

Expected: attempting to mark it VERIFIED without `verify_exact` is rejected.

- [ ] **Step 2: Implement evidence result with explicit `PASS|FAIL|UNRESOLVED`**

- [ ] **Step 3: Bind result to source/destination digests and obligation ID**

- [ ] **Step 4: Run deliberate destination-row mutation**

Expected: verifier returns FAIL while xref lineage remains recorded.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/include/pnp/EvidenceOps.td" \
        "P versus NP Repair Lab/mlir/lib/Evidence" \
        "P versus NP Repair Lab/mlir/python/verify_transform.py" \
        "P versus NP Repair Lab/mlir/test/negative/xref-is-not-evidence.mlir"
git commit -m "feat(pnp-mlir): separate transform lineage from exact verification"
```

---

### Task 6: Preserve state-growth versus relation-growth evidence

**Files:**
- Create: `test/transforms/branch-vs-project-growth.mlir`
- Create: `mlir/python/measure_transform_cost.py`
- Create: `mlir/test/python/test_measure_transform_cost.py`

**Interfaces:**
- Produces named metrics: `state_count`, `relation_rows`, `build_ops`, `verify_ops`, `carrier_bytes`.

- [ ] **Step 1: Write a test instance where branch duplicates state while projection grows relation rows**

The test asserts the two cost channels are reported separately, not summed into one unnamed score.

- [ ] **Step 2: Implement metric extraction**

```python
def cost_record(**dims):
    return {"schema": "pnp-cost-v1", "dimensions": {k: dims[k] for k in sorted(dims)}}
```

- [ ] **Step 3: Add negative test rejecting an unlabeled scalar `total_cost` as the only cost evidence**

- [ ] **Step 4: Run all transform, oracle, and foundation parity tests**

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/test/transforms/branch-vs-project-growth.mlir" \
        "P versus NP Repair Lab/mlir/python/measure_transform_cost.py" \
        "P versus NP Repair Lab/mlir/test/python/test_measure_transform_cost.py"
git commit -m "test(pnp-mlir): preserve transform cost channels"
```

---

## Stage Exit Gate

1. Restriction and existential projection agree with independent exhaustive finite oracles through n=3.
2. Decomposition refuses shared-variable false splits.
3. At least one bounded `explicit_relation -> gf2` conversion round-trips exactly.
4. Every transform emits lineage before evidence; lineage alone cannot become VERIFIED.
5. Deliberate transform corruption is detected.
6. Cost channels remain named and separate.
7. Foundation parity remains green.

## Self-Review Notes

- Covers spec Stages 3 and 5 prerequisites: exact transforms, existential carriers, cross-reference topology primitives, evidence/cost separation.
- Defers wavefront admission, decision policies, temporal ranking, and meta-level reification to later plans.
