# P-vs-NP MLIR Completion and Legacy Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the approved dialect surface, migrate the bounded repair/full-cost execution paths behind exact MLIR contracts, and demote legacy executables to reference/oracle status only after complete parity.

**Architecture:** This is the completion stage after foundation, exact transforms, wave/decision, and meta/temporal stages. It fills the remaining declared operations, ports the exact bounded mutation routes without extending their proof domains, binds full-cost records into typed evidence, and performs the final primary/legacy authority switch with rollback preserved.

**Tech Stack:** LLVM/MLIR 23.1.1, C++/TableGen/ODS, Python 3.12, existing `mutation/` and `full_cost/` implementations as reference oracles.

**Spec:** `docs/superpowers/specs/2026-09-14-pnp-mlir-infinite-level-carrier-wave-design.md`

## Global Constraints

- All four earlier MLIR plans must be green before legacy demotion.
- Restricted mutation proofs retain exactly their original domains; no generalized theorem is inferred by porting them.
- Full-cost channels stay typed and separate; no invented scalar total replaces unlike counters.
- Legacy evidence files remain immutable and addressable after demotion.
- Demotion means “reference/oracle by default,” not deletion.
- Cross-project imports remain method/translation references only unless independently admitted as evidence.

---

## File Structure

Create/extend:

```text
P versus NP Repair Lab/mlir/include/pnp/
  CoreOps.td
  CarrierOps.td
  RelOps.td
  XRefOps.td
  EvidenceOps.td
  MetaOps.td
P versus NP Repair Lab/mlir/lib/
  Carrier/CarrierOps.cpp
  Rel/Join.cpp
  Rel/ChangeBasis.cpp
  Rel/Compile.cpp
  XRef/XRefQueries.cpp
  Evidence/EvidenceOps.cpp
  Meta/ComposePasses.cpp
  Meta/Search.cpp
  Mutation/RepairPass.cpp
  Mutation/ImplicationClosurePass.cpp
  FullCost/CostImport.cpp
P versus NP Repair Lab/mlir/tools/
  pnp-translate/
P versus NP Repair Lab/mlir/python/
  mutation_parity.py
  full_cost_parity.py
  migration_gate.py
P versus NP Repair Lab/mlir/test/
  carrier/query-reconstruct-digest.mlir
  rel/join.mlir
  rel/change-basis.mlir
  rel/compile.mlir
  xref/queries.mlir
  evidence/counterprobe-failure-ceiling.mlir
  meta/compose-search.mlir
  mutation/repair-parity.mlir
  mutation/implication-closure-parity.mlir
  full-cost/import-parity.mlir
  migration/demotion-gate.mlir
```

---

### Task 1: Complete core, carrier, evidence, xref, and meta operation surfaces

**Interfaces:**
- `pnp.core.require`
- `pnp.carrier.materialize`, `query`, `reconstruct`, `digest`
- `pnp.evidence.counterprobe`, `record_failure`, `claim_ceiling`
- `pnp.xref.predecessor`, `successor`, `equivalent_for`, `separation_depth`
- `pnp.meta.compose_passes`, `search`

- [ ] **Step 1: Write one failing round-trip/verifier test per missing op**

Example carrier query:

```mlir
%q = "pnp.carrier.query"(%c) <{kind = "nonempty", obligation = "sat"}> : (!pnp.carrier<boundary_relation>) -> i1
```

- [ ] **Step 2: Define ODS contracts**

`query` names the query semantics; `reconstruct` requires a recovery route; `digest` returns identity metadata only and never semantic truth. `claim_ceiling` is evidence metadata and cannot alter verdicts.

- [ ] **Step 3: Implement xref query ops over explicit lineage graph**

`equivalent_for` requires a named obligation and evidence result; `separation_depth` stores/returns a measured continuation-family depth, including `UNRESOLVED` when no finite witness is established.

- [ ] **Step 4: Implement meta composition/search over finite candidate lists**

`compose_passes` preserves declared pass order and obligation. `search` requires explicit candidate/depth/work caps and returns proposal records only.

- [ ] **Step 5: Run negative tests proving digest/reference/claim-ceiling cannot create evidence or verdict authority**

- [ ] **Step 6: Commit**

```bash
git add "P versus NP Repair Lab/mlir/include/pnp" "P versus NP Repair Lab/mlir/lib/Carrier" "P versus NP Repair Lab/mlir/lib/XRef" "P versus NP Repair Lab/mlir/lib/Evidence" "P versus NP Repair Lab/mlir/lib/Meta" "P versus NP Repair Lab/mlir/test"
git commit -m "feat(pnp-mlir): complete declared dialect operation surface"
```

