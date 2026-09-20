# RMAPL Ω Reference Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bounded standard-library RMAPL v0 reference runtime that projects native Decision Field/S'1-family records into a strict Ω envelope, executes conditional repair/fitting decisions with explicit loss/evidence/cycle accounting, and emits inspectable deterministic evidence without changing native domain authority.

**Architecture:** Implement the common runtime entirely under `Decision Field Operator Lab/` in Python 3.10+ standard library. Native projects remain authoritative; adapters consume native Python objects or JSON-like records and preserve non-generalized content in `domainRemainder`. The runtime has four layers: strict Ω normalization, native adapters, a small declarative RMAPL v0 parser/IR, and a bounded conditional repair/fitting engine.

**Tech Stack:** Python 3.10+ standard library, `unittest`, JSON Schema Draft 2020-12 as a published interchange contract, existing GitHub Actions `Decision Field Operator Lab` workflow.

**Spec:** `docs/superpowers/specs/2026-09-20-rmapl-omega-conditional-repair-design.md`

## Global Constraints

- Canonical executable home is `redogit/Other-Projects-`.
- `redogit/conscience64` is cross-reference/adapters only; no duplicate canonical runtime.
- RMAPL v0 is a separately versioned profile; `RMAPL_PROFILE != RMAL_CORE_FRONTEND`.
- Python implementation uses the standard library only.
- Native schemas such as `s1-experience/v0`, `s1-carrier/v1`, GSFL, image-surface, and Hodge bridge remain authoritative and are not renamed.
- `OMEGA_VIEW != NATIVE_OBJECT`, `CONNECTED != MERGED`, `METHOD_TRANSFER != EVIDENCE_TRANSFER`.
- Evidence is claim-local and typed; representation changes may not manufacture an evidence class.
- Every lossy transform declares induced equivalence/loss and retains native lineage.
- Every adapter preserves an explicit `domainRemainder`.
- Maximal repair means maximal consequential coverage inside declared bounds, never global completeness.
- Repeated-state cycles terminate as `UNRESOLVED`, not success.
- Public fixtures are technical/synthetic and contain no private personal context.
- No implementation task modifies RMALC.
- TDD is mandatory: every production behavior is preceded by a test observed failing for the intended reason.

## Review Focus

- **Mutable/non-JSON-native values:** Ω normalization must fail closed on sets, non-finite floats, callables, and unsupported object types rather than silently stringify them.
- **Hash/equality aliasing:** deterministic Ω identity must include native type, source references, state/path, evidence ceiling, resource bounds, and domain remainder so two consequentially different records cannot collide by omitted fields.
- **Evidence namespace confusion:** a claim requiring `scientific-validation` must remain blocked when only `software-verification` is present even if a mapper/candidate reports success.
- **Repair side effects:** registered repair operators must receive and return normalized copies; an operator that mutates its input object must be detected by before/after canonical comparison and rejected.
- **Cycle/resource interaction:** a repeated state reached exactly at a resource boundary must report both cycle and bound metadata deterministically, with stop reason chosen by the declared precedence.

---

### Task 1: Strict Ω envelope, inspection records, and native extraction fixtures

**Files:**
- Create: `Decision Field Operator Lab/omega.py`
- Create: `Decision Field Operator Lab/omega.schema.json`
- Create: `Decision Field Operator Lab/test_omega.py`
- Create: `Decision Field Operator Lab/fixtures/omega_decision_field_native.json`
- Create: `Decision Field Operator Lab/fixtures/omega_s1_native.json`

**Interfaces:**
- Consumes: existing `DecisionField` object shape and native JSON-like records.
- Produces:
  - `OMEGA_SCHEMA = "rmapl-omega/v0"`
  - `canonical_json(value) -> str`
  - `normalize_json_value(value, label="value") -> JSONValue`
  - `make_omega(...fields...) -> dict`
  - `validate_omega(record: dict) -> dict`
  - `make_inspection_record(...) -> dict`
  - `round_trip_report(original, reconstructed) -> dict`

- [ ] **Step 1: Write failing Ω tests**

