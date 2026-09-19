# RMAL Cooperative Implementation Protocol

This is the executable RMAL carrier for the cooperative implementation/provenance protocol.

## Attribution

- **Design authority:** Ryan McMillan.
- **Implementation relation:** human-AI coimplementation with ChatGPT/OpenAI tooling under Ryan's direction, constraints, corrections, and acceptance gates.
- **Authority boundary:** coimplementation does not transfer design authority, repository authority, or scientific truth authority.

## What the RMAL carrier encodes

The source `RMAL_COOPERATIVE_IMPLEMENTATION_PROTOCOL.rmal` uses the implemented RMAL surface to declare:

- the short-form root goal;
- user design authority;
- human-AI coimplementation;
- cross-workstream write denial;
- reference/proposal/handoff/target-acceptance cooperation;
- preservation of provenance, predecessor evidence, target authority, privacy, accessibility, uncertainty, and unresolved remainder;
- explicit denial of evidence transfer and authority transfer by relation;
- counter-probe and verification statements for non-interference.

## Local RMALC 2.1.1 validation

Validated against the current RMAL Tool Chain 2.1.1 package before this Git branch was written.

```text
rmalc check   PASS
rmalc compile PASS
rmalc audit   PASS

module: cooperative_implementation_protocol
ABI: ABI-59035915580F518D6B99
O0 object hash:
366faf954a18ec33115dc3de17ca209857b90c282c38be2c9918b4547b929797
bytecode instructions: 35
input nodes: 20
```

Audit boundaries were preserved:

```text
AUDIT_PASS != SEMANTIC_TRUTH
HASH_INTEGRITY != CLAIM_VALIDITY
```

## Cooperation law

```text
REFERENCE
  -> PROPOSAL
  -> HANDOFF
  -> TARGET_ACCEPTANCE
  -> TARGET_LOCAL_SUCCESSOR
```

Not:

```text
RELATED -> EDIT
LAST_WRITER_WINS
SHARED_METHOD -> SHARED_EVIDENCE
```

## Implementation boundary

This file is valid implemented RMAL syntax.

The larger cooperative workspace semantics—exclusive namespaces, content-addressed shared objects, target-side handoff decisions, adaptive copy-only sorting, and publication gating—remain broader protocol semantics unless/until they are promoted into first-class RMAL parser/runtime constructs.

`SPECIFIED_SEMANTICS != IMPLEMENTED_CORE_FRONTEND`
