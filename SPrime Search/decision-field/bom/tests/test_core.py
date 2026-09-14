import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import (
    AssemblySpec,
    CostVector,
    EmergentEffectCertificate,
    FailureKind,
    ObligationSpec,
    PartSpec,
    StepPhase,
    VerificationResult,
    canonical_json,
)


class CoreTests(unittest.TestCase):
    def test_cost_vector_pareto_dominance(self):
        a = CostVector.from_mapping({"memory_bits": 1, "probe_steps": 0})
        b = CostVector.from_mapping({"memory_bits": 1, "probe_steps": 1})
        c = CostVector.from_mapping({"memory_bits": 0, "probe_steps": 2})
        self.assertTrue(a.dominates(b))
        self.assertFalse(b.dominates(a))
        self.assertFalse(a.dominates(c))
        self.assertFalse(c.dominates(a))

    def test_cost_vectors_require_same_declared_dimensions(self):
        a = CostVector.from_mapping({"memory_bits": 1})
        b = CostVector.from_mapping({"probe_steps": 1})
        with self.assertRaises(ValueError):
            a.dominates(b)

    def test_obligation_requires_explicit_step_timing(self):
        with self.assertRaises(ValueError):
            ObligationSpec(
                stable_id="o", version=1, subject="synthetic",
                bounds=(("worlds", 2),), required_capabilities=("transition",),
                protected_invariants=(), success_condition="sure_reach",
                allowed_initial=(0, 1), allowed_actions=(0, 1),
                observable_information=("physical",), permissions=("observe",),
                temporal_semantics="path", step_timing=(), exact_regime=True,
                evidence_threshold="exhaustive", unresolved_remainder=(),
                cost_dimensions=("memory_bits",),
            )

    def test_part_rejects_self_construction_dependency(self):
        with self.assertRaises(ValueError):
            PartSpec(
                stable_id="p", version=1,
                provides=("transition",), requires=("transition",),
                input_ports=(("state", "WorldState"),),
                output_ports=(("next", "WorldState"),),
                state_carried=(), assumptions=(), bounds=(), side_effects=(),
                external_dependencies=(), cost=CostVector.from_mapping({"memory_bits": 0}),
                evidence_refs=(), known_failures=(), replaceability_boundary="same obligation",
            )

    def test_emergent_effect_requires_assembly_and_verifier_evidence(self):
        with self.assertRaises(ValueError):
            EmergentEffectCertificate(
                stable_id="e", version=1, assembly_id="", obligation_id="o",
                effect="DISTINGUISHES(mode0,mode1)", verifier_ref="", evidence_refs=(),
            )

    def test_canonical_json_is_key_and_sequence_stable(self):
        left = {"b": 2, "a": [3, 1]}
        right = {"a": [3, 1], "b": 2}
        self.assertEqual(canonical_json(left), canonical_json(right))
        self.assertEqual(json.loads(canonical_json(left)), left)

    def test_failure_kinds_are_closed(self):
        self.assertEqual(
            {x.value for x in FailureKind},
            {"INCOMPATIBLE", "UNSATISFIED", "UNRESOLVED", "DOMINATED", "OUT_OF_BOUND", "VERIFIER_DISAGREEMENT"},
        )


if __name__ == "__main__":
    unittest.main()
