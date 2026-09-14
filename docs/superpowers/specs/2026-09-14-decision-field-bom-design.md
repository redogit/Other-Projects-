# Decision-Field Bill of Materials — Design

Date: 2026-09-14  
Status: design approved in principle; implementation gated on review of this written specification  
Scope: `redogit/Other-Projects-`, SPrime decision-field research

## 1. Purpose

Treat the existing SPrime/decision-field stack as one proven **assembly**, not as the definition of the system.

The system should be able to answer:

1. What functional capabilities are required by a declared obligation?
2. Which available parts provide those capabilities?
3. Can one part provide several capabilities at once?
4. Can a different assembly preserve the obligation with less cost, less coupling, stronger evidence, or better reuse?
5. Which distinctions are still unresolved after substitution?

The design must preserve the evidence boundaries of Passes 06–08. A replacement that passes one obligation is not thereby universally equivalent to the part it replaced.

## 2. Design decision: capability-based BOM, not role-per-component

A fixed role-to-component mapping is rejected.

The Pass 08 hidden-mode witness demonstrates why: an action may be both **consequential** and **diagnostic**. Requiring a separate sensor/probe component would bake an already-refuted architectural assumption into the BOM.

Therefore:

- an **obligation** declares required capabilities and protected consequences;
- a **part** may provide one or many capabilities;
- a **part** may require capabilities from other parts;
- an **assembly** is a compatible set of parts whose provided capabilities cover the requirement set;
- the verifier decides whether that assembly actually satisfies the declared obligation.

This permits like-for-like substitution, fusion of several old parts into one, or decomposition of one old part into several better-bounded parts.

## 3. Required capability vocabulary

The initial finite deterministic BOM uses these capabilities:

| Capability | Contract |
|---|---|
| `transition` | Given hidden/world state and action/context, produce the next hidden/world state. |
| `observe` | Map hidden/world state to an observation available to the controller. |
| `infer` | Update a knowledge carrier from prior knowledge, action and observation. |
| `monitor` | Carry obligation history that is not recoverable from current physical state alone. |
| `decide` | Select an action/context from the information available to the policy. |
| `remember` | Carry policy state that is not part of the physical world or obligation monitor. |
| `schedule` | Generate or constrain context/action sequences over time. |
| `encode` | Give an exact transport/identity representation to a declared object. |
| `verify` | Independently test a declared obligation and evidence boundary. |

The vocabulary is extensible, but adding a capability requires a witnessed obligation that cannot be represented cleanly by the existing vocabulary.

## 4. Core records

### 4.1 ObligationSpec

An obligation is the authority for replacement.

Required fields:

- stable id and version;
- subject/domain and finite bounds;
- allowed initial states/worlds;
- allowed actions/contexts;
- protected invariants;
- success condition;
- required capabilities;
- observable information and permissions;
- temporal semantics, including whether intermediate trajectories matter;
- exact/approximate regime;
- evidence threshold;
- unresolved remainder;
- cost dimensions that may be compared.

Examples of success conditions include sure safety, sure reachability with an explicit monitor, exact reconstruction, or exact final-state equivalence. No generic `success=True` may substitute for the obligation-specific verifier.

### 4.2 PartSpec

A part is an implementation candidate, not an architectural truth.

Required fields:

- stable id/version;
- `provides`: capability set;
- `requires`: capability set;
- typed input/output ports;
- state carried by the part;
- assumptions and finite bounds;
- side effects;
- external dependencies;
- measurable cost vector;
- evidence references;
- known failure modes;
- replaceability boundary.

A part may provide multiple capabilities. Such fusion is allowed but its coupling must be visible in the record.

### 4.3 AssemblySpec

An assembly records:

- obligation id/version;
- selected parts and versions;
- wiring between typed ports;
- capabilities covered;
- unresolved capability or dependency gaps;
- total cost vector;
- verification result and evidence;
- provenance of the search that produced it.

Assemblies are immutable evidence records. A later improved assembly is a successor record, not an overwrite.

## 5. Typed boundaries

The initial interfaces remain deliberately small:

- `WorldState`
- `Action`
- `Observation`
- `KnowledgeState`
- `MonitorState`
- `PolicyMemory`
- `Carrier`
- `VerificationResult`

These are semantic ports, not concrete Python classes that every part must inherit from. Adapters may map existing representations into them.

The boundaries preserve these distinctions:

```text
physical state != knowledge state
knowledge state != obligation state
obligation state != policy memory
policy memory != schedule phase
representation != represented behavior
implementation equivalence != obligation equivalence
```

## 6. Existing stack as reference assembly

Existing research remains unchanged and is exposed through adapters.

Initial adapters:

- Pass 06 `T4` transition rank -> `transition` + `encode` reference part.
- Pass 07 schedule semigroup / Moore scheduler -> `schedule` + optional `remember` reference parts.
- Pass 08 `POSystem.observations` -> `observe` reference part.
- Pass 08 bit-set belief update -> `infer` reference part.
- Pass 08 `lift_reach` sticky visited flag -> `monitor` reference part.
- Pass 08 `ObservationController` -> `decide` + `remember` reference part.
- Existing exhaustive/native audits -> `verify` reference parts.

Adapters must wrap; they must not rewrite the original Pass 06–08 code or alter its evidence files.

## 7. Catalog and compatibility

The catalog is an append-only registry of `PartSpec` records plus factories/adapters for executable parts.

Compatibility is checked before execution:

1. every requirement is provided;
2. every part dependency is provided;
3. port domains agree;
4. assumptions are satisfied by the obligation bounds;
5. side effects do not violate protected invariants;
6. exact/approximate regimes match;
7. no part silently imports authority from unrelated evidence.

