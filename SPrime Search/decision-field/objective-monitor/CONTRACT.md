# Pass 11 computation contract — sticky objective monitor reopening

## Research decision

Test the other reopening axis left by Pass 10: with the **physical state space and action family fixed**, can adding a path-dependent obligation make the old physical-state carrier insufficient?

## Exact computational surrogate

- Physical states: exactly four, `{0,1,2,3}`.
- Actions: exactly two deterministic total maps on those states.
- Action family: all `256 × 256 = 65,536` ordered map pairs.
- Initial conditions: all four physical states for every action pair, giving `262,144` plant/initial cases.
- New obligation memory: one sticky Boolean monitor `M`, where `M=1` iff physical state `1` has been visited at or before the current step.
- Initial monitor: `M = (initial_state == 1)`.
- Update: after an action reaches state `s'`, `M' = M OR (s' == 1)`.

For each fixed plant and fixed initial physical state, exhaust the reachable product graph `(physical_state, M)`. A **monitor collision** exists when both `(s,0)` and `(s,1)` are reachable for the same physical state `s`.

A collision is an exact witness that physical state alone cannot determine the expanded obligation state for that fixed initial condition. The audit also records a shortest-radius certificate: two action words from the same initial state ending at the same physical state with different monitor values, minimizing the maximum word length.

## Arithmetic and conventions

All arithmetic, maps, states, monitors, and BFS distances are exact integers. No floating point, randomness, external packages, or network access are used.

## PASS / failure meaning

PASS requires:

1. independent Python and C++17 exhaustive censuses to agree exactly;
2. two native executions to be byte-identical;
3. the committed bounded counts and witness to reproduce;
4. source hashes in the verification record to match the checked-out computation sources.

A disagreement is an implementation/evidence failure until diagnosed. It is not automatically a mathematical counterexample.

## Claim ceiling

This experiment can establish exact facts only for deterministic two-action four-state plants with the declared sticky monitor. It does **not** establish a universal theorem about memory, sufficient statistics, POMDPs, human cognition, arbitrary temporal logic, stochastic control, minimum automata in general, or semantic compression.

The experiment does not say the physical states cease to exist or that the monitor creates new physical reality. It tests whether the **decision field required by an expanded obligation** must retain a distinction not recoverable from current physical state alone.
