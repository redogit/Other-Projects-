# FKDB Local Tool Integration Design

**Date:** 2026-10-04
**Project:** FKDB — Fighting Knowledge Decay Browser
**Status:** Design approved in conversation; written-spec review pending
**Parent architecture:** FKDB F9 Wasm-HIF capability graph
**Target increment:** F10+ local-first tool integration and cross-carrier ingestion

## 1. Purpose

Make the research, planning, computation, citation, persistence, deployment, and verification tools used by FKDB first-class browser citizens without making FKDB dependent on remote vendor APIs.

The browser must remain useful in a disconnected/local-only environment.

Preferred order:

    embedded/local file
    -> local process
    -> localhost service
    -> portable import/export artifact
    -> user-driven browser/CLI handoff
    -> optional remote integration

A remote service may enrich FKDB, but loss of the service must not erase already acquired knowledge, provenance, or the ability to inspect/reconstruct prior work.

## 2. Success criteria

1. FKDB can discover and describe locally available tool capabilities.
2. Tool access is capability-based and explicitly authorized.
3. A local-only mode can deny non-loopback networking while keeping useful tool integrations available.
4. Every tool result is converted into a common provenance-bearing carrier before entering the FKDB index.
5. Tools without a local runtime still integrate through durable import/export bundles.
6. Vendor-specific objects retain source identity and are never rewritten as FKDB-native evidence.
7. Missing tools and unavailable capabilities return explicit remainder, not fabricated success.
8. Tool integration is usable from modern WebAssembly hosts and from the existing native RMAL fallback.

## 3. Core architecture

### 3.1 Local Tool Bridge

Introduce a host-side Local Tool Bridge (LTB) behind Wasm-HIF.

    FKDB UI / query
          |
          v
    Wasm-HIF capability graph
          |
          v
    Local Tool Bridge
          |
          +--> local files
          +--> user-approved local process
          +--> localhost service
          +--> portable artifact importer/exporter
          +--> optional user-driven external handoff

The LTB is a capability broker, not a universal shell.

### 3.2 Local capability classes

    FILE_READ
    FILE_WRITE
    DIRECTORY_WATCH
    LOCAL_PROCESS
    LOCALHOST_HTTP
    LOCAL_DATABASE
    OPEN_EXTERNAL_URL
    IMPORT_ARTIFACT
    EXPORT_ARTIFACT

Remote TCP/HTTP access is not implied by any local capability.

### 3.3 No-remote mode

FKDB must support NETWORK_POLICY = LOOPBACK_ONLY.

Under this mode:

- browser/Wasm network requests to non-loopback addresses are denied;
- local files, local processes, localhost services, OPFS, IndexedDB and memory remain available;
- imported artifacts remain queryable;
- unavailable remote refreshes become explicit remainder;
- the existing native RMAL carrier obeys the same policy.

Invariant: REMOTE_UNAVAILABLE != KNOWLEDGE_UNAVAILABLE.

## 4. Common ToolCarrier

Every adapter emits a common object before admission:

    ToolCarrier {
        carrier_id
        tool_id
        tool_version
        adapter_kind
        locality
        source_identity
        source_version
        retrieved_at
        payload_type
        payload
        content_hash
        provenance
        authority_scope
        evidence_status
        obligation
        relations
        cost
        loss
        remainder
        recovery_path
    }

Locality values: EMBEDDED, LOCAL_FILE, LOCAL_PROCESS, LOCALHOST, PORTABLE_IMPORT, USER_HANDOFF, REMOTE_OPTIONAL.

Admission invariants:

    TOOL_RESULT != TRUTH
    TOOL_RELATION != AUTHORITY
    IMPORT != EVIDENCE_PROMOTION
    LOCAL_PROCESS_SUCCESS != CLAIM_VERIFIED
    REMOTE_SERVICE_LOSS != HISTORY_LOSS
    FALLBACK != SILENT_SEMANTIC_WEAKENING

## 5. Tool-specific integration

### 5.1 Mathbox

**Locality:** EMBEDDED / LOCAL_FILE / LOCAL_PROCESS.

FKDB recognizes Mathbox computation manifests, research-state ledgers, proof/computation audit outputs, bounds, hashes, claim ceilings and reproduction commands. Allowlisted local Mathbox scripts may be invoked through the LTB. A passing computation never becomes a theorem automatically.

### 5.2 Superpowers

**Locality:** EMBEDDED / LOCAL_FILE.

FKDB recognizes docs/superpowers/specs, docs/superpowers/plans and locally available skill manifests. It presents design approval, plan approval, verification and failure gates as workflow state. Superpowers files remain authoritative for their own workflow semantics.

