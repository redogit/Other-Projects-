import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import CostVector, PartSpec
from catalog import PartCatalog
from adapters import (
    BitsetInferenceAdapter,
    ObservationAdapter,
    T4TransitionAdapter,
    reference_catalog,
    source_hashes,
)


def make_part(stable_id, version, provides):
    return PartSpec(
        stable_id=stable_id, version=version, provides=provides, requires=(),
        input_ports=(("in", "WorldState"),), output_ports=(("out", "WorldState"),),
        state_carried=(), assumptions=(), bounds=(), side_effects=(), external_dependencies=(),
        cost=CostVector.from_mapping({"component_count": 1}), evidence_refs=(), known_failures=(),
        replaceability_boundary="test obligation",
    )


class ToySystem:
    def successors(self, belief, action):
        return (belief ^ (1 << action),)


class CatalogAdapterTests(unittest.TestCase):
    def test_catalog_is_append_only_and_ordered(self):
        catalog = PartCatalog()
        p2 = make_part("z", 1, ("transition",))
        p1 = make_part("a", 1, ("observe",))
        catalog.register(p2, lambda: object())
        catalog.register(p1, lambda: object())
        self.assertEqual([p.stable_id for p in catalog.ordered_specs()], ["a", "z"])
        with self.assertRaises(ValueError):
            catalog.register(p1, lambda: object())

    def test_reference_catalog_contains_versioned_reference_parts(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture_tree(pathlib.Path(td))
            catalog = reference_catalog(root)
            ids = {(p.stable_id, p.version) for p in catalog.ordered_specs()}
            self.assertEqual(ids, {
                ("pass06.t4_transition", 1),
                ("pass07.moore_scheduler", 1),
                ("pass08.observation_partition", 1),
                ("pass08.bitset_belief", 1),
                ("pass08.reach_monitor", 1),
                ("pass08.observation_controller", 1),
            })

    def test_adapters_load_transition_and_preserve_reference_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture_tree(pathlib.Path(td))
            before = source_hashes(root)
            adapter = T4TransitionAdapter(0x12, root)
            self.assertEqual(adapter.next_state(2, 1), (0x12 + 2 + 1) % 4)
            self.assertEqual(source_hashes(root), before)

    def test_observation_and_bitset_inference_are_thin_wrappers(self):
        obs = ObservationAdapter((0, 0, 1, 1))
        self.assertEqual(obs.observe(2), 1)
        belief = BitsetInferenceAdapter().successors(ToySystem(), 0b0011, 1)
        self.assertEqual(belief, (0b0001,))

    @staticmethod
    def _fixture_tree(root):
        (root / "partial-observation").mkdir(parents=True)
        (root / "schedule").mkdir(parents=True)
        (root / "field.py").write_text(
            "def get_next(rank, context, state):\n    return (rank + context + state) % 4\n",
            encoding="utf-8",
        )
        (root / "partial-observation" / "partial.py").write_text(
            "class ObservationController:\n    pass\n",
            encoding="utf-8",
        )
        (root / "schedule" / "schedule.py").write_text(
            "class MooreScheduler:\n    pass\n",
            encoding="utf-8",
        )
        return root


if __name__ == "__main__":
    unittest.main()
