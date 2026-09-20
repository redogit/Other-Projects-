"""Executable Carrier–Surface bridge for the current-working S′ model layer.

This module is additive. Native S′ implementations remain authoritative in
S1 Models Lab. These records exercise the public/current semantic model
definitions as transport contracts; they do not promote scientific evidence.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any

from omega import canonical_json, make_omega, normalize_json_value, validate_omega

SEMANTIC_SCHEMA = "s1-semantic-object/v1"
CARRIER_SCHEMA = "s1-carrier-surface/v1"
CARRIER_TYPES = (
    "candidate-state",
    "survivor",
    "semantic-work-unit",
    "multi-timescale",
)

_REQUIRED_BOUNDARIES = {
    "CURRENT_WORKING_MODEL != OWNER-PINNED_IMPLEMENTATION",
    "S_PRIME_CANDIDATE != ADMITTED_SUCCESSOR",
    "METHOD_TRANSFER != EVIDENCE_TRANSFER",
}
_PROTECTED_ROOTS = {
    "objectId",
    "revision",
    "subjectState",
    "obligationFamily",
    "invariantMap",
    "claimCeiling",
    "provenance",
    "unresolvedRemainder",
}
_REPAIRABLE_PATHS = {
    ("schedule", "tau_s"),
    ("schedule", "tau_w"),
    ("schedule", "tau_T"),
    ("schedule", "tau_K"),
}


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _normalize_semantic_object(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise TypeError("S′ semantic object must be an object")
    native = normalize_json_value(record, "S′ semantic object")
    if native.get("schema") != SEMANTIC_SCHEMA:
        raise ValueError(f"S′ semantic object schema must be {SEMANTIC_SCHEMA}")
    required = {
        "schema",
        "objectId",
        "revision",
        "subjectState",
        "candidateState",
        "obligationFamily",
        "invariantMap",
        "decisionField",
        "survivor",
        "schedule",
        "claimCeiling",
        "provenance",
        "unresolvedRemainder",
    }
    missing = required - set(native)
    if missing:
        raise ValueError(f"S′ semantic object missing fields: {sorted(missing)}")
    if set(native) != required:
        extra = set(native) - required
        raise ValueError(f"S′ semantic object unsupported fields: {sorted(extra)}")
    if not isinstance(native["objectId"], str) or not native["objectId"]:
        raise ValueError("objectId must be a non-empty string")
    if type(native["revision"]) is not int or native["revision"] < 1:
        raise ValueError("revision must be a positive integer")
    for key in ("subjectState", "candidateState", "invariantMap", "decisionField", "survivor", "schedule"):
        if not isinstance(native[key], dict):
            raise TypeError(f"{key} must be an object")
    for key in ("obligationFamily", "claimCeiling", "provenance", "unresolvedRemainder"):
        if not isinstance(native[key], list):
            raise TypeError(f"{key} must be an array")
    if any(not isinstance(item, str) or not item for item in native["obligationFamily"]):
        raise ValueError("obligationFamily must contain non-empty strings")
    if any(not isinstance(item, str) or not item for item in native["claimCeiling"]):
        raise ValueError("claimCeiling must contain non-empty strings")
    if any(not isinstance(item, str) or not item for item in native["unresolvedRemainder"]):
        raise ValueError("unresolvedRemainder must contain non-empty strings")
    if any(not isinstance(item, dict) for item in native["provenance"]):
        raise ValueError("provenance must contain object records")
    return native


def semantic_residuals(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Return typed residuals without silently normalizing semantic failures."""
    native = _normalize_semantic_object(record)
    residuals: list[dict[str, Any]] = []

    if native["invariantMap"].get("objectIdentity") != native["objectId"]:
        residuals.append(
            {
                "kind": "object-identity",
                "expected": native["objectId"],
                "actual": native["invariantMap"].get("objectIdentity"),
            }
        )
    if native["invariantMap"].get("evidenceTransfer") != "DENY":
        residuals.append(
            {
                "kind": "evidence-transfer",
                "expected": "DENY",
                "actual": native["invariantMap"].get("evidenceTransfer"),
            }
        )
    if native["candidateState"].get("admitted") is not False:
        residuals.append(
            {
                "kind": "candidate-admission",
                "expected": False,
                "actual": native["candidateState"].get("admitted"),
            }
        )
    if native["invariantMap"].get("candidateIsNotAdmission") is not True:
        residuals.append(
            {
                "kind": "candidate-admission-boundary",
                "expected": True,
                "actual": native["invariantMap"].get("candidateIsNotAdmission"),
            }
        )
    if native["decisionField"].get("status") != "candidate":
        residuals.append(
            {
                "kind": "decision-field-status",
                "expected": "candidate",
                "actual": native["decisionField"].get("status"),
            }
        )

    schedule = native["schedule"]
    keys = ("tau_s", "tau_w", "tau_T", "tau_K")
    values = []
    schedule_shape_ok = True
    for key in keys:
        value = schedule.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            schedule_shape_ok = False
            residuals.append({"kind": "schedule-value", "field": key, "actual": value})
        else:
            values.append(value)
    if schedule_shape_ok and not (values[0] < values[1] < values[2] < values[3]):
        residuals.append(
            {
                "kind": "schedule-order",
                "expected": "tau_s < tau_w < tau_T < tau_K",
                "actual": {key: schedule[key] for key in keys},
            }
        )

    missing_boundaries = sorted(_REQUIRED_BOUNDARIES - set(native["claimCeiling"]))
    if missing_boundaries:
        residuals.append(
            {
                "kind": "claim-ceiling",
                "missing": missing_boundaries,
            }
        )
    return residuals


