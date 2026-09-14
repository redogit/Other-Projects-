const $ = (selector) => document.querySelector(selector);
const ui = {
  search: $('#project-search'), filter: $('#kind-filter'), clear: $('#clear-filter'),
  hierarchy: $('#hierarchy'), detail: $('#node-detail'), results: $('#results-count'),
  workingList: $('#working-list'), download: $('#download-set'),
};
let catalog;
let nodes = new Map();
let sources = new Map();
let childNodes = new Map();
let selectedId = null;
const workingSet = new Set();

function element(tag, className, text) {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (text !== undefined && text !== null) item.textContent = String(text);
  return item;
}
function words(value) { return String(value || '').replaceAll('_', ' ').replaceAll('-', ' '); }
function announce(message) { $('#action-status').textContent = message; }
function validPublicUrl(source) {
  if (source.access !== 'public' || !source.url) return null;
  try { const url = new URL(source.url); return url.protocol === 'https:' ? url.href : null; }
  catch { return null; }
}
function publicLink(label, href, className) {
  const link = element('a', className, label);
  link.href = href;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  link.append(element('span', 'sr-only', ' (opens in a new tab)'));
  return link;
}
function goButton(node, className, label = node.name, focus = true) {
  const button = element('button', className, label);
  button.type = 'button';
  button.dataset.nodeId = node.id;
  button.addEventListener('click', () => selectNode(node.id, { focus, scroll: focus }));
  return button;
}
function ancestorNodes(node) {
  const parents = [];
  let current = nodes.get(node.parent_id);
  while (current) { parents.unshift(current); current = nodes.get(current.parent_id); }
  return parents;
}
function dateLabel(value) {
  if (!value) return 'Date not specified';
  const date = new Date(`${value.slice(0, 10)}T12:00:00Z`);
  return Number.isNaN(date.valueOf()) ? value : new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }).format(date);
}

function renderHierarchy() {
  const query = ui.search.value.trim().toLocaleLowerCase();
  const kind = ui.filter.value;
  const filtering = Boolean(query || kind !== 'all');
  const openIds = new Set([...ui.hierarchy.querySelectorAll('details[open]')].map((detail) => detail.dataset.branchId));
  const matching = new Set(catalog.nodes.filter((node) =>
    (kind === 'all' || node.kind === kind) && (!query || [node.name, node.summary, ...node.tags].join(' ').toLocaleLowerCase().includes(query))
  ).map((node) => node.id));
  const visible = new Set(matching);
  for (const id of matching) for (const parent of ancestorNodes(nodes.get(id))) visible.add(parent.id);
  ui.clear.hidden = !filtering;
  ui.results.textContent = `${matching.size} ${matching.size === 1 ? 'match' : 'matches'}${filtering ? ' in this catalog' : ' across the map'}.`;

  function build(node, depth = 0) {
    if (!visible.has(node.id)) return null;
    const item = element('li');
    const children = (childNodes.get(node.id) || []).filter((child) => visible.has(child.id));
    if (children.length) {
      const detail = element('details');
      detail.dataset.branchId = node.id;
      detail.open = filtering || openIds.has(node.id) || (!selectedId && depth <= 1);
      const summary = element('summary');
      const size = element('span', 'branch-size', children.length);
      size.setAttribute('aria-label', `${children.length} child ${children.length === 1 ? 'branch' : 'branches'}`);
      summary.append(element('span', '', node.name), size);
      detail.append(summary);
      const list = element('ul');
      if (matching.has(node.id)) {
        const overview = element('li');
        const button = goButton(node, 'node-button group-overview', `About ${node.name}`, false);
        button.setAttribute('aria-pressed', String(selectedId === node.id));
        overview.append(button);
        list.append(overview);
      }
      for (const child of children) { const branch = build(child, depth + 1); if (branch) list.append(branch); }
      detail.append(list);
      item.append(detail);
    } else {
      const button = goButton(node, 'node-button', node.name, false);
      button.setAttribute('aria-pressed', String(selectedId === node.id));
      item.append(button);
    }
    return item;
  }
  const list = element('ul');
  for (const root of catalog.nodes.filter((node) => node.parent_id === null)) {
    const item = build(root);
    if (item) list.append(item);
  }
  ui.hierarchy.replaceChildren(list.children.length ? list : element('p', 'empty-hierarchy', 'No branches match yet. Try a shorter phrase or show everything.'));
}

