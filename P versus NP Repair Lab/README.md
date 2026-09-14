# P versus NP Repair Lab

Continue the main P versus NP line through exact repair, semantic mutations and fully charged construction. The main goal remains open. This checkpoint fixes executable defects, preserves earlier achievements and adds a counterexample plus a tractable repair mechanism.

## What changed

| Work | Result | Boundary |
| --- | --- | --- |
| Symmetry-aware Partial-Hard construction | Reproduced the four-input, six-gate result; found that the all-ones selector loses on score cost at five gates | Exact finite NAND DAG classes; construction still enumerates the class |
| Semantic query plans | Fixed history-dependent type rejection; bounded retained plans and added explicit clearing | Existing three-input SPrime / D1 semantics |
| General CNF assignment repair | Exact protected-bit minimum repair, with explicit resource-limit outcomes | Exponential Hamming-layer enumeration within twenty variables |
| Implication-block repair | Exact minimum repair by reachable closures | One positive clause plus implications; all-zero baseline and protected zeros |

The existing [SPrime cache repair](../SPrime%20Search/compact/CACHE_REPAIR_2026-09-14.md) also repairs stale publication verification while keeping earlier evidence records. Its two complete D1 reruns preserved all scientific outputs. The new work follows the destination in `PROJECT_ROUTING.md`; historical conscience64 source records remain intact.

## Main-line finding

At four inputs and gate budget five, the generated NAND class contains 1,243 functions. Translation `t=7` eliminates that class with 880 score AND-word operations and six observations; all-ones `t=15` uses 1,040 and eight. This refutes universal optimality of the all-ones selector for that complete-route score metric. It does not refute its theorem about the number of initial action orbits, or its earlier six-gate result.

The six-gate calibration still contains 3,310 functions. Its selected paired route still costs 2,080 score AND-word operations versus the generic route's 2,912. Full construction and compilation costs are now recorded alongside these counts. The five-gate alternative does more work in some other counters, so neither result is a claim of dominance on every cost or full application latency. See [full-cost findings](full_cost/NOTES.md) and its frozen run evidence.

## A semantic repair that escapes a local trap

One-bit conflict descent can stop even when repair is possible. Our three-variable witness has one unsatisfied clause at `000`, two after any one-bit change, and zero at `111`. Its only satisfying assignment is `111`, three changes away. A rule forbidding temporary conflict increases cannot move.

The next step repairs the implicated dependency block together. For exactly one positive clause and implication edges, every feasible model contains the reachable closure of at least one variable in the positive clause. Choosing a smallest allowed closure gives an exact minimum repair. This is a polynomial graph method for that restricted class. Arbitrary CNF repair retains the SAT search obligation.

Read [definitions and exact solver proof](mutation/CLAIMS.md), [closure repair proof](mutation/MACRO_REPAIR.md) and [independent review](mutation/INDEPENDENT_REVIEW.md). Compilation cost includes clauses and literals, including empty clauses, plus integer-width and serialization costs. A compiled plan is checked against its embedded source; external source freshness requires comparing the current source separately.

## Run

Python 3.12 and GCC 13.3 were used for this checkpoint. Python components use the standard library; the full-cost experiment compiles its own C++20 executable before any case runs. No package installation or source-project service is required.

From this directory:

```sh
python3 mutation/audit.py --output /tmp/cnf-repair-audit
python3 mutation/audit_macro.py --output /tmp/implication-repair-audit
```

Use a new output directory when preserving a run. The checked-in manifests contain the bounded execution commands and input/output hashes. The full-cost notes document the separately compiled route suite and immutable revision inputs. Current mutation evidence is in `mutation/evidence/run-002` and `mutation/evidence/macro-002`; the earlier runs and their original source snapshot remain available.

For your own small CNF, import `compile_plan` and `Executor` from `mutation/repair.py`, compile the explicit `variables` / `clauses` object, then call `solve(baseline, protected, radius)`. Positive literal `j` means variable j; negative `-j` means its negation. Variable 1 is the least significant assignment bit. Call `clear()` to release an executor's masks. Caller-owned source and plan objects remain under the caller's control.

## Evidence and continuation

- All 21 dimension/budget cases in the full-cost suite: n=2..4 and gates=0..6, with exact class checks on the smaller domain and scalar verification of route choices and survival paths.
- 24,576 complete two-variable CNF repair systems, 128 seeded systems and four minimum-width boundary cases.
- 3,634 complete implication-repair systems through three variables.
- Separate proof review and supplemental boundary probes; these are independent encodings/review passes, not independent human replication.

The live target, corrected assumptions and next discriminating action are in [CURRENT.md](CURRENT.md). Finite circuit classes, syntactic words, Boolean behaviors, assignment repairs, observation queries and natural-language meaning are different objects. Coordinate conventions must be translated before moving a labeled witness between this lab and SPrime.
