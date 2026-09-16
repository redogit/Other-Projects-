# GSFL Bidirectional Macro-Cycle Design

**Date:** 2026-09-16  
**Status:** approved successor design  
**Source baseline:** `COMPLETE_BOUNDED_V0_1`  
**Operator projection:** `GSFL_V0_1_OPERATOR_PROJECTION`

## Purpose

Turn the recurring working invariant

```text
seek → question → reframe → build → observe results → reconstruct inward
```

into a reusable **macro composition** over the already-verified GSFL operator projection.

The macro layer is a successor surface. It must not reopen, rewrite, or inflate the completed GSFL v0.1 baseline.

## Core distinction

```text
MACRO != NEW_PRIMITIVE
OUTWARD_EXPLORATION != VALIDATION
INWARD_COHERENCE != PROOF
BUILD != TRUTH
PROJECTION != SOURCE_MUTATION
```

The existing Decision Field canonical loop remains unchanged:

```text
DISTINGUISH → GROUND → TRANSPORT → ATTACK → REPAIR → SELECT
```

The existing GSFL operator projection remains unchanged as the primitive execution surface.

## Macro definitions

### SEEK — outward acquisition

```text
OBSERVE → GROUND → TRACE_TOOL
```

Purpose: gather observations, establish provenance/grounding route, and record tools used.

### QUESTION — outward discrimination

```text
DISTINGUISH → COMPARE → AUDIT_CONFOUNDS
```

Purpose: freeze the relevant distinction, compare live candidates/claims, and surface confounds before reframing.

### REFRAME — outward representation change

```text
MAP → ROTATE → RELATE → PRESERVE
```

Purpose: move the same declared semantic object through a new representation/viewpoint while checking protected invariants.

### BUILD — outward constructive successor

```text
COMPOSE → REPAIR → VERIFY → SELECT → HANDOFF
```

Purpose: compose a candidate successor, route repair through the canonical operator when required, run bounded verification, route selection through the canonical operator, and hand off the resulting bounded state.

### RETURN_INWARD — inward reconciliation

```text
RECONSTRUCT → TEACH_BACK → DERIVE_COROLLARIES → COMPARE → PRESERVE → FIT
```

Purpose: reconstruct the source meaning from the outward result, record bounded human-understanding evidence when available, derive only contract-level corollaries, compare the return state with the source/working model, recheck invariants, and fit only among already-admitted representations.

## Whole cycle

```text
INWARD MODEL
  → SEEK
  → QUESTION
  → REFRAME
  → BUILD
  → WORLD / OUTWARD RESULT
  → RETURN_INWARD
  → INWARD MODEL'
```

The cycle is repeatable. `MODEL'` is a successor working model, not a retroactive rewrite of `MODEL`.

## Execution contract

A macro invocation consumes a normal GSFL operator envelope and a mapping of per-operator parameters. It expands deterministically to the operator IDs above and calls the existing `gsfl_operator_projection.apply_operator` implementation in sequence.

The runner must:

1. deep-copy the caller envelope;
2. keep a `macro_trace` separate from the underlying operator `trace`;
3. reject unknown macro IDs;
4. reject missing required parameter bundles through the underlying operator fail-closed behavior;
5. preserve the source baseline identity and authority boundaries;
6. never add a macro ID to the primitive operator registry;
7. keep outward and inward phases distinguishable in the returned state.

## Conversation-local application

For this conversation, the same composition is adopted as a **working method**, not a system-level mutation:

- outward: seek evidence/context, question distinctions, reframe representations, build bounded successors;
- inward: reconstruct source meaning, reconcile observations with the working model, record corollaries/confounds, preserve unresolved state.

This does not modify model weights, platform policy, system instructions, or hidden runtime state.

## Evidence ceiling

A passing implementation establishes only that:

- macro expansion is deterministic;
- the approved macro-to-operator mapping is preserved;
- the existing operator projection can execute the composition on bounded fixtures;
- source envelopes are not mutated;
- source meaning survives declared representation-only steps in the bounded fixture;
- outward and inward traces remain reconstructible.

It does not establish that outward exploration finds truth, inward reconciliation proves truth, human teach-back proves universal understanding, or a built artifact validates the theory that inspired it.
