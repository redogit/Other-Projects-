# Context Discovery, Pass 02 — frozen run contract

Recorded before the Pass 02 execution on 2026-09-13. This is an assistant-authored test design, not an independently preregistered human study.

## Aim and boundary
Continue Pass 01 systemically: expression/use -> contextual distinctions -> admissible actions -> diagnostic question -> observation -> consequence -> retained evidence/remainder. Culture, human purpose and observed software behavior are different subjects. No cultural corpus is trained on, rescored, or overwritten. New technical contexts are purposively selected, not a representative or independently sampled benchmark.

## Exact finite experiment
Reuse the 25 stipulated worlds (r,h in 0..4), four binary (early,prominent) actions and payoff e*(r-1)+v*(1-h)-k*[e!=v]. Scan k=0..4 with mixed actions feasible/infeasible. Preserve ties. Initial observation is either r-h or no observation. Query pool: r>=t and h>=t for t=1..4, each with unit diagnostic cost. These are exact noiseless observations whose permission and costs are given, not inferred.

Compare:
- fixed-order questioning until a common optimum exists;
- exact minimax questioning until a common optimum exists;
- exact minimax full-world identification;
- no diagnostic questions (must return unresolved when no shared optimum exists).

A stop is valid only if the intersection of optimal feasible action sets across all still-admitted worlds is nonempty. A stable common action need not identify the world. A result is minimum diagnostic cost only within this declared question pool, objective and model. It does not minimize total utility loss or count questioning as free.

Every query strictly partitions a finite possible-world set. The Bellman recurrence is cost(question)+maximum(child costs), minimized over informative permitted questions. This permits a finite induction certificate, not a universal efficient-planning theorem. Unknown outcomes, invalid observations, empty worlds and malformed models must fail explicitly. Test a pairwise-overlap/empty-global-intersection counterexample; duplicating a world's record must not alter a worst-case decision.

## Executable technical episodes
Local temporary SQLite database, journal mode WAL, serially interleaved operations on multiple connections: a writer commits while a read transaction remains open; the same read retains its snapshot; a reopened read sees the commit; two simultaneous write transactions do not become valid merely because reads/writes separated.

zlib: encode a 1,024-byte payload with a specified 1,024-byte dictionary. Matching dictionary reconstructs exactly; missing/wrong dictionaries fail. Charge dictionary bytes when not already available. No compression superiority threshold is assumed.

No production service, real user database, concurrent stress race, crash durability or network filesystem is tested. Record library versions. The official WAL documentation's version-specific defect notice is retained as a limitation, not tested as a bug-fix certification.

## Evidence and promotion
Re-run Pass 01 from its preserved package and compare its scientific outputs. Re-run Pass 02 twice and require exact scientific JSON equality. Preserve input hashes before/after, runtime/environment, failures and negative controls. Use inherited SP1024-1 only for a separate byte-roundtrip check. Source documentation is evidence of a stated contract; local executions are observations of these selected paths, not proof of every implementation behavior.

Publication destination: redogit/Other-Projects-/Context Discovery/. Append new work; leave archive data, other projects and workflows unchanged. Publish source paraphrases, code and bounded results only; do not export private Library context. No scientific, cultural, language or runtime-authority promotion follows automatically.
