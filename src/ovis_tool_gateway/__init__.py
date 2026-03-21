# ---
# id: MODULE-GATEWAY-0001
# title: Ovis Tool Gateway Package Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gateway
# repo: ovis-runtime
# path: src/ovis_tool_gateway/__init__.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GATEWAY-0001.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
"""Scaffold-only OVIS tool gateway package."""

from .capabilities import DEFAULT_CAPABILITY_REGISTRY, capability
from .dispatcher import CapabilityDispatcher
from .envelopes import placeholder_result
from .registry import CapabilityRegistry
from .schema_loader import PlaceholderSchemaLoader, SchemaHandle, SchemaLoader
from .executor import ExecutionWrapper, PlaceholderExecutionWrapper
from .policy_hooks import PolicyHook, PlaceholderPolicyHook
from .types import (
    CapabilityDefinition,
    ExecutionRequest,
    ExecutionResultEnvelope,
    PolicyDecision,
)

__all__ = [
    "CapabilityDispatcher",
    "CapabilityDefinition",
    "CapabilityRegistry",
    "DEFAULT_CAPABILITY_REGISTRY",
    "ExecutionRequest",
    "ExecutionResultEnvelope",
    "ExecutionWrapper",
    "PlaceholderExecutionWrapper",
    "PlaceholderPolicyHook",
    "PlaceholderSchemaLoader",
    "PolicyDecision",
    "PolicyHook",
    "SchemaHandle",
    "SchemaLoader",
    "capability",
    "placeholder_result",
]
