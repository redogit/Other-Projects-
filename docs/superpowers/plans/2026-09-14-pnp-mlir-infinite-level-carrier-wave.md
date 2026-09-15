# P-vs-NP MLIR Infinite-Level Carrier-Wave Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the active P-vs-NP research execution path with a verified MLIR-based successor that makes carriers, existential transforms, cross-references, wavefronts, decision fields, temporal proposal signals, evidence, cost, and finite meta-level reification explicit while preserving all existing scientific boundaries and legacy evidence.

**Architecture:** Build an out-of-tree MLIR 23.1.0 project under `P versus NP Repair Lab/mlir/`. The legacy Python/C++ implementation remains the parity oracle until the corresponding MLIR path passes frozen parity tests; migration is successor-based rather than destructive. The implementation uses separate MLIR dialect namespaces (`pnp_core`, `pnp_carrier`, `pnp_rel`, `pnp_xref`, `pnp_wave`, `pnp_decision`, `pnp_temporal`, `pnp_evidence`, `pnp_meta`) because MLIR dialect namespaces are bare identifiers; these are the concrete syntax realization of the design document’s conceptual `pnp.core`, `pnp.carrier`, etc. layers.

**Tech Stack:** LLVM/MLIR 23.1.0, C++17 for the MLIR project, CMake >= 3.20, Ninja, Python 3.12 for repository parity tooling, LLVM lit/FileCheck for IR tests, existing C++20 only where `full_cost/` already requires it.

**Spec:** `docs/superpowers/specs/2026-09-14-pnp-mlir-infinite-level-carrier-wave-design.md`

## Global Constraints

- P vs NP remains open; no finite execution may be promoted to `P=NP` or `P!=NP`.
- `PROPOSAL != ADMISSION`, `REFERENCE != EVIDENCE`, `TEMPORAL_SIGNAL != PROOF`, `UNKNOWN != 0`, `UNKNOWN != false`.
- `LEVEL_UP != AUTHORITY_UP`; higher-level meta IR may analyze or compose lower levels but may not alter lower-level obligations or evidence semantics.
- Historical evidence artifacts, negative results, source snapshots, and frozen JSON outputs are predecessors and must not be rewritten.
- The legacy Python/C++ execution path remains authoritative for its current finite scope until parity is observed for the replacement path.
- The existing fast Python path must remain runnable without MLIR installed; MLIR is a new optional build/runtime surface until Stage 8 legacy demotion.
- LLVM and MLIR are pinned to `23.1.0` for this plan. The project must fail configuration when another MLIR ABI/API version is supplied rather than silently compiling against an unreviewed version.
- CMake minimum is `3.20.0`; the MLIR project uses C++17. Existing `full_cost/` C++20 code is not downgraded.
- The existing `P versus NP Repair Lab/decision_field/METHOD_FIREWALL.md` remains binding: cross-project material may transfer method schemas, never mathematical evidence.
- Every realized meta level records finite `realized_level = k`; exceeding the declared level/budget returns a bounded failure, not implicit recursion.
- Cost remains a typed vector. Unlike counters are never summed into an invented scalar total unless an obligation explicitly declares weights and units.
- All new decision logic is test-driven: failing test first, observed failure, minimal implementation, observed pass, then commit.

---

## File Structure

The implementation adds the following focused structure while retaining the existing `decision_field/`, `full_cost/`, and `mutation/` trees during parity:

```text
P versus NP Repair Lab/
  mlir/
    CMakeLists.txt
    README.md
    cmake/
      PNPMLIRConfig.cmake.in
    include/pnp/
      CMakeLists.txt
      CoreDialect.td
      CoreOps.td
      CarrierDialect.td
      CarrierTypes.td
      CarrierOps.td
      RelDialect.td
      RelOps.td
      XRefDialect.td
      XRefOps.td
      WaveDialect.td
      WaveOps.td
      DecisionDialect.td
      DecisionOps.td
      TemporalDialect.td
      TemporalOps.td
      EvidenceDialect.td
      EvidenceTypes.td
      EvidenceOps.td
      MetaDialect.td
      MetaOps.td
    lib/
      CMakeLists.txt
      Core/CoreDialect.cpp
      Carrier/CarrierDialect.cpp
      Rel/RelDialect.cpp
      XRef/XRefDialect.cpp
      Wave/WaveDialect.cpp
      Decision/DecisionDialect.cpp
      Temporal/TemporalDialect.cpp
      Evidence/EvidenceDialect.cpp
      Meta/MetaDialect.cpp
      Transforms/ExistentialProjection.cpp
      Transforms/DecisionWave.cpp
      Transforms/MetaReify.cpp
    tools/
      CMakeLists.txt
      pnp-opt/pnp-opt.cpp
      pnp-translate/pnp-translate.cpp
    python/
      pnp_mlir/__init__.py
      pnp_mlir/ir_model.py
      pnp_mlir/emit_legacy.py
      pnp_mlir/parity_adapter.py
      pnp_mlir/cost_adapter.py
      pnp_mlir/mutation_adapter.py
    test/
      CMakeLists.txt
      lit.cfg.py
      lit.site.cfg.py.in
      dialects/
      transforms/
      parity/
      negative/
      meta/
  mlir_parity/
    BASELINE.json
    SOURCE_LOCK.json
    README.md
.github/workflows/
  pnp-mlir-check.yml
```

The plan deliberately keeps dialect source files small: one dialect definition, operation group, and implementation unit per semantic responsibility.

---

### Task 1: Freeze the Legacy Parity Contract

**Files:**
- Create: `P versus NP Repair Lab/mlir_parity/BASELINE.json`
- Create: `P versus NP Repair Lab/mlir_parity/SOURCE_LOCK.json`
- Create: `P versus NP Repair Lab/mlir_parity/README.md`
- Create: `P versus NP Repair Lab/decision_field/test_mlir_baseline.py`
- Read-only oracle: `P versus NP Repair Lab/decision_field/consequence_selector_k4.py`
- Read-only oracle: `P versus NP Repair Lab/decision_field/one_feedback_round_selector.py`
- Read-only evidence: `P versus NP Repair Lab/decision_field/CONSEQUENCE_SELECTOR_K4_RESULT.json`
- Read-only evidence: `P versus NP Repair Lab/decision_field/ONE_FEEDBACK_ROUND_SELECTOR_RESULT.json`

