# FKDB — CURRENT

**Project:** Fighting Knowledge Decay Browser  
**Project ID:** FKDB  
**Named:** 2026-10-04  
**Lineage:** DIRECT_SUCCESSOR of Independent Browser  
**Merged lineage:** PR #116 at `f3573799185df44b03a1eb1e333bb0721a0805a1`\
**Working PR:** #119 (`fkdb-plan-c-rollout`)\
**Integrated main:** `51b30bd28239b29eab68bf64c472d68923827166`\
**Status:** BUILDING / PLAN C REPAIR CLOSEOUT PENDING

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

## FKDB increments inherited from PR #116 and continued on PR #119

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
- runtime-probed `localToolBridge` capability; `LOCAL_TOOL_ACCESS` selects
  `LOCAL_TOOL_BRIDGE` only when that capability is present;
- compatibility projection preserving existing `selectHostProfile()` callers;
- portable `ToolCarrier` and `ToolBundle` interchange contracts with bounded,
  deterministic validation and SHA-256 payload identity;
- ToolBundle attachments are resolved inside the bundle root and verified against their
  declared size and SHA-256 bytes; symlink escape and aggregate bundle-size overflow fail
  closed;
- loopback-only Local Tool Bridge serving FKDB and local-tool endpoints same-origin;
- per-launch capability token for mutating/run operations;
- exact-origin enforcement, no wildcard CORS, no token in URLs/public receipts;
- deny-by-default local-process grants with exact executable/subcommand/root validation
  and `shell=False` semantics reserved for an isolation-capable backend;
- the portable stdlib bridge marks granted local processes `DEGRADED` and returns
  HTTP 503 before execution while required process network isolation is unavailable
  (and while any requested nonzero memory limit cannot be enforced);
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

Verified by the dedicated browser/RMAL matrix on Linux and Windows after the Plan A
security fix pass: 48/48 tests passed on both platforms.

### F10 Plan B — Local workflow/computation adapters

Plan B is implemented and verified as a read-only/local-artifact adapter layer above the
Plan A Local Tool Bridge. It adds no new process execution authority.

Implemented:

- generic bounded `LocalAdapterRegistry` plus token-gated
  `POST /fkdb-tool-bridge/v1/collect`;
- default production adapter policy remains empty/opt-in;
- per-adapter max-file and max-byte bounds with explicit PARTIAL remainder;
- all returned adapter artifacts are validated as ToolCarrier before admission;

**Mathbox**
- read-only `.mathbox/config.json` and numbered `.mathbox/events/*.json` collection;
- deterministic lexical event ordering;
- invalid JSON and collection limits remain explicit remainder;
- authority/evidence boundary:
  `MATHBOX_RECORDED_STATE_ONLY` /
  `MECHANICAL_LEDGER_RECORD_NOT_PROOF_AUDIT`.

**Superpowers**
- bounded local `docs/superpowers/specs/*.md`,
  `docs/superpowers/plans/*.md`, and progress-ledger collection;
- raw Markdown bytes and hashes are preserved;
- workflow records remain
  `WORKFLOW_ARTIFACT_ONLY` /
  `WORKFLOW_STATE_NOT_CLAIM_VERIFICATION`.

**Zotero**
- read-only Zotero Desktop local API adapter at literal loopback only;
- bounded GET search with URL encoding and redirect denial;
- no API key, no connector writes, no attachment/fulltext/file-view retrieval;
- preserves Zotero item identity separately from citation/BibTeX keys;
- portable raw BibTeX, RIS, and CSL-JSON artifact collection;
- result-limit truncation returns PARTIAL + explicit remainder rather than silent loss.

**Wolfram**
- bounded read-only `.wl`, `.m`, and `.nb` artifact collection;
- binary notebook bytes are preserved/hash-identified;
- `wolframscript` discovery is probe-only;
- a discovered executable is reported DEGRADED because process isolation is unavailable;
- Plan B does not execute Wolfram locally.

**Wasm-HIF / browser**
- vendor-neutral `collect-request` / `collection-result` contract;
- WASI 0.3: native async `collect-local`;
- 0.2 compatibility: explicit collection-operation polling;
- WIT contains no vendor-specific Mathbox/Superpowers/Zotero/Wolfram names;
- browser TOOLS status renders only the safe descriptor projection:
  tool ID, locality, state, capabilities, unresolved requirements;
