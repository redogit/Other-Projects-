# P versus NP: finite selector repair, v6.2

**Result:** the historical n=4, g=6 score-cost advantage reproduces, but a neighboring n=4, g=5 case disproves universal all-ones selector optimality under that same score metric. This is finite circuit-class and certificate research; P versus NP remains open.

## Exact contract

The complete grid is n∈{2,3,4}, g∈{0,1,2,3,4,5,6}. A circuit is an acyclic NAND DAG with at most g gates, arbitrary fanout, repeated gate inputs allowed, and a single output selected from a variable or computed gate. Only variables are initial signals. Internal or output constants are not free: constant one first becomes available at two gates, zero at three. Table bit x is f(x), with variable j read from bit j of x. Arithmetic and certificates are exact integers/Boolean values.

Semantic-state generation keeps the sorted set of computed signals available at each gate depth. Duplicate-function gates can be removed and their outgoing wires replaced by the earlier equivalent signal. Future extensions depend only on the available signal set, so quotienting by that set preserves the functions reachable with at most g gates. This argument permits the constructor's state merging; it is not a complexity-class separation.

The frozen policies are generic single-coordinate greedy and paired greedy for t=2^w−1, one representative for each w=1..n. A paired action imposes the same bit at x and x xor t. Both policy families use the same class, bitset index and observation-preserving input-permutation reduction. Ties minimize `(survivor count, coordinate, bit)`. The all-ones representative is fixed from n, with no circuit-class search used to choose it. Running the other policies is charged experimental comparison work, not a free selector oracle.

These are representative comparisons, not all translations or all possible policies. Lexicographic tie-breaking is not assumed equivariant across different translations of the same weight. A zero-survivor partial table certifies that **no circuit in the declared bounded class matches it**. A nonzero exhausted route is recorded as unsuccessful, never credited as a cheaper successful certificate.

## Executed evidence

Final run: [suite-004/results.json](runs/suite-004/results.json), with [manifest](runs/suite-004/manifest.json). Native C++ compilation completed before any case ran. The full grid completed under a 120-second outer wall cap, a 120-second per-process CPU cap, 1 GiB per-process address-space cap and one allowed core. Python 3.12.14; g++ 13.3.0; `-std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror`. These are invocation-enforced limits; running the Python wrapper alone does not install the hard limits.

| n | g=0 | g=1 | g=2 | g=3 | g=4 | g=5 | g=6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2 | 2 | 5 | 9 | 13 | 15 | 16 | 16 |
| 3 | 3 | 9 | 22 | 48 | 91 | 139 | 192 |
| 4 | 4 | 14 | 45 | 143 | 436 | 1243 | 3310 |

There are **21 cases, 84 routes and 209 greedy steps**. An independent syntactic gate-sequence enumerator, without semantic-state merging, exactly matches every n≤3 class. Every emitted route is independently checked by C++ scalar scoring of every available action and stepwise table filtering. Input-permutation closure and initial pair-orbit counts are also checked.

A separately implemented Python replay imports no producer code. It verifies the final 21 case files and their hashes, complete greedy choices and survival paths, stopping status, observation counts, stabilizer/orbit sizes and named score/application/popcount charges. It passed all 84 routes and 209 steps: [audit-001/results.json](runs/audit-001/results.json), [manifest](runs/audit-001/manifest.json). Its class checks include base cases and monotonicity, but do not independently prove n=4 class completeness.

Ten exhausted non-eliminating routes are retained. At n=2, g≥5 the class is all 16 Boolean functions, so no inconsistent partial table exists. Other failed paired paths are policy outcomes; no broader nonexistence claim is inferred from them.

## Historical calibration retained

At n=4, g=6 the exact class contains 3,310 functions and the historical paths and charges all match:

| Policy | Observations | Candidate scores | Score AND words | Score popcount calls | Application AND words | Survivor popcount calls |
|---|---:|---:|---:|---:|---:|---:|
| generic_sym | 5 | 56 | 2912 | 2912 | 260 | 520 |
| paired_t1 | 10 | 30 | 3120 | 1560 | 520 | 520 |
| paired_t3 | 6 | 30 | 3120 | 1560 | 312 | 312 |
| paired_t7 | 6 | 22 | 2288 | 1144 | 312 | 312 |
| paired_t15 | 8 | 20 | 2080 | 1040 | 416 | 416 |

- `generic_sym`: 3310 → 1371 → 417 → 90 → 1 → 0.
- `paired_t1`: 3310 → 790 → 160 → 45 → 10 → 0.
- `paired_t3`: 3310 → 582 → 32 → 0.
- `paired_t7`: 3310 → 500 → 21 → 0.
- `paired_t15`: 3310 → 548 → 78 → 7 → 0.

The old `wordops` counter is retained precisely as **score AND-word operations**. It does not include score popcounts, application, stabilizer work or construction. The historical 2,080 versus 2,912 advantage is preserved under that declared metric, along with the eight-versus-five observation tradeoff.

## Counterexample and necessary repair

At n=4, g=5, the class contains 1,243 functions:

| Frozen paired policy | Initial action orbits | Orbit representatives by step | Score AND words | Observations | Survivor path |
|---|---:|---|---:|---:|---|
| t=15, all ones | 3 | 3, 3, 4, 3 | 1,040 | 8 | 1243 → 166 → 15 → 1 → 0 |
| t=7 | 4 | 4, 3, 4 | 880 | 6 | 1243 → 182 → 14 → 0 |

The t=7 picks are `(8,0), (9,1), (0,1)`; t=15 uses `(1,0), (3,1), (2,0), (0,0)`. Each pick denotes equal observations at x and x xor t. Independent scalar replay confirms both certificates.

