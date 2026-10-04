# FKDB F10 Core Local Tool Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build FKDB's local-first host boundary: a capability graph, provenance-bearing ToolCarrier bundle contract, loopback-only Local Tool Bridge, Wasm-HIF local-tool interfaces, and a browser TOOLS status surface that works without any vendor cloud API.

**Architecture:** Refactor the current coarse Wasm-HIF tier selector into an obligation-driven capability graph while preserving `selectHostProfile()` as a compatibility projection. Add a stdlib-only local bridge that serves FKDB and its tool API from loopback with same-origin + per-launch capability-token enforcement; the browser remains usable without the bridge, reporting local tools as unavailable/degraded. All imported/local execution results cross the boundary as validated ToolCarrier records with explicit provenance, authority, cost, loss, remainder, and recovery path.

**Tech Stack:** ES modules, browser Web APIs, core WebAssembly/JSPI feature detection, WIT/WASI 0.3 + 0.2 compatibility contracts, Python 3.10+ standard library, JSON, SHA-256, existing CMake/CTest matrix.

**Spec:** `docs/superpowers/specs/2026-10-04-fkdb-local-tool-integration-design.md`

## Global Constraints

- No vendor-specific adapter is implemented in Plan A.
- No new runtime dependency is required; Python bridge code is standard-library only.
- Capability selection uses feature/capability detection, never browser user-agent sniffing.
- WebAssembly Components in browsers are represented as a distinct transpiled-component capability; native Component hosts are a separate capability.
- Default local bridge network policy is `LOOPBACK_ONLY`.
- The bridge binds only loopback addresses and never listens on wildcard/public interfaces.
- The bridge API requires same-origin requests plus a per-launch random capability token for mutating/local-process operations.
- Generic local process execution is deny-by-default; an executable/subcommand/root must be explicitly allowlisted.
- FKDB static/browser-only mode remains valid when the local bridge is absent.
- `ToolCarrier` admission never promotes source evidence or authority.
- `UNKNOWN != FALSE`, `UNRESOLVED != NEGATIVE`, `FALLBACK != SILENT_SEMANTIC_WEAKENING`.
- Existing Independent Browser / RMAL fallback behavior and evidence remain intact.
- Passing tests establish bounded software behavior only.

## Review Focus

1. **Path escape through `..`, absolute paths, or symlinks:** Task 3 must prove the bridge rejects any resolved path outside an allowlisted root.
2. **Non-loopback network target disguised as localhost/hostname:** Task 3 must test literal IPv4/IPv6 loopback acceptance and rejection of non-loopback targets; no DNS name is trusted merely because it contains “localhost”.
3. **Process argument injection or executable substitution:** Task 3 must test exact executable identity, fixed subcommand allowlists, argument vectors without shell interpolation, and deny-by-default behavior.
4. **Malformed/oversized ToolCarrier bundle:** Task 2 must reject unknown schema versions, missing provenance/evidence/recovery fields, duplicate carrier IDs, invalid hashes, and configured size-limit overflow.
5. **Capability graph ambiguity/drift:** Task 1 must enumerate representative overlapping capabilities and prove deterministic path selection plus explicit rejected alternatives/remainder; the compatibility host-profile projection must remain stable for existing tests.

---

### Task 1: Replace the coarse host ladder with an obligation-driven capability graph

**Files:**
- Create: `Decision Field Operator Lab/fkdb/web/host-capability-graph.mjs`
- Modify: `Decision Field Operator Lab/fkdb/web/fkdb-host.mjs`
- Modify: `Decision Field Operator Lab/fkdb/web/capabilities.json`
- Modify: `Decision Field Operator Lab/test_fkdb_web_host.mjs`
- Modify: `Decision Field Operator Lab/test_fkdb_wasm_hif.py`

**Interfaces:**
- Consumes: current capability record from `detectCapabilities(root, declared)`.
- Produces:
  - `selectExecutionPath(capabilities, obligation) -> ExecutionReceipt`
  - `projectLegacyHostProfile(receipt) -> { tier, async, network, storage, worker, sharedMemory }`
  - `ExecutionReceipt = { schema, obligation, selected, considered, rejected, capabilities, remainder, invariants }`
- Existing `selectHostProfile(capabilities)` remains exported and delegates through the graph projection.

- [ ] **Step 1: Write failing Node tests for native-vs-browser Component distinction and deterministic overlap handling**

Add tests asserting:

