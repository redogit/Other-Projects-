# P-vs-NP MLIR Recursive Carrier-Wave Rewrite — Design

Date: 2026-09-14  
Status: architectural design approved in chat; implementation remains gated on written-spec review  
Scope: `redogit/Other-Projects-`, primarily `P versus NP Repair Lab/`, its decision-field/full-cost/mutation surfaces, and the cross-carrier interfaces they consume. Unrelated projects and historical evidence artifacts are not rewritten.

## 1. Purpose

Rewrite the active P-vs-NP research execution path around MLIR so that exact relations, existential carriers, cross-carrier transforms, topology, decision fields, temporal/spiking proposal signals, verification, provenance, and full cost accounting are all explicit compiler objects rather than implicit conventions spread across Python scripts and JSON artifacts.

The rewrite must preserve the current scientific boundary:

- P vs NP remains open;
- finite success is not an asymptotic theorem;
- proposal is not admission;
- representation novelty is not semantic validity;
- cross-reference is not evidence;
- temporal/spiking dynamics are proposal pressure only;
- UNKNOWN is not false and is not zero;
- moving cost between representations is not removing cost;
- legacy evidence is preserved, not rewritten.

The architectural goal is an open-ended recursive hierarchy — informally `L∞` — implemented only to a finite declared level in any run. No implementation may claim to instantiate a literal infinite compiler object.

## 2. Rewrite policy: full successor, no destructive big-bang replacement

“Rewrite all” means the active P-vs-NP execution semantics become expressible through the new MLIR stack. It does **not** mean deleting the legacy Python/C++ evidence path before parity is demonstrated.

Migration rule:

```text
legacy executable semantics
        ↓
MLIR mirror
        ↓
parity verification
        ↓
MLIR-native passes
        ↓
legacy becomes reference/oracle
```

Until parity is earned, the existing solver/checker remains authoritative for its current finite scope.

Historical files, scientific evidence JSON, prior failed runs, and frozen source snapshots are immutable predecessors. The rewrite creates successor artifacts and cross-references them.

## 3. Core architectural principle

Topology is underneath geometry and decision fields.

```text
Exact obligation / relation
        ↓
Carrier topology
        ↓
Existential + cross-carrier transforms
        ↓
Verified wavefront
        ↓
Edge freedoms
        ↓
Decision fields
        ↓
Temporal/spiking proposal pressure
        ↓
Candidate transform
        ↓
Independent exact verification
        ↓
Admit / Reject / Unresolved
```

The 13D'++ Compass, QIT literals, and other coordinate systems are optional atlases over this topology. They do not define truth semantics.

## 4. Recursive levels

The hierarchy is finite in any concrete run but recursively extensible.

### L0 — Problem semantics

Exact source obligation and source relation.

Examples:

- CNF SAT instance;
- partial truth table / circuit-survivor obligation;
- bounded exact repair instance.

Required properties:

- stable source identity;
- encoded-size definition;
- exact success semantics;
- claim ceiling;
- source provenance.

### L1 — Carrier IR

Typed representations of the same or obligation-equivalent information.

Initial carrier kinds:

- `cnf`;
- `boundary_relation`;
- `gf2`;
- `bijunctive`;
- `horn`;
- `dual_horn`;
- `matching`;
- `explicit_relation`;
- `shared_dag`;
- `circuit`;
- `partial_hard_survivor`;
- `nullary`.

### L2 — Transform / cross-reference IR

Every carrier transition is first-class.

A transform records:

- source carrier;
- destination carrier;
- transform kind;
- preconditions;
- preserved obligation;
- exactness certificate or verification requirement;
- cost vector;
- provenance;
- recoverability;
- unresolved remainder.

### L3 — Decision-field IR

Represents the legal consequential next actions from the current verified wavefront.

A decision field is not a generic search space. Each action has typed preconditions, target, direction, predicted consequence, cost, evidence status, reversibility/recovery, authority, and remainder.

### L4 — Temporal/spiking proposal IR

