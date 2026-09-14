# Pass 09 contract — decision-relevant observation lattice

Date: 2026-09-14. This pass asks which state distinctions must be preserved for a declared controller class and objective. It does not assign a universal scalar value to information.

## Fixed domain

- four deterministic physical states;
- two actions, each a total map on the four states;
- one singleton target state, required to be absorbing under both actions;
- memoryless observation controllers only;
- observations are set partitions of the four physical states;
- objective: from every physical start state, eventually reach the target.

There are 15 observation partitions (Bell number B4). For each target, 64 maps preserve that target, so the exhaustive family contains 4 × 64 × 64 = 16,384 plant/target systems and 245,760 plant/partition cases.

## Structural claim tested

A memoryless observation controller induces a state policy that is constant on every observation block. Conversely, any winning full-state policy can be implemented by a sensor whose blocks group states assigned the same action. Therefore an observation partition is sufficient exactly when it refines the action partition of at least one winning state policy.

With two available actions, a fixed deterministic winning policy requires at most two observation classes. If a constant action policy wins, one class suffices. Different winning policies can induce distinct incomparable coarsest sensors, so minimal sufficient sensors form an antichain rather than a unique scalar threshold.

## Tests

The native implementation independently evaluates all 15 observation partitions for every plant/target system, derives the coarsest action partitions from all 16 state policies, and checks the equivalence above in all 245,760 cases. Python independently reconstructs every solvable case and checks the theorem over its winning partitions.

Counterprobe: for target 0 with maps `0x04 = [0,1,0,0]` and `0x18 = [0,2,1,0]`, all four 3+1 two-class sensors have the same class count and block-size profile, but exactly two win and two fail. Thus class count and block-size profile do not determine task sufficiency.

## Claim ceiling

Results are relative to this plant family, absorbing reach objective, and memoryless observation-controller class. A partition that is sufficient here need not be sufficient for another objective, controller memory bound, side-effect obligation, stochastic model, or historical/semantic task. More observation refinement cannot hurt this controller class, but coarsening is justified only when some winning policy survives it.
