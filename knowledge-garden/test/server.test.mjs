import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { once } from 'node:events';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { createServer } from '../server.mjs';
import { fixture } from './fixtures.mjs';

let server;
let port;
let temporary;
const original = fixture();

before(async () => {
  temporary = mkdtempSync(join(tmpdir(), 'knowledge-garden-'));
  writeFileSync(join(temporary, 'index.html'), '<!doctype html><title>Fixture</title>');
  writeFileSync(join(temporary, 'styles.css'), 'body { color: green; }');
  writeFileSync(join(temporary, 'app.js'), 'export const fixture = true;');
  writeFileSync(join(temporary, 'working-set.mjs'), 'export const checkpoint = true;');
  writeFileSync(join(temporary, 'private.txt'), 'must not be served');
  server = createServer(original, { publicDirectory: temporary });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  port = server.address().port;
});

after(async () => {
  await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
  rmSync(temporary, { recursive: true, force: true });
});

// Use a raw request target: fetch and URL constructors can normalize traversal away.
function request(path, { method = 'GET', host, body } = {}) {
  return new Promise((resolve, reject) => {
    const req = http.request({ hostname: '127.0.0.1', port, path, method,
      headers: { Host: host ?? `127.0.0.1:${port}`, ...(body ? { 'Content-Length': Buffer.byteLength(body) } : {}) } }, res => {
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => {
        const text = Buffer.concat(chunks).toString('utf8');
        let json;
        try { json = JSON.parse(text); } catch { /* Static files and HEAD have no JSON. */ }
        resolve({ status: res.statusCode, headers: res.headers, text, json });
      });
      res.on('error', reject);
    });
    req.on('error', reject);
    req.end(body);
  });
}

test('health identifies the immutable reviewed snapshot and read-only behavior', async () => {
  original.catalog_version = 'mutated-after-start';
  const result = await request('/api/health');
  assert.equal(result.status, 200);
  assert.deepEqual(result.json, { status: 'ok', catalog_version: 'fixture.1', read_only: true });
  assert.equal(result.headers['cache-control'], 'no-store');
  assert.equal(result.headers['x-content-type-options'], 'nosniff');
  assert.equal(result.headers['access-control-allow-origin'], undefined);
  assert.match(result.headers['content-security-policy'], /frame-ancestors 'none'/);
});

test('projects filter by kind, exact status and bounded pagination', async () => {
  const all = await request('/api/projects');
  assert.deepEqual(all.json.items.map(node => node.id), ['alpha', 'beta']);
  const one = await request('/api/projects?limit=1&offset=1');
  assert.deepEqual(one.json.items.map(node => node.id), ['beta']);
  assert.equal(one.json.total, 2);
  assert.equal(one.json.limit, 1);
  assert.equal(one.json.offset, 1);
  assert.equal((await request('/api/projects?status=missing')).json.total, 0);
  assert.equal((await request('/api/projects?status=source%20reviewed')).json.total, 2);
  assert.deepEqual((await request('/api/projects?offset=1000000')).json.items, []);
});

test('search is literal and case-insensitive across name, summary and tags', async () => {
  assert.deepEqual((await request('/api/search?q=%5Bgarden%5D')).json.items.map(node => node.id), ['alpha']);
  assert.deepEqual((await request('/api/search?q=runtime')).json.items.map(node => node.id), ['beta']);
  assert.deepEqual((await request('/api/search?q=ROUTER')).json.items.map(node => node.id), ['router']);
  assert.deepEqual((await request('/api/search?q=.*')).json.items, []);
  assert.equal((await request('/api/projects?q=router')).json.total, 0);
  assert.equal((await request('/api/search?q=study&limit=1&offset=1')).json.total, 2);
});

test('query mistakes are explicit 400 responses', async t => {
  const paths = [
    '/api/search', '/api/search?q=', '/api/search?q=%20%20', '/api/search?q=%00',
    `/api/search?q=${'x'.repeat(201)}`, '/api/search?q=ok&q=again',
    '/api/projects?limit=0', '/api/projects?limit=101', '/api/projects?limit=1.5',
    '/api/projects?limit=-1', '/api/projects?limit=1e2', '/api/projects?offset=-1',
    '/api/projects?offset=1000001', '/api/projects?limit=2&limit=3',
    '/api/projects?unknown=true', '/api/health?q=anything', '/api/sources?limit=1',
    '/api/relations?type=proves', '/api/relations?type=', '/api/capabilities?node_id=',
    '/api/search?q=%GG', '/api/search?q=%FF', '/api/projects/alpha?extra=1',
  ];
  for (const path of paths) await t.test(path, async () => {
    const result = await request(path);
    assert.equal(result.status, 400);
    assert.equal(result.json.error.code, 'invalid_request');
  });
});

test('exact project and node identities do not silently substitute records', async () => {
  assert.equal((await request('/api/projects/alpha')).json.id, 'alpha');
  for (const path of ['/api/projects/root', '/api/projects/ALPHA', '/api/projects/alph', '/api/nodes/missing']) {
    assert.equal((await request(path)).status, 404);
  }
  const detail = (await request('/api/nodes/alpha')).json;
  assert.deepEqual(detail.children.map(node => node.id), ['router']);
  assert.deepEqual(detail.relations.map(edge => edge.id), ['alpha-beta']);
  assert.deepEqual(detail.sources.map(source => source.id), ['fixture-source']);
  assert.deepEqual(detail.capabilities.map(capability => capability.id), ['alpha-read']);
});

