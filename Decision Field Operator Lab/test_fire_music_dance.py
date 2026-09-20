import json
import unittest

from fire_music_dance import (
    ALL_WAYS,
    BOUNDARIES,
    CheckResult,
    DanceStep,
    DeltaStatus,
    DynamicFireField,
    FireStage,
    Mutation,
    Triad,
    Verification,
    mutation_signature,
    opposites_bounds_transitions,
)


class FireMusicDanceTests(unittest.TestCase):
    def make_field(self):
        return DynamicFireField.create(
            object_id="Object:demo",
            surface={
                "model": {"depth": 2, "carrier": "tree", "gain": 0},
                "observer": {"mode": "visible"},
            },
            invariants={
                "model.carrier": "tree",
                "observer.mode": "visible",
            },
            provenance=["user:concept", "source:test"],
        )

    def test_triad_is_explicit_and_not_binary(self):
        self.assertEqual({x.value for x in Triad}, {"DARK", "MIDDLE", "LIGHT"})
        self.assertEqual(self.make_field().root.triad, Triad.MIDDLE)

    def test_all_ways_contains_homeward_and_directional_set(self):
        for name in [
            "FORWARD", "BACKWARD", "SIDEWAYS", "INWARD",
            "OUTWARD", "REVERSE", "BRANCH", "HOMEWARD",
        ]:
            self.assertIn(name, ALL_WAYS)
        self.assertEqual(len(ALL_WAYS), len(set(ALL_WAYS)))

    def test_one_degree_default_and_explicit_widening(self):
        field = self.make_field()
        root = field.root
        m1 = Mutation(
            "model.depth", 2, 3,
            operator="DEEPEN", direction="INWARD",
        )
        child = field.generate(root.candidate_id, m1)
        self.assertEqual(child.surface["model"]["depth"], 3)
        with self.assertRaisesRegex(ValueError, "one-degree"):
            field.generate(
                root.candidate_id,
                [
                    m1,
                    Mutation(
                        "model.gain", 0, 1,
                        operator="AMPLIFY", direction="UP",
                    ),
                ],
            )
        wide = field.generate(
            root.candidate_id,
            [
                m1,
                Mutation(
                    "model.gain", 0, 1,
                    operator="AMPLIFY", direction="UP",
                ),
            ],
            allow_wide=True,
        )
        self.assertEqual(wide.surface["model"]["gain"], 1)

    def test_burn_preserves_ash_smoke_and_ember_separately(self):
        field = self.make_field()
        root = field.root

        fail = field.generate(
            root.candidate_id,
            Mutation("model.depth", 2, 3, direction="INWARD"),
        )
        fail = field.burn(
            fail.candidate_id,
            [CheckResult(
                "gate", "FAIL", "depth broke the test", ("ev:1",)
            )],
        )
        self.assertEqual(fail.stage, FireStage.ASH)
        self.assertEqual(fail.verification, Verification.REFUTED_LOCAL)
        self.assertIn(fail.candidate_id, field.ash)

        smoke = field.generate(
            root.candidate_id,
            Mutation("model.gain", 0, 1, direction="UP"),
        )
        smoke = field.burn(
            smoke.candidate_id,
            [CheckResult("gate", "UNRESOLVED", "measurement absent")],
        )
        self.assertEqual(smoke.stage, FireStage.SMOKE)
        self.assertNotIn(smoke.candidate_id, field.ash)
        self.assertNotIn(smoke.candidate_id, field.embers)

        ember = field.generate(
            root.candidate_id,
            Mutation("model.depth", 2, 1, direction="OUTWARD"),
        )
        ember = field.burn(
            ember.candidate_id,
            [CheckResult(
                "gate", "PASS", "bounded check passed", ("ev:2",)
            )],
        )
        self.assertEqual(ember.stage, FireStage.EMBER)
        self.assertEqual(ember.verification, Verification.VERIFIED_LOCAL)
        self.assertIn(ember.candidate_id, field.embers)

    def test_generate_verify_admit_are_separate(self):
        field = self.make_field()
        child = field.generate(
            field.root.candidate_id,
            Mutation("model.depth", 2, 1, direction="OUTWARD"),
        )
        self.assertFalse(child.admitted)
        ember = field.burn(
            child.candidate_id,
            [CheckResult("gate", "PASS", "pass", ("ev:pass",))],
        )
        survivor = field.mark_survivor(ember.candidate_id)
        self.assertFalse(survivor.admitted)
        admitted = field.admit(
            survivor.candidate_id,
            authority="user-explicit",
            evidence_refs=["ev:independent"],
        )
        self.assertTrue(admitted.admitted)
        self.assertEqual(admitted.verification, Verification.ADMITTED)
        self.assertIn("GENERATE != VERIFY != ADMIT", BOUNDARIES)

    def test_music_is_cadence_not_truth(self):
        field = self.make_field()
        pulses = field.music(
            bpm=120,
            bars=2,
            beats_per_bar=4,
            motif=("OBSERVE", "BURN", "REOBSERVE", "REST"),
        )
        self.assertEqual(len(pulses), 8)
        self.assertEqual(
            [p.operator for p in pulses[:4]],
            ["OBSERVE", "BURN", "REOBSERVE", "REST"],
        )
        self.assertEqual(pulses[4].bar, 2)
        self.assertIn("MUSIC != TRUTH", BOUNDARIES)

    def test_dance_is_ordered_all_way_trajectory(self):
        field = self.make_field()
        steps = field.dance(
            [
                DanceStep(
                    0, "INWARD",
                    Mutation("model.depth", 2, 3, direction="INWARD"),
                    "descend",
                ),
                DanceStep(
                    1, "SIDEWAYS",
                    Mutation("model.gain", 0, 1, direction="SIDEWAYS"),
                    "compare",
                ),
                DanceStep(2, "HOMEWARD", None, "return"),
            ]
        )
        self.assertEqual(
            [s.direction for s in steps],
            ["INWARD", "SIDEWAYS", "HOMEWARD"],
        )
        self.assertIn("DANCE != TRUTH", BOUNDARIES)

    def test_homeward_restores_surface_but_carries_knowledge_and_evidence(self):
        field = self.make_field()
        child = field.generate(
            field.root.candidate_id,
            Mutation("model.depth", 2, 1, direction="OUTWARD"),
        )
        ember = field.burn(
            child.candidate_id,
            [CheckResult("gate", "PASS", "pass", ("ev:survived",))],
        )
        survivor = field.mark_survivor(ember.candidate_id)
        rebuilt = field.reconstitute(
            survivor.candidate_id,
            knowledge_patch={"learned": "depth one survived"},
        )
        home = field.homeward(rebuilt.candidate_id)
        self.assertEqual(home.surface, field.root.surface)
        self.assertEqual(home.object_id, field.root.object_id)
        self.assertEqual(home.knowledge["learned"], "depth one survived")
        self.assertIn("ev:survived", home.evidence_refs)

    def test_sleep_blocks_mutation_until_wake(self):
        field = self.make_field()
        sleeping = field.sleep(field.root.candidate_id)
        with self.assertRaisesRegex(RuntimeError, "wake"):
            field.generate(
                sleeping.candidate_id,
                Mutation("model.depth", 2, 3, direction="INWARD"),
            )
        awake = field.wake(
            sleeping.candidate_id,
            trigger="new observation",
        )
        self.assertFalse(awake.resting)
        child = field.generate(
            awake.candidate_id,
            Mutation("model.depth", 2, 3, direction="INWARD"),
        )
        self.assertEqual(child.surface["model"]["depth"], 3)

    def test_delta_zero_closes_only_local_scope_and_unknown_is_not_zero(self):
        field = self.make_field()
        home = field.homeward(field.root.candidate_id)
        zero = field.compare(
            field.root.candidate_id,
            home.candidate_id,
            consequential_paths=["model.depth", "model.carrier"],
        )
        self.assertEqual(zero.status, DeltaStatus.DELTA_ZERO)
        closed = field.close_if_delta_zero(home.candidate_id, zero)
        self.assertEqual(closed.stage, FireStage.CLOSED)
        self.assertTrue(closed.resting)

        field2 = self.make_field()
        same = field2.homeward(field2.root.candidate_id)
        unknown = field2.compare(
            field2.root.candidate_id,
            same.candidate_id,
            consequential_paths=["model.depth"],
            unresolved=["sensor missing"],
        )
        self.assertEqual(unknown.status, DeltaStatus.UNKNOWN)
        with self.assertRaisesRegex(ValueError, "DELTA_ZERO"):
            field2.close_if_delta_zero(same.candidate_id, unknown)

    def test_learning_and_habituation_change_future_route_ordering(self):
        field = self.make_field()
        root = field.root

        bad = Mutation(
            "model.depth", 2, 3,
            operator="DEEPEN", direction="INWARD",
        )
        c1 = field.generate(root.candidate_id, bad)
        field.burn(c1.candidate_id, [CheckResult("x", "FAIL", "bad")])

        good = Mutation(
            "model.depth", 2, 1,
            operator="SIMPLIFY", direction="OUTWARD",
        )
        c2 = field.generate(root.candidate_id, good)
        field.burn(c2.candidate_id, [CheckResult("x", "PASS", "good")])

        self.assertEqual(
            field.recommend_route([
                ("DEEPEN", "INWARD"),
                ("SIMPLIFY", "OUTWARD"),
            ]),
            ("SIMPLIFY", "OUTWARD"),
        )
        sig = mutation_signature(good)
        self.assertEqual(field.memory.signature_counts[sig], 1)
        self.assertEqual(field.memory.novelty(sig), 0.5)

    def test_opposites_bounds_transitions_preserves_middle(self):
        row = opposites_bounds_transitions(5, lower=0, upper=10)
        self.assertEqual(row["midpoint"], 5.0)
        self.assertEqual(row["opposite"], 5.0)
        self.assertEqual(row["regime"], "BETWEEN")
        self.assertEqual(
            opposites_bounds_transitions(-1, lower=0, upper=10)["regime"],
            "BELOW",
        )

    def test_export_is_json_serializable_and_method_only(self):
        exported = self.make_field().export()
        blob = json.dumps(exported, sort_keys=True)
        self.assertIn("fire-music-dance-dynamic-field/v1", blob)
        self.assertEqual(exported["authority"], "method-only")
        self.assertEqual(exported["root"]["object_id"], "Object:demo")


if __name__ == "__main__":
    unittest.main()
