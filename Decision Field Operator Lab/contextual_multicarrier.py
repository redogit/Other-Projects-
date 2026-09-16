from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

CARRIERS = ("SYMBOLIC", "ANALYTICAL", "COMPUTATIONAL", "ANALOGICAL")
ACTIVE_THRESHOLD = 0.6

ROLE_CUES = {
    "gate": {
        "GATE": ("verify", "verification", "admission", "allow", "block", "result", "boundary"),
        "TRANSITION": ("into", "through", "transition", "space", "portal"),
        "CARRIER": ("carry", "carried", "carries"),
        "FILTER": ("filter", "constraint", "constrain"),
    },
    "wave": {
        "PROPAGATION": ("propagate", "propagates", "spread", "signal", "outward"),
        "CARRIER": ("carry", "carries", "carried", "message"),
        "ACTION": ("goodbye", "hand", "gesture"),
        "STATE_CHANGE": ("doubt", "emotion", "mood"),
    },
    "turn": {
        "DIRECTION": ("toward", "direction", "path", "navigate"),
        "TRANSFORM": ("transform", "change", "rotate", "branch"),
    },
}

CLAIM_CEILINGS = {
    "SYMBOLIC": "representation/compression only",
    "ANALYTICAL": "derivation/coherence only",
    "COMPUTATIONAL": "finite executable witness only",
    "ANALOGICAL": "discovery/test-design only",
}


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2, separators=(",", ": ")) + "\n"


def _normalized_context(context: dict[str, Any]) -> str:
    parts = [
        str(context.get("surface", "")),
        str(context.get("context", "")),
        str(context.get("obligation", "")),
        " ".join(map(str, context.get("relations", []))),
    ]
    return " ".join(parts).lower()


def resolve_roles(occurrence: str, context: dict[str, Any]) -> dict[str, Any]:
    scores: dict[str, float] = {}
    hints = context.get("role_hints", {})
    if isinstance(hints, list):
        hints = {str(role): 1.0 for role in hints}
    for role, score in dict(hints).items():
        scores[str(role)] = max(scores.get(str(role), 0.0), float(score))

    text = _normalized_context(context)
    for role, cues in ROLE_CUES.get(occurrence.lower(), {}).items():
        if any(cue in text for cue in cues):
            scores[role] = max(scores.get(role, 0.0), 0.7)

    ordered = sorted(((role, round(min(1.0, score), 6)) for role, score in scores.items()), key=lambda x: (-x[1], x[0]))
    active = [role for role, score in ordered if score >= ACTIVE_THRESHOLD]
    unresolved = [role for role, score in ordered if 0 < score < ACTIVE_THRESHOLD]
    return {
        "occurrence": occurrence,
        "surface": context.get("surface", ""),
        "context": context.get("context", ""),
        "interpreter": context.get("interpreter", "UNKNOWN"),
        "time_label": context.get("time_label", "UNKNOWN"),
        "obligation": context.get("obligation", ""),
        "relations": deepcopy(context.get("relations", [])),
        "candidate_roles": [{"role": role, "support": score} for role, score in ordered],
        "active_roles": active,
        "unresolved_roles": unresolved,
        "provenance": "deterministic contextual role fixture; support is not truth probability",
    }


