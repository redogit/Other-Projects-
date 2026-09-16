# GSFL v0.1 Operator Projection

**Projection status:** executable successor surface  
**Source lifecycle:** `COMPLETE_BOUNDED_V0_1`  
**Source completion merge:** `cf9d5a35a39b1a7b92f30e24b2789f659e913f04`

The completed GSFL v0.1 operations are projected into the Decision Field Operator Lab as a separate reusable operator profile.

```text
GSFL COMPLETE_BOUNDED_V0_1
        ↓ read-only source contract
GSFL_V0_1_OPERATOR_PROJECTION
        ↓
23 reusable operators
```

The projection does not reopen, rewrite, or expand the evidence of GSFL v0.1.

## Counts

```text
total operators = 23
GSFL-native = 19
canonical delegates = 4
```

Canonical delegates:

```text
DISTINGUISH → canonical DISTINGUISH
GROUND      → canonical GROUND
REPAIR      → canonical REPAIR
SELECT      → canonical SELECT
```

This prevents a second implementation from silently competing with the existing canonical Operator Lab semantics.

## Native operator families

### Semantic / epistemic

`OBSERVE`, `MAP`, `RELATE`, `COMPARE`, `ROTATE`, `PRESERVE`, `VERIFY`, `RECONSTRUCT`, `FIT`.

### Structural

`COMPOSE`, `SPLIT`, `MERGE`.

### Human–machine cooperation

`COOPERATE`, `HANDOFF`, `TRACE_TOOL`, `TEACH_BACK`.

### Proverbial calibration

`GENERATE_PROVERB_FIXTURE`, `AUDIT_CONFOUNDS`, `DERIVE_COROLLARIES`.

## Effect separation

Every operator record carries three separate effect declarations:

```text
semantic_effect
evidence_effect
authority_effect
```

Examples:

```text
ROTATE:
  semantic_effect  = REPRESENTATION_ONLY
  evidence_effect  = NONE
  authority_effect = NONE

VERIFY:
  semantic_effect  = NONE
  evidence_effect  = ADD_BOUNDED_CHECK
  authority_effect = NONE

FIT:
  semantic_effect  = SELECT_AMONG_ADMITTED
  evidence_effect  = NONE
  authority_effect = NONE
```

This preserves:

```text
FIT != VERIFY
VERIFY != TRUTH
OPERATOR_EXECUTION != AUTHORITY_TRANSFER
```

## Skill / Agent model

All profile records are first-class operators and explicitly point to the shared bounded runner:

- `skills/operators/gsfl-profile/SKILL.md`
- `agents/operators/gsfl-profile/AGENT.md`

The shared runner reads the per-operator specification rather than flattening the operators into one unnamed action.

## Reference executor

`gsfl_operator_projection.py` provides a deterministic reference carrier using copied envelopes:

```text
{
  payload: {...},
  trace: [...]
}
```

Native execution deep-copies the input. Canonical delegation produces explicit handoff records. `FIT` filters to admitted candidates before ranking. Synthetic proverb generation retains `SYNTHETIC` provenance and does not claim one true meaning.

## Evidence

`evidence/GSFL_OPERATOR_RESULTS.json` freezes the bounded projection audit. The audit exercises observation, rotation, preservation, tool trace, cooperation, verification, fit, confound detection, corollary derivation, and canonical repair handoff.

Current declared results:

```text
23 / 23 registered operators
19 native reference operations
4 canonical delegates
source lifecycle = COMPLETE_BOUNDED_V0_1
source meaning preserved in the bounded audit
```

## Boundaries

```text
PROJECTION != SOURCE_MUTATION
OPERATOR_EXECUTION != AUTHORITY_TRANSFER
FIT != TRUTH
VERIFY != UNIVERSAL_TRUTH
MACHINE_OUTPUT != MACHINE_LEARNING_EVIDENCE
TOOL_USE != TOOL_AUTHORITY
PROVERB != EMPIRICAL_EVIDENCE
```

The canonical Decision Field loop remains unchanged:

```text
DISTINGUISH → GROUND → TRANSPORT → ATTACK → REPAIR → SELECT
```
