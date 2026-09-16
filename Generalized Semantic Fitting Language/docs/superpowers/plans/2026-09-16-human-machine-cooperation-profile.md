# GSFL v0.1 Human–Machine Cooperation Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an additive GSFL v0.1 cooperation profile that foregrounds human understanding, machine-learning claim boundaries, partner cooperation, and tool provenance while preserving GSFL v0 behavior.

**Architecture:** Keep `gsfl.py` as the v0 semantic kernel. Add `gsfl_coop.py` as a successor profile that parses cooperation metadata, audits vocabulary dominance, validates learning/understanding boundaries, delegates semantic fitting to v0, and emits confound findings. Publish a v0.1 example, corollary/confound ledger, and deterministic audit without rewriting v0 evidence.

**Tech Stack:** Python 3.10+ standard library; `unittest`; JSON; Markdown; GitHub Actions.

**Spec:** `Generalized Semantic Fitting Language/docs/superpowers/specs/2026-09-16-human-machine-cooperation-profile-design.md`

## Global Constraints

- GSFL v0 behavior and evidence remain intact.
- More than 50% of v0.1 reserved/domain vocabulary must be classified in HUMAN, MACHINE_LEARNING, UNDERSTANDING, COOPERATION, PARTNER, or TOOL families.
- `MACHINE_OUTPUT != MACHINE_LEARNING_EVIDENCE`.
- `HUMAN_APPROVAL != HUMAN_UNDERSTANDING` and `HUMAN_APPROVAL != GROUND_TRUTH`.
- `TOOL_USE != TOOL_AUTHORITY`.
- Cooperation must preserve distinct human and machine partner identities.
- No third-party Python packages.
- All new evidence is bounded to declared fixtures and software contracts.

---

### Task 1: Cooperation domain model and vocabulary audit

**Files:**
- Create: `Generalized Semantic Fitting Language/gsfl_coop.py`
- Create: `Generalized Semantic Fitting Language/test_gsfl_coop.py`

**Interfaces:**
- Produces `Partner`, `ToolUse`, `CooperationStep`, `LearningClaim`, `CooperationContext` dataclasses.
- Produces `vocabulary_audit() -> dict[str, object]`.
- Produces fixed `RESERVED_VOCABULARY` and `VOCABULARY_FAMILIES` registries.

- [ ] **Step 1: Write failing vocabulary and partner tests**

```python
def test_vocabulary_majority_is_human_machine_cooperation():
    audit = coop.vocabulary_audit()
    assert audit["ratio"] > 0.5
    assert audit["passes"] is True


def test_partner_ids_must_be_distinct():
    with self.assertRaisesRegex(ValueError, "distinct"):
        coop.CooperationContext(
            human_partner=coop.Partner("p", "HUMAN", "intent-owner"),
            machine_partner=coop.Partner("p", "MACHINE", "proposal-partner"),
            tools=(), steps=(), understanding_goal="explain", understanding_evidence="NONE",
            learning_claim=coop.LearningClaim("NO_LEARNING_CLAIM", "")
        )
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest -v test_gsfl_coop.py`
Expected: import/module or missing-interface failures.

- [ ] **Step 3: Implement minimal registries/dataclasses/validation**

Implement the interfaces exactly above, including allowed partner kinds and allowed learning states.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python -m unittest -v test_gsfl_coop.py`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat(gsfl): add v0.1 cooperation domain model`

---

### Task 2: Cooperation parser and v0 semantic delegation

**Files:**
- Modify: `Generalized Semantic Fitting Language/gsfl_coop.py`
- Modify: `Generalized Semantic Fitting Language/test_gsfl_coop.py`

**Interfaces:**
- Produces `parse_cooperation(program: str) -> tuple[gsfl.SemanticObject, list[gsfl.Candidate], CooperationContext]`.
- Produces `execute_cooperation(program: str) -> dict[str, object]`.
- Delegates candidate classification and fit to `gsfl.fit`.

- [ ] **Step 1: Write failing parser/delegation tests**

