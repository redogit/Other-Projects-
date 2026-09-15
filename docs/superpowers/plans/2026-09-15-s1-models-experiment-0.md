# S'1 Models Experiment 0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dependency-free local browser lab where a person can play with one-degree 4D transformations, compare a live object against an immutable mirror through the same observer, save experiences locally, replay them exactly, and reframe them without rewriting history.

**Architecture:** Implement a new self-contained `S1 Models Lab/` browser app in `redogit/Other-Projects-`. Keep geometry/state/experience/storage as pure ES modules that are testable in Node 22, and keep Canvas2D rendering/UI as a thin layer over those contracts. The initial learner is an append-only experience graph; there is no ML training in Experiment 0.

**Tech Stack:** HTML5, CSS, ES2023 modules, Canvas2D, browser `localStorage`, BigInt-based deterministic FNV-1a IDs, Node.js 22 built-in `node:test`; no third-party runtime dependencies.

**Spec:** `docs/superpowers/specs/2026-09-15-s1-models-dimensional-deformation-lab-design.md`

## Global Constraints

- Experiment 0 changes exactly one declared 4D rotational plane by exactly 1 degree per move.
- Initial planes: `xw`, `yw`, `zw` only.
- `S'1_Mirror` is immutable and never trained/adapted.
- `S'1_Experience` is append-only local learning, not ML.
- `S'1_Suggest` is inactive and must not be implemented in this plan.
- Smooth S3-like and tesseract-boundary displays are **synthetic observer/reference surfaces**, not physical-spacetime claims.
- The same observer/frame transform is applied to live and mirror before visual comparison.
- Saving is explicit; no hidden automatic history is required.
- Replay must fail closed on incompatible/corrupt records rather than silently approximating the source event.
- Reframe creates a derived observation referencing the preserved event; it does not rewrite the event.
- `EXPERIENCE_RECORD != INTERPRETATION`.
- `REPETITION != INDEPENDENT_EVIDENCE`.
- `SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION`.
- `real 4D != complex dimension 4`; no Hodge/P-vs-NP/physics promotion is allowed by this app.
- Keyboard-equivalent controls, visible focus, reduced-motion behavior, text labels, and a nonvisual numeric/text inspection path are part of the baseline, not post-release polish.

---

## File Structure

Create one isolated project directory:

```text
S1 Models Lab/
├── README.md                         # user/developer entry point and claim ceilings
├── index.html                        # semantic controls + canvas + text inspection panel
├── styles.css                        # responsive, focus, reduced-motion, forced-colors behavior
├── package.json                      # dependency-free node:test command
├── core.mjs                          # immutable state, 4D rotations, S'1 mirror/difference contracts
├── geometry.mjs                      # S3-like and tesseract-boundary reference sample generators
├── observer.mjs                      # common observer frame + 4D->3D projection contract
├── experience.mjs                    # canonical saved record, stable IDs, graph classification, replay/reframe
├── storage.mjs                       # explicit local save/export/import/clear adapters
├── render.mjs                        # Canvas2D rendering from pure projected scene data
├── app.mjs                           # DOM event wiring only
├── schema/
│   └── s1-experience-v0.schema.json  # machine-readable save contract
└── tests/
    ├── core.test.mjs
    ├── geometry.test.mjs
    ├── observer.test.mjs
    ├── experience.test.mjs
    ├── storage.test.mjs
    └── ui-contract.test.mjs
```

Do not modify `Decision Field Operator Lab/` in Experiment 0. Reuse its concepts by provenance/reference, not source copying. This keeps the new lab independently removable and prevents accidental authority transfer.

---

### Task 1: Establish the project contract and test harness

**Files:**
- Create: `S1 Models Lab/package.json`
- Create: `S1 Models Lab/README.md`
- Create: `S1 Models Lab/schema/s1-experience-v0.schema.json`
- Create: `S1 Models Lab/tests/ui-contract.test.mjs`

