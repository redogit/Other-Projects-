import { createState, applyMove, assertSupportedMove } from './core.mjs';
import { normalizeObserver, projectState } from './observer.mjs';

export const EXPERIENCE_SCHEMA = 's1-experience/v0';
export const OPERATOR_VERSION = "S'1-Ops v0";
export const SHELLS = Object.freeze(['s3-sample', 'tesseract-boundary', 'comparison']);
const INPUT_KEYS = Object.freeze(['initialState','mirrorId','shell','actions','observer','observerField','checkpoints','comparisons','relations','provenance']);
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

function validateCheckpoints(checkpoints, actionCount) {
  if (!Array.isArray(checkpoints)) throw new TypeError('checkpoints must be an array');
  const normalized = checkpoints.map(checkpoint => {
    if (!checkpoint || typeof checkpoint !== 'object' || Array.isArray(checkpoint)) throw new TypeError('checkpoint must be an object');
    assertOnlyKeys(checkpoint, ['actionIndex','label'], 'checkpoint');
    if (!Number.isSafeInteger(checkpoint.actionIndex) || checkpoint.actionIndex < 0 || checkpoint.actionIndex > actionCount) {
      throw new RangeError('checkpoint actionIndex must be within the saved action chronology');
    }
    if (checkpoint.label !== undefined && (typeof checkpoint.label !== 'string' || checkpoint.label.length === 0)) {
      throw new TypeError('checkpoint label must be a non-empty string');
    }
    return checkpoint.label === undefined ? { actionIndex: checkpoint.actionIndex } : { actionIndex: checkpoint.actionIndex, label: checkpoint.label };
  });
  const seen = new Set();
  for (const checkpoint of normalized) {
    const key = `${checkpoint.actionIndex}:${checkpoint.label ?? ''}`;
    if (seen.has(key)) throw new RangeError('duplicate checkpoint');
    seen.add(key);
  }
  return normalized;
}

function validateComparison(summary, label) {
  if (!summary || typeof summary !== 'object' || Array.isArray(summary)) throw new TypeError(`${label} must be an object`);
  assertOnlyKeys(summary, ['equal','maxAbsDelta'], label);
  if (typeof summary.equal !== 'boolean') throw new TypeError(`${label}.equal must be boolean`);
  if (!Number.isFinite(summary.maxAbsDelta) || summary.maxAbsDelta < 0) throw new RangeError(`${label}.maxAbsDelta must be finite and non-negative`);
  return { equal: summary.equal, maxAbsDelta: summary.maxAbsDelta };
}

function validateComparisons(comparisons) {
  if (!comparisons || typeof comparisons !== 'object' || Array.isArray(comparisons)) throw new TypeError('comparisons must be an object');
  assertOnlyKeys(comparisons, ['obligation','againstMirror','againstPrevious'], 'comparisons');
  if (typeof comparisons.obligation !== 'string' || !comparisons.obligation) throw new TypeError('comparison obligation is required');
  return {
    obligation: comparisons.obligation,
    againstMirror: validateComparison(comparisons.againstMirror, 'againstMirror'),
    againstPrevious: validateComparison(comparisons.againstPrevious, 'againstPrevious')
  };
}

