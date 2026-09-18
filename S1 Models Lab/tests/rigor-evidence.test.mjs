import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runAudit } from '../audit.mjs';

const frozenUrl = new URL('../evidence/RIGOR_V1_SUMMARY.json', import.meta.url);
const closureUrl = new URL('../evidence/RIGOR_V1_CLOSURE_SUMMARY.json', import.meta.url);

test('frozen Rigor v1 predecessor remains immutable', async()=>{
  const summary=JSON.parse(await readFile(frozenUrl,'utf8'));
  assert.equal(summary.schema,'s1-rigor-v1-evidence/v1');
  assert.equal(summary.implementationRevision,'da979d2f9909e15019bae628a2c36ee56603dd79');
  assert.equal(summary.implementationCi.workflow,'S1 Models Check');
  assert.equal(summary.implementationCi.runId,35311853490);
  assert.equal(summary.implementationCi.conclusion,'success');
  assert.equal(summary.runtimeVersion,'v22.23.2');
  assert.deepEqual(summary.implementationTests,{total:89,passed:89,failed:0});
  assert.equal(summary.browserSmoke.conclusion,'success');
  assert.equal(summary.audit.sourceRevision,summary.implementationRevision);
  assert.equal(summary.audit.scientificValidation,false);
  assert.equal(Object.keys(summary.audit.checks).length,28);
  assert.equal(Object.values(summary.audit.checks).every(Boolean),true);
  assert.equal(summary.evidenceBoundaries.includes('SHARED_TRIG_PRIMITIVE != INDEPENDENT_TRANSCENDENTAL_ORACLE'),false);
});

test('Rigor v1 closure evidence extends rather than rewrites its predecessor', async()=>{
  const frozen=JSON.parse(await readFile(frozenUrl,'utf8'));
  const summary=JSON.parse(await readFile(closureUrl,'utf8'));

  assert.equal(summary.schema,'s1-rigor-v1-closure-evidence/v1');
  assert.equal(summary.predecessor.path,'S1 Models Lab/evidence/RIGOR_V1_SUMMARY.json');
  assert.equal(summary.predecessor.schema,frozen.schema);
  assert.equal(summary.predecessor.implementationRevision,frozen.implementationRevision);
  assert.deepEqual(summary.predecessor.implementationCi,frozen.implementationCi);
  assert.equal(summary.predecessor.immutable,true);

  assert.equal(summary.implementationRevision,'3040d235d8bfb55e3302effff5528ee71ecb5fad');
  assert.equal(summary.implementationCi.workflow,'S1 Models Check');
  assert.equal(summary.implementationCi.runId,35312567016);
  assert.equal(summary.implementationCi.conclusion,'success');
  assert.equal(summary.runtimeVersion,'v22.23.2');
  assert.deepEqual(summary.implementationTests,{total:92,passed:92,failed:0});
  assert.equal(summary.browserSmoke.conclusion,'success');

  assert.deepEqual(
    summary.audit,
    runAudit({sourceRevision:summary.implementationRevision,runtimeVersion:summary.runtimeVersion})
  );
  assert.equal(Object.keys(summary.audit.checks).length,28);
  assert.equal(Object.values(summary.audit.checks).every(Boolean),true);
  assert.equal(summary.audit.rigor.sweep.maxDepth,8);
  assert.equal(summary.audit.rigor.sweep.pathCount,2_015_539);
  assert.equal(summary.audit.rigor.samePlane.moveCount,1_000_000);
  assert.equal(summary.audit.rigor.mixedInverse.moveCount,600_000);
  assert.equal(summary.audit.carrierV1.version,"S'1-Carrier/Ops v1");
  assert.equal(summary.audit.carrierV1.closed,true);

  for(const boundary of [
    'SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION',
    'FINITE_EXHAUSTIVE_SWEEP != UNBOUNDED_PROOF',
    'FLOATING_POINT_RESIDUAL != MATHEMATICAL_COUNTEREXAMPLE',
    'PROJECTION_CONDITIONING != OBJECT_PROPERTY',
    'HASH_EQUALITY != PAYLOAD_EQUALITY',
    'OPERATOR_RESULT != SCIENTIFIC_EVIDENCE',
    'SHARED_TRIG_PRIMITIVE != INDEPENDENT_TRANSCENDENTAL_ORACLE',
    'Hodge and P-vs-NP remain open'
  ]) assert.ok(summary.evidenceBoundaries.includes(boundary));

  assert.equal(summary.provenance.scientificPromotion,false);
});
