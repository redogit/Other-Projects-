from pathlib import Path
import re

ROOT = Path(__file__).parent
manifest = (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
java = (ROOT / "app/src/main/java/com/redogit/firemusicdance/MainActivity.java").read_text(encoding="utf-8")
js = (ROOT / "app/src/main/assets/app.js").read_text(encoding="utf-8")
html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")

assert "android.permission.INTERNET" not in manifest
assert "android.permission.VIBRATE" in manifest
assert 'loadUrl("file:///android_asset/index.html")' in java
for method in ["copyText", "saveJson", "shareText", "vibrate", "runtime"]:
    assert f"public void {method}" in java or f"public String {method}" in java
for token in [
    "AndroidBridge.copyText",
    "AndroidBridge.saveJson",
    "AndroidBridge.vibrate",
    "fire-music-dance-command/v1",
    "fire-music-dance-bridge-state/v1",
    "GENERATE != VERIFY != ADMIT",
]:
    assert token in js
for control in ["copy-state", "download-state", "import-state", "apply-command", "music-toggle", "dance-pad"]:
    assert re.search(rf'id=["\\\']{re.escape(control)}["\\\']', html)
print("ANDROID_LOCAL_PROJECT_STATIC_CHECKS=PASS")
