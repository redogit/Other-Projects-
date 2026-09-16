import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const summaryUrl = new URL('../evidence/EXPERIMENT_0_SUMMARY.json', import.meta.url);

test('frozen Experiment 0 summary pins the verified implementation without scientific promotion', async () => {
  const summary = JSON.parse(await readFile(summaryUrl, 'utf8'));
  assert.equal(summary.schema, 's1-experiment-0-evidence/v0');
  assert.match(summary.implementationRevision, /^[0-9a-f]{40}$/);
  assert.equal(summary.implementationRevision, '66f68a98e532488bddf44c8de9a0878e760ec7a2');
  assert.equal(summary.implementationCi.runId, 35095361999);
  assert.equal(summary.implementationCi.conclusion, 'success');
  assert.deepEqual(summary.implementationTests, { total: 48, passed: 48, failed: 0 });
  assert.equal(summary.audit.scientificValidation, false);
  assert.equal(Object.values(summary.audit.checks).length, 18);
  assert.equal(Object.values(summary.audit.checks).every(Boolean), true);
  assert.equal(summary.boundedSweeps.legalMovePathsThroughDepth3IncludingEmpty, 259);
  assert.equal(summary.boundedSweeps.operatorOrderedPairs, 64);
  assert.equal(summary.boundedSweeps.observerFrameQuotientCases, 28);
  for (const required of [
    'SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION',
    'real 4D != complex dimension 4',
    'OBSERVATIONAL_REPAIR != OBJECT_REPAIR',
    'FEATURE_AT_ONE_MESH != CONTINUUM_INVARIANT'
  ]) assert.ok(summary.evidenceBoundaries.includes(required));
});
