"""Native-domain adapters for the RMAPL Omega v0 envelope.

Adapters project only repeated shared roles.  Exact native reconstruction data
stays in domainRemainder and does not become generic Omega authority.
"""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any, Callable

from decision_field import DecisionField, Evidence
from omega import canonical_json, make_omega, normalize_json_value, round_trip_report, validate_omega


def _sorted_encoded(items):
    encoded = [_encode_native(item) for item in items]
    return sorted(encoded, key=canonical_json)


def _encode_native(value: Any) -> dict[str, Any]:
    if isinstance(value, Evidence):
        return {
            "type": "Evidence",
            "kind": value.kind,
            "detail": value.detail,
            "certificate": _encode_native(value.certificate),
            "claimCeiling": value.claim_ceiling,
        }
    if isinstance(value, tuple):
        return {"type": "tuple", "items": [_encode_native(item) for item in value]}
    if isinstance(value, frozenset):
        return {"type": "frozenset", "items": _sorted_encoded(value)}
    if isinstance(value, list):
        return {"type": "list", "items": [_encode_native(item) for item in value]}
    if isinstance(value, dict):
        return {
            "type": "dict",
            "items": [[key, _encode_native(value[key])] for key in sorted(value)],
        }
    if is_dataclass(value):
        return {
            "type": f"dataclass:{type(value).__name__}",
            "fields": [[f.name, _encode_native(getattr(value, f.name))] for f in fields(value)],
        }
    return {"type": "json", "value": normalize_json_value(value, "native value")}


def _decode_native(value: dict[str, Any]) -> Any:
    if not isinstance(value, dict) or "type" not in value:
        raise TypeError("encoded native value must be an object with type")
    kind = value["type"]
    if kind == "json":
        return normalize_json_value(value.get("value"), "encoded json")
    if kind == "tuple":
        return tuple(_decode_native(item) for item in value.get("items", []))
    if kind == "frozenset":
        return frozenset(_decode_native(item) for item in value.get("items", []))
    if kind == "list":
        return [_decode_native(item) for item in value.get("items", [])]
    if kind == "dict":
        return {key: _decode_native(item) for key, item in value.get("items", [])}
    if kind == "Evidence":
        return Evidence(
            kind=value["kind"],
            detail=value["detail"],
            certificate=_decode_native(value["certificate"]),
            claim_ceiling=value["claimCeiling"],
        )
    raise ValueError(f"unsupported encoded native type: {kind}")


def _decision_field_native_record(field: DecisionField) -> dict[str, Any]:
    return {
        "possibilities": _encode_native(field.possibilities),
        "relations": _encode_native(field.relations),
        "evidence": _encode_native(field.evidence),
        "goal": _encode_native(field.goal),
        "unresolved": _encode_native(field.unresolved),
        "observer": _encode_native(field.observer),
        "history": _encode_native(field.history),
    }


def _sequence_view(value: Any) -> list[Any]:
    if isinstance(value, frozenset):
        normalized = [normalize_json_value(item, "sequence item") for item in value]
        return sorted(normalized, key=canonical_json)
    if isinstance(value, (tuple, list)):
        return [normalize_json_value(item, "sequence item") for item in value]
    return [normalize_json_value(value, "sequence item")]


def _evidence_view(evidence: Any) -> list[dict[str, Any]]:
    result = []
    for item in evidence:
        if isinstance(item, Evidence):
            result.append(
                {
                    "kind": item.kind,
                    "detail": item.detail,
                    "certificate": normalize_json_value(item.certificate, "evidence certificate"),
                    "claimCeiling": item.claim_ceiling,
                }
            )
        elif isinstance(item, dict):
            result.append(normalize_json_value(item, "evidence"))
        else:
            raise TypeError("Decision Field evidence must contain Evidence or object records")
    return result


def project_decision_field(
    field: DecisionField,
    native_identity: str,
    source_ref: str,
) -> dict[str, Any]:
    if not isinstance(field, DecisionField):
        raise TypeError("field must be a DecisionField")
    if not isinstance(native_identity, str) or not native_identity:
        raise TypeError("native_identity must be a non-empty string")
    if not isinstance(source_ref, str) or not source_ref:
        raise TypeError("source_ref must be a non-empty string")

    evidence = _evidence_view(field.evidence)
    claim_ceiling = sorted(
        {
            item.get("claimCeiling", "BOUNDED")
            for item in evidence
            if isinstance(item.get("claimCeiling", "BOUNDED"), str)
        }
        or {"BOUNDED"}
    )
    native_record = _decision_field_native_record(field)
    unresolved = _sequence_view(field.unresolved)

    return make_omega(
        native_type="decision-field/v1",
        native_identity=native_identity,
        source_refs=(source_ref,),
        state={"possibilities": _sequence_view(field.possibilities)},
        path=_sequence_view(field.history),
        frame=normalize_json_value(field.observer, "Decision Field observer"),
        invariants=(
            "goal-preserved",
            "evidence-kind-preserved",
            "unresolved-explicit",
            "PLANNER != VERIFIER",
        ),
        observations=(),
        residuals=tuple(
            {"kind": "unresolved", "value": value}
            for value in unresolved
        ),
        decision_field={
            "goal": normalize_json_value(field.goal, "Decision Field goal"),
            "relations": _sequence_view(field.relations),
        },
        provenance=(
            {
                "kind": "native-adapter",
                "sourceRef": source_ref,
                "nativeIdentity": native_identity,
            },
        ),
        evidence=tuple(evidence),
        claim_ceiling=tuple(claim_ceiling),
        resource_bounds={},
        domain_remainder={
            "nativeClass": "DecisionField",
            "encodedNative": native_record,
            "projectedFields": [
                "possibilities",
                "relations",
                "evidence",
                "goal",
                "unresolved",
                "observer",
                "history",
            ],
        },
    )


