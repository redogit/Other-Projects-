# Generalized Semantic Fitting Language (GSFL)

**Lifecycle:** `COMPLETE_BOUNDED_V0_1` — complete for the declared v0.1 implementation, verification, publication, routing, and recovery scope. Future successors remain allowed. See `COMPLETE_STATUS_V0_1.md`.

## v0.1 — Human–Machine Cooperation Profile

GSFL v0.1 makes **human understanding, machine learning claim boundaries, cooperation between human and machine partners, and the tools used by those partners** the dominant language surface while preserving the GSFL v0 semantic kernel underneath.

The cooperation cycle is:

```text
human intent / human understanding goal
→ machine proposal or machine interpretation
→ partner cooperation through explicit tools
→ tool provenance + machine-learning claim boundary
→ semantic invariant and reconstruction checks
→ human review / teach-back / task evidence when available
→ fit among already-admitted representations
→ corollaries + confounds + reconstructible partner/tool lineage
```

The v0.1 reserved vocabulary is machine-audited: more than half of the declared domain terms belong to the `HUMAN`, `MACHINE_LEARNING`, `UNDERSTANDING`, `COOPERATION`, `PARTNER`, or `TOOL` families. That lexical majority proves **language emphasis only**; it does not prove human comprehension, machine learning, good cooperation, or truth.

Core boundaries:

```text
HUMAN_APPROVAL != HUMAN_UNDERSTANDING
HUMAN_APPROVAL != GROUND_TRUTH
MACHINE_OUTPUT != MACHINE_LEARNING_EVIDENCE
IN_CONTEXT_ADAPTATION != WEIGHT_UPDATE
TOOL_USE != TOOL_AUTHORITY
COOPERATION != LOSS_OF_PARTNER_IDENTITY
FIT != TRUTH
```

### v0.1 modules

- `gsfl_coop.py` — human/machine partner records, tool provenance, cooperation steps, understanding evidence, bounded machine-learning claim states, vocabulary audit, corollaries, and confounds.
- `gsfl_proverbs.py` — deterministic proverbial fixture generation with separate human, machine, and alternate interpretations plus source/provenance controls.
- `PROVERBIAL_FIXTURES.md` — proverb fixture contract, corollaries, confounds, and evidence ceiling.
- `COROLLARIES_AND_CONFOUNDS.md` — consolidated human-readable ledger separating observations, contract corollaries, confounds/controls, and unresolved empirical questions.
- `test_gsfl_coop.py` and `test_proverb_fixtures.py` — successor-profile tests.
- `run_coop_audit.py` — frozen human–machine cooperation audit.
- `run_proverb_generator.py` — deterministic synthetic proverb-like corpus generator.
- `run_proverb_audit.py` — frozen proverbial corollary/confound audit.

### Proverbial Fixture Generation

The proverb layer turns compact sayings into **cooperation fixtures**, not truth authorities. Traditional/common sayings retain attribution uncertainty; synthetic sayings retain synthetic provenance. Human and machine interpretations stay separate, partner disagreement may remain unresolved, and tool traces remain inspectable.

```sh
python run_proverb_generator.py --seed 20260916 --count 12 \
  --out examples/proverbial_synthetic_fixtures.json
python run_proverb_audit.py --check
```

The bounded reference audit uses 12 synthetic fixtures plus 2 common English-language sayings. It checks deterministic generation, source-status separation, multiple-reading preservation, semantic reconstruction, and confounds such as cultural flattening, false universality, attribution uncertainty, machine-paraphrase-as-human-understanding, popularity-as-truth, and synthetic-provenance laundering.

### Corollary discipline

GSFL v0.1 publishes corollaries only as consequences of declared software contracts. Examples include reconstructible partner attribution, separable tool provenance, semantic admission before fit optimization, useful machine contribution without a machine-learning claim, preserved human/machine distinctions, multiple proverb readings remaining distinct, and synthetic fixtures remaining synthetic.

A corollary is **not** automatically an empirical law about humans, models, cultures, or cognition. See `COROLLARIES_AND_CONFOUNDS.md` for the consolidated ledger and controls.

### Run the successor tests

```sh
python -m unittest -v test_gsfl.py test_gsfl_coop.py test_proverb_fixtures.py
python run_audit.py --check
python run_coop_audit.py --check
python run_proverb_audit.py --check
```

## v0 — preserved semantic kernel

GSFL v0 remains the bounded executable semantic kernel. It separates declared meaning, invariants, human-facing surface, fit metrics, exact reconstruction, valid rotation, mutation, and semantic decay.

```text
VALID_ROTATION != MUTATION != SEMANTIC_DECAY
ADMITTED = VALID_ROTATION && exact_v0_reconstruction
```

For v0 metrics in `[0,1]`:

```text
benefit = clarity * usefulness * recoverability
burden  = 1 + cognitive_effort + ambiguity + semantic_loss
score   = benefit / burden
```

The score is a bounded engineering surrogate rather than a universal model of human cognition. v0 exact reconstruction is a machine-checkable surrogate rather than evidence that a human partner understood the representation.

The original N-observer accessibility fixture and frozen v0 audit remain preserved. The v0.1 profile delegates semantic admission to this kernel instead of rewriting its evidence.

## Evidence ceiling

GSFL can verify its finite records, parser behavior, deterministic fixtures, provenance fields, semantic admission, vocabulary emphasis, corollary registry, and confound controls. It does not establish:

- that a human understood a representation without human-side evidence;
- that a model performed persistent internal learning;
- that in-context adaptation changed model weights;
- that a tool result is true because a tool produced it;
- that partner cooperation is socially or morally optimal;
- that a proverb has one universal meaning;
- that a common saying has a verified exact origin unless independent evidence establishes it;
- that lexical or thematic similarity makes cultures equivalent;
- that synthetic fixtures are inherited cultural knowledge.

See `SPEC.md` for the preserved v0 contract, the approved v0.1 design under `docs/superpowers/specs/`, `PROVERBIAL_FIXTURES.md` for the proverb-generation successor surface, `COROLLARIES_AND_CONFOUNDS.md` for the combined corollary/confound ledger, and `COMPLETE_STATUS_V0_1.md` for the canonical bounded completion state.
