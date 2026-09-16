import test from 'node:test';
import assert from 'node:assert/strict';
import {runAudit} from '../audit.mjs';

test('audit reports deterministic bounded software evidence',()=>{
  const a=runAudit({sourceRevision:'deadbeef',runtimeVersion:'test'});
  const b=runAudit({sourceRevision:'deadbeef',runtimeVersion:'test'});
  assert.deepEqual(a,b);
  assert.equal(a.scientificValidation,false);
  for (const key of [
    'mirrorUnchanged','replayEqualsDirect','previousStepExact','sameObserver','allTesseractCells',
    'graphRepeat','graphNewBranch','graphVariation','graphRebuilt','corruptSaveRejected',
    'duplicateImportCoalesced','unknownAuthorityRejected'
  ]) assert.equal(a.checks[key],true,`${key} must pass`);
  assert.ok(a.metrics.s3MaxRadiusResidual<1e-10);
});
