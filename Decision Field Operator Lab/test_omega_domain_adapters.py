import json
from pathlib import Path
import unittest

from omega_adapters import (
    project_dimensional_record,
    project_gsfl_record,
    project_hodge_bridge,
    project_image_surface,
    project_suggestion_record,
)

ROOT = Path(__file__).parent.parent


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class OmegaDomainAdapterTests(unittest.TestCase):
    def test_gsfl_frozen_audit_preserves_fit_truth_boundary(self):
        native = read_json("Generalized Semantic Fitting Language/evidence/RESULTS.json")
        omega = project_gsfl_record(native)
        self.assertEqual(omega["nativeType"], "gsfl-audit/v0")
        self.assertIn("FIT != TRUTH", omega["invariants"])
        self.assertIn(
            "software verification does not establish universal semantic equivalence",
            omega["claimCeiling"],
        )
        self.assertEqual(
            omega["domainRemainder"]["native"]["selected_candidate"],
            native["selected_candidate"],
        )

    def test_image_surface_keeps_intrinsic_and_projection_observations_separate(self):
        packet = {
            "session": {
                "schema": "s1-image-surface/v0",
                "id": "image-session-1",
                "source": {"schema": "s1-image-source/v0", "id": "image-1"},
                "surface": {"id": "surface-1"},
                "experience": {
                    "id": "experience-1",
                    "actions": [{"plane": "xw", "degrees": 1}],
                    "observer": {"yaw": 0, "pitch": 0, "roll": 0, "wPerspective": 0.35},
                },
                "historyAuthority": "s1-experience/v0",
                "claimCeiling": [
                    "IMAGE_DEFORMATION != PHYSICAL_DEFORMATION",
                    "PROJECTION_DISTORTION != INTRINSIC_DEFORMATION",
                    "FINITE_GRID_CONNECTIVITY != CONTINUUM_TOPOLOGY",
                ],
            },
            "measurement": {
                "intrinsic": {"maxPrincipalStretchDeltaFromOne": 0},
                "extrinsic": {"maxAmbientOrientationAngleRad": 0.017},
                "curvature": {"method": "grid-vector-laplacian-norm/v0", "continuumCurvatureClaim": False},
                "topology": {"method": "fixed-grid-connectivity/v0", "connectivityChanged": False, "continuumTopologyClaim": False},
                "projection": {"maxPrincipalStretchDeltaFromOne": 0.01, "projectionDistortionDetected": True, "intrinsicDeformationImplied": False},
            },
        }
        omega = project_image_surface(packet)
        kinds = [item["kind"] for item in omega["observations"]]
        self.assertIn("intrinsic", kinds)
        self.assertIn("projection", kinds)
        self.assertNotEqual(
            next(x["value"] for x in omega["observations"] if x["kind"] == "intrinsic"),
            next(x["value"] for x in omega["observations"] if x["kind"] == "projection"),
        )
        self.assertIn("PROJECTION_DISTORTION != INTRINSIC_DEFORMATION", omega["claimCeiling"])

    def test_dimensional_projection_requires_explicit_loss_declaration(self):
        native = {
            "version": "s1-dimension-ladder/v0",
            "boundary": "ADJACENT_DIMENSIONS_RELATED != ADJACENT_DIMENSIONS_IDENTICAL",
            "ladder": [0, 1, 2, 3, 4],
            "projectionLoss": {
                "map": "drop coordinate 2",
                "sourceA": [1, 2, 3],
                "sourceB": [1, 2, 9],
                "projectionA": [1, 2],
                "projectionB": [1, 2],
                "sameProjection": True,
                "sourcePointsDistinct": True,
            },
            "claimCeiling": ["finite Euclidean fixtures only", "no universal dimensional law"],
        }
        omega = project_dimensional_record(native)
        loss = next(x for x in omega["observations"] if x["kind"] == "projection-loss")
        self.assertEqual(loss["inducedEquivalence"], "equal-projected-coordinates")
        self.assertEqual(loss["lost"], "dropped-coordinate-distinction")

        bad = dict(native)
        bad["projectionLoss"] = {"map": "drop coordinate 2"}
        with self.assertRaisesRegex(ValueError, "loss declaration"):
            project_dimensional_record(bad)

    def test_suggestion_remains_suggestion_only(self):
        native = {
            "carrierVersion": "s1-transition-carrier/v0",
            "kind": "generated",
            "move": {"plane": "xw", "degrees": 1},
            "prefix": [],
            "contract": {
                "initialState": "fixture",
                "mirrorId": "mirror:fixture",
                "shell": "comparison",
                "observer": {"yaw": 0, "pitch": 0, "roll": 0, "wPerspective": 0.35},
                "operatorVersion": "S'1-Ops v0",
            },
            "provenance": {
                "datasetVersion": "s1-suggest-dataset/v0",
                "modelVersion": "s1-suggest-transition/v0",
                "sourceExperienceIds": [],
                "strategy": "deterministic-fallback/v0",
            },
            "authority": "suggestion-only",
        }
        omega = project_suggestion_record(native)
        self.assertIn("SUGGESTION != EXPERIENCE_AUTHORITY", omega["claimCeiling"])
        self.assertEqual(omega["evidence"][0]["kind"], "suggestion-only")
        with self.assertRaisesRegex(ValueError, "suggestion-only"):
            project_suggestion_record({**native, "authority": "experience-authority"})

    def test_hodge_frozen_bridge_preserves_candidate_authority_and_full_chronology(self):
        native = read_json("Hodge Span Lab/evidence/issue43_bridge_calibration_result.json")
        omega = project_hodge_bridge(native)
        self.assertEqual(omega["nativeType"], "hodge-deformation-bridge-result/v0")
        self.assertEqual(omega["path"], native["source"]["actions"])
        observations = {item["kind"]: item["value"] for item in omega["observations"]}
        self.assertEqual(observations["compressed-signature"], native["source"]["signature_vector"])
        self.assertEqual(observations["candidate-vector"], native["bridge"]["candidate_vector"])
        self.assertIn(native["claim_ceiling"], omega["claimCeiling"])
        self.assertEqual(omega["evidence"][0]["kind"], "candidate-test-only")

    def test_hodge_stronger_unknown_authority_fails_closed(self):
        native = read_json("Hodge Span Lab/evidence/issue43_bridge_calibration_result.json")
        with self.assertRaisesRegex(ValueError, "candidate-test-only"):
            project_hodge_bridge({**native, "authority": "proof"})

    def test_read_only_domain_adapters_do_not_create_software_verification(self):
        gsfl = project_gsfl_record(
            read_json("Generalized Semantic Fitting Language/evidence/RESULTS.json")
        )
        image = project_image_surface({
            "session": {
                "schema": "s1-image-surface/v0",
                "id": "audit-image",
                "source": {"schema": "s1-image-source/v0", "id": "image"},
                "surface": {"id": "surface"},
                "experience": {"id": "event", "actions": [], "observer": {}},
                "historyAuthority": "s1-experience/v0",
                "claimCeiling": ["IMAGE_DEFORMATION != PHYSICAL_DEFORMATION"],
            },
            "measurement": {
                "intrinsic": {}, "extrinsic": {}, "curvature": {},
                "topology": {}, "projection": {},
            },
        })
        dimensional = project_dimensional_record({
            "version": "s1-dimension-ladder/v0",
            "boundary": "ADJACENT_DIMENSIONS_RELATED != ADJACENT_DIMENSIONS_IDENTICAL",
            "ladder": [0,1,2,3,4],
            "projectionLoss": {
                "map": "drop coordinate 2",
                "sourceA": [1,2,3], "sourceB": [1,2,9],
                "projectionA": [1,2], "projectionB": [1,2],
                "sameProjection": True, "sourcePointsDistinct": True,
            },
            "claimCeiling": ["finite Euclidean fixtures only"],
        })
        self.assertEqual(gsfl["evidence"][0]["kind"], "reported-software-verification")
        for omega in (image, dimensional):
            self.assertEqual(omega["evidence"][0]["kind"], "structural-projection")
        for omega in (gsfl, image, dimensional):
            self.assertNotIn("software-verification", {x["kind"] for x in omega["evidence"]})


if __name__ == "__main__":
    unittest.main()