def validate_semantic_object(record: dict[str, Any]) -> dict[str, Any]:
    native = _normalize_semantic_object(record)
    residuals = semantic_residuals(native)
    if residuals:
        kinds = sorted({item["kind"] for item in residuals})
        raise ValueError(f"S′ semantic object has unresolved residuals: {kinds}")
    return native


def protected_invariant_view(record: dict[str, Any]) -> dict[str, Any]:
    native = _normalize_semantic_object(record)
    return {
        key: deepcopy(native[key])
        for key in (
            "objectId",
            "revision",
            "subjectState",
            "obligationFamily",
            "invariantMap",
            "claimCeiling",
            "provenance",
            "unresolvedRemainder",
        )
    }


def _surface_payload(native: dict[str, Any], carrier_type: str) -> dict[str, Any]:
    if carrier_type == "candidate-state":
        return {
            "subjectState": deepcopy(native["subjectState"]),
            "candidateState": deepcopy(native["candidateState"]),
            "decisionField": deepcopy(native["decisionField"]),
        }
    if carrier_type == "survivor":
        return {
            "survivor": deepcopy(native["survivor"]),
            "decisionField": deepcopy(native["decisionField"]),
        }
    if carrier_type == "semantic-work-unit":
        return {
            "workUnit": {
                "objectId": native["objectId"],
                "subjectState": deepcopy(native["subjectState"]),
                "obligationFamily": deepcopy(native["obligationFamily"]),
                "invariantMap": deepcopy(native["invariantMap"]),
                "decisionField": deepcopy(native["decisionField"]),
                "candidateState": deepcopy(native["candidateState"]),
                "survivor": deepcopy(native["survivor"]),
                "schedule": deepcopy(native["schedule"]),
                "claimCeiling": deepcopy(native["claimCeiling"]),
                "provenance": deepcopy(native["provenance"]),
                "unresolvedRemainder": deepcopy(native["unresolvedRemainder"]),
            }
        }
    if carrier_type == "multi-timescale":
        return {
            "schedule": deepcopy(native["schedule"]),
            "decisionField": deepcopy(native["decisionField"]),
        }
    raise ValueError(f"unsupported S′ carrier type: {carrier_type}")


def project_to_carrier(record: dict[str, Any], carrier_type: str) -> dict[str, Any]:
    native = validate_semantic_object(record)
    if carrier_type not in CARRIER_TYPES:
        raise ValueError(f"unsupported S′ carrier type: {carrier_type}")
    base = {
        "schema": CARRIER_SCHEMA,
        "carrierType": carrier_type,
        "objectId": native["objectId"],
        "revision": native["revision"],
        "surfaceAddress": [
            "S′",
            carrier_type,
            native["objectId"],
            native["revision"],
        ],
        "declaredInvariants": sorted(protected_invariant_view(native)),
        "claimCeiling": deepcopy(native["claimCeiling"]),
        "evidenceTransfer": "DENY",
        "authority": "current-working-model-projection",
        "payload": _surface_payload(native, carrier_type),
        "reconstructionPayload": deepcopy(native),
        "provenance": deepcopy(native["provenance"]),
    }
    normalized = normalize_json_value(base, "S′ carrier")
    return {**normalized, "id": _sha256(normalized)}


