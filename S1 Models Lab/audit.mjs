import { writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { createState, createMirror, applyMove, compareStates, materializeTrajectory } from './core.mjs';
import { sampleS3, sampleTesseractBoundary } from './geometry.mjs';
import { DEFAULT_OBSERVER, normalizeObserver, projectPair } from './observer.mjs';
import { makeExperience, replayExperience, classifyExperience, appendExperience, rebuildExperienceGraph } from './experience.mjs';
import { S1_NEUTRAL, makeObserverFrame, joinModels, differenceModels, interactModels, quotientModel } from './operators.mjs';
import { MemoryStore, LocalExperienceStore } from './storage.mjs';

function makeFixture(geometry, actions, relations={familyId:'audit',parentId:null}) {
  return makeExperience({
    initialState: geometry.id,
    mirrorId: `mirror:${geometry.id}`,
    shell: geometry.id,
    actions,
    observer: DEFAULT_OBSERVER,
    observerField: {version:'s1-observer-field/v0',taskVersion:'s1-observer-task/v0',densityId:'audit',calibrations:[]},
    checkpoints: [],
    comparisons: {obligation:'live-vs-mirror',againstMirror:{equal:actions.length===0,maxAbsDelta:actions.length===0?0:0.01},againstPrevious:{equal:actions.length===0,maxAbsDelta:actions.length===0?0:0.01}},
    relations: {...relations, relatedIds: relations.relatedIds ?? []},
    provenance: {source:'audit-fixture'}
  });
}

export function runAudit({ sourceRevision, runtimeVersion = process.version }) {
  if (typeof sourceRevision !== 'string' || !sourceRevision) throw new TypeError('sourceRevision is required');
  const s3 = sampleS3({etaSteps:4,xi1Steps:6,xi2Steps:6,radius:1.6});
  const tess = sampleTesseractBoundary({steps:3,halfExtent:1.4});
  const registry = new Map([[s3.id,s3],[tess.id,tess]]);
  const origin = createState(s3.points4); const mirror = createMirror(origin); const mirrorBefore = JSON.stringify(mirror);
  const actions=[{plane:'xw',degrees:1},{plane:'yw',degrees:-1},{plane:'zw',degrees:1}];
  let direct=origin; for(const move of actions) direct=applyMove(direct,move);
  const record=makeFixture(s3,actions);
  const replayed=replayExperience(record,registry);
  const auditObserver=normalizeObserver({...DEFAULT_OBSERVER,yaw:.2,pitch:-.1});
  const pair=projectPair(direct,mirror,auditObserver);
  const trajectory=materializeTrajectory(s3.points4,actions);
  let expectedPrevious=origin; for(const move of actions.slice(0,-1)) expectedPrevious=applyMove(expectedPrevious,move);
  let maxRadiusResidual=0; for(const p of s3.points4){const norm=Math.sqrt(p.reduce((s,x)=>s+x*x,0));maxRadiusResidual=Math.max(maxRadiusResidual,Math.abs(norm-1.6));}
  const cells=[...new Set(tess.groups.map(g=>g.cell))].sort();

  let graph=Object.freeze({events:Object.freeze([]),invariants:Object.freeze([])});
  const root=makeFixture(s3,[],{familyId:'audit',parentId:null});
  const rootClass=classifyExperience(root,graph); graph=appendExperience(graph,root,rootClass);
  const child=makeFixture(s3,[{plane:'xw',degrees:1}],{familyId:'audit',parentId:root.id});
  const childClass=classifyExperience(child,graph); graph=appendExperience(graph,child,childClass);
  const sibling=makeFixture(s3,[{plane:'yw',degrees:1}],{familyId:'audit',parentId:root.id});
  const siblingClass=classifyExperience(sibling,graph);
  const repeatClass=classifyExperience(root,graph);
  const rebuiltGraph=rebuildExperienceGraph([child,root]);

  const storage = new LocalExperienceStore(new MemoryStore()); storage.save(record); const before=storage.exportJson();
  let corruptSaveRejected=false; try { storage.importJson('{bad'); } catch { corruptSaveRejected=storage.exportJson()===before; }
  const duplicatePayload=JSON.stringify([{event:record,occurrences:2},{event:record,occurrences:3}]);
  const duplicateStore=new LocalExperienceStore(new MemoryStore()); duplicateStore.importJson(duplicatePayload);
  const duplicateRows=duplicateStore.list();
  const duplicateImportCoalesced=duplicateRows.length===1 && duplicateRows[0].occurrences===5;
  let unknownAuthorityRejected=false; try { replayExperience({...record,hiddenAuthority:'smuggled'},registry); } catch { unknownAuthorityRejected=true; }

  const operatorPeer=makeFixture(s3,[{plane:'yw',degrees:1}]);
  const joined=joinModels(record,operatorPeer);
  const diffAB=differenceModels(record,operatorPeer);
  const diffBA=differenceModels(operatorPeer,record);
  const interactionAB=interactModels(record,operatorPeer);
  const interactionBA=interactModels(operatorPeer,record);
  const frame=makeObserverFrame({...DEFAULT_OBSERVER,yaw:.15});
  const quotient=quotientModel(record,frame,registry);
  const neutralJoin=joinModels(S1_NEUTRAL,record);
  const secondOccurrence=makeExperience({
    initialState:record.initialState, mirrorId:record.mirrorId, shell:record.shell, actions:record.actions,
    observer:record.observer, observerField:record.observerField, checkpoints:record.checkpoints,
    comparisons:record.comparisons, relations:{...record.relations,relatedIds:['context-only']},
    provenance:{source:'audit-second-occurrence'}
  });
  const repeatByReplayIdentity=classifyExperience(secondOccurrence,{events:[{event:record,classification:'new-branch'}],invariants:[]})==='repeat';

  return Object.freeze({
    schema:'s1-experiment-0-audit/v0',
    sourceRevision,
    runtimeVersion,
    scientificValidation:false,
    claimCeiling:'bounded deterministic software verification only',
    checks:Object.freeze({
      mirrorUnchanged: JSON.stringify(mirror) === mirrorBefore,
      replayEqualsDirect: compareStates(replayed,direct).equal,
      previousStepExact: compareStates(trajectory.previous,expectedPrevious).equal,
      sameObserver: pair.observer === auditObserver && pair.live.length === pair.mirror.length,
      allTesseractCells: JSON.stringify(cells) === JSON.stringify(['w+','w-','x+','x-','y+','y-','z+','z-']),
      graphRepeat: repeatClass === 'repeat',
      graphNewBranch: rootClass === 'new-branch' && childClass === 'new-branch',
      graphVariation: siblingClass === 'variation',
      graphRebuilt: rebuiltGraph.events.length === 2 && rebuiltGraph.events.some(entry => entry.event.id === root.id) && rebuiltGraph.events.some(entry => entry.event.id === child.id),
      corruptSaveRejected,
      duplicateImportCoalesced,
      unknownAuthorityRejected,
      recordMinimumExplicit: Array.isArray(record.checkpoints) && !!record.comparisons.againstMirror && !!record.comparisons.againstPrevious && Array.isArray(record.relations.relatedIds),
      repeatByReplayIdentity,
      operatorJoin: joined.memberIds.length === 2 && joined.chronology[0] === record.id && neutralJoin.memberIds.length === 1,
      operatorDifferenceDirectional: diffAB.id !== diffBA.id && diffAB.sourceIds[0] === record.id,
      operatorInteractionOrdered: interactionAB.id !== interactionBA.id && interactionAB.sourceIds[0] === record.id,
      operatorQuotient: quotient.sourceId === record.id && quotient.frameId === frame.id && quotient.projected.length === s3.points4.length
    }),
    metrics:Object.freeze({s3MaxRadiusResidual:maxRadiusResidual,actionCount:actions.length,pointCount:s3.points4.length})
  });
}

async function main() {
  const args=process.argv.slice(2); let sourceRevision=null,out=null;
  for(let i=0;i<args.length;i++){if(args[i]==='--source-revision')sourceRevision=args[++i];else if(args[i]==='--out')out=args[++i];else throw new RangeError(`unknown argument: ${args[i]}`);}
  const result=runAudit({sourceRevision}); const text=JSON.stringify(result,null,2)+'\n';
  if(out) await writeFile(out,text,'utf8'); else process.stdout.write(text);
}
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) main().catch(error=>{console.error(error.stack||error.message);process.exitCode=1;});
