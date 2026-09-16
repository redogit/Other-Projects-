# GSFL v0.1 Proverbial Fixture Generation Design

**Status:** approved successor addendum  
**Date:** 2026-09-16  
**Parent:** GSFL v0.1 Human–Machine Cooperation Profile

## Goal

Generate deterministic proverb-like fixtures that help human and machine partners compare meanings, interpretations, tools, provenance, corollaries, and confounds without claiming a single universal meaning or laundering synthetic language into cultural tradition.

## Fixture schema

Each fixture preserves:

```text
source_text
source_status
context
provenance
human_interpretations[]
machine_interpretations[]
alternate_interpretations[]
invariant_meanings[]
cooperation_trace[]
tools[]
human_understanding_evidence
claims_single_true_meaning = false
```

Source statuses remain typed. At minimum, `TRADITIONAL_OR_COMMON` and `SYNTHETIC` must remain reconstructibly distinct.

## Cooperation behavior

A fixture records a human partner framing/reviewing the saying, a machine partner proposing provisional interpretations, and tools that preserve source/provenance or run semantic checks. Partner disagreement is allowed to survive as an unresolved distinction rather than being forced into consensus.

Machine paraphrase does not count as human-understanding evidence. Human approval does not count as truth. Tool use does not confer authority.

## Semantic admission

The proverb layer delegates representation checks to the preserved GSFL v0 kernel. Human, machine, and alternate interpretation surfaces may be represented as valid rotations only when the declared source/status/provenance object remains unchanged and reconstructible.

This verifies representation transport, not interpretation truth.

## Deterministic generator

The synthetic generator accepts `seed` and `count` and must return byte-reproducible fixture records for the same inputs. Generated records remain `SYNTHETIC` and retain generator provenance.

A counterprobe deliberately changes a synthetic fixture's source status without changing provenance; the confound detector must identify `SYNTHETIC_PROVENANCE_LAUNDERING`.

## Bounded corollaries

- `MULTIPLE_READINGS_REMAIN_DISTINCT`
- `SOURCE_STATUS_PRESERVES_LINEAGE`
- `SYNTHETIC_FIXTURES_CAN_CALIBRATE`
- `PARTNER_DISAGREEMENT_IS_RETAINABLE`
- `PROVERB_IS_SURFACE_NOT_EVIDENCE`
- `TOOL_TRACE_SUPPORTS_RECONSTRUCTION`

Each corollary remains a consequence of the declared fixture contract, not a universal law of language, culture, cognition, or machine learning.

## Confounds and controls

The fixture registry must cover at least:

```text
TRANSLATION_LOSS
CULTURAL_FLATTENING
FALSE_UNIVERSALITY
ATTRIBUTION_UNCERTAINTY
LITERAL_FIGURATIVE_COLLAPSE
MACHINE_PARAPHRASE_AS_HUMAN_UNDERSTANDING
POPULARITY_AS_TRUTH
PRESERVATION_AS_ENDORSEMENT
SYNTHETIC_PROVENANCE_LAUNDERING
LEXICAL_SIMILARITY_AS_CROSS_CULTURAL_EQUIVALENCE
FAMILIARITY_BIAS
SURVIVORSHIP_OF_SAYINGS
PROVERB_AS_EMPIRICAL_EVIDENCE
```

Confound findings are review warnings with controls; they do not assert that a confound definitely caused a person's interpretation.

## Reference audit

The bounded reference audit uses:

- 12 deterministic synthetic proverb-like fixtures;
- 2 common English-language sayings with exact-origin claims explicitly left unestablished;
- repeated byte-identical generation/audit;
- no universal-meaning claim;
- semantic transport checks through GSFL v0;
- explicit corollary and confound registries.

## Claim ceiling

```text
PROVERB != EMPIRICAL_EVIDENCE
POPULARITY != TRUTH
PRESERVATION != ENDORSEMENT
MACHINE_PARAPHRASE != HUMAN_UNDERSTANDING
SYNTHETIC != TRADITIONAL
LEXICAL_SIMILARITY != CROSS_CULTURAL_EQUIVALENCE
MULTIPLE_READINGS != ALL_READINGS_EQUALLY_SUPPORTED
```
