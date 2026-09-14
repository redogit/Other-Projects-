import { createHash } from 'node:crypto';
import { validateCatalog, RELATION_TYPES } from './catalog.mjs';

export const COMPILER_VERSION = '1.0.0';
const hash = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');
const freeze = value => {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
};

/** Compile this catalog's structure and literal-search expressions before serving queries. */
export function compileCatalog(catalog) {
  validateCatalog(catalog);
  const nodeIds = catalog.nodes.map(node => node.id);
  const positions = new Map(nodeIds.map((id, i) => [id, i]));
  const sourcePositions = new Map(catalog.sources.map((source, i) => [source.id, i]));
  const rows = () => catalog.nodes.map(() => []);
  const children = rows();
  const relations = rows();
  const capabilities = rows();
  const byType = Object.fromEntries(RELATION_TYPES.map(type => [type, []]));
  const roots = [];
  const projects = [];
  catalog.nodes.forEach((node, i) => {
    if (node.parent_id === null) roots.push(i);
    else children[positions.get(node.parent_id)].push(i);
    if (node.kind === 'project') projects.push(i);
  });
  catalog.relations.forEach((edge, i) => {
    const a = positions.get(edge.from_id), b = positions.get(edge.to_id);
    relations[a].push(i);
    if (a !== b) relations[b].push(i);
    byType[edge.type].push(i);
  });
  catalog.capabilities.forEach((capability, i) => capabilities[positions.get(capability.node_id)].push(i));
  const payload = {
    format: 'knowledge-garden-query-plan', compiler_version: COMPILER_VERSION,
    catalog_version: catalog.catalog_version, catalog_sha256: hash(catalog),
    hash_semantics: 'SHA-256 of JSON.stringify(parsed catalog), UTF-8; not original file bytes or authorship',
    node_ids: nodeIds, roots, projects, children, relations, capabilities,
    source_slots: catalog.nodes.map(node => node.source_ids.map(id => sourcePositions.get(id))),
    relation_types: byType,
    search_text: catalog.nodes.map(node => [node.name, node.summary, ...node.tags].join('\n').toLowerCase()),
  };
  return freeze({ ...payload, plan_sha256: hash(payload) });
}

/** Plans are local build artifacts, never accepted from a browser import or HTTP request. */
export function validatePlan(catalog, plan) {
  const bad = message => { throw new TypeError(`Invalid compiled plan: ${message}. Rebuild with npm run build.`); };
  if (!plan || typeof plan !== 'object' || Array.isArray(plan)) bad('expected an object');
  if (plan.format !== 'knowledge-garden-query-plan' || plan.compiler_version !== COMPILER_VERSION) bad('unsupported format/compiler');
  if (plan.catalog_version !== catalog.catalog_version || plan.catalog_sha256 !== hash(catalog)) bad('catalog changed');
  const { plan_sha256, ...payload } = plan;
  if (plan_sha256 !== hash(payload)) bad('content hash mismatch');
  const count = catalog.nodes.length;
  if (JSON.stringify(plan.node_ids) !== JSON.stringify(catalog.nodes.map(node => node.id))) bad('node identity/order changed');
  const slots = (values, maximum, label) => {
    if (!Array.isArray(values) || values.length > maximum || new Set(values).size !== values.length || values.some(i => !Number.isInteger(i) || i < 0 || i >= maximum)) bad(label);
  };
  slots(plan.roots, count, 'root slots'); slots(plan.projects, count, 'project slots');
  for (const [key, maximum] of [['children', count], ['relations', catalog.relations.length], ['capabilities', catalog.capabilities.length], ['source_slots', catalog.sources.length]]) {
    if (!Array.isArray(plan[key]) || plan[key].length !== count) bad(`${key} row count`);
    plan[key].forEach(row => slots(row, maximum, key));
  }
  if (!Array.isArray(plan.search_text) || plan.search_text.length !== count || plan.search_text.some(text => typeof text !== 'string')) bad('search expressions');
  if (!plan.relation_types || JSON.stringify(Object.keys(plan.relation_types)) !== JSON.stringify(RELATION_TYPES)) bad('relation types');
  for (const type of RELATION_TYPES) slots(plan.relation_types[type], catalog.relations.length, type);
  // A checksum is not a derivation check. Independently verify each compiled row
  // against catalog membership, completeness and source order before execution.
  const ordered = values => values.every((value, i) => i === 0 || values[i - 1] < value);
  const nodePositions = new Map(catalog.nodes.map((node, i) => [node.id, i]));
  const edgeCounts = catalog.nodes.map(() => 0);
  const capabilityCounts = catalog.nodes.map(() => 0);
  const typeCounts = Object.fromEntries(RELATION_TYPES.map(type => [type, 0]));
  for (const edge of catalog.relations) {
    edgeCounts[nodePositions.get(edge.from_id)]++;
    if (edge.from_id !== edge.to_id) edgeCounts[nodePositions.get(edge.to_id)]++;
    typeCounts[edge.type]++;
  }
  for (const capability of catalog.capabilities) capabilityCounts[nodePositions.get(capability.node_id)]++;
  const checkSelection = (values, predicate, count, label) => {
    if (!ordered(values) || values.length !== count || values.some(i => !predicate(i))) bad(`${label} derivation`);
  };
  checkSelection(plan.roots, i => catalog.nodes[i].parent_id === null, catalog.nodes.filter(n => n.parent_id === null).length, 'roots');
  checkSelection(plan.projects, i => catalog.nodes[i].kind === 'project', catalog.nodes.filter(n => n.kind === 'project').length, 'projects');
  const seenChildren = new Set();
  for (let i = 0; i < count; i++) {
    const node = catalog.nodes[i];
    if (!ordered(plan.children[i])) bad('child order');
    for (const slot of plan.children[i]) {
      if (catalog.nodes[slot].parent_id !== node.id || seenChildren.has(slot)) bad('child parent');
      seenChildren.add(slot);
    }
    checkSelection(plan.relations[i], j => catalog.relations[j].from_id === node.id || catalog.relations[j].to_id === node.id, edgeCounts[i], 'node relations');
    checkSelection(plan.capabilities[i], j => catalog.capabilities[j].node_id === node.id, capabilityCounts[i], 'node capabilities');
    if (plan.source_slots[i].length !== node.source_ids.length || plan.source_slots[i].some((j, k) => catalog.sources[j].id !== node.source_ids[k])) bad('node sources');
    if (plan.search_text[i] !== [node.name, node.summary, ...node.tags].join('\n').toLowerCase()) bad('search expression derivation');
  }
  if (seenChildren.size !== count - plan.roots.length) bad('missing child');
  for (const type of RELATION_TYPES) checkSelection(plan.relation_types[type], j => catalog.relations[j].type === type, typeCounts[type], 'relation type');
  return plan;
}

