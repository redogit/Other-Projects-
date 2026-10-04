from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Callable


AUTHORITY_SCOPE = "WOLFRAM_ARTIFACT_ONLY"
EVIDENCE_STATUS = "ARTIFACT_NOT_EXECUTED"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _retrieved_at(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


class WolframAdapter:
    tool_id = "wolfram"

    def __init__(self, *, which_fn: Callable[[str], str | None] | None = None):
        self.which_fn = which_fn or shutil.which

    def _discovered_executable(self) -> str | None:
        value = self.which_fn("wolframscript")
        return value if isinstance(value, str) and value else None

    def _has_artifact(self, context) -> bool:
        for root in context.policy.read_roots:
            for pattern in ("*.wl", "*.m", "*.nb"):
                for path in root.glob(pattern):
                    try:
                        resolved = context.policy.resolve_allowed_path(path, "READ")
                    except PermissionError:
                        continue
                    if resolved.is_file():
                        return True
        return False

    def descriptor(self, context) -> dict[str, Any]:
        executable = self._discovered_executable()
        has_artifact = self._has_artifact(context)
        capabilities = ["COLLECT_ARTIFACT"]
        unresolved: list[str] = []

        if executable is not None:
            capabilities.append("LOCAL_PROCESS_PROBE")
            unresolved.append("PROCESS_ISOLATION_BACKEND_UNAVAILABLE")
            state = "DEGRADED"
        elif has_artifact:
            state = "AVAILABLE"
        else:
            state = "UNAVAILABLE"
            unresolved.append("WOLFRAM_ARTIFACTS_NOT_FOUND")

        return {
            "tool_id": self.tool_id,
            "locality": "LOCAL_FILE",
            "state": state,
            "capabilities": capabilities,
            "unresolved_requirements": unresolved,
        }

    def collect(self, request_value, context) -> dict[str, Any]:
        if context.resolved_root is None:
            raise ValueError("Wolfram artifact collection requires a root")
        options = request_value.get("options", {})
        if options.get("mode") != "artifact":
            raise ValueError("Wolfram collection mode must be artifact")

        path_value = options.get("path")
        if not isinstance(path_value, str) or not path_value:
            raise ValueError("Wolfram artifact path must be a non-empty string")

        candidate = Path(path_value)
        if not candidate.is_absolute():
            candidate = context.resolved_root / candidate
        path = context.resolve_read_path(candidate)
        if not path.is_file():
            return {
                "status": "UNAVAILABLE",
                "carriers": [],
                "remainder": ["WOLFRAM_ARTIFACT_NOT_FOUND"],
                "cost": {"files_scanned": 0, "bytes_read": 0},
            }

        suffix = path.suffix.lower()
        if suffix not in {".wl", ".m", ".nb"}:
            raise ValueError("unsupported Wolfram artifact extension")

        size = path.stat().st_size
        if size > context.max_bytes:
            return {
                "status": "PARTIAL",
                "carriers": [],
                "remainder": ["WOLFRAM_ARTIFACT_BYTE_LIMIT_REACHED"],
                "cost": {"files_scanned": 0, "bytes_read": 0},
            }

        raw = path.read_bytes()
        raw_digest = _sha256(raw)
        relative = path.relative_to(context.resolved_root).as_posix()

        if suffix == ".nb":
            payload: Any = {
                "encoding": "base64",
                "bytes": base64.b64encode(raw).decode("ascii"),
            }
            payload_type = "application/vnd.wolfram.notebook"
            content_hash = _sha256(_canonical_json_bytes(payload))
        else:
            try:
                payload = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError("Wolfram text artifact must be UTF-8") from exc
            payload_type = "text/plain"
            content_hash = raw_digest

        carrier = {
            "schema": "fkdb/tool-carrier/v1",
            "carrier_id": "wolfram-" + _sha256(
                (relative + "\0" + raw_digest).encode("utf-8")
            )[:32],
            "tool_id": "wolfram",
            "tool_version": "artifact-v1",
            "adapter_kind": "LOCAL_FILE",
            "locality": "LOCAL_FILE",
            "source_identity": relative,
            "source_version": raw_digest,
            "retrieved_at": _retrieved_at(path),
            "payload_type": payload_type,
            "payload": payload,
            "content_hash": content_hash,
            "provenance": {
                "provider": "wolfram",
                "source_identity": relative,
                "artifact_sha256": raw_digest,
                "executed": False,
            },
            "authority_scope": AUTHORITY_SCOPE,
            "evidence_status": EVIDENCE_STATUS,
            "obligation": "COLLECT_WOLFRAM_ARTIFACT",
            "relations": [],
            "cost": {"bytes_read": len(raw)},
            "loss": [],
            "remainder": [],
            "recovery_path": (
                "re-read Wolfram artifact " + relative
                + " under the same allowed root; no execution was performed"
            ),
        }
        return {
            "status": "COLLECTED",
            "carriers": [carrier],
            "remainder": [],
            "cost": {"files_scanned": 1, "bytes_read": len(raw)},
        }
