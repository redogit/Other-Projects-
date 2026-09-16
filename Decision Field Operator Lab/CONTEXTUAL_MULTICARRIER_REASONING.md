# Contextual Multi-Carrier Reasoning

This is a successor reasoning profile over the preserved GSFL v0.1 operator projection and bidirectional macro cycle.

## Core model

A word or phrase occurrence does not own one permanent role. Its current job is resolved from the active surface, context, interpreter, time label, obligation, relations, and explicit role hints.

```text
WORD != FIXED_ROLE
ROLE_BINDING != PERMANENT_DEFINITION
MULTI_ROLE != AMBIGUITY_FAILURE
```

One occurrence may therefore carry several simultaneous bounded roles, and different interpreters may retain different bindings without forced merge.

## Four carriers

The same semantic object may be rendered through four parallel carriers:

```text
SYMBOLIC
ANALYTICAL
COMPUTATIONAL
ANALOGICAL
```

Each carrier keeps its own representation, provenance, claim ceiling, declared omissions/introductions, and authority effect.

```text
SYMBOLIC_COMPRESSION != TRUTH
ANALYTICAL_COHERENCE != EMPIRICAL_VALIDATION
COMPUTATIONAL_WITNESS != GENERAL_PROOF
ANALOGY != EVIDENCE_TRANSFER
```

Cross-carrier comparison records shared invariants, losses, introductions, and agreement. Agreement is descriptive only and does not establish independence.

```text
CARRIER_AGREEMENT != INDEPENDENT_VERIFICATION
```

## BBF-style analogy check

Analogical transport is checked as:

```text
FOLD(source)
→ MAP(source structure → target structure)
→ UNFOLD(target)
→ RECONSTRUCT(source invariants)
→ COMPARE
```

Possible bounded outcomes are `PRESERVED`, `LOSS`, `INTRODUCED`, or `UNRESOLVED`. Analogical transport always keeps `evidence_transfer=false` in this reference implementation.

## Promotion gate

A candidate is not promoted because its representations agree. `PROMOTE_SUCCESSOR` requires semantic admission, bounded verification, preserved source invariants, an explicit claim ceiling, and no blocking confounds. Other dispositions are `PRESERVE`, `REOPEN`, `REJECT`, and `UNRESOLVED`.

## Frozen audit

The current bounded audit records:

- 4 reasoning carriers;
- context-dependent role rebinding;
- simultaneous multi-role binding;
- human/machine interpreter separation;
- loss and introduction detection;
- analogy preservation/loss/introduction controls;
- 9 explicit confounds;
- agreement-only candidate → `REOPEN`;
- admitted + verified bounded candidate → `PROMOTE_SUCCESSOR`;
- 14/14 audit checks passing in the frozen fixture.

Audit execution SHA-256:

`d486da9798a729dd658723c27c45c88b9fef9f3907ac38d9597988be65c58cc8`

## Run

```sh
python3 -m unittest discover -s "Decision Field Operator Lab" -p "test_*.py" -v
python3 "Decision Field Operator Lab/run_contextual_multicarrier_audit.py" --check
```

## Boundaries

```text
CONTEXTUAL_ROLE_RESOLUTION != UNIVERSAL_SEMANTIC_PARSER
ROLE_SUPPORT_SCORE != TRUTH_PROBABILITY
MULTI_CARRIER != MULTIPLE_INDEPENDENT_WITNESSES
ANALOGY != EMPIRICAL_EVIDENCE
COMPUTATION != UNIVERSAL_PROOF
ANALYSIS != OBSERVATION
SYMBOL != SUBJECT
COHERENCE != VALIDATION
PROMOTION != SOURCE_REWRITE
```
