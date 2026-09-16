# Contextual Multi-Carrier Reasoning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic successor layer that resolves context-dependent word/phrase roles, projects one semantic object through symbolic/analytical/computational/analogical carriers, compares invariants and deltas, performs BBF-style analogy reconstruction, audits confounds, and gates successor promotion without treating agreement as truth or independence.

**Architecture:** Add a separate `GSFL_CONTEXTUAL_MULTICARRIER_REASONING` profile and Python executor inside Decision Field Operator Lab. It consumes the existing GSFL operator projection and bidirectional macro lineage but does not mutate either. The implementation is deterministic, standard-library only, with frozen evidence and CI integration.

**Tech Stack:** Python 3.10+ standard library, JSON profiles/evidence, unittest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-16-contextual-multicarrier-reasoning-design.md`

## Global Constraints

- Preserve `COMPLETE_BOUNDED_V0_1` and all successor lineage.
- Preserve the canonical Decision Field six-operator loop unchanged.
- `WORD != FIXED_ROLE`.
- `CARRIER_AGREEMENT != INDEPENDENT_VERIFICATION`.
- `ANALOGY != EVIDENCE_TRANSFER`.
- `COMPUTATIONAL_WITNESS != GENERAL_PROOF`.
- `ANALYTICAL_COHERENCE != EMPIRICAL_VALIDATION`.
- `SYMBOLIC_COMPRESSION != TRUTH`.
- Standard library only.
- Every output must retain provenance and a claim ceiling.

---

### Task 1: Contextual role-resolution contract

**Files:**
- Create: `Decision Field Operator Lab/contextual-multicarrier-profile.json`
- Test: `Decision Field Operator Lab/test_contextual_multicarrier.py`

**Interfaces:**
- Consumes: explicit occurrence text and context records.
- Produces: `resolve_roles(occurrence: str, context: dict) -> dict` with interpreter-local multi-role binding.

- [ ] **Step 1: Write failing tests** for deterministic resolution, context-dependent role changes, simultaneous multiple roles, and human/machine separation.
- [ ] **Step 2: Run** `python3 -m unittest "Decision Field Operator Lab/test_contextual_multicarrier.py" -v` and confirm failures are due to missing `contextual_multicarrier` module.
- [ ] **Step 3: Implement minimal role-resolution API** using explicit role hints and bounded deterministic lexical/context cues; support multiple selected roles and unresolved candidates.
- [ ] **Step 4: Re-run focused tests** and confirm green.

### Task 2: Four reasoning carriers

**Files:**
- Create/modify: `Decision Field Operator Lab/contextual_multicarrier.py`
- Test: `Decision Field Operator Lab/test_contextual_multicarrier.py`

**Interfaces:**
- Produces: `project_carriers(semantic_object: dict, carrier_inputs: dict) -> dict[str, dict]`.
- Carrier IDs: `SYMBOLIC`, `ANALYTICAL`, `COMPUTATIONAL`, `ANALOGICAL`.

- [ ] **Step 1: Add failing tests** requiring all four carriers, provenance/claim ceilings, invariant preservation, and explicit losses/introductions.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: Implement carrier records** without importing truth/authority from representation type.
- [ ] **Step 4: Verify GREEN**.

### Task 3: Cross-carrier invariant and delta comparison

**Files:**
- Modify: `Decision Field Operator Lab/contextual_multicarrier.py`
- Test: `Decision Field Operator Lab/test_contextual_multicarrier.py`

**Interfaces:**
- Produces: `compare_carriers(source: dict, carriers: dict, independence_contract: dict | None = None) -> dict`.

- [ ] **Step 1: Add failing tests** for shared invariants, injected loss, injected introduction, unresolved deltas, agreement count, and default `NOT_ESTABLISHED` independence.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: Implement comparison** using exact set/dict comparison only.
- [ ] **Step 4: Verify GREEN**.

### Task 4: BBF-style analogy reconstruction

**Files:**
- Modify: `Decision Field Operator Lab/contextual_multicarrier.py`
- Test: `Decision Field Operator Lab/test_contextual_multicarrier.py`

**Interfaces:**
- Produces: `bbf_analogy_check(source_invariants: dict, mapping: dict, reconstructed: dict) -> dict`.

- [ ] **Step 1: Add failing tests** for preserved round trip, loss, introduced invariant, and `evidence_transfer=false`.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: Implement Fold → Map → Unfold → Compare record** with `PRESERVED|LOSS|INTRODUCED|UNRESOLVED` statuses.
- [ ] **Step 4: Verify GREEN**.

### Task 5: Confound audit and promotion gate

**Files:**
- Modify: `Decision Field Operator Lab/contextual_multicarrier.py`
- Test: `Decision Field Operator Lab/test_contextual_multicarrier.py`

**Interfaces:**
- Produces: `audit_multicarrier_confounds(state: dict) -> list[dict]`.
- Produces: `gate_disposition(candidate: dict, comparison: dict, confounds: list[dict]) -> dict`.

- [ ] **Step 1: Add failing tests** for static-role fallacy, interpreter collapse, agreement-as-truth, agreement-as-independence, analogy-as-evidence-transfer, computation-as-general-proof, analysis-as-validation, symbolic-compression-as-truth, and fit-before-admission.
- [ ] **Step 2: Add failing gate tests** showing agreement-only is rejected/reopened and a verified admitted bounded successor can be promoted.
- [ ] **Step 3: Verify RED**.
- [ ] **Step 4: Implement minimal confound audit and gate** with outcomes `PRESERVE|PROMOTE_SUCCESSOR|REOPEN|REJECT|UNRESOLVED`.
- [ ] **Step 5: Verify GREEN**.

### Task 6: Deterministic audit and frozen evidence

**Files:**
- Create: `Decision Field Operator Lab/run_contextual_multicarrier_audit.py`
- Create: `Decision Field Operator Lab/evidence/CONTEXTUAL_MULTICARRIER_RESULTS.json`

**Interfaces:**
- Audit command: `python3 "Decision Field Operator Lab/run_contextual_multicarrier_audit.py" --check`.

- [ ] **Step 1: Write audit fixture** covering positive and negative controls from the design.
- [ ] **Step 2: Generate canonical JSON and SHA-256** from fresh execution.
- [ ] **Step 3: Freeze concise evidence** and verify `--check` reproduces it byte-for-byte.

### Task 7: Registry, documentation, and CI integration

**Files:**
- Modify: `Decision Field Operator Lab/operator-skill-registry.json`
- Modify: `Decision Field Operator Lab/README.md`
- Modify: `.github/workflows/operator-field-check.yml`
- Create: `Decision Field Operator Lab/CONTEXTUAL_MULTICARRIER_REASONING.md`
- Create: `Generalized Semantic Fitting Language/CONTEXTUAL_MULTICARRIER_SUCCESSOR.md`
- Modify: `Decision Field Operator Lab/test_operator_skills.py`

**Interfaces:**
- Add successor profile reference only; do not modify canonical operator ordering.

- [ ] **Step 1: Add regression test** ensuring canonical loop is unchanged and the new profile is successor-only.
- [ ] **Step 2: Update registry/docs** with explicit boundaries and run commands.
- [ ] **Step 3: Add CI step** for `run_contextual_multicarrier_audit.py --check`.
- [ ] **Step 4: Run full local verification**: all Operator Lab tests plus original, GSFL operator, bidirectional macro, and contextual multicarrier audits.
- [ ] **Step 5: Open non-draft PR** and require exact-head Operator Lab + GSFL workflows to pass before merge.

### Task 8: Post-merge propagation and recovery

**Files/Surfaces:**
- Conscience64 reference-only GSFL bridge successor.
- redogit forward-only federation successor record.
- Library folder `/Library Consolidation/GSFL/2026-09-16/v0.1/contextual-multicarrier/`.

- [ ] **Step 1: Merge Other-Projects only after exact-head verification**.
- [ ] **Step 2: Add Conscience64 reference-only record** with `runtime_effect=NONE` and `authority_effect=NONE`; merge non-draft PR.
- [ ] **Step 3: Add redogit forward-only federation record**; merge non-draft PR.
- [ ] **Step 4: Seal Library packet** with implementation, tests, audit, spec, plan, evidence, merged status, and public lineage.
- [ ] **Step 5: Fresh readback** from all default branches and verify zero open rollout PRs.
