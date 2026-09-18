# S'1 Rigor Layer and Carrier/Ops v1 Design

**Date:** 2026-09-18  
**Repository:** `redogit/Other-Projects-`  
**Baseline:** `main@889d9e4fb3b8e45815f302197e0fb7146e03ce23`

## Purpose

Extend the merged S'1 Models Lab with an independent quantitative verification layer and a successor closed carrier/operator representation while preserving every v0 contract and scientific claim ceiling.

The rigor layer is verification machinery. It must not silently become the production transform kernel, observer authority, physical model, or open-problem evidence.

## Governing boundaries

- `SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION`
- `FLOATING_POINT_RESIDUAL != MATHEMATICAL_COUNTEREXAMPLE`
- `FINITE_EXHAUSTIVE_SWEEP != UNBOUNDED_PROOF`
- `PROJECTION_CONDITIONING != OBJECT_PROPERTY`
- `HASH_EQUALITY != PAYLOAD_EQUALITY`
- `OPERATOR_RESULT != SCIENTIFIC_EVIDENCE`
- `real 4D != complex dimension 4`
- Hodge and P-vs-NP remain open.
- Existing `S'1-Ops v0`, `S'1_Experience`, `S'1_Suggest`, UI, dimensional-ladder, image-surface, and observer-extension semantics remain unchanged unless a new failing test demonstrates a defect in their shared kernel assumptions.

## Architecture

### 1. Independent binary64 matrix oracle

Create `S1 Models Lab/rigor.mjs`.

The module independently represents each legal one-degree `xw`, `yw`, and `zw` move as a 4x4 rotation matrix. It composes matrices without calling `applyMove` or `rotatePoint4`. Shared use of JavaScript binary64 `Math.sin`/`Math.cos` constants is documented; the oracle is implementation-independent at the composition/application level, not an independent transcendental library.

It exposes:

- `rotationMatrix4(plane, degrees)`
- `multiplyMatrix4(left, right)`
- `applyMatrix4(matrix, point)`
- `composeActionMatrix(actions)`
- `matrixInvariantMetrics(matrix)`
- `exhaustiveRotationSweep(maxDepth = 8)`
- `longHorizonRotationProbe(...)`
- `binary64AccumulationBudget(operationCount)`

Metrics include maximum `R^T R - I` residual, determinant residual from +1, and point norm residual.

The declared exhaustive finite corpus is all six legal move choices over path lengths 0..8:

[
\sum_{k=0}^{8} 6^k = 2,015,539.
]

### 2. Observer conditioning report

The rigor module exposes `observerConditionReport(point, observer)` without changing `projectPoint4`.

For the current contract:

[
w_b = \max(-0.9,w), \quad d = 1+p w_b, \quad s = d^{-1}, \quad 0 \le p < 1.
]

The report records:

- whether the negative-w clamp fired;
- denominator and scale;
- the contract-level exclusive denominator floor `0.1`;
- local scale sensitivity `p / d^2` when `w >= -0.9`;
- `0` local sensitivity below the clamp because the implemented mapping is constant there;
- a discontinuity/nondifferentiability flag at the clamp boundary;
- an explicit `informationLoss: true` when `w < -0.9`.

No conditioning quantity is promoted to a property of the modeled object.

### 3. Absolute + relative comparison

Preserve `compareStates` v0 unchanged. Add `compareStatesQuantified(a,b,{absTolerance,relTolerance})` in `rigor.mjs`.

For each coordinate:

[
|a-b| \le \text{absTol} + \text{relTol}\max(|a|,|b|).
]

Return maximum absolute delta, maximum normalized error ratio, and equality under the combined rule. This is a verification comparator, not a replacement serialized contract.

### 4. Digest collision sentinel

Add `replayDescriptor(record)` to `experience.mjs` and redefine `replayIdentity(record)` as FNV-1a-64 of that exact canonical descriptor, preserving current IDs for the same payload.

Add `S1 Models Lab/integrity.mjs` with a generic `guardDigestCollision(index,digest,canonical,label)` function. The function fails closed if an already-seen digest is associated with a different canonical payload.

`LocalExperienceStore` uses both replay digest and canonical replay descriptor. A digest match is mergeable only when the canonical descriptors also match.

This does not claim FNV-1a-64 is cryptographically collision resistant. It converts a hash collision from silent conflation into an explicit integrity failure whenever both colliding payloads are observed.

### 5. Carrier/Ops v1 recursive closure

Create `S1 Models Lab/carrier-v1.mjs`. v0 remains unchanged.

A v1 carrier is an immutable typed node:

- neutral carrier;
- experience leaf carrier;
- observer-frame leaf carrier;
- operation carrier.

All v1 structural operators accept v1 carriers and return v1 carriers, so results can be inputs to later operations.

Required operations:

- `joinCarriers(A,B)`: neutral-eliding, nested-join-flattening ordered join; preserves ordered chronology and unique sorted membership. Parenthesization does not change a three-term join with the same chronological order.
- `differenceCarriers(A,B)`: directional closed node.
- `interactCarriers(A,B)`: ordered closed node.
- `quotientCarrier(A,frame)`: closed structural reframe node using a validated observer-frame carrier.

The v1 carrier ID remains a compact FNV-1a-64 content digest for continuity, but every node also carries its canonical descriptor and creation uses collision guards when a registry is supplied. Hash equality alone never establishes semantic equality.

No v1 operator is claimed to form a group, field, ring, or complete algebra. The verified claims are restricted to the explicitly tested laws: closure, deterministic reconstruction, neutral behavior for join, join parenthesization normalization, and directional/ordered distinction.

### 6. Audit and evidence

Extend `audit.mjs` with a `rigor` section rather than altering the historical Experiment 0 evidence artifact.

Add `S1 Models Lab/evidence/RIGOR_V1_SUMMARY.json` only after an exact implementation checkpoint and exact-head CI run exist. The evidence file pins the implementation SHA, workflow run, finite sweep counts, measured maxima, and claim boundaries.

The existing `EXPERIMENT_0_SUMMARY.json` remains frozen historical evidence.

### 7. CI

The existing `S1 Models Check` already checks the true PR head. Keep that mechanism.

CI must execute:

1. full Node test suite;
2. browser smoke;
3. deterministic audit twice and byte-compare;
4. explicit rigor checks including the depth-8 corpus;
5. claim-ceiling checks.

The depth-8 exhaustive sweep is matrix-only to keep CI bounded and deterministic.

## Acceptance criteria

The branch is acceptable only when all are true:

1. Baseline v0 tests still pass.
2. Matrix oracle agrees with the production kernel on representative and generated bounded paths within calculated binary64 tolerances.
3. All 2,015,539 paths through depth 8 are visited exactly once by the declared traversal.
4. Every visited matrix remains inside the declared orthogonality and determinant residual budgets.
5. Long-horizon same-plane and mixed inverse probes remain inside calculation-derived binary64 budgets.
6. Observer conditioning reports the clamp information-loss boundary and proves the current valid-domain denominator stays above 0.1.
7. Storage collision handling fails closed under a forced-digest unit test and preserves normal deduplication behavior.
8. Carrier/Ops v1 accepts prior operation results as operands and passes its declared structural laws.
9. Audit output is deterministic.
10. Exact PR-head GitHub Actions is green.
11. Evidence text explicitly prevents scientific/open-problem promotion.