function detailSection(title, count, note) {
  const section = element('section', 'detail-section');
  const heading = element('h4', '', title);
  if (count !== undefined) heading.append(element('span', 'section-count', count));
  section.append(heading);
  if (note) section.append(element('p', 'detail-note', note));
  return section;
}

function renderDetail(node) {
  const content = document.createDocumentFragment();
  const breadcrumb = element('nav', 'detail-breadcrumb');
  breadcrumb.setAttribute('aria-label', 'Selected node location');
  const parents = ancestorNodes(node);
  for (const parent of parents) {
    breadcrumb.append(goButton(parent, 'breadcrumb-button'));
    const separator = element('span', '', '/');
    separator.setAttribute('aria-hidden', 'true');
    breadcrumb.append(separator);
  }
  const current = element('span', '', node.name);
  current.setAttribute('aria-current', 'location');
  breadcrumb.append(current);
  content.append(breadcrumb);
  const overline = element('div', 'detail-overline');
  overline.append(element('span', 'detail-kind', node.kind), element('span', 'detail-status', words(node.status)));
  content.append(overline);
  const title = element('h3', 'node-title', node.name);
  title.id = 'selected-node-title';
  title.tabIndex = -1;
  content.append(title, element('p', 'detail-summary', node.summary));
  const tags = element('ul', 'tag-list');
  tags.setAttribute('aria-label', 'Topics');
  for (const tag of node.tags) tags.append(element('li', '', words(tag)));
  if (tags.children.length) content.append(tags);
  const toolbar = element('div', 'detail-toolbar');
  const add = element('button', 'add-button');
  add.id = 'toggle-working-set';
  add.type = 'button';
  updateAddButton(add, node);
  add.addEventListener('click', () => toggleWorkingNode(node.id));
  toolbar.append(add, publicLink('View this record as JSON ↗', `/api/nodes/${encodeURIComponent(node.id)}`, 'detail-api-link'));
  content.append(toolbar);
  const next = element('aside', 'next-action');
  next.setAttribute('aria-label', 'Proposed next action');
  next.append(element('h4', '', 'A possible next step'), element('p', '', node.next_action));
  content.append(next);
  content.append(element('p', 'detail-note', `Evidence status: ${words(node.evidence_status)}. This label describes the reviewed record, not a new verification of the project.`));

  const children = childNodes.get(node.id) || [];
  if (children.length) {
    const section = detailSection('Branches from here', children.length);
    const list = element('ul', 'detail-list child-list');
    for (const child of children) { const item = element('li'); item.append(goButton(child, '', child.name)); list.append(item); }
    section.append(list); content.append(section);
  }
  const relations = catalog.relations.filter((relation) => relation.from_id === node.id || relation.to_id === node.id);
  const section = detailSection('Connections with context', relations.length, 'Direction, type, and scope matter. A related project does not automatically supply evidence.');
  if (!relations.length) section.append(element('p', 'detail-note', 'No scoped connection is recorded for this node yet.'));
  const relationList = element('ul', 'detail-list');
  for (const relation of relations) {
    const item = element('li', 'relation-row');
    const line = element('div', 'relation-top');
    const outgoing = relation.from_id === node.id;
    const other = nodes.get(outgoing ? relation.to_id : relation.from_id);
    const thisNode = element('span', 'relation-direction', 'This node');
    const type = element('span', 'relation-type', words(relation.type));
    const link = goButton(other, 'relation-link');
    if (outgoing) line.append(thisNode, type, link); else line.append(link, type, thisNode);
    if (relation.status === 'proposal') line.append(element('span', 'proposal-label', 'proposed connection'));
    item.append(line, element('p', '', relation.scope));
    item.append(element('p', '', `${words(relation.status)} · ${relation.source_ids.map((id) => sources.get(id)?.title || id).join('; ')}`));
    relationList.append(item);
  }
  section.append(relationList); content.append(section);

  const capabilities = catalog.capabilities.filter((capability) => capability.node_id === node.id);
  if (capabilities.length) {
    const section = detailSection('Capabilities & interfaces', capabilities.length, 'These records describe an interface. Viewing one does not invoke its system.');
    const list = element('ul', 'detail-list');
    for (const capability of capabilities) {
      const card = element('li', 'capability-card');
      const heading = element('div', 'capability-heading');
      heading.append(element('strong', '', capability.name), element('span', 'capability-status', words(capability.status)));
      card.append(heading);
      const description = element('dl');
      for (const [label, value] of [['Transport', words(capability.transport)], ['Interface', capability.invocation], ['Input', capability.input], ['Output', capability.output]]) {
        const detail = element('dd');
        if (label === 'Interface') detail.append(element('code', '', value)); else detail.textContent = value;
        description.append(element('dt', '', label), detail);
      }
      card.append(description);
      if (capability.limitations.length) {
        const limitations = element('ul', 'capability-limits');
        limitations.setAttribute('aria-label', 'Capability limitations');
        for (const limitation of capability.limitations) limitations.append(element('li', '', limitation));
        card.append(limitations);
      }
      list.append(card);
    }
    section.append(list); content.append(section);
  }

  const sourceIds = new Set([...node.source_ids, ...relations.flatMap((relation) => relation.source_ids), ...capabilities.flatMap((capability) => capability.source_ids)]);
  const sourceSection = detailSection('Follow the sources', sourceIds.size, 'Sources cited by this node, its connections, and its capabilities. Owner-held items have a summary here; their full documents are not served.');
  const sourceList = element('ul', 'detail-list');
  for (const id of sourceIds) {
    const source = sources.get(id);
    if (!source) continue;
    const card = element('li', 'source-card');
    const heading = element('span', 'source-title');
    const url = validPublicUrl(source);
    if (url) heading.append(publicLink(`${source.title} ↗`, url)); else heading.textContent = source.title;
    const meta = element('p', 'source-meta');
    meta.append(element('span', 'source-access', source.access === 'owner-held' ? 'Owner-held · summary only' : 'Public source'));
    meta.append(document.createTextNode(`${words(source.evidence_kind)} · ${dateLabel(source.source_date)}`));
    card.append(heading, meta, element('p', '', source.scope));
    sourceList.append(card);
  }
  sourceSection.append(sourceList); content.append(sourceSection);
  ui.detail.replaceChildren(content);
  ui.detail.setAttribute('aria-labelledby', 'selected-node-title');
  ui.detail.removeAttribute('aria-label');
}

