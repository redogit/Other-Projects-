from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_PROFILE = ROOT / "gsfl-operator-profile.json"
CANONICAL_DELEGATES = {"DISTINGUISH", "GROUND", "REPAIR", "SELECT"}


def load_profile(path: Path | str = DEFAULT_PROFILE) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_profile(profile: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    operators = profile.get("operators", [])
    ids = [row.get("id") for row in operators]
    if len(ids) != len(set(ids)):
        errors.append("duplicate operator id")
    if profile.get("authority_model") != "PROJECTION_DOES_NOT_MUTATE_SOURCE_BASELINE":
        errors.append("authority model mismatch")
    source = profile.get("source_contract", {})
    if source.get("lifecycle") != "COMPLETE_BOUNDED_V0_1":
        errors.append("source lifecycle is not complete bounded v0.1")
    for row in operators:
        if row.get("execution") == "DELEGATE_CANONICAL":
            if row.get("delegate_to") not in CANONICAL_DELEGATES:
                errors.append(f"invalid canonical delegate: {row.get('id')}")
        elif row.get("execution") != "GSFL_NATIVE":
            errors.append(f"unknown execution mode: {row.get('id')}")
        for field in ("semantic_effect", "evidence_effect", "authority_effect", "output"):
            if not row.get(field):
                errors.append(f"missing {field}: {row.get('id')}")
    return {"valid": not errors, "errors": errors, "operator_count": len(operators)}


def _spec(operator_id: str, profile: dict[str, Any]) -> dict[str, Any]:
    for row in profile["operators"]:
        if row["id"] == operator_id:
            return row
    raise KeyError(f"unknown GSFL operator: {operator_id}")


def _trace(out: dict[str, Any], spec: dict[str, Any], **extra: Any) -> None:
    out.setdefault("trace", []).append({
        "operator": spec["id"],
        "output": spec["output"],
        "semantic_effect": spec["semantic_effect"],
        "evidence_effect": spec["evidence_effect"],
        "authority_effect": spec["authority_effect"],
        **extra,
    })


def apply_operator(operator_id: str, envelope: dict[str, Any], *, profile_path: Path | str = DEFAULT_PROFILE, **params: Any) -> dict[str, Any]:
    profile = load_profile(profile_path)
    report = validate_profile(profile)
    if not report["valid"]:
        raise ValueError("invalid GSFL operator profile: " + "; ".join(report["errors"]))
    spec = _spec(operator_id, profile)
    out = deepcopy(envelope)
    payload = out.setdefault("payload", {})
    out.setdefault("trace", [])

    if spec["execution"] == "DELEGATE_CANONICAL":
        payload.setdefault("handoffs", []).append({
            "operator": operator_id,
            "delegate_to": spec["delegate_to"],
            "authority": "canonical Decision Field operator",
        })
        _trace(out, spec, delegated_to=spec["delegate_to"])
        return out

    if operator_id == "OBSERVE":
        payload.setdefault("observations", []).append(str(params["observation"]))
    elif operator_id == "MAP":
        payload.setdefault("mappings", []).append({"from": params.get("source"), "to": params.get("target")})
    elif operator_id == "RELATE":
        payload.setdefault("relations", []).append({"left": params.get("left"), "relation": params.get("relation"), "right": params.get("right")})
    elif operator_id == "COMPARE":
        left, right = params.get("left"), params.get("right")
        payload["comparison"] = {"equal": left == right, "left": left, "right": right}
    elif operator_id == "ROTATE":
        if "source_meaning" not in payload:
            raise ValueError("ROTATE requires payload.source_meaning")
        payload["surface"] = str(params["surface"])
    elif operator_id == "PRESERVE":
        source = payload.get("source_meaning", {})
        candidate = payload.get("candidate_meaning", source)
        keys = list(params.get("keys", source.keys()))
        failed = [k for k in keys if source.get(k) != candidate.get(k)]
        payload["preservation"] = {"keys": keys, "passed": not failed, "failed": failed}
    elif operator_id == "COMPOSE":
        payload["composition"] = list(params.get("parts", []))
    elif operator_id == "SPLIT":
        sequence = list(params.get("sequence", []))
        index = int(params.get("index", len(sequence) // 2))
        payload["split"] = [sequence[:index], sequence[index:]]
    elif operator_id == "MERGE":
        groups = list(params.get("groups", []))
        payload["merged"] = [item for group in groups for item in group]
    elif operator_id == "COOPERATE":
        payload.setdefault("cooperation_steps", []).append({"partner_id": params["partner_id"], "action": params["action"], "detail": params.get("detail", "")})
    elif operator_id == "HANDOFF":
        payload.setdefault("handoffs", []).append({"to": params["to"], "reason": params.get("reason", "")})
    elif operator_id == "TRACE_TOOL":
        payload.setdefault("tools", []).append({"tool_id": params["tool_id"], "purpose": params["purpose"], "provenance": params["provenance"]})
    elif operator_id == "TEACH_BACK":
        payload["understanding_evidence"] = {"kind": "TEACH_BACK", "detail": params["detail"]}
    elif operator_id == "VERIFY":
        checks = dict(params.get("checks", {}))
        payload["verification"] = {"checks": checks, "passed": bool(checks) and all(bool(v) for v in checks.values())}
    elif operator_id == "RECONSTRUCT":
        payload["reconstruction"] = deepcopy(params["meaning"])
    elif operator_id == "FIT":
        admitted = [row for row in payload.get("candidates", []) if row.get("admitted")]
        if not admitted:
            raise ValueError("FIT requires at least one admitted candidate")
        payload["fit_selection"] = deepcopy(sorted(admitted, key=lambda row: (-float(row.get("score", 0.0)), str(row.get("id", ""))))[0])
    elif operator_id == "GENERATE_PROVERB_FIXTURE":
        payload["proverb_fixture"] = {
            "source_text": str(params["source_text"]),
            "source_status": "SYNTHETIC",
            "context": str(params.get("context", "")),
            "claims_single_true_meaning": False,
            "provenance": "GSFL operator projection synthetic fixture",
        }
    elif operator_id == "AUDIT_CONFOUNDS":
        claims = payload.get("claims", {})
        findings: list[dict[str, str]] = []
        if claims.get("fit_is_truth"):
            findings.append({"id": "FIT_SCORE_AS_TRUTH", "control": "fit remains downstream of admission and external truth evidence"})
        if claims.get("output_proves_learning"):
            findings.append({"id": "OUTPUT_AS_LEARNING_EVIDENCE", "control": "output behavior does not prove persistent learning"})
        payload["confounds"] = findings
    elif operator_id == "DERIVE_COROLLARIES":
        corollaries: list[dict[str, str]] = []
        if payload.get("tools"):
            corollaries.append({"id": "TOOL_PROVENANCE_SEPARABLE", "statement": "Tool provenance can remain separate from authority."})
        if payload.get("cooperation_steps"):
            corollaries.append({"id": "ATTRIBUTION_RECONSTRUCTIBLE", "statement": "Attributed cooperation steps support bounded trace reconstruction."})
        payload["corollaries"] = corollaries
    else:
        raise KeyError(f"native implementation missing for operator: {operator_id}")

    _trace(out, spec)
    return out


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2, separators=(",", ": ")) + "\n"
