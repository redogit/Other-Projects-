import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { TASK_FIELDS, MAX_IMPORT_BYTES, MAX_HISTORY_BYTES, WorkingSetError, createWorkingSet, parseWorkingSet, createCheckpointHistory } from '../public/working-set.mjs';

const catalog = JSON.parse(await readFile(new URL('../data/catalog.json', import.meta.url), 'utf8'));
const createdAt = '2026-09-14T01:02:03.000Z';
const historyKey = 'knowledge-garden.checkpoints.v1';
const copy = (value) => JSON.parse(JSON.stringify(value));
const create = (nodeIds = ['orbit'], task = {}, options = {}) => createWorkingSet(catalog, nodeIds, task, { createdAt, ...options });
const parse = (value, current = catalog) => parseWorkingSet(JSON.stringify(value), current);
function memoryStorage() {
  const data = new Map();
  return {
    data, calls: [], failGet: false, failSet: false, failRemove: false,
    getItem(key) { this.calls.push(['get', key]); if (this.failGet) throw new Error('permission'); return data.get(key) ?? null; },
    setItem(key, value) { this.calls.push(['set', key]); if (this.failSet) throw new Error('quota'); data.set(key, value); },
    removeItem(key) { this.calls.push(['remove', key]); if (this.failRemove) throw new Error('permission'); data.delete(key); },
  };
}
function throwsCode(action, code) { assert.throws(action, (error) => error instanceof WorkingSetError && error.code === code); }
function fixture() {
  const node = (id, source_ids, parent_id = null) => ({ id, name: id, kind: 'project', parent_id, summary: `${id} summary`, status: 'open', evidence_status: 'source-described', source_ids, tags: [], next_action: 'Review' });
  const source = (id) => ({ id, title: id, source_date: null, reviewed_on: '2026-09-14', access: 'owner-held', url: null, evidence_kind: 'contract', scope: 'Fixture only' });
  return {
    schema_version: '1.0.0', catalog_version: 'fixture.1', reviewed_on: '2026-09-14', rules: ['Fixture rule'],
    nodes: [node('a', ['source-a'], 'c'), node('b', ['source-b']), node('c', ['source-c'])],
    relations: [
      { id: 'a-b', from_id: 'a', to_id: 'b', type: 'related_to', scope: 'No evidence transfer', status: 'proposal', source_ids: ['source-edge'] },
      { id: 'a-c', from_id: 'a', to_id: 'c', type: 'related_to', scope: 'No evidence transfer', status: 'proposal', source_ids: ['source-c'] },
    ],
    capabilities: [{ id: 'cap-a', node_id: 'a', name: 'Proposed step', transport: 'source-contract', status: 'described', invocation: 'Review', input: 'Question', output: 'Proposal', limitations: ['No execution'], source_ids: ['source-cap'] }],
    sources: ['source-a', 'source-b', 'source-c', 'source-edge', 'source-cap'].map(source),
  };
}

test('real catalog exports every selected record with closed source references', () => {
  const snapshot = create(catalog.nodes.map((node) => node.id), { request: 'Choose a bounded next step.' }, { title: 'Next trail' });
  assert.equal(snapshot.format_version, 2);
  assert.equal(snapshot.nodes.length, catalog.nodes.length);
  assert.equal(snapshot.relations.length, catalog.relations.length);
  assert.equal(snapshot.capabilities.length, catalog.capabilities.length);
  assert.equal(snapshot.task.request, 'Choose a bounded next step.');
  assert.deepEqual(Object.keys(snapshot.task), TASK_FIELDS);
  assert.equal(snapshot.task.motivator, '');
  const preview = parse(snapshot);
  assert.deepEqual(preview.missing_ids, []);
  assert.deepEqual(preview.changed_ids, []);
  assert.equal(preview.version_mismatch, false);
  assert.equal(preview.legacy, false);
});

