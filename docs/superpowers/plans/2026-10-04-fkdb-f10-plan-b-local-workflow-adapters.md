# FKDB F10 Plan B Local Workflow/Computation Adapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Mathbox, Superpowers, Zotero, and Wolfram visible to FKDB as local/portable ToolCarrier producers without requiring vendor cloud APIs or reopening local-process execution.

**Architecture:** Add a generic read-only adapter registry behind the verified Local Tool Bridge. Adapters can probe allowed local roots or literal-loopback services and collect bounded artifacts into ToolCarrier records; collection is token-gated and never executes discovered commands. Mathbox and Superpowers are project-file adapters, Zotero is a read-only localhost/portable adapter, and Wolfram is artifact/probe-only until a future process-isolation backend can satisfy FKDB's fail-closed policy.

**Tech Stack:** Python 3.10+ standard library, existing Local Tool Bridge + ToolCarrier contracts, ES modules for tool-status rendering, WIT/WASI 0.3 + 0.2 compatibility contracts, CMake/CTest.

**Spec:** `docs/superpowers/specs/2026-10-04-fkdb-local-tool-integration-design.md`

## Global Constraints

- No remote vendor API is required for any Plan B capability.
- Plan B adds **no local process execution**. Wolfram executable discovery is probe-only.
- All filesystem reads are constrained by existing bridge read roots and resolved-path containment.
- All localhost HTTP targets are literal loopback addresses and must pass `BridgePolicy.validate_loopback_url`.
- Zotero Desktop local API use is read-only; connector write routes are outside Plan B.
- Zotero attachment file URLs/full text are not retrieved in Plan B.
- Mathbox ledger labels remain mechanical evidence-state records, not mathematical truth.
- Superpowers specs/plans remain workflow artifacts, not proof/evidence promotion.
- Every collected artifact becomes a validated `ToolCarrier` before leaving the bridge.
- Adapter probing must not mutate project files, start services, install software, or log in remotely.
- Missing tools return `UNAVAILABLE` or `DEGRADED` with explicit unresolved requirements.
- Browser TOOLS remains useful when every adapter is unavailable.
- `TOOL_RESULT != TRUTH`, `PORTABLE_IMPORT != LIVE_SYNC`, `LOCALHOST != AUTOMATICALLY_TRUSTED`.

## Review Focus

1. **Local-root escape during adapter scans:** all discovered files must be resolved and rechecked against allowed roots, including symlinks.
2. **Unbounded project scanning:** every adapter must have explicit max-files and max-bytes caps and report truncation as remainder.
3. **Zotero localhost confusion:** only literal `127.0.0.1:23119` is allowed; redirects to non-loopback targets must be rejected.
4. **Semantic promotion:** Mathbox status labels, Superpowers approvals, Zotero metadata, and Wolfram artifacts must remain provider/tool records, not FKDB truth.
5. **Process regression:** discovering `wolframscript` must never make `/run` executable while process isolation remains unavailable.

---

### Task 1: Add a generic local adapter registry and bounded collection contract

**Files:**
- Create: `Decision Field Operator Lab/tools/fkdb_local_adapters.py`
- Modify: `Decision Field Operator Lab/tools/fkdb_local_tool_bridge.py`
- Modify: `Decision Field Operator Lab/fkdb/tools/local-tool-policy.json`
- Create: `Decision Field Operator Lab/test_fkdb_local_adapters.py`
- Modify: `Decision Field Operator Lab/rmal-browser/CMakeLists.txt`

**Interfaces:**
- Produces:
  - `AdapterDescriptor`
  - `CollectionRequest`
  - `CollectionResult`
  - `LocalAdapterRegistry.register(adapter)`
  - `LocalAdapterRegistry.descriptors(policy) -> list[dict]`
  - `LocalAdapterRegistry.collect(tool_id, request, policy) -> CollectionResult`
  - adapter protocol: `descriptor(policy)` + `collect(request, policy)`
- Bridge adds token-gated `POST /fkdb-tool-bridge/v1/collect`.
- Default policy adds:
  - `adapter_max_files`
  - `adapter_max_bytes`
  - `adapters` (empty by default)

