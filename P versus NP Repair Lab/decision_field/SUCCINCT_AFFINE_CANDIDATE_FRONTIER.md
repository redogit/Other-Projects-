# Succinct Affine Candidate Frontier

Status: `PROVED_ABSTRACT_FINITE_FIELD / PNP_METHOD_RESULT`

## General counting theorem

Let `F_q` be a finite field and `y in F_q^d`. An affine form is

```text
L_{a,c}(y) = a dot y + c,
```

with `a in F_q^d` and `c in F_q`. Exactly `q` choices (`a=0`) are constant, so the number of nonconstant affine forms is

```text
q^(d+1) - q = q * (q^d - 1).
```

Thus exhaustive planning over the entire affine-form space is exponential in `d` for every fixed `q>1`.

Special cases:

```text
F_2: 2^(d+1) - 2
F_5: 5^(d+1) - 5
```

## SAT64-specific admissibility

SAT64 uses an exact parameterization over `F_5`:

```text
x_j = L_j(y)
```

with Boolean domain guards

```text
L_j(y)(L_j(y)-1)=0.
```

An arbitrary affine form over `F_5` is **not** automatically a Boolean decision coordinate. It may take values `2,3,4` on admissible or intermediate states. Therefore "all affine forms" is not merely too large; most forms also lack the required Boolean-branch certificate.

Every original Boolean coordinate supplies a certified candidate partition on the valid solution set:

```text
x_j = 0  versus  x_j = 1,
```

represented in the current chart as `L_j(y)=0` versus `L_j(y)=1`. With `n` original coordinates there are at most `n` such unordered partitions (at most `2n` labelled branch actions).

Additional affine forms may be admitted only when a separate exact certificate establishes the domain property needed by the intended branch.

## Proof of candidate-size bound

Gaussian elimination carries each of the `n` original coordinates to one affine expression in the free chart. Multiple original variables may collapse to the same partition, reducing the count further; they cannot create more than `n` original-coordinate partitions. QED.

## Current decision-field frontier

The smallest defensible SAT64 candidate family is therefore

```text
free-coordinate partitions
UNION
original-coordinate partitions transported through the exact affine chart
UNION
separately certified structural/carrier partitions.
```

It is **not** the full affine dual space.

This preserves two pressures simultaneously:

1. basis-only branching can hide consequential original-coordinate partitions;
2. arbitrary affine expansion would make planning exponential and can admit non-Boolean pseudo-coordinates.

## Remaining cost

A polynomial candidate family does not imply polynomial solving time. At every state we must still charge:

- candidate scoring/planning;
- exact branch application;
- affine reparameterization and guard rebuilding;
- simplification/component discovery;
- certificate checking;
- search-tree states and depth;
- memory/recovery costs.

The live experiment remains a full-cost comparison of free-only, all-original, and consequence-aware selection on recovered SAT64 instances.

## Claim ceiling

This is a candidate-space result. It proves no polynomial SAT bound and no P-versus-NP conclusion. No Hodge evidence is used or transferred.