# Context Discovery — Systemic Pass 02

Date: September 13, 2026. Status: EXECUTED_BOUNDED_RESEARCH. Implementation home: `redogit/Other-Projects-/Context Discovery/`.

## What changed
The first pass proposed recovering context before combining apparently conflicting advice. This pass implements a finite diagnostic planner and executes selected software boundary cases. It does not infer cultural meaning from a utility table or claim a general theory of idea formation.

The operational sequence is:

`source/use -> context -> protected outcome -> admissible actions -> discriminating question -> observation -> consequence -> evidence/remainder`

There are three distinct paths: inherited cultural use descriptions remain interpretation-bearing source records; a stipulated finite decision model permits exact planning; real software probes test selected mechanisms. None inherits another path's authority. The 91-record archive and six prior context notes remain unchanged. No new cultural accession, user profiling, model training or blanket rights clearance occurred.

## Run
Python 3.11+ and its standard library:

```sh
python "Context Discovery/systemic.py" --out context-output
```

The program checks its assertions and emits `results.json`, `policies.json`, `traces.json` and `software.json`. The checked-in `evidence/` summaries are observations, not a requirement to obtain identical compressed sizes on every library version. Use `python "Context Discovery/verify.py"` to verify publication hashes. `CONTRACT.md` records the design before execution; it is not third-party preregistration.

## 1. Find a useful question, not every missing fact
The 25 worlds and four actions from Pass 01 are reused with five implementation costs and two feasibility regimes. Starting knowledge is either absent or the old difference r-h. Eight permitted binary threshold questions have unit cost. Inputs and payoff values are assumed, not learned from sayings.

Across 100 initial decision problems, all 500 world/policy traces choose an optimal feasible action. In 81 problems no question is needed. The exact planner is cheaper than a fixed-order, early-stopping questioner in 14 problems and cheaper than full-world identification in 80. Maximum modeled diagnostic cost is three. These are overlapping constructed cases, not independent samples or an accuracy estimate for real-world language.

For the fully uncertain, zero-extra-cost, uncoupled case, worst-case questions are two for choosing an optimum, five for the fixed-order baseline, and six for identifying the exact world. The comparison uses the same question pool and unit costs.

In the problematic old-summary class r=h, one question suffices: is r at least one? If not, late/prominent is optimal. Otherwise early/unobtrusive is optimal for every remaining world. At r=h=1 all actions tie; the solver preserves the set of optima before choosing a representative. The exact world is not needed. See `question_example.json`.

### Why the result is exact in this model
For possible worlds W, stop only when the intersection of their acceptable-action sets is nonempty. Otherwise choose the informative permitted question minimizing:

`question cost + max(minimum child cost)`.

Every branch has fewer possible worlds, giving a finite induction argument for minimum worst-case diagnostic cost. If no question can produce a valid terminal policy, return unresolved. This is established finite decision-tree dynamic programming, not a novel general solver or an efficiency claim for arbitrary problems.

A separately written non-memoized query-tree oracle agreed on all 1,024 tested tiny model/cost combinations. Negative controls reject missing answers, contradictions, invalid worlds and costs. Pairwise-overlapping acceptable-action sets with empty global intersection are correctly unresolved. Duplicate world records do not supply extra votes.

Diagnostic cost is not free: these results minimize questioning subject to the exact-action requirement. They do not prove that asking is worth its cost, optimize net utility after questioning, handle noise, or infer the correct feasible set.

## 2. Context can require a different operation, not more repetition
SQL01 kept a read transaction open while another connection committed an update. Three repeated reads returned zero. SQL02 ended that read and opened a new one: it returned one. The missing step was renewing the snapshot, not repeating a query. These are serially interleaved local operations, not concurrent stress tests. Source: [SQLite isolation](https://www.sqlite.org/isolation.html).

SQL03 supplied the counterexample: a second write transaction was rejected with SQLITE_BUSY. Read/write separation does not remove the writer/writer boundary. Source: [SQLite WAL](https://www.sqlite.org/wal.html).

Runtime: SQLite 3.46.1. Current official WAL documentation describes a version-specific WAL-reset race fixed in 3.51.3 and selected backports. These single-thread temporary-database checks do not exercise or certify that fix, general crash safety or production readiness. No real user database was opened.

## 3. A small carrier can depend on large context
ZIP01 reconstructed a 1,024-byte payload from 24 compressed bytes using a specified 1,024-byte dictionary. Sending both costs 1,048 bytes before additional framing; the independent zlib record was 1,035 bytes. ZIP02 and ZIP03 reject missing and wrong dictionaries. The apparent saving is conditional on the correct dictionary already being available. Source: [zlib dictionary contract](https://www.zlib.net/manual.html).

This supports a candidate engineering record, not a learned discovery:

`ContextDependency = (required object/version, authorized acquisition operation, acquisition cost, validation, failure action)`.

For a snapshot, acquire a new permitted read transaction. For a dictionary, supply the exact required bytes. These are different mechanisms with a comparable dependency question, not evidence of one universal physical process.

## 4. Keep the investigation open without inflating its evidence
Feature-flag deployment versus release and RabbitMQ delivery versus completed side effects are source-reviewed candidates in `SOURCES.json`; neither service was executed. They remain next tests, not additional successes.

The ePiC and Proverbs Run in Pairs publisher abstracts remain relevant comparisons for contextual meaning and translation assessment. Neither benchmark was run. The cultural-use branch still requires original-language, situational and community-informed review. Comfort, welcome, memory and art are not reduced to the toy reward.

## Reproduction and lineage
The original Pass 01 script was rerun on the pinned archive; all four scientific JSON outputs matched. Both Pass 02 executions produced the same four scientific JSON files. A separate inherited SP1024-1 check preserves output bytes; that is custody, not semantic validation. Full run records, outputs and the previous package are provided in the downloadable research bundle; no private Library material is published here.

A single author selected cases, constructed targets and wrote both solvers. The tree oracle is a separate implementation path, not independent human replication. Two local systems are purposive examples, not broad empirical generalization. `evidence/RUN_MANIFEST.json` and `evidence/INTEGRATION.json` preserve scope and limits. The manifest verifier is package-local, not the official Mathbox validator or a proof assistant.

**Next gate:** freeze independently selected engineering episodes, targets, permitted observations and acquisition costs before running the planner. Compare question-first, fixed-order and no-question strategies; retain inappropriate suggestions, abstentions, cost and failures. Natural-language-to-model extraction is currently manual and unvalidated.