### 5.3 Zotero

**Locality:** LOCALHOST / LOCAL_FILE / PORTABLE_IMPORT.

Preferred routes: Zotero Desktop loopback API when enabled and explicitly authorized; BibTeX/RIS/CSL-JSON import/export; user-selected local library/file watching. Zotero item keys remain distinct from BibTeX citation keys. Zotero Cloud is not required.

### 5.4 Wolfram

**Locality:** LOCAL_PROCESS / LOCAL_FILE.

When a local Wolfram Engine or wolframscript exists, FKDB may invoke allowlisted computations and capture source expression, engine/version, result, exact/numerical status, resource bounds and a computation receipt. Exported .wl/notebook artifacts may be imported without execution. Wolfram Cloud is optional.

### 5.5 Supabase

**Locality:** LOCAL_DATABASE / LOCALHOST / LOCAL_PROCESS.

Supabase is optional infrastructure, not canonical FKDB knowledge. Preferred route: Supabase CLI local stack -> localhost Postgres/REST/Edge Functions -> FKDB adapter. Uses may include a durable provenance/event ledger, optional synchronized source index, local Edge Function/Wasm experiments and RLS-backed multi-user views. Hosted Supabase remains optional.

### 5.6 Railway

**Locality:** LOCAL_FILE / PORTABLE_IMPORT / USER_HANDOFF.

Railway is cloud-backed for live deployment state, so FKDB must not depend on its remote API. Local integration covers checked-in Railway configuration, imported build/deploy/log snapshots, local Docker/build artifacts and optional user-approved Railway CLI handoff. Live deployment state is REMOTE_OPTIONAL.

### 5.7 Linear

**Locality:** PORTABLE_IMPORT / LOCAL_FILE / USER_HANDOFF.

Linear has no required local runtime. FKDB supports a portable bundle containing project metadata, issues, documents, attachments and a manifest. IDs, timestamps, labels, parent-child relationships and source URLs are preserved. Remote synchronization is optional.

### 5.8 SciSpace / Consensus / Exa

**Locality:** PORTABLE_IMPORT / USER_HANDOFF.

No local runtime is assumed. FKDB ingests exported or user-provided search/paper/result records as ToolCarrier/ResearchCarrier objects. The browser may open a provider in a user-controlled tab, but acquired knowledge enters FKDB only through a durable captured artifact. Provider agreement does not become truth.

## 6. ResearchCarrier

    ResearchCarrier {
        provider
        query
        source_identity
        source_version
        retrieved_at
        title
        authors
        doi_or_url
        abstract_or_excerpt
        content_hash
        evidence_status
        provenance
        authority_scope
        contradictions
        remainder
    }

A Zotero import may point back to one or more ResearchCarrier objects.

## 7. Standards/version decay handling

The standards investigation found current authoritative documentation surfaces that can disagree about release state. Every standards record therefore requires source, source_version, retrieved_at, claim, authority_scope, supersedes, contradicts and verification_status.

FKDB may keep contradictory records simultaneously.

    LATEST_SOURCE != AUTOMATIC_TRUTH
    OLDER_SOURCE != DELETE
    CONTRADICTION -> INSPECT

## 8. Browser UX

Add a local TOOLS surface reachable from FKDB. Each tool card shows NAME, LOCALITY, AVAILABLE/UNAVAILABLE/DEGRADED, CAPABILITIES, LAST LOCAL RECEIPT and UNRESOLVED REQUIREMENTS.

No remote login prompt is shown merely because a tool is unavailable locally.

## 9. Local process security

Local execution is opt-in and allowlisted. A process adapter declaration contains tool_id, executable_identity, allowed_subcommands, working_roots, read_roots, write_roots, network_policy, time_limit, memory_limit and environment_allowlist.

Every execution emits a receipt with argv, executable hash/version where obtainable, exit status, duration and affected paths. Secrets are not copied into browser-visible provenance records.

Security invariants:

    WASM_SANDBOX != HOST_TRUST
    HOST_IMPORT != SAFE_BY_DEFAULT
    LOCALHOST != AUTOMATICALLY_TRUSTED

## 10. WIT boundary

Add a local-tools interface to Wasm-HIF. The WASI 0.3 shape supports listing/inspecting adapters, async artifact import and async local execution. The 0.2 compatibility world uses explicit operation resources/polling. Browser-transpiled Component execution and native Component hosts use the same logical carrier contract.

## 11. Persistence

Default persistence remains OPFS -> IndexedDB -> memory. Optional local Supabase may mirror/index records, but the FKDB local store remains sufficient for offline inspection and recovery.

