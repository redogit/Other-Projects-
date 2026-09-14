# Science Hub — Canonical Research Registry and Public Mirror Design

Date: 2026-09-14  
Status: reviewed design; implementation gated on review of this written specification  
Scope: cross-repository and Library-wide scientific work, with `redogit/Other-Projects-` hosting a derived public mirror

## 1. Purpose

Create one provenance-preserving place from which the scientific state of the user's work can be reconstructed without flattening distinct projects, silently moving authority, or turning navigation into proof.

The Science Hub must answer, mechanically and with bounded claims:

1. What scientific work is known to exist?
2. Where is each source's authoritative carrier?
3. What is each item's epistemic status?
4. Which claims are admitted, provisional, contradicted, superseded, retracted, unresolved, or merely proposed?
5. Which experiments were executed, which failed, which produced null results, and which remain open?
6. What evidence supports each claim, at what exact source revision, and under what claim ceiling?
7. What can be reproduced, independently verified, or empirically replicated?
8. What may safely be published?
9. What remains private, restricted, unresolved, or inaccessible?
10. What scientific territory has been scanned versus not yet scanned?

The Science Hub centralizes discoverability, provenance, status, relations, and export. It does **not** physically absorb every source artifact.

```text
CENTRAL INDEX != CENTRALIZED AUTHORITY
```

Original source artifacts remain authoritative for their own content unless a source-native handoff, version rule, or supersession record explicitly changes that authority.

## 2. Canonical location and public mirror

The selected architecture is dual-surface:

```text
Original source artifacts
        ↓
Library /Science Hub/                ← CANONICAL INDEX
        ↓
validated deterministic export
        ↓
redogit/Other-Projects-/Science-Hub/ ← PUBLIC DERIVED MIRROR
```

The Library is canonical because it can represent public, private, restricted, historical, and recovery material without forcing premature publication.

```text
LIBRARY_CANONICAL = true
GITHUB_PUBLIC_MIRROR = derived
PUBLIC_MIRROR != COMPLETE_SCIENCE
PUBLIC_MIRROR != AUTHORITY
```

Direct edits to the GitHub mirror never silently flow backward into the Library. They become candidate imports requiring explicit canonical admission.

## 3. Source topology and privacy boundary

The canonical Hub inventories all source carriers reachable through the approved tools: public and non-public GitHub repositories, Library roots and loose files, experiment directories, archives, recovery packets, datasets, code, manifests, reports, CI evidence, and external literature.

The public specification and public mirror name only public carriers or explicitly export-approved metadata. Private repository names, private Library paths, private filenames, and other restricted metadata are not enumerated here.

Ingestion does not grant discovered sources equal scientific authority.

Historical identity resolution follows:

```text
stable ID
→ canonical current locator
→ historical alias
→ exact hash match
→ explicit lineage relation
→ unresolved
```

Semantic similarity alone never establishes identity.

## 4. Canonical Library layout

```text
/Science Hub/
├── 00_START_HERE.md
├── CONSTITUTION.md
├── SCIENCE_REGISTRY.json
├── PROJECT_REGISTRY.json
├── CLAIMS_LEDGER.json
├── EXPERIMENTS_LEDGER.json
├── FAILURES_AND_NEGATIVES.json
├── OPEN_QUESTIONS.json
├── SOURCE_MAP.json
├── RELATION_GRAPH.json
├── COVERAGE.json
├── EXPORT_POLICY.json
├── EXTERNAL_SCIENCE.md
├── INGEST_STATUS.md
├── provenance/
│   ├── library_sources.json
│   ├── github_sources.json
│   ├── aliases.json
│   └── unresolved_sources.json
└── snapshots/
    └── versioned hub-state manifests
```

The canonical Hub is a registry and evidence-navigation layer. Large source archives remain in source-native locations unless a separate custody decision is explicitly made.

## 5. Public mirror and export-input snapshot

The generated public mirror lives at:

```text
redogit/Other-Projects-/Science-Hub/
```

Initial outputs:

```text
README.md
PUBLIC_EXPORT_INPUT.json
SCIENCE_REGISTRY.public.json
PROJECT_REGISTRY.public.json
CLAIMS_LEDGER.public.json
EXPERIMENTS_LEDGER.public.json
FAILURES_AND_NEGATIVES.public.json
OPEN_QUESTIONS.public.json
RELATION_GRAPH.public.json
PUBLIC_EXPORT_MANIFEST.json
```

`PUBLIC_EXPORT_INPUT.json` is a sanitized, deterministic snapshot produced from the canonical Library. It contains only material already approved for public processing. GitHub CI regenerates and validates the public mirror from this snapshot; it never requires access to the private Library.

Every generated file records:

- canonical Science Hub version;
- canonical manifest hash;
- export-policy version;
- generation timestamp;
- public source revisions used;
- an explicit `derived_public_mirror` marker.

## 6. Record model

Eight primary scientific record types are used:

```text
SOURCE
PROJECT
EXPERIMENT
CLAIM
RESULT
FAILURE
QUESTION
METHOD
```

External literature is represented as `SOURCE` with `origin_class=EXTERNAL`; it is not a ninth record type.

### 6.1 Shared envelope

Every record carries, where applicable:

```text
id
type
title
project_id
status
epistemic_status
created_at
updated_at

source_refs[]
source_revisions[]
source_hashes[]

origin_class
origin
authoring_context
carrier
canonical_locator
historical_aliases[]

evidence_class
verification_state
independence_class
claim_ceiling

depends_on[]
supports[]
contradicts[]
supersedes[]
superseded_by[]
derived_from[]
related_to[]

public_export_class
sensitivity
notes
```

```text
record identity != source identity != claim identity
```

One file may contain multiple claims or experiments. One claim may depend on multiple sources or runs.

### 6.2 EXPERIMENT

```text
question
hypothesis
motivation
inputs
intervention
controls
measurement
changed_degrees
frozen_degrees
resource_budget
stopping_rule
oracle
independent_verifier
execution_status
result_refs[]
failure_modes[]
reproduction_command
environment
```

### 6.3 CLAIM

```text
statement
scope
subject
evidence_refs[]
claim_strength
claim_ceiling
admission_state
counterexamples[]
known_confounds[]
specification_dependence
```

### 6.4 RESULT

```text
observation
measurement
exactness
domain_size
sample_size
uncertainty
effect_size
raw_artifact_refs[]
interpretation_refs[]
```

### 6.5 FAILURE

```text
failure_kind
failed_component
trigger
observed_behavior
impact
repair_status
whether_claims_affected
```

### 6.6 QUESTION

```text
question
why_open
blocking_dependencies[]
next_discriminator
priority_basis
```

### 6.7 METHOD

```text
procedure
assumptions
inputs
outputs
known_limits
validated_domains[]
```

## 7. Epistemic and lifecycle states

Epistemic status:

```text
OBSERVED
EXPERIMENTAL_RESULT
NULL_RESULT
FAILED_RESULT
USER_OBSERVATION
IDEA
HYPOTHESIS
INFERENCE
OPEN_QUESTION
PROCEDURE
ARTIFACT
SUPERSEDED
RETRACTED
```

Workflow lifecycle is separate:

```text
DISCOVERED
CLASSIFIED
PROVISIONAL
ADMITTED
UNRESOLVED
SUPERSEDED
RETRACTED
```

Epistemic meaning and workflow state are never collapsed into one field.

## 8. Ingestion algorithm

```text
DISCOVER FIRST
CLASSIFY SECOND
INTERPRET LAST
```

### 8.1 Discovery

Enumerate source carriers without first deciding their importance. Each discovered source receives a SOURCE record even when its scientific role is unresolved.

### 8.2 Identity resolution

Resolve identity using stable identifiers, exact locators, revision identifiers, aliases, hashes, and explicit lineage. Never substitute an item purely because it appears semantically similar.

### 8.3 Duplicate classification

```text
EXACT_DUPLICATE
BYTE_VARIANT_SAME_CONTENT
DERIVED_COPY
EXPORT_COPY
RECOVERY_COPY
HISTORICAL_VERSION
INDEPENDENT_REIMPLEMENTATION
SEMANTICALLY_SIMILAR
NOT_DUPLICATE
UNRESOLVED
```

Only exact duplicates may be deduplicated automatically in navigation. Ingestion never physically deletes source history.

### 8.4 Epistemic classification

Classify recovered material before claims are promoted.

### 8.5 Claim extraction

For each candidate claim record the exact assertion, scope, supporting source revision, execution status, verification state, later narrowing, contradictions, counterexamples, and explicit claim ceiling.

