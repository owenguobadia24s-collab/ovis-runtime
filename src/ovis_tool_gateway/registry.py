"""Registry surface for scaffolded capability definitions."""

from __future__ import annotations

from collections.abc import Iterable

from .types import CapabilityDefinition


class CapabilityRegistry:
    """In-memory registry for scaffolded capability definitions only."""

    def __init__(self, definitions: Iterable[CapabilityDefinition] | None = None) -> None:
        self._definitions: dict[str, CapabilityDefinition] = {}
        for definition in definitions or ():
            self.register(definition)

    def register(self, definition: CapabilityDefinition) -> None:
        if definition.name in self._definitions:
            raise ValueError(f"Capability already registered: {definition.name}")
        self._definitions[definition.name] = definition

    def get(self, name: str) -> CapabilityDefinition | None:
        return self._definitions.get(name)

    def list(self) -> tuple[CapabilityDefinition, ...]:
        return tuple(self._definitions.values())
