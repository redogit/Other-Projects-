# FKDB — Fighting Knowledge Decay Browser

FKDB is the **direct successor** of the Independent Browser. It received its first
canonical project name on 2026-10-04. Historical Independent Browser/RMAPL/RMAL
artifacts below retain their original names and remain predecessor evidence.

Current successor surfaces:

- `FKDB_IDENTITY.md` — identity, lineage, inherited substrate and claim ceiling;
- `fkdb_query.rmal` — bounded native RMAL knowledge-decay/cross-carrier query policy;
- `fkdb_bootstrap.rmal` — FKDB orchestration layered around inherited browser stages;
- `fkdb_rmal_host.c` / `fkdb_query_host.c` — native RMAL execution receipts.

Successor relation:

```text
Independent Browser
    ↓ direct successor
FKDB — Fighting Knowledge Decay Browser
```

The generated Independent Browser operator ports are intentionally not renamed:
`DIRECT_SUCCESSOR != RETROACTIVE_RENAME`.

---
# Independent Browser — RMAL / RMALC bootstrap

This directory is the first migration rung away from the Python-hosted RMAPL
runtime used by the independent browser.

## Authority

RMAL and RMALC are **not copied into this repository**.

The build pins the canonical toolchain:

- repository: `redogit/DnD`
- branch lineage: `master`
- exact commit: `57786dd85cb13c4a8f657ae4a66ca6d4058854fa`
- RMAL / RMALC: 3.1
- implementation: ISO C23

`CMakeLists.txt` fetches that exact commit and fails if the resulting Git head
does not match the pin.

## What this proves

`browser_bootstrap.rmal` runs browser orchestration in the canonical RMAL VM.
The host binds one opt-in native capability, `BrowserHandoff(string)`, through
RMAL's stable C callback ABI.

The checked sequence covers:

```text
render:
  HTML_TOKENIZE
  DOM_BUILD
  LAYOUT
  HIT_MAP
  RASTER
  FRAME_VERIFY
  CAMERA_PACK
  FRAME_ADMIT

network:
  URL_RESOLVE
  HTTPS_PLAN
  NATIVE_TLS
  HTTP_RESPONSE_ADMIT

render again
PRESENT
```

The RMAL program owns the order and assertions. The C host only acknowledges
the explicit capability boundary and fails on any unexpected handoff.

This path executes without Python.

## Build

```sh
cmake -S "Decision Field Operator Lab/rmal-browser" \
      -B build/rmal-browser \
      -G Ninja \
      -DCMAKE_C_COMPILER=clang \
      -DCMAKE_BUILD_TYPE=Release
cmake --build build/rmal-browser --parallel
ctest --test-dir build/rmal-browser --output-on-failure
```

## Migration boundary

This is deliberately **not** a claim that arbitrary RMAPL already compiles to
RMAL.

```text
CURRENT BROWSER:
RMAPL source -> Python RMAPL parser/VM -> native carriers

BOOTSTRAP NOW ADDED:
RMAL source -> RMALC -> native RMAL VM -> explicit browser handoffs

NEXT:
RMAPL operator lowering -> RMAL source -> RMALC -> native RMAL VM
                                              -> existing native carriers

LATER:
RMAPL lowering implemented in RMAL itself
```

Claim ceilings:

- `RMAL_BOOTSTRAP != FULL_RMAPL_LOWERING`
- `NATIVE_RMAL_VM != SELF_HOSTED_RMAPL_COMPILER`
- `HANDOFF_SEQUENCE_VERIFIED != BROWSER_SEMANTIC_EQUIVALENCE`
- `PINNED_TOOLCHAIN != FORKED_TOOLCHAIN_AUTHORITY`


## First semantic migration: HTTP request planning

`browser_http_plan.rmal` ports the bounded semantics of
`independent_browser_http.rmapl::browser_http_plan` onto native RMAL.

The RMAL implementation owns:

- HTTP -> port 80 / `native-http-transport-pending`;
- HTTPS -> port 443 / `native-tls-transport-pending`;
- exact HTTP/1.1 GET request construction;
- the 262144-byte response bound;
- unsupported-scheme refusal.

`browser_rmal_http_plan_host` executes that logic under the native RMAL VM and
emits a Python-free receipt.

`verify_http_plan_equivalence.py` then uses the existing RMAPL planner only as
a differential oracle and requires equal host, port, residual kind/detail,
response bound and exact request bytes for HTTP and HTTPS fixtures.

```text
RMAPL planner ───────┐
                     ├─ exact bounded equivalence check
RMAL/RMALC planner ──┘

RMAL runtime path: no Python
Differential verifier: Python test oracle only
```

