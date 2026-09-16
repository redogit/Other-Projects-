import { createState, applyMove, assertSupportedMove } from './core.mjs';
import { normalizeObserver, projectState } from './observer.mjs';

export const EXPERIENCE_SCHEMA = 's1-experience/v0';
export const OPERATOR_VERSION = "S'1-Ops v0";
export const SHELLS = Object.freeze(['s3-sample', 'tesseract-boundary', 'comparison']);
const INPUT_KEYS = Object.freeze(['initialState','mirrorId','shell','actions','observer','observerField','comparisons','relations','provenance']);
const RECORD_KEYS = Object.freeze(['schema','id','operatorVersion',...INPUT_KEYS]);

function assertOnlyKeys(value, allowed, label) {
  for (const key of Object.keys(value)) if (!allowed.includes(key)) throw new RangeError(`unsupported ${label} field: ${key}`);
}

function canonicalValue(value) {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return value;
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new TypeError('canonical values must be finite');
    return Object.is(value, -0) ? 0 : value;
  }
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (typeof value === 'object') {
    const prototype = Object.getPrototypeOf(value);
    if (prototype !== Object.prototype && prototype !== null) throw new TypeError('canonical objects must be plain records');
    const out = Object.create(null);
    for (const key of Object.keys(value).sort()) {
      if (value[key] === undefined) throw new TypeError(`undefined value at ${key}`);
      out[key] = canonicalValue(value[key]);
    }
    return out;
  }
  throw new TypeError(`unsupported canonical value type: ${typeof value}`);
}

export function canonicalJson(value) {
  return JSON.stringify(canonicalValue(value));
}

export function fnv1a64(text) {
  if (typeof text !== 'string') throw new TypeError('text must be a string');
  let hash = 0xcbf29ce484222325n;
  const prime = 0x100000001b3n;
  for (const byte of new TextEncoder().encode(text)) {
    hash ^= BigInt(byte);
    hash = BigInt.asUintN(64, hash * prime);
  }
  return hash.toString(16).padStart(16, '0');
}

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

function validateObserverField(field) {
  if (!field || typeof field !== 'object' || Array.isArray(field)) throw new TypeError('observerField is required');
  assertOnlyKeys(field, ['version','taskVersion','densityId','calibrations'], 'observerField');
  if (field.version !== 's1-observer-field/v0') throw new RangeError('unsupported observerField version');
  if (field.taskVersion !== 's1-observer-task/v0') throw new RangeError('unsupported observer task version');
  if (typeof field.densityId !== 'string' || !field.densityId) throw new TypeError('observerField densityId is required');
  if (!Array.isArray(field.calibrations)) throw new TypeError('observerField calibrations must be an array');
  for (const entry of field.calibrations) {
    if (typeof entry === 'number') {
      if (!Number.isFinite(entry)) throw new TypeError('observer calibration must be finite');
    } else if (entry && typeof entry === 'object' && !Array.isArray(entry)) {
      assertOnlyKeys(entry, ['observerId','calibration'], 'observer calibration');
      if (typeof entry.observerId !== 'string' || !entry.observerId || !Number.isFinite(entry.calibration)) throw new TypeError('invalid observer calibration record');
    } else {
      throw new TypeError('invalid observer calibration record');
    }
  }
}

function validateRelations(relations) {
  if (!relations || typeof relations !== 'object' || Array.isArray(relations)) throw new TypeError('relations must be an object');
  if (relations.testsInvariantId !== undefined && typeof relations.testsInvariantId !== 'string') throw new TypeError('testsInvariantId must be a string');
  if (relations.invariantResult !== undefined && typeof relations.invariantResult !== 'boolean') throw new TypeError('invariantResult must be boolean');
}

function makeBase(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new TypeError('experience input must be an object');
  if (typeof input.initialState !== 'string' || !input.initialState) throw new TypeError('initialState must be a non-empty geometry id');
  if (typeof input.mirrorId !== 'string' || !input.mirrorId) throw new TypeError('mirrorId is required');
  if (!SHELLS.includes(input.shell)) throw new RangeError(`unsupported shell: ${input.shell}`);
  if (!Array.isArray(input.actions)) throw new TypeError('actions must be an array');
  for (const move of input.actions) assertSupportedMove(move);
  const observer = normalizeObserver(input.observer);
  validateObserverField(input.observerField);
  if (!input.comparisons || typeof input.comparisons !== 'object' || Array.isArray(input.comparisons)) throw new TypeError('comparisons must be an object');
  validateRelations(input.relations);
  if (!input.provenance || typeof input.provenance !== 'object' || Array.isArray(input.provenance)) throw new TypeError('provenance must be an object');

  return {
    schema: EXPERIENCE_SCHEMA,
    initialState: input.initialState,
    mirrorId: input.mirrorId,
    shell: input.shell,
    actions: input.actions.map(move => ({ plane: move.plane, degrees: move.degrees })),
    observer,
    observerField: cloneCanonical(input.observerField),
    operatorVersion: OPERATOR_VERSION,
    comparisons: cloneCanonical(input.comparisons),
    relations: cloneCanonical(input.relations),
    provenance: cloneCanonical(input.provenance)
  };
}

