# RMAPL Ω Maximal Conditional Repair/Fitting Contract — Successor Design

**Date:** 2026-09-20  
**Status:** CHAT-DESIGN APPROVED / WRITTEN-SPEC REVIEW PENDING / NOT YET IMPLEMENTED  
**Canonical executable home:** `redogit/Other-Projects-`  
**Canonical design area:** `Decision Field Operator Lab/` + this spec  
**Cross-reference-only research companion:** `redogit/conscience64`  
**Design fork point:** `f93f056a33d5fad0f29b763a0d49c6b79eb18d49`  
**Verified merge-surface authority:** `8de91a93347aaff1ff039a4899fd56eec6689da3`  
**Predecessor design lineage:** `design/rmapl-omega-conditional-repair-20260918` @ `7a280826979b0acbc6335c3ccdd47734befd0965`  
**Current domain collation:** `Decision Field Operator Lab/RMAPL_OMEGA_DOMAIN_COLLATION_2026-09-20.md`

## 0. Design intent

This design consolidates the conversation's recurring computational structure into one **domain-derived repair/fitting profile** without replacing native project authorities.

RMAPL is the authoring/execution surface to be implemented for:

- conditional repair;
- conditional fitting;
- bounded candidate generation;
- consequential-equivalence quotienting;
- one-degree counterprobes;
- reconstruction;
- Knowledge Decay accounting;
- typed evidence admission;
- bounded fixed-point iteration;
- append-only provenance.

Ω is the common interchange/inspection envelope.

Decision Field remains the embedded task-local decision/control structure.

Existing native schemas remain authoritative for their domains.

The implementation target is **not** a master ontology and **not** a rewrite campaign.

```text
RMAPL PROFILE != NATIVE DOMAIN AUTHORITY
OMEGA VIEW != NATIVE OBJECT
CONNECTED != MERGED
METHOD TRANSFER != EVIDENCE TRANSFER
FIT != TRUTH
RECONSTRUCTION != GLOBAL IDENTITY
```

## 1. Relationship to current RMAL cooperation protocol

Current `main` already contains an implemented and validated RMAL cooperative implementation protocol.

That protocol controls cooperation/provenance boundaries such as:

```text
REFERENCE
-> PROPOSAL
-> HANDOFF
-> TARGET ACCEPTANCE
-> TARGET LOCAL SUCCESSOR
```

and denies:

```text
RELATED -> EDIT
SHARED METHOD -> SHARED EVIDENCE
AUTHORITY TRANSFER BY RELATION
```

RMAPL must respect those boundaries.

This design does **not** claim that the current RMAL parser/compiler already accepts the RMAPL constructs specified below.

Initial implementation must treat RMAPL as a separately versioned executable profile with an explicit bridge to native records and, if later desired, to RMAL.

```text
RMAPL PROFILE != RMAL CORE FRONTEND
RMAPL PARSE PASS != RMALC PASS
RMAPL AUDIT != SCIENTIFIC VALIDATION
```

Any future RMAPL-to-RMAL compiler or syntax promotion requires a separate bounded implementation and validation gate.

The later `BIDIRECTIONAL_HANDOFF_ADAPTER_2026-09-20.json` was reconciled into the verified implementation branch. It declares inbound handoff/target-acceptance syntax implemented but leaves the outbound structured response packet unestablished. This design preserves that gap.

```text
INBOUND_HANDOFF_IMPLEMENTED != COMPLETE_BIDIRECTIONAL_RUNTIME
RMAPL_OMEGA != IMPLICIT_STRUCTURED_RETURN_PACKET
```

## 2. Domain-first derivation

The generic contract is earned upward from native domains.

```text
NATIVE INPUT
-> NATIVE CONTRACT
-> NATIVE VERIFIER / COUNTERPROBE
-> INSPECTABLE RESULT
-> SHARED ROLE EXTRACTION
-> Ω PROJECTION
-> NATIVE RECONSTRUCTION OR LOSS CERTIFICATE
```

For domain `D_i`:

```text
D_i = Ω_i + R_i
```

where `R_i` is the explicit native remainder not safely represented by Ω.

`R_i` is not a defect.

The implementation must never force native remainder to zero merely to make the common schema look elegant.

## 3. Minimal Ω envelope

