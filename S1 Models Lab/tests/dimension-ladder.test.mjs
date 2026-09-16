import test from 'node:test';
import assert from 'node:assert/strict';
import {
  EMPTY_DIMENSION,
  LADDER_MAX_DIMENSION,
  ballBoundaryDimension,
  distance,
  embedPoint,
  projectPoint,
  rotatePointOneDegree,
  slicePoints,
  dimensionalLadderFixtures
} from '../dimension-ladder.mjs';

test('adjacent embedding followed by canonical projection is a left inverse from 0D through 3D', () => {
  const points = [[], [2], [2, -3], [2, -3, 5]];
  for (const point of points) {
    const embedded = embedPoint(point);
    assert.equal(embedded.length, point.length + 1);
    assert.deepEqual(projectPoint(embedded, embedded.length - 1), point);
  }
  assert.equal(LADDER_MAX_DIMENSION, 4);
});

test('projection is explicitly many-to-one and can lose information', () => {
  const a = Object.freeze([1, 2, 3]);
  const b = Object.freeze([1, 2, 9]);
  assert.notDeepEqual(a, b);
  assert.deepEqual(projectPoint(a, 2), [1, 2]);
  assert.deepEqual(projectPoint(b, 2), [1, 2]);
});

test('closed n-ball boundary fixture drops one dimension including the empty -1 convention', () => {
  assert.equal(ballBoundaryDimension(0), EMPTY_DIMENSION);
  assert.equal(ballBoundaryDimension(1), 0);
  assert.equal(ballBoundaryDimension(2), 1);
  assert.equal(ballBoundaryDimension(3), 2);
  assert.equal(ballBoundaryDimension(4), 3);
});

test('one-degree rigid rotation preserves intrinsic distance while its projection can deform', () => {
  const a = Object.freeze([-1, 0, 0]);
  const b = Object.freeze([1, 0, 0]);
  const beforeIntrinsic = distance(a, b);
  const beforeProjected = distance(projectPoint(a, 2), projectPoint(b, 2));
  const ar = rotatePointOneDegree(a, 0, 2, 1);
  const br = rotatePointOneDegree(b, 0, 2, 1);
  const afterIntrinsic = distance(ar, br);
  const afterProjected = distance(projectPoint(ar, 2), projectPoint(br, 2));

  assert.ok(Math.abs(afterIntrinsic - beforeIntrinsic) <= 1e-12);
  assert.ok(afterProjected < beforeProjected);
  assert.ok(Math.abs(afterProjected - 2 * Math.cos(Math.PI / 180)) <= 1e-12);
});

test('finite slices preserve source dimension and select only the declared hyperplane', () => {
  const points = [
    [0, 0, -1, 0],
    [1, 2, 0, 4],
    [3, 4, 0, -2],
    [5, 6, 1, 0]
  ];
  const slice = slicePoints(points, { axis: 2, value: 0 });
  assert.deepEqual(slice, [[1, 2, 0, 4], [3, 4, 0, -2]]);
  assert.equal(slice.every(point => point.length === 4), true);
});

test('fixture pack exposes each required witness without promoting an adjacent-dimension identity claim', () => {
  const fixtures = dimensionalLadderFixtures();
  assert.equal(fixtures.version, 's1-dimension-ladder/v0');
  assert.equal(fixtures.boundary, 'ADJACENT_DIMENSIONS_RELATED != ADJACENT_DIMENSIONS_IDENTICAL');
  assert.equal(fixtures.embedding.sourceDimension, 2);
  assert.equal(fixtures.embedding.targetDimension, 3);
  assert.equal(fixtures.projectionLoss.sameProjection, true);
  assert.equal(fixtures.boundaryDrop.object, 'closed-n-ball');
  assert.equal(fixtures.projectedDeformation.intrinsicDistancePreserved, true);
  assert.equal(fixtures.projectedDeformation.projectedDistanceChanged, true);
  assert.equal(fixtures.negativeEdge.dimension, -1);
  assert.equal(fixtures.negativeEdge.physicalClaim, false);
  assert.equal(Object.isFrozen(fixtures), true);
});

test('dimension-ladder primitives fail closed on unsupported dimensions, axes, and non-one-degree rotations', () => {
  assert.throws(() => embedPoint([1, 2, 3, 4]), /0 through 3/);
  assert.throws(() => projectPoint([], 0));
  assert.throws(() => projectPoint([1, 2], 2));
  assert.throws(() => rotatePointOneDegree([1, 2], 0, 1, 2), /exactly \+1 or -1/);
  assert.throws(() => rotatePointOneDegree([1, 2], 0, 0, 1), /distinct/);
  assert.throws(() => ballBoundaryDimension(5), /0 through 4/);
});