Thus **minimum initial pair-orbit count does not imply minimum complete greedy score cost**, even within this small neighboring gate-budget comparison. The all-ones rule uses fewer initial orbits but one extra step and more total scored representatives. No universal full-cost or runtime dominance is claimed: for example, t=7 uses 876 stabilizer coordinate checks versus 712 for t=15 in this case. This is a metric-specific counterexample plus an observation-count improvement.

The required repair is to preserve “all ones minimizes the initial orbit count” separately from the now-refuted extension to full-route score optimality. Neither initial shrink nor initial orbit count is a sufficient certificate of end-to-end optimality. The successful g=6 result remains a bounded achievement. A future selector must state its prediction target and include the cost of selecting, preparing, constructing and verifying; the present run does not train or validate a new universal selector.

## Full process costs and their boundaries

Actual one-time native build: **2.414789 s**. At n=4, g=6: class construction **2.499463 s**; index construction **0.037926 ms**; permutation preparation **0.104004 ms**; common symmetry checks **4.334176 ms**. The independent syntactic class verifier is explicitly not run for n=4; its near-zero timer is not evidence of a free verification.

| n=4, g=6 policy | Instrumented planning ms | Scalar verification ms |
|---|---:|---:|
| generic_sym | 0.262708 | 0.129662 |
| paired_t1 | 0.218933 | 0.082402 |
| paired_t3 | 0.208187 | 0.073528 |
| paired_t7 | 0.148729 | 0.089052 |
| paired_t15 | 0.211602 | 0.078015 |

Class construction dominates these planning measurements. The n=4, g=6 index retains **13,312 mask-payload bytes**; sizeof/capacity accounting totals **14,120 bytes**, excluding allocator metadata. Its process peak RSS is **53,956 KiB**, including construction and process baseline, not just the retained index. The class frontier reaches 888,101 semantic states at depth six. The JSON records construction candidate/duplicate/state counts and each route's score AND/popcount, application AND/store, survivor popcount, stabilizer and orbit counters separately.

Elapsed times are actual single instrumented executions, not calibrated microbenchmarks. Map-based instrumentation, allocation, comparisons, hashing and scheduling affect them. Named primitive counts are a cost ledger, not every source operation or native machine instruction. Per-process elapsed time includes startup and serialization; phase timers do not. Compiler version-probe and wrapper/runner overhead are visible only in the enclosing run time. Compilation is shared once across this suite; this does not establish a universal amortization rule.

## Corrections and provenance

Source baseline: `redogit/conscience64@e6256b3746076eb02a4bf3c32eedb6f57666169b`, file `research/cross-carrier/2026-09-12/v2.2/sql/symmetry_aware_constructor_v5.cpp`; reviewed local source SHA-256 `2d67e936d861e4a3df1500662dee8f0fce2450c45c17ab132d82d623d8c4eb2d`. Destination base: `redogit/Other-Projects-@3c09ab6c07a854f8cc3feb585822cc7c5fd8dcde`. These source/destination anchors are declared provenance. The isolated execution directory has no Git checkout; runner manifests correctly record its commit as unavailable and dirty state as true. Input-file hashes pin the executed revisions; no fictitious execution commit is supplied.

| Run | Preserved source / wrapper / contract | Interpretation |
|---|---|---|
| suite-001 | `constructor.cpp`, `run_suite.py`, `contract.json` | 13 cases; original calibration reproduced; compiler emitted two warnings. |
| suite-002 | `constructor_v6.cpp`, `run_v6.py`, `contract_v6.json` | Complete 21-case grid; warnings fixed; selector counterexample found. |
| suite-003 | `constructor_v6_1.cpp`, `run_v6_1.py`, `contract_v6_1.json` | Independent audit found a scalar-read accounting overcharge from short-circuiting. Eager evaluation fixes the charge's meaning without changing any class, choice, survivor path or score cost. |
| suite-004 | `constructor_v6_1.cpp`, `run_v6_2.py`, `contract_v6_2.json` | Final: wrapper distinguishes requested-case completion from full standard-grid coverage, preventing misleading metadata for future subset runs. |

The first warning concerned compressed indentation; the other concerned the fixed-array std::sort instantiation. Explicit bounded insertion plus clearer control flow removes both under `-Werror`. The historical source unconditionally included both constant outputs; the new class builder admits them only at their actual gate budgets. This changes shallow classes, while leaving the historical g=6 calibration intact. Earlier inputs and aggregate run outputs remain frozen for review.

No P-versus-NP separation, asymptotic circuit lower bound, formula-to-DAG transfer, native instruction optimum, universal selector optimum or measured deployment speedup follows from this work.

## Reproduction

From this directory, set `AUDIT_SKILL_DIR` to the installed computation-audit skill directory. Use a fresh output directory:

```bash
python3 "$AUDIT_SKILL_DIR/scripts/run_experiment.py" \
  --root . --contract contract_v6_2.json \
  --input constructor_v6_1.cpp --input run_v6_2.py --input contract_v6_2.json \
  --output runs/reproduction-001 --result runs/reproduction-001/results.json \
  --timeout 120 --max-output-bytes 1048576 \
  --max-memory-bytes 1073741824 --max-cpu-seconds 120 \
  --max-cores 1 --max-threads 1 -- \
  python3 run_v6_2.py --output runs/reproduction-001
python3 "$AUDIT_SKILL_DIR/scripts/validate_manifest.py" \
  runs/reproduction-001/manifest.json --root .
```

`audit_replay.py --results <suite>/results.json --output <fresh-audit>/results.json` replays the full grid. Its recorded audit contract declares the script, aggregate results and all 21 case files as inputs. No dependencies are installed and no source-project services are called.
