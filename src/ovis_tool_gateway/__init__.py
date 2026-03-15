"""Scaffold-only OVIS tool gateway package."""

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
    "CapabilityDefinition",
    "CapabilityRegistry",
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
    "placeholder_result",
]
