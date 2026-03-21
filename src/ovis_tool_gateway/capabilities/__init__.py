# ---
# id: MODULE-GATEWAY-0002
# title: Capabilities Package Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gateway
# repo: ovis-runtime
# path: src/ovis_tool_gateway/capabilities/__init__.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GATEWAY-0002.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
"""Capability registration helpers for the canonical tool gateway."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..registry import CapabilityRegistry
from ..types import CapabilityDefinition, SideEffectClass

DEFAULT_CAPABILITY_REGISTRY = CapabilityRegistry()


def capability(
    name: str,
    *,
    version: str = "v1",
    schema_ref: str = "",
    side_effect_class: SideEffectClass = "read-only",
    registry: CapabilityRegistry | None = None,
) -> Callable[[Callable[[dict[str, Any]], Any]], Callable[[dict[str, Any]], Any]]:
    """Register a callable capability under a canonical name."""

    target_registry = registry or DEFAULT_CAPABILITY_REGISTRY

    def decorator(handler: Callable[[dict[str, Any]], Any]) -> Callable[[dict[str, Any]], Any]:
        definition = CapabilityDefinition(
            name=name,
            version=version,
            schema_ref=schema_ref,
            side_effect_class=side_effect_class,
        )
        target_registry.register(definition, handler=handler)
        return handler

    return decorator
