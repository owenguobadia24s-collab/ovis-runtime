"""Registry surface for scaffolded capability definitions."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from .types import CapabilityDefinition


class CapabilityRegistry:
    """In-memory registry for scaffolded capability definitions only."""

    def __init__(self, definitions: Iterable[CapabilityDefinition] | None = None) -> None:
        self._definitions: dict[str, CapabilityDefinition] = {}
        self._handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}
        for definition in definitions or ():
            self.register(definition)

    def register(
        self,
        definition: CapabilityDefinition,
        handler: Callable[[dict[str, Any]], Any] | None = None,
    ) -> None:
        if definition.name in self._definitions:
            raise ValueError(f"Capability already registered: {definition.name}")
        self._definitions[definition.name] = definition
        if handler is not None:
            self._handlers[definition.name] = handler

    def get(self, name: str) -> CapabilityDefinition | None:
        return self._definitions.get(name)

    def get_handler(self, name: str) -> Callable[[dict[str, Any]], Any] | None:
        return self._handlers.get(name)

    def resolve(self, name: str) -> tuple[CapabilityDefinition, Callable[[dict[str, Any]], Any]]:
        definition = self.get(name)
        if definition is None:
            raise KeyError(f"Unknown capability: {name}")
        handler = self.get_handler(name)
        if handler is None:
            raise KeyError(f"No handler registered for capability: {name}")
        return definition, handler

    def list(self) -> tuple[CapabilityDefinition, ...]:
        return tuple(self._definitions.values())
