"""Canonical Responses runtime adapter scaffold for OVIS."""

from .adapter import PlaceholderResponsesRuntimeAdapter, ResponsesRuntimeAdapter
from .config import RuntimeAdapterConfig, RuntimeModelConfig, RuntimeSessionConfig
from .continuation import build_chained_continuation, build_root_continuation, has_explicit_continuation
from .hooks import RuntimeHooks
from .session import SessionMode, default_session_config
from .types import RuntimeContinuationRef, RuntimeRequest, RuntimeResponse, RuntimeTurnContext

__all__ = [
    "PlaceholderResponsesRuntimeAdapter",
    "ResponsesRuntimeAdapter",
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