Create tests that require:
```python
class OmegaTests(unittest.TestCase):
    def test_strict_record_is_deterministic_and_closed(self):
        omega = make_omega(
            native_type="decision-field/v1",
            native_identity="fixture:df:1",
            source_refs=("fixture:df:1",),
            state={"possibilities": [0, 1]},
            path=(),
            frame={"obligation": "select-1"},
            invariants=("goal-preserved",),
            observations=(),
            residuals=({"kind": "unresolved", "detail": "0 remains"},),
            decision_field={"goal": 1},
            provenance=({"kind": "fixture", "ref": "omega_decision_field_native.json"},),
            evidence=({"kind": "software-verification", "detail": "fixture", "claimCeiling": "BOUNDED"},),
            claim_ceiling=("SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",),
            resource_bounds={"maxCandidates": 8},
            domain_remainder={"nativeOnly": {"relations": []}},
        )
        self.assertEqual(validate_omega(omega), omega)
        self.assertEqual(omega["schema"], "rmapl-omega/v0")
        self.assertRegex(omega["id"], r"^[0-9a-f]{64}$")
        self.assertEqual(make_omega(**omega["construction"])["id"], omega["id"])

    def test_unknown_authority_field_fails_closed(self):
        omega = fixture_omega()
        with self.assertRaisesRegex(ValueError, "unsupported omega field"):
            validate_omega({**omega, "truthAuthority": "invented"})

    def test_non_json_and_non_finite_values_fail_closed(self):
        with self.assertRaises(TypeError):
            canonical_json({"x": {1, 2}})
        with self.assertRaises(ValueError):
            canonical_json({"x": float("nan")})

    def test_round_trip_report_separates_preserved_lost_introduced_unresolved(self):
        report = round_trip_report(
            {"a": 1, "b": 2, "unknown": None},
            {"a": 1, "b": 3, "c": 4, "unknown": None},
        )
        self.assertEqual(report["preserved"], ["a", "unknown"])
        self.assertEqual(report["lost"], [])
        self.assertEqual(report["introduced"], ["c"])
        self.assertEqual(report["changed"], ["b"])

    def test_inspection_record_exposes_failed_and_skipped_gates(self):
        record = make_inspection_record(
            input_refs=["fixture:1"],
            native_contract="decision-field/v1",
            operator="extract",
            operator_version="v0",
            condition="always",
            trigger="adapter",
            preconditions=["native-valid"],
            obligation="project",
            expected="omega",
            actual="omega",
            residual_before=[],
            residual_after=[],
            preserved=["identity"],
            mutated=[],
            lost=[],
            introduced=[],
            reconstruction={"status": "exact"},
            knowledge_decay={"loss": [], "introduction": []},
            evidence=[],
            claim_ceiling=["BOUNDED"],
            counterprobe={"status": "skipped", "reason": "not-applicable"},
            provenance=[],
            resource_bounds={"maxCandidates": 1},
            resource_usage={"executed": 1},
            unresolved=[],
            next_decision=None,
            domain_remainder={},
            gates=[{"name": "native-valid", "status": "passed"}, {"name": "at-validation", "status": "skipped"}],
        )
        self.assertEqual(record["gates"][1]["status"], "skipped")
```

- [ ] **Step 2: Run tests to verify RED**

Run:
```sh
python3 -m unittest "Decision Field Operator Lab/test_omega.py" -v
```
Expected: import/module failure because `omega.py` does not exist.

- [ ] **Step 3: Implement minimal strict Ω core**

Implement canonical recursive JSON normalization; reject non-finite numbers and unsupported object types; sort object keys; normalize tuples to arrays; deep-copy by canonical round trip. `make_omega` constructs a canonical payload, computes SHA-256 over the payload without `id`, adds `id`, and stores a `construction` object containing the exact arguments necessary to rebuild the record. `validate_omega` accepts exactly:
```python
OMEGA_KEYS = {
    "schema", "id", "nativeType", "nativeIdentity", "sourceRefs", "state",
    "path", "frame", "invariants", "observations", "residuals",
    "decisionField", "provenance", "evidence", "claimCeiling",
    "resourceBounds", "domainRemainder", "construction"
}
```
and recomputes canonical identity.

Publish `omega.schema.json` with Draft 2020-12, those required fields, and `unevaluatedProperties: false`.

- [ ] **Step 4: Add synthetic native fixtures**

`omega_decision_field_native.json` contains one bounded Decision Field-like record with possibilities `[0,1,2]`, goal `1`, one relation, one unresolved value, and software-verification evidence.

