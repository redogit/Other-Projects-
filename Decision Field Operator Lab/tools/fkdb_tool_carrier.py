from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


TOOL_CARRIER_SCHEMA = "fkdb/tool-carrier/v1"
TOOL_BUNDLE_SCHEMA = "fkdb/tool-bundle/v1"

LOCALITIES = frozenset(
    {
        "EMBEDDED",
        "LOCAL_FILE",
        "LOCAL_PROCESS",
        "LOCALHOST",
        "PORTABLE_IMPORT",
        "USER_HANDOFF",
        "REMOTE_OPTIONAL",
    }
)

REQUIRED_CARRIER_FIELDS = (
    "schema",
    "carrier_id",
    "tool_id",
    "tool_version",
    "adapter_kind",
    "locality",
    "source_identity",
    "source_version",
    "retrieved_at",
    "payload_type",
    "payload",
    "content_hash",
    "provenance",
    "authority_scope",
    "evidence_status",
    "obligation",
    "relations",
    "cost",
    "loss",
    "remainder",
    "recovery_path",
)

_HEX = frozenset("0123456789abcdef")


def sha256_hex(data: bytes) -> str:
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("sha256_hex requires bytes-like input")
    return hashlib.sha256(bytes(data)).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _payload_bytes(payload: Any) -> bytes:
    if isinstance(payload, str):
        return payload.encode("utf-8")
    if isinstance(payload, (dict, list, int, float, bool)) or payload is None:
        return _canonical_json_bytes(payload)
    raise ValueError("ToolCarrier payload must be a JSON-compatible value")


def _require_nonempty_string(value: dict[str, Any], field: str) -> str:
    candidate = value.get(field)
    if not isinstance(candidate, str) or not candidate:
        raise ValueError(f"ToolCarrier {field} must be a non-empty string")
    return candidate


def _require_list(value: dict[str, Any], field: str) -> list[Any]:
    candidate = value.get(field)
    if not isinstance(candidate, list):
        raise ValueError(f"ToolCarrier {field} must be a list")
    return candidate


def _validate_hash(value: str, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in _HEX for ch in value)
    ):
        raise ValueError(f"{field} must be a lowercase SHA-256 hex digest")
    return value


