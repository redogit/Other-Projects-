import json
from pathlib import Path
import unittest

from decision_field import DecisionField, Evidence
from omega_adapters import (
    adapter_round_trip,
    project_decision_field,
    project_s1_experience,
    reconstruct_decision_field,
    reconstruct_s1_experience,
)

HERE = Path(__file__).parent


def load_fixture(name):
    return json.loads((HERE / "fixtures" / name).read_text(encoding="utf-8"))


def s1_fixture(actions):
    fixture = load_fixture("omega_s1_native.json")
    fixture["id"] = "fixture-" + "-".join(f"{a['plane']}{a['degrees']}" for a in actions)
    fixture["actions"] = actions
    return fixture


class OmegaAdapterTests(unittest.TestCase):
    def test_decision_field_round_trip_preserves_native_semantics_and_remainder(self):
        field = DecisionField(
            possibilities=frozenset({0, 1, 2}),
            relations=({"kind": "excludes", "left": 0, "right": 2},),
            evidence=(Evidence("software-verification", "fixture"),),
            goal=1,
            unresolved=frozenset({0, 2}),
            observer={"obligation": "select-1"},
            history=("seed",),
        )
        omega = project_decision_field(field, "fixture:df:1", "fixture:df:1")
        rebuilt = reconstruct_decision_field(omega)
        self.assertEqual(rebuilt, field)
        self.assertEqual(omega["domainRemainder"]["nativeClass"], "DecisionField")
        self.assertEqual(omega["state"]["possibilities"], [0, 1, 2])
        self.assertEqual(omega["decisionField"]["goal"], 1)

    def test_decision_field_round_trip_report_is_exact(self):
        field = DecisionField(
            possibilities=(0, 1, 2),
            relations=(),
            evidence=(),
            goal=1,
            unresolved=(0, 2),
            observer="select-1",
            history=("seed",),
        )
        report = adapter_round_trip(
            field,
            lambda value: project_decision_field(value, "fixture:df:2", "fixture:df:2"),
            reconstruct_decision_field,
        )
        self.assertEqual(report["reconstruction"]["changed"], [])
        self.assertEqual(report["reconstruction"]["lost"], [])
        self.assertEqual(report["reconstruction"]["introduced"], [])

    def test_s1_round_trip_keeps_ordered_actions_and_native_only_fields(self):
        native = load_fixture("omega_s1_native.json")
        omega = project_s1_experience(native)
        rebuilt = reconstruct_s1_experience(omega)
        self.assertEqual(rebuilt, native)
        self.assertEqual(omega["path"], [{"degrees": 1, "plane": "xw"}])
        self.assertIn("nativeRemainder", omega["domainRemainder"])
        self.assertNotIn("observerField", omega)

    def test_s1_equal_compressed_counts_do_not_equal_history(self):
        a = s1_fixture([
            {"plane": "xw", "degrees": 1},
            {"plane": "yw", "degrees": 1},
        ])
        b = s1_fixture([
            {"plane": "yw", "degrees": 1},
            {"plane": "xw", "degrees": 1},
        ])
        omega_a = project_s1_experience(a)
        omega_b = project_s1_experience(b)
        self.assertNotEqual(omega_a["path"], omega_b["path"])
        self.assertNotEqual(omega_a["id"], omega_b["id"])

    def test_s1_adapter_rejects_wrong_schema_or_operator_version(self):
        native = load_fixture("omega_s1_native.json")
        with self.assertRaisesRegex(ValueError, "s1-experience/v0"):
            project_s1_experience({**native, "schema": "other"})
        with self.assertRaisesRegex(ValueError, "S'1-Ops v0"):
            project_s1_experience({**native, "operatorVersion": "future"})

    def test_native_only_data_stays_in_domain_remainder(self):
        native = load_fixture("omega_s1_native.json")
        omega = project_s1_experience(native)
        self.assertEqual(
            omega["domainRemainder"]["nativeRemainder"],
            native["nativeRemainder"],
        )
        self.assertNotIn("comparisons", omega)
        self.assertNotIn("observerField", omega)


if __name__ == "__main__":
    unittest.main()