**Interfaces:**
- Consumes: current repository HEAD, existing decision-field JSON records, current selector source hashes.
- Produces: `BASELINE.json` schema with `source_commit`, `oracle_files`, `cases`, `expected_status`, `expected_selected_variables`, `expected_shortlists`, `expected_state_counts`, `expected_negative_results`, and `claim_ceiling`.

- [ ] **Step 1: Write the failing baseline-lock test**

```python
# P versus NP Repair Lab/decision_field/test_mlir_baseline.py
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARITY = ROOT / "mlir_parity"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_baseline_locks_oracles_and_negative_results():
    baseline = json.loads((PARITY / "BASELINE.json").read_text())
    lock = json.loads((PARITY / "SOURCE_LOCK.json").read_text())
    assert baseline["universal_goal_status"] == "OPEN"
    assert baseline["unknown_is_false"] is False
    assert baseline["one_feedback_round"]["status"] == "EXECUTED_BOUNDED_NEGATIVE_RESULT"
    for rel, expected in lock["sha256"].items():
        assert sha256(ROOT / rel) == expected
```

- [ ] **Step 2: Run the test and observe the expected failure**

Run:

```bash
python3 -m pytest "P versus NP Repair Lab/decision_field/test_mlir_baseline.py" -q
```

Expected: FAIL because `mlir_parity/BASELINE.json` and `SOURCE_LOCK.json` do not exist.

- [ ] **Step 3: Generate the frozen baseline from existing records without rerunning or rewriting them**

Create `BASELINE.json` with the current bounded dispositions copied structurally from the existing evidence records, including at minimum:

```json
{
  "schema": "pnp-mlir-parity-v1",
  "universal_goal_status": "OPEN",
  "unknown_is_false": false,
  "unknown_is_zero": false,
  "consequence_k4": {
    "evidence_file": "decision_field/CONSEQUENCE_SELECTOR_K4_RESULT.json",
    "status": "EXECUTED_BOUNDED_NEGATIVE_RESULT"
  },
  "one_feedback_round": {
    "evidence_file": "decision_field/ONE_FEEDBACK_ROUND_SELECTOR_RESULT.json",
    "status": "EXECUTED_BOUNDED_NEGATIVE_RESULT"
  },
  "claim_ceiling": "finite parity contract only; no P-vs-NP conclusion"
}
```

Create `SOURCE_LOCK.json` containing SHA-256 digests for the two selector scripts and three current result records. `README.md` must state that a source change requires an explicit parity-contract successor rather than silent hash refresh.

- [ ] **Step 4: Re-run the baseline test**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir_parity" \
        "P versus NP Repair Lab/decision_field/test_mlir_baseline.py"
git commit -m "test(pnp): freeze MLIR rewrite parity baseline"
```

---

### Task 2: Add the Pinned Out-of-Tree MLIR Build and Test Harness

**Files:**
- Create: `P versus NP Repair Lab/mlir/CMakeLists.txt`
- Create: `P versus NP Repair Lab/mlir/README.md`
- Create: `P versus NP Repair Lab/mlir/include/pnp/CMakeLists.txt`
- Create: `P versus NP Repair Lab/mlir/lib/CMakeLists.txt`
- Create: `P versus NP Repair Lab/mlir/tools/CMakeLists.txt`
- Create: `P versus NP Repair Lab/mlir/test/CMakeLists.txt`
- Create: `P versus NP Repair Lab/mlir/test/lit.cfg.py`
- Create: `P versus NP Repair Lab/mlir/test/lit.site.cfg.py.in`
- Test: `P versus NP Repair Lab/mlir/test/negative/version-gate.test`

**Interfaces:**
- Consumes: installed LLVM/MLIR 23.1.0 CMake package.
- Produces: build targets `PNPMLIR`, `pnp-opt`, `pnp-translate`, and `check-pnp-mlir`.

- [ ] **Step 1: Write the failing CMake version-gate smoke test script**

```bash
# P versus NP Repair Lab/mlir/test/negative/version-gate.test
# RUN: %python %S/../../python/check_version_contract.py 23.1.0
```

Also create the initial failing Python checker invocation in `test/CMakeLists.txt` so `check-pnp-mlir` expects the file `python/check_version_contract.py`.

- [ ] **Step 2: Configure and observe failure before implementation**

Run:

```bash
cmake -S "P versus NP Repair Lab/mlir" -B /tmp/pnp-mlir-build -G Ninja \
  -DMLIR_DIR="$MLIR_DIR" -DLLVM_DIR="$LLVM_DIR"
```

Expected: FAIL because the project CMake files/version checker are not complete.

- [ ] **Step 3: Add the pinned top-level CMake contract**

Use this exact core:

```cmake
cmake_minimum_required(VERSION 3.20.0)
project(PNPMLIR LANGUAGES C CXX)

find_package(LLVM REQUIRED CONFIG)
find_package(MLIR REQUIRED CONFIG)

if(NOT LLVM_PACKAGE_VERSION VERSION_EQUAL "23.1.0")
  message(FATAL_ERROR "PNPMLIR requires LLVM 23.1.0; found ${LLVM_PACKAGE_VERSION}")
endif()
if(NOT MLIR_VERSION_MAJOR EQUAL 23)
  message(FATAL_ERROR "PNPMLIR requires MLIR 23.1.0-compatible APIs")
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED YES)
set(CMAKE_CXX_EXTENSIONS NO)

list(APPEND CMAKE_MODULE_PATH "${MLIR_CMAKE_DIR}" "${LLVM_CMAKE_DIR}")
include(TableGen)
include(AddLLVM)
include(AddMLIR)
include(HandleLLVMOptions)