The first executable Ω schema must contain only roles justified by the domain collation.

Conceptual form:

```text
OmegaRecord {
    identity
    nativeType
    sourceRefs
    state
    path
    frame
    invariants
    observations
    residuals
    decisionField
    provenance
    evidence
    claimCeiling
    resourceBounds
    domainRemainder
}
```

Optional/native extensions may include mirror references, fit budgets, decay budgets, topology observations, semantic metrics, or Hodge authentication records.

They are not universal merely because they are useful.

### 3.1 Versioned source references

Ω preserves exact source versions used by a computation.

If a source changes, create a successor/version edge.

Do not mutate predecessor provenance.

```text
SOURCE CORRECTION -> SUCCESSOR VERSION
SOURCE CORRECTION != HISTORY REWRITE
```

## 4. Embedded Decision Field

Ω carries or references a task-local Decision Field:

```text
DecisionField<X,O,D,R,F,E,G,U>
```

Mapping:

```text
X -> possibilities/current state
O -> obligation/frame/context
D -> consequential distinctions/equivalence scope
R -> typed relations
F -> admitted operations
E -> evidence/provenance/uncertainty
G -> bounded success condition
U -> unresolved remainder
```

The Decision Field remains authoritative for task-local operator generation, admissibility, exact branch fallback, and unresolved-state semantics.

RMAPL uses it; it does not erase it.

## 5. RMAPL surface

The first profile reserves these semantic families:

```text
PROGRAM
LOAD
BOUND
FIELD
WHEN
REQUIRES
PRESERVES
MAY_MUTATE
FORBIDS
APPLY
OBSERVE
COMPARE
FOLD
FLIP
ROTATE
PROJECT
SLICE
COMPRESS
EXPAND
MAP
FIT
GENERATE
SELECT
QUOTIENT
COUNTERPROBE
VERIFY
RECONSTRUCT
MEASURE
ADMIT
REJECT
PRESERVE_BRANCH
PROPAGATE
ARCHIVE
ITERATE
STOP
```

These are design-level language roles.

They do not require native projects to rename their APIs.

## 6. Core program shape

```rmapl
PROGRAM OmegaRepairFit

LOAD Ω

BOUND Ω WITH {
    PRESERVE      = Ω.invariants
    CLAIM_CEILING = Ω.claimCeiling
    EVIDENCE      = Ω.evidence
    LINEAGE       = Ω.provenance
    PATH          = Ω.path
    RESOURCES     = Ω.resourceBounds
}

FIELD D = DECISIONS(Ω)

UNTIL {
    SUCCESS(Ω)
    OR CERTIFIED_IMPOSSIBLE(Ω)
    OR NO_ADMISSIBLE_PROGRESS(Ω)
    OR REPEATED_STATE_CYCLE(Ω)
    OR RESOURCE_BOUND_REACHED(Ω)
    OR EVIDENCE_BOUND_REACHED(Ω)
} DO {

    RESIDUALS R = EXPOSE_RESIDUALS(Ω)

    CANDIDATES C =
        GENERATE {
            REPAIRS(R)
            FITTERS(R)
            ROTATIONS(R)
            REFRAMES(R)
            RECONSTRUCTIONS(R)
            COUNTERPROBES(R)
        }

    C = FILTER_ADMISSIBLE(C, Ω)

    C = QUOTIENT C BY CONSEQUENTIAL_EQUIVALENCE(Ω)

    PROBES P = COUNTERPROBE(C, Ω)

    FRONTIER F = PARETO_RETAIN(P)

    BRANCHES B = APPLY_AND_CLASSIFY(F, Ω)

    Ω = PROPAGATE_AND_REPAIR_TO_FIXED_POINT(B, Ω)

    D = RECOMPUTE_DECISION_FIELD(Ω)
}
```

This syntax is illustrative of the required semantics. The implementation plan must define the exact v0 grammar before production parser code is written.

## 7. Conditional Repair

A repair is a typed conditional object:

```text
ConditionalRepair {
    id
    version
    trigger
    preconditions
    targetResiduals
    operator
    preserves
    mayMutate
    forbiddenMutations
    expectedEffect
    reversibility
    reconstruction
    requiredEvidence
    cost
    failureMode
    provenance
}
```

Example:

```rmapl
REPAIR RecoverInvariant {

    WHEN:
        residual("invariant:X") > 0

    REQUIRES:
        source.available
        reconstruction.available

    PRESERVES:
        source-lineage
        protected-invariants
        claim-ceiling

    MAY_MUTATE:
        representation

    FORBIDS:
        predecessor-history
        verifier-rules
        undeclared-authority

    APPLY:
        candidate = declared_operator(state)

    VERIFY:
        reconstructed = RECONSTRUCT(candidate)
        COMPARE protected_invariants(source, reconstructed)
        COUNTERPROBE declared_risk

    FAIL:
        CLASSIFY exact_failure

    SUCCESS:
        CLASSIFY exact_repair
}
```

Lower residual alone is insufficient for admission.

## 8. Conditional Fitter

A fitter selects among representations or compatible candidates under explicit obligations.

```text
ConditionalFitter {
    id
    version
    trigger
    admissibleDomain
    objectiveDimensions
    invariants
    candidateTransforms
    reconstructionTest
    lossBudget
    ambiguityBudget
    requiredEvidence
    claimCeiling
}
```

The fitter may not silently perform semantic admission unless its declared native contract explicitly includes that responsibility.

```text
FIT_SELECTED != SEMANTICALLY_ADMITTED
SEMANTICALLY_ADMITTED != TRUE
```

GSFL remains authoritative for its own semantic admission and reconstruction rules.

## 9. Maximal conditional repair/fitting

“Maximal” means:

> Generate every consequentially distinct repair/fitting class reachable inside the declared generator, condition, depth, cost, evidence, and resource bounds.

It does not mean search an undefined universe.

For obligation `O`:

```text
A(Ω,O) = {
  r |
  trigger(r,Ω,O)
  && preconditions(r,Ω,O)
  && resourceBounds(r,Ω,O)
  && evidenceBounds(r,Ω,O)
}
```

Candidates are quotiented only under declared consequential equivalence:

```text
r_i ~_(Ω,O) r_j
iff
all admitted consequence tests for O agree
```

Every run records:

```text
generationScope
generatorVersion
depthBound
costBound
evidenceBound
generatedCount
equivalenceClassCount
prunedCount
executedCount
resourceUsage
truncationReason
cycleStatus
unresolvedRemainder
```

Therefore the runtime may claim:

```text
MAXIMAL_WITHIN_DECLARED_SCOPE
```

but never global completeness without separate proof.

## 10. Conditional dependency graph

Repairs and fitters can enable or disable one another.

The runtime therefore maintains a conditional dependency graph:

```text
condition
-> residual
-> candidate operator
-> expected consequence
-> verifier
-> resulting condition changes
```

Each operator declares:

```text
enables
disables
invalidates
requiresRecheck
propagatesTo
```

Propagation is forward-only and typed.

If a repaired premise changes, dependent observations or claims become stale until reverified.

## 11. One-degree default and escalation

Default probe discipline:

```text
change one independently fluctuating degree
-> observe whole-system consequence
-> preserve result
-> run cheapest independent counterprobe
```

If unresolved:

```text
preserve prior result
-> add one new independent degree
-> repeat
```

A fixed multi-variable transform counts as one degree only when its internal relation is frozen as part of the declared probe.

The runtime must record which interpretation was used.

## 12. Pareto retention

Do not collapse repair quality into one magic scalar.

Retain separate dimensions.

Prefer high:

```text
residualReduction
protectedInvariantPreservation
reconstructibility
reversibility
evidenceCoverage
downstreamBranchReduction
provenanceCompleteness
```

Prefer low:

```text
semanticLoss
ambiguityIntroduction
relationGrowth
runtimeCost
economicCost
unresolvedGrowth
irreversibleMutation
```

Candidate `a` dominates `b` only when `a` is no worse on every protected dimension and better on at least one.

Incomparable candidates remain branches.

Stable serialization order is allowed, but:

```text
DETERMINISTIC_ORDER != EVIDENTIARY_RANK
```

## 13. Knowledge Decay accounting

Knowledge Decay is a structured residual vector:

```text
KD {
    loss
    introduction
    aliasing
    ambiguity
    provenanceGap
    reconstructionCost
    oracleShift
    unresolvedGrowth
}
```

Each component may itself be domain-specific.