def validate_tool_carrier(
    value: dict[str, Any], *, max_payload_bytes: int
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("ToolCarrier must be a JSON object")
    if max_payload_bytes < 0:
        raise ValueError("max_payload_bytes must be non-negative")

    missing = [field for field in REQUIRED_CARRIER_FIELDS if field not in value]
    if missing:
        raise ValueError("ToolCarrier missing fields: " + ", ".join(missing))
    if value.get("schema") != TOOL_CARRIER_SCHEMA:
        raise ValueError("unsupported ToolCarrier schema")

    for field in (
        "carrier_id",
        "tool_id",
        "tool_version",
        "adapter_kind",
        "source_identity",
        "source_version",
        "retrieved_at",
        "payload_type",
        "authority_scope",
        "evidence_status",
        "obligation",
        "recovery_path",
    ):
        _require_nonempty_string(value, field)

    locality = _require_nonempty_string(value, "locality")
    if locality not in LOCALITIES:
        raise ValueError(f"unsupported ToolCarrier locality: {locality}")

    provenance = value.get("provenance")
    if not isinstance(provenance, dict) or not provenance:
        raise ValueError("ToolCarrier provenance must be a non-empty object")
    if not isinstance(value.get("cost"), dict):
        raise ValueError("ToolCarrier cost must be an object")
    for field in ("relations", "loss", "remainder"):
        _require_list(value, field)

    payload = _payload_bytes(value.get("payload"))
    if len(payload) > max_payload_bytes:
        raise ValueError(
            f"ToolCarrier payload exceeds bound: {len(payload)} > {max_payload_bytes}"
        )

    expected_hash = _validate_hash(value.get("content_hash"), "content_hash")
    actual_hash = sha256_hex(payload)
    if actual_hash != expected_hash:
        raise ValueError("ToolCarrier content_hash does not match canonical payload bytes")

    # Round-trip through canonical JSON to return a detached JSON-compatible value.
    return json.loads(_canonical_json_bytes(value).decode("utf-8"))


def canonical_carrier_bytes(carrier: dict[str, Any]) -> bytes:
    if not isinstance(carrier, dict):
        raise TypeError("carrier must be a dict")
    return _canonical_json_bytes(carrier)


def _within_bundle_root(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _validate_attachment(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("ToolBundle attachment must be an object")
    required = ("sha256", "size", "path")
    missing = [field for field in required if field not in value]
    if missing:
        raise ValueError("ToolBundle attachment missing fields: " + ", ".join(missing))
    _validate_hash(value.get("sha256"), "attachment sha256")
    size = value.get("size")
    if type(size) is not int or size < 0:
        raise ValueError("ToolBundle attachment size must be a non-negative integer")
    path = value.get("path")
    if not isinstance(path, str) or not path:
        raise ValueError("ToolBundle attachment path must be non-empty")
    pure = Path(path)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError("ToolBundle attachment path must be relative and non-traversing")
    return dict(value)


def load_tool_bundle(
    path: Path, *, max_bundle_bytes: int
) -> dict[str, Any]:
    path = Path(path)
    if max_bundle_bytes < 0:
        raise ValueError("max_bundle_bytes must be non-negative")
    size = path.stat().st_size
    if size > max_bundle_bytes:
        raise ValueError(
            f"ToolBundle exceeds bound: {size} > {max_bundle_bytes}"
        )

    raw = path.read_bytes()
    try:
        bundle = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("ToolBundle is not valid UTF-8 JSON") from exc

    if not isinstance(bundle, dict):
        raise ValueError("ToolBundle must be an object")
    if bundle.get("schema") != TOOL_BUNDLE_SCHEMA:
        raise ValueError("unsupported ToolBundle schema")

    manifest = bundle.get("manifest")
    if not isinstance(manifest, dict):
        raise ValueError("ToolBundle manifest must be an object")
    bundle_id = manifest.get("bundle_id")
    if not isinstance(bundle_id, str) or not bundle_id:
        raise ValueError("ToolBundle manifest.bundle_id must be non-empty")

    carriers = bundle.get("carriers")
    if not isinstance(carriers, list):
        raise ValueError("ToolBundle carriers must be a list")
    validated_carriers: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for carrier in carriers:
        validated = validate_tool_carrier(
            carrier, max_payload_bytes=max_bundle_bytes
        )
        carrier_id = validated["carrier_id"]
        if carrier_id in seen_ids:
            raise ValueError(f"duplicate ToolCarrier id: {carrier_id}")
        seen_ids.add(carrier_id)
        validated_carriers.append(validated)

    attachments = bundle.get("attachments")
    if not isinstance(attachments, list):
        raise ValueError("ToolBundle attachments must be a list")
    validated_attachments: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    bundle_root = path.parent.resolve()
    total_bundle_bytes = size

    for attachment in attachments:
        validated = _validate_attachment(attachment)
        digest = validated["sha256"]
        if digest in seen_hashes:
            raise ValueError(f"duplicate ToolBundle attachment digest: {digest}")

        relative = Path(validated["path"])
        try:
            candidate = (bundle_root / relative).resolve(strict=True)
        except FileNotFoundError as exc:
            raise ValueError(
                f"ToolBundle attachment file is missing: {validated['path']}"
            ) from exc

        if not _within_bundle_root(candidate, bundle_root):
            raise ValueError("ToolBundle attachment escapes bundle root")
        if not candidate.is_file():
            raise ValueError("ToolBundle attachment must reference a regular file")

        declared_size = validated["size"]
        actual_size = candidate.stat().st_size
        if actual_size != declared_size:
            raise ValueError(
                "ToolBundle attachment size does not match referenced bytes"
            )
        if total_bundle_bytes + actual_size > max_bundle_bytes:
            raise ValueError(
                "ToolBundle exceeds bound when attachment bytes are included"
            )

        with candidate.open("rb") as handle:
            raw_attachment = handle.read(actual_size + 1)
        if len(raw_attachment) != actual_size:
            raise ValueError(
                "ToolBundle attachment size changed while validating bytes"
            )
        if sha256_hex(raw_attachment) != digest:
            raise ValueError(
                "ToolBundle attachment sha256 does not match referenced bytes"
            )

        total_bundle_bytes += actual_size
        seen_hashes.add(digest)
        validated_attachments.append(validated)

    return {
        "schema": TOOL_BUNDLE_SCHEMA,
        "manifest": dict(manifest),
        "carriers": validated_carriers,
        "attachments": validated_attachments,
    }
