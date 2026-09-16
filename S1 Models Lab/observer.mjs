export const DEFAULT_OBSERVER = Object.freeze({ yaw: 0, pitch: 0, roll: 0, wPerspective: 0.35 });
const KEYS = Object.freeze(Object.keys(DEFAULT_OBSERVER));

export function normalizeObserver(input = {}) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new TypeError('observer must be an object');
  for (const key of Object.keys(input)) {
    if (!KEYS.includes(key)) throw new RangeError(`unsupported observer key: ${key}`);
  }
  if (Object.isFrozen(input) && Object.keys(input).length === KEYS.length && KEYS.every(key => Object.hasOwn(input, key))) {
    for (const key of KEYS) if (!Number.isFinite(input[key])) throw new TypeError(`${key} must be finite`);
    if (input.wPerspective < 0 || input.wPerspective >= 1) throw new RangeError('wPerspective must be in [0, 1)');
    return input;
  }
  const out = { ...DEFAULT_OBSERVER, ...input };
  for (const key of KEYS) {
    if (!Number.isFinite(out[key])) throw new TypeError(`${key} must be finite`);
  }
  if (out.wPerspective < 0 || out.wPerspective >= 1) {
    throw new RangeError('wPerspective must be in [0, 1)');
  }
  return Object.freeze(out);
}

function validatePoint4(point) {
  if (!Array.isArray(point) || point.length !== 4 || point.some(v => !Number.isFinite(v))) {
    throw new TypeError('point must contain four finite coordinates');
  }
}

function rotate3([x, y, z], { yaw, pitch, roll }) {
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  let x1 = cy * x + sy * z;
  let y1 = y;
  let z1 = -sy * x + cy * z;

  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const x2 = x1;
  const y2 = cp * y1 - sp * z1;
  const z2 = sp * y1 + cp * z1;

  const cr = Math.cos(roll), sr = Math.sin(roll);
  return [cr * x2 - sr * y2, sr * x2 + cr * y2, z2];
}

export function projectPoint4(point, observer = DEFAULT_OBSERVER) {
  validatePoint4(point);
  const o = normalizeObserver(observer);
  const [rx, ry, rz] = rotate3(point.slice(0, 3), o);
  const w = point[3];
  const boundedW = Math.max(-0.9, w);
  const denom = 1 + o.wPerspective * boundedW;
  if (!Number.isFinite(denom) || denom <= 1e-9) throw new RangeError('observer projection is singular');
  const scale = 1 / denom;
  return Object.freeze([rx * scale, ry * scale, rz * scale, rz]);
}

export function projectState(state, observer = DEFAULT_OBSERVER) {
  if (!state || !Array.isArray(state.points)) throw new TypeError('state must expose points');
  const o = normalizeObserver(observer);
  return Object.freeze(state.points.map(point => projectPoint4(point, o)));
}

export function projectPair(live, mirror, observer = DEFAULT_OBSERVER) {
  if (!live || !mirror || !Array.isArray(live.points) || !Array.isArray(mirror.points)) throw new TypeError('live and mirror states are required');
  if (live.points.length !== mirror.points.length) throw new RangeError('live and mirror point counts must match');
  const o = normalizeObserver(observer);
  const liveProjected = Object.freeze(live.points.map(point => projectPoint4(point, o)));
  const mirrorProjected = Object.freeze(mirror.points.map(point => projectPoint4(point, o)));
  return Object.freeze({ live: liveProjected, mirror: mirrorProjected, observer: o });
}
