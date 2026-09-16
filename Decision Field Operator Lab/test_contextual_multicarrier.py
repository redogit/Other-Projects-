import unittest

import contextual_multicarrier as cm


class ContextualMultiCarrierTests(unittest.TestCase):
    def test_same_word_binds_differently_by_context(self):
        boundary = cm.resolve_roles("gate", {
            "surface": "conversation", "context": "gate this result until verification",
            "interpreter": "human", "time_label": "t1", "obligation": "admission control",
            "relations": []
        })
        transition = cm.resolve_roles("gate", {
            "surface": "conversation", "context": "the gate carried us into another space",
            "interpreter": "human", "time_label": "t2", "obligation": "describe transition",
            "relations": []
        })
        self.assertIn("GATE", boundary["active_roles"])
        self.assertNotEqual(boundary["active_roles"], transition["active_roles"])
        self.assertIn("TRANSITION", transition["active_roles"])

    def test_one_occurrence_can_have_multiple_roles(self):
        binding = cm.resolve_roles("wave", {
            "surface": "conversation", "context": "the wave carries and propagates the message",
            "interpreter": "machine", "time_label": "t1", "obligation": "trace message movement",
            "relations": [], "role_hints": {"PROPAGATION": 1.0, "CARRIER": 0.9}
        })
        self.assertIn("PROPAGATION", binding["active_roles"])
        self.assertIn("CARRIER", binding["active_roles"])

    def test_interpreters_remain_separate(self):
        h = cm.resolve_roles("turn", {"surface":"chat","context":"turn toward the evidence","interpreter":"human","time_label":"t","obligation":"navigate","relations":[],"role_hints":{"DIRECTION":1.0}})
        m = cm.resolve_roles("turn", {"surface":"chat","context":"turn transforms the branch","interpreter":"machine","time_label":"t","obligation":"transform","relations":[],"role_hints":{"TRANSFORM":1.0}})
        self.assertEqual("human", h["interpreter"])
        self.assertEqual("machine", m["interpreter"])
        self.assertNotEqual(h["active_roles"], m["active_roles"])

    def test_projection_has_four_carriers_and_claim_ceilings(self):
        source = self.source()
        records = cm.project_carriers(source, self.carrier_inputs())
        self.assertEqual({"SYMBOLIC","ANALYTICAL","COMPUTATIONAL","ANALOGICAL"}, set(records))
        for record in records.values():
            self.assertEqual(source["invariants"], record["invariants"])
            self.assertTrue(record["claim_ceiling"])
            self.assertTrue(record["provenance"])
            self.assertEqual("NONE", record["authority_effect"])
        self.assertFalse(records["ANALOGICAL"]["evidence_transfer"])

    def test_compare_detects_loss_and_introduction(self):
        source = self.source()
        records = cm.project_carriers(source, self.carrier_inputs())
        records["ANALYTICAL"]["invariants"].pop("provenance")
        records["COMPUTATIONAL"]["invariants"]["invented"] = True
        comparison = cm.compare_carriers(source, records)
        self.assertIn("provenance", comparison["carrier_deltas"]["ANALYTICAL"]["losses"])
        self.assertIn("invented", comparison["carrier_deltas"]["COMPUTATIONAL"]["introductions"])
        self.assertEqual("NOT_ESTABLISHED", comparison["independence_state"])

    def test_agreement_does_not_establish_independence(self):
        source = self.source()
        records = cm.project_carriers(source, self.carrier_inputs())
        comparison = cm.compare_carriers(source, records)
        self.assertEqual(4, comparison["agreement_count"])
        self.assertEqual("NOT_ESTABLISHED", comparison["independence_state"])

    def test_bbf_analogy_preserved(self):
        report = cm.bbf_analogy_check(
            {"distinction":"preserved", "authority":"local"},
            {"distinction":"target_distinction", "authority":"target_authority"},
            {"distinction":"preserved", "authority":"local"},
        )
        self.assertEqual("PRESERVED", report["status"])
        self.assertFalse(report["evidence_transfer"])

    def test_bbf_analogy_detects_loss_and_introduction(self):
        loss = cm.bbf_analogy_check({"a":1,"b":2}, {"a":"x","b":"y"}, {"a":1})
        intro = cm.bbf_analogy_check({"a":1}, {"a":"x"}, {"a":1,"c":3})
        self.assertEqual("LOSS", loss["status"])
        self.assertIn("b", loss["losses"])
        self.assertEqual("INTRODUCED", intro["status"])
        self.assertIn("c", intro["introductions"])

    def test_confound_audit_catches_cross_carrier_overclaims(self):
        findings = cm.audit_multicarrier_confounds({
            "static_role_claim": True,
            "collapsed_interpreters": True,
            "agreement_claims_truth": True,
            "agreement_claims_independence": True,
            "analogy_evidence_transfer": True,
            "computation_claims_universal": True,
            "analysis_claims_empirical": True,
            "symbol_claims_truth": True,
            "fit_attempted": True,
            "fit_candidate_admitted": False,
        })
        ids = {row["id"] for row in findings}
        expected = {
            "STATIC_ROLE_FALLACY","INTERPRETER_COLLAPSE","AGREEMENT_AS_TRUTH",
            "AGREEMENT_AS_INDEPENDENCE","ANALOGY_AS_EVIDENCE_TRANSFER",
            "COMPUTATION_AS_GENERAL_PROOF","ANALYSIS_AS_EMPIRICAL_VALIDATION",
            "SYMBOLIC_COMPRESSION_AS_TRUTH","FIT_BEFORE_ADMISSION"
        }
        self.assertTrue(expected.issubset(ids))

    def test_gate_reopens_agreement_only_candidate(self):
        source = self.source()
        comparison = cm.compare_carriers(source, cm.project_carriers(source, self.carrier_inputs()))
        result = cm.gate_disposition(
            {"admitted":False, "verification_passed":False, "claim_ceiling":"bounded", "source_invariants_preserved":True},
            comparison,
            [],
        )
        self.assertEqual("REOPEN", result["disposition"])
        self.assertIn("admission", " ".join(result["reasons"]).lower())

    def test_gate_promotes_verified_admitted_bounded_successor(self):
        source = self.source()
        comparison = cm.compare_carriers(source, cm.project_carriers(source, self.carrier_inputs()))
        result = cm.gate_disposition(
            {"admitted":True, "verification_passed":True, "claim_ceiling":"bounded fixture only", "source_invariants_preserved":True},
            comparison,
            [],
        )
        self.assertEqual("PROMOTE_SUCCESSOR", result["disposition"])

    def test_canonical_json_is_deterministic(self):
        obj = {"b":2,"a":1}
        self.assertEqual(cm.canonical_json(obj), cm.canonical_json({"a":1,"b":2}))

    @staticmethod
    def source():
        return {
            "id":"semantic-object-1",
            "meaning":{"thesis":"same object, multiple views"},
            "invariants":{"meaning":"preserved", "provenance":"attached", "authority":"bounded"},
            "claim_ceiling":"bounded calibration only",
        }

    @staticmethod
    def carrier_inputs():
        inv = {"meaning":"preserved", "provenance":"attached", "authority":"bounded"}
        return {
            "SYMBOLIC":{"representation":"M -> {S,A,C,G}", "invariants":dict(inv), "provenance":"fixture:symbolic"},
            "ANALYTICAL":{"representation":{"premises":["one object","four views"]}, "invariants":dict(inv), "provenance":"fixture:analytical"},
            "COMPUTATIONAL":{"representation":{"finite_check":True}, "invariants":dict(inv), "provenance":"fixture:computational", "bound":"finite fixture"},
            "ANALOGICAL":{"representation":{"source":"lens","target":"carrier"}, "invariants":dict(inv), "provenance":"fixture:analogical"},
        }


if __name__ == "__main__":
    unittest.main()
