from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import mimetypes
import os
from pathlib import Path
import secrets
import socket
import subprocess
import threading
import time
from typing import Any
from urllib.parse import unquote, urlsplit

from fkdb_tool_carrier import sha256_hex, validate_tool_carrier


POLICY_SCHEMA = "fkdb/local-tool-policy/v1"
STATUS_SCHEMA = "fkdb/local-tool-bridge-status/v1"
IMPORT_SCHEMA = "fkdb/local-tool-bridge-import/v1"
RUN_SCHEMA = "fkdb/local-tool-bridge-run/v1"


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _is_loopback_literal(value: str) -> bool:
    try:
        return ipaddress.ip_address(value).is_loopback
    except ValueError:
        return False


def _canonical_payload_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _within(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class ProcessGrant:
    tool_id: str
    executable: Path
    argv: tuple[str, ...]
    cwd: Path
    time_limit: float
    memory_limit: int
    environment_allowlist: tuple[str, ...]
    network_policy: str
    shell: bool = False


@dataclass
class BridgeReceipt:
    bind: str
    port: int
    origin: str
    token: str
    network_policy: str
    started_at: str
    _server: ThreadingHTTPServer = field(repr=False)
    _thread: threading.Thread = field(repr=False)

    def shutdown(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": STATUS_SCHEMA,
            "state": "AVAILABLE",
            "origin": self.origin,
            "network_policy": self.network_policy,
            "started_at": self.started_at,
        }


class BridgePolicy:
    def __init__(self, value: dict[str, Any]):
        self._value = value
        self.schema = value["schema"]
        self.network_policy = value["network_policy"]
        self.read_roots = tuple(Path(p).resolve() for p in value["read_roots"])
        self.write_roots = tuple(Path(p).resolve() for p in value["write_roots"])
        self.processes = tuple(value["processes"])
        self.max_import_bytes = value["max_import_bytes"]
        self.max_request_bytes = value["max_request_bytes"]
        self.environment_allowlist = tuple(value["environment_allowlist"])

    @classmethod
    def load(cls, path: Path) -> "BridgePolicy":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BridgePolicy":
        if not isinstance(value, dict):
            raise ValueError("local tool policy must be an object")
        if value.get("schema") != POLICY_SCHEMA:
            raise ValueError("unsupported local tool policy schema")
        if value.get("network_policy") != "LOOPBACK_ONLY":
            raise ValueError("Plan A local tool policy must be LOOPBACK_ONLY")

        normalized = dict(value)
        for field_name in (
            "read_roots",
            "write_roots",
            "processes",
            "environment_allowlist",
        ):
            item = normalized.get(field_name)
            if not isinstance(item, list):
                raise ValueError(f"{field_name} must be a list")

        for field_name in ("max_import_bytes", "max_request_bytes"):
            item = normalized.get(field_name)
            if type(item) is not int or item <= 0:
                raise ValueError(f"{field_name} must be a positive integer")

        for root_field in ("read_roots", "write_roots"):
            for root in normalized[root_field]:
                if not isinstance(root, str) or not root:
                    raise ValueError(f"{root_field} entries must be non-empty strings")

        for env_name in normalized["environment_allowlist"]:
            if not isinstance(env_name, str) or not env_name:
                raise ValueError("environment_allowlist entries must be non-empty strings")

        for process in normalized["processes"]:
            cls._validate_process_entry(process)

        return cls(normalized)

    @staticmethod
    def _validate_process_entry(process: Any) -> None:
        if not isinstance(process, dict):
            raise ValueError("process allowlist entry must be an object")
        required = (
            "tool_id",
            "executable",
            "allowed_subcommands",
            "working_roots",
            "read_roots",
            "write_roots",
            "network_policy",
            "time_limit",
            "memory_limit",
            "environment_allowlist",
        )
        missing = [field_name for field_name in required if field_name not in process]
        if missing:
            raise ValueError("process allowlist entry missing: " + ", ".join(missing))
        if not isinstance(process["tool_id"], str) or not process["tool_id"]:
            raise ValueError("process tool_id must be non-empty")
        if not isinstance(process["executable"], str) or not process["executable"]:
            raise ValueError("process executable must be non-empty")
        for field_name in (
            "allowed_subcommands",
            "working_roots",
            "read_roots",
            "write_roots",
            "environment_allowlist",
        ):
            if not isinstance(process[field_name], list):
                raise ValueError(f"process {field_name} must be a list")
        if not process["allowed_subcommands"]:
            raise ValueError("process allowed_subcommands must not be empty")
        if process["network_policy"] != "LOOPBACK_ONLY":
            raise ValueError("process network_policy must be LOOPBACK_ONLY")
        if not isinstance(process["time_limit"], (int, float)) or process["time_limit"] <= 0:
            raise ValueError("process time_limit must be positive")
        if type(process["memory_limit"]) is not int or process["memory_limit"] < 0:
            raise ValueError("process memory_limit must be a non-negative integer")

    def resolve_allowed_path(self, path: Path, mode: str) -> Path:
        mode = mode.upper()
        roots = self.read_roots if mode == "READ" else self.write_roots if mode == "WRITE" else None
        if roots is None:
            raise ValueError("mode must be READ or WRITE")
        candidate = Path(path).resolve(strict=False)
        if not any(_within(candidate, root) for root in roots):
            raise PermissionError(f"path is outside allowed {mode.lower()} roots")
        return candidate

    def validate_loopback_url(self, url: str) -> str:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("local tool URL must use http or https")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("credentials are not allowed in local tool URLs")
        hostname = parsed.hostname
        if not hostname or not _is_loopback_literal(hostname):
            raise ValueError("local tool URL host must be a literal loopback address")
        return url

    def validate_process(self, executable: Path, argv: list[str]) -> ProcessGrant:
        executable_path = Path(executable).resolve(strict=False)
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) for x in argv):
            raise PermissionError("process argv must be a non-empty string vector")

        for process in self.processes:
            configured = Path(process["executable"]).resolve(strict=False)
            if executable_path != configured:
                continue
            raw_subcommand = argv[0]
            allowed = False
            for configured_subcommand in process["allowed_subcommands"]:
                if raw_subcommand == configured_subcommand:
                    allowed = True
                    break
                raw_path = Path(raw_subcommand)
                configured_path = Path(configured_subcommand)
                if raw_path.is_absolute() and configured_path.is_absolute():
                    raw_identity = os.path.normcase(str(raw_path.resolve(strict=False)))
                    configured_identity = os.path.normcase(
                        str(configured_path.resolve(strict=False))
                    )
                    if raw_identity == configured_identity:
                        allowed = True
                        break
            if not allowed:
                raise PermissionError("process subcommand is not allowlisted")

            working_roots = tuple(Path(p).resolve() for p in process["working_roots"])
            if not working_roots:
                raise PermissionError("process has no allowlisted working root")
            cwd = working_roots[0]

            first = Path(argv[0])
            if first.is_absolute():
                resolved_subcommand = first.resolve(strict=False)
                read_roots = tuple(Path(p).resolve() for p in process["read_roots"])
                if read_roots and not any(
                    _within(resolved_subcommand, root) for root in read_roots
                ):
                    raise PermissionError("process subcommand is outside read roots")

            env_allowlist = tuple(
                name
                for name in process["environment_allowlist"]
                if name in self.environment_allowlist
            )
            return ProcessGrant(
                tool_id=process["tool_id"],
                executable=executable_path,
                argv=tuple(argv),
                cwd=cwd,
                time_limit=float(process["time_limit"]),
                memory_limit=process["memory_limit"],
                environment_allowlist=env_allowlist,
                network_policy=process["network_policy"],
                shell=False,
            )

        raise PermissionError("process executable is not allowlisted")

    def tool_descriptors(self) -> list[dict[str, Any]]:
        return [
            {
                "tool_id": process["tool_id"],
                "locality": "LOCAL_PROCESS",
                "state": "AVAILABLE",
                "capabilities": ["LOCAL_PROCESS"],
                "network_policy": process["network_policy"],
            }
            for process in self.processes
        ]


