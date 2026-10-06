from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any


AUTHORITY_SCOPE = "WORKFLOW_ARTIFACT_ONLY"
EVIDENCE_STATUS = "WORKFLOW_STATE_NOT_CLAIM_VERIFICATION"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _retrieved_at(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _artifact_kind(path: Path) -> str:
    if path.name.endswith("-progress.md"):
        return "progress"
    if "plans" in path.parts:
        return "plan"
    return "spec"


def _carrier_for(path: Path, root: Path, raw: bytes) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    digest = _sha256(raw)
    carrier_id = "superpowers-" + _sha256(
        (relative + "\0" + digest).encode("utf-8")
    )[:32]
    text = raw.decode("utf-8")
    kind = _artifact_kind(path)
    return {
        "schema": "fkdb/tool-carrier/v1",
        "carrier_id": carrier_id,
        "tool_id": "superpowers",
        "tool_version": "project-artifact-v1",
        "adapter_kind": "LOCAL_FILE",
        "locality": "LOCAL_FILE",
        "source_identity": relative,
        "source_version": digest,
        "retrieved_at": _retrieved_at(path),
        "payload_type": "text/markdown",
        "payload": text,
        "content_hash": digest,
        "provenance": {
            "provider": "superpowers",
            "source_identity": relative,
            "artifact_kind": kind,
        },
        "authority_scope": AUTHORITY_SCOPE,
        "evidence_status": EVIDENCE_STATUS,
        "obligation": "COLLECT_SUPERPOWERS_WORKFLOW_ARTIFACT",
        "relations": [],
        "cost": {"bytes_read": len(raw)},
        "loss": [],
        "remainder": [],
        "recovery_path": f"re-read {relative} under the same allowed project root",
    }


class SuperpowersAdapter:
    tool_id = "superpowers"

    def _directories(self, context, root: Path) -> list[Path]:
        base = context.resolve_read_path(root / "docs" / "superpowers")
        directories: list[Path] = []
        for name in ("plans", "specs"):
            directory = context.resolve_read_path(base / name)
            if directory.exists():
                if not directory.is_dir():
                    raise ValueError(
                        f"Superpowers {name} path exists but is not a directory"
                    )
                directories.append(directory)
        return directories

    def descriptor(self, context) -> dict[str, Any]:
        found = False
        unresolved: list[str] = []
        for root in context.policy.read_roots:
            try:
                directories = self._directories(context, root)
            except PermissionError:
                unresolved.append("SUPERPOWERS_PATH_OUTSIDE_ALLOWED_ROOT")
                continue
            if any(any(directory.glob("*.md")) for directory in directories):
                found = True
                break

        return {
            "tool_id": self.tool_id,
            "locality": "LOCAL_FILE",
            "state": "AVAILABLE" if found else "UNAVAILABLE",
            "capabilities": ["COLLECT", "READ_WORKFLOW_ARTIFACTS"],
            "unresolved_requirements": (
                [] if found else (unresolved or ["SUPERPOWERS_ARTIFACTS_NOT_FOUND"])
            ),
        }

    def collect(self, request_value, context) -> dict[str, Any]:
        if context.resolved_root is None:
            raise ValueError("Superpowers collection requires a project root")

        root = context.resolved_root
        directories = self._directories(context, root)
        candidates: list[Path] = []
        for directory in directories:
            for path in directory.glob("*.md"):
                resolved = context.resolve_read_path(path)
                if resolved.is_file():
                    candidates.append(resolved)

        candidates.sort(key=lambda path: path.relative_to(root).as_posix())
        if not candidates:
            return {
                "status": "UNAVAILABLE",
                "carriers": [],
                "remainder": ["SUPERPOWERS_ARTIFACTS_NOT_FOUND"],
                "cost": {"files_scanned": 0, "bytes_read": 0},
            }

        carriers: list[dict[str, Any]] = []
        remainder: list[str] = []
        files_scanned = 0
        bytes_read = 0

        for path in candidates:
            if files_scanned >= context.max_files:
                remainder.append("SUPERPOWERS_FILE_LIMIT_REACHED")
                break
            size = path.stat().st_size
            if bytes_read + size > context.max_bytes:
                remainder.append("SUPERPOWERS_BYTE_LIMIT_REACHED")
                break

            raw = path.read_bytes()
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                remainder.append(
                    "SUPERPOWERS_INVALID_UTF8:"
                    + path.relative_to(root).as_posix()
                )
                files_scanned += 1
                bytes_read += len(raw)
                continue

            files_scanned += 1
            bytes_read += len(raw)
            carriers.append(_carrier_for(path, root, raw))

        return {
            "status": "PARTIAL" if remainder else "COLLECTED",
            "carriers": carriers,
            "remainder": remainder,
            "cost": {
                "files_scanned": files_scanned,
                "bytes_read": bytes_read,
            },
        }