def project_carriers(semantic_object: dict[str, Any], carrier_inputs: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    source_invariants = deepcopy(semantic_object.get("invariants", {}))
    records: dict[str, dict[str, Any]] = {}
    for carrier in CARRIERS:
        supplied = deepcopy(carrier_inputs.get(carrier, {}))
        record = {
            "carrier": carrier,
            "source_id": semantic_object.get("id"),
            "representation": supplied.get("representation"),
            "invariants": deepcopy(supplied.get("invariants", source_invariants)),
            "introduced_claims": list(supplied.get("introduced_claims", [])),
            "omitted_claims": list(supplied.get("omitted_claims", [])),
            "provenance": supplied.get("provenance", f"derived-from:{semantic_object.get('id', 'unknown')}"),
            "claim_ceiling": supplied.get("claim_ceiling", CLAIM_CEILINGS[carrier]),
            "authority_effect": "NONE",
            "source_claim_ceiling": semantic_object.get("claim_ceiling", ""),
        }
        if carrier == "COMPUTATIONAL":
            record["bound"] = supplied.get("bound", "UNDECLARED_BOUND")
        if carrier == "ANALOGICAL":
            record["evidence_transfer"] = False
        records[carrier] = record
    return records


def compare_carriers(source: dict[str, Any], carriers: dict[str, dict[str, Any]], independence_contract: dict[str, Any] | None = None) -> dict[str, Any]:
    source_inv = deepcopy(source.get("invariants", {}))
    deltas: dict[str, dict[str, Any]] = {}
    agreement_count = 0
    for carrier in CARRIERS:
        record = carriers[carrier]
        inv = record.get("invariants", {})
        losses = sorted(k for k, v in source_inv.items() if k not in inv or inv.get(k) != v)
        introductions = sorted(k for k in inv.keys() if k not in source_inv)
        if inv == source_inv:
            agreement_count += 1
        deltas[carrier] = {
            "losses": losses,
            "introductions": introductions,
            "declared_introduced_claims": sorted(map(str, record.get("introduced_claims", []))),
            "declared_omitted_claims": sorted(map(str, record.get("omitted_claims", []))),
        }

    shared = {
        key: value
        for key, value in source_inv.items()
        if all(carriers[c].get("invariants", {}).get(key, object()) == value for c in CARRIERS)
    }
    independence_state = "NOT_ESTABLISHED"
    if independence_contract and independence_contract.get("established") is True:
        independence_state = "ESTABLISHED_BY_EXPLICIT_CONTRACT"
    return {
        "shared_invariants": shared,
        "carrier_deltas": deltas,
        "agreement_count": agreement_count,
        "carrier_count": len(CARRIERS),
        "independence_state": independence_state,
        "agreement_is_truth": False,
        "agreement_is_independent_verification": False,
    }


def bbf_analogy_check(source_invariants: dict[str, Any], mapping: dict[str, str], reconstructed: dict[str, Any]) -> dict[str, Any]:
    losses = sorted(k for k, v in source_invariants.items() if k not in reconstructed or reconstructed.get(k) != v)
    introductions = sorted(k for k in reconstructed if k not in source_invariants)
    if losses and introductions:
        status = "UNRESOLVED"
    elif losses:
        status = "LOSS"
    elif introductions:
        status = "INTRODUCED"
    else:
        status = "PRESERVED"
    return {
        "status": status,
        "folded": {mapping.get(k, k): deepcopy(v) for k, v in source_invariants.items()},
        "mapping": deepcopy(mapping),
        "reconstructed": deepcopy(reconstructed),
        "losses": losses,
        "introductions": introductions,
        "evidence_transfer": False,
        "authority_effect": "NONE",
        "boundary": "ANALOGY != EVIDENCE_TRANSFER",
    }


CONFOUND_CONTROLS = {
    "STATIC_ROLE_FALLACY": "bind roles from occurrence context; do not assign permanent word types",
    "INTERPRETER_COLLAPSE": "retain interpreter-local bindings and compare without forced merge",
    "AGREEMENT_AS_TRUTH": "carrier agreement is descriptive and does not establish truth",
    "AGREEMENT_AS_INDEPENDENCE": "independence requires an explicit independence contract",
    "ANALOGY_AS_EVIDENCE_TRANSFER": "analogy may guide discovery/test design but transfers no evidence authority",
    "COMPUTATION_AS_GENERAL_PROOF": "finite witnesses retain declared bounds and claim ceilings",
    "ANALYSIS_AS_EMPIRICAL_VALIDATION": "derivation/coherence remains separate from observation",
    "SYMBOLIC_COMPRESSION_AS_TRUTH": "compact representation has no automatic authority effect",
    "FIT_BEFORE_ADMISSION": "fit/selection remains downstream of semantic admission",
}


def audit_multicarrier_confounds(state: dict[str, Any]) -> list[dict[str, str]]:
    checks = [
        ("static_role_claim", "STATIC_ROLE_FALLACY"),
        ("collapsed_interpreters", "INTERPRETER_COLLAPSE"),
        ("agreement_claims_truth", "AGREEMENT_AS_TRUTH"),
        ("agreement_claims_independence", "AGREEMENT_AS_INDEPENDENCE"),
        ("analogy_evidence_transfer", "ANALOGY_AS_EVIDENCE_TRANSFER"),
        ("computation_claims_universal", "COMPUTATION_AS_GENERAL_PROOF"),
        ("analysis_claims_empirical", "ANALYSIS_AS_EMPIRICAL_VALIDATION"),
        ("symbol_claims_truth", "SYMBOLIC_COMPRESSION_AS_TRUTH"),
    ]
    findings = [
        {"id": cid, "control": CONFOUND_CONTROLS[cid]}
        for flag, cid in checks
        if state.get(flag)
    ]
    if state.get("fit_attempted") and not state.get("fit_candidate_admitted"):
        findings.append({"id": "FIT_BEFORE_ADMISSION", "control": CONFOUND_CONTROLS["FIT_BEFORE_ADMISSION"]})
    return findings


def gate_disposition(candidate: dict[str, Any], comparison: dict[str, Any], confounds: list[dict[str, Any]]) -> dict[str, Any]:
    reasons: list[str] = []
    if not candidate.get("source_invariants_preserved"):
        return {"disposition": "REJECT", "reasons": ["source invariants not preserved"]}

    delta_exists = any(
        row.get("losses") or row.get("introductions") or row.get("declared_omitted_claims")
        for row in comparison.get("carrier_deltas", {}).values()
    )
    if delta_exists:
        reasons.append("cross-carrier invariant delta remains unresolved")
    if confounds:
        reasons.append("blocking confounds remain: " + ",".join(sorted(row.get("id", "UNKNOWN") for row in confounds)))
    if not candidate.get("admitted"):
        reasons.append("semantic admission is required before promotion")
    if not candidate.get("verification_passed"):
        reasons.append("bounded verification has not passed")
    if not candidate.get("claim_ceiling"):
        reasons.append("claim ceiling is missing")

    if reasons:
        return {"disposition": "REOPEN", "reasons": reasons}
    return {
        "disposition": "PROMOTE_SUCCESSOR",
        "reasons": ["admitted, bounded verification passed, invariants preserved, no blocking confounds"],
        "claim_ceiling": candidate["claim_ceiling"],
        "independence_state": comparison.get("independence_state", "NOT_ESTABLISHED"),
    }
