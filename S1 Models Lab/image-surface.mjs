import { createState, materializeTrajectory, compareStates } from './core.mjs';
import {
  EXPERIENCE_SCHEMA,
  canonicalJson,
  fnv1a64,
  makeExperience,
  replayExperience,
  reframeExperience,
  validateExperience
} from './experience.mjs';
import { normalizeObserver, projectPoint4 } from './observer.mjs';

export const IMAGE_SURFACE_SCHEMA = 's1-image-surface/v0';
export const IMAGE_SOURCE_SCHEMA = 's1-image-source/v0';
export const IMAGE_PARAMETERIZATION_VERSION = 's1-image-grid-height/v0';
export const IMAGE_SURFACE_CLAIM_CEILING = Object.freeze([
  'IMAGE_DEFORMATION != PHYSICAL_DEFORMATION',
  'GEOMETRIC_RESEMBLANCE != ALGEBRAIC_GEOMETRY_EVIDENCE',
  'PROJECTION_DISTORTION != INTRINSIC_DEFORMATION',
  'FINITE_GRID_CONNECTIVITY != CONTINUUM_TOPOLOGY'
]);

const SESSION_KEYS = Object.freeze(['schema','id','source','surface','experience','historyAuthority','claimCeiling']);
const SOURCE_KEYS = Object.freeze(['schema','id','width','height','channels','pixels','mediaType']);
const SURFACE_KEYS = Object.freeze(['id','sourceImageId','width','height','points4','cells','surfaceOptions','parameterizationVersion']);
const SURFACE_OPTION_KEYS = Object.freeze(['heightChannel','heightScale']);
const CREATE_KEYS = Object.freeze(['source','surfaceOptions','actions','observer','provenance']);
const EPSILON = 1e-12;

function deepFreeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    for (const child of Object.values(value)) deepFreeze(child);
    Object.freeze(value);
  }
  return value;
}

function cloneCanonical(value) {
  return JSON.parse(canonicalJson(value));
}

function assertPlain(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new TypeError(`${label} must be an object`);
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) throw new TypeError(`${label} must be a plain object`);
}

function assertOnlyKeys(value, allowed, label) {
  for (const key of Object.keys(value)) if (!allowed.includes(key)) throw new RangeError(`unsupported ${label} field: ${key}`);
}

function normalizeSource(input) {
  assertPlain(input, 'image source');
  const allowed = ['width','height','channels','pixels','mediaType'];
  assertOnlyKeys(input, allowed, 'image source');
  if (!Number.isInteger(input.width) || input.width < 2) throw new RangeError('image width must be an integer >= 2');
  if (!Number.isInteger(input.height) || input.height < 2) throw new RangeError('image height must be an integer >= 2');
  if (!Number.isInteger(input.channels) || input.channels < 1 || input.channels > 4) throw new RangeError('image channels must be an integer from 1 through 4');
  if (!Array.isArray(input.pixels) || input.pixels.length !== input.width * input.height * input.channels) {
    throw new RangeError('pixel array length must equal width * height * channels');
  }
  if (input.pixels.some(value => !Number.isFinite(value) || value < 0 || value > 255)) {
    throw new RangeError('pixel values must be finite numbers in [0, 255]');
  }
  if (typeof input.mediaType !== 'string' || !input.mediaType) throw new TypeError('image mediaType is required');
  const base = {
    schema: IMAGE_SOURCE_SCHEMA,
    width: input.width,
    height: input.height,
    channels: input.channels,
    pixels: [...input.pixels],
    mediaType: input.mediaType
  };
  return deepFreeze({ ...base, id: fnv1a64(canonicalJson(base)) });
}

function validateSource(record) {
  assertPlain(record, 'image source record');
  assertOnlyKeys(record, SOURCE_KEYS, 'image source record');
  if (record.schema !== IMAGE_SOURCE_SCHEMA) throw new RangeError('unsupported image source schema');
  const rebuilt = normalizeSource({
    width: record.width,
    height: record.height,
    channels: record.channels,
    pixels: record.pixels,
    mediaType: record.mediaType
  });
  if (record.id !== rebuilt.id) throw new RangeError('image source id does not match canonical payload');
  return rebuilt;
}

