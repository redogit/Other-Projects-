# RMAPL / Ω All-Directional Relation Carrier — 2026-09-20

**Status:** bounded executable method carrier  
**Implementation authority:** `redogit/Other-Projects-` / Decision Field Operator Lab  
**Core Ω schema:** unchanged (`rmapl-omega/v0`)  
**Relation carrier schema:** `rmapl-omega-relational-field/v0`

## Purpose

Provide the missing executable sidecar for the all-directional relational field without turning Ω into a shared ontology and without transferring project-local evidence authority.

The carrier binds to an existing Ω identity and records removable typed relations plus a whole-system consequence vector.

```text
OMEGA
+ RELATION FIELD
=
INSPECTABLE RELATIONS
WITHOUT MUTATING NATIVE AUTHORITY
```

## Relation contract

Each relation preserves:

```text
source
target
type
direction
obligation
evidenceRefs
permission
cost
reversibility
uncertainty
provenance
```

`type` is intentionally a non-empty domain-supplied string. Examples may include:

```text
PAIRITY
INTERLINGUA_TRANSLATION
HOLE
DEPENDENCY
WAY_BACK
NEIGHBOR
```

The carrier does not define the domain ontology.

## Consequence vector

Every field carries exactly:

```text
self
neighbor
shared
ambient
delayed
```

This implements:

```text
ONE_DEGREE != ONE_METRIC
LOCAL_SUCCESS != WHOLE_SYSTEM_SUCCESS
```

## Currentness and way back

Currentness uses the shared bounded vocabulary:

```text
CURRENT_EPOCH
CURRENT_CANONICAL
HISTORICAL_PREDECESSOR
HISTORICAL_SUPERSEDED
COEXISTING_LINEAGE
PRESERVED_UNRESOLVED
PRESERVED
```

The sidecar also carries an explicit Ω way-back reference with status:

```text
EXACT_REFERENCE
BOUNDED_REFERENCE
UNRESOLVED
```

## Authority and evidence

The sidecar authority is fixed to:

```text
method-only
```

Relations carry `evidenceRefs`, not evidence promotion. References remain subject to their source authority and claim ceiling.

Hard boundaries:

```text
RELATION != MERGE
METHOD_TRANSFER != EVIDENCE_TRANSFER
OMEGA_VIEW != NATIVE_OBJECT
CURRENT != PROVED
PAIRITY != FORCED_EQUALITY
```

## Identity and tamper behavior

Both each relation and the complete relation field are SHA-256 content-addressed over canonical JSON.

Validation fails closed on:

- unsupported or missing fields;
- invalid Ω identity;
- invalid currentness;
- invalid direction / permission / reversibility;
- negative or non-finite cost;
- uncertainty outside [0,1];
- consequence vectors that do not have exactly the five all-directional keys;
- changed authority/boundaries;
- content/identity tampering.

## Scope

This is a bounded software carrier.

It does **not** establish:

- scientific validity;
- Hodge or P-vs-NP evidence;
- RMALC conformance;
- a universal relation ontology;
- generic multi-agent authority;
- semantic equivalence between connected endpoints.

The source object and every target project retain native authority.
