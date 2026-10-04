from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


AUTHORITY_SCOPE = "MATHBOX_RECORDED_STATE_ONLY"
EVIDENCE_STATUS = "MECHANICAL_LEDGER_RECORD_NOT_PROOF_AUDIT"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _retrieved_at(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _carrier_for(path: Path, root: Path, raw: bytes) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    digest = _sha256(raw)
    carrier_id = "mathbox-" + _sha256(
        (relative + "\0" + digest).encode("utf-8")
    )[:32]
    text = raw.decode("utf-8")
    return {
        "schema": "fkdb/tool-carrier/v1",
        "carrier_id": carrier_id,
        "tool_id": "mathbox",
        "tool_version": "research-state-v1",
        "adapter_kind": "LOCAL_FILE",
        "locality": "LOCAL_FILE",
        "source_identity": relative,
        "source_version": digest,
        "retrieved_at": _retrieved_at(path),
        "payload_type": "application/json",
        "payload": text,
        "content_hash": digest,
        "provenance": {
            "provider": "mathbox",
            "source_identity": relative,
            "record_kind": (
                "config" if relative.endswith("/config.json") else "ledger-event"
            ),
        },
        "authority_scope": AUTHORITY_SCOPE,
        "evidence_status": EVIDENCE_STATUS,
        "obligation": "COLLECT_MATHBOX_RECORDED_STATE",
        "relations": [],
        "cost": {"bytes_read": len(raw)},
        "loss": [],
        "remainder": [],
        "recovery_path": f"re-read {relative} under the same allowed project root",
    }


class MathboxAdapter:
    tool_id = "mathbox"

    def descriptor(self, context) -> dict[str, Any]:
        found = False
        unresolved: list[str] = []
        for root in context.policy.read_roots:
            candidate = root / ".mathbox" / "config.json"
            try:
                resolved = context.policy.resolve_allowed_path(candidate, "READ")
            except PermissionError:
                unresolved.append("MATHBOX_PATH_OUTSIDE_ALLOWED_ROOT")
                continue
            if resolved.is_file():
                found = True
                break

        return {
            "tool_id": self.tool_id,
            "locality": "LOCAL_FILE",
            "state": "AVAILABLE" if found else "UNAVAILABLE",
            "capabilities": ["COLLECT", "READ_MATHBOX_LEDGER"],
            "unresolved_requirements": (
                [] if found else (unresolved or ["MATHBOX_LEDGER_NOT_FOUND"])
            ),
        }

    def collect(self, request_value, context) -> dict[str, Any]:
        if context.resolved_root is None:
            raise ValueError("Mathbox collection requires a project root")

        root = context.resolved_root
        mathbox_dir = context.resolve_read_path(root / ".mathbox")
        config = context.resolve_read_path(mathbox_dir / "config.json")

        if not config.is_file():
            return {
                "status": "UNAVAILABLE",
                "carriers": [],
                "remainder": ["MATHBOX_LEDGER_NOT_FOUND"],
                "cost": {"files_scanned": 0, "bytes_read": 0},
            }

        candidates: list[Path] = [config]
        events_dir = context.resolve_read_path(mathbox_dir / "events")
        if events_dir.exists():
            if not events_dir.is_dir():
                return {
                    "status": "PARTIAL",
                    "carriers": [],
                    "remainder": ["MATHBOX_EVENTS_PATH_NOT_DIRECTORY"],
                    "cost": {"files_scanned": 0, "bytes_read": 0},
                }
            event_candidates = sorted(
                (
                    context.resolve_read_path(path)
                    for path in events_dir.glob("*.json")
                ),
                key=lambda path: path.name,
            )
            candidates.extend(path for path in event_candidates if path.is_file())

        carriers: list[dict[str, Any]] = []
        remainder: list[str] = []
        files_scanned = 0
        bytes_read = 0

        for index, path in enumerate(candidates):
            if files_scanned >= context.max_files:
                remainder.append("MATHBOX_FILE_LIMIT_REACHED")
                break

            size = path.stat().st_size
            if bytes_read + size > context.max_bytes:
                remainder.append("MATHBOX_BYTE_LIMIT_REACHED")
                break

            raw = path.read_bytes()
            files_scanned += 1
            bytes_read += len(raw)

            try:
                json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                relative = path.relative_to(root).as_posix()
                remainder.append(f"MATHBOX_INVALID_JSON:{relative}")
                continue

            carriers.append(_carrier_for(path, root, raw))

        status = "COLLECTED"
        if remainder:
            status = "PARTIAL"
        if not carriers and not remainder:
            status = "UNAVAILABLE"

        return {
            "status": status,
            "carriers": carriers,
            "remainder": remainder,
            "cost": {
                "files_scanned": files_scanned,
                "bytes_read": bytes_read,
            },
        }
