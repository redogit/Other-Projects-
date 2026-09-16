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
