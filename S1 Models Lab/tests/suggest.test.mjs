import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { EXPERIENCE_SCHEMA, OPERATOR_VERSION, makeExperience } from '../experience.mjs';

const moduleUrl = new URL('../suggest.mjs', import.meta.url);
const moduleExists = existsSync(fileURLToPath(moduleUrl));
const suggest = moduleExists ? await import('../suggest.mjs') : null;

function requireSuggest() {
  assert.ok(suggest, 'suggest.mjs must exist and load');
  return suggest;
}

const DEFAULT_OBSERVER = Object.freeze({ yaw: 0, pitch: 0, roll: 0, wPerspective: 0.35 });

function record(actions, source = 'fixture', options = {}) {
  const shell = options.shell ?? 's3-sample';
  const observer = options.observer ?? DEFAULT_OBSERVER;
  return makeExperience({
    initialState: 's3-sample',
    mirrorId: 'mirror:s3-sample',
    shell,
    actions,
    observer,
    observerField: {
      version: 's1-observer-field/v0',
      taskVersion: 's1-observer-task/v0',
      densityId: 'fixture:1',
      calibrations: []
    },
    checkpoints: actions.length === 0
      ? [{ actionIndex: 0, label: 'origin' }]
      : [{ actionIndex: 0, label: 'origin' }, { actionIndex: actions.length, label: 'current' }],
    comparisons: {
      obligation: 'live-vs-mirror',
      againstMirror: { equal: actions.length === 0, maxAbsDelta: actions.length === 0 ? 0 : 0.01 },
      againstPrevious: { equal: actions.length === 0, maxAbsDelta: actions.length === 0 ? 0 : 0.01 }
    },
    relations: { familyId: 's3-sample', parentId: null, relatedIds: [] },
    provenance: { source, localOnly: true }
  });
}

const XW_PLUS = Object.freeze({ plane: 'xw', degrees: 1 });
const YW_PLUS = Object.freeze({ plane: 'yw', degrees: 1 });
const ZW_MINUS = Object.freeze({ plane: 'zw', degrees: -1 });

function context(actions = [], options = {}) {
  return {
    initialState: 's3-sample',
    mirrorId: 'mirror:s3-sample',
    shell: options.shell ?? 's3-sample',
    observer: options.observer ?? DEFAULT_OBSERVER,
    operatorVersion: OPERATOR_VERSION,
    actions
  };
}

test('issue 44 suggestion module exists', () => {
  assert.equal(moduleExists, true);
});

test('derived dataset is versioned and deduplicates replay-equivalent records', () => {
  const { deriveSuggestionDataset, SUGGEST_DATASET_VERSION } = requireSuggest();
  const a = record([XW_PLUS], 'a');
  const duplicateA = record([XW_PLUS], 'a-duplicate-provenance');
  const b = record([YW_PLUS], 'b');
  const dataset = deriveSuggestionDataset([a, duplicateA, b]);

  assert.equal(dataset.version, SUGGEST_DATASET_VERSION);
  assert.equal(dataset.sourceSchema, EXPERIENCE_SCHEMA);
  assert.equal(dataset.operatorVersion, OPERATOR_VERSION);
  assert.deepEqual(dataset.derivation, {
    policy: 'unique-replay-paths',
    inputRecordCount: 3,
    uniqueReplayCount: 2,
    duplicateReplayCount: 1
  });
  assert.equal(dataset.experiences.length, 2);
  assert.equal(dataset.experiences[0].shell, 's3-sample');
  assert.deepEqual(dataset.experiences[0].observer, DEFAULT_OBSERVER);
  assert.ok(Object.isFrozen(dataset));
});

