import test from 'node:test';
import assert from 'node:assert/strict';
import { makeObserverField, TASKS } from '../observer-field.mjs';

const points = [
  [1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1],
  [-1,0,0,0], [0,-1,0,0], [0,0,-1,0], [0,0,0,-1]
];

test('every sampled point gets exactly one observer and one task', () => {
  const field = makeObserverField({points4: points, sourceDimension: 4, densityId:'fixture-8'});
  assert.equal(field.observers.length, points.length);
  for (const observer of field.observers) {
    assert.equal(typeof observer.task, 'string');
    assert.ok(TASKS.includes(observer.task));
    assert.equal(typeof observer.calibration, 'number');
  }
});

test('task assignment is deterministic', () => {
  const a = makeObserverField({points4: points, sourceDimension:4, densityId:'fixture-8'});
  const b = makeObserverField({points4: points, sourceDimension:4, densityId:'fixture-8'});
  assert.deepEqual(a, b);
});

test('task classes repeat across distinct locations at control density', () => {
  const many = Array.from({length: 21}, (_, i) => [i, i+1, i+2, i+3]);
  const field = makeObserverField({points4: many, sourceDimension:4, densityId:'fixture-21'});
  const counts = Object.fromEntries(TASKS.map(task => [task, 0]));
  for (const observer of field.observers) counts[observer.task]++;
  for (const task of TASKS) assert.ok(counts[task] >= 2, `${task} should repeat`);
});

import { measureObserver, repairObserver } from '../observer-field.mjs';

test('each task produces one finite scalar residual', () => {
  const taskPoints = Array.from({length: 7}, (_, i) => [1+i, 2+i, 3+i, 4+i]);
  const field = makeObserverField({points4: taskPoints, sourceDimension:4, densityId:'task-fixture'});
  const byTask = new Map(field.observers.map(o => [o.task, o]));
  for (const task of TASKS) {
    const observer = byTask.get(task);
    assert.ok(observer, `missing ${task}`);
    const live = taskPoints[observer.sourceIndex].map((v,j) => v + (j+1)*0.01);
    const mirror = taskPoints[observer.sourceIndex];
    const result = measureObserver(observer, live, mirror);
    assert.equal(result.task, task);
    assert.ok(Number.isFinite(result.liveValue));
    assert.ok(Number.isFinite(result.mirrorValue));
    assert.ok(Number.isFinite(result.residual));
  }
});

test('one-degree observational repair changes only calibration', () => {
  const field = makeObserverField({points4: points, sourceDimension:4, densityId:'repair-fixture'});
  const observer = field.observers[0];
  const live = JSON.stringify(points[0]);
  const mirror = JSON.stringify(points[0]);
  const repaired = repairObserver(observer, 0.25);
  assert.equal(repaired.calibration, observer.calibration + 0.25);
  assert.equal(repaired.task, observer.task);
  assert.equal(repaired.sourcePointId, observer.sourcePointId);
  assert.equal(observer.calibration, 0);
  assert.equal(JSON.stringify(points[0]), live);
  assert.equal(JSON.stringify(points[0]), mirror);
  assert.throws(() => repairObserver(observer, Number.NaN));
  assert.throws(() => repairObserver(observer, {x: 1}));
});
