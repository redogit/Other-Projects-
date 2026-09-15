# BOM Fast Execution + Decision Questions — Design

Date: 2026-09-14
Status: approved for implementation
Scope: `SPrime Search/decision-field/bom/fast/`

## Goal

Make bounded BOM search materially faster while preserving exact final answers, and make clarification questions consequence-driven rather than conversationally arbitrary.

The fast layer is an accelerator and question planner. It is **not** an authority for validity, equivalence, dominance, or claim promotion.

## Two-lane architecture

### Fast lane

```text
obligation
  -> compiled structural index
  -> proof-safe constraint propagation / branch-and-bound
  -> incremental candidate/frontier state
  -> consequence-ranked question
  -> changed obligation / candidate mask
  -> repeat
```

### Evidence lane

```text
surviving candidate / assembly
  -> existing exact verifier
  -> reference-source locks
  -> exhaustive/native audit where declared
  -> evidence-qualified promotion
```

The fast lane may reorder work. It may not change the accepted answer set.

## Exact compiled index

Each `PartSpec` receives a deterministic integer slot. The index precomputes:

- capability-provide bit masks;
- capability-require bit masks;
- cost tuples in declared dimension order;
- exact port-compatibility adjacency;
- construction dependency edges;
- stable source/version identifiers.

An indexed candidate subset is an integer bit mask. A subset is rejected proof-safely when a required operational capability is absent, a construction dependency has no provider, a declared bound is violated, or a proven lower-bound cost is already dominated by a verified frontier point.

No learned model may create these rejection certificates.

## Incremental state

`IncrementalSearchState` stores:

- obligation fingerprint;
- active part mask;
- proven exclusions with reason/certificate;
- verified assemblies;
- current exact Pareto frontier;
- unresolved distinctions;
- cache provenance (`fresh`, `exact_cache`, `symbolic`, `not_checked`).

When one obligation distinction changes, only caches whose dependency fingerprints include that distinction are invalidated.

## Question engine

A candidate question is admitted only when its answer partitions currently viable verified/candidate assemblies in a way that can alter a declared consequence.

Default scoring is non-probabilistic and minimax:

1. minimize the largest surviving ambiguity bucket;
2. maximize guaranteed candidate elimination;
3. maximize guaranteed Pareto-frontier change potential;
4. minimize question acquisition cost;
5. stable lexical id tie-break.

A question with zero consequential discrimination is not asked.

Question evidence records must include:

- question id/text;
- finite answer domain;
- candidate partition induced by every answer;
- current frontier ids;
- worst-case survivor count;
- guaranteed eliminations;
- whether each answer changes the frontier;
- assumptions and unresolved remainder.

## Explanation surface

Every retained/rejected result supports structured `WHY` records:

- why included;
- why rejected and by what exact certificate;
- why dominated;
- which cost dimensions prevent dominance;
- why a question is consequential;
- which answer changes the frontier;
- which evidence is fresh, cached, symbolic, or not rerun.

## Native kernel

`native_search.cpp` implements the hot exact capability/dependency subset kernel for bounded benchmark families using bit masks. Python remains the readable reference/orchestration implementation.

Native output is promoted only after exact agreement with Python on oracle-sized families. On larger families the native result remains bounded computational evidence; no universal complexity claim follows.

## Training contract

Training is permitted only for **ordering heuristics**:

- which candidate branch to expand first;
- which mutation/substitution to try first;
- tie-breaking among already-admissible consequential questions.

Training is forbidden from deciding:

- validity;
- obligation satisfaction;
- semantic equivalence;
- dominance;
- proof-safe pruning;
- evidence promotion.

### Teacher and dataset

Ground-truth labels come from exact bounded oracle runs. Synthetic task families vary:

- capability coverage structure;
- fused vs split parts;
- dependency depth;
- port compatibility;
- cost vectors;
- hidden invalid candidates;
- question-answer partitions.

Every generated instance stores its seed, family id, exact oracle result, and feature vector.

### Split discipline

Split by **task family**, not by individual rows, to prevent near-duplicate leakage:

- train: 60% of families;
- validation: 20%;
- test: 20%.

A deterministic family hash assigns the split.

### Model

Use a deterministic integer pairwise perceptron/ranker with no external ML dependency. Features are integer-valued structural statistics only. Training order, epochs, and tie-breaking are fixed and recorded.

### Promotion gate

A trained ranker is admitted only if:

1. every held-out task reaches the same exact final answer/frontier as the oracle;
2. the ranker never supplies a pruning certificate;
3. held-out median or total expansion count improves versus stable lexical ordering, or the model remains disabled;
4. adversarial reversed/noisy labels are detected by validation degradation and are not promoted;
5. model weights, dataset manifest, split assignment, and metrics are reproducible byte-for-byte across two runs.

If the learned ordering hurts performance on held-out tasks, fallback is exact deterministic ordering.

## Benchmark contract

Use deterministic benchmark tiers:

- `oracle-small`: <= 16 parts; exhaustive Python subset oracle is mandatory;
- `oracle-medium`: <= 20 parts with structured constraints; Python indexed result must match exhaustive oracle;
- `scale-large`: 32, 48, and 64 parts; compare indexed Python and native exact kernels under explicit resource bounds; no claim that all possible arbitrary BOM instances at those sizes are solved efficiently.

Record candidate counts, expansions, exact-prune counts, runtime, and result hash. Runtime is environment-dependent; candidate/expansion counts are the primary stable comparison.

## Claim ceiling

This layer may establish bounded speedups, exact agreement, and better bounded question ordering on declared task families. It does not establish globally optimal architecture search, universal sample efficiency, universal question value, or a general complexity-class result.
