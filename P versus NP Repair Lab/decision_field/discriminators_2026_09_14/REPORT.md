# Decision-field discriminator checkpoint — 2026-09-14

Status: `EXECUTED_BOUNDED / SEPARATE_CONCLUSIONS / P_VS_NP_OPEN`

## Experiment A — certified symmetry before population construction

The selector is obtained from the **succinct circuit language / query symmetry**, not from an already enumerated survivor population. The bounded NAND language and all-ones paired query are invariant under input-variable permutations, yielding a checkable `S_n` action before class construction.

Held-out `n=4, g=5` result:

- exact function class preserved: **1243 = 1243**;
- candidate NAND attempts: **301,979 → 17,346** (17.41× reduction);
- generated semantic states (excluding initial): **87,880 → 4,345** (20.23× reduction);
- current Python wall-time ratio, quotient/control: **2.40×**.

**Conclusion:** this is a genuine construction-volume discriminator in the bounded experiment, but **not** a runtime-dominance result. Symmetry canonicalization still costs enough to make the Python quotient slower in this run.

## Experiment B — consequence-aware SAT64 branching

The SAT64 source package was recovered from the owner's Library and verified as a readable ZIP. It is **not published by this checkpoint**. The frozen selector contract hash is `d44b3813aa337a2beb0fe55aec999bd26bd56cc9aa722ebe7b6933e002aa6bec`; implementation hash is `1dae1f3a79fae8bdbe5f09c5d62ec8f1331f002613cfcc0e5dd76dd142dc039b`.

Fresh bounded results:

| Case | Selector | Status | Exec states | Depth | Exec row ops | Planning probes | Planning row ops | Wall |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| compiler_0 | occurrence | UNSAT | 7 | 2 | 1,128 | 0 | 0 | 0.167s |
| compiler_0 | consequence | UNSAT | 7 | 2 | 1,128 | 24 | 3,692 | 0.767s |
| balanced_1 | occurrence | SAT | 6 | 5 | 6,100 | 0 | 0 | 3.474s |
| balanced_1 | consequence | SAT | 6 | 4 | 6,946 | 32 | 38,307 | 24.474s |
| balanced_5 | occurrence | UNSAT | 9 | 3 | 12,115 | 0 | 0 | 5.635s |
| balanced_5 | consequence | RESOURCE TIMEOUT | — | — | — | — | — | >10s external cap |

Each completed node solve was checked by the package's separately implemented feedback checker. The resource timeout is **not** a SAT/UNSAT result.

**Conclusion:** this first consequence-aware rule is **not a genuine total-cost discriminator**. It can reduce depth while merely moving or increasing cost into planning.

## Evidence boundaries

- Experiment A attacks the dominant population-construction **volume** in a finite bounded circuit class; it does not establish asymptotic runtime improvement.
- Experiment B is a separate SAT64 route. It neither proves nor disproves the circuit result.
- The owner-held SAT64 archives remain private/unpublished; only hashes, contracts, scripts, and bounded result summaries are committed here.
- `P versus NP` remains open.
- `METHOD_ONLY != EVIDENCE_TRANSFER`; Hodge and unrelated projects do not supply mathematical evidence here.
