# S'1 Models Lab — Experiment 0

A local, dependency-free browser playground for controlled one-degree 4D transformations, live-vs-mirror comparison, explicit local experience saves, deterministic replay/reframe, a distributed point-observer field, and a bounded local suggestion carrier.

## Core models

- `S'1_Mirror` — immutable control.
- `S'1_Experience` — append-only local experience learner; not ML.
- `S'1_ObserverField` — every sampled compass/reference point is an observer with exactly one task and one repairable calibration degree.
- `S'1_Suggest` — explicit derived-dataset transition model that can propose an optional next move without mutating `S'1_Mirror` or becoming authority over `S'1_Experience`.

The smooth S3-like and tesseract-boundary displays are a **synthetic observer/reference surface** system. They are controlled visualization/reference mappings, not claims that the modeled object physically deforms spacetime.

`SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION`

`real 4D != complex dimension 4`

`OBSERVATIONAL_REPAIR != OBJECT_REPAIR`

`FEATURE_AT_ONE_MESH != CONTINUUM_INVARIANT`

`SUGGESTION != EXPERIENCE_AUTHORITY`

Hodge and P-vs-NP remain open. No visual deformation, suggestion, or software result promotes an open-problem claim.

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

## S'1 Suggest transition carrier

`suggest.mjs` derives a versioned local dataset only from validated `S'1_Experience` records. Replay-equivalent records are collapsed before model construction, so repeated occurrences or provenance-only differences do not become independent support.

The model maps an exact replay-context contract plus action prefix to preserved next moves. That context includes initial object identity, immutable mirror identity, shell, normalized observer frame, operator version, and the ordered action prefix. A continuation observed under a different shell or observer frame therefore cannot be mislabeled as observed in the current frame. If an exact preserved continuation exists, the result is marked `observed` and carries the source experience IDs. If no exact continuation exists, a deterministic legal-move fallback is marked `generated` with an empty source-experience list. Both are wrapped in `s1-transition-carrier/v0` with explicit dataset/model provenance and `authority: "suggestion-only"`.

The suggestion carrier is intentionally narrower than the experience record while preserving the distinctions required to reconstruct its meaning: exact transformation/view contract, action prefix, candidate move, derivation provenance, observed/generated status, and authority boundary. It does not infer identity, personality, health, politics, or protected traits from play history; it never writes to the experience graph automatically; and suggestion use/popularity is not scientific validation.

## Saved-record minimum and teach-back separation

Every v0 experience record explicitly carries selected checkpoint indices, both live-vs-mirror and latest-step comparison summaries, parent/related IDs, observer state, observer-field state, operator version, and provenance. Repeat classification/deduplication uses replay identity rather than incidental provenance metadata.

The optional teach-back text box is deliberately outside `S'1_Experience`: a person can describe an observation in their own words, but Experiment 0 neither saves that text nor promotes it to evidence authority.


## Quantified rigor layer v1

`rigor.mjs` is an independent composition/application verification sidecar for the shared one-degree rotation and observer contracts. It does not replace `core.mjs`; it checks that implementation from a separately composed 4×4 matrix path. Both paths use JavaScript's binary64 `Math.sin`/`Math.cos` primitives, so this is **not** an independent transcendental-function oracle.

The declared finite rotation sweep now enumerates every six-way legal move history through depth 8:

```text
1 + 6 + 6^2 + ... + 6^8 = 2,015,539 paths
```

For each matrix it measures `R^T R - I`, determinant residual from +1, and column-norm residual. Long-horizon probes separately measure repeated same-plane rotation and a deterministic mixed forward/inverse trajectory. Their acceptance ceilings are derived from the standard binary64 `gamma_k = ku/(1-ku)` accumulation scale with `u = Number.EPSILON / 2`; the measured residual remains evidence about this implementation and corpus, not a proof over arbitrary trajectories.

The observer-conditioning report makes the implemented clamp explicit. With `w_b = max(-0.9,w)`, `0 <= p < 1`, and `d = 1 + p*w_b`, every valid observer has `d > 0.1`. Values with `w < -0.9` are mapped to the same perspective denominator, so the report marks that region as information-losing rather than pretending it is uniquely reconstructible.

`compareStatesQuantified` adds an audit-only absolute-plus-relative tolerance rule without changing the serialized v0 comparator contract.

## Digest integrity boundary

Replay identity remains the same compact FNV-1a-64 digest of the same canonical replay payload, preserving v0 identity compatibility. The canonical replay preimage is now separately exposed by `replayDescriptor`.

Storage coalescing records both digest and canonical descriptor. Equal digest + equal descriptor may coalesce; equal digest + unequal descriptor fails closed as an integrity error.

`HASH_EQUALITY != PAYLOAD_EQUALITY`

FNV-1a-64 is retained for compatibility and compact deterministic IDs. It is not represented as cryptographic collision resistance.

## S'1 Carrier/Ops v1

`carrier-v1.mjs` is a separately versioned recursive carrier representation. Unlike `S'1-Ops v0`, v1 operation results are themselves valid operands.

Verified structural contracts include:

- experience and observer-frame leaf carriers;
- explicit neutral carrier;
- neutral-eliding, nested-join-flattening ordered join;
- parenthesization normalization for same-order joins;
- unique sorted membership with preserved chronology;
- closed directional difference;
- closed ordered interaction;
- closed structural quotient through an observer-frame carrier;
- deterministic canonical descriptors and compact content IDs;
- source immutability and validation against descriptor/ID tampering.

These verified closure properties do **not** assert that Carrier/Ops v1 is a group, ring, field, or complete algebra.

## Rigor claim boundaries

`SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION`

`FINITE_EXHAUSTIVE_SWEEP != UNBOUNDED_PROOF`

`FLOATING_POINT_RESIDUAL != MATHEMATICAL_COUNTEREXAMPLE`

`PROJECTION_CONDITIONING != OBJECT_PROPERTY`

`HASH_EQUALITY != PAYLOAD_EQUALITY`

`OPERATOR_RESULT != SCIENTIFIC_EVIDENCE`

`SHARED_TRIG_PRIMITIVE != INDEPENDENT_TRANSCENDENTAL_ORACLE`

The Experiment 0 frozen evidence remains historical and unchanged. Rigor v1 receives its own successor evidence record after an exact-head implementation checkpoint passes CI.
