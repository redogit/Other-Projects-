import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import gsfl


class GSFLTests(unittest.TestCase):
    def source(self):
        return gsfl.SemanticObject(
            object_id="observer-field",
            meaning={"cardinality": "N", "world_state": "unchanged", "purpose": "accessible observation"},
            invariants=("cardinality", "world_state"),
        )

    def metrics(self, clarity=0.9, usefulness=0.9, recoverability=0.9,
                cognitive_effort=0.2, ambiguity=0.1, semantic_loss=0.0):
        return gsfl.Metrics(
            clarity=clarity,
            usefulness=usefulness,
            recoverability=recoverability,
            cognitive_effort=cognitive_effort,
            ambiguity=ambiguity,
            semantic_loss=semantic_loss,
        )

    def test_same_meaning_different_surface_is_valid_rotation(self):
        source = self.source()
        candidate = gsfl.Candidate(
            candidate_id="plain-language",
            meaning=dict(source.meaning),
            surface="N observers view one unchanged world state.",
            metrics=self.metrics(),
            reconstructed_meaning=dict(source.meaning),
        )
        result = gsfl.evaluate_candidate(source, candidate)
        self.assertEqual(gsfl.VALID_ROTATION, result.classification)
        self.assertTrue(result.invariants_preserved)
        self.assertTrue(result.reconstruction_pass)

    def test_meaning_change_with_invariants_intact_is_mutation(self):
        source = self.source()
        changed = dict(source.meaning)
        changed["purpose"] = "prediction"
        candidate = gsfl.Candidate(
            candidate_id="mutant",
            meaning=changed,
            surface="Changed purpose.",
            metrics=self.metrics(),
            reconstructed_meaning=changed,
        )
        result = gsfl.evaluate_candidate(source, candidate)
        self.assertEqual(gsfl.MUTATION, result.classification)
        self.assertTrue(result.invariants_preserved)

    def test_required_invariant_change_is_semantic_decay(self):
        source = self.source()
        changed = dict(source.meaning)
        changed["world_state"] = "modified"
        candidate = gsfl.Candidate(
            candidate_id="decay",
            meaning=changed,
            surface="Observer edits the world.",
            metrics=self.metrics(),
            reconstructed_meaning=changed,
        )
        result = gsfl.evaluate_candidate(source, candidate)
        self.assertEqual(gsfl.SEMANTIC_DECAY, result.classification)
        self.assertFalse(result.invariants_preserved)

    def test_fit_admits_only_valid_reconstructible_rotations(self):
        source = self.source()
        low = gsfl.Candidate(
            candidate_id="low",
            meaning=dict(source.meaning),
            surface="Technical wording.",
            metrics=self.metrics(clarity=0.5, usefulness=0.6, recoverability=0.7, cognitive_effort=0.8),
            reconstructed_meaning=dict(source.meaning),
        )
        high = gsfl.Candidate(
            candidate_id="high",
            meaning=dict(source.meaning),
            surface="Clear wording.",
            metrics=self.metrics(clarity=0.95, usefulness=0.95, recoverability=0.95, cognitive_effort=0.1),
            reconstructed_meaning=dict(source.meaning),
        )
        mutant_meaning = dict(source.meaning)
        mutant_meaning["purpose"] = "prediction"
        mutant = gsfl.Candidate(
            candidate_id="mutant",
            meaning=mutant_meaning,
            surface="Looks good but changes meaning.",
            metrics=self.metrics(clarity=1.0, usefulness=1.0, recoverability=1.0, cognitive_effort=0.0),
            reconstructed_meaning=mutant_meaning,
        )
        selected, results = gsfl.fit(source, [low, mutant, high])
        self.assertEqual("high", selected.candidate_id)
        by_id = {r.candidate_id: r for r in results}
        self.assertFalse(by_id["mutant"].admitted)

    def test_reconstruction_failure_blocks_otherwise_valid_rotation(self):
        source = self.source()
        candidate = gsfl.Candidate(
            candidate_id="lossy",
            meaning=dict(source.meaning),
            surface="N observers.",
            metrics=self.metrics(),
            reconstructed_meaning={"cardinality": "N"},
        )
        result = gsfl.evaluate_candidate(source, candidate)
        self.assertEqual(gsfl.VALID_ROTATION, result.classification)
        self.assertFalse(result.reconstruction_pass)
        self.assertFalse(result.admitted)

    def test_fit_tie_break_is_deterministic_by_candidate_id(self):
        source = self.source()
        candidates = [
            gsfl.Candidate("zeta", dict(source.meaning), "z", self.metrics(), dict(source.meaning)),
            gsfl.Candidate("alpha", dict(source.meaning), "a", self.metrics(), dict(source.meaning)),
        ]
        selected, _ = gsfl.fit(source, candidates)
        self.assertEqual("alpha", selected.candidate_id)

    def test_dsl_parses_and_selects_best_rotation(self):
        program = '''
GSFL 0
OBJECT observer-field
MEANING cardinality="N"
MEANING world_state="unchanged"
MEANING purpose="accessible observation"
PRESERVE cardinality
PRESERVE world_state
ROTATE verbose
SURFACE "An N-cardinality collection of observational transforms over invariant desktop state."
METRIC clarity=0.55 usefulness=0.80 recoverability=0.80 cognitive_effort=0.75 ambiguity=0.10 semantic_loss=0
RECONSTRUCT cardinality="N"
RECONSTRUCT world_state="unchanged"
RECONSTRUCT purpose="accessible observation"
END
ROTATE plain
SURFACE "N observers can present different views without changing the desktop."
METRIC clarity=0.95 usefulness=0.95 recoverability=0.95 cognitive_effort=0.15 ambiguity=0.05 semantic_loss=0
RECONSTRUCT cardinality="N"
RECONSTRUCT world_state="unchanged"
RECONSTRUCT purpose="accessible observation"
END
FIT
'''
        execution = gsfl.execute(program)
        self.assertEqual("plain", execution["selected_candidate"])
        self.assertEqual(2, len(execution["evaluations"]))

    def test_cli_executes_program_and_writes_canonical_json(self):
        program = '''
GSFL 0
OBJECT x
MEANING identity="same"
PRESERVE identity
ROTATE plain
SURFACE "same thing, clearer"
METRIC clarity=1 usefulness=1 recoverability=1 cognitive_effort=0 ambiguity=0 semantic_loss=0
RECONSTRUCT identity="same"
END
FIT
'''
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "input.gsfl"
            out = Path(td) / "result.json"
            src.write_text(program, encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "run_gsfl.py", str(src), "--out", str(out)],
                cwd=Path(__file__).parent,
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, proc.returncode, proc.stderr)
            result = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual("plain", result["selected_candidate"])
            self.assertTrue(out.read_text(encoding="utf-8").endswith("\n"))

    def test_audit_check_passes_against_frozen_evidence(self):
        proc = subprocess.run(
            [sys.executable, "run_audit.py", "--check"],
            cwd=Path(__file__).parent,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

    def test_duplicate_meaning_key_is_rejected(self):
        program = '''
GSFL 0
OBJECT x
MEANING identity="a"
MEANING identity="b"
PRESERVE identity
ROTATE plain
SURFACE "x"
METRIC clarity=1 usefulness=1 recoverability=1 cognitive_effort=0 ambiguity=0 semantic_loss=0
RECONSTRUCT identity="a"
END
FIT
'''
        with self.assertRaisesRegex(ValueError, "duplicate MEANING"):
            gsfl.execute(program)

    def test_duplicate_candidate_id_is_rejected(self):
        program = '''
GSFL 0
OBJECT x
MEANING identity="same"
PRESERVE identity
ROTATE duplicate
SURFACE "a"
METRIC clarity=1 usefulness=1 recoverability=1 cognitive_effort=0 ambiguity=0 semantic_loss=0
RECONSTRUCT identity="same"
END
ROTATE duplicate
SURFACE "b"
METRIC clarity=1 usefulness=1 recoverability=1 cognitive_effort=0 ambiguity=0 semantic_loss=0
RECONSTRUCT identity="same"
END
FIT
'''
        with self.assertRaisesRegex(ValueError, "duplicate candidate id"):
            gsfl.execute(program)

    def test_fit_must_be_terminal(self):
        program = '''
GSFL 0
OBJECT x
MEANING identity="same"
PRESERVE identity
ROTATE plain
SURFACE "a"
METRIC clarity=1 usefulness=1 recoverability=1 cognitive_effort=0 ambiguity=0 semantic_loss=0
RECONSTRUCT identity="same"
END
FIT
MEANING late="not allowed"
'''
        with self.assertRaisesRegex(ValueError, "FIT must be terminal"):
            gsfl.execute(program)

    def test_canonical_json_is_repeatable(self):
        obj = {"b": [2, 1], "a": {"z": True, "x": None}}
        self.assertEqual(gsfl.canonical_json(obj), gsfl.canonical_json(obj))
        self.assertTrue(gsfl.canonical_json(obj).endswith("\n"))
        self.assertEqual(obj, json.loads(gsfl.canonical_json(obj)))


if __name__ == "__main__":
    unittest.main()
