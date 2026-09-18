# RMAPL Ω Conditional Repair/Fitting Contract — Design

**Date:** 2026-09-18  
**Status:** APPROVED DESIGN / NOT YET IMPLEMENTED  
**Canonical executable home:** `redogit/Other-Projects-`  
**Cross-reference only:** `redogit/conscience64`

## 1. Purpose

Define one executable RMAPL interchange and verification contract for the structures already present in:

- Decision Field Operator Lab;
- S'1 core / experience / carrier / observer / image-surface / Suggest work;
- dimensional-ladder experiments;
- GSFL / BBF semantic rotation and reconstruction;
- Knowledge Decay residual accounting;
- Hodge candidate bridges.

The goal is **not** to merge these systems or replace their native authority. The goal is to make their shared computational obligations machine-checkable through a common projection.

Core relation:

```text
native object
  -> typed Ω projection
  -> conditional repair / fitting / verification
  -> explicit residuals + provenance
  -> native reconstruction or declared non-reconstructible remainder
```

Required boundaries:

```text
OMEGA_VIEW != NATIVE_OBJECT
CONNECTED != MERGED
METHOD_TRANSFER != EVIDENCE_TRANSFER
REPRESENTATION_EQUALITY != SOURCE_EQUALITY
FIT != TRUTH
OBSERVER != TRUTH_AUTHORITY
SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION
```

## 2. Why Ω is a projection, not a replacement

Three existing structures already carry most of the needed semantics:

1. `DecisionField<X,O,D,R,F,E,G,U>` provides possibilities, obligation/context, distinctions, relations, admitted operators, evidence, goal, and unresolved remainder.
2. `s1-carrier/v1` provides canonical typed carriers, neutral/join/difference/interaction/quotient operations, deterministic identities, and collision guards.
3. GSFL provides semantic admission, fit, reconstruction, mutation separation, and semantic-decay controls.

A fourth independent implementation would duplicate authority and increase reconstruction cost.

Therefore Ω is a **common typed projection** over native objects. Native schemas remain authoritative for their domain.

## 3. Canonical Ω record

RMAPL surface:

```rmapl
TYPE Omega<
    Identity,
    Type,
    SourceRefs,
    MirrorRefs,
    State,
    Path,
    Frame,
    Invariants,
    Observations,
    Residuals,
    DecisionField,
    Provenance,
    Evidence,
    ClaimCeiling,
    Resources,
    AllowedDecay
>
```

Normalized conceptual record:

```text
OmegaRecord {
    identity
    type
    sourceRefs
    mirrorRefs
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
    resources
    allowedDecay
}
```

### Source correction

Ω does **not** assume that the real-world or mathematical thing being modeled is globally immutable.

It requires immutable **references to the particular source versions used by the computation**, plus derivation/activity edges.

```text
sourceRefs = exact versioned inputs used here
path       = ordered activities / transforms
state      = current derived state
```

If a source changes, that is represented as a successor entity/version, not an in-place rewrite of historical provenance.

## 4. Provenance and derivation

The internal contract should align structurally with established provenance practice without claiming standards compliance.

Required notions:

```text
Entity/version
Activity/transform
Derivation edge
Agent/tool identity when relevant
Input references
Output identity
Exact parameters
Dependencies
Verifier identity/version
```

Every admitted transition records:

```text
parentOmegaId
operatorId
operatorVersion
inputRefs
outputRef
parameters
preserved
mayMutate
loss
introduction
residual
evidence
claimCeiling
reconstruction
provenance
```

History is forward-only. Corrections create successors and invalidate/down-rank dependent claims explicitly; they do not rewrite predecessor evidence.

## 5. RMAPL operator families

Reserved design-level operator families:

```text
LOAD
BOUND
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
COUNTERPROBE
VERIFY
RECONSTRUCT
ADMIT
REJECT
LINK
ARCHIVE
PROPAGATE
REPAIR
```

These are semantic roles, not an instruction to rename all existing APIs.

Native implementations may map their existing functions to these roles through adapters.

## 6. Conditional repair contract

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

RMAPL form:

```rmapl
REPAIR RecoverInvariant {
    WHEN:
        residual("invariant:X") > 0

    REQUIRES:
        declared preconditions

    PRESERVES:
        identity-lineage
        protected-invariants
        claim-ceiling

    MAY_MUTATE:
        declared representation fields

    FORBIDS:
        source-version history
        verifier rules
        undeclared authority

    APPLY:
        candidate = declared operator

    VERIFY:
        reconstruct candidate
        compare protected invariants
        counterprobe declared risk

    FAIL:
        classify exact failure

    SUCCESS:
        classify exact repair
}
```

