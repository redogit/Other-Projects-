# P-vs-NP MLIR Foundation and Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a buildable MLIR 23.1.1 foundation that mirrors the current P-vs-NP execution record without changing solver semantics, and prove deterministic parity on frozen cases.

**Architecture:** The existing Python/C++ SAT64 and repair code remains authoritative during this stage. New `pnp.core`, `pnp.carrier`, and `pnp.evidence` dialects model source identity, carrier identity, verdicts, certificates, and cost records; a deterministic Python emitter converts frozen legacy execution records into MLIR, and a parity checker reconstructs the same scientific fields from MLIR.

**Tech Stack:** LLVM/MLIR `llvmorg-23.1.1`, CMake + Ninja, C++/TableGen/ODS, Python 3.12 standard library, lit/FileCheck where available, existing repository Python tests.

**Spec:** `docs/superpowers/specs/2026-09-14-pnp-mlir-infinite-level-carrier-wave-design.md`

## Global Constraints

- P vs NP remains open.
- Finite success is not an asymptotic theorem.
- Proposal is not admission.
- Cross-reference is not evidence.
- `UNKNOWN` is neither `false` nor numeric zero.
- Legacy evidence artifacts and failed runs are immutable predecessors.
- No temporal or meta-level object may create a SAT/UNSAT verdict in this stage.
- Existing `decision_field/`, `full_cost/`, and `mutation/` executables remain behaviorally unchanged.
- Pin compiler integration tests to LLVM/MLIR `llvmorg-23.1.1`; record `mlir-opt --version`, compiler version, and source tag in the parity manifest.
- Use `find_package(MLIR REQUIRED CONFIG)` and an explicit `MLIR_DIR`; do not vendor or silently download LLVM during normal local builds.

---

## File Structure

Create:

```text
P versus NP Repair Lab/mlir/
  CMakeLists.txt
  README.md
  cmake/PNPMLIRConfig.cmake
  include/pnp/
    CMakeLists.txt
    CoreDialect.td
    CoreOps.td
    CarrierDialect.td
    CarrierTypes.td
    CarrierOps.td
    EvidenceDialect.td
    EvidenceOps.td
    RegisterDialects.h
  lib/
    CMakeLists.txt
    Core/CoreDialect.cpp
    Carrier/CarrierDialect.cpp
    Evidence/EvidenceDialect.cpp
    RegisterDialects.cpp
  tools/pnp-opt/
    CMakeLists.txt
    pnp-opt.cpp
  python/
    freeze_parity_manifest.py
    emit_legacy_mlir.py
    check_parity.py
  test/
    lit.cfg.py
    lit.site.cfg.py.in
    CMakeLists.txt
    dialects/core-roundtrip.mlir
    dialects/carrier-roundtrip.mlir
    dialects/evidence-roundtrip.mlir
    negative/unknown-is-distinct.mlir
    python/test_freeze_parity_manifest.py
    python/test_emit_legacy_mlir.py
    python/test_check_parity.py
  evidence/parity-v1/
    manifest.json
```

Modify only after tests require it:

```text
P versus NP Repair Lab/decision_field/consequence_selector_k4.py
.github/workflows/pnp-decision-field-check.yml
```

The selector modification is restricted to an optional deterministic record-export hook; selection, checking, recursion, and result logic stay unchanged.

---

### Task 1: Freeze the legacy parity contract

**Files:**
- Create: `P versus NP Repair Lab/mlir/python/freeze_parity_manifest.py`
- Create: `P versus NP Repair Lab/mlir/test/python/test_freeze_parity_manifest.py`
- Create: `P versus NP Repair Lab/mlir/evidence/parity-v1/manifest.json`

**Interfaces:**
- Consumes: legacy `tree.json`, `SUMMARY.json`, node certificate JSON files, source commit metadata.
- Produces: `build_manifest(records: list[dict], metadata: dict) -> dict` and a canonical JSON manifest with sorted keys and SHA-256 file digests.

- [ ] **Step 1: Write the failing canonicalization test**

