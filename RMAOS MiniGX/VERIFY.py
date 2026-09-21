from pathlib import Path
import json,subprocess,sys,tempfile
ROOT=Path(__file__).parent
with tempfile.TemporaryDirectory() as td:
    td=Path(td);out=td/'graph.json';java=td/'MiniGXGraph.java'
    subprocess.run([sys.executable,str(ROOT/'toolchain/minigxc.py'),str(ROOT/'circuits/five_eyes_fermat_fire.rmal'),'--out',str(out),'--java',str(java)],check=True,stdout=subprocess.DEVNULL)
    ir=json.loads(out.read_text());graph=java.read_text()
manifest=(ROOT/'android/rmaos-minigx/app/src/main/AndroidManifest.xml').read_text()
renderer=(ROOT/'android/rmaos-minigx/app/src/main/java/org/rmaos/mingx/MiniGXRenderer.java').read_text()
frag=(ROOT/'android/rmaos-minigx/app/src/main/assets/shaders/fermat_fire.frag').read_text()
game=(ROOT/'android/rmaos-minigx/app/src/main/java/org/rmaos/mingx/MiniGXGameState.java').read_text()
gradle=(ROOT/'android/rmaos-minigx/app/build.gradle').read_text()
assert ir['schema']=='rmaos/minigx-ir/v1' and len(ir['nodes'])==13 and len(ir['edges'])==17
assert ir['digest'] in graph and 'package org.rmaos.mingx.generated;' in graph
assert 'android.permission.INTERNET' not in manifest and 'android.permission.VIBRATE' in manifest
assert "applicationId 'org.rmaos.mingx'" in gradle and 'generateMiniGX' in gradle
for token in ['FIVE_EYES','ALL_WAYS','FERMAT_FIRE','COGNATE_FILAMENTS','TRACE_TAP','SURVIVOR_SCORE']:assert any(n['op']==token for n in ir['nodes'])
for token in ['GLES31','loadAsset("shaders/fullscreen.vert")','loadAsset("shaders/fermat_fire.frag")']:assert token in renderer
for token in ['#version 310 es','fire(vec2 uv','eyes(vec2 uv','circuits(vec2 uv','sparks(vec2 uv']:assert token in frag
for token in ['CYC:MGX:','ASH','EMBER','SURVIVOR','uniqueWays']:assert token in game
print('RMAOS_MINIGX_STATIC_CHECKS=PASS');print(ir['digest'])
