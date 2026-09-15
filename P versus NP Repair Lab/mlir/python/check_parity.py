"""Parity checks between frozen legacy scientific records and MLIR-bound sidecars."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

_LOAD_BEARING_FIELDS = (
    "status",
    "selected_variable",
    "planning_shortlist",
    "states_evaluated",
    "maximum_depth",
    "bounded_reason",
    "certificate_ids",
    "certificate_digests",
)


def _display(value: Any) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return repr(value)


def compare(expected: Mapping[str, Any], reconstructed: Mapping[str, Any]) -> list[str]:
    mismatches: list[str] = []
    for field in _LOAD_BEARING_FIELDS:
        if field not in expected:
            continue
        want = expected[field]
        got = reconstructed.get(field)
        if got != want:
            mismatches.append(
                f"{field}: expected {_display(want)}, got {_display(got)}"
            )
    return mismatches


def validate_sidecar(mlir_text: str, sidecar: Mapping[str, Any]) -> dict[str, Any]:
    if sidecar.get("schema") != "pnp-mlir-parity-sidecar-v1":
        raise ValueError("unsupported parity sidecar schema")
    actual = hashlib.sha256(mlir_text.encode("utf-8")).hexdigest()
    if sidecar.get("mlir_sha256") != actual:
        raise ValueError("MLIR digest mismatch")
    scientific = sidecar.get("scientific")
    if not isinstance(scientific, dict):
        raise ValueError("parity sidecar is missing scientific record")
    return dict(scientific)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("expected", type=Path)
    parser.add_argument("mlir", type=Path)
    parser.add_argument("sidecar", type=Path)
    ns = parser.parse_args(argv)
    expected = json.loads(ns.expected.read_text(encoding="utf-8"))
    sidecar = json.loads(ns.sidecar.read_text(encoding="utf-8"))
    reconstructed = validate_sidecar(ns.mlir.read_text(encoding="utf-8"), sidecar)
    errors = compare(expected, reconstructed)
    if errors:
        for error in errors:
            print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
