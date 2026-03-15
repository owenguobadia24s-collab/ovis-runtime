"""Schema loader scaffolds for the OVIS tool gateway."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SchemaHandle:
    schema_ref: str
    source: str


class SchemaLoader(Protocol):
    def load_schema(self, schema_ref: str) -> SchemaHandle:
        """Resolve a schema reference for a capability definition."""


class PlaceholderSchemaLoader:
    """Placeholder-only schema loader used by the scaffold."""

    def load_schema(self, schema_ref: str) -> SchemaHandle:
        raise NotImplementedError("CJ-001 scaffold only: no schema loading implementation.")
