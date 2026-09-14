# Independent review of CNF repair and implication closure

Date: 2026-09-14. Reviewer: delegated agent `pnp_state_recovery`, in a separate review turn. Review scope: the raw statements, proofs, implementation and pinned evidence listed below. This review did not modify implementation or prior run artifacts.

**Primary verdict: proved as written**, for the mathematical claims in CLAIMS.md and MACRO_REPAIR.md under their explicit scopes. No blocking correctness defect was found. The software evidence remains finite; the unrestricted complexity and restricted polynomiality statements rest on the arguments below, not on extrapolation from tests.

## Claims reconstructed independently

1. **General repair decision.** For a CNF formula F on n variables, explicit n-bit baseline b, protected positions P and nonnegative integer radius k, decide whether some satisfying assignment agrees on P and differs from b in at most k positions. This problem is NP-complete for growing n, already when b is zero and P is empty.
2. **Exact bounded solver.** For validated executable inputs with 0 <= n <= 20, exhaustive Hamming layers find the minimum permitted distance, count all minima and choose the numerically smallest minimum. An interrupted layer returns resource_limit rather than a complete certificate.
3. **Local-descent obstruction.** For n >= 3, a positive clause containing all variables together with every ordered implication has only the all-one model. Non-increasing single-bit conflict descent cannot leave zero.
4. **Restricted closure repair.** With exactly one nonempty positive clause, implications only, zero baseline and protected zeros, the minimum models are exactly the distinct smallest admissible reachability closures from variables in the positive clause. This yields a uniform polynomial algorithm for that class. The current executable inherits n <= 20.

## Dependency and obligation matrix

| Arrow or obligation | Evidence kind | Result |
|---|---|---|
| CNF-SAT is NP-complete | Primary external statement, SAT/3-SAT completeness | Passed |
| F maps to repair(F, zero, empty, n) | Explicit polynomial reduction | Passed |
| Repair assignment is a polynomial-size checkable witness | Internal argument, explicit baseline | Passed |
| Clause masks have exactly the input clause semantics | Boolean identity, implementation inspection | Passed |
| Editable subsets biject permitted assignments at each distance | Internal finite-set argument | Passed |
| Completing first successful layer gives exact multiplicity | Internal counting argument | Passed |
| Resource interruption does not certify complete multiplicity | Code path and cap-sensitive probes | Passed |
| Clique implications force either all-zero or all-one | Internal implication argument | Passed |
| A positive clause excludes zero | Internal argument | Passed |
| Reachability closure is a feasible model if unprotected | Internal graph-closure argument | Passed |
| Every feasible model contains a candidate closure | Internal implication argument | Passed |
| Every cardinality-minimum model equals such a closure | Inclusion plus equal finite cardinality | Passed |
| Original run cardinalities and file provenance agree | Enumerator and manifest inspection | Passed in stated finite scope |
| General SAT, arbitrary baseline, or multiple-positive-clause polynomial repair | Not claimed | Out of scope |
| Native compilation speedup, total optimal execution, or immediate GC | Not claimed | Out of scope |

## Decisive mathematical checks

**NP-completeness.** A repair witness has n bits. Clause scanning, protected-position comparison and Hamming counting are polynomial in the explicit input. From a CNF-SAT instance, retain F and append zero baseline, no locks and radius n. The radius admits every n-bit assignment, giving equivalence in both directions. If variable identifiers are sparse, renumber the variables actually appearing before forming the explicit baseline; this preserves satisfiability and polynomial encoding size. This is a standard corollary, not a separation.

