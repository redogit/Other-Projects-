// Packaging-level tests of real app code with the upstream Node DOM/fetch harness.
// This is not a browser-origin, visual-rendering or production-security audit.
import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('../', import.meta.url)));
const site = resolve(process.argv[2] || `${root}/build/site`);
process.argv[2] = site;
await import(pathToFileURL(`${site}/tools/check_site.mjs`).href);
if (process.exitCode) throw new Error('Upstream site checker failed');
const api = globalThis.Conscience64API;
assert.equal(api.version, '1.2.0-coop.2');
let checks = 0;
function rejected(fn, code) {
  assert.throws(fn, error => error.code === code); checks++;
}
rejected(() => api.search.advanced({from:'missing:publication-probe'}), 'UNRESOLVED_REFERENCE');
rejected(() => api.search.advanced({to:''}), 'INVALID_REFERENCE');
rejected(() => api.search.advanced(null), 'INVALID_QUERY');
const caller = {I:{text:'publication smoke test'}, R:{scope:'local'}, P:{action:'receipt'}, O:{value:1}};
api.irpo(caller);
caller.O.value = 9;
assert.equal(api.history().at(-1).O.value, 1); checks++;
const copy = api.history(); copy.at(-1).O.value = 11;
assert.equal(api.history().at(-1).O.value, 1); checks++;
for (const output of [1n, (() => { const x={}; x.self=x; return x; })(), () => 1]) {
  const before = api.history();
  const view = ['i','r','p','o'].map(k => document.getElementById(`irpo-${k}`).textContent);
  rejected(() => api.irpo({I:'reject me', O:output}), 'INVALID_IRPO_RECORD');
  assert.deepEqual(api.history(), before);
  assert.deepEqual(['i','r','p','o'].map(k => document.getElementById(`irpo-${k}`).textContent), view);
}
async function message(method, args) {
  return new Promise((done, fail) => {
    const timer = setTimeout(() => fail(new Error('API response timeout')), 3000);
    const event = new Event('message');
    const id = `publish-${method}`;
    Object.defineProperties(event, {
      data:{value:{type:'conscience64.api',id,method,args}},
      source:{value:{postMessage(reply){clearTimeout(timer);done(reply);}}}
    });
    dispatchEvent(event);
  });
}
for (const method of ['chat','constructor','toString']) {
  const reply = await message(method, []);
  assert.equal(reply.ok, false); assert.equal(reply.errorCode, 'UNKNOWN_METHOD'); checks++;
}
const malformed = await message('search.advanced', {});
assert.equal(malformed.ok, false); assert.equal(malformed.errorCode, 'INVALID_ARGUMENTS'); checks++;
const receipt = await message('irpo', [{I:'New project packaging check',R:{scope:'local'},
  P:{action:'receipt'},O:{author:'ChatGPT',independentCompanionEndorsement:false}}]);
assert.equal(receipt.ok,true); assert.equal(receipt.result.O.independentCompanionEndorsement,false); checks++;
console.log(JSON.stringify({status:'PASS',candidateVersion:api.version,
  packagingChecks:checks,transport:'Node EventTarget/source-window stand-in; not a browser session',
  graphs:api.stats().total,projects:api.projects.list().total}));
