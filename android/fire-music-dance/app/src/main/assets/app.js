(() => {
  "use strict";

  const UI_SCHEMA = "fire-music-dance-live-ui/v1";
  const COMMAND_SCHEMA = "fire-music-dance-command/v1";
  const STORAGE_KEY = "other-projects.fire-music-dance-live.v1";
  const ALL_WAYS = ["FORWARD","BACKWARD","UP","DOWN","SIDEWAYS","INWARD","OUTWARD","AROUND","THROUGH","REVERSE","BRANCH","HOMEWARD"];
  const TRIADS = ["DARK","MIDDLE","LIGHT"];
  const MOTIF = ["OBSERVE","BURN","REOBSERVE","REST"];
  const BOUNDARIES = [
    "GENERATE != VERIFY != ADMIT",
    "METHOD_TRANSFER != EVIDENCE_TRANSFER",
    "SOFTWARE_VERIFICATION != DOMAIN_PROOF",
    "RELATION != SUPPORT",
    "FAILED_REPRESENTATION != FAILED_OBJECT",
    "ATTACKABILITY != FALSITY",
    "MUSIC != TRUTH",
    "DANCE != TRUTH",
    "DELTA_ZERO_IS_LOCAL_NOT_GLOBAL",
    "UNKNOWN != ZERO",
    "OBJECT_IDENTITY_IS_INVARIANT",
    "COORDINATES_AND_CARRIERS_ARE_NEGOTIABLE"
  ];

  const $ = (id) => document.getElementById(id);
  const clone = (value) => JSON.parse(JSON.stringify(value));
  const nowIso = () => new Date().toISOString();
  const shortId = (id) => id ? `${id.slice(0,8)}…${id.slice(-6)}` : "—";

  function stable(value) {
    if (Array.isArray(value)) return value.map(stable);
    if (value && typeof value === "object") {
      return Object.fromEntries(Object.keys(value).sort().map(k => [k, stable(value[k])]));
    }
    return value;
  }

  async function sha256(value) {
    const bytes = new TextEncoder().encode(JSON.stringify(stable(value)));
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2,"0")).join("");
  }

  function getPath(root, path) {
    return path.split(".").reduce((cur, part) => {
      if (!cur || typeof cur !== "object" || !(part in cur)) throw new Error(`Unknown path: ${path}`);
      return cur[part];
    }, root);
  }

  function setPath(root, path, value) {
    const parts = path.split(".");
    let cur = root;
    for (const part of parts.slice(0,-1)) {
      if (!cur || typeof cur[part] !== "object") throw new Error(`Unknown path: ${path}`);
      cur = cur[part];
    }
    const leaf = parts[parts.length - 1];
    if (!(leaf in cur)) throw new Error(`Unknown path: ${path}`);
    cur[leaf] = value;
  }

  function parseValue(text) {
    try { return JSON.parse(text); } catch { return text; }
  }

  function defaultState() {
    const surface = {
      system: { depth: 2, temperature: 0, carrier: "seed" },
      observer: { mode: "visible" }
    };
    return {
      schema: UI_SCHEMA,
      authority: "method-only",
      objectId: "Object:live-fire-field",
      rootSurface: clone(surface),
      invariants: { "system.carrier": "seed", "observer.mode": "visible" },
      current: {
        candidateId: "root-pending",
        parentId: null,
        stage: "OBSERVE",
        triad: "MIDDLE",
        verification: "GENERATED",
        surface,
        knowledge: {},
        evidenceRefs: [],
        provenance: ["user:FIRE+Music+Dance", "ui:live-field"],
        mutation: null,
        remainder: [],
        admitted: false,
        resting: false
      },
      bins: { ash: [], smoke: [], embers: [], survivors: [] },
      memory: { experiences: [], signatureCounts: {} },
      dance: { lastDirection: "HOMEWARD", trail: [] },
      music: { bpm: 108, playing: false, pulse: 0, beat: 1, bar: 1, operator: "OBSERVE" },
      delta: { status: "UNKNOWN", changedPaths: [], protectedViolations: [], unresolved: [], note: "Not compared yet" },
      trace: [],
      boundaries: [...BOUNDARIES],
      updatedAt: nowIso()
    };
  }

  let state = defaultState();
  let musicTimer = null;

  async function initializeRootId() {
    if (state.current.candidateId === "root-pending") {
      state.current.candidateId = await sha256({objectId: state.objectId, surface: state.rootSurface, invariants: state.invariants, provenance: state.current.provenance});
      save();
    }
  }

  function save() {
    state.updatedAt = nowIso();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    $("persist-status").textContent = "Saved locally";
  }

  async function load() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        if (parsed.schema === UI_SCHEMA && parsed.objectId && parsed.current) state = parsed;
      } catch { /* keep default */ }
    }
    state.music.playing = false;
    await initializeRootId();
    renderAll();
  }

  function addTrace(op, detail = {}) {
    state.trace.push({ no: state.trace.length + 1, at: nowIso(), op, candidateId: state.current.candidateId, stage: state.current.stage, verification: state.current.verification, detail: clone(detail) });
    if (state.trace.length > 250) state.trace = state.trace.slice(-250);
    save();
  }

  function invariantViolations(surface) {
    const violations = [];
    for (const [path, expected] of Object.entries(state.invariants)) {
      try { if (JSON.stringify(getPath(surface,path)) !== JSON.stringify(expected)) violations.push(path); }
      catch { violations.push(path); }
    }
    return violations;
  }

  function mutationSignature(m) {
    return `${m.path}|${m.operator}|${m.direction}|${typeof m.before}->${typeof m.after}`;
  }

  function recordExperience(outcome) {
    const m = state.current.mutation;
    if (!m) return;
    const signature = mutationSignature(m);
    const beforeCount = state.memory.signatureCounts[signature] || 0;
    const exp = { signature, operator: m.operator, direction: m.direction, outcome, candidateId: state.current.candidateId, noveltyBefore: 1/(1+beforeCount), at: nowIso() };
    state.memory.experiences.push(exp);
    state.memory.signatureCounts[signature] = beforeCount + 1;
  }

  function routeRecommendation() {
    const groups = new Map();
    for (const exp of state.memory.experiences) {
      const key = `${exp.operator}|${exp.direction}`;
      const row = groups.get(key) || {operator:exp.operator,direction:exp.direction,ember:0,ash:0,smoke:0,count:0};
      row.count += 1;
      if (exp.outcome === "EMBER") row.ember += 1;
      if (exp.outcome === "ASH") row.ash += 1;
      if (exp.outcome === "SMOKE") row.smoke += 1;
      groups.set(key,row);
    }
    const rows = [...groups.values()].map(row => ({...row,score:(2*row.ember)-row.ash-(.25*row.smoke)}));
    rows.sort((a,b) => b.score-a.score || a.count-b.count || a.operator.localeCompare(b.operator));
    return rows[0] || null;
  }

  async function mutate({path, after, operator="CHANGE_ONE", direction="SIDEWAYS", note="ui"}) {
    if (state.current.resting) throw new Error("Candidate is sleeping/resting. Wake it first.");
    if (!ALL_WAYS.includes(direction)) throw new Error(`Unsupported direction: ${direction}`);
    const before = clone(getPath(state.current.surface,path));
    if (JSON.stringify(before) === JSON.stringify(after)) throw new Error("One-degree mutation must actually change the value.");
    const surface = clone(state.current.surface);
    setPath(surface,path,clone(after));
    const parentId = state.current.candidateId;
    const mutation = {path,before,after:clone(after),operator,direction};
    const candidateId = await sha256({schema:"fire-music-dance-dynamic-field/v1",objectId:state.objectId,parentId,surface,mutation,triad:state.current.triad});
    state.current = {
      ...state.current,
      candidateId,
      parentId,
      stage:"FUEL",
      verification:"GENERATED",
      surface,
      mutation,
      remainder:[],
      admitted:false,
      resting:false,
      provenance:[...state.current.provenance,`MUTATE:${note}`]
    };
    state.delta = {status:"UNKNOWN",changedPaths:[],protectedViolations:[],unresolved:[],note:"New candidate not yet compared"};
    addTrace("GENERATE", {mutation});
    renderAll();
    return state.current;
  }

  function burn(status, observation, evidenceRefs=[]) {
    if (!observation.trim()) throw new Error("Burn requires an explicit observation.");
    if (!["PASS","FAIL","UNRESOLVED"].includes(status)) throw new Error("Unsupported burn status.");
    if (status === "FAIL") {
      state.current.stage = "ASH";
      state.current.verification = "REFUTED_LOCAL";
      state.current.remainder = [observation];
      state.bins.ash.push(snapshotBin("ASH",observation));
      recordExperience("ASH");
    } else if (status === "UNRESOLVED") {
      state.current.stage = "SMOKE";
      state.current.verification = "UNRESOLVED";
      state.current.remainder = [observation];
      state.bins.smoke.push(snapshotBin("SMOKE",observation));
      recordExperience("SMOKE");
    } else {
      state.current.stage = "EMBER";
      state.current.verification = "VERIFIED_LOCAL";
      state.current.remainder = [];
      state.bins.embers.push(snapshotBin("EMBER",observation));
      recordExperience("EMBER");
    }
    state.current.evidenceRefs = [...state.current.evidenceRefs, ...evidenceRefs.filter(Boolean)];
    addTrace("BURN", {status,observation,evidenceRefs});
    renderAll();
  }

  function snapshotBin(kind,note) {
    return {kind,candidateId:state.current.candidateId,note,at:nowIso(),mutation:clone(state.current.mutation)};
  }

  function markSurvivor() {
    if (state.current.stage !== "EMBER" || state.current.verification !== "VERIFIED_LOCAL") throw new Error("Only a locally verified EMBER can become SURVIVOR.");
    state.current.stage = "SURVIVOR";
    state.bins.survivors.push(snapshotBin("SURVIVOR","locally verified survivor"));
    addTrace("SURVIVOR",{});
    renderAll();
  }

  async function reconstitute(knowledgePatch) {
    if (state.current.stage !== "SURVIVOR") throw new Error("RECONSTITUTE requires SURVIVOR.");
    const parentId = state.current.candidateId;
    state.current.knowledge = {...state.current.knowledge,...knowledgePatch};
    state.current.parentId = parentId;
    state.current.candidateId = await sha256({objectId:state.objectId,parentId,surface:state.current.surface,knowledge:state.current.knowledge,stage:"RECONSTITUTE"});
    state.current.stage = "RECONSTITUTE";
    state.current.mutation = null;
    addTrace("RECONSTITUTE",{knowledgePatch});
    renderAll();
  }

  async function homeward(note="ui") {
    const parentId = state.current.candidateId;
    const candidateId = await sha256({objectId:state.objectId,rootSurface:state.rootSurface,knowledge:state.current.knowledge,evidenceRefs:state.current.evidenceRefs,from:parentId});
    state.current = {...state.current,candidateId,parentId,stage:"HOMEWARD",triad:"MIDDLE",surface:clone(state.rootSurface),mutation:null,resting:false,provenance:[...state.current.provenance,`HOMEWARD:${note}`]};
    state.dance.lastDirection = "HOMEWARD";
    state.dance.trail.push({direction:"HOMEWARD",at:nowIso(),note:"execute"});
    addTrace("HOMEWARD",{from:parentId,toRootSurface:true});
    renderAll();
  }

  function sleep() {
    state.current.stage = "SLEEP";
    state.current.resting = true;
    stopMusic();
    addTrace("SLEEP",{});
    renderAll();
  }

  function wake(trigger) {
    if (!state.current.resting) throw new Error("Candidate is not sleeping/resting.");
    if (!trigger.trim()) throw new Error("Wake requires a new trigger.");
    state.current.stage = "REOBSERVE";
    state.current.resting = false;
    state.current.provenance.push(`WAKE:${trigger}`);
    addTrace("WAKE",{trigger});
    renderAll();
  }

  function dance(direction,note="ui") {
    if (!ALL_WAYS.includes(direction)) throw new Error(`Unsupported direction: ${direction}`);
    state.dance.lastDirection = direction;
    state.dance.trail.push({direction,at:nowIso(),note});
    if (state.dance.trail.length > 80) state.dance.trail = state.dance.trail.slice(-80);
    addTrace("DANCE",{direction,note});
    if (window.AndroidBridge && typeof window.AndroidBridge.vibrate === "function") {
      window.AndroidBridge.vibrate(direction === "HOMEWARD" ? 60 : 24);
    }
    renderAll();
  }

  function setTriad(triad,note="ui") {
    if (!TRIADS.includes(triad)) throw new Error(`Unsupported triad: ${triad}`);
    state.current.triad = triad;
    addTrace("SET_TRIAD",{triad,note});
    renderAll();
  }

  function compare(paths=["system.depth","system.carrier","observer.mode"], unresolved=[]) {
    const changedPaths=[];
    const protectedViolations=invariantViolations(state.current.surface);
    for (const path of paths) {
      try { if (JSON.stringify(getPath(state.rootSurface,path)) !== JSON.stringify(getPath(state.current.surface,path))) changedPaths.push(path); }
      catch { protectedViolations.push(path); }
    }
    let status,note;
    if (unresolved.length || protectedViolations.length) { status="UNKNOWN"; note="Unresolved observation or invariant/measurement gap remains."; }
    else if (changedPaths.length) { status="DELTA_NONZERO"; note="Consequential difference observed in declared comparison scope."; }
    else { status="DELTA_ZERO"; note="No consequential difference in declared tested scope."; }
    state.delta={status,changedPaths,protectedViolations:[...new Set(protectedViolations)].sort(),unresolved,note};
    addTrace("COMPARE",{paths,delta:state.delta});
    renderAll();
    return state.delta;
  }

  function closeNoChange() {
    if (state.delta.status !== "DELTA_ZERO") throw new Error("NO_CHANGE is permitted only for DELTA_ZERO.");
    state.current.stage="CLOSED";
    state.current.resting=true;
    stopMusic();
    addTrace("DELTA_ZERO_NO_CHANGE",{delta:state.delta});
    renderAll();
  }

  function pulseMusic() {
    state.music.pulse += 1;
    state.music.beat = ((state.music.pulse-1)%4)+1;
    state.music.bar = Math.floor((state.music.pulse-1)/4)+1;
    state.music.operator = MOTIF[(state.music.pulse-1)%MOTIF.length];
    const wave=$("field-visual").querySelector(".music-wave");
    wave.classList.remove("pulse");
    void wave.offsetWidth;
    wave.classList.add("pulse");
    setTimeout(()=>wave.classList.remove("pulse"),Math.min(300,(60000/state.music.bpm)*.7));
    addTrace("MUSIC_PULSE",{bpm:state.music.bpm,bar:state.music.bar,beat:state.music.beat,operator:state.music.operator});
    if (window.AndroidBridge && typeof window.AndroidBridge.vibrate === "function") {
      window.AndroidBridge.vibrate(state.music.beat === 1 ? 34 : 12);
    }
    renderAll();
  }

  function startMusic() {
    stopMusic(false);
    state.music.playing=true;
    musicTimer=setInterval(pulseMusic,60000/state.music.bpm);
    addTrace("MUSIC_START",{bpm:state.music.bpm});
    renderAll();
  }

  function stopMusic(trace=true) {
    if (musicTimer) clearInterval(musicTimer);
    musicTimer=null;
    const wasPlaying=state.music.playing;
    state.music.playing=false;
    if (trace && wasPlaying) addTrace("MUSIC_STOP",{});
  }

  function toggleMusic() { state.music.playing ? stopMusic() : startMusic(); renderAll(); }

  function setBpm(bpm) {
    state.music.bpm=Math.max(40,Math.min(220,Number(bpm)||108));
    if (state.music.playing) startMusic(); else { save(); renderAll(); }
  }

  async function applyCommandPacket(packet) {
    if (!packet || packet.schema !== COMMAND_SCHEMA) throw new Error(`Command schema must be ${COMMAND_SCHEMA}`);
    const commands = Array.isArray(packet.commands) ? packet.commands : [packet];
    for (const cmd of commands) {
      switch (cmd.command) {
        case "SET_TRIAD": setTriad(cmd.triad,"bridge"); break;
        case "DANCE": dance(cmd.direction,"bridge"); break;
        case "MUTATE": await mutate({path:cmd.path,after:cmd.after,operator:cmd.operator||"CHANGE_ONE",direction:cmd.direction||"SIDEWAYS",note:"bridge"}); break;
        case "BURN": burn(cmd.status,cmd.observation||"bridge observation",cmd.evidenceRefs||[]); break;
        case "SURVIVOR": markSurvivor(); break;
        case "RECONSTITUTE": await reconstitute(cmd.knowledgePatch||{}); break;
        case "HOMEWARD": await homeward("bridge"); break;
        case "SLEEP": sleep(); break;
        case "WAKE": wake(cmd.trigger||"bridge trigger"); break;
        case "COMPARE": compare(cmd.paths||["system.depth","system.carrier","observer.mode"],cmd.unresolved||[]); break;
        default: throw new Error(`Unsupported bridge command: ${cmd.command}`);
      }
    }
    addTrace("BRIDGE_PACKET_APPLIED",{commandCount:commands.length});
    renderAll();
  }

  function bridgeSnapshot() {
    return {schema:"fire-music-dance-bridge-state/v1",uiSchema:UI_SCHEMA,authority:state.authority,objectId:state.objectId,current:clone(state.current),bins:clone(state.bins),memory:clone(state.memory),dance:clone(state.dance),music:clone(state.music),delta:clone(state.delta),trace:clone(state.trace),boundaries:[...BOUNDARIES],updatedAt:state.updatedAt};
  }

  async function copyText(text) {
    if (window.AndroidBridge && typeof window.AndroidBridge.copyText === "function") {
      window.AndroidBridge.copyText(text);
      return;
    }
    await navigator.clipboard.writeText(text);
  }

  function downloadJson(name,data) {
    const encoded=JSON.stringify(data,null,2)+"\n";
    if (window.AndroidBridge && typeof window.AndroidBridge.saveJson === "function") {
      window.AndroidBridge.saveJson(name,encoded);
      return;
    }
    const blob=new Blob([encoded],{type:"application/json"});
    const url=URL.createObjectURL(blob);
    const a=document.createElement("a"); a.href=url; a.download=name; a.click();
    setTimeout(()=>URL.revokeObjectURL(url),500);
  }

  function renderWayLabels() {
    const group=$("way-labels");
    group.innerHTML="";
    const cx=380,cy=250,r=215;
    ALL_WAYS.forEach((way,i)=>{
      const angle=(-Math.PI/2)+(i/ALL_WAYS.length)*Math.PI*2;
      const x=cx+Math.cos(angle)*r, y=cy+Math.sin(angle)*r;
      const g=document.createElementNS("http://www.w3.org/2000/svg","g");
      g.setAttribute("class",`way-label${state.dance.lastDirection===way?" active":""}`);
      g.setAttribute("transform",`translate(${x.toFixed(1)} ${y.toFixed(1)})`);
      const c=document.createElementNS("http://www.w3.org/2000/svg","circle"); c.setAttribute("r","16");
      const t=document.createElementNS("http://www.w3.org/2000/svg","text"); t.setAttribute("y","3.5"); t.textContent=way.slice(0,3);
      g.append(c,t); group.appendChild(g);
    });
  }

  function renderBins() {
    const config=[
      ["ash","ash-list","ash-count"], ["smoke","smoke-list","smoke-count"],
      ["embers","ember-list","ember-count"], ["survivors","survivor-list","survivor-count"]
    ];
    for (const [key,listId,countId] of config) {
      const rows=state.bins[key]||[];
      $(countId).textContent=rows.length;
      $(listId).innerHTML=rows.slice(-12).reverse().map(row=>`<li title="${escapeHtml(row.note||"")}"><code>${shortId(row.candidateId)}</code> ${escapeHtml(row.note||"")}</li>`).join("");
    }
  }

  function escapeHtml(value) { return String(value).replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c])); }

  function renderTrace() {
    $("trace-list").innerHTML=state.trace.slice(-80).reverse().map(row=>{
      const detail=Object.keys(row.detail||{}).length?` <code>${escapeHtml(JSON.stringify(row.detail))}</code>`:"";
      return `<li><strong>${escapeHtml(row.op)}</strong> · ${escapeHtml(row.stage||"")} · <span>${escapeHtml(new Date(row.at).toLocaleTimeString())}</span>${detail}</li>`;
    }).join("");
  }

  function renderDance() {
    document.querySelectorAll("#dance-pad button").forEach(btn=>btn.classList.toggle("active",btn.dataset.direction===state.dance.lastDirection));
    $("dance-trail").innerHTML=state.dance.trail.slice(-20).reverse().map(row=>`<li><strong>${escapeHtml(row.direction)}</strong> <span>${escapeHtml(row.note||"")}</span></li>`).join("");
  }

  function renderAll() {
    $("field-visual").dataset.triad=state.current.triad;
    $("field-visual").dataset.stage=state.current.stage;
    $("stage-badge").textContent=state.current.stage;
    $("now-stage").textContent=state.current.stage;
    $("now-triad").textContent=state.current.triad;
    $("now-verification").textContent=state.current.verification;
    $("now-delta").textContent=state.delta.status;
    $("now-music").textContent=state.music.playing?`${state.music.bpm} BPM · ${state.music.operator}`:"Stopped";
    $("now-dance").textContent=state.dance.lastDirection;
    $("candidate-id").textContent=state.current.candidateId;
    $("surface-view").textContent=JSON.stringify(state.current.surface,null,2);
    document.querySelectorAll("[data-triad]").forEach(btn=>{ if(btn.tagName==="BUTTON") btn.classList.toggle("selected",btn.dataset.triad===state.current.triad); });
    $("music-bpm").value=state.music.bpm; $("music-bpm-output").textContent=state.music.bpm;
    $("music-bar").textContent=state.music.bar; $("music-beat").textContent=state.music.beat; $("music-operator").textContent=state.music.operator;
    $("music-toggle").textContent=state.music.playing?"Stop music":"Start music";
    const rec=routeRecommendation();
    $("route-recommendation").textContent=rec?`${rec.operator} · ${rec.direction} (score ${rec.score.toFixed(2)})`:"No experience yet";
    if (state.current.mutation) {
      const sig=mutationSignature(state.current.mutation), count=state.memory.signatureCounts[sig]||0;
      $("novelty-display").textContent=`Novelty: ${(1/(1+count)).toFixed(3)} · repetitions ${count}`;
    } else $("novelty-display").textContent="Novelty: —";
    $("mark-survivor").disabled=!(state.current.stage==="EMBER"&&state.current.verification==="VERIFIED_LOCAL");
    $("reconstitute").disabled=state.current.stage!=="SURVIVOR";
    $("sleep").disabled=state.current.resting;
    $("wake").disabled=!state.current.resting;
    $("delta-strip").dataset.delta=state.delta.status;
    $("delta-label").textContent=`Δ ${state.delta.status.replace("DELTA_","")}`;
    $("delta-note").textContent=state.delta.note;
    $("close-no-change").disabled=state.delta.status!=="DELTA_ZERO";
    renderWayLabels(); renderBins(); renderTrace(); renderDance(); save();
  }

  function buildControls() {
    const directionSelect=$("mutation-direction");
    directionSelect.innerHTML=ALL_WAYS.map(x=>`<option value="${x}">${x}</option>`).join("");
    directionSelect.value="SIDEWAYS";
    const pad=$("dance-pad");
    pad.innerHTML=ALL_WAYS.map(x=>`<button type="button" data-direction="${x}">${x}</button>`).join("");
    pad.addEventListener("click",e=>{ const b=e.target.closest("button[data-direction]"); if(b) dance(b.dataset.direction); });
  }

  function errorToStatus(error) { $("bridge-status").textContent=error instanceof Error?error.message:String(error); $("bridge-status").style.color="var(--danger)"; }
  function okStatus(message) { $("bridge-status").textContent=message; $("bridge-status").style.color="var(--ok)"; }

  function bind() {
    document.querySelectorAll(".triad-controls button[data-triad]").forEach(btn=>btn.addEventListener("click",()=>setTriad(btn.dataset.triad)));
    $("apply-mutation").addEventListener("click",async()=>{ try{await mutate({path:$("mutation-path").value,after:parseValue($("mutation-after").value),operator:$("mutation-operator").value||"CHANGE_ONE",direction:$("mutation-direction").value});okStatus("One-degree candidate generated.");}catch(e){errorToStatus(e);} });
    $("burn-fail").addEventListener("click",()=>{try{burn("FAIL",$("burn-observation").value,[$("burn-evidence").value].filter(Boolean));}catch(e){errorToStatus(e);}});
    $("burn-unresolved").addEventListener("click",()=>{try{burn("UNRESOLVED",$("burn-observation").value,[$("burn-evidence").value].filter(Boolean));}catch(e){errorToStatus(e);}});
    $("burn-pass").addEventListener("click",()=>{try{burn("PASS",$("burn-observation").value,[$("burn-evidence").value].filter(Boolean));}catch(e){errorToStatus(e);}});
    $("mark-survivor").addEventListener("click",()=>{try{markSurvivor();}catch(e){errorToStatus(e);}});
    $("reconstitute").addEventListener("click",async()=>{try{await reconstitute({lesson:$("knowledge-note").value||"survived bounded burn"});okStatus("Reconstituted from survivor.");}catch(e){errorToStatus(e);}});
    $("music-toggle").addEventListener("click",toggleMusic); $("music-step").addEventListener("click",pulseMusic); $("music-bpm").addEventListener("input",e=>setBpm(e.target.value));
    $("homeward").addEventListener("click",async()=>{try{await homeward();}catch(e){errorToStatus(e);}});
    $("sleep").addEventListener("click",()=>{try{sleep();}catch(e){errorToStatus(e);}});
    $("wake").addEventListener("click",()=>{try{wake("human wake control");}catch(e){errorToStatus(e);}});
    $("compare-root").addEventListener("click",()=>compare()); $("close-no-change").addEventListener("click",()=>{try{closeNoChange();}catch(e){errorToStatus(e);}});
    $("copy-state").addEventListener("click",async()=>{try{await copyText(JSON.stringify(bridgeSnapshot(),null,2));okStatus("State copied. Paste it into ChatGPT so we operate on this exact visible state.");}catch(e){errorToStatus(e);}});
    $("download-state").addEventListener("click",()=>downloadJson(`fire-live-state-${Date.now()}.json`,bridgeSnapshot()));
    $("import-state").addEventListener("change",async e=>{try{const file=e.target.files[0];if(!file)return;const packet=JSON.parse(await file.text());if(packet.schema==="fire-music-dance-bridge-state/v1"&&packet.uiSchema===UI_SCHEMA){state={...state,...packet,current:packet.current,bins:packet.bins,memory:packet.memory,dance:packet.dance,music:{...packet.music,playing:false},delta:packet.delta,trace:packet.trace,boundaries:[...BOUNDARIES]};save();renderAll();okStatus("Bridge state imported.");}else if(packet.schema===UI_SCHEMA){state=packet;state.music.playing=false;save();renderAll();okStatus("Full UI state imported.");}else throw new Error("Unsupported state schema.");}catch(err){errorToStatus(err);}finally{e.target.value="";}});
    $("apply-command").addEventListener("click",async()=>{try{const p=JSON.parse($("command-input").value);await applyCommandPacket(p);okStatus("Command packet applied.");}catch(e){errorToStatus(e);}});
    $("copy-command-template").addEventListener("click",async()=>{const template={schema:COMMAND_SCHEMA,commands:[{command:"DANCE",direction:"INWARD"},{command:"MUTATE",path:"system.depth",after:3,operator:"DEEPEN",direction:"INWARD"},{command:"BURN",status:"UNRESOLVED",observation:"record exact observation",evidenceRefs:[]}]};try{await copyText(JSON.stringify(template,null,2));okStatus("Command template copied.");}catch(e){errorToStatus(e);}});
    $("reset-all").addEventListener("click",async()=>{if(confirm("Reset this browser's FIRE live state?")){stopMusic(false);localStorage.removeItem(STORAGE_KEY);state=defaultState();await initializeRootId();addTrace("RESET",{});renderAll();}});
    $("clear-trace-view").addEventListener("click",()=>$("trace-list").toggleAttribute("hidden"));
  }

  window.FireMusicDanceLive = { getState:()=>clone(state), bridgeSnapshot, applyCommandPacket, compare, mutate, burn, dance, homeward, setTriad, schemas:{UI_SCHEMA,COMMAND_SCHEMA} };

  buildControls(); bind(); load();
})();