- arbitrary adapter fields, local paths, secrets and remote-login prompts are not exposed.

Verified at implementation head `c570a881686373badb4f4313679c06a1af366b3f`:

```text
Linux   53 / 53 PASS
Windows 53 / 53 PASS
Broad Decision Field audit PASS
```

Plan B boundaries:

```text
ADAPTER_COLLECTION != CLAIM_VERIFICATION
MATHBOX_RECORDED_STATE != MATHEMATICAL_PROOF
SUPERPOWERS_WORKFLOW_STATE != EVIDENCE_PROMOTION
ZOTERO_LOCAL_API != ZOTERO_CLOUD
PORTABLE_ZOTERO_IMPORT != LIVE_SYNC
WOLFRAM_EXECUTABLE_DISCOVERY != EXECUTION_AUTHORITY
COLLECTED_TOOLCARRIER != FKDB_SOURCE_INDEX_ADMISSION
```

### F10 Plan C — local infrastructure adapters (implemented; repair closeout pending)

Supabase and Railway adapters and their dedicated tests are already implemented.
PR #119 retains that implementation while addressing the secret-path failures recorded
by PR #118. No hosted-service dependency, database connection, vendor CLI execution,
or live deployment query is added.

- Supabase collects local configuration, migrations, seed SQL and Edge Function
  TS/JSON artifacts. Carriers retain `SUPABASE_LOCAL_PROJECT_ARTIFACT_ONLY`,
  `CONFIG_OR_MIGRATION_NOT_APPLIED_STATE` and `runtime_state_observed = false`.
- Railway collects checked-in IaC/legacy/build configuration and explicitly requested
  portable snapshots. Carriers retain `RAILWAY_REPOSITORY_ARTIFACT_ONLY`,
  `DEPLOYMENT_ARTIFACT_NOT_LIVE_DEPLOYMENT_STATE` and `live_state_observed = false`.
- Railway IaC/deprecation/cutoff labels are repository metadata, not independently
  verified vendor policy. Legacy configuration remains recoverable.
- Production adapters, read/write roots, process grants and environment allowlist
  remain empty. Adapter opt-in is enforced at the token/origin-gated HTTP collection
  boundary; internal registry `collect()` calls are not an authorization boundary.

Historical receipts remain scoped to the revisions actually executed:

| Gate | Exact revision | Observed result |
| --- | --- | --- |
| Pre-merge Linux / Windows | `461a1aab4487a33ada2eee6102cc87eb02840f15` | 55/55 CTest targets on each platform |
| PR #118 Linux / Windows reruns | `f3573799185df44b03a1eb1e333bb0721a0805a1` | 55/55 CTest targets on each platform |
| PR #118 broad audit rerun | `4a05785e4376c558ed7ad761f89db9dd241bca7b` | PASS |
| PR #118 supplemental Linux probes | Exact source blobs from `4a05785...` | 8 methods pass; 2 fail (4 failed assertions/subtests) |
| PR #119 Linux / Windows | `2a7180c7e26117e2834603ac0be82fda186ec016` | 57/57 CTest targets on each platform |
| PR #119 broad audit | `2a7180c7e26117e2834603ac0be82fda186ec016` | 356 unittest tests and all evidence/stress steps PASS |

The older green tests did not cover the retained synthetic negative witnesses:

- `PLAN-C-SECRET-001`: Railway admitted explicitly requested `.env.json`,
  `service_role.json` and `secrets.txt` with their raw synthetic payloads.
- `PLAN-C-SECRET-002`: Supabase admitted
  `supabase/functions/secrets/credentials.json`; basename-only filtering did not
  exclude its credential-like directory.
- `PLAN-C-MATRIX-001`: PR #118 had no dedicated Linux/Windows execution at its
  newer `4a05785...` base. PR #119 later verified its own exact `2a7180c...` head;
  those receipts do not verify the repaired head or the integration with newer main.

No real credentials were used in these probes. Repair acceptance requires secret-path
exclusion before payload reads, retained negative regressions, and fresh dedicated
Linux/Windows matrices plus the current broad audit at one exact final head. Plan B,
portable Plan D and Plan E overlay behavior must remain green in the same executions.
Final repaired-head receipts are pending; Plan C closeout is not claimed.

