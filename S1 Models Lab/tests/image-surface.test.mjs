import test from 'node:test';
import assert from 'node:assert/strict';
import { EXPERIENCE_SCHEMA, canonicalJson } from '../experience.mjs';
import { DEFAULT_OBSERVER } from '../observer.mjs';
import { MemoryStore, LocalExperienceStore } from '../storage.mjs';
import {
  IMAGE_SURFACE_SCHEMA,
  createImageSurfaceSession,
  measureImageSurface,
  recoverSourceImage,
  replayImageSurface,
  reframeImageSurface,
  validateImageSurfaceSession
} from '../image-surface.mjs';

const bumpPixels = Object.freeze([
  0, 0, 0,
  0, 255, 0,
  0, 0, 0
]);

function makeSession({heightScale = 0.5, actions = [{ plane: 'xw', degrees: 1 }]} = {}) {
  return createImageSurfaceSession({
    source: {
      width: 3,
      height: 3,
      channels: 1,
      pixels: bumpPixels,
      mediaType: 'image/x-s1-fixture'
    },
    surfaceOptions: { heightChannel: 0, heightScale },
    actions,
    observer: DEFAULT_OBSERVER,
    provenance: { source: 'issue-42-test-fixture' }
  });
}

test('image source remains exactly recoverable while surface and event identities are deterministic', () => {
  const a = makeSession();
  const b = makeSession();
  assert.equal(a.schema, IMAGE_SURFACE_SCHEMA);
  assert.equal(a.id, b.id);
  assert.equal(a.source.id, b.source.id);
  assert.equal(a.surface.id, b.surface.id);
  assert.deepEqual(recoverSourceImage(a).pixels, [...bumpPixels]);
  assert.equal(a.experience.schema, EXPERIENCE_SCHEMA);
  assert.equal(a.experience.initialState, a.surface.id);
  assert.equal(a.historyAuthority, EXPERIENCE_SCHEMA);
  assert.equal(Object.isFrozen(a), true);
});

test('image adapter reuses S1 experience storage and replay instead of creating a second history', () => {
  const session = makeSession({actions:[
    { plane: 'xw', degrees: 1 },
    { plane: 'yw', degrees: -1 }
  ]});
  const before = canonicalJson(session.source);
  const replayed = replayImageSurface(session);
  assert.deepEqual(replayed.actions, session.experience.actions);
  assert.equal(canonicalJson(session.source), before);

  const memory = new MemoryStore();
  const store = new LocalExperienceStore(memory);
  const saved = store.save(session.experience);
  assert.equal(saved.event.id, session.experience.id);
  const exported = store.exportJson();
  const restored = new LocalExperienceStore(new MemoryStore());
  restored.importJson(exported);
  assert.equal(restored.list()[0].event.id, session.experience.id);
});

test('intrinsic metric, ambient orientation, curvature proxy, and connectivity are kept distinct', () => {
  const session = makeSession();
  const m = measureImageSurface(session);

  assert.ok(m.intrinsic.maxPrincipalStretchDeltaFromOne <= 1e-12);
  assert.ok(m.intrinsic.maxShearCosineDelta <= 1e-12);
  assert.ok(m.intrinsic.maxAreaRatioDeltaFromOne <= 1e-12);
  assert.ok(m.extrinsic.maxAmbientOrientationAngleRad > 0);
  assert.ok(m.curvature.originMax > 0);
  assert.ok(Math.abs(m.curvature.liveMax - m.curvature.originMax) <= 1e-12);
  assert.equal(m.topology.connectivityChanged, false);
  assert.equal(m.topology.continuumTopologyClaim, false);
  assert.equal(m.areaElement.dimension, 2);
});

test('projection-induced distortion is reported separately from intrinsic deformation', () => {
  const session = makeSession({heightScale:0});
  const m = measureImageSurface(session);
  assert.ok(m.intrinsic.maxPrincipalStretchDeltaFromOne <= 1e-12);
  assert.ok(m.projection.maxPrincipalStretchDeltaFromOne > 1e-8);
  assert.equal(m.projection.projectionDistortionDetected, true);
  assert.equal(m.projection.intrinsicDeformationImplied, false);
});

test('reframe preserves source and S1 event identity', () => {
  const session = makeSession();
  const beforeSource = canonicalJson(session.source);
  const beforeExperience = canonicalJson(session.experience);
  const reframed = reframeImageSurface(session, {...DEFAULT_OBSERVER, yaw:0.2});
  assert.equal(reframed.sourceImageId, session.source.id);
  assert.equal(reframed.sourceEventId, session.experience.id);
  assert.equal(reframed.reframe.sourceId, session.experience.id);
  assert.equal(canonicalJson(session.source), beforeSource);
  assert.equal(canonicalJson(session.experience), beforeExperience);
});

test('image-surface record validates canonically and preserves evidence ceilings', () => {
  const session = makeSession();
  assert.deepEqual(validateImageSurfaceSession(session), session);
  assert.equal(session.claimCeiling.includes('IMAGE_DEFORMATION != PHYSICAL_DEFORMATION'), true);
  assert.equal(session.claimCeiling.includes('GEOMETRIC_RESEMBLANCE != ALGEBRAIC_GEOMETRY_EVIDENCE'), true);
});

test('invalid image data and unsupported transforms fail closed', () => {
  assert.throws(() => createImageSurfaceSession({
    source:{width:2,height:2,channels:1,pixels:[0,1,2],mediaType:'image/test'},
    actions:[], observer:DEFAULT_OBSERVER, provenance:{source:'bad'}
  }), /pixel/);
  assert.throws(() => createImageSurfaceSession({
    source:{width:2,height:2,channels:1,pixels:[0,1,2,3],mediaType:'image/test'},
    actions:[{plane:'xy',degrees:1}], observer:DEFAULT_OBSERVER, provenance:{source:'bad'}
  }));
  const session = makeSession();
  const corrupted = {...session, id:'0000000000000000'};
  assert.throws(() => validateImageSurfaceSession(corrupted), /id/);
});