include_directories(${LLVM_INCLUDE_DIRS})
include_directories(${MLIR_INCLUDE_DIRS})
include_directories(${PROJECT_SOURCE_DIR}/include)
include_directories(${PROJECT_BINARY_DIR}/include)
add_definitions(${LLVM_DEFINITIONS})

add_subdirectory(include)
add_subdirectory(lib)
add_subdirectory(tools)
add_subdirectory(test)
```

Create `python/check_version_contract.py` to return nonzero for anything other than `23.1.0`.

- [ ] **Step 4: Configure and run the empty harness**

Run:

```bash
cmake -S "P versus NP Repair Lab/mlir" -B /tmp/pnp-mlir-build -G Ninja \
  -DMLIR_DIR="$MLIR_DIR" -DLLVM_DIR="$LLVM_DIR"
ninja -C /tmp/pnp-mlir-build check-pnp-mlir
```

Expected: PASS for the harness/version contract.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir"
git commit -m "build(pnp): add pinned MLIR 23.1.0 harness"
```

---

### Task 3: Implement `pnp_core` and `pnp_carrier` Dialects

**Files:**
- Create: `P versus NP Repair Lab/mlir/include/pnp/CoreDialect.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/CoreOps.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/CarrierDialect.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/CarrierTypes.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/CarrierOps.td`
- Create: `P versus NP Repair Lab/mlir/lib/Core/CoreDialect.cpp`
- Create: `P versus NP Repair Lab/mlir/lib/Carrier/CarrierDialect.cpp`
- Test: `P versus NP Repair Lab/mlir/test/dialects/core-carrier.mlir`
- Test: `P versus NP Repair Lab/mlir/test/negative/unknown-is-not-false.mlir`

**Interfaces:**
- Produces: `!pnp_core.problem`, `!pnp_core.obligation`, `!pnp_core.verdict`, `!pnp_carrier.carrier<kind>` and operations `pnp_core.source`, `pnp_core.require`, `pnp_core.return`, `pnp_carrier.materialize`, `pnp_carrier.query`, `pnp_carrier.reconstruct`, `pnp_carrier.digest`.

- [ ] **Step 1: Write parse/verify tests before dialect code**

```mlir
// RUN: pnp-opt %s | FileCheck %s
module {
  %src = pnp_core.source {source_id = "case-0", encoded_size = 3 : i64}
      : () -> !pnp_core.problem
  %cnf = pnp_carrier.materialize %src {kind = "cnf", arity = 3 : i64}
      : !pnp_core.problem -> !pnp_carrier.carrier<"cnf">
  // CHECK: pnp_core.source
  // CHECK: !pnp_carrier.carrier<"cnf">
}
```

Negative test must attempt to encode `UNKNOWN` as a boolean attribute on a verdict-producing op and expect verifier rejection with `UNKNOWN is a distinct verdict state`.

- [ ] **Step 2: Run and observe unknown dialect failures**

Run:

```bash
ninja -C /tmp/pnp-mlir-build check-pnp-mlir
```

Expected: FAIL because `pnp_core` and `pnp_carrier` are not registered.

- [ ] **Step 3: Define ODS dialects/types/ops**

Use TableGen dialect names `pnp_core` and `pnp_carrier`; do not use dots in the dialect namespace. Define `CarrierType` with a string parameter `kind` and a verifier that accepts only the initial approved kinds:

```text
cnf, boundary_relation, gf2, bijunctive, horn, dual_horn,
matching, explicit_relation, shared_dag, circuit,
partial_hard_survivor, nullary
```

- [ ] **Step 4: Register both dialects in `pnp-opt` and pass tests**

`pnp-opt` registration must explicitly insert both generated dialect classes into a `DialectRegistry` before invoking `MlirOptMain`.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir"
git commit -m "feat(pnp-mlir): add core and carrier dialects"
```

---

### Task 4: Implement Exact Relation and Existential-Carrier Operations

**Files:**
- Create: `P versus NP Repair Lab/mlir/include/pnp/RelDialect.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/RelOps.td`
- Create: `P versus NP Repair Lab/mlir/lib/Rel/RelDialect.cpp`
- Create: `P versus NP Repair Lab/mlir/lib/Transforms/ExistentialProjection.cpp`
- Test: `P versus NP Repair Lab/mlir/test/transforms/project-exists.mlir`
- Test: `P versus NP Repair Lab/mlir/test/transforms/project-exists-exhaustive.py`
- Test: `P versus NP Repair Lab/mlir/test/negative/project-exists-invalid-partition.mlir`

**Interfaces:**
- Produces: `pnp_rel.restrict`, `pnp_rel.project_exists`, `pnp_rel.join`, `pnp_rel.decompose`, `pnp_rel.change_basis`, `pnp_rel.change_carrier`, `pnp_rel.compile`.
- `project_exists` consumes a carrier plus `hidden` and `retained` integer arrays and returns a destination carrier.

- [ ] **Step 1: Write the exhaustive small truth-table oracle first**

```python
from itertools import product


def project(rows, retained):
    return {tuple(row[i] for i in retained) for row in rows}


def test_projection_matches_existential_semantics():
    rows = {(0, 0, 0), (0, 1, 1), (1, 0, 1)}
    assert project(rows, (0, 2)) == {(0, 0), (0, 1), (1, 1)}
```

The executable test then generates every relation on up to 3 Boolean variables, every nonempty retained-coordinate subset, runs the MLIR transform, and compares the returned explicit relation to the independent Python set projection.

- [ ] **Step 2: Run and observe failure because the pass/op does not exist**

Expected: FAIL naming `pnp_rel.project_exists` or missing transform registration.

- [ ] **Step 3: Implement verifier and transform**

The verifier must enforce:

```text
hidden ∩ retained = ∅
hidden ∪ retained = [0, arity)
no duplicate coordinates
source arity matches the declared partition
obligation attribute is nonempty
```

For the first executable carrier, implement exact projection only for `explicit_relation` using a deterministic sorted tuple representation. For other kinds, retain the op but return `UNSUPPORTED_CARRIER` through pass diagnostics rather than pretending exact lowering exists.

- [ ] **Step 4: Run exhaustive projection and negative tests**

Expected: PASS for all relations through 3 variables and rejection of malformed partitions.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir"
git commit -m "feat(pnp-mlir): add exact existential carrier projection"
```