Unresolved support keeps the claim `PROVISIONAL` or `UNRESOLVED`.

### 8.6 Conflict handling

```text
DIRECT_CONTRADICTION
SCOPE_MISMATCH
VERSION_DRIFT
DIFFERENT_DEFINITION
DIFFERENT_DOMAIN
IMPLEMENTATION_DISAGREEMENT
INTERPRETATION_DISAGREEMENT
UNRESOLVED
```

Conflicts are preserved, not averaged away. A later result does not erase an earlier one.

### 8.7 Supersession

Supersession changes current navigation while retaining history. Every supersession records its reason: bug fix, stronger evidence, broader domain, narrowed claim, new source authority, format migration, historical correction, or another explicit category.

### 8.8 Admission

`ADMITTED` requires:

- sufficiently resolved source identity;
- provenance complete enough for the stated claim;
- evidence class recorded;
- claim ceiling explicit;
- conflict check completed;
- verification state recorded;
- reproduction path present when applicable.

A green execution alone is not admission.

## 9. Completeness and coverage

```text
NOT INDEXED != DOES NOT EXIST
```

`COVERAGE.json` records denominators:

```text
sources_discovered
sources_scanned
sources_indexed
sources_classified
sources_unresolved
sources_excluded_with_reason
sources_unreadable
repos_known
repos_scanned
library_roots_known
library_roots_scanned
historical_aliases_resolved
historical_aliases_unresolved
```

A completeness statement must name its carrier universe and scan boundary.

## 10. Experimental Surface Atlas

The Science Hub contains or links an Experimental Surface Atlas so testing coverage can expand without inflating evidence claims.

A surface records at least:

```text
ExperimentSurface {
  id,
  subject,
  physical_states,
  action_family,
  transition_kind,
  observation_structure,
  observation_noise,
  controller_memory,
  obligation_monitor,
  objective_kind,
  horizon,
  uncertainty_model,
  mutation_policy,
  carrier,
  compiler_mode,
  adversary,
  cost_vector,
  changed_degrees,
  frozen_degrees,
  exactness_class,
  oracle,
  independent_verifier,
  resource_budget,
  expected_failure_modes,
  counterprobes,
  evidence_class,
  claim_ceiling
}
```

Existing admitted passes remain immutable historical evidence records.

```text
experiment definition
!= execution
!= verification
!= interpretation
!= admission
```

## 11. Experiment tiers

### Tier 0 — admitted exact baselines

Existing bounded exact work remains the regression floor.

### Tier 1 — exhaustive perturbation surfaces

Priority families include sensor × memory frontiers, action × objective reopening, continuation-depth witnesses, carrier/integrity attacks, and direct/compiled/AOP equivalence with full cost accounting.

### Tier 2 — larger finite systems

Where total enumeration becomes infeasible, use exact per-instance algorithms, deterministic sampling contracts, exhaustive subspaces, structural invariants, adversarial cases, and independent or orthogonal validation. Tier 2 never inherits Tier 1's exhaustive language.

### Tier 3 — new mathematical regimes

Nondeterminism, stochasticity, noisy observation, probabilistic belief, adversarial corruption, changing objectives, online action admission, and learned policies require separate contracts.

### Tier 4 — cross-domain method probes

```text
METHOD TRANSFER      allowed
QUESTION TRANSFER    allowed
TEST SHAPE TRANSFER  allowed
RESULT TRANSFER      prohibited by default
EVIDENCE TRANSFER    prohibited by default
AUTHORITY TRANSFER   prohibited by default
```

Open-problem, physics, game, compiler, and other evidence firewalls remain intact unless a direct tested relation is separately established.

## 12. Evidence lanes

Every run belongs to exactly one lane:

```text
EXPLORE
CONFIRM
VERIFY
ATTACK
```

- **EXPLORE:** may adapt freely; discovers candidate structure but cannot promote a claim by itself.
- **CONFIRM:** frozen protocol, predeclared surfaces, protected feedback, declared stopping rule, and declared multiplicity family when inference is used.
- **VERIFY:** independent implementation, orthogonal invariant, clean-environment reproduction, or another explicitly classified verifier.
- **ATTACK:** seeks counterexamples, implementation defects, provenance failures, or overclaiming; it may narrow or revoke but cannot inflate a claim merely because attacks fail.

```text
explore widely
confirm narrowly
verify independently
attack aggressively
admit slowly
```

