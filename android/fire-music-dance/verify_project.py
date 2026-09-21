from pathlib import Path
import re

ROOT=Path(__file__).parent
manifest=(ROOT/"app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
java=(ROOT/"app/src/main/java/com/redogit/firemusicdance/MainActivity.java").read_text(encoding="utf-8")
js=(ROOT/"app/src/main/assets/game.js").read_text(encoding="utf-8")
html=(ROOT/"app/src/main/assets/index.html").read_text(encoding="utf-8")

assert "android.permission.INTERNET" not in manifest
assert "android.permission.VIBRATE" in manifest
assert 'loadUrl("file:///android_asset/index.html")' in java
for method in ["copyText","saveJson","shareText","vibrate","runtime"]:
    assert ("public void "+method) in java or ("public String "+method) in java
for token in ["ROOT:W114","EYE:GEO","EYE:HUMAN","ALL_WAYS","BBF_REVERSE","HOMEWARD","GAME_SCORE != MATHEMATICAL_EVIDENCE"]:
    assert token in js
for control in ["field","pulse","scan","music","home","ledger-toggle"]:
    assert re.search(r'id=["\\']'+re.escape(control)+r'["\\']',html)
print("ANDROID_FIVE_EYES_W114_STATIC_CHECKS=PASS")