---

### Task 5: Implement Cross-Reference Topology and Provenance Identity

**Files:**
- Create: `P versus NP Repair Lab/mlir/include/pnp/XRefDialect.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/XRefOps.td`
- Create: `P versus NP Repair Lab/mlir/lib/XRef/XRefDialect.cpp`
- Test: `P versus NP Repair Lab/mlir/test/dialects/xref.mlir`
- Test: `P versus NP Repair Lab/mlir/test/negative/xref-is-not-evidence.mlir`
- Test: `P versus NP Repair Lab/mlir/test/transforms/shared-identity-distinct-provenance.mlir`

**Interfaces:**
- Produces: `!pnp_xref.edge`, `pnp_xref.link`, `predecessor`, `successor`, `equivalent_for`, `separation_depth`.
- Every link stores `source_id`, `destination_id`, `transform_id`, `obligation_id`, `preconditions`, `certificate_status`, `cost_ref`, `provenance_ref`, `recovery_ref`, and `remainder`.

- [ ] **Step 1: Write a negative test that tries to use an xref as an exact certificate**

```mlir
// RUN: not pnp-opt %s 2>&1 | FileCheck %s
module {
  // construct source, destination, and pnp_xref.link
  // then pass the edge to pnp_wave.admit without evidence
  // CHECK: admission requires pnp_evidence exact verification result
}
```

- [ ] **Step 2: Observe failure before xref/evidence typing exists**

- [ ] **Step 3: Implement xref identity semantics**

Two derivations may point to the same semantic carrier digest but must preserve different `provenance_ref` values. `equivalent_for` records obligation-relative equivalence and must require a named verifier reference; it is metadata about a checked relation, not automatic global identity.

- [ ] **Step 4: Pass identity/provenance tests**

Expected: same carrier digest can appear on two edges while provenance paths remain distinguishable.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir"
git commit -m "feat(pnp-mlir): add cross-reference carrier topology"
```

---

### Task 6: Implement Evidence, Typed Cost, and Admission Authority

**Files:**
- Create: `P versus NP Repair Lab/mlir/include/pnp/EvidenceDialect.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/EvidenceTypes.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/EvidenceOps.td`
- Create: `P versus NP Repair Lab/mlir/lib/Evidence/EvidenceDialect.cpp`
- Test: `P versus NP Repair Lab/mlir/test/dialects/evidence.mlir`
- Test: `P versus NP Repair Lab/mlir/test/negative/cost-unit-mismatch.mlir`

**Interfaces:**
- Produces: `!pnp_evidence.certificate`, `!pnp_evidence.cost`, `!pnp_evidence.result`, plus `verify_exact`, `counterprobe`, `record_failure`, `record_cost`, `claim_ceiling`.
- Cost vector fields: `state`, `relation`, `coupling`, `transform`, `decomposition`, `planning`, `carrier_discovery`, `selection`, `coupling_removal`, `boundary_construction`, `boundary_verification`, `proof_reconstruction`, `storage`, `query`, `recovery`.

- [ ] **Step 1: Write a failing typed-cost test**

The test creates two cost records with dimensions `row_operations` and `seconds` and attempts an unweighted add. Verifier must reject it with `cost dimensions require declared compatible unit or explicit weighting`.

- [ ] **Step 2: Observe failure before evidence dialect implementation**

- [ ] **Step 3: Implement evidence and cost types**

`verify_exact` returns an evidence result with enum status `PASS`, `FAIL`, or `UNRESOLVED`. `claim_ceiling` is mandatory on any result used by `pnp_wave.admit`. Cost stores a dictionary of named integer/decimal dimensions and their units; no generic `total` field is provided.

- [ ] **Step 4: Pass cost/evidence tests**

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir"
git commit -m "feat(pnp-mlir): add evidence and typed cost contracts"
```

---

### Task 7: Implement Wavefront and Decision-Field Dialects

**Files:**
- Create: `P versus NP Repair Lab/mlir/include/pnp/WaveDialect.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/WaveOps.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/DecisionDialect.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/DecisionOps.td`
- Create: `P versus NP Repair Lab/mlir/lib/Wave/WaveDialect.cpp`
- Create: `P versus NP Repair Lab/mlir/lib/Decision/DecisionDialect.cpp`
- Create: `P versus NP Repair Lab/mlir/lib/Transforms/DecisionWave.cpp`
- Test: `P versus NP Repair Lab/mlir/test/dialects/wave-decision.mlir`
- Test: `P versus NP Repair Lab/mlir/test/negative/admit-without-verifier.mlir`
- Test: `P versus NP Repair Lab/mlir/test/negative/unknown-direction.mlir`

**Interfaces:**
- Produces: `pnp_wave.seed`, `frontier`, `expand`, `admit`, `reject`, `unresolved`; `pnp_decision.available`, `compose`, `select`, `branch`, `rollback`.
- Decision action record fields: `op`, `direction`, `target`, `preconditions`, `predicted_consequence`, `cost_ref`, `evidence_ref`, `recovery_ref`, `authority`, `expected_remainder`.

- [ ] **Step 1: Write admission and UNKNOWN firewall tests**

One test must prove an unverified proposal cannot enter the admitted region. Another must prove the direction literal `UNKNOWN` cannot be parsed/normalized as `0`.

- [ ] **Step 2: Observe failures**

- [ ] **Step 3: Implement edge-first frontier semantics**

`pnp_wave.frontier` takes admitted carrier IDs and candidate xref edges; it returns only legal outgoing edges. `pnp_decision.available` filters actions whose explicit preconditions are satisfied. No Cartesian product is formed automatically; composition occurs only through `pnp_decision.compose` and requires compatibility attributes.

