# Decision-Field Bill of Materials — Design

Date: 2026-09-14  
Status: reviewed design; implementation gated on review of this written specification  
Scope: `redogit/Other-Projects-`, SPrime decision-field research

## 1. Purpose

Treat the existing SPrime/decision-field stack as one proven **assembly**, not as the definition of the system.

The BOM should answer:

1. What operational capabilities are required by a declared obligation?
2. Which available parts intrinsically provide those capabilities?
3. Which useful properties emerge only after several parts are composed?
4. Can one part replace several old parts, or several better-bounded parts replace one old part?
5. Can a different verified assembly preserve the same obligation with lower declared cost, less coupling, stronger evidence, or greater reuse?
6. Which distinctions remain unresolved after substitution?

The design preserves the evidence boundaries of Passes 06–08. A replacement that passes one obligation is not thereby universally equivalent to the part it replaced.

## 2. Design decision: capability-based BOM, not role-per-component

A fixed role-to-component mapping is rejected.

The Pass 08 hidden-mode witness demonstrates why: an action can be both **consequential** and **diagnostic in composition**. Requiring a separate sensor/probe component would bake an already-refuted architectural assumption into the BOM.

Therefore:

- an **obligation** declares required operational capabilities and protected consequences;
- a **part** may intrinsically provide one or many capabilities;
- a **part** may require capabilities from other parts;
- an **assembly** is a compatible set of parts whose intrinsic capabilities cover the operational requirements;
- useful information or other properties that appear only after composition are recorded as **emergent effects**, not falsely assigned to one component;
- the obligation-specific verifier decides whether the composed assembly actually works.

This permits like-for-like substitution, fusion of several old parts into one, decomposition of one old part into several better-bounded parts, and discovery of useful interactions between parts.

## 3. Two planes: operational assembly and evidence/transport sidecars

The self-review rejects placing verification machinery inside the runtime BOM by default.

### Operational capabilities

| Capability | Contract |
|---|---|
| `transition` | Given hidden/world state and action/context, produce the next hidden/world state. |
| `observe` | Produce an observation/event made available at a declared point in the step cycle. |
| `infer` | Update a knowledge carrier from prior knowledge plus declared action/observation history. |
| `monitor` | Carry obligation history that is not recoverable from current physical state alone. |
| `decide` | Select an action/context from information available to the policy. |
| `remember` | Carry policy state that is not part of the physical world or obligation monitor. |
| `schedule` | Generate or constrain context/action sequences over time. |

### Evidence/transport sidecars

| Sidecar | Contract |
|---|---|
| `encode` | Give an exact transport/identity representation to a declared object when transport is part of the obligation. |
| `verify` | Independently test the obligation, finite boundary, and evidence claim. It never certifies itself by being present in the runtime assembly. |

An obligation may explicitly require transport, but verification remains external assurance rather than a runtime capability that can satisfy its own evidence requirement.

The vocabulary is extensible only when a witnessed obligation cannot be represented cleanly using the current terms.

## 4. Intrinsic capability versus emergent effect

A part may claim only what its own interface provides.

For example, a consequential action does **not** automatically claim `infer` merely because choosing it can reveal hidden state. Diagnostic value may emerge from:

```text
action primitive
+ transition dynamics
+ observation model
+ knowledge update
```

The assembly verifier may then record an effect such as:

```text
DISTINGUISHES(hidden_mode_A, hidden_mode_B) under declared observation contract
```

Search may use previously verified emergent-effect certificates as evidence, but it may not assume an effect solely from a component name or source-code shape.

This distinction prevents the BOM from replacing architectural dogma with capability-label dogma.

## 5. Core records

### 5.1 ObligationSpec

An obligation is the authority for replacement.

Required fields:

- stable id and version;
- subject/domain and finite bounds;
- allowed initial states/worlds;
- allowed actions/contexts;
- protected invariants;
- success condition;
- required operational capabilities;
- observable information and permissions;
- temporal semantics, including whether intermediate trajectories matter;
- step timing: what is known before action, after transition, and after observation;
- exact/approximate regime;
- evidence threshold;
- unresolved remainder;
- cost dimensions that may be compared.

Examples include sure safety, sure reachability with an explicit monitor, exact reconstruction, or exact final-state equivalence. No generic `success=True` may substitute for the obligation-specific verifier.

### 5.2 PartSpec

A part is an implementation candidate, not an architectural truth.

Required fields:

- stable id/version;
- `provides`: intrinsic operational capability set;
- `requires`: operational capability set;
- typed input/output ports;
- phase/timing of each port;
- state carried by the part;
- assumptions and finite bounds;
- side effects;
- external dependencies;
- measurable cost vector;
- evidence references;
- known failure modes;
- replaceability boundary.

A part may provide multiple capabilities. Such fusion is allowed but its coupling and common failure boundary must be visible.

### 5.3 SidecarSpec

Evidence/transport machinery records:

- sidecar type (`encode` or `verify` initially);
- object/obligation version it applies to;
- exact input/output contract;
- assumptions and finite bounds;
- provenance;
- independent or orthogonal evidence status;
- known limitations.

