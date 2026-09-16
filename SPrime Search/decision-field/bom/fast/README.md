# Pass 09 — Fast BOM Execution + Decision Questions

This layer accelerates the existing decision-field BOM search without replacing its correctness authority.

## What changed

The fast layer adds:

- deterministic compiled bit-mask indexes for parts, capabilities, costs, dependencies, and ports;
- proof-safe incremental candidate filtering with explicit certificates;
- exact MRV branch-and-bound search for harder dependency-heavy fields;
- native C++17 kernels for hot exact search paths;
- a Z3 symbolic verifier for bounded exact minimum-cover/dependency checks;
- consequence-ranked questions with answer-specific Pareto recomputation;
- structured `WHY` records;
- a deterministic integer pairwise ranker trained only to order search work;
- family-separated train/validation/test evaluation and corrupted-label negative control;
- independent Wolfram and SciSpace grounding records.

## Authority boundary

The learned ranker may choose which branch or candidate is examined first. It may **not** decide validity, obligation satisfaction, equivalence, dominance, pruning certificates, or evidence promotion.

If the learned ordering disagrees with an exact solver, the learned ordering loses; if it fails to improve held-out expansion count, it is disabled.

## Verification group

The bounded Pass 09 evidence uses independent mechanisms:

1. exhaustive Python oracle on small/medium cases;
2. Python MRV branch-and-bound;
3. native C++ exact kernels;
4. Z3 symbolic optimization;
5. a frozen Wolfram Language exhaustive check for the 12-part benchmark.

Disagreement is a hard failure.

## Training result

The frozen 60-family dataset splits by family hash into 36 train, 8 validation, and 16 test families. The deterministic integer pairwise perceptron learned weights `[1,1,1,1]` in 8 epochs.

On held-out test families, exact results remained identical while search expansions fell from **4,370 to 858**. A reversed-label control expanded from **1,822 to 3,568** on validation and was correctly not promoted.

On the structurally different dependency-trap family, the exact answer remained unchanged and total MRV expansions across 12/16/20/32 parts fell from **2,810 to 2,576**. The 64-part dependency trap remains intentionally hard: 50,336 lexical MRV expansions versus 50,292 with learned ordering.

## Questions

Questions are ranked only when at least one answer can alter the current viable set or Pareto frontier. The current two-assembly field surfaces concrete questions about one-bit memory, sensor availability, and a two-component cap. Zero-value questions are omitted.

## Evidence

- `evidence/SUMMARY.json` — bounded benchmark and question results.
- `evidence/TRAINING.json` — dataset split, model, held-out metrics, and corrupted-label control.
- `evidence/VERIFICATION.json` — source hashes and cross-verifier results.
- `evidence/WOLFRAM_CHECK.json` — independent exact Wolfram check.
- `RESEARCH_GROUNDING.md` — SciSpace literature grounding and non-claims.

Claim ceiling: **bounded exact BOM acceleration and question ordering on declared finite families only**. No global architecture optimum, universal learned heuristic, general sensor/memory interchangeability, or complexity-class conclusion is claimed.
