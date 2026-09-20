"""Strict RMAPL Omega v0 interchange envelope.

Omega is a projection/inspection record, not a replacement for native domain
objects.  The module intentionally accepts only JSON-compatible values and
fails closed on undeclared top-level authority fields.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from typing import Any

OMEGA_SCHEMA = "rmapl-omega/v0"
INSPECTION_SCHEMA = "rmapl-omega-inspection/v0"

OMEGA_KEYS = {
    "schema",
    "id",
    "nativeType",
    "nativeIdentity",
    "sourceRefs",
    "state",
    "path",
    "frame",
    "invariants",
    "observations",
    "residuals",
    "decisionField",
    "provenance",
    "evidence",
    "claimCeiling",
    "resourceBounds",
    "domainRemainder",
    "construction",
}

_CONSTRUCTION_KEYS = {
    "native_type",
    "native_identity",
    "source_refs",
    "state",
    "path",
    "frame",
    "invariants",
    "observations",
    "residuals",
    "decision_field",
    "provenance",
    "evidence",
    "claim_ceiling",
    "resource_bounds",
    "domain_remainder",
}


def normalize_json_value(value: Any, label: str = "value") -> Any:
    """Return a canonical JSON-compatible deep copy or fail closed."""
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{label} contains a non-finite number")
        return 0.0 if value == 0.0 else value
    if isinstance(value, (list, tuple)):
        return [
            normalize_json_value(item, f"{label}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key in sorted(value):
            if not isinstance(key, str):
                raise TypeError(f"{label} object keys must be strings")
            normalized[key] = normalize_json_value(value[key], f"{label}.{key}")
        return normalized
    raise TypeError(f"{label} contains unsupported JSON value type: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    normalized = normalize_json_value(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _construction(
    *,
    native_type: str,
    native_identity: str,
    source_refs: Any,
    state: Any,
    path: Any,
    frame: Any,
    invariants: Any,
    observations: Any,
    residuals: Any,
    decision_field: Any,
    provenance: Any,
    evidence: Any,
    claim_ceiling: Any,
    resource_bounds: Any,
    domain_remainder: Any,
) -> dict[str, Any]:
    return normalize_json_value(
        {
            "native_type": native_type,
            "native_identity": native_identity,
            "source_refs": source_refs,
            "state": state,
            "path": path,
            "frame": frame,
            "invariants": invariants,
            "observations": observations,
            "residuals": residuals,
            "decision_field": decision_field,
            "provenance": provenance,
            "evidence": evidence,
            "claim_ceiling": claim_ceiling,
            "resource_bounds": resource_bounds,
            "domain_remainder": domain_remainder,
        },
        "omega construction",
    )


def make_omega(
    *,
    native_type: str,
    native_identity: str,
    source_refs: Any,
    state: Any,
    path: Any,
    frame: Any,
    invariants: Any,
    observations: Any,
    residuals: Any,
    decision_field: Any,
    provenance: Any,
    evidence: Any,
    claim_ceiling: Any,
    resource_bounds: Any,
    domain_remainder: Any,
) -> dict[str, Any]:
    if not isinstance(native_type, str) or not native_type:
        raise TypeError("native_type must be a non-empty string")
    if not isinstance(native_identity, str) or not native_identity:
        raise TypeError("native_identity must be a non-empty string")

    construction = _construction(
        native_type=native_type,
        native_identity=native_identity,
        source_refs=source_refs,
        state=state,
        path=path,
        frame=frame,
        invariants=invariants,
        observations=observations,
        residuals=residuals,
        decision_field=decision_field,
        provenance=provenance,
        evidence=evidence,
        claim_ceiling=claim_ceiling,
        resource_bounds=resource_bounds,
        domain_remainder=domain_remainder,
    )
    base = {
        "schema": OMEGA_SCHEMA,
        "nativeType": construction["native_type"],
        "nativeIdentity": construction["native_identity"],
        "sourceRefs": construction["source_refs"],
        "state": construction["state"],
        "path": construction["path"],
        "frame": construction["frame"],
        "invariants": construction["invariants"],
        "observations": construction["observations"],
        "residuals": construction["residuals"],
        "decisionField": construction["decision_field"],
        "provenance": construction["provenance"],
        "evidence": construction["evidence"],
        "claimCeiling": construction["claim_ceiling"],
        "resourceBounds": construction["resource_bounds"],
        "domainRemainder": construction["domain_remainder"],
        "construction": construction,
    }
    normalized_base = normalize_json_value(base, "omega")
    return {**deepcopy(normalized_base), "id": _sha256(normalized_base)}


def validate_omega(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise TypeError("omega record must be an object")
    extra = set(record) - OMEGA_KEYS
    if extra:
        raise ValueError(f"unsupported omega field(s): {sorted(extra)}")
    missing = OMEGA_KEYS - set(record)
    if missing:
        raise ValueError(f"missing omega field(s): {sorted(missing)}")
    if record.get("schema") != OMEGA_SCHEMA:
        raise ValueError("unsupported omega schema")
    construction = record.get("construction")
    if not isinstance(construction, dict):
        raise TypeError("omega construction must be an object")
    if set(construction) != _CONSTRUCTION_KEYS:
        raise ValueError("omega construction fields do not match v0 contract")
    rebuilt = make_omega(**construction)
    if canonical_json(record) != canonical_json(rebuilt):
        raise ValueError("omega record does not match canonical construction")
    return rebuilt


def round_trip_report(original: Any, reconstructed: Any) -> dict[str, list[str]]:
    left = normalize_json_value(original, "original")
    right = normalize_json_value(reconstructed, "reconstructed")
    if not isinstance(left, dict) or not isinstance(right, dict):
        raise TypeError("round-trip comparison requires objects")

    left_keys = set(left)
    right_keys = set(right)
    preserved = sorted(k for k in left_keys & right_keys if left[k] == right[k])
    changed = sorted(k for k in left_keys & right_keys if left[k] != right[k])
    lost = sorted(left_keys - right_keys)
    introduced = sorted(right_keys - left_keys)
    unresolved = sorted(k for k in preserved if left[k] is None)
    return {
        "preserved": preserved,
        "lost": lost,
        "introduced": introduced,
        "changed": changed,
        "unresolved": unresolved,
    }


def make_inspection_record(
    *,
    input_refs: Any,
    native_contract: str,
    operator: str,
    operator_version: str,
    condition: Any,
    trigger: Any,
    preconditions: Any,
    obligation: Any,
    expected: Any,
    actual: Any,
    residual_before: Any,
    residual_after: Any,
    preserved: Any,
    mutated: Any,
    lost: Any,
    introduced: Any,
    reconstruction: Any,
    knowledge_decay: Any,
    evidence: Any,
    claim_ceiling: Any,
    counterprobe: Any,
    provenance: Any,
    resource_bounds: Any,
    resource_usage: Any,
    unresolved: Any,
    next_decision: Any,
    domain_remainder: Any,
    gates: Any,
) -> dict[str, Any]:
    for name, value in {
        "native_contract": native_contract,
        "operator": operator,
        "operator_version": operator_version,
    }.items():
        if not isinstance(value, str) or not value:
            raise TypeError(f"{name} must be a non-empty string")
    body = normalize_json_value(
        {
            "schema": INSPECTION_SCHEMA,
            "inputRefs": input_refs,
            "nativeContract": native_contract,
            "operator": operator,
            "operatorVersion": operator_version,
            "condition": condition,
            "trigger": trigger,
            "preconditions": preconditions,
            "obligation": obligation,
            "expected": expected,
            "actual": actual,
            "residualBefore": residual_before,
            "residualAfter": residual_after,
            "preserved": preserved,
            "mutated": mutated,
            "lost": lost,
            "introduced": introduced,
            "reconstruction": reconstruction,
            "knowledgeDecay": knowledge_decay,
            "evidence": evidence,
            "claimCeiling": claim_ceiling,
            "counterprobe": counterprobe,
            "provenance": provenance,
            "resourceBounds": resource_bounds,
            "resourceUsage": resource_usage,
            "unresolved": unresolved,
            "nextDecision": next_decision,
            "domainRemainder": domain_remainder,
            "gates": gates,
        },
        "inspection record",
    )
    return body