```js
assert.equal(
  selectExecutionPath(
    caps({ wasmCore: true, componentNative03: true, componentBrowserTranspiled03: true, jspi: true }),
    "EXECUTE_COMPONENT"
  ).selected.kind,
  "COMPONENT_NATIVE_0_3"
);

const browser = selectExecutionPath(
  caps({ wasmCore: true, componentBrowserTranspiled03: true, jspi: true, fetch: true }),
  "EXECUTE_COMPONENT_IN_BROWSER"
);
assert.equal(browser.selected.kind, "COMPONENT_BROWSER_TRANSPILED_0_3");
assert.ok(browser.considered.includes("WASM_JSPI"));
assert.ok(browser.rejected.some((x) => x.kind === "COMPONENT_NATIVE_0_3"));
```

Also pin the existing legacy profile outputs for the current test fixtures.

- [ ] **Step 2: Run Node test and verify it fails**

Run:

```sh
node "Decision Field Operator Lab/test_fkdb_web_host.mjs"
```

Expected: FAIL because `selectExecutionPath`, `componentNative03`, and `componentBrowserTranspiled03` do not exist.

- [ ] **Step 3: Implement `host-capability-graph.mjs` and refactor `fkdb-host.mjs`**

Define exact obligations:

```text
EXECUTE_COMPONENT
EXECUTE_COMPONENT_IN_BROWSER
ASYNC_HOST_CALL
NETWORK_BYTES
PERSIST_BYTES
LOCAL_TOOL_ACCESS
```

Define path kinds at minimum:

```text
COMPONENT_NATIVE_0_3
COMPONENT_BROWSER_TRANSPILED_0_3
WASM_JSPI
WASM_PROMISE_HANDOFF
WASM_LEGACY_WEB
JS_MODERN_FALLBACK
JS_LEGACY_FALLBACK
NATIVE_RMAL_FALLBACK
UNRESOLVED
```

Selection must return all considered/rejected paths with reasons, not only the winner.

Update `capabilities.json` to replace the single ambiguous `componentModel03` declaration with:

```json
"componentNative03": "declared_binding",
"componentBrowserTranspiled03": "declared_binding"
```

Retain backward compatibility only inside `detectCapabilities(..., declared)`: a legacy `componentModel03: true` may set neither new capability automatically; it must appear in `remainder` as `LEGACY_COMPONENT_DECLARATION_AMBIGUOUS`.

- [ ] **Step 4: Add Python contract tests for capability names and ambiguity invariant**

Assert:
- both new Component capabilities are declared;
- `componentModel03` is no longer a canonical capability;
- `WASM_COMPONENT_0_3` remains available only as the legacy profile projection;
- no user-agent inspection exists.

- [ ] **Step 5: Run Node + Python host tests**

Run:

