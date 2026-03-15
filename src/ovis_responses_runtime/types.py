"""Shared request and response types for the runtime adapter scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from ovis_tool_gateway.types import ExecutionRequest

from .session import SessionMode


@dataclass(frozen=True)
class RuntimeTurnContext:
    """Canonical branch and object context for one runtime turn."""

    branch_id: str
    correlation_id: str
    object_context: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeContinuationRef:
    """Explicit response-chaining reference for governed continuation."""

    previous_response_id: str | None
    branch_id: str
    correlation_id: str


@dataclass(frozen=True)
class RuntimeRequest:
    """Thin runtime request envelope for the canonical adapter surface."""

    input_payload: Mapping[str, Any]
    turn_context: RuntimeTurnContext
    continuation: RuntimeContinuationRef | None = None
    session_mode_override: SessionMode | None = None


@dataclass(frozen=True)
class RuntimeResponse:
    """Thin runtime response envelope for the canonical adapter surface."""

    response_id: str | None
    output_text: str
    continuation: RuntimeContinuationRef | None
    provider_response_ref: str | None = None
    gateway_requests: tuple[ExecutionRequest, ...] = ()
