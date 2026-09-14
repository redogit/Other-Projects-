# Pass 10 — future-safe continuation quotients

Pass 09 made observation compression task-relative. Pass 10 asks when an old quotient stops being safe because the **future action family changes**.

## Exact continuation equivalence

For a deterministic labeled transition system, two states are continuation-equivalent when every finite word over the declared action alphabet ends in states with the same declared label. The implementation computes the coarsest stable quotient by partition refinement and produces a shortest distinguishing action word whenever two states are not equivalent.

This is the familiar finite-state automata idea applied directly to the decision field: preserve exactly the distinctions that some declared future continuation can expose.

## Action expansion splits old compressions

Every ordered pair of four-state action maps was tested: **65,536 systems**. The old quotient sees only action 0; the expanded quotient sees actions 0 and 1.

| old classes → new classes | systems |
|---|---:|
| 2 → 2 | 12,544 |
| 2 → 3 | 6,144 |
| 2 → 4 | 9,984 |
| 3 → 3 | 9,216 |
| 3 → 4 | 15,360 |
| 4 → 4 | 12,288 |

In **31,488 / 65,536** systems, adding one action strictly refines the old quotient. No case merges an old distinction.

All six unordered state pairs were checked in every system: **393,216 pair-equivalence queries**. Every quotient distinction has a finite witness or is proved equivalent by the stable partition.

## A latent two-step distinction

Take the old action:

```text
A = [0,0,0,0]
```

With the label “is the state 0?”, the old quotient is:

```text
[0,1,1,1]
```

so states 1, 2, and 3 are safely merged under every word made only from A.

Now add:

```text
B = [0,3,1,0]
```

The new quotient is:

```text
[0,1,2,3]
```

States 1 and 2 do not become distinguishable after a single B: both are still non-target. Their shortest distinguishing continuation is **B,B**:

```text
1 -> 3 -> 0   target
2 -> 1 -> 3   non-target
```

This is a concrete finite witness that a consequential distinction may be **latent in future composition**, not visible in the present representation or after one step.

Across the complete census, shortest distinguishing-word lengths were:

| length | state-pair cases |
|---:|---:|
| 0 | 196,608 |
| 1 | 119,808 |
| 2 | 23,808 |

Maximum in this four-state/two-action census: 2.

## Consequence for compression and “new ideas”

A quotient may be perfectly future-safe for the capabilities available at time `t` and become insufficient when a new action is admitted at `t+1`.

That gives a precise reopening rule:

```text
old action/objective family
    -> compute coarsest future-safe quotient
    -> preserve source/reopen route
new action or objective arrives
    -> recompute continuation equivalence
    -> split any block exposed by a finite witness
```

The split is not evidence that the underlying physical states suddenly came into existence. What changed was **which distinction became consequential under the expanded future**.

For the larger research direction, this is one concrete candidate for a “new idea” event: a previously lawful equivalence class splits because a newly available continuation can now expose a difference that matters.

## Run

```sh
cd "SPrime Search/decision-field/continuation"
python3 audit.py --out /tmp/pass10
```

The audit uses independent Python and C++17 implementations and deterministic double runs. The result is bounded to four-state deterministic labeled transition systems; path objectives require the objective-monitor construction from Pass 08 before quotienting.
