# FKDB Wasm-HIF — WebAssembly Host Interoperability Framework

**Project:** FKDB — Fighting Knowledge Decay Browser  
**Role:** first-class WebAssembly + modern Web host layer  
**Lineage:** additive successor layer; Independent Browser / RMAL fallbacks remain preserved

## Purpose

Wasm-HIF makes WebAssembly and current Web platform capabilities first-class FKDB
execution carriers while preserving explicit fallbacks for older browsers, older WASI
toolchains, legacy Emscripten builds, and the existing native RMAL browser path.

The governing rule is feature/capability detection rather than user-agent detection.

```text
modern capability
-> use directly
-> otherwise select explicit adapter
-> otherwise preserve unresolved requirement
-> never silently weaken provenance, evidence, or recovery obligations
```

## Current standards normalization

### JS Promise Integration

The WebAssembly JS Promise Integration proposal currently defines
`WebAssembly.Suspending` and `WebAssembly.promising`. It is listed in the
WebAssembly proposal tracker at Phase 5.

FKDB treats JSPI as a runtime-detected capability, not as an assumed browser property.

```text
JSPI_AVAILABLE
  -> WebAssembly.Suspending(import)
  -> WebAssembly.promising(export)

JSPI_UNAVAILABLE
  -> explicit Promise / outer-controller handoff
  -> no fake synchronous semantics
```

### Component Model / WIT / WASI 0.3

WASI 0.3 is the current Preview 3 track. It adds native Component Model async:

- `async func`
- `stream<T>`
- `future<T>`

There is no WASI 0.3 `wasi:io` package; its polling/stream resource patterns are
replaced by Component Model primitives.

FKDB therefore treats WIT/WASI 0.3 as the preferred typed component contract and keeps
a separate explicit-poll WIT compatibility contract for 0.2-era hosts.

### HTTP

Primary component/edge contract:

```text
wasi:http@0.3
  service
  middleware
  client.send: async func(...)
  handler.handle: async func(...)
```

Browser-host contract:

```text
Fetch + ReadableStream
  -> JSPI when available
  -> explicit Promise handoff otherwise
```

Compatibility:

```text
wasi:http@0.2 proxy
  -> XMLHttpRequest fallback
  -> existing Independent Browser native HTTP/TLS carrier
```

### Files / persistence

Preferred order is capability dependent:

```text
WASI 0.3 filesystem component contract
OR browser OPFS
  -> IndexedDB
  -> Emscripten WasmFS / IDBFS adapter when building legacy C/C++
  -> MEMFS / memory-only
  -> native host filesystem only when explicitly authorized
```

Emscripten documentation currently describes WasmFS inconsistently as both stable-but-
not-feature-complete and experimental in different documentation surfaces. FKDB therefore
treats WasmFS as a compatibility adapter, not as normative architectural authority.

## Host capability profile

Every Web host is reduced to an explicit capability record:

```text
WebAssembly core
JSPI
instantiateStreaming
Fetch
ReadableStream
Worker
SharedArrayBuffer + crossOriginIsolated
OPFS
IndexedDB
XMLHttpRequest
declared Component Model 0.3 binding
declared WASI HTTP 0.3 binding
declared WASI HTTP 0.2 binding
```

No capability is inferred from a browser brand/version string.

## Execution tiers

### Tier A — WASM_COMPONENT_0_3

Preferred when a Component Model 0.3 runtime/binding is available.

```text
WIT 0.3
-> Canonical ABI
-> async func / stream / future
-> host capability interfaces
```

### Tier B — WASM_JSPI

Browser core Wasm + JSPI.

```text
Wasm export
-> WebAssembly.promising
-> Wasm
-> WebAssembly.Suspending host import
-> Promise-based Web API
-> resume Wasm
```

### Tier C — WASM_PROMISE_HANDOFF

Core Wasm is available but JSPI is not.

The host must use FKDB's explicit continuation/outer-controller model. An async host
operation may not be presented to a synchronous Wasm caller as if it completed inline.

### Tier D — WASM_LEGACY_WEB

Core Wasm exists but modern Fetch/Streams are missing. Use explicit adapters such as XHR
or legacy Emscripten integration where available.

### Tier E — JS_MODERN_FALLBACK

No usable Wasm execution path, but modern JavaScript/Web APIs exist. FKDB query,
provenance, recovery and carrier records remain usable through the same serialized
contracts.

### Tier F — JS_LEGACY_FALLBACK

Use bounded XMLHttpRequest / IndexedDB or memory adapters. Unsupported capabilities
remain explicit.

### Tier G — NATIVE_RMAL_FALLBACK

Use the inherited Independent Browser / RMAL C23 host and native HTTP/TLS carriers.

This is a preserved fallback, not a demotion of the predecessor lineage.

## Modern Web first-class capabilities

FKDB Web code treats these as direct capabilities when present:

- ES modules;
- WebAssembly core;
- JSPI;
- Fetch;
- Streams;
- Web Workers;
- SharedArrayBuffer only with the required cross-origin isolation;
- OPFS;
- IndexedDB;
- AbortController;
- TextEncoder / TextDecoder.

Optional capabilities must never become hidden requirements.

## Typed carrier rule

A carrier crossing the Wasm/host boundary must retain:

```text
identity
payload type
source
provenance
evidence status
obligation
cost
loss
remainder
recovery path
authority status
```

The host may transform representation. It may not silently promote evidence.

```text
CANONICAL_ABI_TRANSLATION != EVIDENCE_TRANSFER
HOST_CAPABILITY != AUTHORITY
ASYNC_RESUME != SUCCESS
NETWORK_RESPONSE != ADMITTED_KNOWLEDGE
PERSISTED_BYTES != RECONSTRUCTIBLE_MEANING
```

## Fallback invariant

Fallback means a different lawful carrier, not weaker truth semantics.

```text
MODERN_PATH_FAILURE
-> select next declared adapter
-> retain failure + reason
-> preserve obligation
-> preserve source/provenance
-> expose lost capability
```

If no fallback satisfies the obligation:

```text
RETURN UNRESOLVED
```

Do not manufacture success.

## Current source anchors

- WebAssembly JSPI proposal:
  https://github.com/WebAssembly/js-promise-integration
- WebAssembly proposal phase tracker:
  https://github.com/WebAssembly/proposals
- WebAssembly Component Model:
  https://component-model.bytecodealliance.org/
- WASI 0.3:
  https://wasi.dev/releases/wasi-p3
- WASI:
  https://github.com/WebAssembly/WASI
- Emscripten filesystem:
  https://emscripten.org/docs/porting/files/file_systems_overview.html
- Emscripten WasmFS API notes:
  https://emscripten.org/docs/api_reference/Filesystem-API.html

## Claim ceiling

This layer defines and tests FKDB host capability selection and typed interoperability
contracts. It does not establish universal runtime support, complete Component Model
toolchain compatibility, browser security, or semantic equivalence across all fallbacks.
