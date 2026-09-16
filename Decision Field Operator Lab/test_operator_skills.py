import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "operator-skill-registry.json"
EXPECTED = ["DISTINGUISH", "GROUND", "TRANSPORT", "ATTACK", "REPAIR", "SELECT"]


class OperatorSkillRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_canonical_operator_order(self):
        self.assertEqual(self.data["canonical_loop"], EXPECTED)
        self.assertEqual([op["id"] for op in self.data["operators"]], EXPECTED)

    def test_each_operator_has_skill_agent_and_output_contract(self):
        for op in self.data["operators"]:
            skill = ROOT / op["skill"]
            agent = ROOT / op["agent"]
            self.assertTrue(skill.is_file(), skill)
            self.assertTrue(agent.is_file(), agent)
            skill_text = skill.read_text(encoding="utf-8")
            agent_text = agent.read_text(encoding="utf-8")
            self.assertIn(op["output"], skill_text)
            self.assertIn(op["output"], agent_text)
            self.assertIn("## Output", skill_text)
            self.assertIn("## Output", agent_text)

    def test_coordination_contract_exists(self):
        coordination = ROOT / self.data["coordination"]
        self.assertTrue(coordination.is_file())
        text = coordination.read_text(encoding="utf-8")
        for field in (
            "from_project",
            "to_project",
            "source_revision",
            "authority_scope",
            "claim_ceiling",
            "unknowns",
            "return_route",
        ):
            self.assertIn(field, text)

    def test_authority_and_independence_boundaries_are_explicit(self):
        self.assertEqual(
            self.data["authority_model"],
            "PROPOSE_SEARCH__VERIFY__ADMIT_RETAIN_SEPARATED",
        )
        self.assertIn("not_independent", self.data["review_policy"])
        agent_index = (ROOT / "agents/operators/README.md").read_text(encoding="utf-8")
        self.assertIn("not automatically independent", agent_index)
        self.assertIn("never self-ratify", agent_index)

    def test_cross_project_transfer_is_not_automatic(self):
        coordination = (ROOT / "COORDINATION.md").read_text(encoding="utf-8")
        self.assertIn("do not automatically transfer", coordination)
        self.assertIn("Project conclusions remain with their owning project", coordination)

    def test_gsfl_profile_is_successor_projection_without_canonical_reordering(self):
        self.assertEqual(self.data["canonical_loop"], EXPECTED)
        profiles = {row["id"]: row for row in self.data.get("profiles", [])}
        self.assertIn("GSFL_V0_1_OPERATOR_PROJECTION", profiles)
        profile_ref = profiles["GSFL_V0_1_OPERATOR_PROJECTION"]
        self.assertTrue(profile_ref["canonical_loop_unchanged"])
        self.assertEqual("COMPLETE_BOUNDED_V0_1", profile_ref["source_lifecycle"])
        profile_path = ROOT / profile_ref["registry"]
        self.assertTrue(profile_path.is_file(), profile_path)
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        self.assertEqual("PROJECTION_DOES_NOT_MUTATE_SOURCE_BASELINE", profile["authority_model"])
        self.assertEqual(23, len(profile["operators"]))


if __name__ == "__main__":
    unittest.main()
