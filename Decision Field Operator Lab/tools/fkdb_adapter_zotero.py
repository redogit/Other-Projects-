from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib import error, parse, request


LOCAL_AUTHORITY = "ZOTERO_LOCAL_LIBRARY_METADATA_ONLY"
PORTABLE_AUTHORITY = "ZOTERO_PORTABLE_ARTIFACT_ONLY"
EVIDENCE_STATUS = "BIBLIOGRAPHIC_METADATA_NOT_SOURCE_VERIFICATION"


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


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


class _LoopbackRedirectHandler(request.HTTPRedirectHandler):
    def __init__(self, policy):
        super().__init__()
        self.policy = policy

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        try:
            self.policy.validate_loopback_url(newurl)
        except ValueError as exc:
            raise PermissionError("Zotero redirect left literal loopback") from exc
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class ZoteroAdapter:
    tool_id = "zotero"

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:23119",
        timeout: float = 0.5,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = float(timeout)

    def _opener(self, context):
        context.policy.validate_loopback_url(self.base_url + "/")
        return request.build_opener(_LoopbackRedirectHandler(context.policy))

    def _get_bytes(self, path: str, context, *, max_bytes: int) -> bytes:
        url = self.base_url + path
        context.policy.validate_loopback_url(url)
        req = request.Request(
            url,
            method="GET",
            headers={
                "Accept": "application/json",
                "User-Agent": "FKDB-Zotero-Local/1",
            },
        )
        opener = self._opener(context)
        with opener.open(req, timeout=self.timeout) as response:
            raw = response.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise ValueError("Zotero local API response exceeds configured byte bound")
        return raw

    def descriptor(self, context) -> dict[str, Any]:
        try:
            self._get_bytes("/api/", context, max_bytes=min(context.max_bytes, 8192))
            state = "AVAILABLE"
            unresolved: list[str] = []
        except PermissionError:
            raise
        except (
            error.URLError,
            error.HTTPError,
            TimeoutError,
            ConnectionError,
            OSError,
            ValueError,
        ):
            state = "UNAVAILABLE"
            unresolved = ["ZOTERO_LOCAL_API_UNAVAILABLE"]

        return {
            "tool_id": self.tool_id,
            "locality": "LOCALHOST",
            "state": state,
            "capabilities": [
                "READ_LOCAL_API",
                "IMPORT_PORTABLE_BIBLIOGRAPHY",
            ],
            "unresolved_requirements": unresolved,
        }

    def _local_api_carrier(self, item: dict[str, Any]) -> dict[str, Any]:
        item_key = item.get("key")
        if not isinstance(item_key, str) or not item_key:
            data = item.get("data")
            if isinstance(data, dict):
                item_key = data.get("key")
        if not isinstance(item_key, str) or not item_key:
            raise ValueError("Zotero local API item is missing item key")

        raw = _canonical_json_bytes(item)
        digest = _sha256(raw)
        data = item.get("data")
        citation_key = None
        if isinstance(data, dict):
            candidate = data.get("citationKey")
            if isinstance(candidate, str) and candidate:
                citation_key = candidate

        provenance = {
            "provider": "zotero",
            "zotero_item_key": item_key,
            "source": "desktop-local-api",
        }
        if citation_key is not None:
            provenance["citation_key"] = citation_key

        version = item.get("version")
        source_version = str(version) if version is not None else digest

        return {
            "schema": "fkdb/tool-carrier/v1",
            "carrier_id": "zotero-" + _sha256(
                ("item:" + item_key + "\0" + digest).encode("utf-8")
            )[:32],
            "tool_id": "zotero",
            "tool_version": "web-api-v3-local",
            "adapter_kind": "LOCALHOST",
            "locality": "LOCALHOST",
            "source_identity": "zotero:item:" + item_key,
            "source_version": source_version,
            "retrieved_at": _utc_now(),
            "payload_type": "application/json",
            "payload": raw.decode("utf-8"),
            "content_hash": digest,
            "provenance": provenance,
            "authority_scope": LOCAL_AUTHORITY,
            "evidence_status": EVIDENCE_STATUS,
            "obligation": "COLLECT_ZOTERO_BIBLIOGRAPHIC_METADATA",
            "relations": [],
            "cost": {"bytes_read": len(raw)},
            "loss": [],
            "remainder": [],
            "recovery_path": (
                "re-query Zotero Desktop local API for item key " + item_key
            ),
        }

    def _collect_local_api(self, options: dict[str, Any], context) -> dict[str, Any]:
        query = options.get("query", "")
        if not isinstance(query, str):
            raise ValueError("Zotero query must be a string")
        requested_limit = options.get("limit", context.max_files)
        if type(requested_limit) is not int or requested_limit <= 0:
            raise ValueError("Zotero limit must be a positive integer")
        limit = min(requested_limit, context.max_files, 100)

        encoded = parse.urlencode({"q": query, "limit": limit})
        raw = self._get_bytes(
            "/api/users/0/items?" + encoded,
            context,
            max_bytes=context.max_bytes,
        )
        try:
            items = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Zotero local API returned invalid JSON") from exc
        if not isinstance(items, list):
            raise ValueError("Zotero local API item search must return a list")

        selected = items[:limit]
        carriers = [self._local_api_carrier(item) for item in selected]
        remainder: list[str] = []
        status = "COLLECTED"
        if len(items) > limit:
            remainder.append("ZOTERO_RESULT_LIMIT_REACHED")
            status = "PARTIAL"

        return {
            "status": status,
            "carriers": carriers,
            "remainder": remainder,
            "cost": {
                "files_scanned": len(carriers),
                "bytes_read": len(raw),
            },
        }

    def _collect_portable(self, options: dict[str, Any], context) -> dict[str, Any]:
        if context.resolved_root is None:
            raise ValueError("portable Zotero collection requires a root")

        path_value = options.get("path")
        if not isinstance(path_value, str) or not path_value:
            raise ValueError("portable Zotero path must be a non-empty string")

        candidate = Path(path_value)
        if not candidate.is_absolute():
            candidate = context.resolved_root / candidate
        path = context.resolve_read_path(candidate)
        if not path.is_file():
            return {
                "status": "UNAVAILABLE",
                "carriers": [],
                "remainder": ["ZOTERO_PORTABLE_ARTIFACT_NOT_FOUND"],
                "cost": {"files_scanned": 0, "bytes_read": 0},
            }

        suffix = path.suffix.lower()
        payload_types = {
            ".bib": "application/x-bibtex",
            ".ris": "application/x-research-info-systems",
            ".json": "application/json",
        }
        payload_type = payload_types.get(suffix)
        if payload_type is None:
            raise ValueError("unsupported Zotero portable artifact extension")

        size = path.stat().st_size
        if size > context.max_bytes:
            return {
                "status": "PARTIAL",
                "carriers": [],
                "remainder": ["ZOTERO_PORTABLE_BYTE_LIMIT_REACHED"],
                "cost": {"files_scanned": 0, "bytes_read": 0},
            }

        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Zotero portable artifact must be UTF-8") from exc

        relative = path.relative_to(context.resolved_root).as_posix()
        digest = _sha256(raw)
        carrier = {
            "schema": "fkdb/tool-carrier/v1",
            "carrier_id": "zotero-portable-" + _sha256(
                (relative + "\0" + digest).encode("utf-8")
            )[:32],
            "tool_id": "zotero",
            "tool_version": "portable-v1",
            "adapter_kind": "PORTABLE_IMPORT",
            "locality": "PORTABLE_IMPORT",
            "source_identity": relative,
            "source_version": digest,
            "retrieved_at": _utc_now(),
            "payload_type": payload_type,
            "payload": text,
            "content_hash": digest,
            "provenance": {
                "provider": "zotero",
                "source": "portable-artifact",
                "source_identity": relative,
            },
            "authority_scope": PORTABLE_AUTHORITY,
            "evidence_status": EVIDENCE_STATUS,
            "obligation": "COLLECT_ZOTERO_PORTABLE_BIBLIOGRAPHY",
            "relations": [],
            "cost": {"bytes_read": len(raw)},
            "loss": [],
            "remainder": [],
            "recovery_path": (
                "re-read portable Zotero artifact " + relative
                + " under the same allowed root"
            ),
        }
        return {
            "status": "COLLECTED",
            "carriers": [carrier],
            "remainder": [],
            "cost": {"files_scanned": 1, "bytes_read": len(raw)},
        }

    def collect(self, request_value, context) -> dict[str, Any]:
        options = request_value.get("options", {})
        mode = options.get("mode")
        if mode == "local-api":
            return self._collect_local_api(options, context)
        if mode == "portable":
            return self._collect_portable(options, context)
        raise ValueError("Zotero collection mode must be local-api or portable")
