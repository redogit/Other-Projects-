# FIG-5 v0.26: fresh width-4 panel preregistration

Status: **seeds frozen; formulas not materialized**. This continuation of PR
#89 ends at preregistration. It creates no new scientific result.

The authoritative contract is `FIG5_V026_WIDTH4_PREREGISTRATION.json`.
`FIG5_V026_WIDTH4_SEED_PANEL.json` contains the exact five public block seeds.
`FIG5_V026_WIDTH4_PREREGISTRATION.sha256` binds both files and this note by
exact-byte SHA-256. Their first immutable Git commit is the freeze anchor;
the moving branch head is not a substitute. No seed is selected by a commit
hash, outcome, formula inspection, or score.

## Recovered obligation and relation ledger

The preserved v0.25 cap-160 panel admitted 25/30 rows: five each at n=8..11,
four at n=12, and one at n=13. Its exact-five validation was unevaluable at
the last two levels. Its status remains
`WIDTH4_DENSITY4_INCONCLUSIVE_ADMISSION`. No old formula is rerun at a larger
cap and no old row is pooled into v0.26.

| Relation | Frozen commitment | Consequence of changing it |
|---|---|---|
| Question → construct | Does calibration of the non-tautological candidate survival fraction meet the same bounded held-out prediction rule on a fresh width-4/density-4 panel? | Changes the target claim |
| Construct → observation | R counts executed non-tautological candidates; P_DP sums executed parent-pair pressures | Changes the estimand |
| Design → units | Five fresh blocks, each with n=8..13 and m=4n; n levels share a seed within each block | Changes dependence or panel identity |
| Measurement → evidence | Frozen constructor, DP mirror, complete truth and separate stage receipts | Breaks method or provenance comparability |
| Evidence → claim | Calibration n=8..10; exact-five median log-error comparisons at each n=11..13 | Changes success; no post-hoc repair |
| Claim → decision | Bounded rule met, bounded rule not met, or inconclusive/invalid with explicit reason | Never an asymptotic or P-versus-NP decision |

## Allowance chosen without new outcomes

Declare an active executed-candidate budget of **131,072** for 30 rows.
Divide equally and round down to a power of two:

```text
floor(131072 / 30) = 4369
largest power of two <= 4369 = 4096
30 * 4096 = 122880; unallocated = 8192
```

Thus the active cap is **4,096 per row**, identical at every n and block.
This budget is a declared operational policy, not a measured machine limit
or proof of sufficiency. The old admission obstruction motivates this new
attempt, but old cap-crossing values and new formula outcomes do not set
the allowance. No budget is borrowed between rows. No escalation, retry,
reseed, row replacement, or favorable early stopping is permitted.

The DP mirror computes previews before enforcing its executed-R cap.
Consequently cap 4,096 does not bound planning, normalization, or runtime.
A separate fixed guard gives each GENERATE/VERIFY row-stage child process
120 CPU seconds and 2 GiB of address space. Default concurrency is one,
maximum five; the runner must record its environment. Linux resource-limit
support is a pre-materialization requirement. Limits are policy choices,
not benchmark-derived capacity estimates. Aborts are retained, not retried;
an incomplete row-stage leaves the row unadmitted. Parent orchestration is
outside the per-child guard. Across 30 GENERATE and 30 VERIFY children the
nominal CPU allowance is 7,200 seconds, excluding parent overhead.

## Preserved analysis and evidence authority

Use the unchanged width-4 constructor and priority namespace from v0.25:
bottom SHA-256 priority, canonical-clause tie-break, one maximum-universe
ranking per block, stable lower-n filtering. Only the seeds and active
allowance change; this is not a paired estimate of the cap's effect.

The frozen active solver remains `FIG5-DP-MIRROR/v0.20`. Its default cap is
not authoritative: v0.26 must explicitly pass 4,096. The independent DP
diagnostic remains at 160 and never substitutes for complete truth. The
truth procedure may stop at a checked SAT witness; an UNSAT result requires
exhaustion. Admission still requires a resolved active result agreeing with
valid complete-truth evidence and sealed provenance.

Fit fresh medians on admitted calibration rows only:
`eta_hat=median(R/P_DP)` for P_DP>0, `a_hat=median(R/n)`,
`b_hat=median(R/n²)`. Predict `eta_hat*P_DP`, `a_hat*n`, and `b_hat*n²`.
Use exact rational medians/predictions and the existing floating log1p error.
No v0.25 coefficient is reused. All three validation levels must have exactly
five admitted rows and strictly smaller median error for the survival-fraction
predictor than both controls. Ties do not pass. Unavailable calibration or
missing admission is inconclusive, not evidence of predictor failure.

Carrier probes retain their v0.25 diagnostic role: all 15 validation rows,
reversed variables and clause/literal order, sealed transported elimination
sequence, exact executed-prefix counters and truth. The replay cap follows
the new active cap. Their pass flag does not silently become a new admission
predicate; any mismatch remains visible and bounds carrier claims.

Five fresh 256-bit OS-random seeds were drawn once without constructing or
scoring formulas. They are disjoint from the 30 seeds in available prior
official manifests. This gives fresh random inputs, not a proof of statistical
independence of SHA-256 priorities. Within-block n levels remain dependent.
Formula overlap with the old panel is checked only after the freeze during
MATERIALIZE; any collision/support failure stops without replacement.

## Execution boundary

`PREREGISTER → MATERIALIZE → GENERATE → VERIFY → ADMIT → ANALYZE` remains
separated by immutable, hash-linked receipts. POSTHOC cannot promote a result.
Every fixed row is accounted for, including aborts and rejected evidence.

The current v0.25 official runner deliberately rejects another panel or cap.
It is preserved as the hashed **method reference**, not presented as an
executable v0.26 runner. Before any official formula is materialized, a v0.26
adapter must be committed and hashed, checked against this immutable contract
using non-official fixtures, and must enforce the seed, cap, row-set, resource,
source-hash, receipt and stage guards. It may adapt identities and allowance
plumbing only. If implementing it requires a scientific-method change, stop
and retain this attempt; do not edit this preregistration retrospectively.

No new experiment was executed to validate this document. Integrity checks
are checks of the preregistration and preserved bytes, not DP/truth outcomes.

```text
WIDTH4_INCONCLUSIVE != SURVIVAL_FRACTION_FAILURE
FINITE_FOUR_PANEL_PROGRAM != ASYMPTOTIC_LAW
PREREGISTRATION != EXECUTED_RESULT
GENERATE != VERIFY != ADMIT
P ?= NP = OPEN
```
