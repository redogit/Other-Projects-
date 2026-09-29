from pathlib import Path
import json,subprocess,sys,tempfile
ROOT=Path(__file__).parent
with tempfile.TemporaryDirectory() as td:
    td=Path(td);out=td/'graph.json';java=td/'MiniGXGraph.java'
    subprocess.run([sys.executable,str(ROOT/'toolchain/minigxc.py'),str(ROOT/'circuits/w114_perturbation.rmal'),'--out',str(out),'--java',str(java)],check=True,stdout=subprocess.DEVNULL)
    ir=json.loads(out.read_text());graph=java.read_text()
manifest=(ROOT/'android/rmaos-minigx/app/src/main/AndroidManifest.xml').read_text();renderer=(ROOT/'android/rmaos-minigx/app/src/main/java/org/rmaos/mingx/MiniGXRenderer.java').read_text();circuit=(ROOT/'android/rmaos-minigx/app/src/main/java/org/rmaos/mingx/MiniGXCircuit.java').read_text();frag=(ROOT/'shaders/w114_field.frag').read_text();vert=(ROOT/'shaders/fullscreen.vert').read_text();game=(ROOT/'android/rmaos-minigx/app/src/main/java/org/rmaos/mingx/MiniGXGameState.java').read_text();gradle=(ROOT/'android/rmaos-minigx/app/build.gradle').read_text()
assert ir['schema']=='rmaos/minigx-ir/v1' and len(ir['nodes'])==13 and len(ir['edges'])==17 and ir['provenance']['source_sha256'].startswith('sha256:')
assert ir['digest'] in graph and 'package org.rmaos.mingx.generated;' in graph
assert 'android.permission.INTERNET' not in manifest and 'android.permission.VIBRATE' in manifest and 'WebView' not in renderer
assert "applicationId 'org.rmaos.mingx'" in gradle and 'generateMiniGX' in gradle and 'syncMiniGXShaders' in gradle
assert not (ROOT/'android/rmaos-minigx/app/src/main/assets/shaders').exists()
for token in ['OBSERVER_CHANNELS','TRANSFORM_SET','W114_FIELD','COGNATE_LINKS','TRACE_TAP','ROBUST_SCORE']:assert any(n['op']==token for n in ir['nodes'])
for token in ['circuit.param("W114_FIELD","vertex_shader")','circuit.param("W114_FIELD","shader")','circuit.intParam("OBSERVER_CHANNELS","count")','circuit.floatParam("FRAME_FEEDBACK","decay")','circuit.floatParam("BLOOM_TONEMAP","bloom")']:assert token in renderer
for token in ['RUNTIME_OPS','No MiniGX runtime backend for op','execution order incomplete','validateBackendContract','Unsupported MiniGX value','MiniGX integer out of range','MiniGX float out of range','Unsafe MiniGX shader path']:assert token in circuit
for token in ['#version 310 es','field(vec2 uv','observers(vec2 uv','branches(vec2 uv','cognates(vec2 uv','points(vec2 uv','uFeedback','uPulseRate','uBloom','uExposure']:assert token in frag
assert '#version 310 es' in vert

import re
active_text="\n".join([
    (ROOT/'circuits/w114_perturbation.rmal').read_text(),
    renderer,
    circuit,
    frag,
    game,
    (ROOT/'android/rmaos-minigx/app/src/main/java/org/rmaos/mingx/MiniGXHudView.java').read_text(),
    (ROOT/'android/rmaos-minigx/app/src/main/java/org/rmaos/mingx/MiniGXView.java').read_text(),
    (ROOT/'README.md').read_text(),
])
removed_terms=("FIRE","ASH","EMBER","SURVIVOR","HOMEWARD","MUSIC","DANCE","EYE","STORM","FUZZBALL")
words=set(re.findall(r"[A-Za-z]+",active_text.upper()))
for token in removed_terms:
    assert token not in words, f"removed metaphor term returned: {token}"
for token in ['CYC:MGX:','REJECTED','PARTIAL','ROBUST','uniqueTransforms']:assert token in game
byop={n['op']:n for n in ir['nodes']}
assert 1<=int(byop['W114_FIELD']['params']['ray_steps'])<=64
assert int(byop['OBSERVER_CHANNELS']['params']['count'])==5
assert 1<=int(byop['GPU_POINTS']['params']['count'])<=96
assert 1<=float(byop['PULSE_OSCILLATOR']['params']['rate'])<=400
assert 0<=float(byop['FRAME_FEEDBACK']['params']['decay'])<=1 and 0<=float(byop['FRAME_FEEDBACK']['params']['mix'])<=1
assert 0<=float(byop['BLOOM_TONEMAP']['params']['bloom'])<=4 and .1<=float(byop['BLOOM_TONEMAP']['params']['exposure'])<=4
for key in ('vertex_shader','shader'):
    p=byop['W114_FIELD']['params'][key]
    assert p.startswith('shaders/') and '..' not in Path(p).parts and '\\' not in p and not p.startswith('/')
print('RMAOS_MINIGX_STATIC_CHECKS=PASS');print(ir['digest'])
