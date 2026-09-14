# Pass 08 contract — partial observation, belief, and obligation state

Date: 2026-09-14. This is a bounded deterministic finite-state experiment. It is not a human-subject model and not a stochastic POMDP solver.

## Objects kept separate

- physical plant state;
- observation symbol;
- set-valued belief over hidden worlds;
- target/obligation monitor state;
- hidden environment/mode state;
- controller memory;
- action/context;
- source representation and evidence.

A belief is a nonempty subset of hidden worlds consistent with the current observation history and chosen actions. Belief update applies an action to every possible world, then splits the result by the received observation. No probabilities are introduced.

## Objectives

Safety is a current-state invariant and is solved by a greatest fixed point over beliefs. `sure_current_reach` is a finite-horizon knowledge-target attractor. It may represent path reachability directly only when the target is absorbing. General path reachability is lifted to a product with a sticky `visited` monitor.

## Main finite census

Exhaust every pair of two actions on four physical states subject to a chosen singleton target being absorbing under both actions. There are 4 targets × 64 × 64 action-map pairs = 16,384 plant/target systems. Cross each with all 15 set partitions of four states, for 245,760 plant/observation cases.

For every case compare:
1. exact belief-based sure reachability;
2. a stationary observation-only action map;
3. refinement monotonicity.

Also compute the shortest no-observation open-loop synchronizing word and exhaust autonomous controllers with one, two, then three memory states. The native implementation is an independent path from the Python implementation.

## Counterprobes

1. No-observation witness: prove one memory state fails and two states succeed.
2. Nonabsorbing reach witness: the same physical belief occurs before and after target visitation; a sticky monitor distinguishes them.
3. Hidden-mode witness: physical state returns to the same observation while hidden mode knowledge changes. Exhaust every one-state controller (256) and every two-state controller (16,777,216). Preserve the smaller controller even if it contradicts the design intuition.
4. Compare the Python belief fixed point to an independently recursive finite-horizon oracle on 500 seeded absorbing-target plants across all 15 partitions.

## Claim ceiling

Passing establishes the finite computations and the stated deterministic constructions. It does not establish that set-valued beliefs suffice in stochastic games, that controller memory is generally bounded by these examples, or that a probabilistic belief state is unnecessary. No cultural or natural-language semantics are inferred.
