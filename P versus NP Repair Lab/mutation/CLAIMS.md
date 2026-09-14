# CNF mutation: exact scope and proofs

This continuation separates validity, behavioral change, repair distance and representation cost. It is a small executable bridge from the earlier protected-bit repair work to a SAT constraint system. It does not reproduce the historical Independent Set mutation CSV: that CSV lacks its generator and seed in the recovered standalone carrier.

## Problem

Let F be a CNF formula on n Boolean variables, b an explicit n-bit baseline, P a set of protected variable positions and k a radius. A repair is an assignment a satisfying F, agreeing with b on P, and having Hamming distance at most k from b. The optimization task minimizes that distance; equal-distance choices are ordered by the assignment's unsigned integer value. Count all repairs at the minimum distance.

This is assignment repair under declared Boolean semantics. It is not program synthesis, natural-language semantic inference or the Minimum Circuit Size Problem. The unrestricted mathematical problem allows growing n. The executable supports 0 through 20 variables, at most 10,000 clauses and 100,000 literals.

## Decision complexity

The unrestricted repair decision problem is NP-complete, even with no protected positions and b equal to the all-zero assignment.

Membership in NP: an n-bit assignment is a certificate. Scan each clause, compare protected positions and count changed bits. All checks are polynomial in the explicit input size.

Hardness: map a CNF formula F on n variables to (F, 0^n, empty set, n). Every assignment is within distance n of the baseline, so this repair instance is feasible exactly when F is satisfiable. The construction is polynomial. This is a direct corollary of CNF-SAT completeness, not a new complexity separation. The fixed twenty-variable implementation is a bounded experiment, not itself an asymptotic hardness theorem.

External leaf: Stephen Cook, [The P Versus NP Problem](https://www.claymath.org/wp-content/uploads/2022/06/pvsnp.pdf), sections 1–2, printed pages 4–5 (SAT and 3-SAT completeness, polynomial reductions and checking relations), checked September 14, 2026. This primary description supports the standard SAT leaf; the reduction above is explicit project reasoning. No novelty claim is made.

## Why the exact solver is correct

Compile each clause into positive and negative bit masks. A clause is satisfied exactly when at least one positive literal is set or at least one negative literal is unset. Empty clauses remain false and tautologies remain true. Compilation does not enumerate satisfying assignments.

Let E be the editable positions. For each d from zero through min(k, |E|), enumerate every d-element subset of E and flip precisely those baseline bits. Every permitted assignment has a unique such subset. Thus all permitted assignments at smaller distance have been rejected before a successful layer. Scanning the complete successful layer establishes the minimum distance, its exact multiplicity and the smallest unsigned candidate. If all layers fail, infeasibility is established only within the declared radius. If the assignment cap interrupts a layer, the result is `resource_limit` and no optimality or infeasibility is certified.

The solver may visit sum(d=0..k) binomial(|E|, d) assignments, up to 2^|E|. Prepared clauses accelerate repeated checking but do not remove this search cost. Python bit operations also depend on bit width; there is no unit-cost arbitrary-integer assumption in the asymptotic claim.

## A barrier to monotone local repair

For n at least 3, define

F_n = (x_1 OR ... OR x_n) AND the clauses (NOT x_i OR x_j) for every ordered pair i != j.

Its only satisfying assignment is 1^n: any true variable forces every other variable true, while the leading clause excludes all-zero. At a state with r true bits, where 0 < r < n, exactly r(n-r) implication clauses are false. At all-zero exactly the leading clause is false; at all-one none is false.

Consequently every one-bit move from all-zero increases the number of unsatisfied clauses from 1 to n-1. A repair strategy restricted to single-bit moves that never increase this count cannot start, although a repair exists. Its minimum Hamming distance is n. This is a counterexample to that local strategy, even on a directly solvable formula family; it is not a lower bound against arbitrary SAT algorithms.

The executed n=3 case checks all eight assignments. The observed conflict counts in integer order are [1,2,2,2,2,2,2,0]. Protecting any baseline zero position makes this instance infeasible. This contrasts task constraints with a temporary heuristic score: accepting a temporary score increase does not permit violating protected positions.

## Clearing and evidence

The compiled executor retains only clause masks and width. `clear()` drops those mask references and rejects subsequent execution. Caller-owned source and serialized plans remain caller-owned. There is no global plan cache and no promise of a particular garbage-collection time.

`audit.py` compares the compiled solver with an independently written scalar assignment oracle over all 512 subsets of the nine non-tautological clauses on two variables, every baseline, protected mask and radius: 24,576 complete systems. It also uses 128 seeded systems at widths 3–6, boundary cases, the local-search counterexample, invalid-type inputs and a source-inconsistent plan. The manifest records actual execution status; this description alone is not a passing result.