```python
from freeze_parity_manifest import build_manifest


def test_manifest_is_order_independent():
    metadata = {"source_commit": "abc", "llvm_tag": "llvmorg-23.1.1"}
    a = [{"path": "b.json", "sha256": "22"}, {"path": "a.json", "sha256": "11"}]
    b = list(reversed(a))
    assert build_manifest(a, metadata) == build_manifest(b, metadata)
```

- [ ] **Step 2: Run the test and confirm it fails because the module/function does not exist**

Run:

```bash
cd "P versus NP Repair Lab/mlir"
python3 -m unittest test/python/test_freeze_parity_manifest.py -v
```

Expected: import/function failure.

- [ ] **Step 3: Implement canonical manifest construction**

```python
def build_manifest(records, metadata):
    ordered = sorted(records, key=lambda x: x["path"])
    return {
        "schema": "pnp-mlir-parity-v1",
        "metadata": dict(sorted(metadata.items())),
        "records": ordered,
    }
```

Add SHA-256 helpers using `hashlib.sha256(path.read_bytes()).hexdigest()` and JSON serialization with `sort_keys=True`, `separators=(",", ":")`.

- [ ] **Step 4: Add a frozen-field test**

```python
def test_manifest_keeps_scientific_fields_explicit():
    record = {
        "case": "compiler_0",
        "status": "UNKNOWN",
        "selected_variable": 3,
        "planning_shortlist": [3, 1, 0],
        "states_evaluated": 7,
        "maximum_depth": 2,
    }
    out = build_manifest([{"path": "case.json", "sha256": "aa", "scientific": record}], {"source_commit": "abc"})
    assert out["records"][0]["scientific"]["status"] == "UNKNOWN"
```

- [ ] **Step 5: Run the unit tests**

Expected: PASS.

- [ ] **Step 6: Generate `manifest.json` from the current frozen cases without modifying their source artifacts**

Record at minimum: repository commit, selector file SHA-256, case names, status, shortlist, selected variable where present, state count, maximum depth, certificate paths/digests, and known failed-policy records.

- [ ] **Step 7: Commit**

```bash
git add "P versus NP Repair Lab/mlir/python/freeze_parity_manifest.py" \
        "P versus NP Repair Lab/mlir/test/python/test_freeze_parity_manifest.py" \
        "P versus NP Repair Lab/mlir/evidence/parity-v1/manifest.json"
git commit -m "test(pnp-mlir): freeze legacy parity contract"
```

---

### Task 2: Bootstrap an out-of-tree MLIR project

**Files:**
- Create: `P versus NP Repair Lab/mlir/CMakeLists.txt`
- Create: `P versus NP Repair Lab/mlir/README.md`
- Create: `P versus NP Repair Lab/mlir/include/pnp/CMakeLists.txt`
- Create: `P versus NP Repair Lab/mlir/lib/CMakeLists.txt`
- Create: `P versus NP Repair Lab/mlir/test/CMakeLists.txt`
- Create: `P versus NP Repair Lab/mlir/test/lit.cfg.py`
- Create: `P versus NP Repair Lab/mlir/test/lit.site.cfg.py.in`

**Interfaces:**
- Consumes: installed LLVM/MLIR 23.1.1 via `MLIR_DIR`.
- Produces: CMake targets `PNPMLIRHeaders`, `PNPMLIR`, `pnp-opt`, and `check-pnp-mlir`.

- [ ] **Step 1: Write a configure smoke script that expects the targets**

Create a CTest/lit smoke test whose failure message checks that `pnp-opt` is absent before target creation.

- [ ] **Step 2: Configure and confirm failure**

```bash
cmake -S "P versus NP Repair Lab/mlir" -B build/pnp-mlir -G Ninja -DMLIR_DIR="$MLIR_DIR"
```

Expected: fail because project CMake files/targets are incomplete.

- [ ] **Step 3: Add the root CMake configuration**

Use this structure:

```cmake
cmake_minimum_required(VERSION 3.20)
project(PNPMLIR LANGUAGES C CXX)

find_package(MLIR REQUIRED CONFIG)
find_package(LLVM REQUIRED CONFIG)

message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using MLIRConfig.cmake: ${MLIR_DIR}")

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

add_subdirectory(include/pnp)
add_subdirectory(lib)
add_subdirectory(tools/pnp-opt)
add_subdirectory(test)
```

