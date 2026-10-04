import assert from "node:assert/strict";

import * as fkdbHost from "./fkdb/web/fkdb-host.mjs";

import {
  HOST_TIERS,
  buildHostReceipt,
  createByteStore,
  createWasmAsyncBoundary,
  detectCapabilities,
  fetchBytes,
  selectHostProfile,
  selectNetworkStrategy,
  selectStorageStrategy,
} from "./fkdb/web/fkdb-host.mjs";

assert.equal(
  typeof fkdbHost.selectExecutionPath,
  "function",
  "selectExecutionPath must be exported by the Wasm-HIF host"
);

const graphNative = fkdbHost.selectExecutionPath(
  caps({
    wasmCore: true,
    componentNative03: true,
    componentBrowserTranspiled03: true,
    jspi: true,
  }),
  "EXECUTE_COMPONENT"
);
assert.equal(graphNative.selected.kind, "COMPONENT_NATIVE_0_3");

const graphBrowser = fkdbHost.selectExecutionPath(
  caps({
    wasmCore: true,
    componentBrowserTranspiled03: true,
    jspi: true,
    fetch: true,
  }),
  "EXECUTE_COMPONENT_IN_BROWSER"
);
assert.equal(graphBrowser.selected.kind, "COMPONENT_BROWSER_TRANSPILED_0_3");
assert.ok(graphBrowser.considered.includes("WASM_JSPI"));
assert.ok(
  graphBrowser.rejected.some((entry) => entry.kind === "COMPONENT_NATIVE_0_3")
);

const graphLegacyAmbiguous = fkdbHost.detectCapabilities({}, {
  componentModel03: true,
});
assert.equal(graphLegacyAmbiguous.componentNative03, false);
assert.equal(graphLegacyAmbiguous.componentBrowserTranspiled03, false);
assert.ok(
  graphLegacyAmbiguous.remainder.includes(
    "LEGACY_COMPONENT_DECLARATION_AMBIGUOUS"
  )
);

function caps(overrides = {}) {
  return {
    wasmCore: false,
    wasmStreaming: false,
    jspi: false,
    fetch: false,
    streams: false,
    worker: false,
    sharedMemory: false,
    opfs: false,
    indexedDb: false,
    xhr: false,
    abortController: false,
    textCodec: false,
    componentModel03: false,
    componentNative03: false,
    componentBrowserTranspiled03: false,
    wasiHttp03: false,
    wasiHttp02: false,
    wasiFilesystem03: false,
    emscriptenWasmFs: false,
    ...overrides,
  };
}

assert.equal(
  selectHostProfile(
    caps({
      wasmCore: true,
      componentModel03: true,
      wasiHttp03: true,
      wasiFilesystem03: true,
    })
  ).tier,
  HOST_TIERS.WASM_COMPONENT_0_3
);

assert.equal(
  selectHostProfile(caps({ wasmCore: true, jspi: true, fetch: true })).tier,
  HOST_TIERS.WASM_JSPI
);

assert.equal(
  selectHostProfile(caps({ wasmCore: true, fetch: true })).tier,
  HOST_TIERS.WASM_PROMISE_HANDOFF
);

assert.equal(
  selectHostProfile(caps({ wasmCore: true, xhr: true })).tier,
  HOST_TIERS.WASM_LEGACY_WEB
);

assert.equal(
  selectHostProfile(caps({ fetch: true })).tier,
  HOST_TIERS.JS_MODERN_FALLBACK
);

assert.equal(
  selectHostProfile(caps({ xhr: true })).tier,
  HOST_TIERS.JS_LEGACY_FALLBACK
);

assert.equal(
  selectHostProfile(caps()).tier,
  HOST_TIERS.NATIVE_RMAL_FALLBACK
);

assert.equal(
  selectNetworkStrategy(
    caps({ wasmCore: true, componentModel03: true, wasiHttp03: true })
  ),
  "WASI_HTTP_0_3"
);
assert.equal(
  selectNetworkStrategy(caps({ fetch: true, streams: true })),
  "FETCH_STREAMS"
);
assert.equal(selectNetworkStrategy(caps({ fetch: true })), "FETCH");
assert.equal(
  selectNetworkStrategy(caps({ wasmCore: true, wasiHttp02: true })),
  "WASI_HTTP_0_2"
);
assert.equal(selectNetworkStrategy(caps({ xhr: true })), "XHR");
assert.equal(selectNetworkStrategy(caps()), "NATIVE_RMAL_HTTP_TLS");

