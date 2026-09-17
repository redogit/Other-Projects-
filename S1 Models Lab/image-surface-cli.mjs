import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { analyzeImageSurface } from './image-surface.mjs';

const inputPath = process.argv[2];
if (!inputPath) {
  process.stderr.write('usage: node image-surface-cli.mjs <calibration.json>\n');
  process.exit(2);
}

try {
  const raw = await readFile(resolve(inputPath));
  if (raw.length > 2_000_000) throw new RangeError('calibration input exceeds 2 MB');
  const payload = JSON.parse(raw.toString('utf8'));
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) throw new TypeError('calibration input must be an object');
  const allowed = new Set(['source', 'actions', 'observer']);
  for (const key of Object.keys(payload)) if (!allowed.has(key)) throw new RangeError(`unsupported calibration field: ${key}`);
  const result = analyzeImageSurface(payload.source, payload.actions ?? [], payload.observer);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
} catch (error) {
  process.stderr.write(`Invalid image-surface calibration: ${error.message}\n`);
  process.exit(2);
}
