/** Browser-side proposals only. Imported snapshots never execute project instructions. */
export const TASK_FIELDS = Object.freeze(['subject', 'motivator', 'request', 'obligation', 'surface', 'output_definition']);
export const MAX_IMPORT_BYTES = 1024 * 1024;
export const MAX_HISTORY_BYTES = 2 * 1024 * 1024;
const encoder = new TextEncoder();
const SNAPSHOT_FIELDS = ['kind', 'schema_version', 'created_at', 'catalog_version', 'catalog_reviewed_on', 'status', 'scope', 'navigation_note', 'nodes', 'relations', 'capabilities', 'sources', 'rules'];
const CURRENT_FIELDS = [...SNAPSHOT_FIELDS, 'format_version', 'title', 'task'];
const MAX_RECORDS = 10000;
let fallbackCounter = 0;

export class WorkingSetError extends Error {
  constructor(code, message, cause) {
    super(message, cause === undefined ? undefined : { cause });
    this.name = 'WorkingSetError';
    this.code = code;
  }
}

function fail(message, code = 'invalid-working-set') { throw new WorkingSetError(code, message); }
function object(value, label) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) fail(`${label} must be an object.`);
}
function required(value, fields, label) {
  object(value, label);
  for (const field of fields) if (!Object.hasOwn(value, field)) fail(`${label} is missing ${field}.`);
}
function text(value, label, max = 20000, min = 0) {
  if (typeof value !== 'string' || value.length < min || value.length > max) fail(`${label} must be text of ${min}–${max} characters.`);
  return value;
}
function id(value, label) {
  if (typeof value !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(value)) fail(`${label} must be a stable ID of 1–128 letters, digits, dots, underscores, colons or hyphens.`);
  return value;
}
function array(value, label, max = MAX_RECORDS) {
  if (!Array.isArray(value) || value.length > max) fail(`${label} must be a list with at most ${max} entries.`);
  return value;
}
function ids(value, label) {
  array(value, label);
  const seen = new Set();
  for (const item of value) {
    id(item, label);
    if (seen.has(item)) fail(`${label} contains duplicate ID ${item}.`);
    seen.add(item);
  }
  return seen;
}
function date(value, label) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) fail(`${label} must be an ISO calendar date.`);
  const parsed = new Date(`${value}T00:00:00.000Z`);
  if (!Number.isFinite(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== value) fail(`${label} is not a valid calendar date.`);
}
function timestamp(value, label) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,3})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.test(value) || !Number.isFinite(Date.parse(value))) fail(`${label} must be an ISO timestamp with a timezone.`);
  date(value.slice(0, 10), label);
}
function taskContext(value = {}) {
  object(value, 'Task context');
  for (const key of Object.keys(value)) if (!TASK_FIELDS.includes(key)) fail(`Unknown task field ${key}.`);
  return Object.fromEntries(TASK_FIELDS.map((key) => [key, text(Object.hasOwn(value, key) ? value[key] : '', `Task ${key}`, 2000)]));
}
function serialized(value, maxBytes, label) {
  let result;
  try { result = JSON.stringify(value); } catch (error) { throw new WorkingSetError('invalid-working-set', `${label} must be JSON data without circular references.`, error); }
  if (typeof result !== 'string') fail(`${label} must contain JSON data.`);
  if (encoder.encode(result).byteLength > maxBytes) fail(`${label} exceeds its ${maxBytes / 1024} KiB UTF-8 size limit.`, 'size-limit');
  return result;
}
function boundedJSON(textValue, maxBytes, label) {
  if (typeof textValue !== 'string') fail(`${label} must be JSON text.`);
  if (encoder.encode(textValue).byteLength > maxBytes) fail(`${label} exceeds its ${maxBytes / 1024} KiB UTF-8 size limit.`, 'size-limit');
  let value;
  try { value = JSON.parse(textValue); } catch (error) { throw new WorkingSetError('invalid-json', `${label} is not valid JSON.`, error); }
  // Bound recursive comparisons before inspecting arbitrary imported snapshots.
  const stack = [[value, 0]];
  while (stack.length) {
    const [item, depth] = stack.pop();
    if (depth > 32) fail(`${label} contains data nested too deeply.`);
    if (item && typeof item === 'object') for (const child of Object.values(item)) stack.push([child, depth + 1]);
  }
  return value;
}
function recordList(value, label, fields) {
  array(value, label);
  const map = new Map();
  for (const record of value) {
    required(record, ['id', ...fields], label);
    id(record.id, `${label} ID`);
    if (map.has(record.id)) fail(`${label} contains duplicate ID ${record.id}.`);
    map.set(record.id, record);
  }
  return map;
}
function validateSnapshot(value) {
  required(value, SNAPSHOT_FIELDS, 'Working set');
  const legacy = !Object.hasOwn(value, 'format_version');
  if (value.kind !== 'proposed-working-set' || value.status !== 'proposal') fail('Only proposed Knowledge Garden working sets can be restored.');
  if (value.schema_version !== '1.0.0' || (!legacy && value.format_version !== 2)) fail('This working-set format or catalog schema version is not supported.', 'unsupported-version');
  const allowed = legacy ? [...SNAPSHOT_FIELDS, 'title', 'task'] : CURRENT_FIELDS;
  for (const key of Object.keys(value)) if (!allowed.includes(key)) fail(`Unknown working-set field ${key}.`);
  if (!legacy) {
    required(value, CURRENT_FIELDS, 'Working set');
    required(value.task, TASK_FIELDS, 'Task context');
  }
  text(Object.hasOwn(value, 'title') ? value.title : '', 'Task title', 120);
  taskContext(Object.hasOwn(value, 'task') ? value.task : {});
  timestamp(value.created_at, 'Creation time');
  text(value.catalog_version, 'Catalog version', 120, 1);
  date(value.catalog_reviewed_on, 'Catalog review date');
  text(value.scope, 'Working-set scope', 20000, 1);
  text(value.navigation_note, 'Navigation note', 20000, 1);
  array(value.rules, 'Rules', 1000).forEach((rule) => text(rule, 'Rule', 20000, 1));
  const nodes = recordList(value.nodes, 'Nodes', ['name', 'kind', 'parent_id', 'summary', 'status', 'evidence_status', 'source_ids', 'tags', 'next_action']);
  const sources = recordList(value.sources, 'Sources', ['title', 'source_date', 'reviewed_on', 'access', 'url', 'evidence_kind', 'scope']);
  const relations = recordList(value.relations, 'Relations', ['from_id', 'to_id', 'type', 'scope', 'status', 'source_ids']);
  const capabilities = recordList(value.capabilities, 'Capabilities', ['node_id', 'name', 'transport', 'status', 'invocation', 'input', 'output', 'limitations', 'source_ids']);
  for (const node of nodes.values()) {
    for (const field of ['name', 'summary', 'status', 'evidence_status', 'next_action']) text(node[field], `Node ${field}`, 20000, 1);
    if (!['group', 'project', 'component', 'role'].includes(node.kind)) fail('Node kind is not recognized.');
    if (node.parent_id !== null) id(node.parent_id, 'Parent ID');
    array(node.tags, 'Node tags', 1000).forEach((tag) => text(tag, 'Tag', 2000, 1));
  }
  for (const relation of relations.values()) {
    if (!nodes.has(relation.from_id) || !nodes.has(relation.to_id)) fail('A relation refers outside the selected node set.');
    text(relation.type, 'Relation type', 120, 1);
    text(relation.scope, 'Relation scope', 20000, 1);
    text(relation.status, 'Relation status', 120, 1);
  }
  for (const capability of capabilities.values()) {
    if (!nodes.has(capability.node_id)) fail('A capability refers outside the selected node set.');
    for (const field of ['name', 'transport', 'status', 'invocation', 'input', 'output']) text(capability[field], `Capability ${field}`, 20000, 1);
    array(capability.limitations, 'Capability limitations', 1000).forEach((item) => text(item, 'Capability limitation', 20000, 1));
  }
  for (const source of sources.values()) {
    for (const field of ['title', 'access', 'evidence_kind', 'scope']) text(source[field], `Source ${field}`, 20000, 1);
    if (source.source_date !== null) date(source.source_date, 'Source date');
    date(source.reviewed_on, 'Source review date');
    if (source.url !== null) text(source.url, 'Source URL', 4000, 1);
  }
  for (const record of [...nodes.values(), ...relations.values(), ...capabilities.values()]) {
    for (const sourceId of ids(record.source_ids, 'Source IDs')) if (!sources.has(sourceId)) fail(`Source ${sourceId} is missing from the working set.`);
  }
  return { legacy, nodes };
}
function copySnapshot(value) {
  const copy = boundedJSON(serialized(value, MAX_IMPORT_BYTES, 'Working set'), MAX_IMPORT_BYTES, 'Working set');
  validateSnapshot(copy);
  return copy;
}
function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value && typeof value === 'object') return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
  return JSON.stringify(value);
}

