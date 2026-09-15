"""Deterministic textual MLIR emission for frozen legacy P-vs-NP records."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

_ALLOWED_STATUS = {"SAT", "UNSAT", "UNKNOWN", "BOUND"}


def _mlir_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _i64(name: str, value: Any) -> str:
    return f"{name} = {int(value)} : i64"


def _i64_array(name: str, values: list[int]) -> str:
    body = ", ".join(str(int(value)) for value in values)
    return f"{name} = array<i64: {body}>"


def _module_attributes(case: Mapping[str, Any]) -> str:
    attrs = [f"pnp_case = {_mlir_string(str(case['case']))}"]
    if case.get("planning_shortlist") is not None:
        attrs.append(_i64_array("planning_shortlist", list(case["planning_shortlist"])))
    if case.get("selected_variable") is not None:
        attrs.append(_i64("selected_variable", case["selected_variable"]))
    if case.get("states_evaluated") is not None:
        attrs.append(_i64("states_evaluated", case["states_evaluated"]))
    if case.get("maximum_depth") is not None:
        attrs.append(_i64("maximum_depth", case["maximum_depth"]))
    if case.get("bounded_reason") is not None:
        attrs.append(f"bounded_reason = {_mlir_string(str(case['bounded_reason']))}")
    if case.get("provenance_digest") is not None:
        attrs.append(f"provenance_digest = {_mlir_string(str(case['provenance_digest']))}")
    certificate_ids = sorted(str(item) for item in case.get("certificate_ids", []))
    if certificate_ids:
        body = ", ".join(_mlir_string(item) for item in certificate_ids)
        attrs.append(f"certificate_ids = [{body}]")
    return ", ".join(attrs)


def emit_case(case: Mapping[str, Any]) -> str:
    status = str(case["status"])
    if status not in _ALLOWED_STATUS:
        raise ValueError(f"unsupported symbolic status: {status}")

    case_id = str(case["case"])
    obligation = str(case.get("obligation", "sat"))
    carrier_kind = str(case.get("carrier_kind", "cnf"))
    attrs = _module_attributes(case)
    lines = [f"module attributes {{{attrs}}} {{"]
    lines.append(
        "  %src = \"pnp_core.source\"() "
        f"<{{source_id = {_mlir_string(case_id)}, obligation = {_mlir_string(obligation)}}}> "
        f": () -> !pnp_carrier.carrier<{_mlir_string(carrier_kind)}>"
    )

    cert_ids = sorted(str(item) for item in case.get("certificate_ids", []))
    costs = {str(k): v for k, v in case.get("costs", {}).items()}
    if cert_ids or costs:
        reference = cert_ids[0] if cert_ids else "legacy-parity-sidecar"
        lines.append(
            "  %cert = \"pnp_evidence.certificate\"(%src) "
            f"<{{verifier = \"legacy-parity\", reference = {_mlir_string(reference)}}}> "
            f": (!pnp_carrier.carrier<{_mlir_string(carrier_kind)}>) -> !pnp_evidence.certificate"
        )
        if costs:
            cost_items = []
            for name in sorted(costs):
                value = costs[name]
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise TypeError(f"cost {name!r} must be numeric")
                if value < 0:
                    raise ValueError(f"cost {name!r} must be nonnegative")
                if isinstance(value, int):
                    cost_items.append(f"{name} = {value} : i64")
                else:
                    cost_items.append(f"{name} = {value!r} : f64")
            lines.append(
                "  \"pnp_evidence.record_cost\"(%cert) "
                f"<{{costs = {{{', '.join(cost_items)}}}}}> : (!pnp_evidence.certificate) -> ()"
            )

    lines.append(
        "  \"pnp_core.return\"(%src) "
        f"<{{status = #pnp_core.status<{_mlir_string(status)}>}}> "
        f": (!pnp_carrier.carrier<{_mlir_string(carrier_kind)}>) -> ()"
    )
    lines.append("}")
    return "\n".join(lines) + "\n"


def build_sidecar(mlir_text: str, scientific: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": "pnp-mlir-parity-sidecar-v1",
        "mlir_sha256": hashlib.sha256(mlir_text.encode("utf-8")).hexdigest(),
        "scientific": dict(scientific),
    }


def find_case(manifest: Mapping[str, Any], case_name: str) -> dict[str, Any]:
    for record in manifest.get("records", []):
        scientific = record.get("scientific", {})
        for case in scientific.get("cases", []):
            if case.get("case") == case_name:
                out = dict(case)
                out["provenance_digest"] = record.get("sha256", "")
                out.setdefault(
                    "costs",
                    {
                        key: value
                        for key, value in case.items()
                        if key.startswith("planning_") and isinstance(value, (int, float))
                    },
                )
                return out
    raise KeyError(case_name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("case")
    parser.add_argument("output", type=Path)
    parser.add_argument("--sidecar", type=Path)
    ns = parser.parse_args(argv)
    manifest = json.loads(ns.manifest.read_text(encoding="utf-8"))
    case = find_case(manifest, ns.case)
    text = emit_case(case)
    ns.output.parent.mkdir(parents=True, exist_ok=True)
    ns.output.write_text(text, encoding="utf-8")
    if ns.sidecar:
        sidecar = build_sidecar(text, case)
        ns.sidecar.parent.mkdir(parents=True, exist_ok=True)
        ns.sidecar.write_text(
            json.dumps(sidecar, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
