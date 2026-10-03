"""Fail-closed lowering for the independent-browser HTTP planner family.

This is intentionally not a generic RMAPL compiler. It consumes the immutable
RMAPL parser IR, accepts only the currently admitted scalar/string/control-flow
family used by browser_http_plan, and emits canonical RMAL 3.1 source.

Any unsupported opcode, missing path, changed branch label, changed write
surface, or changed request-construction chain is rejected instead of guessed.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from rmapl import OperatorSpec, parse_rmapl


ALLOWED_OPCODES = {
    "CLONE",
    "GET",
    "EQ",
    "JUMP_IF_FALSE",
    "CONST",
    "JUMP",
    "LABEL",
    "CONCAT",
    "BYTES_UTF8",
    "SET",
    "OMEGA_REBUILD",
    "RETURN",
}

INPUT_PATHS = {
    "scheme": "construction.state.navigation.pendingUrl.scheme",
    "host": "construction.state.navigation.pendingUrl.authority",
    "path": "construction.state.navigation.pendingUrl.path",
}

OUTPUT_PATHS = {
    "host": "construction.state.network.request.host",
    "port": "construction.state.network.request.port",
    "request_bytes": "construction.state.network.request.bytes",
    "max_bytes": "construction.state.network.request.maxResponseBytes",
    "residual": "construction.residuals",
}


@dataclass(frozen=True)
class Instruction:
    opcode: str
    args: tuple[Any, ...]


@dataclass(frozen=True)
class LoweredPlan:
    http_port: int
    http_transport_kind: str
    http_transport_detail: str
    http_consequence: str
    https_port: int
    https_transport_kind: str
    https_transport_detail: str
    https_consequence: str
    prefix: str
    protocol: str
    headers: str
    max_response_bytes: int
    unsupported_kind: str
    unsupported_detail: str
    unsupported_consequence: str


def parse_instruction(line: str) -> Instruction:
    opcode, sep, payload = line.partition(" ")
    if opcode not in ALLOWED_OPCODES:
        raise ValueError(f"unsupported lowering opcode {opcode!r}")
    if not sep:
        raise ValueError(f"instruction {opcode!r} is missing JSON arguments")
    args = json.loads(payload)
    if not isinstance(args, list):
        raise ValueError(f"instruction {opcode!r} arguments must be a JSON array")
    return Instruction(opcode, tuple(args))


def find_operator(source: str, operator_id: str) -> OperatorSpec:
    program = parse_rmapl(source)
    matches = [op for op in program.operators if op.operator_id == operator_id]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one operator {operator_id!r}, got {len(matches)}")
    return matches[0]


def label_positions(instructions: tuple[Instruction, ...]) -> dict[str, int]:
    labels: dict[str, int] = {}
    for index, instruction in enumerate(instructions):
        if instruction.opcode != "LABEL":
            continue
        if len(instruction.args) != 1 or not isinstance(instruction.args[0], str):
            raise ValueError("LABEL must contain exactly one string")
        label = instruction.args[0]
        if label in labels:
            raise ValueError(f"duplicate label {label!r}")
        labels[label] = index
    return labels


def const_assignments(items: tuple[Instruction, ...]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for instruction in items:
        if instruction.opcode != "CONST":
            continue
        if len(instruction.args) != 2 or not isinstance(instruction.args[0], str):
            raise ValueError("CONST lowering requires [name,value]")
        result[instruction.args[0]] = instruction.args[1]
    return result


def require_get(
    instructions: tuple[Instruction, ...],
    destination: str,
    expected_path: str,
) -> None:
    hits = [
        ins
        for ins in instructions
        if ins.opcode == "GET"
        and len(ins.args) == 3
        and ins.args[0] == destination
        and ins.args[2] == expected_path
    ]
    if len(hits) != 1:
        raise ValueError(
            f"expected one GET for {destination!r} from {expected_path!r}, got {len(hits)}"
        )


def require_set(
    instructions: tuple[Instruction, ...],
    path: str,
    source: str,
) -> None:
    hits = [
        ins
        for ins in instructions
        if ins.opcode == "SET"
        and len(ins.args) == 3
        and ins.args[0] == "$candidate"
        and ins.args[1] == path
        and ins.args[2] == source
    ]
    if len(hits) != 1:
        raise ValueError(f"expected one candidate SET {path!r} <- {source!r}")


def require_exact_request_chain(instructions: tuple[Instruction, ...]) -> None:
    wanted = (
        Instruction("CONCAT", ("request", "$prefix", "$path")),
        Instruction("CONCAT", ("request", "$request", "$protocol")),
        Instruction("CONCAT", ("request", "$request", "$host")),
        Instruction("CONCAT", ("request", "$request", "$headers")),
        Instruction("BYTES_UTF8", ("request_bytes", "$request")),
    )
    cursor = 0
    for instruction in instructions:
        if cursor < len(wanted) and instruction == wanted[cursor]:
            cursor += 1
    if cursor != len(wanted):
        raise ValueError("request-construction chain changed outside lowering contract")


def scalar(value: Any, label: str, expected_type: type) -> Any:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be {expected_type.__name__}")
    return value


def lower_operator(operator: OperatorSpec) -> LoweredPlan:
    instructions = tuple(parse_instruction(line) for line in operator.instructions)
    if not instructions or instructions[0] != Instruction("CLONE", ("candidate", "$omega")):
        raise ValueError("lowering family requires CLONE candidate from $omega")

    labels = label_positions(instructions)
    required_labels = {"check_https", "build_request", "unsupported"}
    if set(labels) != required_labels:
        raise ValueError(
            f"planner labels changed: expected {sorted(required_labels)}, got {sorted(labels)}"
        )

    check_https = labels["check_https"]
    build_request = labels["build_request"]
    unsupported = labels["unsupported"]
    if not (0 < check_https < build_request < unsupported):
        raise ValueError("planner label order changed")

    require_get(instructions, "scheme", INPUT_PATHS["scheme"])
    require_get(instructions, "host", INPUT_PATHS["host"])
    require_get(instructions, "path", INPUT_PATHS["path"])

    http_consts = const_assignments(instructions[:check_https])
    https_consts = const_assignments(instructions[check_https:build_request])
    request_consts = const_assignments(instructions[build_request:unsupported])
    unsupported_consts = const_assignments(instructions[unsupported:])

    require_exact_request_chain(instructions)

    require_set(instructions, OUTPUT_PATHS["host"], "$host")
    require_set(instructions, OUTPUT_PATHS["port"], "$port")
    require_set(instructions, OUTPUT_PATHS["request_bytes"], "$request_bytes")
    require_set(instructions, OUTPUT_PATHS["max_bytes"], "$max_bytes")
    require_set(instructions, OUTPUT_PATHS["residual"], "$transport_residual")

    transport_template = request_consts.get("transport_residual")
    if transport_template != [{"kind": "", "detail": ""}]:
        raise ValueError("transport residual template changed")
    if Instruction("SET", ("$transport_residual", "0.kind", "$transport_kind")) not in instructions:
        raise ValueError("transport residual kind write changed")
    if Instruction("SET", ("$transport_residual", "0.detail", "$transport_detail")) not in instructions:
        raise ValueError("transport residual detail write changed")

    unsupported_residual = unsupported_consts.get("unsupported_residual")
    if (
        not isinstance(unsupported_residual, list)
        or len(unsupported_residual) != 1
        or not isinstance(unsupported_residual[0], dict)
        or set(unsupported_residual[0]) != {"kind", "detail"}
    ):
        raise ValueError("unsupported residual shape changed")

    returns = [ins for ins in instructions if ins.opcode == "RETURN"]
    if len(returns) != 2:
        raise ValueError(f"expected two RETURN instructions, got {len(returns)}")
    if returns[0] != Instruction("RETURN", ("$candidate", "$consequence")):
        raise ValueError("supported RETURN shape changed")
    unsupported_consequence = returns[1].args[1]
    if not isinstance(unsupported_consequence, str) or unsupported_consequence.startswith("$"):
        raise ValueError("unsupported RETURN consequence must be a literal string")

    # These branch edges are part of the admitted lowering family.
    required_edges = {
        Instruction("JUMP_IF_FALSE", ("$is_http", "check_https")),
        Instruction("JUMP", ("build_request",)),
        Instruction("JUMP_IF_FALSE", ("$is_https", "unsupported")),
    }
    missing = required_edges.difference(instructions)
    if missing:
        raise ValueError(f"planner branch edges changed: missing {sorted(map(str, missing))}")

    return LoweredPlan(
        http_port=scalar(http_consts.get("port"), "http port", int),
        http_transport_kind=scalar(
            http_consts.get("transport_kind"), "http transport kind", str
        ),
        http_transport_detail=scalar(
            http_consts.get("transport_detail"), "http transport detail", str
        ),
        http_consequence=scalar(
            http_consts.get("consequence"), "http consequence", str
        ),
        https_port=scalar(https_consts.get("port"), "https port", int),
        https_transport_kind=scalar(
            https_consts.get("transport_kind"), "https transport kind", str
        ),
        https_transport_detail=scalar(
            https_consts.get("transport_detail"), "https transport detail", str
        ),
        https_consequence=scalar(
            https_consts.get("consequence"), "https consequence", str
        ),
        prefix=scalar(request_consts.get("prefix"), "request prefix", str),
        protocol=scalar(request_consts.get("protocol"), "request protocol", str),
        headers=scalar(request_consts.get("headers"), "request headers", str),
        max_response_bytes=scalar(
            request_consts.get("max_bytes"), "max response bytes", int
        ),
        unsupported_kind=scalar(
            unsupported_residual[0]["kind"], "unsupported residual kind", str
        ),
        unsupported_detail=scalar(
            unsupported_residual[0]["detail"], "unsupported residual detail", str
        ),
        unsupported_consequence=unsupported_consequence,
    )


def q(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render(plan: LoweredPlan, profile: dict[str, Any]) -> str:
    module = profile["module"]
    callback = profile["callback"]
    fixtures = profile["fixtures"]
    unsupported = profile["unsupported_fixture"]
    if not isinstance(module, str) or not isinstance(callback, str):
        raise ValueError("profile module/callback must be strings")
    if not isinstance(fixtures, list) or len(fixtures) < 1:
        raise ValueError("profile requires at least one fixture")

    request_expression = (
        q(plan.prefix)
        + " + path + "
        + q(plan.protocol)
        + " + host + "
        + q(plan.headers)
    )

    lines = [
        "# GENERATED FILE — DO NOT EDIT BY HAND",
        "# Lowered from examples/independent_browser_http.rmapl::browser_http_plan",
        "# Lowering family: rmapl-rmal-http-plan-lowering/v1",
        "",
        f"MODULE {module};",
        "",
        'CONTEXT RMAPL_HTTP_PLAN_PORT status="GENERATED" authority="LOCAL" evidence_transfer="DENY"',
        'BOUNDARY RMAPL_HTTP_PLAN_PORT CLAIM_CEILING BOUNDED_GENERATED_PORT REASON "lowering family is fail-closed and differentially checked; arbitrary RMAPL lowering remains unresolved"',
        "",
        "fn emit_plan(scheme, host, path, port, transport_kind, transport_detail, consequence) {",
        f"    let request = {request_expression};",
        f"    let acknowledgement = {callback}(scheme, host, port, transport_kind, transport_detail, consequence, request, {plan.max_response_bytes});",
        '    REQUIRE acknowledgement == consequence + ":ACK";',
        "    return consequence;",
        "}",
        "",
        "fn plan_request(scheme, host, path) {",
        '    if scheme == "http" {',
        f"        return emit_plan(scheme, host, path, {plan.http_port}, {q(plan.http_transport_kind)}, {q(plan.http_transport_detail)}, {q(plan.http_consequence)});",
        "    } else {",
        '        if scheme == "https" {',
        f"            return emit_plan(scheme, host, path, {plan.https_port}, {q(plan.https_transport_kind)}, {q(plan.https_transport_detail)}, {q(plan.https_consequence)});",
        "        } else {",
        f"            return {q(plan.unsupported_consequence)};",
        "        }",
        "    }",
        "}",
        "",
    ]

    for fixture in fixtures:
        lines.append(
            "REQUIRE plan_request("
            + q(fixture["scheme"])
            + ", "
            + q(fixture["host"])
            + ", "
            + q(fixture["path"])
            + ") == "
            + q(fixture["consequence"])
            + ";"
        )
    lines.append(
        "REQUIRE plan_request("
        + q(unsupported["scheme"])
        + ", "
        + q(unsupported["host"])
        + ", "
        + q(unsupported["path"])
        + ") == "
        + q(unsupported["consequence"])
        + ";"
    )
    lines.extend(
        [
            "",
            'print "RMAL_HTTP_PLAN_PASS";',
            "STOP;",
            "",
        ]
    )
    return "\n".join(lines)


def load_profile(path: Path) -> dict[str, Any]:
    profile = json.loads(path.read_text(encoding="utf-8"))
    if profile.get("schema") != "rmapl-rmal-http-plan-lowering/v1":
        raise ValueError("unsupported lowering profile schema")
    return profile


def generated_text(profile_path: Path) -> tuple[Path, str]:
    profile = load_profile(profile_path)
    source_path = (profile_path.parent / profile["source"]).resolve()
    output_path = (profile_path.parent / profile["output"]).resolve()
    source = source_path.read_text(encoding="utf-8")
    operator = find_operator(source, profile["operator"])
    plan = lower_operator(operator)
    return output_path, render(plan, profile)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()

    profile_path = args.profile.resolve()
    output_path, expected = generated_text(profile_path)
    if args.write:
        output_path.write_text(expected, encoding="utf-8")
        print(f"WROTE {output_path}")
        return 0

    actual = output_path.read_text(encoding="utf-8")
    if actual != expected:
        print(
            "LOWERING DRIFT: committed RMAL does not match RMAPL source. "
            "Run --write and review the generated diff.",
            file=sys.stderr,
        )
        return 1
    print("RMAPL_RMAL_HTTP_PLAN_LOWERING_CHECK PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
