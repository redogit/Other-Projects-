# S'1 Observer Field Addendum Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. This addendum modifies the parent Experiment 0 plan before production code begins.

**Goal:** Make every sampled 3D/4D compass/reference point a deterministic point observer with exactly one observation task and exactly one repairable calibration degree, while preserving live/mirror/source-state immutability.

**Architecture:** Extend the parent plan with a pure `observer-field.mjs` module between geometry generation and rendering/experience. Point observers are deterministic derived records. Their one-DOF repairs mutate only derived observer calibration records, never source geometry, live state, mirror state, or event history.

**Tech Stack:** Same as parent plan: dependency-free ES2023 modules, Node 22 `node:test`, Canvas2D UI.

**Specs:**
- `docs/superpowers/specs/2026-09-15-s1-models-dimensional-deformation-lab-design.md`
- `docs/superpowers/specs/2026-09-15-s1-observer-field-addendum.md`

## Parent-plan changes

The parent plan remains authoritative except where this addendum explicitly changes it.

1. Task 4 no longer represents the entire observer model. `observer.mjs` remains the shared global visualization frame/projection contract.
2. Add `observer-field.mjs` after geometry and before experience/rendering.
3. Saved experience records include observer-field version, density, task-assignment version, and calibration state.
4. UI exposes observer/task inspection without requiring users to inspect every point.
5. Audit includes observer-field invariants.

## Files added/extended

```text
S1 Models Lab/
├── observer-field.mjs
└── tests/
    └── observer-field.test.mjs
```

Modify later parent-plan files:

- `experience.mjs`
- `schema/s1-experience-v0.schema.json`
- `render.mjs`
- `app.mjs`
- `audit.mjs`
- `README.md`
- `tests/experience.test.mjs`
- `tests/ui-contract.test.mjs`
- `tests/audit.test.mjs`

---

### Addendum Task A: Define point observers and deterministic one-task assignment

**Files:**
- Create: `S1 Models Lab/tests/observer-field.test.mjs`
- Create after RED: `S1 Models Lab/observer-field.mjs`

**Interfaces:**

```js
OBSERVER_FIELD_VERSION = 's1-observer-field/v0'
TASK_ASSIGNMENT_VERSION = 's1-observer-task/v0'
TASKS = ['x','y','z','w','xw','yw','zw']

makeObserverField({ points4, sourceDimension, densityId })
  -> frozen { version, taskVersion, densityId, observers }

measureObserver(observer, livePoint, mirrorPoint)
  -> frozen { observerId, task, liveValue, mirrorValue, residual }

repairObserver(observer, delta)
  -> new frozen observer
```

Observer record:

```js
{
  id,
  sourcePointId,
  sourceIndex,
  sourceDimension,
  task,
  calibration: 0,
  localFrameVersion: 's1-local-frame/v0'
}
```

- [ ] **Step A1: Write failing observer-count/task tests**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { makeObserverField, TASKS } from '../observer-field.mjs';

const points = [
  [1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1],
  [-1,0,0,0], [0,-1,0,0], [0,0,-1,0], [0,0,0,-1]
];

test('every sampled point gets exactly one observer and one task', () => {
  const field = makeObserverField({points4: points, sourceDimension: 4, densityId:'fixture-8'});
  assert.equal(field.observers.length, points.length);
  for (const observer of field.observers) {
    assert.equal(typeof observer.task, 'string');
    assert.ok(TASKS.includes(observer.task));
    assert.equal(typeof observer.calibration, 'number');
  }
});