- [ ] **Step 4: Add lit configuration with `pnp-opt` substitution**

Use `%pnp-opt` as the executable substitution and `%FileCheck` for checks; do not hard-code build paths in `.mlir` tests.

- [ ] **Step 5: Configure against LLVM/MLIR 23.1.1 and verify generation succeeds**

Run:

```bash
cmake -S "P versus NP Repair Lab/mlir" -B build/pnp-mlir -G Ninja -DMLIR_DIR="$MLIR_DIR"
```

Expected: configuration succeeds and reports LLVM package version 23.1.1.

- [ ] **Step 6: Commit**

```bash
git add "P versus NP Repair Lab/mlir/CMakeLists.txt" \
        "P versus NP Repair Lab/mlir/README.md" \
        "P versus NP Repair Lab/mlir/include/pnp/CMakeLists.txt" \
        "P versus NP Repair Lab/mlir/lib/CMakeLists.txt" \
        "P versus NP Repair Lab/mlir/test"
git commit -m "build(pnp-mlir): bootstrap standalone MLIR project"
```

---

### Task 3: Define `pnp.core`, `pnp.carrier`, and `pnp.evidence`

**Files:**
- Create: `include/pnp/CoreDialect.td`, `CoreOps.td`
- Create: `include/pnp/CarrierDialect.td`, `CarrierTypes.td`, `CarrierOps.td`
- Create: `include/pnp/EvidenceDialect.td`, `EvidenceOps.td`
- Create: `lib/Core/CoreDialect.cpp`, `lib/Carrier/CarrierDialect.cpp`, `lib/Evidence/EvidenceDialect.cpp`
- Create: dialect round-trip and negative tests listed above.

**Interfaces:**
- Produces MLIR names: `pnp.core.source`, `pnp.core.return`, `!pnp.core.verdict`, `!pnp.carrier<kind>`, `pnp.evidence.certificate`, `pnp.evidence.record_cost`.

- [ ] **Step 1: Write failing round-trip tests**

Example `core-roundtrip.mlir`:

```mlir
module {
  %src = "pnp.core.source"() <{source_id = "compiler_0", obligation = "sat"}> : () -> !pnp.carrier<cnf>
  "pnp.core.return"(%src) <{status = #pnp.core.status<UNKNOWN>}> : (!pnp.carrier<cnf>) -> ()
}
// CHECK: pnp.core.source
// CHECK: #pnp.core.status<UNKNOWN>
```

- [ ] **Step 2: Run lit and verify the dialect is unknown**

```bash
cmake --build build/pnp-mlir --target check-pnp-mlir
```

Expected: parser reports unknown `pnp.*` dialect/types.

- [ ] **Step 3: Define the dialects and carrier enum/type**

Carrier kinds must include at least: `cnf`, `boundary_relation`, `gf2`, `bijunctive`, `horn`, `dual_horn`, `matching`, `explicit_relation`, `shared_dag`, `circuit`, `partial_hard_survivor`, `nullary`.

Status enum must be symbolic only: `SAT`, `UNSAT`, `UNKNOWN`, `BOUND`.

- [ ] **Step 4: Add verifier rules**

`pnp.core.return` must require a declared symbolic status; no integer-to-status conversion op is provided. `pnp.evidence.record_cost` must require named dimensions and nonnegative integer/decimal payloads, not one implicit scalar total.

- [ ] **Step 5: Run round-trip and negative tests**

Expected: all pass; malformed status/cost records fail with deterministic verifier messages.

- [ ] **Step 6: Commit**

```bash
git add "P versus NP Repair Lab/mlir/include/pnp" "P versus NP Repair Lab/mlir/lib" "P versus NP Repair Lab/mlir/test/dialects" "P versus NP Repair Lab/mlir/test/negative"
git commit -m "feat(pnp-mlir): add core carrier and evidence dialects"
```

---

