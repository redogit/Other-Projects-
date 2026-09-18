import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const summaryUrl = new URL('../evidence/RIGOR_V1_SUMMARY.json', import.meta.url);

test('frozen Rigor v1 summary pins exact implementation evidence without scientific promotion', async()=>{
  const summary=JSON.parse(await readFile(summaryUrl,'utf8'));
  assert.equal(summary.schema,'s1-rigor-v1-evidence/v1');
  assert.equal(summary.implementationRevision,'da979d2f9909e15019bae628a2c36ee56603dd79');
  assert.equal(summary.implementationCi.workflow,'S1 Models Check');
  assert.equal(summary.implementationCi.runId,35311853490);
  assert.equal(summary.implementationCi.conclusion,'success');
  assert.equal(summary.runtimeVersion,'v22.23.2');
  assert.deepEqual(summary.implementationTests,{total:89,passed:89,failed:0});
  assert.equal(summary.browserSmoke.conclusion,'success');

  assert.equal(summary.audit.schema,'s1-models-audit/v1');
  assert.equal(summary.audit.scientificValidation,false);
  assert.equal(Object.keys(summary.audit.checks).length,28);
  assert.equal(Object.values(summary.audit.checks).every(Boolean),true);

  assert.equal(summary.audit.rigor.sweep.maxDepth,8);
  assert.equal(summary.audit.rigor.sweep.pathCount,2_015_539);
  assert.equal(summary.audit.rigor.sweep.maxOrthogonalityResidual,1.3322676295501878e-15);
  assert.equal(summary.audit.rigor.sweep.maxDeterminantResidual,1.1102230246251565e-15);
  assert.equal(summary.audit.rigor.sweep.errorBudget,8.526512829121929e-14);

  assert.equal(summary.audit.rigor.samePlane.moveCount,1_000_000);
  assert.equal(summary.audit.rigor.samePlane.maxAbsDelta,2.992239789278983e-11);
  assert.equal(summary.audit.rigor.samePlane.normResidual,6.014888587202449e-11);
  assert.ok(summary.audit.rigor.samePlane.maxAbsDelta<=summary.audit.rigor.samePlane.errorBudget);

  assert.equal(summary.audit.rigor.mixedInverse.moveCount,600_000);
  assert.equal(summary.audit.rigor.mixedInverse.maxAbsDelta,8.969269771341715e-12);
  assert.equal(summary.audit.rigor.mixedInverse.normResidual,1.7935652962819404e-11);
  assert.ok(summary.audit.rigor.mixedInverse.maxAbsDelta<=summary.audit.rigor.mixedInverse.errorBudget);

  assert.equal(summary.audit.rigor.observer.stressed.denominator,0.10000090000000006);
  assert.equal(summary.audit.rigor.observer.stressed.localScaleSensitivityToW,99.99810002609955);
  assert.equal(summary.audit.rigor.observer.clamped.informationLoss,true);
  assert.equal(summary.audit.carrierV1.version,"S'1-Carrier/Ops v1");
  assert.equal(summary.audit.carrierV1.closed,true);

  for(const boundary of [
    'SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION',
    'FINITE_EXHAUSTIVE_SWEEP != UNBOUNDED_PROOF',
    'FLOATING_POINT_RESIDUAL != MATHEMATICAL_COUNTEREXAMPLE',
    'PROJECTION_CONDITIONING != OBJECT_PROPERTY',
    'HASH_EQUALITY != PAYLOAD_EQUALITY',
    'OPERATOR_RESULT != SCIENTIFIC_EVIDENCE',
    'Hodge and P-vs-NP remain open'
  ]) assert.ok(summary.evidenceBoundaries.includes(boundary));
});