- [ ] **Step 1: Write failing registry/bridge tests**

Test:
- duplicate adapter IDs rejected;
- unknown adapter returns explicit unavailable/error;
- collect endpoint requires exact Origin + bridge token;
- adapter result carriers are validated before response;
- max-files/max-bytes truncation is explicit remainder;
- adapter registry cannot bypass bridge read-root resolution;
- default production policy enables no vendor adapter automatically.

- [ ] **Step 2: Run RED**

Run:
```sh
python -m unittest "Decision Field Operator Lab/test_fkdb_local_adapters.py" -v
```

Expected: FAIL because registry/collect endpoint do not exist.

- [ ] **Step 3: Implement registry and `/collect` minimally**

Use no dynamic import-by-name from user input. The bridge constructs the known adapter registry in code; policy only enables/configures known adapter IDs.

Collection response schema:
```text
fkdb/local-tool-collection/v1
tool_id
status = COLLECTED | PARTIAL | UNAVAILABLE
carriers[]
remainder[]
cost { files_scanned, bytes_read }
```

- [ ] **Step 4: Run registry + existing bridge tests**

Expected: PASS.

- [ ] **Step 5: Commit**

```sh
git add "Decision Field Operator Lab/tools/fkdb_local_adapters.py" \
        "Decision Field Operator Lab/tools/fkdb_local_tool_bridge.py" \
        "Decision Field Operator Lab/fkdb/tools/local-tool-policy.json" \
        "Decision Field Operator Lab/test_fkdb_local_adapters.py" \
        "Decision Field Operator Lab/rmal-browser/CMakeLists.txt"
git commit -m "FKDB: add bounded local adapter registry"
```

---

### Task 2: Add the Mathbox local-file adapter

**Files:**
- Create: `Decision Field Operator Lab/tools/fkdb_adapter_mathbox.py`
- Create: `Decision Field Operator Lab/test_fkdb_adapter_mathbox.py`
- Modify: `Decision Field Operator Lab/tools/fkdb_local_adapters.py`
- Modify: `Decision Field Operator Lab/rmal-browser/CMakeLists.txt`

**Interfaces:**
- Adapter ID: `mathbox`
- Locality: `LOCAL_FILE`
- Probe targets per allowed read root:
  - `.mathbox/config.json`
  - `.mathbox/events/*.json`
- Collection emits one ToolCarrier per config/event artifact with raw JSON payload + SHA-256.
- Provider authority scope: `MATHBOX_RECORDED_STATE_ONLY`.
- Evidence status: `MECHANICAL_LEDGER_RECORD_NOT_PROOF_AUDIT`.

- [ ] **Step 1: Write failing fixture tests**

Create temp project fixtures and assert:
- no `.mathbox` => UNAVAILABLE;
- valid config/events => AVAILABLE descriptor + deterministic carriers;
- events are ordered lexically by numbered filename;
- invalid JSON becomes explicit remainder, not crash;
- symlinked `.mathbox` escaping allowed root is rejected;
- max-files cap yields PARTIAL + `MATHBOX_FILE_LIMIT_REACHED`;
- no record is renamed to “proved”.

- [ ] **Step 2: Run RED**

Expected: adapter missing.

- [ ] **Step 3: Implement bounded read-only adapter**

Do not invoke Mathbox helper scripts in Plan B.

- [ ] **Step 4: Run adapter + ToolCarrier tests**

Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `FKDB: add local Mathbox ledger adapter`.

---

### Task 3: Add the Superpowers project-artifact adapter

**Files:**
- Create: `Decision Field Operator Lab/tools/fkdb_adapter_superpowers.py`
- Create: `Decision Field Operator Lab/test_fkdb_adapter_superpowers.py`
- Modify: `Decision Field Operator Lab/tools/fkdb_local_adapters.py`
- Modify: `Decision Field Operator Lab/rmal-browser/CMakeLists.txt`