test('model returns an observed continuation with provenance but no authority transfer', () => {
  const { deriveSuggestionDataset, trainSuggestionModel, suggestNextMove } = requireSuggest();
  const a = record([XW_PLUS], 'a');
  const b = record([YW_PLUS], 'b');
  const model = trainSuggestionModel(deriveSuggestionDataset([a, b]));
  const result = suggestNextMove(model, context([]));

  assert.equal(result.kind, 'observed');
  assert.deepEqual(result.move, XW_PLUS);
  assert.equal(result.authority, 'suggestion-only');
  assert.equal(result.contract.initialState, 's3-sample');
  assert.equal(result.contract.mirrorId, 'mirror:s3-sample');
  assert.equal(result.contract.shell, 's3-sample');
  assert.deepEqual(result.contract.observer, DEFAULT_OBSERVER);
  assert.equal(result.contract.operatorVersion, OPERATOR_VERSION);
  assert.deepEqual(result.provenance.sourceExperienceIds, [a.id]);
  assert.match(result.provenance.datasetVersion, /^s1-suggest-dataset\//);
  assert.match(result.provenance.modelVersion, /^s1-suggest-transition\//);
  assert.ok(Object.isFrozen(result));
});

test('observer frame and shell remain part of exact observed-continuation identity', () => {
  const { deriveSuggestionDataset, trainSuggestionModel, suggestNextMove } = requireSuggest();
  const observerB = { yaw: 0.2, pitch: 0, roll: 0, wPerspective: 0.35 };
  const observerUnknown = { yaw: 0.4, pitch: 0, roll: 0, wPerspective: 0.35 };
  const frameA = record([XW_PLUS], 'frame-a');
  const frameB = record([YW_PLUS], 'frame-b', { observer: observerB });
  const shellC = record([ZW_MINUS], 'shell-c', { shell: 'comparison' });
  const model = trainSuggestionModel(deriveSuggestionDataset([frameA, frameB, shellC]));

  const a = suggestNextMove(model, context([]));
  const b = suggestNextMove(model, context([], { observer: observerB }));
  const c = suggestNextMove(model, context([], { shell: 'comparison' }));
  const unknown = suggestNextMove(model, context([], { observer: observerUnknown }));

  assert.equal(a.kind, 'observed');
  assert.deepEqual(a.move, XW_PLUS);
  assert.deepEqual(a.provenance.sourceExperienceIds, [frameA.id]);
  assert.equal(b.kind, 'observed');
  assert.deepEqual(b.move, YW_PLUS);
  assert.deepEqual(b.provenance.sourceExperienceIds, [frameB.id]);
  assert.equal(c.kind, 'observed');
  assert.deepEqual(c.move, ZW_MINUS);
  assert.deepEqual(c.provenance.sourceExperienceIds, [shellC.id]);
  assert.equal(unknown.kind, 'generated');
  assert.deepEqual(unknown.provenance.sourceExperienceIds, []);
});

test('unseen prefix gets deterministic generated suggestion explicitly separated from observed paths', () => {
  const { deriveSuggestionDataset, trainSuggestionModel, suggestNextMove } = requireSuggest();
  const model = trainSuggestionModel(deriveSuggestionDataset([record([XW_PLUS], 'a')]));
  const before = context([ZW_MINUS]);
  const snapshot = JSON.stringify(before);
  const one = suggestNextMove(model, before);
  const two = suggestNextMove(model, before);

  assert.deepEqual(one, two);
  assert.equal(one.kind, 'generated');
  assert.equal(one.authority, 'suggestion-only');
  assert.deepEqual(one.provenance.sourceExperienceIds, []);
  assert.match(one.provenance.strategy, /^deterministic-fallback\//);
  assert.equal(JSON.stringify(before), snapshot, 'suggestion must not mutate caller state');
});

test('suggestion derivation rejects malformed or version-smuggled experience records', () => {
  const { deriveSuggestionDataset } = requireSuggest();
  const valid = record([XW_PLUS], 'a');
  const tampered = structuredClone(valid);
  tampered.operatorVersion = "S'1-Ops future";
  assert.throws(() => deriveSuggestionDataset([tampered]), /operator version|unsupported/i);
});

test('suggestion carrier contains no identity/personality inference fields', () => {
  const { deriveSuggestionDataset, trainSuggestionModel, suggestNextMove } = requireSuggest();
  const result = suggestNextMove(trainSuggestionModel(deriveSuggestionDataset([])), context([]));
  const text = JSON.stringify(result).toLowerCase();
  for (const forbidden of ['personality', 'identityinference', 'healthinference', 'politicalinference', 'protectedtrait']) {
    assert.equal(text.includes(forbidden), false);
  }
});

test('UI exposes suggestion as optional text and keeps it outside S1_Experience construction', async () => {
  const root = new URL('../', import.meta.url);
  const html = await readFile(new URL('index.html', root), 'utf8');
  const app = await readFile(new URL('app.mjs', root), 'utf8');

  assert.match(html, /id=["']suggest["']/);
  assert.match(html, /id=["']suggestion["']/);
  assert.match(app, /deriveSuggestionDataset/);
  assert.match(app, /trainSuggestionModel/);
  assert.match(app, /suggestNextMove/);

  const currentRecord = app.match(/function currentRecord\(\) \{[\s\S]*?\n\}\n\nfunction refreshSaved/);
  assert.ok(currentRecord, 'currentRecord function must remain inspectable');
  assert.doesNotMatch(currentRecord[0], /suggest/i, 'suggestions must not enter S1_Experience records');
});
