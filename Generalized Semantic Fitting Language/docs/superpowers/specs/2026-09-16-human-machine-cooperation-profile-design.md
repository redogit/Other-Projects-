# GSFL v0.1 Human–Machine Cooperation Profile Design

**Status:** approved successor design  
**Date:** 2026-09-16  
**Predecessor:** GSFL v0 remains intact and authoritative for its own bounded evidence.

## Goal

Make GSFL's dominant domain vocabulary describe **human understanding, machine learning claims, cooperation between human and machine partners, and the tools used by those partners**, while retaining v0 semantic rotation, invariant preservation, reconstruction, and fit as the underlying admission machinery.

## Success criteria

1. GSFL v0 remains executable and its tests/evidence remain valid.
2. GSFL v0.1 adds first-class human partner, machine partner, tool-use, cooperation-step, understanding-goal, and machine-learning-claim records.
3. A machine-checkable vocabulary audit requires **more than 50% of GSFL v0.1 reserved/domain terms** to belong to the human/machine/understanding/cooperation/partner/tool vocabulary families. Filler prose is not counted.
4. Human and machine partner identities remain distinct through every cooperation trace.
5. Tool use carries purpose and provenance but never grants a tool truth authority.
6. Machine-learning claims are explicit and bounded. In-context adaptation, observed behavior change, external training evidence, and no-learning-claim states remain distinct.
7. Human understanding is represented as a target/evidence field and is never inferred merely from exact machine reconstruction or human approval.
8. Corollaries and confounds are published in both human-readable and machine-readable form.
9. The N-observer example demonstrates human intent → machine proposal → tool-supported comparison → partner review → admitted human-facing representation.

## Architecture

GSFL v0.1 is an **additive cooperation profile** implemented beside, not inside, the v0 parser. `gsfl.py` stays the v0 semantic kernel. A new `gsfl_coop.py` module defines cooperation records, vocabulary classification/audit, machine-learning claim validation, confound checks, and a v0.1 cooperation parser that delegates semantic candidate evaluation to `gsfl.py`.

This keeps the semantic core small and preserves backwards compatibility:

```text
GSFL v0 semantic kernel
        ↑
        │ delegates semantic admission
GSFL v0.1 cooperation profile
        │
        ├─ human partner
        ├─ machine partner
        ├─ tool provenance
        ├─ cooperation trace
        ├─ understanding target/evidence
        ├─ machine-learning claim boundary
        └─ corollary/confound audit
```

## Cooperation record

A v0.1 execution carries:

```text
human_partner
machine_partner
tools[]
cooperation_steps[]
understanding_goal
understanding_evidence
machine_learning_claim
selected_semantic_surface
semantic_evaluations[]
confound_findings[]
vocabulary_audit
```

### Partner identity

Each partner has:

```text
id
kind = HUMAN | MACHINE
role
```

Exactly one declared HUMAN partner and one declared MACHINE partner are required in the bounded v0.1 profile. Their IDs must differ.

### Tool use

Each tool record has:

```text
id
purpose
provenance
```

A cooperation step may reference zero or more declared tools. Unknown tool references fail closed.

### Cooperation step

Each step records:

```text
actor_partner_id
action
detail
tools[]
```

Actors must be declared partners. This preserves attribution instead of collapsing the interaction into an anonymous system action.

## Machine-learning claim states

Allowed states are deliberately conservative:

```text
NO_LEARNING_CLAIM
IN_CONTEXT_ADAPTATION
OBSERVED_BEHAVIOR_CHANGE
EXTERNAL_TRAINING_EVIDENCE
```

The profile does not infer weight updates, training, generalization, or persistent learning from conversation behavior. A state stronger than `NO_LEARNING_CLAIM` requires an explicit evidence string. `EXTERNAL_TRAINING_EVIDENCE` means only that evidence was supplied; GSFL does not independently certify the training event unless a separate verifier is attached.

Core boundary:

```text
MACHINE_OUTPUT != MACHINE_LEARNING_EVIDENCE
IN_CONTEXT_ADAPTATION != WEIGHT_UPDATE
OBSERVED_BEHAVIOR_CHANGE != TRAINING_PROOF
```

## Human-understanding boundary

`UNDERSTANDING_GOAL` expresses what the human partner is intended to be able to reconstruct, explain, decide, or use. `UNDERSTANDING_EVIDENCE` records bounded evidence such as teach-back, task completion, participant response, or `NONE`.

GSFL does not infer understanding from approval, readability, machine reconstruction, or fit score.