function validateRelations(relations) {
  if (!relations || typeof relations !== 'object' || Array.isArray(relations)) throw new TypeError('relations must be an object');
  assertOnlyKeys(relations, ['familyId','parentId','relatedIds','testsInvariantId','invariantResult'], 'relations');
  if (relations.familyId !== undefined && (typeof relations.familyId !== 'string' || !relations.familyId)) throw new TypeError('familyId must be a non-empty string');
  const parentId = relations.parentId ?? null;
  if (parentId !== null && (typeof parentId !== 'string' || !parentId)) throw new TypeError('parentId must be null or a non-empty string');
  const relatedIds = relations.relatedIds ?? [];
  if (!Array.isArray(relatedIds) || relatedIds.some(id => typeof id !== 'string' || !id)) throw new TypeError('relatedIds must contain non-empty strings');
  if (new Set(relatedIds).size !== relatedIds.length) throw new RangeError('relatedIds must be unique');
  if (relations.testsInvariantId !== undefined && (typeof relations.testsInvariantId !== 'string' || !relations.testsInvariantId)) throw new TypeError('testsInvariantId must be a non-empty string');
  if (relations.invariantResult !== undefined && typeof relations.invariantResult !== 'boolean') throw new TypeError('invariantResult must be boolean');
  const out = { parentId, relatedIds: [...relatedIds] };
  if (relations.familyId !== undefined) out.familyId = relations.familyId;
  if (relations.testsInvariantId !== undefined) out.testsInvariantId = relations.testsInvariantId;
  if (relations.invariantResult !== undefined) out.invariantResult = relations.invariantResult;
  return out;
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
  const checkpoints = validateCheckpoints(input.checkpoints ?? [], input.actions.length);
  const comparisons = validateComparisons(input.comparisons);
  const relations = validateRelations(input.relations);
  if (!input.provenance || typeof input.provenance !== 'object' || Array.isArray(input.provenance)) throw new TypeError('provenance must be an object');

  return {
    schema: EXPERIENCE_SCHEMA,
    initialState: input.initialState,
    mirrorId: input.mirrorId,
    shell: input.shell,
    actions: input.actions.map(move => ({ plane: move.plane, degrees: move.degrees })),
    observer,
    observerField: cloneCanonical(input.observerField),
    checkpoints: cloneCanonical(checkpoints),
    operatorVersion: OPERATOR_VERSION,
    comparisons: cloneCanonical(comparisons),
    relations: cloneCanonical(relations),
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

export function replayDescriptor(record) {
  const valid = validateExperience(record);
  return canonicalJson({
    initialState: valid.initialState,
    mirrorId: valid.mirrorId,
    shell: valid.shell,
    operatorVersion: valid.operatorVersion,
    actions: valid.actions,
    observer: valid.observer
  });
}

export function replayIdentity(record) {
  return fnv1a64(replayDescriptor(record));
}

export function replayEquivalent(
  a,
  b,
  { identityFor = replayIdentity, descriptorFor = replayDescriptor } = {}
) {
  if (typeof identityFor !== 'function' || typeof descriptorFor !== 'function') {
    throw new TypeError('identityFor and descriptorFor must be functions');
  }
  const left = validateExperience(a);
  const right = validateExperience(b);
  const leftIdentity = identityFor(left);
  const rightIdentity = identityFor(right);
  if (typeof leftIdentity !== 'string' || !leftIdentity || typeof rightIdentity !== 'string' || !rightIdentity) {
    throw new TypeError('replay identity must be a non-empty string');
  }
  if (leftIdentity !== rightIdentity) return false;
  const leftDescriptor = descriptorFor(left);
  const rightDescriptor = descriptorFor(right);
  if (typeof leftDescriptor !== 'string' || typeof rightDescriptor !== 'string') {
    throw new TypeError('replay descriptor must be a string');
  }
  if (leftDescriptor !== rightDescriptor) {
    throw new RangeError('replay digest collision: equal digest names unequal canonical replay payloads');
  }
  return true;
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
  if (events.some(existing => replayEquivalent(existing, valid))) return 'repeat';

  const invId = valid.relations.testsInvariantId;
  if (invId && typeof valid.relations.invariantResult === 'boolean' && Array.isArray(graph?.invariants)) {
    const prior = graph.invariants.find(inv => inv?.id === invId);
    if (prior && typeof prior.passed === 'boolean' && prior.passed !== valid.relations.invariantResult) return 'counterexample';
  }

  const hasFamily = typeof valid.relations.familyId === 'string' && valid.relations.familyId.length > 0;
  if (!hasFamily) return 'unresolved';

  const sameContract = existing =>
    existing.initialState === valid.initialState &&
    existing.mirrorId === valid.mirrorId &&
    existing.operatorVersion === valid.operatorVersion &&
    existing.comparisons?.obligation === valid.comparisons.obligation;
  const familyEvents = events.filter(existing => existing.relations?.familyId === valid.relations.familyId);
  const contractFamily = familyEvents.filter(sameContract);
  const parentId = valid.relations.parentId;

  if (parentId !== null) {
    const parent = events.find(existing => existing.id === parentId);
    if (!parent || !sameContract(parent) || parent.relations?.familyId !== valid.relations.familyId) return 'unresolved';
    const siblings = contractFamily.filter(existing => existing.relations?.parentId === parentId);
    return siblings.length === 0 ? 'new-branch' : 'variation';
  }

  if (contractFamily.length > 0) return 'variation';
  if (familyEvents.length > 0) return 'unresolved';
  return 'new-branch';
}

export function appendExperience(graph, record, classification = classifyExperience(record, graph)) {
  const valid = validateExperience(record);
  const existingEvents = Array.isArray(graph?.events) ? graph.events : [];
  if (existingEvents.some(entry => replayEquivalent(entry?.event ?? entry, valid))) return graph;
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

