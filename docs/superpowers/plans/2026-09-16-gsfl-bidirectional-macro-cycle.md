# GSFL Bidirectional Macro-Cycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved `SEEK → QUESTION → REFRAME → BUILD → RETURN_INWARD` macro cycle as a deterministic successor composition over the existing GSFL operator projection.

**Architecture:** Add a separate macro registry and executor beside the existing GSFL operator projection. Macros expand to existing operators; they are never inserted into the primitive operator registry. Add unit tests, a frozen audit, CI integration, a GSFL successor pointer, and cross-project lineage records after merge.

**Tech Stack:** Python 3.10+ standard library, JSON registries, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-16-gsfl-bidirectional-macro-cycle-design.md`

## Global Constraints

- Preserve `COMPLETE_BOUNDED_V0_1` as a frozen predecessor baseline.
- Preserve the Decision Field canonical loop exactly as `DISTINGUISH, GROUND, TRANSPORT, ATTACK, REPAIR, SELECT`.
- Macros are compositions, not primitive operators.
- Macro execution must deep-copy the input envelope.
- Keep underlying operator trace and macro trace distinct.
- Preserve `OUTWARD_EXPLORATION != VALIDATION`, `INWARD_COHERENCE != PROOF`, and `BUILD != TRUTH`.
- No dependency beyond the Python standard library.

---

### Task 1: Macro registry and failing contract tests

**Files:**
- Create: `Decision Field Operator Lab/gsfl-bidirectional-macro-profile.json`
- Create: `Decision Field Operator Lab/test_gsfl_bidirectional_cycle.py`

**Interfaces:**
- Consumes: existing `gsfl-operator-profile.json` and `gsfl_operator_projection.apply_operator`.
- Produces: macro IDs `SEEK`, `QUESTION`, `REFRAME`, `BUILD`, `RETURN_INWARD` and their approved expansions.

- [ ] Write tests asserting the five macro IDs and exact operator expansions.
- [ ] Write a test asserting macro IDs do not appear in the primitive GSFL operator registry.
- [ ] Write a test asserting the Decision Field canonical loop remains unchanged.
- [ ] Run the tests and confirm they fail because the macro profile/executor does not exist yet.

### Task 2: Macro executor

**Files:**
- Create: `Decision Field Operator Lab/gsfl_bidirectional_cycle.py`
- Modify: `Decision Field Operator Lab/test_gsfl_bidirectional_cycle.py`

**Interfaces:**
- `load_macro_profile(path=DEFAULT_MACRO_PROFILE) -> dict`
- `validate_macro_profile(profile, operator_profile=None) -> dict`
- `apply_macro(macro_id, envelope, *, macro_params=None, profile_path=..., operator_profile_path=...) -> dict`
- `run_bidirectional_cycle(envelope, *, cycle_params, profile_path=..., operator_profile_path=...) -> dict`

- [ ] Implement fail-closed macro-profile validation.
- [ ] Implement `apply_macro` using `deepcopy` and sequential calls to `gsfl_operator_projection.apply_operator`.
- [ ] Add `macro_trace` entries with macro ID, phase, and expansion.
- [ ] Implement `run_bidirectional_cycle` in approved macro order.
- [ ] Test input immutability, outward/inward phase separation, canonical delegation, source-meaning preservation, and admitted-only fit behavior.
- [ ] Run the full macro test module and confirm green.

### Task 3: Frozen bidirectional audit

**Files:**
- Create: `Decision Field Operator Lab/run_gsfl_bidirectional_audit.py`
- Create: `Decision Field Operator Lab/evidence/GSFL_BIDIRECTIONAL_RESULTS.json`

**Interfaces:**
- `build_summary() -> dict`
- CLI `--write`, `--check`, optional `--out`.

- [ ] Build a deterministic fixture with source meaning, admitted/rejected fit candidates, observations, tool provenance, confound claim, reconstruction, and teach-back evidence.
- [ ] Run the cycle twice and require byte-identical canonical JSON.
- [ ] Assert five macros execute in the approved order.
- [ ] Assert source input and source meaning are preserved.
- [ ] Assert outward and inward traces are both present.
- [ ] Assert fit selects only an admitted candidate.
- [ ] Assert confound and corollary findings survive the inward return.
- [ ] Freeze the summary in `GSFL_BIDIRECTIONAL_RESULTS.json`.

### Task 4: Registry/docs/CI integration

**Files:**
- Modify: `Decision Field Operator Lab/operator-skill-registry.json`
- Create: `Decision Field Operator Lab/GSFL_BIDIRECTIONAL_MACRO_CYCLE.md`
- Modify: `Decision Field Operator Lab/README.md`
- Modify: `.github/workflows/operator-field-check.yml`
- Create: `Generalized Semantic Fitting Language/BIDIRECTIONAL_OPERATOR_SUCCESSOR.md`

**Interfaces:**
- Canonical registry gets a removable `macro_profiles` pointer only.
- CI runs original Operator Lab audit, GSFL operator projection audit, and bidirectional macro audit.

- [ ] Add the macro-profile pointer without changing canonical operator order.
- [ ] Document the outward/inward composition and evidence ceiling.
- [ ] Add a GSFL successor pointer that explicitly preserves `COMPLETE_BOUNDED_V0_1`.
- [ ] Extend CI with `run_gsfl_bidirectional_audit.py --check`.
- [ ] Run exact-head GitHub Actions and require all relevant workflows green.

### Task 5: Merge and external propagation

**Files/Surfaces:**
- Other-Projects PR and merge.
- Conscience64 reference-only successor bridge.
- redogit federation successor record.
- `/Library Consolidation/GSFL/2026-09-16/v0.1/bidirectional-macro-cycle/` recovery packet.

- [ ] Open a non-draft PR.
- [ ] Merge only after exact-head CI is green.
- [ ] Record the merged implementation SHA in Conscience64 without runtime/authority transfer.
- [ ] Record the successor lineage in redogit without centralizing authority.
- [ ] Archive registry, executor, tests, audit, frozen evidence, spec/plan, and final lineage in the Library.
- [ ] Confirm zero open rollout PRs for this successor.
