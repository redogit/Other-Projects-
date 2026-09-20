import importlib
from copy import deepcopy
import unittest


OMEGA_ID = "a" * 64


def _relation(kind="NEIGHBOR", source="A", target="B"):
    return {
        "source": source,
        "target": target,
        "type": kind,
        "direction": "BIDIRECTIONAL",
        "obligation": {"kind": "preserve-distinction", "required": True},
        "evidenceRefs": ["evidence:bounded"],
        "permission": "ALLOW",
        "cost": 1.25,
        "reversibility": "REVERSIBLE",
        "uncertainty": 0.125,
        "provenance": ["source:test"],
    }


def _consequence():
    return {
        "self": ["self:unchanged"],
        "neighbor": ["neighbor:observed"],
        "shared": ["shared:bounded"],
        "ambient": ["ambient:none-observed"],
        "delayed": ["delayed:unresolved"],
    }


class OmegaRelationalFieldTests(unittest.TestCase):
    def module(self):
        try:
            return importlib.import_module("omega_relations")
        except ModuleNotFoundError:
            self.fail("RELATIONAL_FIELD_CARRIER_MISSING")

    def make(self, **overrides):
        mod = self.module()
        kwargs = {
            "omega_id": OMEGA_ID,
            "currentness": "CURRENT_CANONICAL",
            "relations": [_relation()],
            "consequence": _consequence(),
            "way_back": {"omegaId": OMEGA_ID, "status": "EXACT_REFERENCE"},
        }
        kwargs.update(overrides)
        return mod.make_relation_field(**kwargs)

    def test_relational_field_is_deterministic_content_addressed_and_validates(self):
        mod = self.module()
        first = self.make()
        second = self.make()
        self.assertEqual(first, second)
        self.assertEqual(first["schema"], "rmapl-omega-relational-field/v0")
        self.assertRegex(first["id"], r"^[0-9a-f]{64}$")
        self.assertEqual(mod.validate_relation_field(first), first)
        self.assertRegex(first["relations"][0]["id"], r"^[0-9a-f]{64}$")

    def test_relation_preserves_endpoints_without_forcing_shared_ontology(self):
        field = self.make(
            relations=[
                _relation("PAIRITY", "route:A", "route:B"),
                _relation("INTERLINGUA_TRANSLATION", "carrier:text", "carrier:logic"),
                _relation("HOLE", "path:entry", "path:exit"),
            ]
        )
        self.assertEqual(
            [item["type"] for item in field["relations"]],
            ["PAIRITY", "INTERLINGUA_TRANSLATION", "HOLE"],
        )
        self.assertEqual(field["relations"][0]["source"], "route:A")
        self.assertEqual(field["relations"][0]["target"], "route:B")
        self.assertNotEqual(field["relations"][0]["source"], field["relations"][0]["target"])

    def test_consequence_vector_is_exactly_all_directional(self):
        mod = self.module()
        field = self.make()
        self.assertEqual(
            set(field["consequence"]),
            {"self", "neighbor", "shared", "ambient", "delayed"},
        )
        broken = _consequence()
        broken.pop("ambient")
        with self.assertRaisesRegex(ValueError, "consequence fields"):
            mod.make_relation_field(
                omega_id=OMEGA_ID,
                currentness="CURRENT_CANONICAL",
                relations=[_relation()],
                consequence=broken,
                way_back={"omegaId": OMEGA_ID, "status": "EXACT_REFERENCE"},
            )

    def test_currentness_way_back_and_authority_boundaries_are_explicit(self):
        mod = self.module()
        field = self.make(currentness="PRESERVED_UNRESOLVED")
        self.assertEqual(field["authority"], "method-only")
        self.assertEqual(field["currentness"], "PRESERVED_UNRESOLVED")
        self.assertEqual(field["wayBack"], {"omegaId": OMEGA_ID, "status": "EXACT_REFERENCE"})
        for boundary in [
            "RELATION != MERGE",
            "METHOD_TRANSFER != EVIDENCE_TRANSFER",
            "OMEGA_VIEW != NATIVE_OBJECT",
            "CURRENT != PROVED",
            "PAIRITY != FORCED_EQUALITY",
        ]:
            self.assertIn(boundary, field["boundaries"])
        with self.assertRaisesRegex(ValueError, "currentness"):
            mod.make_relation_field(
                omega_id=OMEGA_ID,
                currentness="PROVED",
                relations=[_relation()],
                consequence=_consequence(),
                way_back={"omegaId": OMEGA_ID, "status": "EXACT_REFERENCE"},
            )

    def test_inputs_are_not_mutated(self):
        relations = [_relation()]
        consequence = _consequence()
        way_back = {"omegaId": OMEGA_ID, "status": "EXACT_REFERENCE"}
        before = deepcopy((relations, consequence, way_back))
        self.make(relations=relations, consequence=consequence, way_back=way_back)
        self.assertEqual((relations, consequence, way_back), before)

    def test_tamper_and_invalid_relation_contract_fail_closed(self):
        mod = self.module()
        field = self.make()
        tampered = deepcopy(field)
        tampered["relations"][0]["target"] = "C"
        with self.assertRaisesRegex(ValueError, "canonical"):
            mod.validate_relation_field(tampered)

        bad = _relation()
        bad["direction"] = "SIDEWAYS_MAGIC"
        with self.assertRaisesRegex(ValueError, "direction"):
            self.make(relations=[bad])

        bad = _relation()
        bad["permission"] = "OWNER"
        with self.assertRaisesRegex(ValueError, "permission"):
            self.make(relations=[bad])

        bad = _relation()
        bad["uncertainty"] = 2.0
        with self.assertRaisesRegex(ValueError, "uncertainty"):
            self.make(relations=[bad])

    def test_relation_evidence_is_reference_only_not_authority_promotion(self):
        field = self.make()
        relation = field["relations"][0]
        self.assertIn("evidenceRefs", relation)
        self.assertNotIn("evidence", relation)
        self.assertEqual(field["authority"], "method-only")
        self.assertIn("METHOD_TRANSFER != EVIDENCE_TRANSFER", field["boundaries"])


if __name__ == "__main__":
    unittest.main()