```text
HUMAN_APPROVAL != GROUND_TRUTH
HUMAN_APPROVAL != HUMAN_UNDERSTANDING
MACHINE_RECONSTRUCTION != HUMAN_UNDERSTANDING
```

## Vocabulary-majority rule

The v0.1 reserved/domain vocabulary is published as a fixed registry. Terms are classified into thematic families:

- `HUMAN`
- `MACHINE_LEARNING`
- `UNDERSTANDING`
- `COOPERATION`
- `PARTNER`
- `TOOL`
- `SEMANTIC_CORE`

The union of the first six families is the **cooperation vocabulary**. The audit passes only when:

```text
cooperation_terms / all_reserved_terms > 0.50
```

This metric is intentionally lexical and bounded. It proves vocabulary emphasis, not human comprehension, social quality, model capability, or actual cooperation effectiveness.

## v0.1 DSL surface

The successor example uses:

```text
GSFL 0.1
OBJECT <id>
MEANING <key>=<value>
PRESERVE <key>
HUMAN <id> role=<value>
MACHINE <id> role=<value>
TOOL <id> purpose=<value> provenance=<value>
UNDERSTANDING_GOAL <value>
UNDERSTANDING_EVIDENCE <value>
MACHINE_LEARNING <state> evidence=<value>
COOPERATE <partner-id> action=<value> detail=<value> tools=<comma-list-or-none>
...
ROTATE ...
...
FIT
```

Candidate blocks reuse v0 `SURFACE`, `SET`, `DROP`, `METRIC`, `RECONSTRUCT`, and `END` behavior through delegation to the v0 kernel.

## Corollaries

The implementation will publish bounded corollaries, each explicitly contingent on the v0.1 contract:

1. **Attribution corollary:** if partner IDs and cooperation steps are preserved, contribution attribution is reconstructible within the trace.
2. **Tool-provenance corollary:** tool use can be audited independently of granting the tool semantic or truth authority.
3. **Admission-before-optimization corollary:** a higher human-use fit score cannot admit a semantic mutation or invariant failure.
4. **Learning-claim separation corollary:** useful machine contribution can be recorded without asserting machine learning or weight updates.
5. **Understanding separation corollary:** exact machine reconstruction and human-facing fit can coexist with `UNDERSTANDING_EVIDENCE = NONE`.
6. **Partner-distinction corollary:** cooperation can compose contributions while retaining human/machine identity and role distinctions.
7. **Reversible-lineage corollary:** a v0.1 result can preserve source meaning, selected surface, partner/tool trace, and claim boundaries as separate reconstructible fields.

These are contract consequences, not universal theorems about people or machine learning.

## Confounds and controls

The profile will detect or document at least these confounds:

- `APPROVAL_AS_UNDERSTANDING`
- `APPROVAL_AS_TRUTH`
- `OUTPUT_AS_LEARNING_EVIDENCE`
- `IN_CONTEXT_AS_WEIGHT_UPDATE`
- `TOOL_RESULT_AS_AUTHORITY`
- `CORRELATED_TOOLS_AS_INDEPENDENT_VERIFICATION`
- `LEXICAL_MAJORITY_AS_COMPREHENSION`
- `FIT_SCORE_AS_TRUTH`
- `PARTNER_ROLE_COLLAPSE`
- `PROVENANCE_LAUNDERING`
- `AUTOMATION_BIAS`
- `SYNTHETIC_FIXTURE_GENERALIZATION`
- `SELECTION_BIAS_IN_HUMAN_VALIDATION`
- `VERBOSITY_AS_CLARITY`

Machine-detectable confounds fail or warn based on explicit fields; epistemic/social confounds remain published warnings with specified controls.

## Evidence ceiling

GSFL v0.1 may establish that its records, vocabulary audit, parser, claim boundaries, and finite examples behave as declared. It does not establish:

- that a model learned internally;
- that a human understood a surface;
- that cooperation was socially optimal;
- that tool outputs were true;
- that lexical emphasis caused comprehension;
- that the N-observer fixture generalizes to arbitrary tasks or people;
- that machine and human partners have equivalent agency, responsibility, cognition, or authority.

## Publication routing

- `redogit/Other-Projects-` remains the operative implementation home.
- Conscience64 receives a reference-only successor bridge update.
- `redogit/redogit` receives a federation successor record under Knowledge, language, and reconstruction.
- `/Library Consolidation/GSFL/2026-09-16/` receives a v0.1 successor packet without deleting v0.
