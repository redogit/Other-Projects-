from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fkdb_tool_carrier import validate_tool_carrier


COLLECTION_SCHEMA = "fkdb/local-tool-collection/v1"
VALID_COLLECTION_STATUSES = frozenset({"COLLECTED", "PARTIAL", "UNAVAILABLE"})


def _within(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class AdapterContext:
    policy: Any
    resolved_root: Path | None
    max_files: int
    max_bytes: int

    def resolve_read_path(self, path: Path) -> Path:
        resolved = self.policy.resolve_allowed_path(Path(path), "READ")
        if self.resolved_root is not None and not _within(resolved, self.resolved_root):
            raise PermissionError("adapter path is outside requested collection root")
        return resolved


class LocalAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, Any] = {}

    def register(self, adapter: Any) -> None:
        tool_id = getattr(adapter, "tool_id", None)
        if not isinstance(tool_id, str) or not tool_id:
            raise ValueError("adapter tool_id must be a non-empty string")
        if tool_id in self._adapters:
            raise ValueError(f"duplicate adapter id: {tool_id}")
        descriptor = getattr(adapter, "descriptor", None)
        collect = getattr(adapter, "collect", None)
        if not callable(descriptor) or not callable(collect):
            raise ValueError("adapter must define descriptor() and collect()")
        self._adapters[tool_id] = adapter

    def known_tool_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))

    def descriptors(self, policy: Any) -> list[dict[str, Any]]:
        descriptors: list[dict[str, Any]] = []
        for tool_id in sorted(self._adapters):
            if hasattr(policy, "adapter_enabled") and not policy.adapter_enabled(tool_id):
                continue
            descriptor = self._adapters[tool_id].descriptor(
                AdapterContext(
                    policy=policy,
                    resolved_root=None,
                    max_files=policy.adapter_max_files,
                    max_bytes=policy.adapter_max_bytes,
                )
            )
            if not isinstance(descriptor, dict):
                raise ValueError(f"adapter {tool_id} descriptor must be an object")
            if descriptor.get("tool_id") != tool_id:
                raise ValueError(f"adapter {tool_id} descriptor changed tool_id")
            descriptors.append(dict(descriptor))
        return descriptors

    def collect(
        self,
        tool_id: str,
        request_value: dict[str, Any],
        policy: Any,
    ) -> dict[str, Any]:
        if not isinstance(tool_id, str) or not tool_id:
            raise ValueError("tool_id must be a non-empty string")
        if not isinstance(request_value, dict):
            raise ValueError("collection request must be an object")

        adapter = self._adapters.get(tool_id)
        if adapter is None:
            return {
                "schema": COLLECTION_SCHEMA,
                "tool_id": tool_id,
                "status": "UNAVAILABLE",
                "carriers": [],
                "remainder": ["LOCAL_ADAPTER_UNAVAILABLE"],
                "cost": {"files_scanned": 0, "bytes_read": 0},
            }

        root_value = request_value.get("root")
        resolved_root: Path | None = None
        if root_value is not None:
            if not isinstance(root_value, str) or not root_value:
                raise ValueError("collection root must be a non-empty string")
            resolved_root = policy.resolve_allowed_path(Path(root_value), "READ")
            if not resolved_root.is_dir():
                raise ValueError("collection root must be an allowed directory")

        options = request_value.get("options", {})
        if not isinstance(options, dict):
            raise ValueError("collection options must be an object")

        context = AdapterContext(
            policy=policy,
            resolved_root=resolved_root,
            max_files=policy.adapter_max_files,
            max_bytes=policy.adapter_max_bytes,
        )
        raw_result = adapter.collect(
            {
                "root": str(resolved_root) if resolved_root is not None else None,
                "options": dict(options),
            },
            context,
        )
        if not isinstance(raw_result, dict):
            raise ValueError(f"adapter {tool_id} result must be an object")

        status = raw_result.get("status")
        if status not in VALID_COLLECTION_STATUSES:
            raise ValueError(f"adapter {tool_id} returned invalid status")

        raw_carriers = raw_result.get("carriers")
        if not isinstance(raw_carriers, list):
            raise ValueError(f"adapter {tool_id} carriers must be a list")
        validated_carriers = [
            validate_tool_carrier(
                value,
                max_payload_bytes=context.max_bytes,
            )
            for value in raw_carriers
        ]

        remainder = raw_result.get("remainder")
        if not isinstance(remainder, list) or not all(
            isinstance(item, str) and item for item in remainder
        ):
            raise ValueError(f"adapter {tool_id} remainder must be a string list")

        cost = raw_result.get("cost")
        if not isinstance(cost, dict):
            raise ValueError(f"adapter {tool_id} cost must be an object")
        files_scanned = cost.get("files_scanned")
        bytes_read = cost.get("bytes_read")
        if type(files_scanned) is not int or files_scanned < 0:
            raise ValueError("adapter files_scanned must be a non-negative integer")
        if type(bytes_read) is not int or bytes_read < 0:
            raise ValueError("adapter bytes_read must be a non-negative integer")
        if files_scanned > context.max_files:
            raise ValueError("adapter files_scanned exceeds configured bound")
        if bytes_read > context.max_bytes:
            raise ValueError("adapter bytes_read exceeds configured bound")

        return {
            "schema": COLLECTION_SCHEMA,
            "tool_id": tool_id,
            "status": status,
            "carriers": validated_carriers,
            "remainder": list(remainder),
            "cost": {
                "files_scanned": files_scanned,
                "bytes_read": bytes_read,
            },
        }



def build_default_registry() -> LocalAdapterRegistry:
    registry = LocalAdapterRegistry()

    # Known adapters are registered in code but remain unavailable to the bridge
    # unless local-tool-policy.json explicitly enables their tool_id.
    from fkdb_adapter_mathbox import MathboxAdapter
    from fkdb_adapter_superpowers import SuperpowersAdapter
    from fkdb_adapter_zotero import ZoteroAdapter

    registry.register(MathboxAdapter())
    registry.register(SuperpowersAdapter())
    registry.register(ZoteroAdapter())
    return registry