test('containment hierarchy stays separate from typed relation edges', async () => {
  const full = (await request('/api/hierarchy')).json;
  assert.deepEqual(full.roots.map(node => node.id), ['root']);
  assert.deepEqual(full.roots[0].children.map(node => node.id), ['alpha', 'beta']);
  const subtree = (await request('/api/hierarchy?root=alpha')).json;
  assert.deepEqual(subtree.roots.map(node => node.id), ['alpha']);
  assert.deepEqual(subtree.roots[0].children.map(node => node.id), ['router']);
  assert.equal((await request('/api/hierarchy?root=missing')).status, 404);
});

test('relation filters include either endpoint and retain proposal scope', async () => {
  for (const nodeId of ['alpha', 'beta']) {
    const result = await request(`/api/relations?node_id=${nodeId}&type=related_to`);
    assert.equal(result.json.total, 1);
    assert.equal(result.json.items[0].status, 'proposal');
    assert.match(result.json.items[0].scope, /Proposed comparison/);
  }
  assert.equal((await request('/api/relations?node_id=router')).json.total, 0);
  assert.equal((await request('/api/relations?node_id=missing')).status, 404);
  assert.equal((await request('/api/relations?type=supports')).json.total, 0);
});

test('sources, capability descriptions and proposal trails are readable without invocation', async () => {
  const source = (await request('/api/sources')).json.items[0];
  assert.equal(source.access, 'owner-held');
  assert.equal(source.url, null);
  assert.equal((await request('/api/capabilities?node_id=alpha')).json.total, 1);
  assert.equal((await request('/api/capabilities?node_id=beta')).json.total, 0);
  assert.equal((await request('/api/capabilities?node_id=missing')).status, 404);
  assert.equal((await request('/api/trails')).json.items[0].status, 'proposal');
  assert.equal((await request('/api/catalog')).json.nodes.length, 4);
});

test('all write methods fail with 405 and cannot change the snapshot', async () => {
  for (const method of ['POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']) {
    const result = await request('/api/catalog', { method, body: '{"nodes":[]}' });
    assert.equal(result.status, 405);
    assert.equal(result.headers.allow, 'GET, HEAD');
    assert.equal(result.json.error.code, 'method_not_allowed');
  }
  assert.equal((await request('/api/catalog')).json.nodes.length, 4);
});

test('HEAD mirrors GET without a response body', async () => {
  for (const path of ['/api/projects', '/', '/unknown']) {
    const get = await request(path);
    const head = await request(path, { method: 'HEAD' });
    assert.equal(head.status, get.status);
    assert.equal(head.headers['content-length'], get.headers['content-length']);
    assert.equal(head.text, '');
  }
});

test('static files are served only from the allowlist with correct MIME types', async () => {
  const index = await request('/');
  assert.equal(index.status, 200);
  assert.match(index.headers['content-type'], /^text\/html/);
  assert.match((await request('/styles.css')).headers['content-type'], /^text\/css/);
  assert.match((await request('/app.js')).headers['content-type'], /^text\/javascript/);
  assert.equal((await request('/working-set.mjs')).status, 200);
  assert.match((await request('/working-set.mjs')).headers['content-type'], /^text\/javascript/);
  for (const path of ['/private.txt', '/data/catalog.json', '/server.mjs', '/package.json', '/api/unknown', '/api/projects/']) {
    assert.equal((await request(path)).status, 404);
  }
});

test('raw traversal, malformed encoding and excessive targets are rejected', async () => {
  for (const path of ['/../private.txt', '/%2e%2e/private.txt', '/a/../index.html', '/a/%2e%2e/index.html', '/%00', '/%GG', '/%FF', '/%5cprivate.txt', '//index.html', '/index.html#fragment', `/${'a'.repeat(4096)}`]) {
    const result = await request(path);
    assert.equal(result.status, 400, path.slice(0, 60));
    assert.equal(result.json.error.code, 'invalid_request');
  }
});

test('Host checks block external and misleading hostnames', async () => {
  for (const host of ['example.com', 'localhost.evil.example', '127.0.0.1.evil.example', 'localhost@evil.example', 'localhost/evil', 'localhost:99999']) {
    assert.equal((await request('/api/health', { host })).status, 403, host);
  }
  for (const host of ['localhost', 'localhost:4317', '[::1]:4317', '127.0.0.1']) {
    assert.equal((await request('/api/health', { host })).status, 200, host);
  }
});

test('OpenAPI covers each implemented API route and GET/HEAD behavior', async () => {
  const result = await request('/api/openapi.json');
  assert.equal(result.status, 200);
  assert.equal(result.json.openapi, '3.1.0');
  const expected = ['/api/health', '/api/catalog', '/api/projects', '/api/projects/{id}', '/api/nodes/{id}', '/api/hierarchy', '/api/relations', '/api/sources', '/api/capabilities', '/api/trails', '/api/search', '/api/openapi.json'];
  assert.deepEqual(Object.keys(result.json.paths).sort(), expected.sort());
  for (const path of expected) {
    assert.ok(result.json.paths[path].get.responses['405']);
    assert.ok(result.json.paths[path].head);
  }
});

test('closing releases the executor and a closed server cannot reuse released state', async () => {
  const disposable = createServer(fixture());
  disposable.listen(0, '127.0.0.1');
  await once(disposable, 'listening');
  await new Promise((resolve, reject) => disposable.close(error => error ? reject(error) : resolve()));
  assert.throws(() => disposable.listen(0, '127.0.0.1'), /released its catalog/);
});
