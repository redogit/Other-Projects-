from pathlib import Path
import random,tempfile,unittest,sys
ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT))
import minigxc
SOURCE=ROOT.parent/"circuits"/"w114_perturbation.rmal"

class MiniGXCompilerTests(unittest.TestCase):
    def test_canonical_compile_is_deterministic(self):
        a=minigxc.canonical_ir(SOURCE);b=minigxc.canonical_ir(SOURCE)
        self.assertEqual(a,b);self.assertTrue(a["digest"].startswith("sha256:"));self.assertEqual(len(a["nodes"]),13);self.assertEqual(len(a["edges"]),17)
    def test_carrier_filename_does_not_change_semantic_digest(self):
        text=SOURCE.read_text()
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/"a.rmal";b=Path(td)/"b.rmal";a.write_text(text);b.write_text(text)
            ia=minigxc.canonical_ir(a);ib=minigxc.canonical_ir(b)
            self.assertEqual(ia["digest"],ib["digest"]);self.assertNotEqual(ia["provenance"]["source_file"],ib["provenance"]["source_file"])
    def test_comments_and_layout_do_not_change_semantic_digest(self):
        text=SOURCE.read_text();base=minigxc.canonical_ir(SOURCE)["digest"]
        decorated="# carrier comment\n"+text.replace("MODULE rmaos.minigx.w114_perturbation","MODULE rmaos.minigx.w114_perturbation # inline")
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/SOURCE.name;p.write_text(decorated);self.assertEqual(base,minigxc.canonical_ir(p)["digest"])
    def test_line_order_is_semantically_stable(self):
        src=SOURCE.read_text();base=minigxc.canonical_ir(SOURCE)["digest"];headers=[];cats={"ENTITY":[],"RELATE":[],"CLAIM":[]}
        for line in src.splitlines():
            s=line.strip()
            if not s or s.startswith("#"):continue
            h=s.split()[0]
            if h in ("MODULE","SURFACE","TARGET"):headers.append(s)
            else:cats[h].append(s)
        for seed in range(200):
            rng=random.Random(seed);groups=[]
            for key in ("ENTITY","RELATE","CLAIM"):
                rows=cats[key][:];rng.shuffle(rows);groups+=rows
            with tempfile.TemporaryDirectory() as td:
                p=Path(td)/SOURCE.name;p.write_text("\n".join(headers+groups)+"\n");self.assertEqual(base,minigxc.canonical_ir(p)["digest"])
    def test_feedback_edge_is_explicit(self):
        ir=minigxc.canonical_ir(SOURCE);f=[e for e in ir["edges"] if e["relation"]=="FEEDBACK_TO"]
        self.assertEqual(len(f),1);self.assertEqual(f[0]["src"],"Node.Feedback");self.assertEqual(f[0]["dst"],"Node.Field")
    def test_boundaries_survive_compile(self):
        texts={c["text"] for c in minigxc.canonical_ir(SOURCE)["claims"]};self.assertIn("GAME_SCORE != MATHEMATICAL_EVIDENCE",texts);self.assertIn("COGNATE != IDENTITY",texts)
    def compile_text(self,text):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.rmal";p.write_text(text);return minigxc.canonical_ir(p)
    def base(self): return 'MODULE x\nSURFACE minigx\nTARGET android.opengl_es_3_1\n'
    def test_unknown_op_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"unsupported OP"):self.compile_text(self.base()+'ENTITY Node.X KIND "MINIGX_NODE" FAMILY "FIELD" OP "INVENTED" STAGE "0" PARAMS ""\n')
    def test_untyped_cycle_fails(self):
        t=self.base()+'ENTITY Node.A KIND "MINIGX_NODE" FAMILY "STATE" OP "RECENTER" STAGE "0" PARAMS ""\nENTITY Node.B KIND "MINIGX_NODE" FAMILY "TRACE" OP "TRACE_TAP" STAGE "0" PARAMS ""\nRELATE Node.A AS FEEDS TO Node.B PORT "x"\nRELATE Node.B AS FEEDS TO Node.A PORT "y"\n'
        with self.assertRaisesRegex(ValueError,"non-feedback cycle"):self.compile_text(t)
    def test_duplicate_edge_fails(self):
        t=self.base()+'ENTITY Node.A KIND "MINIGX_NODE" FAMILY "STATE" OP "RECENTER" STAGE "0" PARAMS ""\nENTITY Node.B KIND "MINIGX_NODE" FAMILY "TRACE" OP "TRACE_TAP" STAGE "1" PARAMS ""\nRELATE Node.A AS FEEDS TO Node.B PORT "x"\nRELATE Node.A AS FEEDS TO Node.B PORT "x"\n'
        with self.assertRaisesRegex(ValueError,"duplicate edge"):self.compile_text(t)
    def test_duplicate_claim_fails(self):
        t=self.base()+'ENTITY Node.A KIND "MINIGX_NODE" FAMILY "STATE" OP "RECENTER" STAGE "0" PARAMS ""\nCLAIM C KIND "BOUNDARY" STATUS "PRESERVED" TEXT "A"\nCLAIM C KIND "BOUNDARY" STATUS "PRESERVED" TEXT "B"\n'
        with self.assertRaisesRegex(ValueError,"duplicate claim"):self.compile_text(t)
    def test_duplicate_directive_fails(self):
        t='MODULE x\nMODULE y\nSURFACE minigx\nTARGET android.opengl_es_3_1\nENTITY Node.A KIND "MINIGX_NODE" FAMILY "STATE" OP "RECENTER" STAGE "0" PARAMS ""\n'
        with self.assertRaisesRegex(ValueError,"duplicate MODULE"):self.compile_text(t)
    def test_negative_stage_fails(self):
        with self.assertRaisesRegex(ValueError,"STAGE must be >= 0"):self.compile_text(self.base()+'ENTITY Node.A KIND "MINIGX_NODE" FAMILY "STATE" OP "RECENTER" STAGE "-1" PARAMS ""\n')
    def test_feedback_source_must_be_feedback_family(self):
        t=self.base()+'ENTITY Node.A KIND "MINIGX_NODE" FAMILY "STATE" OP "RECENTER" STAGE "0" PARAMS ""\nENTITY Node.B KIND "MINIGX_NODE" FAMILY "FIELD" OP "W114_FIELD" STAGE "1" PARAMS ""\nRELATE Node.A AS FEEDBACK_TO TO Node.B PORT "history"\n'
        with self.assertRaisesRegex(ValueError,"FAMILY FEEDBACK"):self.compile_text(t)
    def test_random_dags_compile_and_random_cycles_reject(self):
        ops=[("STATE","RECENTER"),("TRACE","TRACE_TAP"),("FIELD","W114_FIELD"),("CONTROL","TRANSFORM_SET"),("POINT","GPU_POINTS"),("POST","BLOOM_TONEMAP")]
        for seed in range(100):
            rng=random.Random(seed);n=8;lines=[self.base().rstrip()]
            for i in range(n):
                fam,op=ops[i%len(ops)];lines.append(f'ENTITY Node.N{i} KIND "MINIGX_NODE" FAMILY "{fam}" OP "{op}" STAGE "{i}" PARAMS ""')
            for i in range(n-1): lines.append(f'RELATE Node.N{i} AS FEEDS TO Node.N{i+1} PORT "p{i}"')
            for i in range(n-2):
                if rng.random()<.35:lines.append(f'RELATE Node.N{i} AS MODULATES TO Node.N{i+2} PORT "m{i}"')
            self.compile_text("\n".join(lines)+"\n")
            cyc="\n".join(lines+[f'RELATE Node.N{n-1} AS FEEDS TO Node.N0 PORT "cycle"'])+"\n"
            with self.assertRaisesRegex(ValueError,"non-feedback cycle"):self.compile_text(cyc)
if __name__=="__main__":unittest.main()
