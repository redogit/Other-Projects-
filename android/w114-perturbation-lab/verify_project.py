from pathlib import Path
ROOT=Path(__file__).parent
manifest=(ROOT/"app/src/main/AndroidManifest.xml").read_text()
java=(ROOT/"app/src/main/java/com/redogit/w114perturbation/MainActivity.java").read_text()
js=(ROOT/"app/src/main/assets/game.js").read_text()
html=(ROOT/"app/src/main/assets/index.html").read_text()
assert "android.permission.INTERNET" not in manifest
assert "android.permission.VIBRATE" in manifest
assert 'loadUrl("file:///android_asset/index.html")' in java
for x in ["ROOT:W114","OBS:GEO","OBS:CLAIM","TRANSFORM_SET","REVERSE","RECENTER","GAME_SCORE != MATHEMATICAL_EVIDENCE"]: assert x in js
for x in ["field","perturb","scan","clock","recenter","ledger-toggle"]: assert ('id="' + x + '"') in html
print("ANDROID_W114_PERTURBATION_STATIC_CHECKS=PASS")
