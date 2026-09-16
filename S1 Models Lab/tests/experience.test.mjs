import test from 'node:test'; import assert from 'node:assert/strict'; import {sampleS3} from '../geometry.mjs'; import {createState,applyMove,compareStates} from '../core.mjs'; import {DEFAULT_OBSERVER} from '../observer.mjs'; import {canonicalJson,makeExperience,replayExperience,reframeExperience,classifyExperience,appendExperience} from '../experience.mjs';
const geom=sampleS3({etaSteps:2,xi1Steps:3,xi2Steps:3,radius:1}); const registry=new Map([[geom.id,geom]]);
function input(actions=[{plane:'xw',degrees:1}],relations={familyId:'f0'}){const same=actions.length===0;return {initialState:geom.id,mirrorId:'mirror:'+geom.id,shell:'s3-sample',actions,observer:DEFAULT_OBSERVER,observerField:{version:'s1-observer-field/v0',taskVersion:'s1-observer-task/v0',densityId:'fixture',calibrations:[]},checkpoints:[],comparisons:{obligation:'live-vs-mirror',againstMirror:{equal:same,maxAbsDelta:same?0:0.01},againstPrevious:{equal:same,maxAbsDelta:same?0:0.01}},relations,provenance:{source:'unit'}};}
test('canonical ID ignores object key insertion order and changes with action',()=>{const a=makeExperience(input());const x=input();const b=makeExperience({provenance:x.provenance,relations:x.relations,comparisons:x.comparisons,observerField:x.observerField,observer:x.observer,actions:x.actions,shell:x.shell,mirrorId:x.mirrorId,initialState:x.initialState});assert.equal(a.id,b.id);assert.notEqual(a.id,makeExperience(input([{plane:'yw',degrees:1}])).id);assert.equal(canonicalJson(a),canonicalJson(b));});
test('replay equals direct application and corrupt records fail closed',()=>{const actions=[{plane:'xw',degrees:1},{plane:'yw',degrees:-1},{plane:'zw',degrees:1}];const r=makeExperience(input(actions));let direct=createState(geom.points4);for(const m of actions)direct=applyMove(direct,m);assert.equal(compareStates(replayExperience(r,registry),direct).equal,true);assert.throws(()=>replayExperience({...r,schema:'bad'},registry));assert.throws(()=>replayExperience({...r,initialState:'missing'},registry));});
test('reframe preserves source record byte identity',()=>{const r=makeExperience(input());const before=canonicalJson(r);const a=reframeExperience(r,{...DEFAULT_OBSERVER,yaw:.2},registry);const b=reframeExperience(r,{...DEFAULT_OBSERVER,pitch:.2},registry);assert.equal(canonicalJson(r),before);assert.equal(a.sourceId,r.id);assert.notDeepEqual(a.projected,b.projected);});
test('graph classifies repeat new branch variation counterexample and unresolved',()=>{let graph=Object.freeze({events:Object.freeze([]),invariants:Object.freeze([{id:'inv1',passed:true}])});const first=makeExperience(input([], {familyId:'f0',parentId:null}));assert.equal(classifyExperience(first,graph),'new-branch');graph=appendExperience(graph,first,'new-branch');assert.equal(classifyExperience(first,graph),'repeat');const variation=makeExperience(input([{plane:'xw',degrees:1}],{familyId:'f0',parentId:first.id}));assert.equal(classifyExperience(variation,graph),'new-branch');graph=appendExperience(graph,variation,'new-branch');const sibling=makeExperience(input([{plane:'yw',degrees:1}],{familyId:'f0',parentId:first.id}));assert.equal(classifyExperience(sibling,graph),'variation');const counter=makeExperience(input([{plane:'zw',degrees:1}],{familyId:'f0',testsInvariantId:'inv1',invariantResult:false}));assert.equal(classifyExperience(counter,graph),'counterexample');const u=makeExperience(input([{plane:'zw',degrees:-1}],{}));assert.equal(classifyExperience(u,graph),'unresolved');});

test('experience validation rejects unknown top-level authority fields',()=>{
  const r=makeExperience(input());
  assert.throws(()=>replayExperience({...r,hiddenAuthority:'smuggled'},registry));
});

