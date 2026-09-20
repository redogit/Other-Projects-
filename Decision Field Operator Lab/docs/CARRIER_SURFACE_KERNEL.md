# Carrier–Surface Kernel — Public Working Contract

**Date:** 2026-09-20  
**Status:** CURRENT_WORKING / PUBLIC / OPEN_VISIBILITY  
**Authority effect:** Method/specification only. Publication does not promote scientific authority, merge project authorities, transfer evidence, or establish external validation.

## Governing invariant

> **Object identity is invariant; coordinates are negotiable.**

Smallest reusable core:

`Thing + Address + Relation + Carrier + Transform + Invariant + Provenance`

A carrier transports an identified thing between Surfaces, representations, schemas, coordinate systems, modalities, or implementations without silently changing identity, authority, evidence class, or lineage.

## Canonical carrier traversal

`RESOLVE -> ENCODE -> CARRY -> DECODE -> RECONSTRUCT -> COMPARE -> TRACE -> RETURN_HOME`

A traversal is valid only relative to its declared invariant set.

If reconstruction fails the declared invariants, classify the result as **MUTATION / SEMANTIC_DECAY / UNKNOWN**, not as a successful semantic rotation.

## Discrete Surface substrate

```text
Surface[(k1, k2, ..., kn)] -> {ObjectID...}
ObjectID -> {(SurfaceID, k1, k2, ..., kn)...}
```

The reverse mapping is a **preimage set**, not necessarily a single inverse.

### Core operations

- `PUT(surface, address, object_id)`
- `GET(surface, address)`
- `LOCATE(object_id) -> addresses`
- `SLICE(surface, partial_address)`
- `ROTATE(address, source_schema -> target_schema)`
- `PROJECT(surface, kept_dimensions)`
- `EMBED(surface, added_dimensions)`
- `FIT(object_id, target_surface)`
- `UNFIT(address) -> reconstructed identity/meaning`
- `COMPARE(original, reconstructed, invariant_set)`
- `TRACE(object_id or traversal_id) -> provenance`
- `RETURN_HOME(traversal_id) -> recoverable source state`

## Carrier record

Each traversal records at minimum:

```json
{
  "traversal_id": "...",
  "object_id": "...",
  "source_surface": "...",
  "source_address": ["..."],
  "target_surface": "...",
  "target_address": ["..."],
  "carrier_id": "...",
  "transform_id": "...",
  "declared_invariants": ["..."],
  "authority_before": "...",
  "authority_after": "...",
  "privacy_before": "...",
  "privacy_after": "...",
  "evidence_class_before": "...",
  "evidence_class_after": "...",
  "provenance_refs": ["..."],
  "expectation": "...",
  "observation": "...",
  "residual": "...",
  "reconstruction": "...",
  "classification": "ROTATION|MUTATION|SEMANTIC_DECAY|UNKNOWN",
  "recovery": "...",
  "remainder": ["..."]
}
```

## Side-to-side carrier map

| Source | Target | May change | Must not silently change |
|---|---|---|---|
| Mathematical notation | Code/data | syntax, coordinate representation | represented identity, declared semantics |
| Code | Database/index | storage key/schema | object identity, provenance |
| Database/index | Graph | relation encoding | node/object identity, edge meaning |
| Graph | Human language | presentation, ordering | asserted relations, uncertainty |
| Human language | RMAL/RMALKDVMLLL | grammar/carrier encoding | obligation, claim ceiling, source distinction |
| File | Repository artifact | path, packaging | required bytes/meaning, provenance |
| Visual | Structured data | projection/viewpoint | declared invariants, ambiguity record |
| Decision Field | Executable operator | implementation carrier | obligations, bounds, evidence status |

Connections are **relations**, not automatic merges or evidence transfers.

## Semantic Rotation / BBF

A re-key or representation change is accepted as a semantic rotation only after:

`Fold/Resolve -> Transform -> Unfold/Reconstruct -> Compare invariants`

Round trip:

`A -> Carrier -> B -> Carrier^-1 -> A'`

Accept only when `A' ≡ A` under the declared invariant set.

## Fitter

`FIT` chooses an address/representation for a target Surface.

A fitter does **not** create truth. It proposes a placement.

Required follow-up:

`FIT -> COUNTERPROBE -> RECONSTRUCT -> COMPARE -> TRACE`

## Decision Field binding

A Decision Field can be addressed as:

`D[State, Context, Constraints, Observation, Authority, Evidence] -> DecisionCandidate`

The carrier may transport that candidate into another representation, but:

```text
GENERATE != VERIFY != ADMIT
ADMIT != SHARE != PUBLISH
METHOD_TRANSFER != EVIDENCE_TRANSFER
```

## Side-to-side checks before synchronization

For every neighboring component compare:

1. exact revision
2. inputs/outputs
3. interpretation and identity
4. tests/counterprobes
5. storage/schema
6. authority
7. privacy/disclosure
8. resources/cost
9. accessibility
10. recovery/reconstruction

Do not infer ancestry or compatibility from version numbers, upload order, naming similarity, or a locally passing test suite.

## Minimal acceptance matrix

| Check | Expected |
|---|---|
| forward lookup | exact ObjectID set |
| reverse lookup | complete preimage set |
| partial-key slice | only matching addresses |
| round trip | invariant-equivalent reconstruction |
| alias separation | distinct identities remain distinct unless explicitly related |
| authority conservation | no silent promotion |
| evidence conservation | no silent evidence transfer |
| provenance | traversal is reconstructible |
| failure path | failed invariant check produces mutation/decay/unknown |
| recovery | RETURN_HOME restores required source state or records impossibility |
| Remainder | unresolved items remain explicit |

## Mathematical boundary

A multi-key relation is a useful **discrete substrate** for manifold-like systems.

It is not, by itself, a mathematical manifold. Topology, continuity, smoothness, differentiability, metric structure, and compatible charts remain separate structures and obligations.

## Integration rule

This kernel is an adapter contract beneath/alongside existing Surface, Context, Semantic Rotation, BBF, carrier/fitter, Decision Field, Knowledge Decay, provenance, and recoverability structures.

It does **not** create a competing top-level runtime or ontology.

## Public claim ceiling

This publication makes the method **publicly visible**.

It does **not** by itself establish:

- independent scientific validation;
- correctness of every carrier implementation;
- interoperability with every RMAL/RMAPL implementation;
- a proof about manifolds, Hodge, P vs NP, or other open mathematical problems;
- permission to reinterpret evidence or authority merely because the representation moved.

See `CARRIER_SURFACE_PUBLICATION.md` for publication/visibility boundaries.
