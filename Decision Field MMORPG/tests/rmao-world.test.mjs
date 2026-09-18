import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {RMAO_WORLD_ID,RMAO_LIMB_STATES,chunkKey3D,makeManyArmedBody,detachLimb} from '../core.mjs';

const contract=JSON.parse(await readFile(new URL('../rmao-world-contract.json',import.meta.url),'utf8'));
assert.equal(RMAO_WORLD_ID,'rmao-world');
assert.deepEqual(RMAO_LIMB_STATES,['attached','damaged','disabled','detached']);
assert.equal(chunkKey3D(0,0,0),'0:0:0');
assert.equal(chunkKey3D(255.9,256,-0.1),'0:1:-1');
assert.throws(()=>chunkKey3D(0,0,0,0));

const body=makeManyArmedBody(12);
assert.equal(body.nodes.filter(n=>n.kind==='arm').length,12);
const result=detachLimb(body,'arm:7');
assert.equal(result.graph.nodes.find(n=>n.limbId==='arm:7').state,'detached');
assert.deepEqual(result.lostCapabilities,['arm-use:7']);
assert.deepEqual(result.lostEquipmentSlots,['hand:7']);
assert.equal(body.nodes.find(n=>n.limbId==='arm:7').state,'attached');
assert.throws(()=>makeManyArmedBody(129));

assert.equal(contract.worldId,'rmao-world');
assert.equal(contract.spatial.dimensions,3);
assert.equal(contract.limbGraph.arbitraryArmCount,true);
assert.equal(contract.authority.serverRequiredForMMORPGClaim,true);
assert.equal(contract.currentRenderer.massive3DClaim,false);
console.log('PASS RMAO world seed: 3D chunk keys, arbitrary arms, immutable detachment consequences, authority ceiling');