### 5.4 AssemblySpec

An assembly records:

- obligation id/version;
- selected parts and versions;
- runtime wiring between typed ports;
- capabilities covered;
- verified emergent effects;
- unresolved capability/dependency/effect gaps;
- total cost vector;
- verification result and sidecars;
- provenance of the search that produced it.

Assemblies are immutable evidence records. A later improved assembly is a successor record, not an overwrite.

## 6. Typed runtime boundaries and step phases

The initial semantic ports are:

- `WorldState`
- `Action`
- `Observation`
- `KnowledgeState`
- `MonitorState`
- `PolicyMemory`
- `ScheduleState`
- `VerificationResult` (evidence plane only)
- `Carrier` (transport sidecar only unless explicitly required by the obligation)

Adapters may map existing representations into these ports; consumers need not inherit concrete Python base classes.

The default deterministic step order is explicit:

```text
knowledge + monitor + policy memory + schedule state
                    ↓
                 decide
                    ↓
                 action
                    ↓
                transition
                    ↓
             post-action world
                    ↓
                 observe
                    ↓
        infer / monitor / memory updates
                    ↓
             next decision state
```

An obligation may define a different phase order, but the order must be explicit before parts are wired.

The boundaries preserve:

```text
physical state != knowledge state
knowledge state != obligation state
obligation state != policy memory
policy memory != schedule phase
representation != represented behavior
intrinsic capability != emergent effect
implementation equivalence != obligation equivalence
```

## 7. Dependency cycles versus runtime feedback

Build-time dependency cycles are rejected when no part can be constructed without another unavailable part.

Runtime feedback is expected and allowed: policy affects action, action affects world, world affects observation, observation affects knowledge, and knowledge affects the next policy decision.

Therefore the compatibility checker distinguishes:

- **construction dependency graph** — must be resolvable;
- **runtime signal graph** — may contain declared temporal feedback edges.

A cycle is never rejected merely because a controller operates in a loop over time.

## 8. Existing stack as reference assembly

Existing research remains unchanged and is exposed through adapters.

Initial adapters:

- Pass 06 `T4` transition rank -> `transition` reference part, with existing codec as transport sidecar.
- Pass 07 schedule semigroup / Moore scheduler -> `schedule` + optional `remember` reference parts.
- Pass 08 `POSystem.observations` -> `observe` reference part.
- Pass 08 bit-set belief update -> `infer` reference part.
- Pass 08 `lift_reach` sticky visited flag -> `monitor` reference part.
- Pass 08 `ObservationController` -> `decide` + `remember` reference part.
- Existing exhaustive/native audits -> verifier sidecars.

Adapters must wrap; they must not rewrite the original Pass 06–08 code or alter its scientific evidence files.

## 9. Catalog and compatibility

The catalog is an append-only registry of `PartSpec` and `SidecarSpec` records plus executable factories/adapters.

Compatibility is checked before execution:

1. every required operational capability is intrinsically provided;
2. every construction dependency is provided;
3. typed port domains agree;
4. phase/timing contracts agree;
5. assumptions are satisfied by the obligation bounds;
6. side effects do not violate protected invariants;
7. exact/approximate regimes match;
8. construction dependencies are resolvable;
9. runtime feedback edges are explicitly phased;
10. no part or sidecar silently imports authority from unrelated evidence.

A compatible assembly is only a candidate. Verification remains mandatory.

## 10. Search strategy

The first search engine is finite and deterministic.

### Phase A — intrinsic capability cover

Enumerate candidate part sets whose intrinsic capabilities cover the operational requirement set while satisfying construction dependencies.

Because a part can provide several capabilities, this is not a one-part-per-role lookup.

### Phase B — wiring and compatibility

Enumerate valid typed and phased wiring. Reject incompatible bounds, missing dependencies, unresolved construction cycles, invalid phase order, and forbidden side effects.

### Phase C — obligation verification and emergent-effect discovery

Run the obligation-specific verifier over the full declared finite domain or the explicitly stated bounded sample/proof regime.

Record verified assembly-level effects, including diagnostic distinctions, reachable states, obligation-monitor behavior, and trajectory-sensitive consequences.

A candidate that is cheaper but fails the obligation is not retained as a solution.

### Phase D — Pareto frontier

Do **not** collapse cost to one arbitrary scalar by default.

Retain nondominated assemblies across declared dimensions such as:

- controller memory states/bits;
- observation classes or sensor dependency;
- action count;
- dedicated probe count;
- temporal steps;
- carrier bytes/bits where transport is relevant;
- runtime/work;
- external dependencies;
- verification burden;
- part count;
- coupling/failure-domain count.

A single winner is selected only when the obligation declares priorities or weights.

## 11. First substitution experiment

Use the Pass 08 hidden-mode witness as a regression-quality BOM experiment.

The experiment compares three candidate assemblies under the same versioned obligation.

### Candidate A — synthetic separated-probe assembly

Construct an explicit experimental baseline in which one step is dedicated to information acquisition before a consequential commit. This is a **new synthetic comparator**, not a claim that historical Pass 08 used a dedicated probe.