`omega_s1_native.json` contains one `s1-experience/v0` record with:
```json
{
  "schema": "s1-experience/v0",
  "id": "fixture-s1-native-1",
  "operatorVersion": "S'1-Ops v0",
  "initialState": "fixture",
  "mirrorId": "mirror:fixture",
  "shell": "comparison",
  "actions": [{"plane":"xw","degrees":1}],
  "observer": {"yaw":0,"pitch":0,"roll":0,"wPerspective":0.35},
  "provenance": {"source":"rmapl-omega-fixture"}
}
```
plus a `nativeRemainder` field carrying omitted S'1-only fixture metadata.

- [ ] **Step 5: Run Task 1 tests GREEN**

Run:
```sh
python3 -m unittest "Decision Field Operator Lab/test_omega.py" -v
```
Expected: all Task 1 tests pass.

- [ ] **Step 6: Commit**

```sh
git add "Decision Field Operator Lab/omega.py" "Decision Field Operator Lab/omega.schema.json" "Decision Field Operator Lab/test_omega.py" "Decision Field Operator Lab/fixtures"
git commit -m "feat: add strict RMAPL omega envelope"
```

---

### Task 2: Decision Field and S'1 native adapters with explicit remainder

**Files:**
- Create: `Decision Field Operator Lab/omega_adapters.py`
- Create: `Decision Field Operator Lab/test_omega_adapters.py`
- Modify: `Decision Field Operator Lab/omega.py`

**Interfaces:**
- Consumes: `DecisionField`, validated Ω functions, S'1 JSON-like records.
- Produces:
  - `project_decision_field(field, native_identity, source_ref) -> dict`
  - `reconstruct_decision_field(omega) -> DecisionField`
  - `project_s1_experience(record) -> dict`
  - `reconstruct_s1_experience(omega) -> dict`
  - `adapter_round_trip(native, projector, reconstructor) -> dict`

- [ ] **Step 1: Write failing adapter tests**

Tests must assert:
```python
def test_decision_field_round_trip_preserves_native_semantics_and_remainder():
    field = DecisionField(
        possibilities=(0,1,2),
        relations=({"kind":"excludes","left":0,"right":2},),
        evidence=(Evidence("software-verification","fixture"),),
        goal=1,
        unresolved=(0,2),
        observer={"obligation":"select-1"},
        history=("seed",),
    )
    omega = project_decision_field(field, "fixture:df:1", "fixture:df:1")
    rebuilt = reconstruct_decision_field(omega)
    assert rebuilt == field
    assert omega["domainRemainder"]["nativeClass"] == "DecisionField"

def test_s1_round_trip_keeps_ordered_actions_and_native_only_fields():
    native = load_fixture("omega_s1_native.json")
    omega = project_s1_experience(native)
    rebuilt = reconstruct_s1_experience(omega)
    assert rebuilt == native
    assert omega["path"] == [{"plane":"xw","degrees":1}]
    assert "nativeRemainder" in omega["domainRemainder"]

def test_s1_equal_compressed_counts_do_not_equal_history():
    a = fixture_s1(actions=[{"plane":"xw","degrees":1},{"plane":"yw","degrees":1}])
    b = fixture_s1(actions=[{"plane":"yw","degrees":1},{"plane":"xw","degrees":1}])
    assert project_s1_experience(a)["path"] != project_s1_experience(b)["path"]
```

Also test that a native-only field survives only through `domainRemainder` and is not silently promoted into a generic Ω field.

- [ ] **Step 2: Run RED**

Run:
```sh
python3 -m unittest "Decision Field Operator Lab/test_omega_adapters.py" -v
```
Expected: import failure for `omega_adapters`.

- [ ] **Step 3: Implement Decision Field adapter**

Use exact native fields. Convert tuple/frozenset values to deterministic JSON-compatible arrays only in Ω; store enough type metadata in `domainRemainder` to reconstruct exact tuple/frozenset semantics. Evidence maps `Evidence(kind, detail, certificate, claim_ceiling)` without changing kind or ceiling.

- [ ] **Step 4: Implement S'1 adapter**

