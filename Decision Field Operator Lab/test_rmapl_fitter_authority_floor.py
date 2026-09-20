import unittest

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_runtime import run_program


def metrics(**overrides):
    values = {
        "residualReduction": 1,
        "invariantPreservation": 1,
        "reconstructibility": 1,
        "reversibility": 1,
        "evidenceCoverage": 1,
        "branchReduction": 1,
        "provenanceCompleteness": 1,
        "semanticLoss": 0,
        "ambiguityIntroduction": 0,
        "relationGrowth": 0,
        "runtimeCost": 0,
        "economicCost": 0,
        "unresolvedGrowth": 0,
        "irreversibleMutation": 0,
    }
    values.update(overrides)
    return values


def source_omega():
    return make_omega(
        native_type="fixture/v0",
        native_identity="fixture:authority-floor",
        source_refs=("fixture:source",),
        state={"x": 0, "protected": 7},
        path=(),
        frame={"obligation": "fit-x"},
        invariants=("state.protected",),
        observations=(),
        residuals=({"kind": "x-residual", "detail": "x != 1"},),
        decision_field={"goal": "x=1"},
        provenance=({"kind": "fixture", "ref": "authority-floor"},),
        evidence=(
            {
                "kind": "software-verification",
                "detail": "fixture",
                "claimCeiling": "BOUNDED",
            },
        ),
        claim_ceiling=("SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",),
        resource_bounds={"maxCandidates": 8, "maxSteps": 1},
        domain_remainder={"native": "synthetic"},
    )


def fitter_program():
    return parse_rmapl(
        """RMAPL 0
PROGRAM fitter-authority-floor
LOAD fixture
BOUND maxCandidates=8
BOUND maxSteps=1
FITTER fit
WHEN "x-residual"
REQUIRES []
PRESERVES ["state.protected"]
OBJECTIVES {"residualReduction":"max"}
APPLY fitter_op
EVIDENCE []
COST 1
END
RUN
"""
    )


def updated(omega, **changes):
    args = dict(omega["construction"])
    args.update(changes)
    return make_omega(**args)


def proposal(candidate):
    return {
        "omega": candidate,
        "consequenceKey": "candidate",
        "metrics": metrics(),
        "knowledgeDecay": {
            "loss": [],
            "introduction": [],
            "aliasing": [],
            "ambiguity": [],
            "provenanceGap": [],
            "reconstructionCost": 0,
            "oracleShift": [],
            "unresolvedGrowth": [],
        },
        "reconstruction": {"status": "exact"},
    }


class FitterAuthorityFloorTests(unittest.TestCase):
    def run_candidate(self, transform):
        source = source_omega()

        def fitter_op(value):
            return proposal(transform(value))

        return run_program(fitter_program(), source, {"fitter_op": fitter_op})

    def assert_authority_rejected(self, transform, expected_path):
        result = self.run_candidate(transform)
        self.assertEqual(result["stopReason"], "NO_ADMISSIBLE_PROGRESS")
        self.assertEqual(len(result["branches"]), 1)
        branch = result["branches"][0]
        self.assertEqual(branch["classification"], "MUTATION")
        self.assertFalse(branch["admitted"])
        self.assertIn(expected_path, branch["inspection"]["mutated"])
        gate = next(
            item
            for item in branch["inspection"]["gates"]
            if item["name"] == "fitter_authority"
        )
        self.assertEqual(gate["status"], "failed")
        self.assertIn(expected_path, gate["paths"])

    def test_fitter_cannot_change_native_identity(self):
        self.assert_authority_rejected(
            lambda value: updated(
                value,
                native_identity="fixture:authority-floor:rewritten",
                state={"x": 1, "protected": 7},
                residuals=(),
            ),
            "nativeIdentity",
        )

    def test_fitter_cannot_change_source_refs(self):
        self.assert_authority_rejected(
            lambda value: updated(
                value,
                source_refs=("fixture:other-source",),
                state={"x": 1, "protected": 7},
                residuals=(),
            ),
            "sourceRefs",
        )

    def test_fitter_cannot_change_evidence(self):
        self.assert_authority_rejected(
            lambda value: updated(
                value,
                evidence=(
                    {
                        "kind": "scientific-validation",
                        "detail": "synthetic escalation",
                        "claimCeiling": "UNBOUNDED",
                    },
                ),
                state={"x": 1, "protected": 7},
                residuals=(),
            ),
            "evidence",
        )

    def test_fitter_cannot_change_claim_ceiling(self):
        self.assert_authority_rejected(
            lambda value: updated(
                value,
                claim_ceiling=("PROVED",),
                state={"x": 1, "protected": 7},
                residuals=(),
            ),
            "claimCeiling",
        )

    def test_fitter_cannot_change_provenance(self):
        self.assert_authority_rejected(
            lambda value: updated(
                value,
                provenance=({"kind": "fixture", "ref": "rewritten"},),
                state={"x": 1, "protected": 7},
                residuals=(),
            ),
            "provenance",
        )

    def test_fitter_can_refit_ordinary_state_when_declared_preserve_survives(self):
        result = self.run_candidate(
            lambda value: updated(
                value,
                state={"x": 1, "protected": 7},
                residuals=(),
            )
        )
        self.assertEqual(result["stopReason"], "SUCCESS")
        branch = result["branches"][0]
        self.assertEqual(branch["classification"], "VALID_REFIT")
        self.assertTrue(branch["admitted"])
        self.assertFalse(
            any(item["name"] == "fitter_authority" for item in branch["inspection"]["gates"])
        )


if __name__ == "__main__":
    unittest.main()
