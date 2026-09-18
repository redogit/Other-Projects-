import test from 'node:test';
import assert from 'node:assert/strict';
import {runAudit} from '../audit.mjs';

test('audit reports deterministic bounded software and rigor evidence',()=>{
  const a=runAudit({sourceRevision:'deadbeef',runtimeVersion:'test'});
  const b=runAudit({sourceRevision:'deadbeef',runtimeVersion:'test'});
  assert.deepEqual(a,b);
  assert.equal(a.schema,'s1-models-audit/v1');
  assert.equal(a.scientificValidation,false);
  for (const key of [
    'mirrorUnchanged','replayEqualsDirect','previousStepExact','sameObserver','allTesseractCells',
    'graphRepeat','graphNewBranch','graphVariation','graphRebuilt','corruptSaveRejected',
    'duplicateImportCoalesced','unknownAuthorityRejected','recordMinimumExplicit','repeatByReplayIdentity',
    'operatorJoin','operatorDifferenceDirectional','operatorInteractionOrdered','operatorQuotient',
    'rigorDepth8Complete','rigorMatrixWithinBudget','rigorLongHorizonWithinBudget',
    'observerConditionBounded','observerClampInformationLoss','replayDigestCollisionRejected',
    'carrierV1Closure','carrierV1JoinNormalized','carrierV1Directional','carrierV1Quotient'
  ]) assert.equal(a.checks[key],true,`${key} must pass`);

  assert.ok(a.metrics.s3MaxRadiusResidual<1e-10);
  assert.equal(a.rigor.sweep.maxDepth,8);
  assert.equal(a.rigor.sweep.pathCount,2_015_539);
  assert.ok(a.rigor.sweep.maxOrthogonalityResidual<=a.rigor.sweep.errorBudget);
  assert.ok(a.rigor.sweep.maxDeterminantResidual<=a.rigor.sweep.errorBudget);
  assert.ok(a.rigor.samePlane.maxAbsDelta<=a.rigor.samePlane.errorBudget);
  assert.ok(a.rigor.mixedInverse.maxAbsDelta<=a.rigor.mixedInverse.errorBudget);
  assert.ok(a.rigor.observer.stressed.denominator>0.1);
  assert.equal(a.rigor.observer.clamped.informationLoss,true);
  assert.equal(a.carrierV1.version,"S'1-Carrier/Ops v1");
  assert.equal(a.carrierV1.closed,true);

  for(const boundary of [
    'SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION',
    'FINITE_EXHAUSTIVE_SWEEP != UNBOUNDED_PROOF',
    'FLOATING_POINT_RESIDUAL != MATHEMATICAL_COUNTEREXAMPLE',
    'PROJECTION_CONDITIONING != OBJECT_PROPERTY',
    'HASH_EQUALITY != PAYLOAD_EQUALITY',
    'OPERATOR_RESULT != SCIENTIFIC_EVIDENCE'
  ]) assert.ok(a.claimBoundaries.includes(boundary));
});