- [ ] **Step 4: Run wave/decision tests**

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir"
git commit -m "feat(pnp-mlir): add verified wavefront and decision fields"
```

---

### Task 8: Implement Temporal Proposal and Finite Meta-Level Reification Firewalls

**Files:**
- Create: `P versus NP Repair Lab/mlir/include/pnp/TemporalDialect.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/TemporalOps.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/MetaDialect.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/MetaOps.td`
- Create: `P versus NP Repair Lab/mlir/lib/Temporal/TemporalDialect.cpp`
- Create: `P versus NP Repair Lab/mlir/lib/Meta/MetaDialect.cpp`
- Create: `P versus NP Repair Lab/mlir/lib/Transforms/MetaReify.cpp`
- Test: `P versus NP Repair Lab/mlir/test/negative/temporal-cannot-verdict.mlir`
- Test: `P versus NP Repair Lab/mlir/test/meta/reify-finite.mlir`
- Test: `P versus NP Repair Lab/mlir/test/negative/reify-over-budget.mlir`

**Interfaces:**
- Produces: temporal operations `attach_edge_state`, `spike`, `measure_phase`, `measure_locking`, `rank_frontier`.
- Produces: meta operations `reify`, `compose_passes`, `search`, `crystallize`, `lower_level`.
- `reify` requires integer attributes `source_level`, `realized_level`, `max_level`; valid iff `realized_level == source_level + 1 && realized_level <= max_level`.

- [ ] **Step 1: Write the authority firewall tests first**

A temporal result passed directly to `pnp_core.return` or `pnp_wave.admit` must fail verification. A `pnp_meta.reify` request from level 3 to level 4 with `max_level = 3` must fail with `OUT_OF_BOUND`.

- [ ] **Step 2: Observe failures**

- [ ] **Step 3: Implement temporal data as proposal-only values and finite level checks**

Temporal state may store phase, frequency/subharmonic index, amplitude, rigidity, perturbation response, and spike history, but its result type must not be convertible to `!pnp_core.verdict` or `!pnp_evidence.result`.

- [ ] **Step 4: Pass meta/temporal tests**

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir"
git commit -m "feat(pnp-mlir): add temporal proposals and finite meta reification"
```

---

### Task 9: Build `pnp-opt` and Deterministic Legacy-to-MLIR Emission

**Files:**
- Create: `P versus NP Repair Lab/mlir/tools/pnp-opt/pnp-opt.cpp`
- Create: `P versus NP Repair Lab/mlir/tools/pnp-translate/pnp-translate.cpp`
- Create: `P versus NP Repair Lab/mlir/python/pnp_mlir/__init__.py`
- Create: `P versus NP Repair Lab/mlir/python/pnp_mlir/ir_model.py`
- Create: `P versus NP Repair Lab/mlir/python/pnp_mlir/emit_legacy.py`
- Modify: `P versus NP Repair Lab/decision_field/consequence_selector_k4.py`
- Test: `P versus NP Repair Lab/mlir/test/parity/emitter_determinism.py`

**Interfaces:**
- Adds optional CLI flag to the selector: `--emit-mlir PATH`. Existing positional invocation remains valid and behavior-identical when the flag is absent.
- `emit_legacy.py` exposes `emit_selector_run(run: dict) -> str`.

- [ ] **Step 1: Write the deterministic emitter test**

```python
from pnp_mlir.emit_legacy import emit_selector_run


def test_same_record_emits_byte_identical_ir():
    record = {
        "mode": "consequence_k4",
        "status": "UNKNOWN",
        "states_evaluated": 3,
        "planning_candidates": 4,
    }
    assert emit_selector_run(record).encode() == emit_selector_run(record).encode()
```

- [ ] **Step 2: Observe import/function failure**

- [ ] **Step 3: Implement stable Python IR model and emitter**

Emitter ordering must be canonical: stable keys, stable carrier IDs derived from source lineage/digest, no timestamps, no filesystem-dependent absolute paths. The selector must emit only after completing its existing calculation so emission cannot affect planning RNG/state.

- [ ] **Step 4: Verify legacy invocation is unchanged**

Run existing selector compile/check commands from `.github/workflows/pnp-decision-field-check.yml`, then run the new emitter test twice and compare SHA-256.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir" \
        "P versus NP Repair Lab/decision_field/consequence_selector_k4.py"
git commit -m "feat(pnp): emit deterministic MLIR from legacy selector"
```

---

### Task 10: Add Parity Reconstruction and Freeze the First MLIR Milestone

**Files:**
- Create: `P versus NP Repair Lab/mlir/python/pnp_mlir/parity_adapter.py`
- Create: `P versus NP Repair Lab/mlir/test/parity/consequence_selector_parity.py`
- Create: `P versus NP Repair Lab/mlir/test/parity/bounded_termination.py`
- Create: `P versus NP Repair Lab/mlir_parity/MILESTONE_1.json`

**Interfaces:**
- Produces: `reconstruct_selector_record(mlir_text: str) -> dict` with keys `status`, `selected_variables`, `shortlists`, `states_evaluated`, `maximum_depth`, `certificate_refs`, and `bounded_termination`.

- [ ] **Step 1: Write a parity test that compares emitted/reconstructed records to the frozen oracle**

The test must compare exactly the scientific/control fields named above and intentionally ignore non-semantic formatting.

- [ ] **Step 2: Observe failure because reconstruction is absent**

- [ ] **Step 3: Implement parser/reconstruction using `pnp-translate` JSON output**

Do not parse MLIR with regex. `pnp-translate --pnp-to-json` must load the dialects, parse MLIR, and emit canonical JSON; Python then compares that JSON to the legacy record.

- [ ] **Step 4: Run parity twice and create `MILESTONE_1.json` only from observed passing runs**

`MILESTONE_1.json` must record command lines, LLVM/MLIR version, source commit, source-lock digest, and the two output hashes. It must retain `universal_goal_status = OPEN`.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir" "P versus NP Repair Lab/mlir_parity/MILESTONE_1.json"
git commit -m "test(pnp-mlir): establish legacy parity milestone"
```