**Interfaces:**
- Adapter ID: `superpowers`
- Locality: `LOCAL_FILE`
- Bounded probe/collection paths:
  - `docs/superpowers/specs/*.md`
  - `docs/superpowers/plans/*.md`
- Optional progress ledgers matching `docs/superpowers/plans/*-progress.md` remain ordinary artifacts.
- Authority scope: `WORKFLOW_ARTIFACT_ONLY`.
- Evidence status: `WORKFLOW_STATE_NOT_CLAIM_VERIFICATION`.

- [ ] **Step 1: Write failing tests**

Assert:
- specs/plans are distinguished by adapter metadata;
- file content and hash are preserved;
- lexical ordering is deterministic;
- symlink/path escape rejected;
- no file is parsed as approval unless the source artifact itself explicitly contains that record;
- max-files/max-bytes caps produce explicit remainder.

- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Implement adapter.**
- [ ] **Step 4: Run adapter + carrier tests.**
- [ ] **Step 5: Commit:** `FKDB: add local Superpowers artifact adapter`.

---

### Task 4: Add Zotero read-only localhost + portable artifact adapter

**Files:**
- Create: `Decision Field Operator Lab/tools/fkdb_adapter_zotero.py`
- Create: `Decision Field Operator Lab/test_fkdb_adapter_zotero.py`
- Modify: `Decision Field Operator Lab/tools/fkdb_local_adapters.py`
- Modify: `Decision Field Operator Lab/rmal-browser/CMakeLists.txt`

**Interfaces:**
- Adapter ID: `zotero`
- Localities: `LOCALHOST`, `PORTABLE_IMPORT`
- Probe URL exactly: `http://127.0.0.1:23119/api/`
- Search route: `/api/users/0/items?q=<encoded-query>&limit=<bounded-limit>`
- No API key.
- No connector write routes.
- No attachment/fulltext/file-view routes.
- Portable collection accepts user-provided `.bib`, `.ris`, or CSL-JSON files as raw source artifacts; parsing is not required for Plan B.
- Preserve Zotero item key separately from any citation/BibTeX key when present in local API JSON.

- [ ] **Step 1: Write failing tests with a local fake HTTP server**

Assert:
- unavailable port => descriptor UNAVAILABLE;
- valid local API response => AVAILABLE;
- redirects to non-loopback denied;
- only GET is used;
- query is URL-encoded and result count bounded;
- attachment/fulltext URLs are never fetched;
- response items become separate ToolCarriers with Zotero item key/source identity;
- portable .bib/.ris/.json raw files round-trip as carriers without claiming live sync.

- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Implement read-only adapter with `urllib.request` and redirect guard.**
- [ ] **Step 4: Run Zotero + bridge/carrier tests.**
- [ ] **Step 5: Commit:** `FKDB: add local and portable Zotero adapter`.

---

### Task 5: Add Wolfram artifact/probe-only adapter

**Files:**
- Create: `Decision Field Operator Lab/tools/fkdb_adapter_wolfram.py`
- Create: `Decision Field Operator Lab/test_fkdb_adapter_wolfram.py`
- Modify: `Decision Field Operator Lab/tools/fkdb_local_adapters.py`
- Modify: `Decision Field Operator Lab/rmal-browser/CMakeLists.txt`

**Interfaces:**
- Adapter ID: `wolfram`
- Localities: `LOCAL_FILE`, optional descriptor `LOCAL_PROCESS`
- File collection: explicitly requested/allowed-root `.wl`, `.m`, `.nb` artifacts as raw bytes/metadata.
- Process probe: `shutil.which("wolframscript")` only.
- If executable exists, descriptor state remains `DEGRADED` with `PROCESS_ISOLATION_BACKEND_UNAVAILABLE`.
- No Wolfram process execution in Plan B.

- [ ] **Step 1: Write failing tests**

Assert:
- artifact collection is read-only + bounded;
- binary notebook bytes hash correctly;
- executable absence => no process capability;
- fake discovered executable => DEGRADED, never executable;
- bridge `/run` remains 503/fail-closed.

- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Implement probe/artifact adapter.**
- [ ] **Step 4: Run Wolfram + bridge tests.**
- [ ] **Step 5: Commit:** `FKDB: add Wolfram artifact and degraded process probe`.

---

### Task 6: Extend Wasm-HIF collection contract without vendor names

**Files:**
- Modify: `Decision Field Operator Lab/fkdb/wasm/wit/0.3/fkdb-hif.wit`
- Modify: `Decision Field Operator Lab/fkdb/wasm/wit/0.2/fkdb-hif.wit`
- Modify: `Decision Field Operator Lab/test_fkdb_wasm_hif.py`

**Interfaces:**
- Add generic:
  - `collect-request`
  - `collection-result`
- 0.3: `collect-local: async func(...)`.
- 0.2: `begin-collect: func(...) -> tool-operation` or a collection-operation resource if result multiplicity requires it.
- WIT contains no `mathbox`, `superpowers`, `zotero`, or `wolfram` vendor identifier.

- [ ] **Step 1: Write failing WIT contract tests.**
- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Extend both WIT tracks generically.**
- [ ] **Step 4: Run WIT tests.**
- [ ] **Step 5: Commit:** `FKDB: add generic local collection WIT contract`.

---

### Task 7: Expose richer read-only adapter status in the browser

**Files:**
- Modify: `Decision Field Operator Lab/fkdb/web/index.html`
- Modify: `Decision Field Operator Lab/fkdb/web/local-tool-client.mjs`
- Modify: `Decision Field Operator Lab/test_fkdb_web_host.mjs`
- Modify: `Decision Field Operator Lab/fkdb/pages/tools.html` only if bounded text changes are required.
- Modify: `Decision Field Operator Lab/test_fkdb_surface.py` only if bounded navigation changes.

**Interfaces:**
- Browser remains read-only without an injected mutation token.
- Tool cards display:
  - tool ID/name
  - locality
  - state
  - capabilities
  - unresolved requirements
- No remote login CTA is generated.

- [ ] **Step 1: Write failing browser rendering/client tests.**
- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Render descriptors without exposing local paths, tokens, or secrets.**
- [ ] **Step 4: Run Node + bounded browser tests.**
- [ ] **Step 5: Commit:** `FKDB: surface local workflow adapter status`.

---

### Task 8: Verify Plan B and advance the FKDB ledger

**Files:**
- Modify: `Decision Field Operator Lab/fkdb/CURRENT.md`
- Modify: `Decision Field Operator Lab/rmal-browser/README.md`
- Modify: PR #116 body after tests.
- Test: all new adapter gates + existing 48-test baseline.

**Interfaces:**
- Consumes Tasks 1–7.
- Produces the verified Plan B boundary only after green CI.

- [ ] **Step 1: Add any remaining adapter tests to CTest.**
- [ ] **Step 2: Run focused adapter tests.**
- [ ] **Step 3: Run full dedicated browser/RMAL CTest on Linux and Windows.**
- [ ] **Step 4: Require broader Decision Field audit success at the final head.**
- [ ] **Step 5: Update CURRENT/README with exact verified capabilities and remainder.**

Required remainder after Plan B:
- no Wolfram execution;
- no Zotero writes/full text/attachment path reads;
- no cloud sync;
- no SciSpace/Consensus/Exa/Linear/Supabase/Railway adapters yet;
- collected ToolCarriers are not yet promoted into FKDB's cross-carrier source index until Plan E.

- [ ] **Step 6: Commit:** `FKDB: verify local workflow adapter boundary`.

## Self-Review Result

- **Spec coverage:** Plan B covers all four adapters named by the umbrella architecture without requiring remote APIs.
- **Security:** no new process execution path; Zotero is literal-loopback/read-only; filesystem adapters inherit bridge root containment and caps.
- **Type consistency:** every adapter produces existing ToolCarrier; generic collection semantics are added once to bridge/WIT.
- **Knowledge boundary:** Mathbox/Superpowers/Zotero/Wolfram records retain their provider authority and evidence status.
- **Deferred integration:** ToolCarrier-to-FKDB source-index admission stays Plan E by design rather than being silently coupled here.
