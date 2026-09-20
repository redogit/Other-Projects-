"""Public runtime regressions for intersecting independent resource limits."""
from copy import deepcopy
import json
import unittest

from omega import canonical_json, make_omega
from rmapl import parse_rmapl
from rmapl_runtime import run_program


def source(bounds):
    return make_omega(
        native_type="resource-limit-fixture/v0",
        native_identity="fixture:runtime-bounds",
        source_refs=["fixture:runtime-bounds"],
        state={"x": 0},
        path=[],
        frame={"obligation": "bounded-progress"},
        invariants=["identity", "claim-ceiling"],
        observations=[],
        residuals=[{"kind": "gap"}],
        decision_field={"goal": "progress-within-limits"},
        provenance=[{"kind": "fixture"}],
        evidence=[],
        claim_ceiling=["BOUNDED_SOFTWARE_FIXTURE"],
        resource_bounds=bounds,
        domain_remainder={},
    )


def program(bounds, operators=(), evidence=()):
    lines = ["RMAPL 0", "PROGRAM bounds-test", "LOAD fixture"]
    lines += [f"BOUND {name}={json.dumps(value)}" for name, value in bounds.items()]
    for name in operators:
        lines += [
            f"REPAIR {name}", 'WHEN "gap"', "REQUIRES []",
            'TARGETS ["gap"]', 'PRESERVES ["identity","claim-ceiling"]',
            'MAY_MUTATE ["state.x"]', 'FORBIDS ["evidence","provenance"]',
            f"APPLY {name}", f"EVIDENCE {json.dumps(list(evidence))}",
            "COST 1", "END",
        ]
    return parse_rmapl("\n".join([*lines, "RUN", ""]))


def progress_operator(calls):
    def progress(omega):
        calls.append(omega["state"]["x"])
        args = deepcopy(omega["construction"])
        args["state"]["x"] += 1
        candidate = make_omega(**args)
        return {
            "omega": candidate,
            "consequenceKey": f"x={candidate['state']['x']}",
            "metrics": {
                "residualReduction": 1.0, "invariantPreservation": 1.0,
                "reconstructibility": 1.0, "reversibility": 1.0,
                "evidenceCoverage": 1.0, "branchReduction": 1.0,
                "provenanceCompleteness": 1.0, "semanticLoss": 0.0,
                "ambiguityIntroduction": 0.0, "relationGrowth": 0.0,
                "runtimeCost": 1.0, "economicCost": 0.0,
                "unresolvedGrowth": 0.0, "irreversibleMutation": 0.0,
            },
            "knowledgeDecay": {},
            "reconstruction": {"status": "exact"},
        }
    return progress


class RuntimeBoundContractTests(unittest.TestCase):
    def test_input_candidate_limit_cannot_be_widened_by_program(self):
        calls = []
        op = progress_operator(calls)
        result = run_program(
            program({"maxCandidates": 4, "maxSteps": 1}, ("a", "b")),
            source({"maxCandidates": 1, "maxSteps": 1}), {"a": op, "b": op},
        )
        self.assertEqual(calls, [0])
        self.assertEqual(result["generation"]["maxCandidates"], 1)
        self.assertEqual(result["generation"]["executedCount"], 1)
        self.assertEqual(result["generation"]["prunedCount"], 1)
        self.assertEqual(result["generation"]["truncationReason"], "maxCandidates")

    def test_input_step_limit_cannot_be_widened_by_program(self):
        calls = []
        result = run_program(
            program({"maxSteps": 3}, ("advance",)), source({"maxSteps": 1}),
            {"advance": progress_operator(calls)},
        )
        self.assertEqual(calls, [0])
        self.assertEqual(result["generation"]["maxSteps"], 1)
        self.assertEqual(result["generation"]["stepsExecuted"], 1)
        self.assertEqual(result["stopReason"], "RESOURCE_BOUND")
        self.assertEqual(result["branches"][0]["omega"]["residuals"], [{"kind": "gap"}])

    def test_program_can_tighten_both_input_limits(self):
        result = run_program(
            program({"maxCandidates": 2, "maxSteps": 1}),
            source({"maxCandidates": 8, "maxSteps": 4}), {},
        )
        self.assertEqual(result["generation"]["maxCandidates"], 2)
        self.assertEqual(result["generation"]["maxSteps"], 1)

    def test_each_limit_uses_its_own_stricter_source(self):
        result = run_program(
            program({"maxCandidates": 2, "maxSteps": 4}),
            source({"maxCandidates": 8, "maxSteps": 1}), {},
        )
        self.assertEqual(result["generation"]["maxCandidates"], 2)
        self.assertEqual(result["generation"]["maxSteps"], 1)

    def test_absent_limits_keep_existing_defaults(self):
        result = run_program(program({}), source({}), {})
        self.assertEqual(result["generation"]["maxCandidates"], 32)
        self.assertEqual(result["generation"]["maxSteps"], 1)

    def test_one_sided_declarations_are_not_capped_by_defaults(self):
        declared = {"maxCandidates": 40, "maxSteps": 3}
        for input_bounds, program_bounds in ((declared, {}), ({}, declared)):
            with self.subTest(input_bounds=input_bounds, program_bounds=program_bounds):
                result = run_program(program(program_bounds), source(input_bounds), {})
                self.assertEqual(result["generation"]["maxCandidates"], 40)
                self.assertEqual(result["generation"]["maxSteps"], 3)

    def test_invalid_input_limit_is_not_hidden_by_valid_program_limit(self):
        invalid = (0, -1, True, False, 1.0, "2", None, [], {})
        for name in ("maxCandidates", "maxSteps"):
            for value in invalid:
                with self.subTest(name=name, value=value):
                    calls = []
                    with self.assertRaisesRegex(ValueError, name + ".*positive integer"):
                        run_program(program({name: 2}, ("advance",)), source({name: value}),
                                    {"advance": progress_operator(calls)})
                    self.assertEqual(calls, [])

    def test_invalid_program_limit_is_not_hidden_by_valid_input_limit(self):
        for name in ("maxCandidates", "maxSteps"):
            for value in (0, -1, True, False, 1.0, "2", None, [], {}):
                with self.subTest(name=name, value=value):
                    calls = []
                    with self.assertRaisesRegex(ValueError, name + ".*positive integer"):
                        run_program(program({name: value}, ("advance",)), source({name: 2}),
                                    {"advance": progress_operator(calls)})
                    self.assertEqual(calls, [])

    def test_non_mapping_input_bounds_fail_before_operator_execution(self):
        for value in ([], [["maxSteps", 1]], "", "bad", 3, None, True):
            with self.subTest(value=value):
                calls = []
                with self.assertRaises((TypeError, ValueError)) as caught:
                    run_program(program({"maxSteps": 2}, ("advance",)), source(value),
                                {"advance": progress_operator(calls)})
                self.assertIsInstance(caught.exception, TypeError)
                self.assertRegex(str(caught.exception), "resourceBounds.*mapping")
                self.assertEqual(calls, [])

    def test_inputs_and_unrelated_metadata_are_preserved(self):
        bounds = {"maxSteps": 1, "domain": {"units": ["native", None]}}
        omega = source(bounds)
        p = program({"maxSteps": 3, "domain": {"label": [1, None]}})
        before = canonical_json(omega)
        run_program(p, omega, {})
        self.assertEqual(canonical_json(omega), before)
        self.assertEqual(bounds, {"maxSteps": 1, "domain": {"units": ["native", None]}})
        self.assertEqual(p.bounds["maxSteps"], 3)
        self.assertEqual(p.bounds["domain"]["label"], (1, None))

    def test_replay_is_deterministic_with_intersected_limits(self):
        p = program({"maxSteps": 5}, ("advance",))
        omega = source({"maxSteps": 2})
        first = run_program(p, omega, {"advance": progress_operator([])})
        second = run_program(p, omega, {"advance": progress_operator([])})
        self.assertEqual(canonical_json(first), canonical_json(second))
        self.assertEqual(first["generation"]["executedCount"], 2)

    def test_evidence_gate_still_blocks_unauthorized_candidate(self):
        calls = []
        result = run_program(
            program({"maxSteps": 3}, ("advance",), evidence=("independent-check",)),
            source({"maxSteps": 1}), {"advance": progress_operator(calls)},
        )
        self.assertEqual(calls, [])
        self.assertEqual(result["stopReason"], "EVIDENCE_BOUND")
        self.assertEqual(result["generation"]["executedCount"], 0)


if __name__ == "__main__":
    unittest.main()
