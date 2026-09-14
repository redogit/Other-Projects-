const idPattern = /^[a-z0-9][a-z0-9_.-]{0,127}$/;
export const RELATION_TYPES = Object.freeze(['related_to', 'depends_on', 'supports', 'derived_from', 'predecessor']);
const relationTypes = new Set(RELATION_TYPES);

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

