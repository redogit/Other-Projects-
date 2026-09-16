import copy
import json
import unittest
from pathlib import Path

import gsfl_bidirectional_cycle as cycle


ROOT = Path(__file__).resolve().parent
MACRO_PROFILE = ROOT / "gsfl-bidirectional-macro-profile.json"
OPERATOR_PROFILE = ROOT / "gsfl-operator-profile.json"
CANONICAL_REGISTRY = ROOT / "operator-skill-registry.json"

EXPECTED_MACROS = ["SEEK", "QUESTION", "REFRAME", "BUILD", "RETURN_INWARD"]
EXPECTED_EXPANSIONS = {
    "SEEK": ["OBSERVE", "GROUND", "TRACE_TOOL"],
    "QUESTION": ["DISTINGUISH", "COMPARE", "AUDIT_CONFOUNDS"],
    "REFRAME": ["MAP", "ROTATE", "RELATE", "PRESERVE"],
    "BUILD": ["COMPOSE", "REPAIR", "VERIFY", "SELECT", "HANDOFF"],
    "RETURN_INWARD": ["RECONSTRUCT", "TEACH_BACK", "DERIVE_COROLLARIES", "COMPARE", "PRESERVE", "FIT"],
}


def base_envelope():
    return {
        "payload": {
            "source_meaning": {"identity": "same", "purpose": "cooperative understanding"},
            "candidate_meaning": {"identity": "same", "purpose": "cooperative understanding"},
            "claims": {"fit_is_truth": True},
            "candidates": [
                {"id": "admitted", "admitted": True, "score": 0.8},
                {"id": "rejected", "admitted": False, "score": 1.0},
            ],
        },
        "trace": [],
    }


def macro_params():
    return {
        "SEEK": {
            "OBSERVE": {"observation": "A representation changed while the protected meaning remained stable."},
            "TRACE_TOOL": {"tool_id": "semantic-audit", "purpose": "trace bounded comparison", "provenance": "GSFL operator projection"},
        },
        "QUESTION": {
            "COMPARE": {"left": "source meaning", "right": "candidate meaning"},
            "AUDIT_CONFOUNDS": {},
        },
        "REFRAME": {
            "MAP": {"source": "technical surface", "target": "human surface"},
            "ROTATE": {"surface": "Same meaning, clearer cooperative representation."},
            "RELATE": {"left": "human", "relation": "cooperates_with", "right": "machine"},
            "PRESERVE": {"keys": ["identity", "purpose"]},
        },
        "BUILD": {
            "COMPOSE": {"parts": ["source", "rotation", "verification"]},
            "VERIFY": {"checks": {"meaning_preserved": True, "tool_provenance_present": True}},
            "HANDOFF": {"to": "human-partner", "reason": "bounded successor ready for review"},
        },
        "RETURN_INWARD": {
            "RECONSTRUCT": {"meaning": {"identity": "same", "purpose": "cooperative understanding"}},
            "TEACH_BACK": {"detail": "The human partner can restate the preserved distinction in task-local terms."},
            "DERIVE_COROLLARIES": {},
            "COMPARE": {"left": {"identity": "same"}, "right": {"identity": "same"}},
            "PRESERVE": {"keys": ["identity", "purpose"]},
            "FIT": {},
        },
    }


