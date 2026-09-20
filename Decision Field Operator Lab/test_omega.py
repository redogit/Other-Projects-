import json
from pathlib import Path
import unittest

from omega import (
    OMEGA_SCHEMA,
    canonical_json,
    make_inspection_record,
    make_omega,
    round_trip_report,
    validate_omega,
)


def fixture_omega(**overrides):
    args = dict(
        native_type="decision-field/v1",
        native_identity="fixture:df:1",
        source_refs=("fixture:df:1",),
        state={"possibilities": [0, 1]},
        path=(),
        frame={"obligation": "select-1"},
        invariants=("goal-preserved",),
        observations=(),
        residuals=({"kind": "unresolved", "detail": "0 remains"},),
        decision_field={"goal": 1},
        provenance=({"kind": "fixture", "ref": "omega_decision_field_native.json"},),
        evidence=(
            {
                "kind": "software-verification",
                "detail": "fixture",
                "claimCeiling": "BOUNDED",
            },
        ),
        claim_ceiling=("SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",),
        resource_bounds={"maxCandidates": 8},
        domain_remainder={"nativeOnly": {"relations": []}},
    )
    args.update(overrides)
    return make_omega(**args)


class OmegaTests(unittest.TestCase):
    def test_strict_record_is_deterministic_and_closed(self):
        omega = fixture_omega()
        self.assertEqual(validate_omega(omega), omega)
        self.assertEqual(omega["schema"], OMEGA_SCHEMA)
        self.assertEqual(OMEGA_SCHEMA, "rmapl-omega/v0")
        self.assertRegex(omega["id"], r"^[0-9a-f]{64}$")
        self.assertEqual(make_omega(**omega["construction"])["id"], omega["id"])

    def test_unknown_authority_field_fails_closed(self):
        omega = fixture_omega()
        with self.assertRaisesRegex(ValueError, "unsupported omega field"):
            validate_omega({**omega, "truthAuthority": "invented"})

    def test_non_json_and_non_finite_values_fail_closed(self):
        with self.assertRaises(TypeError):
            canonical_json({"x": {1, 2}})
        with self.assertRaises(ValueError):
            canonical_json({"x": float("nan")})

    def test_round_trip_report_separates_preserved_lost_introduced_changed_and_unresolved(self):
        report = round_trip_report(
            {"a": 1, "b": 2, "unknown": None},
            {"a": 1, "b": 3, "c": 4, "unknown": None},
        )
        self.assertEqual(report["preserved"], ["a", "unknown"])
        self.assertEqual(report["lost"], [])
        self.assertEqual(report["introduced"], ["c"])
        self.assertEqual(report["changed"], ["b"])
        self.assertEqual(report["unresolved"], ["unknown"])

    def test_inspection_record_exposes_skipped_gate(self):
        record = make_inspection_record(
            input_refs=["fixture:1"],
            native_contract="decision-field/v1",
            operator="extract",
            operator_version="v0",
            condition="always",
            trigger="adapter",
            preconditions=["native-valid"],
            obligation="project",
            expected="omega",
            actual="omega",
            residual_before=[],
            residual_after=[],
            preserved=["identity"],
            mutated=[],
            lost=[],
            introduced=[],
            reconstruction={"status": "exact"},
            knowledge_decay={"loss": [], "introduction": []},
            evidence=[],
            claim_ceiling=["BOUNDED"],
            counterprobe={"status": "skipped", "reason": "not-applicable"},
            provenance=[],
            resource_bounds={"maxCandidates": 1},
            resource_usage={"executed": 1},
            unresolved=[],
            next_decision=None,
            domain_remainder={},
            gates=[
                {"name": "native-valid", "status": "passed"},
                {"name": "at-validation", "status": "skipped"},
            ],
        )
        self.assertEqual(record["gates"][1]["status"], "skipped")

    def test_identity_covers_claim_ceiling_resource_bounds_and_remainder(self):
        base = fixture_omega()
        changed_ceiling = fixture_omega(claim_ceiling=("DIFFERENT",))
        changed_bounds = fixture_omega(resource_bounds={"maxCandidates": 9})
        changed_remainder = fixture_omega(domain_remainder={"nativeOnly": {"relations": ["x"]}})
        self.assertNotEqual(base["id"], changed_ceiling["id"])
        self.assertNotEqual(base["id"], changed_bounds["id"])
        self.assertNotEqual(base["id"], changed_remainder["id"])

    def test_mutating_caller_after_construction_does_not_mutate_omega(self):
        state = {"possibilities": [0, 1]}
        omega = fixture_omega(state=state)
        state["possibilities"].append(2)
        self.assertEqual(omega["state"], {"possibilities": [0, 1]})

    def test_published_schema_construction_is_satisfiable_by_declared_fields(self):
        schema = json.loads(
            (Path(__file__).parent / "omega.schema.json").read_text(encoding="utf-8")
        )
        construction = schema["properties"]["construction"]
        self.assertEqual(
            set(construction["properties"]),
            set(construction["required"]),
        )
        self.assertIs(construction["additionalProperties"], False)


if __name__ == "__main__":
    unittest.main()
