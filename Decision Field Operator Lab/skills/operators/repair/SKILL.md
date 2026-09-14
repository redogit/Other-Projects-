---
name: operator-repair
version: 0.1.0
description: Localize a witnessed residual and construct the weakest faithful repair that reduces it without breaking preserved obligations.
---

# REPAIR Skill

## Purpose
Correct only what the evidence requires, preserving prior satisfied obligations, provenance, recoverability, and future revision capacity.

## Procedure
1. Require a witnessed residual; do not invent a mechanism in the absence of failure.
2. Localize the smallest causal/observational obligation that failed.
3. Generate materially different candidate repairs.
4. Order candidates under an explicit complexity preorder.
5. Test weaker candidates first.
6. Require strict reduction of unresolved obligations or a justified well-founded defect rank.
7. Re-run prior obligations and preservation checks.
8. Ablate/neutralize the proposed repair and verify recurrence of its motivating failure or an equivalent target-relevant failure.
9. Record unresolved ties as an equivalence class rather than choosing by name or familiarity.

## Invariants
- a repair that fixes one target while breaking a prior obligation is rejected.
- minimality is subordinate to evidence preservation and future self-revision.
- working does not imply necessary; bounded necessity does not imply universal necessity.

## Output
`REPAIR_PACKET`: residual, lost distinction, candidates, complexity ordering, simpler attempts, restoration evidence, regression evidence, recoverability status, ablation recurrence, minimality status, and claim ceiling.

## Stop / handoff
- repair needs adversarial pressure -> `ATTACK`
- repair changes a load-bearing representation -> `TRANSPORT`
- candidate survives required checks -> `SELECT` for status/authority/economic decision.
