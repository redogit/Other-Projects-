import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ASPECT_AXES, createAspectProfile, mutateAspect, revertAspectMutation, createAspectRuntime } from '../aspects.mjs';
import { createExecutor } from '../compiler.mjs';
import { fixture } from './fixtures.mjs';

test('profiles use declared adjectives while semantic authority remains fixed', () => {
  const p = createAspectProfile({ purpose: 'playful', temperament: 'whimsical' });
  assert.equal(p.authority, 'sidecar-only'); assert.equal(p.semantics, 'preserved');
  for (const [axis, values] of Object.entries(ASPECT_AXES)) assert.ok(values.includes(p[axis]));
  assert.throws(() => createAspectProfile({ semantics: 'mutable' }), /preserved/);
  assert.throws(() => createAspectProfile({ authority: 'compiler-write' }), /sidecar-only/);
});

test('mutation is deterministic, replayable, bounded and reversible', () => {
  const p = createAspectProfile();
  for (let generation = 0; generation < 1000; generation++) {
    const a = mutateAspect(p, 640064, generation), b = mutateAspect(p, 640064, generation);
    assert.deepEqual(a, b);
    assert.equal(a.after.semantics, 'preserved'); assert.equal(a.after.authority, 'sidecar-only');
    assert.deepEqual(revertAspectMutation(a), p);
  }
});

test('aspect runtime preserves compiled executor outputs before and after mutation', () => {
  const catalog = fixture();
  const raw = createExecutor(catalog);
  const wrapped = createAspectRuntime(createExecutor(catalog), createAspectProfile({ purpose: 'playful', temperament: 'whimsical' }));
  for (const id of catalog.nodes.map(node => node.id)) {
    assert.deepEqual(wrapped.node(id), raw.node(id));
    assert.deepEqual(wrapped.detail(id), raw.detail(id));
    assert.deepEqual(wrapped.hierarchy(id), raw.hierarchy(id));
  }
  assert.deepEqual(wrapped.hierarchy(), raw.hierarchy());
  assert.deepEqual(wrapped.relations(), raw.relations());
  assert.deepEqual(wrapped.capabilities(), raw.capabilities());
  for (const q of [null, '', 'alpha', '.*']) assert.deepEqual(wrapped.search(q), raw.search(q));
  const mutation = wrapped.mutate(640064, 3);
  assert.equal(mutation.after.semantics, 'preserved');
  assert.deepEqual(wrapped.hierarchy(), raw.hierarchy());
  assert.deepEqual(wrapped.search('alpha'), raw.search('alpha'));
  assert.ok(wrapped.events().every(event => event.semantics === 'preserved'));
  wrapped.dispose(); raw.dispose();
  assert.throws(() => wrapped.profile(), /released/);
});

test('immutable adjective profiles reject mutation explicitly', () => {
  assert.throws(() => mutateAspect(createAspectProfile({ mutation: 'immutable' })), /cannot mutate/);
});