The supplemental controls established deterministic raw-byte/hash preservation,
read-only fixture behavior, requested-root symlink/traversal rejection, static-file
file/byte limits with explicit PARTIAL remainder, and invalid-UTF-8 remainder.
They did not establish bounded directory enumeration, concurrent-growth safety or
race-hard file reads. Secret-name/path exclusion is not content-based credential
scanning and does not establish that arbitrary admitted artifacts contain no secrets.

The full historical record, source hashes, job links and runnable failure witness remain
in the [Plan C progress ledger](../../docs/superpowers/plans/2026-10-05-fkdb-f10-plan-c-local-infrastructure-adapters-progress.md).

### F10 Plan D — portable research/project adapters (implemented)

One `PortableProviderAdapter` reads user-selected JSON envelopes for SciSpace,
Consensus, Exa and Linear under an allowed root. Provider identity and record fields
are retained with separate discovery/synthesis/workflow authority scopes and
`PORTABLE_PROVIDER_RECORD_UNVERIFIED`. Each record is serialized as canonical JSON
for its carrier payload and SHA-256; original export-file formatting is not preserved.
Production policy remains opt-in, and no network, authentication or synchronization is
required. File-byte and returned-record limits remain explicit.

### F10 Plan E — ToolCarrier admission and external index overlay (implemented helpers)

The callable admission path validates ToolCarriers and retains source identity,
provenance, payload, authority scope and evidence status without evidence promotion.
Contradictions require the same explicitly declared subject key and different claim
values; they remain unresolved. External records use the `EXT-` namespace, reject ID
collisions and overlay the local query index without modifying canonical static records.

Tests cover admission and queryable overlays. This is not an automatic browser or HTTP
collection-to-index workflow. Admission limits each payload to 1 MiB; index terms have a
configurable per-record ceiling (32 by default). No aggregate carrier-count bound or
full-payload search guarantee is claimed.

Plan D/E implementation receipts and the pending final-head gate are recorded in the
[portable/admission progress ledger](../../docs/superpowers/plans/2026-10-08-fkdb-f10-plan-d-e-portable-admission-progress.md).

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

1. ToolCarrier admission and collision-safe external source-index overlay helpers are implemented.
2. Supabase and Railway Plan C repair closeout remains pending fresh exact-head
   negative regressions, Linux/Windows matrices and the current broad audit.
3. Portable SciSpace, Consensus, Exa and Linear Plan D adapters are implemented as
   offline JSON provider envelopes; final integrated-head verification remains pending.
4. No remote synchronization is required or implemented.
5. Zotero writes, fulltext, attachment-file URL reads and connector mutations remain outside
   the verified boundary.
6. Wolfram local execution remains fail-closed until a process-isolation backend can enforce
   the declared policy.
7. Actual Component Model/WASI toolchain compilation of the WIT packages remains unproven.
8. Richer free-text interpretation beyond exact token matching remains open.
9. Any result ordering must not promote evidence by resemblance.
10. Scrolling and larger-page layout remain open.
11. Native/RMAL migration of remaining FKDB-specific outer-controller/index logic remains open.

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

Close the **Plan C secret-path repair and final-head verification gate** while preserving
implemented Plan D portable providers and Plan E admission/index helpers:

- retain the PR #118 negative witnesses and exclude secret-like paths before payload reads;
- execute dedicated Linux/Windows matrices and the current broad Decision Field audit
  at the same final head, including Plan B, Plan D/E and the new regressions;
- keep hosted Supabase, live Railway state, runtime/database queries and cloud sync
  outside the claim boundary.

After those gates pass, return to the **human-level intellect design questions** with the
verified local carrier substrate. Component Model toolchain compilation, richer free-text
interpretation, optional synchronization, process isolation, scrolling/larger-page layout,
further native/RMAL migration and an automatic collection-to-index workflow remain open.

## Claim ceiling

FKDB is now a functioning bounded successor surface with exact live-query routing, a
bounded provenance-preserving local source index, in-browser source/recovery inspection
for unambiguous matches, a tested modern-first WebAssembly/Web host interoperability
layer and a verified local-first ToolCarrier/Local Tool Bridge substrate with Plan B
artifact adapters. Supabase/Railway, portable SciSpace/Consensus/Exa/Linear adapters
and ToolCarrier admission/index helpers are implemented with historical exact-head
receipts. The secret-path repairs and integration with newer main still require the
same final-head verification before Plan C closeout or merge.
It is not yet a complete knowledge-recovery browser, a semantic search engine, or
evidence authority.
