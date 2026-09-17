# Evidence Boundary

## Proved / exact within the design

- DEAN-4 is NP-complete in the unbounded family.
- Four distinct outputs reduce to polynomially many calls to an exact existence solver because four is fixed.
- Independent-set include/exclude recurrence and the reference exact fallback are correct and terminating.
- Compatibility q-core pruning and exclusion-isolated inclusion are existence-preserving.
- Component and join factorization are exact.
- Independent Set <-> Vertex Cover complement duality, pressure forcing `deg(v)>k`, and the elementary O(k^2) residual kernel are exact.
- Pressure closure is monotone.
- Connected non-bipartite regular cores can simultaneously stall several local repair systems.
- Exact context signatures, Pareto dominance, the exponential matching frontier, and the disjointness-rank barrier are proved.
- Gyroscopic closure is sound under its carrier contracts.
- Frontier-mass contraction and polynomial semantic-event progress are sufficient polynomial-time theorems, conditional on their stated progress hypotheses.
- Maximal linear PCA exactly characterizes all linear invariants of the true solution set; the empty graph proves linear PCA is not a universal terminal measure.
- Certified Macaulay linearization is sound; logarithmic certified nullity over a polynomial dictionary is polynomially terminal.
- Lifted MPCA, curvature sandwich, stabilization, semantic Jacobian and block-curvature identities are proved as analysis theorems over the true solution set.
- The graph-Hilbert bridge is exact.
- Fractional-dual support frames give exact odd-cycle defect and tight-factorization bounds.
- Multi-frame inconsistency and low-nullity affine stacks are exact certificates.
- Candidate-action rank gain is monotone submodular and admits the stated greedy rank-cover bound.

## Executable evidence

- Hand-picked exact tests include C6, K4, empty-graph four-result enumeration, and the 20-vertex cubic calibration core.
- Exhaustive comparison with brute force passed every labeled graph through five vertices and every positive target q: 5,405 graph/target cases.
- Petersen and G20 calibration files preserve counterexamples / flat cores used to falsify weaker universal claims.

## Analysis-only objects

The true solution-set covariance, lifted Hilbert dimensions, and semantic Jacobian characterize semantic structure exactly, but they are generally not directly computable without already resolving the solution set. The operational solver therefore relies only on certified equations generated from the input and proved consequences. Numerical SVD/PCA may steer; exact rank/certificates alone may change logical state.

## Open

No proof is claimed that all instances reach logarithmic nullity or a polynomial carrier after polynomially many gyro actions. In particular, no universal theorem is proved for constant-fraction semantic dissipation, logarithmic gyroscopic depth, polynomial frame entropy, or a polynomial semantic-event basis with guaranteed progress. Any sufficiently strong universal result would settle `P` versus `NP`, which remains open.
