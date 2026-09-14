export function fixture() {
  const node = (id, name, kind, parent_id, summary, tags = []) => ({
    id, name, kind, parent_id, summary, tags,
    status: 'source reviewed', evidence_status: 'bounded source record',
    source_ids: ['fixture-source'], next_action: 'Inspect the original source before extending this example.',
  });
  return {
    schema_version: '1.0.0', catalog_version: 'fixture.1', reviewed_on: '2026-09-13',
    title: 'Test Garden', scope: 'Synthetic test fixture; no owner records.',
    rules: ['Containment is navigation.'],
    nodes: [
      node('root', 'Fixture Garden', 'group', null, 'Synthetic hierarchy root.'),
      node('alpha', 'Alpha Project', 'project', 'root', 'A Literal [garden] study.', ['botany']),
      node('beta', 'Beta Project', 'project', 'root', 'A second study.', ['RUNTIME']),
      node('router', 'Router', 'component', 'alpha', 'A routing component.'),
    ],
    sources: [{ id: 'fixture-source', title: 'Synthetic owner-held source', source_date: null,
      reviewed_on: '2026-09-13', access: 'owner-held', url: null,
      evidence_kind: 'test fixture', scope: 'Synthetic records only.' }],
    relations: [{ id: 'alpha-beta', from_id: 'alpha', to_id: 'beta', type: 'related_to',
      scope: 'Proposed comparison of synthetic examples.', status: 'proposal', source_ids: ['fixture-source'] }],
    capabilities: [{ id: 'alpha-read', node_id: 'alpha', name: 'Read alpha', transport: 'local-http',
      status: 'implemented', invocation: 'GET /api/projects/alpha', input: 'Exact project ID.',
      output: 'Recorded node.', limitations: ['Read-only.'], source_ids: ['fixture-source'] }],
    trails: [{ id: 'fixture-trail', title: 'A synthetic trail', summary: 'Explore the test projects.',
      node_ids: ['alpha', 'beta'], next_action: 'Read the fixtures.', status: 'proposal' }],
  };
}
