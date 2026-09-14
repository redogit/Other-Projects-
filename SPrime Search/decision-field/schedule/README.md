# Schedule Field Pass 07

Pass 07 implements the missing temporal layer identified by the hardening of Pass 06: **the schedule is part of the decision-field subject**.

For a fixed T4 system, each context is one map on four states. Any finite context word composes to another map on four states. There are only `4^4 = 256` possible such maps, so the complete open-loop schedule closure is finite even though there are infinitely many words.

The module provides:
- exact finite-word composition and shortest representative words;
- complete schedule-semigroup closure;
- periodic-block cycle analysis;
- exact arbitrary-switching reachability and safety fixed points;
- finite-memory, observation-driven Moore schedulers;
- scheduler minimization and minimum memory-bit accounting.

The important distinction is:

```text
same final composed plant map
!=
same intermediate trajectory
!=
same emitted context history
!=
same external consequence
```

So schedule equivalence is deliberately task-relative.

For the Pass 06 witness `T4AAAAgF`, contexts `0` and `1` generate a 12-element transformation semigroup. Their alternating block `(0,1)` induces map `0x0a`, whose block-boundary dynamics contain the cycle `(0,2)`. A periodic alternator requires two scheduler phases, hence one bit of temporal memory; a three-phase schedule requires three states, hence two bits.

The audit also finds words with the same final composed plant map but different intermediate trajectories. This prevents final-map compression from being silently reused for path-sensitive obligations.

Run from `SPrime Search/decision-field/schedule/`:

```sh
python audit.py
```

The audit is deterministic, uses Python's standard library plus a small C++17 independent oracle, and is intended to run under the existing SPrime Decision Field CI. `evidence/SUMMARY.json` records the bounded results and `evidence/VERIFICATION.json` records the source hashes and validation scope.