A compatible assembly is only a candidate. Verification remains mandatory.

## 8. Search strategy

The first search engine is intentionally finite and deterministic.

### Phase A — capability cover

Enumerate candidate part sets whose union covers the required capabilities while satisfying declared dependencies.

Because a part can provide multiple capabilities, this is not a one-part-per-role lookup.

### Phase B — wiring and compatibility

Enumerate valid typed wiring among candidate parts. Reject incompatible bounds, missing dependencies, circular construction requirements, and forbidden side effects.

### Phase C — obligation verification

Run the obligation-specific verifier over the full declared finite domain or the explicitly stated bounded sample/proof regime. A candidate that is cheaper but fails the obligation is not retained as a solution.

### Phase D — Pareto frontier

Do **not** collapse cost to one arbitrary scalar by default.

Retain nondominated assemblies across declared dimensions such as:

- controller memory states/bits;
- observation classes or sensor dependency;
- action/probe count;
- temporal steps;
- carrier bytes/bits;
- runtime/work;
- external dependencies;
- verification burden;
- coupling count.

A single winner is selected only when the obligation declares priorities or weights.

## 9. First substitution experiment

Use the existing Pass 08 hidden-mode witness as a regression-quality BOM experiment.

### Baseline assembly

Represent sensing/probing and consequential committing as separate conceptual capabilities/parts.

### Candidate fused assembly

Use a consequential action that also produces diagnostic information. The action provides both `transition` and the information needed by `infer`; no dedicated probe step is required.

### Additional candidate

A temporal-memory construction with minimal or no sensor distinction where applicable.

### Obligation

From every allowed initial hidden world, satisfy the existing reach/safety requirement while preserving all protected behavior and the explicit hidden-mode uncertainty semantics.

### Measurements

Compare:

- success over the complete finite witness domain;
- controller memory bits;
- observation/sensor distinctions required;
- number of consequential steps;
- dedicated probe steps;
- component count;
- coupling count;
- verification work.

Expected regression: the fused diagnostic/consequential action must be admitted and should dominate the artificially separated probe design on at least component/probe count without weakening the obligation. The search must not be hard-coded to that outcome.

## 10. Replacement rule

A replacement is accepted only if:

1. it satisfies the same versioned `ObligationSpec`;
2. protected invariants pass the same or stronger verifier;
3. any changed assumptions are explicit;
4. its cost vector is measured, not inferred from source length alone;
5. provenance and failures are retained;
6. any lost capability is either irrelevant to the obligation or recorded as unresolved remainder.

Therefore “better” means **better under declared obligations and cost dimensions**, not globally superior.

## 11. Failure handling

Failures are first-class outputs:

- `INCOMPATIBLE`: parts cannot be wired under the contract;
- `UNSATISFIED`: assembled behavior violates the obligation;
- `UNRESOLVED`: evidence or dependency is missing;
- `DOMINATED`: valid assembly exists but another verified assembly is no worse in every declared cost dimension and better in at least one;
- `OUT_OF_BOUND`: the candidate exceeds the finite domain or resource contract;
- `VERIFIER_DISAGREEMENT`: independent verification paths differ; no promotion allowed.

No failure state is silently converted to absence or impossibility.

## 12. Evidence and reproducibility

Every retained assembly records:

- source revisions;
- exact obligation/part versions;
- deterministic search ordering;
- commands and software versions;
- scientific output hashes;
- independent/orthogonal verifier where load-bearing;
- failed candidates when they establish a boundary;
- distinction between executed finite results and general mathematical consequences.

Existing Pass 06–08 evidence is referenced, not rewritten.

## 13. Repository layout

Proposed implementation location:

```text
SPrime Search/decision-field/bom/
  README.md
  core.py          # immutable specs and validation
  catalog.py       # append-only part registry
  adapters.py      # wrappers around Pass 06–08 implementations
  search.py        # capability/dependency/wiring enumeration + Pareto frontier
  experiment.py    # first hidden-mode substitution experiment
  audit.py         # independent finite checks
  evidence/
```

Design/specification stays at:

```text
docs/superpowers/specs/2026-09-14-decision-field-bom-design.md
```

## 14. Testing requirements

Before promotion:

1. unit tests for spec validation and canonical ordering;
2. exhaustive small capability-cover oracle against brute-force subsets;
3. dependency-cycle and incompatible-port negative tests;
4. Pareto-frontier oracle against direct pairwise dominance;
5. adapters reproduce the original reference assembly outcomes;
6. hidden-mode substitution experiment exhausts its declared finite world/controller domain;
7. deliberately invalid cheap assemblies are rejected;
8. fused multi-capability part passes without creating implicit capabilities;
9. removing a genuinely required capability causes a witnessed failure;
10. two independent runs produce byte-identical scientific outputs;
11. exact-head CI reruns the BOM audit.

## 15. Non-goals / claim ceiling

This design does not claim:

- a universal decomposition of intelligence or ideas;
- globally optimal architecture search;
- universal semantic equivalence;
- that fewer components is always better;
- that an obligation chosen for one experiment is valid for another;
- that a component's compact encoding is evidence of truth;
- that sensor information and memory are universally interchangeable.

The BOM is a controlled way to search alternative constructions while keeping obligations, evidence, and replacement boundaries explicit.

## 16. Promotion gate

Implementation may begin after this written design is reviewed.

The first implementation milestone is complete when the existing Pass 08 assembly and the fused diagnostic/consequential alternative are both expressible through the same BOM contracts, independently verified, and placed on a declared Pareto frontier without modifying the original Pass 08 scientific artifacts.
