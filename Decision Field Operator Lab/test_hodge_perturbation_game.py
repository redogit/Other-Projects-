from pathlib import Path
import re
import unittest

ROOT=Path(__file__).parent/"hodge-perturbation-game"
BANNED=("FIRE","ASH","EMBER","SURVIVOR","HOMEWARD","MUSIC","DANCE","EYE","STORM","FUZZBALL")

class W114PerturbationGameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=(ROOT/"index.html").read_text(encoding="utf-8")
        cls.js=(ROOT/"game.js").read_text(encoding="utf-8")
        cls.css=(ROOT/"styles.css").read_text(encoding="utf-8")
        cls.readme=(ROOT/"README.md").read_text(encoding="utf-8")
        cls.active="\n".join((cls.html,cls.js,cls.css,cls.readme))

    def test_frozen_w114_target(self):
        for token in ['degree:114','alpha:[1,7,78,79,86,91]','target:"x1^6*x2^77*x3^78*x4^85*x5^90"','center:"MOT-1"']:
            self.assertIn(token,self.js)

    def test_five_observer_channels(self):
        for obs in ["OBS:GEO","OBS:CHAR","OBS:DEFORM","OBS:EVENT","OBS:CLAIM"]:
            self.assertIn(obs,self.js)
        self.assertIn("simultaneous:true",self.js)

    def test_transform_set_complete(self):
        for op in ["FORWARD","BACKWARD","UP","DOWN","SIDEWAYS","INWARD","OUTWARD","AROUND","THROUGH","REVERSE","BRANCH","RECENTER"]:
            self.assertIn('"'+op+'"',self.js)

    def test_candidate_states(self):
        for state in ["GENERATED","REJECTED","PARTIAL","ROBUST"]:
            self.assertIn(state,self.js)

    def test_scientific_boundaries(self):
        for boundary in ["GAME_SCORE != MATHEMATICAL_EVIDENCE","COGNATE != IDENTITY","NEW_TO_ACTIVE_SEARCH != NEW_MATHEMATICAL_CYCLE","SOFTWARE_VERIFICATION != MATHEMATICAL_PROOF"]:
            self.assertIn(boundary,self.active)

    def test_metaphor_vocabulary_absent(self):
        words=re.findall(r"[A-Za-z]+",self.active.upper())
        for token in BANNED:
            with self.subTest(token=token):
                self.assertNotIn(token,words)

    def test_play_surface(self):
        for control in ['id="field"','id="perturb"','id="scan"','id="clock"','id="recenter"','id="ledger-toggle"']:
            self.assertIn(control,self.html)
        self.assertNotIn("<form",self.html.lower())

if __name__=="__main__":
    unittest.main()
