export const SECRET_SEQUENCE = ['q','2','e','3','r','1'];
export const FRONTIERS = [
  {name:'Quantum Gravity',q:'What framework consistently unifies quantum theory with dynamical spacetime?',boundary:'No experimentally confirmed complete quantum-gravity theory.',probe:'Look for observables that distinguish candidate low-energy or cosmological signatures.'},
  {name:'Black Hole Information',q:'How is quantum information preserved through black-hole formation and evaporation?',boundary:'Semiclassical reasoning, unitarity and spacetime descriptions remain in tension in important regimes.',probe:'Track which assumptions must change when information recovery is enforced.'},
  {name:'Measurement Problem',q:'What physical account, if any, selects definite outcomes from quantum superpositions?',boundary:'Interpretations reproduce ordinary quantum predictions but differ in ontology and sometimes proposed extensions.',probe:'Separate interpretation from experimentally distinguishable modification.'},
  {name:'Dark Matter',q:'What accounts for the gravitational evidence attributed to dark matter?',boundary:'Many candidates remain viable; none is established as the complete explanation.',probe:'Seek discriminating signatures across astrophysical, direct and collider searches.'},
  {name:'Cosmological Constant',q:'Why is observed vacuum energy so small compared with naive quantum-field estimates?',boundary:'The hierarchy is unresolved.',probe:'Test whether a proposed mechanism predicts something beyond restating the observed value.'},
  {name:'Quantum Foundations',q:'Which operational principles uniquely determine quantum theory, and where could they fail?',boundary:'Reconstructions exist but do not settle ontology or all extensions.',probe:'Find a minimal assumption whose removal changes experimentally accessible predictions.'}
];
export function normalizeProfile(raw={}) {
  return {
    version: 2,
    moves: Number.isFinite(raw.moves)?raw.moves:0,
    pulses: Number.isFinite(raw.pulses)?raw.pulses:0,
    events: Number.isFinite(raw.events)?raw.events:0,
    failures: Number.isFinite(raw.failures)?raw.failures:0,
    signals: Number.isFinite(raw.signals)?raw.signals:0,
    discoveries: Array.isArray(raw.discoveries)?[...new Set(raw.discoveries.filter(x=>typeof x==='string'))]:[],
    input: {keyboard:0,pointer:0,motion:0,speech:0,...(raw.input||{})}
  };
}
export function advanceSecret(buffer,key){
  const next=[...buffer,key].slice(-SECRET_SEQUENCE.length);
  return {buffer:next, unlocked:SECRET_SEQUENCE.every((v,i)=>next[i]===v)};
}
export function makeFrontier(index){
  const p=FRONTIERS[((index%FRONTIERS.length)+FRONTIERS.length)%FRONTIERS.length];
  return {...p,status:'UNRESOLVED'};
}
export function eventInterval(profile){
  const activity=(profile.events||0)+(profile.signals||0)+(profile.pulses||0)/20;
  return Math.max(8,Math.min(18,16-activity*.02));
}


export const RMAO_WORLD_ID='rmao-world';
export const RMAO_LIMB_STATES=Object.freeze(['attached','damaged','disabled','detached']);

export function chunkKey3D(x,y,z,chunkSize=256){
  if(!Number.isFinite(chunkSize)||chunkSize<=0) throw new TypeError('chunkSize must be positive');
  for(const v of [x,y,z]) if(!Number.isFinite(v)) throw new TypeError('coordinates must be finite');
  return [Math.floor(x/chunkSize),Math.floor(y/chunkSize),Math.floor(z/chunkSize)].join(':');
}

export function makeManyArmedBody(armCount=2){
  if(!Number.isInteger(armCount)||armCount<0||armCount>128) throw new RangeError('armCount must be an integer in [0,128]');
  const nodes=[{limbId:'core',kind:'core',parentLimbId:null,state:'attached',capabilities:['locomotion'],equipmentSlots:[]}];
  for(let i=0;i<armCount;i++) nodes.push({
    limbId:`arm:${i}`,kind:'arm',parentLimbId:'core',state:'attached',
    capabilities:[`arm-use:${i}`],equipmentSlots:[`hand:${i}`]
  });
  return {schema:'rmao.limb-graph/v1',nodes};
}

export function detachLimb(graph,limbId){
  if(!graph||!Array.isArray(graph.nodes)) throw new TypeError('invalid limb graph');
  const byId=new Map(graph.nodes.map(n=>[n.limbId,n]));
  if(!byId.has(limbId)) throw new RangeError('unknown limbId');
  if(limbId==='core') throw new RangeError('core detachment is not an arm-removal operation');
  const descendants=new Set([limbId]);
  let changed=true;
  while(changed){changed=false;for(const n of graph.nodes){if(n.parentLimbId&&descendants.has(n.parentLimbId)&&!descendants.has(n.limbId)){descendants.add(n.limbId);changed=true;}}}
  const lostCapabilities=[],lostEquipmentSlots=[];
  const nodes=graph.nodes.map(n=>{
    if(!descendants.has(n.limbId)) return {...n,capabilities:[...(n.capabilities||[])],equipmentSlots:[...(n.equipmentSlots||[])]};
    lostCapabilities.push(...(n.capabilities||[])); lostEquipmentSlots.push(...(n.equipmentSlots||[]));
    return {...n,state:'detached',capabilities:[],equipmentSlots:[]};
  });
  return {graph:{...graph,nodes},detached:[...descendants].sort(),lostCapabilities:[...new Set(lostCapabilities)].sort(),lostEquipmentSlots:[...new Set(lostEquipmentSlots)].sort()};
}
