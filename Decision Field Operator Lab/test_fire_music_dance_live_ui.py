from pathlib import Path
import re
import unittest


ROOT = Path(__file__).parent
UI = ROOT / "live-fire-field"


class FireMusicDanceLiveUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (UI / "index.html").read_text(encoding="utf-8")
        cls.js = (UI / "app.js").read_text(encoding="utf-8")
        cls.css = (UI / "styles.css").read_text(encoding="utf-8")

    def test_required_controls_exist(self):
        ids = [
            "field-visual", "stage-badge",
            "burn-pass", "burn-fail", "burn-unresolved",
            "apply-mutation", "music-toggle", "dance-pad",
            "homeward", "sleep", "wake",
            "ash-list", "smoke-list", "ember-list", "survivor-list",
            "trace-list", "copy-state", "download-state", "import-state",
            "command-input", "apply-command",
        ]
        for control_id in ids:
            with self.subTest(control_id=control_id):
                self.assertRegex(
                    self.html,
                    rf'id=["\']{re.escape(control_id)}["\']',
                )

    def test_bridge_commands_are_explicit_and_bounded(self):
        commands = [
            "SET_TRIAD", "DANCE", "MUTATE", "BURN", "SURVIVOR",
            "RECONSTITUTE", "HOMEWARD", "SLEEP", "WAKE", "COMPARE",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertIn(f'case "{command}"', self.js)
        self.assertIn(
            'const COMMAND_SCHEMA = "fire-music-dance-command/v1"',
            self.js,
        )

    def test_method_boundaries_remain_visible(self):
        boundaries = [
            "GENERATE != VERIFY != ADMIT",
            "METHOD_TRANSFER != EVIDENCE_TRANSFER",
            "SOFTWARE_VERIFICATION != DOMAIN_PROOF",
            "MUSIC != TRUTH",
            "DANCE != TRUTH",
            "DELTA_ZERO_IS_LOCAL_NOT_GLOBAL",
            "UNKNOWN != ZERO",
            "OBJECT_IDENTITY_IS_INVARIANT",
        ]
        corpus = self.html + "\n" + self.js
        for boundary in boundaries:
            with self.subTest(boundary=boundary):
                self.assertIn(boundary, corpus)

    def test_interface_exposes_shared_state_bridge(self):
        self.assertIn("window.FireMusicDanceLive", self.js)
        self.assertIn("bridgeSnapshot", self.js)
        self.assertIn("applyCommandPacket", self.js)
        self.assertIn("localStorage", self.js)
        self.assertIn("fire-music-dance-bridge-state/v1", self.js)

    def test_accessibility_hooks_are_present(self):
        self.assertIn('class="skip-link"', self.html)
        self.assertIn('aria-live="polite"', self.html)
        self.assertIn('role="img"', self.html)
        self.assertIn(
            "@media (prefers-reduced-motion: reduce)",
            self.css,
        )

    def test_full_legend_is_represented(self):
        for token in [
            "DARK", "MIDDLE", "LIGHT",
            "ASH", "SMOKE", "EMBER", "SURVIVOR",
            "RECONSTITUTE", "HOMEWARD",
            "SLEEP", "REOBSERVE",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, self.html + self.js)
        for direction in [
            "FORWARD", "BACKWARD", "UP", "DOWN", "SIDEWAYS", "INWARD",
            "OUTWARD", "AROUND", "THROUGH", "REVERSE", "BRANCH", "HOMEWARD",
        ]:
            with self.subTest(direction=direction):
                self.assertIn(direction, self.js)


if __name__ == "__main__":
    unittest.main()
