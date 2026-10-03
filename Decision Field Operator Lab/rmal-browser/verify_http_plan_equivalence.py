"""Differential evidence: current RMAPL HTTP planner vs RMAL port.

Python is an oracle for this migration test only. The RMAL runtime host under
test is a native executable and does not invoke Python.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

LAB = Path(__file__).resolve().parents[1]
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from tools.plan_independent_browser_http import plan


FIXTURES = (
    ("http", "127.0.0.1", "/test"),
    ("https", "example.com", "/docs"),
)


def parse_line(line: str) -> dict[str, str]:
    fields = {}
    for token in line.split()[1:]:
        key, value = token.split("=", 1)
        fields[key] = value
    return fields


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: verify_http_plan_equivalence.py "
            "<browser_rmal_http_plan_host> <browser_http_plan.rmal>"
        )

    host = Path(sys.argv[1])
    source = Path(sys.argv[2])
    completed = subprocess.run(
        [str(host), str(source)],
        capture_output=True,
        text=True,
        check=True,
    )

    plan_lines = [
        parse_line(line)
        for line in completed.stdout.splitlines()
        if line.startswith("RMAL_HTTP_PLAN ")
    ]
    if len(plan_lines) != len(FIXTURES):
        raise AssertionError(
            f"expected {len(FIXTURES)} RMAL plan lines, got {len(plan_lines)}\n"
            + completed.stdout
        )

    for actual, (scheme, host_name, path) in zip(plan_lines, FIXTURES):
        payload, receipt = plan(
            host=host_name,
            path=path,
            scheme=scheme,
        )
        expected_residual = receipt["residual"]

        assert actual["scheme"] == scheme, actual
        assert actual["host"] == receipt["host"], actual
        assert int(actual["port"]) == receipt["port"], actual
        assert actual["transport"] == expected_residual["kind"], actual
        assert actual["detail"] == expected_residual["detail"], actual
        assert int(actual["max"]) == receipt["maxResponseBytes"], actual
        assert bytes.fromhex(actual["request_hex"]) == payload, actual

    if "RMAL_HTTP_PLAN_RECEIPT calls=2 python_runtime_used=false" not in completed.stdout:
        raise AssertionError("native RMAL planner receipt missing")

    print("RMAPL_RMAL_HTTP_PLAN_EQUIVALENCE PASS")
    print("PYTHON_DIFFERENTIAL_ORACLE != RMAL_RUNTIME_DEPENDENCY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
