import test from 'node:test';
import assert from 'node:assert/strict';
import { rotatePoint4, createState } from '../core.mjs';
import { DEFAULT_OBSERVER } from '../observer.mjs';
import {
  IDENTITY4,
  LEGAL_MOVES,
  rotationMatrix4,
  multiplyMatrix4,
  applyMatrix4,
  composeActionMatrix,
  matrixInvariantMetrics,
  compareStatesQuantified,
  binary64AccumulationBudget,
  longHorizonRotationProbe,
  exhaustiveRotationSweep,
  observerConditionReport
} from '../rigor.mjs';

function maxAbsDelta(a,b) {
  let max = 0;
  for (let i=0;i<a.length;i++) max = Math.max(max, Math.abs(a[i]-b[i]));
  return max;
}

function direct(point, actions) {
  let p = point;
  for (const move of actions) p = rotatePoint4(p, move.plane, move.degrees);
  return p;
}

test('independent 4x4 oracle agrees with production kernel on representative paths', () => {
  assert.deepEqual([...IDENTITY4], [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]);
  assert.equal(LEGAL_MOVES.length, 6);

  const point = [0.25,-0.5,0.75,-1.25];
  const paths = [
    [],
    [{plane:'xw',degrees:1}],
    [{plane:'yw',degrees:-1},{plane:'zw',degrees:1}],
    [
      {plane:'xw',degrees:1},{plane:'yw',degrees:1},{plane:'zw',degrees:-1},
      {plane:'xw',degrees:-1},{plane:'yw',degrees:1},{plane:'zw',degrees:1}
    ]
  ];

  for (const actions of paths) {
    const matrix = composeActionMatrix(actions);
    const viaMatrix = applyMatrix4(matrix, point);
    const viaKernel = direct(point, actions);
    const bound = binary64AccumulationBudget(Math.max(1, actions.length) * 96);
    assert.ok(maxAbsDelta(viaMatrix, viaKernel) <= bound, `path length ${actions.length}`);
    const metrics = matrixInvariantMetrics(matrix);
    assert.ok(metrics.orthogonalityResidual <= binary64AccumulationBudget(Math.max(1, actions.length) * 96));
    assert.ok(metrics.determinantResidual <= binary64AccumulationBudget(Math.max(1, actions.length) * 96));
  }
});

test('rotation composition retains directional noncommutativity', () => {
  const x = rotationMatrix4('xw', 1);
  const y = rotationMatrix4('yw', 1);
  const xy = multiplyMatrix4(y, x);
  const yx = multiplyMatrix4(x, y);
  assert.ok(maxAbsDelta(xy, yx) > 1e-6);
});

test('quantified state comparison uses absolute plus relative tolerance', () => {
  const a = createState([[1, 1e9, 0, 0]]);
  const b = createState([[1 + 5e-13, 1e9 + 5e-4, 1e-13, 0]]);
  const pass = compareStatesQuantified(a,b,{absTolerance:1e-12,relTolerance:1e-12});
  assert.equal(pass.equal, true);
  assert.ok(pass.maxAbsDelta >= 5e-4);
  assert.ok(pass.maxErrorRatio <= 1);

  const fail = compareStatesQuantified(a,b,{absTolerance:1e-15,relTolerance:1e-15});
  assert.equal(fail.equal, false);
  assert.ok(fail.maxErrorRatio > 1);
});

test('binary64 budget is finite, monotone, and rejects an unsafe denominator', () => {
  const a = binary64AccumulationBudget(1);
  const b = binary64AccumulationBudget(1_000_000);
  assert.ok(a > 0);
  assert.ok(b > a);
  assert.ok(Number.isFinite(b));
  assert.throws(() => binary64AccumulationBudget(Number.MAX_SAFE_INTEGER));
});

test('long-horizon same-plane and mixed inverse probes stay inside their calculated budgets', () => {
  const samePlane = longHorizonRotationProbe({
    point:[1,0,0,0],
    actions:[{plane:'xw',degrees:1}],
    repetitions:1_000_000,
    expectedAngleDegrees:1_000_000
  });
  assert.ok(samePlane.maxAbsDelta <= samePlane.errorBudget);
  assert.ok(samePlane.normResidual <= samePlane.errorBudget);

  const mixedActions = [
    {plane:'xw',degrees:1},{plane:'yw',degrees:-1},{plane:'zw',degrees:1},
    {plane:'yw',degrees:1},{plane:'xw',degrees:-1},{plane:'zw',degrees:-1}
  ];
  const mixed = longHorizonRotationProbe({
    point:[0.5,-0.5,0.5,-0.5],
    actions:mixedActions,
    repetitions:50_000,
    inverseRoundTrip:true
  });
  assert.ok(mixed.maxAbsDelta <= mixed.errorBudget);
  assert.ok(mixed.normResidual <= mixed.errorBudget);
});

test('depth-eight finite move tree is exhaustively visited under matrix invariants', () => {
  const sweep = exhaustiveRotationSweep(8);
  assert.equal(sweep.maxDepth, 8);
  assert.equal(sweep.pathCount, 2_015_539);
  const budget = binary64AccumulationBudget(8 * 96);
  assert.ok(sweep.maxOrthogonalityResidual <= budget);
  assert.ok(sweep.maxDeterminantResidual <= budget);
});

test('observer conditioning exposes clamp information loss and valid-domain denominator floor', () => {
  const ordinary = observerConditionReport([1,2,3,0.2], DEFAULT_OBSERVER);
  assert.equal(ordinary.clamped, false);
  assert.equal(ordinary.informationLoss, false);
  assert.ok(ordinary.denominator > 0.1);

  const stressed = observerConditionReport([1,2,3,-0.9], {...DEFAULT_OBSERVER,wPerspective:0.999999});
  assert.equal(stressed.atClampBoundary, true);
  assert.ok(stressed.denominator > 0.1);
  assert.ok(stressed.localScaleSensitivityToW > 90);

  const clamped = observerConditionReport([1,2,3,-10], {...DEFAULT_OBSERVER,wPerspective:0.999999});
  assert.equal(clamped.clamped, true);
  assert.equal(clamped.informationLoss, true);
  assert.equal(clamped.localScaleSensitivityToW, 0);
  assert.equal(clamped.contractDenominatorFloorExclusive, 0.1);
});
