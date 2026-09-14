export const ASPECT_AXES = Object.freeze({
  scope: Object.freeze(['local', 'task-wide', 'project-wide', 'cross-cutting', 'boundary-only', 'execution-only']),
  effect: Object.freeze(['observational', 'validating', 'annotative', 'measuring', 'decorative', 'protective']),
  mutation: Object.freeze(['immutable', 'bounded-mutable', 'reversible']),
  persistence: Object.freeze(['ephemeral', 'session-lived', 'checkpointed']),
  predictability: Object.freeze(['deterministic', 'seeded', 'reactive']),
  purpose: Object.freeze(['diagnostic', 'exploratory', 'adversarial', 'educational', 'playful', 'accessibility-oriented']),
  temperament: Object.freeze(['curious', 'conservative', 'whimsical', 'quiet', 'skeptical', 'experimental']),
});

const MUTABLE_AXES = Object.freeze(['scope', 'effect', 'persistence', 'predictability', 'purpose', 'temperament']);
const FIXED = Object.freeze({ authority: 'sidecar-only', semantics: 'preserved' });

function hash32(text) {
  let h = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) { h ^= text.charCodeAt(i); h = Math.imul(h, 0x01000193); }
  return h >>> 0;
}

export function createAspectProfile(overrides = {}) {
  if (!overrides || typeof overrides !== 'object' || Array.isArray(overrides)) throw new TypeError('Aspect overrides must be an object.');
  const defaults = {
    scope: 'cross-cutting', effect: 'annotative', mutation: 'bounded-mutable', persistence: 'session-lived',
    predictability: 'seeded', purpose: 'playful', temperament: 'curious', ...FIXED,
  };
  const profile = { ...defaults, ...overrides };
  for (const [axis, values] of Object.entries(ASPECT_AXES)) {
    if (!values.includes(profile[axis])) throw new RangeError(`Unknown ${axis} adjective: ${profile[axis]}`);
  }
  if (profile.authority !== FIXED.authority) throw new RangeError('Aspect authority must remain sidecar-only.');
  if (profile.semantics !== FIXED.semantics) throw new RangeError('Aspect semantics must remain preserved.');
  const extras = Object.keys(profile).filter(key => ![...Object.keys(ASPECT_AXES), ...Object.keys(FIXED)].includes(key));
  if (extras.length) throw new RangeError(`Unknown aspect field: ${extras[0]}`);
  return Object.freeze(profile);
}

export function mutateAspect(profile, seed = 640064, generation = 0) {
  const before = createAspectProfile(profile);
  if (before.mutation === 'immutable') throw new TypeError('Immutable aspects cannot mutate.');
  if (!Number.isSafeInteger(seed) || !Number.isSafeInteger(generation) || generation < 0) throw new RangeError('Mutation seed/generation must be safe integers and generation non-negative.');
  const axis = MUTABLE_AXES[hash32(`${seed}:${generation}:axis`) % MUTABLE_AXES.length];
  const values = ASPECT_AXES[axis];
  const current = values.indexOf(before[axis]);
  const step = 1 + (hash32(`${seed}:${generation}:${axis}:step`) % (values.length - 1));
  const to = values[(current + step) % values.length];
  const after = createAspectProfile({ ...before, [axis]: to });
  return Object.freeze({
    before, after,
    receipt: Object.freeze({ axis, from: before[axis], to, seed, generation, authority: FIXED.authority, semantics: FIXED.semantics }),
  });
}

export function revertAspectMutation(mutation) {
  if (!mutation?.before || !mutation?.receipt) throw new TypeError('A complete mutation receipt is required.');
  return createAspectProfile(mutation.before);
}

export function createAspectRuntime(executor, initialProfile = createAspectProfile()) {
  if (!executor || typeof executor !== 'object') throw new TypeError('An executor is required.');
  let profile = createAspectProfile(initialProfile), disposed = false;
  const events = [];
  const ensure = () => { if (disposed) throw new Error('This aspect runtime has been released.'); };
  const record = (operation, phase) => events.push(Object.freeze({ operation, phase, purpose: profile.purpose, temperament: profile.temperament, semantics: profile.semantics }));
  const forward = name => (...args) => {
    ensure();
    if (typeof executor[name] !== 'function') throw new TypeError(`Executor does not expose ${name}().`);
    record(name, 'before');
    const output = executor[name](...args);
    record(name, 'after');
    return output;
  };
  const api = {
    profile() { ensure(); return profile; },
    events() { ensure(); return Object.freeze([...events]); },
    mutate(seed = 640064, generation = 0) { ensure(); const change = mutateAspect(profile, seed, generation); profile = change.after; return change; },
    catalog: forward('catalog'), has: forward('has'), node: forward('node'), detail: forward('detail'),
    hierarchy: forward('hierarchy'), relations: forward('relations'), capabilities: forward('capabilities'), search: forward('search'),
    dispose() { if (disposed) return; record('dispose', 'before'); executor.dispose?.(); disposed = true; events.length = 0; profile = null; },
  };
  return Object.freeze(api);
}
