#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import platform
import sys

from adapters import source_hashes
from catalog import PartCatalog
from core import CostVector, EmergentEffectCertificate, FailureKind, ObligationSpec, PartSpec, StepPhase, canonical_json
from experiment import (
    _hidden_transition,
    certify_effect,
    fused_commit_parts,
    hidden_mode_obligation,
    invalid_cheap_parts,
    open_loop_parts,
    reference_probe_parts,
    verify_hidden_mode,
)
from search import candidate_part_sets, pareto_frontier

ROOT = Path(__file__).resolve().parent
DECISION_FIELD = ROOT.parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(canonical_json(value), encoding="utf-8")


def _part(pid, provides, requires=()):
    return PartSpec(
        stable_id=pid, version=1, provides=tuple(provides), requires=tuple(requires),
        input_ports=(), output_ports=(), state_carried=(), assumptions=(), bounds=(),
        side_effects=(), external_dependencies=(), cost=CostVector.from_mapping({"component_count": 1}),
        evidence_refs=(), known_failures=(), replaceability_boundary="audit toy",
    )


def _small_search_oracle() -> int:
    obligation = ObligationSpec(
        stable_id="audit.cover", version=1, subject="audit toy", bounds=(("worlds", 1),),
        required_capabilities=("transition", "observe", "infer"), protected_invariants=(),
        success_condition="cover", allowed_initial=(0,), allowed_actions=(0,),
        observable_information=("o",), permissions=("observe",), temporal_semantics="one_step",
        step_timing=(StepPhase.PRE_ACTION, StepPhase.TRANSITION, StepPhase.OBSERVATION),
        exact_regime=True, evidence_threshold="exhaustive", unresolved_remainder=(),
        cost_dimensions=("component_count",),
    )
    parts = (
        _part("t", ("transition",)),
        _part("o", ("observe",)),
        _part("i", ("infer",), ("transition", "observe")),
        _part("f", ("transition", "observe")),
    )
    catalog = PartCatalog()
    for p in parts:
        catalog.register(p, lambda: None)
    got = {tuple(p.stable_id for p in subset) for subset in candidate_part_sets(obligation, catalog)}
    expected = set()
    ordered = tuple(sorted(parts, key=lambda p: p.stable_id))
    for size in range(1, len(ordered) + 1):
        for subset in itertools.combinations(ordered, size):
            provided = set().union(*(set(p.provides) for p in subset))
            if not set(obligation.required_capabilities) <= provided:
                continue
            if any(not set(p.requires) <= provided for p in subset):
                continue
            expected.add(tuple(p.stable_id for p in subset))
    if got != expected:
        raise AssertionError("capability-cover search disagrees with brute-force subset oracle")
    return len(got)


