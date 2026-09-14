import itertools
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalog import PartCatalog
from core import AssemblySpec, CostVector, ObligationSpec, PartSpec, StepPhase
from search import candidate_part_sets, compatible_wirings, construction_order, pareto_frontier


def obligation(required):
    return ObligationSpec(
        stable_id="toy", version=1, subject="toy",
        bounds=(("worlds", 4),), required_capabilities=tuple(required),
        protected_invariants=(), success_condition="exact",
        allowed_initial=(0,), allowed_actions=(0, 1),
        observable_information=("observation",), permissions=("observe",),
        temporal_semantics="one_step",
        step_timing=(StepPhase.PRE_ACTION, StepPhase.TRANSITION, StepPhase.OBSERVATION),
        exact_regime=True, evidence_threshold="exhaustive", unresolved_remainder=(),
        cost_dimensions=("component_count", "memory_bits"),
    )


def part(pid, provides, requires=(), *, in_type="WorldState", out_type="WorldState"):
    return PartSpec(
        stable_id=pid, version=1, provides=tuple(provides), requires=tuple(requires),
        input_ports=(("in", in_type),), output_ports=(("out", out_type),),
        state_carried=(), assumptions=(), bounds=(), side_effects=(), external_dependencies=(),
        cost=CostVector.from_mapping({"component_count": 1, "memory_bits": 0}),
        evidence_refs=(), known_failures=(), replaceability_boundary="toy",
    )


def catalog_of(*parts):
    c = PartCatalog()
    for p in parts:
        c.register(p, lambda: None)
    return c


def assembly(aid, component_count, memory_bits):
    return AssemblySpec(
        stable_id=aid, version=1, obligation_id="toy", obligation_version=1,
        parts=((aid, 1),), wiring=(), covered_capabilities=("transition",), unresolved_gaps=(),
        cost=CostVector.from_mapping({"component_count": component_count, "memory_bits": memory_bits}),
    )


class SearchTests(unittest.TestCase):
    def test_multi_capability_part_and_single_parts_are_both_candidates(self):
        fused = part("fused", ("transition", "observe"))
        t = part("transition", ("transition",))
        o = part("observe", ("observe",))
        got = candidate_part_sets(obligation(("transition", "observe")), catalog_of(fused, t, o))
        ids = {tuple(p.stable_id for p in subset) for subset in got}
        self.assertIn(("fused",), ids)
        self.assertIn(("observe", "transition"), ids)

    def test_candidate_part_sets_match_bruteforce_subset_oracle(self):
        parts = (
            part("t", ("transition",)),
            part("o", ("observe",)),
            part("i", ("infer",), ("transition", "observe")),
            part("f", ("transition", "observe")),
        )
        catalog = catalog_of(*parts)
        for r in range(1, 4):
            for required in itertools.combinations(("transition", "observe", "infer"), r):
                got = {tuple(p.stable_id for p in x) for x in candidate_part_sets(obligation(required), catalog)}
                expected = set()
                for size in range(1, len(parts)+1):
                    for subset in itertools.combinations(sorted(parts, key=lambda p:p.stable_id), size):
                        provided = set().union(*(set(p.provides) for p in subset))
                        if not set(required) <= provided:
                            continue
                        if any(not set(p.requires) <= provided for p in subset):
                            continue
                        expected.add(tuple(p.stable_id for p in subset))
                self.assertEqual(got, expected)

    def test_construction_cycle_is_rejected(self):
        a = part("a", ("transition",), ("observe",))
        b = part("b", ("observe",), ("transition",))
        with self.assertRaises(ValueError):
            construction_order((a, b))

    def test_construction_order_accepts_acyclic_dependencies(self):
        t = part("t", ("transition",))
        i = part("i", ("infer",), ("transition",))
        self.assertEqual([p.stable_id for p in construction_order((i, t))], ["t", "i"])

    def test_compatible_wiring_uses_exact_semantic_types(self):
        producer = part("producer", ("observe",), in_type="Environment", out_type="Observation")
        consumer = part("consumer", ("decide",), in_type="Observation", out_type="Action")
        wiring = compatible_wirings(obligation(("observe", "decide")), (producer, consumer))
        self.assertEqual(wiring, ((("producer", "out", "consumer", "in"),),))

    def test_pareto_frontier_matches_direct_oracle(self):
        values = (assembly("a", 1, 1), assembly("b", 1, 2), assembly("c", 2, 0), assembly("d", 2, 2))
        got = {a.stable_id for a in pareto_frontier(values)}
        expected = {a.stable_id for a in values if not any(b is not a and b.cost.dominates(a.cost) for b in values)}
        self.assertEqual(got, expected)
        self.assertEqual(got, {"a", "c"})


if __name__ == "__main__":
    unittest.main()