Optional proposal-priority layer attached to frontier edges. It may store phase, event/spike state, synchronization/subharmonic measurements, persistence, rigidity, or other declared dynamical features.

It cannot produce SAT/UNSAT or certify an exact transform.

### L5 — Meta-compiler IR

Represents search, composition, and scheduling over L1-L4 objects: which carriers to construct, which transforms to try, which frontier edge to expand, and which verified macro/pass to reuse.

### L(n+1) — Reification rule

Any finite, typed, provenance-preserving L(n) object or transformation graph may itself be represented as an L(n+1) carrier **only** when:

1. its semantics are declared;
2. its identity is stable;
3. its obligations are explicit;
4. transport preserves those obligations;
5. query/build/verification costs are charged;
6. the new level does not silently acquire authority over the level below.

This rule gives the architecture an open-ended `L0 -> L1 -> ... -> Lk` structure without pretending an infinite object has been materialized.

## 5. MLIR dialect decomposition

Use multiple small dialects rather than one monolithic `pnp` dialect.

### `pnp.core`

Authority-bearing exact problem semantics and verdict state.

Types/attributes:

- `!pnp.core.problem`
- `!pnp.core.obligation`
- `!pnp.core.verdict`
- `#pnp.core.status<SAT|UNSAT|UNKNOWN|BOUND>`

Operations:

- `pnp.core.source`
- `pnp.core.require`
- `pnp.core.return`

### `pnp.carrier`

Typed carrier values.

Types:

```text
!pnp.carrier<cnf>
!pnp.carrier<boundary_relation>
!pnp.carrier<gf2>
!pnp.carrier<matching>
!pnp.carrier<shared_dag>
!pnp.carrier<circuit>
!pnp.carrier<partial_hard_survivor>
!pnp.carrier<nullary>
```

Operations:

- `pnp.carrier.materialize`
- `pnp.carrier.query`
- `pnp.carrier.reconstruct`
- `pnp.carrier.digest`

### `pnp.rel`

Exact relational transformations.

Operations:

- `pnp.rel.restrict`
- `pnp.rel.project_exists`
- `pnp.rel.join`
- `pnp.rel.decompose`
- `pnp.rel.change_basis`
- `pnp.rel.change_carrier`
- `pnp.rel.compile`

`project_exists` is the canonical existential-carrier operation:

```text
R_X --exists Z--> R_B
```

### `pnp.xref`

Cross-reference and provenance topology.

Type:

- `!pnp.xref.edge`

Operations:

- `pnp.xref.link`
- `pnp.xref.predecessor`
- `pnp.xref.successor`
- `pnp.xref.equivalent_for`
- `pnp.xref.separation_depth`

A cross-reference never certifies its own semantic correctness.

### `pnp.wave`

Verified carrier-wave traversal.

Operations:

- `pnp.wave.seed`
- `pnp.wave.frontier`
- `pnp.wave.expand`
- `pnp.wave.admit`
- `pnp.wave.reject`
- `pnp.wave.unresolved`

The wavefront contains only verified/admitted carriers. Proposed outgoing edges remain proposals until checked.

### `pnp.decision`

Decision-field topology and action selection.

Types:

- `!pnp.decision.field`
- `!pnp.decision.action`
- `!pnp.decision.plan`

Operations:

- `pnp.decision.available`
- `pnp.decision.compose`
- `pnp.decision.select`
- `pnp.decision.branch`
- `pnp.decision.rollback`

Action relations include enables, blocks, independent/commuting, must-precede, reversible-pair, coupled, and obligation-relative equivalence.

### `pnp.temporal`

Proposal-only temporal/spiking dynamics.

Operations:

- `pnp.temporal.attach_edge_state`
- `pnp.temporal.spike`
- `pnp.temporal.measure_phase`
- `pnp.temporal.measure_locking`
- `pnp.temporal.rank_frontier`

No `pnp.temporal` operation may return a `!pnp.core.verdict` or directly feed `pnp.wave.admit` without exact verification.

### `pnp.evidence`

