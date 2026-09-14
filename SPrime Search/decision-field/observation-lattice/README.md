# Pass 09 — decision-relevant observation lattices

Pass 08 established that observation and memory can substitute in bounded deterministic control. Pass 09 asks a sharper question: **which distinctions are actually necessary for a fixed task and controller class?**

## Winning sensors are a region, not a number

Observation structures are the 15 set partitions of four physical states. Refinement means splitting one or more observation blocks, therefore revealing more state distinction.

For deterministic memoryless control, the winning sensor partitions are upward-closed under refinement. Their coarsest winning elements form an antichain of task-sufficient sensor designs.

Across the 16,384 target-absorbing two-action plant/target systems:

| coarsest winning sensor designs | systems |
|---:|---:|
| 1 | 7,168 |
| 2 | 1,392 |
| 4 | 1,872 |
| 6 | 264 |
| no winning full-state policy | 5,688 |

The 7,168 systems with one minimal sensor need no state distinction: a constant action already wins. Every other solvable system has two-class minimal sensors, but there can be several incomparable choices. Across all minimal two-class designs, 5,928 have block profile 3+1 and 5,928 have profile 2+2.

## Why two classes suffice here

A memoryless sensor controller chooses one of two actions from the current observation. Any such controller induces a full-state action policy. Conversely, take any winning full-state policy and group together exactly the states assigned the same action. That action partition implements the same policy and has at most two classes.

Therefore, in this declared two-action memoryless setting:

```text
sensor P is sufficient
iff
P refines the action partition of at least one winning state policy.
```

The native audit checks that statement independently in all **245,760 plant/partition cases**. The Python path checks it again in all **160,440 solvable plant/partition cases**.

This is controller-class relative. It does not imply that arbitrary tasks, side effects, temporal monitors, stochastic systems, or history-dependent controllers need at most two observations.

## Same apparent amount of information, different consequence

A concrete witness uses target 0 and maps:

```text
A = 0x04 = [0,1,0,0]
B = 0x18 = [0,2,1,0]
```

Consider only two-class sensors with block profile 3+1. All four sensors have the same number of observation symbols and the same block-size profile:

```text
[0,0,0,1]  loses
[0,0,1,0]  wins
[0,1,0,0]  wins
[0,1,1,1]  loses
```

So neither class count nor block-size profile determines decision sufficiency. **Which states were separated matters.**

The broader exhaustive count shows the same phenomenon:

- 3,528 plant/target systems have a mixture of winning and losing two-class sensors;
- all 3,528 show that mixture even inside the fixed 3+1 profile;
- 3,264 show it inside the fixed 2+2 profile;
- 3,264 also mix success and failure among three-class 2+1+1 sensors.

That is a precise finite witness for the distinction:

```text
more / equally much information
!=
the consequential distinction for this task.
```

## Implication for compression

A sensor partition is also a lossy quotient of physical state. In this experiment, coarsening remains justified only while at least one winning state policy is constant on every resulting block. The minimal winning antichain therefore records **task-relative safe forgetting boundaries** for this controller class.

There need not be a unique minimal quotient. Several incomparable compressions can preserve the same obligation by supporting different winning policies.

## Run

```sh
cd "SPrime Search/decision-field/observation-lattice"
python3 audit.py --out /tmp/pass09
```

The audit compiles and executes an independent C++17 census twice, then rebuilds the structural result in Python. No external packages or network access are required.
