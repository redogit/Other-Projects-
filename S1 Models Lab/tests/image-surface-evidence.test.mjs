import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = new URL('../', import.meta.url);
const cliUrl = new URL('image-surface-cli.mjs', root);
const calibrationUrl = new URL('image_surface_calibration.json', root);
const evidenceUrl = new URL('evidence/issue42_image_surface_result.json', root);

function path(url) { return fileURLToPath(url); }

test('committed issue 42 carrier is exact deterministic CLI output', async () => {
  assert.equal(existsSync(path(cliUrl)), true, 'image-surface-cli.mjs must exist');
  assert.equal(existsSync(path(calibrationUrl)), true, 'image_surface_calibration.json must exist');
  assert.equal(existsSync(path(evidenceUrl)), true, 'frozen issue-42 carrier must exist');

  const run = () => spawnSync(process.execPath, [path(cliUrl), path(calibrationUrl)], {
    cwd: path(root), encoding: 'utf8'
  });
  const one = run();
  const two = run();
  assert.equal(one.status, 0, one.stderr);
  assert.equal(two.status, 0, two.stderr);
  assert.equal(one.stdout, two.stdout);

  const frozen = await readFile(evidenceUrl, 'utf8');
  assert.equal(one.stdout, frozen);
  const result = JSON.parse(frozen);
  assert.equal(result.schema, 's1-image-surface-analysis/v0');
  assert.equal(result.authority, 'image-surface-observation-only');
  assert.equal(result.topology.changed, false);
  assert.ok(result.projection.live.maxEdgeScaleDeviation > 0);
  assert.ok(result.intrinsic.maxAreaRatioDeviation < 1e-10);
});
