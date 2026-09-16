export const DEG = Math.PI / 180;
const PLANE_INDEX = Object.freeze({ xw: [0, 3], yw: [1, 3], zw: [2, 3] });

function freezePoint(point) {
  if (!Array.isArray(point) || point.length !== 4 || point.some(v => !Number.isFinite(v))) {
    throw new TypeError('point must contain four finite coordinates');
  }
  return Object.freeze([...point]);
}

function freezeMove(move) {
  return Object.freeze({ plane: move.plane, degrees: move.degrees });
}

export function assertSupportedMove(move) {
  if (!move || typeof move !== 'object') throw new TypeError('move must be an object');
  if (!Object.hasOwn(PLANE_INDEX, move.plane)) throw new RangeError(`unsupported plane: ${move.plane}`);
  if (!Number.isFinite(move.degrees) || Math.abs(move.degrees) !== 1) {
    throw new RangeError('degrees must be exactly +1 or -1');
  }
  return true;
}

export function createState(points, actions = []) {
  if (!Array.isArray(points)) throw new TypeError('points must be an array');
  const frozenPoints = Object.freeze(points.map(freezePoint));
  const frozenActions = Object.freeze(actions.map(move => {
    assertSupportedMove(move);
    return freezeMove(move);
  }));
  return Object.freeze({ points: frozenPoints, actions: frozenActions });
}

export function rotatePoint4(point, plane, degrees) {
  assertSupportedMove({ plane, degrees });
  const p = freezePoint(point);
  const [a, b] = PLANE_INDEX[plane];
  const theta = degrees * DEG;
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  const q = [...p];
  q[a] = p[a] * c - p[b] * s;
  q[b] = p[a] * s + p[b] * c;
  return Object.freeze(q);
}

export function applyMove(state, move) {
  assertSupportedMove(move);
  if (!state || !Array.isArray(state.points) || !Array.isArray(state.actions)) {
    throw new TypeError('invalid state');
  }
  return createState(
    state.points.map(point => rotatePoint4(point, move.plane, move.degrees)),
    [...state.actions, move]
  );
}

export function createMirror(state) {
  if (!state || !Array.isArray(state.points)) throw new TypeError('invalid state');
  return createState(state.points, []);
}

export function compareStates(a, b, epsilon = 1e-12) {
  if (!Number.isFinite(epsilon) || epsilon < 0) throw new RangeError('epsilon must be finite and non-negative');
  if (!a || !b || !Array.isArray(a.points) || !Array.isArray(b.points) || a.points.length !== b.points.length) {
    throw new RangeError('states must have matching point counts');
  }
  let maxAbsDelta = 0;
  const pointDeltas = a.points.map((point, i) => {
    const other = b.points[i];
    if (!Array.isArray(other) || point.length !== other.length) throw new RangeError('states must have matching point dimensions');
    const delta = point.map((value, j) => value - other[j]);
    for (const value of delta) maxAbsDelta = Math.max(maxAbsDelta, Math.abs(value));
    return Object.freeze(delta);
  });
  return Object.freeze({
    equal: maxAbsDelta <= epsilon,
    maxAbsDelta,
    pointDeltas: Object.freeze(pointDeltas)
  });
}

export function materializeTrajectory(points, actions = []) {
  if (!Array.isArray(actions)) throw new TypeError('actions must be an array');
  const origin = createState(points);
  const mirror = createMirror(origin);
  let previous = origin;
  let live = origin;
  for (const move of actions) {
    previous = live;
    live = applyMove(live, move);
  }
  return Object.freeze({ origin, mirror, previous, live });
}