### Task 4: Register dialects in `pnp-opt`

**Files:**
- Create: `include/pnp/RegisterDialects.h`
- Create: `lib/RegisterDialects.cpp`
- Create: `tools/pnp-opt/pnp-opt.cpp`
- Create: `tools/pnp-opt/CMakeLists.txt`

**Interfaces:**
- Produces: executable `pnp-opt` that parses/prints all Stage-1 dialects.

- [ ] **Step 1: Write a failing executable smoke test**

```bash
%pnp-opt %s | %FileCheck %s
```

using a module containing all three dialects.

- [ ] **Step 2: Build and confirm failure because `pnp-opt` is missing/unregistered**

- [ ] **Step 3: Implement registry**

```cpp
void pnp::registerDialects(mlir::DialectRegistry &registry) {
  registry.insert<pnp::core::CoreDialect,
                  pnp::carrier::CarrierDialect,
                  pnp::evidence::EvidenceDialect>();
}
```

`pnp-opt.cpp` should use `MlirOptMain` with this registry and no transformation passes yet.

- [ ] **Step 4: Build and run**

```bash
cmake --build build/pnp-mlir --target pnp-opt check-pnp-mlir
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add "P versus NP Repair Lab/mlir/include/pnp/RegisterDialects.h" \
        "P versus NP Repair Lab/mlir/lib/RegisterDialects.cpp" \
        "P versus NP Repair Lab/mlir/tools/pnp-opt"
git commit -m "feat(pnp-mlir): register dialects in pnp-opt"
```

---

### Task 5: Emit deterministic MLIR from frozen legacy records

**Files:**
- Create: `mlir/python/emit_legacy_mlir.py`
- Create: `mlir/test/python/test_emit_legacy_mlir.py`
- Modify: `decision_field/consequence_selector_k4.py` only to add an optional post-run export call, with default behavior unchanged.

**Interfaces:**
- Produces: `emit_case(case: dict) -> str` and CLI `emit_legacy_mlir.py MANIFEST CASE OUT.mlir`.

- [ ] **Step 1: Write a failing deterministic emission test**

```python
from emit_legacy_mlir import emit_case


def test_unknown_remains_symbolic():
    text = emit_case({
        "case": "compiler_0",
        "status": "UNKNOWN",
        "planning_shortlist": [3, 1],
        "selected_variable": 3,
        "states_evaluated": 7,
    })
    assert "#pnp.core.status<UNKNOWN>" in text
    assert "status = 0" not in text
```

- [ ] **Step 2: Run and observe failure**

- [ ] **Step 3: Implement textual emission with stable ordering and escaped MLIR string attributes**

Required emitted facts: source identity, obligation, carrier kind, symbolic status, shortlist, selected variable where present, state/depth bounds, certificate reference IDs, named cost dimensions, provenance digest.

- [ ] **Step 4: Add byte-determinism test**

Call `emit_case` twice and assert exact string equality.

- [ ] **Step 5: Add optional selector export hook**

The selector may accept `--emit-mlir PATH` or an environment-neutral explicit function argument; when omitted, output bytes and execution logic must remain unchanged.

- [ ] **Step 6: Re-run the frozen selector regression and compare legacy outputs**

Expected: all pre-existing scientific JSON outputs are byte-identical when MLIR emission is disabled.

- [ ] **Step 7: Commit**

```bash
git add "P versus NP Repair Lab/mlir/python/emit_legacy_mlir.py" \
        "P versus NP Repair Lab/mlir/test/python/test_emit_legacy_mlir.py" \
        "P versus NP Repair Lab/decision_field/consequence_selector_k4.py"
git commit -m "feat(pnp-mlir): emit deterministic legacy mirror IR"
```

---

### Task 6: Reconstruct and enforce parity

**Files:**
- Create: `mlir/python/check_parity.py`
- Create: `mlir/test/python/test_check_parity.py`
- Create: `mlir/test/parity/frozen-cases.mlir`

**Interfaces:**
- Produces: `compare(expected: dict, reconstructed: dict) -> list[str]`; empty list means parity.

- [ ] **Step 1: Write a failing mismatch test**

