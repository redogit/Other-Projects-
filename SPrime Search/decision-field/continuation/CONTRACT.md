# Pass 10 contract — future-safe continuation equivalence

Date: 2026-09-14. This pass makes the future-safe quotient idea executable on a finite deterministic labeled transition system.

## Declared subject

- four physical states;
- state label: whether the current state is state 0;
- action maps are arbitrary total functions on the four states;
- old continuation family: one declared action;
- expanded continuation family: the old action plus one new action;
- obligation: preserve the state label after **every finite action word** in the declared action alphabet.

This is a Moore-machine / labeled-transition equivalence. It is not semantic equivalence of natural-language states and not path-objective equivalence unless the relevant objective monitor has already been included in the state.

## Quotient

Start by grouping states with equal current labels. Repeatedly split a block whenever two states have successors in different current blocks under any declared action. The stable partition is the coarsest quotient preserving labels under every finite action continuation.

Adding an action cannot merge old quotient blocks: it can only preserve or refine them. A split has an explicit finite distinguishing word, found by breadth-first search over state pairs.

## Exhaustive finite assertion

Enumerate every ordered pair of four-state action maps: 256 × 256 = 65,536 systems. For each system compare the quotient under action 0 with the quotient under actions 0 and 1. Check all six unordered state pairs, for 393,216 pair-equivalence queries. An independent C++ implementation repeats the census and witness search.

## Counterexample

Old action `[0,0,0,0]` merges non-target states 1,2,3. Add action `[0,3,1,0]`. States 1 and 2 remain non-target after one use of the new action, but after the word `(1,1)`:

- state 1 follows `1 -> 3 -> 0` and reaches the labeled target;
- state 2 follows `2 -> 1 -> 3` and remains non-target.

Thus the old quotient is not future-safe after the action-set expansion even though the distinguishing consequence is latent for one step.

## Claim ceiling

The stable quotient is exact for the declared deterministic action alphabet and current-state label. New actions, new labels/objectives, side-effect obligations, stochastic transitions, timing, or hidden state change the continuation family and require reopening/recomputing the quotient. This pass does not prove historical novelty or a universal theory of ideas.
