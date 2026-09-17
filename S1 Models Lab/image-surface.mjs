import { compareStates, materializeTrajectory } from './core.mjs';
import { DEFAULT_OBSERVER, normalizeObserver, projectState } from './observer.mjs';
import { canonicalJson, fnv1a64, OPERATOR_VERSION } from './experience.mjs';

export const IMAGE_SURFACE_SCHEMA = 's1-image-surface/v0';
export const IMAGE_SURFACE_ANALYSIS_SCHEMA = 's1-image-surface-analysis/v0';
const EMBEDDING = 'xy-plane-z0-w0';
const SOURCE_KEYS = Object.freeze(['schema', 'sourceImageId', 'width', 'height', 'channels', 'samples', 'embedding']);
const MAX_SAMPLES = 1_048_576;
const EPS = 1e-15;

function deepFreeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    for (const child of Object.values(value)) deepFreeze(child);
    Object.freeze(value);
  }
  return value;
}

function assertPlainObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new TypeError(`${label} must be an object`);
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) throw new TypeError(`${label} must be a plain object`);
}

function assertOnlyKeys(value, allowed, label) {
  for (const key of Object.keys(value)) if (!allowed.includes(key)) throw new RangeError(`unsupported ${label} field: ${key}`);
}

function normalizeSource(source) {
  assertPlainObject(source, 'image surface source');
  assertOnlyKeys(source, SOURCE_KEYS, 'image surface source');
  if (source.schema !== IMAGE_SURFACE_SCHEMA) throw new RangeError('unsupported image surface schema');
  if (typeof source.sourceImageId !== 'string' || !source.sourceImageId.trim()) throw new TypeError('sourceImageId is required');
  if (!Number.isInteger(source.width) || source.width < 2 || source.width > 1024) throw new RangeError('width must be an integer in 2..1024');
  if (!Number.isInteger(source.height) || source.height < 2 || source.height > 1024) throw new RangeError('height must be an integer in 2..1024');
  if (!Number.isInteger(source.channels) || source.channels < 1 || source.channels > 4) throw new RangeError('channels must be an integer in 1..4');
  if (source.embedding !== EMBEDDING) throw new RangeError(`embedding must be ${EMBEDDING}`);
  if (!Array.isArray(source.samples)) throw new TypeError('samples must be an array');
  const expected = source.width * source.height * source.channels;
  if (expected > MAX_SAMPLES) throw new RangeError(`image payload exceeds ${MAX_SAMPLES} samples`);
  if (source.samples.length !== expected) throw new RangeError(`samples length must equal width*height*channels (${expected})`);
  const samples = source.samples.map((sample, index) => {
    if (!Number.isInteger(sample) || sample < 0 || sample > 255) throw new TypeError(`sample ${index} must be a uint8 integer`);
    return sample;
  });
  return {
    schema: IMAGE_SURFACE_SCHEMA,
    sourceImageId: source.sourceImageId,
    width: source.width,
    height: source.height,
    channels: source.channels,
    samples,
    embedding: EMBEDDING
  };
}

function hashValue(value) {
  return `fnv1a64:${fnv1a64(canonicalJson(value))}`;
}

function gridPoints(width, height) {
  const points = [];
  for (let row = 0; row < height; row++) {
    const y = -1 + (2 * row) / (height - 1);
    for (let col = 0; col < width; col++) {
      const x = -1 + (2 * col) / (width - 1);
      points.push([x, y, 0, 0]);
    }
  }
  return points;
}

function sub(a, b) {
  return a.map((value, index) => value - b[index]);
}

function dot(a, b) {
  let total = 0;
  for (let i = 0; i < a.length; i++) total += a[i] * b[i];
  return total;
}

function norm(v) {
  return Math.sqrt(Math.max(0, dot(v, v)));
}

function areaFromTangents(u, v) {
  const value = dot(u, u) * dot(v, v) - dot(u, v) ** 2;
  return Math.sqrt(Math.max(0, value));
}

function angleBetween(a, b) {
  const denom = norm(a) * norm(b);
  if (!(denom > EPS)) throw new RangeError('cannot compare zero-length tangent orientation');
  const cosine = Math.max(-1, Math.min(1, dot(a, b) / denom));
  return Math.acos(cosine);
}

function gridTopology(width, height) {
  const vertices = width * height;
  const edges = (width - 1) * height + (height - 1) * width;
  const faces = (width - 1) * (height - 1);
  return {
    vertices,
    edges,
    faces,
    eulerCharacteristic: vertices - edges + faces,
    connectedComponents: 1,
    changed: false,
    capability: 'fixed-grid-connectivity-under-s1-rotations/v0'
  };
}

