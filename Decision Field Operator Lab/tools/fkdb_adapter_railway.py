from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any


AUTHORITY_SCOPE = "RAILWAY_REPOSITORY_ARTIFACT_ONLY"
EVIDENCE_STATUS = "DEPLOYMENT_ARTIFACT_NOT_LIVE_DEPLOYMENT_STATE"
LEGACY_CUTOFF = "2026-12-01"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _retrieved_at(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _artifact_metadata(relative: str) -> tuple[str, str, list[str]]:
    if relative == ".railway/railway.ts":
        return ("infrastructure-as-code", "CURRENT_IAC", [])
    if relative in {"railway.json", "railway.toml"}:
        return (
            "legacy-config-as-code",
            "LEGACY_DEPRECATED_CONFIG",
            [
                "RAILWAY_CONFIG_AS_CODE_DEPRECATED",
                "RAILWAY_CONFIG_AS_CODE_CUTOFF_2026_12_01",
            ],
        )
    if relative in {"Dockerfile", "nixpacks.toml", "Procfile"}:
        return ("build-config", "REPOSITORY_BUILD_INPUT", [])
    return ("portable-deployment-snapshot", "PORTABLE_SNAPSHOT", [])


def _payload_type(path: Path) -> str:
    name = path.name
    suffix = path.suffix.lower()
    if name == "railway.ts":
        return "text/typescript"
    if suffix == ".json":
        return "application/json"
    if suffix == ".toml":
        return "application/toml"
    if suffix == ".log":
        return "text/plain"
    return "text/plain"


def _carrier(path: Path, root: Path, raw: bytes) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    digest = _sha256(raw)
    text = raw.decode("utf-8")
    artifact_kind, authority_status, remainder = _artifact_metadata(relative)
    return {
        "schema": "fkdb/tool-carrier/v1",
        "carrier_id": "railway-" + _sha256(
            (relative + "\0" + digest).encode("utf-8")
        )[:32],
        "tool_id": "railway",
        "tool_version": "repository-artifact-v1",
        "adapter_kind": "LOCAL_FILE",
        "locality": "LOCAL_FILE",
        "source_identity": relative,
        "source_version": digest,
        "retrieved_at": _retrieved_at(path),
        "payload_type": _payload_type(path),
        "payload": text,
        "content_hash": digest,
        "provenance": {
            "provider": "railway",
            "source_identity": relative,
            "artifact_kind": artifact_kind,
            "railway_authority_status": authority_status,
            "live_state_observed": False,
            "legacy_config_cutoff": (
                LEGACY_CUTOFF if authority_status == "LEGACY_DEPRECATED_CONFIG" else None
            ),
        },
        "authority_scope": AUTHORITY_SCOPE,
        "evidence_status": EVIDENCE_STATUS,
        "obligation": "COLLECT_RAILWAY_REPOSITORY_ARTIFACT",
        "relations": [],
        "cost": {"bytes_read": len(raw)},
        "loss": [],
        "remainder": remainder,
        "recovery_path": (
            "re-read " + relative
            + " under the same allowed repository root; no Railway live deployment state was queried"
        ),
    }


class RailwayAdapter:
    tool_id = "railway"

    def _fixed_candidates(self, context, root: Path) -> list[Path]:
        candidates: list[Path] = []
        paths = (
            root / ".railway" / "railway.ts",
            root / "railway.json",
            root / "railway.toml",
            root / "Dockerfile",
            root / "nixpacks.toml",
            root / "Procfile",
        )
        for path in paths:
            resolved = context.resolve_read_path(path)
            if resolved.is_file():
                candidates.append(resolved)
        return candidates

    def descriptor(self, context) -> dict[str, Any]:
        for root in context.policy.read_roots:
            try:
                candidates = self._fixed_candidates(context, root)
            except PermissionError:
                continue
            if candidates:
                has_current = any(
                    path.relative_to(root).as_posix() == ".railway/railway.ts"
                    for path in candidates
                )
                unresolved = [] if has_current else [
                    "RAILWAY_CURRENT_IAC_NOT_FOUND"
                ]
                return {
                    "tool_id": self.tool_id,
                    "locality": "LOCAL_FILE",
                    "state": "AVAILABLE" if has_current else "DEGRADED",
                    "capabilities": ["COLLECT", "READ_REPOSITORY_ARTIFACTS"],
                    "unresolved_requirements": unresolved,
                }
        return {
            "tool_id": self.tool_id,
            "locality": "LOCAL_FILE",
            "state": "UNAVAILABLE",
            "capabilities": ["COLLECT", "READ_REPOSITORY_ARTIFACTS"],
            "unresolved_requirements": ["RAILWAY_PROJECT_ARTIFACTS_NOT_FOUND"],
        }

    def collect(self, request_value, context) -> dict[str, Any]:
        if context.resolved_root is None:
            raise ValueError("Railway collection requires a repository root")
        root = context.resolved_root
        candidates = self._fixed_candidates(context, root)

        options = request_value.get("options", {})
        snapshot_paths = options.get("snapshot_paths", [])
        if not isinstance(snapshot_paths, list):
            raise ValueError("Railway snapshot_paths must be a list")
        for value in snapshot_paths:
            if not isinstance(value, str) or not value:
                raise ValueError("Railway snapshot path must be a non-empty string")
            candidate = Path(value)
            if not candidate.is_absolute():
                candidate = root / candidate
            resolved = context.resolve_read_path(candidate)
            if not resolved.is_file():
                raise ValueError("Railway snapshot path must reference a file")
            if resolved.suffix.lower() not in {".log", ".txt", ".json", ".ndjson"}:
                raise ValueError("unsupported Railway snapshot extension")
            candidates.append(resolved)

        candidates = sorted(
            {path: None for path in candidates},
            key=lambda path: path.relative_to(root).as_posix(),
        )

        if not candidates:
            return {
                "status": "UNAVAILABLE",
                "carriers": [],
                "remainder": ["RAILWAY_PROJECT_ARTIFACTS_NOT_FOUND"],
                "cost": {"files_scanned": 0, "bytes_read": 0},
            }

        carriers: list[dict[str, Any]] = []
        remainder: list[str] = []
        files_scanned = 0
        bytes_read = 0

        for path in candidates:
            if files_scanned >= context.max_files:
                remainder.append("RAILWAY_FILE_LIMIT_REACHED")
                break
            size = path.stat().st_size
            if bytes_read + size > context.max_bytes:
                remainder.append("RAILWAY_BYTE_LIMIT_REACHED")
                break

            raw = path.read_bytes()
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                remainder.append(
                    "RAILWAY_INVALID_UTF8:" + path.relative_to(root).as_posix()
                )
                files_scanned += 1
                bytes_read += len(raw)
                continue

            files_scanned += 1
            bytes_read += len(raw)
            carriers.append(_carrier(path, root, raw))

        return {
            "status": "PARTIAL" if remainder else "COLLECTED",
            "carriers": carriers,
            "remainder": remainder,
            "cost": {
                "files_scanned": files_scanned,
                "bytes_read": bytes_read,
            },
        }