A repair is never admitted merely because it lowers a residual.

## 7. Conditional fitter contract

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

A fitter operates only over already-admissible semantic candidates unless its task explicitly includes semantic admission.

```text
FIT_SELECTED != SEMANTICALLY_ADMITTED
SEMANTICALLY_ADMITTED != TRUE
```

GSFL remains authoritative for its semantic-rotation admission rules.

## 8. Maximal conditional repair: precise meaning

“Maximal” is task-local and bounded.

It means:

> Generate all consequentially distinct admissible repair/fitting classes reachable within the declared generator, depth, cost, evidence, and resource bounds.

It does **not** mean exhaustive search over an undefined universe.

For Ω with obligation `O`:

```text
A(Ω) = { r | trigger(r,Ω) && preconditions(r,Ω) && withinBounds(r,Ω) }
```

Quotient repairs by declared consequential equivalence:

```text
r_i ~_Ω r_j
iff
all admitted consequence tests for current obligation agree
```

The runtime records:

```text
generationScope
equivalenceScope
visitedCount
generatedCount
quotientedCount
executedCount
prunedCount
truncationReason
resourceUsage
```

Therefore a result can say “maximal within declared scope” without implying global completeness.

## 9. Pareto admission, not one magic score

Candidate comparison retains separate dimensions:

```text
MAX:
  residual reduction
  protected invariant preservation
  reconstructibility
  reversibility
  evidence coverage
  downstream branch reduction
  provenance completeness

MIN:
  semantic loss
  ambiguity introduction
  relation growth
  runtime/economic cost
  unresolved growth
  irreversible mutation
```

A candidate dominates another only if it is no worse on every protected dimension and strictly better on at least one.

Incomparable candidates remain separate branches.

A deterministic tie-order may stabilize serialization, but tie-order **must not** be described as evidentiary superiority.

## 10. Typed evidence admission — correction to scalar “evidence strength”

Evidence is not modeled as one scalar.

Each claim declares the evidence predicates/domains required for admission.

Example:

```text
Claim: "candidate vector is outside supplied rational span"

Requires:
  exact-input-authenticated
  rational-map-valid
  exact-linear-algebra-verifier-pass

Does not require:
  human-usability evidence
  browser-render evidence
```

Example:

```text
Claim: "rendered interface is screen-reader usable"

Requires:
  rendered-interface target
  declared assistive-technology evidence

Cannot be admitted from:
  Node unit tests alone
```

Rule:

```text
ADMIT(claim)
iff
every evidence obligation required by that exact claim is satisfied
and
no dependency crosses an undeclared authority bridge
```

This replaces the earlier scalar `min(evidenceStrength)` idea.

### No Evidence Amplification

A transform may carry, narrow, or invalidate source evidence. It cannot create an unrelated evidence class by representation change alone.

```text
METHOD_TRANSFER != EVIDENCE_TRANSFER
REPRESENTATION_CHANGE != EVIDENCE_CREATION
RETRIEVAL != INDEPENDENT_VALIDATION
```

## 11. Lossy transforms require explicit quotient semantics

Every non-injective projection/compression must declare:

```text
sourceDomain
outputDomain
equivalenceInduced
preserved
lost
introduced
reconstructionAvailable
counterprobe
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
        full source chronology reference
        source digest
}
```

This directly preserves the correction already made in the Hodge deformation bridge.

## 12. Knowledge Decay vector

Knowledge Decay is represented as a typed residual vector rather than one score:

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

Each field is domain-defined and may itself be structured.

A fitter or repair is admissible only if every protected KD component remains inside its declared budget.

```text
LOWER_TOTAL_KD != AUTOMATICALLY_BETTER
```

because a reduction in one component may destroy a protected distinction in another.

## 13. One-degree experiments

Default experimental discipline:

```text
change one independently fluctuating degree
-> observe whole-system consequence
-> preserve result
-> run cheapest independent counterprobe
-> add another degree only if the obligation remains unresolved
```

This is a default research operator, not a universal mathematical law.

A fixed declared transform may coordinate multiple variables while still counting as one experimental degree when its internal relation is frozen for the probe.

## 14. Repair-to-fixed-point termination

Conditional repair can cycle. Therefore termination must be explicit.

Runtime state includes a canonical transition signature over at least:

```text
native source refs
native object identity
residual signature
decision obligation
admitted operator set/version
claim ceiling
```

The repair loop stops on any of:

