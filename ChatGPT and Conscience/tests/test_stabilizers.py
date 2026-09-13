"""Packaging checks, not a rerun of every historical benchmark."""
import hashlib
import itertools
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from stabilizer_adaptive import adaptive_stabilizers
from stabilizer_matched import anchor_control, reuse_control


def oracle(points, dimension):
    if not points:
        return {"kind": "ALL_NONZERO_TRANSLATIONS", "dimension": dimension}
    classes = [{x for x, b in points.items() if b == label} for label in (0, 1)]
    found = [t for t in range(1, 1 << dimension)
             if all({x ^ t for x in group} == group for group in classes)]
    return {"kind": "EXPLICIT", "dimension": dimension, "nonzero": found}


class StabilizerTests(unittest.TestCase):
    def test_all_partial_tables_through_three_variables(self):
        cases = 0
        for n in range(4):
            for labels in itertools.product((-1, 0, 1), repeat=1 << n):
                points = {x: b for x, b in enumerate(labels) if b >= 0}
                expected = oracle(points, n)
                self.assertEqual(adaptive_stabilizers(points, n), expected)
                self.assertEqual(anchor_control(points, n), expected)
                self.assertEqual(reuse_control(points, n), expected)
                cases += 1
        self.assertEqual(cases, 6654)

    def test_stored_target(self):
        points = dict(zip([0, 1, 6, 7, 8, 10, 11, 12, 13, 15],
                          [0, 1, 1, 0, 1, 0, 0, 0, 0, 1]))
        self.assertEqual(adaptive_stabilizers(points, 4)["nonzero"], [7])

    def test_large_empty_domain_remains_symbolic(self):
        self.assertEqual(adaptive_stabilizers({}, 1_000_000),
                         {"kind": "ALL_NONZERO_TRANSLATIONS", "dimension": 1_000_000})

    def test_named_structural_cases(self):
        for points in ({x: 0 for x in range(64)},
                       {x: x.bit_count() % 2 for x in range(64)},
                       {x: (x.bit_count() % 2) ^ (x in (0, 63)) for x in range(64)}):
            self.assertEqual(adaptive_stabilizers(points, 6), oracle(points, 6))

    def test_reject_invalid_inputs(self):
        for points, n in [({0: True}, 1), ({-1: 0}, 1), ({8: 0}, 3),
                          ({0: 2}, 1), ({0: 0}, -1), ({0: 0}, True), ([], 2)]:
            with self.subTest(points=points, n=n):
                with self.assertRaises((ValueError, TypeError)):
                    adaptive_stabilizers(points, n)

    def test_original_code_and_patch_identities(self):
        provenance = json.loads((ROOT / "PROVENANCE.json").read_text())
        for entry in provenance["copied_files"]:
            actual = hashlib.sha256((ROOT / entry["destination"]).read_bytes()).hexdigest()
            self.assertEqual(actual, entry["sha256"], entry["destination"])

    def test_recorded_results_not_relabelled_as_new(self):
        summary = json.loads((ROOT / "evidence/benchmark-summary.json").read_text())
        self.assertIn("not a new benchmark", summary["integrity_state"])
        self.assertEqual(summary["correctness_cases"], 72444)
        self.assertEqual(len(summary["results"]), 6)


if __name__ == "__main__":
    unittest.main()
