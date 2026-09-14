import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateCatalog, createServer } from '../server.mjs';
import { fixture } from './fixtures.mjs';

test('the shipped catalog passes structural validation', () => {
  const catalog = JSON.parse(readFileSync(new URL('../data/catalog.json', import.meta.url), 'utf8'));
  assert.equal(validateCatalog(catalog), catalog);
  assert.ok(catalog.nodes.some(node => node.kind === 'project'));
});

test('bad identities and missing references fail before the server starts', async t => {
  const cases = [
    ['duplicate node ID', catalog => catalog.nodes.push({ ...catalog.nodes[0] })],
    ['duplicate source ID', catalog => catalog.sources.push({ ...catalog.sources[0] })],
    ['invalid node ID', catalog => catalog.nodes[0].id = '../escape'],
    ['missing parent', catalog => catalog.nodes[1].parent_id = 'missing'],
    ['missing node source', catalog => catalog.nodes[1].source_ids = ['missing']],
    ['missing edge endpoint', catalog => catalog.relations[0].to_id = 'missing'],
    ['missing edge source', catalog => catalog.relations[0].source_ids = ['missing']],
    ['missing capability node', catalog => catalog.capabilities[0].node_id = 'missing'],
    ['missing capability source', catalog => catalog.capabilities[0].source_ids = ['missing']],
    ['missing trail node', catalog => catalog.trails[0].node_ids = ['missing']],
  ];
  for (const [name, mutate] of cases) await t.test(name, () => {
    const catalog = fixture(); mutate(catalog);
    assert.throws(() => createServer(catalog), /Invalid catalog:/);
  });
});

test('containment cycles fail but typed relation cycles are permitted', () => {
  const self = fixture(); self.nodes[0].parent_id = 'root';
  assert.throws(() => validateCatalog(self), /containment cycle/);
  const longer = fixture(); longer.nodes[0].parent_id = 'router';
  assert.throws(() => validateCatalog(longer), /containment cycle/);
  const typed = fixture();
  typed.relations.push({ ...typed.relations[0], id: 'beta-alpha', from_id: 'beta', to_id: 'alpha' });
  assert.equal(validateCatalog(typed), typed);
});

test('supports cannot be inferred from an ungrounded proposal', () => {
  const catalog = fixture();
  const edge = catalog.relations[0];
  edge.type = 'supports';
  assert.throws(() => validateCatalog(catalog), /supports requires a source-described basis/);
  edge.status = 'source-described';
  edge.source_ids = [];
  assert.throws(() => validateCatalog(catalog), /source_ids must not be empty/);
  edge.source_ids = ['fixture-source'];
  edge.scope = ' ';
  assert.throws(() => validateCatalog(catalog), /scope must be a nonempty string/);
  edge.scope = 'The synthetic source describes support only for this bounded fixture relation.';
  assert.equal(validateCatalog(catalog), catalog);
});

test('all source-described edges require a cited source', () => {
  const catalog = fixture(); catalog.relations[0].status = 'source-described';
  catalog.relations[0].source_ids = [];
  assert.throws(() => validateCatalog(catalog), /source_ids must not be empty/);
});

test('source links preserve the public versus owner-held boundary', () => {
  const catalog = fixture();
  const source = catalog.sources[0];
  source.url = 'https://example.com/private';
  assert.throws(() => validateCatalog(catalog), /owner-held sources must not expose a URL/);
  source.access = 'public';
  for (const url of ['http://example.com', 'javascript:alert(1)', 'https://user:secret@example.com', null]) {
    source.url = url;
    assert.throws(() => validateCatalog(catalog), /public source needs an HTTPS URL/);
  }
  source.url = 'https://example.com/source';
  assert.equal(validateCatalog(catalog), catalog);
});

test('unknown schema values, invalid dates and promoted trails are rejected', async t => {
  const cases = [
    ['schema', catalog => catalog.schema_version = '2.0.0'],
    ['invalid date', catalog => catalog.reviewed_on = '2026-02-30'],
    ['kind', catalog => catalog.nodes[0].kind = 'authority'],
    ['edge type', catalog => catalog.relations[0].type = 'proves'],
    ['edge status', catalog => catalog.relations[0].status = 'verified'],
    ['transport', catalog => catalog.capabilities[0].transport = 'remote-post'],
    ['capability status', catalog => catalog.capabilities[0].status = 'trusted'],
    ['mismatched capability status', catalog => catalog.capabilities[0].status = 'described'],
    ['trail status', catalog => catalog.trails[0].status = 'approved'],
    ['empty trail', catalog => catalog.trails[0].node_ids = []],
  ];
  for (const [name, mutate] of cases) await t.test(name, () => {
    const catalog = fixture(); mutate(catalog);
    assert.throws(() => validateCatalog(catalog), /Invalid catalog:/);
  });
});

test('unexpected fields are rejected at every published record boundary', async t => {
  for (const key of ['root', 'nodes', 'relations', 'sources', 'capabilities', 'trails']) await t.test(key, () => {
    const catalog = fixture();
    const target = key === 'root' ? catalog : catalog[key][0];
    target.private_path = '/private/owner-document';
    assert.throws(() => validateCatalog(catalog), /unexpected field private_path/);
  });
});

test('all cited record types and capability limitations must be nonempty', async t => {
  for (const [key, field] of [['nodes', 'source_ids'], ['relations', 'source_ids'], ['capabilities', 'source_ids'], ['capabilities', 'limitations']]) await t.test(`${key}.${field}`, () => {
    const catalog = fixture(); catalog[key][0][field] = [];
    assert.throws(() => validateCatalog(catalog), /must not be empty/);
  });
});