function selectNode(id, { focus = false, scroll = false, updateHash = true, speak = true } = {}) {
  const node = nodes.get(id);
  if (!node) return false;
  selectedId = id;
  renderDetail(node);
  for (const button of ui.hierarchy.querySelectorAll('button[data-node-id]')) button.setAttribute('aria-pressed', String(button.dataset.nodeId === id));
  const parentIds = new Set(ancestorNodes(node).map((parent) => parent.id));
  parentIds.add(node.id);
  for (const branch of ui.hierarchy.querySelectorAll('details')) if (parentIds.has(branch.dataset.branchId)) branch.open = true;
  if (updateHash && location.hash !== `#node/${encodeURIComponent(id)}`) history.pushState(null, '', `#node/${encodeURIComponent(id)}`);
  if (focus) $('#selected-node-title').focus({ preventScroll: true });
  if (scroll) ui.detail.scrollIntoView({ block: 'start', behavior: 'auto' });
  if (speak && !focus) announce(`Showing ${node.name}. ${words(node.status)}. Details follow the project hierarchy.`);
  return true;
}

function updateAddButton(button, node) {
  const added = workingSet.has(node.id);
  button.textContent = added ? '✓ In working set · remove' : '+ Add to working set';
  button.setAttribute('aria-label', `${added ? 'Remove' : 'Add'} ${node.name} ${added ? 'from' : 'to'} working set`);
  button.setAttribute('aria-pressed', String(added));
}
function toggleWorkingNode(id) {
  const node = nodes.get(id);
  if (!node) return;
  const removed = workingSet.has(id);
  if (removed) workingSet.delete(id); else workingSet.add(id);
  renderWorkingSet();
  if (selectedId) updateAddButton($('#toggle-working-set'), nodes.get(selectedId));
  $('#download-status').textContent = '';
  announce(`${node.name} ${removed ? 'removed from' : 'added to'} working set. ${workingSet.size} selected.`);
}
function renderWorkingSet() {
  $('#set-count').textContent = workingSet.size;
  $('#working-total').textContent = `${workingSet.size} selected`;
  $('#working-empty').hidden = workingSet.size > 0;
  ui.download.disabled = workingSet.size === 0;
  const list = document.createDocumentFragment();
  for (const id of workingSet) {
    const node = nodes.get(id);
    const item = element('li');
    const text = element('div');
    text.append(goButton(node, 'working-node-button'), element('div', 'working-node-meta', `${words(node.kind)} · ${words(node.status)}`));
    const remove = element('button', 'remove-button', 'Remove');
    remove.type = 'button';
    remove.dataset.removeId = id;
    remove.setAttribute('aria-label', `Remove ${node.name} from working set`);
    remove.addEventListener('click', () => {
      const index = [...workingSet].indexOf(id);
      toggleWorkingNode(id);
      const remaining = ui.workingList.querySelectorAll('button.remove-button');
      if (remaining.length) remaining[Math.min(index, remaining.length - 1)].focus();
      else { $('#working-title').tabIndex = -1; $('#working-title').focus({ preventScroll: true }); }
    });
    item.append(text, remove); list.append(item);
  }
  ui.workingList.replaceChildren(list);
}

