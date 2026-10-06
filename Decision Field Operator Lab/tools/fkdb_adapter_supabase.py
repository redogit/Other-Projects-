from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any


AUTHORITY_SCOPE = "SUPABASE_LOCAL_PROJECT_ARTIFACT_ONLY"
EVIDENCE_STATUS = "CONFIG_OR_MIGRATION_NOT_APPLIED_STATE"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _retrieved_at(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _secret_like(path: Path) -> bool:
    name = path.name.lower()
    return (
        name.startswith(".env")
        or "service_role" in name
        or "service-role" in name
        or "secret" in name
        or name.endswith(".key")
        or name.endswith(".pem")
    )


def _artifact_kind(relative: str) -> str:
    if relative == "supabase/config.toml":
        return "config"
    if relative == "supabase/seed.sql":
        return "seed"
    if relative.startswith("supabase/migrations/"):
        return "migration"
    if relative.startswith("supabase/functions/"):
        return "edge-function"
    return "local-project-artifact"


def _payload_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".sql":
        return "application/sql"
    if suffix == ".toml":
        return "application/toml"
    if suffix == ".json":
        return "application/json"
    if suffix == ".ts":
        return "text/typescript"
    return "text/plain"


def _carrier(path: Path, root: Path, raw: bytes) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    digest = _sha256(raw)
    text = raw.decode("utf-8")
    kind = _artifact_kind(relative)
    return {
        "schema": "fkdb/tool-carrier/v1",
        "carrier_id": "supabase-" + _sha256(
            (relative + "\0" + digest).encode("utf-8")
        )[:32],
        "tool_id": "supabase",
        "tool_version": "local-project-v1",
        "adapter_kind": "LOCAL_FILE",
        "locality": "LOCAL_FILE",
        "source_identity": relative,
        "source_version": digest,
        "retrieved_at": _retrieved_at(path),
        "payload_type": _payload_type(path),
        "payload": text,
        "content_hash": digest,
        "provenance": {
            "provider": "supabase",
            "source_identity": relative,
            "artifact_kind": kind,
            "runtime_state_observed": False,
        },
        "authority_scope": AUTHORITY_SCOPE,
        "evidence_status": EVIDENCE_STATUS,
        "obligation": "COLLECT_SUPABASE_LOCAL_PROJECT_ARTIFACT",
        "relations": [],
        "cost": {"bytes_read": len(raw)},
        "loss": [],
        "remainder": [],
        "recovery_path": (
            "re-read " + relative
            + " under the same allowed project root; no database or hosted state was queried"
        ),
    }


class SupabaseAdapter:
    tool_id = "supabase"

    def _supabase_root(self, context, root: Path) -> Path:
        return context.resolve_read_path(root / "supabase")

    def descriptor(self, context) -> dict[str, Any]:
        for root in context.policy.read_roots:
            try:
                supabase = self._supabase_root(context, root)
                config = context.resolve_read_path(supabase / "config.toml")
            except PermissionError:
                continue
            if config.is_file():
                return {
                    "tool_id": self.tool_id,
                    "locality": "LOCAL_FILE",
                    "state": "AVAILABLE",
                    "capabilities": ["COLLECT", "READ_LOCAL_PROJECT"],
                    "unresolved_requirements": [
                        "LIVE_SUPABASE_RUNTIME_STATE_NOT_QUERIED"
                    ],
                }
        return {
            "tool_id": self.tool_id,
            "locality": "LOCAL_FILE",
            "state": "UNAVAILABLE",
            "capabilities": ["COLLECT", "READ_LOCAL_PROJECT"],
            "unresolved_requirements": ["SUPABASE_LOCAL_PROJECT_NOT_FOUND"],
        }

    def _candidates(self, context, root: Path) -> list[Path]:
        supabase = self._supabase_root(context, root)
        if not supabase.exists():
            return []
        if not supabase.is_dir():
            raise ValueError("supabase path exists but is not a directory")

        candidates: list[Path] = []
        fixed = (supabase / "config.toml", supabase / "seed.sql")
        for path in fixed:
            resolved = context.resolve_read_path(path)
            if resolved.is_file() and not _secret_like(resolved):
                candidates.append(resolved)

        migrations = context.resolve_read_path(supabase / "migrations")
        if migrations.exists():
            if not migrations.is_dir():
                raise ValueError("supabase/migrations exists but is not a directory")
            for path in migrations.glob("*.sql"):
                resolved = context.resolve_read_path(path)
                if resolved.is_file() and not _secret_like(resolved):
                    candidates.append(resolved)

        functions = context.resolve_read_path(supabase / "functions")
        if functions.exists():
            if not functions.is_dir():
                raise ValueError("supabase/functions exists but is not a directory")
            for pattern in ("**/*.ts", "**/*.json"):
                for path in functions.glob(pattern):
                    resolved = context.resolve_read_path(path)
                    if resolved.is_file() and not _secret_like(resolved):
                        candidates.append(resolved)

        unique = {path: None for path in candidates}
        return sorted(unique, key=lambda path: path.relative_to(root).as_posix())

    def collect(self, request_value, context) -> dict[str, Any]:
        if context.resolved_root is None:
            raise ValueError("Supabase collection requires a project root")
        root = context.resolved_root
        candidates = self._candidates(context, root)
        if not candidates:
            return {
                "status": "UNAVAILABLE",
                "carriers": [],
                "remainder": ["SUPABASE_LOCAL_PROJECT_NOT_FOUND"],
                "cost": {"files_scanned": 0, "bytes_read": 0},
            }

        carriers: list[dict[str, Any]] = []
        remainder: list[str] = []
        files_scanned = 0
        bytes_read = 0

        for path in candidates:
            if files_scanned >= context.max_files:
                remainder.append("SUPABASE_FILE_LIMIT_REACHED")
                break
            size = path.stat().st_size
            if bytes_read + size > context.max_bytes:
                remainder.append("SUPABASE_BYTE_LIMIT_REACHED")
                break

            raw = path.read_bytes()
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                remainder.append(
                    "SUPABASE_INVALID_UTF8:" + path.relative_to(root).as_posix()
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