function cellTangents(points, width, row, col) {
  const i = row * width + col;
  return {
    u: sub(points[i + 1], points[i]),
    v: sub(points[i + width], points[i])
  };
}

function principalStretches(originTangents, liveTangents) {
  const u0 = originTangents.u, v0 = originTangents.v;
  const u1 = liveTangents.u, v1 = liveTangents.v;
  const g00 = dot(u0, u0), g01 = dot(u0, v0), g11 = dot(v0, v0);
  const h00 = dot(u1, u1), h01 = dot(u1, v1), h11 = dot(v1, v1);
  const detG = g00 * g11 - g01 * g01;
  if (!(detG > EPS)) throw new RangeError('source image grid contains a degenerate cell');

  const a = (g11 * h00 - g01 * h01) / detG;
  const b = (g11 * h01 - g01 * h11) / detG;
  const c = (-g01 * h00 + g00 * h01) / detG;
  const d = (-g01 * h01 + g00 * h11) / detG;
  const trace = a + d;
  const determinant = a * d - b * c;
  const discriminant = Math.max(0, trace * trace - 4 * determinant);
  const root = Math.sqrt(discriminant);
  const lambda1 = Math.max(0, (trace - root) / 2);
  const lambda2 = Math.max(0, (trace + root) / 2);
  return [Math.sqrt(lambda1), Math.sqrt(lambda2)];
}

function cosineBetween(u, v) {
  const denom = norm(u) * norm(v);
  if (!(denom > EPS)) throw new RangeError('grid tangent must be nonzero');
  return dot(u, v) / denom;
}

function curvatureProxy(points, width, height) {
  let maximum = 0;
  const secondDifference = (left, center, right) => left.map((value, index) => value - 2 * center[index] + right[index]);
  for (let row = 0; row < height; row++) {
    for (let col = 1; col + 1 < width; col++) {
      const i = row * width + col;
      maximum = Math.max(maximum, norm(secondDifference(points[i - 1], points[i], points[i + 1])));
    }
  }
  for (let row = 1; row + 1 < height; row++) {
    for (let col = 0; col < width; col++) {
      const i = row * width + col;
      maximum = Math.max(maximum, norm(secondDifference(points[i - width], points[i], points[i + width])));
    }
  }
  return maximum;
}

function intrinsicMetrics(originPoints, livePoints, width, height) {
  let principalStretchMin = Infinity;
  let principalStretchMax = 0;
  let maxShearChange = 0;
  let maxAreaRatioDeviation = 0;
  let maxOrientationChangeRadians = 0;

  for (let row = 0; row + 1 < height; row++) {
    for (let col = 0; col + 1 < width; col++) {
      const origin = cellTangents(originPoints, width, row, col);
      const live = cellTangents(livePoints, width, row, col);
      const stretches = principalStretches(origin, live);
      principalStretchMin = Math.min(principalStretchMin, stretches[0]);
      principalStretchMax = Math.max(principalStretchMax, stretches[1]);
      maxShearChange = Math.max(maxShearChange, Math.abs(cosineBetween(live.u, live.v) - cosineBetween(origin.u, origin.v)));
      const originArea = areaFromTangents(origin.u, origin.v);
      const liveArea = areaFromTangents(live.u, live.v);
      if (!(originArea > EPS)) throw new RangeError('source image grid cell has zero area');
      maxAreaRatioDeviation = Math.max(maxAreaRatioDeviation, Math.abs(liveArea / originArea - 1));
      maxOrientationChangeRadians = Math.max(
        maxOrientationChangeRadians,
        angleBetween(origin.u, live.u),
        angleBetween(origin.v, live.v)
      );
    }
  }

  return {
    principalStretchMin,
    principalStretchMax,
    maxShearChange,
    maxAreaRatioDeviation,
    maxOrientationChangeRadians,
    curvatureProxyOriginMax: curvatureProxy(originPoints, width, height),
    curvatureProxyLiveMax: curvatureProxy(livePoints, width, height),
    interpretation: 'intrinsic-grid-metric-separate-from-observer-projection'
  };
}

function edgePairs(width, height) {
  const pairs = [];
  for (let row = 0; row < height; row++) {
    for (let col = 0; col + 1 < width; col++) {
      const i = row * width + col;
      pairs.push([i, i + 1]);
    }
  }
  for (let row = 0; row + 1 < height; row++) {
    for (let col = 0; col < width; col++) {
      const i = row * width + col;
      pairs.push([i, i + width]);
    }
  }
  return pairs;
}