A repair/fitter must expose its KD result.

A candidate cannot be admitted merely because the sum of its KD components is numerically smaller.

Protected dimensions remain separate.

## 14. BBF reconstruction classification

BBF is represented as:

```text
FOLD
-> FLIP
-> UNFOLD
-> COMPARE DECLARED INVARIANTS
-> MEASURE KD
-> CLASSIFY
```

Required classifications:

```text
EXACT_REPAIR
BOUNDED_REPAIR
VALID_REFIT
LOSSY_REFIT
MUTATION
SEMANTIC_DECAY
FAILED
UNRESOLVED
```

Successful reconstruction establishes only the declared invariant/equivalence relation.

```text
RECONSTRUCTED_INVARIANTS != GLOBAL_SOURCE_IDENTITY
```

## 15. Typed evidence admission

Evidence is not one scalar.

Each claim declares exact evidence obligations.

```text
Claim:
  id
  statement
  requiredEvidenceClasses
  forbiddenPromotions
  dependencies
  verifier
  claimCeiling
```

Admission:

```text
ADMIT(claim)
iff
all required evidence predicates are satisfied
and
all dependencies remain valid
and
no undeclared authority bridge is crossed
```

### 15.1 No Evidence Amplification

Representation changes cannot manufacture unrelated evidence.

```text
METHOD_TRANSFER != EVIDENCE_TRANSFER
REPRESENTATION_CHANGE != EVIDENCE_CREATION
RETRIEVAL != INDEPENDENT_VALIDATION
FIT_SCORE != TRUTH
```

If a target claim needs a stronger or different evidence class, RMAPL emits an unresolved evidence obligation rather than promoting the claim.

## 16. Lossy transforms and quotient semantics

Any non-injective operation must declare:

```text
sourceDomain
targetDomain
inducedEquivalence
preserved
lost
introduced
reconstructionAvailable
counterprobe
sourceReferenceRetention
```

Example:

```rmapl
COMPRESS SignedPlaneCounts {

    SOURCE:
        OrderedS1Chronology

    OUTPUT:
        Vector<xw,yw,zw>

    EQUIVALENCE:
        sameOutput => SIGNED_PLANE_COUNT_EQUIVALENCE

    DENY:
        sameOutput => FULL_DEFORMATION_EQUIVALENCE

    PRESERVE:
        sourceChronologyReference
        sourceDigest
}
```

## 17. Repair closure and cycle detection

Fixed point means:

> no admitted conditional repair changes a protected consequence under the current obligation and current bounds.

It does not mean global optimum.

Canonical cycle signature includes at least:

```text
native source refs
native object identity
obligation
residual signature
admitted operator set/version
claim ceiling
resource-bound identity
```

Stop certificates:

```text
SUCCESS
CERTIFIED_IMPOSSIBLE
NO_ADMISSIBLE_PROGRESS
REPEATED_STATE_CYCLE
RESOURCE_BOUND
EVIDENCE_BOUND
OUTER_CONTROLLER_BOUND
```

A cycle returns `UNRESOLVED` plus the repeated-state certificate.

## 18. Justified propagation

A repair may reduce adjacent issue surface only through explicit dependency edges.

Examples:

```text
software-contract repair
  -> software dependents

semantic reconstruction repair
  -> semantic dependents

exact algebraic calculation
  -> claims that depend on that exact calculation
```

Forbidden implicit leap:

```text
software repair
  -> Hodge algebraicity evidence
```

unless an explicit bridge declares and verifies that implication.

When a predecessor changes:

1. preserve predecessor;
2. create successor;
3. mark dependent results stale;
4. rerun only affected downstream verifiers;
5. propagate newly justified consequences;
6. preserve unresolved branches.

## 19. Native adapters

### 19.1 Decision Field

Project native fields into Ω without replacing native solver behavior.

Initial adapter must expose:
- state;
- obligation;
- distinctions;
- relations;
- admitted operations;
- evidence;
- goal;
- unresolved;
- native remainder.

### 19.2 S'1

Project:
- source/initial identity;
- mirror reference where relevant;
- ordered ±1° chronology;
- frame/observer;
- comparisons;
- replay/reconstruction relation;
- evidence ceiling.

Do not replace `s1-experience/v0` or `s1-carrier/v1`.

