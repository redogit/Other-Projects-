# Affine Coordinate Branching Theorem

Status: `PROVED_ABSTRACT / PNP_METHOD_RESULT`

## Statement

Let `y=(y_1,...,y_d) in {0,1}^d`, and let

```text
ell(y) = c XOR XOR_{i in S} y_i
```

be a nonconstant affine Boolean form with support `S` of size `k >= 1`.

Suppose the protected binary decision is exactly `d(y)=ell(y)`.

1. If the only allowed observations are individual basis-coordinate queries `y_i`, every deterministic exact decision tree has worst-case depth at least `k`; querying all support coordinates attains depth `k`.
2. If the lawful observation/action set additionally permits the affine predicate `ell(y)`, the decision has depth `1`.

Therefore a coordinate-only branching policy is not invariant under exact affine reparameterization.

## Proof

The upper bound `k` for basis-coordinate queries is immediate: query every coordinate in `S` and XOR the answers with `c`.

For the lower bound, consider any deterministic decision tree using only individual `y_i` queries. If a root-to-leaf transcript leaves some `y_j`, `j in S`, unqueried, choose two assignments consistent with the transcript and identical on all queried coordinates and all other unqueried coordinates, differing only in `y_j`. Because `j` appears with coefficient `1` in `ell`, the two assignments have opposite values of `ell`. Thus the leaf cannot correctly label both assignments. Every correct worst-case path must therefore query every coordinate in `S`, so its depth is at least `k`.

If `ell` itself is a lawful query/predicate, its returned bit is exactly `d(y)`, so one query suffices.

QED.

## SAT64 interpretation

After exact affine elimination, an original Boolean variable can remain represented as

```text
x_j = ell_j(y)
```

in the surviving free coordinates `y`.

Branching on the original variable `x_j=b` is then the affine cut

```text
ell_j(y)=b.
```

The theorem shows structurally why restricting candidate branches to free basis coordinates can exclude a much sharper lawful partition. This matches the previously observed SAT64 phenomenon that dependent original coordinates can be useful branch variables.

## What this does not prove

- It does not show that all-original branching is always faster.
- It does not bound the cost of maintaining or simplifying the affine cut.
- It does not imply a polynomial-time SAT algorithm.
- It does not resolve P versus NP.
- It imports no Hodge evidence.

The next live discriminator is to compare candidate-set benefit against full planning, affine-update, simplification, verification, and search-tree costs on recovered SAT64 instances.