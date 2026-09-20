"""Bounded all-directional relation sidecar for RMAPL/Omega v0.

The relation field binds method-only relation and consequence metadata to an
existing Omega identity without modifying the Omega record or promoting any
referenced evidence. Domain-specific relation types remain open strings so the
shared carrier does not become a shared ontology.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import math
import re
from typing import Any, Mapping

from omega import canonical_json, normalize_json_value


RELATION_FIELD_SCHEMA = "rmapl-omega-relational-field/v0"
AUTHORITY = "method-only"

CURRENTNESS = frozenset(
    {
        "CURRENT_CANONICAL",
        "CURRENT_EPOCH",
        "HISTORICAL_PREDECESSOR",
        "HISTORICAL_SUPERSEDED",
        "COEXISTING_LINEAGE",
        "PRESERVED_UNRESOLVED",
        "PRESERVED",
    }
)
DIRECTIONS = frozenset({"A_TO_B", "B_TO_A", "BIDIRECTIONAL", "AMBIENT", "UNDIRECTED"})
PERMISSIONS = frozenset({"ALLOW", "DENY", "UNKNOWN"})
REVERSIBILITY = frozenset({"REVERSIBLE", "BOUNDED", "IRREVERSIBLE", "UNKNOWN"})
WAY_BACK_STATUS = frozenset({"EXACT_REFERENCE", "BOUNDED_REFERENCE", "UNRESOLVED"})

BOUNDARIES = (
    "RELATION != MERGE",
    "METHOD_TRANSFER != EVIDENCE_TRANSFER",
    "OMEGA_VIEW != NATIVE_OBJECT",
    "CURRENT != PROVED",
    "PAIRITY != FORCED_EQUALITY",
)

_CONSEQUENCE_KEYS = {"self", "neighbor", "shared", "ambient", "delayed"}
_RELATION_INPUT_KEYS = {
    "source",
    "target",
    "type",
    "direction",
    "obligation",
    "evidenceRefs",
    "permission",
    "cost",
    "reversibility",
    "uncertainty",
    "provenance",
}
_RELATION_KEYS = _RELATION_INPUT_KEYS | {"id"}
_FIELD_KEYS = {
    "schema",
    "id",
    "omegaId",
    "currentness",
    "authority",
    "relations",
    "consequence",
    "wayBack",
    "boundaries",
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{label} must be a non-empty string")
    return value


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{label} must be a list")
    out = []
    for index, item in enumerate(value):
        out.append(_nonempty_string(item, f"{label}[{index}]"))
    return out


def _omega_id(value: Any, label: str = "omega_id") -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"{label} must be a lowercase SHA-256 Omega id")
    return value


def _relation(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("relation must be an object")
    if set(value) != _RELATION_INPUT_KEYS:
        missing = sorted(_RELATION_INPUT_KEYS - set(value))
        extra = sorted(set(value) - _RELATION_INPUT_KEYS)
        raise ValueError(f"relation fields mismatch: missing={missing}, extra={extra}")

    source = _nonempty_string(value["source"], "relation source")
    target = _nonempty_string(value["target"], "relation target")
    kind = _nonempty_string(value["type"], "relation type")

    direction = value["direction"]
    if direction not in DIRECTIONS:
        raise ValueError(f"unsupported relation direction: {direction!r}")

    permission = value["permission"]
    if permission not in PERMISSIONS:
        raise ValueError(f"unsupported relation permission: {permission!r}")

    reversibility = value["reversibility"]
    if reversibility not in REVERSIBILITY:
        raise ValueError(f"unsupported relation reversibility: {reversibility!r}")

    cost = value["cost"]
    if isinstance(cost, bool) or not isinstance(cost, (int, float)):
        raise TypeError("relation cost must be numeric")
    cost = float(cost)
    if not math.isfinite(cost) or cost < 0:
        raise ValueError("relation cost must be a non-negative finite number")

    uncertainty = value["uncertainty"]
    if isinstance(uncertainty, bool) or not isinstance(uncertainty, (int, float)):
        raise TypeError("relation uncertainty must be numeric")
    uncertainty = float(uncertainty)
    if not math.isfinite(uncertainty) or not 0.0 <= uncertainty <= 1.0:
        raise ValueError("relation uncertainty must be in [0, 1]")

    body = normalize_json_value(
        {
            "source": source,
            "target": target,
            "type": kind,
            "direction": direction,
            "obligation": value["obligation"],
            "evidenceRefs": _string_list(value["evidenceRefs"], "relation evidenceRefs"),
            "permission": permission,
            "cost": cost,
            "reversibility": reversibility,
            "uncertainty": uncertainty,
            "provenance": _string_list(value["provenance"], "relation provenance"),
        },
        "relation",
    )
    return {"id": _sha256(body), **deepcopy(body)}


def _consequence(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("consequence must be an object")
    if set(value) != _CONSEQUENCE_KEYS:
        missing = sorted(_CONSEQUENCE_KEYS - set(value))
        extra = sorted(set(value) - _CONSEQUENCE_KEYS)
        raise ValueError(f"consequence fields mismatch: missing={missing}, extra={extra}")
    return normalize_json_value(dict(value), "consequence")


def _way_back(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise TypeError("way_back must be an object")
    if set(value) != {"omegaId", "status"}:
        raise ValueError("way_back fields must be exactly omegaId and status")
    omega_id = _omega_id(value["omegaId"], "way_back omegaId")
    status = value["status"]
    if status not in WAY_BACK_STATUS:
        raise ValueError(f"unsupported way_back status: {status!r}")
    return {"omegaId": omega_id, "status": status}


def make_relation_field(
    *,
    omega_id: str,
    currentness: str,
    relations: Any,
    consequence: Any,
    way_back: Any,
) -> dict[str, Any]:
    """Create a canonical method-only relation field bound to an Omega id."""
    omega_id = _omega_id(omega_id)
    if currentness not in CURRENTNESS:
        raise ValueError(f"unsupported currentness: {currentness!r}")
    if not isinstance(relations, (list, tuple)):
        raise TypeError("relations must be a list")

    base = normalize_json_value(
        {
            "schema": RELATION_FIELD_SCHEMA,
            "omegaId": omega_id,
            "currentness": currentness,
            "authority": AUTHORITY,
            "relations": [_relation(item) for item in relations],
            "consequence": _consequence(consequence),
            "wayBack": _way_back(way_back),
            "boundaries": list(BOUNDARIES),
        },
        "relation field",
    )
    return {"id": _sha256(base), **deepcopy(base)}


def validate_relation_field(record: Any) -> dict[str, Any]:
    """Validate canonical shape and identity, rebuilding from declared inputs."""
    if not isinstance(record, Mapping):
        raise TypeError("relation field must be an object")
    if set(record) != _FIELD_KEYS:
        missing = sorted(_FIELD_KEYS - set(record))
        extra = sorted(set(record) - _FIELD_KEYS)
        raise ValueError(f"relation field fields mismatch: missing={missing}, extra={extra}")
    if record.get("schema") != RELATION_FIELD_SCHEMA:
        raise ValueError("unsupported relation field schema")
    if record.get("authority") != AUTHORITY:
        raise ValueError("relation field authority changed")
    if tuple(record.get("boundaries", ())) != BOUNDARIES:
        raise ValueError("relation field boundaries changed")

    raw_relations = []
    relations = record.get("relations")
    if not isinstance(relations, list):
        raise TypeError("relation field relations must be a list")
    for item in relations:
        if not isinstance(item, Mapping) or set(item) != _RELATION_KEYS:
            raise ValueError("relation field relation does not match canonical fields")
        raw_relations.append({key: deepcopy(item[key]) for key in _RELATION_INPUT_KEYS})

    rebuilt = make_relation_field(
        omega_id=record.get("omegaId"),
        currentness=record.get("currentness"),
        relations=raw_relations,
        consequence=record.get("consequence"),
        way_back=record.get("wayBack"),
    )
    if canonical_json(record) != canonical_json(rebuilt):
        raise ValueError("relation field does not match canonical construction")
    return rebuilt