---

### Task 2: Implement remaining exact relation operations

**Interfaces:**
- `pnp.rel.join`
- `pnp.rel.change_basis`
- `pnp.rel.compile`

- [ ] **Step 1: Write failing exact join test**

For finite relations sharing a declared boundary, compare join rows against direct tuple compatibility enumeration.

- [ ] **Step 2: Implement exact finite join**

Charge output-row construction separately from source read/query cost.

- [ ] **Step 3: Write failing reversible basis-change test**

Use a bounded invertible GF(2) affine transform and assert source -> transformed -> inverse reconstructs identical rows.

- [ ] **Step 4: Implement `change_basis` only for transforms carrying an explicit inverse/certificate path**

- [ ] **Step 5: Implement `compile` as a typed wrapper around a named compiler route**

Initial compiler routes must be explicitly registered; an unknown route is `UNRESOLVED`, not guessed.

- [ ] **Step 6: Add counterexamples for noninvertible basis matrices and compile routes whose verifier rejects**

- [ ] **Step 7: Commit**

```bash
git add "P versus NP Repair Lab/mlir/lib/Rel" "P versus NP Repair Lab/mlir/test/rel"
git commit -m "feat(pnp-mlir): complete exact relation transform set"
```

---

### Task 3: Port bounded general CNF repair without changing its boundary

**Files:**
- Create: `lib/Mutation/RepairPass.cpp`
- Create: `python/mutation_parity.py`
- Create: `test/mutation/repair-parity.mlir`

**Interfaces:**
- Pass: `--pnp-repair-bounded-cnf`
- Inputs: source CNF carrier, baseline assignment, protected bits, radius/resource cap.
- Outputs: exact repair result or explicit bound outcome plus evidence/cost record.

- [ ] **Step 1: Freeze reference outputs from current `mutation/repair.py` and audit cases**

- [ ] **Step 2: Write parity tests covering satisfiable repair, no repair within radius, protected-bit conflict, and resource-limit result**

- [ ] **Step 3: Implement pass by translating to the same declared search semantics**

Do not optimize in a way that changes minimum-repair ordering until parity is complete.

- [ ] **Step 4: Run the existing complete two-variable and seeded audit panels against both implementations**

- [ ] **Step 5: Assert identical status/minimum-repair witnesses and explicit cost-channel correspondence**

- [ ] **Step 6: Commit**

```bash
git add "P versus NP Repair Lab/mlir/lib/Mutation/RepairPass.cpp" "P versus NP Repair Lab/mlir/python/mutation_parity.py" "P versus NP Repair Lab/mlir/test/mutation/repair-parity.mlir"
git commit -m "feat(pnp-mlir): port bounded CNF repair with parity"
```

---

### Task 4: Port exact implication-closure repair with proof boundary encoded

**Files:**
- Create: `lib/Mutation/ImplicationClosurePass.cpp`
- Create: `test/mutation/implication-closure-parity.mlir`

**Interfaces:**
- Pass accepts only the declared class: one positive clause plus implication edges, all-zero baseline, and protected-zero semantics matching the current proof.

- [ ] **Step 1: Write positive-class parity fixtures from current macro audit**

- [ ] **Step 2: Write negative domain tests**

Reject multiple positive clauses, unsupported baseline semantics, or non-implication clauses with a deterministic `OUT_OF_DOMAIN`/`UNRESOLVED` result.

- [ ] **Step 3: Implement reachable-closure solver**

Choose the smallest allowed reachable closure under the same tie/ordering contract as the reference implementation.

