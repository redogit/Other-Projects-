# Original-Coordinate Partition Invariance

Status: `PROVED_ABSTRACT_F5 / PNP_METHOD_RESULT`

## Setup

Let a SAT64 residual be represented over `F_5` by an affine chart

```text
x = A y + b,
```

with admissible parameter set `D_y` defined by the transported Boolean guards. Let a second exact chart be related by an invertible affine change

```text
y = M z + d,
```

with `M` invertible over `F_5`; its admissible set `D_z` maps bijectively to `D_y`.

For every original Boolean coordinate `x_j`, write

```text
x_j = L_j(y) = L'_j(z)
```

where `L'_j(z)=L_j(Mz+d)`.

## Theorem

The unordered branch partition induced by the original coordinate,

```text
P_j = { valid states with x_j=0 } | { valid states with x_j=1 },
```

is invariant under the exact affine chart change. The displayed coefficient support of `L_j`, however, is not invariant.

## Proof

The coordinate change is a bijection between admissible parameterizations of the same residual states. For corresponding `y=Mz+d`,

```text
L'_j(z)=L_j(y)=x_j.
```

Hence a residual state belongs to the `x_j=0` or `x_j=1` side independently of which affine chart displays it. The two charts encode the same unordered partition of the underlying valid states.

Coefficient support is chart-dependent. For example over any field of characteristic not forcing cancellation, the form `L(y)=y_1` under the invertible change `y_1=z_1+z_2`, `y_2=z_2` becomes `L'(z)=z_1+z_2`, changing support size from one to two. QED.

## Research consequence

A planner may safely regard **original-coordinate partitions** as chart-stable candidate identities while treating these as chart-local metadata only:

- support size of the displayed affine expression;
- coefficient pattern;
- which free variables occur;
- basis-coordinate index.

Therefore a consequence-aware selector should prefer features attached to the induced partition or residual consequence, such as exact component separation or certified simplification, rather than assuming a short affine expression is intrinsically better.

## Decision-field interpretation

This gives SAT64 a cleaner decision field:

```text
underlying state partition = stable object
current affine expression = carrier / coordinate chart
```

Changing chart may change the carrier without changing the decision represented.

## Claim ceiling

This theorem concerns exact affine reparameterizations of a fixed residual problem. It supplies no runtime bound, no polynomial search-tree bound, and no P-versus-NP result. No Hodge evidence is imported.