def _bounded_text(text: str, limit: int) -> tuple[str, bool]:
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text, False
    clipped = encoded[:limit]
    return clipped.decode("utf-8", errors="ignore"), True


def _process_carrier(
    grant: ProcessGrant,
    completed: subprocess.CompletedProcess[str],
    duration_ms: int,
    obligation: str,
    max_payload_bytes: int,
) -> dict[str, Any]:
    stdout, stdout_truncated = _bounded_text(completed.stdout or "", max_payload_bytes // 2)
    stderr, stderr_truncated = _bounded_text(completed.stderr or "", max_payload_bytes // 2)
    payload = {
        "executable": str(grant.executable),
        "argv": list(grant.argv),
        "cwd": str(grant.cwd),
        "shell": False,
        "exit_code": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "duration_ms": duration_ms,
    }
    payload_bytes = _canonical_payload_bytes(payload)
    remainder: list[str] = []
    loss: list[str] = []
    if stdout_truncated:
        loss.append("STDOUT_TRUNCATED")
    if stderr_truncated:
        loss.append("STDERR_TRUNCATED")
    if grant.network_policy == "LOOPBACK_ONLY":
        remainder.append(
            "PROCESS_NETWORK_POLICY_NOT_ENFORCED_BY_PORTABLE_STDLIB_BRIDGE"
        )
    if grant.memory_limit:
        remainder.append("MEMORY_LIMIT_NOT_ENFORCED_BY_PORTABLE_STDLIB_BRIDGE")

    value = {
        "schema": "fkdb/tool-carrier/v1",
        "carrier_id": "process-" + secrets.token_hex(16),
        "tool_id": grant.tool_id,
        "tool_version": "unknown",
        "adapter_kind": "LOCAL_PROCESS",
        "locality": "LOCAL_PROCESS",
        "source_identity": "local-process:" + grant.tool_id,
        "source_version": str(grant.executable),
        "retrieved_at": _utc_now(),
        "payload_type": "application/vnd.fkdb.local-process+json",
        "payload": payload,
        "content_hash": sha256_hex(payload_bytes),
        "provenance": {
            "executable": str(grant.executable),
            "argv": list(grant.argv),
            "cwd": str(grant.cwd),
        },
        "authority_scope": "LOCAL_PROCESS_EXECUTION_ONLY",
        "evidence_status": "EXECUTION_RECEIPT_NOT_CLAIM_VERIFICATION",
        "obligation": obligation,
        "relations": [],
        "cost": {"duration_ms": duration_ms},
        "loss": loss,
        "remainder": remainder,
        "recovery_path": "rerun only with the same explicit local process grant",
    }
    return validate_tool_carrier(value, max_payload_bytes=max_payload_bytes)


class _BridgeHTTPServer(ThreadingHTTPServer):
    daemon_threads = True


class _BridgeHTTPServerV6(_BridgeHTTPServer):
    address_family = socket.AF_INET6


class _BridgeHandler(BaseHTTPRequestHandler):
    server_version = "FKDBLocalToolBridge/1"

    def log_message(self, format: str, *args: Any) -> None:
        # Deliberately suppress request/header logging; the capability token must not leak.
        return

    @property
    def _bridge(self) -> ThreadingHTTPServer:
        return self.server

    def _send_json(self, status: int, value: Any) -> None:
        raw = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _deny(self, status: int, message: str) -> None:
        self._send_json(status, {"status": "DENIED", "error": message})

    def _read_json_body(self) -> dict[str, Any]:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise ValueError("Content-Length is required")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        max_request = self._bridge.fkdb_policy.max_request_bytes  # type: ignore[attr-defined]
        if length < 0 or length > max_request:
            raise ValueError("request body exceeds configured bound")
        raw = self.rfile.read(length)
        if len(raw) != length:
            raise ValueError("truncated request body")
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        return value

    def _authorized_post(self) -> bool:
        origin = self.headers.get("Origin")
        if origin != self._bridge.fkdb_origin:  # type: ignore[attr-defined]
            return False
        token = self.headers.get("X-FKDB-Bridge-Token")
        expected = self._bridge.fkdb_token  # type: ignore[attr-defined]
        return isinstance(token, str) and secrets.compare_digest(token, expected)

    def do_GET(self) -> None:
        if self.path == "/fkdb-tool-bridge/v1/status":
            receipt = self._bridge.fkdb_receipt  # type: ignore[attr-defined]
            value = receipt.public_dict()
            value["capabilities"] = [
                "IMPORT_ARTIFACT",
                "LOCAL_PROCESS",
                "LOCALHOST_HTTP",
            ]
            value["tool_count"] = len(
                self._bridge.fkdb_policy.tool_descriptors()  # type: ignore[attr-defined]
            )
            self._send_json(200, value)
            return

        if self.path == "/fkdb-tool-bridge/v1/tools":
            self._send_json(
                200,
                {
                    "schema": "fkdb/local-tool-list/v1",
                    "tools": self._bridge.fkdb_policy.tool_descriptors(),  # type: ignore[attr-defined]
                },
            )
            return

        parsed = urlsplit(self.path)
        relative = unquote(parsed.path)
        if relative == "/":
            relative = "/index.html"
        candidate = (
            self._bridge.fkdb_web_root / relative.lstrip("/")  # type: ignore[attr-defined]
        ).resolve(strict=False)
        root = self._bridge.fkdb_web_root  # type: ignore[attr-defined]
        if not _within(candidate, root) or not candidate.is_file():
            self._deny(404, "not found")
            return
        raw = candidate.read_bytes()
        mime, _ = mimetypes.guess_type(candidate.name)
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self) -> None:
        if not self._authorized_post():
            self._deny(403, "origin or capability token denied")
            return
        try:
            body = self._read_json_body()
            if self.path == "/fkdb-tool-bridge/v1/import":
                raw_carrier = body.get("carrier")
                validated = validate_tool_carrier(
                    raw_carrier,
                    max_payload_bytes=self._bridge.fkdb_policy.max_import_bytes,  # type: ignore[attr-defined]
                )
                self._send_json(
                    200,
                    {
                        "schema": IMPORT_SCHEMA,
                        "status": "ADMITTED",
                        "carrier": validated,
                        "remainder": [],
                    },
                )
                return

            if self.path == "/fkdb-tool-bridge/v1/run":
                executable = body.get("executable")
                argv = body.get("argv")
                obligation = body.get("obligation", "LOCAL_PROCESS_EXECUTION")
                if not isinstance(executable, str) or not executable:
                    raise ValueError("executable must be a non-empty string")
                if not isinstance(argv, list):
                    raise ValueError("argv must be a list")
                if not isinstance(obligation, str) or not obligation:
                    raise ValueError("obligation must be a non-empty string")
                policy = self._bridge.fkdb_policy  # type: ignore[attr-defined]
                grant = policy.validate_process(Path(executable), argv)
                env = {
                    name: os.environ[name]
                    for name in grant.environment_allowlist
                    if name in os.environ
                }
                start = time.monotonic()
                completed = subprocess.run(
                    [str(grant.executable), *grant.argv],
                    cwd=str(grant.cwd),
                    capture_output=True,
                    text=True,
                    shell=False,
                    timeout=grant.time_limit,
                    env=env,
                    check=False,
                )
                duration_ms = int((time.monotonic() - start) * 1000)
                carrier = _process_carrier(
                    grant,
                    completed,
                    duration_ms,
                    obligation,
                    policy.max_import_bytes,
                )
                self._send_json(
                    200,
                    {
                        "schema": RUN_SCHEMA,
                        "status": "EXECUTED",
                        "carrier": carrier,
                    },
                )
                return

            self._deny(404, "unknown bridge endpoint")
        except PermissionError as exc:
            self._deny(403, str(exc))
        except subprocess.TimeoutExpired:
            self._deny(408, "local process exceeded configured time limit")
        except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._deny(400, str(exc))


def run_bridge(
    *,
    bind: str = "127.0.0.1",
    port: int = 0,
    web_root: Path,
    policy: BridgePolicy | None = None,
) -> BridgeReceipt:
    if not _is_loopback_literal(bind):
        raise ValueError("bridge bind address must be a literal loopback address")
    if type(port) is not int or not (0 <= port <= 65535):
        raise ValueError("bridge port must be in [0, 65535]")

    root = Path(web_root).resolve()
    if not root.is_dir():
        raise ValueError("web_root must be an existing directory")

    if policy is None:
        policy_path = (
            Path(__file__).resolve().parent.parent
            / "fkdb"
            / "tools"
            / "local-tool-policy.json"
        )
        policy = BridgePolicy.load(policy_path)

    server_cls = _BridgeHTTPServerV6 if ":" in bind else _BridgeHTTPServer
    server = server_cls((bind, port), _BridgeHandler)
    actual_port = int(server.server_address[1])
    host_for_url = f"[{bind}]" if ":" in bind else bind
    origin = f"http://{host_for_url}:{actual_port}"
    token = secrets.token_urlsafe(32)

    server.fkdb_policy = policy  # type: ignore[attr-defined]
    server.fkdb_web_root = root  # type: ignore[attr-defined]
    server.fkdb_origin = origin  # type: ignore[attr-defined]
    server.fkdb_token = token  # type: ignore[attr-defined]

    thread = threading.Thread(
        target=server.serve_forever,
        name="fkdb-local-tool-bridge",
        daemon=True,
    )
    receipt = BridgeReceipt(
        bind=bind,
        port=actual_port,
        origin=origin,
        token=token,
        network_policy=policy.network_policy,
        started_at=_utc_now(),
        _server=server,
        _thread=thread,
    )
    server.fkdb_receipt = receipt  # type: ignore[attr-defined]
    thread.start()
    return receipt
