# FKDB — CURRENT

**Project:** Fighting Knowledge Decay Browser  
**Project ID:** FKDB  
**Named:** 2026-10-04  
**Lineage:** DIRECT_SUCCESSOR of Independent Browser  
**Working PR:** #116  
**Status:** BUILDING / BOUNDED VERIFIED INCREMENTS

## Current purpose

Turn the Independent Browser substrate into a browser for finding, reconnecting,
reconstructing, comparing and carrying knowledge without silently losing source
identity, provenance, consequential relations, failures, uncertainty or recovery paths.

## Inherited browser substrate

The predecessor currently supplies bounded, tested:

- local and network URL resolution;
- pointer and keyboard link activation;
- HTTP/HTTPS request planning and transport handoffs;
- bounded HTTP response admission;
- HTML tokenization;
- DOM construction;
- layout and hit-map construction;
- raster/frame verification and admission;
- presentation carrier;
- RMAPL -> generated RMAL migration with differential checks;
- native RMAL/RMALC orchestration.

Historical Independent Browser artifacts retain predecessor identity.

## FKDB increments currently on PR #116

### F0 — identity and direct lineage

- `rmal-browser/FKDB_IDENTITY.md`
- README direct-successor header
- no retroactive rename of predecessor artifacts

### F1 — bounded native query policy

- `rmal-browser/fkdb_query.rmal`
- knowledge-decay status gate
- cross-carrier admission gate
- continuation-cost gate
- native C23 execution receipt

### F2 — successor orchestration

- `rmal-browser/fkdb_bootstrap.rmal`
- NEED -> HISTORY -> DECAY -> RECOVER -> RELATE -> browser transport/render -> RETURN
- native C23 handoff host

### F3 — human-visible local surface

- HOME / HISTORY / RECOVER / LINEAGE pages
- pointer and keyboard navigation through inherited browser semantics
- live launcher reuses `interact_independent_browser.py`

### F4 — typed page/recovery manifest

- page identity, role, purpose, relations, provenance and recovery path
- direct-successor metadata
- relation-to-link parity gate

### F5 — structured current-query projection

- `state/current_query.json`
- deterministic page projection
- CI fails on stale committed pages

### F6 — bounded live query input

- exact source-preserving native RMAL query router;
- MATCH / NO_MATCH / UNRESOLVED remain distinct;
- exact declared routes: HISTORY / DECAY / RECOVER / RELATE / LINEAGE / FKDB;
- bounded comparison cost reported in the native receipt;
- unresolved queries do not become false or arbitrary matches.

### F7 — bounded local source/history index

- local typed source records with source refs, provenance, evidence status, recovery path, carrier and relations;
- deterministic token matching only;
- raw human query retained;
- explicit scan cost;
- multiple candidates remain multiple;
- NO_MATCH is bounded to the local index;
- unsupported query material remains UNRESOLVED;
- unresolved live queries fall through to the index only after exact RMAL routing;
- bounded RESULT page plus authoritative full-result sidecar JSON.

Retained failure:

- F6-001 — page projection rejected an over-width display string; semantic intent was preserved while only the display projection was shortened.

## Current query progression

```text
NEED
-> HISTORY
-> DECAY
-> RECOVER
-> RELATE
-> RETURN
```

Visible progression:

```text
FKDB
-> HISTORY
-> DECAY
-> RECOVER
-> RELATE
-> FKDB
```

`LINEAGE` is an inspectable side route that returns to FKDB.

## Current invariants

```text
DIRECT_SUCCESSOR != RETROACTIVE_RENAME
SOURCE_IDENTITY != CURRENT_PROJECT_IDENTITY
REPRESENTATION != MEANING
UNKNOWN != FALSE
UNRESOLVED != NEGATIVE
FAILURE != DISCARD
RECOVERY != REWRITE
RELATION != AUTHORITY
METHOD_TRANSFER != EVIDENCE_TRANSFER
QUERY_STATE_PROJECTION != QUERY_EXECUTION
DISPLAYED_STATUS != VERIFIED_TRUTH
```

## Verified boundary

Dedicated browser/RMAL CI verifies FKDB check/compile/native execution together
with the inherited browser tests. Repository-wide Decision Field CI is an additional
independent gate.

Passing software tests establish only the bounded implemented behavior.

## Current remainder

1. Live external/history ingestion beyond the bounded local source index.
2. Live cross-carrier candidate retrieval with provenance.
3. Human-readable source/provenance/recovery inspection inside the browser.
4. Richer free-text interpretation beyond exact token matching.
5. Any result ordering must not promote evidence by resemblance.
6. Scrolling and larger-page layout.
7. Native/RMAL migration of remaining FKDB-specific outer-controller/index logic.

## F6 — bounded live query input

Implemented bounded exact query routing:

```text
human query
-> preserved source expression
-> bounded RMAL query routing
-> explicit MATCH / NO_MATCH / UNRESOLVED
-> selected FKDB surface
-> provenance + remainder
```

Current exact recognized intents: `HISTORY`, `DECAY`, `RECOVER`, `RELATE`, `LINEAGE`, `FKDB`.
Empty input returns `NO_MATCH`; all other text returns `UNRESOLVED`.

Constraints preserved:

- query text remains source-authoritative;
- routing cannot claim semantic truth;
- no network/history search is hidden inside the router;
- UNKNOWN and UNRESOLVED remain distinct;
- routing cost is explicit;
- every selected result retains the route that selected it.

## Next one-degree step

Build **F8 — in-browser source/provenance inspection**. A single bounded index match may expose a human-readable inspection page, but the full sidecar remains authoritative. Multiple candidates may not be silently ranked or collapsed.

## Claim ceiling

FKDB is now a functioning bounded successor surface with exact live-query routing and a bounded provenance-preserving local source index.
It is not yet a complete knowledge-recovery browser, a semantic search engine, or
evidence authority.
