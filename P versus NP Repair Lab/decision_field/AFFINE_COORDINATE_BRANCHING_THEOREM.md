# Affine Coordinate Branching Theorem

Status: `PROVED_ABSTRACT_F2_CALIBRATION / PNP_METHOD_RESULT`

## Exact statement

Let `y=(y_1,...,y_d) in {0,1}^d`, and let

```text
ell(y) = c XOR XOR_{i in S} y_i
```

be a nonconstant affine Boolean form over `F_2`, with support `S` of size `k >= 1`.
Assume the admissible domain is the **full Boolean cube** and the protected binary decision is exactly `d(y)=ell(y)`.

1. If observations are restricted to individual basis-coordinate queries `y_i`, every deterministic exact decision tree has worst-case depth at least `k`; querying all support coordinates attains depth `k`.
2. If the lawful observation set additionally permits the affine predicate `ell(y)`, the decision has depth `1`.

Thus basis-coordinate-only querying is not invariant under affine reparameterization even in this simplest exact model.

## Proof

The upper bound is immediate. For the lower bound, if a leaf transcript leaves some `y_j`, `j in S`, unqueried, choose two full-cube assignments consistent with the transcript and differing only in `y_j`. They have opposite values of `ell`, so the leaf cannot label both correctly. Therefore every worst-case path queries every support coordinate. Directly querying `ell` returns the decision bit in one step. QED.

## Relation to SAT64 — calibration only

SAT64's recovered exact algebra route is different:

```text
A x = 1 over F_5,
x in {0,1}^n,
x_j = L_j(y),
L_j(y)(L_j(y)-1)=0 on valid solutions.
```

The surviving free coordinates are Boolean, but `L_j` is an affine form over `F_5`, and the guard system restricts the admissible subset of the free Boolean cube. Consequently the `k`-query lower bound above **does not automatically apply** to SAT64: guard relations can correlate the free coordinates and make a supported affine form decidable from fewer basis queries.

What does transfer is the research question:

> an original Boolean coordinate eliminated from the chosen basis can still define a lawful partition `L_j(y)=0` versus `L_j(y)=1` on the valid SAT64 solution domain.

The reported SAT64 experiments provide bounded evidence that retaining such original-coordinate partitions can matter. That evidence is independent of the `F_2` theorem above.

## What this proves

- an exact mechanism in the full-cube `F_2` calibration;
- a counterexample to treating basis-coordinate simplicity as coordinate-invariant in general.

## What it does not prove

- the same depth lower bound on a constrained `F_5` SAT64 guard domain;
- that all-original branching is uniformly better;
- a bound on maintenance/simplification/planning cost;
- polynomial-time SAT;
- P = NP or P != NP;
- any Hodge statement.

The SAT64 continuation therefore needs its own `F_5`/guard-domain theorems and exact experiments rather than inheriting the `F_2` depth result.