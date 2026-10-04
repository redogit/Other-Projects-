export const EXECUTION_PATHS = Object.freeze({
  COMPONENT_NATIVE_0_3: "COMPONENT_NATIVE_0_3",
  COMPONENT_BROWSER_TRANSPILED_0_3: "COMPONENT_BROWSER_TRANSPILED_0_3",
  WASM_JSPI: "WASM_JSPI",
  WASM_PROMISE_HANDOFF: "WASM_PROMISE_HANDOFF",
  WASM_LEGACY_WEB: "WASM_LEGACY_WEB",
  JS_MODERN_FALLBACK: "JS_MODERN_FALLBACK",
  JS_LEGACY_FALLBACK: "JS_LEGACY_FALLBACK",
  NATIVE_RMAL_FALLBACK: "NATIVE_RMAL_FALLBACK",
  UNRESOLVED: "UNRESOLVED",
});

export const EXECUTION_OBLIGATIONS = Object.freeze([
  "EXECUTE_COMPONENT",
  "EXECUTE_COMPONENT_IN_BROWSER",
  "ASYNC_HOST_CALL",
  "NETWORK_BYTES",
  "PERSIST_BYTES",
  "LOCAL_TOOL_ACCESS",
]);

const INVARIANTS = Object.freeze([
  "FALLBACK != SILENT_SEMANTIC_WEAKENING",
  "HOST_CAPABILITY != AUTHORITY",
  "CANONICAL_ABI_TRANSLATION != EVIDENCE_TRANSFER",
  "ASYNC_RESUME != SUCCESS",
  "UNRESOLVED != NEGATIVE",
]);

function available(capabilities, key) {
  return capabilities?.[key] === true;
}

function candidate(kind, ok, reason) {
  return Object.freeze({ kind, ok, reason });
}

function componentCandidates(capabilities, browserOnly) {
  const native = candidate(
    EXECUTION_PATHS.COMPONENT_NATIVE_0_3,
    !browserOnly &&
      available(capabilities, "wasmCore") &&
      available(capabilities, "componentNative03"),
    browserOnly
      ? "NATIVE_COMPONENT_HOST_NOT_BROWSER_PATH"
      : available(capabilities, "componentNative03")
        ? available(capabilities, "wasmCore")
          ? "AVAILABLE"
          : "WASM_CORE_UNAVAILABLE"
        : "NATIVE_COMPONENT_HOST_UNAVAILABLE"
  );

  const transpiled = candidate(
    EXECUTION_PATHS.COMPONENT_BROWSER_TRANSPILED_0_3,
    available(capabilities, "wasmCore") &&
      available(capabilities, "componentBrowserTranspiled03"),
    available(capabilities, "componentBrowserTranspiled03")
      ? available(capabilities, "wasmCore")
        ? "AVAILABLE"
        : "WASM_CORE_UNAVAILABLE"
      : "BROWSER_TRANSPILED_COMPONENT_UNAVAILABLE"
  );

  const jspi = candidate(
    EXECUTION_PATHS.WASM_JSPI,
    false,
    available(capabilities, "jspi")
      ? "CORE_WASM_ASYNC_NOT_COMPONENT_EQUIVALENT"
      : "JSPI_UNAVAILABLE"
  );

  const promise = candidate(
    EXECUTION_PATHS.WASM_PROMISE_HANDOFF,
    false,
    available(capabilities, "wasmCore") && available(capabilities, "fetch")
      ? "CORE_WASM_PROMISE_HANDOFF_NOT_COMPONENT_EQUIVALENT"
      : "PROMISE_WASM_PATH_UNAVAILABLE"
  );

  return browserOnly
    ? [native, transpiled, jspi, promise]
    : [native, transpiled, jspi, promise];
}

function asyncCandidates(capabilities) {
  return [
    candidate(
      EXECUTION_PATHS.WASM_JSPI,
      available(capabilities, "wasmCore") && available(capabilities, "jspi"),
      available(capabilities, "jspi") ? "AVAILABLE" : "JSPI_UNAVAILABLE"
    ),
    candidate(
      EXECUTION_PATHS.WASM_PROMISE_HANDOFF,
      available(capabilities, "wasmCore") &&
        (available(capabilities, "fetch") ||
          available(capabilities, "componentNative03") ||
          available(capabilities, "componentBrowserTranspiled03")),
      "EXPLICIT_PROMISE_HANDOFF"
    ),
    candidate(
      EXECUTION_PATHS.JS_MODERN_FALLBACK,
      available(capabilities, "fetch"),
      "MODERN_JS_ASYNC"
    ),
    candidate(
      EXECUTION_PATHS.JS_LEGACY_FALLBACK,
      available(capabilities, "xhr"),
      "LEGACY_CALLBACK_ASYNC"
    ),
    candidate(
      EXECUTION_PATHS.NATIVE_RMAL_FALLBACK,
      true,
      "NATIVE_OUTER_CONTROLLER"
    ),
  ];
}

function networkCandidates(capabilities) {
  return [
    candidate(
      EXECUTION_PATHS.COMPONENT_NATIVE_0_3,
      available(capabilities, "componentNative03") &&
        available(capabilities, "wasiHttp03"),
      "WASI_HTTP_0_3_NATIVE"
    ),
    candidate(
      EXECUTION_PATHS.COMPONENT_BROWSER_TRANSPILED_0_3,
      available(capabilities, "componentBrowserTranspiled03") &&
        available(capabilities, "wasiHttp03"),
      "WASI_HTTP_0_3_BROWSER_TRANSPILED"
    ),
    candidate(
      EXECUTION_PATHS.WASM_PROMISE_HANDOFF,
      available(capabilities, "wasmCore") && available(capabilities, "fetch"),
      "FETCH_HOST_HANDOFF"
    ),
    candidate(
      EXECUTION_PATHS.WASM_LEGACY_WEB,
      available(capabilities, "wasmCore") &&
        (available(capabilities, "xhr") ||
          available(capabilities, "wasiHttp02")),
      "LEGACY_WASM_NETWORK"
    ),
    candidate(
      EXECUTION_PATHS.JS_MODERN_FALLBACK,
      available(capabilities, "fetch"),
      "FETCH"
    ),
    candidate(
      EXECUTION_PATHS.JS_LEGACY_FALLBACK,
      available(capabilities, "xhr"),
      "XHR"
    ),
    candidate(
      EXECUTION_PATHS.NATIVE_RMAL_FALLBACK,
      true,
      "NATIVE_RMAL_HTTP_TLS"
    ),
  ];
}

function persistenceCandidates(capabilities) {
  return [
    candidate(
      EXECUTION_PATHS.COMPONENT_NATIVE_0_3,
      available(capabilities, "componentNative03") &&
        available(capabilities, "wasiFilesystem03"),
      "WASI_FILESYSTEM_0_3_NATIVE"
    ),
    candidate(
      EXECUTION_PATHS.COMPONENT_BROWSER_TRANSPILED_0_3,
      available(capabilities, "componentBrowserTranspiled03") &&
        (available(capabilities, "opfs") ||
          available(capabilities, "indexedDb")),
      "BROWSER_COMPONENT_PERSISTENCE"
    ),
    candidate(
      EXECUTION_PATHS.WASM_PROMISE_HANDOFF,
      available(capabilities, "wasmCore") &&
        (available(capabilities, "opfs") ||
          available(capabilities, "indexedDb")),
      "WASM_BROWSER_STORAGE_HANDOFF"
    ),
    candidate(
      EXECUTION_PATHS.WASM_LEGACY_WEB,
      available(capabilities, "wasmCore") &&
        available(capabilities, "emscriptenWasmFs"),
      "WASMFS_OR_IDBFS"
    ),
    candidate(
      EXECUTION_PATHS.JS_MODERN_FALLBACK,
      available(capabilities, "opfs") ||
        available(capabilities, "indexedDb"),
      "WEB_STORAGE"
    ),
    candidate(
      EXECUTION_PATHS.NATIVE_RMAL_FALLBACK,
      true,
      "NATIVE_OR_MEMORY_PERSISTENCE"
    ),
  ];
}

