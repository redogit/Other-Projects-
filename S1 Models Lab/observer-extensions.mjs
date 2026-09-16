import { canonicalJson, fnv1a64, replayExperience, validateExperience } from './experience.mjs';
import { distance, projectPoint, slicePoints } from './dimension-ladder.mjs';

export const OBSERVATION_SCHEMA = 's1-observation/v0';
export const OBSERVER_ORDER = Object.freeze(['projection', 'slice', 'metric', 'topology', 'sound']);
export const OBSERVER_BOUNDARIES = Object.freeze([
  'OBSERVER != TRUTH_AUTHORITY',
  'SAME_EVENT != SAME_OBSERVATION'
]);

const MAPPING_VERSION = Object.freeze({
  projection: 's1-projection/drop-axis-v0',
  slice: 's1-slice/coordinate-hyperplane-v0',
  metric: 's1-metric/origin-radius-v0',
  topology: 's1-topology/finite-incidence-proxy-v0',
  sound: 's1-sonification/action-triad-v0'
});
const OBSERVATION_KEYS = Object.freeze([
  'schema', 'id', 'sourceEventId', 'observerType', 'mappingVersion', 'parameters', 'payload',
  'losses', 'invariants', 'evidenceRole', 'truthAuthority'
]);
const MIDI_BASE = Object.freeze({ xw: 60, yw: 64, zw: 67 });
const METRIC_EPSILON = 1e-12;

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

function assertOnlyKeys(value, allowed, label) {
  for (const key of Object.keys(value)) if (!allowed.includes(key)) throw new RangeError(`unsupported ${label} field: ${key}`);
}

function assertPlainRecord(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new TypeError(`${label} must be an object`);
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) throw new TypeError(`${label} must be a plain object`);
}

function assertStringArray(value, label) {
  if (!Array.isArray(value) || value.some(entry => typeof entry !== 'string' || entry.length === 0)) {
    throw new TypeError(`${label} must contain non-empty strings`);
  }
}

function makeObservationRecord({ sourceEventId, observerType, parameters, payload, losses, invariants }) {
  if (typeof sourceEventId !== 'string' || !sourceEventId) throw new TypeError('sourceEventId is required');
  if (!OBSERVER_ORDER.includes(observerType)) throw new RangeError(`unsupported observer type: ${observerType}`);
  assertPlainRecord(parameters, 'parameters');
  assertPlainRecord(payload, 'payload');
  assertStringArray(losses, 'losses');
  assertStringArray(invariants, 'invariants');

  const base = {
    schema: OBSERVATION_SCHEMA,
    sourceEventId,
    observerType,
    mappingVersion: MAPPING_VERSION[observerType],
    parameters: cloneCanonical(parameters),
    payload: cloneCanonical(payload),
    losses: cloneCanonical(losses),
    invariants: cloneCanonical(invariants),
    evidenceRole: 'derived-observation',
    truthAuthority: false
  };
  const id = fnv1a64(canonicalJson(base));
  return deepFreeze({ ...base, id });
}

export function validateObservationRecord(record) {
  assertPlainRecord(record, 'observation record');
  assertOnlyKeys(record, OBSERVATION_KEYS, 'observation record');
  if (record.schema !== OBSERVATION_SCHEMA) throw new RangeError('unsupported observation schema');
  if (!OBSERVER_ORDER.includes(record.observerType)) throw new RangeError(`unsupported observer type: ${record.observerType}`);
  if (record.mappingVersion !== MAPPING_VERSION[record.observerType]) throw new RangeError('unsupported observer mapping version');
  if (record.evidenceRole !== 'derived-observation') throw new RangeError('observation evidence role must remain derived-observation');
  if (record.truthAuthority !== false) throw new RangeError('observer records cannot be truth authority');
  const rebuilt = makeObservationRecord({
    sourceEventId: record.sourceEventId,
    observerType: record.observerType,
    parameters: record.parameters,
    payload: record.payload,
    losses: record.losses,
    invariants: record.invariants
  });
  if (typeof record.id !== 'string' || record.id !== rebuilt.id) throw new RangeError('observation id does not match canonical payload');
  return rebuilt;
}

function lookupGeometry(registry, id) {
  const geometry = registry instanceof Map ? registry.get(id) : registry?.[id];
  if (!geometry || geometry.id !== id || !Array.isArray(geometry.points4) || geometry.points4.length === 0) {
    throw new RangeError(`unknown observation geometry: ${id}`);
  }
  for (const point of geometry.points4) {
    if (!Array.isArray(point) || point.length !== 4 || point.some(value => !Number.isFinite(value))) {
      throw new TypeError('observation geometry must contain finite 4D points');
    }
  }
  return geometry;
}

function assertAxis(axis) {
  if (!Number.isInteger(axis) || axis < 0 || axis > 3) throw new RangeError('axis must be an integer from 0 through 3');
}

