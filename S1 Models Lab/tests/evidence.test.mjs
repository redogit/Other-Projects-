import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const summaryUrl = new URL('../evidence/EXPERIMENT_0_SUMMARY.json', import.meta.url);

test('frozen Experiment 0 summary pins the verified implementation without scientific promotion', async () => {
  const summary = JSON.parse(await readFile(summaryUrl, 'utf8'));
  assert.equal(summary.schema, 's1-experiment-0-evidence/v0');
  assert.match(summary.implementationRevision, /^[0-9a-f]{40}$/);
  assert.equal(summary.implementationRevision, '4c5b3d0e599c029cc05478eaa5119b00d096e3c4');
  assert.equal(summary.implementationCi.workflow, 'S1 Models Check');
  assert.equal(summary.implementationCi.runId, 35125214829);
  assert.equal(summary.implementationCi.conclusion, 'success');
  assert.deepEqual(summary.implementationTests, { total: 46, passed: 46, failed: 0 });
  assert.equal(summary.browserSmoke.conclusion, 'success');
  assert.deepEqual(summary.browserSmoke.checks, ['boot','move','save','replay','shell-reframe','observer','reframe','clear']);
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
    'FEATURE_AT_ONE_MESH != CONTINUUM_INVARIANT',
    'functional browser smoke != rendered usability or assistive-technology validation'
  ]) assert.ok(summary.evidenceBoundaries.includes(required));
});
