"""Parser and immutable IR for the bounded RMAPL v0 profile.

RMAPL v0 is intentionally small and declarative.  It is not RMALC syntax and
this module makes no claim that RMALC accepts RMAPL programs.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from types import MappingProxyType
from typing import Any, Mapping

RMAPL_VERSION = "RMAPL 0"
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.:-]*$")


@dataclass(frozen=True)
class RepairSpec:
    repair_id: str
    trigger: str
    requires: tuple[str, ...]
    targets: tuple[str, ...]
    preserves: tuple[str, ...]
    may_mutate: tuple[str, ...]
    forbids: tuple[str, ...]
    operator: str
    evidence: tuple[str, ...]
    cost: float


@dataclass(frozen=True)
class FitterSpec:
    fitter_id: str
    trigger: str
    requires: tuple[str, ...]
    preserves: tuple[str, ...]
    objectives: Mapping[str, str]
    operator: str
    evidence: tuple[str, ...]
    cost: float


@dataclass(frozen=True)
class Program:
    version: str
    program_id: str
    load_ref: str
    bounds: Mapping[str, Any]
    repairs: tuple[RepairSpec, ...]
    fitters: tuple[FitterSpec, ...]


def _identifier(value: str, label: str) -> str:
    if not _IDENT_RE.fullmatch(value):
        raise ValueError(f"invalid {label} identifier: {value!r}")
    return value


def _strict_json(text: str, label: str) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"{label} must be finite JSON, got {value}")

    try:
        return json.loads(text, parse_constant=reject_constant)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"{label} must be valid JSON: {exc}") from exc


def _json_string(text: str, label: str) -> str:
    value = _strict_json(text, label)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty JSON string")
    return value


def _string_array(text: str, label: str) -> tuple[str, ...]:
    value = _strict_json(text, label)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{label} must be a JSON array of non-empty strings")
    return tuple(value)


def _cost(text: str) -> float:
    value = _strict_json(text, "COST")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("COST must be a non-negative finite JSON number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError("COST must be a non-negative finite JSON number")
    return number


def _clean_lines(program: str) -> list[str]:
    if not isinstance(program, str):
        raise TypeError("RMAPL program must be text")
    lines = []
    for raw in program.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def _after_prefix(line: str, prefix: str, label: str) -> str:
    if not line.startswith(prefix):
        raise ValueError(f"expected {label}, got {line!r}")
    value = line[len(prefix):].strip()
    if not value:
        raise ValueError(f"{label} requires a value")
    return value


def parse_rmapl(program: str) -> Program:
    lines = _clean_lines(program)
    if not lines or lines[0] != RMAPL_VERSION:
        raise ValueError(f"program must start with {RMAPL_VERSION!r}")
    if len(lines) < 4:
        raise ValueError("incomplete RMAPL program")

    program_id = _identifier(_after_prefix(lines[1], "PROGRAM ", "PROGRAM"), "PROGRAM")
    load_ref = _identifier(_after_prefix(lines[2], "LOAD ", "LOAD"), "LOAD")
    index = 3

    bounds: dict[str, Any] = {}
    while index < len(lines) and lines[index].startswith("BOUND "):
        assignment = _after_prefix(lines[index], "BOUND ", "BOUND")
        if "=" not in assignment:
            raise ValueError("BOUND requires identifier=JSON")
        key, raw = assignment.split("=", 1)
        key = _identifier(key.strip(), "BOUND")
        if key in bounds:
            raise ValueError(f"duplicate BOUND {key!r}")
        bounds[key] = _strict_json(raw.strip(), f"BOUND {key}")
        index += 1

    repairs: list[RepairSpec] = []
    fitters: list[FitterSpec] = []
    block_ids: set[str] = set()

    def next_line(expected_prefix: str, label: str) -> str:
        nonlocal index
        if index >= len(lines):
            raise ValueError(f"expected {label}, got end of program")
        value = _after_prefix(lines[index], expected_prefix, label)
        index += 1
        return value

    while index < len(lines):
        line = lines[index]
        if line == "RUN":
            if index != len(lines) - 1:
                raise ValueError("RUN must be terminal")
            return Program(
                version=RMAPL_VERSION,
                program_id=program_id,
                load_ref=load_ref,
                bounds=MappingProxyType(dict(bounds)),
                repairs=tuple(repairs),
                fitters=tuple(fitters),
            )

        if line.startswith("REPAIR "):
            repair_id = _identifier(_after_prefix(line, "REPAIR ", "REPAIR"), "REPAIR")
            if repair_id in block_ids:
                raise ValueError(f"duplicate block id {repair_id!r}")
            block_ids.add(repair_id)
            index += 1
            trigger = _json_string(next_line("WHEN ", "WHEN"), "WHEN")
            requires = _string_array(next_line("REQUIRES ", "REQUIRES"), "REQUIRES")
            targets = _string_array(next_line("TARGETS ", "TARGETS"), "TARGETS")
            preserves = _string_array(next_line("PRESERVES ", "PRESERVES"), "PRESERVES")
            may_mutate = _string_array(next_line("MAY_MUTATE ", "MAY_MUTATE"), "MAY_MUTATE")
            forbids = _string_array(next_line("FORBIDS ", "FORBIDS"), "FORBIDS")
            operator = _identifier(next_line("APPLY ", "APPLY"), "APPLY")
            evidence = _string_array(next_line("EVIDENCE ", "EVIDENCE"), "EVIDENCE")
            cost = _cost(next_line("COST ", "COST"))
            if index >= len(lines) or lines[index] != "END":
                got = "end of program" if index >= len(lines) else repr(lines[index])
                raise ValueError(f"expected END, got {got}")
            index += 1
            repairs.append(
                RepairSpec(
                    repair_id=repair_id,
                    trigger=trigger,
                    requires=requires,
                    targets=targets,
                    preserves=preserves,
                    may_mutate=may_mutate,
                    forbids=forbids,
                    operator=operator,
                    evidence=evidence,
                    cost=cost,
                )
            )
            continue

        if line.startswith("FITTER "):
            fitter_id = _identifier(_after_prefix(line, "FITTER ", "FITTER"), "FITTER")
            if fitter_id in block_ids:
                raise ValueError(f"duplicate block id {fitter_id!r}")
            block_ids.add(fitter_id)
            index += 1
            trigger = _json_string(next_line("WHEN ", "WHEN"), "WHEN")
            requires = _string_array(next_line("REQUIRES ", "REQUIRES"), "REQUIRES")
            preserves = _string_array(next_line("PRESERVES ", "PRESERVES"), "PRESERVES")
            objectives_raw = _strict_json(next_line("OBJECTIVES ", "OBJECTIVES"), "OBJECTIVES")
            if not isinstance(objectives_raw, dict) or any(
                not isinstance(key, str) or value not in {"max", "min"}
                for key, value in objectives_raw.items()
            ):
                raise ValueError("OBJECTIVES must be a JSON object mapping names to 'max' or 'min'")
            operator = _identifier(next_line("APPLY ", "APPLY"), "APPLY")
            evidence = _string_array(next_line("EVIDENCE ", "EVIDENCE"), "EVIDENCE")
            cost = _cost(next_line("COST ", "COST"))
            if index >= len(lines) or lines[index] != "END":
                got = "end of program" if index >= len(lines) else repr(lines[index])
                raise ValueError(f"expected END, got {got}")
            index += 1
            fitters.append(
                FitterSpec(
                    fitter_id=fitter_id,
                    trigger=trigger,
                    requires=requires,
                    preserves=preserves,
                    objectives=MappingProxyType(dict(sorted(objectives_raw.items()))),
                    operator=operator,
                    evidence=evidence,
                    cost=cost,
                )
            )
            continue

        raise ValueError(f"unknown top-level operation: {line!r}")

    raise ValueError("program must terminate with RUN")
