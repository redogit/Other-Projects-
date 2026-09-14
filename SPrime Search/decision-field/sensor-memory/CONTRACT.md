# Pass 12 computation contract — one-bit memory versus two-class sensors

## Research decision

Pass 08 established that observation and controller memory can substitute in finite deterministic control, while Pass 09 showed that the identity of the observed distinction matters. Pass 12 tests one degree only: **can exactly one controller-memory bit rescue a fixed two-class sensor that no memoryless controller can use?**

## Exact computational surrogate

- Physical states: exactly four, `{0,1,2,3}`.
- Actions: exactly two deterministic total maps.
- Objective: sure reachability of one absorbing target state from **all four physical starting states**.
- Plant/target family: the same Pass 09 family. For each target `t`, both action maps must fix `t`. This gives exactly `16,384` plant/target systems.
- Sensors: exactly the seven set partitions of four states into two observation classes.
- Memoryless baseline: one action is selected for each of the two current observations.
- Memory treatment: exactly two controller states, fixed initial memory state `0`. For each `(memory, current observation)` cell the controller chooses both an action and its next memory state. There are `4^4 = 256` such controllers for each fixed two-class sensor.
- Controller update convention is inherited from Pass 08: current observation selects both the action and next memory; the physical transition then applies the selected action.

A sensor is **memory-rescued** exactly when no memoryless observation policy guarantees target reachability from all starts but at least one declared two-state controller does.

## Arithmetic and coverage

All transitions, observations, policies, controller tables, and reachability checks use exact integers. No probability, floating point, randomness, network access, or external package is used.

The exact census contains:

`16,384 systems × 7 two-class sensors = 114,688 sensor cases`.

## PASS requirements

PASS requires:

1. independent C++17 and Python exhaustive censuses agree exactly;
2. native runs are byte-identical;
3. fresh output equals the committed summary and witness;
4. source hashes match the exact checked-out computation sources;
5. previously admitted Passes 07–11 remain green under their own gates.

## Claim ceiling

This can establish only a bounded finite sensor-specific memory substitution result. It does not establish that one bit is universally sufficient, a general memory/observation tradeoff theorem, a POMDP result, optimal control, a model of human memory, or semantic compression in general.
