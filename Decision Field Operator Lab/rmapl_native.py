"""Bounded native operator VM for the RMAPL 0 reference profile.

This module closes one specific seam in the original RMAPL 0 runtime: APPLY
targets may now be implemented by RMAPL OPERATOR bodies rather than requiring
a host-language callback registry.  The VM is deliberately pure: it has no
filesystem, network, subprocess, clock, random, or dynamic host-call opcode.

Native execution remains bounded by each operator's LIMIT and BUFFER_LIMIT.
The resulting proposal is still verified by rmapl_runtime; native execution
does not bypass GENERATE != VERIFY != ADMIT.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import json
import math
import re
from typing import Any, Callable

from omega import make_omega, validate_omega
from rmapl import OperatorSpec, Program

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.:-]*$")
_NUMERIC_OPS = {"ADD", "SUB", "MUL", "DIV", "MOD"}
_BITWISE_OPS = {"BIT_AND", "BIT_OR", "BIT_XOR", "SHL", "SHR"}
_COMPARE_OPS = {"EQ", "NE", "LT", "LE", "GT", "GE"}


class NativeOperatorError(ValueError):
    """Malformed or invalid native operator execution."""


class NativeResourceBound(NativeOperatorError):
    """A declared native operator resource bound was reached."""


def _strict_json(text: str, label: str) -> Any:
    def reject_constant(value: str) -> None:
        raise NativeOperatorError(f"{label} must be finite JSON, got {value}")

    def finite_float(value: str) -> float:
        number = float(value)
        if not math.isfinite(number):
            raise NativeOperatorError(f"{label} must be finite JSON, got {value}")
        return number

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise NativeOperatorError(f"{label} contains duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        return json.loads(
            text,
            parse_constant=reject_constant,
            parse_float=finite_float,
            object_pairs_hook=unique_object,
        )
    except (json.JSONDecodeError, TypeError) as exc:
        raise NativeOperatorError(f"{label} must be valid JSON: {exc}") from exc


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return deepcopy(value)


def _compile_instruction(line: str, index: int) -> tuple[str, list[Any]]:
    if not isinstance(line, str) or not line.strip():
        raise NativeOperatorError(f"instruction {index} must be non-empty text")
    opcode, separator, payload = line.strip().partition(" ")
    opcode = opcode.upper()
    if not _NAME_RE.fullmatch(opcode):
        raise NativeOperatorError(f"instruction {index} has invalid opcode {opcode!r}")
    if not separator:
        args: Any = []
    else:
        args = _strict_json(payload.strip(), f"instruction {index} {opcode}")
    if not isinstance(args, list):
        raise NativeOperatorError(f"instruction {index} {opcode} arguments must be a JSON array")
    return opcode, args


def _name(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _NAME_RE.fullmatch(value) or value.startswith("$"):
        raise NativeOperatorError(f"{label} must be an identifier")
    return value


def _ref_name(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.startswith("$"):
        raise NativeOperatorError(f"{label} must be a variable reference like '$candidate'")
    name = value[1:]
    if not _NAME_RE.fullmatch(name):
        raise NativeOperatorError(f"{label} has invalid variable name {name!r}")
    return name


def _value(value: Any, env: dict[str, Any]) -> Any:
    if isinstance(value, str) and value.startswith("$"):
        name = _ref_name(value, "value")
        if name not in env:
            raise NativeOperatorError(f"unknown variable {name!r}")
        return env[name]
    return value


def _target(value: Any, env: dict[str, Any]) -> tuple[str, Any]:
    name = _ref_name(value, "target")
    if name == "omega":
        raise NativeOperatorError("input variable '$omega' is read-only")
    if name not in env:
        raise NativeOperatorError(f"unknown target variable {name!r}")
    return name, env[name]


def _path_parts(path: Any) -> tuple[str, ...]:
    if not isinstance(path, str) or not path:
        raise NativeOperatorError("path must be a non-empty dotted string")
    parts = tuple(path.split("."))
    if any(not part for part in parts):
        raise NativeOperatorError(f"invalid path {path!r}")
    return parts


def _list_index(part: str, length: int, *, allow_end: bool = False) -> int:
    try:
        index = int(part, 10)
    except ValueError as exc:
        raise NativeOperatorError(f"list path component must be an integer, got {part!r}") from exc
    upper = length if allow_end else length - 1
    if index < 0 or index > upper:
        raise NativeOperatorError(f"list index {index} outside [0, {upper}]")
    return index


def _get_path(root: Any, path: Any) -> Any:
    current = root
    for part in _path_parts(path):
        if isinstance(current, Mapping):
            if part not in current:
                raise NativeOperatorError(f"path {path!r} is missing key {part!r}")
            current = current[part]
        elif isinstance(current, list):
            current = current[_list_index(part, len(current))]
        else:
            raise NativeOperatorError(f"path {path!r} crosses scalar at {part!r}")
    return current


def _parent_for_path(root: Any, path: Any) -> tuple[Any, str]:
    parts = _path_parts(path)
    current = root
    for part in parts[:-1]:
        if isinstance(current, dict):
            if part not in current:
                raise NativeOperatorError(f"path {path!r} is missing intermediate key {part!r}")
            current = current[part]
        elif isinstance(current, list):
            current = current[_list_index(part, len(current))]
        else:
            raise NativeOperatorError(f"path {path!r} crosses scalar at {part!r}")
    return current, parts[-1]


def _set_path(root: Any, path: Any, value: Any) -> None:
    parent, leaf = _parent_for_path(root, path)
    if isinstance(parent, dict):
        parent[leaf] = deepcopy(value)
    elif isinstance(parent, list):
        parent[_list_index(leaf, len(parent))] = deepcopy(value)
    else:
        raise NativeOperatorError(f"cannot SET path {path!r} on scalar parent")


def _delete_path(root: Any, path: Any) -> None:
    parent, leaf = _parent_for_path(root, path)
    if isinstance(parent, dict):
        if leaf not in parent:
            raise NativeOperatorError(f"cannot DELETE absent key {leaf!r}")
        del parent[leaf]
    elif isinstance(parent, list):
        del parent[_list_index(leaf, len(parent))]
    else:
        raise NativeOperatorError(f"cannot DELETE path {path!r} on scalar parent")


def _append_path(root: Any, path: Any, value: Any) -> None:
    target = _get_path(root, path)
    if not isinstance(target, list):
        raise NativeOperatorError(f"APPEND target {path!r} must be a list")
    target.append(deepcopy(value))


def _numeric(value: Any, label: str) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise NativeOperatorError(f"{label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise NativeOperatorError(f"{label} must be finite")
    return value


def _integral(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise NativeOperatorError(f"{label} must be an integer")
    return value


def _checked_number(value: Any, label: str) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise NativeOperatorError(f"{label} produced a non-numeric value")
    if not math.isfinite(float(value)):
        raise NativeOperatorError(f"{label} produced a non-finite value")
    return value


def _buffer_shape(value: Any, *, limit: int, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise NativeOperatorError(f"{label} must be a byte buffer list")
    if len(value) > limit:
        raise NativeResourceBound(f"{label} length {len(value)} exceeds BUFFER_LIMIT {limit}")
    return value


def _byte(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not (0 <= value <= 255):
        raise NativeOperatorError(f"{label} must be a byte, got {value!r}")
    return value


def _buffer(value: Any, *, limit: int, label: str) -> list[int]:
    data = _buffer_shape(value, limit=limit, label=label)
    for index, item in enumerate(data):
        _byte(item, f"{label}[{index}]")
    return data


def _compile(spec: OperatorSpec) -> tuple[tuple[str, list[Any]], ...]:
    compiled = tuple(
        _compile_instruction(line, index + 1)
        for index, line in enumerate(spec.instructions)
    )
    labels: set[str] = set()
    for opcode, args in compiled:
        if opcode == "LABEL":
            if len(args) != 1:
                raise NativeOperatorError("LABEL expects [name]")
            label = _name(args[0], "LABEL")
            if label in labels:
                raise NativeOperatorError(f"duplicate LABEL {label!r}")
            labels.add(label)
    for opcode, args in compiled:
        if opcode in {"JUMP", "JUMP_IF_FALSE"}:
            expected = 1 if opcode == "JUMP" else 2
            if len(args) != expected:
                raise NativeOperatorError(f"{opcode} expects {expected} argument(s)")
            label = _name(args[-1], opcode)
            if label not in labels:
                raise NativeOperatorError(f"{opcode} references unknown LABEL {label!r}")
    return compiled


def _native_callable(spec: OperatorSpec) -> Callable[[dict[str, Any]], dict[str, Any]]:
    compiled = _compile(spec)
    label_pc = {
        _name(args[0], "LABEL"): index
        for index, (opcode, args) in enumerate(compiled)
        if opcode == "LABEL"
    }

    def execute(omega: dict[str, Any]) -> dict[str, Any]:
        validate_omega(omega)
        env: dict[str, Any] = {"omega": omega}
        pc = 0
        steps = 0

        while pc < len(compiled):
            steps += 1
            if steps > spec.max_instructions:
                raise NativeResourceBound(
                    f"OPERATOR {spec.operator_id!r} exceeded LIMIT {spec.max_instructions}"
                )

            opcode, args = compiled[pc]
            next_pc = pc + 1

            if opcode == "LABEL":
                if len(args) != 1:
                    raise NativeOperatorError("LABEL expects [name]")

            elif opcode == "CONST":
                if len(args) != 2:
                    raise NativeOperatorError("CONST expects [name,value]")
                env[_name(args[0], "CONST name")] = deepcopy(args[1])

            elif opcode == "CLONE":
                if len(args) != 2:
                    raise NativeOperatorError("CLONE expects [name,source]")
                env[_name(args[0], "CLONE name")] = deepcopy(_value(args[1], env))

            elif opcode == "GET":
                if len(args) != 3:
                    raise NativeOperatorError("GET expects [name,source,path]")
                source = _value(args[1], env)
                env[_name(args[0], "GET name")] = deepcopy(_get_path(source, args[2]))

            elif opcode == "SET":
                if len(args) != 3:
                    raise NativeOperatorError("SET expects [target,path,value]")
                _, target = _target(args[0], env)
                _set_path(target, args[1], _value(args[2], env))

            elif opcode == "DELETE":
                if len(args) != 2:
                    raise NativeOperatorError("DELETE expects [target,path]")
                _, target = _target(args[0], env)
                _delete_path(target, args[1])

            elif opcode == "APPEND":
                if len(args) != 3:
                    raise NativeOperatorError("APPEND expects [target,path,value]")
                _, target = _target(args[0], env)
                _append_path(target, args[1], _value(args[2], env))

            elif opcode == "LEN":
                if len(args) != 2:
                    raise NativeOperatorError("LEN expects [name,source]")
                source = _value(args[1], env)
                if not isinstance(source, (str, list, tuple, dict)):
                    raise NativeOperatorError("LEN source must be text, list, tuple, or object")
                env[_name(args[0], "LEN name")] = len(source)

            elif opcode == "INDEX":
                if len(args) != 3:
                    raise NativeOperatorError("INDEX expects [name,source,index]")
                source = _value(args[1], env)
                index = _integral(_value(args[2], env), "INDEX index")
                if not isinstance(source, (str, list, tuple)):
                    raise NativeOperatorError("INDEX source must be text or a sequence")
                if index < 0 or index >= len(source):
                    raise NativeOperatorError(f"INDEX {index} outside sequence length {len(source)}")
                env[_name(args[0], "INDEX name")] = deepcopy(source[index])

            elif opcode == "MAP_GET":
                if len(args) != 3:
                    raise NativeOperatorError("MAP_GET expects [name,source,key]")
                source = _value(args[1], env)
                key = _value(args[2], env)
                if not isinstance(source, Mapping):
                    raise NativeOperatorError("MAP_GET source must be an object")
                if not isinstance(key, str):
                    raise NativeOperatorError("MAP_GET key must be text")
                if key not in source:
                    raise NativeOperatorError(f"MAP_GET missing key {key!r}")
                env[_name(args[0], "MAP_GET name")] = deepcopy(source[key])

            elif opcode == "STR_STARTS":
                if len(args) != 3:
                    raise NativeOperatorError("STR_STARTS expects [name,text,prefix]")
                text = _value(args[1], env)
                prefix = _value(args[2], env)
                if not isinstance(text, str) or not isinstance(prefix, str):
                    raise NativeOperatorError("STR_STARTS operands must be text")
                env[_name(args[0], "STR_STARTS name")] = text.startswith(prefix)

            elif opcode == "STR_FIND":
                if len(args) not in {3, 4}:
                    raise NativeOperatorError("STR_FIND expects [name,text,needle] or [name,text,needle,start]")
                text = _value(args[1], env)
                needle = _value(args[2], env)
                if not isinstance(text, str) or not isinstance(needle, str):
                    raise NativeOperatorError("STR_FIND operands must be text")
                start = 0 if len(args) == 3 else _integral(_value(args[3], env), "STR_FIND start")
                if start < 0 or start > len(text):
                    raise NativeOperatorError("STR_FIND start outside text bounds")
                env[_name(args[0], "STR_FIND name")] = text.find(needle, start)

            elif opcode == "SLICE":
                if len(args) not in {3, 4}:
                    raise NativeOperatorError("SLICE expects [name,source,start] or [name,source,start,end]")
                source = _value(args[1], env)
                start = _integral(_value(args[2], env), "SLICE start")
                end = len(source) if len(args) == 3 else _integral(_value(args[3], env), "SLICE end")
                if not isinstance(source, (str, list, tuple)):
                    raise NativeOperatorError("SLICE source must be text or a sequence")
                if start < 0 or end < start or end > len(source):
                    raise NativeOperatorError("SLICE bounds outside source")
                env[_name(args[0], "SLICE name")] = deepcopy(source[start:end])

            elif opcode == "BYTES_UTF8":
                if len(args) != 2:
                    raise NativeOperatorError("BYTES_UTF8 expects [name,text]")
                text = _value(args[1], env)
                if not isinstance(text, str):
                    raise NativeOperatorError("BYTES_UTF8 source must be text")
                data = list(text.encode("utf-8"))
                _buffer(data, limit=spec.max_buffer_bytes, label="BYTES_UTF8 output")
                env[_name(args[0], "BYTES_UTF8 name")] = data

            elif opcode == "TEXT_UTF8":
                if len(args) != 2:
                    raise NativeOperatorError("TEXT_UTF8 expects [name,buffer]")
                data = list(_value(args[1], env))
                _buffer(data, limit=spec.max_buffer_bytes, label="TEXT_UTF8 input")
                try:
                    env[_name(args[0], "TEXT_UTF8 name")] = bytes(data).decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise NativeOperatorError(f"TEXT_UTF8 input is not valid UTF-8: {exc}") from exc

            elif opcode == "BUF_NEW":
                if len(args) not in {2, 3}:
                    raise NativeOperatorError("BUF_NEW expects [name,size] or [name,size,fill]")
                size = _integral(_value(args[1], env), "BUF_NEW size")
                fill = 0 if len(args) == 2 else _integral(_value(args[2], env), "BUF_NEW fill")
                if size < 0 or size > spec.max_buffer_bytes:
                    raise NativeResourceBound(
                        f"BUF_NEW size {size} exceeds BUFFER_LIMIT {spec.max_buffer_bytes}"
                    )
                if not (0 <= fill <= 255):
                    raise NativeOperatorError("BUF_NEW fill must be a byte")
                env[_name(args[0], "BUF_NEW name")] = [fill] * size

            elif opcode == "BUF_GET":
                if len(args) != 3:
                    raise NativeOperatorError("BUF_GET expects [name,buffer,index]")
                data = _buffer_shape(
                    _value(args[1], env),
                    limit=spec.max_buffer_bytes,
                    label="BUF_GET buffer",
                )
                index = _integral(_value(args[2], env), "BUF_GET index")
                if index < 0 or index >= len(data):
                    raise NativeOperatorError(f"BUF_GET index {index} outside buffer length {len(data)}")
                env[_name(args[0], "BUF_GET name")] = _byte(
                    data[index],
                    f"BUF_GET buffer[{index}]",
                )

            elif opcode == "BUF_SET":
                if len(args) != 3:
                    raise NativeOperatorError("BUF_SET expects [buffer,index,value]")
                buffer_name, data = _target(args[0], env)
                data = _buffer_shape(data, limit=spec.max_buffer_bytes, label="BUF_SET buffer")
                index = _integral(_value(args[1], env), "BUF_SET index")
                value = _byte(_value(args[2], env), "BUF_SET value")
                if index < 0 or index >= len(data):
                    raise NativeOperatorError(f"BUF_SET index {index} outside buffer length {len(data)}")
                data[index] = value
                env[buffer_name] = data

            elif opcode in _NUMERIC_OPS:
                if len(args) != 3:
                    raise NativeOperatorError(f"{opcode} expects [name,left,right]")
                left = _numeric(_value(args[1], env), f"{opcode} left")
                right = _numeric(_value(args[2], env), f"{opcode} right")
                if opcode == "ADD":
                    result = left + right
                elif opcode == "SUB":
                    result = left - right
                elif opcode == "MUL":
                    result = left * right
                elif opcode == "DIV":
                    if right == 0:
                        raise NativeOperatorError("DIV by zero")
                    result = left / right
                else:
                    if right == 0:
                        raise NativeOperatorError("MOD by zero")
                    result = left % right
                env[_name(args[0], f"{opcode} name")] = _checked_number(result, opcode)

            elif opcode in _BITWISE_OPS:
                if len(args) != 3:
                    raise NativeOperatorError(f"{opcode} expects [name,left,right]")
                left = _integral(_value(args[1], env), f"{opcode} left")
                right = _integral(_value(args[2], env), f"{opcode} right")
                if opcode in {"SHL", "SHR"} and right < 0:
                    raise NativeOperatorError(f"{opcode} shift must be non-negative")
                if opcode == "BIT_AND":
                    result = left & right
                elif opcode == "BIT_OR":
                    result = left | right
                elif opcode == "BIT_XOR":
                    result = left ^ right
                elif opcode == "SHL":
                    result = left << right
                else:
                    result = left >> right
                env[_name(args[0], f"{opcode} name")] = result

            elif opcode in _COMPARE_OPS:
                if len(args) != 3:
                    raise NativeOperatorError(f"{opcode} expects [name,left,right]")
                left = _value(args[1], env)
                right = _value(args[2], env)
                if opcode == "EQ":
                    result = left == right
                elif opcode == "NE":
                    result = left != right
                elif opcode == "LT":
                    result = left < right
                elif opcode == "LE":
                    result = left <= right
                elif opcode == "GT":
                    result = left > right
                else:
                    result = left >= right
                env[_name(args[0], f"{opcode} name")] = bool(result)

            elif opcode == "NOT":
                if len(args) != 2:
                    raise NativeOperatorError("NOT expects [name,value]")
                env[_name(args[0], "NOT name")] = not bool(_value(args[1], env))

            elif opcode in {"AND", "OR"}:
                if len(args) != 3:
                    raise NativeOperatorError(f"{opcode} expects [name,left,right]")
                left = bool(_value(args[1], env))
                right = bool(_value(args[2], env))
                env[_name(args[0], f"{opcode} name")] = left and right if opcode == "AND" else left or right

            elif opcode == "CONCAT":
                if len(args) != 3:
                    raise NativeOperatorError("CONCAT expects [name,left,right]")
                left = _value(args[1], env)
                right = _value(args[2], env)
                if isinstance(left, str) and isinstance(right, str):
                    result = left + right
                elif isinstance(left, list) and isinstance(right, list):
                    result = deepcopy(left) + deepcopy(right)
                    if all(isinstance(item, int) and not isinstance(item, bool) for item in result):
                        _buffer(result, limit=spec.max_buffer_bytes, label="CONCAT byte buffer")
                else:
                    raise NativeOperatorError("CONCAT operands must both be text or both be lists")
                env[_name(args[0], "CONCAT name")] = result

            elif opcode == "JUMP":
                if len(args) != 1:
                    raise NativeOperatorError("JUMP expects [label]")
                next_pc = label_pc[_name(args[0], "JUMP")]

            elif opcode == "JUMP_IF_FALSE":
                if len(args) != 2:
                    raise NativeOperatorError("JUMP_IF_FALSE expects [condition,label]")
                if not bool(_value(args[0], env)):
                    next_pc = label_pc[_name(args[1], "JUMP_IF_FALSE")]

            elif opcode == "OMEGA_REBUILD":
                if len(args) != 1:
                    raise NativeOperatorError("OMEGA_REBUILD expects [target]")
                target_name, value = _target(args[0], env)
                if not isinstance(value, Mapping):
                    raise NativeOperatorError("OMEGA_REBUILD target must be an object")
                construction = value.get("construction", value)
                if not isinstance(construction, Mapping):
                    raise NativeOperatorError("OMEGA_REBUILD requires an Omega record or construction object")
                env[target_name] = make_omega(**_thaw(construction))

            elif opcode == "RETURN":
                if len(args) != 2:
                    raise NativeOperatorError("RETURN expects [candidate,consequence]")
                candidate = deepcopy(_value(args[0], env))
                consequence = _value(args[1], env)
                if not isinstance(consequence, str) or not consequence:
                    raise NativeOperatorError("RETURN consequence must be non-empty text")
                candidate = validate_omega(candidate)
                return {
                    "omega": candidate,
                    "consequenceKey": consequence,
                    "metrics": _thaw(spec.metrics),
                    "knowledgeDecay": _thaw(spec.knowledge_decay),
                    "reconstruction": {"status": spec.reconstruction},
                }

            else:
                raise NativeOperatorError(f"unsupported native opcode {opcode!r}")

            pc = next_pc

        raise NativeOperatorError(f"OPERATOR {spec.operator_id!r} terminated without RETURN")

    return execute


def native_registry(program: Program) -> dict[str, Callable[[dict[str, Any]], dict[str, Any]]]:
    """Compile all declared OPERATOR bodies into the existing APPLY registry shape."""
    if not isinstance(program, Program):
        raise TypeError("program must be a parsed RMAPL Program")
    return {
        spec.operator_id: _native_callable(spec)
        for spec in program.operators
    }


def merged_registry(
    program: Program,
    external: Mapping[str, Callable[[dict[str, Any]], Mapping[str, Any]]] | None = None,
) -> dict[str, Callable[[dict[str, Any]], Mapping[str, Any]]]:
    """Merge native and explicit external operators, refusing ambiguous authority."""
    result: dict[str, Callable[[dict[str, Any]], Mapping[str, Any]]] = dict(native_registry(program))
    if external:
        overlap = set(result) & set(external)
        if overlap:
            raise NativeOperatorError(
                f"operator authority collision between native and external registries: {sorted(overlap)}"
            )
        result.update(external)
    return result
