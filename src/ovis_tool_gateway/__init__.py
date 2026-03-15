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