---

### Task 11: Port the Consequence Selector into MLIR-Native Decision/Wave Passes

**Files:**
- Create: `P versus NP Repair Lab/mlir/lib/Transforms/ConsequenceSelector.cpp`
- Create: `P versus NP Repair Lab/mlir/include/pnp/Passes.td`
- Create: `P versus NP Repair Lab/mlir/include/pnp/Passes.h`
- Test: `P versus NP Repair Lab/mlir/test/parity/consequence-selector-native.mlir`
- Test: `P versus NP Repair Lab/mlir/test/parity/consequence-selector-native.py`

**Interfaces:**
- Produces pass `--pnp-consequence-selector='k=4 node-cap=63 depth-cap=8'`.
- Pass consumes `pnp_decision.field` plus exact certificate summaries and produces `pnp_decision.select` and `pnp_wave` child edges.

- [ ] **Step 1: Write parity test for one frozen case**

Test must assert native pass selects the same variable and produces the same ordered child values as the legacy selector on `compiler_0`.

- [ ] **Step 2: Observe failure because pass is absent**

- [ ] **Step 3: Implement only the existing ordering semantics**

Port the existing burden tuple unchanged:

```text
(unknown_flag,
 max_unknown_component,
 unknown_component_count,
 d)
```

and the existing tie-break structure:

```text
(worst_burden, combined_unknown_component, -occurrence_count, variable)
```

Do not add a new heuristic in this task.

- [ ] **Step 4: Run all frozen selector cases and compare native vs legacy**

Expected: exact parity on status, selected variables, child ordering, state count, and bounded termination for the declared cases.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir"
git commit -m "feat(pnp-mlir): port consequence selector as native pass"
```

---

### Task 12: Preserve the Failed One-Feedback Policy as a First-Class Negative Result

**Files:**
- Create: `P versus NP Repair Lab/mlir/lib/Transforms/OneFeedbackSelector.cpp`
- Test: `P versus NP Repair Lab/mlir/test/parity/one-feedback-negative.py`
- Modify: `P versus NP Repair Lab/mlir_parity/MILESTONE_1.json`

**Interfaces:**
- Produces pass `--pnp-one-feedback-selector`.
- The pass has no promotion path; it reproduces the historical bounded policy for parity/counterprobe use.

- [ ] **Step 1: Write failing negative-result parity test**

Assert that `compiler_0` under the one-feedback policy uses strictly more states and greater maximum depth than its frozen baseline, while `compiler_1` retains its frozen state count, matching the current evidence record.

- [ ] **Step 2: Observe failure before pass implementation**

- [ ] **Step 3: Implement the policy without “repairing” it**

The point of this pass is historical reproducibility. Preserve its choice rule and scope boundary; do not substitute the new consequence selector.

- [ ] **Step 4: Run and confirm the negative result remains negative**

Update milestone metadata only with an added reproduction hash; do not change the scientific disposition.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir" "P versus NP Repair Lab/mlir_parity/MILESTONE_1.json"
git commit -m "test(pnp-mlir): preserve failed feedback selector evidence"
```

---

### Task 13: Integrate Full-Cost Records without Inventing a Scalar Objective

**Files:**
- Create: `P versus NP Repair Lab/mlir/python/pnp_mlir/cost_adapter.py`
- Create: `P versus NP Repair Lab/mlir/test/parity/full-cost-adapter.py`
- Read-only oracle: `P versus NP Repair Lab/full_cost/audit_replay.py`
- Read-only contracts: `P versus NP Repair Lab/full_cost/contract.json`, `contract_v6.json`, `audit_contract.json`

**Interfaces:**
- Produces: `load_full_cost_record(path) -> CostVector` and emission to `pnp_evidence.record_cost`.

- [ ] **Step 1: Write a failing adapter test using a checked-in small cost record**

The expected vector must preserve named counters and units independently. Assert there is no `total` key.

- [ ] **Step 2: Observe failure**

- [ ] **Step 3: Implement strict field mapping**

Known timing fields map to unit `seconds`; operation counts map to their exact named count units; bytes/bits remain storage units. Unknown fields are retained under `unclassified.<name>` and make the evidence result `UNRESOLVED` until explicitly classified; they are not dropped.

- [ ] **Step 4: Replay current full-cost audit and compare the mapped record**

Expected: source scientific outputs unchanged; adapter only adds a successor representation.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir"
git commit -m "feat(pnp-mlir): import full-cost vectors without scalar collapse"
```

---

### Task 14: Represent Mutation and Restricted Macro-Repair as Preconditioned MLIR Passes

**Files:**
- Create: `P versus NP Repair Lab/mlir/python/pnp_mlir/mutation_adapter.py`
- Create: `P versus NP Repair Lab/mlir/lib/Transforms/MutationRepair.cpp`
- Create: `P versus NP Repair Lab/mlir/lib/Transforms/ImplicationClosureRepair.cpp`
- Test: `P versus NP Repair Lab/mlir/test/parity/mutation-repair.py`
- Test: `P versus NP Repair Lab/mlir/test/negative/macro-repair-outside-proof-domain.mlir`
- Read-only oracle: `P versus NP Repair Lab/mutation/repair.py`
- Read-only oracle: `P versus NP Repair Lab/mutation/macro_repair.py`

**Interfaces:**
- General mutation pass returns exact finite bounded outcomes with the same caps as the source implementation.
- Implication-closure pass requires explicit precondition attribute `problem_class = "one_positive_clause_plus_implications"` and rejects all other classes.

- [ ] **Step 1: Write the proof-boundary rejection test**

Feed a CNF with two positive requirement clauses to the implication-closure pass and require rejection with `outside certified macro-repair domain`.

- [ ] **Step 2: Observe failure**

- [ ] **Step 3: Implement adapters and passes with source-equivalent preconditions**

Do not broaden the theorem. The general CNF repair path remains bounded search; the closure path remains polynomial only for its declared special class.

- [ ] **Step 4: Run existing mutation audits plus MLIR parity checks**

Expected: original audits pass unchanged and MLIR successors reconstruct the same results within the declared finite domain.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir"
git commit -m "feat(pnp-mlir): encode mutation repairs with proof boundaries"
```