export function createWorkingSet(catalog, nodeIds, task = {}, options = {}) {
  required(catalog, ['schema_version', 'catalog_version', 'reviewed_on', 'nodes', 'relations', 'capabilities', 'sources', 'rules'], 'Catalog');
  if (!Array.isArray(nodeIds) && !(nodeIds instanceof Set)) fail('Selected node IDs must be a list or set.');
  object(options, 'Working-set options');
  const selection = ids(Array.from(nodeIds), 'Selected node IDs');
  const catalogNodes = recordList(catalog.nodes, 'Catalog nodes', []);
  const catalogSources = recordList(catalog.sources, 'Catalog sources', []);
  const nodes = [...selection].map((nodeId) => {
    if (!catalogNodes.has(nodeId)) fail(`Node ${nodeId} is not in the current catalog.`, 'unknown-node');
    return catalogNodes.get(nodeId);
  });
  const relations = catalog.relations.filter((relation) => selection.has(relation.from_id) && selection.has(relation.to_id));
  const capabilities = catalog.capabilities.filter((capability) => selection.has(capability.node_id));
  const sourceIds = new Set([...nodes, ...relations, ...capabilities].flatMap((record) => record.source_ids));
  const sources = [...sourceIds].map((sourceId) => {
    if (!catalogSources.has(sourceId)) fail(`Source ${sourceId} is not in the current catalog.`);
    return catalogSources.get(sourceId);
  });
  return copySnapshot({
    kind: 'proposed-working-set', format_version: 2, schema_version: catalog.schema_version,
    created_at: Object.hasOwn(options, 'createdAt') ? options.createdAt : new Date().toISOString(), catalog_version: catalog.catalog_version,
    catalog_reviewed_on: catalog.reviewed_on, status: 'proposal', title: Object.hasOwn(options, 'title') ? options.title : '', task: taskContext(task),
    scope: 'Explicit browser selection and task context from the Knowledge Garden catalog. No project was invoked, changed, or independently verified.',
    navigation_note: 'Parent IDs are navigation references; ancestor records may be outside this selected set. Connections retain their recorded type and scope.',
    nodes, relations, capabilities, sources, rules: catalog.rules,
  });
}