Verification, evidence status, cost, and claim boundaries.

Types:

- `!pnp.evidence.certificate`
- `!pnp.evidence.cost`
- `!pnp.evidence.result`

Operations:

- `pnp.evidence.verify_exact`
- `pnp.evidence.counterprobe`
- `pnp.evidence.record_failure`
- `pnp.evidence.record_cost`
- `pnp.evidence.claim_ceiling`

Evidence machinery stays logically separate from proposal-generation machinery.

### `pnp.meta`

Reifies finite lower-level graphs/programs as higher-level carrier objects and runs bounded meta-search.

Operations:

- `pnp.meta.reify`
- `pnp.meta.compose_passes`
- `pnp.meta.search`
- `pnp.meta.crystallize`
- `pnp.meta.lower_level`

Meta-level admission still requires independent lower-level verification.

## 6. Existential carrier contract

Given exact relation `R(X)` and retained interface `B subset X`, with hidden coordinates `Z = X \ B`:

```text
E_B[R] = pi_B(R) = { b : exists z, R(b,z) }
```

In MLIR:

```mlir
%boundary = pnp.rel.project_exists %source {
  hidden = [4, 7, 9],
  obligation = "sat-preservation"
} : !pnp.carrier<cnf> -> !pnp.carrier<boundary_relation>
```

Required checks:

- source and destination arities are consistent;
- hidden/retained coordinates partition the declared domain;
- the exactness obligation is named;
- build/representation cost is recorded;
- the transform has a verifier path;
- source lineage remains recoverable.

## 7. Cross-reference topology

The carrier topology is the graph:

```text
T = (Carriers, TypedTransformEdges)
```

Each edge contains:

```text
(source,
 destination,
 transform,
 obligation,
 preconditions,
 certificate-status,
 cost-vector,
 provenance,
 recovery-route,
 unresolved-remainder)
```

Multiple derivations may point to one semantic carrier identity. Same carrier identity does not imply same derivation or independent evidence.

Obligation-relative equivalence is explicit:

```text
Ci equiv_Q Cj
```

iff all admissible Q-relevant continuation queries agree. This relation does not automatically transfer to a different obligation `Q'`.

## 8. Edge-first freedoms and topology

Freedoms live at the verified frontier, not in an arbitrarily large latent vector.

Let `K_t` be the verified carrier region. The frontier is the set of legal outgoing typed transform edges from admitted carriers to not-yet-admitted carriers.

The degree-of-freedom budget is therefore the active frontier action set, not a fixed number like 199.

Expansion rule:

```text
verified region
  -> frontier
  -> decision field
  -> proposal
  -> exact verification
  -> admit/reject/unresolved
```

Outward expansion occurs only when the current frontier cannot resolve the declared remainder.

## 9. Decision fields

Each action is represented as:

```text
(Op,
 Direction,
 Target,
 Preconditions,
 PredictedConsequence,
 Cost,
 Evidence,
 ReversibilityOrRecovery,
 Authority,
 ExpectedRemainder)
```

QIT-style direction literals may be attached as metadata/attributes:

```text
0.[S'] { -1, 0, +1, @, UNKNOWN }
```

They are project-defined orientation metadata, not standard complexity-theory semantics.

`UNKNOWN != 0` is enforced.

Decision fields may be vector-valued; no arbitrary scalar objective is required. Pareto or obligation-declared ordering is preferred when costs are incomparable.

## 10. Temporal/spiking/time-crystal-inspired layer

This layer is optional and proposal-only.

Edge state may include:

```text
phase
frequency/subharmonic index
amplitude/order parameter
coupling state
rigidity/persistence
perturbation response
spike/event history
```

Coupling inherits exact carrier/cross-reference adjacency rather than creating a separate authoritative topology.

Required firewall:

```text
TEMPORAL_SIGNAL != SAT_AUTHORITY
PHYSICAL_DTC != DTC_INSPIRED_SIMULATION
```

A temporal signal may rank a frontier transform for probing. It cannot certify SAT/UNSAT, semantic equivalence, or P-vs-NP consequences.

