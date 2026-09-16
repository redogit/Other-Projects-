import { applyMove, compareStates, materializeTrajectory } from './core.mjs';
import { sampleS3, sampleTesseractBoundary } from './geometry.mjs';
import { DEFAULT_OBSERVER, normalizeObserver, projectPair } from './observer.mjs';
import { makeObserverField } from './observer-field.mjs';
import {
  OPERATOR_VERSION,
  makeExperience, classifyExperience, appendExperience, replayExperience, reframeExperience,
  findLongestPrefixParent, rebuildExperienceGraph
} from './experience.mjs';
import { LocalExperienceStore } from './storage.mjs';
import { renderScene, formatInspection } from './render.mjs';
import { deriveSuggestionDataset, trainSuggestionModel, suggestNextMove } from './suggest.mjs';

const geometries = new Map([
  ['s3-sample', sampleS3()],
  ['tesseract-boundary', sampleTesseractBoundary()]
]);
const store = new LocalExperienceStore(window.localStorage);
let geometryId = 's3-sample';
let viewShell = 's3-sample';
let origin, mirror, live, previousLive;
let observer = DEFAULT_OBSERVER;
let graph = Object.freeze({ events: Object.freeze([]), invariants: Object.freeze([]) });

const $ = id => document.getElementById(id);
const scene = $('scene'), inspection = $('inspection'), status = $('status'), savedSelect = $('saved-events'), suggestionOutput = $('suggestion');

function trajectoryFor(id, actions = []) {
  const geometry = geometries.get(id);
  if (!geometry) throw new RangeError(`unknown geometry: ${id}`);
  return materializeTrajectory(geometry.points4, actions);
}

function adoptTrajectory(id, trajectory) {
  geometryId = id;
  ({ origin, mirror, live, previous: previousLive } = trajectory);
}

function observerFromControls() {
  return normalizeObserver({
    yaw: Number($('yaw').value), pitch: Number($('pitch').value), roll: Number($('roll').value),
    wPerspective: Number($('w-perspective').value)
  });
}

function render() {
  const pair = projectPair(live, mirror, observer);
  renderScene(scene, pair);
  const comparison = compareStates(live, mirror);
  const latest = live.actions.at(-1) ?? null;
  inspection.textContent = formatInspection({
    shell: viewShell,
    actionCount: live.actions.length,
    latestMove: latest,
    comparison,
    originDisplacement: compareStates(live, origin).maxAbsDelta,
    latestStepChange: compareStates(live, previousLive).maxAbsDelta,
    observer
  });
}

function currentFieldSnapshot() {
  const geometry = geometries.get(geometryId);
  const field = makeObserverField({ points4: geometry.points4, sourceDimension: 4, densityId: `${geometry.id}:${geometry.points4.length}` });
  return {
    version: field.version, taskVersion: field.taskVersion, densityId: field.densityId,
    calibrations: field.observers.filter(o => o.calibration !== 0).map(o => ({ observerId: o.id, calibration: o.calibration }))
  };
}

function currentRecord() {
  const familyId = geometryId;
  const parentId = findLongestPrefixParent(graph, familyId, live.actions);
  return makeExperience({
    initialState: geometryId,
    mirrorId: `mirror:${geometryId}`,
    shell: viewShell,
    actions: live.actions,
    observer,
    observerField: currentFieldSnapshot(),
    checkpoints: live.actions.length === 0
      ? [{ actionIndex: 0, label: 'origin' }]
      : [{ actionIndex: 0, label: 'origin' }, { actionIndex: live.actions.length, label: 'current' }],
    comparisons: {
      obligation: 'live-vs-mirror',
      againstMirror: (() => { const c = compareStates(live, mirror); return { equal: c.equal, maxAbsDelta: c.maxAbsDelta }; })(),
      againstPrevious: (() => { const c = compareStates(live, previousLive); return { equal: c.equal, maxAbsDelta: c.maxAbsDelta }; })()
    },
    relations: { familyId, parentId, relatedIds: parentId ? [parentId] : [] },
    provenance: { source: 'S1 Models Lab Experiment 0', localOnly: true }
  });
}

function refreshSaved(rows = store.list()) {
  savedSelect.replaceChildren();
  if (rows.length === 0) savedSelect.append(new Option('No saved events', ''));
  else for (const row of rows) {
    savedSelect.append(new Option(`${row.event.id} · ${row.event.actions.length} move(s) · x${row.occurrences}`, row.event.id));
  }
}

function currentSuggestionContext() {
  return {
    initialState: geometryId,
    mirrorId: `mirror:${geometryId}`,
    operatorVersion: OPERATOR_VERSION,
    actions: live.actions
  };
}

function rebuildGraphFromStore(rows = store.list()) {
  graph = rebuildExperienceGraph(rows.map(row => row.event));
  return rows;
}

function selectedRow() {
  return store.list().find(row => row.event.id === savedSelect.value) ?? null;
}

for (const button of document.querySelectorAll('[data-plane][data-degrees]')) {
  button.addEventListener('click', () => {
    previousLive = live;
    live = applyMove(live, { plane: button.dataset.plane, degrees: Number(button.dataset.degrees) });
    render();
  });
}