function renderTrails() {
  const grid = document.createDocumentFragment();
  catalog.trails.forEach((trail, index) => {
    const card = element('article', 'trail-card');
    const marker = element('div', 'trail-number');
    marker.append(element('span', '', String(index + 1).padStart(2, '0')));
    const ornament = element('span', 'trail-flower', ['✳', '✴', '✧'][index % 3]);
    ornament.setAttribute('aria-hidden', 'true');
    marker.append(ornament);
    card.append(marker, element('h3', '', trail.title), element('p', '', trail.summary));
    const stops = element('ol', 'trail-stops');
    stops.setAttribute('aria-label', `${trail.title} suggested sequence`);
    for (const id of trail.node_ids) { const item = element('li'); item.append(goButton(nodes.get(id), '')); stops.append(item); }
    card.append(stops);
    const next = element('p', '', `Next: ${trail.next_action}`);
    card.append(next);
    const footer = element('div', 'trail-footer');
    const button = element('button', '', 'Gather this trail ↗');
    button.type = 'button';
    button.dataset.trailId = trail.id;
    button.setAttribute('aria-label', `Add the ${trail.title} trail to your working set`);
    button.addEventListener('click', () => {
      for (const id of trail.node_ids) workingSet.add(id);
      renderWorkingSet();
      if (selectedId) updateAddButton($('#toggle-working-set'), nodes.get(selectedId));
      announce(`${trail.title} added to working set. ${workingSet.size} selected. This trail is a proposal.`);
      $('#download-status').textContent = '';
    });
    footer.append(button, element('span', '', 'PROPOSED TRAIL'));
    card.append(footer); grid.append(card);
  });
  $('#trail-grid').replaceChildren(grid);
}