def _load_pass08_hidden(reference_root: Path):
    pdir = reference_root / "partial-observation"
    audit_path = pdir / "audit.py"
    if not audit_path.is_file():
        raise FileNotFoundError(audit_path)
    old = list(sys.path)
    try:
        sys.path.insert(0, str(pdir))
        spec = importlib.util.spec_from_file_location("bom_reference_pass08_audit", audit_path)
        if spec is None or spec.loader is None:
            raise ImportError(audit_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.hidden_system().transitions
    finally:
        sys.path[:] = old


def _reference_hashes(reference_root: Path) -> dict[str, str]:
    hashes = source_hashes(reference_root)
    hashes["pass08.audit"] = sha256(reference_root / "partial-observation" / "audit.py")
    return dict(sorted(hashes.items()))


def _scientific_record():
    obligation = hidden_mode_obligation()
    candidates = (
        reference_probe_parts(obligation),
        fused_commit_parts(obligation),
        open_loop_parts(obligation),
        invalid_cheap_parts(obligation),
    )
    results = {candidate.stable_id: verify_hidden_mode(candidate) for candidate in candidates}
    valid_specs = []
    invalid = []
    effects: list[EmergentEffectCertificate] = []
    for candidate in candidates:
        result = results[candidate.stable_id]
        if result.passed:
            valid_specs.append(replace(candidate.spec, verification=result))
        else:
            invalid.append({
                "assembly_id": candidate.stable_id,
                "failure_kind": result.failure_kind.value,
                "detail": result.detail,
            })
    effects.append(certify_effect(results["pass08.fused_commit"], "DISTINGUISHES(hidden_mode_A,hidden_mode_B)", "pass08.fused_commit"))

    frontier = pareto_frontier(tuple(valid_specs))
    direct = tuple(
        assembly for assembly in sorted(valid_specs, key=lambda a: (a.cost.items, a.stable_id))
        if not any(other is not assembly and other.cost.dominates(assembly.cost) for other in valid_specs)
    )
    if tuple(a.stable_id for a in frontier) != tuple(a.stable_id for a in direct):
        raise AssertionError("Pareto implementation disagrees with direct dominance oracle")
    if [a.stable_id for a in frontier] != ["openloop.312", "pass08.fused_commit"]:
        raise AssertionError("hidden-mode Pareto frontier changed")
    if not results["synthetic.probe_baseline"].passed:
        raise AssertionError("synthetic probe regression no longer satisfies obligation")
    if results["invalid.always_zero"].failure_kind != FailureKind.UNSATISFIED:
        raise AssertionError("invalid cheap candidate failure classification changed")

    summary = {
        "status": "PASS_BOUNDED",
        "obligation_id": obligation.stable_id,
        "obligation_version": obligation.version,
        "candidate_count": len(candidates),
        "verified_count": len(valid_specs),
        "invalid_rejected_count": len(invalid),
        "emergent_effect_certificates": [effect.stable_id for effect in effects],
        "reference_assembly": "pass08.fused_commit",
        "synthetic_baseline": "synthetic.probe_baseline",
        "additional_candidate": "openloop.312",
        "pareto_frontier_ids": [a.stable_id for a in frontier],
        "small_cover_oracle_candidates": _small_search_oracle(),
        "claim_ceiling": "obligation-relative finite BOM substitution only",
    }
    frontier_doc = []
    effect_by_assembly = {}
    for effect in effects:
        effect_by_assembly.setdefault(effect.assembly_id, []).append(effect.stable_id)
    for assembly in frontier:
        frontier_doc.append({
            "assembly_id": assembly.stable_id,
            "parts": [{"id": pid, "version": version} for pid, version in assembly.parts],
            "cost": assembly.cost.as_dict(),
            "verification": {
                "passed": assembly.verification.passed,
                "metrics": dict(assembly.verification.metrics),
                "evidence_refs": list(assembly.verification.evidence_refs),
            },
            "emergent_effects": sorted(effect_by_assembly.get(assembly.stable_id, ())),
        })
    return summary, frontier_doc, invalid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--skip-reference-check", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    reference_before = None
    reference_semantics_match = None
    if not args.skip_reference_check:
        reference_before = _reference_hashes(DECISION_FIELD)
        expected = tuple(tuple(_hidden_transition(world, action) for world in range(8)) for action in range(4))
        actual = tuple(tuple(row) for row in _load_pass08_hidden(DECISION_FIELD))
        if actual != expected:
            raise AssertionError("BOM hidden-mode fixture drifted from Pass 08 hidden_system")
        reference_semantics_match = True

    summary, frontier_doc, invalid = _scientific_record()
    write_json(args.out / "SUMMARY.json", summary)
    write_json(args.out / "FRONTIER.json", frontier_doc)

    source_files = ("core.py", "catalog.py", "adapters.py", "search.py", "experiment.py", "audit.py")
    verification = {
        "status": "PASS_DEV" if args.skip_reference_check else "PASS",
        "python": platform.python_version(),
        "source_sha256": {name: sha256(ROOT / name) for name in source_files},
        "reference_sources_verified": not args.skip_reference_check,
        "reference_semantics_match": reference_semantics_match,
        "reference_sha256_before": reference_before or {},
        "invalid_candidates": invalid,
        "deterministic_ordering": True,
        "scope": summary["claim_ceiling"],
    }
    if not args.skip_reference_check:
        after = _reference_hashes(DECISION_FIELD)
        if after != reference_before:
            raise AssertionError("reference Pass 06-08 source mutated during BOM audit")
        verification["reference_sha256_after"] = after
    write_json(args.out / "VERIFICATION.json", verification)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