function projectedMetrics(intrinsicPoints, projectedPoints, width, height) {
  const projected3 = projectedPoints.map(point => point.slice(0, 3));
  let maxEdgeScaleDeviation = 0;
  for (const [a, b] of edgePairs(width, height)) {
    const intrinsicLength = norm(sub(intrinsicPoints[b], intrinsicPoints[a]));
    const projectedLength = norm(sub(projected3[b], projected3[a]));
    if (!(intrinsicLength > EPS)) throw new RangeError('intrinsic grid edge has zero length');
    maxEdgeScaleDeviation = Math.max(maxEdgeScaleDeviation, Math.abs(projectedLength / intrinsicLength - 1));
  }

  let maxAreaScaleDeviation = 0;
  for (let row = 0; row + 1 < height; row++) {
    for (let col = 0; col + 1 < width; col++) {
      const intrinsic = cellTangents(intrinsicPoints, width, row, col);
      const projected = cellTangents(projected3, width, row, col);
      const intrinsicArea = areaFromTangents(intrinsic.u, intrinsic.v);
      const projectedArea = areaFromTangents(projected.u, projected.v);
      if (!(intrinsicArea > EPS)) throw new RangeError('intrinsic grid cell has zero area');
      maxAreaScaleDeviation = Math.max(maxAreaScaleDeviation, Math.abs(projectedArea / intrinsicArea - 1));
    }
  }
  return { maxEdgeScaleDeviation, maxAreaScaleDeviation };
}

function normalizeActions(actions) {
  if (!Array.isArray(actions)) throw new TypeError('actions must be an array');
  return actions.map(move => ({ plane: move.plane, degrees: move.degrees }));
}

export function analyzeImageSurface(source, actions = [], observer = DEFAULT_OBSERVER) {
  const normalizedSource = normalizeSource(source);
  const normalizedActions = normalizeActions(actions);
  const normalizedObserver = normalizeObserver(observer);
  const points = gridPoints(normalizedSource.width, normalizedSource.height);
  const trajectory = materializeTrajectory(points, normalizedActions);
  const originHash = hashValue(trajectory.origin.points);
  const mirrorHash = hashValue(trajectory.mirror.points);
  const liveHash = hashValue(trajectory.live.points);
  const payloadHash = hashValue({
    width: normalizedSource.width,
    height: normalizedSource.height,
    channels: normalizedSource.channels,
    samples: normalizedSource.samples
  });

  const intrinsic = intrinsicMetrics(
    trajectory.origin.points,
    trajectory.live.points,
    normalizedSource.width,
    normalizedSource.height
  );
  const mirrorProjected = projectState(trajectory.mirror, normalizedObserver);
  const liveProjected = projectState(trajectory.live, normalizedObserver);
  const mirrorProjectionMetrics = projectedMetrics(
    trajectory.mirror.points,
    mirrorProjected,
    normalizedSource.width,
    normalizedSource.height
  );
  const liveProjectionMetrics = projectedMetrics(
    trajectory.live.points,
    liveProjected,
    normalizedSource.width,
    normalizedSource.height
  );
  const comparison = compareStates(trajectory.live, trajectory.mirror);

  return deepFreeze({
    schema: IMAGE_SURFACE_ANALYSIS_SCHEMA,
    source: {
      ...normalizedSource,
      payloadHash,
      geometryHash: originHash
    },
    trajectory: {
      operatorVersion: OPERATOR_VERSION,
      actions: normalizedActions,
      mirrorGeometryHash: mirrorHash,
      liveGeometryHash: liveHash,
      liveEqualsMirror: comparison.equal,
      liveMaxDeltaFromMirror: comparison.maxAbsDelta
    },
    intrinsic,
    topology: gridTopology(normalizedSource.width, normalizedSource.height),
    projection: {
      observer: normalizedObserver,
      mirror: mirrorProjectionMetrics,
      live: liveProjectionMetrics,
      changeFromMirrorMaxEdgeScaleDeviation: Math.abs(liveProjectionMetrics.maxEdgeScaleDeviation - mirrorProjectionMetrics.maxEdgeScaleDeviation),
      interpretation: 'observer-projection-distortion-not-intrinsic-deformation'
    },
    historyAuthority: 'reuse-s1-trajectory-no-second-history',
    authority: 'image-surface-observation-only',
    claimCeiling: 'IMAGE_DEFORMATION != PHYSICAL_DEFORMATION; GEOMETRIC_RESEMBLANCE != ALGEBRAIC_GEOMETRY_EVIDENCE; observer projection distortion remains separate from intrinsic deformation; fixed-grid topology under supported v0 S1 rotations is not a general topology-change detector.'
  });
}
