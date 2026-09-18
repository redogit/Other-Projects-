import test from 'node:test';
import assert from 'node:assert/strict';
import { makeExperience, canonicalJson } from '../experience.mjs';
import { DEFAULT_OBSERVER } from '../observer.mjs';
import {
  CARRIER_VERSION,
  S1_CARRIER_NEUTRAL,
  experienceCarrier,
  observerFrameCarrier,
  joinCarriers,
  differenceCarriers,
  interactCarriers,
  quotientCarrier,
  validateCarrier
} from '../carrier-v1.mjs';

function record(actions, source) {
  return makeExperience({
    initialState:'fixture',
    mirrorId:'mirror:fixture',
    shell:'comparison',
    actions,
    observer:DEFAULT_OBSERVER,
    observerField:{version:'s1-observer-field/v0',taskVersion:'s1-observer-task/v0',densityId:'carrier-v1',calibrations:[]},
    checkpoints:[],
    comparisons:{
      obligation:'live-vs-mirror',
      againstMirror:{equal:actions.length===0,maxAbsDelta:actions.length===0?0:0.01},
      againstPrevious:{equal:actions.length===0,maxAbsDelta:actions.length===0?0:0.01}
    },
    relations:{familyId:'carrier-v1',parentId:null,relatedIds:[]},
    provenance:{source}
  });
}

function fixtures() {
  const A=experienceCarrier(record([], 'A'));
  const B=experienceCarrier(record([{plane:'xw',degrees:1}], 'B'));
  const C=experienceCarrier(record([{plane:'yw',degrees:1}], 'C'));
  return {A,B,C};
}

test('v1 carrier operators are recursively closed over prior results',()=>{
  const {A,B,C}=fixtures();
  const joinAB=joinCarriers(A,B);
  const joinABC=joinCarriers(joinAB,C);
  const diff=differenceCarriers(joinAB,C);
  const interaction=interactCarriers(diff,joinCarriers(B,C));
  const frame=observerFrameCarrier({...DEFAULT_OBSERVER,yaw:0.2});
  const quotient=quotientCarrier(interaction,frame);

  for(const carrier of [A,B,C,joinAB,joinABC,diff,interaction,frame,quotient]){
    assert.equal(validateCarrier(carrier).id,carrier.id);
    assert.equal(carrier.schema,'s1-carrier/v1');
    assert.equal(carrier.version,CARRIER_VERSION);
    assert.equal(Object.isFrozen(carrier),true);
  }
  assert.equal(joinABC.kind,'join');
  assert.equal(diff.kind,'difference');
  assert.equal(interaction.kind,'interaction');
  assert.equal(quotient.kind,'quotient');
});

test('join has explicit neutral elision and parenthesization-normalized ordered chronology',()=>{
  const {A,B,C}=fixtures();
  assert.equal(joinCarriers(S1_CARRIER_NEUTRAL,A).id,A.id);
  assert.equal(joinCarriers(A,S1_CARRIER_NEUTRAL).id,A.id);

  const left=joinCarriers(joinCarriers(A,B),C);
  const right=joinCarriers(A,joinCarriers(B,C));
  assert.equal(left.id,right.id);
  assert.equal(left.descriptor,right.descriptor);
  assert.deepEqual(left.payload.chronology.map(carrier=>carrier.id),[A.id,B.id,C.id]);
  assert.deepEqual(left.payload.memberIds,[A.id,B.id,C.id].sort());
});

test('difference and interaction remain directional/ordered while sources stay immutable',()=>{
  const {A,B}=fixtures();
  const beforeA=canonicalJson(A),beforeB=canonicalJson(B);
  const ab=differenceCarriers(A,B),ba=differenceCarriers(B,A);
  const ixAB=interactCarriers(A,B),ixBA=interactCarriers(B,A);
  assert.notEqual(ab.id,ba.id);
  assert.notEqual(ixAB.id,ixBA.id);
  assert.equal(canonicalJson(A),beforeA);
  assert.equal(canonicalJson(B),beforeB);
});

test('quotient requires an observer-frame carrier and accepts any valid source carrier',()=>{
  const {A,B}=fixtures();
  const source=interactCarriers(A,B);
  const frame=observerFrameCarrier({...DEFAULT_OBSERVER,pitch:-0.3,wPerspective:0.8});
  const q=quotientCarrier(source,frame);
  assert.equal(q.payload.source.id,source.id);
  assert.equal(q.payload.frame.id,frame.id);
  assert.throws(()=>quotientCarrier(source,A),/observer-frame/i);
});

test('carrier construction is deterministic and rejects descriptor or id tampering',()=>{
  const r=record([{plane:'zw',degrees:-1}],'deterministic');
  const a=experienceCarrier(r),b=experienceCarrier(r);
  assert.equal(a.id,b.id);
  assert.equal(a.descriptor,b.descriptor);
  assert.throws(()=>validateCarrier({...a,id:'0000000000000000'}),/id/i);
  assert.throws(()=>validateCarrier({...a,descriptor:'{}'}),/descriptor/i);
});


test('recursive carrier validation propagates one collision registry through descendants',()=>{
  const {A,B}=fixtures();
  const joined=joinCarriers(A,B);
  const registry=new Map([[A.id,'forced-unequal-canonical-descriptor']]);
  assert.throws(()=>validateCarrier(joined,registry),/digest collision/i);

  const creationRegistry=new Map([[A.id,'forced-unequal-canonical-descriptor']]);
  assert.throws(()=>joinCarriers(A,B,creationRegistry),/digest collision/i);
});
