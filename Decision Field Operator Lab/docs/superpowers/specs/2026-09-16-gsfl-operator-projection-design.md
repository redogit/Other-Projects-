# GSFL v0.1 Operator Projection Design

**Status:** approved implementation design  
**Date:** 2026-09-16  
**Source baseline:** GSFL `COMPLETE_BOUNDED_V0_1`  
**Target:** Decision Field Operator Lab

## Goal

Project the completed GSFL v0.1 operations into a reusable operator profile without changing the frozen GSFL v0.1 evidence or the Decision Field canonical six-operator loop.

## Authority split

```text
GSFL v0.1 complete baseline = semantic/source authority
Decision Field Operator Lab = reusable operator-projection authority
```

```text
PROJECTION != SOURCE_MUTATION
OPERATOR_EXECUTION != AUTHORITY_TRANSFER
```

The source completion merge is pinned as `cf9d5a35a39b1a7b92f30e24b2789f659e913f04`.

## Architecture

The existing canonical registry remains:

```text
DISTINGUISH → GROUND → TRANSPORT → ATTACK → REPAIR → SELECT
```

A separate `gsfl-operator-profile.json` registers 23 GSFL operations. Overlapping operations `DISTINGUISH`, `GROUND`, `REPAIR`, and `SELECT` delegate to the canonical Operator Lab versions rather than creating competing semantics. The remaining 19 operations use a bounded native reference executor.

All 23 operator records explicitly carry:

```text
id
family
execution
output
skill
agent
semantic_effect
evidence_effect
authority_effect
```

A shared profile Skill and Agent execute one operator id at a time while retaining per-operator typed effects and outputs.

## Registered operators

```text
OBSERVE
DISTINGUISH
GROUND
MAP
RELATE
COMPARE
ROTATE
PRESERVE
COMPOSE
SPLIT
MERGE
COOPERATE
HANDOFF
TRACE_TOOL
TEACH_BACK
VERIFY
RECONSTRUCT
REPAIR
FIT
SELECT
GENERATE_PROVERB_FIXTURE
AUDIT_CONFOUNDS
DERIVE_COROLLARIES
```

## Operator families

- semantic/epistemic: `OBSERVE`, `DISTINGUISH`, `GROUND`, `MAP`, `RELATE`, `COMPARE`, `ROTATE`, `PRESERVE`, `VERIFY`, `RECONSTRUCT`, `REPAIR`, `FIT`, `SELECT`;
- cooperation: `COOPERATE`, `HANDOFF`, `TRACE_TOOL`, `TEACH_BACK`;
- structural: `COMPOSE`, `SPLIT`, `MERGE`;
- proverbial: `GENERATE_PROVERB_FIXTURE`, `AUDIT_CONFOUNDS`, `DERIVE_COROLLARIES`.

## Reference execution envelope

```text
envelope = {
  payload: {...},
  trace: [...]
}
```

Every native operator deep-copies the incoming envelope and appends a trace entry with semantic, evidence, and authority effects. Delegated canonical operators append an explicit handoff rather than executing a shadow implementation.

## Critical constraints

```text
FIT != TRUTH
VERIFY != UNIVERSAL_TRUTH
MACHINE_OUTPUT != MACHINE_LEARNING_EVIDENCE
TOOL_USE != TOOL_AUTHORITY
PROVERB != EMPIRICAL_EVIDENCE
```

`FIT` may select only candidates already marked `admitted`.

`ROTATE` may change presentation but not the declared `source_meaning`.

Generated proverb fixtures must remain `SYNTHETIC` and must not claim one universal meaning.

## Verification

The projection must provide:

- unit tests for registry completeness, delegation, immutability, semantic rotation, fit admission, cooperation/tool attribution, proverb provenance, and confound detection;
- deterministic bounded audit with 23 operators, 19 native operators, 4 canonical delegates;
- frozen `evidence/GSFL_OPERATOR_RESULTS.json`;
- exact-head CI via the existing Operator Lab workflow.

## Publication rule

The canonical operator registry may point to the GSFL profile but its `canonical_loop` and six canonical `operators` entries must remain unchanged.

The completed GSFL v0.1 baseline remains frozen. This projection is a successor surface, not a revision of what v0.1 established.