function candidatesFor(capabilities, obligation) {
  switch (obligation) {
    case "EXECUTE_COMPONENT":
      return componentCandidates(capabilities, false);
    case "EXECUTE_COMPONENT_IN_BROWSER":
      return componentCandidates(capabilities, true);
    case "ASYNC_HOST_CALL":
      return asyncCandidates(capabilities);
    case "NETWORK_BYTES":
      return networkCandidates(capabilities);
    case "PERSIST_BYTES":
      return persistenceCandidates(capabilities);
    case "LOCAL_TOOL_ACCESS":
      return [
        candidate(
          EXECUTION_PATHS.UNRESOLVED,
          true,
          "LOCAL_TOOL_BRIDGE_NOT_IMPLEMENTED"
        ),
      ];
    default:
      return [
        candidate(
          EXECUTION_PATHS.UNRESOLVED,
          true,
          "UNKNOWN_EXECUTION_OBLIGATION"
        ),
      ];
  }
}

export function selectExecutionPath(capabilities, obligation) {
  const candidates = candidatesFor(capabilities, obligation);
  const selected =
    candidates.find((entry) => entry.ok) ??
    candidate(EXECUTION_PATHS.UNRESOLVED, true, "NO_LAWFUL_PATH");

  const remainder = Array.isArray(capabilities?.remainder)
    ? [...capabilities.remainder]
    : [];
  if (selected.kind === EXECUTION_PATHS.UNRESOLVED) {
    remainder.push(selected.reason);
  }

  return Object.freeze({
    schema: "fkdb/wasm-hif-execution-receipt/v1",
    obligation,
    selected: Object.freeze({
      kind: selected.kind,
      reason: selected.reason,
    }),
    considered: Object.freeze(candidates.map((entry) => entry.kind)),
    rejected: Object.freeze(
      candidates
        .filter((entry) => entry.kind !== selected.kind || !entry.ok)
        .map((entry) =>
          Object.freeze({ kind: entry.kind, reason: entry.reason })
        )
    ),
    capabilities,
    remainder: Object.freeze([...new Set(remainder)]),
    invariants: INVARIANTS,
  });
}

export function projectLegacyHostProfile(receipt, capabilities) {
  let tier;
  if (
    capabilities.componentNative03 ||
    capabilities.componentBrowserTranspiled03 ||
    capabilities.componentModel03
  ) {
    tier = "WASM_COMPONENT_0_3";
  } else if (capabilities.wasmCore && capabilities.jspi) {
    tier = "WASM_JSPI";
  } else if (capabilities.wasmCore && capabilities.fetch) {
    tier = "WASM_PROMISE_HANDOFF";
  } else if (
    capabilities.wasmCore &&
    (capabilities.xhr || capabilities.emscriptenWasmFs)
  ) {
    tier = "WASM_LEGACY_WEB";
  } else if (capabilities.fetch) {
    tier = "JS_MODERN_FALLBACK";
  } else if (capabilities.xhr || capabilities.indexedDb) {
    tier = "JS_LEGACY_FALLBACK";
  } else {
    tier = "NATIVE_RMAL_FALLBACK";
  }

  return Object.freeze({
    tier,
    async: capabilities.jspi
      ? "JSPI"
      : capabilities.fetch ||
          capabilities.componentNative03 ||
          capabilities.componentBrowserTranspiled03 ||
          capabilities.componentModel03
        ? "EXPLICIT_PROMISE_HANDOFF"
        : "CALLBACK_OR_OUTER_CONTROLLER",
    network: null,
    storage: null,
    worker: capabilities.worker ? "WORKER" : "MAIN_THREAD_COOPERATIVE",
    sharedMemory: capabilities.sharedMemory ? "AVAILABLE" : "UNAVAILABLE",
    executionReceipt: receipt,
  });
}
