"""Regressions for the PR #82 metadata-to-stress dependency boundary.

The workflow reader intentionally supports this repository's quoted, positive,
block-list path filters only. It is not a general YAML or GitHub Actions parser.
"""
from __future__ import annotations

import ast
import fnmatch
import json
from pathlib import Path, PurePosixPath
import unittest

from run_rmapl_omega_stress import _rmal_boundary_snapshot

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def _root_relative_path(node: ast.AST) -> PurePosixPath:
    if isinstance(node, ast.Name) and node.id == "ROOT":
        return PurePosixPath()
    if (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Div)
        and isinstance(node.right, ast.Constant)
        and isinstance(node.right.value, str)
    ):
        return _root_relative_path(node.left) / node.right.value
    raise AssertionError("Review new stress file dependency expression explicitly")


def _positive_path_filters(text: str, event: str) -> tuple[str, ...]:
    lines = text.splitlines()
    start = lines.index(f"  {event}:") + 1
    body = []
    for line in lines[start:]:
        if line.strip() and len(line) - len(line.lstrip()) <= 2:
            break
        body.append(line)
    index = body.index("    paths:") + 1
    patterns = []
    for line in body[index:]:
        if not line.strip():
            continue
        if not line.startswith("      - "):
            break
        value = ast.literal_eval(line[len("      - "):].strip())
        if not isinstance(value, str) or not value or value.startswith("!"):
            raise AssertionError("Review non-positive workflow path filter explicitly")
        patterns.append(value)
    if not patterns:
        raise AssertionError(f"No positive path filters found for {event}")
    return tuple(patterns)


class StressCurrentnessDependenciesTests(unittest.TestCase):
    def test_frozen_boundary_matches_live_metadata(self):
        frozen = json.loads(
            (HERE / "evidence" / "RMAPL_OMEGA_STRESS_RESULTS.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            frozen["rmalResponseBoundary"],
            _rmal_boundary_snapshot(),
            "Frozen stress metadata drifted; replay and preserve the predecessor before refresh",
        )

    def test_workflow_watches_direct_stress_json_inputs_on_push_and_pr(self):
        source = ast.parse((HERE / "run_rmapl_omega_stress.py").read_text(encoding="utf-8"))
        dependencies = {
            str(_root_relative_path(node.args[0]))
            for node in ast.walk(source)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_load_json"
        }
        self.assertTrue(dependencies, "Stress JSON dependency discovery unexpectedly empty")
        workflow = (ROOT / ".github" / "workflows" / "operator-field-check.yml").read_text(
            encoding="utf-8"
        )
        for event in ("push", "pull_request"):
            patterns = _positive_path_filters(workflow, event)
            for dependency in sorted(dependencies):
                with self.subTest(event=event, dependency=dependency):
                    self.assertTrue(
                        any(fnmatch.fnmatchcase(dependency, pattern) for pattern in patterns),
                        f"{event}.paths does not watch direct stress input {dependency}",
                    )


if __name__ == "__main__":
    unittest.main()