function bounds(points) {
  if (!Array.isArray(points) || points.length === 0) throw new TypeError('points are required');
  const dimension = points[0].length;
  if (!Number.isInteger(dimension) || dimension < 1) throw new RangeError('points must have positive dimension');
  if (points.some(point => !Array.isArray(point) || point.length !== dimension || point.some(value => !Number.isFinite(value)))) {
    throw new TypeError('points must have matching finite dimensions');
  }
  const minima = Array(dimension).fill(Infinity);
  const maxima = Array(dimension).fill(-Infinity);
  for (const point of points) {
    for (let axis = 0; axis < dimension; axis++) {
      minima[axis] = Math.min(minima[axis], point[axis]);
      maxima[axis] = Math.max(maxima[axis], point[axis]);
    }
  }
  return Object.freeze(minima.map((min, axis) => Object.freeze({ min, max: maxima[axis], extent: maxima[axis] - min })));
}

function maxExtentDelta(a, b) {
  if (a.length !== b.length) throw new RangeError('bounds must have matching dimensions');
  return Math.max(...a.map((entry, index) => Math.abs(entry.extent - b[index].extent)));
}

function projectionObservation(event, originPoints, livePoints, config = {}) {
  assertPlainRecord(config, 'projection config');
  assertOnlyKeys(config, ['axis'], 'projection config');
  const axis = config.axis ?? 3;
  assertAxis(axis);
  const originProjected = originPoints.map(point => projectPoint(point, axis));
  const liveProjected = livePoints.map(point => projectPoint(point, axis));
  const originBounds = bounds(originProjected);
  const liveBounds = bounds(liveProjected);
  const extentDelta = maxExtentDelta(originBounds, liveBounds);
  return makeObservationRecord({
    sourceEventId: event.id,
    observerType: 'projection',
    parameters: { axis },
    payload: {
      sourceDimension: 4,
      observedDimension: 3,
      pointCount: livePoints.length,
      originBounds,
      liveBounds,
      maxExtentDelta: extentDelta,
      extentChanged: extentDelta > METRIC_EPSILON,
      nonInjectiveByContract: true
    },
    losses: ['dropped coordinate is not recoverable from projection alone'],
    invariants: ['source event identity', 'projected point count']
  });
}

function selectedIndices(points, axis, value, epsilon) {
  return points.flatMap((point, index) => Math.abs(point[axis] - value) <= epsilon ? [index] : []);
}

function sliceObservation(event, originPoints, livePoints, config = {}) {
  assertPlainRecord(config, 'slice config');
  assertOnlyKeys(config, ['axis', 'value', 'epsilon'], 'slice config');
  const axis = config.axis ?? 3;
  const value = config.value ?? 0;
  const epsilon = config.epsilon ?? 1e-9;
  assertAxis(axis);
  if (!Number.isFinite(value)) throw new TypeError('slice value must be finite');
  if (!Number.isFinite(epsilon) || epsilon < 0) throw new RangeError('slice epsilon must be finite and non-negative');

  const originSlice = slicePoints(originPoints, { axis, value, epsilon });
  const liveSlice = slicePoints(livePoints, { axis, value, epsilon });
  const originSelectedIndices = selectedIndices(originPoints, axis, value, epsilon);
  const liveSelectedIndices = selectedIndices(livePoints, axis, value, epsilon);
  if (originSlice.length !== originSelectedIndices.length || liveSlice.length !== liveSelectedIndices.length) {
    throw new Error('slice index reconstruction mismatch');
  }

  return makeObservationRecord({
    sourceEventId: event.id,
    observerType: 'slice',
    parameters: { axis, value, epsilon },
    payload: {
      sourceDimension: 4,
      sourcePointCount: livePoints.length,
      originSelectedIndices,
      liveSelectedIndices,
      originSelectedCount: originSelectedIndices.length,
      liveSelectedCount: liveSelectedIndices.length,
      selectionChanged: canonicalJson(originSelectedIndices) !== canonicalJson(liveSelectedIndices)
    },
    losses: ['points outside the declared slice are not observed'],
    invariants: ['source event identity', 'source point identity for retained indices']
  });
}

function radius(point) {
  return Math.hypot(...point);
}

function metricObservation(event, originPoints, livePoints) {
  if (originPoints.length !== livePoints.length) throw new RangeError('metric observer requires matching point counts');
  let maxOriginRadiusDelta = 0;
  let maxPointDisplacement = 0;
  for (let index = 0; index < originPoints.length; index++) {
    maxOriginRadiusDelta = Math.max(maxOriginRadiusDelta, Math.abs(radius(originPoints[index]) - radius(livePoints[index])));
    maxPointDisplacement = Math.max(maxPointDisplacement, distance(originPoints[index], livePoints[index]));
  }
  return makeObservationRecord({
    sourceEventId: event.id,
    observerType: 'metric',
    parameters: { epsilon: METRIC_EPSILON, invariant: 'origin-centered-radius' },
    payload: {
      pointCount: livePoints.length,
      maxOriginRadiusDelta,
      maxPointDisplacement,
      originRadiusPreserved: maxOriginRadiusDelta <= METRIC_EPSILON,
      intrinsicRigidityClaim: false
    },
    losses: ['origin-centered radii alone do not establish full intrinsic rigidity'],
    invariants: ['source event identity', 'point index correspondence', 'origin-centered radius under declared rotations']
  });
}

