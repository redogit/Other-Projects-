# Succinct Affine Candidate Frontier

Status: `PROVED_ABSTRACT / PNP_METHOD_RESULT`

## Statement

Let `y in {0,1}^d` be the surviving free-coordinate vector after exact affine elimination over GF(2), and consider nonconstant affine Boolean predicates

```text
ell_{a,c}(y) = c XOR (a dot y),
```

with `a in {0,1}^d \ {0}` and `c in {0,1}`.

There are exactly

```text
2 * (2^d - 1) = 2^(d+1) - 2
```

nonconstant affine predicates on the free basis.

Therefore exhaustive planning over all affine cuts is exponential in the number `d` of free coordinates.

By contrast, if the original SAT/EO3 instance has `n` original Boolean coordinates, exact elimination represents each original coordinate by at most one affine form

```text
x_j = L_j(y).
```

Hence the family of branch predicates inherited from original coordinates has cardinality at most `n` (or at most `2n` if both displayed literals `L_j=0` and `L_j=1` are counted as separate actions). The candidate-family size is polynomial in the input coordinate count even though individual forms may have large support.

## Proof

An affine Boolean predicate is determined uniquely by its coefficient vector `a` and constant bit `c`. There are `2^d` coefficient vectors and two constants. The two choices with `a=0` are constant functions, so removing them leaves `2^(d+1)-2` nonconstant predicates.

Gaussian elimination expresses every original coordinate `x_j` as one affine form in the chosen free basis. There are only `n` original coordinates, so there are at most `n` such forms, irrespective of support size. QED.

## Consequence for the SAT64 decision field

The earlier affine-coordinate branching theorem showed that basis-only branching can hide a sharp lawful partition. This theorem supplies the opposite pressure: admitting every possible affine partition makes planning exponential before search begins.

The smallest defensible candidate family is therefore currently:

```text
free basis coordinates
UNION
nonconstant original-coordinate affine forms
UNION
separately certified structural carrier predicates
```

not the full affine dual space.

This family is representation-aware but succinctly inherited from the input/elimination map.

## Remaining cost

Polynomial candidate count does **not** imply polynomial total solving time. For each state we must still charge:

- scoring/planning over candidates;
- applying an affine branch condition;
- rebuilding the exact parameterization/guards;
- simplification and component detection;
- certificate verification;
- number and depth of visited states.

The unresolved question is whether a consequence-aware score on this succinct family gives enough tree reduction to repay those costs on a growing, independently checked family.

## Claim ceiling

This is a candidate-space theorem only. It proves no polynomial SAT bound and no P-versus-NP result. No Hodge evidence is used or transferred.