import unittest

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_runtime import (
    CandidateOutcome,
    ClaimSpec,
    KnowledgeDecay,
    admit_claim,
    pareto_frontier,
    run_program,
)


MAX_KEYS = (
    "residualReduction",
    "invariantPreservation",
    "reconstructibility",
    "reversibility",
    "evidenceCoverage",
    "branchReduction",
    "provenanceCompleteness",
)
MIN_KEYS = (
    "semanticLoss",
    "ambiguityIntroduction",
    "relationGrowth",
    "runtimeCost",
    "economicCost",
    "unresolvedGrowth",
    "irreversibleMutation",
)


def metrics(**overrides):
    values = {key: 1.0 for key in MAX_KEYS}
    values.update({key: 0.0 for key in MIN_KEYS})
    values.update(overrides)
    return values


def kd(**overrides):
    values = dict(
        loss=(),
        introduction=(),
        aliasing=(),
        ambiguity=(),
        provenance_gap=(),
        reconstruction_cost=0.0,
        oracle_shift=(),
        unresolved_growth=(),
    )
    values.update(overrides)
    return KnowledgeDecay(**values)


def omega_with_residual(kind="x-residual", state=None, evidence=("software-verification",), max_steps=1):
    return make_omega(
        native_type="synthetic/v0",
        native_identity="fixture:runtime:1",
        source_refs=("fixture:runtime:1",),
        state=state or {"x": 0, "protected": 7},
        path=(),
        frame={"obligation": "repair-x"},
        invariants=("state.protected", "claim-ceiling"),
        observations=(),
        residuals=({"kind": kind, "detail": "fixture"},),
        decision_field={"goal": "x=1"},
        provenance=({"kind": "fixture", "ref": "runtime"},),
        evidence=tuple(
            {"kind": item, "detail": "fixture", "claimCeiling": "BOUNDED"}
            for item in evidence
        ),
        claim_ceiling=("SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",),
        resource_bounds={"maxCandidates": 8, "maxSteps": max_steps},
        domain_remainder={"native": "synthetic"},
    )


def updated(omega, *, state=None, residuals=None, provenance=None):
    args = dict(omega["construction"])
    if state is not None:
        args["state"] = state
    if residuals is not None:
        args["residuals"] = residuals
    if provenance is not None:
        args["provenance"] = provenance
    return make_omega(**args)


def proposal(candidate, consequence, *, metric_values=None, decay=None, reconstruction="exact"):
    return {
        "omega": candidate,
        "consequenceKey": consequence,
        "metrics": metric_values or metrics(),
        "knowledgeDecay": decay or {
            "loss": [],
            "introduction": [],
            "aliasing": [],
            "ambiguity": [],
            "provenanceGap": [],
            "reconstructionCost": 0,
            "oracleShift": [],
            "unresolvedGrowth": [],
        },
        "reconstruction": {"status": reconstruction},
    }


def program(repairs, *, max_candidates=8, max_steps=1):
    blocks = []
    for rid, operator, evidence, preserves in repairs:
        blocks.append(
            f"""REPAIR {rid}
WHEN "x-residual"
REQUIRES []
TARGETS ["x-residual"]
PRESERVES {preserves}
MAY_MUTATE ["state.x","residuals"]
FORBIDS ["provenance","evidence"]
APPLY {operator}
EVIDENCE {evidence}
COST 1
END"""
        )
    return parse_rmapl(
        "RMAPL 0\n"
        "PROGRAM runtime-test\n"
        "LOAD fixture\n"
        f"BOUND maxCandidates={max_candidates}\n"
        f"BOUND maxSteps={max_steps}\n"
        + "\n".join(blocks)
        + "\nRUN\n"
    )


class RuntimeTests(unittest.TestCase):
    def test_claim_local_evidence_does_not_amplify(self):
        claim = ClaimSpec("science", ("scientific-validation",), ())
        self.assertFalse(admit_claim(claim, {"software-verification"}))
        self.assertTrue(
            admit_claim(
                claim,
                {"scientific-validation", "software-verification"},
            )
        )

    def test_equivalent_candidates_are_quotiented_with_provenance_union(self):
        source = omega_with_residual()
        p = program([
            ("a", "repair_a", "[]", '["state.protected"]'),
            ("b", "repair_b", "[]", '["state.protected"]'),
        ])

        def repair_a(value):
            candidate = updated(value, state={"x": 1, "protected": 7}, residuals=[])
            return proposal(candidate, "x=1")

        def repair_b(value):
            candidate = updated(
                value,
                state={"x": 1, "protected": 7},
                residuals=[],
                provenance=[{"kind": "fixture", "ref": "other-route"}],
            )
            return proposal(candidate, "x=1")

        result = run_program(p, source, {"repair_a": repair_a, "repair_b": repair_b})
        self.assertEqual(result["generation"]["equivalenceClassCount"], 1)
        self.assertEqual(result["branches"][0]["sourceCandidateIds"], ["a", "b"])

    def test_pareto_incomparable_candidates_remain_separate(self):
        source = omega_with_residual()
        a = CandidateOutcome(
            candidate_id="a",
            omega=source,
            consequence_key="a",
            classification="EXACT_REPAIR",
            admitted=True,
            metrics=metrics(residualReduction=2, semanticLoss=1),
            knowledge_decay=kd(),
            inspection={},
            source_candidate_ids=("a",),
        )
        b = CandidateOutcome(
            candidate_id="b",
            omega=source,
            consequence_key="b",
            classification="EXACT_REPAIR",
            admitted=True,
            metrics=metrics(residualReduction=1, semanticLoss=0),
            knowledge_decay=kd(),
            inspection={},
            source_candidate_ids=("b",),
        )
        self.assertEqual([x.candidate_id for x in pareto_frontier((a, b))], ["a", "b"])

    def test_repair_breaking_protected_invariant_is_rejected_even_if_residual_falls(self):
        source = omega_with_residual()
        p = program([("break", "break_protected", "[]", '["state.protected"]')])

        def break_protected(value):
            candidate = updated(value, state={"x": 1, "protected": 8}, residuals=[])
            return proposal(candidate, "x=1")

        result = run_program(p, source, {"break_protected": break_protected})
        self.assertEqual(result["branches"][0]["classification"], "MUTATION")
        self.assertFalse(result["branches"][0]["admitted"])

    def test_mutating_operator_input_is_rejected(self):
        source = omega_with_residual()
        p = program([("bad", "bad_operator", "[]", '["state.protected"]')])

        def bad_operator(value):
            value["state"]["x"] = 2
            return proposal(value, "bad")

        with self.assertRaisesRegex(ValueError, "mutated input"):
            run_program(p, source, {"bad_operator": bad_operator})

    def test_cycle_and_resource_fact_are_both_recorded_with_cycle_precedence(self):
        source = omega_with_residual(max_steps=1)
        p = program([("loop", "loop", "[]", '["state.protected"]')], max_steps=1)

        def loop(value):
            return proposal(updated(value), "same")

        result = run_program(p, source, {"loop": loop})
        self.assertIn("REPEATED_STATE_CYCLE", result["stopFacts"])
        self.assertIn("RESOURCE_BOUND", result["stopFacts"])
        self.assertEqual(result["stopReason"], "REPEATED_STATE_CYCLE")

    def test_missing_required_evidence_stops_at_evidence_bound(self):
        source = omega_with_residual(evidence=("software-verification",))
        p = program([
            ("science", "repair_x", '["scientific-validation"]', '["state.protected"]'),
        ])

        def repair_x(value):
            return proposal(updated(value, residuals=[]), "x=1")

        result = run_program(p, source, {"repair_x": repair_x})
        self.assertEqual(result["stopReason"], "EVIDENCE_BOUND")
        self.assertEqual(result["generation"]["executedCount"], 0)

    def test_kd_dimensions_are_separate(self):
        decay = KnowledgeDecay(
            loss=("x",),
            introduction=("y",),
            aliasing=(),
            ambiguity=(),
            provenance_gap=(),
            reconstruction_cost=1,
            oracle_shift=(),
            unresolved_growth=(),
        )
        self.assertEqual(decay.loss, ("x",))
        self.assertEqual(decay.introduction, ("y",))
        self.assertEqual(decay.reconstruction_cost, 1)

    def test_max_candidates_bound_is_recorded_and_deterministic(self):
        source = omega_with_residual()
        p = program(
            [
                ("a", "a_op", "[]", '["state.protected"]'),
                ("b", "b_op", "[]", '["state.protected"]'),
            ],
            max_candidates=1,
        )

        def op(value):
            return proposal(updated(value, residuals=[]), "done")

        result = run_program(p, source, {"a_op": op, "b_op": op})
        self.assertEqual(result["generation"]["generatedCount"], 2)
        self.assertEqual(result["generation"]["executedCount"], 1)
        self.assertEqual(result["generation"]["prunedCount"], 1)
        self.assertEqual(result["generation"]["truncationReason"], "maxCandidates")

    def test_rejected_mutation_cannot_pareto_dominate_admitted_repair(self):
        source = omega_with_residual()
        p = program([
            ("good", "good_op", "[]", '["state.protected"]'),
            ("bad", "bad_op", "[]", '["state.protected"]'),
        ])

        def good_op(value):
            candidate = updated(value, state={"x": 1, "protected": 7}, residuals=[])
            return proposal(
                candidate, "good",
                metric_values=metrics(
                    residualReduction=1,
                    invariantPreservation=1,
                    semanticLoss=0,
                ),
            )

        def bad_op(value):
            candidate = updated(value, state={"x": 1, "protected": 8}, residuals=[])
            return proposal(
                candidate, "bad",
                metric_values=metrics(
                    residualReduction=100,
                    invariantPreservation=100,
                    reconstructibility=100,
                    reversibility=100,
                    evidenceCoverage=100,
                    branchReduction=100,
                    provenanceCompleteness=100,
                    semanticLoss=0,
                ),
            )

        result = run_program(p, source, {"good_op": good_op, "bad_op": bad_op})
        self.assertEqual(result["stopReason"], "SUCCESS")
        self.assertTrue(any(x["candidateId"] == "good" and x["admitted"] for x in result["branches"]))

    def test_mutation_and_valid_repair_with_same_consequence_are_not_quotiented_together(self):
        source = omega_with_residual()
        p = program([
            ("good", "good_op", "[]", '["state.protected"]'),
            ("bad", "bad_op", "[]", '["state.protected"]'),
        ])

        def good_op(value):
            return proposal(
                updated(value, state={"x": 1, "protected": 7}, residuals=[]),
                "x=1",
            )

        def bad_op(value):
            return proposal(
                updated(value, state={"x": 1, "protected": 8}, residuals=[]),
                "x=1",
            )

        result = run_program(p, source, {"good_op": good_op, "bad_op": bad_op})
        self.assertEqual(result["generation"]["equivalenceClassCount"], 2)
        classes = {(x["candidateId"], x["classification"]) for x in result["branches"]}
        self.assertIn(("good", "EXACT_REPAIR"), classes)
        self.assertIn(("bad", "MUTATION"), classes)


if __name__ == "__main__":
    unittest.main()
