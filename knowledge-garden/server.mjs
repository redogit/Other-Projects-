import http from 'node:http';
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const directory = dirname(fileURLToPath(import.meta.url));
const idPattern = /^[a-z0-9][a-z0-9_.-]{0,127}$/;
const relationTypes = new Set(['related_to', 'depends_on', 'supports', 'derived_from', 'predecessor']);
const staticFiles = new Map([
  ['/', ['index.html', 'text/html; charset=utf-8']],
  ['/index.html', ['index.html', 'text/html; charset=utf-8']],
  ['/styles.css', ['styles.css', 'text/css; charset=utf-8']],
  ['/app.js', ['app.js', 'text/javascript; charset=utf-8']],
]);

function invariant(condition, message) {
  if (!condition) throw new TypeError(`Invalid catalog: ${message}`);
}

function record(value, label) {
  invariant(value !== null && typeof value === 'object' && !Array.isArray(value), `${label} must be an object`);
}

function fields(value, allowed, label) {
  for (const key of Object.keys(value)) invariant(allowed.includes(key), `${label} has unexpected field ${key}`);
  for (const key of allowed) invariant(Object.hasOwn(value, key), `${label} is missing field ${key}`);
}

function string(value, label, maximum = 10000) {
  invariant(typeof value === 'string' && value.trim().length > 0 && value.length <= maximum, `${label} must be a nonempty string of at most ${maximum} characters`);
}

function strings(value, label, { nonempty = false } = {}) {
  invariant(Array.isArray(value) && value.length <= 5000, `${label} must be an array of at most 5000 strings`);
  invariant(!nonempty || value.length > 0, `${label} must not be empty`);
  value.forEach((item, index) => string(item, `${label}[${index}]`));
  invariant(new Set(value).size === value.length, `${label} contains duplicates`);
}

function date(value, label, nullable = false) {
  if (nullable && value === null) return;
  invariant(typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value), `${label} must be an ISO calendar date`);
  const parsed = new Date(`${value}T00:00:00.000Z`);
  invariant(Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value, `${label} is not a valid date`);
}

function records(value, label, allowed) {
  invariant(Array.isArray(value) && value.length <= 5000, `${label} must be an array of at most 5000 records`);
  const map = new Map();
  value.forEach((item, index) => {
    const path = `${label}[${index}]`;
    record(item, path);
    fields(item, allowed, path);
    invariant(typeof item.id === 'string' && idPattern.test(item.id), `${path}.id must be a stable lowercase identifier`);
    invariant(!map.has(item.id), `${label} has duplicate id ${item.id}`);
    map.set(item.id, item);
  });
  return map;
}

function references(ids, map, label, nonempty = false) {
  strings(ids, label, { nonempty });
  ids.forEach(id => invariant(map.has(id), `${label} references missing id ${id}`));
}

