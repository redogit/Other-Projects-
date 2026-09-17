# Extended Proof Report

The Decision Field / GYRO-DEAN thread closed or sharpened the following bounded claims while keeping the universal complexity question open.

## Closed claims

- DEAN-4 is NP-complete in the scalable pairwise-exclusion family.
- Four distinct outputs reduce to polynomially many calls to an exact existence solver because four is fixed.
- The exact include/exclude fallback is correct and terminating.
- Compatibility q-core deletion and exclusion-isolated inclusion are safe.
- Independent Set / Vertex Cover duality and pressure forcing are exact.
- Pressure repair is monotone under forced omissions.
- Component/join factorization is exact.
- Exact context signatures and Pareto dominance are proved; exact context frontiers can still be exponential.
- Connected non-bipartite regular cores provide a repair plateau for several local methods.
- Gyroscopic closure is sound when every carrier is exact/certificate-backed.
- Frontier-mass contraction and polynomial-event progress are sufficient conditional polynomial-time theorems.
- Maximal linear PCA characterizes all exact linear invariants of the true solution set; linear PCA is not universally terminal.
- Certified Macaulay linearization gives a computable exact-rank/nullity carrier.
- Lifted MPCA curvature, semantic Jacobian, block exposure, Graph-Hilbert bridge and submodular rank-gain laws were derived.
- Fractional dual support frames yield odd-cycle defect and tight-factorization equations.
- Multiple target-tight frames can yield exact low-nullity or inconsistency certificates.

## Claims falsified as universal routes

- local degree/pressure repair always progresses;
- one fixed polynomial frontier always exists;
- ordinary linear rank always compresses a bad cut;
- original-variable PCA always collapses hard instances;
- unary/pairwise semantic facts always progress;
- static lift-until-complete is always polynomial;
- universal small boundary graph representatives always exist.

## Executable evidence from the reference package

- hand-picked exact tests passed;
- exhaustive comparison with brute force passed every labeled graph through five vertices and every positive target q: **5,405 graph/target cases**;
- Petersen q=4 returns four valid cohorts;
- G20 q=8 returns four valid cohorts;
- G20 q=9 returns no cohort, matching `alpha(G20)=8`.

## Boundary

No universal polynomial bound on gyro depth, semantic mass, frame entropy, certified nullity or operator progress is proved. `P ?= NP` remains OPEN.
