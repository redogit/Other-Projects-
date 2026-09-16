export const EMPTY_DIMENSION = -1;
export const LADDER_MIN_DIMENSION = 0;
export const LADDER_MAX_DIMENSION = 4;
export const DIMENSION_LADDER_BOUNDARY = 'ADJACENT_DIMENSIONS_RELATED != ADJACENT_DIMENSIONS_IDENTICAL';

const DEG = Math.PI / 180;

function freezePoint(point, { minDimension = 0, maxDimension = LADDER_MAX_DIMENSION } = {}) {
  if (!Array.isArray(point)) throw new TypeError('point must be an array');
  if (point.length < minDimension || point.length > maxDimension) {
    throw new RangeError(`point dimension must be ${minDimension} through ${maxDimension}`);
  }
  if (point.some(value => !Number.isFinite(value))) throw new TypeError('point coordinates must be finite');
  return Object.freeze(point.map(value => Object.is(value, -0) ? 0 : value));
}

function assertAxis(axis, dimension, name = 'axis') {
  if (!Number.isInteger(axis) || axis < 0 || axis >= dimension) {
    throw new RangeError(`${name} must be an integer in [0, ${dimension - 1}]`);
  }
}

function assertLadderDimension(dimension) {
  if (!Number.isInteger(dimension) || dimension < LADDER_MIN_DIMENSION || dimension > LADDER_MAX_DIMENSION) {
    throw new RangeError('dimension must be an integer from 0 through 4');
  }
}

function freezeRecord(record) {
  for (const [key, value] of Object.entries(record)) {
    if (Array.isArray(value) && !Object.isFrozen(value)) Object.freeze(value);
    if (value && typeof value === 'object' && !Object.isFrozen(value)) Object.freeze(value);
  }
  return Object.freeze(record);
}

export function embedPoint(point) {
  const source = freezePoint(point, { minDimension: 0, maxDimension: LADDER_MAX_DIMENSION - 1 });
  return Object.freeze([...source, 0]);
}

export function projectPoint(point, axis = undefined) {
  const source = freezePoint(point, { minDimension: 1, maxDimension: LADDER_MAX_DIMENSION });
  const resolvedAxis = axis === undefined ? source.length - 1 : axis;
  assertAxis(resolvedAxis, source.length);
  return Object.freeze(source.filter((_, index) => index !== resolvedAxis));
}

export function distance(a, b) {
  const left = freezePoint(a);
  const right = freezePoint(b);
  if (left.length !== right.length) throw new RangeError('points must have matching dimensions');
  return Math.hypot(...left.map((value, index) => value - right[index]));
}

export function rotatePointOneDegree(point, axisA, axisB, direction) {
  const source = freezePoint(point, { minDimension: 2, maxDimension: LADDER_MAX_DIMENSION });
  assertAxis(axisA, source.length, 'axisA');
  assertAxis(axisB, source.length, 'axisB');
  if (axisA === axisB) throw new RangeError('rotation axes must be distinct');
  if (direction !== 1 && direction !== -1) throw new RangeError('direction must be exactly +1 or -1');

  const theta = direction * DEG;
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  const rotated = [...source];
  rotated[axisA] = source[axisA] * c - source[axisB] * s;
  rotated[axisB] = source[axisA] * s + source[axisB] * c;
  return freezePoint(rotated, { minDimension: source.length, maxDimension: source.length });
}

export function slicePoints(points, { axis, value, epsilon = 0 } = {}) {
  if (!Array.isArray(points) || points.length === 0) throw new TypeError('points must be a non-empty array');
  if (!Number.isFinite(value)) throw new TypeError('slice value must be finite');
  if (!Number.isFinite(epsilon) || epsilon < 0) throw new RangeError('epsilon must be finite and non-negative');

  const frozen = points.map(point => freezePoint(point));
  const dimension = frozen[0].length;
  if (dimension === 0) throw new RangeError('cannot define a coordinate hyperplane slice in 0D');
  if (frozen.some(point => point.length !== dimension)) throw new RangeError('all points must have matching dimensions');
  assertAxis(axis, dimension);

  return Object.freeze(
    frozen.filter(point => Math.abs(point[axis] - value) <= epsilon)
  );
}

