# GSFL v0 specification

**Status:** bounded executable reference specification  
**Date:** 2026-09-16  
**Name:** Generalized Semantic Fitting Language  
**Abbreviation:** GSFL

## 1. Purpose

GSFL expresses a controlled transformation from a semantic object to one or more human-facing representations while making semantic preservation testable.

The intended abstraction is:

\[
F(M,H,C,T) \rightarrow R^*
\]

where:

- `M` is declared source meaning;
- `H` is the relevant human/use model;
- `C` is context;
- `T` is task;
- `F` is the fitter;
- `R*` is the selected admitted representation.

GSFL v0 does not attempt to fully encode `H`, `C`, or `T`. Their influence is represented by an explicit candidate metric vector. That limitation is part of the claim ceiling.

## 2. Semantic object

A source object is:

\[
M = (id, meaning, invariants)
\]

where `meaning` is a finite key/value map and `invariants` is an ordered set of protected meaning keys.

The reference implementation treats exact finite map equality as its v0 semantic identity surrogate.

## 3. Candidate rotation

A candidate is:

\[
R_i = (id_i, meaning_i, surface_i, metrics_i, reconstruction_i)
\]

`surface_i` may change freely. `meaning_i` is compared against the source object to determine whether the candidate is a rotation, mutation, or decay.

## 4. Classification

Let `I` be the declared invariant keys.

### VALID_ROTATION

\[
meaning_i = meaning_{source}
\]

The semantic object is unchanged and only its representation differs.

### MUTATION

All declared invariants are preserved, but:

\[
meaning_i \ne meaning_{source}
\]

The result may be useful, but it is not labeled as a semantic rotation.

### SEMANTIC_DECAY

At least one required invariant is absent or changed:

\[
\exists k \in I: meaning_i[k] \ne meaning_{source}[k]
\]

Missing required keys count as failure rather than `UNKNOWN == ABSENT` substitution.

## 5. Reconstruction gate

The v0 executable admission gate requires:

\[
reconstruction_i = meaning_{source}
\]

This is deliberately stronger than invariant preservation. A surface that preserves the implementation's meaning object but cannot reconstruct it in the declared fixture is not admitted.

Therefore:

```text
classification == VALID_ROTATION
```

is necessary but not sufficient for admission.

## 6. Fitter objective

Each candidate declares:

```text
clarity
usefulness
recoverability
cognitive_effort
ambiguity
semantic_loss
```

Each metric is constrained to `[0,1]`.

The v0 fitter uses:

\[
Q_i = \frac{clarity_i \cdot usefulness_i \cdot recoverability_i}
{1 + cognitiveEffort_i + ambiguity_i + semanticLoss_i}
\]

Only admitted candidates participate in selection.

Ties are resolved lexically by candidate ID so repeated execution is deterministic.

The score is an engineering fixture, not an empirical law of cognition.

## 7. Surface syntax

A program begins with:

```text
GSFL 0
```

The minimal grammar is:

```text
GSFL 0
OBJECT <id>
MEANING <key>=<JSON-or-string-value>
PRESERVE <key>

ROTATE <candidate-id>
SURFACE <JSON-string>
SET <key>=<value>          # optional semantic mutation probe
DROP <key>                 # optional semantic loss probe
METRIC clarity=<0..1> usefulness=<0..1> recoverability=<0..1> cognitive_effort=<0..1> ambiguity=<0..1> semantic_loss=<0..1>
RECONSTRUCT <key>=<value>
END

FIT
```

Comments start with `#` on otherwise standalone lines.

`SET` and `DROP` exist so negative controls can be represented explicitly. They are not shortcuts for claiming a valid rotation.

## 8. Core semantic primitives

The larger GSFL vocabulary is intentionally broader than the v0 parser. The semantic primitive set is:

```text
OBSERVE
DISTINGUISH
SELECT
FIT
ROTATE
MAP
RELATE
COMPOSE
SPLIT
MERGE
COMPARE
REPAIR
VERIFY
RECONSTRUCT
```

v0 directly operationalizes `ROTATE`, `FIT`, `VERIFY`, and `RECONSTRUCT`, with meaning/invariant declarations providing the current `DISTINGUISH` surface.

Future primitives must not be considered implemented merely because they are named here.

## 9. Invariants

The following are normative GSFL design invariants:

```text
MEANING != SURFACE
ROTATION != MUTATION
MUTATION != SEMANTIC_DECAY
FIT != TRUTH
OBSERVATION != INTERPRETATION
GENERATION != CERTIFICATION
RECONSTRUCTION != SOURCE
RELATED != AUTHORITY_TRANSFER
UNKNOWN != ABSENT
```

The current exact-map implementation is only one carrier for these distinctions.

## 10. Determinism

For a fixed program and implementation version:

- candidate classification is deterministic;
- score computation is deterministic within the declared Python reference carrier;
- tie-breaking is deterministic;
- canonical JSON output is key-sorted and newline-terminated;
- the bounded audit executes the example twice and requires byte identity.

## 11. Human validation boundary

The v0 reconstruction map is supplied explicitly in the test fixture. It proves only that the declared machine reconstruction matches the declared source map.

It does **not** prove that a human reader reconstructs the intended meaning. Participant testing, accessibility testing, comprehension measurement, and empirical cognitive validation remain separate gates.

## 12. Evolution rule

A future version may add richer semantic graphs, typed relations, empirical human metrics, learned fitters, alternate objective functions, or cross-carrier compilation only if:

1. the predecessor semantics remain recoverable;
2. changed assumptions are explicit;
3. failures and negative controls are retained;
4. provenance survives transport;
5. new capability does not retroactively inflate v0 evidence.
