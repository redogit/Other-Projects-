import copy
import json
from pathlib import Path
import unittest

from s1_carrier_surface import (
    CARRIER_TYPES,
    protected_invariant_view,
    project_to_carrier,
    reconstruct_from_carrier,
    project_carrier_to_omega,
    reconstruct_carrier_from_omega,
    evaluate_round_trip,
    semantic_residuals,
    one_degree_repair,
)

ROOT = Path(__file__).parent


def fixture():
    return json.loads((ROOT / "fixtures" / "s1_current_semantic_object.json").read_text(encoding="utf-8"))


class S1CarrierSurfaceTests(unittest.TestCase):
    def test_all_four_new_surfaces_round_trip_same_object(self):
        native = fixture()
        expected = protected_invariant_view(native)
        self.assertEqual(
            set(CARRIER_TYPES),
            {"candidate-state", "survivor", "semantic-work-unit", "multi-timescale"},
        )
        for carrier_type in CARRIER_TYPES:
            with self.subTest(carrier_type=carrier_type):
                carrier = project_to_carrier(native, carrier_type)
                rebuilt = reconstruct_from_carrier(carrier)
                self.assertEqual(rebuilt, native)
                self.assertEqual(protected_invariant_view(rebuilt), expected)
                report = evaluate_round_trip(native, carrier)
                self.assertEqual(report["classification"], "ROTATION")
                self.assertEqual(report["residuals"], [])

    def test_omega_is_a_second_transport_not_new_authority(self):
        native = fixture()
        for carrier_type in CARRIER_TYPES:
            carrier = project_to_carrier(native, carrier_type)
            omega = project_carrier_to_omega(carrier)
            rebuilt_carrier = reconstruct_carrier_from_omega(omega)
            rebuilt_native = reconstruct_from_carrier(rebuilt_carrier)
            self.assertEqual(rebuilt_carrier, carrier)
            self.assertEqual(rebuilt_native, native)
            self.assertIn("METHOD_TRANSFER != EVIDENCE_TRANSFER", omega["claimCeiling"])
            self.assertEqual(omega["evidence"][0]["kind"], "structural-projection")

    def test_stripped_reconstruction_sidecar_is_not_called_rotation(self):
        native = fixture()
        carrier = project_to_carrier(native, "candidate-state")
        stripped = copy.deepcopy(carrier)
        stripped["reconstructionPayload"] = None
        report = evaluate_round_trip(native, stripped)
        self.assertEqual(report["classification"], "UNKNOWN")
        self.assertIn("reconstruction-unavailable", {r["kind"] for r in report["residuals"]})

    def test_tampering_protected_identity_is_semantic_decay(self):
        native = fixture()
        carrier = project_to_carrier(native, "survivor")
        tampered = copy.deepcopy(carrier)
        tampered["objectId"] = "s1:semantic:other"
        report = evaluate_round_trip(native, tampered)
        self.assertEqual(report["classification"], "SEMANTIC_DECAY")
        kinds = {r["kind"] for r in report["residuals"]}
        self.assertIn("protected-invariant-mismatch", kinds)

    def test_candidate_surface_never_promotes_candidate_to_admitted(self):
        native = fixture()
        carrier = project_to_carrier(native, "candidate-state")
        self.assertIs(carrier["payload"]["candidateState"]["admitted"], False)
        self.assertIn("S_PRIME_CANDIDATE != ADMITTED_SUCCESSOR", carrier["claimCeiling"])

    def test_survivor_surface_retains_counterexample_and_next_cut(self):
        carrier = project_to_carrier(fixture(), "survivor")
        self.assertEqual(carrier["payload"]["survivor"]["kind"], "counterexample")
        self.assertEqual(
            carrier["payload"]["survivor"]["nextCut"],
            "require-independent-verification",
        )

    def test_semantic_work_unit_surface_carries_full_reconstruction_roles(self):
        carrier = project_to_carrier(fixture(), "semantic-work-unit")
        work = carrier["payload"]["workUnit"]
        self.assertEqual(work["objectId"], "s1:semantic:fixture-1")
        self.assertIn("obligationFamily", work)
        self.assertIn("invariantMap", work)
        self.assertIn("decisionField", work)
        self.assertIn("unresolvedRemainder", work)

    def test_multi_timescale_surface_preserves_strict_schedule_order(self):
        carrier = project_to_carrier(fixture(), "multi-timescale")
        schedule = carrier["payload"]["schedule"]
        self.assertLess(schedule["tau_s"], schedule["tau_w"])
        self.assertLess(schedule["tau_w"], schedule["tau_T"])
        self.assertLess(schedule["tau_T"], schedule["tau_K"])

    def test_schedule_order_is_a_typed_residual_not_silent_normalization(self):
        native = fixture()
        native["schedule"]["tau_w"] = 20
        residuals = semantic_residuals(native)
        self.assertIn("schedule-order", {r["kind"] for r in residuals})

    def test_one_degree_repair_closes_only_the_witnessed_schedule_residual(self):
        native = fixture()
        native["schedule"]["tau_w"] = 20
        result = one_degree_repair(native, ("schedule", "tau_w"), 4)
        self.assertEqual(result["status"], "REPAIRED")
        self.assertEqual(result["changedSemanticPaths"], ["schedule.tau_w"])
        self.assertIn("schedule-order", {r["kind"] for r in result["residualBefore"]})
        self.assertEqual(result["residualAfter"], [])
        self.assertEqual(
            protected_invariant_view(result["candidate"]),
            protected_invariant_view(fixture()),
        )

    def test_repair_cannot_mutate_protected_identity_or_claim_ceiling(self):
        native = fixture()
        with self.assertRaisesRegex(ValueError, "protected"):
            one_degree_repair(native, ("objectId",), "other")
        with self.assertRaisesRegex(ValueError, "protected"):
            one_degree_repair(native, ("claimCeiling",), ["stronger"])

    def test_projection_does_not_mutate_input(self):
        native = fixture()
        before = copy.deepcopy(native)
        for carrier_type in CARRIER_TYPES:
            project_to_carrier(native, carrier_type)
        self.assertEqual(native, before)


if __name__ == "__main__":
    unittest.main()