class BidirectionalMacroCycleTests(unittest.TestCase):
    def test_macro_cycle_order_is_exact(self):
        profile = json.loads(MACRO_PROFILE.read_text(encoding="utf-8"))
        self.assertEqual(EXPECTED_MACROS, profile["cycle_order"])

    def test_macro_expansions_are_exact(self):
        profile = json.loads(MACRO_PROFILE.read_text(encoding="utf-8"))
        by_id = {row["id"]: row for row in profile["macros"]}
        self.assertEqual(EXPECTED_EXPANSIONS, {key: by_id[key]["expansion"] for key in EXPECTED_MACROS})

    def test_macros_are_not_primitive_operators(self):
        operator_profile = json.loads(OPERATOR_PROFILE.read_text(encoding="utf-8"))
        primitive_ids = {row["id"] for row in operator_profile["operators"]}
        self.assertTrue(set(EXPECTED_MACROS).isdisjoint(primitive_ids))

    def test_canonical_decision_field_loop_remains_unchanged(self):
        registry = json.loads(CANONICAL_REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(
            ["DISTINGUISH", "GROUND", "TRANSPORT", "ATTACK", "REPAIR", "SELECT"],
            registry["canonical_loop"],
        )

    def test_profile_validates_against_operator_projection(self):
        report = cycle.validate_macro_profile(cycle.load_macro_profile(), cycle.load_operator_profile())
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(5, report["macro_count"])
        self.assertEqual(19, report["unique_operator_count"])

    def test_seek_is_outward_and_does_not_mutate_input(self):
        envelope = base_envelope()
        original = copy.deepcopy(envelope)
        result = cycle.apply_macro("SEEK", envelope, macro_params=macro_params()["SEEK"])
        self.assertEqual(original, envelope)
        self.assertEqual("OUTWARD", result["macro_trace"][-1]["phase"])
        self.assertEqual("SEEK", result["macro_trace"][-1]["macro"])
        self.assertEqual("A representation changed while the protected meaning remained stable.", result["payload"]["observations"][0])
        self.assertEqual("semantic-audit", result["payload"]["tools"][0]["tool_id"])
        self.assertTrue(any(row.get("delegate_to") == "GROUND" for row in result["payload"]["handoffs"]))

    def test_question_surfaces_confound_and_canonical_distinguish_handoff(self):
        result = cycle.apply_macro("QUESTION", base_envelope(), macro_params=macro_params()["QUESTION"])
        self.assertTrue(any(row["id"] == "FIT_SCORE_AS_TRUTH" for row in result["payload"]["confounds"]))
        self.assertTrue(any(row.get("delegate_to") == "DISTINGUISH" for row in result["payload"]["handoffs"]))

    def test_reframe_changes_surface_but_preserves_declared_meaning(self):
        envelope = base_envelope()
        result = cycle.apply_macro("REFRAME", envelope, macro_params=macro_params()["REFRAME"])
        self.assertEqual(envelope["payload"]["source_meaning"], result["payload"]["source_meaning"])
        self.assertEqual("Same meaning, clearer cooperative representation.", result["payload"]["surface"])
        self.assertTrue(result["payload"]["preservation"]["passed"])

    def test_build_routes_repair_and_select_without_claiming_authority(self):
        result = cycle.apply_macro("BUILD", base_envelope(), macro_params=macro_params()["BUILD"])
        handoffs = result["payload"]["handoffs"]
        self.assertTrue(any(row.get("delegate_to") == "REPAIR" for row in handoffs))
        self.assertTrue(any(row.get("delegate_to") == "SELECT" for row in handoffs))
        self.assertTrue(any(row.get("to") == "human-partner" for row in handoffs))
        self.assertTrue(result["payload"]["verification"]["passed"])
        self.assertTrue(all(row["authority_effect"] == "NONE" for row in result["trace"]))

    def test_return_inward_reconstructs_teaches_back_and_fits_admitted_only(self):
        envelope = base_envelope()
        envelope["payload"]["tools"] = [{"tool_id": "semantic-audit", "purpose": "audit", "provenance": "fixture"}]
        envelope["payload"]["cooperation_steps"] = [{"partner_id": "human", "action": "review", "detail": "reviewed"}]
        result = cycle.apply_macro("RETURN_INWARD", envelope, macro_params=macro_params()["RETURN_INWARD"])
        self.assertEqual("INWARD", result["macro_trace"][-1]["phase"])
        self.assertEqual(envelope["payload"]["source_meaning"], result["payload"]["reconstruction"])
        self.assertEqual("TEACH_BACK", result["payload"]["understanding_evidence"]["kind"])
        self.assertEqual("admitted", result["payload"]["fit_selection"]["id"])
        ids = {row["id"] for row in result["payload"]["corollaries"]}
        self.assertIn("TOOL_PROVENANCE_SEPARABLE", ids)
        self.assertIn("ATTRIBUTION_RECONSTRUCTIBLE", ids)

    def test_full_cycle_is_deterministic_and_keeps_outward_inward_phases(self):
        envelope = base_envelope()
        first = cycle.run_bidirectional_cycle(envelope, cycle_params=macro_params())
        second = cycle.run_bidirectional_cycle(envelope, cycle_params=macro_params())
        self.assertEqual(cycle.canonical_json(first), cycle.canonical_json(second))
        self.assertEqual(EXPECTED_MACROS, [row["macro"] for row in first["macro_trace"]])
        self.assertEqual(["OUTWARD", "OUTWARD", "OUTWARD", "OUTWARD", "INWARD"], [row["phase"] for row in first["macro_trace"]])
        self.assertEqual("admitted", first["payload"]["fit_selection"]["id"])
        self.assertEqual({"identity": "same", "purpose": "cooperative understanding"}, first["payload"]["source_meaning"])


if __name__ == "__main__":
    unittest.main()
