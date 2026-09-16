import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python"))

from freeze_parity_manifest import build_manifest


class FreezeParityManifestTests(unittest.TestCase):
    def test_manifest_is_order_independent(self):
        metadata = {"source_commit": "abc", "llvm_tag": "llvmorg-23.1.1"}
        a = [{"path": "b.json", "sha256": "22"}, {"path": "a.json", "sha256": "11"}]
        b = list(reversed(a))
        self.assertEqual(build_manifest(a, metadata), build_manifest(b, metadata))

    def test_manifest_keeps_scientific_fields_explicit(self):
        record = {
            "case": "compiler_0",
            "status": "UNKNOWN",
            "selected_variable": 3,
            "planning_shortlist": [3, 1, 0],
            "states_evaluated": 7,
            "maximum_depth": 2,
        }
        out = build_manifest(
            [{"path": "case.json", "sha256": "aa", "scientific": record}],
            {"source_commit": "abc"},
        )
        self.assertEqual(out["records"][0]["scientific"]["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