document.addEventListener('keydown', event => {
  if (['INPUT','SELECT','TEXTAREA'].includes(document.activeElement?.tagName)) return;
  const map = { q:['xw',1], a:['xw',-1], w:['yw',1], s:['yw',-1], e:['zw',1], d:['zw',-1] };
  const move = map[event.key.toLowerCase()];
  if (!move) return;
  event.preventDefault();
  previousLive = live;
  live = applyMove(live, { plane: move[0], degrees: move[1] });
  render();
});

$('shell').addEventListener('change', event => {
  const nextShell = event.target.value;
  try {
    if (nextShell !== 'comparison' && nextShell !== geometryId) {
      const nextTrajectory = trajectoryFor(nextShell, live.actions);
      adoptTrajectory(nextShell, nextTrajectory);
    }
    viewShell = nextShell;
    render();
    status.textContent = 'Reference surface reframed; the action trajectory was preserved.';
  } catch (error) {
    event.target.value = viewShell;
    status.textContent = `Reframe refused; live trajectory preserved: ${error.message}`;
  }
});

for (const id of ['yaw','pitch','roll','w-perspective']) {
  $(id).addEventListener('input', () => {
    try { observer = observerFromControls(); render(); }
    catch (error) { status.textContent = `Observer update refused: ${error.message}`; }
  });
}

$('reframe').addEventListener('click', () => {
  try {
    const nextObserver = observerFromControls();
    const row = selectedRow();
    if (row) {
      const framed = reframeExperience(row.event, nextObserver, geometries);
      status.textContent = `Reframed ${framed.sourceId}; source record unchanged.`;
    } else {
      status.textContent = 'Reframed the current live event; no saved source was modified.';
    }
    observer = nextObserver;
    render();
  } catch (error) { status.textContent = `Reframe refused: ${error.message}`; }
});

$('save').addEventListener('click', () => {
  try {
    const record = currentRecord();
    const classification = classifyExperience(record, graph);
    graph = appendExperience(graph, record, classification);
    store.save(record);
    const rows = store.list();
    refreshSaved(rows);
    savedSelect.value = record.id;
    status.textContent = `Saved ${record.id} as ${classification}.`;
  } catch (error) { status.textContent = `Save refused: ${error.message}`; }
});

$('replay').addEventListener('click', () => {
  try {
    const row = selectedRow();
    if (!row) { status.textContent = 'Choose a saved event to replay.'; return; }
    const candidate = replayExperience(row.event, geometries);
    const nextTrajectory = trajectoryFor(row.event.initialState, row.event.actions);
    if (!compareStates(candidate, nextTrajectory.live).equal) throw new RangeError('replay disagrees with trajectory materialization');
    const nextObserver = normalizeObserver(row.event.observer);

    adoptTrajectory(row.event.initialState, nextTrajectory);
    viewShell = row.event.shell;
    $('shell').value = viewShell;
    observer = nextObserver;
    for (const id of ['yaw','pitch','roll']) $(id).value = observer[id];
    $('w-perspective').value = observer.wPerspective;
    status.textContent = `Replayed ${row.event.id} exactly.`;
    render();
  } catch (error) { status.textContent = `Replay refused; live state preserved: ${error.message}`; }
});

$('suggest').addEventListener('click', () => {
  try {
    const rows = store.list();
    const dataset = deriveSuggestionDataset(rows.map(row => row.event));
    const model = trainSuggestionModel(dataset);
    const result = suggestNextMove(model, currentSuggestionContext());
    const signedDegrees = `${result.move.degrees > 0 ? '+' : ''}${result.move.degrees}°`;
    const basis = result.kind === 'observed'
      ? `observed in ${result.provenance.sourceExperienceIds.length} preserved unique replay path(s)`
      : 'generated by the deterministic fallback because this exact prefix has no preserved continuation';
    suggestionOutput.textContent = `${result.kind === 'observed' ? 'Observed' : 'Generated'} suggestion: ${result.move.plane} ${signedDegrees}; ${basis}. Suggestion only; current state and saved experience are unchanged.`;
  } catch (error) {
    suggestionOutput.textContent = `Suggestion refused: ${error.message}`;
  }
});

$('export').addEventListener('click', () => {
  try {
    const blob = new Blob([store.exportJson()], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 's1-experiences.json'; a.click(); URL.revokeObjectURL(url);
  } catch (error) { status.textContent = `Export refused: ${error.message}`; }
});

$('import-file').addEventListener('change', async event => {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    const count = store.importJson(await file.text());
    const rows = rebuildGraphFromStore();
    refreshSaved(rows);
    status.textContent = `Imported ${count} validated event row(s).`;
  } catch (error) { status.textContent = `Import refused; existing history preserved: ${error.message}`; }
  finally { event.target.value = ''; }
});

$('clear').addEventListener('click', () => {
  if (!window.confirm('Clear only this lab\'s local S1 history?')) return;
  store.clear();
  graph = Object.freeze({ events:Object.freeze([]), invariants:Object.freeze([]) });
  refreshSaved([]);
  suggestionOutput.textContent = 'No suggestion requested.';
  status.textContent = 'Local S1 history cleared.';
});

adoptTrajectory(geometryId, trajectoryFor(geometryId, []));
try {
  const rows = rebuildGraphFromStore();
  refreshSaved(rows);
} catch (error) {
  refreshSaved([]);
  status.textContent = `Stored history is unreadable and was not modified: ${error.message}`;
}
render();
