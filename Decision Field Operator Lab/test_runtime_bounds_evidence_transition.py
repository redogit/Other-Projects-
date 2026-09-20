"""Explain, rather than conceal, the resource-bound replay successor."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from omega import canonical_json
from run_rmapl_omega_stress import _run_runtime_family

HERE = Path(__file__).resolve().parent


class RuntimeBoundEvidenceTransitionTests(unittest.TestCase):
    def test_only_effective_candidate_cap_changes_in_frozen_runtime_observations(self):
        previous = json.loads((HERE / "evidence/history/RMAPL_OMEGA_STRESS_PRE_RUNTIME_BOUNDS_20260920.json").read_text(encoding="utf-8"))
        current = json.loads((HERE / "evidence/RMAPL_OMEGA_STRESS_RESULTS.json").read_text(encoding="utf-8"))
        observations = []
        failures = []

        class Recorder:
            def observe(self, family, case_index, payload):
                observations.append({"family": family, "case": case_index, "payload": deepcopy(payload)})

            def fail(self, family, case_index, check, detail):
                failures.append((family, case_index, check, detail))

        checks = dict(current["checks"])
        _run_runtime_family(current["families"]["runtimeMatrix"], current["seed"], Recorder(), checks)
        self.assertEqual(failures, [])
        self.assertEqual(checks, current["checks"])
        self.assertEqual(len(observations), 1024)
        old_hash, new_hash = hashlib.sha256(), hashlib.sha256()
        for index, observation in enumerate(observations):
            self.assertEqual(observation["family"], "runtimeMatrix")
            self.assertEqual(observation["case"], index)
            self.assertEqual(observation["payload"]["generation"]["maxCandidates"], 4)
            self.assertEqual(observation["payload"]["generation"]["maxSteps"], 1)
            new_hash.update(canonical_json(observation).encode("utf-8"))
            restored = deepcopy(observation)
            restored["payload"]["generation"]["maxCandidates"] = 8
            old_hash.update(canonical_json(restored).encode("utf-8"))

        self.assertEqual(old_hash.hexdigest(), previous["familyDigests"]["runtimeMatrix"])
        self.assertEqual(new_hash.hexdigest(), current["familyDigests"]["runtimeMatrix"])
        restored_report = deepcopy(current)
        restored_report["familyDigests"]["runtimeMatrix"] = previous["familyDigests"]["runtimeMatrix"]
        restored_report["digestSha256"] = previous["digestSha256"]
        self.assertEqual(restored_report, previous)
        for report in (previous, current):
            payload = {key: report[key] for key in (
                "seed", "scale", "families", "checks", "familyDigests", "failures", "rmalResponseBoundary"
            )}
            self.assertEqual(hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest(), report["digestSha256"])


if __name__ == "__main__":
    unittest.main()
