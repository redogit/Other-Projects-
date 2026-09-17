import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { DEG } from '../core.mjs';
import { DEFAULT_OBSERVER } from '../observer.mjs';

const moduleUrl = new URL('../image-surface.mjs', import.meta.url);
const moduleExists = existsSync(fileURLToPath(moduleUrl));
const surface = moduleExists ? await import('../image-surface.mjs') : null;

function requireSurface() {
  assert.ok(surface, 'image-surface.mjs must exist and load');
  return surface;
}

function imageSource() {
  return {
    schema: 's1-image-surface/v0',
    sourceImageId: 'synthetic-3x3-grayscale',
    width: 3,
    height: 3,
    channels: 1,
    samples: [0, 32, 64, 96, 128, 160, 192, 224, 255],
    embedding: 'xy-plane-z0-w0'
  };
}

const XW_PLUS = Object.freeze({ plane: 'xw', degrees: 1 });
const YW_PLUS = Object.freeze({ plane: 'yw', degrees: 1 });

function near(actual, expected, epsilon = 1e-10, label = 'value') {
  assert.ok(Math.abs(actual - expected) <= epsilon, `${label}: expected ${expected}, got ${actual}`);
}

test('issue 42 image-surface module exists', () => {
  assert.equal(moduleExists, true);
});

test('source image payload is preserved and identity is deterministic without mutating caller input', () => {
  const { analyzeImageSurface } = requireSurface();
  const source = imageSource();
  const snapshot = JSON.stringify(source);
  const one = analyzeImageSurface(source, [], DEFAULT_OBSERVER);
  const two = analyzeImageSurface(imageSource(), [], DEFAULT_OBSERVER);

  assert.equal(JSON.stringify(source), snapshot);
  assert.deepEqual(one, two);
  assert.deepEqual(one.source.samples, source.samples);
  assert.equal(one.source.width, 3);
  assert.equal(one.source.height, 3);
  assert.equal(one.source.channels, 1);
  assert.match(one.source.payloadHash, /^fnv1a64:[0-9a-f]{16}$/);
  assert.match(one.source.geometryHash, /^fnv1a64:[0-9a-f]{16}$/);
  assert.ok(Object.isFrozen(one));
});

test('identity analysis reports exact grid topology and no intrinsic or projection distortion', () => {
  const { analyzeImageSurface } = requireSurface();
  const result = analyzeImageSurface(imageSource(), [], DEFAULT_OBSERVER);

  assert.deepEqual(result.topology, {
    vertices: 9,
    edges: 12,
    faces: 4,
    eulerCharacteristic: 1,
    connectedComponents: 1,
    changed: false,
    capability: 'fixed-grid-connectivity-under-s1-rotations/v0'
  });
  near(result.intrinsic.principalStretchMin, 1, 1e-12, 'principalStretchMin');
  near(result.intrinsic.principalStretchMax, 1, 1e-12, 'principalStretchMax');
  near(result.intrinsic.maxShearChange, 0, 1e-12, 'maxShearChange');
  near(result.intrinsic.maxAreaRatioDeviation, 0, 1e-12, 'maxAreaRatioDeviation');
  near(result.intrinsic.maxOrientationChangeRadians, 0, 1e-12, 'maxOrientationChangeRadians');
  near(result.intrinsic.curvatureProxyOriginMax, 0, 1e-12, 'curvatureProxyOriginMax');
  near(result.intrinsic.curvatureProxyLiveMax, 0, 1e-12, 'curvatureProxyLiveMax');
  near(result.projection.mirror.maxEdgeScaleDeviation, 0, 1e-12, 'mirror projection edge distortion');
  near(result.projection.live.maxEdgeScaleDeviation, 0, 1e-12, 'live projection edge distortion');
});

