import { readFileSync, writeFileSync, mkdirSync, renameSync, rmSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { performance } from 'node:perf_hooks';
import { compileCatalog } from '../compiler.mjs';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const start = performance.now();
const catalog = JSON.parse(readFileSync(join(root, 'data/catalog.json'), 'utf8'));
const plan = compileCatalog(catalog);
const output = join(root, 'build/catalog.plan.json');
mkdirSync(dirname(output), { recursive: true });
const temporary = `${output}.${process.pid}.tmp`;
try {
  writeFileSync(temporary, JSON.stringify(plan) + '\n', { flag: 'wx' });
  renameSync(temporary, output);
} finally { rmSync(temporary, { force: true }); }
console.log(`Compiled ${catalog.nodes.length} nodes for catalog ${catalog.catalog_version} in ${(performance.now() - start).toFixed(2)} ms.`);
console.log(`Plan ${plan.plan_sha256}; ${Buffer.byteLength(JSON.stringify(plan))} JSON bytes. No source project was executed.`);
