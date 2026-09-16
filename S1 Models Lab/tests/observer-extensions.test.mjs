import test from 'node:test';
import assert from 'node:assert/strict';
import { canonicalJson, makeExperience } from '../experience.mjs';
import { sampleS3 } from '../geometry.mjs';
import { DEFAULT_OBSERVER } from '../observer.mjs';
import {
  OBSERVATION_SCHEMA,
  OBSERVER_ORDER,
  compareObservationRecords,
  observeExperience,
  validateObservationRecord
} from '../observer-extensions.mjs';

function makeFixture(actions = [{ plane: 'xw', degrees: 1 }]) {
  const geometry = sampleS3({ etaSteps: 2, xi1Steps: 4, xi2Steps: 4, radius: 1 });
  const event = makeExperience({
    initialState: geometry.id,
    mirrorId: `mirror:${geometry.id}`,
    shell: geometry.id,
    actions,
    observer: DEFAULT_OBSERVER,
    observerField: {
      version: 's1-observer-field/v0',
      taskVersion: 's1-observer-task/v0',
      densityId: 'observer-extension-test',
      calibrations: []
    },
    checkpoints: [],
    comparisons: {
      obligation: 'same-event-observer-extension-test',
      againstMirror: { equal: actions.length === 0, maxAbsDelta: actions.length === 0 ? 0 : 0.1 },
      againstPrevious: { equal: actions.length === 0, maxAbsDelta: actions.length === 0 ? 0 : 0.1 }
    },
    relations: { familyId: 'observer-extension-test', parentId: null, relatedIds: [] },
    provenance: { source: 'observer-extension-test' }
  });
  return { geometry, event, registry: new Map([[geometry.id, geometry]]) };
}

test('observer sidecars preserve one source event identity while producing five separate records', () => {
  const { event, registry } = makeFixture();
  const before = canonicalJson(event);
  const records = observeExperience(event, registry);

  assert.deepEqual(records.map(record => record.observerType), OBSERVER_ORDER);
  assert.equal(records.length, 5);
  assert.equal(new Set(records.map(record => record.id)).size, 5);
  assert.equal(records.every(record => record.schema === OBSERVATION_SCHEMA), true);
  assert.equal(records.every(record => record.sourceEventId === event.id), true);
  assert.equal(records.every(record => record.truthAuthority === false), true);
  assert.equal(records.every(record => record.evidenceRole === 'derived-observation'), true);
  assert.equal(records.every(record => Object.isFrozen(record)), true);
  assert.equal(canonicalJson(event), before);
});

test('projection, slice, metric, and topology observers expose losses without promoting them to source truth', () => {
  const { event, geometry, registry } = makeFixture();
  const records = observeExperience(event, registry, {
    projection: { axis: 3 },
    slice: { axis: 3, value: 0, epsilon: 1e-12 }
  });
  const byType = Object.fromEntries(records.map(record => [record.observerType, record]));

  assert.equal(byType.projection.mappingVersion, 's1-projection/drop-axis-v0');
  assert.equal(byType.projection.payload.sourceDimension, 4);
  assert.equal(byType.projection.payload.observedDimension, 3);
  assert.equal(byType.projection.payload.pointCount, geometry.points4.length);
  assert.equal(byType.projection.payload.nonInjectiveByContract, true);
  assert.equal(byType.projection.payload.extentChanged, true);

  assert.equal(byType.slice.mappingVersion, 's1-slice/coordinate-hyperplane-v0');
  assert.equal(byType.slice.payload.sourcePointCount, geometry.points4.length);
  assert.equal(Array.isArray(byType.slice.payload.originSelectedIndices), true);
  assert.equal(Array.isArray(byType.slice.payload.liveSelectedIndices), true);
  assert.equal(byType.slice.losses.includes('points outside the declared slice are not observed'), true);

  assert.equal(byType.metric.mappingVersion, 's1-metric/origin-radius-v0');
  assert.equal(byType.metric.payload.originRadiusPreserved, true);
  assert.ok(byType.metric.payload.maxPointDisplacement > 0);
  assert.equal(byType.metric.payload.intrinsicRigidityClaim, false);

  assert.equal(byType.topology.mappingVersion, 's1-topology/finite-incidence-proxy-v0');
  assert.equal(byType.topology.payload.sourcePointCount, geometry.points4.length);
  assert.equal(byType.topology.payload.groupCount, geometry.groups.length);
  assert.equal(byType.topology.payload.continuumTopologyClaim, false);
});

test('sonification is deterministic replay metadata for the same event and adds no evidence', () => {
  const { event, registry } = makeFixture([
    { plane: 'xw', degrees: 1 },
    { plane: 'yw', degrees: -1 },
    { plane: 'zw', degrees: 1 }
  ]);
  const first = observeExperience(event, registry);
  const second = observeExperience(event, registry);
  assert.deepEqual(first, second);

  const sound = first.find(record => record.observerType === 'sound');
  assert.equal(sound.mappingVersion, 's1-sonification/action-triad-v0');
  assert.equal(sound.payload.evidenceAdded, false);
  assert.deepEqual(sound.payload.notes.map(note => note.midi), [60, 52, 67]);
  assert.equal(sound.payload.notes.every(note => note.durationMs === 120), true);
});

test('comparison keeps disagreement explicit and requests a discriminator instead of forced consensus', () => {
  const { event, registry } = makeFixture();
  const records = observeExperience(event, registry);
  const comparison = compareObservationRecords(records);

  assert.equal(comparison.sourceEventId, event.id);
  assert.equal(comparison.sameSourceEvent, true);
  assert.equal(comparison.sharedInvariants.includes('source event identity'), true);
  const disagreement = comparison.disagreements.find(entry => entry.kind === 'projection-vs-metric');
  assert.ok(disagreement);
  assert.equal(disagreement.resolution, 'new-discriminator-required');
  assert.equal(disagreement.forcedConsensus, false);
  assert.equal(comparison.soundAddsEvidence, false);
});

test('observation records validate canonically and mixed-event comparison fails closed', () => {
  const first = makeFixture([{ plane: 'xw', degrees: 1 }]);
  const second = makeFixture([{ plane: 'yw', degrees: 1 }]);
  const a = observeExperience(first.event, first.registry);
  const b = observeExperience(second.event, second.registry);

  for (const record of a) assert.deepEqual(validateObservationRecord(record), record);
  assert.throws(() => compareObservationRecords([a[0], b[1]]), /same source event/);
  assert.throws(() => observeExperience(first.event, first.registry, { projection: { axis: 4 } }));
  assert.throws(() => observeExperience(first.event, first.registry, { slice: { axis: 3, value: 0, epsilon: -1 } }));
});