function normalizeSurfaceOptions(input, channels) {
  const options = input ?? {};
  assertPlain(options, 'surface options');
  assertOnlyKeys(options, SURFACE_OPTION_KEYS, 'surface options');
  const heightChannel = options.heightChannel ?? 0;
  const heightScale = options.heightScale ?? 0;
  if (!Number.isInteger(heightChannel) || heightChannel < 0 || heightChannel >= channels) {
    throw new RangeError('heightChannel must select an existing image channel');
  }
  if (!Number.isFinite(heightScale) || heightScale < 0) throw new RangeError('heightScale must be finite and non-negative');
  return deepFreeze({ heightChannel, heightScale });
}

function pixelAt(source, row, column, channel) {
  return source.pixels[(row * source.width + column) * source.channels + channel];
}

function createSurface(sourceRecord, optionsInput = {}) {
  const source = validateSource(sourceRecord);
  const surfaceOptions = normalizeSurfaceOptions(optionsInput, source.channels);
  const points4 = [];
  for (let row = 0; row < source.height; row++) {
    const y = source.height === 1 ? 0 : 1 - 2 * row / (source.height - 1);
    for (let column = 0; column < source.width; column++) {
      const x = source.width === 1 ? 0 : -1 + 2 * column / (source.width - 1);
      const sample = pixelAt(source, row, column, surfaceOptions.heightChannel) / 255;
      const z = sample * surfaceOptions.heightScale;
      points4.push([x, y, z, 0]);
    }
  }
  const cells = [];
  for (let row = 0; row < source.height - 1; row++) {
    for (let column = 0; column < source.width - 1; column++) {
      const tl = row * source.width + column;
      const tr = tl + 1;
      const bl = (row + 1) * source.width + column;
      const br = bl + 1;
      cells.push([tl, tr, bl, br]);
    }
  }
  const base = {
    sourceImageId: source.id,
    width: source.width,
    height: source.height,
    points4,
    cells,
    surfaceOptions,
    parameterizationVersion: IMAGE_PARAMETERIZATION_VERSION
  };
  return deepFreeze({ ...base, id: fnv1a64(canonicalJson(base)) });
}

function validateSurface(record, sourceRecord) {
  assertPlain(record, 'image surface record');
  assertOnlyKeys(record, SURFACE_KEYS, 'image surface record');
  const source = validateSource(sourceRecord);
  const rebuilt = createSurface(source, record.surfaceOptions);
  if (record.id !== rebuilt.id) throw new RangeError('image surface id does not match canonical payload');
  if (canonicalJson(record) !== canonicalJson(rebuilt)) throw new RangeError('image surface payload does not match source parameterization');
  return rebuilt;
}

function comparisonSummary(comparison) {
  return { equal: comparison.equal, maxAbsDelta: comparison.maxAbsDelta };
}

export function createImageSurfaceSession(input) {
  assertPlain(input, 'image surface session input');
  assertOnlyKeys(input, CREATE_KEYS, 'image surface session input');
  const source = normalizeSource(input.source);
  const surface = createSurface(source, input.surfaceOptions ?? {});
  const actions = input.actions ?? [];
  if (!Array.isArray(actions)) throw new TypeError('actions must be an array');
  const observer = normalizeObserver(input.observer ?? {});
  const provenance = input.provenance ?? {};
  assertPlain(provenance, 'image surface provenance');

  const trajectory = materializeTrajectory(surface.points4, actions);
  const againstMirror = compareStates(trajectory.live, trajectory.mirror);
  const againstPrevious = compareStates(trajectory.live, trajectory.previous);
  const experience = makeExperience({
    initialState: surface.id,
    mirrorId: `mirror:${surface.id}`,
    shell: 'comparison',
    actions,
    observer,
    observerField: {
      version: 's1-observer-field/v0',
      taskVersion: 's1-observer-task/v0',
      densityId: `image-surface:${surface.id}`,
      calibrations: []
    },
    checkpoints: [],
    comparisons: {
      obligation: 'image-surface-live-vs-source-mirror',
      againstMirror: comparisonSummary(againstMirror),
      againstPrevious: comparisonSummary(againstPrevious)
    },
    relations: { familyId: `image-surface:${source.id}`, parentId: null, relatedIds: [] },
    provenance: {
      ...cloneCanonical(provenance),
      adapter: IMAGE_SURFACE_SCHEMA,
      sourceImageId: source.id,
      surfaceId: surface.id
    }
  });

  const base = {
    schema: IMAGE_SURFACE_SCHEMA,
    source,
    surface,
    experience,
    historyAuthority: EXPERIENCE_SCHEMA,
    claimCeiling: IMAGE_SURFACE_CLAIM_CEILING
  };
  return deepFreeze({ ...base, id: fnv1a64(canonicalJson(base)) });
}

