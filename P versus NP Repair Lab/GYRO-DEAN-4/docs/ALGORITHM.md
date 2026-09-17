# Algorithm Specification

## Core problem

Input: exclusion graph `G=(V,E)`, exact cohort size `q`, dorm capacity `C`, result count `r=4`.

A valid cohort `R` satisfies:

- `|R| = q`;
- `q <= C`;
- `R` is an independent set of `G`.

## Solver principle

The algorithm is exact branch-and-reduce. Gyroscopic carriers attempt to shrink the residual before branching. A carrier may not change the answer. A destructive carrier must carry reconstruction provenance.

## Carrier atlas

1. **Graph** — bitset propagation, q-core, components, modules.
2. **Vertex Cover / LP** — omit `k=n-q`, pressure forcing, half-integral LP.
3. **Dual Frame** — extreme fractional-matching support, odd-cycle defect, tight-frame equations.
4. **SAT / Consensus** — failed literals, no-goods, branch-common consequences.
5. **Factor/SQL** — relational compilation, decomposition, exact verification.
6. **Certified Macaulay/MPCA** — polynomial consequences -> sparse exact linear system -> nullspace-directed attack.

## Gravity

Prefer actions lexicographically by:

1. certified contradiction / solution;
2. irreversible forcing;
3. decomposition;
4. exact rank gain in the current certified nullspace;
5. repair avalanche;
6. heuristic SVD/PCA energy;
7. cost.

## Correctness fallback

If no polynomial carrier progresses, choose a pivot `v` and recurse on:

- `G-v, q`;
- `G-N[v], q-1`.

This is the classical exact independent-set recurrence. It is what guarantees correctness even though a universal polynomial runtime is not proved.