test('longest prefix parent and graph rebuild preserve persisted relations', async()=>{
  const { findLongestPrefixParent, rebuildExperienceGraph } = await import('../experience.mjs');
  const root=makeExperience(input([],{familyId:'f0',parentId:null}));
  const one=makeExperience(input([{plane:'xw',degrees:1}],{familyId:'f0',parentId:root.id}));
  const twoActions=[{plane:'xw',degrees:1},{plane:'yw',degrees:1}];
  const graph=rebuildExperienceGraph([root,one]);
  assert.equal(graph.events.length,2);
  assert.equal(findLongestPrefixParent(graph,'f0',twoActions),one.id);
  assert.equal(findLongestPrefixParent(graph,'other',twoActions),null);
});

test('canonical JSON preserves literal prototype-like keys without prototype mutation',()=>{
  const value=JSON.parse('{"z":1,"__proto__":{"polluted":true}}');
  const text=canonicalJson(value);
  assert.match(text,/"__proto__"/);
  assert.equal(Object.prototype.polluted,undefined);
  assert.deepEqual(JSON.parse(text),value);
});

test('observer field runtime validation matches strict schema authority surface',()=>{
  const base=input();
  assert.throws(()=>makeExperience({...base,observerField:{...base.observerField,hiddenAuthority:true}}));
  assert.throws(()=>makeExperience({...base,observerField:{...base.observerField,calibrations:[{observerId:'x',calibration:0,extra:true}]}}));
});

test('saved experience exposes explicit checkpoints and both required comparison relations',()=>{
  const base=input([{plane:'xw',degrees:1}]);
  const record=makeExperience({
    ...base,
    checkpoints:[{actionIndex:0,label:'origin'},{actionIndex:1,label:'after-xw'}],
    comparisons:{
      obligation:'live-vs-mirror',
      againstMirror:{equal:false,maxAbsDelta:0.1},
      againstPrevious:{equal:false,maxAbsDelta:0.1}
    },
    relations:{familyId:'f0',parentId:null,relatedIds:[]}
  });
  assert.deepEqual(record.checkpoints,[{actionIndex:0,label:'origin'},{actionIndex:1,label:'after-xw'}]);
  assert.equal(record.comparisons.againstMirror.equal,false);
  assert.equal(record.comparisons.againstPrevious.equal,false);
  assert.deepEqual(record.relations.relatedIds,[]);
});

test('checkpoints are bounded by action chronology and comparison records are strict',()=>{
  const base=input([{plane:'xw',degrees:1}]);
  assert.throws(()=>makeExperience({...base,checkpoints:[{actionIndex:2}]}));
  assert.throws(()=>makeExperience({...base,checkpoints:[{actionIndex:1,extra:true}]}));
  assert.throws(()=>makeExperience({...base,comparisons:{obligation:'x',againstMirror:{equal:true,maxAbsDelta:0},againstPrevious:{equal:true,maxAbsDelta:0},hidden:true}}));
});

test('repeat classification uses replay identity rather than full record metadata identity',()=>{
  const first=makeExperience({...input([{plane:'xw',degrees:1}],{familyId:'f0',parentId:null,relatedIds:[]}),provenance:{source:'first'}});
  const sameReplay=makeExperience({...input([{plane:'xw',degrees:1}],{familyId:'f0',parentId:'different-parent',relatedIds:['different-parent']}),provenance:{source:'second'}});
  assert.notEqual(first.id,sameReplay.id);
  let graph=Object.freeze({events:Object.freeze([{event:first,classification:'new-branch'}]),invariants:Object.freeze([])});
  assert.equal(classifyExperience(sameReplay,graph),'repeat');
  assert.strictEqual(appendExperience(graph,sameReplay,'repeat'),graph);
});

test('family labels cannot create variation across different initial-state identities',()=>{
  const first=makeExperience(input([{plane:'xw',degrees:1}],{familyId:'f0',parentId:null,relatedIds:[]}));
  const graph=Object.freeze({events:Object.freeze([{event:first,classification:'new-branch'}]),invariants:Object.freeze([])});
  const other=makeExperience({...input([{plane:'yw',degrees:1}],{familyId:'f0',parentId:null,relatedIds:[]}),initialState:'different-origin',mirrorId:'mirror:different-origin'});
  assert.equal(classifyExperience(other,graph),'unresolved');
});