The external source was independently opened on 2026-09-14: Stephen Cook, [The P Versus NP Problem](https://www.claymath.org/wp-content/uploads/2022/06/pvsnp.pdf). Printed page 4 defines polynomial reductions and NP-completeness; page 5 states SAT and 3-SAT completeness and explains checking assignments. The file is an authoritative primary account, not a newly supplied proof of Cook-Levin. Its 3-SAT statement supplies the needed CNF-SAT leaf. No novelty search was attempted or needed.

**Mask semantics.** For an n-bit assignment a, the implementation uses `inverse = a XOR ((1<<n)-1)`. Thus a positive mask intersects a exactly for a true positive literal; a negative mask intersects inverse exactly for a true negative literal. Empty clauses yield two zero masks and remain false. A clause containing a literal and its negation is always satisfied. Duplicate literals do not change acceptance.

**Layer correctness.** Every admissible assignment differs from b on a unique subset of editable positions. The d-subsets enumerate exactly distance d. Protected positions never enter that subset. All smaller layers finish before any larger layer is explored. The entire first successful layer is counted; numerical minimum is taken explicitly, independently of combinations order. Returning optimal after the last allowed assignment is correct if that also finishes the successful layer. If the cap stops before the layer finishes, candidate may be a feasible provisional witness, while distance and count remain uncertified.

**Local obstruction.** Any true variable forces every other variable true. The positive clause rejects the all-zero assignment, leaving exactly all-one. At an intermediate assignment, exactly the implications from a true variable to a false variable fail, hence r(n-r) failures. At zero only the leading clause fails. A single-bit change produces n-1 failures, strictly greater than one precisely when n >= 3. At n=2 the first move ties rather than increases, so the claimed n>=3 restriction matters. At n=1 there is no trap. With any protected baseline zero, the unique all-one model is inadmissible.

**Closure macro.** A reachable set R(v) is closed under implication edges by transitivity of reachability, and contains a positive-clause variable. If it avoids locks it is a feasible assignment. Conversely, every feasible assignment T contains some positive-clause variable v and must contain every vertex reachable from v. Therefore R(v) is admissible and |R(v)| <= |T|. If T is a global cardinality minimum, a strict inclusion would give a smaller feasible assignment, so T=R(v). This proves both optimization and the complete list of minimizers. Distinct starts in the same strongly connected region can yield the same closure; deduplication before counting is necessary and implemented.

The proof applies to arbitrary finite explicit graphs. At most |C| traversals, polynomial graph construction, sorting, bitset storage and comparison keep it polynomial. It does not invoke the twenty-variable cap to establish polynomiality. The parser enforces the narrower promised clause class.

## Boundary and implementation review

- n=0: the general executor accepts the empty conjunction at assignment zero and rejects an empty clause. Radius and protected mask can only be zero. The macro has no valid n=0 input because its positive clause must be nonempty; rejection is appropriate.
- Radius zero, all-protected inputs, infeasible radii, multiple optimal assignments and unsigned tie ordering are handled.
- Invalid Boolean/float integers are rejected where integer values are required.
- The general solver's default cap is 2^20; a smaller cap yields resource_limit where unfinished. The macro exposes neither an arbitrary baseline nor a radius; both remain outside its API contract.
- Self-implications, duplicate implication edges and duplicate positive literals preserve the macro argument. Its set operations normalize these harmless repetitions.
- A second positive clause, negative unit clause, empty clause or unsupported mixed clause is rejected by the macro rather than silently generalized.
- Executor construction rederives masks from the plan's embedded source and compares the full canonical plan. Source edits, mask edits, version changes, hash changes and numeric type changes were rejected.
- This is **embedded-source consistency**. Without a caller-supplied expected source/hash, loading a self-consistent older plan cannot detect that a separate external source changed. No authenticity or live-source freshness follows from the checksum.
- clear() drops executor-owned masks and rejects future accepts/solve calls. Caller-owned source/plan objects remain retained by their callers.

One minor wording issue remains in the reviewed repair.py module docstring: “linear in the input literal count” should include clause count, since empty clauses still cost work. The safe bound is linear in clause-plus-literal representation size, with the stated integer-width and serialization costs. This does not invalidate the mathematical claims or observed results.

## Evidence checks and supplemental execution

All input and output hashes in run-001 and macro-001 matched the reviewed files. Original enumerator cardinalities are correct:
- General: 512 clause families times 4 baselines times 4 protected masks times 3 radii = 24,576 systems.
- Macro: sum over n=1,2,3 of 2^(n(n-1)) (2^n-1) 2^n = 3,634 systems.

Independent supplemental probes ran with Python 3.12.14, using `python3 -B -` and fresh scalar Boolean evaluation rather than importing the author's oracle. They created no output artifacts and did not rerun or overwrite the original audits:
- 4,338 cap-sensitive comparisons across eight explicitly selected boundary/constraint families at n=0..3; 470 resource-limit outcomes checked for conservative status and valid provisional candidates.
- Five independent plan corruption/type controls.
- Every assignment of the local-obstruction family at n=1..8.
- 256 sampled macro systems at n=1..7, seed 92317, including duplicate positive literals, duplicate edges and self-loops; compared with complete scalar assignment enumeration.
- Five unsupported macro-class controls.
- Clique macro results at every n=1..20, including protected-zero infeasibility.

All passed. These supplemental counts describe this reviewer execution, not additions to either original run manifest. They are finite counterprobes, not substitutes for the proofs.

## Reviewed SHA-256 identities

| File | SHA-256 |
|---|---|
| CLAIMS.md | c3f9497de59a354879763fdb72cca6e34e421d94e5c6520be5b98db3a772e1a1 |
| repair.py | 5914a2ee46f5f479643460043808697f476fa1943f5661f87b7f0291173eeeee |
| audit.py | 1fce0cc5f4121609061ac3401f87ca9378098a82a55d7480dab2fd16751b0082 |
| contract.json | 77274652837241c99d1008fae7a8bff02910c52d671962189c720451798a2dd7 |
| evidence/run-001/manifest.json | 806588cab8433450ef17b31d83101865e16c45e057c97b3bdd5eadcd903eb044 |
| evidence/run-001/results.json | fbaceb09387bdc904496c64e7eaf3d254108ec01257a78679ea5103248099d7a |
| evidence/run-001/trap.plan.json | 3212d3e23d8bbd1831ab50e5ceb09cccd5996a231b72ba959f415fd832bf8dc1 |
| MACRO_REPAIR.md | 7e029113d7ce137dc672fe1ccf8ce1ddcd9995037c8d08a9834825b76abbf633 |
| macro_repair.py | 9f8f19d277d5ca13308809d55396985a57857164c2c54b5ea20aad3f2a1abff7 |
| audit_macro.py | 792ed26e393a1b74cfed5b5f37ada812de620a6a415d7cba8bef41e9265ea4c5 |
| evidence/macro-001/manifest.json | bcf2a8196c3130d9c757a13abe6e29ed52a3a3172d5eb336401ff8f3e2ec4728 |
| evidence/macro-001/results.json | 3ba78a2b91f075f05492123ec34cf6ad208e9c7d111a533166dddc124db8d6a2 |

## Remaining gap and strongest safe conclusion

The general decision boundary, exact bounded solver and local-strategy counterexample are justified. The dependency-closure repair is an exact uniform polynomial method for the stated restricted class and provides a valid way past that particular heuristic trap. No argument here supplies unrestricted polynomial SAT repair, a growing unrestricted Partial-Hard constructor, a general circuit lower bound, or a P-versus-NP resolution.

The next useful investigation would change one restriction at a time with a new exact contract; it should not promote the special case merely because the bounded audits passed.

## Review addendum — 2026-09-14, documentation correction and current runs

The compilation-cost wording is now corrected. I compared the exact original source preserved at history/repair_pre_doc_fix.py with current repair.py. The only text difference replaces the module-docstring sentence about literal count with clause-plus-literal input size and integer-width/serialization costs. Python ASTs are identical after removing the initial module docstrings; no executable statement changed.

The preserved source matches the original reviewed repair.py hash. Original run-001 and macro-001 manifests and result artifacts retain their recorded hashes. Fresh run-002 and macro-002 manifests report completed execution with exit status zero, and every listed current input/output hash matches its file. General results match run-001 after excluding timing_ns; macro results match macro-001 exactly. The trap plan is byte-identical. This addendum adds no new mathematical proof claim or broad test run; the original review and hash table above remain unchanged.

| Current or preserved file | SHA-256 |
|---|---|
| history/repair_pre_doc_fix.py | 5914a2ee46f5f479643460043808697f476fa1943f5661f87b7f0291173eeeee |
| repair.py | 983022f7566c0a9b0d8858feec08e5b31181142d058eb2b326443f3bc1a8df07 |
| evidence/run-002/manifest.json | 5d175aebfdfb457ebf1d22a7ffd85220882d58a682e7d60563870fa1b33b4413 |
| evidence/run-002/results.json | dd3505dc7450f0768f2b7257d935e95b9bc5fdb104edc04ed530460a49f34d5f |
| evidence/run-002/trap.plan.json | 3212d3e23d8bbd1831ab50e5ceb09cccd5996a231b72ba959f415fd832bf8dc1 |
| evidence/macro-002/manifest.json | d69e0f5f54e28d598d02cd325ddca475ccc08e645aa4ec983c1bf72d78ff0aee |
| evidence/macro-002/results.json | 3ba78a2b91f075f05492123ec34cf6ad208e9c7d111a533166dddc124db8d6a2 |

The original verdict stands. The external-source freshness boundary still applies: consistency with an embedded source is not a comparison against a separately changed source.
