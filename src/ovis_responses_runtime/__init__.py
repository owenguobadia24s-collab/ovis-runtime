# ---
# id: MODULE-RUNTIME-0001
# title: Ovis Responses Runtime Package Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: runtime
# repo: ovis-runtime
# path: src/ovis_responses_runtime/__init__.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-RUNTIME-0001.yaml
# module_id: MOD-RUNTIME-GATEWAY-0001
# module_slug: runtime_gateway
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Canonical Responses runtime adapter scaffold for OVIS."""

from .adapter import PlaceholderResponsesRuntimeAdapter, ResponsesRuntimeAdapter, RuntimeAdapter
from .config import RuntimeAdapterConfig, RuntimeModelConfig, RuntimeSessionConfig
from .continuation import build_chained_continuation, build_root_continuation, has_explicit_continuation
from .hooks import RuntimeHooks
from .provider import OpenAIProviderResult, OpenAIResponsesProviderAdapter
from .session import SessionMode, default_session_config
from .types import RuntimeContinuationRef, RuntimeRequest, RuntimeResponse, RuntimeTurnContext

__all__ = [
    "OpenAIProviderResult",
    "OpenAIResponsesProviderAdapter",
    "PlaceholderResponsesRuntimeAdapter",
    "ResponsesRuntimeAdapter",
    "RuntimeAdapter",
    "RuntimeAdapterConfig",
    "RuntimeContinuationRef",
    "RuntimeHooks",
    "RuntimeModelConfig",
    "RuntimeRequest",
    "RuntimeResponse",
    "RuntimeSessionConfig",
    "RuntimeTurnContext",
    "SessionMode",
    "build_chained_continuation",
    "build_root_continuation",
    "default_session_config",
    "has_explicit_continuation",
]