function downloadWorkingSet() {
  if (!workingSet.size) return;
  const selectedNodes = [...workingSet].map((id) => nodes.get(id));
  const selectedRelations = catalog.relations.filter((relation) => workingSet.has(relation.from_id) && workingSet.has(relation.to_id));
  const selectedCapabilities = catalog.capabilities.filter((capability) => workingSet.has(capability.node_id));
  const selectedSourceIds = new Set([...selectedNodes.flatMap((node) => node.source_ids), ...selectedRelations.flatMap((relation) => relation.source_ids), ...selectedCapabilities.flatMap((capability) => capability.source_ids)]);
  const proposal = {
    kind: 'proposed-working-set', schema_version: catalog.schema_version,
    created_at: new Date().toISOString(), catalog_version: catalog.catalog_version,
    catalog_reviewed_on: catalog.reviewed_on, status: 'proposal',
    scope: 'Explicit browser selection from the Knowledge Garden catalog. No project was invoked, changed, or independently verified.',
    navigation_note: 'Parent IDs are navigation references; ancestor records may be outside this selected set. Connections retain their recorded type and scope.',
    nodes: selectedNodes, relations: selectedRelations, capabilities: selectedCapabilities,
    sources: [...selectedSourceIds].map((id) => sources.get(id)),
    rules: catalog.rules,
  };
  const blob = new Blob([JSON.stringify(proposal, null, 2) + '\n'], { type: 'application/json' });
  const href = URL.createObjectURL(blob);
  const link = element('a');
  link.href = href;
  link.download = `knowledge-garden-working-set-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(href), 1000);
  $('#download-status').textContent = `Prepared a proposed working set with ${workingSet.size} ${workingSet.size === 1 ? 'node' : 'nodes'}.`;
}

function applyHash({ initial = false } = {}) {
  if (!catalog || !location.hash.startsWith('#node/')) return false;
  let id;
  try { id = decodeURIComponent(location.hash.slice(6)); } catch { id = ''; }
  if (selectNode(id, { updateHash: false, speak: !initial, focus: !initial, scroll: !initial })) return true;
  announce('This node link is not in the current catalog. Choose a branch to continue.');
  if (!initial) $('#results-count').textContent = 'That linked node is not in this catalog. The current selection remains available.';
  return false;
}

async function loadCatalog() {
  $('#load-error').hidden = true;
  $('#explorer-grid').setAttribute('aria-busy', 'true');
  try {
    const response = await fetch('/api/catalog', { headers: { Accept: 'application/json' }, cache: 'no-store' });
    if (!response.ok) throw new Error(`The catalog returned HTTP ${response.status}.`);
    const data = await response.json();
    if (!Array.isArray(data.nodes) || !Array.isArray(data.sources) || !Array.isArray(data.relations) || !Array.isArray(data.capabilities) || !Array.isArray(data.trails)) throw new Error('The catalog response is incomplete.');
    catalog = data;
    nodes = new Map(catalog.nodes.map((node) => [node.id, node]));
    sources = new Map(catalog.sources.map((source) => [source.id, source]));
    childNodes = new Map();
    for (const node of catalog.nodes) {
      if (!childNodes.has(node.parent_id)) childNodes.set(node.parent_id, []);
      childNodes.get(node.parent_id).push(node);
    }
    $('#project-count').textContent = catalog.nodes.filter((node) => node.kind === 'project').length;
    $('#connection-count').textContent = catalog.relations.length;
    $('#source-count').textContent = catalog.sources.length;
    $('#review-date').textContent = dateLabel(catalog.reviewed_on);
    $('#catalog-scope').textContent = catalog.scope;
    $('#catalog-version').textContent = `Catalog ${catalog.catalog_version} · Schema ${catalog.schema_version} · Reviewed ${dateLabel(catalog.reviewed_on)}`;
    $('#catalog-rules').replaceChildren(...catalog.rules.map((rule) => element('li', '', rule)));
    renderHierarchy();
    renderTrails();
    renderWorkingSet();
    if (!applyHash({ initial: true })) {
      const first = nodes.get('knowledge-garden') || catalog.nodes.find((node) => node.kind === 'project') || catalog.nodes[0];
      if (first) selectNode(first.id, { updateHash: false, speak: false });
    }
    $('#surprise-button').disabled = false;
  } catch (error) {
    $('#load-error-text').textContent = `The garden could not load. ${error.message} Start the local server and try again.`;
    $('#load-error').hidden = false;
    ui.results.textContent = 'Catalog unavailable.';
    ui.detail.replaceChildren(element('div', 'empty-detail', 'The project details will appear when the catalog is available.'));
  } finally { $('#explorer-grid').setAttribute('aria-busy', 'false'); }
}

ui.search.addEventListener('input', () => { if (catalog) renderHierarchy(); });
ui.filter.addEventListener('change', () => { if (catalog) renderHierarchy(); });
ui.clear.addEventListener('click', () => {
  ui.search.value = '';
  ui.filter.value = 'all';
  if (catalog) renderHierarchy();
  ui.search.focus();
});
$('#surprise-button').addEventListener('click', () => {
  const projects = catalog.nodes.filter((node) => node.kind === 'project' && node.id !== selectedId);
  if (!projects.length) return;
  const randomness = new Uint32Array(1);
  crypto.getRandomValues(randomness);
  const project = projects[randomness[0] % projects.length];
  selectNode(project.id, { focus: true, scroll: true });
});
ui.download.addEventListener('click', downloadWorkingSet);
$('#retry-button').addEventListener('click', loadCatalog);
window.addEventListener('hashchange', () => applyHash());
window.addEventListener('popstate', () => applyHash());
await loadCatalog();