/** An executor owns immutable copies; dispose releases its catalog, plan and lookup references. */
export function createExecutor(catalog, compiled = compileCatalog(catalog)) {
  validateCatalog(catalog);
  validatePlan(catalog, compiled);
  let snapshot = freeze(structuredClone(catalog));
  let plan = freeze(structuredClone(compiled));
  let positions = new Map(plan.node_ids.map((id, i) => [id, i]));
  const ensure = () => { if (!snapshot) throw new Error('This query executor has been released.'); };
  const position = id => {
    ensure();
    if (!positions.has(id)) throw new RangeError(`Unknown node: ${id}`);
    return positions.get(id);
  };
  const mapNodes = slots => slots.map(i => snapshot.nodes[i]);
  const nested = slot => ({ ...snapshot.nodes[slot], children: plan.children[slot].map(nested) });
  return Object.freeze({
    catalog() { ensure(); return snapshot; },
    has(id) { ensure(); return positions.has(id); },
    node(id) { const i = position(id); return snapshot.nodes[i]; },
    detail(id) {
      const i = position(id);
      return { node: snapshot.nodes[i], children: mapNodes(plan.children[i]),
        relations: plan.relations[i].map(j => snapshot.relations[j]),
        capabilities: plan.capabilities[i].map(j => snapshot.capabilities[j]),
        sources: plan.source_slots[i].map(j => snapshot.sources[j]) };
    },
    hierarchy(root = null) {
      ensure();
      return { roots: (root === null ? plan.roots : [position(root)]).map(nested) };
    },
    relations(nodeId = null, type = null) {
      ensure();
      if (type !== null && !RELATION_TYPES.includes(type)) throw new RangeError(`Unknown relation type: ${type}`);
      if (nodeId === null && type === null) return [...snapshot.relations];
      const indices = nodeId === null ? plan.relation_types[type] : plan.relations[position(nodeId)];
      return indices.filter(i => type === null || snapshot.relations[i].type === type).map(i => snapshot.relations[i]);
    },
    capabilities(nodeId = null) {
      ensure();
      return nodeId === null ? [...snapshot.capabilities] : plan.capabilities[position(nodeId)].map(i => snapshot.capabilities[i]);
    },
    search(query = null, { projectsOnly = false, status = null } = {}) {
      ensure();
      if (query !== null && typeof query !== 'string') throw new TypeError('Search query must be a string or null.');
      const q = query?.toLowerCase() ?? null;
      const matches = i => (q === null || plan.search_text[i].includes(q)) && (status === null || snapshot.nodes[i].status === status);
      return projectsOnly ? plan.projects.filter(matches).map(i => snapshot.nodes[i]) : snapshot.nodes.filter((_, i) => matches(i));
    },
    dispose() { snapshot = null; plan = null; positions?.clear(); positions = null; },
  });
}