/** Check containment, typed edges and their recorded basis; this is not a scientific truth check. */
export function validateCatalog(catalog) {
  record(catalog, 'root');
  fields(catalog, ['schema_version', 'catalog_version', 'reviewed_on', 'title', 'scope', 'rules', 'nodes', 'relations', 'sources', 'capabilities', 'trails'], 'root');
  invariant(catalog.schema_version === '1.0.0', 'schema_version must be 1.0.0');
  string(catalog.catalog_version, 'catalog_version', 100);
  date(catalog.reviewed_on, 'reviewed_on');
  string(catalog.title, 'title', 200);
  string(catalog.scope, 'scope');
  strings(catalog.rules, 'rules', { nonempty: true });
  const nodes = records(catalog.nodes, 'nodes', ['id', 'name', 'kind', 'parent_id', 'summary', 'status', 'evidence_status', 'source_ids', 'tags', 'next_action']);
  const sources = records(catalog.sources, 'sources', ['id', 'title', 'source_date', 'reviewed_on', 'access', 'url', 'evidence_kind', 'scope']);
  records(catalog.relations, 'relations', ['id', 'from_id', 'to_id', 'type', 'scope', 'status', 'source_ids']);
  records(catalog.capabilities, 'capabilities', ['id', 'node_id', 'name', 'transport', 'status', 'invocation', 'input', 'output', 'limitations', 'source_ids']);
  records(catalog.trails, 'trails', ['id', 'title', 'summary', 'node_ids', 'next_action', 'status']);

  for (const node of nodes.values()) {
    string(node.name, `${node.id}.name`, 200);
    invariant(['group', 'project', 'component', 'role'].includes(node.kind), `${node.id}.kind is unknown`);
    invariant(node.parent_id === null || nodes.has(node.parent_id), `${node.id}.parent_id references a missing node`);
    for (const key of ['summary', 'status', 'evidence_status', 'next_action']) string(node[key], `${node.id}.${key}`);
    references(node.source_ids, sources, `${node.id}.source_ids`, true);
    strings(node.tags, `${node.id}.tags`);
    const ancestors = new Set([node.id]);
    let parent = node.parent_id;
    while (parent !== null) {
      invariant(!ancestors.has(parent), `containment cycle involving ${node.id}`);
      ancestors.add(parent);
      invariant(ancestors.size <= 100, 'containment depth exceeds 100');
      parent = nodes.get(parent).parent_id;
      invariant(parent === null || nodes.has(parent), `missing ancestor of ${node.id}`);
    }
  }

  for (const source of sources.values()) {
    string(source.title, `${source.id}.title`, 500);
    date(source.source_date, `${source.id}.source_date`, true);
    date(source.reviewed_on, `${source.id}.reviewed_on`);
    string(source.evidence_kind, `${source.id}.evidence_kind`, 200);
    string(source.scope, `${source.id}.scope`);
    invariant(['public', 'owner-held'].includes(source.access), `${source.id}.access is unknown`);
    if (source.access === 'owner-held') {
      invariant(source.url === null, `${source.id}: owner-held sources must not expose a URL`);
    } else {
      let url;
      try { url = new URL(source.url); } catch { /* Report a catalog error below. */ }
      invariant(typeof source.url === 'string' && url?.protocol === 'https:' && !url.username && !url.password, `${source.id}: public source needs an HTTPS URL without credentials`);
    }
  }

  for (const edge of catalog.relations) {
    invariant(nodes.has(edge.from_id) && nodes.has(edge.to_id), `${edge.id}: relation endpoint is missing`);
    invariant(relationTypes.has(edge.type), `${edge.id}: unknown relation type`);
    string(edge.scope, `${edge.id}.scope`);
    invariant(['source-described', 'proposal'].includes(edge.status), `${edge.id}: unknown relation status`);
    references(edge.source_ids, sources, `${edge.id}.source_ids`, true);
    invariant(edge.type !== 'supports' || edge.status === 'source-described', `${edge.id}: supports requires a source-described basis`);
  }

  for (const capability of catalog.capabilities) {
    invariant(nodes.has(capability.node_id), `${capability.id}: capability node is missing`);
    invariant(['local-http', 'external-browser', 'source-contract'].includes(capability.transport), `${capability.id}: unknown transport`);
    invariant(['implemented', 'source-inspected', 'described'].includes(capability.status), `${capability.id}: unknown capability status`);
    const transportStatus = { 'local-http': 'implemented', 'external-browser': 'source-inspected', 'source-contract': 'described' };
    invariant(capability.status === transportStatus[capability.transport], `${capability.id}: capability transport and status do not match`);
    for (const key of ['name', 'invocation', 'input', 'output']) string(capability[key], `${capability.id}.${key}`);
    strings(capability.limitations, `${capability.id}.limitations`, { nonempty: true });
    references(capability.source_ids, sources, `${capability.id}.source_ids`, true);
  }

  for (const trail of catalog.trails) {
    for (const key of ['title', 'summary', 'next_action']) string(trail[key], `${trail.id}.${key}`);
    invariant(trail.status === 'proposal', `${trail.id}: discovery trails are proposals`);
    references(trail.node_ids, nodes, `${trail.id}.node_ids`, true);
  }
  return catalog;
}