```sh
node "Decision Field Operator Lab/test_fkdb_web_host.mjs"
python -m unittest "Decision Field Operator Lab/test_fkdb_wasm_hif.py" -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```sh
git add "Decision Field Operator Lab/fkdb/web"         "Decision Field Operator Lab/test_fkdb_web_host.mjs"         "Decision Field Operator Lab/test_fkdb_wasm_hif.py"
git commit -m "FKDB: replace host tier with capability graph"
```

---

### Task 2: Define and validate the portable ToolCarrier bundle

**Files:**
- Create: `Decision Field Operator Lab/fkdb/tools/tool-carrier.schema.json`
- Create: `Decision Field Operator Lab/fkdb/tools/tool-bundle.schema.json`
- Create: `Decision Field Operator Lab/tools/fkdb_tool_carrier.py`
- Create: `Decision Field Operator Lab/test_fkdb_tool_carrier.py`

**Interfaces:**
- Produces:
  - `validate_tool_carrier(value: dict, *, max_payload_bytes: int) -> dict`
  - `load_tool_bundle(path: Path, *, max_bundle_bytes: int) -> dict`
  - `canonical_carrier_bytes(carrier: dict) -> bytes`
  - `sha256_hex(data: bytes) -> str`
- `ToolCarrier` canonical fields are exactly the spec fields:
  `carrier_id, tool_id, tool_version, adapter_kind, locality, source_identity, source_version, retrieved_at, payload_type, payload, content_hash, provenance, authority_scope, evidence_status, obligation, relations, cost, loss, remainder, recovery_path`.

- [ ] **Step 1: Write failing validation and round-trip tests**

Tests must cover:
- one valid minimal carrier;
- deterministic canonical serialization;
- SHA-256 matches payload bytes;
- duplicate carrier IDs rejected;
- wrong schema version rejected;
- missing `provenance`, `evidence_status`, or `recovery_path` rejected;
- hash mismatch rejected;
- payload and bundle size limits rejected;
- unknown locality rejected.

- [ ] **Step 2: Run tests and verify failure**

Run:

```sh
python -m unittest "Decision Field Operator Lab/test_fkdb_tool_carrier.py" -v
```

Expected: FAIL because the validator module and schemas do not exist.

- [ ] **Step 3: Implement stdlib-only carrier/bundle validation**

Use explicit validation code; do not add a JSON Schema runtime dependency. The schema files are interchange documentation and are checked structurally by the unit tests.

Bundle schema:

```text
fkdb/tool-bundle/v1
manifest
carriers[]
attachments[]
```

Attachments are content-addressed and referenced by SHA-256; they are never trusted by filename alone.

- [ ] **Step 4: Run carrier tests**

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```sh
git add "Decision Field Operator Lab/fkdb/tools"         "Decision Field Operator Lab/tools/fkdb_tool_carrier.py"         "Decision Field Operator Lab/test_fkdb_tool_carrier.py"
git commit -m "FKDB: add portable ToolCarrier bundle contract"
```

---

### Task 3: Build the loopback-only Local Tool Bridge core

**Files:**
- Create: `Decision Field Operator Lab/tools/fkdb_local_tool_bridge.py`
- Create: `Decision Field Operator Lab/fkdb/tools/local-tool-policy.json`
- Create: `Decision Field Operator Lab/test_fkdb_local_tool_bridge.py`

**Interfaces:**
- Consumes: validated ToolCarrier bundles from Task 2.
- Produces:
  - `BridgePolicy.load(path: Path) -> BridgePolicy`
  - `BridgePolicy.resolve_allowed_path(path: Path, mode: str) -> Path`
  - `BridgePolicy.validate_loopback_url(url: str) -> str`
  - `BridgePolicy.validate_process(executable: Path, argv: list[str]) -> ProcessGrant`
  - `run_bridge(bind="127.0.0.1", port=0, web_root=...) -> BridgeReceipt`
- HTTP API v1:
  - `GET /fkdb-tool-bridge/v1/status`
  - `GET /fkdb-tool-bridge/v1/tools`
  - `POST /fkdb-tool-bridge/v1/import`
  - `POST /fkdb-tool-bridge/v1/run`
- The bridge also serves the FKDB Web root so the browser UI and bridge API are same-origin.

- [ ] **Step 1: Write failing security/unit tests**

Pin these behaviors:
- bind address other than `127.0.0.1` or `::1` is rejected;
- `http://127.0.0.1` and `http://[::1]` are accepted by loopback policy;
- `http://localhost.evil.example`, private LAN IPs, and public IPs are rejected;
- `..` path escape rejected;
- symlink resolving outside an allowed root rejected;
- process execution rejected when no allowlist entry exists;
- executable path must resolve exactly to allowlisted identity;
- argv is passed as a vector with `shell=False`; metacharacters remain ordinary argument bytes;
- mutating/run requests without the bridge token are denied;
- bridge token is random per launch and absent from URLs/log receipts;
- imported ToolCarrier is validated before acknowledgement.

- [ ] **Step 2: Run bridge tests and verify failure**

Run:

```sh
python -m unittest "Decision Field Operator Lab/test_fkdb_local_tool_bridge.py" -v
```

Expected: FAIL because bridge implementation/policy do not exist.

- [ ] **Step 3: Implement the bridge core**

Use `http.server.ThreadingHTTPServer`, `secrets.token_urlsafe(32)`, `ipaddress`, `urllib.parse`, `pathlib.Path.resolve()`, `subprocess.run(..., shell=False)`, and explicit timeouts.

Default `local-tool-policy.json`:
- network policy `LOOPBACK_ONLY`;
- no process allowlist entries;
- read/write roots empty;
- max import bytes and request bytes explicitly bounded;
- environment allowlist empty.

For browser calls:
- require exact bridge Origin;
- require `X-FKDB-Bridge-Token` for POST/run/import;
- return no permissive wildcard CORS headers.

- [ ] **Step 4: Add one harmless process fixture inside the test only**