## 12. Deployment

Railway is an optional runtime/deployment evidence source. FKDB must be deployable as a static/local application without Railway. A Railway deployment, when used, is evidence about one deployment environment only.

## 13. Formal/computational evidence

The existing seven-tier host selector was exhaustively checked over all 64 assignments of its six Boolean capability inputs. Coverage was 64/64 and all seven outputs were reachable.

Observed distribution:

    WASM_COMPONENT_0_3      16
    WASM_JSPI                8
    WASM_PROMISE_HANDOFF     4
    WASM_LEGACY_WEB          3
    JS_MODERN_FALLBACK      16
    JS_LEGACY_FALLBACK       8
    NATIVE_RMAL_FALLBACK     9

This verifies the finite selector only. The implementation plan replaces the coarse ladder with a capability graph while retaining an explicit selected-execution receipt.

## 14. Research implication

Peer-reviewed WebAssembly security work indicates that sandbox guarantees do not automatically extend through host/WASI interactions. Therefore the Local Tool Bridge is part of the security boundary and must be audited as such.

## 15. Required testing

1. Capability-graph totality and deterministic selection.
2. Loopback-only network-policy tests.
3. Local-file path traversal negatives.
4. Process allowlist and argument-injection negatives.
5. Zotero local-unavailable and local-available probes.
6. Wolfram process-unavailable and bounded-run receipts.
7. Portable bundle round trips for Linear/SciSpace/Consensus/Exa.
8. Local Supabase adapter with hosted Supabase absent.
9. Remote-only Railway state represented as unavailable rather than required.
10. ToolCarrier provenance survives import, storage, query and browser inspection.
11. No adapter silently transfers evidence authority.
12. Modern Wasm path and native RMAL fallback preserve equivalent carrier invariants.

## 16. Non-goals

- Do not clone SciSpace, Consensus, Exa, Linear or Railway.
- Do not bypass vendor authentication.
- Do not scrape private user data without user action.
- Do not require cloud accounts.
- Do not treat localhost services as automatically trusted.
- Do not guarantee identical functionality across all fallbacks.
- Do not make tool availability equivalent to knowledge validity.

## 17. Implementation decomposition

This document is the umbrella architecture. It is deliberately too broad for one
implementation plan.

Implementation is split into independently reviewable plans:

### Plan A — F10 Core Local Tool Bridge

Scope:

    capability graph
    + selected-execution receipt
    + Local Tool Bridge interface
    + ToolCarrier schema
    + loopback-only network policy
    + file/process capability allowlists
    + portable bundle envelope
    + TOOLS discovery/status shell

No vendor-specific adapter is required for Plan A to be useful.

### Plan B — Local workflow/computation adapters

Scope:

    Mathbox
    + Superpowers
    + Zotero local/portable
    + Wolfram local-process

### Plan C — Local infrastructure adapters

Scope:

    Supabase local stack
    + Railway local configuration/artifact ingestion

Hosted Supabase and live Railway cloud state remain optional.

### Plan D — Portable research/project adapters

Scope:

    SciSpace
    + Consensus
    + Exa
    + Linear

These adapters operate first on portable artifacts and user-driven handoffs. Live remote
synchronization is a separate optional future layer.

### Plan E — Cross-carrier ingestion

Scope:

    ToolCarrier -> FKDB source index
    + browser inspection
    + contradiction surfacing
    + recovery-path traversal
    + no-authority-transfer gates

Each plan must produce working software without requiring any later plan.

## 18. Current evidence and unresolved probes

Design evidence used in this review includes:

- current WebAssembly Component Model and WASI 0.3 documentation;
- Jco/componentize-js documentation for browser transpilation of components;
- peer-reviewed WebAssembly runtime/security literature, including research identifying
  host/WASI interactions as a separate trust boundary;
- Supabase documentation for local development, RLS and Edge Function Wasm support;
- an exact Wolfram enumeration of the existing 64-state coarse host selector.

Environment-specific facts:

- no existing FKDB Linear project was found;
- no existing Supabase project was found;
- no existing Railway project was found;
- Zotero Desktop local availability was not probed from this remote environment;
- local Wolfram Engine/wolframscript availability was not probed.

Those local capabilities must be discovered at runtime rather than assumed.

## 19. Claim ceiling

    LOCAL_INTEGRATION != TOOL_REIMPLEMENTATION
    PORTABLE_IMPORT != LIVE_SYNC
    LOCAL_PROCESS_SUCCESS != CLAIM_VERIFIED
    REMOTE_OPTIONAL != REQUIRED_DEPENDENCY
    TOOL_CONSENSUS != TRUTH
    SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION
