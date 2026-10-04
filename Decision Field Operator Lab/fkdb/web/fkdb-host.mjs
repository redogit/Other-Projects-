import {
  projectLegacyHostProfile,
  selectExecutionPath as selectExecutionPathFromGraph,
} from "./host-capability-graph.mjs";

export { EXECUTION_OBLIGATIONS, EXECUTION_PATHS } from "./host-capability-graph.mjs";

export const HOST_TIERS = Object.freeze({
  WASM_COMPONENT_0_3: "WASM_COMPONENT_0_3",
  WASM_JSPI: "WASM_JSPI",
  WASM_PROMISE_HANDOFF: "WASM_PROMISE_HANDOFF",
  WASM_LEGACY_WEB: "WASM_LEGACY_WEB",
  JS_MODERN_FALLBACK: "JS_MODERN_FALLBACK",
  JS_LEGACY_FALLBACK: "JS_LEGACY_FALLBACK",
  NATIVE_RMAL_FALLBACK: "NATIVE_RMAL_FALLBACK",
});

export function detectCapabilities(root = globalThis, declared = {}) {
  const wasm = root.WebAssembly;
  const navigatorObject = root.navigator;

  return Object.freeze({
    wasmCore:
      typeof wasm?.instantiate === "function" ||
      typeof wasm?.Instance === "function",
    wasmStreaming:
      typeof wasm?.instantiateStreaming === "function" ||
      typeof wasm?.compileStreaming === "function",
    jspi:
      typeof wasm?.Suspending === "function" &&
      typeof wasm?.promising === "function",
    fetch: typeof root.fetch === "function",
    streams: typeof root.ReadableStream === "function",
    worker: typeof root.Worker === "function",
    sharedMemory:
      typeof root.SharedArrayBuffer === "function" &&
      root.crossOriginIsolated === true,
    opfs: typeof navigatorObject?.storage?.getDirectory === "function",
    indexedDb: typeof root.indexedDB !== "undefined",
    xhr: typeof root.XMLHttpRequest === "function",
    abortController: typeof root.AbortController === "function",
    textCodec:
      typeof root.TextEncoder === "function" &&
      typeof root.TextDecoder === "function",
    componentNative03: declared.componentNative03 === true,
    componentBrowserTranspiled03:
      declared.componentBrowserTranspiled03 === true,
    wasiHttp03: declared.wasiHttp03 === true,
    wasiHttp02: declared.wasiHttp02 === true,
    wasiFilesystem03: declared.wasiFilesystem03 === true,
    emscriptenWasmFs: declared.emscriptenWasmFs === true,
    localToolBridge: declared.localToolBridge === true,
    remainder:
      declared.componentModel03 === true
        ? Object.freeze(["LEGACY_COMPONENT_DECLARATION_AMBIGUOUS"])
        : Object.freeze([]),
  });
}

export function selectAsyncStrategy(capabilities) {
  if (capabilities.jspi) return "JSPI";
  if (
    capabilities.fetch ||
    capabilities.componentNative03 ||
    capabilities.componentBrowserTranspiled03 ||
    capabilities.componentModel03
  ) {
    return "EXPLICIT_PROMISE_HANDOFF";
  }
  return "CALLBACK_OR_OUTER_CONTROLLER";
}

export function selectNetworkStrategy(capabilities) {
  if (
    (capabilities.componentNative03 ||
      capabilities.componentBrowserTranspiled03 ||
      capabilities.componentModel03) &&
    capabilities.wasiHttp03
  ) {
    return "WASI_HTTP_0_3";
  }
  if (capabilities.fetch && capabilities.streams) return "FETCH_STREAMS";
  if (capabilities.fetch) return "FETCH";
  if (capabilities.wasmCore && capabilities.wasiHttp02) {
    return "WASI_HTTP_0_2";
  }
  if (capabilities.xhr) return "XHR";
  return "NATIVE_RMAL_HTTP_TLS";
}

export function selectStorageStrategy(capabilities) {
  if (
    (capabilities.componentNative03 ||
      capabilities.componentBrowserTranspiled03 ||
      capabilities.componentModel03) &&
    capabilities.wasiFilesystem03
  ) {
    return "WASI_FILESYSTEM_0_3";
  }
  if (capabilities.opfs) return "OPFS";
  if (capabilities.indexedDb) return "INDEXED_DB";
  if (capabilities.emscriptenWasmFs) return "WASMFS_OR_IDBFS";
  return "MEMORY";
}

export function selectExecutionPath(capabilities, obligation) {
  return selectExecutionPathFromGraph(capabilities, obligation);
}

export function selectHostProfile(capabilities) {
  const compatibilityCapabilities =
    capabilities.componentModel03 === true &&
    !capabilities.componentNative03 &&
    !capabilities.componentBrowserTranspiled03
      ? { ...capabilities, componentNative03: true }
      : capabilities;

  const receipt = selectExecutionPathFromGraph(
    compatibilityCapabilities,
    "NETWORK_BYTES"
  );
  const projected = projectLegacyHostProfile(receipt, compatibilityCapabilities);
  return Object.freeze({
    ...projected,
    async: selectAsyncStrategy(capabilities),
    network: selectNetworkStrategy(capabilities),
    storage: selectStorageStrategy(capabilities),
  });
}