### Candidate B — consequential/diagnostic composition

Use the existing hidden-mode transition/observation structure in which a consequential action can also make hidden mode distinguishable through the subsequent observation/history. Diagnostic power is recorded as an emergent assembly effect, not as an intrinsic `infer` capability of the action itself.

### Candidate C — temporal-memory alternative

Test whether temporal memory can replace some observation distinction or dedicated sensing while preserving the same obligation.

### Obligation

From every allowed initial hidden world, satisfy the existing reach/safety requirement while preserving protected behavior, hidden-mode uncertainty semantics, and any declared trajectory constraints.

### Measurements

Compare:

- success over the complete finite witness domain;
- controller memory bits;
- observation/sensor distinctions required;
- consequential steps;
- dedicated probe steps;
- part count;
- coupling/failure-domain count;
- verification work.

Expected regression: Candidate B must be discoverable by the search and should dominate the artificially separated probe comparator on at least dedicated-probe/part dimensions without weakening the obligation. The search must not be hard-coded to that outcome.

## 12. Replacement rule

A replacement is accepted only if:

1. it satisfies the same versioned `ObligationSpec`;
2. protected invariants pass the same or stronger verifier;
3. any changed assumptions are explicit;
4. its cost vector is measured rather than inferred from source length alone;
5. provenance and failures are retained;
6. any lost capability or emergent property is irrelevant to the obligation or recorded as unresolved remainder;
7. trajectory-sensitive obligations are not replaced using final-state-only equivalence.

Therefore “better” means **better under declared obligations and cost dimensions**, not globally superior.

## 13. Failure handling

Failures are first-class outputs:

- `INCOMPATIBLE`: parts cannot be wired under the contract;
- `UNSATISFIED`: assembled behavior violates the obligation;
- `UNRESOLVED`: evidence, dependency, or emergent-effect status is missing;
- `DOMINATED`: another verified assembly is no worse in every declared cost dimension and better in at least one;
- `OUT_OF_BOUND`: candidate exceeds the finite domain or resource contract;
- `VERIFIER_DISAGREEMENT`: independent verification paths differ; no promotion allowed.

No failure is silently converted to absence or impossibility.

## 14. Evidence and reproducibility

Every retained assembly records:

- source revisions;
- exact obligation/part/sidecar versions;
- deterministic search ordering;
- commands and software versions;
- scientific output hashes;
- independent/orthogonal verifier where load-bearing;
- failed candidates when they establish a boundary;
- distinction between executed finite results and general mathematical consequences.

Existing Pass 06–08 evidence is referenced, not rewritten.

## 15. Repository layout

Implementation location:

```text
SPrime Search/decision-field/bom/
  README.md
  core.py          # immutable specs, ports, phases, validation
  catalog.py       # append-only part/sidecar registry
  adapters.py      # wrappers around Pass 06–08 implementations
  search.py        # cover/dependency/wiring enumeration + Pareto frontier
  experiment.py    # first hidden-mode substitution experiment
  audit.py         # independent finite checks
  evidence/
```

Design specification:

```text
docs/superpowers/specs/2026-09-14-decision-field-bom-design.md
```

## 16. Testing requirements

Before promotion:

1. unit tests for immutable spec validation and canonical ordering;
2. exhaustive small capability-cover oracle against brute-force subsets;
3. construction-dependency-cycle negative tests while allowing declared runtime feedback;
4. incompatible-port and invalid-phase-order negative tests;
5. Pareto-frontier oracle against direct pairwise dominance;
6. adapters reproduce original reference-assembly outcomes;
7. hidden-mode substitution experiment exhausts its declared finite world/controller domain;
8. deliberately invalid cheap assemblies are rejected;
9. fused multi-capability parts pass without acquiring undeclared intrinsic capabilities;
10. emergent diagnostic effects require verifier evidence;
11. removing a genuinely required capability causes a witnessed failure;
12. final-map-equivalent but trajectory-different assemblies remain distinct when the obligation is trajectory-sensitive;
13. two independent runs produce byte-identical scientific outputs;
14. exact-head CI reruns the BOM audit.

## 17. Non-goals / claim ceiling

This design does not claim:

- a universal decomposition of intelligence or ideas;
- globally optimal architecture search;
- universal semantic equivalence;
- that fewer parts is always better;
- that an obligation chosen for one experiment is valid for another;
- that compact encoding is evidence of truth;
- that sensor information and memory are universally interchangeable;
- that assembly-level diagnostic information belongs intrinsically to one action component.

The BOM is a controlled way to search alternative constructions while keeping obligations, evidence, emergent effects, and replacement boundaries explicit.

## 18. Promotion gate

Implementation may begin after this written design is reviewed.

The first implementation milestone is complete when:

1. the existing Pass 08 assembly is expressible through adapters without modifying its scientific artifacts;
2. the synthetic separated-probe comparator and the consequential/diagnostic composition are expressible under the same obligation;
3. their intrinsic capabilities and emergent effects remain distinct;
4. both are independently verified over the declared finite domain;
5. verified assemblies are placed on a declared Pareto frontier;
6. exact-head CI reproduces the BOM audit.
