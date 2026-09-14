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

## Update-first review — September 14, 2026

The fresh review checked open work as well as main. [SPrime D2 PR #4](https://github.com/redogit/Other-Projects-/pull/4), based on the same repository main, had not been included in this checkpoint's active context. Its predecessor is `614f6823a6bbe6cbff64470ed53df646252a1f09`. D2 adds XOR to NAND, reaches all 256 three-input behaviors in at most five operations, and supplies compact witnesses for all four retained repairs. This changes the representation boundary; it does not invalidate the NAND-only D1 result or improve a NAND-only gate budget by definition.

Source inspection found that D2 ignored reserved instruction bit 7, breaking byte identity across the float carrier. The repair is maintained with the D2 work in PR #4. A fresh two-pass native census preserved every published numerical summary and all four repair witnesses. A separate grammar/codec audit checked all 65,792 payloads of length one or two, 31,455 canonical rank occurrences, and 10,260 high-bit mutation occurrences. The corrected shared parser rejects the alias. No D2 implementation is copied into this lab.

The review also recovered owner-held `SAT64_LINEAR_ECS_2026-09-13.md` and `SAT64_GUARD_FEEDBACK_2026-09-13.md`. Their reported executions were read, not rerun here. They preserve complementary field-elimination and matching routes, describe exact Boolean-guard feedback, and give a compiler-family fixed-point limitation. Their adaptive panel reports that branching on dependent original coordinates can help, with a SAT counterexample to uniform improvement. The relevant next SAT64 comparison is a consequence-aware selector against the cheap occurrence rule, charging all planning, recomputation and checking costs. Its source packages and certificates must be recovered before execution. This is a distinct route from the circuit Partial-Hard target above.

The S′ transform-wave design similarly separates candidate generation from admission and uses explicit depth, beam and total-candidate caps. Its distributed v1 notes add state and policy components; those packages were not executed or imported. They provide no reason to equate representation novelty with semantic validity.

Orbit's current pointer now includes Wave 33 synchronization. Master 2.0 / Plan 2.2 / Implementation 2.6 remain the named current roles. Companion remains support-only, and the ACCESS3 R1 clean-exit repair remains a candidate without production admission. Knowledge Garden PR #2 has a separate reversible adjective sidecar; its source-reported results are not this lab's results. Conscience64 main advanced by one game-description commit after the pinned historical source; the inspected diff changes only `play/mmo-world/` files.

The proposed arbitrary-baseline implication extension has therefore been deferred behind the witnessed D2 repair and recovery of the more directly relevant SAT64 frontier. It remains an unimplemented candidate, with no new minimum-repair or P-versus-NP claim. Historical evidence and previous failed routes are preserved.
