# BOM Fast Execution + Decision Questions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an exact indexed/native BOM accelerator, incremental search state, consequence-ranked questions, structured explanations, and a safely trained ordering heuristic without changing the exact obligation or evidence boundary.

**Architecture:** The existing BOM search remains the exhaustive oracle. `bom/fast/` compiles parts/obligations into bit masks, performs proof-safe pruning and incremental updates, ranks consequential questions, and optionally uses a trained deterministic integer ranker only to order work. A C++ kernel accelerates the exact subset hot path; all load-bearing results are cross-checked against Python on bounded oracle families.

**Tech Stack:** Python 3.12+ standard library, C++17, unittest, JSON evidence.

**Spec:** `docs/superpowers/specs/2026-09-14-bom-fast-question-engine-design.md`

## Global Constraints

- Existing `bom/` implementation is the correctness oracle and must not be weakened.
- Learned ranking may reorder work only; it cannot validate, prune, dominate, or promote.
- All synthetic task generation is deterministic and seed/family recorded.
- Train/validation/test split is by task family: 60/20/20 via deterministic family hash.
- Exact scientific outputs must reproduce byte-for-byte across two runs.
- Runtime claims are environment-qualified; candidate/expansion counts are primary stable metrics.
- Existing Pass 06–08 and BOM scientific artifacts remain unchanged.

---

### Task 1: Compile exact BOM structural index

**Files:**
- Create: `SPrime Search/decision-field/bom/fast/index.py`
- Create: `SPrime Search/decision-field/bom/fast/tests/test_index.py`

**Interfaces:**
- Consumes: `ObligationSpec`, `PartSpec`, `PartCatalog`.
- Produces: `CompiledIndex`, `compile_index(obligation, catalog)`, exact masks and stable slots.

- [ ] **Step 1: Write failing tests** verifying deterministic slots, capability masks, dependency masks, cost tuples, and exact port adjacency independent of catalog registration order.
- [ ] **Step 2: Run** `python3 -m unittest discover -s "SPrime Search/decision-field/bom/fast/tests" -p 'test_index.py' -v`; expected import/module failure.
- [ ] **Step 3: Implement minimal `CompiledIndex`** with canonical slot order `(stable_id,version)`, capability bit assignment sorted lexically, part provide/require masks, declared cost tuple order, and port adjacency.
- [ ] **Step 4: Re-run tests** and require all pass.
- [ ] **Step 5: Commit** `Add exact compiled BOM structural index`.

### Task 2: Add proof-safe indexed search and incremental state

**Files:**
- Create: `SPrime Search/decision-field/bom/fast/incremental.py`
- Create: `SPrime Search/decision-field/bom/fast/tests/test_incremental.py`

**Interfaces:**
- Consumes: `CompiledIndex`.
- Produces: `SearchCertificate`, `IncrementalSearchState`, `enumerate_indexed_candidates()`, `apply_distinction()`.

- [ ] **Step 1: Write failing tests** comparing indexed candidate masks with existing `candidate_part_sets()` on generated <=12-part cases; test exact rejection reasons and cache invalidation by dependency fingerprint.
- [ ] **Step 2: Run targeted tests**; expected module failure.
- [ ] **Step 3: Implement proof-safe masks**: missing required capability, missing dependency provider, explicit active-part exclusion; no learned pruning.
- [ ] **Step 4: Implement incremental fingerprints** using canonical JSON hashes of obligation distinctions; changed keys invalidate only dependent cached records.
- [ ] **Step 5: Re-run tests** including randomized deterministic seed set and require exact candidate-set equality.
- [ ] **Step 6: Commit** `Add proof-safe incremental BOM search`.

### Task 3: Consequence-ranked question engine and WHY records

**Files:**
- Create: `SPrime Search/decision-field/bom/fast/question.py`
- Create: `SPrime Search/decision-field/bom/fast/explain.py`
- Create: `SPrime Search/decision-field/bom/fast/tests/test_question.py`

**Interfaces:**
- Produces: `QuestionSpec`, `QuestionScore`, `rank_questions()`, `why_assembly()`, `why_question()`.

- [ ] **Step 1: Write failing tests** where a zero-value question is rejected, a 2/2 split outranks a 3/1 split under minimax, frontier-changing questions outrank equal-survivor non-frontier questions, and cost breaks remaining ties.
- [ ] **Step 2: Run tests**; expected module failure.
- [ ] **Step 3: Implement exact question partitions** over current viable assembly ids and answer domains.
- [ ] **Step 4: Implement lexicographic minimax score** `(worst_survivors, -guaranteed_eliminations, -frontier_change_answers, acquisition_cost, question_id)`.
- [ ] **Step 5: Implement structured WHY output** carrying inclusion/rejection certificate, dominance dimensions, cache provenance, and answer-specific frontier effect.
- [ ] **Step 6: Re-run tests** and commit `Add consequence-ranked BOM questions and explanations`.

