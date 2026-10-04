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

### F8 — in-browser source/provenance inspection

- single bounded index match may expose a SOURCE page;
- SOURCE shows bounded carrier + provenance-relation projections;
- RECOVERY shows a bounded recovery synopsis;
- the full candidate record, source refs, provenance and recovery path remain in the JSON sidecar;
- multiple candidates produce no SOURCE or RECOVERY target;
- display truncation is explicit remainder, never silent replacement.

### F9 — WebAssembly Host Interoperability Framework

User-directed priority change: WebAssembly and modern Web technologies are now
first-class FKDB host capabilities, with explicit fallback paths for older systems.

Primary artifacts:

- `web/WASM_HIF.md` — architecture and standards normalization;
- `web/capabilities.json` — feature-detected capability/fallback contract;
- `web/fkdb-host.mjs` — executable host selector, JSPI boundary, Fetch/XHR and storage adapters;
- `web/index.html` — progressive modern-Web entry surface;
- `wasm/wit/0.3/fkdb-hif.wit` — primary native-async WIT contract;
- `wasm/wit/0.2/fkdb-hif.wit` — explicit-poll compatibility contract.

Modern-first execution ladder:

```text
WASM_COMPONENT_0_3
-> WASM_JSPI
-> WASM_PROMISE_HANDOFF
-> WASM_LEGACY_WEB
-> JS_MODERN_FALLBACK
-> JS_LEGACY_FALLBACK
-> NATIVE_RMAL_FALLBACK
```

Network ladder:

```text
WASI_HTTP_0_3
-> FETCH_STREAMS
-> FETCH
-> WASI_HTTP_0_2
-> XHR
-> NATIVE_RMAL_HTTP_TLS
```

Persistence ladder:

```text
WASI_FILESYSTEM_0_3
-> OPFS
-> INDEXED_DB
-> WASMFS_OR_IDBFS
-> MEMORY
```

JSPI is used only when runtime feature detection confirms
`WebAssembly.Suspending` and `WebAssembly.promising`. When absent, FKDB uses an
explicit Promise/outer-controller handoff and does not fake synchronous Wasm semantics.

The Wasm-HIF framework is indexed as `FKDB-HIF-001`, so FKDB can recover it from a
human query such as `WebAssembly`.

### F10 Plan A — Core Local Tool Bridge

The approved local-first tool architecture now has a verified shared substrate before any
vendor-specific adapter is admitted.

Implemented:

- obligation-driven host capability graph with explicit execution receipts;
- distinct `componentNative03` and `componentBrowserTranspiled03` capabilities;
- compatibility projection preserving existing `selectHostProfile()` callers;
- portable `ToolCarrier` and `ToolBundle` interchange contracts with bounded,
  deterministic validation and SHA-256 payload identity;
- loopback-only Local Tool Bridge serving FKDB and local-tool endpoints same-origin;
- per-launch capability token for mutating/run operations;
- exact-origin enforcement, no wildcard CORS, no token in URLs/public receipts;
- deny-by-default process execution with explicit executable/subcommand/root grants and
  `shell=False`;
- path traversal and symlink-escape rejection;
- native-async WASI 0.3 `local-tools` WIT contract plus 0.2 explicit-poll compatibility;
- modern browser local-tool client using relative same-origin requests only;
- bounded `TOOLS` page in the inherited Independent Browser surface.

Default production policy remains:

```text
NETWORK_POLICY = LOOPBACK_ONLY
read_roots = []
write_roots = []
processes = []
environment_allowlist = []
```

The browser remains valid when the Local Tool Bridge is absent:

```text
LOCAL_TOOL_BRIDGE_UNAVAILABLE != FKDB_UNAVAILABLE
```

Verified by the dedicated browser/RMAL matrix on Linux and Windows after Task 5.

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

`TOOLS` and `LINEAGE` are inspectable side routes that return to FKDB.

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

1. Vendor adapters remain intentionally absent: Mathbox/Superpowers, Zotero, Wolfram,
   local Supabase, and portable SciSpace/Consensus/Exa/Linear/Railway ingestion are later
   plans.
2. No remote synchronization is required or implemented.
3. Actual Component Model/WASI toolchain compilation of the WIT packages remains
   unproven.
4. The default Local Tool Bridge process allowlist is intentionally empty.
5. Richer free-text interpretation beyond exact token matching remains open.
6. Any result ordering must not promote evidence by resemblance.
7. Scrolling and larger-page layout remain open.
8. Native/RMAL migration of remaining FKDB-specific outer-controller/index logic remains
   open.

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

Build **F10 Plan B — local workflow/computation adapters** on top of the verified bridge:
Mathbox and Superpowers local-file carriers first, followed by Zotero local/portable and
Wolfram local-process adapters. Each adapter must emit ToolCarrier and remain independently
usable without remote APIs.

## Claim ceiling

FKDB is now a functioning bounded successor surface with exact live-query routing, a bounded provenance-preserving local source index, in-browser source/recovery inspection for unambiguous matches, a tested modern-first WebAssembly/Web host interoperability layer, and a verified local-first ToolCarrier/Local Tool Bridge substrate.
It is not yet a complete knowledge-recovery browser, a semantic search engine, or
evidence authority.
