from __future__ import annotations

from collections.abc import Callable

from core import PartSpec


class PartCatalog:
    def __init__(self) -> None:
        self._entries: dict[tuple[str, int], tuple[PartSpec, Callable]] = {}

    def register(self, spec: PartSpec, factory: Callable) -> None:
        if not isinstance(spec, PartSpec):
            raise ValueError("catalog accepts PartSpec records")
        if not callable(factory):
            raise ValueError("factory must be callable")
        key = (spec.stable_id, spec.version)
        if key in self._entries:
            raise ValueError(f"duplicate part version: {key}")
        self._entries[key] = (spec, factory)

    def get(self, stable_id: str, version: int) -> PartSpec:
        try:
            return self._entries[(stable_id, version)][0]
        except KeyError as exc:
            raise KeyError(f"unknown part: {(stable_id, version)}") from exc

    def factory(self, stable_id: str, version: int):
        try:
            return self._entries[(stable_id, version)][1]
        except KeyError as exc:
            raise KeyError(f"unknown part: {(stable_id, version)}") from exc

    def ordered_specs(self) -> tuple[PartSpec, ...]:
        return tuple(self._entries[key][0] for key in sorted(self._entries))
