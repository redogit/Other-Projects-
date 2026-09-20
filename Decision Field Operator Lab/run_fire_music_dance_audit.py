#!/usr/bin/env python3
"""Deterministic bounded audit for FIRE + Music + Dance dynamic field."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import unittest

from fire_music_dance import (
    CheckResult,
    DanceStep,
    DynamicFireField,
    Mutation,
    Triad,
    opposites_bounds_transitions,
)


def run_demo() -> dict:
    field = DynamicFireField.create(
        object_id="Object:demo-fire-field",
        surface={
            "system": {"depth": 2, "temperature": 0, "carrier": "seed"},
            "observer": {"mode": "visible"},
        },
        invariants={
            "system.carrier": "seed",
            "observer.mode": "visible",
        },
        provenance=[
            "user:FIRE+Music+Dance",
            "repo:Other-Projects-",
        ],
        triad=Triad.MIDDLE,
    )

    music = field.music(
        bpm=108,
        bars=2,
        beats_per_bar=4,
    )
    dance = field.dance(
        [
            DanceStep(
                0,
                "INWARD",
                Mutation(
                    "system.depth",
                    2,
                    3,
                    operator="DESCEND",
                    direction="INWARD",
                ),
            ),
            DanceStep(
                1,
                "SIDEWAYS",
                Mutation(
                    "system.temperature",
                    0,
                    1,
                    operator="IGNITE",
                    direction="SIDEWAYS",
                ),
            ),
            DanceStep(2, "HOMEWARD", None, "return after observation"),
        ]
    )

    burned = field.generate(
        field.root.candidate_id,
        Mutation(
            "system.depth",
            2,
            3,
            operator="DESCEND",
            direction="INWARD",
        ),
        provenance=["demo:one-degree"],
    )
    field.burn(
        burned.candidate_id,
        [
            CheckResult(
                "depth-control",
                "FAIL",
                "synthetic control rejects depth=3",
                ("evidence:synthetic",),
            )
        ],
    )

    ember = field.generate(
        field.root.candidate_id,
        Mutation(
            "system.depth",
            2,
            1,
            operator="SIMPLIFY",
            direction="OUTWARD",
        ),
        provenance=["demo:one-degree"],
    )
    ember = field.burn(
        ember.candidate_id,
        [
            CheckResult(
                "depth-control",
                "PASS",
                "synthetic control accepts depth=1",
                ("evidence:synthetic",),
            )
        ],
    )
    survivor = field.mark_survivor(ember.candidate_id)
    rebuilt = field.reconstitute(
        survivor.candidate_id,
        knowledge_patch={
            "lesson": "depth=1 survived this bounded synthetic control"
        },
    )
    home = field.homeward(rebuilt.candidate_id)
    delta = field.compare(
        field.root.candidate_id,
        home.candidate_id,
        consequential_paths=[
            "system.depth",
            "system.carrier",
            "observer.mode",
        ],
    )
    field.close_if_delta_zero(home.candidate_id, delta)

    recommendation = field.recommend_route(
        [
            ("DESCEND", "INWARD"),
            ("SIMPLIFY", "OUTWARD"),
        ]
    )

    return {
        "schema": "fire-music-dance-audit/v1",
        "status": "PASS",
        "synthetic_only": True,
        "music_pulses": [pulse.__dict__ for pulse in music],
        "dance": [
            {
                "index": step.index,
                "direction": step.direction,
                "mutation": None
                if step.mutation is None
                else step.mutation.__dict__,
                "note": step.note,
            }
            for step in dance
        ],
        "ash_count": len(field.ash),
        "ember_count": len(field.embers),
        "survivor_count": len(field.survivors),
        "recommendation_after_learning": recommendation,
        "delta": {
            "status": delta.status.value,
            "changed_paths": list(delta.changed_paths),
            "protected_violations": list(delta.protected_violations),
            "unresolved": list(delta.unresolved),
            "note": delta.note,
        },
        "opposites_bounds_transitions": opposites_bounds_transitions(
            0.25,
            lower=-1.0,
            upper=1.0,
        ),
        "field": field.export(),
        "boundaries": [
            "SYNTHETIC_AUDIT != DOMAIN_VALIDATION",
            "MUSIC != TRUTH",
            "DANCE != TRUTH",
            "GENERATE != VERIFY != ADMIT",
            "DELTA_ZERO_IS_LOCAL_NOT_GLOBAL",
        ],
    }


def run_tests() -> unittest.result.TestResult:
    suite = unittest.defaultTestLoader.discover(
        Path(__file__).parent,
        pattern="test_fire_music_dance.py",
    )
    return unittest.TextTestRunner(verbosity=1).run(suite)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default="evidence/FIRE_MUSIC_DANCE_RESULTS.json",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    result = run_demo()
    tests = run_tests()
    result["tests"] = {
        "run": tests.testsRun,
        "failures": len(tests.failures),
        "errors": len(tests.errors),
        "pass": tests.wasSuccessful(),
    }
    if not tests.wasSuccessful():
        result["status"] = "FAILED"

    path = Path(args.out)
    if not path.is_absolute():
        path = Path(__file__).parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"

    if args.check and path.exists():
        if path.read_text(encoding="utf-8") != encoded:
            print("FIRE_MUSIC_DANCE_RESULTS_MISMATCH")
            return 2
        print("FIRE_MUSIC_DANCE_RESULTS_MATCH")
        return 0

    path.write_text(encoded, encoding="utf-8")
    print(path)
    return 0 if tests.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