**Interfaces:**
- Produces constants/contracts later modules must match: schema `s1-experience/v0`, operator semantics `S'1-Ops v0`, planes `xw|yw|zw`, shell ids `s3-sample|tesseract-boundary|comparison`.

- [ ] **Step 1: Write the failing static contract test**

Create `S1 Models Lab/tests/ui-contract.test.mjs`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const root = new URL('../', import.meta.url);

async function text(name) {
  return readFile(new URL(name, root), 'utf8');
}

test('README preserves experiment claim ceilings', async () => {
  const readme = await text('README.md');
  for (const required of [
    'synthetic observer/reference surface',
    'SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION',
    'real 4D != complex dimension 4',
    "S'1_Mirror",
    "S'1_Experience",
    "S'1_Suggest"
  ]) assert.match(readme, new RegExp(required.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
});

test('schema declares the exact v0 identity', async () => {
  const schema = JSON.parse(await text('schema/s1-experience-v0.schema.json'));
  assert.equal(schema.$id, 's1-experience/v0');
  assert.deepEqual(schema.properties.operatorVersion.const, "S'1-Ops v0");
});
```

- [ ] **Step 2: Run the test and verify it fails because files are missing**

Run:

```bash
cd "S1 Models Lab"
node --test tests/ui-contract.test.mjs
```

Expected: FAIL with missing `README.md` or schema.

- [ ] **Step 3: Add the minimal package and contracts**

Create `package.json`:

```json
{
  "name": "s1-models-lab",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "node --test tests/*.test.mjs"
  }
}
```

Create JSON Schema requiring these top-level fields:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "s1-experience/v0",
  "type": "object",
  "required": [
    "schema", "id", "initialState", "mirrorId", "shell",
    "actions", "observer", "operatorVersion", "comparisons",
    "relations", "provenance"
  ],
  "properties": {
    "schema": {"const": "s1-experience/v0"},
    "operatorVersion": {"const": "S'1-Ops v0"},
    "shell": {"enum": ["s3-sample", "tesseract-boundary", "comparison"]},
    "actions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["plane", "degrees"],
        "properties": {
          "plane": {"enum": ["xw", "yw", "zw"]},
          "degrees": {"enum": [-1, 1]}
        },
        "additionalProperties": false
      }
    }
  }
}
```

Write `README.md` describing local use, all global boundaries, and explicitly state that `S'1_Suggest` is inactive.

- [ ] **Step 4: Run the static contract test**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add "S1 Models Lab"
git commit -m "test: establish S1 Experiment 0 contracts"
```

---

### Task 2: Implement exact 4D state, rotations, and immutable mirror comparisons

**Files:**
- Create: `S1 Models Lab/core.mjs`
- Create: `S1 Models Lab/tests/core.test.mjs`

**Interfaces:**
- Produces:
  - `DEG = Math.PI / 180`
  - `createState(points)` -> deeply frozen `{ points, actions }`
  - `rotatePoint4(point, plane, degrees)` -> frozen `[x,y,z,w]`
  - `applyMove(state, {plane,degrees})` -> new frozen state
  - `createMirror(state)` -> deeply frozen baseline clone
  - `compareStates(a,b,epsilon=1e-12)` -> `{ equal, maxAbsDelta, pointDeltas }`
  - `assertSupportedMove(move)` throws on unknown plane, non-finite, or magnitude other than 1.

- [ ] **Step 1: Write failing rotation/control tests**

Create tests for:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  createState, createMirror, applyMove, rotatePoint4, compareStates
} from '../core.mjs';

test('xw +1 degree moves x into w without mutating input', () => {
  const p = Object.freeze([1, 0, 0, 0]);
  const q = rotatePoint4(p, 'xw', 1);
  assert.ok(Math.abs(q[0] - Math.cos(Math.PI / 180)) < 1e-12);
  assert.ok(Math.abs(q[3] - Math.sin(Math.PI / 180)) < 1e-12);
  assert.deepEqual(p, [1,0,0,0]);
});

test('mirror remains equal to origin while live state moves', () => {
  const origin = createState([[1,0,0,0],[0,1,0,0]]);
  const mirror = createMirror(origin);
  const live = applyMove(origin, { plane: 'xw', degrees: 1 });
  assert.equal(compareStates(origin, mirror).equal, true);
  assert.equal(compareStates(live, mirror).equal, false);
  assert.equal(mirror.actions.length, 0);
});

test('only one-degree declared moves are admitted', () => {
  const origin = createState([[1,0,0,0]]);
  assert.throws(() => applyMove(origin, {plane:'xy', degrees:1}));
  assert.throws(() => applyMove(origin, {plane:'xw', degrees:2}));
  assert.throws(() => applyMove(origin, {plane:'xw', degrees:NaN}));
});
```

- [ ] **Step 2: Run tests; verify module-not-found failure**

Run: `node --test tests/core.test.mjs`.

- [ ] **Step 3: Implement only xw/yw/zw plane rotations**

Use a single helper that identifies the two rotated coordinate indices and applies the standard 2D rotation inside 4D. Freeze returned point arrays and state objects. `applyMove` appends the exact move to a new action array.

- [ ] **Step 4: Run core tests**

Expected: PASS.

- [ ] **Step 5: Add latest-step vs origin comparison test**

Assert:

```js
const origin = createState([[1,0,0,0]]);
const s1 = applyMove(origin, {plane:'xw',degrees:1});
const s2 = applyMove(s1, {plane:'xw',degrees:1});
assert.ok(compareStates(s2, origin).maxAbsDelta > compareStates(s2, s1).maxAbsDelta);
```

- [ ] **Step 6: Run full core test file and commit**

```bash
npm test
git add "S1 Models Lab/core.mjs" "S1 Models Lab/tests/core.test.mjs"
git commit -m "feat: add immutable S1 4D state kernel"
```

---

### Task 3: Generate synthetic S3-like and tesseract-boundary reference samples

**Files:**
- Create: `S1 Models Lab/geometry.mjs`
- Create: `S1 Models Lab/tests/geometry.test.mjs`

**Interfaces:**
- Produces:
  - `sampleS3({etaSteps=7, xi1Steps=16, xi2Steps=16, radius=1.6})`
  - `sampleTesseractBoundary({steps=4, halfExtent=1.4})`
  - each returns `{ id, points4, groups }`; `groups` supplies stable cell/band labels for rendering/comparison.

- [ ] **Step 1: Write S3 membership tests**

For each generated S3 sample point `p`, assert:

```js
const norm2 = p.reduce((s,x) => s + x*x, 0);
assert.ok(Math.abs(norm2 - radius*radius) < 1e-10);
```

Also assert deterministic point count and stable output for repeated calls.

- [ ] **Step 2: Write tesseract-boundary tests**

For every boundary point, assert at least one coordinate has absolute value `halfExtent` within tolerance. Assert the generator exposes all eight signed boundary-cell identities: `x-`, `x+`, `y-`, `y+`, `z-`, `z+`, `w-`, `w+`.

- [ ] **Step 3: Run tests and observe failure**

- [ ] **Step 4: Implement S3 sampling with Hopf coordinates**

Use:

```text
x = r cos(eta) cos(xi1)
y = r cos(eta) sin(xi1)
z = r sin(eta) cos(xi2)
w = r sin(eta) sin(xi2)
```

Sample `eta` over `[0,pi/2]` and both `xi` angles over `[0,2pi)` with endpoint de-duplication. This is a finite sample of S3, never label it a complete numerical representation of every S3 point.

- [ ] **Step 5: Implement tesseract boundary sample**

For each of the eight fixed-coordinate cells, enumerate a small deterministic 3D lattice for the remaining coordinates. Deduplicate identical seam points by exact coordinate key.

- [ ] **Step 6: Run tests and commit**

```bash
npm test
git add "S1 Models Lab/geometry.mjs" "S1 Models Lab/tests/geometry.test.mjs"
git commit -m "feat: add S1 synthetic 4D reference surfaces"
```

---

### Task 4: Implement one shared observer frame and 4D-to-3D projection

**Files:**
- Create: `S1 Models Lab/observer.mjs`
- Create: `S1 Models Lab/tests/observer.test.mjs`

**Interfaces:**
- Produces:
  - `DEFAULT_OBSERVER = { yaw:0, pitch:0, roll:0, wPerspective:0.35 }`
  - `normalizeObserver(input)` -> validated frozen observer
  - `projectPoint4(point, observer)` -> `[x,y,z,depth]`
  - `projectState(state, observer)` -> frozen projected scene points
  - `projectPair(live, mirror, observer)` -> `{live,mirror,observer}` using exactly one normalized observer object.

- [ ] **Step 1: Write same-observer invariant tests**

Test that projecting identical live/mirror states through a non-default observer yields identical projected coordinates. Test that changing the observer changes both projections but does not change the underlying 4D states.

- [ ] **Step 2: Write invalid-observer tests**

Reject non-finite yaw/pitch/roll/perspective values and unsupported keys.

- [ ] **Step 3: Implement projection**

First apply 3D yaw/pitch/roll to xyz as an observer-only frame. Then apply bounded w-perspective scale:

```js
const scale = 1 / (1 + observer.wPerspective * Math.max(-0.9, w));
return [x * scale, y * scale, z * scale, z];
```

Document this as a visualization projection, not an intrinsic geometry map.

- [ ] **Step 4: Run observer + core tests and commit**

```bash
npm test
git add "S1 Models Lab/observer.mjs" "S1 Models Lab/tests/observer.test.mjs"
git commit -m "feat: add shared S1 observer projection"
```

---

### Task 5: Implement canonical experience records, deterministic IDs, replay, reframe, and graph classification

**Files:**
- Create: `S1 Models Lab/experience.mjs`
- Create: `S1 Models Lab/tests/experience.test.mjs`

**Interfaces:**
- Produces:
  - `canonicalJson(value)` stable key ordering
  - `fnv1a64(text)` -> 16-char hex string
  - `makeExperience(input)` -> frozen validated record
  - `replayExperience(record, geometryRegistry)` -> exact live state
  - `reframeExperience(record, observer)` -> derived `{sourceId, observer, projected}` without record mutation
  - `classifyExperience(record, graph)` -> `repeat|variation|new-branch|counterexample|unresolved`
  - `appendExperience(graph, record, classification)` -> new frozen graph.

- [ ] **Step 1: Write deterministic ID tests**

Two structurally identical records with different object key insertion order must receive the same ID. One changed action must change the ID.

- [ ] **Step 2: Write replay tests**

Build a record with `[xw +1, yw -1, zw +1]`; replay from its declared initial geometry; assert `compareStates(replayed, directlyApplied).equal === true`.

Reject:
- wrong schema;
- wrong operator version;
- missing initial geometry id;
- malformed action;
- unsupported shell.

- [ ] **Step 3: Write reframe immutability test**

Reframe the same record under two observers. Assert the record JSON and ID remain byte-for-byte/canonical-string identical while projected observations differ.

- [ ] **Step 4: Write graph classification fixtures**

Use exact rules:
- **repeat**: same canonical event ID already exists;
- **new-branch**: no existing event shares the exact action-prefix parent and this record is its first saved child;
- **variation**: same initial geometry + shell + declared comparison obligation, but different valid action/result path with a known related prefix/family;
- **counterexample**: record explicitly names `testsInvariantId` and its comparison contradicts a stored invariant predicate result;
- **unresolved**: insufficient relation metadata for the previous classes.

Do not infer counterexamples from visual surprise alone.

- [ ] **Step 5: Implement minimal canonicalization, FNV-1a, replay/reframe, classification**

Use BigInt FNV-1a 64-bit in pure JS so browser and Node produce identical IDs without async crypto differences.

- [ ] **Step 6: Run tests and commit**

```bash
npm test
git add "S1 Models Lab/experience.mjs" "S1 Models Lab/tests/experience.test.mjs"
git commit -m "feat: add S1 experience replay and graph contracts"
```

---

### Task 6: Add explicit local persistence, export/import, and clear

**Files:**
- Create: `S1 Models Lab/storage.mjs`
- Create: `S1 Models Lab/tests/storage.test.mjs`

**Interfaces:**
- Produces:
  - `MemoryStore` for tests
  - `LocalExperienceStore(storage, key='s1-experience-v0')`
  - methods: `list()`, `save(record)`, `replaceAll(records)`, `clear()`, `exportJson()`, `importJson(text)`
- `save()` happens only when called explicitly; constructing the store performs no write.

- [ ] **Step 1: Write no-auto-save test**

Provide a fake storage object counting `setItem` calls; instantiate the store; assert zero writes.

- [ ] **Step 2: Write save/dedup occurrence test**

Saving the same canonical event twice must not manufacture a second event node. Preserve occurrence metadata separately, e.g. `{event, occurrences: 2}`.

- [ ] **Step 3: Write export/import round-trip and corruption tests**

Export -> clear -> import -> list must recover identical canonical records. Reject invalid JSON, wrong schema, unknown operator version, and records failing `makeExperience` validation without altering existing storage.

- [ ] **Step 4: Implement storage adapters**

Use a temporary validated array before `replaceAll` so failed imports are atomic.

- [ ] **Step 5: Run tests and commit**

```bash
npm test
git add "S1 Models Lab/storage.mjs" "S1 Models Lab/tests/storage.test.mjs"
git commit -m "feat: add explicit local S1 experience storage"
```

---

### Task 7: Render live, mirror, and comparison views without making rendering authoritative

**Files:**
- Create: `S1 Models Lab/render.mjs`
- Create: `S1 Models Lab/index.html`
- Create: `S1 Models Lab/styles.css`
- Extend: `S1 Models Lab/tests/ui-contract.test.mjs`

**Interfaces:**
- `render.mjs` consumes projected scene data only; it may not mutate geometry/state/experience records.
- Produces `renderScene(canvas, scene, options)` and `formatInspection(model)`.

- [ ] **Step 1: Extend static UI contract tests**

Read HTML/CSS as text and assert presence of:
- buttons for `xw +1`, `xw -1`, `yw +1`, `yw -1`, `zw +1`, `zw -1`;
- shell selector with all three views;
- Save, Replay, Reframe, Export, Import, Clear controls;
- `<canvas>` plus a text inspection element with `aria-live="polite"`;
- CSS `:focus-visible`;
- `@media (prefers-reduced-motion: reduce)`;
- `@media (forced-colors: active)`.

- [ ] **Step 2: Create semantic HTML before JavaScript wiring**

Use real `<button>`, `<select>`, `<details>`, `<output>`, and `<input type=file>` elements. Provide concise labels; do not require pointer gestures.

- [ ] **Step 3: Implement Canvas2D renderer**

Render projected points/segments with non-color-only distinction:
- mirror: dashed/thin outline markers;
- live: solid/thicker markers;
- displacement: short connector marks where corresponding samples exist;
- comparison view: side-by-side or overlay toggle using the same observer.

Keep animation optional. In reduced-motion mode, update discretely with no interpolation.

- [ ] **Step 4: Implement `formatInspection`**

Return plain text including:
- shell id;
- current action count;
- current plane/latest move;
- live vs mirror equality;
- max absolute coordinate delta;
- origin displacement summary;
- latest-step change summary;
- current observer values.

- [ ] **Step 5: Run tests and manually open static page**

Run `npm test`, then:

```bash
python -m http.server 8000 --bind 127.0.0.1
```

Open `/S1%20Models%20Lab/` and confirm the no-JS document still explains purpose/boundaries.

- [ ] **Step 6: Commit**

```bash
git add "S1 Models Lab/index.html" "S1 Models Lab/styles.css" "S1 Models Lab/render.mjs" "S1 Models Lab/tests/ui-contract.test.mjs"
git commit -m "feat: add accessible S1 deformation views"
```

---

### Task 8: Wire play controls to state, save, replay, reframe, and graph status

**Files:**
- Create: `S1 Models Lab/app.mjs`
- Modify: `S1 Models Lab/index.html`
- Extend: `S1 Models Lab/tests/ui-contract.test.mjs`

**Interfaces:**
- `app.mjs` owns only orchestration and DOM event handlers.
- It imports state/geometry/observer/experience/storage/render modules and must not duplicate their rules.

- [ ] **Step 1: Add static checks that `index.html` loads only `app.mjs` as its application module**

This prevents hidden alternate state machines in inline scripts.

- [ ] **Step 2: Wire initialization**

At page load:
- choose `s3-sample` as default display;
- construct origin + immutable mirror;
- set live = origin;
- set `DEFAULT_OBSERVER`;
- render without writing local storage.

- [ ] **Step 3: Wire movement buttons and keyboard shortcuts**

Every action calls `applyMove(live, {plane,degrees})`, updates `previousLive`, projects live+mirror through one observer, renders, and updates the text inspection output.

Keyboard mapping must be documented and must not hijack typing while focus is inside an input/select.

- [ ] **Step 4: Wire shell/view changes as reframing, not object moves**

Changing smooth/tesseract/comparison display must not append to the 4D action sequence. It changes current presentation metadata only.

- [ ] **Step 5: Wire explicit Save**

On Save:
- build a validated `makeExperience` record;
- classify against current graph;
- append/reuse graph node according to classification;
- call store `save` explicitly;
- show classification and record ID in the UI.

- [ ] **Step 6: Wire Replay**

Replay selected saved record from origin via `replayExperience`; update live state only after replay fully validates. A replay error leaves the current live state untouched and displays a clear error.

- [ ] **Step 7: Wire Reframe**

Allow observer yaw/pitch/roll/perspective controls and shell selection to produce a derived observation without changing the saved source record/action list.

- [ ] **Step 8: Wire export/import/clear with confirmation on destructive clear**

Import validates atomically before replacement. Clear affects only the lab's own local key.

- [ ] **Step 9: Run all tests and manual keyboard/reduced-motion smoke checks**

- [ ] **Step 10: Commit**

```bash
git add "S1 Models Lab/app.mjs" "S1 Models Lab/index.html" "S1 Models Lab/tests/ui-contract.test.mjs"
git commit -m "feat: wire S1 play save replay and reframe"
```

---

### Task 9: Add an independent audit and frozen Experiment 0 evidence summary

**Files:**
- Create: `S1 Models Lab/audit.mjs`
- Create: `S1 Models Lab/evidence/EXPERIMENT_0_SUMMARY.json`
- Create: `S1 Models Lab/tests/audit.test.mjs`
- Modify: `S1 Models Lab/README.md`

**Interfaces:**
- `audit.mjs` reruns deterministic software fixtures and emits JSON observations only.
- Evidence summary must declare scope and claim ceiling; it is not a scientific promotion record.

- [ ] **Step 1: Write failing audit test**

Require the audit to report:
- exact mirror unchanged after a fixed action sequence;
- replay equals direct application for fixed fixtures;
- same-observer pair uses equal observer identity/settings;
- S3 sample radius residual maximum;
- all eight tesseract boundary cell ids present;
- repeat and variation graph fixtures classified as expected;
- corrupted save rejected;
- `scientificValidation: false`.

- [ ] **Step 2: Implement `audit.mjs` using public module interfaces only**

Do not import test-only internals. Run two identical audit invocations and verify stable scientific/software output fields.

- [ ] **Step 3: Generate `EXPERIMENT_0_SUMMARY.json`**

Record:
- schema/version;
- exact source commit placeholder is **not** allowed; generate only after the implementation commit exists, then pin its SHA through the audit invocation argument;
- runtime version;
- test counts;
- deterministic fixture outputs;
- explicit boundaries: synthetic surfaces, software-only verification, no Hodge/physics/open-problem promotion.

- [ ] **Step 4: Run full test suite and audit twice**

```bash
npm test
node audit.mjs --source-revision "$(git rev-parse HEAD)" --out /tmp/s1-audit-a.json
node audit.mjs --source-revision "$(git rev-parse HEAD)" --out /tmp/s1-audit-b.json
cmp /tmp/s1-audit-a.json /tmp/s1-audit-b.json
```

Expected: tests PASS and audit files byte-identical for deterministic fields.

- [ ] **Step 5: Update README with exact run commands and evidence ceiling**

- [ ] **Step 6: Commit**

```bash
git add "S1 Models Lab/audit.mjs" "S1 Models Lab/evidence" "S1 Models Lab/tests/audit.test.mjs" "S1 Models Lab/README.md"
git commit -m "test: freeze bounded S1 Experiment 0 evidence"
```

---

### Task 10: Add repository CI gate and federation routing only after the local suite passes

**Files:**
- Create: `.github/workflows/s1-models-check.yml`
- Modify: `README.md`
- Modify: `federation/active-projects.json` only if Experiment 0 is merged and verified; otherwise keep it out of `active`.

**Interfaces:**
- CI checks exact public `$GITHUB_SHA` using the repository's established direct-Git/action-light pattern.

- [ ] **Step 1: Create workflow scoped to S1 files**

Trigger on pull requests/pushes touching:

```yaml
paths:
  - 'S1 Models Lab/**'
  - '.github/workflows/s1-models-check.yml'
```

Job steps:
1. initialize Git repo;
2. fetch exact `$GITHUB_SHA`;
3. verify checked-out SHA;
4. `cd "S1 Models Lab"`;
5. print Node version and require major >= 22;
6. `npm test`;
7. run audit to a temporary output and validate required boundary flags.

- [ ] **Step 2: Open implementation PR and require exact-head CI success**

Do not merge based on a workflow from an older head.

- [ ] **Step 3: After merge, update owner-local active routing in a separate small change**

Only after the merged main revision is verified may `federation/active-projects.json` describe S1 as active/runnable. Keep Conscience64 bridge work separate and gated by its issue #94.

- [ ] **Step 4: Final two-pass review**

Pass 1: functional/evidence review.  
Pass 2: look specifically for stale links, provenance errors, hidden autosave, mutable mirror paths, accidental profile inference, Hodge/physics overclaims, inaccessible controls, and observer/frame contamination.

---

## Plan Self-Review

### Spec coverage

Covered explicitly:
- Observer 0 play surface — Tasks 7–8.
- Smooth S3-like + tesseract + comparison views — Tasks 3, 7.
- 1° xw/yw/zw rule — Task 2.
- immutable mirror and two comparison relations — Task 2.
- same-observer rule — Task 4.
- replay/reframe — Tasks 5, 8.
- `S'1-Ops v0` metadata/contracts — Tasks 1, 2, 5.
- explicit local save/export/import/clear — Task 6, 8.
- append-only experience graph — Task 5.
- deterministic repeat/variation/branch/counterexample/unresolved rules — Task 5.
- faithful transport/provenance fields — Tasks 1, 5.
- privacy/user-profile boundary — Tasks 1, 5, 8.
- accessibility baseline — Task 7–8.
- fail-closed replay/import — Tasks 5–6, 8.
- Hodge/open-problem firewall — Tasks 1, 9.
- bounded verification and publication gate — Tasks 9–10.
- `S'1_Suggest` remains unimplemented — Global Constraints and Task 1 documentation.

### Placeholder scan

No `TBD`, `TODO`, or unbound implementation placeholders are permitted. The audit source revision is explicitly supplied at execution time and must never be committed as an invented value.

### Type/interface consistency

All later tasks consume the public interfaces defined in earlier tasks. Rendering does not own source state. Storage validates through experience contracts. App orchestration does not duplicate math, graph classification, or persistence rules.

## Execution Handoff

After this plan is reviewed, implementation may proceed either:

1. **Subagent-driven** — fresh isolated worker per task with review gates; or
2. **Inline execution** — execute this plan task-by-task with checkpoints.

Do not start implementation until the plan/spec review gate is accepted.
