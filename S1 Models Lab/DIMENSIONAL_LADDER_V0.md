# S'1 Dimensional Ladder v0

This note implements issue #40 as a bounded Euclidean fixture layer for adjacent dimensions.

## Claim boundary

`ADJACENT_DIMENSIONS_RELATED != ADJACENT_DIMENSIONS_IDENTICAL`

The executable layer covers dimensions `0..4` only. It supplies examples and counterexamples for transport between adjacent finite-dimensional Euclidean spaces. It does **not** establish a universal dimensional law, physical negative-dimensional space, continuum completeness, or evidence about Hodge or P vs NP.

## 1. Canonical adjacent embedding

For `0 <= n < 4`, use

`E_n(x_1, ..., x_n) = (x_1, ..., x_n, 0)`.

Dropping the appended coordinate is a left inverse on the embedded image:

`P_(n+1)(E_n(x)) = x`.

This preserves Euclidean norm on the embedded image, but it does not make `R^n` and `R^(n+1)` identical.

## 2. Projection loses information

Coordinate projection is generally many-to-one. The fixture uses

- `a = (1, 2, 3)`
- `b = (1, 2, 9)`

with the third coordinate dropped. Both project to `(1, 2)` although `a != b`.

Therefore reconstruction from a single projection is not unique without additional constraints or observations.

## 3. Boundary dimension for closed balls

For the specific family of closed balls `D^n`, the conventional relationship is

`boundary(D^n) = S^(n-1)`.

The bounded ladder records:

- `D^0 -> S^-1`, using `S^-1 = empty set`, dimension `-1`;
- `D^1 -> S^0`, dimension `0`;
- `D^2 -> S^1`, dimension `1`;
- `D^3 -> S^2`, dimension `2`;
- `D^4 -> S^3`, dimension `3`.

The `-1` entry is a mathematical convention for the empty set in this context. It is not a claim that physical negative-dimensional space exists, and the v0 carrier defines no extension below `-1`.

## 4. Slice/intersection fixture

`slicePoints` selects the members of a finite point carrier lying on a declared coordinate hyperplane within an explicit tolerance. It preserves the source coordinates rather than silently re-encoding the slice into a lower-dimensional coordinate system.

This keeps two questions separate:

1. which source points belong to an intersection; and
2. what intrinsic coordinate system or dimension should later be assigned to that intersection.

## 5. Projected deformation confound

Take the rigid 3D segment with endpoints `(-1,0,0)` and `(1,0,0)`. Rotate it by exactly `+1°` in the `x-z` plane, then drop `z`.

- intrinsic 3D segment length before: `2`;
- intrinsic 3D segment length after: `2` within floating-point tolerance;
- projected 2D length before: `2`;
- projected 2D length after: `2*cos(1°) < 2`.

So the observer surface reports a change even though the ambient object underwent a rigid transformation. This is a concrete counterexample to treating every projected deformation as intrinsic deformation.

## 6. Transported vs observer-dependent quantities

For the declared fixtures:

- canonical embedding preserves the source coordinates and Euclidean norm;
- one-degree orthogonal rotation preserves Euclidean distance;
- coordinate projection can erase distinctions;
- projected lengths can vary under rigid ambient rotation;
- a finite slice depends on the declared slicing hyperplane and tolerance.

The correct downstream contract is therefore to record the transport/projection operation alongside the observed result rather than promoting the observation to source truth.

## Executable surface

- `dimension-ladder.mjs` — bounded primitives and frozen fixture pack;
- `tests/dimension-ladder.test.mjs` — executable examples, counterexamples, and fail-closed boundary checks.
