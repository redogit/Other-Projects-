import { normalizeObserver } from './observer.mjs';
import {
  OPERATOR_VERSION, canonicalJson, fnv1a64, validateExperience, reframeExperience
} from './experience.mjs';

export const S1_NEUTRAL = Object.freeze({
  schema: 's1-neutral/v0',
  operatorVersion: OPERATOR_VERSION,
  kind: 'neutral',
  id: "S'1_",
  observation: false,
  claim: false
});

function deepFreeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    for (const child of Object.values(value)) deepFreeze(child);
    Object.freeze(value);
  }
  return value;
}

function clone(value) {
  return JSON.parse(canonicalJson(value));
}

function isNeutral(value) {
  return value === S1_NEUTRAL || (
    value && value.schema === S1_NEUTRAL.schema && value.operatorVersion === OPERATOR_VERSION &&
    value.kind === 'neutral' && value.id === S1_NEUTRAL.id && value.observation === false && value.claim === false
  );
}

function operand(value) {
  if (isNeutral(value)) return S1_NEUTRAL;
  return validateExperience(value);
}

function operandId(value) {
  return isNeutral(value) ? S1_NEUTRAL.id : value.id;
}

function result(operation, fields) {
  const base = {
    schema: 's1-operator-result/v0',
    operatorVersion: OPERATOR_VERSION,
    operation,
    ...fields
  };
  const id = fnv1a64(canonicalJson(base));
  return deepFreeze({ ...base, id });
}

export function makeObserverFrame(observer) {
  const normalized = normalizeObserver(observer);
  const base = {
    schema: 's1-observer-frame/v0',
    operatorVersion: OPERATOR_VERSION,
    kind: 'observer-frame',
    observer: normalized
  };
  return deepFreeze({ ...base, id: `frame:${fnv1a64(canonicalJson(base))}` });
}

function validateObserverFrame(frame) {
  if (!frame || typeof frame !== 'object' || Array.isArray(frame)) throw new TypeError('frame must be an object');
  const allowed = ['schema','operatorVersion','kind','observer','id'];
  for (const key of Object.keys(frame)) if (!allowed.includes(key)) throw new RangeError(`unsupported frame field: ${key}`);
  if (frame.schema !== 's1-observer-frame/v0' || frame.operatorVersion !== OPERATOR_VERSION || frame.kind !== 'observer-frame') {
    throw new RangeError('unsupported quotient frame contract');
  }
  const rebuilt = makeObserverFrame(frame.observer);
  if (frame.id !== rebuilt.id) throw new RangeError('frame id does not match canonical frame payload');
  return rebuilt;
}

export function joinModels(a, b) {
  const left = operand(a), right = operand(b);
  const chronology = [left, right].filter(value => !isNeutral(value)).map(operandId);
  const memberIds = [...new Set(chronology)].sort();
  const authorities = [left, right]
    .filter(value => !isNeutral(value))
    .map(value => ({ id: value.id, provenance: clone(value.provenance) }));
  return result('join', {
    memberIds,
    chronology,
    localAuthority: authorities
  });
}

function differenceAt(a, b, path = '$') {
  if (canonicalJson(a) === canonicalJson(b)) return [];
  const aObject = a !== null && typeof a === 'object';
  const bObject = b !== null && typeof b === 'object';
  if (!aObject || !bObject || Array.isArray(a) !== Array.isArray(b)) {
    return [{ path, kind: 'changed', inA: clone(a), inB: clone(b) }];
  }
  if (Array.isArray(a)) {
    const out = [];
    const n = Math.max(a.length, b.length);
    for (let i = 0; i < n; i++) {
      const p = `${path}[${i}]`;
      if (i >= b.length) out.push({ path:p, kind:'present-in-a', inA:clone(a[i]) });
      else if (i >= a.length) out.push({ path:p, kind:'absent-from-a', inB:clone(b[i]) });
      else out.push(...differenceAt(a[i], b[i], p));
    }
    return out;
  }
  const out = [];
  for (const key of [...new Set([...Object.keys(a), ...Object.keys(b)])].sort()) {
    const p = `${path}.${key}`;
    if (!Object.hasOwn(b,key)) out.push({ path:p, kind:'present-in-a', inA:clone(a[key]) });
    else if (!Object.hasOwn(a,key)) out.push({ path:p, kind:'absent-from-a', inB:clone(b[key]) });
    else out.push(...differenceAt(a[key], b[key], p));
  }
  return out;
}

function snapshot(value) {
  return isNeutral(value) ? S1_NEUTRAL : value;
}

export function differenceModels(a, b) {
  const left = operand(a), right = operand(b);
  return result('difference', {
    sourceIds: [operandId(left), operandId(right)],
    direction: 'A-relative-to-B',
    changes: differenceAt(snapshot(left), snapshot(right))
  });
}

export function interactModels(a, b) {
  const left = operand(a), right = operand(b);
  return result('interaction', {
    sourceIds: [operandId(left), operandId(right)],
    contract: 'structural-directional-coupling/v0',
    primaryDifference: differenceAt(snapshot(left), snapshot(right))
  });
}

export function quotientModel(model, frame, geometryRegistry) {
  const source = validateExperience(model);
  const validFrame = validateObserverFrame(frame);
  const reframed = reframeExperience(source, validFrame.observer, geometryRegistry);
  return result('quotient', {
    sourceId: source.id,
    frameId: validFrame.id,
    observer: reframed.observer,
    projected: reframed.projected
  });
}
