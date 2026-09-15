# S'1 Models — Dimensional Deformation Lab Design

Date: 2026-09-15
Status: DESIGN_APPROVED_IN_CHAT / IMPLEMENTATION_NOT_STARTED
Owner: `redogit/Other-Projects-`
Peer observer/router: `redogit/conscience64`

## Purpose

Build a small, local, playful dimensional-deformation lab that reuses the existing 4D Compass orientation grammar, observer experiments, faithful-transport discipline, and provenance boundaries.

The first objective is not to prove a physical or mathematical conjecture. It is to let people play with a 4D-oriented object, observe 3D deformations under controlled 1° transformations, save exact replayable experiences, and accumulate an inspectable local experience graph.

The lab should make it easy to ask:

- what changed from the original object;
- what changed on the latest move;
- what stayed invariant across observers or shells;
- what was only a projection/reframing effect;
- what new play trajectory differs from prior saved trajectories.

## Existing lineage reused

This design does not invent a new authority stack.

It reuses:

- `Decision Field Operator Lab/` for the exact 4D Compass orientation grammar, bounded operator discipline, and `PROPOSE -> VERIFY -> ADMIT_UNIQUE -> PROMOTE` pattern;
- Conscience64 `research/projects/geometry-codecs.md` for preserved 3D/4D observer lineage and the evidence ceiling `useful geometric representation != physical truth`;
- existing faithful-transport rules for source identity, chronology, provenance, reconstruction, and interpretation separation;
- current federation rules such as `RELATION != MERGE` and `RELATION != EVIDENCE_TRANSFER`.

No existing result is silently promoted by this lab.

## User experience: Observer 0 is play

The first observer is simply the person playing with the object.

The initial interface should prioritize direct manipulation over formulas:

1. drag/rotate the displayed object;
2. apply a controlled 1° move in one declared 4D rotation plane;
3. switch between the smooth and tesseract boundary views;
4. compare live vs mirror deformation;
5. explicitly save an experiment;
6. replay it or reframe the same preserved event through another observer/view.

No formula display is required by default. Technical metrics may exist behind an optional inspection surface.

The system learns from interaction records, not from inferred identity or personality.

## Experiment 0 geometry

The first experiment uses three synchronized views.

### A. Smooth 3D hypersurface in 4D

Use a smooth `S^3`-like enclosing shell around the 4D object.

Purpose:

- expose smooth local stretch;
- curvature change;
- orientation change;
- local volume-element change;
- deformation fields without corners/seams dominating the signal.

### B. Tesseract boundary

Use the 3D boundary of a 4D cube/tesseract, represented as eight connected 3D cubic cells.

Purpose:

- provide a combinatorial and piecewise-linear control;
- make adjacency, seams, corners, and cell identity easier to track;
- challenge signatures that appear only in the smooth representation.

### C. Synchronized comparison view

Apply the same declared 1° transformation to both A and B and compare what survives the change of shell representation.

C is not a third independent geometric object. It is the controlled comparison surface.

## Controlled transformation rule

Experiment 0 changes one degree and one 4D rotational plane at a time.

Initial plane family:

- `xw`
- `yw`
- `zw`

Each move is exactly one declared step:

`delta_theta = 1 degree`

The lab must preserve the exact ordered action sequence so the result can be replayed deterministically.

No multi-plane simultaneous move is required for the initial implementation.

## S'1 model family

The family name is `S'1 Models`.

### `S'1_Mirror`

Immutable control.

Definition:

`M = S_0`

The mirror is never trained, adapted, rewritten, or modified by play.

Its purpose is to preserve a trustworthy local baseline for comparison.

### `S'1_Experience`

Interactive learner.

It does not begin as an ML model. It learns structurally through an append-only local experience graph.

Core loop:

`SAVE -> COMPARE -> PRESERVE DIFFERENCE -> ADD OR REUSE`

The experience layer may recognize:

- repeat;
- variation;
- new branch;
- counterexample.

Those labels describe relation to prior saved trajectories; they are not judgments about the person operating the lab.

### `S'1_Suggest`

Future trained derivative.

Inactive in Experiment 0.

If later enabled, it may learn from preserved `S'1_Experience` records to suggest playful next moves.