Require `schema == "s1-experience/v0"`, `operatorVersion == "S'1-Ops v0"`, string `initialState`, `mirrorId`, `shell`, and ordered action array. Project actions directly to `path`; observer to `frame`; source/mirror/shell/operator-specific values remain reconstructible through `domainRemainder`. Preserve the entire canonical native record under a remainder reconstruction section, but report which common fields were independently projected so reconstruction is inspectable rather than opaque.

- [ ] **Step 5: Add round-trip report helper**

`adapter_round_trip` returns:
```python
{
  "omegaId": omega["id"],
  "nativeType": omega["nativeType"],
  "reconstruction": round_trip_report(native_canonical, rebuilt_canonical),
  "domainRemainder": omega["domainRemainder"],
}
```

- [ ] **Step 6: Run GREEN**

Run:
```sh
python3 -m unittest "Decision Field Operator Lab/test_omega.py" "Decision Field Operator Lab/test_omega_adapters.py" -v
```
Expected: all pass.

- [ ] **Step 7: Commit**

```sh
git add "Decision Field Operator Lab/omega.py" "Decision Field Operator Lab/omega_adapters.py" "Decision Field Operator Lab/test_omega_adapters.py"
git commit -m "feat: add native omega adapters"
```

---

### Task 3: Exact RMAPL v0 grammar and parser/IR

**Files:**
- Create: `Decision Field Operator Lab/RMAPL_V0_GRAMMAR.md`
- Create: `Decision Field Operator Lab/rmapl.py`
- Create: `Decision Field Operator Lab/test_rmapl.py`
- Create: `Decision Field Operator Lab/examples/omega_repair_fit.rmapl`

**Interfaces:**
- Consumes: JSON literals and symbolic operator names.
- Produces:
  - `RMAPL_VERSION = "RMAPL 0"`
  - frozen `Program`, `RepairSpec`, `FitterSpec`
  - `parse_rmapl(text: str) -> Program`

**Exact v0 grammar:**
```text
program       := "RMAPL 0" NL "PROGRAM " IDENT NL "LOAD " IDENT NL bound* block* "RUN" NL?
bound         := "BOUND " IDENT "=" JSON NL
block         := repair | fitter
repair        := "REPAIR " IDENT NL
                 "WHEN " STRING NL
                 "REQUIRES " JSON_ARRAY NL
                 "TARGETS " JSON_ARRAY NL
                 "PRESERVES " JSON_ARRAY NL
                 "MAY_MUTATE " JSON_ARRAY NL
                 "FORBIDS " JSON_ARRAY NL
                 "APPLY " IDENT NL
                 "EVIDENCE " JSON_ARRAY NL
                 "COST " JSON_NUMBER NL
                 "END" NL
fitter        := "FITTER " IDENT NL
                 "WHEN " STRING NL
                 "REQUIRES " JSON_ARRAY NL
                 "PRESERVES " JSON_ARRAY NL
                 "OBJECTIVES " JSON_OBJECT NL
                 "APPLY " IDENT NL
                 "EVIDENCE " JSON_ARRAY NL
                 "COST " JSON_NUMBER NL
                 "END" NL
```

Identifiers match `[A-Za-z_][A-Za-z0-9_.:-]*`. JSON is parsed by `json.loads`. Unknown/reordered/missing block fields fail closed.

- [ ] **Step 1: Write failing parser tests**

Tests:
```python
def test_parse_minimal_program():
    p = parse_rmapl(MINIMAL)
    assert p.version == "RMAPL 0"
    assert p.program_id == "omega-repair"
    assert p.load_ref == "fixture"
    assert p.bounds["maxCandidates"] == 4
    assert p.repairs[0].operator == "repair_x"

def test_unknown_operation_fails_closed():
    with pytest_raises(ValueError, "unknown top-level"):
        parse_rmapl("RMAPL 0\nPROGRAM x\nLOAD y\nMAGIC z\nRUN\n")

def test_reordered_repair_fields_fail_closed():
    bad = MINIMAL.replace("REQUIRES", "TEMP").replace("TARGETS", "REQUIRES", 1).replace("TEMP", "TARGETS", 1)
    with self.assertRaisesRegex(ValueError, "expected REQUIRES"):
        parse_rmapl(bad)

def test_nonfinite_or_non_json_bound_rejected():
    with self.assertRaises(ValueError):
        parse_rmapl('RMAPL 0\nPROGRAM x\nLOAD y\nBOUND x=NaN\nRUN\n')
```

