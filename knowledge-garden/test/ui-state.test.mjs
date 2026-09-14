import assert from 'node:assert/strict';
import vm from 'node:vm';
import fs from 'node:fs';
import * as core from '../public/working-set.mjs';
import { test } from 'node:test';
// This harness executes state transitions with DOM stubs; it is not browser or AT acceptance.
test('UI save, restore and clear transitions preserve the explicit state boundaries', () => {
const base = new URL('../', import.meta.url);
const html = fs.readFileSync(new URL('public/index.html', base), 'utf8');
const catalog = JSON.parse(fs.readFileSync(new URL('data/catalog.json', base), 'utf8'));
class Element {
  constructor(tag = 'div') { this.tagName=tag; this.children=[]; this.dataset={}; this.attributes={}; this.handlers={}; this.value=''; this.textContent=''; this.hidden=false; this.disabled=false; this.isConnected=true; this.files=[]; }
  append(...items) { this.children.push(...items); }
  replaceChildren(...items) { this.children=[...items]; }
  setAttribute(k,v) { this.attributes[k]=v; }
  removeAttribute(k) { delete this.attributes[k]; }
  addEventListener(k,fn) { (this.handlers[k]??=[]).push(fn); }
  querySelectorAll() { return []; }
  focus() { this.focused=true; }
  scrollIntoView() {}
  reset() { for (const [id, item] of ids) if (id.startsWith('task-')) item.value=''; }
  remove() { this.isConnected=false; }
}
const ids=new Map([...html.matchAll(/\bid="([^"]+)"/g)].map((match)=>[match[1],new Element()]));
const store=new Map([['other-app.key','retain me']]);
const storage={ getItem:key=>store.get(key)??null,setItem:(key,value)=>store.set(key,value),removeItem:key=>store.delete(key) };
class Reader {
  static LOADING=1;
  readyState=0;
  readAsText(file) { this.readyState=1; this.file=file; }
  abort() { this.aborted=true; this.readyState=2; this.file=null; }
}
const context=vm.createContext({ ...core,testCatalog:catalog,testStorage:storage,FileReader:Reader,Map,Set,Date,JSON,Intl,URL,Blob,console,crypto:globalThis.crypto,
 document:{ querySelector:s=>ids.get(s.slice(1)),createElement:t=>new Element(t),createDocumentFragment:()=>new Element('fragment'),createTextNode:t=>({textContent:t}),body:new Element('body')},
 window:{localStorage:storage,setTimeout,addEventListener(){}},location:{hash:''},history:{pushState(){}},fetch(){throw Error('Unexpected network call');} });
const source=fs.readFileSync(new URL('public/app.js',base),'utf8').replace(/^import[^\n]+\n/,'').replace(/renderCheckpoints\(\);\nawait loadCatalog\(\);\s*$/,'');
vm.runInContext(source,context);
const run=s=>vm.runInContext(s,context);
run('catalog=testCatalog;nodes=new Map(catalog.nodes.map(node=>[node.id,node]));sources=new Map(catalog.sources.map(source=>[source.id,source]));');
const state=()=>JSON.parse(run('JSON.stringify({snapshot:activeSnapshot(),pending:!!pendingRestore,undo:!!undoSnapshot,reader:!!pendingReader,file:$("#open-working-set").value})'));
const first=catalog.nodes[0].id, second=catalog.nodes[1].id;
run(`workingSet.add(${JSON.stringify(first)});$('#task-title').value='Before restore';$('#task-request').value='Preserve this request';`);
const original=state().snapshot;
run('checkpointHistory={save(){throw new Error("quota full")}};saveCheckpoint({clearAfter:true});');
assert.deepEqual(state().snapshot,original);
assert.match(ids.get('action-status').textContent,/not saved.*unchanged/);
run('checkpointHistory=createCheckpointHistory(testStorage);saveCheckpoint({clearAfter:true});');
assert.equal(state().snapshot.node_ids.length,0); assert.equal(state().snapshot.title,''); assert.equal(run('checkpointHistory.list().length'),1);
run(`workingSet.add(${JSON.stringify(first)});$('#task-title').value='Before restore';$('#task-request').value='Preserve this request';`);
context.importText=JSON.stringify(core.createWorkingSet(catalog,[second],{request:'<script>do not execute</script>'},{title:'Restored task',createdAt:'2026-09-14T00:00:00Z'}));
run('reviewWorkingSet(importText);');
assert.deepEqual(state().snapshot,original); assert.equal(state().pending,true);
run('restoreReviewedSelection();');
assert.equal(state().snapshot.title,'Restored task'); assert.deepEqual(state().snapshot.node_ids,[second]);assert.equal(state().snapshot.task.request,'<script>do not execute</script>'); assert.equal(state().undo,true);assert.equal(state().pending,false);
run('undoRestore();');assert.deepEqual(state().snapshot,original); assert.equal(state().undo,false);
// Active clearing invalidates and aborts an outstanding file read.
ids.get('open-working-set').files=[{size:22}]; ids.get('open-working-set').value='some-file.json';
run('openWorkingSetFile();');const reader=run('pendingReader');const staleHandler=reader.onload;
run('clearActiveWorkingSet();');assert.equal(reader.aborted,true);assert.equal(reader.onload,null);assert.equal(state().reader,false);assert.equal(state().file,'');assert.equal(state().snapshot.node_ids.length,0);staleHandler();assert.equal(state().pending,false);
// Saved-history clear preserves active content and the unrelated application key.
run(`workingSet.add(${JSON.stringify(first)});$('#task-title').value='Keep active';`);
const activeBeforeHistoryClear=state().snapshot;
ids.get('confirm-clear-checkpoints').handlers.click[0]();
assert.deepEqual(state().snapshot,activeBeforeHistoryClear);assert.equal(store.get('other-app.key'),'retain me');assert.equal(store.has('knowledge-garden.checkpoints.v1'),false);
});
