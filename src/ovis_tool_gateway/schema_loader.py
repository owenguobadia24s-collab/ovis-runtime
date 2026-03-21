# ---
# id: MODULE-GATEWAY-0008
# title: Schema Loader Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gateway
# repo: ovis-runtime
# path: src/ovis_tool_gateway/schema_loader.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GATEWAY-0008.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
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