test('pure xw rotation changes orientation but preserves intrinsic metric area shear curvature and connectivity', () => {
  const { analyzeImageSurface } = requireSurface();
  const result = analyzeImageSurface(imageSource(), [XW_PLUS], DEFAULT_OBSERVER);

  near(result.intrinsic.principalStretchMin, 1, 1e-10, 'principalStretchMin');
  near(result.intrinsic.principalStretchMax, 1, 1e-10, 'principalStretchMax');
  near(result.intrinsic.maxShearChange, 0, 1e-10, 'maxShearChange');
  near(result.intrinsic.maxAreaRatioDeviation, 0, 1e-10, 'maxAreaRatioDeviation');
  near(result.intrinsic.maxOrientationChangeRadians, DEG, 1e-10, 'orientation change');
  near(result.intrinsic.curvatureProxyOriginMax, 0, 1e-10, 'origin curvature proxy');
  near(result.intrinsic.curvatureProxyLiveMax, 0, 1e-10, 'live curvature proxy');
  assert.equal(result.topology.changed, false);
  assert.equal(result.trajectory.actions.length, 1);
  assert.deepEqual(result.trajectory.actions[0], XW_PLUS);
  assert.equal(result.trajectory.mirrorGeometryHash, result.source.geometryHash);
});

test('observer projection distortion is measured separately from intrinsic deformation', () => {
  const { analyzeImageSurface } = requireSurface();
  const result = analyzeImageSurface(imageSource(), [XW_PLUS], DEFAULT_OBSERVER);

  near(result.intrinsic.maxAreaRatioDeviation, 0, 1e-10, 'intrinsic area change');
  near(result.projection.mirror.maxEdgeScaleDeviation, 0, 1e-12, 'mirror projection distortion');
  assert.ok(result.projection.live.maxEdgeScaleDeviation > 0);
  assert.ok(result.projection.live.maxAreaScaleDeviation > 0);
  assert.ok(result.projection.changeFromMirrorMaxEdgeScaleDeviation > 0);
  assert.equal(result.projection.interpretation, 'observer-projection-distortion-not-intrinsic-deformation');
});

test('ordered S1 chronology is preserved and noncommuting paths remain distinguishable', () => {
  const { analyzeImageSurface } = requireSurface();
  const a = analyzeImageSurface(imageSource(), [XW_PLUS, YW_PLUS], DEFAULT_OBSERVER);
  const b = analyzeImageSurface(imageSource(), [YW_PLUS, XW_PLUS], DEFAULT_OBSERVER);

  assert.deepEqual(a.trajectory.actions, [XW_PLUS, YW_PLUS]);
  assert.deepEqual(b.trajectory.actions, [YW_PLUS, XW_PLUS]);
  assert.notEqual(a.trajectory.liveGeometryHash, b.trajectory.liveGeometryHash);
  assert.equal(a.source.payloadHash, b.source.payloadHash);
  assert.equal(a.topology.changed, false);
  assert.equal(b.topology.changed, false);
});

test('image surface rejects malformed payloads and unsupported deformation moves', () => {
  const { analyzeImageSurface } = requireSurface();
  const badLength = imageSource();
  badLength.samples.pop();
  assert.throws(() => analyzeImageSurface(badLength, [], DEFAULT_OBSERVER), /samples|length|payload/i);

  const badSample = imageSource();
  badSample.samples[0] = 0.5;
  assert.throws(() => analyzeImageSurface(badSample, [], DEFAULT_OBSERVER), /sample|uint8|integer/i);

  assert.throws(
    () => analyzeImageSurface(imageSource(), [{ plane: 'xy', degrees: 1 }], DEFAULT_OBSERVER),
    /unsupported plane/i
  );
});

test('carrier keeps image/physics/algebraic evidence boundaries explicit', () => {
  const { analyzeImageSurface } = requireSurface();
  const result = analyzeImageSurface(imageSource(), [XW_PLUS], DEFAULT_OBSERVER);
  assert.equal(result.authority, 'image-surface-observation-only');
  assert.equal(result.historyAuthority, 'reuse-s1-trajectory-no-second-history');
  assert.match(result.claimCeiling, /IMAGE_DEFORMATION != PHYSICAL_DEFORMATION/);
  assert.match(result.claimCeiling, /GEOMETRIC_RESEMBLANCE != ALGEBRAIC_GEOMETRY_EVIDENCE/);
  assert.match(result.claimCeiling, /projection/i);
  const text = JSON.stringify(result).toLowerCase();
  assert.equal(text.includes('is_hodge_class'), false);
  assert.equal(text.includes('physical_deformation_proved'), false);
});