test('scopes relations to both endpoints and includes capability and edge source closure', () => {
  const sample = fixture();
  const snapshot = createWorkingSet(sample, new Set(['a', 'b']), {}, { createdAt });
  assert.deepEqual(snapshot.nodes.map((node) => node.id), ['a', 'b']);
  assert.deepEqual(snapshot.relations.map((edge) => edge.id), ['a-b']);
  assert.deepEqual(snapshot.sources.map((source) => source.id).sort(), ['source-a', 'source-b', 'source-cap', 'source-edge']);
  assert.equal(snapshot.nodes[0].parent_id, 'c', 'ancestor need not enter the active set');
  assert.equal(snapshot.relations[0].type, 'related_to');
});

test('snapshot copies task, records, nested fields and rules without caller aliases', () => {
  const sample = fixture();
  const task = { request: 'Keep my wording' };
  const snapshot = createWorkingSet(sample, ['a'], task, { createdAt });
  snapshot.nodes[0].summary = 'Changed snapshot';
  snapshot.nodes[0].source_ids.push('other');
  snapshot.capabilities[0].limitations.push('other');
  snapshot.rules.push('other');
  snapshot.task.request = 'Changed snapshot';
  assert.equal(sample.nodes[0].summary, 'a summary');
  assert.deepEqual(sample.nodes[0].source_ids, ['source-a']);
  assert.deepEqual(sample.capabilities[0].limitations, ['No execution']);
  assert.deepEqual(sample.rules, ['Fixture rule']);
  assert.equal(task.request, 'Keep my wording');
});

test('empty selections support notes and retain unknown task fields as empty strings', () => {
  const empty = create([], { surface: 'An open page' }, { title: 'Note' });
  assert.deepEqual(empty.nodes, []);
  assert.deepEqual(empty.sources, []);
  assert.deepEqual(empty.relations, []);
  assert.deepEqual(empty.capabilities, []);
  assert.equal(parse(empty).proposal.task.surface, 'An open page');
  assert.deepEqual(create([]).task, Object.fromEntries(TASK_FIELDS.map((field) => [field, ''])));
});

test('selection rejects unknown, duplicate, malformed and coerced IDs', () => {
  throwsCode(() => create(['missing']), 'unknown-node');
  for (const selection of [['orbit', 'orbit'], [''], [42], ['orbit\n'], undefined, 'orbit']) {
    const action = selection === undefined ? () => createWorkingSet(catalog, undefined) : () => create(selection);
    throwsCode(action, 'invalid-working-set');
  }
});

test('task fields and title preserve literal text and reject wrong types and excess length', () => {
  const literal = '<script>throw new Error("no")</script> $() 🤧';
  assert.equal(parse(create(['orbit'], { request: literal })).proposal.task.request, literal);
  assert.equal(create([], { request: 'x'.repeat(2000) }, { title: 'x'.repeat(120) }).title.length, 120);
  for (const task of [{ request: 1 }, { request: null }, { request: ['text'] }, { request: 'x'.repeat(2001) }, { hidden_instruction: 'execute' }, null]) {
    throwsCode(() => create([], task), 'invalid-working-set');
  }
  throwsCode(() => create([], {}, { title: 'x'.repeat(121) }), 'invalid-working-set');
  throwsCode(() => create([], {}, { title: null }), 'invalid-working-set');
  throwsCode(() => create([], {}, { createdAt: null }), 'invalid-working-set');
});

test('preview reports exact missing IDs without substitutions and changed records separately', () => {
  const snapshot = create(['orbit', 'master-librarian']);
  const current = copy(catalog);
  current.nodes = current.nodes.filter((node) => node.id !== 'orbit');
  current.nodes.find((node) => node.id === 'master-librarian').summary += ' revised';
  current.catalog_version = 'next';
  const preview = parse(snapshot, current);
  assert.deepEqual(preview.proposal.node_ids, ['orbit', 'master-librarian']);
  assert.deepEqual(preview.available_ids, ['master-librarian']);
  assert.deepEqual(preview.missing_ids, ['orbit']);
  assert.deepEqual(preview.changed_ids, ['master-librarian']);
  assert.equal(preview.version_mismatch, true);
});