## 11. Full cost model

Every pass and cross-reference can attach a typed cost vector. Do not collapse unlike units by default.

Tracked dimensions include:

```text
Co_state
Co_relation
Co_coupling
Co_transform
Co_decomposition
Co_planning
Co_carrier_discovery
Co_selection
Co_coupling_removal
Co_boundary_construction
Co_boundary_verification
Co_proof_reconstruction
Co_storage
Co_query
Co_recovery
```

Constructive P=NP evidence through this architecture would require a uniform polynomial bound on all consequential cost channels, carrier sizes, and path length for every SAT input. No finite benchmark can establish that alone.

## 12. P-vs-NP theorem obligations

### Constructive side

A genuine P=NP result through this framework requires one uniform deterministic procedure and polynomial `q` such that for every CNF `F` of encoded size `n`:

- every admitted transform preserves the required exact semantics;
- total planning/selection/transform/build/query/verify/reconstruct cost is at most `q(n)`;
- all live/intermediate carrier sizes are at most `q(n)`;
- the procedure returns SAT or UNSAT correctly.

### Lower-bound side

Failure of one dialect, carrier, transform family, decision policy, or wave strategy proves only that architecture's limitation unless the computational model is proved sufficiently general. A P != NP route must survive DAG sharing, auxiliary state, representation changes, and the standard barrier obligations relevant to the proposed proof method.

## 13. Rewrite mapping from current code

The new MLIR successor must cover current active semantics rather than deleting them.

### `decision_field/consequence_selector_k4.py`

Current roles map to:

- source CNF -> `pnp.core` + `pnp.carrier<cnf>`;
- exact `solve/check` results -> `pnp.evidence` certificates;
- affine candidate shortlist -> `pnp.decision.field`;
- branch probes -> `pnp.rel.restrict` + planned successor carriers;
- burden tuple -> obligation-scoped decision cost/ordering attributes;
- selected variable -> `pnp.decision.select`;
- recursive tree -> `pnp.wave` lineage;
- SAT/UNSAT/UNKNOWN -> `pnp.core.verdict`.

### `decision_field/one_feedback_round_selector.py`

Becomes a distinct MLIR policy/pass, preserving its failed scientific disposition rather than being silently replaced.

### Decision-field theorem/calibration files

Remain documentation/evidence predecessors. The MLIR rewrite cross-references them; it does not rewrite their conclusions.

### `full_cost/`

Cost-producing code becomes the reference source for `pnp.evidence.cost` parity tests before any new cost pass is authoritative.

### `mutation/`

CNF repair and restricted implication-closure repair become separate dialect conversions/passes with explicit preconditions and no extension of their proof domain.

### SPrime / cross-carrier inputs

Imported only through explicit cross-reference and translation contracts. No cross-project mathematical evidence transfer.

## 14. New repository layout

```text
P versus NP Repair Lab/
  mlir/
    CMakeLists.txt
    README.md
    include/pnp/
      CoreDialect.td
      CoreOps.td
      CarrierDialect.td
      CarrierTypes.td
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
      EvidenceOps.td
      MetaDialect.td
      MetaOps.td
    lib/
      Core/
      Carrier/
      Rel/
      XRef/
      Wave/
      Decision/
      Temporal/
      Evidence/
      Meta/
      Transforms/
    tools/
      pnp-opt/
      pnp-translate/
    python/
      emit_legacy.py
      parity_adapter.py
    test/
      dialects/
      transforms/
      parity/
      negative/
      meta/
```

Existing `decision_field/`, `full_cost/`, and `mutation/` remain in place through the parity phase.

## 15. Rewrite stages

### Stage 0 — Frozen parity manifest

Freeze current branch/commit, current finite panels, command lines, scientific outputs, hashes, and known failures.

### Stage 1 — Parse/print-only dialect stack

Define all dialects/types/ops and round-trip representative IR. No algorithm changes.

### Stage 2 — Legacy-to-MLIR emission