def reconstruct_decision_field(omega: dict[str, Any]) -> DecisionField:
    valid = validate_omega(omega)
    if valid["nativeType"] != "decision-field/v1":
        raise ValueError("omega record is not a Decision Field projection")
    remainder = valid["domainRemainder"]
    if remainder.get("nativeClass") != "DecisionField":
        raise ValueError("Decision Field native remainder is missing")
    native = remainder.get("encodedNative")
    if not isinstance(native, dict):
        raise TypeError("Decision Field encoded native record is missing")
    return DecisionField(
        possibilities=_decode_native(native["possibilities"]),
        relations=_decode_native(native["relations"]),
        evidence=_decode_native(native["evidence"]),
        goal=_decode_native(native["goal"]),
        unresolved=_decode_native(native["unresolved"]),
        observer=_decode_native(native["observer"]),
        history=_decode_native(native["history"]),
    )


def _validate_s1(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise TypeError("S'1 experience must be an object")
    if record.get("schema") != "s1-experience/v0":
        raise ValueError("S'1 adapter requires schema s1-experience/v0")
    if record.get("operatorVersion") != "S'1-Ops v0":
        raise ValueError("S'1 adapter requires operatorVersion S'1-Ops v0")
    for key in ("id", "initialState", "mirrorId", "shell"):
        if not isinstance(record.get(key), str) or not record[key]:
            raise ValueError(f"S'1 {key} must be a non-empty string")
    actions = record.get("actions")
    if not isinstance(actions, list):
        raise TypeError("S'1 actions must be a list")
    normalized_actions = []
    for action in actions:
        if not isinstance(action, dict) or set(action) != {"plane", "degrees"}:
            raise ValueError("S'1 action must contain exactly plane and degrees")
        if action["plane"] not in {"xw", "yw", "zw"}:
            raise ValueError("S'1 action plane must be xw, yw, or zw")
        if type(action["degrees"]) is not int or action["degrees"] not in (-1, 1):
            raise ValueError("S'1 action degrees must be exact +1 or -1")
        normalized_actions.append(
            {"plane": action["plane"], "degrees": action["degrees"]}
        )
    observer = record.get("observer")
    if not isinstance(observer, dict):
        raise TypeError("S'1 observer must be an object")
    normalized = normalize_json_value(record, "S'1 experience")
    normalized["actions"] = normalized_actions
    return normalized


def project_s1_experience(record: dict[str, Any]) -> dict[str, Any]:
    native = _validate_s1(record)
    native_remainder = normalize_json_value(native.get("nativeRemainder", {}), "S'1 native remainder")
    provenance = normalize_json_value(native.get("provenance", {}), "S'1 provenance")
    return make_omega(
        native_type="s1-experience/v0",
        native_identity=native["id"],
        source_refs=(native["id"], native["initialState"]),
        state={
            "initialState": native["initialState"],
            "shell": native["shell"],
        },
        path=tuple(native["actions"]),
        frame=native["observer"],
        invariants=(
            "ordered-action-chronology",
            "source-identity",
            "mirror-reference",
            "SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",
        ),
        observations=(),
        residuals=(),
        decision_field={
            "obligation": "replay-and-reframe",
            "mirrorId": native["mirrorId"],
        },
        provenance=(
            {"kind": "native-s1-provenance", "detail": provenance},
        ),
        evidence=(
            {
                "kind": "software-verification",
                "detail": "S'1 native experience projection",
                "claimCeiling": "SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",
            },
        ),
        claim_ceiling=(
            "SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",
            "OBSERVER != TRUTH_AUTHORITY",
            "SAME_EVENT != SAME_OBSERVATION",
        ),
        resource_bounds={},
        domain_remainder={
            "nativeRemainder": native_remainder,
            "native": native,
            "projectedFields": [
                "id",
                "initialState",
                "mirrorId",
                "shell",
                "operatorVersion",
                "actions",
                "observer",
                "provenance",
            ],
        },
    )


def reconstruct_s1_experience(omega: dict[str, Any]) -> dict[str, Any]:
    valid = validate_omega(omega)
    if valid["nativeType"] != "s1-experience/v0":
        raise ValueError("omega record is not an S'1 experience projection")
    native = valid["domainRemainder"].get("native")
    if not isinstance(native, dict):
        raise TypeError("S'1 native reconstruction record is missing")
    return normalize_json_value(native, "S'1 native reconstruction")


def _native_comparison_view(value: Any) -> dict[str, Any]:
    if isinstance(value, DecisionField):
        return _decision_field_native_record(value)
    if isinstance(value, dict):
        return normalize_json_value(value, "native record")
    return {"encoded": _encode_native(value)}


def adapter_round_trip(
    native: Any,
    projector: Callable[[Any], dict[str, Any]],
    reconstructor: Callable[[dict[str, Any]], Any],
) -> dict[str, Any]:
    omega = projector(native)
    rebuilt = reconstructor(omega)
    return {
        "omegaId": omega["id"],
        "nativeType": omega["nativeType"],
        "reconstruction": round_trip_report(
            _native_comparison_view(native),
            _native_comparison_view(rebuilt),
        ),
        "domainRemainder": omega["domainRemainder"],
    }