export function validateImageSurfaceSession(record) {
  assertPlain(record, 'image surface session');
  assertOnlyKeys(record, SESSION_KEYS, 'image surface session');
  if (record.schema !== IMAGE_SURFACE_SCHEMA) throw new RangeError('unsupported image surface schema');
  if (record.historyAuthority !== EXPERIENCE_SCHEMA) throw new RangeError('image surface history authority must remain s1-experience/v0');
  if (canonicalJson(record.claimCeiling) !== canonicalJson(IMAGE_SURFACE_CLAIM_CEILING)) throw new RangeError('image surface claim ceiling mismatch');
  const source = validateSource(record.source);
  const surface = validateSurface(record.surface, source);
  const experience = validateExperience(record.experience);
  if (experience.initialState !== surface.id || experience.mirrorId !== `mirror:${surface.id}` || experience.shell !== 'comparison') {
    throw new RangeError('image surface experience does not reference the canonical surface');
  }
  const base = {
    schema: IMAGE_SURFACE_SCHEMA,
    source,
    surface,
    experience,
    historyAuthority: EXPERIENCE_SCHEMA,
    claimCeiling: IMAGE_SURFACE_CLAIM_CEILING
  };
  const id = fnv1a64(canonicalJson(base));
  if (record.id !== id) throw new RangeError('image surface session id does not match canonical payload');
  return deepFreeze({ ...base, id });
}

export function recoverSourceImage(session) {
  const valid = validateImageSurfaceSession(session);
  return deepFreeze({
    width: valid.source.width,
    height: valid.source.height,
    channels: valid.source.channels,
    pixels: [...valid.source.pixels],
    mediaType: valid.source.mediaType,
    id: valid.source.id
  });
}

function registryFor(session) {
  return new Map([[session.surface.id, session.surface]]);
}

export function replayImageSurface(session) {
  const valid = validateImageSurfaceSession(session);
  return replayExperience(valid.experience, registryFor(valid));
}

export function reframeImageSurface(session, observer) {
  const valid = validateImageSurfaceSession(session);
  const reframe = reframeExperience(valid.experience, observer, registryFor(valid));
  return deepFreeze({
    sourceImageId: valid.source.id,
    sourceEventId: valid.experience.id,
    reframe
  });
}

function subtract(a, b) {
  return a.map((value, index) => value - b[index]);
}

function dot(a, b) {
  return a.reduce((sum, value, index) => sum + value * b[index], 0);
}

function norm(vector) {
  return Math.hypot(...vector);
}

function clampUnit(value) {
  return Math.max(-1, Math.min(1, value));
}

function frame(points, cell) {
  const origin = points[cell[0]];
  return { u: subtract(points[cell[1]], origin), v: subtract(points[cell[2]], origin) };
}

function metric(frameValue) {
  const uu = dot(frameValue.u, frameValue.u);
  const uv = dot(frameValue.u, frameValue.v);
  const vv = dot(frameValue.v, frameValue.v);
  const det = uu * vv - uv * uv;
  if (!(uu > 0) || !(vv > 0) || !(det > 0)) throw new RangeError('surface cell metric must be non-degenerate');
  return {
    uu,
    uv,
    vv,
    determinant: det,
    area: Math.sqrt(det),
    shearCosine: uv / Math.sqrt(uu * vv)
  };
}

function principalStretches(originMetric, liveMetric) {
  const det0 = originMetric.determinant;
  const a = (originMetric.vv * liveMetric.uu - originMetric.uv * liveMetric.uv) / det0;
  const b = (originMetric.vv * liveMetric.uv - originMetric.uv * liveMetric.vv) / det0;
  const c = (-originMetric.uv * liveMetric.uu + originMetric.uu * liveMetric.uv) / det0;
  const d = (-originMetric.uv * liveMetric.uv + originMetric.uu * liveMetric.vv) / det0;
  const trace = a + d;
  const determinant = a * d - b * c;
  const discriminant = Math.max(0, trace * trace - 4 * determinant);
  const root = Math.sqrt(discriminant);
  const lambda1 = Math.max(0, (trace + root) / 2);
  const lambda2 = Math.max(0, (trace - root) / 2);
  return [Math.sqrt(lambda1), Math.sqrt(lambda2)];
}

