---
name: operator-select
version: 0.1.0
description: Separate truth, necessity, minimality, verification, authority, lifecycle cost, and deployment before any admission or promotion decision.
---

# SELECT Skill

## Purpose
Make the final bounded decision without collapsing distinct statuses into one score or allowing candidate production to certify itself.

## Status dimensions
Track independently:
- empirical/formal support;
- negative results and counterexamples;
- verification status;
- necessity status;
- minimality status;
- applicability/scope;
- authority/admission status;
- lifecycle/economic cost;
- deployment status.

## Procedure
1. Consume outputs from prior operators with provenance and exact source revisions.
2. Confirm `PROPOSE/SEARCH -> VERIFY -> ADMIT/RETAIN` separation.
3. Reject unsupported interpretation promotion.
4. Compare alternatives under declared obligations and an explicit cost ordering; do not sum incomparable costs without a justified model.
5. Charge construction, indexing, planning, verification, maintenance, migration, and operational costs when relevant.
6. Respect the active ratifier/owner boundary. If authority is missing, return a recommendation rather than changing canonical state.
7. Preserve `UNRESOLVED`, `NO_PROMOTION`, and bounded claims as first-class outcomes.

## Output
`SELECTION_DECISION`: candidates, independent status vector, obligation fit, cost model, decision/recommendation, authority used, claim ceiling, retained remainder, and rollback/recovery pointer.

## Stop / handoff
- evidence insufficient -> route to the operator that owns the missing distinction.
- authority missing -> stop at recommendation.
- admission is permitted only under the owning project's governance; this skill does not transfer authority across projects.
