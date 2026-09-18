import { canonicalJson, fnv1a64, validateExperience } from './experience.mjs';
import { normalizeObserver } from './observer.mjs';
import { guardDigestCollision } from './integrity.mjs';

export const CARRIER_VERSION = "S'1-Carrier/Ops v1";
export const CARRIER_SCHEMA = 's1-carrier/v1';
const CARRIER_KEYS = Object.freeze(['schema','version','kind','payload','descriptor','id']);

function deepFreeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    for (const child of Object.values(value)) deepFreeze(child);
    Object.freeze(value);
  }
  return value;
}

function assertOnlyKeys(value, allowed, label) {
  for (const key of Object.keys(value)) {
    if (!allowed.includes(key)) throw new RangeError(`unsupported ${label} field: ${key}`);
  }
}

function makeCarrier(kind, payload, registry) {
  if (typeof kind !== 'string' || !kind) throw new TypeError('carrier kind is required');
  const base = { schema:CARRIER_SCHEMA, version:CARRIER_VERSION, kind, payload };
  const descriptor = canonicalJson(base);
  const id = fnv1a64(descriptor);
  if (registry !== undefined) {
    if (!(registry instanceof Map)) throw new TypeError('carrier registry must be a Map');
    guardDigestCollision(registry,id,descriptor,'carrier');
  }
  return deepFreeze({ ...base, descriptor, id });
}

function normalizePayload(carrier) {
  switch (carrier.kind) {
    case 'neutral': {
      assertOnlyKeys(carrier.payload, [], 'neutral payload');
      return {};
    }
    case 'experience': {
      assertOnlyKeys(carrier.payload, ['experience'], 'experience carrier payload');
      return { experience:validateExperience(carrier.payload.experience) };
    }
    case 'observer-frame': {
      assertOnlyKeys(carrier.payload, ['observer'], 'observer-frame payload');
      return { observer:normalizeObserver(carrier.payload.observer) };
    }
    case 'join': {
      assertOnlyKeys(carrier.payload, ['chronology','memberIds'], 'join payload');
      if (!Array.isArray(carrier.payload.chronology) || carrier.payload.chronology.length < 2) {
        throw new RangeError('join chronology must contain at least two carriers');
      }
      const chronology = carrier.payload.chronology.map(item=>validateCarrier(item));
      const memberIds = [...new Set(chronology.map(item=>item.id))].sort();
      if (!Array.isArray(carrier.payload.memberIds) || canonicalJson(carrier.payload.memberIds) !== canonicalJson(memberIds)) {
        throw new RangeError('join memberIds do not match normalized chronology');
      }
      return { chronology, memberIds };
    }
    case 'difference':
    case 'interaction': {
      assertOnlyKeys(carrier.payload, ['left','right'], `${carrier.kind} payload`);
      return { left:validateCarrier(carrier.payload.left), right:validateCarrier(carrier.payload.right) };
    }
    case 'quotient': {
      assertOnlyKeys(carrier.payload, ['source','frame'], 'quotient payload');
      const source=validateCarrier(carrier.payload.source);
      const frame=validateCarrier(carrier.payload.frame);
      if (frame.kind !== 'observer-frame') throw new RangeError('quotient frame must be an observer-frame carrier');
      return { source, frame };
    }
    default:
      throw new RangeError(`unsupported carrier kind: ${carrier.kind}`);
  }
}

export function validateCarrier(carrier, registry) {
  if (!carrier || typeof carrier !== 'object' || Array.isArray(carrier)) throw new TypeError('carrier must be an object');
  assertOnlyKeys(carrier,CARRIER_KEYS,'carrier');
  if (carrier.schema !== CARRIER_SCHEMA) throw new RangeError('unsupported carrier schema');
  if (carrier.version !== CARRIER_VERSION) throw new RangeError('unsupported carrier version');
  if (!carrier.payload || typeof carrier.payload !== 'object' || Array.isArray(carrier.payload)) throw new TypeError('carrier payload must be an object');
  const normalized = makeCarrier(carrier.kind,normalizePayload(carrier),registry);
  if (typeof carrier.descriptor !== 'string' || carrier.descriptor !== normalized.descriptor) {
    throw new RangeError('carrier descriptor does not match canonical payload');
  }
  if (typeof carrier.id !== 'string' || carrier.id !== normalized.id) {
    throw new RangeError('carrier id does not match canonical descriptor');
  }
  return normalized;
}

export const S1_CARRIER_NEUTRAL = makeCarrier('neutral',{});

export function experienceCarrier(record, registry) {
  return makeCarrier('experience',{experience:validateExperience(record)},registry);
}

export function observerFrameCarrier(observer, registry) {
  return makeCarrier('observer-frame',{observer:normalizeObserver(observer)},registry);
}

function flattenJoin(carrier) {
  const valid=validateCarrier(carrier);
  if (valid.kind === 'neutral') return [];
  if (valid.kind === 'join') return [...valid.payload.chronology];
  return [valid];
}

export function joinCarriers(a,b,registry) {
  const chronology=[...flattenJoin(a),...flattenJoin(b)];
  if (chronology.length===0) return S1_CARRIER_NEUTRAL;
  if (chronology.length===1) {
    const only=chronology[0];
    if (registry !== undefined) guardDigestCollision(registry,only.id,only.descriptor,'carrier');
    return only;
  }
  const memberIds=[...new Set(chronology.map(carrier=>carrier.id))].sort();
  return makeCarrier('join',{chronology,memberIds},registry);
}

export function differenceCarriers(a,b,registry) {
  return makeCarrier('difference',{left:validateCarrier(a),right:validateCarrier(b)},registry);
}

export function interactCarriers(a,b,registry) {
  return makeCarrier('interaction',{left:validateCarrier(a),right:validateCarrier(b)},registry);
}

export function quotientCarrier(source,frame,registry) {
  const validSource=validateCarrier(source);
  const validFrame=validateCarrier(frame);
  if (validFrame.kind !== 'observer-frame') throw new RangeError('quotient frame must be an observer-frame carrier');
  return makeCarrier('quotient',{source:validSource,frame:validFrame},registry);
}
