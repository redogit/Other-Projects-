"""Regressions for PR #82 metadata and pinned-artifact stress dependencies.

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
HODGE_CONTROL_INPUTS = (
    "dependencies/hodge.lock.json",
    "tools/hodge_dependency.py",
    "tools/tests/test_hodge_dependency.py",
)


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


def _dependency_inputs(node: ast.AST) -> tuple[str, ...]:
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "resolve_artifact"
    ):
        expected = ast.parse("resolve_artifact('issue43_bridge_calibration')", mode="eval").body
        if ast.dump(node) != ast.dump(expected):
            raise AssertionError("Review new pinned Hodge artifact dependency explicitly")
        return HODGE_CONTROL_INPUTS
    return (str(_root_relative_path(node)),)


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
    def test_dependency_discovery_rejects_unreviewed_artifact_expressions(self):
        for expression in (
            "resolve_artifact('new_artifact')",
            "resolve_artifact('issue43_bridge_calibration', root=ROOT)",
            "unverified_artifact('issue43_bridge_calibration')",
        ):
            with self.subTest(expression=expression), self.assertRaisesRegex(AssertionError, "Review new"):
                _dependency_inputs(ast.parse(expression, mode="eval").body)

    def test_stress_hodge_dependency_uses_the_verified_external_artifact(self):
        source = ast.parse((HERE / "run_rmapl_omega_stress.py").read_text(encoding="utf-8"))
        resolutions = [
            node.args[0]
            for node in ast.walk(source)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_load_json"
            and isinstance(node.args[0], ast.Call)
            and isinstance(node.args[0].func, ast.Name)
            and node.args[0].func.id == "resolve_artifact"
        ]
        self.assertEqual(len(resolutions), 1, "Hodge input must cross the verified resolver")
        self.assertEqual(
            ast.dump(resolutions[0]),
            ast.dump(ast.parse("resolve_artifact('issue43_bridge_calibration')", mode="eval").body),
        )

    def test_workflow_watches_pinned_hodge_controls_after_relocation(self):
        workflow = (ROOT / ".github" / "workflows" / "operator-field-check.yml").read_text(
            encoding="utf-8"
        )
        for event in ("push", "pull_request"):
            patterns = _positive_path_filters(workflow, event)
            self.assertNotIn("Hodge Span Lab/evidence/issue43_bridge_calibration_result.json", patterns)
            for dependency in HODGE_CONTROL_INPUTS:
                with self.subTest(event=event, dependency=dependency):
                    self.assertTrue(
                        any(fnmatch.fnmatchcase(dependency, pattern) for pattern in patterns),
                        f"{event}.paths does not watch Hodge dependency control {dependency}",
                    )

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
            dependency
            for node in ast.walk(source)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_load_json"
            for dependency in _dependency_inputs(node.args[0])
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
