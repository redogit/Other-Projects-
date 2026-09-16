# GSFL v0.1 Proverbial Fixture Generation

Proverbial Fixture Generation is a bounded calibration surface for **human understanding, machine interpretation, partner cooperation, tool provenance, semantic rotation, corollaries, and confounds**.

It does not declare a proverb's one true meaning. It preserves a saying together with its source status, human interpretation, machine interpretation, alternate readings, cooperation trace, tools, provenance, semantic invariants, corollaries, and confound controls.

## Fixture record

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

`TRADITIONAL_OR_COMMON` and `SYNTHETIC` are deliberately different source states. A synthetic machine/human cooperation fixture cannot become traditional merely because it sounds proverbial.

## Human–machine cooperation cycle

```text
human partner frames or supplies the saying
→ machine partner proposes a bounded interpretation
→ tools preserve source/provenance and run semantic checks
→ human partner reviews, rejects, revises, or preserves disagreement
→ GSFL v0 checks whether the representation preserves the declared source object
→ corollaries and confounds remain attached
```

Machine paraphrase is never used as evidence that the human partner understood the saying. Human approval is never used as proof that the saying is true. Tool results never become truth authority merely because a tool produced them.

## Corollaries

The current bounded generator exposes these contract consequences:

- `MULTIPLE_READINGS_REMAIN_DISTINCT` — human, machine, and alternate readings can coexist without forced consensus.
- `SOURCE_STATUS_PRESERVES_LINEAGE` — common/traditional, translated, quoted, and synthetic source states can remain reconstructible.
- `SYNTHETIC_FIXTURES_CAN_CALIBRATE` — invented sayings can test semantic cooperation without acquiring cultural provenance.
- `PARTNER_DISAGREEMENT_IS_RETAINABLE` — disagreement can remain evidence for review rather than being erased as failure.
- `PROVERB_IS_SURFACE_NOT_EVIDENCE` — compact memorable language is not empirical proof.
- `TOOL_TRACE_SUPPORTS_RECONSTRUCTION` — partner/tool history can be reconstructed without granting the tools semantic authority.

These are consequences of the fixture contract, not universal theorems about people, cultures, language, or machine learning.

## Confounds

The registry includes:

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

A confound finding is a warning/control surface, not a claim that the confound definitely caused a human interpretation.

## Deterministic generator

```sh
python run_proverb_generator.py --seed 20260916 --count 12 \
  --out examples/proverbial_synthetic_fixtures.json
```

Generated output contains synthetic proverb-like fixtures only. The audit separately adds two common English-language sayings with explicit **unverified exact-origin** boundaries; it does not claim authorship, date, or universal cultural ownership.

## Audit

```sh
python run_proverb_audit.py --check
```

The frozen bounded audit currently checks:

- 14 total fixtures;
- 12 synthetic fixtures;
- 2 traditional/common fixtures;
- byte-identical deterministic reruns;
- no universal-meaning claim;
- preservation of human/machine/alternate readings;
- v0 semantic admission for the representation surfaces;
- presence of human-understanding, cultural-context, and provenance confounds.

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