function metricChange(originPoints, livePoints, cells) {
  let maxPrincipalStretchDeltaFromOne = 0;
  let maxShearCosineDelta = 0;
  let maxAreaRatioDeltaFromOne = 0;
  for (const cell of cells) {
    const originMetric = metric(frame(originPoints, cell));
    const liveMetric = metric(frame(livePoints, cell));
    for (const stretch of principalStretches(originMetric, liveMetric)) {
      maxPrincipalStretchDeltaFromOne = Math.max(maxPrincipalStretchDeltaFromOne, Math.abs(stretch - 1));
    }
    maxShearCosineDelta = Math.max(maxShearCosineDelta, Math.abs(liveMetric.shearCosine - originMetric.shearCosine));
    maxAreaRatioDeltaFromOne = Math.max(maxAreaRatioDeltaFromOne, Math.abs(liveMetric.area / originMetric.area - 1));
  }
  return { maxPrincipalStretchDeltaFromOne, maxShearCosineDelta, maxAreaRatioDeltaFromOne };
}

function ambientOrientationChange(originPoints, livePoints, cells) {
  let maxAmbientOrientationAngleRad = 0;
  for (const cell of cells) {
    const a = frame(originPoints, cell).u;
    const b = frame(livePoints, cell).u;
    const denominator = norm(a) * norm(b);
    if (!(denominator > 0)) continue;
    maxAmbientOrientationAngleRad = Math.max(maxAmbientOrientationAngleRad, Math.acos(clampUnit(dot(a, b) / denominator)));
  }
  return { maxAmbientOrientationAngleRad };
}

function curvatureProxy(points, width, height) {
  let maximum = 0;
  for (let row = 1; row < height - 1; row++) {
    for (let column = 1; column < width - 1; column++) {
      const centerIndex = row * width + column;
      const neighbors = [centerIndex - 1, centerIndex + 1, centerIndex - width, centerIndex + width];
      const laplacian = points[centerIndex].map((value, axis) =>
        neighbors.reduce((sum, index) => sum + points[index][axis], 0) - 4 * value
      );
      maximum = Math.max(maximum, norm(laplacian));
    }
  }
  return maximum;
}

function gridTopology(width, height) {
  return {
    vertices: width * height,
    edges: (width - 1) * height + (height - 1) * width,
    cells: (width - 1) * (height - 1),
    connectedComponents: 1
  };
}

export function measureImageSurface(session) {
  const valid = validateImageSurfaceSession(session);
  const origin = createState(valid.surface.points4);
  const live = replayExperience(valid.experience, registryFor(valid));
  const cells = valid.surface.cells;
  const intrinsic = metricChange(origin.points, live.points, cells);
  const extrinsic = ambientOrientationChange(origin.points, live.points, cells);
  const originCurvature = curvatureProxy(origin.points, valid.surface.width, valid.surface.height);
  const liveCurvature = curvatureProxy(live.points, valid.surface.width, valid.surface.height);
  const topology = gridTopology(valid.surface.width, valid.surface.height);

  const projectedOrigin = origin.points.map(point => projectPoint4(point, valid.experience.observer).slice(0, 3));
  const projectedLive = live.points.map(point => projectPoint4(point, valid.experience.observer).slice(0, 3));
  const projectionMetric = metricChange(projectedOrigin, projectedLive, cells);

  return deepFreeze({
    sourceImageId: valid.source.id,
    sourceEventId: valid.experience.id,
    intrinsic,
    extrinsic,
    curvature: {
      method: 'grid-vector-laplacian-norm/v0',
      originMax: originCurvature,
      liveMax: liveCurvature,
      continuumCurvatureClaim: false
    },
    topology: {
      method: 'fixed-grid-connectivity/v0',
      ...topology,
      connectivityChanged: false,
      continuumTopologyClaim: false
    },
    areaElement: { dimension: 2, method: 'sqrt(det(first-fundamental-form))/v0' },
    projection: {
      ...projectionMetric,
      projectionDistortionDetected: projectionMetric.maxPrincipalStretchDeltaFromOne > EPSILON || projectionMetric.maxShearCosineDelta > EPSILON || projectionMetric.maxAreaRatioDeltaFromOne > EPSILON,
      intrinsicDeformationImplied: false
    },
    claimCeiling: IMAGE_SURFACE_CLAIM_CEILING
  });
}