- [ ] **Step 2: Run RED**

Run:
```sh
python3 -m unittest "Decision Field Operator Lab/test_rmapl.py" -v
```
Expected: module import failure.

- [ ] **Step 3: Implement frozen IR and parser**

Use `@dataclass(frozen=True)`. Parse non-comment, nonblank lines. Enforce exact field sequence. Reject duplicate IDs, duplicate bounds, non-string WHEN, non-array requirements/evidence, negative/non-finite cost, and trailing content after RUN.

- [ ] **Step 4: Add canonical example**

`omega_repair_fit.rmapl`:
```text
RMAPL 0
PROGRAM omega-repair
LOAD fixture
BOUND maxCandidates=4
BOUND maxSteps=8
REPAIR repair-x
WHEN "x-residual"
REQUIRES ["source.available"]
TARGETS ["x-residual"]
PRESERVES ["identity","claim-ceiling"]
MAY_MUTATE ["state.x"]
FORBIDS ["provenance","evidence"]
APPLY repair_x
EVIDENCE ["software-verification"]
COST 1
END
FITTER refit-surface
WHEN "surface-fit"
REQUIRES ["semantic-admitted"]
PRESERVES ["meaning"]
OBJECTIVES {"clarity":"max","ambiguity":"min"}
APPLY fit_surface
EVIDENCE ["semantic-reconstruction"]
COST 2
END
RUN
```

- [ ] **Step 5: Run GREEN**

Run:
```sh
python3 -m unittest "Decision Field Operator Lab/test_rmapl.py" -v
```
Expected: all pass.

- [ ] **Step 6: Commit**

```sh
git add "Decision Field Operator Lab/RMAPL_V0_GRAMMAR.md" "Decision Field Operator Lab/rmapl.py" "Decision Field Operator Lab/test_rmapl.py" "Decision Field Operator Lab/examples/omega_repair_fit.rmapl"
git commit -m "feat: add exact RMAPL v0 parser"
```

---

### Task 4: Conditional repair/fitting runtime, evidence admission, KD, Pareto, cycles

**Files:**
- Create: `Decision Field Operator Lab/rmapl_runtime.py`
- Create: `Decision Field Operator Lab/test_rmapl_runtime.py`

**Interfaces:**
- Consumes: validated Ω, parsed `Program`, operator registry `dict[str, Callable]`.
- Produces:
  - `ClaimSpec`
  - `KnowledgeDecay`
  - `CandidateOutcome`
  - `admit_claim(claim, evidence_kinds) -> bool`
  - `pareto_frontier(outcomes) -> tuple[CandidateOutcome,...]`
  - `run_program(program, omega, registry) -> dict`

`CandidateOutcome` carries:
```python
candidate_id, omega, consequence_key, classification,
metrics, knowledge_decay, inspection
```

Stop precedence is:
```text
SUCCESS
CERTIFIED_IMPOSSIBLE
NO_ADMISSIBLE_PROGRESS
REPEATED_STATE_CYCLE
RESOURCE_BOUND
EVIDENCE_BOUND
OUTER_CONTROLLER_BOUND
```
When multiple stop facts arise on one step, `stopFacts` contains all, while `stopReason` is the first by this precedence.

- [ ] **Step 1: Write failing runtime tests**

