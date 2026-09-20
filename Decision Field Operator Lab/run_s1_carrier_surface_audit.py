from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from s1_carrier_surface import (
    CARRIER_TYPES,
    evaluate_round_trip,
    one_degree_repair,
    project_carrier_to_omega,
    project_to_carrier,
    reconstruct_carrier_from_omega,
    reconstruct_from_carrier,
    semantic_residuals,
)

ROOT = Path(__file__).parent
FIXTURE = ROOT / "fixtures" / "s1_current_semantic_object.json"
EVIDENCE = ROOT / "evidence" / "S1_CARRIER_SURFACE_RESULTS.json"
MODULE = ROOT / "s1_carrier_surface.py"


def git_blob_sha1(path: Path) -> str:
    raw = path.read_bytes()
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def build_result():
    native = load_fixture()
    round_trips = {}
    omega_round_trips = {}
    evidence_transfer_denied = True
    candidate_not_admission = True

    for carrier_type in CARRIER_TYPES:
        carrier = project_to_carrier(native, carrier_type)
        report = evaluate_round_trip(native, carrier)
        round_trips[carrier_type] = {
            "classification": report["classification"],
            "residualKinds": sorted({x["kind"] for x in report["residuals"]}),
        }

        omega = project_carrier_to_omega(carrier)
        rebuilt_carrier = reconstruct_carrier_from_omega(omega)
        rebuilt_native = reconstruct_from_carrier(rebuilt_carrier)
        omega_round_trips[carrier_type] = {
            "carrierEqual": rebuilt_carrier == carrier,
            "nativeEqual": rebuilt_native == native,
            "omegaEvidenceKind": omega["evidence"][0]["kind"],
        }
        evidence_transfer_denied = (
            evidence_transfer_denied
            and carrier["evidenceTransfer"] == "DENY"
            and omega["domainRemainder"]["evidenceTransfer"] == "DENY"
        )
        candidate_not_admission = (
            candidate_not_admission
            and carrier["claimCeiling"].count("S_PRIME_CANDIDATE != ADMITTED_SUCCESSOR") == 1
        )

    stripped = project_to_carrier(native, "candidate-state")
    stripped["reconstructionPayload"] = None
    stripped_report = evaluate_round_trip(native, stripped)

    tampered = project_to_carrier(native, "survivor")
    tampered["objectId"] = "s1:semantic:tampered"
    tampered_report = evaluate_round_trip(native, tampered)

    bad_schedule = copy.deepcopy(native)
    bad_schedule["schedule"]["tau_w"] = 20
    schedule_residuals = semantic_residuals(bad_schedule)
    repair = one_degree_repair(bad_schedule, ("schedule", "tau_w"), 4)

    protected_repair_rejected = False
    try:
        one_degree_repair(native, ("objectId",), "tampered")
    except ValueError:
        protected_repair_rejected = True

    checks = {
        "fourSurfaceRoundTrips": all(
            item["classification"] == "ROTATION" and item["residualKinds"] == []
            for item in round_trips.values()
        ),
        "omegaSecondTransport": all(
            item["carrierEqual"]
            and item["nativeEqual"]
            and item["omegaEvidenceKind"] == "structural-projection"
            for item in omega_round_trips.values()
        ),
        "strippedSidecarUnknown": stripped_report["classification"] == "UNKNOWN",
        "identityTamperDecay": tampered_report["classification"] == "SEMANTIC_DECAY",
        "scheduleResidualTyped": "schedule-order" in {x["kind"] for x in schedule_residuals},
        "oneDegreeRepair": (
            repair["status"] == "REPAIRED"
            and repair["changedSemanticPaths"] == ["schedule.tau_w"]
            and repair["residualAfter"] == []
            and repair["admitted"] is False
        ),
        "protectedRepairRejected": protected_repair_rejected,
        "evidenceTransferDenied": evidence_transfer_denied,
        "candidateNotAdmission": candidate_not_admission,
    }

    return {
        "schema": "s1-carrier-surface-audit/v1",
        "fixtureId": native["objectId"],
        "sourceGitBlobs": {
            "s1_carrier_surface.py": git_blob_sha1(MODULE),
            "s1_current_semantic_object.json": git_blob_sha1(FIXTURE),
        },
        "carrierTypes": list(CARRIER_TYPES),
        "roundTrips": round_trips,
        "omegaRoundTrips": omega_round_trips,
        "negativeControls": {
            "strippedSidecar": {
                "classification": stripped_report["classification"],
                "residualKinds": sorted({x["kind"] for x in stripped_report["residuals"]}),
            },
            "identityTamper": {
                "classification": tampered_report["classification"],
                "residualKinds": sorted({x["kind"] for x in tampered_report["residuals"]}),
            },
            "scheduleOrder": {
                "residualKinds": sorted({x["kind"] for x in schedule_residuals}),
            },
        },
        "repair": {
            "status": repair["status"],
            "changedSemanticPaths": repair["changedSemanticPaths"],
            "residualBeforeKinds": sorted({x["kind"] for x in repair["residualBefore"]}),
            "residualAfterKinds": sorted({x["kind"] for x in repair["residualAfter"]}),
            "admitted": repair["admitted"],
        },
        "checks": checks,
        "boundaries": [
            "OBJECT_IDENTITY_INVARIANT_COORDINATES_NEGOTIABLE",
            "CURRENT_WORKING_MODEL != OWNER-PINNED_IMPLEMENTATION",
            "S_PRIME_CANDIDATE != ADMITTED_SUCCESSOR",
            "METHOD_TRANSFER != EVIDENCE_TRANSFER",
            "ROTATION != MUTATION != SEMANTIC_DECAY",
            "PROJECTION_SUCCESS != RECONSTRUCTION_SUCCESS",
            "SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",
        ],
        "claimCeiling": "bounded software verification of the declared fixture and transport contracts only",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()
    result = build_result()

    if args.check:
        expected = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        if result != expected:
            raise SystemExit("S1 Carrier-Surface evidence drift")
        print(
            f"PASS S1 Carrier-Surface audit: {len(CARRIER_TYPES)} carriers; "
            "round-trip, Omega transport, negative controls, and one-degree repair reproduced"
        )
        return

    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