def validate_carrier(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise TypeError("S′ carrier must be an object")
    carrier = normalize_json_value(record, "S′ carrier")
    required = {
        "schema",
        "id",
        "carrierType",
        "objectId",
        "revision",
        "surfaceAddress",
        "declaredInvariants",
        "claimCeiling",
        "evidenceTransfer",
        "authority",
        "payload",
        "reconstructionPayload",
        "provenance",
    }
    if set(carrier) != required:
        raise ValueError("S′ carrier fields do not match v1 contract")
    if carrier["schema"] != CARRIER_SCHEMA:
        raise ValueError("unsupported S′ carrier schema")
    if carrier["carrierType"] not in CARRIER_TYPES:
        raise ValueError("unsupported S′ carrier type")
    if carrier["evidenceTransfer"] != "DENY":
        raise ValueError("S′ carrier may not enable evidence transfer")
    if carrier["authority"] != "current-working-model-projection":
        raise ValueError("S′ carrier authority changed")
    base = {key: carrier[key] for key in carrier if key != "id"}
    if carrier["id"] != _sha256(base):
        raise ValueError("S′ carrier id does not match canonical content")
    return carrier


def reconstruct_from_carrier(record: dict[str, Any]) -> dict[str, Any]:
    carrier = validate_carrier(record)
    native = carrier["reconstructionPayload"]
    if not isinstance(native, dict):
        raise ValueError("S′ carrier reconstruction payload is unavailable")
    rebuilt = validate_semantic_object(native)
    if rebuilt["objectId"] != carrier["objectId"]:
        raise ValueError("S′ carrier object identity disagrees with reconstruction payload")
    if rebuilt["revision"] != carrier["revision"]:
        raise ValueError("S′ carrier revision disagrees with reconstruction payload")
    if rebuilt["claimCeiling"] != carrier["claimCeiling"]:
        raise ValueError("S′ carrier claim ceiling disagrees with reconstruction payload")
    return rebuilt


def project_carrier_to_omega(record: dict[str, Any]) -> dict[str, Any]:
    carrier = validate_carrier(record)
    return make_omega(
        native_type=f"s1-current-model/{carrier['carrierType']}/v1",
        native_identity=carrier["objectId"],
        source_refs=(carrier["id"],),
        state={
            "carrierType": carrier["carrierType"],
            "revision": carrier["revision"],
        },
        path=(),
        frame={"surfaceAddress": carrier["surfaceAddress"]},
        invariants=tuple(carrier["declaredInvariants"]),
        observations=(
            {"kind": "carrier-payload", "value": carrier["payload"]},
        ),
        residuals=(),
        decision_field={
            "obligation": "transport-current-s1-model",
            "carrierType": carrier["carrierType"],
        },
        provenance=tuple(
            [
                *carrier["provenance"],
                {
                    "kind": "carrier-surface-to-omega",
                    "carrierId": carrier["id"],
                },
            ]
        ),
        evidence=(
            {
                "kind": "structural-projection",
                "detail": "Carrier–Surface to Ω transport; no independent evidence or authority is added",
                "claimCeiling": "METHOD_TRANSFER != EVIDENCE_TRANSFER",
            },
        ),
        claim_ceiling=tuple(carrier["claimCeiling"]),
        resource_bounds={},
        domain_remainder={
            "carrier": carrier,
            "authority": "current-working-model-projection",
            "evidenceTransfer": "DENY",
        },
    )


def reconstruct_carrier_from_omega(record: dict[str, Any]) -> dict[str, Any]:
    omega = validate_omega(record)
    native_type = omega["nativeType"]
    if not native_type.startswith("s1-current-model/") or not native_type.endswith("/v1"):
        raise ValueError("Omega record is not a current S′ Carrier–Surface projection")
    remainder = omega["domainRemainder"]
    carrier = remainder.get("carrier")
    if not isinstance(carrier, dict):
        raise TypeError("Omega record is missing the S′ carrier remainder")
    rebuilt = validate_carrier(carrier)
    if omega["nativeIdentity"] != rebuilt["objectId"]:
        raise ValueError("Omega native identity disagrees with S′ carrier")
    if omega["claimCeiling"] != rebuilt["claimCeiling"]:
        raise ValueError("Omega claim ceiling disagrees with S′ carrier")
    if remainder.get("evidenceTransfer") != "DENY":
        raise ValueError("Omega remainder attempted evidence transfer")
    return rebuilt


def evaluate_round_trip(
    original: dict[str, Any],
    carrier: dict[str, Any],
) -> dict[str, Any]:
    native = _normalize_semantic_object(original)
    residuals: list[dict[str, Any]] = []

    if not isinstance(carrier, dict):
        return {
            "classification": "UNKNOWN",
            "residuals": [{"kind": "carrier-unavailable"}],
            "reconstruction": None,
        }

    if carrier.get("objectId") != native["objectId"]:
        residuals.append(
            {
                "kind": "protected-invariant-mismatch",
                "field": "objectId",
                "expected": native["objectId"],
                "actual": carrier.get("objectId"),
            }
        )
    if carrier.get("claimCeiling") != native["claimCeiling"]:
        residuals.append(
            {
                "kind": "protected-invariant-mismatch",
                "field": "claimCeiling",
                "expected": native["claimCeiling"],
                "actual": carrier.get("claimCeiling"),
            }
        )

    reconstruction_payload = carrier.get("reconstructionPayload")
    if reconstruction_payload is None:
        residuals.append({"kind": "reconstruction-unavailable"})
        return {
            "classification": "SEMANTIC_DECAY"
            if any(item["kind"] == "protected-invariant-mismatch" for item in residuals)
            else "UNKNOWN",
            "residuals": residuals,
            "reconstruction": None,
        }

    try:
        validate_carrier(carrier)
    except (TypeError, ValueError) as exc:
        residuals.append({"kind": "carrier-integrity", "detail": str(exc)})

    try:
        rebuilt = _normalize_semantic_object(reconstruction_payload)
    except (TypeError, ValueError) as exc:
        residuals.append({"kind": "reconstruction-invalid", "detail": str(exc)})
        return {
            "classification": "SEMANTIC_DECAY",
            "residuals": residuals,
            "reconstruction": None,
        }

    original_protected = protected_invariant_view(native)
    rebuilt_protected = protected_invariant_view(rebuilt)
    for key in sorted(original_protected):
        if original_protected[key] != rebuilt_protected[key]:
            residuals.append(
                {
                    "kind": "protected-invariant-mismatch",
                    "field": key,
                    "expected": original_protected[key],
                    "actual": rebuilt_protected[key],
                }
            )

    if any(item["kind"] == "protected-invariant-mismatch" for item in residuals):
        classification = "SEMANTIC_DECAY"
    elif canonical_json(native) == canonical_json(rebuilt):
        classification = "ROTATION"
    else:
        residuals.append({"kind": "non-protected-change"})
        classification = "MUTATION"

    return {
        "classification": classification,
        "residuals": residuals,
        "reconstruction": rebuilt,
    }


def _set_path(value: dict[str, Any], path: tuple[str, ...], new_value: Any) -> None:
    cursor: Any = value
    for segment in path[:-1]:
        if not isinstance(cursor, dict) or segment not in cursor:
            raise ValueError(f"repair path does not exist: {'.'.join(path)}")
        cursor = cursor[segment]
    if not isinstance(cursor, dict) or path[-1] not in cursor:
        raise ValueError(f"repair path does not exist: {'.'.join(path)}")
    cursor[path[-1]] = normalize_json_value(new_value, "repair value")


def one_degree_repair(
    record: dict[str, Any],
    path: tuple[str, ...],
    new_value: Any,
) -> dict[str, Any]:
    native = _normalize_semantic_object(record)
    if not isinstance(path, tuple) or not path or any(not isinstance(x, str) or not x for x in path):
        raise TypeError("repair path must be a non-empty tuple of strings")
    if path[0] in _PROTECTED_ROOTS:
        raise ValueError(f"repair path is protected: {'.'.join(path)}")
    if path not in _REPAIRABLE_PATHS:
        raise ValueError(f"path is not a declared one-degree repair path: {'.'.join(path)}")

    before = semantic_residuals(native)
    candidate = deepcopy(native)
    _set_path(candidate, path, new_value)
    after = semantic_residuals(candidate)

    changed = []
    if canonical_json(native) != canonical_json(candidate):
        changed.append(".".join(path))
    if len(changed) != 1:
        raise ValueError("one-degree repair must change exactly one semantic path")

    before_kinds = {item["kind"] for item in before}
    after_kinds = {item["kind"] for item in after}
    improved = len(after) < len(before) and after_kinds.issubset(before_kinds)
    status = "REPAIRED" if improved else "CANDIDATE_ONLY"

    return {
        "status": status,
        "changedSemanticPaths": changed,
        "candidate": candidate,
        "residualBefore": before,
        "residualAfter": after,
        "counterprobe": {
            "kind": "no-repair-baseline",
            "residuals": before,
            "distinguishes": before != after,
        },
        "admitted": False,
        "claimCeiling": deepcopy(native["claimCeiling"]),
    }