Must cover:
```python
def test_claim_local_evidence_does_not_amplify():
    claim = ClaimSpec("science", ("scientific-validation",), ())
    self.assertFalse(admit_claim(claim, {"software-verification"}))
    self.assertTrue(admit_claim(claim, {"scientific-validation","software-verification"}))

def test_equivalent_candidates_are_quotiented_with_provenance_union():
    # repair_a and repair_b return same consequence_key but different provenance
    result = run_program(program_with_two_repairs(), omega_with_residual(), registry)
    self.assertEqual(result["generation"]["equivalenceClassCount"], 1)
    self.assertEqual(sorted(result["branches"][0]["sourceCandidateIds"]), ["a","b"])

def test_pareto_incomparable_candidates_remain_separate():
    a = outcome(metrics={"residualReduction":2,"semanticLoss":1})
    b = outcome(metrics={"residualReduction":1,"semanticLoss":0})
    self.assertEqual(len(pareto_frontier((a,b))), 2)

def test_repair_breaking_protected_invariant_is_rejected_even_if_residual_falls():
    result = run_program(...repair changes invariant...)
    self.assertEqual(result["branches"][0]["classification"], "MUTATION")
    self.assertFalse(result["branches"][0]["admitted"])

def test_mutating_operator_input_is_rejected():
    def bad_operator(omega):
        omega["state"]["x"] = 2
        return omega
    with self.assertRaisesRegex(ValueError, "mutated input"):
        run_program(...)

def test_cycle_and_resource_fact_are_both_recorded_with_cycle_precedence_after_no_progress():
    result = run_program(...maxSteps=1, operator returns canonical prior state...)
    self.assertIn("REPEATED_STATE_CYCLE", result["stopFacts"])
    self.assertIn("RESOURCE_BOUND", result["stopFacts"])
    self.assertEqual(result["stopReason"], "REPEATED_STATE_CYCLE")

def test_kd_dimensions_are_separate():
    kd = KnowledgeDecay(loss=("x",), introduction=("y",), aliasing=(), ambiguity=(), provenance_gap=(), reconstruction_cost=1, oracle_shift=(), unresolved_growth=())
    self.assertEqual(kd.loss, ("x",))
    self.assertEqual(kd.introduction, ("y",))
```

- [ ] **Step 2: Run RED**

Run:
```sh
python3 -m unittest "Decision Field Operator Lab/test_rmapl_runtime.py" -v
```
Expected: module import failure.

- [ ] **Step 3: Implement typed evidence and KD**

`ClaimSpec` is frozen. `admit_claim` requires all evidence kinds and denies explicitly forbidden kinds/promotions. `KnowledgeDecay` retains each field independently.

- [ ] **Step 4: Implement candidate execution with side-effect guard**

Before calling an operator, compute `canonical_json(omega)`; pass a deep canonical copy; after call, verify the passed copy was not mutated by comparing its canonical form to the before snapshot. Normalize returned Ω. Operators are registry callables `operator(omega_copy) -> dict`.

- [ ] **Step 5: Implement quotient and Pareto**

Group outcomes by `consequence_key`. Preserve source candidate IDs and provenance for every member. Pareto dimensions are explicit in each outcome as:
```python
{
 "residualReduction": float,
 "invariantPreservation": float,
 "reconstructibility": float,
 "reversibility": float,
 "evidenceCoverage": float,
 "branchReduction": float,
 "provenanceCompleteness": float,
 "semanticLoss": float,
 "ambiguityIntroduction": float,
 "relationGrowth": float,
 "runtimeCost": float,
 "economicCost": float,
 "unresolvedGrowth": float,
 "irreversibleMutation": float,
}
```
First seven maximize; last seven minimize.

- [ ] **Step 6: Implement bounded run loop**

Trigger repair when its `WHEN` string matches a residual `kind`. Require all declared evidence kinds. Track generated/executed/pruned counts, exact bounds, state signatures, and stop facts. Fitter execution uses the same operator registry but remains classified `VALID_REFIT` only if preserved invariants and reconstruction status pass.

- [ ] **Step 7: Run GREEN**

Run:
```sh
python3 -m unittest "Decision Field Operator Lab/test_omega.py" "Decision Field Operator Lab/test_omega_adapters.py" "Decision Field Operator Lab/test_rmapl.py" "Decision Field Operator Lab/test_rmapl_runtime.py" -v
```
Expected: all pass.

- [ ] **Step 8: Commit**

```sh
git add "Decision Field Operator Lab/rmapl_runtime.py" "Decision Field Operator Lab/test_rmapl_runtime.py"
git commit -m "feat: execute bounded conditional RMAPL repairs"
```

---

### Task 5: Falsification adapters for GSFL, image surface, dimensional ladder, Suggest, and Hodge

**Files:**
- Modify: `Decision Field Operator Lab/omega_adapters.py`
- Create: `Decision Field Operator Lab/test_omega_domain_adapters.py`

**Interfaces:**
- Produces:
  - `project_gsfl_record(record) -> dict`
  - `project_image_surface(record) -> dict`
  - `project_dimensional_record(record) -> dict`
  - `project_suggestion_record(record) -> dict`
  - `project_hodge_bridge(record) -> dict`

Each projector validates the native schema/version fields it relies on, projects only justified shared roles, puts everything else in `domainRemainder`, and installs the native claim ceiling verbatim.