```text
SUCCESS
CERTIFIED_IMPOSSIBLE
NO_ADMISSIBLE_PROGRESS
REPEATED_STATE_CYCLE
RESOURCE_BOUND
EVIDENCE_BOUND
USER/OUTER_CONTROLLER_BOUND
```

A repeated canonical state produces a cycle certificate and remains `UNRESOLVED`; it is not silently treated as convergence.

Fixed point means:

```text
no admitted conditional repair changes any protected consequence
under the current obligation and bounds
```

—not “the globally optimal solution was found.”

## 15. Core RMAPL execution law

```rmapl
MAXIMALLY_REPAIR Ω {

    NORMALIZE Ω
    EXPOSE residuals

    GENERATE
        all consequentially distinct
        admissible repairs/fits
        within declared bounds

    QUOTIENT
        only under declared consequential equivalence

    COUNTERPROBE
        surviving classes

    RETAIN
        Pareto-undominated candidates

    APPLY
        without rewriting predecessor history

    RECONSTRUCT
        protected invariants where declared possible

    MEASURE
        typed Knowledge Decay residuals

    VERIFY
        exact claim-local evidence obligations

    REJECT
        undeclared mutation
        authority amplification
        provenance loss
        forbidden semantic decay

    PROPAGATE
        only typed justified consequences

    ARCHIVE
        successes, failures, unresolved branches, counterexamples

    ITERATE
        until bounded fixed point or explicit stop certificate
}
```

## 16. Native adapters

### Decision Field Operator Lab

Native authority remains:

```text
DecisionField<X,O,D,R,F,E,G,U>
```

Ω projection maps:

```text
X -> state / possibilities
O -> frame / obligation
D -> distinctions / quotient scope
R -> relations
F -> admitted repair/operator set
E -> evidence + provenance
G -> acceptance/success condition
U -> residuals / unresolved remainder
```

No native solver semantics are replaced merely by adding Ω.

### S'1

Map existing:

- `s1-experience/v0`;
- `s1-carrier/v1`;
- mirror state;
- ordered one-degree actions;
- observer sidecars;
- comparison residuals.

Do not rename or supersede these schemas.

### Image Surface

Preserve exact source-image version/reference, parameterized surface identity, experience identity, intrinsic metric, projection metric, curvature proxy, and finite-grid topology as separate observations.

```text
IMAGE_DEFORMATION != PHYSICAL_DEFORMATION
FINITE_GRID_CONNECTIVITY != CONTINUUM_TOPOLOGY
PROJECTION_DISTORTION != INTRINSIC_DEFORMATION
```

### S'1 Suggest

Suggestion remains generator-only:

```text
SUGGESTION != EXPERIENCE_AUTHORITY
GENERATOR != VERIFIER
```

Ω may carry suggestion provenance and counterprobe results, but suggestion frequency cannot manufacture truth/evidence.

### GSFL / BBF

GSFL remains semantic-authority owner for its declared semantic reconstruction tests.

BBF maps naturally to:

```text
FOLD -> FLIP -> UNFOLD -> COMPARE_INVARIANTS -> KD
```

Failure to reconstruct declared invariants is mutation/decay under the task contract, not a valid semantic rotation.

### Dimensional Ladder

Embeddings, projections, slices, and observer transforms declare injectivity/loss and reconstruction domains explicitly.

```text
ADJACENT_DIMENSIONS_RELATED != ADJACENT_DIMENSIONS_IDENTICAL
```

### Hodge bridge

The Hodge bridge may expose an Ω projection of its existing result carrier.

It must preserve:

```text
REAL_4D != COMPLEX_DIMENSION_4
DEFORMATION_SIGNATURE != HODGE_CLASS
CANDIDATE_DIRECTION != ALGEBRAIC_CYCLE
SPAN_RESULT != ALGEBRAICITY_OR_COMPLETENESS_PROOF
CONSCIENCE64_RETRIEVAL != INDEPENDENT_EVIDENCE
```

No generic Ω operator may weaken these boundaries.

## 17. Conscience64 relation

`conscience64` receives documentation/adapters/cross-references only.

Permitted:

```text
CONSCIENCE64 --references/adapts--> canonical RMAPL Ω contract
```

Not permitted by reference alone:

```text
CONSCIENCE64_REFERENCE == IMPLEMENTATION_AUTHORITY
CONSCIENCE64_RETRIEVAL == INDEPENDENT_EVIDENCE
```

No duplicate Ω runtime is created there.

## 18. Schema strategy

Use JSON Schema Draft 2020-12 for machine-readable interchange schemas.

Prefer closed authority surfaces for canonical records:

```text
unevaluatedProperties: false
```

where composition permits it, or equivalent explicit validation in native runtime code.

Extension points must be named and typed rather than relying on silent arbitrary fields.

## 19. External sanity checks used for this design

These are calibration references, not authorities over project semantics:

- W3C PROV family: entity/activity/derivation/provenance modeling and provenance interchange.
- Martin Fowler, Event Sourcing: ordered events as the basis for reconstructing historical state.
- JSON Schema Draft 2020-12: strict schema composition and unevaluated-property control.
- SLSA / in-toto provenance: explicit artifact inputs, process/build identity, dependencies, trust boundaries, and verifiable provenance.

The project does **not** claim conformance to W3C PROV, SLSA, or in-toto unless a future bounded conformance task is executed.

## 20. Adversarial corrections incorporated

The following attractive but unsafe formulations are explicitly rejected:

1. **Scalar evidence strength**
   - Rejected because evidence domains are only partially ordered and often incomparable.
   - Replaced with claim-local typed evidence obligations.

2. **Globally immutable source object**
   - Rejected because sources/objects may legitimately evolve.
   - Replaced with immutable references to exact source versions plus derivation edges.

3. **“Maximal” means globally exhaustive**
   - Rejected.
   - Replaced with maximal consequential coverage inside declared generator/resource/evidence bounds.

4. **Fixed point means global optimum**
   - Rejected.
   - Fixed point means no admitted repair changes a protected consequence under current bounds.

5. **Pareto frontier proves best**
   - Rejected.
   - Pareto filtering is a planning/selection device only.

6. **One-degree experiments are universally sufficient**
   - Rejected.
   - They remain the default bounded probe; additional independent degrees are admitted when necessary.

7. **Successful reconstruction proves source identity**
   - Rejected.
   - Reconstruction establishes only the declared invariant/equivalence contract.

## 21. Implementation acceptance criteria

A future implementation plan must prove at least:

1. Ω schema rejects undeclared authority fields.
2. Native -> Ω -> native reconstruction preserves declared canonical identity for an exact reversible fixture.
3. Lossy projection requires an explicit quotient/loss declaration.
4. Two histories that share a compressed signature remain distinguishable.
5. Typed evidence admission rejects a claim requiring a missing evidence domain.
6. Cross-domain adapter cannot promote software verification to scientific validation.
7. Repair generation records its declared scope and truncation state.
8. Consequentially equivalent repair candidates are quotiented without erasing their provenance.
9. Pareto-incomparable candidates remain separate branches.
10. Repeated-state cycles stop with an `UNRESOLVED` cycle certificate.
11. Knowledge Decay components remain separately inspectable.
12. S'1, GSFL, image-surface, dimensional-ladder, and Hodge fixtures can each expose an Ω view without changing their native schema identity.
13. Conscience64 contains no duplicate canonical runtime.
14. Existing native tests continue to pass unchanged unless a separately justified defect is found.

## 22. Rollout boundary

First implementation should be deliberately narrow:

```text
Phase 1:
  generic Ω schema + validator
  typed evidence admission
  repair/fitter metadata contracts
  bounded repair frontier + cycle detection
  Decision Field adapter
  S'1 adapter
  exact tests

Phase 2:
  GSFL adapter
  image-surface adapter
  dimensional-ladder adapter
  Hodge bridge adapter

Phase 3:
  conscience64 cross-reference
  documentation federation
  optional provenance-format exporters
```

No phase may silently change native scientific claim status.

## 23. Final design statement

RMAPL is the executable repair/fitting surface.

Ω is the common projection and verification envelope.

Decision Fields remain native decision/control objects inside or projected through Ω.

RMALKDVMLLL remains the broader VM/link-layer framework; this design does not redefine it.

The execution law is:

```text
SOURCE VERSION
-> TRANSFORM
-> OBSERVE
-> COMPARE
-> EXPOSE RESIDUAL
-> GENERATE CONDITIONAL REPAIRS/FITS
-> QUOTIENT CONSEQUENTIAL EQUIVALENTS
-> COUNTERPROBE
-> PARETO RETAIN
-> APPLY
-> RECONSTRUCT
-> MEASURE DECAY
-> VERIFY CLAIM-LOCAL EVIDENCE
-> ADMIT / REJECT / PRESERVE UNRESOLVED
-> PROPAGATE JUSTIFIED CONSEQUENCES
-> ARCHIVE
-> REPEAT TO BOUNDED FIXED POINT
```

Every stage preserves native lineage, explicit uncertainty, and evidence boundaries.
