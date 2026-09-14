# Current research checkpoint — PNP-REPAIR-2026-09-14

## Target retained

The main constructive target is nonlocal, growing Partial-Hard / Range Avoidance without explicitly enumerating the circuit population, all labelings or all survivors. A P-versus-NP resolution still requires a uniform polynomial algorithm for an NP-complete problem or the appropriate rigorous separation. Finite success and a failed heuristic establish neither.

Base implementation repository: `redogit/Other-Projects-` at `3c09ab6c07a854f8cc3feb585822cc7c5fd8dcde`. Historical main-line source: `redogit/conscience64` at `e6256b3746076eb02a4bf3c32eedb6f57666169b`, especially `research/pnp/2026-09-12/` and `research/cross-carrier/2026-09-12/v2.2/sql/`.

## Three executed routes

1. **Construct and falsify the selector.** Reproduce v5 under generated-only NAND constants, charge compilation/construction/index/planning/verification and change the circuit budget. The five-gate counterexample closes universal complete-route score optimality of the fixed all-ones selector. Its initial-orbit theorem and six-gate finite win survive.
2. **Repair semantic query execution.** Reproduce the cache-dependent bool/float bypass and stale verifier. Validate before memoization, bound retained plans, clear explicitly and use a versioned current publication record. Existing finite semantics and scientific outputs survive.
3. **Test mutation and derive a structural repair.** General CNF repair is exact within its cap. The implication-clique family defeats non-increasing one-bit conflict moves. Reachability closures then solve the declared one-positive-clause implication class exactly, with a uniform special-case argument and separate finite checks.

## Corrections that must travel with the work

| Earlier candidate or shortcut | Current rule |
| --- | --- |
| Formula-complexity lower bounds proposed for DAG search | Formula and DAG costs differ. Historical 11→10 and 12→8 witnesses forbid using a formula lower bound to prune smaller DAG circuits. A constructed formula is only a one-sided circuit upper-bound witness. |
| Transform → quotient → target treated as cheaper than exact direct optimum | The staged construction is itself a direct circuit in the same basis; its cost cannot beat that target's exact optimum. Compare discovery/verification costs separately. |
| Arbitrary semantic mutation treated as cost-preserving | Behavioral equality, allowed change and cost preservation need separate evidence. Input-variable permutation symmetry is the certified action used here; arbitrary observation relabeling or input negation is not inherited. |
| General finite-group notation in the historical HSP quotient note | This continuation uses finite abelian groups, specifically Boolean translation groups. Nonabelian coset orientation/normality is outside this result. |
| Score-mask counts described as full execution cost | Keep compilation, circuit-class construction, index build, symmetry work, application, verification and memory separate. No unweighted sum of unlike counters is called a total optimum. |
| Truth-table width confused with input-variable count | n input variables require 2^n truth-table rows; pointwise linear work in rows need not be polynomial in n. |

These dated corrections preserve the earlier records as historical evidence. They do not silently promote their proposed routes or delete failed attempts. Knowledge Decay remains an active method: retain failed implications, exact recovery handles and achievements so future context reduction cannot turn a bounded result into a universal one.

## Next discriminating action

The circuit population construction remains the dominant measured cost and the main unresolved dependency. The next admissible candidate must obtain a useful symmetry or semantic boundary from succinct input with a checkable certificate, before constructing the entire circuit class. Freeze its choice rule before evaluating it on unseen dimension/budget cases; charge discovery and certification, and retain generic and all-ones controls. A predictor based on the already enumerated survivor class has not removed that obligation.

For semantic mutations, the useful certified branch is reachability closure. Extending it to arbitrary baselines or multiple positive requirements changes the optimization problem; do not silently reuse its proof. A new extension needs its own derivation and counterprobe before entering the dispatcher. No such broader extension is claimed in this checkpoint.

No long-running research process is left active. No change here merges a PR, deploys a site, invokes a companion or changes another project's research authority.
