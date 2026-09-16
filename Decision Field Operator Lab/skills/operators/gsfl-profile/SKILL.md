---
name: gsfl-operator-profile
version: 0.1.0
description: Execute one registered GSFL v0.1 operator projection without mutating the completed GSFL source baseline or transferring project authority.
---

# GSFL Operator Projection Skill

## Purpose
Execute a single operator from `gsfl-operator-profile.json` using the shared operator envelope.

## Required inputs
- operator id;
- payload;
- trace;
- declared parameters;
- source contract and claim ceiling when crossing project boundaries.

## Procedure
1. Load the operator specification from the profile registry.
2. If `execution=DELEGATE_CANONICAL`, emit a typed handoff to the matching canonical Decision Field operator; do not duplicate its authority.
3. If `execution=GSFL_NATIVE`, copy the envelope before applying the bounded reference operation.
4. Append a trace record containing operator id, semantic effect, evidence effect, and authority effect.
5. Preserve the GSFL v0.1 completed source contract as read-only provenance.
6. Fail closed on unknown operators or missing required parameters.

## Invariants
- `PROJECTION != SOURCE_MUTATION`.
- `OPERATOR_EXECUTION != AUTHORITY_TRANSFER`.
- `FIT != TRUTH`.
- `VERIFY != UNIVERSAL_TRUTH`.
- `TOOL_USE != TOOL_AUTHORITY`.
- synthetic proverb fixtures remain synthetic.

## Output
The output contract is the registered operator's typed packet, including `OBSERVATION_PACKET`, `ROTATION_PACKET`, `VERIFICATION_PACKET`, `FIT_PACKET`, `PROVERB_FIXTURE_PACKET`, `CONFOUND_AUDIT`, `COROLLARY_PACKET`, or the canonical delegated packet.

## Stop / handoff
Delegated canonical operators must hand off to their existing Skill/Agent rather than self-ratifying inside the GSFL profile.
