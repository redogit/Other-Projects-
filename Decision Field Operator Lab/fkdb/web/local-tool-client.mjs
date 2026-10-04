const STATUS_PATH = "/fkdb-tool-bridge/v1/status";
const TOOLS_PATH = "/fkdb-tool-bridge/v1/tools";
const IMPORT_PATH = "/fkdb-tool-bridge/v1/import";
const RUN_PATH = "/fkdb-tool-bridge/v1/run";

function unavailable(remainder = "LOCAL_TOOL_BRIDGE_UNAVAILABLE", token = null) {
  return Object.freeze({
    state: "UNAVAILABLE",
    token,
    receipt: null,
    remainder: Object.freeze([remainder]),
  });
}

function degraded(receipt, remainder, token = null) {
  return Object.freeze({
    state: "DEGRADED",
    token,
    receipt: receipt ?? null,
    remainder: Object.freeze([remainder]),
  });
}

function isRelativeBridgePath(value) {
  return typeof value === "string" && value.startsWith("/") && !value.startsWith("//");
}

async function readJsonResponse(response) {
  if (!response?.ok) {
    throw new Error("local tool bridge request failed");
  }
  return response.json();
}

export async function discoverLocalToolBridge({
  root = globalThis,
  token = null,
} = {}) {
  if (typeof root?.fetch !== "function") {
    return unavailable("LOCAL_TOOL_BRIDGE_UNAVAILABLE", token);
  }

  try {
    if (!isRelativeBridgePath(STATUS_PATH)) {
      return degraded(null, "LOCAL_TOOL_BRIDGE_INVALID_CLIENT_PATH", token);
    }
    const response = await root.fetch(STATUS_PATH, {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
    });
    const receipt = await readJsonResponse(response);
    if (
      receipt?.schema !== "fkdb/local-tool-bridge-status/v1" ||
      receipt?.state !== "AVAILABLE" ||
      receipt?.network_policy !== "LOOPBACK_ONLY"
    ) {
      return degraded(receipt, "LOCAL_TOOL_BRIDGE_INVALID_RECEIPT", token);
    }

    const browserOrigin = root?.location?.origin;
    if (
      typeof browserOrigin === "string" &&
      browserOrigin &&
      typeof receipt.origin === "string" &&
      receipt.origin !== browserOrigin
    ) {
      return degraded(receipt, "LOCAL_TOOL_BRIDGE_ORIGIN_MISMATCH", token);
    }

    return Object.freeze({
      state: "AVAILABLE",
      token,
      receipt: Object.freeze({ ...receipt }),
      remainder: Object.freeze([]),
    });
  } catch {
    return unavailable("LOCAL_TOOL_BRIDGE_UNAVAILABLE", token);
  }
}

export async function listLocalTools(
  bridge,
  { root = globalThis } = {}
) {
  if (bridge?.state !== "AVAILABLE" || typeof root?.fetch !== "function") {
    return [];
  }
  const response = await root.fetch(TOOLS_PATH, {
    method: "GET",
    credentials: "same-origin",
    cache: "no-store",
  });
  const value = await readJsonResponse(response);
  if (
    value?.schema !== "fkdb/local-tool-list/v1" ||
    !Array.isArray(value.tools)
  ) {
    throw new Error("invalid local tool list receipt");
  }
  return value.tools;
}

function mutationHeaders(bridge) {
  if (
    bridge?.state !== "AVAILABLE" ||
    typeof bridge?.token !== "string" ||
    bridge.token.length === 0
  ) {
    throw new Error("local tool bridge capability token is required");
  }
  return {
    "Content-Type": "application/json",
    "X-FKDB-Bridge-Token": bridge.token,
  };
}

async function postBridge(path, bridge, body, root) {
  if (!isRelativeBridgePath(path)) {
    throw new Error("local tool bridge path must remain same-origin");
  }
  if (typeof root?.fetch !== "function") {
    throw new Error("fetch is unavailable");
  }
  const response = await root.fetch(path, {
    method: "POST",
    credentials: "same-origin",
    cache: "no-store",
    headers: mutationHeaders(bridge),
    body: JSON.stringify(body),
  });
  return readJsonResponse(response);
}

export async function importToolCarrier(
  bridge,
  carrier,
  { root = globalThis } = {}
) {
  return postBridge(IMPORT_PATH, bridge, { carrier }, root);
}

export async function runLocalTool(
  bridge,
  request,
  { root = globalThis } = {}
) {
  return postBridge(RUN_PATH, bridge, request, root);
}
