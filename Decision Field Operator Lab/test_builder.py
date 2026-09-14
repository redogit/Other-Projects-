import json
import tempfile
import unittest
from pathlib import Path

import builder


class BooleanCalibrationTests(unittest.TestCase):
    def test_complete_boolean_registry(self):
        registry = builder.boolean_registry()
        self.assertEqual(len(registry), 16)
        self.assertEqual({op.truth_mask for op in registry}, set(range(16)))

    def test_all_nand_certificates_verify(self):
        certificates = builder.all_boolean_certificates()
        self.assertTrue(all(c.verified and builder.execute_nand_certificate(c) for c in certificates.values()))
        self.assertEqual(max(len(c.gates) for c in certificates.values()), 5)
        self.assertEqual(len(certificates[6].gates), 4)
        self.assertEqual(len(certificates[9].gates), 5)

    def test_xnor_negative_control_at_four_gates(self):
        with self.assertRaises(LookupError):
            builder.synthesize_nand(9, max_gates=4)

    def test_operator_properties_spot_checks(self):
        registry = {op.id: op for op in builder.boolean_registry()}
        self.assertTrue(registry["XOR"].commutative)
        self.assertTrue(registry["XOR"].associative)
        self.assertEqual(registry["XOR"].identity, 0)
        self.assertTrue(registry["XOR"].invertible_each_argument)
        self.assertEqual(registry["AND"].identity, 1)
        self.assertEqual(registry["AND"].absorbing, 0)
        self.assertEqual(registry["OR"].demorgan_dual, "AND")
        self.assertEqual(registry["A_IMPLIES_B"].converse, "B_IMPLIES_A")


class CompassTests(unittest.TestCase):
    def test_compass_census_and_independent_orbits(self):
        audit = builder.compass_audit()
        self.assertEqual(audit["heading_count"], 80)
        expected = {1: 8, 2: 24, 3: 32, 4: 16}
        self.assertEqual(audit["support_counts"], expected)
        self.assertEqual(audit["independent_orbit_counts"], expected)
        self.assertTrue(audit["coverage_verified"])
        self.assertTrue(audit["opposites_verified"])

    def test_heading_canonicalization(self):
        for heading in builder.compass_headings():
            self.assertEqual(
                heading.canonical,
                tuple([1] * heading.support + [0] * (4 - heading.support)),
            )


class SPrimeTests(unittest.TestCase):
    def test_equal_gain_loss_is_not_no_change(self):
        score = builder.score_sprime({"a"}, {"b"}, representation_changed=True)
        self.assertEqual(score.signed, 0.0)
        self.assertEqual(score.magnitude, 2)
        self.assertFalse(score.representation_only)

    def test_representation_only(self):
        score = builder.score_sprime({"a"}, {"a"}, representation_changed=True)
        self.assertEqual(score.magnitude, 0)
        self.assertTrue(score.representation_only)


class BuilderProtocolTests(unittest.TestCase):
    def test_protocol_and_duplicate(self):
        machine = builder.AlgorithmicBuilder()
        self.assertEqual(machine.propose("x").status, "PROPOSED")
        self.assertEqual(machine.verify("x", lambda: True).status, "VERIFIED")
        self.assertEqual(machine.admit_unique("x", semantic_key="m:6").status, "ADMITTED_UNIQUE")
        self.assertEqual(machine.promote("x").status, "PROMOTED_PRIMITIVE")
        machine.propose("y")
        machine.verify("y", lambda: True)
        self.assertEqual(machine.admit_unique("y", semantic_key="m:6").status, "DUPLICATE")

    def test_rejected_proposal_cannot_be_admitted(self):
        machine = builder.AlgorithmicBuilder()
        machine.propose("x")
        self.assertEqual(machine.verify("x", lambda: False).status, "REJECTED")
        with self.assertRaises(ValueError):
            machine.admit_unique("x", semantic_key="x")


class BalanceTests(unittest.TestCase):
    def test_expected_fixture_winners(self):
        report = builder.balance_report()["fixtures"]
        self.assertEqual(report["exclusive_change"]["winner"], "XOR")
        self.assertEqual(report["agreement"]["winner"], "XNOR")
        self.assertEqual(report["intersection"]["winner"], "AND")
        self.assertEqual(report["coverage"]["winner"], "OR")
        self.assertNotEqual(report["endpoint_preserving_symmetric"]["winner"], "XOR")

    def test_structural_operators_are_incomparable_without_bridge(self):
        report = builder.balance_report()["fixtures"]["structural_comparison"]
        self.assertTrue(report)
        self.assertTrue(all(value == "INCOMPARABLE_ON_BOOLEAN_FIXTURES" for value in report.values()))


class ArtifactTests(unittest.TestCase):
    def test_periodic_table_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "table.json"
            builder.write_periodic_table(path)
            data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(data["boolean_operators"]), 16)
        self.assertEqual(data["compass"]["heading_count"], 80)
        self.assertTrue(all(row["certificate_verified"] for row in data["boolean_operators"]))

    def test_bounded_audit_controls(self):
        audit = builder.bounded_audit()
        self.assertFalse(audit["negative_controls"]["xnor_reachable_within_four_nand_gates"])
        self.assertEqual(audit["admission_protocol"]["duplicate"]["status"], "DUPLICATE")
        self.assertEqual(audit["equal_gain_loss_control"]["magnitude"], 2)


if __name__ == "__main__":
    unittest.main()