export function ballBoundaryDimension(dimension) {
  assertLadderDimension(dimension);
  return dimension === 0 ? EMPTY_DIMENSION : dimension - 1;
}

export function dimensionalLadderFixtures() {
  const embeddedSource = Object.freeze([2, -1]);
  const embeddedTarget = embedPoint(embeddedSource);

  const projectionA = Object.freeze([1, 2, 3]);
  const projectionB = Object.freeze([1, 2, 9]);
  const projectionA2 = projectPoint(projectionA, 2);
  const projectionB2 = projectPoint(projectionB, 2);

  const segmentA = Object.freeze([-1, 0, 0]);
  const segmentB = Object.freeze([1, 0, 0]);
  const rotatedA = rotatePointOneDegree(segmentA, 0, 2, 1);
  const rotatedB = rotatePointOneDegree(segmentB, 0, 2, 1);
  const intrinsicBefore = distance(segmentA, segmentB);
  const intrinsicAfter = distance(rotatedA, rotatedB);
  const projectedBefore = distance(projectPoint(segmentA, 2), projectPoint(segmentB, 2));
  const projectedAfter = distance(projectPoint(rotatedA, 2), projectPoint(rotatedB, 2));

  const boundaryExamples = Object.freeze(
    Array.from({ length: LADDER_MAX_DIMENSION + 1 }, (_, dimension) =>
      freezeRecord({ objectDimension: dimension, boundaryDimension: ballBoundaryDimension(dimension) })
    )
  );

  return freezeRecord({
    version: 's1-dimension-ladder/v0',
    ladder: Object.freeze([0, 1, 2, 3, 4]),
    boundary: DIMENSION_LADDER_BOUNDARY,
    embedding: freezeRecord({
      map: 'R^n -> R^(n+1) by appending 0',
      sourceDimension: embeddedSource.length,
      targetDimension: embeddedTarget.length,
      source: embeddedSource,
      target: embeddedTarget,
      normPreserved: Math.abs(distance(embeddedSource, Object.freeze([0, 0])) - distance(embeddedTarget, Object.freeze([0, 0, 0]))) <= 1e-12
    }),
    projectionLoss: freezeRecord({
      map: 'drop coordinate 2',
      sourceA: projectionA,
      sourceB: projectionB,
      projectionA: projectionA2,
      projectionB: projectionB2,
      sameProjection: projectionA2.every((value, index) => value === projectionB2[index]),
      sourcePointsDistinct: projectionA.some((value, index) => value !== projectionB[index])
    }),
    boundaryDrop: freezeRecord({
      object: 'closed-n-ball',
      convention: 'boundary(D^n) = S^(n-1); S^-1 is the empty set',
      examples: boundaryExamples
    }),
    projectedDeformation: freezeRecord({
      transform: 'rigid +1 degree rotation in the x-z plane followed by z projection',
      intrinsicDistanceBefore: intrinsicBefore,
      intrinsicDistanceAfter: intrinsicAfter,
      projectedDistanceBefore: projectedBefore,
      projectedDistanceAfter: projectedAfter,
      intrinsicDistancePreserved: Math.abs(intrinsicAfter - intrinsicBefore) <= 1e-12,
      projectedDistanceChanged: Math.abs(projectedAfter - projectedBefore) > 1e-12,
      interpretation: 'projection changes the observed segment length while the ambient segment length is invariant'
    }),
    negativeEdge: freezeRecord({
      object: 'empty-set convention used for the boundary of D^0',
      dimension: EMPTY_DIMENSION,
      physicalClaim: false,
      extensionBelowMinusOneSupported: false
    }),
    claimCeiling: Object.freeze([
      'finite Euclidean fixtures only',
      'no universal dimensional law',
      'no physical negative-dimensional-space claim',
      'no Hodge or P-vs-NP evidence transfer'
    ])
  });
}