Emit deterministic MLIR from the existing consequence selector, full-cost records, and mutation plans.

Required parity: the emitted IR reconstructs the same relevant source identity, candidate shortlist, selected branch, status, and evidence references.

### Stage 3 — MLIR-native exact transforms

Implement `restrict`, `project_exists`, decomposition, and carrier change behind exact verification gates.

### Stage 4 — Decision/wave passes

Port consequence-aware selection and wavefront traversal. Preserve existing failure/UNKNOWN behavior.

### Stage 5 — Cross-referenced existential carriers

Add existential-carrier creation, equivalence-for-obligation, separation-depth metadata, and recovery lineage.

### Stage 6 — Meta-level composition

Allow verified transform sequences to crystallize into reusable passes/macros. Proposal and admission remain separate.

### Stage 7 — Temporal/spiking proposal pass

Add optional temporal frontier ranking. It cannot affect verdict semantics without passing through the exact verifier.

### Stage 8 — Legacy demotion

Only after full declared parity, make the MLIR stack the primary active implementation while retaining legacy programs as evidence/reference oracles.

## 16. Tests and gates

Before promotion of any stage:

1. TableGen/ODS verifier tests for malformed types/ops;
2. parse/print round-trip tests;
3. `UNKNOWN != 0/false` negative tests;
4. existential projection truth-table equivalence on exhaustive small cases;
5. carrier-change exactness tests;
6. cross-reference does not imply verification tests;
7. temporal op cannot create verdict/admission tests;
8. cost-channel preservation tests;
9. current consequence-selector parity on frozen cases;
10. current failed one-feedback-round result remains represented as failure, not erased;
11. mutation restricted-class proof boundary tests;
12. branch/project state-vs-relation growth counterexamples preserved;
13. repeated derivation -> same carrier identity but distinct provenance paths;
14. meta reification is finite and declares realized level `k`;
15. two-run byte-identical scientific outputs where determinism is promised;
16. exact-head CI on the review branch before promotion.

## 17. L∞ safety rule

`L∞` is shorthand for an extensible hierarchy, not an executable infinity.

Every run records:

```text
realized_level = k
```

and the compiler must reject recursive reification past its declared level/budget rather than silently continuing.

A higher level may analyze, route, compose, or reify a lower level, but it never gains permission to alter the lower level's obligation or evidence semantics.

Formally:

```text
LEVEL_UP != AUTHORITY_UP
```

and:

```text
VIEWPOINT_CHANGE != TASK_CHANGE
```

## 18. Evidence firewall and claim ceiling

The rewrite may improve architecture, observability, testability, carrier composition, and experimentation. It does not itself contribute new evidence for P=NP or P!=NP.

Required standing distinctions:

```text
SOURCE != RECONSTRUCTION
REFERENCE != EVIDENCE
RELATED != SUPPORTS
FINITE_VERIFICATION != UNIVERSALITY
PROPOSAL != ADMISSION
TEMPORAL_SIGNAL != PROOF
COMPACT_CARRIER != CHEAP_QUERY
SMALL_DAG != POLYNOMIAL_DECISION
LOWER_LEVEL_OPTIMIZATION != AUTHORITY_TO_CHANGE_OBLIGATION
```

## 19. First implementation milestone

The first milestone is intentionally conservative despite the full rewrite target.

Complete when:

1. all core dialects parse and verify;
2. the current consequence-selector execution can emit deterministic MLIR;
3. current SAT/UNSAT/UNKNOWN, selected branch, shortlist, certificate references, and bounded termination reconstruct identically from the MLIR record;
4. existential-carrier and cross-reference ops pass exhaustive small exactness tests;
5. no temporal/meta operation can bypass exact verification;
6. CI reproduces the parity audit on the exact branch head.

Only after this milestone may the MLIR implementation begin replacing current decision logic.

## 20. Promotion gate

This written design is the architecture boundary. Implementation planning begins only after user review of this file. The next process step is the `writing-plans` skill, followed by TDD execution against the reviewed plan.
