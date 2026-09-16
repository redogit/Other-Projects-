# S'1 Models Lab — Experiment 0

A local, dependency-free browser playground for controlled one-degree 4D transformations, live-vs-mirror comparison, explicit local experience saves, deterministic replay/reframe, and a distributed point-observer field.

## Core models

- `S'1_Mirror` — immutable control.
- `S'1_Experience` — append-only local experience learner; not ML.
- `S'1_ObserverField` — every sampled compass/reference point is an observer with exactly one task and one repairable calibration degree.
- `S'1_Suggest` — inactive in Experiment 0.

The smooth S3-like and tesseract-boundary displays are a **synthetic observer/reference surface** system. They are controlled visualization/reference mappings, not claims that the modeled object physically deforms spacetime.

`SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION`

`real 4D != complex dimension 4`

`OBSERVATIONAL_REPAIR != OBJECT_REPAIR`

`FEATURE_AT_ONE_MESH != CONTINUUM_INVARIANT`

Hodge and P-vs-NP remain open. No visual deformation or software result promotes an open-problem claim.

## Run

```bash
cd "S1 Models Lab"
npm test
node audit.mjs --source-revision "$(git rev-parse HEAD)" --out /tmp/s1-audit.json
python -m http.server 8000 --bind 127.0.0.1
```

Open `/S1%20Models%20Lab/`. The app requires no account and performs no hidden telemetry. Saving occurs only when the user activates **Save**. Local history is visible, exportable, importable with fail-closed validation, and clearable.

Keyboard moves outside form controls: `Q/A` = xw ±1°, `W/S` = yw ±1°, `E/D` = zw ±1°. Pointer and keyboard routes invoke the same move contract.

## Verification scope

The audit exercises mirror immutability, exact replay against direct application, same-observer projection, S3 radius residual, all eight tesseract boundary cells, graph repeat/branch/variation classification, and corrupt-import rejection. It reports deterministic software observations only; it does not establish continuum completeness, physical truth, accessibility certification, or any result about Hodge or P-vs-NP.

The bounded possibility sweep covers all six legal ±1° moves and every legal move sequence through depth 3 (259 paths including the empty path), plus representative invalid-move, observer-boundary, record-authority, and malformed-history cases. This is exhaustive only for that declared finite corpus; arbitrary-length trajectories remain an unbounded state space.


## S'1 operator algebra v0

`operators.mjs` implements the separately testable `S'1-Ops v0` contracts without redefining ordinary arithmetic:

- `joinModels(A, B)` (`A + B`) creates a federated working set with commutative membership, ordered chronology, preserved source IDs, and local provenance authority.
- `differenceModels(A, B)` (`A - B`) emits a directional structural difference without mutating either source.
- `interactModels(A, B)` (`A * B`) records an ordered, deterministic, source-linked coupling using the v0 structural-directional interaction contract.
- `quotientModel(A, frame, registry)` (`A / B`) reframes a preserved experience through an explicit validated observer frame and refuses unsupported frame contracts.
- `S1_NEUTRAL` (`S'1_`) is an explicit no-observation/no-claim carrier distinct from false, zero, null, undefined, and unknown.

Operator results are versioned records. Later operator semantics require a successor version; saved v0 experience records retain `S'1-Ops v0`.

## Saved-record minimum and teach-back separation

Every v0 experience record explicitly carries selected checkpoint indices, both live-vs-mirror and latest-step comparison summaries, parent/related IDs, observer state, observer-field state, operator version, and provenance. Repeat classification/deduplication uses replay identity rather than incidental provenance metadata.

The optional teach-back text box is deliberately outside `S'1_Experience`: a person can describe an observation in their own words, but Experiment 0 neither saves that text nor promotes it to evidence authority.
