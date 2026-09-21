from pathlib import Path
import tempfile,unittest,sys
ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT))
import minigxc
SOURCE=ROOT.parent/"circuits"/"five_eyes_fermat_fire.rmal"

class MiniGXCompilerTests(unittest.TestCase):
    def test_canonical_compile_is_deterministic(self):
        a=minigxc.canonical_ir(SOURCE);b=minigxc.canonical_ir(SOURCE)
        self.assertEqual(a,b);self.assertTrue(a["digest"].startswith("sha256:"))
        self.assertEqual(len(a["nodes"]),13);self.assertEqual(len(a["edges"]),17)
    def test_feedback_edge_is_explicit(self):
        ir=minigxc.canonical_ir(SOURCE);f=[e for e in ir["edges"] if e["relation"]=="FEEDBACK_TO"]
        self.assertEqual(len(f),1);self.assertEqual(f[0]["src"],"Node.Feedback");self.assertEqual(f[0]["dst"],"Node.Fire")
    def test_boundaries_survive_compile(self):
        texts={c["text"] for c in minigxc.canonical_ir(SOURCE)["claims"]}
        self.assertIn("GAME_SCORE != MATHEMATICAL_EVIDENCE",texts);self.assertIn("COGNATE != IDENTITY",texts)
    def test_unknown_op_fails_closed(self):
        txt='MODULE x\nSURFACE minigx\nTARGET android.opengl_es_3_1\nENTITY Node.X KIND "MINIGX_NODE" FAMILY "FIELD" OP "INVENTED" STAGE "0" PARAMS ""\n'
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"bad.rmal";p.write_text(txt)
            with self.assertRaisesRegex(ValueError,"unsupported OP"):minigxc.canonical_ir(p)
    def test_untyped_cycle_fails(self):
        txt='MODULE x\nSURFACE minigx\nTARGET android.opengl_es_3_1\nENTITY Node.A KIND "MINIGX_NODE" FAMILY "STATE" OP "HOMEWARD" STAGE "0" PARAMS ""\nENTITY Node.B KIND "MINIGX_NODE" FAMILY "TRACE" OP "TRACE_TAP" STAGE "0" PARAMS ""\nRELATE Node.A AS FEEDS TO Node.B PORT "x"\nRELATE Node.B AS FEEDS TO Node.A PORT "y"\n'
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"cycle.rmal";p.write_text(txt)
            with self.assertRaisesRegex(ValueError,"non-feedback cycle"):minigxc.canonical_ir(p)
if __name__=="__main__":unittest.main()
