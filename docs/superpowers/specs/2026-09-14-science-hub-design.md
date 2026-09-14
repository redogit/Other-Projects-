# Science Hub — Canonical Research Registry and Public Mirror Design

Date: 2026-09-14  
Status: reviewed design; implementation gated on review of this written specification  
Scope: cross-repository and Library-wide scientific work, with `redogit/Other-Projects-` hosting the public mirror implementation

## 1. Purpose

Create one provenance-preserving place from which the scientific state of the user's work can be reconstructed without flattening distinct projects, silently moving authority, or turning navigation into proof.

The Science Hub must answer, mechanically and with bounded claims:

1. What scientific work is known to exist?
2. Where is each source's authoritative carrier?
3. What is each item's epistemic status?
4. Which claims are admitted, provisional, contradicted, superseded, retracted, unresolved, or merely proposed?
5. Which experiments were executed, which failed, which produced null results, and which remain open?
6. What evidence supports each claim, at what exact source revision, and under what claim ceiling?
7. What can be reproduced, independently verified, or externally replicated?
8. What may safely be published?
9. What remains private, restricted, unresolved, or inaccessible?
10. What scientific territory has been scanned versus not yet scanned?

The Science Hub centralizes discoverability, provenance, status, relations, and export. It does **not** physically absorb every source artifact.

Core invariant:

```text
CENTRAL INDEX != CENTRALIZED AUTHORITY
```

Original source artifacts remain authoritative for their own content unless a project-internal handoff or supersession rule explicitly changes that authority.

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

The GitHub mirror is derived only.

```text
LIBRARY_CANONICAL = true
GITHUB_PUBLIC_MIRROR = derived
PUBLIC_MIRROR != COMPLETE_SCIENCE
PUBLIC_MIRROR != AUTHORITY
```

Direct GitHub mirror edits never silently rewrite the Library. They become candidate imports requiring explicit canonical admission.

## 3. Existing source topology and preservation boundary

The current source landscape includes:

- GitHub repositories: `redogit/redogit`, `redogit/conscience64`, `redogit/Other-Projects-`, `redogit/orbit`, `redogit/FirstNeuralNetwork`, `redogit/Dream-To-Action`, `redogit/MauiBrickBreak`, and `redogit/DnD`;
- Library roots including CSOL, One_Level_Up, One_Level_Up_Airlock, Operator Moonshot, MoonShot recovery material, Orbit Lab, R³ Scientific Method, SHADOW, TBCL and TBCL — Context Language Lab, Parameter_Differential_Reflow, RuntimeRelationIndex, and related standalone research artifacts;
- current research lines including SPrime / decision fields / BOM work, P versus NP, Hodge, Conscience64 research, geometry/codecs, model experiments, knowledge recovery, compiler/retrieval work, and experimental method infrastructure;
- external scientific literature used for methodological checks.

The Hub may reference all of these. Ingestion does not grant them equal scientific authority.

Historical alias resolution follows:

