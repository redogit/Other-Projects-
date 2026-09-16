import test from 'node:test';
import assert from 'node:assert/strict';
import { createState, createMirror, applyMove, compareStates } from '../core.mjs';
import { sampleS3 } from '../geometry.mjs';
import { DEFAULT_OBSERVER, normalizeObserver, projectPair } from '../observer.mjs';
import { makeExperience, replayExperience } from '../experience.mjs';
import { MemoryStore, LocalExperienceStore } from '../storage.mjs';

const moves = Object.freeze([
  {plane:'xw',degrees:1},{plane:'xw',degrees:-1},
  {plane:'yw',degrees:1},{plane:'yw',degrees:-1},
  {plane:'zw',degrees:1},{plane:'zw',degrees:-1}
]);
const geom = sampleS3({etaSteps:2,xi1Steps:3,xi2Steps:3,radius:1});
const registry = new Map([[geom.id, geom]]);

function sequences(depth, prefix=[]) {
  if (depth === 0) return [prefix];
  return moves.flatMap(move => sequences(depth - 1, [...prefix, move]));
}
function record(actions) {
  return makeExperience({
    initialState:geom.id, mirrorId:`mirror:${geom.id}`, shell:geom.id, actions,
    observer:DEFAULT_OBSERVER,
    observerField:{version:'s1-observer-field/v0',taskVersion:'s1-observer-task/v0',densityId:'sweep',calibrations:[]},
    comparisons:{obligation:'live-vs-mirror'}, relations:{familyId:'sweep'}, provenance:{source:'bounded-possibility-sweep'}
  });
}

test('all declared one-degree moves have bounded inverse behavior and preserve mirror', () => {
  const origin=createState(geom.points4); const mirror=createMirror(origin); const before=JSON.stringify(mirror);
  for (const move of moves) {
    const out=applyMove(origin,move);
    const back=applyMove(out,{plane:move.plane,degrees:-move.degrees});
    assert.equal(compareStates(back,origin,1e-12).equal,true,`${move.plane} ${move.degrees}`);
    assert.equal(JSON.stringify(mirror),before);
  }
});

test('all legal move sequences through depth three replay exactly under the frozen contract', () => {
  const origin=createState(geom.points4); const ids=new Set(); let count=0;
  for (let depth=0; depth<=3; depth++) {
    for (const actions of sequences(depth)) {
      let direct=origin; for(const move of actions) direct=applyMove(direct,move);
      const event=record(actions); const replayed=replayExperience(event,registry);
      assert.equal(compareStates(replayed,direct,1e-12).equal,true,`depth ${depth}`);
      assert.equal(ids.has(event.id),false,`unexpected bounded ID collision ${event.id}`);
      ids.add(event.id); count++;
    }
  }
  assert.equal(count,259);
});

test('declared invalid move and observer boundary corpus fails closed', () => {
  const origin=createState(geom.points4);
  for (const bad of [
    {plane:'',degrees:1},{plane:'xy',degrees:1},{plane:'xw',degrees:0},{plane:'xw',degrees:2},
    {plane:'xw',degrees:-2},{plane:'xw',degrees:NaN},{plane:'xw',degrees:Infinity},{plane:'xw',degrees:null}
  ]) assert.throws(()=>applyMove(origin,bad));
  for (const badObserver of [
    {yaw:NaN},{pitch:Infinity},{roll:'0'},{wPerspective:-0.01},{wPerspective:1},{extra:0}
  ]) assert.throws(()=>normalizeObserver(badObserver));
  const near=normalizeObserver({wPerspective:0.999});
  const pair=projectPair(origin,createMirror(origin),near);
  assert.equal(pair.live.length,pair.mirror.length);
});

test('representative malformed storage possibilities are atomic', () => {
  const memory=new MemoryStore(); const store=new LocalExperienceStore(memory); store.save(record([])); const before=store.exportJson();
  const malformed=[
    'null','{}','[null]','[{"occurrences":0}]','[{"event":{},"occurrences":1}]',
    JSON.stringify([{event:{...record([]),id:'0000000000000000'},occurrences:1}])
  ];
  for(const payload of malformed){assert.throws(()=>store.importJson(payload));assert.equal(store.exportJson(),before);}
});
