import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import FailureKind, VerificationResult
from experiment import (
    certify_effect,
    fused_commit_parts,
    hidden_mode_obligation,
    invalid_cheap_parts,
    open_loop_parts,
    reference_probe_parts,
    verify_hidden_mode,
)


class ExperimentTests(unittest.TestCase):
    def test_all_candidates_use_same_obligation(self):
        obligation = hidden_mode_obligation()
        for candidate in (reference_probe_parts(obligation), fused_commit_parts(obligation), open_loop_parts(obligation)):
            self.assertEqual(candidate.obligation_id, obligation.stable_id)
            self.assertEqual(candidate.spec.obligation_version, obligation.version)

    def test_obligation_does_not_bake_optional_sensor_or_memory_into_requirements(self):
        obligation = hidden_mode_obligation()
        self.assertEqual(set(obligation.required_capabilities), {"transition", "decide"})

    def test_failed_assembly_cannot_receive_emergent_effect_certificate(self):
        failed = VerificationResult.fail(FailureKind.UNSATISFIED, "missed hidden mode")
        with self.assertRaises(ValueError):
            certify_effect(failed, "DISTINGUISHES(mode0,mode1)", "bad")

    def test_fused_diagnostic_value_is_system_effect_not_part_capability(self):
        candidate = fused_commit_parts(hidden_mode_obligation())
        action_part = next(p for p in candidate.parts if p.stable_id == "fused.commit_action")
        self.assertNotIn("infer", action_part.provides)
        result = verify_hidden_mode(candidate)
        self.assertTrue(result.passed)
        cert = certify_effect(result, "DISTINGUISHES(mode0,mode1)", candidate.stable_id)
        self.assertEqual(cert.assembly_id, candidate.stable_id)

    def test_probe_fused_and_open_loop_all_satisfy_same_reach_obligation(self):
        obligation = hidden_mode_obligation()
        results = {
            c.stable_id: verify_hidden_mode(c)
            for c in (reference_probe_parts(obligation), fused_commit_parts(obligation), open_loop_parts(obligation))
        }
        self.assertTrue(all(r.passed for r in results.values()))
        self.assertEqual(dict(results["synthetic.probe_baseline"].metrics)["worst_case_steps"], 3)
        self.assertEqual(dict(results["pass08.fused_commit"].metrics)["worst_case_steps"], 3)
        self.assertEqual(dict(results["openloop.312"].metrics)["worst_case_steps"], 3)

    def test_invalid_cheap_candidate_is_unsatisfied_not_dominated(self):
        candidate = invalid_cheap_parts(hidden_mode_obligation())
        result = verify_hidden_mode(candidate)
        self.assertFalse(result.passed)
        self.assertEqual(result.failure_kind, FailureKind.UNSATISFIED)

    def test_costs_show_probe_baseline_is_dominated_but_fused_and_openloop_trade_off(self):
        obligation = hidden_mode_obligation()
        probe = reference_probe_parts(obligation)
        fused = fused_commit_parts(obligation)
        openloop = open_loop_parts(obligation)
        self.assertTrue(fused.spec.cost.dominates(probe.spec.cost))
        self.assertTrue(openloop.spec.cost.dominates(probe.spec.cost))
        self.assertFalse(fused.spec.cost.dominates(openloop.spec.cost))
        self.assertFalse(openloop.spec.cost.dominates(fused.spec.cost))


if __name__ == "__main__":
    unittest.main()
