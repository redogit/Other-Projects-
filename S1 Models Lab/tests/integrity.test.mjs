import test from 'node:test';
import assert from 'node:assert/strict';
import { guardDigestCollision } from '../integrity.mjs';
import { makeExperience, replayDescriptor, replayIdentity, fnv1a64 } from '../experience.mjs';
import { DEFAULT_OBSERVER } from '../observer.mjs';

function record({ actions = [], relatedIds = [], source = 'integrity-test' } = {}) {
  return makeExperience({
    initialState:'fixture',
    mirrorId:'mirror:fixture',
    shell:'comparison',
    actions,
    observer:DEFAULT_OBSERVER,
    observerField:{version:'s1-observer-field/v0',taskVersion:'s1-observer-task/v0',densityId:'fixture',calibrations:[]},
    checkpoints:[],
    comparisons:{
      obligation:'live-vs-mirror',
      againstMirror:{equal:actions.length===0,maxAbsDelta:actions.length===0?0:0.01},
      againstPrevious:{equal:actions.length===0,maxAbsDelta:actions.length===0?0:0.01}
    },
    relations:{familyId:'integrity',parentId:null,relatedIds},
    provenance:{source}
  });
}

test('digest sentinel accepts identical canonical payload and rejects a forced collision', () => {
  const index = new Map();
  assert.equal(guardDigestCollision(index,'forced-digest','{"a":1}','unit'), '{"a":1}');
  assert.equal(guardDigestCollision(index,'forced-digest','{"a":1}','unit'), '{"a":1}');
  assert.throws(
    () => guardDigestCollision(index,'forced-digest','{"a":2}','unit'),
    /digest collision/i
  );
});

test('replay descriptor is the canonical preimage of the preserved v0 replay identity', () => {
  const a = record();
  const b = record({ relatedIds:['context-only'], source:'different-provenance' });
  assert.equal(replayIdentity(a), fnv1a64(replayDescriptor(a)));
  assert.equal(replayIdentity(b), fnv1a64(replayDescriptor(b)));
  assert.equal(replayDescriptor(a), replayDescriptor(b));
  assert.equal(replayIdentity(a), replayIdentity(b));
});

test('replay descriptor distinguishes a genuinely different trajectory', () => {
  const a = record();
  const b = record({actions:[{plane:'xw',degrees:1}]});
  assert.notEqual(replayDescriptor(a), replayDescriptor(b));
  assert.notEqual(replayIdentity(a), replayIdentity(b));
});