assert.equal(
  selectStorageStrategy(
    caps({ componentModel03: true, wasiFilesystem03: true })
  ),
  "WASI_FILESYSTEM_0_3"
);
assert.equal(selectStorageStrategy(caps({ opfs: true })), "OPFS");
assert.equal(selectStorageStrategy(caps({ indexedDb: true })), "INDEXED_DB");
assert.equal(
  selectStorageStrategy(caps({ emscriptenWasmFs: true })),
  "WASMFS_OR_IDBFS"
);
assert.equal(selectStorageStrategy(caps()), "MEMORY");

const fakeRoot = {
  WebAssembly: {
    instantiate() {},
    instantiateStreaming() {},
    classMarker: true,
    Suspending: class Suspending {
      constructor(fn) {
        this.fn = fn;
      }
    },
    promising(fn) {
      return (...args) => Promise.resolve(fn(...args));
    },
  },
  fetch() {},
  ReadableStream: class {},
  Worker: class {},
  SharedArrayBuffer: class {},
  crossOriginIsolated: true,
  navigator: { storage: { getDirectory() {} } },
  indexedDB: {},
  XMLHttpRequest: class {},
  AbortController: class {},
  TextEncoder: class {},
  TextDecoder: class {},
};

const detected = detectCapabilities(fakeRoot, {
  componentNative03: true,
  wasiHttp03: true,
});
assert.equal(detected.wasmCore, true);
assert.equal(detected.jspi, true);
assert.equal(detected.fetch, true);
assert.equal(detected.streams, true);
assert.equal(detected.worker, true);
assert.equal(detected.sharedMemory, true);
assert.equal(detected.opfs, true);
assert.equal(detected.componentNative03, true);
assert.equal(detected.componentBrowserTranspiled03, false);
assert.equal(detected.wasiHttp03, true);

const boundary = createWasmAsyncBoundary(fakeRoot.WebAssembly);
assert.equal(boundary.mode, "JSPI");
const suspended = boundary.wrapImport((value) => Promise.resolve(value + 1));
assert.equal(typeof suspended.fn, "function");
const promised = boundary.wrapExport((value) => value + 1);
assert.equal(await promised(41), 42);

const fallbackBoundary = createWasmAsyncBoundary({});
assert.equal(fallbackBoundary.mode, "EXPLICIT_HANDOFF");
assert.throws(() => fallbackBoundary.wrapImport(() => {}), /JSPI unavailable/);
assert.throws(() => fallbackBoundary.wrapExport(() => {}), /JSPI unavailable/);

const fetchRoot = {
  async fetch() {
    return {
      ok: true,
      status: 200,
      async arrayBuffer() {
        return Uint8Array.from([1, 2, 3]).buffer;
      },
    };
  },
};
assert.deepEqual(
  Array.from(await fetchBytes("https://example.invalid", { root: fetchRoot })),
  [1, 2, 3]
);

class FakeXHR {
  open() {}
  send() {
    this.status = 200;
    this.response = Uint8Array.from([4, 5]).buffer;
    this.onload();
  }
}
assert.deepEqual(
  Array.from(
    await fetchBytes("https://example.invalid", {
      root: { XMLHttpRequest: FakeXHR },
    })
  ),
  [4, 5]
);

const store = await createByteStore(caps(), { root: {} });
assert.equal(store.kind, "MEMORY");
assert.equal(await store.get("missing"), null);
await store.put("record", Uint8Array.from([7, 8, 9]));
assert.deepEqual(Array.from(await store.get("record")), [7, 8, 9]);

const receipt = buildHostReceipt(caps({ wasmCore: true, fetch: true }));
assert.equal(receipt.schema, "fkdb/wasm-hif-host-receipt/v1");
assert.equal(receipt.profile.tier, HOST_TIERS.WASM_PROMISE_HANDOFF);
assert.ok(receipt.invariants.includes("HOST_CAPABILITY != AUTHORITY"));

const emptyWasm = Uint8Array.from([0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00]);
assert.equal(WebAssembly.validate(emptyWasm), true);

console.log("FKDB_WASM_HIF_NODE PASS");