test('changed comparison ignores object key order and observes nested or added data', () => {
  const snapshot = create(['orbit']);
  snapshot.nodes[0] = Object.fromEntries(Object.entries(snapshot.nodes[0]).reverse());
  assert.deepEqual(parse(snapshot).changed_ids, []);
  snapshot.nodes[0].tags = [...snapshot.nodes[0].tags, 'changed'];
  assert.deepEqual(parse(snapshot).changed_ids, ['orbit']);
  snapshot.nodes[0] = copy(catalog.nodes.find((node) => node.id === 'orbit'));
  snapshot.nodes[0].new_field = 'not current';
  assert.deepEqual(parse(snapshot).changed_ids, ['orbit']);
});

test('changed review date triggers mismatch even when catalog version text is unchanged', () => {
  const current = copy(catalog);
  current.reviewed_on = '2026-09-15';
  assert.equal(parse(create(), current).version_mismatch, true);
});

test('imported sources, relations, capabilities and snapshot descriptions never become restored authority', () => {
  const snapshot = create(['orbit', 'master-librarian']);
  snapshot.sources[0].scope = 'Untrusted imported source claim';
  snapshot.nodes[0].summary = 'Untrusted imported node claim';
  snapshot.relations[0].type = 'unsupported imported relation';
  const preview = parse(snapshot);
  assert.deepEqual(Object.keys(preview.proposal), ['title', 'task', 'node_ids', 'created_at', 'catalog_version', 'catalog_reviewed_on']);
  assert.ok(preview.changed_ids.includes('orbit'));
  const restored = createWorkingSet(catalog, preview.available_ids, preview.proposal.task, { title: preview.proposal.title, createdAt });
  assert.deepEqual(restored.nodes, catalog.nodes.filter((node) => preview.available_ids.includes(node.id)));
  assert.ok(!JSON.stringify(restored).includes('Untrusted imported'));
  assert.ok(!JSON.stringify(restored).includes('unsupported imported relation'));
});

test('accepts exact legacy 1.0.0 proposals with optional task context', () => {
  const legacy = create();
  delete legacy.format_version;
  delete legacy.title;
  delete legacy.task;
  const preview = parse(legacy);
  assert.equal(preview.legacy, true);
  assert.equal(preview.proposal.title, '');
  assert.equal(preview.proposal.task.request, '');
  legacy.title = 'Earlier task';
  legacy.task = { request: 'Keep literal wording' };
  assert.equal(parse(legacy).proposal.task.request, 'Keep literal wording');
});

test('rejects unsupported versions, authority status and other JSON containers', () => {
  for (const [field, value] of [['format_version', 3], ['format_version', '2'], ['format_version', null], ['schema_version', '2.0.0']]) {
    const snapshot = create(); snapshot[field] = value;
    throwsCode(() => parse(snapshot), 'unsupported-version');
  }
  for (const [field, value] of [['kind', 'instructions'], ['status', 'executed'], ['nodes', {}], ['task', null], ['title', null]]) {
    const snapshot = create(); snapshot[field] = value;
    throwsCode(() => parse(snapshot), 'invalid-working-set');
  }
  for (const value of [null, [], 1, 'text']) throwsCode(() => parse(value), 'invalid-working-set');
  throwsCode(() => parseWorkingSet('{broken', catalog), 'invalid-json');
});

test('format 2 requires every declared export field and every explicit task key', () => {
  const original = create();
  for (const field of Object.keys(original).filter((field) => field !== 'format_version')) {
    const value = copy(original); delete value[field];
    throwsCode(() => parse(value), 'invalid-working-set');
  }
  for (const field of TASK_FIELDS) {
    const value = copy(original); delete value.task[field];
    throwsCode(() => parse(value), 'invalid-working-set');
  }
});