### 19.3 S'1 Suggest

Project candidate provenance and observed/generated status.

Never promote suggestion frequency or model output into experience authority.

### 19.4 Image Surface

Project:
- exact source image version;
- surface identity;
- intrinsic observations;
- extrinsic observations;
- projection observations;
- topology observations;
- replay relation.

Keep each evidence class separate.

### 19.5 GSFL / BBF

Project:
- source meaning/representation;
- semantic invariants;
- candidate rotation;
- fit objective;
- reconstruction result;
- KD residual;
- provenance.

GSFL retains semantic-admission authority.

### 19.6 Dimensional Ladder

Every embed/project/slice operation declares injectivity, loss, induced equivalence, and reconstruction domain.

### 19.7 Hodge bridge

Project the existing bridge result without changing its authority.

Preserve:

```text
REAL_4D != COMPLEX_DIMENSION_4
DEFORMATION_SIGNATURE != HODGE_CLASS
CANDIDATE_DIRECTION != ALGEBRAIC_CYCLE
SPAN_RESULT != ALGEBRAICITY_OR_COMPLETENESS_PROOF
CONSCIENCE64_RETRIEVAL != INDEPENDENT_EVIDENCE
```

### 19.8 Conscience64

Conscience64 gets adapters/pointers/documentation only.

No duplicate canonical Ω runtime.

## 20. Inspectability contract

Every executed RMAPL transition emits an inspection record:

```text
inputRefs
nativeContract
operator
operatorVersion
condition
trigger
preconditions
obligation
expected
actual
residualBefore
residualAfter
preserved
mutated
lost
introduced
reconstruction
knowledgeDecay
evidence
claimCeiling
counterprobe
provenance
resourceBounds
resourceUsage
unresolved
nextDecision
domainRemainder
```

No known failed/skipped gate, uncertainty, truncation, loss, assumption, provenance gap, or evidence limitation may be hidden.

## 21. Privacy and publication boundary

The common carrier must not become a reason to aggregate private personal context into public artifacts.

Adapters use the minimum data needed for the declared obligation.

```text
SHARED_CARRIER != SHARED_PRIVATE_CONTEXT
PROVENANCE != PUBLICATION_PERMISSION
INDEXABLE != PUBLISHABLE
```

Public repository fixtures should use technical/synthetic records unless a specific source is explicitly approved.

## 22. Accessibility boundary

Accessibility remains a first-class requirement where the resulting runtime has a human surface.

Machine-readable Ω inspection output is necessary but not sufficient for accessibility.

```text
STRUCTURED_OUTPUT != SCREEN_READER_VALIDATION
ACCESSIBLE_UI_CHECK != ASSISTIVE_TECHNOLOGY_CERTIFICATION
```

No RMAPL runtime should require a visual-only representation to inspect evidence, residuals, branches, or claim ceilings.

## 23. Schema strategy

Use JSON Schema Draft 2020-12 for interchange records.

Canonical authority surfaces should prefer strict schemas:

```text
unevaluatedProperties: false
```

or equivalent explicit runtime validation.

Extension points must be named, typed, and versioned.

No silent arbitrary authority fields.

## 24. Initial implementation boundary

Implementation proceeds in the smallest falsifiable sequence.

### Phase 1A — Native extraction first

Implement:
- Decision Field extraction fixture;
- S'1 extraction fixture;
- inspection record;
- native remainder;
- round-trip/loss report;
- shared-role intersection.

Do **not** implement a broad generic runtime first.

### Phase 1B — Minimal Ω + RMAPL v0

Only after Phase 1A passes:
- freeze minimal Ω v0 schema;
- freeze exact RMAPL v0 grammar;
- parser/validator;
- conditional repair metadata;
- conditional fitter metadata;
- typed evidence obligations;
- bounded candidate generation;
- consequential-equivalence quotienting;
- cycle detection;
- inspection records;
- Decision Field adapter;
- S'1 adapter.

### Phase 2 — Falsification adapters

Add independently:
- GSFL/BBF;
- image surface;
- dimensional ladder;
- S'1 Suggest;
- Hodge bridge.

Each adapter may force Ω v1 only if its missing role is consequential and cannot remain in native remainder.

### Phase 3 — Federation