## 13. Protected confirmation interface

Adaptive experiment selection must not freely inspect confirmation evidence. The confirmation interface exposes only predeclared outputs necessary for the confirmation decision. Detailed holdout feedback does not flow back into hypothesis generation unless a new versioned confirmation batch is created.

An exploratory surprise creates a new confirmation contract rather than changing the active one in place.

## 14. Surface identity and deduplication

```text
RUN ID     = one execution
SURFACE ID = one scientific question under a declared contract
CLAIM ID   = one interpretation
```

Repeated runs of one surface are repeated executions or reproduction attempts, not automatically independent evidence.

Surface relations:

```text
NEW
REPRODUCTION
STRICT_SUPERSET
STRICT_SUBSET
REPRESENTATIONAL_VARIANT
INTERACTION_TEST
ADVERSARIAL_COUNTERPROBE
UNRESOLVED_RELATION
```

Empirical replication is reserved for a genuinely new study/data-generating attempt at the same scientific question.

## 15. Degree-of-change discipline and DOE

Default confirmatory experiments change one consequential degree:

```text
Δ = 1
```

Pairwise changes require explicit interaction purpose:

```text
Δ = 2
purpose = interaction
```

Three-or-more-degree perturbations are exploratory by default until decomposed.

Large factor spaces use:

```text
one-degree exact tests
→ screening designs
→ targeted interactions
→ focused factorial or response-surface work
```

The Atlas does not blindly execute a full Cartesian product.

## 16. Performance measurement discipline

Performance experiments record and, where applicable, randomize or block by hardware/runner, compiler/runtime version, cache state, thermal/load regime, filesystem/network regime, and input ordering.

Cost claims name the compared vector:

```text
construction
indexing
planning
compilation
verification
execution
memory
serialization
recovery
```

Execution speed alone is not total-cost dominance.

## 17. Exact versus statistical evidence

Complete finite enumeration reports exact counts and finite-domain statements rather than unnecessary p-values.

Sampled or stochastic regimes may require effect sizes, uncertainty intervals, declared hypothesis families, multiplicity control, minimum consequential effect thresholds, and predeclared stopping rules.

```text
EXACT_ABSENCE_IN_DOMAIN
NEGATIVE_OBSERVED
INCONCLUSIVE_RESOURCE
INCONCLUSIVE_ORACLE
```

Failure to observe an effect in a sampled regime is not an impossibility result.

## 18. Reproducibility, verification, and replication

The Hub distinguishes:

```text
computational reproducibility
implementation independence
algorithmic independence
evidence/data independence
empirical replication
```

Two independently written programs over the same finite domain are independent computational verification when their independence contract supports that label; they are not automatically empirical replication.

Promoted computational results should provide sufficient environment and execution information for clean-environment replay where practical.

## 19. Specification families

When multiple scientifically defensible choices exist, the Hub records a `SPECIFICATION_FAMILY` rather than silently choosing the most favorable formulation.

```text
ROBUST
CONDITIONAL
FRAGILE
UNRESOLVED
```

A specification multiverse is primarily a robustness surface unless a separate inferential procedure is justified.

## 20. Atlas Constitution

The Atlas is itself a fallible scientific object.

```text
THE ATLAS IS ALSO FALLIBLE
SCHEDULER != SCIENTIST OF RECORD
METRIC != OBJECTIVE
ONTOLOGY != TRUTH
VERSION CHANGE != EVIDENCE UPGRADE
METHOD SUCCESS != SCIENTIFIC SUCCESS
MORE EVIDENCE != INDEPENDENT EVIDENCE
ADMISSION IS REVERSIBLE
UNKNOWN != FALSE
CROSS-DOMAIN ANALOGY != TRANSFER
```

The scheduler chooses where to look; it does not decide what is true.

## 21. Scheduler audit and selection bias

Every scheduling decision records:

```text
SchedulerDecision {
  candidates_considered,
  candidates_selected,
  candidates_rejected,
  selection_rule,
  information_available_at_selection,
  expected_information_gain,
  expected_cost,
  diversity_or_challenge_allocation,
  decision_revision
}
```

Reports retain the denominator: eligible surfaces, selected surfaces, and selection rule.

Resource-allocation categories remain distinct:

```text
EXPLOIT
EXPLORE
REPRODUCE
VERIFY
REPLICATE
ATTACK
NEGATIVE_CONTROL
RANDOM_AUDIT
```