---

### Task 15: Add Cross-Carrier Hard-Variety Calibration and Edge-First Wave Tests

**Files:**
- Create: `P versus NP Repair Lab/mlir/test/transforms/xor-native-vs-cnf.py`
- Create: `P versus NP Repair Lab/mlir/test/transforms/xor-amo-coupling.py`
- Create: `P versus NP Repair Lab/mlir/test/transforms/frontier-shells.py`
- Create: `P versus NP Repair Lab/mlir_parity/HARD_VARIETY_CALIBRATION.json`

**Interfaces:**
- Produces bounded calibration records for native GF(2), exact CNF encoding of the same relation, and coupled XOR+AMO relation cases.
- These are discriminator/calibration records only; they do not modify theorem status.

- [ ] **Step 1: Write the matched-obligation test first**

Use the same Boolean relation in native GF(2) and CNF encoding. Assert exact witness/nonemptiness agreement while permitting carrier cost/topology to differ.

- [ ] **Step 2: Observe failure until carrier transforms are wired**

- [ ] **Step 3: Implement only the minimum exact carrier bridges needed by the test**

No generic “smart hardness classifier” belongs in this task. Build explicit cross-references and record topology/cost differences.

- [ ] **Step 4: Add XOR+AMO coupling test and frontier-shell expansion check**

Expansion must occur from unresolved boundary edges only. The test must fail if a nonadjacent carrier is activated without a typed transform edge.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir" "P versus NP Repair Lab/mlir_parity/HARD_VARIETY_CALIBRATION.json"
git commit -m "test(pnp-mlir): add matched hard-variety carrier calibration"
```

---

### Task 16: Add Temporal Ranking as Proposal-Only Experimental Pass

**Files:**
- Create: `P versus NP Repair Lab/mlir/lib/Transforms/TemporalFrontierRank.cpp`
- Test: `P versus NP Repair Lab/mlir/test/negative/temporal-no-admission.mlir`
- Test: `P versus NP Repair Lab/mlir/test/transforms/temporal-ranking-deterministic.py`

**Interfaces:**
- Produces pass `--pnp-temporal-rank-frontier` which annotates frontier edges with ranking metadata only.
- Consumes declared phase/locking/spike metadata; produces no verdict and no evidence certificate.

- [ ] **Step 1: Write a test proving the pass cannot change SAT/UNSAT/UNKNOWN**

Run the same module with and without the temporal pass and compare all `pnp_core.return` verdict operands/attributes byte-for-byte.

- [ ] **Step 2: Observe failure before pass implementation**

- [ ] **Step 3: Implement deterministic ranking metadata**

Use a lexicographic tuple of explicitly supplied observables; do not create physical time-crystal claims. Record `physical_dtc = false` and `model = "dtc-inspired"` on the pass output.

- [ ] **Step 4: Run determinism and no-admission tests**

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir"
git commit -m "feat(pnp-mlir): add proposal-only temporal frontier ranking"
```

---

### Task 17: Add Recursive Meta-Composition and Crystallization with Finite-Level Budgets

**Files:**
- Create: `P versus NP Repair Lab/mlir/lib/Transforms/MetaSearch.cpp`
- Create: `P versus NP Repair Lab/mlir/lib/Transforms/Crystallize.cpp`
- Test: `P versus NP Repair Lab/mlir/test/meta/compose-verified-passes.mlir`
- Test: `P versus NP Repair Lab/mlir/test/meta/crystallize-unique.mlir`
- Test: `P versus NP Repair Lab/mlir/test/negative/crystallize-ambiguous.mlir`
- Test: `P versus NP Repair Lab/mlir/test/negative/meta-level-authority.mlir`

**Interfaces:**
- `pnp_meta.search` generates bounded candidate compositions from admitted lower-level operations.
- `pnp_meta.crystallize` succeeds only when exactly one candidate has independent `PASS` verification under the declared obligation.

- [ ] **Step 1: Write unique/none/multiple admission tests**

Required outcomes:

```text
1 verified candidate  -> ADMIT_UNIQUE
0 verified candidates -> REJECT_FRACTURE
>1 verified candidates -> REJECT_AMBIGUOUS
```

- [ ] **Step 2: Observe failure**

- [ ] **Step 3: Implement bounded search with explicit `max_depth`, `beam_width`, `candidate_cap`, `max_level`**

All four limits are mandatory attributes. Missing limits are verifier errors. `crystallize` may create a reusable pass reference but may not rewrite the obligation or claim ceiling.

- [ ] **Step 4: Pass meta and authority tests**

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir"
git commit -m "feat(pnp-mlir): add bounded recursive meta composition"
```

---

### Task 18: Add Exact-Head MLIR CI without Weakening Existing Fast Checks

**Files:**
- Create: `.github/workflows/pnp-mlir-check.yml`
- Modify: `.github/workflows/pnp-decision-field-check.yml`
- Modify: `P versus NP Repair Lab/mlir/README.md`

**Interfaces:**
- Existing `pnp-decision-field-check.yml` remains the fast Python/evidence gate.
- New `pnp-mlir-check.yml` pins llvm-project tag `llvmorg-23.1.0`, configures only LLVM+MLIR needed by this project, caches the LLVM build keyed by tag/toolchain, and runs `check-pnp-mlir` plus Python parity tests.

- [ ] **Step 1: Write local workflow-equivalent script and confirm it fails before CI plumbing**

Run:

```bash
git clone --depth 1 --branch llvmorg-23.1.0 https://github.com/llvm/llvm-project.git /tmp/llvm-project
cmake -S /tmp/llvm-project/llvm -B /tmp/llvm-build -G Ninja \
  -DLLVM_ENABLE_PROJECTS=mlir \
  -DLLVM_TARGETS_TO_BUILD=Native \
  -DLLVM_ENABLE_ASSERTIONS=ON \
  -DCMAKE_BUILD_TYPE=Release