export function makeExperience(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new TypeError('experience input must be an object');
  assertOnlyKeys(input, INPUT_KEYS, 'experience');
  const base = makeBase(input);
  const id = fnv1a64(canonicalJson(base));
  return deepFreeze({ ...base, id });
}

export function validateExperience(record) {
  if (!record || typeof record !== 'object' || Array.isArray(record)) throw new TypeError('experience record must be an object');
  assertOnlyKeys(record, RECORD_KEYS, 'experience record');
  if (record.schema !== EXPERIENCE_SCHEMA) throw new RangeError('unsupported experience schema');
  if (record.operatorVersion !== OPERATOR_VERSION) throw new RangeError('unsupported operator version');
  const payload = Object.fromEntries(INPUT_KEYS.map(key => [key, record[key]]));
  const rebuilt = makeExperience(payload);
  if (typeof record.id !== 'string' || record.id !== rebuilt.id) throw new RangeError('experience id does not match canonical payload');
  return rebuilt;
}

function lookupGeometry(registry, id) {
  const geometry = registry instanceof Map ? registry.get(id) : registry?.[id];
  if (!geometry || geometry.id !== id || !Array.isArray(geometry.points4)) throw new RangeError(`unknown initial geometry: ${id}`);
  return geometry;
}

export function replayExperience(record, geometryRegistry) {
  const valid = validateExperience(record);
  const geometry = lookupGeometry(geometryRegistry, valid.initialState);
  let state = createState(geometry.points4);
  for (const move of valid.actions) state = applyMove(state, move);
  return state;
}

export function reframeExperience(record, observer, geometryRegistry) {
  const valid = validateExperience(record);
  const normalized = normalizeObserver(observer);
  const replayed = replayExperience(valid, geometryRegistry);
  return deepFreeze({ sourceId: valid.id, observer: normalized, projected: projectState(replayed, normalized) });
}

function eventsOf(graph) {
  if (!graph || !Array.isArray(graph.events)) return [];
  return graph.events.map(entry => entry?.event ?? entry).filter(Boolean);
}

export function classifyExperience(record, graph) {
  const valid = validateExperience(record);
  const events = eventsOf(graph);
  if (events.some(existing => existing.id === valid.id)) return 'repeat';

  const invId = valid.relations.testsInvariantId;
  if (invId && typeof valid.relations.invariantResult === 'boolean' && Array.isArray(graph?.invariants)) {
    const prior = graph.invariants.find(inv => inv?.id === invId);
    if (prior && typeof prior.passed === 'boolean' && prior.passed !== valid.relations.invariantResult) return 'counterexample';
  }

  const hasFamily = typeof valid.relations.familyId === 'string' && valid.relations.familyId.length > 0;
  const hasParentField = Object.hasOwn(valid.relations, 'parentId');
  if (hasFamily && hasParentField) {
    const parentId = valid.relations.parentId;
    const siblings = events.filter(existing => existing.relations?.familyId === valid.relations.familyId && existing.relations?.parentId === parentId);
    return siblings.length === 0 ? 'new-branch' : 'variation';
  }

  if (hasFamily && events.some(existing => existing.relations?.familyId === valid.relations.familyId)) return 'variation';
  return 'unresolved';
}

export function appendExperience(graph, record, classification = classifyExperience(record, graph)) {
  const valid = validateExperience(record);
  const existingEvents = Array.isArray(graph?.events) ? graph.events : [];
  if (existingEvents.some(entry => (entry?.event ?? entry)?.id === valid.id)) return graph;
  const invariants = Array.isArray(graph?.invariants) ? graph.invariants : [];
  return deepFreeze({
    ...(graph && typeof graph === 'object' ? cloneCanonical(graph) : {}),
    invariants: cloneCanonical(invariants),
    events: [...cloneCanonical(existingEvents), { event: valid, classification }]
  });
}

function sameMove(a, b) {
  return a?.plane === b?.plane && a?.degrees === b?.degrees;
}

function isStrictActionPrefix(prefix, actions) {
  return Array.isArray(prefix) && prefix.length < actions.length && prefix.every((move, index) => sameMove(move, actions[index]));
}

export function findLongestPrefixParent(graph, familyId, actions) {
  if (typeof familyId !== 'string' || !familyId) throw new TypeError('familyId is required');
  if (!Array.isArray(actions)) throw new TypeError('actions must be an array');
  for (const move of actions) assertSupportedMove(move);
  const candidates = eventsOf(graph)
    .filter(event => event.relations?.familyId === familyId && isStrictActionPrefix(event.actions, actions))
    .sort((a, b) => b.actions.length - a.actions.length || a.id.localeCompare(b.id));
  return candidates[0]?.id ?? null;
}

export function rebuildExperienceGraph(records, invariants = []) {
  if (!Array.isArray(records)) throw new TypeError('records must be an array');
  if (!Array.isArray(invariants)) throw new TypeError('invariants must be an array');
  let graph = deepFreeze({ events: [], invariants: cloneCanonical(invariants) });
  const ordered = records.map(validateExperience).sort((a, b) => a.actions.length - b.actions.length || a.id.localeCompare(b.id));
  for (const record of ordered) graph = appendExperience(graph, record, classifyExperience(record, graph));
  return graph;
}

