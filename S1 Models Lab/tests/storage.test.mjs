import test from 'node:test'; import assert from 'node:assert/strict'; import {MemoryStore,LocalExperienceStore} from '../storage.mjs'; import {makeExperience} from '../experience.mjs'; import {DEFAULT_OBSERVER} from '../observer.mjs';
function rec(){return makeExperience({initialState:'fixture',mirrorId:'m',shell:'comparison',actions:[],observer:DEFAULT_OBSERVER,observerField:{version:'s1-observer-field/v0',taskVersion:'s1-observer-task/v0',densityId:'fixture',calibrations:[]},comparisons:{obligation:'live-vs-mirror'},relations:{familyId:'f'},provenance:{source:'unit'}})}
test('constructing store performs zero writes',()=>{const m=new MemoryStore();new LocalExperienceStore(m);assert.equal(m.writeCount,0);});
test('save deduplicates event and increments occurrence count',()=>{const s=new LocalExperienceStore(new MemoryStore());const r=rec();s.save(r);s.save(r);const rows=s.list();assert.equal(rows.length,1);assert.equal(rows[0].occurrences,2);});
test('export import roundtrip is atomic and rejects corruption',()=>{const s=new LocalExperienceStore(new MemoryStore());const r=rec();s.save(r);const text=s.exportJson();s.clear();assert.equal(s.list().length,0);s.importJson(text);assert.equal(s.list()[0].event.id,r.id);const before=s.exportJson();assert.throws(()=>s.importJson('{'));assert.equal(s.exportJson(),before);assert.throws(()=>s.importJson(JSON.stringify([{event:{...r,operatorVersion:'bad'},occurrences:1}])));assert.equal(s.exportJson(),before);});

test('import coalesces duplicate canonical events and preserves a safe occurrence total',()=>{
  const s=new LocalExperienceStore(new MemoryStore()); const r=rec();
  const payload=JSON.stringify([{event:r,occurrences:2},{event:r,occurrences:3}]);
  s.importJson(payload);
  const rows=s.list(); assert.equal(rows.length,1); assert.equal(rows[0].occurrences,5);
  assert.throws(()=>s.importJson(JSON.stringify([{event:r,occurrences:Number.MAX_SAFE_INTEGER},{event:r,occurrences:1}])));
  assert.equal(s.list()[0].occurrences,5);
});
