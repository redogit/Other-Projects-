# RMAL Bidirectional Handoff Response Carrier

**Date:** 2026-09-20  
**Status:** `AUTHORED SUCCESSOR / CONTROLLED VALIDATED-SURFACE SUBSET / NOT_RMALC_REVALIDATED`

This is the additive Other-Projects response-side carrier for the central Bidirectional Handoff Pairity protocol.

## Why this exists

The predecessor RMAL carrier already established:

```text
REFERENCE
-> PROPOSAL
-> HANDOFF
-> TARGET_ACCEPTANCE
-> TARGET_LOCAL_SUCCESSOR
```

The missing relation was an explicit return carrier:

```text
REQUEST
-> TARGET-LOCAL DECISION
-> RESPONSE
-> REQUESTER
```

This file adds that relation without claiming generic network/runtime transport.

## RMAL surface discipline

`RMAL_BIDIRECTIONAL_HANDOFF_RESPONSE.rmal` intentionally uses only constructs already present in the RMALC-validated predecessor:

- `MODULE`
- `EXPORT`
- `CONST`
- `CONTEXT`
- `RELATION`
- `PRESERVE`
- `ALLOW`
- `CLAIM`
- `EVIDENCE`
- `COUNTERPROBE`
- `VERIFY`
- `CONTINUE`

The repository-local checker enforces that restricted line-prefix surface and required boundary tokens.

That is **not** equivalent to fresh RMALC validation.

```text
CONTROLLED_SURFACE_CHECK != RMALC_CHECK
CONTROLLED_SURFACE_CHECK != RMALC_COMPILE
CONTROLLED_SURFACE_CHECK != RMALC_AUDIT
```

## Response semantics

The carrier declares:

```text
request identity
target-local decision
response status
provenance
way back
privacy
unresolved remainder
```

Response states:

```text
accepted
rejected
needs_evidence
unresolved
```

A counterproposal must preserve the prior request/response and create a new handoff relation.

## Authority

```text
REQUEST != COMMAND
RESPONSE != AUTHORITY_TRANSFER
RELATED != AUTHORIZED_TO_EDIT
SHARED_METHOD != SHARED_EVIDENCE
TARGET_LOCAL_SUCCESSOR != CROSS_WRITE
```

## Validation status

The predecessor carrier was validated with RMALC 2.1.1:

- check: PASS
- compile: PASS
- audit: PASS
- merge anchor: `f93f056a33d5fad0f29b763a0d49c6b79eb18d49`

This successor has **not** been freshly run through RMALC because the compiler/toolchain is not present in the repository-accessible Git surface used for this change.

The local checker therefore records only:

```text
restricted known RMAL surface = checked
required response/boundary declarations = checked
fresh RMALC compilation = NOT ESTABLISHED
runtime transport = NOT ESTABLISHED
```

## Claim ceiling

`AUTHORED_RMAL_RESPONSE_SUCCESSOR_WITHOUT_FRESH_COMPILER_OR_RUNTIME_EVIDENCE`