### Task 4: Proper deterministic training pipeline

**Files:**
- Create: `SPrime Search/decision-field/bom/fast/train.py`
- Create: `SPrime Search/decision-field/bom/fast/tests/test_train.py`

**Interfaces:**
- Produces: `TrainingExample`, `RankerModel`, `generate_training_families()`, `family_split()`, `train_pairwise_perceptron()`, `evaluate_ranker()`.

- [ ] **Step 1: Write failing tests** for family-level 60/20/20 disjoint splits, deterministic examples/weights, exact final-frontier invariance with and without model, model fallback on degraded held-out performance, and rejection of deliberately label-corrupted training.
- [ ] **Step 2: Run tests**; expected module failure.
- [ ] **Step 3: Implement deterministic family generator** using exact small BOM oracle labels; record family id, seed, feature tuple, exact preferred ordering label.
- [ ] **Step 4: Implement deterministic integer pairwise perceptron** with fixed epochs/order and canonical tie-breaking; no floating-point learned correctness decisions.
- [ ] **Step 5: Implement promotion gate**: held-out exact frontier equality mandatory; expansion improvement mandatory; otherwise `enabled=false` with reason.
- [ ] **Step 6: Re-run tests twice** and compare serialized model/dataset manifests byte-for-byte.
- [ ] **Step 7: Commit** `Train bounded BOM ordering heuristic behind exact gate`.

### Task 5: Native exact subset kernel

**Files:**
- Create: `SPrime Search/decision-field/bom/fast/native_search.cpp`
- Create: `SPrime Search/decision-field/bom/fast/native.py`
- Create: `SPrime Search/decision-field/bom/fast/tests/test_native.py`

**Interfaces:**
- Produces: native executable JSON protocol and `run_native(index)` wrapper.

- [ ] **Step 1: Write failing test** compiling C++17 and comparing native accepted subset masks/counts with Python indexed search on deterministic <=16-part families.
- [ ] **Step 2: Run test**; expected missing source failure.
- [ ] **Step 3: Implement C++ kernel** for <=64 parts using `uint64_t` subset masks and capability/dependency bit checks; deterministic ascending-mask traversal for oracle sizes.
- [ ] **Step 4: Implement Python wrapper** with explicit timeout and exact JSON schema validation.
- [ ] **Step 5: Re-run native/Python equality tests** and commit `Add exact native BOM subset kernel`.

### Task 6: Hard benchmark and audit

**Files:**
- Create: `SPrime Search/decision-field/bom/fast/benchmark.py`
- Create: `SPrime Search/decision-field/bom/fast/audit.py`
- Create: `SPrime Search/decision-field/bom/fast/README.md`
- Create: `SPrime Search/decision-field/bom/fast/tests/test_audit.py`
- Create after verified run: `SPrime Search/decision-field/bom/fast/evidence/SUMMARY.json`
- Create after verified run: `SPrime Search/decision-field/bom/fast/evidence/TRAINING.json`
- Create after verified run: `SPrime Search/decision-field/bom/fast/evidence/VERIFICATION.json`

**Interfaces:**
- Benchmark tiers: <=16 exhaustive oracle; <=20 exhaustive/indexed comparison; 32/48/64 structured scale cases.

- [ ] **Step 1: Write failing audit test** demanding byte-identical scientific results across two runs and exact agreement for oracle tiers.
- [ ] **Step 2: Implement benchmark generator** with fused/split parts, dependency chains, port conflicts, invalid cheap parts, and 5–8 cost dimensions.
- [ ] **Step 3: Implement audit** recording candidate counts, expansions, proof-safe prunes, question scores, training split/metrics, model promotion state, native/Python agreement, runtimes, source hashes, and claim ceiling.
- [ ] **Step 4: Execute audit twice**; require identical `SUMMARY.json` and `TRAINING.json` scientific content.
- [ ] **Step 5: Run full `bom/fast/tests` and existing `bom/tests`**; require zero failures.
- [ ] **Step 6: Commit code and verified evidence** `Audit fast BOM execution and trained questions`.

### Task 7: Exact-head CI and reviewable PR

**Files:**
- Modify: `.github/workflows/sprime-decision-field-check.yml`

- [ ] **Step 1: Append CI gate** that runs existing decision-field/BOM checks first, then all fast tests, two fast audits, byte comparison, committed evidence comparison, native/Python equality assertions, and training promotion invariants.
- [ ] **Step 2: Push branch and inspect exact-head workflow**; do not promote on partial status.
- [ ] **Step 3: If current `main` moved, rebuild a clean successor commit on the new main carrying only Pass 09 files/CI changes.
- [ ] **Step 4: Open reviewable PR** with bounded claims and exact benchmark/training evidence.
- [ ] **Step 5: Merge only after exact-head CI is green and branch is 0 behind current main.**
