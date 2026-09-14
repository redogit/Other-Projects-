# Pass 08 — partial observation and knowledge state

Pass 07 made context schedule part of the temporal subject. Pass 08 removes perfect state observation.

The implementation uses exact **set-valued beliefs**: all hidden worlds still compatible with action/observation history. The new state stack is:

```text
physical state
+ observation partition
+ hidden-world belief
+ obligation monitor
+ controller memory
```

These components are deliberately not collapsed.

## Three earned distinctions

### 1. Sensor information and controller memory can substitute for each other

The compact witness is `T4AEBBgE`, using contexts 0 and 1 with maps `[0,1,0,0]` and `[0,2,1,0]`. Start uncertain among physical states `{0,1,2}`; target state 0 is absorbing.

With every state producing the same observation, a stationary controller cannot win. A two-state controller alternating contexts 0 and 1 does win, so one bit of temporal memory is sufficient. Across all 15 observation partitions this witness remains belief-winning; only 10 admit a memoryless observation policy.

The native census widens this to every target-absorbing two-action four-state plant: 16,384 plant/target systems × 15 partitions = **245,760 cases**. It checks 983,040 refinement implications. Of the 10,696 solvable plant/target systems, no observation distinction is required when time-varying control is allowed. Minimum autonomous controller states are 1 for 7,168 systems, 2 for 3,000, and 3 for 528. A memoryless controller instead needs one observation class in 7,168 systems and a two-class sensor partition in 3,528.

That is a finite sensor/memory tradeoff, not a universal cost equivalence.

### 2. Physical belief is not obligation state

For a nonabsorbing reachability target, current-state belief can recur after the target has already been visited. Pass 08 therefore lifts reachability to `physical state × visited-bit`. A two-state swap witness returns to the same physical state after visiting the target; the product belief is different. If post-target behavior differs from pre-target behavior, the physical belief alone cannot select the correct action.

This is why the target-absorbing condition is explicit in the broad census rather than silently assumed.

### 3. Hidden context can survive after the same physical observation returns

An eight-world synthetic system has four physical states and a hidden two-valued mode. A first consequential commit either succeeds or reveals the other mode. After a reset, the physical observation is again state 0, but the hidden-world belief is different and the required commit action changes.

The audit exhausts all **256 one-state controllers**: none wins. It then exhausts all **16,777,216 two-state controllers**: 360,448 win. Thus one bit of controller memory is necessary and sufficient for this witness.

The smallest discovered controller also corrects an initial design assumption: it does not perform a separate probe. It tries one commit first; failure is itself informative, so the action is both consequential and epistemic.

## Run

```sh
cd "SPrime Search/decision-field/partial-observation"
python3 audit.py --out /tmp/pass08
```

The audit compiles two C++17 independent finite-domain checkers. Python standard-library code supplies the reusable belief/monitor/controller implementation.

## Literature boundary

Probabilistic POMDPs commonly use a probability distribution over states as a sufficient statistic for history. Pass 08 does something narrower: deterministic set-valued uncertainty and sure objectives. Richer partial-observation stochastic games can require memory beyond simple belief-based strategies; this project does not reproduce or contradict those results.

References used for calibration:
- Chatterjee & Doyen, *Partial-Observation Stochastic Games: How to Win When Belief Fails* (LICS 2012), https://arxiv.org/abs/1107.2141
- MIT 6.231 lecture notes on imperfect state information and belief/sufficient-statistic reformulation, https://ocw.mit.edu/courses/6-231-dynamic-programming-and-stochastic-control-fall-2015/