No success metric may silently eliminate challenge or random-audit capacity.

## 22. Meta-experiments on the research process

The Hub should eventually maintain synthetic scientific universes with hidden ground truth. These test the research methodology, not a domain hypothesis.

Synthetic worlds may contain true effects, interactions, nulls, latent confounds, aliases, false correlations, rare counterexamples, regime boundaries, resource traps, stale artifacts, and checksum-valid semantic corruption.

Diagnostics may include:

```text
false-admission rate
missed-discovery rate
time-to-counterexample
time-to-correct-revocation
claim-calibration error
confirmation leakage
duplicate-evidence inflation
scheduler selection bias
ontology-miss rate
resource efficiency
negative-result retention
```

These are diagnostics, not optimization objectives.

## 23. Constitutional amendment protocol

```text
PROPOSE AMENDMENT
→ state failure or motivation
→ identify affected invariants
→ replay historical corpus
→ run blinded synthetic-science corpus
→ run adversarial challenge
→ compare old and new governance
→ ADOPT / REJECT / EXPERIMENTAL
```

A later constitution version never retroactively upgrades the prospective status of older evidence.

## 24. External challenge boundary

A claim approaching promotion should be challengeable by a reviewer, implementation, or agent tasked to find alternative explanations, simpler explanations, counterexamples, implementation confounds, provenance defects, omitted costs, equivalent representations, and claim-ceiling violations.

The challenger is not rewarded for agreement.

## 25. Public export policy

Export is default deny.

```text
PUBLIC
PUBLIC_METADATA_ONLY
PRIVATE
RESTRICTED
UNRESOLVED
```

- `PUBLIC`: eligible for full public record export.
- `PUBLIC_METADATA_ONLY`: only approved metadata may export.
- `PRIVATE`: no public payload.
- `RESTRICTED`: no public payload without explicit policy change.
- `UNRESOLVED`: never automatically exported.

A public claim depending materially on inaccessible private evidence may export as admitted only when sufficient public evidence independently supports the public statement. Otherwise it remains non-public or clearly non-admitted.

The exporter must scrub private locators, names, identifiers, inaccessible evidence references, and non-public source metadata.

## 26. One-way export flow

Canonical-side export occurs in the environment that can read the Library:

```text
Library canonical state
→ export-class filter
→ sensitivity check
→ private-metadata scrub
→ public-source resolvability check
→ claim-ceiling check
→ deterministic PUBLIC_EXPORT_INPUT.json
```

GitHub then validates only sanitized public material:

```text
PUBLIC_EXPORT_INPUT.json
→ deterministic mirror generation
→ schema/privacy/source checks
→ diff against committed mirror
→ reviewable pull request
```

GitHub CI never requires credentials or access to the canonical private Library.

## 27. Versioning and rollback

Canonical versions use explicit parentage, for example:

```text
ScienceHub v1.0.0
ScienceHub v1.0.1
```

Every version manifest records:

```text
parent_version
added_records
changed_records
superseded_records
revoked_claims
new_unknowns
source_identity_changes
export_policy_changes
manifest_sha256
```

Rollback changes the current pointer; it does not delete later evidence or rewrite historical versions.

## 28. v1 ingestion order

The first canonical wave proceeds by scientific priority, not by folder order:

1. current admitted or actively tested mathematical/computational research;
2. current research-method and evidence-governance infrastructure;
3. preserved verified lineages and negative-result corpora;
4. historical and recovery material;
5. external literature, represented as `SOURCE` records with `origin_class=EXTERNAL`.

Within each wave, public and private carriers remain separately classified and source-native authority is preserved.

## 29. Validation and CI topology

### Canonical-side gates

These run where Library access exists:

- `canonical-schema`: structural validation;
- `canonical-provenance`: source/revision/hash and alias-resolution checks;
- `canonical-claims`: claim/evidence/status/ceiling consistency;
- `canonical-export-policy`: default-deny classification and scrub checks;
- `canonical-coverage`: denominator accounting and unresolved-source retention.

### GitHub public gates

These run only against sanitized public inputs:

- `science-hub-schema`: public schema validation;
- `science-hub-public-export`: deterministic regeneration from `PUBLIC_EXPORT_INPUT.json`;
- `science-hub-public-provenance`: public source/revision/resolvability checks;
- `science-hub-claims`: public claim/evidence/status/ceiling consistency;
- `science-hub-regression`: historical public IDs, negative results, failures, and supersession relations are not silently dropped;
- `science-hub-counterprobe`: deliberately invalid public records must be rejected.

Counterprobes include missing source, private metadata leak, circular self-authority, bogus supersession, admitted claim without ceiling, result without evidence, inaccessible public source reference, and exact-vs-sampled evidence mislabeling.

## 30. Tool and carrier interoperability

The design is implementable with the current tool surfaces:

- Library tools can search, list, read, materialize, create folders, and upload generated artifacts while preserving originals;
- GitHub tools can inspect exact revisions and create review branches, files, pull requests, and workflow-visible artifacts;
- academic-literature tools can retrieve external methodology sources for EXTERNAL-origin records;
- exact repository revisions can be pinned rather than assuming repository state is static.

Tool availability is execution capability, not scientific evidence.

## 31. v1 success criterion

Science Hub v1 succeeds only when machine-readable records can answer:

> What science do we currently know about, where is its authoritative source, what is its epistemic status, what claims are admitted, what failed, what remains open, and what can safely be published?

It must also answer:

> What known source territory has not yet been scanned, classified, or resolved?

A large record count is not sufficient.

## 32. Explicit non-goals

Science Hub v1 does not claim:

- every scientific artifact has already been found;
- Library indexing grants scientific authority;
- external literature proves internal research claims;
- two implementations constitute empirical replication;
- finite results generalize to stochastic, open-ended, physical, or human domains;
- any named open mathematical problem is solved merely by being indexed;
- the scheduler can determine truth;
- the public mirror is complete science;
- historical supersession authorizes deletion;
- passing CI upgrades an unsupported claim.

## 33. Scientific-method basis

The design aligns with established methodological ideas while keeping external methodology distinct from internal domain evidence:

- prospective protocol specification / preregistration to reduce outcome-contingent analytic decisions;
- exploration/holdout separation and limited holdout exposure for adaptive analysis;
- screening designs before expensive interaction mapping;
- randomization, blocking, and replication where appropriate for performance experiments;
- separation of exact finite enumeration from statistical inference;
- multiplicity, effect-size, and stopping-rule discipline in sampled regimes;
- distinction among reproducibility, independent computational verification, and replication;
- specification/multiverse analysis as a robustness check where defensible choices differ;
- adversarial challenge and falsification as first-class activities.

Representative external references:

1. Hardwicke, T. E. & Wagenmakers, E.-J. (2023), *Reducing bias, increasing transparency and calibrating confidence with preregistration*, Nature Human Behaviour, DOI `10.1038/s41562-022-01497-2`.
2. Nakkiran, P. & Błasiok, J. (2018), *The Generic Holdout: Preventing False-Discoveries in Adaptive Data Science*, arXiv `1809.05596`.
3. Dirnagl, U. (2020), *Preregistration of exploratory research: Learning from the golden age of discovery*, PLOS Biology, DOI `10.1371/journal.pbio.3000690`.
4. Srivastava, S. (2018), *Sound Inference in Complicated Research: A Multi-Strategy Approach*, DOI `10.31234/osf.io/bwr48`.
5. National Academies of Sciences, Engineering, and Medicine (2019), *Reproducibility and Replicability in Science*, DOI `10.17226/25303`.
6. Wasserstein, R. L. & Lazar, N. A. (2016), *The ASA Statement on p-Values: Context, Process, and Purpose*, The American Statistician, DOI `10.1080/00031305.2016.1154108`.
7. Simonsohn, U., Simmons, J. P. & Nelson, L. D. (2020), *Specification curve analysis*, Nature Human Behaviour, DOI `10.1038/s41562-020-0912-z`.
8. NIST/SEMATECH, *e-Handbook of Statistical Methods*, Design of Experiments sections, used as methodological guidance for screening, blocking, randomization, and factorial reasoning.

These sources motivate process. They do not validate domain-specific internal scientific claims.

## 34. Implementation boundary

This specification authorizes design, not implementation.

Implementation begins only after this written specification is explicitly reviewed and approved. The implementation plan must then be produced separately and decomposed into small, testable, reviewable steps.

No canonical Hub folder, schema, exporter, ingestion engine, public mirror, or CI workflow is considered complete merely because this design exists.
