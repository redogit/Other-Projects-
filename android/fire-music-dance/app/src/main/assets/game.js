(() => {
"use strict";

const canvas=document.getElementById("field"),ctx=canvas.getContext("2d",{alpha:false});
const ui=id=>document.getElementById(id);
let W=0,H=0,DPR=1,last=performance.now(),eventT=0,spawnT=0;
const TAU=Math.PI*2;

const W114=Object.freeze({
  objectId:"ROOT:W114",
  degree:114,
  alpha:[1,7,78,79,86,91],
  jacobian:[0,6,77,78,85,90],
  target:"x1^6*x2^77*x3^78*x4^85*x5^90",
  deck:[1,1,0,1,0,1],
  halfSplit:[[1,79,91],[7,78,86]],
  center:"MOT-1"
});

const EYES=Object.freeze([
  {id:"EYE:GEO",name:"GEOMETRY",color:"#ffb35b"},
  {id:"EYE:DATA",name:"DATA/CHAR",color:"#67f3ff"},
  {id:"EYE:FLOW",name:"FLOW/DEFORM",color:"#77ff9b"},
  {id:"EYE:EVENT",name:"EVENT/FIRE",color:"#ff6b6b"},
  {id:"EYE:HUMAN",name:"HUMAN/CLAIM",color:"#c78cff"}
]);

const ALL_WAYS=Object.freeze(["FORWARD","BACKWARD","UP","DOWN","SIDEWAYS","INWARD","OUTWARD","AROUND","THROUGH","REVERSE","BRANCH","HOMEWARD"]);

const ASH_CONTROLS=Object.freeze([
  {id:"ASH:PAIR-KOSZUL",label:"pair-separated Koszul / skew-gauge",kind:"GEOMETRY"},
  {id:"ASH:SAME-LEVEL",label:"ordinary same-level decompositions",kind:"TOPOLOGY"},
  {id:"ASH:PURE-POWER",label:"proper-divisor pure-power descents",kind:"GEOMETRY"},
  {id:"ASH:X57-PULLBACK",label:"ordinary 114→57 pullbacks",kind:"TOPOLOGY"},
  {id:"ASH:TATE-LIFT",label:"lifted standard Tate-plane family",kind:"GEOMETRY"},
  {id:"ASH:SIMPLE-TENSOR",label:"simple divisor tensor family",kind:"GEOMETRY"},
  {id:"ASH:CUBIC-DELSARTE",label:"six-monomial cubic Delsarte preimages",kind:"CHARACTER"},
  {id:"ASH:LIFT-e2-e8-d2",label:"lift multipliers e=2..8 at depth≤2",kind:"CERTIFICATE"},
  {id:"ASH:LIFTED-PAIR-PLANE",label:"q-twisted lifted pair-plane family 0/15",kind:"MOTIVIC"}
]);

const EMBER_CONTROLS=Object.freeze([
  {id:"EMBER:57-57",label:"unique 57/57 lobe split",kind:"CHARACTER"},
  {id:"EMBER:JAC-EQ",label:"equal-degree Jacobian skeleton",kind:"GEOMETRY"},
  {id:"EMBER:JAC-UNEQ",label:"unequal-degree Jacobian skeleton",kind:"GEOMETRY"},
  {id:"EMBER:DECK",label:"nontrivial deck parity p=(1,1,0,1,0,1)",kind:"TOPOLOGY"},
  {id:"EMBER:DOUBLE-COVER",label:"X114 → Yp → X57 anti-invariant sector",kind:"GEOMETRY"},
  {id:"EMBER:AQ",label:"quadratic A_q carrier q=7-ζ3",kind:"MOTIVIC"},
  {id:"EMBER:TATE-PROJECTOR",label:"explicit level-57 Tate plane projector",kind:"CHOW"},
  {id:"EMBER:DUP-WORD",label:"exact 114→57 duplication word",kind:"ARITHMETIC"}
]);

const FRONTIERS=Object.freeze([
  {species:"nonpair-correspondence",parts:["M_gap","A_q","deck−"],color:"#73f7ff"},
  {species:"lobe-determinantal",parts:["A-lobe","B→−A","ACM"],color:"#ffd26f"},
  {species:"mixed-mf",parts:["non-CI","AB=QI","W114"],color:"#ff79a8"},
  {species:"half-twist",parts:["component-resolved","Shioda#","deck"],color:"#b995ff"},
  {species:"weighted-shioda",parts:["higher-degree","weighted","character"],color:"#85ffb1"},
  {species:"graph-projector-chain",parts:["Tate-plane","N/D3/D19","twist"],color:"#ff9b5b"},
  {species:"curve-product",parts:["curve","Artin","rank-one"],color:"#eafc76"}
]);

const EVENTS=Object.freeze([
  "THE HODGE SEAM STARTED SINGING BACKWARDS",
  "A PROJECTOR FORGOT WHICH WAY WAS FORWARD",
  "THE DECK INVOLUTION GREW TEETH",
  "JACOBIAN RING RAIN IS FALLING SIDEWAYS",
  "FIVE EYES BLINKED OUT OF PHASE",
  "ASH REMEMBERED ITS PREVIOUS LIFE",
  "THE 57/57 LOBE SPLIT OPENED LIKE A DOOR",
  "FUZZBALL APPEARED IN THE QUOTIENT",
  "THE COMPASS ROSE TURNED ITSELF INSIDE OUT",
  "A COGNATE CLAIMED TO BE ITS OWN COUSIN"
]);

const profile=loadProfile();
const state={
  score:profile.score||0,combo:1,heat:0,epoch:profile.epoch||0,
  music:profile.music||false,bpm:108,beat:0,
  yaw:0,pitch:0,zoom:1,elevation:0,spin:0,storm:0.25,
  target:null,pulseNo:0,shardNo:profile.shardNo||0,
  ash:[...ASH_CONTROLS],embers:[...EMBER_CONTROLS],survivors:profile.survivors||[],habits:profile.habits||{},
  remainder:["MOT-1 explicit nonzero Chow morphism remains open","MF-1 genuinely mixed non-CI carrier remains open","LIFT-1 level-342 depth-3 is unresolved by runtime"],
  trace:profile.trace||[],cognates:profile.cognates||[],
  wayHits:Object.fromEntries(ALL_WAYS.map(x=>[x,0])),activeWay:"AROUND",
  eyeRead:Object.fromEntries(EYES.map(e=>[e.id,0])),
  lastWay:null,firePhase:0,reverseParity:0,fuzzball:profile.fuzzball||false,
  ledger:false
};

const particles=makeFireParticles(430);
const filaments=makeFractalFire();
const sparks=[];
const shards=[];
const ghosts=makeGhostControls();
const eyes=EYES.map((e,i)=>({...e,phase:i/EYES.length*TAU,pulse:0}));
let pointer={down:false,x:0,y:0,px:0,py:0,downAt:0,moved:false};
let audio=null,musicTimer=null;

function loadProfile(){try{return JSON.parse(localStorage.getItem("five-eyes-fermat-fire-v2")||"{}")}catch{return {}}}
function save(){
  localStorage.setItem("five-eyes-fermat-fire-v2",JSON.stringify({
    score:state.score,epoch:state.epoch,shardNo:state.shardNo,music:state.music,habits:state.habits,
    survivors:state.survivors,cognates:state.cognates,trace:state.trace.slice(-180),fuzzball:state.fuzzball
  }));
}
function hash(s){let h=2166136261>>>0;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return(h>>>0).toString(16).padStart(8,"0")}
function randFrom(s,k=0){const h=parseInt(hash(s+":"+k),16)>>>0;return((h%1000003)/1000003)}
function idFor(species,n){return"CYC:"+species.toUpperCase().slice(0,6)+":"+hash(species+":"+n).slice(0,8)}
function clamp(v,a,b){return Math.max(a,Math.min(b,v))}
function lerp(a,b,t){return a+(b-a)*t}

function resize(){
  DPR=Math.min(2,devicePixelRatio||1);W=innerWidth;H=innerHeight;
  canvas.width=Math.floor(W*DPR);canvas.height=Math.floor(H*DPR);canvas.style.width=W+"px";canvas.style.height=H+"px";
  ctx.setTransform(DPR,0,0,DPR,0,0);
}
addEventListener("resize",resize);resize();

function makeFireParticles(n){
  const out=[];
  for(let i=0;i<n;i++){
    const u=randFrom("fire",i),v=randFrom("firev",i),w=randFrom("firew",i);
    const h=u*2.4-0.8,rad=(1-Math.max(0,h)/2.6)*(0.15+v*.62);
    const a=v*TAU*5+w*2;
    out.push({base:[Math.cos(a)*rad,h,Math.sin(a)*rad,(v-.5)*1.4,(w-.5)*1.4,(u-.5)*1.2],phase:w*TAU,size:1+v*4});
  }
  return out;
}
function makeFractalFire(){
  const segs=[];
  function branch(p,dir,len,depth,seed){
    if(depth<=0)return;
    const e=p.map((x,i)=>x+dir[i]*len);
    segs.push({a:p,b:e,depth});
    for(let k=0;k<3;k++){
      const n=dir.slice();
      const q=(seed*17+k*31+depth*7)%6,r=(q+1+k)%6;
      const ang=(k-1)*.46+Math.sin(seed+depth)*.13;
      const c=Math.cos(ang),s=Math.sin(ang),x=n[q],y=n[r];n[q]=x*c-y*s;n[r]=x*s+y*c;
      n[1]+=0.08;
      branch(e,n,len*.72,depth-1,seed+k+1);
    }
  }
  branch([0,-.65,0,0,0,0],[0,1,0,.12,.07,.05],.48,5,3);
  return segs;
}
function makeGhostControls(){
  return ASH_CONTROLS.map((a,i)=>({id:a.id,label:a.label,kind:a.kind,phase:i/ASH_CONTROLS.length*TAU,ring:1.7+(i%3)*.22}));
}

function rotatePair(v,i,j,a){const c=Math.cos(a),s=Math.sin(a),x=v[i],y=v[j];v[i]=x*c-y*s;v[j]=x*s+y*c}
function transform6(src,t,extra=0){
  const v=src.slice();
  const weights=ALL_WAYS.map((_,i)=>(state.wayHits[ALL_WAYS[i]]||0)*.0025+0.03);
  rotatePair(v,0,3,t*.18+state.yaw+weights[7]);
  rotatePair(v,1,4,t*.13+state.pitch+weights[2]-weights[3]);
  rotatePair(v,2,5,t*.16+state.spin+weights[9]*state.reverseParity);
  rotatePair(v,0,5,t*.07+weights[4]);
  rotatePair(v,1,3,t*.09+weights[5]-weights[6]);
  rotatePair(v,2,4,t*.11+weights[8]);
  if(extra)rotatePair(v,0,1,extra);
  return v;
}
function project6(src,t,scale=1){
  const v=transform6(src,t);
  const x=v[0]+v[3]*.34+Math.sin(v[5]*2+t*.2)*.08;
  const y=v[1]+v[4]*.23;
  const z=v[2]+v[5]*.31;
  const cy=Math.cos(state.yaw*.25),sy=Math.sin(state.yaw*.25),cp=Math.cos(state.pitch*.2),sp=Math.sin(state.pitch*.2);
  let X=x*cy-z*sy,Z=x*sy+z*cy,Y=y*cp-Z*sp;Z=y*sp+Z*cp;
  const p=1/(1+Math.max(-.75,Z*.24));
  return {x:W/2+X*Math.min(W,H)*.23*state.zoom*scale*p,y:H/2-Y*Math.min(W,H)*.23*state.zoom*scale*p,z:Z,p};
}

function spawnCandidate(parent=null,forced=null){
  state.shardNo++;
  const f=forced||FRONTIERS[Math.floor(randFrom("frontier",state.shardNo)*FRONTIERS.length)];
  const id=idFor(f.species,state.shardNo);
  const habit=state.habits[f.species]||0;
  const stability=.42+randFrom(id,1)*.46+Math.min(.08,habit*.005);
  const vec=Array.from({length:6},(_,i)=>randFrom(id,i+4)*2-1);
  vec[1]=randFrom(id,20)*1.6-.35;
  const parts=f.parts.slice();
  const obj={id,species:f.species,parts,color:f.color,vec,vel:Array.from({length:6},(_,i)=>(randFrom(id,30+i)-.5)*.05),
    integrity:1,stability,hits:0,uniqueWays:[],status:"GENERATED",parentId:parent?.id||W114.objectId,age:0,cognates:[],bbf:false};
  findCognates(obj);
  shards.push(obj);
  trace("GENERATE",obj.id,{species:obj.species,parentId:obj.parentId,cognates:obj.cognates});
  popup("+ CANDIDATE",W/2,H*.62,obj.color);
  return obj;
}
function findCognates(obj){
  const source=[...ASH_CONTROLS,...EMBER_CONTROLS,...state.survivors];
  const tokens=new Set(obj.parts.map(x=>x.toLowerCase()));
  for(const row of source){
    const text=(row.label||row.species||"").toLowerCase();
    let overlap=0;for(const t of tokens)if(text.includes(t.split("→")[0].split("-")[0]))overlap++;
    if(overlap||randFrom(obj.id+row.id,99)>.92){
      const rel={from:obj.id,to:row.id,type:row.id.startsWith("ASH:")?"BURNED_COGNATE":"SURVIVING_COGNATE",strength:clamp(.2+overlap*.25+randFrom(obj.id+row.id,7)*.35,0,1)};
      obj.cognates.push(rel);state.cognates.push(rel);
    }
  }
  state.cognates=state.cognates.slice(-80);
}

function fiveEyes(obj,way){
  const values={};
  const base=obj?obj.stability:.5;
  EYES.forEach((e,i)=>{
    const v=clamp(.18+base*.46+randFrom((obj?.id||"ROOT")+e.id+way,state.pulseNo+i)*.42,0,1);
    values[e.id]=v;state.eyeRead[e.id]=v;eyes[i].pulse=1;
  });
  return values;
}

function primaryWay(){
  const i=state.pulseNo%ALL_WAYS.length;
  return ALL_WAYS[i];
}
function hitTarget(){
  state.pulseNo++;state.heat=clamp(state.heat+7,0,100);
  const way=primaryWay();state.activeWay=way;state.wayHits[way]++;state.lastWay=way;
  shockwave(way);
  const obj=state.target&&shards.includes(state.target)?state.target:nearestLiveShard();
  const eyesNow=fiveEyes(obj,way);
  if(!obj){state.score+=5;trace("FIRE_PULSE",W114.objectId,{way,eyes:eyesNow,remainder:"no candidate locked"});return}
  obj.hits++;
  if(!obj.uniqueWays.includes(way))obj.uniqueWays.push(way);
  const repeated=Math.max(0,obj.hits-obj.uniqueWays.length);
  const oneDegree=.07+.15*(1-obj.stability)+state.heat*.0008+repeated*.015;
  obj.integrity-=oneDegree;
  const novelty=1/(1+(state.habits[obj.species]||0));
  const pts=Math.round(20*novelty*(1+obj.uniqueWays.length*.35));
  state.score+=pts*state.combo;
  popup("+"+pts*state.combo,(project6(obj.vec,state.firePhase).x),(project6(obj.vec,state.firePhase).y),obj.color);
  trace("BURN",obj.id,{way,oneDegree:true,integrity:obj.integrity,eyeResponses:eyesNow});
  if(obj.integrity<=0){
    obj.status="ASH";state.ash.push({id:obj.id,label:obj.species,kind:"GAME_CANDIDATE"});
    state.habits[obj.species]=(state.habits[obj.species]||0)+1;
    state.combo=1;state.remainder.push(obj.id+" collapsed under "+way);
    popup("ASH",W/2,H/2,"#8a858d");
    state.target=null;
  }else{
    if(obj.uniqueWays.length>=3&&obj.status==="GENERATED"){
      obj.status="EMBER";state.embers.push({id:obj.id,label:obj.species,kind:"GAME_CANDIDATE"});
      state.score+=150;state.combo=Math.min(9,state.combo+1);popup("EMBER",W/2,H/2,"#ffd86a");
    }
    if(obj.uniqueWays.length>=6&&obj.bbf&&obj.integrity>.34&&obj.status!=="SURVIVOR"){
      obj.status="SURVIVOR";state.survivors.push({id:obj.id,label:obj.species,kind:"GAME_CANDIDATE",integrity:obj.integrity});
      state.score+=1000*state.combo;state.combo=Math.min(12,state.combo+2);popup("SURVIVOR",W/2,H/2,"#92ff9d");
      trace("SURVIVOR",obj.id,{uniqueWays:obj.uniqueWays,integrity:obj.integrity,boundary:"GAME_SURVIVOR != CHOW_CYCLE"});
    }
  }
  save();
}
function reverseProbe(){
  state.reverseParity*=-1;state.wayHits.REVERSE++;state.activeWay="REVERSE";
  const obj=state.target&&shards.includes(state.target)?state.target:nearestLiveShard();
  if(obj){
    const before=obj.integrity;const fold=hash(JSON.stringify(obj.vec));const unfold=hash(JSON.stringify(obj.vec));
    obj.bbf=fold===unfold;state.score+=obj.bbf?80:0;
    trace("BBF_REVERSE",obj.id,{fold,unfold,reconstructs:obj.bbf,integrityBefore:before,integrityAfter:obj.integrity});
    popup(obj.bbf?"BBF ✓":"DECAY",W/2,H*.42,obj.bbf?"#67f3ff":"#ff6b6b");
  }
  state.yaw*=-1;state.spin*=-1;haptic(48);save();
}
function branch(){
  state.wayHits.BRANCH++;state.activeWay="BRANCH";
  const parent=state.target&&shards.includes(state.target)?state.target:null;
  for(let i=0;i<3;i++)spawnCandidate(parent,FRONTIERS[(state.shardNo+i)%FRONTIERS.length]);
  trace("BRANCH",parent?.id||W114.objectId,{children:3});haptic(35);
}
function homeward(){
  state.wayHits.HOMEWARD++;state.activeWay="HOMEWARD";state.yaw=state.pitch=state.spin=state.elevation=0;state.zoom=1;state.storm=.25;state.target=null;state.heat*=.55;
  trace("HOMEWARD",W114.objectId,{recentered:true,knowledgePreserved:true});popup("HOMEWARD",W/2,H*.35,"#fff1b8");haptic(70);
}

function nearestLiveShard(){
  let best=null,bd=Infinity;
  for(const s of shards)if(s.integrity>0){const p=project6(s.vec,state.firePhase),d=Math.hypot(p.x-W/2,p.y-H/2);if(d<bd){bd=d;best=s}}
  return best;
}
function selectAt(x,y){
  let best=null,bd=50;
  for(const s of shards)if(s.integrity>0){const p=project6(s.vec,state.firePhase),d=Math.hypot(p.x-x,p.y-y);if(d<bd){bd=d;best=s}}
  state.target=best;if(best){trace("LOCK_OBJECT",best.id,{species:best.species});popup(best.id,x,y,best.color);haptic(22)}
}

function trace(op,objectId,detail){
  state.trace.push({n:state.trace.length+1,t:Date.now(),op,objectId,detail});
  if(state.trace.length>220)state.trace=state.trace.slice(-220);
}
function popup(text,x,y,color="#ffd86a"){
  const d=document.createElement("div");d.className="popup";d.textContent=text;d.style.left=x+"px";d.style.top=y+"px";d.style.color=color;ui("popups").appendChild(d);setTimeout(()=>d.remove(),950);
}
function showEvent(s){
  ui("event").textContent=s;ui("event").classList.add("show");setTimeout(()=>ui("event").classList.remove("show"),1800);
}
function haptic(ms){try{window.AndroidBridge?.vibrate?.(ms)}catch{}}
function shockwave(way){
  sparks.push({kind:"wave",born:performance.now(),way});
  for(let i=0;i<18;i++)sparks.push({kind:"spark",born:performance.now(),a:i/18*TAU,r:.1,way});
  haptic(state.beat%4===0?42:20);
}

function weirdEvent(){
  state.epoch++;const s=EVENTS[state.epoch%EVENTS.length];showEvent(s);
  if(s.includes("FUZZBALL")){state.fuzzball=true;spawnCandidate(null,{species:"fuzzball-gap",parts:["UNRESOLVED","cognate?","??? "],color:"#ff72ec"})}
  const mode=state.epoch%6;if(mode===0)reverseProbe();if(mode===1)branch();if(mode===2)state.spin+=.6;if(mode===3)state.storm=.9;if(mode===4)spawnCandidate();if(mode===5)state.zoom=.8+randFrom("event",state.epoch)*.8;
  trace("WORLD_EVENT",W114.objectId,{event:s,gameOnly:true});save();
}

function beat(){
  state.beat++;state.firePhase+=.08;state.heat=Math.max(0,state.heat-.8);
  if(state.music){tone(state.beat%4===1?180:120,state.beat%4===1?.055:.025);haptic(state.beat%4===1?24:8)}
}
function toggleMusic(){
  state.music=!state.music;if(state.music){ensureAudio();clearInterval(musicTimer);musicTimer=setInterval(beat,60000/state.bpm);showEvent("MUSIC ENTERS THE FIRE")}else{clearInterval(musicTimer);musicTimer=null;showEvent("MUSIC RESTS")}
  save();
}
function ensureAudio(){if(!audio)audio=new (window.AudioContext||window.webkitAudioContext)()}
function tone(freq,dur){if(!audio)return;const o=audio.createOscillator(),g=audio.createGain();o.frequency.value=freq;o.type="sine";g.gain.value=.025;o.connect(g);g.connect(audio.destination);o.start();g.gain.exponentialRampToValueAtTime(.0001,audio.currentTime+dur);o.stop(audio.currentTime+dur)}

function drawBackground(t){
  const g=ctx.createRadialGradient(W/2,H/2,20,W/2,H/2,Math.max(W,H)*.72);g.addColorStop(0,"#1b081f");g.addColorStop(.34,"#090411");g.addColorStop(1,"#020104");ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
  ctx.save();ctx.translate(W/2,H/2);ctx.rotate(t*.01+state.yaw*.05);ctx.strokeStyle="#7b5c9b18";ctx.lineWidth=1;
  for(let r=100;r<Math.max(W,H);r+=78){ctx.beginPath();for(let a=0;a<=TAU+.1;a+=.18){const rr=r+Math.sin(a*5+t*.3)*8;const x=Math.cos(a)*rr,y=Math.sin(a)*rr;a===0?ctx.moveTo(x,y):ctx.lineTo(x,y)}ctx.stroke()}ctx.restore();
}
function drawGhosts(t){
  ctx.save();ctx.font="9px ui-monospace,monospace";ctx.textAlign="center";
  ghosts.forEach((g,i)=>{const a=g.phase+t*.045*(i%2?1:-1),r=Math.min(W,H)*.20*g.ring;const x=W/2+Math.cos(a)*r,y=H/2+Math.sin(a)*r*.45;ctx.globalAlpha=.18;ctx.strokeStyle="#b0abb3";ctx.beginPath();ctx.arc(x,y,7,0,TAU);ctx.stroke();if(i%3===0){ctx.fillStyle="#aaa5ad";ctx.fillText(g.id.replace("ASH:",""),x,y-11)}});
  ctx.restore();ctx.globalAlpha=1;
}
function drawFilaments(t){
  ctx.save();ctx.lineWidth=1;
  for(const s of filaments){const a=project6(s.a,t,.9),b=project6(s.b,t,.9);ctx.strokeStyle="rgba(255,120,55,"+(0.07+s.depth*.018)+")";ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke()}
  ctx.restore();
}
function drawFire(t){
  const pts=particles.map(p=>{const v=p.base.slice();v[1]+=Math.sin(t*2+p.phase)*.05;return{p,pr:project6(v,t,1.1)}}).sort((a,b)=>a.pr.z-b.pr.z);
  for(const row of pts){
    const pr=row.pr,p=row.p,life=clamp((p.base[1]+.8)/3,0,1);const r=(1.5+p.size)*pr.p*(.8+state.heat*.008);
    ctx.fillStyle=life>.62?"rgba(255,221,111,.62)":life>.28?"rgba(255,112,43,.5)":"rgba(150,65,255,.32)";
    ctx.beginPath();ctx.arc(pr.x,pr.y,r,0,TAU);ctx.fill();
  }
  const c=project6([0,.25,0,0,0,0],t),rad=Math.min(W,H)*.07*(1+state.heat*.004);
  const g=ctx.createRadialGradient(c.x,c.y,0,c.x,c.y,rad*1.8);g.addColorStop(0,"#fffbd4");g.addColorStop(.18,"#ffd35b");g.addColorStop(.55,"#ff632e88");g.addColorStop(1,"#8a2fff00");ctx.fillStyle=g;ctx.beginPath();ctx.arc(c.x,c.y,rad*1.8,0,TAU);ctx.fill();
  // Three FIRE shells: pull/lift/return.
  ["#ff7a38","#a96dff","#68e9ff"].forEach((col,i)=>{ctx.strokeStyle=col+"55";ctx.lineWidth=1+i*.4;ctx.beginPath();ctx.ellipse(c.x,c.y,rad*(1.8+i*.58),rad*(.55+i*.19),t*(.15+i*.04),0,TAU);ctx.stroke()});
}
function drawEyes(t){
  const cr=Math.min(W,H)*.32;ctx.save();ctx.textAlign="center";ctx.font="9px ui-monospace,monospace";
  eyes.forEach((e,i)=>{const a=e.phase+t*.12+(i%2?state.yaw:-state.yaw)*.15;const z=Math.sin(a)*.4;const x=W/2+Math.cos(a)*cr,y=H/2+Math.sin(a)*cr*.34+Math.sin(t*.3+i)*10;const scale=.75+(z+1)*.18;e.x=x;e.y=y;
    ctx.globalAlpha=.12+e.pulse*.22;ctx.strokeStyle=e.color;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(W/2,H/2);ctx.stroke();ctx.globalAlpha=1;
    ctx.fillStyle="#08040b";ctx.strokeStyle=e.color;ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(x,y,18*scale,9*scale,a*.2,0,TAU);ctx.fill();ctx.stroke();ctx.fillStyle=e.color;ctx.beginPath();ctx.arc(x,y,3.5*scale,0,TAU);ctx.fill();
    if(W>700){ctx.fillStyle=e.color;ctx.fillText(e.name,x,y+20)}
    e.pulse*=.92;
  });ctx.restore();
}
function drawCognates(t){
  ctx.save();
  for(const s of shards)if(s.integrity>0)for(const rel of s.cognates.slice(0,2)){
    const p=project6(s.vec,t);const idx=Math.abs(parseInt(hash(rel.to),16))%ghosts.length;const g=ghosts[idx];const a=g.phase+t*.045,r=Math.min(W,H)*.2*g.ring;const q={x:W/2+Math.cos(a)*r,y:H/2+Math.sin(a)*r*.45};
    ctx.strokeStyle=rel.type==="BURNED_COGNATE"?"#ff7f7f20":"#72f6ff2b";ctx.setLineDash([3,6]);ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.stroke();
  }
  ctx.setLineDash([]);ctx.restore();
}
function drawShards(t){
  const rows=shards.filter(s=>s.integrity>0).map(s=>({s,p:project6(s.vec,t,1.5)})).sort((a,b)=>a.p.z-b.p.z);
  ctx.save();ctx.textAlign="center";ctx.font="9px ui-monospace,monospace";
  for(const {s,p} of rows){
    s.age+=.016;for(let i=0;i<6;i++)s.vec[i]+=s.vel[i]*.008;
    const locked=state.target===s,size=(locked?18:10+8*s.integrity)*p.p;
    ctx.save();ctx.translate(p.x,p.y);ctx.rotate(t*.35+parseInt(hash(s.id),16)%10);ctx.strokeStyle=s.status==="SURVIVOR"?"#92ff9d":s.status==="EMBER"?"#ffd86a":s.color;ctx.fillStyle=s.status==="ASH"?"#666":s.color+"28";ctx.lineWidth=locked?3:1.4;
    ctx.beginPath();for(let k=0;k<6;k++){const a=k/6*TAU,r=size*(k%2?1:.65);const x=Math.cos(a)*r,y=Math.sin(a)*r;(k===0?ctx.moveTo(x,y):ctx.lineTo(x,y))}ctx.closePath();ctx.fill();ctx.stroke();ctx.restore();
    if(locked||s.status!=="GENERATED"){ctx.fillStyle=s.status==="SURVIVOR"?"#aaffb2":"#e8dfff";ctx.fillText(s.id,p.x,p.y-size-7);ctx.fillStyle="#aaa";ctx.fillText(Math.max(0,s.integrity).toFixed(2)+" · "+s.uniqueWays.length+" ways",p.x,p.y+size+14)}
  }
  ctx.restore();
}
function drawSparks(now){
  for(let i=sparks.length-1;i>=0;i--){const s=sparks[i],age=(now-s.born)/1000;if(age>1.1){sparks.splice(i,1);continue}const c=project6([0,.2,0,0,0,0],state.firePhase);
    if(s.kind==="wave"){ctx.strokeStyle="rgba(255,188,85,"+(1-age)+")";ctx.lineWidth=2;ctx.beginPath();ctx.arc(c.x,c.y,age*Math.min(W,H)*.45,0,TAU);ctx.stroke()}
    else{const r=age*Math.min(W,H)*.35,x=c.x+Math.cos(s.a)*r,y=c.y+Math.sin(s.a)*r;ctx.fillStyle="rgba(255,135,66,"+(1-age)+")";ctx.fillRect(x,y,2,2)}
  }
}

function update(dt,t){
  state.firePhase+=dt*(.38+state.storm*.2);state.heat=Math.max(0,state.heat-dt*2.6);state.storm=lerp(state.storm,.25,dt*.25);
  state.spin+=dt*.03*(1+state.wayHits.AROUND*.002);
  for(const s of shards)if(s.integrity>0){s.vec[1]+=Math.sin(t*.6+parseInt(hash(s.id),16))*dt*.006}
  eventT+=dt;spawnT+=dt;
  if(eventT>11+randFrom("evt",state.epoch)*8){eventT=0;weirdEvent()}
  if(spawnT>8&&shards.filter(s=>s.integrity>0).length<5){spawnT=0;spawnCandidate()}
  profile.score=state.score;profile.epoch=state.epoch;profile.shardNo=state.shardNo;profile.music=state.music;profile.habits=state.habits;profile.survivors=state.survivors;profile.cognates=state.cognates;profile.fuzzball=state.fuzzball;
}
function draw(now){
  const t=state.firePhase;drawBackground(t);drawGhosts(t);drawCognates(t);drawFilaments(t);drawFire(t);drawShards(t);drawEyes(t);drawSparks(now);
  // central object label
  ctx.textAlign="center";ctx.font="900 12px ui-monospace,monospace";ctx.fillStyle="#fff7d9";ctx.fillText("W114",W/2,H/2+Math.min(W,H)*.115);
  ctx.font="9px ui-monospace,monospace";ctx.fillStyle="#b98fe0";ctx.fillText("projection orbit ∞ · object identity fixed",W/2,H/2+Math.min(W,H)*.135);
}

function hud(){
  ui("score").textContent=String(Math.round(state.score)).padStart(6,"0");ui("combo").textContent="COMBO ×"+state.combo;ui("heat").textContent=Math.round(state.heat);ui("embers").textContent=state.embers.length;ui("ash").textContent=state.ash.length;
  ui("object-id").textContent=state.target?.id||W114.objectId;ui("status").textContent=state.target?(state.target.status+" · "+state.activeWay):("EYE CENTERED · "+state.activeWay);
}
function renderLedger(){
  ui("eye-readout").innerHTML='<div class="eye-row">'+EYES.map(e=>'<span class="eye-chip '+(state.eyeRead[e.id]>.6?"hot":"")+'">'+e.name+" "+(state.eyeRead[e.id]||0).toFixed(2)+"</span>").join("")+"</div>";
  ui("ways-readout").innerHTML='<div class="way-row">'+ALL_WAYS.map(w=>'<span class="way-chip '+(w===state.activeWay?"hot":"")+'">'+w+" "+state.wayHits[w]+"</span>").join("")+"</div>";
  ui("ash-list").innerHTML=state.ash.slice(-18).map(x=>"<li><code>"+x.id+"</code> "+(x.label||x.kind||"")+"</li>").join("");
  ui("ember-list").innerHTML=[...state.embers,...state.survivors].slice(-18).map(x=>"<li><code>"+x.id+"</code> "+(x.label||x.kind||"")+"</li>").join("");
  ui("cognate-list").innerHTML=state.cognates.slice(-16).reverse().map(x=>"<li>"+x.from+" ↔ "+x.to+" · "+x.type+" · "+x.strength.toFixed(2)+"</li>").join("");
  ui("remainder-list").innerHTML=state.remainder.slice(-16).map(x=>"<li>"+x+"</li>").join("");
  ui("trace").innerHTML=state.trace.slice(-80).reverse().map(x=>"<li><b>"+x.op+"</b> · "+x.objectId+" · "+JSON.stringify(x.detail)+"</li>").join("");
}
function frame(now){
  const dt=Math.min(.05,(now-last)/1000);last=now;update(dt,now/1000);draw(now);hud();if(state.ledger)renderLedger();requestAnimationFrame(frame)
}

canvas.addEventListener("pointerdown",e=>{pointer={down:true,x:e.clientX,y:e.clientY,px:e.clientX,py:e.clientY,downAt:performance.now(),moved:false};canvas.setPointerCapture?.(e.pointerId);ui("hint").classList.add("hide")});
canvas.addEventListener("pointermove",e=>{if(!pointer.down)return;const dx=e.clientX-pointer.px,dy=e.clientY-pointer.py;pointer.px=e.clientX;pointer.py=e.clientY;if(Math.hypot(e.clientX-pointer.x,e.clientY-pointer.y)>6)pointer.moved=true;state.yaw+=dx*.006;state.pitch=clamp(state.pitch+dy*.006,-2,2);state.wayHits.SIDEWAYS++;state.wayHits.AROUND++;state.activeWay=Math.abs(dx)>Math.abs(dy)?"SIDEWAYS":dy<0?"UP":"DOWN"});
canvas.addEventListener("pointerup",e=>{if(!pointer.down)return;const held=performance.now()-pointer.downAt;if(held>650&&!pointer.moved)homeward();else if(!pointer.moved){selectAt(e.clientX,e.clientY);if(!state.target&&Math.hypot(e.clientX-W/2,e.clientY-H/2)<Math.min(W,H)*.18)hitTarget()}pointer.down=false});
canvas.addEventListener("dblclick",e=>{e.preventDefault();reverseProbe()});
canvas.addEventListener("wheel",e=>{e.preventDefault();const inward=e.deltaY<0;state.zoom=clamp(state.zoom*(inward?1.08:.92),.55,2.1);const w=inward?"INWARD":"OUTWARD";state.wayHits[w]++;state.activeWay=w},{passive:false});

addEventListener("keydown",e=>{const k=e.key.toLowerCase();if(e.code==="Space"){e.preventDefault();hitTarget()}else if(k==="h")homeward();else if(k==="b")branch();else if(k==="r")reverseProbe();else if(k==="m")toggleMusic();else if(k==="l")toggleLedger();else if(k==="w"){state.pitch-=.1;state.activeWay="UP"}else if(k==="s"){state.pitch+=.1;state.activeWay="DOWN"}else if(k==="a"){state.yaw-=.1;state.activeWay="SIDEWAYS"}else if(k==="d"){state.yaw+=.1;state.activeWay="SIDEWAYS"}else if(k==="f")state.activeWay="FORWARD";else if(k==="v")state.activeWay="BACKWARD"});

ui("pulse").onclick=()=>hitTarget();ui("scan").onclick=()=>{fiveEyes(state.target||nearestLiveShard(),"THROUGH");state.wayHits.THROUGH++;state.activeWay="THROUGH";trace("FIVE_EYES_SCAN",state.target?.id||W114.objectId,{simultaneous:true});shockwave("THROUGH")};
ui("music").onclick=toggleMusic;ui("home").onclick=homeward;ui("ledger-toggle").onclick=toggleLedger;ui("ledger-close").onclick=toggleLedger;
function toggleLedger(){state.ledger=!state.ledger;ui("ledger").hidden=!state.ledger;if(state.ledger)renderLedger()}
ui("reset").onclick=()=>{localStorage.removeItem("five-eyes-fermat-fire-v2");location.reload()};
ui("copy-state").onclick=async()=>{const text=JSON.stringify(exportState(),null,2);try{if(window.AndroidBridge?.copyText)window.AndroidBridge.copyText(text);else await navigator.clipboard.writeText(text)}catch{}};
ui("export-state").onclick=()=>{const text=JSON.stringify(exportState(),null,2)+"\n";if(window.AndroidBridge?.saveJson)window.AndroidBridge.saveJson("five-eyes-w114-state.json",text);else{const b=new Blob([text],{type:"application/json"}),u=URL.createObjectURL(b),a=document.createElement("a");a.href=u;a.download="five-eyes-w114-state.json";a.click();setTimeout(()=>URL.revokeObjectURL(u),500)}};
ui("import-state").onchange=async e=>{const f=e.target.files[0];if(!f)return;try{const p=JSON.parse(await f.text());if(p.schema!=="five-eyes-fermat-fire-game/v2")throw new Error("wrong schema");Object.assign(state,p.state);trace("IMPORT",W114.objectId,{source:f.name})}catch(err){showEvent("IMPORT REFUSED: "+err.message)}e.target.value=""};

function exportState(){return{schema:"five-eyes-fermat-fire-game/v2",authority:"game/research-control carrier only",w114:W114,state:{score:state.score,combo:state.combo,heat:state.heat,epoch:state.epoch,ash:state.ash,embers:state.embers,survivors:state.survivors,habits:state.habits,remainder:state.remainder,trace:state.trace,cognates:state.cognates,wayHits:state.wayHits,eyeRead:state.eyeRead,activeWay:state.activeWay},boundaries:["GAME_SCORE != MATHEMATICAL_EVIDENCE","COGNATE != IDENTITY","NEW_TO_ACTIVE_SEARCH != NEW_MATHEMATICAL_CYCLE","GENERATE != VERIFY != ADMIT","SOFTWARE_VERIFICATION != MATHEMATICAL_PROOF","VISUAL_PROJECTION_ORBIT != MATHEMATICAL_DIMENSION"]}}

window.FiveEyesFermatFire={exportState,spawnCandidate,hitTarget,homeward,branch,reverseProbe,W114,ALL_WAYS,EYES};

for(let i=0;i<4;i++)spawnCandidate();
trace("FREEZE",W114.objectId,{alpha:W114.alpha,target:W114.target,center:W114.center});
showEvent("FIVE EYES ONLINE · ALL_WAYS LIVE");
requestAnimationFrame(frame);
})();