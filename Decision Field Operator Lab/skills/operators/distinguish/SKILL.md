---
name: operator-distinguish
version: 0.1.0
description: Freeze the scientific question and convert observed failure into the smallest obligation-relevant distinction before any repair is proposed.
---

# DISTINGUISH Skill

## Purpose
Turn an ambiguous task or witnessed failure into a frozen, testable distinction contract.

## Required inputs
Use the shared operator envelope. At minimum require `subject`, `obligation`, `surface`, `output_definition`, available witnesses, and explicit unknowns.

## Procedure
1. Freeze subject, domain, question, target equivalence, obligations, metrics, thresholds, and status meanings.
2. Separate observed failure from interpretation.
3. Identify the smallest distinction whose loss explains the failure.
4. State what would count as preserving versus collapsing that distinction.
5. Record unresolved alternatives rather than selecting a preferred mechanism.
6. Produce the cheapest lawful discriminator when the distinction is still ambiguous.

## Invariants
- Distinction precedes mechanism.
- Unknown does not mean irrelevant or absent.
- Viewpoint change is not automatically task change.
- Do not use hidden/evaluator truth to choose discovery evidence.
- A finite witness supports only its declared scope.

## Output
`DISTINCTION_PACKET` containing: subject, frozen obligation, domain/surface, witnesses, lost distinction, target equivalence, metrics/thresholds, status vocabulary, unknowns, claim ceiling, and next discriminator.

## Stop / handoff
- provenance or observation semantics unclear -> `GROUND`
- representation/encoding may alter the distinction -> `TRANSPORT`
- multiple live distinctions need a discriminator -> `ATTACK`
- do not hand directly to implementation merely because a mechanism is familiar.
