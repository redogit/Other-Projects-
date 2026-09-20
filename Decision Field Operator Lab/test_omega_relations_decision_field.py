from copy import deepcopy
import unittest

from decision_field import DecisionField, Evidence
from omega import canonical_json
from omega_adapters import project_decision_field, reconstruct_decision_field
from omega_relations import make_relation_field, validate_relation_field


class DecisionFieldRelationalWitnessTests(unittest.TestCase):
    def native_field(self):
        return DecisionField(
            possibilities=frozenset({0, 1, 2}),
            relations=({"kind": "excludes", "left": 0, "right": 2},),
            evidence=(Evidence("software-verification", "bounded-native-fixture"),),
            goal=1,
            unresolved=frozenset({0, 2}),
            observer={"obligation": "select-1"},
            history=("seed",),
        )

    def test_decision_field_projects_binds_relation_sidecar_and_reconstructs_exactly(self):
        native = self.native_field()
        omega = project_decision_field(native, "fixture:df:relational", "fixture:df:relational")
        before = canonical_json(omega)

        relation_field = make_relation_field(
            omega_id=omega["id"],
            currentness="CURRENT_CANONICAL",
            relations=[
                {
                    "source": "decision-field:fixture:df:relational",
                    "target": "neighbor:constraint-monitor",
                    "type": "NEIGHBOR",
                    "direction": "BIDIRECTIONAL",
                    "obligation": {
                        "kind": "preserve-native-goal-and-unresolved",
                        "goal": 1,
                    },
                    "evidenceRefs": ["omega:" + omega["id"]],
                    "permission": "ALLOW",
                    "cost": 1.0,
                    "reversibility": "REVERSIBLE",
                    "uncertainty": 0.0,
                    "provenance": ["fixture:decision-field-relational-witness"],
                },
                {
                    "source": "unresolved:{0,2}",
                    "target": "goal:1",
                    "type": "HOLE",
                    "direction": "A_TO_B",
                    "obligation": {
                        "kind": "minimum-span-needed",
                        "required": True,
                    },
                    "evidenceRefs": ["omega:" + omega["id"]],
                    "permission": "UNKNOWN",
                    "cost": 0.0,
                    "reversibility": "UNKNOWN",
                    "uncertainty": 1.0,
                    "provenance": ["fixture:decision-field-relational-witness"],
                },
            ],
            consequence={
                "self": ["native-state-unchanged"],
                "neighbor": ["constraint-monitor-visible"],
                "shared": ["goal-and-unresolved-explicit"],
                "ambient": ["no-authority-transfer"],
                "delayed": ["future-repair-unresolved"],
            },
            way_back={"omegaId": omega["id"], "status": "EXACT_REFERENCE"},
        )

        self.assertEqual(validate_relation_field(relation_field), relation_field)
        self.assertEqual(relation_field["omegaId"], omega["id"])
        self.assertEqual(relation_field["wayBack"]["omegaId"], omega["id"])
        self.assertEqual(canonical_json(omega), before)
        self.assertEqual(reconstruct_decision_field(omega), native)

    def test_relation_sidecar_does_not_promote_native_evidence_or_rewrite_native_relations(self):
        native = self.native_field()
        native_before = deepcopy(native)
        omega = project_decision_field(native, "fixture:df:relational:2", "fixture:df:relational:2")

        relation_field = make_relation_field(
            omega_id=omega["id"],
            currentness="PRESERVED_UNRESOLVED",
            relations=[
                {
                    "source": "route:A",
                    "target": "route:B",
                    "type": "PAIRITY",
                    "direction": "BIDIRECTIONAL",
                    "obligation": {"kind": "compare-before-equivalence"},
                    "evidenceRefs": ["native-reference-only"],
                    "permission": "ALLOW",
                    "cost": 0.5,
                    "reversibility": "REVERSIBLE",
                    "uncertainty": 0.25,
                    "provenance": ["fixture:pairity"],
                }
            ],
            consequence={
                "self": [],
                "neighbor": [],
                "shared": ["comparison-visible"],
                "ambient": [],
                "delayed": ["equivalence-not-admitted"],
            },
            way_back={"omegaId": omega["id"], "status": "EXACT_REFERENCE"},
        )

        self.assertEqual(native, native_before)
        self.assertEqual(reconstruct_decision_field(omega), native)
        self.assertEqual(relation_field["authority"], "method-only")
        self.assertEqual(relation_field["relations"][0]["evidenceRefs"], ["native-reference-only"])
        self.assertNotIn("evidence", relation_field["relations"][0])
        self.assertIn("METHOD_TRANSFER != EVIDENCE_TRANSFER", relation_field["boundaries"])
        self.assertIn("PAIRITY != FORCED_EQUALITY", relation_field["boundaries"])


if __name__ == "__main__":
    unittest.main()