- [ ] **Step 1: Write failing domain-adapter tests**

Tests use synthetic records matching the current native contracts and assert:
- GSFL: `FIT != TRUTH` and semantic reconstruction evidence remain distinct.
- Image surface: intrinsic and projection observations remain separate.
- Dimensional: lossy projection record contains explicit induced equivalence/loss; missing loss declaration fails.
- Suggest: `authority == "suggestion-only"` maps into claim ceiling and cannot become experience authority.
- Hodge: `authority == "candidate-test-only"`; claim ceiling text is preserved; compressed signature and full action chronology remain separately inspectable.
- A Hodge record with an unknown stronger `authority: "proof"` fails closed.

- [ ] **Step 2: Run RED**

Run:
```sh
python3 -m unittest "Decision Field Operator Lab/test_omega_domain_adapters.py" -v
```
Expected: missing projector functions.

- [ ] **Step 3: Implement five projectors**

All projectors call `make_omega`; no projector modifies native source records. Domain-specific data that does not belong in common Ω roles stays in `domainRemainder["native"]`.

- [ ] **Step 4: Run GREEN**

Run:
```sh
python3 -m unittest discover -s "Decision Field Operator Lab" -p "test_*.py" -v
```
Expected: all Decision Field Operator Lab tests pass.

- [ ] **Step 5: Commit**

```sh
git add "Decision Field Operator Lab/omega_adapters.py" "Decision Field Operator Lab/test_omega_domain_adapters.py"
git commit -m "feat: add omega falsification adapters"
```

---

### Task 6: Deterministic audit, frozen evidence, workflow gate, and documentation routing

**Files:**
- Create: `Decision Field Operator Lab/run_rmapl_omega_audit.py`
- Create: `Decision Field Operator Lab/evidence/RMAPL_OMEGA_RESULTS.json`
- Create: `Decision Field Operator Lab/test_rmapl_omega_audit.py`
- Modify: `Decision Field Operator Lab/README.md`
- Modify: `DECISION_FIELD.md`
- Modify: `.github/workflows/operator-field-check.yml`

**Interfaces:**
- Audit output schema: `rmapl-omega-audit/v0`.
- CLI: `python3 "Decision Field Operator Lab/run_rmapl_omega_audit.py" --check`.

- [ ] **Step 1: Write failing audit test**

Test runs the audit script twice to temporary files, requires byte-identical output, requires:
```python
audit["schema"] == "rmapl-omega-audit/v0"
audit["scientificValidation"] is False
audit["checks"] == {
    "omegaStrict": True,
    "decisionFieldRoundTrip": True,
    "s1ChronologyDistinct": True,
    "typedEvidenceNoAmplification": True,
    "lossyQuotientExplicit": True,
    "paretoBranchPreserved": True,
    "cycleBounded": True,
    "hodgeCeilingPreserved": True,
    "suggestionAuthorityPreserved": True,
}
```
and `--check` must compare generated output to the committed frozen evidence file.

- [ ] **Step 2: Run RED**

Run:
```sh
python3 -m unittest "Decision Field Operator Lab/test_rmapl_omega_audit.py" -v
```
Expected: script/evidence missing.

- [ ] **Step 3: Implement deterministic audit**

The script constructs bounded synthetic fixtures using the public APIs from Tasks 1–5. Serialize with sorted keys and stable indentation. Set:
```json
{
  "scientificValidation": false,
  "claimCeiling": [
    "RMAPL_PROFILE != RMAL_CORE_FRONTEND",
    "OMEGA_VIEW != NATIVE_OBJECT",
    "METHOD_TRANSFER != EVIDENCE_TRANSFER",
    "SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",
    "MAXIMAL_WITHIN_DECLARED_SCOPE != GLOBAL_COMPLETENESS"
  ]
}
```

- [ ] **Step 4: Freeze audit evidence**

Run the script once and commit exact output as `evidence/RMAPL_OMEGA_RESULTS.json`. `--check` exits nonzero on byte mismatch.

- [ ] **Step 5: Update workflow**

Append:
```yaml
      - name: Verify RMAPL Omega conditional repair evidence is reproducible
        run: python3 "Decision Field Operator Lab/run_rmapl_omega_audit.py" --check
```
to `operator-field-check.yml`.