It never becomes the source of truth for the experience records and never mutates `S'1_Mirror`.

Governing rule:

`learning never mutates the control`

## Live and mirror comparison

Let:

`L_t = T_t o T_(t-1) o ... o T_1(S_0)`

and:

`M = S_0`.

Two comparisons are preserved:

1. `L_t - M` — total displacement/change from origin;
2. `L_t - L_(t-1)` — change caused by the latest move.

The subtraction symbol here denotes the S'1 difference relation, not ordinary scalar subtraction.

### Same-observer rule

Observer/frame transforms must be applied equally to live and mirror views when producing a visual comparison.

If `O` is the current observer/frame:

`O(L_t)` and `O(M)`

are compared under the same `O`.

This prevents a camera/projection change from being mislabeled as object deformation.

## Replay and reframe models

### `S'1_Replay`

Reconstruct the saved experiment from:

- initial state identity;
- shell identity;
- ordered action sequence;
- observer/frame state;
- operator-semantics version;
- selected checkpoints.

Replay reconstructs the event path. It does not reinterpret or rewrite the event.

### `S'1_Reframe`

Hold the transported event fixed while changing an observer, projection, shell presentation, or declared equivalence/frame.

Core distinction:

`same event != same observation`

and:

`reframe != rewrite`.

A reframe result references the preserved source event rather than replacing it.

## S'1 operator algebra v0

The initial operator family is versioned and mutable by successor version rather than silently redefined.

Version name:

`S'1-Ops v0`

### `A + B` — Join

Place two models into one federated working set while preserving both identities, source trails, chronology, and local authority.

Set-level join may be commutative for membership while chronology remains ordered.

### `A - B` — Difference

Return what is present, changed, or consequential in A relative to B.

Directional.

Neither operand is overwritten.

### `A * B` — Interaction

Run the two models against each other or through the same experiment and record the coupled result.

Ordered by default because `A * B` may differ from `B * A`.

The result must remain replayable and source-linked.

### `A / B` — Reframe / quotient

View A through the equivalence, observer, or frame declared by B.

Directional and partial.

The operation must refuse when the framing/equivalence contract is invalid rather than silently collapsing distinctions.

### `_` — empty / neutral carrier

`S'1_` represents no observation and no claim.

It is distinct from false, zero, absent, and unknown.

## Versioning rule

Operator semantics are versioned:

- `S'1-Ops v0`
- `S'1-Ops v1`
- later successors as needed.

An older saved experiment always retains the operator-semantics version it used.

Later play may motivate new operators or revised semantics, but later versions do not reinterpret old records in place.

Rule:

`play can change the system`

while:

`later meaning does not rewrite earlier experience`.

## Save model

Saving is explicit and local.

There is no automatic hidden history requirement.

A saved experiment contains reconstructible state rather than every rendered frame.

Minimum record:

- record ID;
- schema/version;
- initial object identity;
- immutable mirror identity;
- shell type;
- ordered 1° action sequence;
- current observer/frame state;
- selected checkpoints;
- `S'1-Ops` version;
- comparison result against mirror;
- comparison result against prior step;
- parent/related experience IDs;
- provenance/source references.

Rendered frames may be regenerated from deterministic state where possible.

## Local experience graph

The experience graph is the initial learning core.

Pipeline:

`PLAY -> SAVE -> COMPARE -> CLASSIFY -> GRAPH -> REPLAY/REFRAME`

Classification is local and inspectable:

- exact repeat;
- variation;
- new branch;
- counterexample.

### Repetition rule

Repeated trajectories remain useful as operational history but do not automatically become independent evidence.

`repetition != independent evidence`

A repeated path may reuse an existing graph node with a new occurrence record rather than manufacturing novelty.

A meaningful divergence becomes a linked variation or branch.

## Faithful transport

The lab reuses the existing faithful-transport obligations rather than inventing a new preservation protocol.

Every save must preserve enough information to reconstruct:

- origin;
- chronology;
- state lineage;
- operator version;
- observer/frame;
- provenance;
- interpretation separation.

Derived interpretation remains separate from the transported experience record.

`EXPERIENCE_RECORD != INTERPRETATION`

## Observer model

Experiment 0 requires only the human/play observer plus internal comparison machinery.

