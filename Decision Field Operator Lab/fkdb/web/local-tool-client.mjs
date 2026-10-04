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

function isLiteralLoopbackHostname(hostname) {
  if (hostname === "::1" || hostname === "[::1]") return true;
  if (typeof hostname !== "string") return false;
  const parts = hostname.split(".");
  if (parts.length !== 4) return false;
  const numbers = parts.map((part) => {
    if (!/^[0-9]+$/.test(part)) return null;
    const value = Number(part);
    return Number.isInteger(value) && value >= 0 && value <= 255 ? value : null;
  });
  return numbers.every((value) => value !== null) && numbers[0] === 127;
}

function stringList(value, field) {
  if (
    !Array.isArray(value) ||
    !value.every((item) => typeof item === "string" && item.length > 0)
  ) {
    throw new Error(`invalid local tool descriptor ${field}`);
  }
  return Object.freeze([...value]);
}

function sanitizeToolDescriptor(value) {
  if (!value || typeof value !== "object") {
    throw new Error("invalid local tool descriptor");
  }
  for (const field of ["tool_id", "locality", "state"]) {
    if (typeof value[field] !== "string" || value[field].length === 0) {
      throw new Error(`invalid local tool descriptor ${field}`);
    }
  }
  return Object.freeze({
    tool_id: value.tool_id,
    locality: value.locality,
    state: value.state,
    capabilities: stringList(value.capabilities ?? [], "capabilities"),
    unresolved_requirements: stringList(
      value.unresolved_requirements ?? [],
      "unresolved_requirements"
    ),
  });
}

export function formatLocalToolDescriptor(value) {
  const tool = sanitizeToolDescriptor(value);
  const capabilities =
    tool.capabilities.length > 0 ? tool.capabilities.join(", ") : "NONE";
  const unresolved =
    tool.unresolved_requirements.length > 0
      ? tool.unresolved_requirements.join(", ")
      : "NONE";
  return (
    `${tool.tool_id} — ${tool.locality} — ${tool.state}` +
    ` — CAPABILITIES: ${capabilities}` +
    ` — UNRESOLVED: ${unresolved}`
  );
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

  const hostname = root?.location?.hostname;
  if (!isLiteralLoopbackHostname(hostname)) {
    return unavailable("LOCAL_TOOL_BRIDGE_NOT_LOOPBACK", token);
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
  return value.tools.map(sanitizeToolDescriptor);
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