function loadCatalog() {
  return JSON.parse(readFileSync(join(directory, 'data', 'catalog.json'), 'utf8'));
}

function freeze(value) {
  if (value && typeof value === 'object') {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
}

class RequestError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

function invalid(message) { throw new RequestError(400, 'invalid_request', message); }
function missing(message = 'Route not found.') { throw new RequestError(404, 'not_found', message); }

function queryParameters(url, allowed = []) {
  for (const key of url.searchParams.keys()) {
    if (!allowed.includes(key)) invalid(`Unknown query parameter: ${key}.`);
    if (url.searchParams.getAll(key).length !== 1) invalid(`Query parameter ${key} must occur once.`);
  }
  return url.searchParams;
}

function textParameter(params, key, { required = false, maximum = 200 } = {}) {
  if (!params.has(key)) {
    if (required) invalid(`Query parameter ${key} is required.`);
    return null;
  }
  const raw = params.get(key);
  if (raw.length > maximum || !raw.trim().length || /[\u0000-\u001f\u007f]/.test(raw)) invalid(`${key} must contain 1 to ${maximum} printable characters.`);
  return raw.trim();
}

function numberParameter(params, key, defaultValue, minimum, maximum) {
  if (!params.has(key)) return defaultValue;
  const raw = params.get(key);
  if (!/^\d{1,7}$/.test(raw)) invalid(`${key} must be an integer from ${minimum} to ${maximum}.`);
  const value = Number(raw);
  if (value < minimum || value > maximum) invalid(`${key} must be an integer from ${minimum} to ${maximum}.`);
  return value;
}

function page(items, params) {
  const limit = numberParameter(params, 'limit', 50, 1, 100);
  const offset = numberParameter(params, 'offset', 0, 0, 1000000);
  return { items: items.slice(offset, offset + limit), total: items.length, offset, limit };
}

function matches(node, query) {
  return query === null || [node.name, node.summary, ...node.tags].join('\n').toLowerCase().includes(query.toLowerCase());
}

function parseRequestTarget(target) {
  if (typeof target !== 'string' || target.length > 4096) invalid('Request target must be at most 4096 characters.');
  if (!target.startsWith('/') || target.startsWith('//') || target.includes('#') || target.includes('\\')) invalid('Use an absolute path without a fragment or backslash.');
  // Check the original path before URL normalization can erase traversal segments.
  const rawPath = target.split('?')[0];
  let path;
  try { path = decodeURIComponent(rawPath); } catch { invalid('Malformed path encoding.'); }
  if (path.includes('\\') || /[\u0000-\u001f\u007f]/.test(path) || path.split('/').some(part => part === '.' || part === '..')) invalid('Invalid path.');
  if (/%(?![0-9a-fA-F]{2})/.test(target)) invalid('Malformed percent encoding.');
  const query = target.includes('?') ? target.slice(target.indexOf('?') + 1) : '';
  try { decodeURIComponent(query.replace(/\+/g, ' ')); } catch { invalid('Malformed query encoding.'); }
  return { path, url: new URL(target, 'http://localhost') };
}

function normalizedHost(host) {
  if (typeof host !== 'string' || !host || /[\s/@,\\]/.test(host)) return null;
  try {
    const url = new URL(`http://${host}`);
    if (url.pathname !== '/' || url.search || url.hash || url.username || url.password) return null;
    return url.hostname.toLowerCase();
  } catch { return null; }
}

/**
 * Return an unbound Node HTTP server. With no arguments, loads data/catalog.json.
 * Tests/embedders may provide a catalog and { publicDirectory, allowedHosts }.
 * Call server.listen(port, '127.0.0.1'); no requests are made by this module.
 */
export function createServer(catalog = loadCatalog(), options = {}) {
  const snapshot = freeze(validateCatalog(structuredClone(catalog)));
  const nodes = new Map(snapshot.nodes.map(node => [node.id, node]));
  const sources = new Map(snapshot.sources.map(source => [source.id, source]));
  const openapi = JSON.parse(readFileSync(join(directory, 'openapi.json'), 'utf8'));
  const publicDirectory = options.publicDirectory ?? join(directory, 'public');
  const allowedHosts = new Set(['127.0.0.1', 'localhost', '[::1]', ...(options.allowedHosts ?? []).map(normalizedHost).filter(Boolean)]);

  function nodeById(id) {
    if (!nodes.has(id)) missing('Node not found.');
    return nodes.get(id);
  }

  function nodeParameter(params, key) {
    const id = textParameter(params, key, { maximum: 128 });
    if (id !== null) nodeById(id);
    return id;
  }

  function hierarchy(rootId) {
    const nested = new Map(snapshot.nodes.map(node => [node.id, { ...node, children: [] }]));
    const roots = [];
    for (const node of snapshot.nodes) {
      if (node.parent_id === null) roots.push(nested.get(node.id));
      else nested.get(node.parent_id).children.push(nested.get(node.id));
    }
    return { roots: rootId === null ? roots : [nested.get(rootId)] };
  }

  function api(path, url) {
    if (path === '/api/health') {
      queryParameters(url);
      return { status: 'ok', catalog_version: snapshot.catalog_version, read_only: true };
    }
    if (path === '/api/catalog') { queryParameters(url); return snapshot; }
    if (path === '/api/openapi.json') { queryParameters(url); return openapi; }
    if (path === '/api/projects') {
      const params = queryParameters(url, ['q', 'status', 'limit', 'offset']);
      const q = textParameter(params, 'q');
      const status = textParameter(params, 'status', { maximum: 120 });
      return page(snapshot.nodes.filter(node => node.kind === 'project' && matches(node, q) && (status === null || node.status === status)), params);
    }
    const projectMatch = /^\/api\/projects\/([^/]+)$/.exec(path);
    if (projectMatch) {
      queryParameters(url);
      const node = nodeById(projectMatch[1]);
      if (node.kind !== 'project') missing('Project not found.');
      return node;
    }
    const nodeMatch = /^\/api\/nodes\/([^/]+)$/.exec(path);
    if (nodeMatch) {
      queryParameters(url);
      const node = nodeById(nodeMatch[1]);
      return {
        node,
        children: snapshot.nodes.filter(item => item.parent_id === node.id),
        relations: snapshot.relations.filter(edge => edge.from_id === node.id || edge.to_id === node.id),
        sources: node.source_ids.map(id => sources.get(id)),
        capabilities: snapshot.capabilities.filter(capability => capability.node_id === node.id),
      };
    }
    if (path === '/api/hierarchy') {
      const params = queryParameters(url, ['root']);
      return hierarchy(nodeParameter(params, 'root'));
    }
    if (path === '/api/relations') {
      const params = queryParameters(url, ['node_id', 'type']);
      const nodeId = nodeParameter(params, 'node_id');
      const type = textParameter(params, 'type', { maximum: 30 });
      if (type !== null && !relationTypes.has(type)) invalid('Unknown relation type.');
      const items = snapshot.relations.filter(edge => (nodeId === null || edge.from_id === nodeId || edge.to_id === nodeId) && (type === null || edge.type === type));
      return { items, total: items.length };
    }
    if (path === '/api/capabilities') {
      const params = queryParameters(url, ['node_id']);
      const nodeId = nodeParameter(params, 'node_id');
      const items = snapshot.capabilities.filter(capability => nodeId === null || capability.node_id === nodeId);
      return { items, total: items.length };
    }
    if (path === '/api/sources' || path === '/api/trails') {
      queryParameters(url);
      const items = path === '/api/sources' ? snapshot.sources : snapshot.trails;
      return { items, total: items.length };
    }
    if (path === '/api/search') {
      const params = queryParameters(url, ['q', 'limit', 'offset']);
      const q = textParameter(params, 'q', { required: true });
      return page(snapshot.nodes.filter(node => matches(node, q)), params);
    }
    missing();
  }

  const server = http.createServer({ maxHeaderSize: 8192 }, (request, response) => {
    response.setHeader('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'");
    response.setHeader('X-Content-Type-Options', 'nosniff');
    response.setHeader('Referrer-Policy', 'no-referrer');
    response.setHeader('Cross-Origin-Resource-Policy', 'same-origin');
    response.setHeader('Cache-Control', 'no-store');

    function send(status, payload, contentType = 'application/json; charset=utf-8') {
      const bytes = Buffer.isBuffer(payload) ? payload : Buffer.from(JSON.stringify(payload));
      response.writeHead(status, { 'Content-Type': contentType, 'Content-Length': bytes.length });
      response.end(request.method === 'HEAD' ? undefined : bytes);
    }

    try {
      if (!allowedHosts.has(normalizedHost(request.headers.host))) throw new RequestError(403, 'host_not_allowed', 'Use a configured local host.');
      if (!['GET', 'HEAD'].includes(request.method)) {
        response.setHeader('Allow', 'GET, HEAD');
        request.resume();
        throw new RequestError(405, 'method_not_allowed', 'This API is read-only. Use GET or HEAD.');
      }
      const { path, url } = parseRequestTarget(request.url);
      if (path.startsWith('/api/')) { send(200, api(path, url)); return; }
      const staticFile = staticFiles.get(path);
      if (!staticFile) missing();
      queryParameters(url);
      let bytes;
      try { bytes = readFileSync(join(publicDirectory, staticFile[0])); }
      catch (error) { if (error.code === 'ENOENT') missing('Static file not found.'); throw error; }
      response.setHeader('Cache-Control', 'no-cache');
      send(200, bytes, staticFile[1]);
    } catch (error) {
      if (error instanceof RequestError) send(error.status, { error: { code: error.code, message: error.message } });
      else send(500, { error: { code: 'internal_error', message: 'The request could not be completed.' } });
    }
  });
  server.requestTimeout = 10000;
  server.headersTimeout = 10000;
  server.keepAliveTimeout = 5000;
  server.maxRequestsPerSocket = 1000;
  return server;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const catalog = loadCatalog();
    validateCatalog(catalog);
    if (process.argv.includes('--check-catalog')) {
      console.log(`Catalog ${catalog.catalog_version} is structurally valid: ${catalog.nodes.length} nodes, ${catalog.relations.length} typed relations, ${catalog.sources.length} sources.`);
    } else {
      const host = process.env.HOST || '127.0.0.1';
      const rawPort = process.env.PORT || '4317';
      if (!/^\d+$/.test(rawPort) || Number(rawPort) < 1 || Number(rawPort) > 65535) throw new Error('PORT must be an integer from 1 to 65535.');
      const extraHosts = (process.env.ALLOWED_HOSTS || '').split(',').map(value => value.trim()).filter(Boolean);
      const server = createServer(catalog, { allowedHosts: [host, ...extraHosts] });
      server.on('error', error => { console.error(`Knowledge Garden could not start: ${error.message}`); process.exitCode = 1; });
      server.listen(Number(rawPort), host, () => console.log(`Knowledge Garden: http://${host.includes(':') ? `[${host}]` : host}:${rawPort} (read-only API)`));
      for (const signal of ['SIGINT', 'SIGTERM']) process.once(signal, () => server.close());
    }
  } catch (error) {
    console.error(`Knowledge Garden could not start: ${error.message}`);
    process.exitCode = 1;
  }
}
