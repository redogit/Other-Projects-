import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { performance } from 'node:perf_hooks';
import { compileCatalog, createExecutor } from '../compiler.mjs';

const catalog = JSON.parse(readFileSync(new URL('../data/catalog.json', import.meta.url), 'utf8'));
const freeze = value => { if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); } return value; };
const baselineInitStart = performance.now();
freeze(catalog);
const nodes = new Map(catalog.nodes.map(node => [node.id, node]));
const sources = new Map(catalog.sources.map(source => [source.id, source]));
const baseline = {
  detail(id) {
    const node = nodes.get(id);
    return { node, children: catalog.nodes.filter(n => n.parent_id === id),
      relations: catalog.relations.filter(e => e.from_id === id || e.to_id === id),
      capabilities: catalog.capabilities.filter(c => c.node_id === id),
      sources: node.source_ids.map(id => sources.get(id)) };
  },
  search(q) { return catalog.nodes.filter(node => [node.name, node.summary, ...node.tags].join('\n').toLowerCase().includes(q.toLowerCase())); },
};
const baselineInitMs = performance.now() - baselineInitStart;
const compileStart = performance.now();
const plan = compileCatalog(catalog);
const compileMs = performance.now() - compileStart;
const buildStart = performance.now();
const build = spawnSync(process.execPath, [fileURLToPath(new URL('./build.mjs', import.meta.url))], { encoding: 'utf8' });
if (build.status !== 0) throw new Error(build.stderr || 'Plan build failed');
const buildCliMs = performance.now() - buildStart;
const readStart = performance.now();
const diskPlan = JSON.parse(readFileSync(new URL('../build/catalog.plan.json', import.meta.url), 'utf8'));
const planReadParseMs = performance.now() - readStart;
assert.deepEqual(diskPlan, plan);
if (typeof global.gc === 'function') global.gc();
const before = process.memoryUsage().heapUsed;
const createStart = performance.now();
const executor = createExecutor(catalog, diskPlan);
const createMs = performance.now() - createStart;
if (typeof global.gc === 'function') global.gc();
const active = process.memoryUsage().heapUsed;

const detailWork = catalog.nodes.map(n => ({ method: 'detail', arg: n.id }));
const searchWork = ['master', 'carrier', 'context', 'nothing-matches-this-query', 'R³', '.*', 'api', 'source', 'human', 'memory'].map(q => ({ method: 'search', arg: q }));
for (const work of [...detailWork, ...searchWork]) assert.deepEqual(executor[work.method](work.arg), baseline[work.method](work.arg));

let consumed = 0;
function time(run, workload, repetitions) {
  const begin = performance.now();
  for (let r = 0; r < repetitions; r++) for (const work of workload) {
    const value = run[work.method](work.arg);
    consumed += Array.isArray(value) ? value.length : value.children.length + value.relations.length;
  }
  return performance.now() - begin;
}
const median = a => [...a].sort((a, b) => a - b)[Math.floor(a.length / 2)];
const results = [];
for (const [name, workload] of [['node-detail', detailWork], ['literal-search', searchWork]]) {
  time(baseline, workload, 100); time(executor, workload, 100);
  const old = [], compiled = [];
  for (let trial = 0; trial < 7; trial++) {
    const order = trial % 2 ? [[executor, compiled], [baseline, old]] : [[baseline, old], [executor, compiled]];
    for (const [run, output] of order) output.push(time(run, workload, 1000));
  }
  const baselineMs = median(old), compiledMs = median(compiled);
  const queries = workload.length * 1000;
  const savingPerQuery = (baselineMs - compiledMs) / queries;
  results.push({ workload: name, distinct_queries: workload.length, queries_per_trial: queries,
    trials: 7, baseline_ms: old, compiled_ms: compiled, median_baseline_ms: baselineMs,
    median_compiled_ms: compiledMs, speed_ratio: baselineMs / compiledMs,
    estimated_extra_startup_amortization_queries: savingPerQuery > 0 ? Math.ceil(Math.max(0, buildCliMs + planReadParseMs + createMs - baselineInitMs) / savingPerQuery) : null });
}
executor.dispose();
if (typeof global.gc === 'function') global.gc();
const released = process.memoryUsage().heapUsed;
console.log(JSON.stringify({
  schema: 'knowledge-garden-query-benchmark/1', node: process.version, measured_at: new Date().toISOString(),
  catalog_version: catalog.catalog_version, catalog_sha256: plan.catalog_sha256, plan_sha256: plan.plan_sha256,
  catalog_json_bytes: Buffer.byteLength(JSON.stringify(catalog)), plan_json_bytes: Buffer.byteLength(JSON.stringify(plan)),
  isolated_in_memory_compile_ms: compileMs, node_build_process_ms: buildCliMs, plan_read_parse_ms: planReadParseMs, executor_load_ms: createMs, baseline_index_initialization_ms: baselineInitMs,
  heap_observation: {gc_requested: typeof global.gc === 'function', before_executor_bytes: before, after_executor_bytes: active, after_release_and_trials_bytes: released,
    interpretation: 'Noisy process heap observations. Catalog and compiled plan remain held by this benchmark; later values also include trial/JIT activity. These are not browser clearing measurements.'},
  output_equality_checks: detailWork.length + searchWork.length, consumed, results,
  scope: 'One local environment and shipped 50-node catalog. Compares old scan-based detail and literal-search expressions over a frozen catalog with precompiled indices. Records Node startup, compilation and plan serialization/write as one build-process total, with plan read/parse and executor initialization separately; npm wrapper and common server startup are excluded. Query timings exclude HTTP and response JSON serialization, browser and source-project execution. This is query-plan compilation, not native machine-code compilation. No universal optimality claim.'
}, null, 2));