Test a `GSFL 0.1` program containing HUMAN, MACHINE, TOOL, UNDERSTANDING_GOAL, UNDERSTANDING_EVIDENCE, MACHINE_LEARNING, COOPERATE, and ordinary v0 candidate blocks. Assert partner/tool trace fields and selected semantic candidate.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest -v test_gsfl_coop.GSFLCooperationTests.test_cooperation_program_delegates_semantic_fit`
Expected: missing parser/executor failure.

- [ ] **Step 3: Implement minimal parser**

Validate declared partners/tools, fail on unknown actors/tools, convert candidate portion into a temporary `GSFL 0` program, and delegate to v0 parse/fit semantics.

- [ ] **Step 4: Verify GREEN and regression**

Run:
`python -m unittest -v test_gsfl_coop.py`
`python -m unittest -v test_gsfl.py`
Expected: all pass.

- [ ] **Step 5: Commit**

Commit message: `feat(gsfl): execute human-machine cooperation traces`

---

### Task 3: Confound detection and bounded corollaries

**Files:**
- Modify: `Generalized Semantic Fitting Language/gsfl_coop.py`
- Modify: `Generalized Semantic Fitting Language/test_gsfl_coop.py`
- Create: `Generalized Semantic Fitting Language/COROLLARIES_AND_CONFOUNDS.md`
- Create: `Generalized Semantic Fitting Language/confounds.json`

**Interfaces:**
- Produces `detect_confounds(context: CooperationContext, semantic_result: dict[str, object]) -> list[dict[str, str]]`.
- Publishes seven bounded corollaries from the approved design.
- Publishes at least fourteen confounds with trigger/control/boundary fields.

- [ ] **Step 1: Write failing confound tests**

Assert that approval-only understanding evidence triggers `APPROVAL_AS_UNDERSTANDING`, in-context adaptation never reports a weight update, unknown/correlated tool independence claims are rejected or warned, and lexical majority is labeled as lexical-only evidence.

- [ ] **Step 2: Verify RED**

Run targeted confound tests and observe expected missing-function/behavior failures.

- [ ] **Step 3: Implement detection rules and ledgers**

Implement deterministic findings ordered by confound ID. Keep social/epistemic confounds as warnings rather than pretending they are mechanically resolved.

- [ ] **Step 4: Verify GREEN**

Run all v0.1 and v0 tests.

- [ ] **Step 5: Commit**

Commit message: `feat(gsfl): add corollary and confound discipline`

---

### Task 4: Cooperative N-observer fixture and deterministic audit

**Files:**
- Create: `Generalized Semantic Fitting Language/examples/n_observer_human_machine_cooperation.gsfl`
- Create: `Generalized Semantic Fitting Language/run_cooperation_audit.py`
- Create: `Generalized Semantic Fitting Language/evidence/COOPERATION_RESULTS.json`
- Modify: `Generalized Semantic Fitting Language/test_gsfl_coop.py`

**Interfaces:**
- The example traces human intent, machine proposal, Python/Windows-Magnification-API documentation tools, partner review, and selected surface.
- The audit proves vocabulary-majority, trace attribution, tool provenance, confound emission, v0 semantic admission, and deterministic byte-identical output.

- [ ] **Step 1: Write failing audit test**

Test `run_cooperation_audit.py --check` before the audit/evidence exists.

- [ ] **Step 2: Verify RED**

Expected: missing script/evidence failure.

- [ ] **Step 3: Implement example + audit and freeze evidence**

Generate canonical JSON twice and require byte identity. Record exact admitted candidate, vocabulary ratio, partner IDs, tool IDs, learning state, understanding evidence, corollary IDs, and confound IDs.

- [ ] **Step 4: Verify GREEN**

Run v0.1 tests, v0 tests, `run_audit.py --check`, and `run_cooperation_audit.py --check`.

- [ ] **Step 5: Commit**

Commit message: `test(gsfl): freeze v0.1 cooperation evidence`

---

### Task 5: Documentation, routing, and CI

**Files:**
- Modify: `Generalized Semantic Fitting Language/README.md`
- Create: `Generalized Semantic Fitting Language/COOPERATION_PROFILE.md`
- Modify: `.github/workflows/gsfl-check.yml`
- Later successor updates: Conscience64 bridge, redogit federation record, Library packet.

**Interfaces:**
- README keeps v0 history and clearly points to v0.1 successor.
- CI runs both v0 and v0.1 tests/audits.

- [ ] **Step 1: Update docs with majority-vocabulary rule and evidence ceilings**

Use the exact boundaries from the design spec.

- [ ] **Step 2: Update exact-head CI**

Run `test_*.py`, `run_audit.py --check`, and `run_cooperation_audit.py --check`.

- [ ] **Step 3: Run complete local verification twice**

Expected: identical successful results and byte-identical audit outputs.

- [ ] **Step 4: Review diff for v0 mutation**

Require that `gsfl.py` and `evidence/RESULTS.json` are unchanged unless a verified backwards-compatible defect is found. No such change is planned.

- [ ] **Step 5: Open review PR and require exact-head CI before merge**

After merge, publish reference/navigation successor records and retain a Library v0.1 packet.
