import { assertSupportedMove } from './core.mjs';
import {
  EXPERIENCE_SCHEMA,
  OPERATOR_VERSION,
  canonicalJson,
  fnv1a64,
  replayIdentity,
  validateExperience
} from './experience.mjs';

export const SUGGEST_DATASET_VERSION = 's1-suggest-dataset/v0';
export const SUGGEST_MODEL_VERSION = 's1-suggest-transition/v0';
export const SUGGEST_CARRIER_VERSION = 's1-transition-carrier/v0';

const LEGAL_MOVES = Object.freeze([
  Object.freeze({ plane: 'xw', degrees: 1 }),
  Object.freeze({ plane: 'xw', degrees: -1 }),
  Object.freeze({ plane: 'yw', degrees: 1 }),
  Object.freeze({ plane: 'yw', degrees: -1 }),
  Object.freeze({ plane: 'zw', degrees: 1 }),
  Object.freeze({ plane: 'zw', degrees: -1 })
]);
const MOVE_ORDER = new Map(LEGAL_MOVES.map((move, index) => [`${move.plane}:${move.degrees}`, index]));
const CONTEXT_KEYS = Object.freeze(['initialState', 'mirrorId', 'operatorVersion', 'actions']);
const DERIVED_EXPERIENCE_KEYS = Object.freeze(['id', 'replayId', ...CONTEXT_KEYS]);

function deepFreeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    for (const child of Object.values(value)) deepFreeze(child);
    Object.freeze(value);
  }
  return value;
}

function assertPlainObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new TypeError(`${label} must be an object`);
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) throw new TypeError(`${label} must be a plain object`);
}

function assertOnlyKeys(value, allowed, label) {
  for (const key of Object.keys(value)) if (!allowed.includes(key)) throw new RangeError(`unsupported ${label} field: ${key}`);
}

function cloneMove(move) {
  assertSupportedMove(move);
  return { plane: move.plane, degrees: move.degrees };
}

function moveKey(move) {
  return `${move.plane}:${move.degrees}`;
}

function compareMoves(a, b) {
  return MOVE_ORDER.get(moveKey(a)) - MOVE_ORDER.get(moveKey(b));
}

function normalizeContext(context) {
  assertPlainObject(context, 'suggestion context');
  assertOnlyKeys(context, CONTEXT_KEYS, 'suggestion context');
  if (typeof context.initialState !== 'string' || !context.initialState) throw new TypeError('suggestion initialState is required');
  if (typeof context.mirrorId !== 'string' || !context.mirrorId) throw new TypeError('suggestion mirrorId is required');
  if (context.operatorVersion !== OPERATOR_VERSION) throw new RangeError('unsupported suggestion operator version');
  if (!Array.isArray(context.actions)) throw new TypeError('suggestion actions must be an array');
  return {
    initialState: context.initialState,
    mirrorId: context.mirrorId,
    operatorVersion: context.operatorVersion,
    actions: context.actions.map(cloneMove)
  };
}

function contextKey(context) {
  return canonicalJson(normalizeContext(context));
}

function normalizedExperience(record) {
  const valid = validateExperience(record);
  return {
    id: valid.id,
    replayId: replayIdentity(valid),
    initialState: valid.initialState,
    mirrorId: valid.mirrorId,
    operatorVersion: valid.operatorVersion,
    actions: valid.actions.map(cloneMove)
  };
}

export function deriveSuggestionDataset(records) {
  if (!Array.isArray(records)) throw new TypeError('experience records must be an array');
  const unique = new Map();
  for (const record of records) {
    const item = normalizedExperience(record);
    if (!unique.has(item.replayId)) unique.set(item.replayId, item);
  }
  const experiences = [...unique.values()];
  return deepFreeze({
    version: SUGGEST_DATASET_VERSION,
    sourceSchema: EXPERIENCE_SCHEMA,
    operatorVersion: OPERATOR_VERSION,
    derivation: {
      policy: 'unique-replay-paths',
      inputRecordCount: records.length,
      uniqueReplayCount: experiences.length,
      duplicateReplayCount: records.length - experiences.length
    },
    experiences
  });
}

function validateDataset(dataset) {
  assertPlainObject(dataset, 'suggestion dataset');
  if (dataset.version !== SUGGEST_DATASET_VERSION) throw new RangeError('unsupported suggestion dataset version');
  if (dataset.sourceSchema !== EXPERIENCE_SCHEMA) throw new RangeError('unsupported suggestion source schema');
  if (dataset.operatorVersion !== OPERATOR_VERSION) throw new RangeError('unsupported suggestion dataset operator version');
  if (!Array.isArray(dataset.experiences)) throw new TypeError('suggestion dataset experiences must be an array');
  for (const item of dataset.experiences) {
    assertPlainObject(item, 'derived experience');
    assertOnlyKeys(item, DERIVED_EXPERIENCE_KEYS, 'derived experience');
    if (typeof item.id !== 'string' || !item.id || typeof item.replayId !== 'string' || !item.replayId) throw new TypeError('derived experience ids are required');
    normalizeContext({
      initialState: item.initialState,
      mirrorId: item.mirrorId,
      operatorVersion: item.operatorVersion,
      actions: item.actions
    });
  }
  return dataset;
}

export function trainSuggestionModel(dataset) {
  const valid = validateDataset(dataset);
  const routeMap = new Map();

  for (const experience of valid.experiences) {
    for (let index = 0; index < experience.actions.length; index++) {
      const context = normalizeContext({
        initialState: experience.initialState,
        mirrorId: experience.mirrorId,
        operatorVersion: experience.operatorVersion,
        actions: experience.actions.slice(0, index)
      });
      const key = contextKey(context);
      let route = routeMap.get(key);
      if (!route) {
        route = { key, context, candidates: new Map() };
        routeMap.set(key, route);
      }
      const move = cloneMove(experience.actions[index]);
      const candidateKey = moveKey(move);
      let candidate = route.candidates.get(candidateKey);
      if (!candidate) {
        candidate = { move, sourceExperienceIds: new Set() };
        route.candidates.set(candidateKey, candidate);
      }
      candidate.sourceExperienceIds.add(experience.id);
    }
  }

  const routes = [...routeMap.values()]
    .sort((a, b) => a.key.localeCompare(b.key))
    .map(route => ({
      key: route.key,
      context: route.context,
      candidates: [...route.candidates.values()]
        .sort((a, b) => compareMoves(a.move, b.move))
        .map(candidate => ({
          move: candidate.move,
          sourceExperienceIds: [...candidate.sourceExperienceIds].sort()
        }))
    }));

  return deepFreeze({
    version: SUGGEST_MODEL_VERSION,
    datasetVersion: valid.version,
    sourceSchema: valid.sourceSchema,
    operatorVersion: valid.operatorVersion,
    routes
  });
}

function validateModel(model) {
  assertPlainObject(model, 'suggestion model');
  if (model.version !== SUGGEST_MODEL_VERSION) throw new RangeError('unsupported suggestion model version');
  if (model.datasetVersion !== SUGGEST_DATASET_VERSION) throw new RangeError('unsupported suggestion model dataset version');
  if (model.sourceSchema !== EXPERIENCE_SCHEMA) throw new RangeError('unsupported suggestion model source schema');
  if (model.operatorVersion !== OPERATOR_VERSION) throw new RangeError('unsupported suggestion model operator version');
  if (!Array.isArray(model.routes)) throw new TypeError('suggestion model routes must be an array');
  return model;
}

export function suggestNextMove(model, context) {
  const validModel = validateModel(model);
  const normalized = normalizeContext(context);
  const key = canonicalJson(normalized);
  const route = validModel.routes.find(candidate => candidate.key === key);
  const observed = route?.candidates?.[0] ?? null;

  let kind;
  let move;
  let sourceExperienceIds;
  let strategy;
  if (observed) {
    kind = 'observed';
    move = cloneMove(observed.move);
    sourceExperienceIds = [...observed.sourceExperienceIds];
    strategy = 'observed-transition/v0';
  } else {
    kind = 'generated';
    const hash = BigInt(`0x${fnv1a64(key)}`);
    move = cloneMove(LEGAL_MOVES[Number(hash % BigInt(LEGAL_MOVES.length))]);
    sourceExperienceIds = [];
    strategy = 'deterministic-fallback/v0';
  }

  return deepFreeze({
    carrierVersion: SUGGEST_CARRIER_VERSION,
    kind,
    move,
    prefix: normalized.actions,
    contract: {
      initialState: normalized.initialState,
      mirrorId: normalized.mirrorId,
      operatorVersion: normalized.operatorVersion
    },
    provenance: {
      datasetVersion: validModel.datasetVersion,
      modelVersion: validModel.version,
      sourceExperienceIds,
      strategy
    },
    authority: 'suggestion-only'
  });
}
