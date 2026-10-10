from __future__ import annotations

from pathlib import Path
import re
from typing import Any


_SERVICE_ROLE = re.compile(r"service[._\s-]*role")
_PRIVATE_KEY = re.compile(r"private[._\s-]*key")
_SSH_IDENTITY = re.compile(r"^id_(?:rsa|dsa|ecdsa|ed25519)(?:$|[._-])")
_KEY_SUFFIXES = (".key", ".pem", ".p12", ".pfx", ".pkcs12", ".keystore", ".jks")
_INFRASTRUCTURE_TOOLS = frozenset({"supabase", "railway"})


def is_secret_sensitive_path(path: str | Path) -> bool:
    """Classify path names, not payloads; callers supply project-relative paths."""
    for component in str(path).replace("\\", "/").split("/"):
        # Screen both the underlying filename and Windows alternate stream names.
        for segment in component.casefold().split(":"):
            name = segment.rstrip(" .")
            if (
                name.startswith(".env")
                or "secret" in name
                or "credential" in name
                or _SERVICE_ROLE.search(name)
                or _PRIVATE_KEY.search(name)
                or name.endswith(_KEY_SUFFIXES)
                or (_SSH_IDENTITY.search(name) and not name.endswith(".pub"))
            ):
                return True
    return False


def reject_secret_sensitive_infrastructure_sources(
    value: dict[str, Any], *, include_source_refs: bool = False,
) -> None:
    """Reject recognizable Plan C sources, including their retained projections."""
    provenance = value.get("provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    tool_ids = (value.get("tool_id"), provenance.get("tool_id"), provenance.get("provider"))
    if not any(
        isinstance(tool_id, str) and tool_id.casefold() in _INFRASTRUCTURE_TOOLS
        for tool_id in tool_ids
    ):
        return
    sources = [value.get("source_identity"), provenance.get("source_identity")]
    if include_source_refs and isinstance(value.get("source_refs"), list):
        sources.extend(value["source_refs"])
    if any(isinstance(source, str) and is_secret_sensitive_path(source) for source in sources):
        raise ValueError("secret-sensitive Supabase/Railway artifact source is forbidden")
