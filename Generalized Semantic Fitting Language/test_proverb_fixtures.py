import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import gsfl_proverbs as proverbs
except ImportError:
    proverbs = None


class ProverbFixtureTests(unittest.TestCase):
    def require(self):
        self.assertIsNotNone(proverbs, "gsfl_proverbs module must exist")

    def test_traditional_and_synthetic_sources_remain_distinct(self):
        self.require()
        traditional = proverbs.traditional_fixture(
            fixture_id="many-hands",
            source_text="Many hands make light work.",
            context="common English-language saying",
        )
        synthetic = proverbs.synthetic_fixture(
            fixture_id="shared-lanterns",
            source_text="Shared lanterns shorten the dark road.",
            context="synthetic cooperation fixture",
        )
        self.assertEqual("TRADITIONAL_OR_COMMON", traditional.source_status)
        self.assertEqual("SYNTHETIC", synthetic.source_status)
        self.assertNotEqual(traditional.provenance.source_kind, synthetic.provenance.source_kind)

    def test_fixture_requires_human_and_machine_interpretations(self):
        self.require()
        with self.assertRaisesRegex(ValueError, "human.*machine|machine.*human"):
            proverbs.ProverbFixture(
                fixture_id="incomplete",
                source_text="A small saying.",
                source_status="SYNTHETIC",
                context="test",
                provenance=proverbs.ProverbProvenance("synthetic", "generated in test", "fixture"),
                human_interpretations=(),
                machine_interpretations=("machine reading",),
                alternate_interpretations=(),
                invariant_meanings=("cooperation",),
                cooperation_trace=(),
                tools=(),
            )

    def test_generator_is_deterministic(self):
        self.require()
        first = proverbs.generate_synthetic_fixtures(seed=17, count=6)
        second = proverbs.generate_synthetic_fixtures(seed=17, count=6)
        self.assertEqual(first, second)
        self.assertEqual(6, len(first))
        self.assertEqual(6, len({f.fixture_id for f in first}))

    def test_generated_fixture_preserves_partner_and_tool_trace(self):
        self.require()
        fixture = proverbs.generate_synthetic_fixtures(seed=3, count=1)[0]
        self.assertTrue(fixture.human_interpretations)
        self.assertTrue(fixture.machine_interpretations)
        self.assertTrue(fixture.cooperation_trace)
        actors = {step.partner_kind for step in fixture.cooperation_trace}
        self.assertEqual({"HUMAN", "MACHINE"}, actors)
        self.assertTrue(fixture.tools)
        self.assertTrue(all(tool.provenance for tool in fixture.tools))

    def test_confound_registry_covers_required_proverb_failures(self):
        self.require()
        ids = {row["id"] for row in proverbs.PROVERB_CONFOUND_REGISTRY}
        required = {
            "TRANSLATION_LOSS",
            "CULTURAL_FLATTENING",
            "FALSE_UNIVERSALITY",
            "ATTRIBUTION_UNCERTAINTY",
            "LITERAL_FIGURATIVE_COLLAPSE",
            "MACHINE_PARAPHRASE_AS_HUMAN_UNDERSTANDING",
            "POPULARITY_AS_TRUTH",
            "PRESERVATION_AS_ENDORSEMENT",
            "SYNTHETIC_PROVENANCE_LAUNDERING",
            "LEXICAL_SIMILARITY_AS_CROSS_CULTURAL_EQUIVALENCE",
        }
        self.assertTrue(required.issubset(ids), required - ids)

    def test_traditional_fixture_triggers_attribution_and_universality_confounds(self):
        self.require()
        fixture = proverbs.traditional_fixture(
            fixture_id="stitch",
            source_text="A stitch in time saves nine.",
            context="common English-language saying; exact origin not established by this fixture",
        )
        ids = {f["id"] for f in proverbs.detect_proverb_confounds(fixture)}
        self.assertIn("ATTRIBUTION_UNCERTAINTY", ids)
        self.assertIn("FALSE_UNIVERSALITY", ids)
        self.assertIn("POPULARITY_AS_TRUTH", ids)

    def test_synthetic_fixture_cannot_masquerade_as_traditional(self):
        self.require()
        fixture = proverbs.synthetic_fixture(
            fixture_id="bridge",
            source_text="A bridge remembered by both banks carries more than feet.",
            context="synthetic human-machine cooperation fixture",
        )
        corrupted = proverbs.replace_source_status(fixture, "TRADITIONAL_OR_COMMON")
        ids = {f["id"] for f in proverbs.detect_proverb_confounds(corrupted)}
        self.assertIn("SYNTHETIC_PROVENANCE_LAUNDERING", ids)

    def test_multiple_interpretations_are_not_collapsed_to_one_truth(self):
        self.require()
        fixture = proverbs.generate_synthetic_fixtures(seed=5, count=1)[0]
        result = proverbs.audit_fixture(fixture)
        self.assertGreaterEqual(result["interpretation_count"], 3)
        self.assertFalse(result["claims_single_true_meaning"])
        self.assertIn("MULTIPLE_READINGS_REMAIN_DISTINCT", {c["id"] for c in result["corollaries"]})

    def test_machine_paraphrase_is_not_human_understanding_evidence(self):
        self.require()
        fixture = proverbs.generate_synthetic_fixtures(seed=9, count=1)[0]
        result = proverbs.audit_fixture(fixture)
        ids = {f["id"] for f in result["confounds"]}
        self.assertIn("MACHINE_PARAPHRASE_AS_HUMAN_UNDERSTANDING", ids)
        self.assertEqual("NONE", result["human_understanding_evidence"])

    def test_corpus_audit_separates_observation_corollary_and_confound(self):
        self.require()
        corpus = list(proverbs.generate_synthetic_fixtures(seed=11, count=4))
        corpus.append(proverbs.traditional_fixture(
            fixture_id="hands",
            source_text="Many hands make light work.",
            context="common English-language saying",
        ))
        audit = proverbs.audit_corpus(corpus)
        self.assertEqual(5, audit["fixture_count"])
        self.assertIn("observations", audit)
        self.assertIn("corollaries", audit)
        self.assertIn("confounds", audit)
        self.assertGreater(audit["confound_count"], 0)
        self.assertFalse(audit["universal_meaning_claim"])

    def test_cli_generates_deterministic_json_corpus(self):
        self.require()
        with tempfile.TemporaryDirectory() as td:
            first = Path(td) / "first.json"
            second = Path(td) / "second.json"
            cmd = [sys.executable, "run_proverb_generator.py", "--seed", "23", "--count", "5"]
            proc1 = subprocess.run(cmd + ["--out", str(first)], cwd=Path(__file__).parent, text=True, capture_output=True)
            proc2 = subprocess.run(cmd + ["--out", str(second)], cwd=Path(__file__).parent, text=True, capture_output=True)
            self.assertEqual(0, proc1.returncode, proc1.stdout + proc1.stderr)
            self.assertEqual(0, proc2.returncode, proc2.stdout + proc2.stderr)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            payload = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(5, payload["fixture_count"])
            self.assertEqual(5, len(payload["fixtures"]))
            self.assertTrue(all(row["source_status"] == "SYNTHETIC" for row in payload["fixtures"]))
            self.assertTrue(all(row["human_interpretations"] and row["machine_interpretations"] for row in payload["fixtures"]))


if __name__ == "__main__":
    unittest.main()