function finiteIncidencePayload(geometry) {
  const groups = Array.isArray(geometry.groups) ? geometry.groups : [];
  const pointCount = geometry.points4.length;
  const incidenceCounts = Array(pointCount).fill(0);
  const normalizedGroups = groups.map((group, index) => {
    if (!group || typeof group !== 'object' || Array.isArray(group) || !Array.isArray(group.pointIndices)) {
      throw new TypeError('geometry groups must expose pointIndices');
    }
    const indices = [...new Set(group.pointIndices)];
    if (indices.some(value => !Number.isInteger(value) || value < 0 || value >= pointCount)) throw new RangeError('group point index out of range');
    for (const pointIndex of indices) incidenceCounts[pointIndex]++;
    return {
      label: typeof group.cell === 'string' ? group.cell : typeof group.band === 'string' ? group.band : `group-${index}`,
      size: indices.length,
      pointIndices: indices
    };
  });
  const histogramMap = new Map();
  for (const count of incidenceCounts) histogramMap.set(count, (histogramMap.get(count) ?? 0) + 1);
  const incidenceHistogram = [...histogramMap.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([incidences, count]) => ({ incidences, count }));
  const incidenceSignature = fnv1a64(canonicalJson(normalizedGroups));
  return {
    sourcePointCount: pointCount,
    groupCount: normalizedGroups.length,
    groupSizes: normalizedGroups.map(group => group.size).sort((a, b) => a - b),
    incidenceHistogram,
    incidenceSignature,
    declaredGroupIncidenceAvailable: normalizedGroups.length > 0,
    continuumTopologyClaim: false
  };
}

function topologyObservation(event, geometry) {
  return makeObservationRecord({
    sourceEventId: event.id,
    observerType: 'topology',
    parameters: { method: 'finite-declared-group-incidence' },
    payload: finiteIncidencePayload(geometry),
    losses: ['continuum topology is not inferable from this finite incidence proxy'],
    invariants: ['source event identity', 'declared point/group incidence']
  });
}

function soundObservation(event) {
  const durationMs = 120;
  const notes = event.actions.map((move, index) => ({
    index,
    plane: move.plane,
    degrees: move.degrees,
    midi: MIDI_BASE[move.plane] + (move.degrees < 0 ? -12 : 0),
    durationMs
  }));
  return makeObservationRecord({
    sourceEventId: event.id,
    observerType: 'sound',
    parameters: { durationMs, negativeDirectionOctaveOffset: -12, planeMidi: MIDI_BASE },
    payload: { notes, evidenceAdded: false },
    losses: ['sonification does not add evidentiary authority'],
    invariants: ['source event identity', 'action chronology']
  });
}

export function observeExperience(record, geometryRegistry, options = {}) {
  assertPlainRecord(options, 'observer options');
  assertOnlyKeys(options, ['projection', 'slice'], 'observer options');
  const event = validateExperience(record);
  const geometry = lookupGeometry(geometryRegistry, event.initialState);
  const replayed = replayExperience(event, geometryRegistry);
  const originPoints = geometry.points4;
  const livePoints = replayed.points;

  const observations = [
    projectionObservation(event, originPoints, livePoints, options.projection ?? {}),
    sliceObservation(event, originPoints, livePoints, options.slice ?? {}),
    metricObservation(event, originPoints, livePoints),
    topologyObservation(event, geometry),
    soundObservation(event)
  ];
  return deepFreeze(observations);
}

export function compareObservationRecords(records) {
  if (!Array.isArray(records) || records.length === 0) throw new TypeError('observation records are required');
  const valid = records.map(validateObservationRecord);
  const sourceEventId = valid[0].sourceEventId;
  if (valid.some(record => record.sourceEventId !== sourceEventId)) {
    throw new RangeError('observation records must share the same source event');
  }

  const sharedInvariants = valid[0].invariants.filter(invariant =>
    valid.every(record => record.invariants.includes(invariant))
  );
  const byType = new Map(valid.map(record => [record.observerType, record]));
  const disagreements = [];
  const projection = byType.get('projection');
  const metric = byType.get('metric');
  if (projection?.payload.extentChanged === true && metric?.payload.originRadiusPreserved === true) {
    disagreements.push({
      kind: 'projection-vs-metric',
      observation: 'projected extent changed while the declared 4D origin-radius invariant was preserved',
      resolution: 'new-discriminator-required',
      forcedConsensus: false
    });
  }
  const slice = byType.get('slice');
  if (slice?.payload.selectionChanged === true) {
    disagreements.push({
      kind: 'slice-membership-change',
      observation: 'membership in the declared coordinate slice changed after the source transformation',
      resolution: 'new-discriminator-required',
      forcedConsensus: false
    });
  }

  return deepFreeze({
    sourceEventId,
    sameSourceEvent: true,
    observerTypes: valid.map(record => record.observerType),
    sharedInvariants,
    declaredLosses: Object.fromEntries(valid.map(record => [record.observerType, record.losses])),
    disagreements,
    soundAddsEvidence: byType.get('sound')?.payload.evidenceAdded === true,
    boundaries: OBSERVER_BOUNDARIES
  });
}