Future observer types may include:

- projection observer;
- slice observer;
- metric/deformation observer;
- topology observer;
- sound/sonification observer.

These are not required for the first deployment surface.

No observer is automatically treated as truth authority.

## Hodge and open-problem firewall

The lab may generate visual/geometric candidates, invariants, symmetry hints, or deformation signatures.

It does not by itself establish:

- an algebraic cycle;
- a Hodge class;
- a Hodge-conjecture proof;
- a physical theory;
- a P-vs-NP result.

The valid research route is:

`visual/deformation signature -> candidate mathematical structure -> exact representation -> independent mathematical test -> bounded evidence state`

Never:

`interesting image -> conjecture solved`.

Also preserve:

`real 4D != complex dimension 4`.

## Privacy and human boundaries

The initial learner uses interaction records only.

It must not infer or store hidden claims about:

- identity;
- health;
- personality;
- politics;
- protected traits;
- psychological profile.

Local history should be visible, exportable, clearable, and saveable only by explicit action.

## Accessibility

The initial interface should be usable without requiring precise pointer input.

Minimum requirements:

- keyboard-equivalent 1° controls;
- visible focus;
- reduced-motion option;
- text labels for shell, plane, move count, mirror/live state, and save/replay controls;
- no reliance on color alone for live-vs-mirror comparison;
- numerical/text inspection route for users who cannot use the 3D view effectively.

Rendered 3D usability and assistive-technology acceptance remain separate validation tasks.

## Failure handling

Fail closed on:

- unknown operator-semantics version;
- malformed action sequence;
- incompatible shell/state version;
- missing source identity required for replay;
- invalid reframe/equivalence contract;
- non-finite transform inputs;
- corrupted local save.

A failed replay must not silently approximate the original event.

The system may offer a clearly labeled best-effort visualization only as a separate reconstruction attempt, never as the original replay.

## Testing strategy

Implementation should include at least:

1. deterministic replay tests from exact saved action sequences;
2. mirror immutability tests;
3. same-observer tests proving frame changes affect live and mirror equally before comparison;
4. one-step vs origin comparison tests;
5. smooth-shell and tesseract-boundary test fixtures;
6. exact-repeat graph classification tests;
7. variation/new-branch/counterexample classification fixtures;
8. operator-version migration/rejection tests;
9. corrupted-save rejection tests;
10. accessibility-oriented keyboard and reduced-motion checks;
11. explicit Hodge/open-problem claim-ceiling checks in docs/UI text.

A passing software suite establishes implementation behavior only.

`SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION`

## Deployment and repository boundaries

Implementation home: `redogit/Other-Projects-`.

Conscience64 may link to or observe the lab after the implementation earns its own bounded verification.

The bridge relation should remain navigation/observation only unless a separate Conscience64 admission process says otherwise.

No Conscience64 research registry, world canon, game authority, or evidence ledger is modified by this design.

## Initial implementation slice

The smallest useful implementation should contain only:

- one local browser surface;
- one 4D-oriented object representation;
- smooth `S^3`-like shell view;
- tesseract-boundary view;
- synchronized comparison view;
- 1° `xw`, `yw`, `zw` moves;
- immutable mirror;
- live object;
- explicit local save;
- append-only local experience graph;
- deterministic replay;
- reframe using current supported shell/observer choices;
- `S'1-Ops v0` metadata.

Not in the first implementation:

- ML training;
- next-move suggestions;
- remote multi-user service;
- cloud history;
- automatic evidence promotion;
- Hodge-specific cycle generation;
- physics claims;
- sound observer.

## Success criteria for Experiment 0

A person can:

1. open the lab locally;
2. play with the object without needing the mathematical formalism;
3. apply 1° moves one at a time;
4. switch/compare smooth and tesseract shells;
5. see live vs mirror deformation under the same observer;
6. save an experiment locally;
7. replay it deterministically;
8. reframe the same preserved event without rewriting it;
9. see whether the new save is a repeat, variation, branch, or counterexample relative to local history;
10. clear/export local history explicitly.

The lab is successful as software when those behaviors work reproducibly. Any deeper mathematical/scientific interpretation remains a separate research claim with its own evidence obligations.