export function createWasmAsyncBoundary(wasmNamespace = globalThis.WebAssembly) {
  const available =
    typeof wasmNamespace?.Suspending === "function" &&
    typeof wasmNamespace?.promising === "function";

  return Object.freeze({
    mode: available ? "JSPI" : "EXPLICIT_HANDOFF",
    wrapImport(fn) {
      if (!available) {
        throw new Error(
          "JSPI unavailable: use FKDB explicit Promise/outer-controller handoff"
        );
      }
      return new wasmNamespace.Suspending(fn);
    },
    wrapExport(fn) {
      if (!available) {
        throw new Error(
          "JSPI unavailable: use FKDB explicit Promise/outer-controller handoff"
        );
      }
      return wasmNamespace.promising(fn);
    },
  });
}

function normalizeBytes(value) {
  if (value instanceof Uint8Array) return value;
  if (value instanceof ArrayBuffer) return new Uint8Array(value);
  if (ArrayBuffer.isView(value)) {
    return new Uint8Array(value.buffer, value.byteOffset, value.byteLength);
  }
  throw new TypeError("FKDB byte value must be ArrayBuffer or Uint8Array-compatible");
}

export async function fetchBytes(
  url,
  { root = globalThis, signal = undefined } = {}
) {
  if (typeof root.fetch === "function") {
    const response = await root.fetch(url, { signal });
    if (!response.ok) {
      throw new Error(`FKDB fetch failed: HTTP ${response.status}`);
    }
    return new Uint8Array(await response.arrayBuffer());
  }

  if (typeof root.XMLHttpRequest === "function") {
    return new Promise((resolve, reject) => {
      const request = new root.XMLHttpRequest();
      request.open("GET", url, true);
      request.responseType = "arraybuffer";
      request.onload = () => {
        if (request.status >= 200 && request.status < 300) {
          resolve(new Uint8Array(request.response));
        } else {
          reject(new Error(`FKDB XHR failed: HTTP ${request.status}`));
        }
      };
      request.onerror = () => reject(new Error("FKDB XHR transport failed"));
      request.send();
    });
  }

  throw new Error("FKDB web network unavailable; use native RMAL HTTP/TLS carrier");
}

function safeKey(key) {
  if (typeof key !== "string" || key.length === 0) {
    throw new TypeError("FKDB storage key must be a non-empty string");
  }
  return encodeURIComponent(key);
}

function memoryStore() {
  const values = new Map();
  return Object.freeze({
    kind: "MEMORY",
    async get(key) {
      const value = values.get(key);
      return value ? value.slice() : null;
    },
    async put(key, bytes) {
      values.set(key, normalizeBytes(bytes).slice());
    },
  });
}

async function opfsStore(root) {
  const directory = await root.navigator.storage.getDirectory();
  const fkdb = await directory.getDirectoryHandle("fkdb", { create: true });
  return Object.freeze({
    kind: "OPFS",
    async get(key) {
      try {
        const handle = await fkdb.getFileHandle(safeKey(key));
        const file = await handle.getFile();
        return new Uint8Array(await file.arrayBuffer());
      } catch (error) {
        if (error?.name === "NotFoundError") return null;
        throw error;
      }
    },
    async put(key, bytes) {
      const handle = await fkdb.getFileHandle(safeKey(key), { create: true });
      const writer = await handle.createWritable();
      await writer.write(normalizeBytes(bytes));
      await writer.close();
    },
  });
}

function openIndexedDb(indexedDB) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("fkdb", 1);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains("records")) {
        request.result.createObjectStore("records");
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function indexedDbStore(root) {
  const db = await openIndexedDb(root.indexedDB);
  function request(mode, action) {
    return new Promise((resolve, reject) => {
      const tx = db.transaction("records", mode);
      const store = tx.objectStore("records");
      const operation = action(store);
      operation.onsuccess = () => resolve(operation.result ?? null);
      operation.onerror = () => reject(operation.error);
    });
  }
  return Object.freeze({
    kind: "INDEXED_DB",
    async get(key) {
      const value = await request("readonly", (store) => store.get(key));
      return value == null ? null : normalizeBytes(value);
    },
    async put(key, bytes) {
      await request("readwrite", (store) =>
        store.put(normalizeBytes(bytes), key)
      );
    },
  });
}

export async function createByteStore(
  capabilities,
  { root = globalThis } = {}
) {
  const strategy = selectStorageStrategy(capabilities);
  if (strategy === "OPFS") return opfsStore(root);
  if (strategy === "INDEXED_DB") return indexedDbStore(root);
  return memoryStore();
}

export function buildHostReceipt(capabilities) {
  const profile = selectHostProfile(capabilities);
  return Object.freeze({
    schema: "fkdb/wasm-hif-host-receipt/v1",
    profile,
    capabilities,
    invariants: [
      "FALLBACK != SILENT_SEMANTIC_WEAKENING",
      "HOST_CAPABILITY != AUTHORITY",
      "ASYNC_RESUME != SUCCESS",
      "NETWORK_RESPONSE != ADMITTED_KNOWLEDGE",
      "PERSISTED_BYTES != RECONSTRUCTIBLE_MEANING",
    ],
  });
}
