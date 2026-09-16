from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import gsfl_operator_projection as projection

ROOT = Path(__file__).resolve().parent
DEFAULT_MACRO_PROFILE = ROOT / "gsfl-bidirectional-macro-profile.json"
DEFAULT_OPERATOR_PROFILE = ROOT / "gsfl-operator-profile.json"
EXPECTED_CYCLE = ["SEEK", "QUESTION", "REFRAME", "BUILD", "RETURN_INWARD"]


def load_macro_profile(path: Path | str = DEFAULT_MACRO_PROFILE) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_operator_profile(path: Path | str = DEFAULT_OPERATOR_PROFILE) -> dict[str, Any]:
    return projection.load_profile(path)


def validate_macro_profile(
    profile: dict[str, Any],
    operator_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    operator_profile = operator_profile or load_operator_profile()
    operator_report = projection.validate_profile(operator_profile)
    if not operator_report["valid"]:
        errors.append("operator profile is invalid")

    if profile.get("kind") != "COMPOSITE_MACRO_PROFILE":
        errors.append("profile kind mismatch")
    if profile.get("authority_model") != "MACRO_COMPOSITION_DOES_NOT_CREATE_PRIMITIVE_AUTHORITY":
        errors.append("authority model mismatch")
    if profile.get("source_gsfl_lifecycle") != "COMPLETE_BOUNDED_V0_1":
        errors.append("source lifecycle mismatch")

    macros = profile.get("macros", [])
    macro_ids = [row.get("id") for row in macros]
    if len(macro_ids) != len(set(macro_ids)):
        errors.append("duplicate macro id")
    if profile.get("cycle_order") != EXPECTED_CYCLE:
        errors.append("cycle order mismatch")
    if macro_ids != EXPECTED_CYCLE:
        errors.append("macro registry order mismatch")

    operator_ids = {row.get("id") for row in operator_profile.get("operators", [])}
    if set(macro_ids) & operator_ids:
        errors.append("macro id collides with primitive operator id")

    unique_operators: set[str] = set()
    for row in macros:
        macro_id = row.get("id")
        phase = row.get("phase")
        expansion = row.get("expansion")
        if phase not in {"OUTWARD", "INWARD"}:
            errors.append(f"invalid phase: {macro_id}")
        if not isinstance(expansion, list) or not expansion:
            errors.append(f"empty expansion: {macro_id}")
            continue
        unknown = [operator_id for operator_id in expansion if operator_id not in operator_ids]
        if unknown:
            errors.append(f"unknown operator in {macro_id}: {unknown[0]}")
        unique_operators.update(expansion)

    if macros:
        outward = [row.get("id") for row in macros if row.get("phase") == "OUTWARD"]
        inward = [row.get("id") for row in macros if row.get("phase") == "INWARD"]
        if outward != ["SEEK", "QUESTION", "REFRAME", "BUILD"]:
            errors.append("outward macro order mismatch")
        if inward != ["RETURN_INWARD"]:
            errors.append("inward macro order mismatch")

    return {
        "valid": not errors,
        "errors": errors,
        "macro_count": len(macros),
        "unique_operator_count": len(unique_operators),
    }


def _macro_spec(macro_id: str, profile: dict[str, Any]) -> dict[str, Any]:
    for row in profile["macros"]:
        if row["id"] == macro_id:
            return row
    raise KeyError(f"unknown GSFL macro: {macro_id}")


def apply_macro(
    macro_id: str,
    envelope: dict[str, Any],
    *,
    macro_params: dict[str, dict[str, Any]] | None = None,
    profile_path: Path | str = DEFAULT_MACRO_PROFILE,
    operator_profile_path: Path | str = DEFAULT_OPERATOR_PROFILE,
) -> dict[str, Any]:
    profile = load_macro_profile(profile_path)
    operator_profile = load_operator_profile(operator_profile_path)
    report = validate_macro_profile(profile, operator_profile)
    if not report["valid"]:
        raise ValueError("invalid GSFL bidirectional macro profile: " + "; ".join(report["errors"]))

    spec = _macro_spec(macro_id, profile)
    out = deepcopy(envelope)
    out.setdefault("macro_trace", [])
    params_by_operator = macro_params or {}

    for operator_id in spec["expansion"]:
        operator_params = dict(params_by_operator.get(operator_id, {}))
        out = projection.apply_operator(
            operator_id,
            out,
            profile_path=operator_profile_path,
            **operator_params,
        )

    out.setdefault("macro_trace", []).append({
        "macro": macro_id,
        "phase": spec["phase"],
        "purpose": spec["purpose"],
        "expansion": list(spec["expansion"]),
        "source_lifecycle": profile["source_gsfl_lifecycle"],
    })
    return out


def run_bidirectional_cycle(
    envelope: dict[str, Any],
    *,
    cycle_params: dict[str, dict[str, dict[str, Any]]] | None = None,
    profile_path: Path | str = DEFAULT_MACRO_PROFILE,
    operator_profile_path: Path | str = DEFAULT_OPERATOR_PROFILE,
) -> dict[str, Any]:
    profile = load_macro_profile(profile_path)
    operator_profile = load_operator_profile(operator_profile_path)
    report = validate_macro_profile(profile, operator_profile)
    if not report["valid"]:
        raise ValueError("invalid GSFL bidirectional macro profile: " + "; ".join(report["errors"]))

    out = deepcopy(envelope)
    out.setdefault("macro_trace", [])
    params_by_macro = cycle_params or {}
    for macro_id in profile["cycle_order"]:
        out = apply_macro(
            macro_id,
            out,
            macro_params=params_by_macro.get(macro_id, {}),
            profile_path=profile_path,
            operator_profile_path=operator_profile_path,
        )

    out["cycle_summary"] = {
        "profile_id": profile["profile_id"],
        "cycle_order": list(profile["cycle_order"]),
        "outward": ["SEEK", "QUESTION", "REFRAME", "BUILD"],
        "inward": ["RETURN_INWARD"],
        "completed": True,
        "source_lifecycle": profile["source_gsfl_lifecycle"],
        "boundaries": list(profile["boundaries"]),
    }
    return out


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2, separators=(",", ": ")) + "\n"