```python
from check_parity import compare


def test_selected_variable_mismatch_is_load_bearing():
    expected = {"status": "UNKNOWN", "selected_variable": 3}
    got = {"status": "UNKNOWN", "selected_variable": 2}
    assert compare(expected, got) == ["selected_variable: expected 3, got 2"]
```

- [ ] **Step 2: Implement explicit field comparison**

Compare at least: status, selected variable, shortlist, states evaluated, maximum depth, bounded termination reason, certificate IDs/digests. Do not compare incidental wall-clock seconds for equality.

- [ ] **Step 3: Add a parser/reconstruction path**

Use `pnp-opt` canonical printed IR as the input boundary. The checker may initially parse a sidecar JSON emitted alongside MLIR if Python MLIR bindings are unavailable, but the MLIR file digest must be bound into that sidecar so it cannot drift independently.

- [ ] **Step 4: Run all frozen cases**

Expected: zero parity mismatches.

- [ ] **Step 5: Add deliberate corruption counterprobe**

Change one copied test fixture's selected variable/status and assert the checker fails.

- [ ] **Step 6: Commit**

```bash
git add "P versus NP Repair Lab/mlir/python/check_parity.py" \
        "P versus NP Repair Lab/mlir/test/python/test_check_parity.py" \
        "P versus NP Repair Lab/mlir/test/parity"
git commit -m "test(pnp-mlir): enforce legacy-to-MLIR parity"
```

---

### Task 7: Add exact-head CI without weakening existing checks

**Files:**
- Modify: `.github/workflows/pnp-decision-field-check.yml`
- Modify: `P versus NP Repair Lab/mlir/README.md`

**Interfaces:**
- CI adds a separate `pnp-mlir-parity` job; it does not replace existing P-vs-NP jobs.

- [ ] **Step 1: Add a failing workflow-level local script check**

The job must verify the expected LLVM tag/version and fail if it differs.

- [ ] **Step 2: Add dependency setup for LLVM/MLIR 23.1.1**

Use a pinned release/source package or a repository-owned cached installation path. Never use an unpinned `latest` URL. Record SHA-256 for downloaded archives in the workflow or repository metadata.

- [ ] **Step 3: Run the build/test sequence**

```bash
cmake -S "P versus NP Repair Lab/mlir" -B build/pnp-mlir -G Ninja -DMLIR_DIR="$MLIR_DIR"
cmake --build build/pnp-mlir --target pnp-opt check-pnp-mlir
python3 -m unittest discover -s "P versus NP Repair Lab/mlir/test/python" -v
```

- [ ] **Step 4: Run existing P-vs-NP regression checks in the same workflow without modification to their acceptance criteria**

Expected: existing checks still pass; new job reports parity independently.

- [ ] **Step 5: Update README with exact local build commands and claim ceiling**

Include the text: `MLIR parity is a representation/migration result, not evidence for P=NP or P!=NP.`

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/pnp-decision-field-check.yml "P versus NP Repair Lab/mlir/README.md"
git commit -m "ci(pnp-mlir): gate foundation on exact parity"
```

---

## Stage Exit Gate

Do not start native carrier transformations until all are true:

1. `pnp-opt` builds against LLVM/MLIR 23.1.1.
2. Core/carrier/evidence dialect parse-print tests pass.
3. `UNKNOWN` is represented symbolically and cannot be coerced to `false`/`0` by this dialect surface.
4. Frozen legacy cases emit deterministic MLIR.
5. Required scientific fields reconstruct with zero parity mismatches.
6. Deliberate parity corruption is detected.
7. Existing selector scientific outputs remain unchanged when emission is disabled.
8. Existing P-vs-NP CI remains intact.

## Self-Review Notes

- Spec coverage in this plan: Stages 0-2, core/carrier/evidence dialect foundation, legacy preservation, exact-head parity gate.
- Deliberately deferred: native existential transforms, topology/waves, decision passes, temporal dynamics, meta reification; each has its own plan.
- No placeholder implementation steps remain; each task has a concrete test, implementation boundary, command, and commit.
