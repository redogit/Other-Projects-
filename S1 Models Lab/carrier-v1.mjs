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

function normalizePayload(carrier, registry) {
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
      const chronology = carrier.payload.chronology.map(item=>validateCarrier(item,registry));
      const memberIds = [...new Set(chronology.map(item=>item.id))].sort();
      if (!Array.isArray(carrier.payload.memberIds) || canonicalJson(carrier.payload.memberIds) !== canonicalJson(memberIds)) {
        throw new RangeError('join memberIds do not match normalized chronology');
      }
      return { chronology, memberIds };
    }
    case 'difference':
    case 'interaction': {
      assertOnlyKeys(carrier.payload, ['left','right'], `${carrier.kind} payload`);
      return { left:validateCarrier(carrier.payload.left,registry), right:validateCarrier(carrier.payload.right,registry) };
    }
    case 'quotient': {
      assertOnlyKeys(carrier.payload, ['source','frame'], 'quotient payload');
      const source=validateCarrier(carrier.payload.source,registry);
      const frame=validateCarrier(carrier.payload.frame,registry);
      if (frame.kind !== 'observer-frame') throw new RangeError('quotient frame must be an observer-frame carrier');
      return { source, frame };
    }
    default:
      throw new RangeError(`unsupported carrier kind: ${carrier.kind}`);
  }
}

function useCollisionRegistry(registry) {
  if (registry === undefined) return new Map();
  if (!(registry instanceof Map)) throw new TypeError('carrier registry must be a Map');
  return registry;
}

export function validateCarrier(carrier, registry) {
  const collisionIndex = useCollisionRegistry(registry);
  if (!carrier || typeof carrier !== 'object' || Array.isArray(carrier)) throw new TypeError('carrier must be an object');
  assertOnlyKeys(carrier,CARRIER_KEYS,'carrier');
  if (carrier.schema !== CARRIER_SCHEMA) throw new RangeError('unsupported carrier schema');
  if (carrier.version !== CARRIER_VERSION) throw new RangeError('unsupported carrier version');
  if (!carrier.payload || typeof carrier.payload !== 'object' || Array.isArray(carrier.payload)) throw new TypeError('carrier payload must be an object');
  const normalized = makeCarrier(carrier.kind,normalizePayload(carrier,collisionIndex),collisionIndex);
  if (typeof carrier.descriptor !== 'string' || carrier.descriptor !== normalized.descriptor) {
    throw new RangeError('carrier descriptor does not match canonical payload');
  }
  if (typeof carrier.id !== 'string' || carrier.id !== normalized.id) {
    throw new RangeError('carrier id does not match canonical descriptor');
  }
  return normalized;
}

export const S1_CARRIER_NEUTRAL = makeCarrier('neutral',{},new Map());

export function experienceCarrier(record, registry) {
  const collisionIndex=useCollisionRegistry(registry);
  return makeCarrier('experience',{experience:validateExperience(record)},collisionIndex);
}

export function observerFrameCarrier(observer, registry) {
  const collisionIndex=useCollisionRegistry(registry);
  return makeCarrier('observer-frame',{observer:normalizeObserver(observer)},collisionIndex);
}

function flattenJoin(carrier, registry) {
  const valid=validateCarrier(carrier,registry);
  if (valid.kind === 'neutral') return [];
  if (valid.kind === 'join') return [...valid.payload.chronology];
  return [valid];
}

export function joinCarriers(a,b,registry) {
  const collisionIndex=useCollisionRegistry(registry);
  const chronology=[...flattenJoin(a,collisionIndex),...flattenJoin(b,collisionIndex)];
  if (chronology.length===0) return validateCarrier(S1_CARRIER_NEUTRAL,collisionIndex);
  if (chronology.length===1) return chronology[0];
  const memberIds=[...new Set(chronology.map(carrier=>carrier.id))].sort();
  return makeCarrier('join',{chronology,memberIds},collisionIndex);
}

export function differenceCarriers(a,b,registry) {
  const collisionIndex=useCollisionRegistry(registry);
  return makeCarrier('difference',{
    left:validateCarrier(a,collisionIndex),
    right:validateCarrier(b,collisionIndex)
  },collisionIndex);
}

export function interactCarriers(a,b,registry) {
  const collisionIndex=useCollisionRegistry(registry);
  return makeCarrier('interaction',{
    left:validateCarrier(a,collisionIndex),
    right:validateCarrier(b,collisionIndex)
  },collisionIndex);
}

export function quotientCarrier(source,frame,registry) {
  const collisionIndex=useCollisionRegistry(registry);
  const validSource=validateCarrier(source,collisionIndex);
  const validFrame=validateCarrier(frame,collisionIndex);
  if (validFrame.kind !== 'observer-frame') throw new RangeError('quotient frame must be an observer-frame carrier');
  return makeCarrier('quotient',{source:validSource,frame:validFrame},collisionIndex);
}
