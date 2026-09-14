import http from 'node:http';
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateCatalog, RELATION_TYPES } from './catalog.mjs';
import { compileCatalog, createExecutor } from './compiler.mjs';
export { validateCatalog } from './catalog.mjs';

const directory = dirname(fileURLToPath(import.meta.url));
const relationTypes = new Set(RELATION_TYPES);
const staticFiles = new Map([
  ['/', ['index.html', 'text/html; charset=utf-8']],
  ['/index.html', ['index.html', 'text/html; charset=utf-8']],
  ['/styles.css', ['styles.css', 'text/css; charset=utf-8']],
  ['/app.js', ['app.js', 'text/javascript; charset=utf-8']],
  ['/working-set.mjs', ['working-set.mjs', 'text/javascript; charset=utf-8']],
]);

function loadCatalog() {
  return JSON.parse(readFileSync(join(directory, 'data', 'catalog.json'), 'utf8'));
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
 * Tests/embedders may provide a catalog and { publicDirectory, allowedHosts, compiledPlan }.
 * Call server.listen(port, '127.0.0.1'); no requests are made by this module.
 */
export function createServer(catalog = loadCatalog(), options = {}) {
  // Compilation and integrity checks finish before a server can accept a request.
  const executor = createExecutor(catalog, options.compiledPlan ?? compileCatalog(catalog));
  let snapshot = executor.catalog();
  const openapi = JSON.parse(readFileSync(join(directory, 'openapi.json'), 'utf8'));
  const publicDirectory = options.publicDirectory ?? join(directory, 'public');
  const allowedHosts = new Set(['127.0.0.1', 'localhost', '[::1]', ...(options.allowedHosts ?? []).map(normalizedHost).filter(Boolean)]);

  function nodeById(id) {
    if (!executor.has(id)) missing('Node not found.');
    return executor.node(id);
  }

  function nodeParameter(params, key) {
    const id = textParameter(params, key, { maximum: 128 });
    if (id !== null) nodeById(id);
    return id;
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
      return page(executor.search(q, { projectsOnly: true, status }), params);
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
      return executor.detail(node.id);
    }
    if (path === '/api/hierarchy') {
      const params = queryParameters(url, ['root']);
      return executor.hierarchy(nodeParameter(params, 'root'));
    }
    if (path === '/api/relations') {
      const params = queryParameters(url, ['node_id', 'type']);
      const nodeId = nodeParameter(params, 'node_id');
      const type = textParameter(params, 'type', { maximum: 30 });
      if (type !== null && !relationTypes.has(type)) invalid('Unknown relation type.');
      const items = executor.relations(nodeId, type);
      return { items, total: items.length };
    }
    if (path === '/api/capabilities') {
      const params = queryParameters(url, ['node_id']);
      const nodeId = nodeParameter(params, 'node_id');
      const items = executor.capabilities(nodeId);
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
      return page(executor.search(q), params);
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
  let released = false;
  const listen = server.listen;
  server.listen = function (...args) {
    if (released) throw new Error('This server has released its catalog. Create a new server to listen again.');
    return listen.apply(this, args);
  };
  server.once('close', () => { released = true; snapshot = null; executor.dispose(); });
  // Request handlers use the immutable executor snapshot, not these input handles.
  catalog = null;
  options = null;
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
      let compiledPlan;
      try { compiledPlan = JSON.parse(readFileSync(join(directory, 'build/catalog.plan.json'), 'utf8')); }
      catch { throw new Error('Compiled query plan unavailable. Run npm run build or use npm start.'); }
      const server = createServer(catalog, { allowedHosts: [host, ...extraHosts], compiledPlan });
      server.on('error', error => { console.error(`Knowledge Garden could not start: ${error.message}`); process.exitCode = 1; });
      server.listen(Number(rawPort), host, () => console.log(`Knowledge Garden: http://${host.includes(':') ? `[${host}]` : host}:${rawPort} (read-only API)`));
      for (const signal of ['SIGINT', 'SIGTERM']) process.once(signal, () => server.close());
    }
  } catch (error) {
    console.error(`Knowledge Garden could not start: ${error.message}`);
    process.exitCode = 1;
  }
}
