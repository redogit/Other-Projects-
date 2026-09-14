# Pass 11 — objective expansion and obligation-memory reopening

Pass 10 showed that a quotient safe for one action family can become unsafe when a new action is admitted. Pass 11 changes the **other** variable named by the reopening rule: the plant and action family stay fixed, but the obligation gains one sticky path-dependent fact.

The added monitor is deliberately tiny:

```text
M = have we visited physical state 1 yet?
```

It starts from the actual initial state and stays true after the first visit to state 1.

## Exact bounded result

Every ordered pair of deterministic four-state action maps was exhausted (`65,536` plants), with all four initial states (`262,144` plant/initial cases).

A monitor collision means that, from the same fixed initial state, two action histories reach the same current physical state while carrying different monitor values. In that situation the current physical state is not sufficient to reconstruct the expanded obligation state.

Results:

- systems with at least one collision: **48,822 / 65,536**;
- plant/initial cases with a collision: **126,360 / 262,144**;
- colliding physical-state occurrences across those initial cases: **253,380**;
- plant/initial cases by number of colliding physical states: `0: 135,784`, `1: 39,708`, `2: 46,284`, `3: 40,368`, `4: 0`;
- shortest-radius collision certificates: radius `2: 57,024`, `3: 54,756`, `4: 14,580`;
- maximum minimum certificate radius in the census: **4**.

The lexicographically first minimum-radius witness is:

```text
A = [0,0,0,0]
B = [1,0,0,0]
initial = 0
final physical state = 0

word []      -> physical 0, M=0
word [B,A]   -> 0 -> 1 -> 0, M=1
```

So both histories end at physical state `0`, but the expanded obligation state differs. No function of **current physical state alone** can recover that monitor value for this fixed initial condition.

## Interpretation

This gives a second precise reopening mode:

```text
old decision field + old obligation
    -> physical state may be sufficient
same plant + same actions + expanded path obligation
    -> augment with obligation monitor
    -> histories can collide in physical state
    -> retain the monitor distinction
```

The new bit is not claimed to be universally minimal memory. It is the declared monitor for this obligation. Pass 11 tests whether that distinction can be discarded once the objective is expanded; the exhaustive answer is **no** for the collision cases above.

## Run

```sh
cd "SPrime Search/decision-field/objective-monitor"
python3 audit.py --out /tmp/pass11
```

The audit compiles an independent C++17 census, runs it twice, then reconstructs the entire census independently in Python and compares exact JSON results.
