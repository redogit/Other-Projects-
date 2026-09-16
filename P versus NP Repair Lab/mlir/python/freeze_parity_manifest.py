"""Build canonical, provenance-preserving parity manifests for PNP MLIR migration."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def build_manifest(records: Iterable[Mapping[str, Any]], metadata: Mapping[str, Any]) -> dict[str, Any]:
    ordered = sorted((dict(record) for record in records), key=lambda item: item["path"])
    return {
        "schema": "pnp-mlir-parity-v1",
        "metadata": dict(sorted(metadata.items())),
        "records": ordered,
    }


def write_manifest(path: Path, records: Iterable[Mapping[str, Any]], metadata: Mapping[str, Any]) -> dict[str, Any]:
    manifest = build_manifest(records, metadata)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_dumps(manifest), encoding="utf-8")
    return manifest
