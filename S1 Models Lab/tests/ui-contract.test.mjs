import test from 'node:test'; import assert from 'node:assert/strict'; import {readFile} from 'node:fs/promises'; const root=new URL('../',import.meta.url); async function text(name){return readFile(new URL(name,root),'utf8');}
test('README preserves experiment claim ceilings',async()=>{const readme=await text('README.md');for(const required of ['synthetic observer/reference surface','SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION','real 4D != complex dimension 4',"S'1_Mirror","S'1_Experience","S'1_Suggest","S'1_ObserverField"])assert.match(readme,new RegExp(required.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));});
test('schema declares exact v0 identity',async()=>{const s=JSON.parse(await text('schema/s1-experience-v0.schema.json'));assert.equal(s.$id,'s1-experience/v0');assert.equal(s.properties.operatorVersion.const,"S'1-Ops v0");assert.equal(s.additionalProperties,false);assert.equal(s.properties.observer.additionalProperties,false);assert.equal(s.properties.observerField.additionalProperties,false);});
test('accessible UI exposes all baseline controls and one application module',async()=>{const html=await text('index.html'),css=await text('styles.css');for(const id of ['xw-plus','xw-minus','yw-plus','yw-minus','zw-plus','zw-minus','save','replay','reframe','export','import-file','clear','shell','scene','inspection'])assert.match(html,new RegExp(`id=["']${id}["']`));assert.match(html,/aria-live=["']polite["']/);assert.match(html,/type=["']module["'][^>]*src=["']\.\/app\.mjs["']/);assert.equal((html.match(/<script/gi)||[]).length,1);assert.match(css,/:focus-visible/);assert.match(css,/prefers-reduced-motion:\s*reduce/);assert.match(css,/forced-colors:\s*active/);});
test('app preserves trajectory across shell reframes and rebuilds persisted graph state',async()=>{const app=await text('app.mjs');assert.match(app,/materializeTrajectory/);assert.match(app,/findLongestPrefixParent/);assert.match(app,/rebuildExperienceGraph/);assert.doesNotMatch(app,/function\s+resetGeometry\s*\(/);});

test('experience schema includes the full issue-39 saved-record minimum',async()=>{
  const s=JSON.parse(await text('schema/s1-experience-v0.schema.json'));
  assert.ok(s.required.includes('checkpoints'));
  assert.deepEqual(s.properties.comparisons.required,['obligation','againstMirror','againstPrevious']);
  assert.ok(s.properties.relations.required.includes('parentId'));
  assert.ok(s.properties.relations.required.includes('relatedIds'));
});

test('play surface includes optional teach-back without making it record authority',async()=>{
  const html=await text('index.html'), app=await text('app.mjs');
  assert.match(html,/id=["']teach-back["']/);
  assert.match(html,/own words|what did you observe/i);
  assert.doesNotMatch(app,/teach-back[^\n]*(makeExperience|currentRecord)/i);
});

test('live and mirror rendering has a non-color-only distinction',async()=>{const render=await text('render.mjs');assert.match(render,/setLineDash/);assert.match(render,/solid \? 2\.6 : 2\.1/);assert.match(render,/if \(solid\) ctx\.fill\(\); else ctx\.stroke\(\)/);});
