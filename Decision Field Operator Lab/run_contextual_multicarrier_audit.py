from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import contextual_multicarrier as cm

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence/CONTEXTUAL_MULTICARRIER_RESULTS.json"


def fixture_source():
    return {
        "id": "semantic-object-1",
        "meaning": {"thesis": "same object, multiple views"},
        "invariants": {"meaning": "preserved", "provenance": "attached", "authority": "bounded"},
        "claim_ceiling": "bounded calibration only",
    }


def fixture_inputs():
    inv = {"meaning": "preserved", "provenance": "attached", "authority": "bounded"}
    return {
        "SYMBOLIC": {"representation": "M -> {S,A,C,G}", "invariants": dict(inv), "provenance": "fixture:symbolic"},
        "ANALYTICAL": {"representation": {"premises": ["one object", "four views"]}, "invariants": dict(inv), "provenance": "fixture:analytical"},
        "COMPUTATIONAL": {"representation": {"finite_check": True}, "invariants": dict(inv), "provenance": "fixture:computational", "bound": "finite fixture"},
        "ANALOGICAL": {"representation": {"source": "lens", "target": "carrier"}, "invariants": dict(inv), "provenance": "fixture:analogical"},
    }


def fresh_payload():
    gate_boundary = cm.resolve_roles("gate", {
        "surface": "conversation", "context": "gate this result until verification",
        "interpreter": "human", "time_label": "t1", "obligation": "admission control", "relations": []
    })
    gate_transition = cm.resolve_roles("gate", {
        "surface": "conversation", "context": "the gate carried us into another space",
        "interpreter": "human", "time_label": "t2", "obligation": "describe transition", "relations": []
    })
    wave = cm.resolve_roles("wave", {
        "surface": "conversation", "context": "the wave carries and propagates the message",
        "interpreter": "machine", "time_label": "t1", "obligation": "trace message movement", "relations": [],
        "role_hints": {"PROPAGATION": 1.0, "CARRIER": 0.9}
    })
    human_turn = cm.resolve_roles("turn", {
        "surface":"chat", "context":"turn toward the evidence", "interpreter":"human", "time_label":"t", "obligation":"navigate", "relations":[], "role_hints":{"DIRECTION":1.0}
    })
    machine_turn = cm.resolve_roles("turn", {
        "surface":"chat", "context":"turn transforms the branch", "interpreter":"machine", "time_label":"t", "obligation":"transform", "relations":[], "role_hints":{"TRANSFORM":1.0}
    })

    source = fixture_source()
    carriers = cm.project_carriers(source, fixture_inputs())
    comparison = cm.compare_carriers(source, carriers)

    mutated = cm.project_carriers(source, fixture_inputs())
    mutated["ANALYTICAL"]["invariants"].pop("provenance")
    mutated["COMPUTATIONAL"]["invariants"]["invented"] = True
    delta_comparison = cm.compare_carriers(source, mutated)

    analogy_ok = cm.bbf_analogy_check(
        {"distinction":"preserved", "authority":"local"},
        {"distinction":"target_distinction", "authority":"target_authority"},
        {"distinction":"preserved", "authority":"local"},
    )
    analogy_loss = cm.bbf_analogy_check({"a":1,"b":2}, {"a":"x","b":"y"}, {"a":1})
    analogy_intro = cm.bbf_analogy_check({"a":1}, {"a":"x"}, {"a":1,"c":3})

    findings = cm.audit_multicarrier_confounds({
        "static_role_claim": True,
        "collapsed_interpreters": True,
        "agreement_claims_truth": True,
        "agreement_claims_independence": True,
        "analogy_evidence_transfer": True,
        "computation_claims_universal": True,
        "analysis_claims_empirical": True,
        "symbol_claims_truth": True,
        "fit_attempted": True,
        "fit_candidate_admitted": False,
    })

    agreement_only = cm.gate_disposition(
        {"admitted":False, "verification_passed":False, "claim_ceiling":"bounded", "source_invariants_preserved":True},
        comparison, [],
    )
    promotable = cm.gate_disposition(
        {"admitted":True, "verification_passed":True, "claim_ceiling":"bounded fixture only", "source_invariants_preserved":True},
        comparison, [],
    )

    checks = {
        "same_word_changes_role_with_context": gate_boundary["active_roles"] != gate_transition["active_roles"],
        "multi_role_binding_supported": set(("PROPAGATION", "CARRIER")).issubset(wave["active_roles"]),
        "interpreters_remain_separate": human_turn["active_roles"] != machine_turn["active_roles"],
        "four_carriers_present": set(carriers) == set(cm.CARRIERS),
        "positive_fixture_preserves_invariants": comparison["agreement_count"] == 4,
        "agreement_not_independence": comparison["independence_state"] == "NOT_ESTABLISHED",
        "loss_detected": "provenance" in delta_comparison["carrier_deltas"]["ANALYTICAL"]["losses"],
        "introduction_detected": "invented" in delta_comparison["carrier_deltas"]["COMPUTATIONAL"]["introductions"],
        "analogy_preservation_detected": analogy_ok["status"] == "PRESERVED" and not analogy_ok["evidence_transfer"],
        "analogy_loss_detected": analogy_loss["status"] == "LOSS",
        "analogy_introduction_detected": analogy_intro["status"] == "INTRODUCED",
        "nine_confounds_detected": len({row["id"] for row in findings}) == 9,
        "agreement_only_reopened": agreement_only["disposition"] == "REOPEN",
        "verified_admitted_successor_promoted": promotable["disposition"] == "PROMOTE_SUCCESSOR",
    }
    body = {
        "artifact": "GSFL_CONTEXTUAL_MULTICARRIER_REASONING",
        "source_lifecycle": "COMPLETE_BOUNDED_V0_1",
        "carrier_count": len(cm.CARRIERS),
        "carriers": list(cm.CARRIERS),
        "role_examples": {
            "gate_boundary": gate_boundary["active_roles"],
            "gate_transition": gate_transition["active_roles"],
            "wave_multi_role": wave["active_roles"],
            "human_turn": human_turn["active_roles"],
            "machine_turn": machine_turn["active_roles"],
        },
        "agreement_count": comparison["agreement_count"],
        "independence_state": comparison["independence_state"],
        "confound_ids": sorted(row["id"] for row in findings),
        "gate_controls": {
            "agreement_only": agreement_only["disposition"],
            "verified_admitted": promotable["disposition"],
        },
        "checks": checks,
        "boundaries": [
            "WORD != FIXED_ROLE",
            "ROLE_BINDING != PERMANENT_DEFINITION",
            "MULTI_CARRIER != MULTIPLE_INDEPENDENT_WITNESSES",
            "ANALOGY != EMPIRICAL_EVIDENCE",
            "COMPUTATION != UNIVERSAL_PROOF",
            "ANALYSIS != OBSERVATION",
            "SYMBOL != SUBJECT",
            "COHERENCE != VALIDATION",
            "PROMOTION != SOURCE_REWRITE"
        ],
    }
    canonical = cm.canonical_json(body)
    body["execution_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    payload = fresh_payload()
    text = cm.canonical_json(payload)
    if args.check:
        expected = EVIDENCE.read_text(encoding="utf-8")
        if expected != text:
            print("contextual multicarrier evidence mismatch")
            return 1
        if not all(payload["checks"].values()):
            print("one or more contextual multicarrier checks failed")
            return 1
        print(f"contextual multicarrier audit passed: {sum(payload['checks'].values())}/{len(payload['checks'])} checks")
        print(payload["execution_sha256"])
        return 0
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
