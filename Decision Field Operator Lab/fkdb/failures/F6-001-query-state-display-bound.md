# FKDB Failure F6-001 — query-state display bound

**Date:** 2026-10-04  
**Observed on:** PR #116, Linux browser CI  
**Status:** REPAIRED LOCALLY / RETAINED

## Original obligation

Project structured FKDB query state into the inherited 160x64 Independent Browser
surface while keeping page-generation drift fail-closed.

## Attempt

`current_query.json` carried:

```text
relate = PROVENANCE BEFORE PROMOTION
```

`build_fkdb_pages.py --check` validates bounded display strings at <=25 uppercase
characters so generated text cannot silently exceed the verified one-line surface width.

## Failure

CI test `fkdb_page_build_check` rejected the state before page admission:

```text
ValueError: relate exceeds bounded FKDB line width
```

All six F6 live-query RMAL tests passed in the same run. The failure was therefore
localized to the human-visible projection contract, not query routing.

## Repair

Changed only the bounded display projection to:

```text
PROVENANCE BEFORE CLAIM
```

The broader invariant remains:

```text
RELATION != EVIDENCE_TRANSFER
PROVENANCE PRECEDES CLAIM PROMOTION
```

## Local lesson

Human-visible carriers have physical/representational limits that must be charged.
Semantic intent may require a shorter projection without rewriting the underlying concept.

## Provisional generalization

Every FKDB projection should validate its carrier-specific dimensions before admission.
Carrier-fit failure must remain distinct from semantic failure.

## Prevention rule

```text
CARRIER_FIT_FAILURE != SEMANTIC_FAILURE
PROJECT_ONLY_AFTER_BOUND_CHECK
```