export function parseWorkingSet(jsonText, catalog) {
  const value = boundedJSON(jsonText, MAX_IMPORT_BYTES, 'Working set');
  const { legacy, nodes } = validateSnapshot(value);
  const current = recordList(catalog.nodes, 'Current catalog nodes', []);
  const available_ids = [], missing_ids = [], changed_ids = [];
  for (const [nodeId, node] of nodes) {
    if (!current.has(nodeId)) missing_ids.push(nodeId);
    else {
      available_ids.push(nodeId);
      if (canonical(node) !== canonical(current.get(nodeId))) changed_ids.push(nodeId);
    }
  }
  return {
    proposal: { title: value.title ?? '', task: taskContext(value.task ?? {}), node_ids: [...nodes.keys()], created_at: value.created_at, catalog_version: value.catalog_version, catalog_reviewed_on: value.catalog_reviewed_on },
    available_ids, missing_ids, changed_ids,
    version_mismatch: value.catalog_version !== catalog.catalog_version || value.catalog_reviewed_on !== catalog.reviewed_on || value.schema_version !== catalog.schema_version,
    legacy,
  };
}

export function createCheckpointHistory(storage, key = 'knowledge-garden.checkpoints.v1', limit = 12) {
  if (!storage || typeof storage.getItem !== 'function' || typeof storage.setItem !== 'function' || typeof storage.removeItem !== 'function') fail('Checkpoint storage is unavailable in this browser.', 'storage-unavailable');
  text(key, 'Checkpoint storage key', 200, 1);
  if (!Number.isInteger(limit) || limit < 1 || limit > 12) fail('Checkpoint history limit must be between 1 and 12.');
  function read() {
    let raw;
    try { raw = storage.getItem(key); } catch (error) { throw new WorkingSetError('storage-unavailable', 'Could not read checkpoints on this device. Browser storage may be disabled.', error); }
    if (raw === null) return [];
    try {
      const entries = boundedJSON(raw, MAX_HISTORY_BYTES, 'Saved checkpoints');
      array(entries, 'Saved checkpoints', limit);
      const seen = new Set();
      for (const entry of entries) {
        required(entry, ['id', 'saved_at', 'title', 'working_set'], 'Checkpoint');
        if (Object.keys(entry).some((field) => !['id', 'saved_at', 'title', 'working_set'].includes(field))) fail('Checkpoint contains an unknown field.');
        id(entry.id, 'Checkpoint ID');
        if (seen.has(entry.id)) fail('Saved checkpoints contain duplicate IDs.');
        seen.add(entry.id);
        timestamp(entry.saved_at, 'Checkpoint save time');
        text(entry.title, 'Checkpoint title', 120);
        serialized(entry.working_set, MAX_IMPORT_BYTES, 'Working set');
        validateSnapshot(entry.working_set);
        if (entry.title !== (entry.working_set.title ?? '')) fail('Checkpoint title differs from its working set.');
      }
      return entries;
    } catch (error) { throw new WorkingSetError('storage-invalid', 'Saved checkpoint data could not be read safely. Existing data was left unchanged.', error); }
  }
  function write(entries) {
    const raw = serialized(entries, MAX_HISTORY_BYTES, 'Saved checkpoints');
    try { storage.setItem(key, raw); } catch (error) { throw new WorkingSetError('storage-write-failed', 'Could not save checkpoints. Browser storage may be full or disabled; existing checkpoints were left unchanged.', error); }
  }
  return {
    list: read,
    save(workingSet) {
      const entries = read();
      if (entries.length >= limit) fail(`All ${limit} checkpoint slots are in use. Download a checkpoint to keep a copy, then remove one before saving.`, 'history-full');
      const copy = copySnapshot(workingSet);
      const used = new Set(entries.map((entry) => entry.id));
      let checkpointId;
      do {
        const token = globalThis.crypto?.randomUUID?.() ?? Date.now().toString(36);
        checkpointId = `checkpoint-${token}-${++fallbackCounter}`;
      } while (used.has(checkpointId));
      const entry = { id: checkpointId, saved_at: new Date().toISOString(), title: copy.title ?? '', working_set: copy };
      write([...entries, entry]);
      return entry;
    },
    remove(checkpointId) {
      id(checkpointId, 'Checkpoint ID');
      const entries = read();
      const retained = entries.filter((entry) => entry.id !== checkpointId);
      if (retained.length === entries.length) return false;
      write(retained);
      return true;
    },
    clear() {
      const entries = read();
      try { storage.removeItem(key); } catch (error) { throw new WorkingSetError('storage-write-failed', 'Could not clear saved checkpoints. Browser storage may be disabled; existing checkpoints were left unchanged.', error); }
      return entries.length > 0;
    },
  };
}