test('validates dates, duplicate snapshot identities and source/reference integrity', () => {
  for (const dateValue of ['2026-02-30', '2026-13-01', 'yesterday']) {
    const value = create(); value.catalog_reviewed_on = dateValue;
    throwsCode(() => parse(value), 'invalid-working-set');
  }
  for (const time of ['2026-02-30T01:02:03Z', '2026-09-14', '2026-09-14T24:00:00Z', '2026-09-14T01:02:03']) {
    const value = create(); value.created_at = time;
    throwsCode(() => parse(value), 'invalid-working-set');
  }
  const offset = create([], {}, { createdAt: '2026-09-14T01:02:03-04:00' });
  assert.equal(parse(offset).proposal.created_at, offset.created_at);
  for (const field of ['nodes', 'sources', 'relations', 'capabilities']) {
    const value = create(catalog.nodes.map((node) => node.id));
    value[field].push(copy(value[field][0]));
    throwsCode(() => parse(value), 'invalid-working-set');
  }
  const missing = create(); missing.sources = [];
  throwsCode(() => parse(missing), 'invalid-working-set');
  const crossEdge = create(['orbit', 'master-librarian']); crossEdge.relations[0].to_id = 'elsewhere';
  throwsCode(() => parse(crossEdge), 'invalid-working-set');
});

test('UTF-8 byte budget accepts the exact boundary and rejects Unicode bytes above it', () => {
  const raw = JSON.stringify(create());
  const padding = MAX_IMPORT_BYTES - Buffer.byteLength(raw);
  assert.equal(parseWorkingSet(raw + ' '.repeat(padding), catalog).legacy, false);
  throwsCode(() => parseWorkingSet(raw + ' '.repeat(padding + 1), catalog), 'size-limit');
  const unicode = '🤧'.repeat(270000);
  assert.ok(unicode.length < MAX_IMPORT_BYTES);
  assert.ok(Buffer.byteLength(unicode) > MAX_IMPORT_BYTES);
  throwsCode(() => parseWorkingSet(unicode, catalog), 'size-limit');
});

test('deep imported structures are rejected before recursive comparison', () => {
  const value = create();
  let nested = {};
  for (let index = 0; index < 40; index += 1) nested = { child: nested };
  value.nodes[0].extra = nested;
  throwsCode(() => parse(value), 'invalid-working-set');
});

test('history saves independent immutable copies and returns fresh lists', () => {
  const storage = memoryStorage();
  const history = createCheckpointHistory(storage);
  assert.deepEqual(history.list(), []);
  const snapshot = create([], { request: 'Keep me' }, { title: 'Local task' });
  const entry = history.save(snapshot);
  snapshot.task.request = 'Changed caller';
  entry.working_set.task.request = 'Changed result';
  const firstList = history.list();
  assert.equal(firstList[0].working_set.task.request, 'Keep me');
  firstList[0].title = 'Changed list';
  assert.equal(history.list()[0].title, 'Local task');
  assert.deepEqual([...storage.data.keys()], [historyKey]);
});

test('history keeps twelve checkpoints without automatic pruning or overwrite', () => {
  const storage = memoryStorage();
  const history = createCheckpointHistory(storage);
  for (let index = 0; index < 12; index += 1) history.save(create([], {}, { title: `Checkpoint ${index}` }));
  const entries = history.list();
  assert.equal(new Set(entries.map((entry) => entry.id)).size, 12);
  const before = storage.data.get(historyKey);
  throwsCode(() => history.save(create()), 'history-full');
  assert.equal(storage.data.get(historyKey), before);
  assert.match(entries[0].title, /Checkpoint 0/);
});