- documentation routing;
- conscience64 cross-reference;
- optional RMAL bridge experiment;
- optional provenance exporters.

No phase silently changes scientific claim status.

## 25. TDD acceptance requirements for the future plan

The implementation plan must establish red-green evidence for at least:

1. Native Decision Field extraction preserves its declared native identity and remainder.
2. Native S'1 extraction preserves source identity, ordered chronology, and replay relation.
3. Native -> Ω -> native round trip reports preserved/lost/introduced/unresolved fields.
4. Ω rejects undeclared authority fields.
5. A deliberately native-only field stays in `domainRemainder`.
6. A lossy projection without quotient semantics fails closed.
7. Equal compressed signatures do not imply equal histories.
8. A missing claim-local evidence class blocks admission.
9. Software verification cannot become scientific validation through an adapter.
10. Repair generation records exact bounds and truncation.
11. Consequentially equivalent candidates can be quotiented while retaining all source provenance.
12. Pareto-incomparable candidates remain distinct.
13. A one-degree probe changes only its declared independent degree.
14. A repair that lowers one residual but breaks a protected invariant is rejected.
15. BBF reconstruction classifies exact repair, mutation, and semantic decay distinctly.
16. Knowledge Decay dimensions remain separately inspectable.
17. Repeated-state cycles terminate as `UNRESOLVED`.
18. Dependency propagation invalidates stale downstream observations after a predecessor changes.
19. Hodge adapter preserves its existing claim ceiling.
20. Suggest adapter cannot write suggestion output into experience authority.
21. Conscience64 has no duplicate canonical runtime.
22. Private-context fields not declared by the adapter fail closed for public interchange fixtures.
23. Inspection records expose skipped/failed gates and unresolved remainder.
24. Existing native test suites remain green without schema renaming.

## 26. RMAPL / RMAL integration boundary

The first RMAPL implementation should not modify RMALC merely to achieve naming unification.

Preferred initial architecture:

```text
RMAPL source
-> RMAPL v0 parser/validator
-> normalized Ω / repair IR
-> native adapters/verifiers
-> inspection/evidence output
```

Optional later experiment:

```text
RMAPL IR
-> explicit RMAL bridge/compiler adapter
-> RMALC check/compile/audit
```

That experiment is admitted only if it preserves semantics and provenance and supplies its own negative fixtures.

## 27. Claim ceiling

This design supports the engineering hypothesis that:

> multiple existing project domains can expose a minimal common, provenance-preserving repair/fitting projection with explicit native remainder, conditional operations, reconstruction/loss accounting, typed evidence admission, and bounded maximal search.

This design does **not** establish:

- a universal representation for all computation;
- a universal repair algorithm;
- global optimization;
- global semantic equivalence;
- a theorem about Hodge;
- a P-vs-NP consequence;
- a physical field;
- that RMAPL is already implemented in RMALC;
- that successful software tests establish scientific truth.

## 28. Final execution law

```text
SOURCE VERSION
-> LOAD NATIVE CONTRACT
-> PROJECT MINIMAL Ω VIEW
-> EXPOSE RESIDUAL
-> GENERATE CONDITIONALLY ADMISSIBLE REPAIRS/FITS
-> QUOTIENT CONSEQUENTIAL EQUIVALENTS
-> COUNTERPROBE
-> PARETO RETAIN
-> APPLY WITHOUT REWRITING HISTORY
-> RECONSTRUCT / REPORT LOSS
-> MEASURE KNOWLEDGE DECAY
-> VERIFY CLAIM-LOCAL EVIDENCE
-> ADMIT / REJECT / PRESERVE UNRESOLVED
-> INVALIDATE STALE DEPENDENTS
-> PROPAGATE ONLY JUSTIFIED CONSEQUENCES
-> ARCHIVE FULL LINEAGE
-> REPEAT TO BOUNDED FIXED POINT OR STOP CERTIFICATE
```

RMAPL is the executable conditional repair/fitting surface.

Ω is the minimal common projection and inspection envelope.

Decision Field is the embedded task-local control/decision structure.

RMAL supplies the current implemented cooperation/provenance protocol and remains separately authoritative for its own compiler/runtime.

RMALKDVMLLL remains the broader VM/link-layer research line and is not redefined here.

The system maximizes **conditional consequential coverage**, not indiscriminate mutation.