Use the current Python executable plus a temporary fixture script as the allowlisted test process. Do not add a default production process grant.

- [ ] **Step 5: Run bridge + carrier tests**

Expected: PASS.

- [ ] **Step 6: Commit**

```sh
git add "Decision Field Operator Lab/tools/fkdb_local_tool_bridge.py"         "Decision Field Operator Lab/fkdb/tools/local-tool-policy.json"         "Decision Field Operator Lab/test_fkdb_local_tool_bridge.py"
git commit -m "FKDB: add loopback-only Local Tool Bridge core"
```

---

### Task 4: Extend Wasm-HIF with the Local Tool Bridge contract

**Files:**
- Modify: `Decision Field Operator Lab/fkdb/wasm/wit/0.3/fkdb-hif.wit`
- Modify: `Decision Field Operator Lab/fkdb/wasm/wit/0.2/fkdb-hif.wit`
- Modify: `Decision Field Operator Lab/test_fkdb_wasm_hif.py`

**Interfaces:**
- Consumes: ToolCarrier semantics from Task 2 and Local Tool Bridge capability semantics from Task 3.
- Produces WIT types/interfaces with the same logical fields in both tracks.

- [ ] **Step 1: Write failing WIT contract tests**

WASI 0.3 must contain:
- `enum tool-locality`;
- `record tool-descriptor`;
- `record tool-carrier`;
- `record import-request`;
- `record local-run-request`;
- `interface local-tools`;
- `import-artifact: async func(...)`;
- `run-local: async func(...)`;
- `world fkdb-browser` imports `local-tools`.

0.2 compatibility must contain the same logical records but no `async func`; it must expose operation resources with `poll`/finish semantics.

- [ ] **Step 2: Run Python contract test and verify failure**

Run:

```sh
python -m unittest "Decision Field Operator Lab/test_fkdb_wasm_hif.py" -v
```

Expected: FAIL because local-tool WIT interfaces are absent.

- [ ] **Step 3: Extend both WIT packages**

Do not add vendor names to WIT. Keep the interface generic and ToolCarrier-based.

- [ ] **Step 4: Run WIT contract tests**

Expected: PASS.

- [ ] **Step 5: Commit**

```sh
git add "Decision Field Operator Lab/fkdb/wasm/wit"         "Decision Field Operator Lab/test_fkdb_wasm_hif.py"
git commit -m "FKDB: add local-tool Wasm-HIF contract"
```

---

### Task 5: Add browser bridge client and TOOLS status surface

**Files:**
- Create: `Decision Field Operator Lab/fkdb/web/local-tool-client.mjs`
- Modify: `Decision Field Operator Lab/fkdb/web/index.html`
- Modify: `Decision Field Operator Lab/fkdb/pages/manifest.json`
- Modify: `Decision Field Operator Lab/tools/build_fkdb_pages.py`
- Modify: `Decision Field Operator Lab/test_fkdb_web_host.mjs`
- Modify: `Decision Field Operator Lab/test_fkdb_manifest.py`
- Modify: `Decision Field Operator Lab/test_fkdb_surface.py`

**Interfaces:**
- Consumes bridge endpoints from Task 3.
- Produces:
  - `discoverLocalToolBridge({ root, token }) -> ToolBridgeStatus`
  - `listLocalTools(bridge) -> ToolDescriptor[]`
  - visible FKDB `TOOLS` page/status shell.

- [ ] **Step 1: Write failing browser client tests**

Use a fake `fetch` root and assert:
- bridge unavailable => `{ state: "UNAVAILABLE", remainder: ["LOCAL_TOOL_BRIDGE_UNAVAILABLE"] }`;
- 200 status with valid receipt => `AVAILABLE`;
- malformed bridge schema => `DEGRADED`, never silently accepted;
- mutating requests attach token in `X-FKDB-Bridge-Token`, never query string;
- remote URL is never generated by the client.

- [ ] **Step 2: Write failing page/manifest tests for TOOLS**

Add `tools` page to manifest:
- role `LOCAL_TOOL_STATUS`;
- relation from `fkdb` to `tools`;
- relation from `tools` back to `fkdb`;
- provenance points to the local-tool integration spec;
- page remains useful when all tools are unavailable.

Update generated bounded page text to show `TOOLS` without exceeding current 160x64 constraints.

- [ ] **Step 3: Run browser + page tests and verify failure**

Run:

