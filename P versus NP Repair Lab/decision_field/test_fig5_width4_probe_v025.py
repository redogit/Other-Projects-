from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import unittest

import fig5_width4_family_v025 as family
import fig5_width4_probe_v025 as probe


class Width4UniverseTests(unittest.TestCase):
    def test_canonical_clause_rejects_non_width4_inputs(self) -> None:
        for clause in ((1, 2, 3), (1, 2, 3, 4, 5), (1, -1, 2, 3), (0, 2, 3, 4)):
            with self.subTest(clause=clause), self.assertRaises(ValueError):
                family.canonical_clause(clause)

    def test_universe_is_exact_non_tautological_width4_space(self) -> None:
        for n in family.ALLOWED_N:
            with self.subTest(n=n):
                universe = family.clause_universe(n)
                self.assertEqual(len(universe), 16 * math.comb(n, 4))
                self.assertEqual(len(universe), len(set(universe)))
                for clause in universe:
                    self.assertEqual(len(clause), 4)
                    self.assertEqual(len({abs(literal) for literal in clause}), 4)
                    self.assertFalse(any(-literal in clause for literal in clause))

    def test_density4_formula_uses_exactly_4n_clauses_and_all_variables(self) -> None:
        for n in family.ALLOWED_N:
            with self.subTest(n=n):
                formula, trace = family.generate_formula("TEST-WIDTH4-STRUCTURAL", n)
                self.assertEqual(len(formula), 4 * n)
                self.assertEqual(trace.width, 4)
                self.assertEqual(trace.target_clause_count, 4 * n)
                self.assertEqual(
                    {abs(literal) for clause in formula for literal in clause},
                    set(range(1, n + 1)),
                )

    def test_width4_identity_and_priority_namespace_are_honest(self) -> None:
        contract = family.describe_contract()
        self.assertEqual(contract["family_version"], "FIG5-clause-priority-4cnf-density4/v0.25")
        self.assertEqual(contract["width"], 4)
        self.assertEqual(contract["priority_method"], "SHA256(length-prefixed namespace, block seed, canonical clause bytes)")
        self.assertIn("4CNF", contract["priority_namespace"])
        self.assertNotIn("3cnf", contract["family_version"].lower())

    def test_same_width4_clause_priority_is_invariant_across_n(self) -> None:
        clause = family.canonical_clause((1, -2, 3, -4))
        expected = family.clause_priority("TEST-WIDTH4-PRIORITY", clause)
        for n in family.ALLOWED_N:
            with self.subTest(n=n):
                self.assertTrue({abs(x) for x in clause} <= set(range(1, n + 1)))
                self.assertEqual(family.clause_priority("TEST-WIDTH4-PRIORITY", clause), expected)

    def test_block_generation_hashes_maximum_universe_once(self) -> None:
        seed = "TEST-WIDTH4-EFFICIENT-BLOCK"
        batch, efficiency = family.generate_block(seed, family.ALLOWED_N)
        expected_digests = {
            8: "0280f6a1517f4a3355b91d7cefa4274a321a1e30833cac57c80a07d6c60c27b7",
            9: "3ed727ac76ca326f52c7b32aebb41137e3fd9a12b61e2359551dcdc5bf0c5fbd",
            10: "77ff39d3142caba3b68cee544f9ea09b07a6361572656717a35ed2790601beea",
            11: "ff5188eb5b40858b66542aed82d9969d178edb56e005af31e23254077b4d9444",
            12: "4fa4abcf0737cabd495152cc9b98c085a0155562ff1f5ba681c027c812570a31",
            13: "b7efd2a8884b11da237167463a86da095e04320e2e748d100c11866759eff1f5",
        }

        self.assertEqual(efficiency["priority_evaluations"], 16 * math.comb(max(family.ALLOWED_N), 4))
        self.assertEqual(efficiency["sort_count"], 1)
        for n in family.ALLOWED_N:
            scalar_formula, scalar_trace = family.generate_formula(seed, n)
            batch_formula, batch_trace = batch[n]
            self.assertEqual(batch_formula, scalar_formula)
            self.assertEqual(batch_trace, scalar_trace)
            self.assertEqual(batch_trace.formula_digest, expected_digests[n])


class StageFirewallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.test_seed = probe.derive_seed(
            namespace=probe.TEST_SEED_NAMESPACE,
            preregistration_commit="0" * 40,
            block_id=0,
        )
        cls.manifest = probe.materialize_rows(
            seeds=[{"block_id": 0, "seed": cls.test_seed}],
            n_levels=(8,),
            provenance={"test_only": True},
        )

    def test_materialize_does_not_execute_generate_verify_or_admit(self) -> None:
        self.assertEqual(self.manifest["stage"], "MATERIALIZE")
        self.assertEqual(self.manifest["schema"], "fig5-v025-width4-test-manifest/v1")
        self.assertTrue(self.manifest["experiment_id"].startswith("TEST-ONLY/"))
        self.assertFalse(self.manifest["generate_run"])
        self.assertFalse(self.manifest["verify_run"])
        self.assertFalse(self.manifest["admit_run"])
        self.assertNotIn("active", self.manifest["rows"][0])

    def test_generate_receipt_contains_no_verifier_or_admission_result(self) -> None:
        generated = probe.run_generate(self.manifest, active_cap=160)
        self.assertEqual(generated["stage"], "GENERATE")
        self.assertFalse(generated["verify_run"])
        self.assertFalse(generated["admit_run"])
        self.assertIn("active", generated["rows"][0])
        self.assertNotIn("truth", generated["rows"][0])
        self.assertNotIn("admitted", generated["rows"][0])

    def test_verify_and_admit_remain_separate(self) -> None:
        generated = probe.run_generate(self.manifest, active_cap=160)
        verified = probe.run_verify(self.manifest, generated, validation_n=frozenset({8}))
        self.assertEqual(verified["stage"], "VERIFY")
        self.assertFalse(verified["admit_run"])
        self.assertIn("truth", verified["rows"][0])
        self.assertNotIn("admitted", verified["rows"][0])

        admitted = probe.run_admit(self.manifest, generated, verified)
        self.assertEqual(admitted["stage"], "ADMIT")
        self.assertFalse(admitted["analysis_run"])
        self.assertIn("admitted", admitted["rows"][0])
        self.assertNotIn("prediction_errors", admitted["rows"][0])

    def test_analysis_records_inconclusive_when_calibration_is_unavailable(self) -> None:
        generated = probe.run_generate(self.manifest, active_cap=0)
        verified = probe.run_verify(self.manifest, generated, validation_n=frozenset())
        admitted = probe.run_admit(self.manifest, generated, verified)

        analysis = probe.run_analyze(self.manifest, generated, verified, admitted)

        self.assertEqual(analysis["status"], "WIDTH4_DENSITY4_INCONCLUSIVE_ADMISSION")
        self.assertFalse(analysis["success"])
        self.assertEqual(analysis["calibration"]["admitted_calibration_rows"], 0)

    def test_parallel_generate_and_verify_are_byte_identical_to_serial(self) -> None:
        seeds = [
            {
                "block_id": block_id,
                "seed": probe.derive_seed(
                    namespace=probe.TEST_SEED_NAMESPACE,
                    preregistration_commit="1" * 40,
                    block_id=block_id,
                ),
            }
            for block_id in range(2)
        ]
        manifest = probe.materialize_rows(seeds, (8,), {"test_only": True})

        serial_generate = probe.run_generate(manifest, workers=1)
        parallel_generate = probe.run_generate(manifest, workers=2)
        self.assertEqual(serial_generate, parallel_generate)

        serial_verify = probe.run_verify(manifest, serial_generate, validation_n=frozenset({8}), workers=1)
        parallel_verify = probe.run_verify(manifest, parallel_generate, validation_n=frozenset({8}), workers=2)
        self.assertEqual(serial_verify, parallel_verify)


class OfficialConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parent
        cls.manifest = json.loads((root / "FIG5_V025_WIDTH4_MANIFEST.json").read_text())
        cls.generated = json.loads((root / "FIG5_V025_WIDTH4_GENERATE.json").read_text())
        cls.verified = json.loads((root / "FIG5_V025_WIDTH4_VERIFY.json").read_text())

    def test_official_generate_rejects_nonfrozen_cap(self) -> None:
        with self.assertRaisesRegex(ValueError, "official active cap must remain 160"):
            probe.run_generate(self.manifest, active_cap=0, workers=1)

    def test_official_generate_rejects_partial_panel(self) -> None:
        partial = copy.deepcopy(self.manifest)
        partial["rows"] = partial["rows"][:-1]
        with self.assertRaisesRegex(ValueError, "official manifest row identities"):
            probe.run_generate(partial, workers=1)

    def test_official_manifest_rejects_a_different_preregistration_commit(self) -> None:
        with self.assertRaisesRegex(ValueError, "frozen preregistration commit"):
            probe.official_manifest("0" * 40)

    def test_official_verify_rejects_a_different_carrier_scope(self) -> None:
        with self.assertRaisesRegex(ValueError, "official carrier scope"):
            probe.run_verify(
                self.manifest,
                self.generated,
                validation_n=frozenset({11}),
                workers=1,
            )

    def test_official_manifest_rejects_formula_tampering(self) -> None:
        tampered = copy.deepcopy(self.manifest)
        tampered["rows"][0]["formula"][0][0] *= -1
        with self.assertRaisesRegex(ValueError, "official MATERIALIZE receipt hash"):
            probe.run_generate(tampered, workers=1)

    def test_official_verify_rejects_generate_receipt_tampering(self) -> None:
        tampered = copy.deepcopy(self.generated)
        tampered["rows"][0]["active"]["generated_resolvents"] += 1
        with self.assertRaisesRegex(ValueError, "official GENERATE receipt hash"):
            probe.run_verify(self.manifest, tampered, workers=1)

    def test_official_admit_rejects_verify_receipt_tampering(self) -> None:
        tampered = copy.deepcopy(self.verified)
        tampered["rows"][0]["truth"]["assignments_tested"] += 1
        with self.assertRaisesRegex(ValueError, "official VERIFY receipt hash"):
            probe.run_admit(self.manifest, self.generated, tampered)


if __name__ == "__main__":
    unittest.main()