This advances the migration boundary:

```text
before: browser orchestration only in RMAL
now:    browser orchestration + HTTP request-planning semantics in RMAL
next:   lower additional RMAPL operator families, then automate lowering
```

Additional ceiling:

- `BOUNDED_HTTP_PLAN_EQUIVALENCE != GENERAL_RMAPL_LOWERING`
- `PYTHON_DIFFERENTIAL_ORACLE != RMAL_RUNTIME_DEPENDENCY`


## Automated lowering family: HTTP request planner

The HTTP planner is no longer maintained twice by hand.

Canonical semantic source:

```text
examples/independent_browser_http.rmapl
  OPERATOR browser_http_plan
```

Lowering contract:

```text
browser_http_plan.lowering.json
        +
lower_rmapl_http_plan.py
        ↓
browser_http_plan.rmal
        ↓
RMALC 3.1
        ↓
native RMAL VM
```

`browser_http_plan.rmal` is a generated artifact. The lowerer consumes the
immutable RMAPL parser IR and accepts only the admitted planner family. It fails
closed if the operator introduces a new opcode, branch label, input path,
output path, residual shape, request-construction chain, or return shape.

CI requires all three layers simultaneously:

1. committed generated RMAL == lowerer output from current RMAPL;
2. generated RMAL parses/compiles/runs under pinned canonical RMALC;
3. native RMAL output remains exactly equivalent to the current RMAPL planner
   for the bounded HTTP/HTTPS fixtures.

Python is currently used to perform this **build-time lowering and differential
verification**. It is not used by the generated RMAL runtime path.

```text
BUILD_TIME_PYTHON != RUNTIME_PYTHON
GENERATED_RMAL != PROVED_GENERAL_LOWERING
BOUNDED_LOWERING_FAMILY != ALL_RMAPL
```

The next migration obligation is to expand the fail-closed lowering families,
then implement the lowerer itself in RMAL so the final build-time Python
dependency can be retired without discarding the RMAPL evidence lineage.


## Generated HTTP response-admission family

`browser_http_response.rmal` is generated from
`independent_browser_http.rmapl::browser_http_response_admit`.

RMAL owns the policy:

- require the bounded `HTTP/1.1 200 ` status prefix;
- scan for the first `CRLF CRLF` header/body delimiter;
- require a non-empty body;
- request bounded UTF-8 projection of that body;
- choose admitted vs invalid residual/consequence;
- declare the admitted state-transition contract:
  append current URL to history, promote pending URL, clear navigation
  transients, and clear render state before the next HTML-tokenization pass.

The native host does **not** decide any of those. It exposes only the mechanical
operations RMAL 3.1 currently lacks because its executable value domain has no
byte-buffer kind:

```text
BrowserResponseSelect(test fixture)
BrowserResponseLength()
BrowserResponseByte(index)
BrowserResponseUtf8(start, length)
BrowserResponseResult(...)   # records RMAL's decision
```

The response migration is checked against four byte streams:

- valid 200 + HTML body;
- 404 response;
- 200 response missing `CRLF CRLF`;
- 200 response with an empty body.

Differential verification compares RMAL against the current RMAPL operator for
status, body bytes, residual kind/detail, consequence, history append, pending
URL promotion, navigation clearing and render-state clearing.

```text
BYTE_MECHANICS_CALLBACKS != HTTP_POLICY
BOUNDED_RESPONSE_ADMISSION != GENERAL_HTTP_PARSER
PYTHON_DIFFERENTIAL_ORACLE != RMAL_RUNTIME_DEPENDENCY
```


## Generated URL-resolution family

`browser_url_resolve.rmal` is generated from
`independent_browser_url.rmapl::browser_url_resolve`.

RMAL owns the bounded URL policy:

- `rmapl://local/<page>` absolute local resolution;
- relative local page IDs;
- HTTP and HTTPS scheme recognition;
- host extraction;
- default network path `/`;
- path/canonical URL construction;
- local vs network routing;
- malformed `:`, `/`, `?`, `#`, space handling according to the
  existing bounded RMAPL contract;
- pending-href normalization for local navigation;
- residual and consequence selection.

The native URL host exposes only input mechanics:

```text
BrowserUrlSelect(test fixture)
BrowserUrlRaw()
BrowserUrlLength()
BrowserUrlByte(index)
BrowserUrlChar(index)
BrowserUrlResult(...)    # records RMAL's decision
```

Differential fixtures cover:

- absolute local URL;
- relative local page ID;
- HTTPS path;
- HTTP URL with default `/` path;
- malformed query-bearing network URL;
- empty local target;
- empty href.

The differential oracle requires field-for-field equality for pending URL,
pending href, networkRequired, residual and consequence.

```text
BYTE_MECHANICS_CALLBACKS != URL_POLICY
BOUNDED_URL_RESOLUTION != WHATWG_URL_CONFORMANCE
PYTHON_DIFFERENTIAL_ORACLE != RMAL_RUNTIME_DEPENDENCY
```


## Generated input-activation family

`browser_input_activate.rmal` is generated from the paired RMAPL operators:

- `browser_pointer_activate`
- `browser_keyboard_activate`

They migrate together because both consume the same hit-map/focus state.

RMAL owns:

- pointer rectangle hit-testing;
- first matching link selection;
- pointer miss behavior;
- TAB focus advancement and wrapping;
- TAB no-target behavior;
- ENTER focused-link activation;
- invalid focus handling;
- unsupported keyboard handling;
- pendingHref, lastHit, focusIndex and focusedHref mutations;
- residual and consequence selection.

The native host exposes only input/hit-map fields and records RMAL's result.

Differential fixtures cover second-hit pointer activation, pointer miss, first TAB,
TAB wrap, TAB with no links, valid ENTER, invalid ENTER and unsupported key.

```text
HIT_MAP_ACCESS_CALLBACKS != INPUT_POLICY
BOUNDED_LINK_ACTIVATION != GENERAL_INPUT_SYSTEM
PYTHON_DIFFERENTIAL_ORACLE != RMAL_RUNTIME_DEPENDENCY
```

## FKDB local progression surface

FKDB now has a bounded local browser surface under `Decision Field Operator Lab/fkdb/pages`.
`manifest.json` is the typed registry for page identity, provenance, recovery path,
declared relations, direct-successor lineage, and the current query progression:

```text
NEED -> HISTORY -> DECAY -> RECOVER -> RELATE -> RETURN
```

The live launcher intentionally reuses the Independent Browser driver rather than
duplicating browser semantics:

```sh
python "Decision Field Operator Lab/tools/interact_fkdb.py" \
  --presenter <path-to-win32-camera-presenter>
```

Optional `--http-carrier` and `--tls-carrier` arguments pass through to the inherited
live browser driver. The FKDB launcher performs manifest/page binding only.

Current local progression:

```text
FKDB -> HISTORY -> DECAY -> RECOVER -> RELATE -> FKDB
```

`LINEAGE` is an inspectable direct-successor side route that returns to FKDB.

Current boundaries:

```text
FKDB_PAGE_MANIFEST != KNOWLEDGE
LOCAL_FKDB_SURFACE != COMPLETE_KNOWLEDGE_RECOVERY
LAUNCHER_BINDING != BROWSER_SEMANTICS
RELATION != EVIDENCE_TRANSFER
```

### FKDB query-state projection

`Decision Field Operator Lab/fkdb/state/current_query.json` is the current bounded
query-state carrier. `tools/build_fkdb_pages.py` deterministically projects its
human-visible fields into the local FKDB pages. CI requires the committed pages to
match that projection exactly.

```text
current_query.json
    -> bounded projection
FKDB local pages
    -> inherited Independent Browser renderer
human-visible surface
```

This is deliberately not yet free-text query execution:

```text
QUERY_STATE_PROJECTION != QUERY_EXECUTION
DISPLAYED_STATUS != VERIFIED_TRUTH
```

### FKDB bounded live query

`fkdb_live_query.rmal` preserves the exact human query text supplied by the host and
performs only bounded exact intent routing. Current recognized queries are:

```text
HISTORY -> history
DECAY   -> decay
RECOVER -> recover
RELATE  -> relate
LINEAGE -> lineage
FKDB    -> fkdb
```

Empty input returns `NO_MATCH`; all other text returns `UNRESOLVED` and remains
on the FKDB current-common-point page.

A built native query host can be connected to the live launcher:

```sh
python "Decision Field Operator Lab/tools/interact_fkdb.py" \
  --presenter <path-to-presenter> \
  --query "HISTORY" \
  --query-host <build-path-to-fkdb_live_query_host>
```

The native receipt reports route, bounded comparison cost and source preservation.

```text
EXACT_INTENT_ROUTING != SEMANTIC_SEARCH
UNRESOLVED != NO_MATCH
QUERY_ROUTE != EVIDENCE
```

## FKDB WebAssembly / modern Web first-class host

FKDB Wasm-HIF makes WebAssembly and modern Web APIs first-class execution carriers while
retaining the Independent Browser / native RMAL path as an explicit fallback.

Primary host selection is capability based, not user-agent based:

```text
WASM_COMPONENT_0_3
-> WASM_JSPI
-> WASM_PROMISE_HANDOFF
-> WASM_LEGACY_WEB
-> JS_MODERN_FALLBACK
-> JS_LEGACY_FALLBACK
-> NATIVE_RMAL_FALLBACK
```

Primary typed interface: WIT/WASI 0.3 native async (`async func`, `stream<T>`,
`future<T>`). A separate 0.2-era WIT compatibility package uses explicit operation
resources/polling instead of pretending native async exists.

Browser I/O prefers Fetch/Streams and OPFS/IndexedDB. JSPI is feature-detected; without
JSPI, async Wasm work must pass through the explicit FKDB continuation/outer-controller
boundary. Legacy XHR, Emscripten filesystem adapters, and the native RMAL HTTP/TLS carrier
remain declared fallbacks.

See:

- `../fkdb/web/WASM_HIF.md`
- `../fkdb/web/capabilities.json`
- `../fkdb/web/fkdb-host.mjs`
- `../fkdb/wasm/wit/0.3/fkdb-hif.wit`
- `../fkdb/wasm/wit/0.2/fkdb-hif.wit`

```text
FALLBACK != SILENT_SEMANTIC_WEAKENING
CANONICAL_ABI_TRANSLATION != EVIDENCE_TRANSFER
ASYNC_RESUME != SUCCESS
NETWORK_RESPONSE != ADMITTED_KNOWLEDGE
```

## FKDB F10 core Local Tool Bridge

FKDB's local tool substrate is now implemented above Wasm-HIF without requiring any
vendor cloud API.

```text
FKDB
-> obligation-driven capability graph
-> Local Tool Bridge
-> ToolCarrier
-> local files / allowlisted local processes / localhost / portable artifacts
```

The capability graph distinguishes native Component Model 0.3 hosts from browser-
transpiled Component execution while preserving the older host-profile projection for
existing callers. `LOCAL_TOOL_ACCESS` now selects a runtime-probed
`LOCAL_TOOL_BRIDGE` path only when that capability is actually present.

The portable ToolCarrier boundary requires source identity, version, provenance,
authority scope, evidence status, obligation, cost, loss, remainder and recovery path.
ToolBundle imports are bounded and reject duplicate carrier IDs and payload hash
mismatches. Attachment metadata is checked against the referenced bytes: the resolved
file must remain inside the bundle root, match declared size and SHA-256, and fit inside
the aggregate bundle-byte bound.

The stdlib-only Local Tool Bridge:

- binds literal loopback only;
- serves FKDB and bridge endpoints same-origin;
- requires exact Origin plus `X-FKDB-Bridge-Token` for import/run mutations;
- suppresses request logging so the token is not copied into logs;
- rejects path/symlink escape outside allowed roots;
- denies all local processes unless explicitly granted;
- validates granted executable/subcommand/root identity without shell interpolation;
- fails closed before process execution while the portable bridge cannot enforce
  `LOOPBACK_ONLY` for the child process, or when a requested nonzero memory limit lacks
  an enforcement backend;
- reports such process adapters as `DEGRADED` with explicit unresolved requirements;
- validates ToolCarrier before admission.
  
An isolation-capable future backend may execute the already-validated argv with
`shell=False` and return an execution ToolCarrier, but the current portable stdlib
bridge does not pretend that allowlisting alone is isolation.

Default policy grants no file roots or processes.

Browser discovery is read-only by default. `local-tool-client.mjs` uses only relative
same-origin bridge paths. If the bridge is absent the browser reports
`LOCAL_TOOL_BRIDGE_UNAVAILABLE`; it does not prompt for a remote login.

The bounded Independent Browser surface now exposes:

```text
FKDB -> TOOLS -> FKDB
```

alongside the existing knowledge-decay progression.

Wasm-HIF now defines the generic `local-tools` interface in both tracks:

- WASI 0.3: native async `import-artifact` / `run-local`;
- 0.2 compatibility: explicit `tool-operation` polling.

Current claim ceilings:

```text
LOCAL_TOOL_BRIDGE != UNIVERSAL_SHELL
PROCESS_ALLOWLIST != PROCESS_ISOLATION
DECLARED_LOOPBACK_ONLY != ENFORCED_PROCESS_NETWORK_NAMESPACE
LOCAL_PROCESS_SUCCESS != CLAIM_VERIFIED
LOCALHOST != AUTOMATICALLY_TRUSTED
TOOL_RESULT != TRUTH
IMPORT != EVIDENCE_PROMOTION
LOCAL_TOOL_BRIDGE_UNAVAILABLE != FKDB_UNAVAILABLE
```

Vendor adapters and remote synchronization are deliberately outside this verified
boundary.
