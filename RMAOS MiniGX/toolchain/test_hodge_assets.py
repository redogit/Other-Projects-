"""Exercise canonical input generation and APK parity across the dependency boundary."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parent
HELPER = ROOT / "toolchain" / "hodge_assets.py"


class HodgeAssetTests(unittest.TestCase):
    def run_helper(self, *args):
        return subprocess.run(
            [sys.executable, str(HELPER), *map(str, args)],
            text=True, capture_output=True,
        )

    def generate(self, root):
        result = self.run_helper("build", "--generated-root", root)
        self.assertEqual(result.returncode, 0, result.stderr)
        return root / "assets"

    def package(self, assets, apk, change_fragment=False):
        with ZipFile(apk, "w") as archive:
            for path in sorted(assets.rglob("*")):
                if path.is_file():
                    data = path.read_bytes()
                    if change_fragment and path.name == "w114_field.frag":
                        data += b"\n// unrelated local fragment\n"
                    archive.writestr("assets/" + path.relative_to(assets).as_posix(), data)

    def test_build_keeps_canonical_raw_source_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            generated = Path(directory)
            assets = self.generate(generated)
            sys.path.insert(0, str(REPOSITORY / "tools"))
            from hodge_dependency import resolve_artifact
            source = resolve_artifact("w114_circuit")
            shader = resolve_artifact("w114_shader")
            ir = json.loads((assets / "minigx/w114_perturbation.minigx.json").read_text())
            self.assertEqual(ir["provenance"], {
                "source_file": source.name,
                "source_sha256": "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest(),
            })
            self.assertEqual((assets / "shaders/w114_field.frag").read_bytes(), shader.read_bytes())
            self.assertEqual((assets / "shaders/fullscreen.vert").read_bytes(), (ROOT / "shaders/fullscreen.vert").read_bytes())
            java = (generated / "java/org/rmaos/mingx/generated/MiniGXGraph.java").read_text()
            self.assertIn(ir["digest"], java)
            self.assertEqual(ir["boundaries"]["software_proof"], "SOFTWARE_VERIFICATION != MATHEMATICAL_PROOF")

    def test_parity_accepts_assets_from_the_pinned_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = self.generate(root / "generated")
            apk = root / "app.apk"
            self.package(assets, apk)
            result = self.run_helper("parity", apk)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("MINIGX_APK_SOURCE_PARITY=PASS", result.stdout)

    def test_parity_rejects_fragment_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = self.generate(root / "generated")
            apk = root / "app.apk"
            self.package(assets, apk, change_fragment=True)
            result = self.run_helper("parity", apk)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("shader asset mismatch", result.stderr)

    def test_parity_rejects_raw_source_provenance_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = self.generate(root / "generated")
            path = assets / "minigx/w114_perturbation.minigx.json"
            ir = json.loads(path.read_text())
            ir["provenance"]["source_sha256"] = "sha256:" + "0" * 64
            path.write_text(json.dumps(ir))
            apk = root / "app.apk"
            self.package(assets, apk)
            result = self.run_helper("parity", apk)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("circuit asset mismatch", result.stderr)

    def test_generation_removes_stale_owned_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = self.generate(root)
            stale = assets / "shaders/competing_w114.frag"
            stale.write_text("unrelated shader")
            self.generate(root)
            self.assertFalse(stale.exists())

    def test_parity_rejects_competing_extra_shader(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = self.generate(root / "generated")
            (assets / "shaders/competing_w114.frag").write_text("unrelated shader")
            apk = root / "app.apk"
            self.package(assets, apk)
            result = self.run_helper("parity", apk)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected MiniGX asset", result.stderr)


if __name__ == "__main__":
    unittest.main()
