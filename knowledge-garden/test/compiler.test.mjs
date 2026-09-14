import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { compileCatalog, createExecutor, validatePlan } from '../compiler.mjs';
import { RELATION_TYPES } from '../catalog.mjs';
import { fixture } from './fixtures.mjs';

const shipped = JSON.parse(readFileSync(new URL('../data/catalog.json', import.meta.url), 'utf8'));
const detail = (c, id) => {
  const node = c.nodes.find(n => n.id === id);
  return { node, children: c.nodes.filter(n => n.parent_id === id),
    relations: c.relations.filter(e => e.from_id === id || e.to_id === id),
    capabilities: c.capabilities.filter(x => x.node_id === id),
    sources: node.source_ids.map(id => c.sources.find(s => s.id === id)) };
};
const hierarchy = (c, root = null) => {
  const nest = node => ({ ...node, children: c.nodes.filter(n => n.parent_id === node.id).map(nest) });
  return { roots: c.nodes.filter(n => root === null ? n.parent_id === null : n.id === root).map(nest) };
};

test('compiled plan is deterministic and preserves all shipped node/detail and hierarchy outputs', () => {
  const plan = compileCatalog(shipped);
  assert.deepEqual(plan, compileCatalog(structuredClone(shipped)));
  const run = createExecutor(shipped, JSON.parse(JSON.stringify(plan)));
  assert.deepEqual(run.hierarchy(), hierarchy(shipped));
  for (const node of shipped.nodes) {
    assert.deepEqual(run.node(node.id), node);
    assert.deepEqual(run.detail(node.id), detail(shipped, node.id));
    assert.deepEqual(run.hierarchy(node.id), hierarchy(shipped, node.id));
  }
  run.dispose();
});

test('compiled relation and capability selection matches source-order scans for every node and type', () => {
  const run = createExecutor(shipped);
  for (const id of [null, ...shipped.nodes.map(n => n.id)]) {
    for (const type of [null, ...RELATION_TYPES]) {
      assert.deepEqual(run.relations(id, type), shipped.relations.filter(e => (id === null || e.from_id === id || e.to_id === id) && (type === null || e.type === type)));
    }
    assert.deepEqual(run.capabilities(id), shipped.capabilities.filter(c => id === null || c.node_id === id));
  }
  run.dispose();
});

test('compiled literal search preserves original casing, ordering, filters and no-match behavior', () => {
  const run = createExecutor(shipped);
  const queries = [null, '', 'MASTER', 'R³', '1024', '.*', '[x]', 'Quantum', 'word-that-is-absent', ...shipped.nodes.flatMap(n => n.tags)];
  for (const q of queries) for (const projectsOnly of [false, true]) for (const status of [null, 'public project present', 'missing status']) {
    const expected = shipped.nodes.filter(n => (!projectsOnly || n.kind === 'project') && (status === null || n.status === status) && (q === null || [n.name, n.summary, ...n.tags].join('\n').toLowerCase().includes(q.toLowerCase())));
    assert.deepEqual(run.search(q, { projectsOnly, status }), expected);
  }
  run.dispose();
});

test('source edits, stale compiler versions and altered plan bytes fail before execution', () => {
  const c = fixture(); const plan = compileCatalog(c);
  const changed = structuredClone(c); changed.nodes[0].summary += ' revised';
  assert.throws(() => createExecutor(changed, plan), /catalog changed/);
  const corrupt = structuredClone(plan); corrupt.children[0] = [];
  assert.throws(() => validatePlan(c, corrupt), /content hash mismatch/);
  const version = structuredClone(plan); version.compiler_version = '999.0.0';
  assert.throws(() => createExecutor(c, version), /unsupported format/);
});

test('executor snapshots isolate caller mutation, exact identity and repeated release', () => {
  const c = fixture(); const plan = JSON.parse(JSON.stringify(compileCatalog(c)));
  const run = createExecutor(c, plan);
  c.nodes[0].name = 'changed'; plan.search_text[0] = 'changed';
  assert.notEqual(run.node('root').name, 'changed');
  assert.throws(() => { run.node('root').name = 'changed'; }, TypeError);
  assert.throws(() => run.node('ROOT'), /Unknown node/);
  assert.throws(() => run.relations(null, 'proves'), /Unknown relation type/);
  run.dispose(); run.dispose();
  for (const action of [() => run.node('root'), () => run.detail('alpha'), () => run.hierarchy(), () => run.search(''), () => run.catalog(), () => run.has('root')]) assert.throws(action, /released/);
});

test('a recomputed checksum cannot hide wrong, incomplete or reordered derived instructions', () => {
  const c = fixture();
  const mutations = [
    p => { p.children[0] = [0]; },
    p => { p.children[0] = []; },
    p => { p.children[0].reverse(); },
    p => { p.projects = []; },
    p => { p.relations[1] = []; },
    p => { p.capabilities[1] = []; },
    p => { p.source_slots[1] = []; },
    p => { p.search_text[1] = 'silently changed meaning'; },
    p => { p.relation_types.related_to = []; },
  ];
  for (const mutate of mutations) {
    const plan = structuredClone(compileCatalog(c));
    mutate(plan);
    const { plan_sha256, ...payload } = plan;
    plan.plan_sha256 = createHash('sha256').update(JSON.stringify(payload)).digest('hex');
    assert.throws(() => createExecutor(c, plan), /Invalid compiled plan/);
  }
});

test('a self-relation is emitted once, while ordinary graph cycles stay valid', () => {
  const c = fixture(); c.relations.push({ ...c.relations[0], id: 'self', from_id: 'alpha', to_id: 'alpha' });
  const run = createExecutor(c);
  assert.equal(run.relations('alpha').filter(e => e.id === 'self').length, 1);
  assert.deepEqual(run.detail('alpha'), detail(c, 'alpha'));
  run.dispose();
});
