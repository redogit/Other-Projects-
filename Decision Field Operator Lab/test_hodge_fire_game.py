from pathlib import Path
import unittest

ROOT=Path(__file__).parent/"hodge-fire-game"

class FiveEyesFermatFireGameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=(ROOT/"index.html").read_text(encoding="utf-8")
        cls.js=(ROOT/"game.js").read_text(encoding="utf-8")
        cls.css=(ROOT/"styles.css").read_text(encoding="utf-8")
        cls.readme=(ROOT/"README.md").read_text(encoding="utf-8")

    def test_frozen_w114_target(self):
        for token in ['degree:114','alpha:[1,7,78,79,86,91]','target:"x1^6*x2^77*x3^78*x4^85*x5^90"','center:"MOT-1"']:
            self.assertIn(token,self.js)

    def test_five_eyes_are_simultaneous(self):
        for eye in ["EYE:GEO","EYE:DATA","EYE:FLOW","EYE:EVENT","EYE:HUMAN"]:
            self.assertIn(eye,self.js)
        self.assertIn("simultaneous:true",self.js)

    def test_all_ways_complete(self):
        for way in ["FORWARD","BACKWARD","UP","DOWN","SIDEWAYS","INWARD","OUTWARD","AROUND","THROUGH","REVERSE","BRANCH","HOMEWARD"]:
            self.assertIn('"'+way+'"',self.js)

    def test_known_families_preserved_as_ash_controls(self):
        for item in ["PAIR-KOSZUL","CUBIC-DELSARTE","LIFTED-PAIR-PLANE","TATE-LIFT"]:
            self.assertIn(item,self.js)
        self.assertIn("masked from active novelty generation but never erased",self.readme)

    def test_best_piece_carriers_present(self):
        for token in ["makeFractalFire","BBF_REVERSE","HOMEWARD","Cognate","RMA-SDCAN","Knowledge Decay","Decision Field MMORPG"]:
            self.assertIn(token,self.js+self.readme)

    def test_scientific_boundaries_visible(self):
        for boundary in [
            "GAME_SCORE != MATHEMATICAL_EVIDENCE",
            "COGNATE != IDENTITY",
            "NEW_TO_ACTIVE_SEARCH != NEW_MATHEMATICAL_CYCLE",
            "SOFTWARE_VERIFICATION != MATHEMATICAL_PROOF",
            "VISUAL_PROJECTION_ORBIT != MATHEMATICAL_DIMENSION",
        ]:
            self.assertIn(boundary,self.js+self.readme)

    def test_play_first_surface(self):
        for control in ['id="field"','id="pulse"','id="scan"','id="music"','id="home"','id="ledger-toggle"']:
            self.assertIn(control,self.html)
        self.assertNotIn("<form",self.html.lower())

if __name__=="__main__":
    unittest.main()