- [ ] **Step 4: Re-run the complete finite implication audit and compare witnesses/results**

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/lib/Mutation/ImplicationClosurePass.cpp" "P versus NP Repair Lab/mlir/test/mutation/implication-closure-parity.mlir"
git commit -m "feat(pnp-mlir): port exact implication closure repair"
```

---

### Task 5: Import and verify the full-cost evidence surface

**Files:**
- Create: `lib/FullCost/CostImport.cpp`
- Create: `python/full_cost_parity.py`
- Create: `test/full-cost/import-parity.mlir`

**Interfaces:**
- `pnp.evidence.record_cost` dimensions map one-to-one to reference counters; unlike units remain separate.

- [ ] **Step 1: Freeze current full-cost output schemas and digests**

- [ ] **Step 2: Write failing mapping tests**

Every reference dimension must map to a named MLIR cost dimension; unmapped/extra load-bearing counters fail parity.

- [ ] **Step 3: Implement importer**

Preserve compilation, construction, index, planning, application, verification, memory/storage, and any route-specific counters separately.

- [ ] **Step 4: Add forbidden-collapse test**

An import that emits only `total_cost = sum(counters)` must fail validation.

- [ ] **Step 5: Run all current full-cost dimension/budget cases and compare typed records**

- [ ] **Step 6: Commit**

```bash
git add "P versus NP Repair Lab/mlir/lib/FullCost/CostImport.cpp" "P versus NP Repair Lab/mlir/python/full_cost_parity.py" "P versus NP Repair Lab/mlir/test/full-cost/import-parity.mlir"
git commit -m "feat(pnp-mlir): import full-cost evidence without scalar collapse"
```

---

### Task 6: Add `pnp-translate` for stable ingress/egress

**Files:**
- Create: `tools/pnp-translate/CMakeLists.txt`
- Create: `tools/pnp-translate/pnp-translate.cpp`
- Create translation tests.

**Interfaces:**
- `--import-parity-json`
- `--export-parity-json`
- `--import-cost-json`

- [ ] **Step 1: Write a failing JSON -> MLIR -> JSON round-trip test**

Use canonical key ordering and bind source digest/version.

- [ ] **Step 2: Implement translations using registered parser/printer functions**

- [ ] **Step 3: Reject JSON with unknown schema version or missing source digest**

- [ ] **Step 4: Verify exported JSON matches canonical parity/cost schema exactly for frozen fixtures**

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/tools/pnp-translate" "P versus NP Repair Lab/mlir/test"
git commit -m "feat(pnp-mlir): add provenance-bound translation tool"
```

---

### Task 7: Execute the final migration gate and demote legacy code safely

**Files:**
- Create: `python/migration_gate.py`
- Create: `test/migration/demotion-gate.mlir`
- Modify: `P versus NP Repair Lab/README.md`
- Modify: `P versus NP Repair Lab/CURRENT.md`
- Modify: `.github/workflows/pnp-decision-field-check.yml`

**Interfaces:**
- `migration_gate.py` returns success only when every declared parity/evidence suite passes at the same exact commit.

- [ ] **Step 1: Write failing gate test with one missing suite result**

```python
required = {"foundation", "transforms", "wave", "meta", "mutation", "full_cost"}
assert gate(required - {"full_cost"}) is False
```

- [ ] **Step 2: Implement gate requiring exact commit SHA and successful suite digests**

- [ ] **Step 3: Run complete CI twice on the same commit**

Require byte-identical deterministic scientific outputs for suites that promise determinism.

- [ ] **Step 4: Change documentation authority only after the gate passes**

README/CURRENT should state MLIR is the primary active implementation; legacy Python/C++ remains the reference/oracle and historical evidence path.

- [ ] **Step 5: Do not delete legacy code or evidence**

Add explicit links/commands for replaying the reference path.

- [ ] **Step 6: Add rollback instruction**

If future MLIR parity breaks, restore legacy-primary execution by documentation/config switch without rewriting history.

- [ ] **Step 7: Commit**

```bash
git add "P versus NP Repair Lab/mlir/python/migration_gate.py" "P versus NP Repair Lab/mlir/test/migration" "P versus NP Repair Lab/README.md" "P versus NP Repair Lab/CURRENT.md" .github/workflows/pnp-decision-field-check.yml
git commit -m "chore(pnp-mlir): promote verified MLIR successor"
```

---

## Final Completion Gate

1. Every operation named in the approved spec exists or has an explicit rejected/deferred disposition with evidence; this plan intends no deferred named operations.
2. Bounded CNF repair parity passes.
3. Restricted implication-closure parity passes and out-of-domain inputs are rejected.
4. Full-cost evidence maps without scalar collapse.
5. Translation round trips preserve schema, source identity, and provenance.
6. All earlier MLIR stages stay green.
7. Two exact-commit complete runs agree on deterministic scientific outputs.
8. Legacy code is demoted only after the migration gate; no historical artifact is deleted.

## Self-Review Notes

- Closes the operation-surface and legacy-migration gaps found during plan self-review.
- Preserves current proof domains and negative results.
- Completes the spec’s Stage 8 demotion requirement with an explicit reversible gate.
