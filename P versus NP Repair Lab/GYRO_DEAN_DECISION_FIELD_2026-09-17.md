# GYRO-DEAN as a Parameterized Decision Field — 2026-09-17

**Status:** exact algorithmic architecture / open complexity research. `P ?= NP` remains OPEN.

This document re-expresses the current DEAN/P-vs-NP thread through the canonical Decision Field interface.

## Field

For residual graph `G=(V,E)`, target cohort size `q`, dorm capacity `C`, and desired result count `r=4`:

```text
X = exact residual candidate/cohort state
O = obligation: return r distinct valid size-q cohorts
D = consequential distinctions under exclusions/capacity/goal
R = exclusion, compatibility, cover, LP, frame, clause, factor and algebra relations
F = admitted exact transforms/operators
E = proof/evidence/provenance ledger
G_goal = four certified cohorts or a certified impossibility/fewer-than-four result
U = unresolved hard core
```

## Exact outer result

For each returned cohort `R_i`:

```text
|R_i| = q
R_i contains no exclusion edge
q <= C
R_i != R_j for i != j
```

The scalable pairwise-exclusion family is NP-complete through the established Independent-Set reduction using a disjoint `K4`. This is a calibration/theorem about the problem family, not a `P=NP` result.

## Operators

### Graph carrier

```text
FILTER_EXCLUDED
COMPATIBILITY_Q_CORE
COMPONENT_SPLIT
COCOMPONENT_SPLIT
MODULE_TWIN_REPAIR
COLOR_BOUND
EXACT_BRANCH
```

### Cover carrier

For `m=|V|`, `ell=m-q`:

```text
ROTATE_TO_VERTEX_COVER
PRESSURE_FORCE: deg(v) > ell => omit v
CROWN / KERNEL REPAIR
```

### LP carrier

```text
VERTEX_COVER_LP
NEMHAUSER_TROTTER
ABOVE_LP_PARAMETER
FRACTIONAL_MATCHING_DUAL
```

### Dual-frame carrier

Extreme half-integral fractional-perfect-matching support decomposes into matching edges plus odd cycles.

For a target-tight frame:

```text
edge {u,v}: x_u + x_v = 1
odd cycle P=C_(2r+1): sum_{v in P} x_v = r
```

Multiple frames may add independent equalities or produce a sparse linear contradiction.

### SAT / repair carrier

```text
CLAUSE_PROPAGATION
FAILED_LITERAL
CONSENSUS_LEARNING
NO_GOOD_LEARNING
ONE_POSITIVE_CLAUSE_IMPLICATION_CLOSURE
```

The one-positive-clause + implications repair class is a proved polynomial fast path. Multiple positive clauses are NP-hard even without implications by Hitting Set reduction, so they rotate back to generic SAT/cover unless more structure is proved.

### SQL/factor carrier

```text
BITSET_COMPILATION
FACTOR_DECOMPOSITION
VARIABLE_ELIMINATION
CONTEXT_FRONTIER
```

### Certified algebra / MPCA carrier

Maintain a polynomial-size feature dictionary and exact proved relations:

```text
A y = b
```

with certified nullity:

```text
d = |M| - rank(A)
M_affine = 2^d
```

New exact relation batch `B y = c`, with `N` spanning `ker(A)`, gains:

```text
g = rank(B N)
d' = d - g
M_affine' = M_affine / 2^g
```

PCA/SVD is steering only; exact rank is proof.

## Maximal repair loop

```text
function Normalize(DF):
    repeat until fixed point:
        apply cardinality/capacity rules
        apply graph q-core/components/modules
        apply cover pressure/kernel rules
        apply LP/NT/frame consequences
        apply SAT/consensus/no-good consequences
        row-reduce exact algebra relations
        extract degree falls into cheaper carriers
        canonicalize and memoize
    return DF
```

Every repair causes all other carriers to be recomputed.

## Gyroscopic scheduler

```text
while not terminal:
    DF = Normalize(DF)

    candidates = GenerateAdmittedOperators(DF)
    probes = ProbeAll(candidates)

    best = lexicographic max by:
        terminal certificate
        irreversible exact fact
        factorization
        exact rank/nullity gain
        kernel/width contraction
        heuristic steering gain / cost

    if best gives exact progress:
        DF = Apply(best)
        DF = LearnAndRotate(DF)
        continue

    children = ExactBranch(DF)
    solve each normalized child
    combine exactly
```

## Repair pressure theorem used by the field

Let omission budget be `ell` and:

```text
rho(v) = deg(v) - ell
```

If `rho(v)>0`, `v` is forced into the cover/forced out of the cohort.

After forcing `v` out:

```text
rho'(u) = rho(u) + 1 - 1[(u,v) in E]
```

Thus pressure does not decrease for any surviving vertex, giving a monotone fixed-point closure for this rule.

## Context equivalence

Across cut `A | B`, partial independent sets `X,Y subset A` are future-equivalent when:

```text
|X| = |Y|
N(X) intersect B = N(Y) intersect B
```

For existence, `(k1,F1)` dominates `(k2,F2)` if:

```text
k1 >= k2
F1 subseteq F2
```

Exact context frontiers may still be exponential; this is retained as a barrier/counterexample, not hidden.

## Frontier-mass sufficient theorem

If a positive integer mass `M(S)` for unresolved canonical states satisfies polynomial initial mass and every expansion has exact normalized children `T_i` with:

```text
1 + sum_i M(T_i) <= M(S)
```

then the total number of state expansions is polynomial.

No universal mass satisfying this for all NP instances is currently proved.

## Four-result reconstruction

The expensive inner solver may remain an existence solver. After one `q`-cohort `S_1` is found, a new cohort distinct from prior `S_1...S_j` exists iff for some choice `v_i in S_i`, deleting `{v_1...v_j}` still permits a `q`-cohort. For fixed four results this uses at most `q + q^2 + q^3` existence calls.

## Decision Field interpretation

The P-vs-NP obligation is therefore:

```text
one field
+ a typed set of exact functions
+ a scheduler/repair closure
-> desired certified result
```

The open theorem is whether a uniformly polynomial function-generation/selection/repair strategy exists for every NP-complete residual without hiding exponential cost in state space, relation space, feature space, planning, verification, or reconstruction.

## Claim ceiling

```text
EXACT_ALGORITHM_ARCHITECTURE != P_EQUALS_NP_PROOF
FINITE_COUNTEREXAMPLE != ASYMPTOTIC_LOWER_BOUND
HEURISTIC_GAIN != CERTIFIED_PROGRESS
SHARED_DECISION_FIELD != SHARED_DOMAIN_MECHANISM
```