```sh
node "Decision Field Operator Lab/test_fkdb_web_host.mjs"
python -m unittest "Decision Field Operator Lab/test_fkdb_manifest.py" -v
python -m unittest "Decision Field Operator Lab/test_fkdb_surface.py" -v
```

Expected: FAIL for missing client/page.

- [ ] **Step 4: Implement bridge client and TOOLS page**

The modern `web/index.html` may show richer tool descriptors. The inherited tiny Independent Browser page remains a bounded status/navigation surface.

Do not prompt for remote sign-in when bridge/tool state is unavailable.

- [ ] **Step 5: Run browser/page tests**

Expected: PASS.

- [ ] **Step 6: Commit**

```sh
git add "Decision Field Operator Lab/fkdb/web"         "Decision Field Operator Lab/fkdb/pages"         "Decision Field Operator Lab/tools/build_fkdb_pages.py"         "Decision Field Operator Lab/test_fkdb_web_host.mjs"         "Decision Field Operator Lab/test_fkdb_manifest.py"         "Decision Field Operator Lab/test_fkdb_surface.py"
git commit -m "FKDB: add local TOOLS discovery surface"
```

---

### Task 6: Gate Plan A in CI and record the achieved boundary

**Files:**
- Modify: `Decision Field Operator Lab/rmal-browser/CMakeLists.txt`
- Modify: `Decision Field Operator Lab/fkdb/CURRENT.md`
- Modify: `Decision Field Operator Lab/rmal-browser/README.md`
- Test: all Plan A tests plus existing FKDB/Independent Browser matrix.

**Interfaces:**
- Consumes all prior Plan A artifacts.
- Produces one reproducible verification boundary for PR #116.

- [ ] **Step 1: Add CTest entries**

Add:
- `fkdb_tool_carrier`
- `fkdb_local_tool_bridge`

Existing Node/Wasm-HIF and browser-surface tests remain the gates for Tasks 1, 4, and 5.

- [ ] **Step 2: Run the focused Plan A matrix locally/CI-compatible**

Run:

```sh
python -m unittest "Decision Field Operator Lab/test_fkdb_tool_carrier.py" -v
python -m unittest "Decision Field Operator Lab/test_fkdb_local_tool_bridge.py" -v
python -m unittest "Decision Field Operator Lab/test_fkdb_wasm_hif.py" -v
node "Decision Field Operator Lab/test_fkdb_web_host.mjs"
python -m unittest "Decision Field Operator Lab/test_fkdb_manifest.py" -v
python -m unittest "Decision Field Operator Lab/test_fkdb_surface.py" -v
```

Expected: PASS.

- [ ] **Step 3: Run the dedicated browser CTest matrix**

Run the existing documented configure/build/CTest sequence for `Decision Field Operator Lab/rmal-browser`.

Expected:
- all predecessor browser tests still pass;
- all current FKDB tests still pass;
- new Plan A tests pass.

- [ ] **Step 4: Update `CURRENT.md` and README only after verification**

Record F10 Plan A as implemented only if the above tests pass. Preserve explicit remainder:
- no vendor adapters yet;
- no Component Model toolchain compilation yet unless separately proven;
- no remote synchronization;
- process allowlist empty by default.

- [ ] **Step 5: Commit**

```sh
git add "Decision Field Operator Lab/rmal-browser/CMakeLists.txt"         "Decision Field Operator Lab/fkdb/CURRENT.md"         "Decision Field Operator Lab/rmal-browser/README.md"
git commit -m "FKDB: verify core Local Tool Bridge boundary"
```

## Self-Review Result

- **Spec coverage:** Plan A covers capability graph, Local Tool Bridge, ToolCarrier, loopback-only policy, process/file allowlists, portable bundle envelope, WIT boundary, TOOLS status shell, and offline/static fallback. Vendor adapters are intentionally deferred to Plans B-D; cross-carrier index admission remains Plan E.
- **Type consistency:** `ToolCarrier`, `ExecutionReceipt`, bridge status, and WIT local-tool concepts have one named owner and are consumed by later tasks through those interfaces.
- **Security coverage:** loopback restriction, path traversal/symlink escape, token enforcement, process identity/argv, and malformed bundle tests are assigned explicitly.
- **Review Focus coverage:** all five listed failure classes are pinned to concrete tests.
- **Proportion:** six reviewable tasks; each produces a independently testable capability and can be rejected without invalidating unrelated later vendor adapters.
