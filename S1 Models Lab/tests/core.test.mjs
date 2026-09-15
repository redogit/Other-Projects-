import test from 'node:test';
import assert from 'node:assert/strict';
import {
  createState, createMirror, applyMove, rotatePoint4, compareStates
} from '../core.mjs';

test('xw +1 degree moves x into w without mutating input', () => {
  const p = Object.freeze([1, 0, 0, 0]);
  const q = rotatePoint4(p, 'xw', 1);
  assert.ok(Math.abs(q[0] - Math.cos(Math.PI / 180)) < 1e-12);
  assert.ok(Math.abs(q[3] - Math.sin(Math.PI / 180)) < 1e-12);
  assert.deepEqual(p, [1,0,0,0]);
});

test('mirror remains equal to origin while live state moves', () => {
  const origin = createState([[1,0,0,0],[0,1,0,0]]);
  const mirror = createMirror(origin);
  const live = applyMove(origin, { plane: 'xw', degrees: 1 });
  assert.equal(compareStates(origin, mirror).equal, true);
  assert.equal(compareStates(live, mirror).equal, false);
  assert.equal(mirror.actions.length, 0);
});

test('only one-degree declared moves are admitted', () => {
  const origin = createState([[1,0,0,0]]);
  assert.throws(() => applyMove(origin, {plane:'xy', degrees:1}));
  assert.throws(() => applyMove(origin, {plane:'xw', degrees:2}));
  assert.throws(() => applyMove(origin, {plane:'xw', degrees:NaN}));
});

test('origin displacement exceeds latest-step displacement after two same-plane moves', () => {
  const origin = createState([[1,0,0,0]]);
  const s1 = applyMove(origin, {plane:'xw',degrees:1});
  const s2 = applyMove(s1, {plane:'xw',degrees:1});
  assert.ok(compareStates(s2, origin).maxAbsDelta > compareStates(s2, s1).maxAbsDelta);
});
