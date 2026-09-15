export const OBSERVER_FIELD_VERSION = 's1-observer-field/v0';
export const TASK_ASSIGNMENT_VERSION = 's1-observer-task/v0';
export const LOCAL_FRAME_VERSION = 's1-local-frame/v0';
export const TASKS = Object.freeze(['x','y','z','w','xw','yw','zw']);

function fnv1a64(text) {
  let hash = 0xcbf29ce484222325n;
  const prime = 0x100000001b3n;
  for (const byte of new TextEncoder().encode(text)) {
    hash ^= BigInt(byte);
    hash = BigInt.asUintN(64, hash * prime);
  }
  return hash.toString(16).padStart(16, '0');
}

function pointKey(point) {
  if (!Array.isArray(point) || point.length !== 4 || point.some(v => !Number.isFinite(v))) {
    throw new TypeError('observer source point must contain four finite coordinates');
  }
  return point.map(v => Object.is(v, -0) ? '0' : Number(v).toPrecision(17)).join('|');
}

export function makeObserverField({points4, sourceDimension, densityId}) {
  if (!Array.isArray(points4)) throw new TypeError('points4 must be an array');
  if (![3,4].includes(sourceDimension)) throw new RangeError('sourceDimension must be 3 or 4');
  if (typeof densityId !== 'string' || densityId.length === 0) throw new TypeError('densityId is required');

  const base = points4.map((point, sourceIndex) => {
    const sourcePointId = fnv1a64(`${densityId}|${sourceIndex}|${pointKey(point)}`);
    return { sourceIndex, sourcePointId, id: `obs-${sourcePointId}` };
  });
  const sorted = [...base].sort((a,b) => a.id.localeCompare(b.id));
  const taskByIndex = new Map();
  sorted.forEach((item, rank) => taskByIndex.set(item.sourceIndex, TASKS[rank % TASKS.length]));

  const observers = base.map(item => Object.freeze({
    id: item.id,
    sourcePointId: item.sourcePointId,
    sourceIndex: item.sourceIndex,
    sourceDimension,
    task: taskByIndex.get(item.sourceIndex),
    calibration: 0,
    localFrameVersion: LOCAL_FRAME_VERSION
  }));

  return Object.freeze({
    version: OBSERVER_FIELD_VERSION,
    taskVersion: TASK_ASSIGNMENT_VERSION,
    densityId,
    sourceDimension,
    observers: Object.freeze(observers)
  });
}

const COORD_INDEX = Object.freeze({ x:0, y:1, z:2, w:3 });
const PLANE_PAIR = Object.freeze({ xw:[0,3], yw:[1,3], zw:[2,3] });

function validateMeasurementPoint(point) {
  if (!Array.isArray(point) || point.length !== 4 || point.some(v => !Number.isFinite(v))) {
    throw new TypeError('measurement point must contain four finite coordinates');
  }
}

function normalizeAngle(value) {
  let x = value;
  while (x > Math.PI) x -= 2 * Math.PI;
  while (x < -Math.PI) x += 2 * Math.PI;
  return x;
}

function taskValue(task, point) {
  if (Object.hasOwn(COORD_INDEX, task)) return point[COORD_INDEX[task]];
  const pair = PLANE_PAIR[task];
  if (!pair) throw new RangeError(`unsupported observer task: ${task}`);
  return Math.atan2(point[pair[1]], point[pair[0]]);
}

export function measureObserver(observer, livePoint, mirrorPoint) {
  if (!observer || !TASKS.includes(observer.task) || !Number.isFinite(observer.calibration)) {
    throw new TypeError('invalid observer');
  }
  validateMeasurementPoint(livePoint);
  validateMeasurementPoint(mirrorPoint);
  const liveValue = taskValue(observer.task, livePoint);
  const mirrorValue = taskValue(observer.task, mirrorPoint);
  const raw = Object.hasOwn(PLANE_PAIR, observer.task)
    ? normalizeAngle(liveValue - mirrorValue)
    : liveValue - mirrorValue;
  return Object.freeze({
    observerId: observer.id,
    task: observer.task,
    liveValue,
    mirrorValue,
    residual: raw,
    repairedResidual: raw - observer.calibration
  });
}

export function repairObserver(observer, delta) {
  if (!observer || !TASKS.includes(observer.task) || !Number.isFinite(observer.calibration)) {
    throw new TypeError('invalid observer');
  }
  if (typeof delta !== 'number' || !Number.isFinite(delta)) {
    throw new TypeError('repair delta must be one finite scalar');
  }
  return Object.freeze({ ...observer, calibration: observer.calibration + delta });
}
