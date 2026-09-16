# GSFL v0.1 Operator Projection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the completed GSFL v0.1 operation set into a reusable, audited Decision Field operator profile without mutating either source authority.

**Architecture:** Keep the existing canonical six-operator loop unchanged. Add a separate GSFL profile registry and reference executor; delegate overlapping canonical operations and execute only GSFL-native operations locally. Register the profile from the canonical registry as a removable successor profile.

**Tech Stack:** Python 3.10+ standard library; JSON; Markdown; unittest; GitHub Actions.

**Spec:** `Decision Field Operator Lab/docs/superpowers/specs/2026-09-16-gsfl-operator-projection-design.md`

## Global Constraints

- GSFL v0.1 source lifecycle remains `COMPLETE_BOUNDED_V0_1`.
- Source completion merge is pinned to `cf9d5a35a39b1a7b92f30e24b2789f659e913f04`.
- Canonical Decision Field loop remains exactly `DISTINGUISH, GROUND, TRANSPORT, ATTACK, REPAIR, SELECT`.
- `DISTINGUISH`, `GROUND`, `REPAIR`, and `SELECT` delegate to canonical operators.
- Native operators never mutate their input envelope.
- `FIT` selects only already-admitted candidates.
- `PROJECTION != SOURCE_MUTATION` and `OPERATOR_EXECUTION != AUTHORITY_TRANSFER`.

---

### Task 1: Operator profile registry

**Files:**
- Create: `Decision Field Operator Lab/gsfl-operator-profile.json`
- Test: `Decision Field Operator Lab/test_gsfl_operator_projection.py`

**Interfaces:**
- Produces 23 unique operator records with typed effects/output and shared Skill/Agent paths.

- [ ] Write failing tests for exact operator order, uniqueness, source lifecycle, and canonical delegation.
- [ ] Run `python -m unittest -v test_gsfl_operator_projection.py` and confirm failure before profile/module exists.
- [ ] Add the profile registry with 19 `GSFL_NATIVE` and 4 `DELEGATE_CANONICAL` records.
- [ ] Rerun the targeted tests.

### Task 2: Executable projection

**Files:**
- Create: `Decision Field Operator Lab/gsfl_operator_projection.py`
- Modify: `Decision Field Operator Lab/test_gsfl_operator_projection.py`

**Interfaces:**
- `load_profile(path) -> dict`
- `validate_profile(profile) -> dict`
- `apply_operator(operator_id, envelope, **params) -> dict`
- `canonical_json(obj) -> str`

- [ ] Add failing tests for input immutability, rotation preservation, admission-before-fit, attributed tool/cooperation traces, proverb provenance, and confound detection.
- [ ] Implement the smallest deterministic handlers needed for all GSFL-native operators.
- [ ] Ensure canonical overlaps return explicit handoff packets.
- [ ] Run the complete projection test file.

### Task 3: Shared Skill/Agent backing

**Files:**
- Create: `Decision Field Operator Lab/skills/operators/gsfl-profile/SKILL.md`
- Create: `Decision Field Operator Lab/agents/operators/gsfl-profile/AGENT.md`

**Interfaces:**
- All 23 operator records point to these shared profile runner contracts while retaining distinct per-operator effects and outputs.

- [ ] Add/retain tests that each profile record carries Skill, Agent, and output fields.
- [ ] Document canonical delegation and source-baseline immutability.
- [ ] Run projection tests.

### Task 4: Deterministic audit

**Files:**
- Create: `Decision Field Operator Lab/run_gsfl_operator_audit.py`
- Create: `Decision Field Operator Lab/evidence/GSFL_OPERATOR_RESULTS.json`

**Interfaces:**
- `build_summary() -> dict`
- CLI `--write` and `--check`.

- [ ] Exercise a bounded chain through observation, rotation, preservation, tool trace, cooperation, verification, fit, confound audit, corollary derivation, and canonical repair handoff.
- [ ] Freeze counts at 23 total / 19 native / 4 delegated.
- [ ] Write deterministic evidence and verify with `--check`.

### Task 5: Registry and documentation integration

**Files:**
- Modify: `Decision Field Operator Lab/operator-skill-registry.json`
- Modify: `Decision Field Operator Lab/README.md`
- Create: `Decision Field Operator Lab/GSFL_OPERATOR_PROJECTION.md`
- Modify: `.github/workflows/operator-field-check.yml`

**Interfaces:**
- Canonical registry gains only a removable `profiles` pointer; canonical loop/operators remain unchanged.

- [ ] Add the GSFL profile pointer to the canonical registry.
- [ ] Document the projection and evidence boundaries.
- [ ] Extend CI with `run_gsfl_operator_audit.py --check`.
- [ ] Run all Operator Lab tests and both audits.

### Task 6: Successor propagation

**Files:**
- Create: `Generalized Semantic Fitting Language/OPERATOR_PROJECTION_SUCCESSOR.md`
- Update reference/index surfaces only after the implementation merges.

**Interfaces:**
- Preserve `COMPLETE_BOUNDED_V0_1` as source baseline; record the operator projection as a successor relation.

- [ ] Add the GSFL-side successor pointer without editing the completed source contract.
- [ ] Merge only after exact-head CI passes.
- [ ] Propagate the merged projection identity to Conscience64/redogit/Library as reference/navigation records, not evidence transfer.
