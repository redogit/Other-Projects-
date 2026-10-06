# FKDB — Fighting Knowledge Decay Browser

**Named:** 2026-10-04  
**Lineage:** DIRECT_SUCCESSOR  
**Predecessor:** Independent Browser  
**Current implementation home:** Decision Field Operator Lab/rmal-browser

## Identity

FKDB is the directly descended successor of the Independent Browser.

This is a naming and successor event, not a retroactive rename of historical artifacts.
Existing independent_browser.*, RMAPL browser, RMAL browser, and generated lowering
artifacts retain their original names and provenance.

Independent Browser
    ↓ direct successor
FKDB — Fighting Knowledge Decay Browser

## Inherited substrate

FKDB inherits the bounded browser pipeline already implemented and tested here:

- URL resolution;
- HTTP/HTTPS request planning;
- bounded HTTP response admission;
- local and network navigation state;
- pointer and keyboard activation;
- HTML tokenization handoff;
- DOM build handoff;
- layout, hit-map, raster, frame verification/admission, presentation;
- RMAPL → generated RMAL migration lineage;
- native RMAL/RMALC execution with explicit capability handoffs.

## FKDB purpose

FKDB adds a query/recovery layer whose job is to help a human ask:

- what did we know?
- what became disconnected?
- what still matters now?
- where did it come from?
- what relations made it meaningful?
- what failed?
- what can reconstruct it?
- what carrier can safely receive it?
- what remains unresolved?

The browser remains a browser. FKDB adds explicit knowledge-recovery policy above
the inherited transport/render/input substrate.

## First successor increment

1. fkdb_query.rmal — bounded knowledge-decay and cross-carrier policy kernel.
2. fkdb_bootstrap.rmal — FKDB orchestration around inherited browser handoffs.

The historical generated Independent Browser RMAL operator files are not rewritten.

## Invariants

DIRECT_SUCCESSOR != RETROACTIVE_RENAME
SOURCE_IDENTITY != CURRENT_PROJECT_IDENTITY
REPRESENTATION != MEANING
UNKNOWN != FALSE
UNRESOLVED != NEGATIVE
METHOD_TRANSFER != EVIDENCE_TRANSFER
RELATION != AUTHORITY
RECOVERY != REWRITE
FAILURE != DISCARD

## Claim ceiling

This increment establishes a bounded successor identity and executable policy fixtures.
It does not establish complete knowledge recovery, browser completeness, semantic truth,
or automatic cross-domain evidence transfer.