test('history enforces total UTF-8 bytes atomically', () => {
  const storage = memoryStorage();
  const history = createCheckpointHistory(storage);
  const large = create([]);
  // Valid extra source snapshots remain inert; their byte cost still counts.
  large.sources = Array.from({ length: 40 }, (_, index) => ({ id: `source-${index}`, title: 'Fixture', source_date: null, reviewed_on: '2026-09-14', access: 'owner-held', url: null, evidence_kind: 'fixture', scope: 'é'.repeat(9000) }));
  assert.ok(Buffer.byteLength(JSON.stringify(large)) < MAX_IMPORT_BYTES);
  history.save(large);
  history.save(large);
  const before = storage.data.get(historyKey);
  assert.ok(Buffer.byteLength(before) < MAX_HISTORY_BYTES);
  throwsCode(() => history.save(large), 'size-limit');
  assert.equal(storage.data.get(historyKey), before);
  assert.equal(history.list().length, 2);
});

test('remove changes only the requested checkpoint and missing IDs leave storage untouched', () => {
  const storage = memoryStorage();
  const history = createCheckpointHistory(storage);
  const first = history.save(create([], {}, { title: 'First' }));
  const second = history.save(create([], {}, { title: 'Second' }));
  assert.equal(history.remove(first.id), true);
  assert.deepEqual(history.list().map((entry) => entry.id), [second.id]);
  const before = storage.data.get(historyKey);
  assert.equal(history.remove(first.id), false);
  assert.equal(storage.data.get(historyKey), before);
});

test('malformed saved JSON, duplicate IDs and invalid snapshots never get overwritten or cleared', () => {
  const storage = memoryStorage();
  const history = createCheckpointHistory(storage);
  const entry = history.save(create());
  const malformed = [
    '{broken', '{}', JSON.stringify([entry, entry]),
    JSON.stringify([{ ...entry, title: 'Different' }]),
    JSON.stringify([{ ...entry, working_set: { ...entry.working_set, status: 'executed' } }]),
  ];
  for (const raw of malformed) {
    storage.data.set(historyKey, raw);
    for (const action of [() => history.list(), () => history.save(create()), () => history.remove(entry.id), () => history.clear()]) {
      throwsCode(action, 'storage-invalid');
      assert.equal(storage.data.get(historyKey), raw);
    }
  }
});

test('quota and permission errors leave existing checkpoints unchanged', () => {
  const storage = memoryStorage();
  const history = createCheckpointHistory(storage);
  const entry = history.save(create());
  const before = storage.data.get(historyKey);
  storage.failSet = true;
  throwsCode(() => history.save(create()), 'storage-write-failed');
  throwsCode(() => history.remove(entry.id), 'storage-write-failed');
  assert.equal(storage.data.get(historyKey), before);
  storage.failGet = true;
  for (const action of [() => history.list(), () => history.save(create()), () => history.clear()]) throwsCode(action, 'storage-unavailable');
  assert.equal(storage.data.get(historyKey), before);
});

test('clear removes only this history key, retains unrelated state and releases the stored entries', () => {
  const storage = memoryStorage();
  storage.setItem('unrelated-app', 'keep');
  const history = createCheckpointHistory(storage);
  history.save(create());
  assert.equal(history.clear(), true);
  assert.equal(storage.data.has(historyKey), false);
  assert.equal(storage.data.get('unrelated-app'), 'keep');
  assert.deepEqual(history.list(), []);
  assert.equal(history.clear(), false);
  const mutations = storage.calls.filter(([operation]) => operation !== 'get').slice(1);
  assert.ok(mutations.every(([, key]) => key === historyKey));
});

test('failed clear keeps history, and custom history keys never affect the default key', () => {
  const storage = memoryStorage();
  const history = createCheckpointHistory(storage, 'garden-test', 2);
  storage.setItem(historyKey, 'untouched');
  history.save(create());
  const before = storage.data.get('garden-test');
  storage.failRemove = true;
  throwsCode(() => history.clear(), 'storage-write-failed');
  assert.equal(storage.data.get('garden-test'), before);
  storage.failRemove = false;
  history.clear();
  assert.equal(storage.data.get(historyKey), 'untouched');
  for (const limit of [0, 13, 1.5]) throwsCode(() => createCheckpointHistory(storage, 'x', limit), 'invalid-working-set');
  throwsCode(() => createCheckpointHistory(null), 'storage-unavailable');
});