test('task assignment is deterministic', () => {
  const a = makeObserverField({points4: points, sourceDimension:4, densityId:'fixture-8'});
  const b = makeObserverField({points4: points, sourceDimension:4, densityId:'fixture-8'});
  assert.deepEqual(a, b);
});
```

- [ ] **Step A2: Run test and verify RED**

Run:

```bash
cd "S1 Models Lab"
node --test tests/observer-field.test.mjs
```

Expected: FAIL because `observer-field.mjs` does not exist.

- [ ] **Step A3: Implement deterministic task assignment**

Use stable point identity from exact coordinate serialization plus source index/density id. Assign task by deterministic 64-bit hash modulo `TASKS.length`; do not use randomness.

Guarantee control repetition: if the field has at least `2 * TASKS.length` points, each task must appear at least twice. If raw hash assignment does not satisfy that coverage, use deterministic round-robin task assignment over observers sorted by stable id. Prefer the round-robin rule for v0 because it is simpler to audit.

- [ ] **Step A4: Add repeated-control coverage test**

Generate at least 14 observers and assert every task appears at least twice.

- [ ] **Step A5: Run tests and commit**

```bash
npm test
git add "S1 Models Lab/observer-field.mjs" "S1 Models Lab/tests/observer-field.test.mjs"
git commit -m "feat: add S1 point observer field"
```

---

### Addendum Task B: Enforce one-degree observational repair

**Files:**
- Extend: `S1 Models Lab/tests/observer-field.test.mjs`
- Modify: `S1 Models Lab/observer-field.mjs`

**Task semantics:**

- `x|y|z|w` observer: measure one coordinate residual plus its own scalar calibration.
- `xw|yw|zw` observer: measure one signed plane-angle residual derived from the selected coordinate pair, plus its own scalar calibration.

Use:

```js
angle2(a,b) = Math.atan2(b,a)
```

and normalized signed angle difference in radians.

- [ ] **Step B1: Write failing scalar-measurement tests**

For each task, assert `measureObserver` returns one finite scalar live value, mirror value, and residual.

- [ ] **Step B2: Write failing repair-isolation test**

```js
const repaired = repairObserver(observer, 0.25);
assert.equal(repaired.calibration, observer.calibration + 0.25);
assert.equal(repaired.task, observer.task);
assert.equal(repaired.sourcePointId, observer.sourcePointId);
assert.equal(observer.calibration, 0);
```

Also deep-compare live/mirror source point arrays before/after repair and require byte-equivalent JSON.

- [ ] **Step B3: Implement minimal measurement and repair**

`repairObserver` accepts exactly one finite scalar delta. Reject objects, arrays, NaN, infinities, and attempts to supply another task/dimension.

- [ ] **Step B4: Run tests and commit**

```bash
npm test
git add "S1 Models Lab/observer-field.mjs" "S1 Models Lab/tests/observer-field.test.mjs"
git commit -m "feat: enforce one-degree S1 observational repairs"
```

---

### Addendum Task C: Preserve observer fields in experience replay/reframe

**Files:**
- Extend: `S1 Models Lab/schema/s1-experience-v0.schema.json`
- Extend: `S1 Models Lab/experience.mjs`
- Extend: `S1 Models Lab/tests/experience.test.mjs`

Add saved fields:

```json
{
  "observerField": {
    "version": "s1-observer-field/v0",
    "taskVersion": "s1-observer-task/v0",
    "densityId": "...",
    "calibrations": [{"observerId":"...","value":0.0}]
  }
}
```

- [ ] **Step C1: Write failing replay test**

Save an experience with a deterministic field and two nonzero observer calibration repairs. Replay it and assert exact observer ids, tasks, and calibrations are reconstructed.

- [ ] **Step C2: Write failing reframe test**

Reframe changes display/global observer settings but preserves the source point-observer ids/tasks/calibrations and source experience id.

- [ ] **Step C3: Implement schema + experience integration**

Reject unknown observer-field/task versions and calibrations referring to nonexistent observer ids.

- [ ] **Step C4: Run tests and commit**

```bash
npm test
git add "S1 Models Lab/schema/s1-experience-v0.schema.json" "S1 Models Lab/experience.mjs" "S1 Models Lab/tests/experience.test.mjs"
git commit -m "feat: preserve S1 observer fields in replay"
```

---

### Addendum Task D: Add observer-field inspection to the play UI

**Files:**
- Extend: `S1 Models Lab/index.html`
- Extend: `S1 Models Lab/render.mjs`
- Extend: `S1 Models Lab/app.mjs`
- Extend: `S1 Models Lab/tests/ui-contract.test.mjs`

- [ ] **Step D1: Write failing static UI checks**

Require:
- observer count text;
- task filter/select;
- selected-observer report;
- keyboard-selectable next/previous observer controls;
- text summary of task distribution and largest residuals.

- [ ] **Step D2: Render sparse observer markers only**

Do not draw every marker at high density. Rendering is a view of the field, not the field itself. Keep full records in data/model.

- [ ] **Step D3: Wire task filter and keyboard observer navigation**

Changing selected observer/task filter is a reframe/inspection action and must not append an object movement.

- [ ] **Step D4: Run tests/manual keyboard smoke and commit**

```bash
npm test
git add "S1 Models Lab/index.html" "S1 Models Lab/render.mjs" "S1 Models Lab/app.mjs" "S1 Models Lab/tests/ui-contract.test.mjs"
git commit -m "feat: expose S1 point observers for play"
```

---

### Addendum Task E: Audit observer-field invariants and two deterministic densities

**Files:**
- Extend: `S1 Models Lab/audit.mjs`
- Extend: `S1 Models Lab/tests/audit.test.mjs`
- Extend: `S1 Models Lab/README.md`

- [ ] **Step E1: Write failing audit assertions**

Require audit output for:
- observer count equals sampled point count;
- exactly one task per observer;
- all task classes represented and repeated at default density;
- no source-state mutation after observational repairs;
- replay reconstructs observer ids/tasks/calibrations;
- density fixture A and B are deterministic;
- summary retains source observer ids;
- `continuumComplete: false`;
- `unique4DReconstructionEstablished: false`;
- `scientificValidation: false`.

- [ ] **Step E2: Add second deterministic density fixture**

Use two declared density ids such as `coarse-v0` and `fine-v0`. Do not infer convergence from two samples; report differences only.

- [ ] **Step E3: Implement audit fields and README boundaries**

- [ ] **Step E4: Run full suite + audit twice and commit**

```bash
npm test
node audit.mjs --source-revision "$(git rev-parse HEAD)" --out /tmp/s1-observer-a.json
node audit.mjs --source-revision "$(git rev-parse HEAD)" --out /tmp/s1-observer-b.json
cmp /tmp/s1-observer-a.json /tmp/s1-observer-b.json
```

---

## Integration order with parent plan

Execute parent Tasks 1-3 first.

Then execute Addendum Tasks A-B before parent Task 4.

Execute parent Task 4, then parent Task 5 together with Addendum Task C.

Execute parent Tasks 6-7, then Addendum Task D before parent Task 8 completion.

Execute parent Task 8, then parent Task 9 together with Addendum Task E.

Finish with parent Task 10 CI/routing gate.

## Addendum self-review

- Every new behavior has a test-first RED step.
- Point-observer field is deterministic and finite.
- Finite mesh is never called a continuum-complete observation.
- One observer has one task and one repairable calibration scalar.
- Repairs do not mutate live/mirror/source history.
- Observer records survive replay and remain source-linked through reframe.
- No unique 4D reconstruction is assumed.
- No biological/physical/Hodge claim is promoted.