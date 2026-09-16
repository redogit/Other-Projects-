# GSFL v0.1 Bidirectional Macro Cycle

**Profile:** `GSFL_V0_1_BIDIRECTIONAL_MACRO_CYCLE`  
**Kind:** composite macro profile  
**Source operator projection:** `GSFL_V0_1_OPERATOR_PROJECTION`  
**Source GSFL lifecycle:** `COMPLETE_BOUNDED_V0_1`

The completed GSFL operator surface now has a reusable outward/inward composition:

```text
INWARD MODEL
  → SEEK
  → QUESTION
  → REFRAME
  → BUILD
  → OUTWARD RESULT
  → RETURN_INWARD
  → INWARD MODEL'
```

## Expansion

```text
SEEK
  = OBSERVE → GROUND → TRACE_TOOL

QUESTION
  = DISTINGUISH → COMPARE → AUDIT_CONFOUNDS

REFRAME
  = MAP → ROTATE → RELATE → PRESERVE

BUILD
  = COMPOSE → REPAIR → VERIFY → SELECT → HANDOFF

RETURN_INWARD
  = RECONSTRUCT → TEACH_BACK → DERIVE_COROLLARIES
    → COMPARE → PRESERVE → FIT
```

These five names are **macros**, not primitive operators. They expand into the previously verified GSFL operator profile. The Decision Field canonical loop remains:

```text
DISTINGUISH → GROUND → TRANSPORT → ATTACK → REPAIR → SELECT
```

## Why bidirectional

The outward half increases contact with observations, distinctions, alternate representations, and bounded construction. The inward half asks whether the result can be reconstructed back into the working model without silently losing provenance, invariants, unresolved questions, or human/machine distinctions.

This produces a repeatable research/build loop:

```text
working model
→ outward exploration
→ bounded construction
→ observed result
→ inward reconstruction
→ reconciled successor model
```

A successor model does not retroactively overwrite its predecessor.

## Reference implementation

- `gsfl-bidirectional-macro-profile.json` — macro registry and exact expansions.
- `gsfl_bidirectional_cycle.py` — deterministic macro executor over `gsfl_operator_projection.apply_operator`.
- `test_gsfl_bidirectional_cycle.py` — contract tests.
- `run_gsfl_bidirectional_audit.py` — reproducible audit.
- `evidence/GSFL_BIDIRECTIONAL_RESULTS.json` — frozen audit summary.

## Bounded evidence

The frozen local audit records:

```text
macro_count = 5
unique_operator_count = 19
operator_invocation_count = 21
macro_phases = OUTWARD, OUTWARD, OUTWARD, OUTWARD, INWARD
selected_candidate = human-admitted
```

It checks deterministic repeat execution, input immutability, source-meaning preservation, source reconstruction, invariant preservation, canonical delegate handoffs, bounded verification, admitted-only fit, confound detection, tool-provenance corollary retention, and preservation of the `COMPLETE_BOUNDED_V0_1` source lifecycle.

Audit execution SHA-256:

`39e9d78e71fb5c88c0bca474e00a0c834fca62a90d5397e6282b9f98943b8267`

## Conversation-local working method

The same structure may be used as a working method in the originating conversation:

```text
OUTWARD:
  seek evidence/context
  → question distinctions
  → reframe representations
  → build bounded successors

INWARD:
  reconstruct source meaning
  → reconcile observations with the working model
  → retain corollaries/confounds/unresolved state
```

That is a behavior/organization convention only. It does not modify model weights, system instructions, platform policy, or hidden runtime state.

## Boundaries

```text
MACRO != NEW_PRIMITIVE
OUTWARD_EXPLORATION != VALIDATION
INWARD_COHERENCE != PROOF
BUILD != TRUTH
PROJECTION != SOURCE_MUTATION
OPERATOR_EXECUTION != AUTHORITY_TRANSFER
FIT != TRUTH
VERIFY != UNIVERSAL_TRUTH
```

A future refinement should be added as another successor rather than silently changing what this macro profile established.