```text
stable ID
→ canonical current path
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

The canonical hub is a registry and evidence-navigation layer. Large source archives remain in source-native locations unless a separate custody decision is explicitly made.

## 5. Public mirror layout

The generated public mirror lives at:

```text
redogit/Other-Projects-/Science-Hub/
```

Initial outputs:

```text
README.md
SCIENCE_REGISTRY.public.json
PROJECT_REGISTRY.public.json
CLAIMS_LEDGER.public.json
EXPERIMENTS_LEDGER.public.json
FAILURES_AND_NEGATIVES.public.json
OPEN_QUESTIONS.public.json
RELATION_GRAPH.public.json
PUBLIC_EXPORT_MANIFEST.json
```

Every generated file records:

- canonical Science Hub version;
- canonical manifest hash;
- export-policy version;
- generation timestamp;
- source revisions used;
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

origin
authoring_context
carrier
canonical_path
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

Three identities remain distinct:

```text
record identity != source identity != claim identity
```

One file can contain multiple claims and experiments. One claim can depend on multiple files or runs.

### 6.2 EXPERIMENT fields

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

### 6.3 CLAIM fields

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

### 6.4 RESULT fields

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

### 6.5 FAILURE fields

```text
failure_kind
failed_component
trigger
observed_behavior
impact
repair_status
whether_claims_affected
```

### 6.6 QUESTION fields

```text
question
why_open
blocking_dependencies[]
next_discriminator
priority_basis
```

### 6.7 METHOD fields

```text
procedure
assumptions
inputs
outputs
known_limits
validated_domains[]
```

## 7. Epistemic statuses

The Hub preserves distinctions already established in the research-recovery discipline:

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

Operational lifecycle states are separate:

```text
DISCOVERED
CLASSIFIED
PROVISIONAL
ADMITTED
UNRESOLVED
SUPERSEDED
RETRACTED
```

Epistemic meaning and workflow state are not collapsed into one field.

## 8. Ingestion algorithm

The ingestion doctrine is:

```text
DISCOVER FIRST
CLASSIFY SECOND
INTERPRET LAST
```

### 8.1 Phase 1 — discovery

Enumerate source carriers without first deciding their scientific importance:

- Library roots and loose research files;
- GitHub repositories and science-bearing paths;
- historical archives and recovery packets;
- experiment directories;
- code, datasets, manifests, CI evidence, reports, ledgers, and hashes;
- external literature records.

Each discovered source receives a SOURCE record even when its scientific role remains unresolved.

### 8.2 Phase 2 — identity resolution

Resolve source identity using stable identifiers, exact paths, aliases, hashes, and explicit lineage. Never substitute an item purely because it looks semantically similar.

### 8.3 Phase 3 — duplicate classification

Candidate duplicates receive one of:

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

Only exact duplicates may be deduplicated automatically in navigation. No ingestion operation physically deletes source history.

### 8.4 Phase 4 — epistemic classification

Scientific content is classified using the statuses in Section 7 before claims are promoted.

### 8.5 Phase 5 — claim extraction

For every candidate claim, record:

- exact assertion;
- declared scope;
- supporting source revision;
- whether it was executed;
- verification state;
- later narrowing or contradiction;
- counterexamples;
- explicit non-claims / claim ceiling.

Unresolved support means the claim remains `PROVISIONAL` or `UNRESOLVED`.

### 8.6 Phase 6 — conflict handling

Conflicts are preserved rather than averaged away.

Conflict classes:

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

A later result does not erase an earlier one.

### 8.7 Phase 7 — supersession

Supersession changes current navigation but preserves historical addressability.

Each supersession records its cause, such as:

```text
bug fix
stronger evidence
broader domain
narrowed claim
new source authority
format migration
historical correction
```

### 8.8 Phase 8 — admission

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

The Hub never equates search exhaustion with ontological completeness.

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

The Science Hub contains or links an Experimental Surface Atlas so large-scale testing expands coverage without inflating claims.

A surface descriptor records at least:

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

The Atlas sits above existing admitted passes rather than rewriting them.

```text
experiment definition
!= execution
!= verification
!= interpretation
!= admission
```

## 11. Experiment tiers

### Tier 0 — admitted exact baselines

Current bounded exact work, including established SPrime decision-field passes and their successors, remains immutable evidence history.

### Tier 1 — exhaustive perturbation surfaces

Priority families:

- sensor × memory frontier;
- action × objective reopening;
- continuation-depth witnesses;
- carrier/integrity attacks;
- direct/compiled/AOP equivalence and full cost accounting.

### Tier 2 — larger finite systems

For state/action sizes where total enumeration becomes infeasible:

- exact per-instance algorithms;
- deterministic sampling contracts;
- exhaustive subspaces;
- structural invariants;
- adversarially chosen instances;
- independent implementation or orthogonal verification where load-bearing.

Tier 2 results never inherit Tier 1's exhaustive wording.

### Tier 3 — new mathematical regimes

Separate contracts are required for:

- nondeterministic transitions;
- stochastic transitions;
- noisy observation;
- probabilistic beliefs;
- adversarial observation corruption;
- changing objectives;
- online action admission;
- learned/adaptive policies.

### Tier 4 — cross-domain method probes

Methods, questions, and test shapes may move into compiler, carrier, Knowledge Garden, game-ECS, or other domains.

```text
METHOD TRANSFER      allowed
QUESTION TRANSFER    allowed
TEST SHAPE TRANSFER  allowed
RESULT TRANSFER      prohibited by default
EVIDENCE TRANSFER    prohibited by default
AUTHORITY TRANSFER   prohibited by default
```

P-versus-NP, Hodge, physics, game, and other firewalls remain intact unless a direct tested relation is separately established.

## 12. Evidence lanes

Every experimental run belongs to exactly one lane:

```text
EXPLORE
CONFIRM
VERIFY
ATTACK
```

### EXPLORE

May adapt freely. It discovers hypotheses, structure, and candidate counterexamples but cannot promote a claim by itself.

### CONFIRM

Uses a frozen protocol, predeclared surface family, protected feedback interface, declared stopping rule, and declared family for any inferential multiplicity control.

### VERIFY

Uses an independent implementation, orthogonal invariant, clean-environment reproduction, or other declared verifier. Independence type must be stated.

### ATTACK

Attempts to break an admitted result, implementation, carrier, or interpretation. Attack evidence can narrow, suspend, supersede, or revoke a claim; it cannot inflate one merely because attacks failed.

The progression is:

```text
explore widely
confirm narrowly
verify independently
attack aggressively
admit slowly
```

## 13. Protected confirmation interface

Adaptive experiment selection must not freely inspect confirmation evidence.

The confirmation interface exposes only predeclared outputs necessary for the specific confirmation decision. Detailed holdout feedback does not flow back into adaptive hypothesis generation unless a new versioned confirmation batch is declared.

An exploratory surprise creates a new confirmation contract rather than retroactively changing the active one.

## 14. Surface identity and deduplication

Three identifiers remain distinct:

```text
RUN ID     = one execution
SURFACE ID = one scientific question under a declared contract
CLAIM ID   = one interpretation
```

Repeated executions of one surface are replication/reproduction activity, not automatically independent evidence.

Candidate surface relations:

```text
NEW
REPLICATION
STRICT_SUPERSET
STRICT_SUBSET
REPRESENTATIONAL_VARIANT
INTERACTION_TEST
ADVERSARIAL_COUNTERPROBE
UNRESOLVED_RELATION
```

## 15. Degree-of-change discipline and DOE

Default confirmatory experiments change one consequential degree:

```text
Δ = 1
```

Pairwise changes require an explicit interaction purpose.

```text
Δ = 2
purpose = interaction
```

Three-or-more-degree perturbations are exploratory by default until decomposed.

For many-factor regimes, the Atlas does not take a blind Cartesian product. It uses scientific design-of-experiments discipline:

```text
one-degree exact tests
→ screening designs
→ targeted interactions
→ local response-surface or focused factorial work
```

Compute is concentrated near consequential transitions rather than uniformly across already-stable regions.

## 16. Performance measurement discipline

Semantic exactness tests are distinct from performance tests.

Performance experiments must record and, where applicable, randomize or block by:

```text
hardware / runner
compiler/runtime version
cache state
thermal/load regime
filesystem/network regime
input ordering
```

Cost claims must specify the compared vector, such as:

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

A local execution speedup cannot be presented as total-cost dominance without full declared cost accounting.

## 17. Exact versus statistical evidence

Complete finite enumeration should report exact counts and domain-bounded statements rather than importing unnecessary inferential statistics.

Sampled or stochastic regimes may require:

- effect sizes;
- uncertainty intervals;
- declared hypothesis families;
- multiple-testing control where applicable;
- minimum consequential effect thresholds;
- predeclared stopping rules.

Statuses distinguish:

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

Two independently written programs over the same finite domain are valuable independent computational verification, not automatically empirical replication.

Promoted computational results should provide enough environment and execution information for clean-environment replay where practical.

## 19. Specification families

When several scientifically defensible choices exist, the Hub records a `SPECIFICATION_FAMILY` rather than silently selecting the most favorable one.

Claims may be classified:

```text
ROBUST
CONDITIONAL
FRAGILE
UNRESOLVED
```

Running many specifications does not itself create valid inference. Specification analysis is primarily a robustness surface unless a separate inferential procedure is justified.

## 20. Atlas Constitution

The Atlas itself is governed as a fallible scientific object.

Core constitutional invariants:

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

The scheduler allocates tests; it does not decide truth.

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

Reports retain the denominator: how many eligible surfaces existed, how many were sampled, and why.

A resource allocator maintains distinct categories for:

```text
EXPLOIT
EXPLORE
REPRODUCE_OR_REPLICATE
ATTACK
NEGATIVE_CONTROL
RANDOM_AUDIT
```

No success metric may silently eliminate challenge or random-audit capacity.

## 22. Meta-experiments on the research process

The Science Hub should eventually maintain synthetic scientific universes with hidden ground truth. These test the research methodology rather than the domain hypothesis.

Synthetic worlds may contain:

- true main effects;
- true interactions;
- true nulls;
- latent confounds;
- representation aliases;
- false correlations;
- rare counterexamples;
- regime boundaries;
- resource traps;
- stale artifacts;
- checksum-valid semantic corruption.

Meta-level diagnostics may include:

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

These metrics are diagnostics, not objectives to game.

## 23. Constitutional amendment protocol

Governance changes use:

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

A later constitution version never retroactively converts an older exploratory result into a preregistered or prospectively confirmed result.

## 24. External challenge boundary

A claim approaching promotion should be challengeable by an agent, implementation, or reviewer tasked to seek:

- alternative explanations;
- simpler explanations;
- counterexamples;
- implementation confounds;
- provenance defects;
- omitted costs;
- equivalent representations;
- claim-ceiling violations.

The challenger is not rewarded for agreement.

## 25. Public export policy

Export is default deny.

Each canonical record receives exactly one export class:

```text
PUBLIC
PUBLIC_METADATA_ONLY
PRIVATE
RESTRICTED
UNRESOLVED
```

Rules:

- `PUBLIC`: eligible for full public record export.
- `PUBLIC_METADATA_ONLY`: only approved public metadata may export.
- `PRIVATE`: no public payload.
- `RESTRICTED`: no public payload without an explicit policy change.
- `UNRESOLVED`: never automatically exported.

A public claim depending materially on inaccessible private evidence may export as admitted only when sufficient public evidence independently supports the public statement. Otherwise it remains non-public or clearly non-admitted.

The exporter must prevent leakage of private Library paths, private filenames, sensitive identifiers, inaccessible evidence references, and non-public source metadata.

## 26. One-way export flow

```text
Library canonical state
→ export-class filter
→ sensitivity check
→ private-path scrub
→ public-source resolvability check
→ claim-ceiling check
→ deterministic generation
→ independent validator
→ diff against current GitHub mirror
→ reviewable pull request
```

The mirror never self-certifies.

## 27. Versioning and rollback

Canonical Hub versions use explicit parentage, for example:

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

Rollback changes the current Hub pointer. It does not delete later evidence or rewrite historical versions.

Claim narrowing, suspension, revocation, and supersession remain explicit relations.

## 28. v1 ingestion order

The first canonical wave proceeds in this order:

1. Current admitted or actively tested research:
   - SPrime / decision fields / current BOM work;
   - P versus NP;
   - Hodge;
   - Conscience64 scientific work.
2. Current method and infrastructure:
   - R³;
   - One_Level_Up and Airlock boundaries;
   - Orbit / Orbit Lab;
   - Knowledge Garden / compiler / retrieval machinery.
3. Preserved verified lineages:
   - TBCL / Tiny Babel;
   - SHADOW;
   - geometry / 4D codecs / float64 carriers;
   - model experiments.
4. Historical and recovery material:
   - Operator Moonshot;
   - MoonShot recovery/export material;
   - archived experiment packages;
   - historical-recovery maps and ledgers.
5. External literature:
   - indexed only as `EXTERNAL_SOURCE` evidence unless a direct relation is separately established.

## 29. CI topology

The public implementation must provide at least these gates:

### `science-hub-schema`

Validates structural schemas and required fields.

### `science-hub-provenance`

Checks source identity, revision/hash recording, alias resolution, and unresolved-source classification.

### `science-hub-claims`

Checks claim/evidence/status/ceiling consistency and rejects unsupported `ADMITTED` promotion.

### `science-hub-public-export`

Regenerates the public mirror deterministically and checks privacy/export rules plus public source resolvability.

### `science-hub-regression`

Checks that historical IDs, negative results, failures, and supersession relations are not silently dropped.

### `science-hub-counterprobe`

Injects deliberately invalid records and requires rejection, including:

- missing source;
- private path leak;
- circular self-authority;
- bogus supersession;
- admitted claim with no ceiling;
- result with no evidence;
- inaccessible public source reference;
- exact-vs-sampled evidence mislabeling.

## 30. Tool and carrier interoperability

The design is compatible with the tools currently available in this environment:

- Library files can be searched, listed, read, materialized, and persistently organized;
- Library folders and generated artifacts can be created or uploaded without moving original source files;
- GitHub repositories, branches, files, pull requests, and workflow evidence can be inspected and modified through reviewable branches;
- academic literature can be retrieved through the research connector and recorded as external evidence;
- repository revisions can be pinned by commit SHA rather than assuming repository state is static.

Implementation must treat tool availability as an execution capability, not scientific evidence.

## 31. First v1 success criterion

Science Hub v1 is successful only when it can answer from machine-readable records:

> What science do we currently know about, where is its authoritative source, what is its epistemic status, what claims are admitted, what failed, what remains open, and what can safely be published?

It must also answer:

> What known source territory has not yet been scanned or resolved?

A large number of records is not sufficient.

## 32. Explicit non-goals

Science Hub v1 does not claim:

- that every scientific artifact has already been found;
- that Library indexing grants scientific authority;
- that external literature proves internal research claims;
- that two implementations constitute independent empirical replication;
- that exact finite results generalize to stochastic, open-ended, physical, or human domains;
- that P versus NP, Hodge, or other open mathematical targets are solved;
- that the scheduler can determine truth;
- that public export is complete science;
- that historical supersession authorizes deletion;
- that passing CI upgrades an unsupported claim.

## 33. Scientific-method basis

The governance design is deliberately aligned with established methodological ideas while keeping those references external to internal evidence:

- preregistration / prospective protocol specification to reduce outcome-contingent analytic decisions;
- exploration/holdout separation and limited holdout exposure for adaptive analysis;
- design-of-experiments screening before expensive interaction mapping;
- randomization, blocking, and replication for performance experiments;
- separation of exact finite enumeration from statistical inference;
- explicit multiplicity and effect-size discipline in sampled regimes;
- distinction between reproducibility, independent computational verification, and empirical replication;
- multiverse/specification analysis as a robustness check where defensible analysis choices differ;
- adversarial challenge and falsification as first-class research activities.

Representative external methodological references include:

1. Hardwicke, T. E. & Wagenmakers, E.-J. (2023), *Reducing bias, increasing transparency and calibrating confidence with preregistration*, Nature Human Behaviour, DOI `10.1038/s41562-022-01497-2`.
2. Nakkiran, P. & Błasiok, J. (2018), *The Generic Holdout: Preventing False-Discoveries in Adaptive Data Science*, arXiv `1809.05596`.
3. Dirnagl, U. (2020), *Preregistration of exploratory research: Learning from the golden age of discovery*, PLOS Biology, DOI `10.1371/journal.pbio.3000690`.
4. Srivastava, S. (2018), *Sound Inference in Complicated Research: A Multi-Strategy Approach*, DOI `10.31234/osf.io/bwr48`.

These sources motivate methodology. They do not validate domain-specific internal scientific claims.

## 34. Implementation boundary

This specification authorizes design, not implementation.

Implementation begins only after this written specification is explicitly reviewed and approved. The implementation plan must then be produced separately and should decompose work into small, testable, reviewable steps.

No Science Hub canonical folder, public mirror, schema, exporter, ingestion engine, or CI workflow should be treated as complete merely because this design exists.