- [ ] **Step 6: Update documentation**

README adds a bounded RMAPL/Ω section, run command, schema/profile status, native-authority boundaries, and links to spec/domain collation.

`DECISION_FIELD.md` replaces the old prospective September 18 pointer with the September 20 successor pointer while retaining the predecessor as historical lineage, explicitly stating implementation status only after the audit exists.

- [ ] **Step 7: Run complete local-domain verification**

Run:
```sh
python3 -m unittest discover -s "Decision Field Operator Lab" -p "test_*.py" -v
python3 "Decision Field Operator Lab/run_audit.py" --check
python3 "Decision Field Operator Lab/run_gsfl_operator_audit.py" --check
python3 "Decision Field Operator Lab/run_gsfl_bidirectional_audit.py" --check
python3 "Decision Field Operator Lab/run_contextual_multicarrier_audit.py" --check
python3 "Decision Field Operator Lab/run_rmapl_omega_audit.py" --check
```
Expected: all commands exit 0.

- [ ] **Step 8: Commit**

```sh
git add ".github/workflows/operator-field-check.yml" "DECISION_FIELD.md" "Decision Field Operator Lab"
git commit -m "test: freeze RMAPL omega reference evidence"
```

---

### Task 7: Cross-domain regression verification and Conscience64 pointer

**Files:**
- Other-Projects-: no production changes unless regression evidence identifies a defect.
- Conscience64: modify only `research/hodge/CONSCIENCE64_COOPERATION.md` after Other-Projects exact-head verification succeeds.

**Interfaces:**
- Cross-reference points to canonical Other-Projects- spec/runtime; no copied runtime.

- [ ] **Step 1: Verify exact-head GitHub Actions for Other-Projects-**

Open/update the implementation PR and require success for:
- Decision Field Operator Lab workflow.
- S1 Models Check if any S1 file changed; expected not triggered.
- GSFL workflow if any GSFL file changed; expected not triggered.
- Hodge Span Check if any Hodge file changed; expected not triggered.

The implementation must not make success claims from local-domain tests alone; exact-head workflow success is the integration evidence.

- [ ] **Step 2: Run/adjudicate repository diff review**

Confirm changed files are limited to the plan/spec, Decision Field Operator Lab runtime/tests/evidence/docs, Decision Field pointer, and its workflow. No native S'1/GSFL/Hodge production files may change unless a separately ledgered defect requires it.

- [ ] **Step 3: Add Conscience64 cross-reference after canonical verification**

Append a concise section:
```markdown
## RMAPL / Ω conditional repair reference

Canonical implementation and evidence live in `redogit/Other-Projects-`.
Conscience64 consumes the contract only as research-navigation/provenance context.

`CONSCIENCE64_REFERENCE != IMPLEMENTATION_AUTHORITY`
`CONSCIENCE64_RETRIEVAL != INDEPENDENT_EVIDENCE`
`RMAPL_PROFILE != RMAL_CORE_FRONTEND`
```
with repository path pointers, not copied implementation.

- [ ] **Step 4: Verify Conscience64 diff is documentation-only**

No executable runtime or Hodge claim status changes.

- [ ] **Step 5: Commit Conscience64 pointer separately**

Commit message:
```text
docs: reference canonical RMAPL omega runtime
```

---

## Final whole-branch verification

Before integration:

```sh
python3 -m unittest discover -s "Decision Field Operator Lab" -p "test_*.py" -v
python3 "Decision Field Operator Lab/run_audit.py" --check
python3 "Decision Field Operator Lab/run_gsfl_operator_audit.py" --check
python3 "Decision Field Operator Lab/run_gsfl_bidirectional_audit.py" --check
python3 "Decision Field Operator Lab/run_contextual_multicarrier_audit.py" --check
python3 "Decision Field Operator Lab/run_rmapl_omega_audit.py" --check
```

Then require fresh exact-head GitHub Actions success and a final branch review against this plan and the September 20 spec.

The runtime's highest supported claim remains:

```text
A bounded, deterministic reference implementation demonstrates a common
provenance-preserving Ω projection and conditional RMAPL repair/fitting
calculus over declared fixtures and native adapters.

It does not establish a universal repair algorithm, global completeness,
scientific truth, a Hodge proof, a P-vs-NP consequence, or RMALC support
for RMAPL syntax.
```