ninja -C /tmp/llvm-build mlir-opt mlir-tblgen
cmake -S "P versus NP Repair Lab/mlir" -B /tmp/pnp-mlir-build -G Ninja \
  -DMLIR_DIR=/tmp/llvm-build/lib/cmake/mlir \
  -DLLVM_DIR=/tmp/llvm-build/lib/cmake/llvm
ninja -C /tmp/pnp-mlir-build check-pnp-mlir
```

Expected before workflow changes: local build may pass, but repository CI has no MLIR job and therefore the CI coverage test added in this task fails.

- [ ] **Step 2: Add workflow and path filters**

Trigger on:

```text
P versus NP Repair Lab/mlir/**
P versus NP Repair Lab/mlir_parity/**
P versus NP Repair Lab/decision_field/**
P versus NP Repair Lab/mutation/**
P versus NP Repair Lab/full_cost/**
.github/workflows/pnp-mlir-check.yml
```

Use the repository’s existing manual exact-commit checkout pattern rather than introducing a new checkout action dependency.

- [ ] **Step 3: Extend the fast workflow only with source-lock/parity-file validation**

Do not make the existing eight-minute Python workflow build LLVM. It should only verify that MLIR parity metadata refers to the exact commit/source lock when relevant files change.

- [ ] **Step 4: Run local workflow-equivalent commands twice**

Expected: both complete with byte-identical deterministic parity outputs.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/pnp-mlir-check.yml \
        .github/workflows/pnp-decision-field-check.yml \
        "P versus NP Repair Lab/mlir/README.md"
git commit -m "ci(pnp): add exact-head MLIR rewrite verification"
```

---

### Task 19: Document Migration Status and Demote Legacy Logic Only After Full Declared Parity

**Files:**
- Modify: `P versus NP Repair Lab/README.md`
- Modify: `P versus NP Repair Lab/CURRENT.md`
- Create: `P versus NP Repair Lab/mlir/MIGRATION_STATUS.md`
- Create: `P versus NP Repair Lab/mlir_parity/FINAL_PARITY.json`

**Interfaces:**
- `MIGRATION_STATUS.md` records each legacy surface as `ORACLE`, `MIRRORED`, `NATIVE_PARITY`, or `PRIMARY_MLIR`.
- A surface may become `PRIMARY_MLIR` only when its declared parity tests and CI pass at the exact branch head.

- [ ] **Step 1: Write a migration-state validation test**

Create `mlir/test/parity/migration_status.py` that rejects `PRIMARY_MLIR` unless a matching parity evidence entry exists with `status = PASS`, source hashes, exact commit, and two-run deterministic hashes.

- [ ] **Step 2: Observe failure if any surface is prematurely promoted**

- [ ] **Step 3: Populate migration status from actual observed evidence**

Do not mark unported functionality primary. Negative-result policies remain archived/oracle surfaces even if perfectly reproduced.

- [ ] **Step 4: Run the complete test suite and produce `FINAL_PARITY.json` from observed outputs**

Run:

```bash
python3 -m pytest "P versus NP Repair Lab/decision_field/test_mlir_baseline.py" -q
python3 "P versus NP Repair Lab/mutation/audit.py" --output /tmp/cnf-repair-audit-final
python3 "P versus NP Repair Lab/mutation/audit_macro.py" --output /tmp/implication-repair-audit-final
ninja -C /tmp/pnp-mlir-build check-pnp-mlir
```

Then re-run the MLIR suite a second time and require deterministic scientific/parity hashes where promised.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/README.md" \
        "P versus NP Repair Lab/CURRENT.md" \
        "P versus NP Repair Lab/mlir/MIGRATION_STATUS.md" \
        "P versus NP Repair Lab/mlir_parity/FINAL_PARITY.json"
git commit -m "docs(pnp): record verified MLIR successor migration state"
```

---

## Self-Review Results

### 1. Spec coverage

- Exact problem/carrier semantics: Tasks 3-4.
- Existential carriers: Task 4.
- Cross-reference topology/provenance: Task 5.
- Evidence/cost/claim ceiling: Task 6 and Task 13.
- Edge-first wavefront freedoms and Decision Fields: Task 7.
- Temporal/spiking proposal-only layer: Tasks 8 and 16.
- Finite recursive `L(n+1)` reification and `LEVEL_UP != AUTHORITY_UP`: Tasks 8 and 17.
- Legacy consequence selector parity/native port: Tasks 9-11.
- Historical failed selector preserved: Task 12.
- Full-cost and mutation proof-boundary integration: Tasks 13-14.
- Hard-variety cross-carrier calibration: Task 15.
- CI and exact-head verification: Task 18.
- Legacy demotion only after parity: Task 19.

No approved design section is intentionally dropped.

### 2. Placeholder scan

The plan contains no `TBD`, `TODO`, “implement later”, unspecified error-handling instruction, or “similar to Task N” shortcut. Each task names concrete files, commands, expected failure/pass behavior, and commit boundary.

### 3. Type/name consistency

Concrete MLIR namespaces intentionally use underscores (`pnp_core`, `pnp_carrier`, `pnp_rel`, `pnp_xref`, `pnp_wave`, `pnp_decision`, `pnp_temporal`, `pnp_evidence`, `pnp_meta`) because MLIR dialect namespaces are bare identifiers. The approved design’s dotted names remain conceptual section labels only. `UNKNOWN` remains an explicit verdict status throughout and never aliases boolean false or integer zero. `pnp_wave.admit` consistently requires a `pnp_evidence` exact verification result. `pnp_meta.reify` consistently uses finite `source_level`, `realized_level`, and `max_level` attributes.

## Execution Handoff

The selected execution mode is **1. Subagent-Driven**. Execute this plan from an isolated worktree using `superpowers:subagent-driven-development`, with one fresh implementer per task, task-level spec/code review after every commit, and a whole-branch review before integration.
