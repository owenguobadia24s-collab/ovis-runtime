"""Canonical Responses runtime adapter interfaces."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from ovis_event_log import build_child_event, build_root_event, emit_event
from ovis_ids import generate_event_id
from ovis_state_models import EventType, ObjectType

from .config import RuntimeAdapterConfig
from .continuation import build_chained_continuation
from .hooks import RuntimeHooks
from .provider.openai_responses_adapter import OpenAIProviderResult, OpenAIResponsesProviderAdapter
from .types import RuntimeRequest, RuntimeResponse


class ResponsesRuntimeAdapter(Protocol):
    """Canonical runtime adapter boundary for governed model invocation."""

    def invoke(self, request: RuntimeRequest) -> RuntimeResponse:
        """Invoke the runtime adapter with an explicit governed request."""


class PlaceholderResponsesRuntimeAdapter:
    """Placeholder-only adapter with no provider behavior."""

    def invoke(self, request: RuntimeRequest) -> RuntimeResponse:
        raise NotImplementedError("CJ-004 scaffold only: no Responses runtime implementation.")


class RuntimeAdapter:
    """Canonical runtime adapter implementation for provider-mediated invocation."""

    def __init__(
        self,
        config: RuntimeAdapterConfig,
        hooks: RuntimeHooks | None = None,
        provider_adapter: OpenAIResponsesProviderAdapter | None = None,
    ) -> None:
        self._config = config
        self._hooks = hooks or RuntimeHooks()
        self._provider_adapter = provider_adapter or OpenAIResponsesProviderAdapter()

    def invoke(self, request: RuntimeRequest) -> RuntimeResponse:
        self._validate_turn_context(request)
        requested_event = self._emit_runtime_requested(request)
        try:
            provider_result = self._provider_adapter.invoke(request=request, config=self._config)
            response = self._map_runtime_response(request, provider_result)
            self._emit_runtime_response_received(requested_event, request, provider_result)
            return response
        except Exception as exc:
            self._emit_runtime_error(requested_event, request, exc)
            raise

    def _validate_turn_context(self, request: RuntimeRequest) -> None:
        if not request.turn_context.branch_id.startswith("br_"):
            raise ValueError("RuntimeRequest.turn_context.branch_id must use the canonical br_ prefix.")
        if not request.turn_context.correlation_id.startswith("corr_"):
            raise ValueError("RuntimeRequest.turn_context.correlation_id must use the canonical corr_ prefix.")

    def _map_runtime_response(
        self,
        request: RuntimeRequest,
        provider_result: OpenAIProviderResult,
    ) -> RuntimeResponse:
        continuation = None
        if provider_result.provider_response_id:
            continuation = build_chained_continuation(
                previous_response_id=provider_result.provider_response_id,
                branch_id=request.turn_context.branch_id,
                correlation_id=request.turn_context.correlation_id,
            )
        return RuntimeResponse(
            response_id=None,
            provider_name=provider_result.provider_name,
            output_text=provider_result.output_text,
            continuation=continuation,
            provider_response_ref=provider_result.provider_response_id,
            finish_reason=provider_result.finish_reason,
            gateway_requests=(),
        )

    def _emit_runtime_requested(self, request: RuntimeRequest) -> dict[str, object] | None:
        if not self._config.emit_events or self._hooks.event_writer is None:
            return None
        event = build_root_event(
            event_id=generate_event_id(),
            event_type=EventType.RUNTIME_REQUESTED,
            correlation_id=request.turn_context.correlation_id,
            object_type=ObjectType.BRANCH,
            object_id=request.turn_context.branch_id,
            branch_id=request.turn_context.branch_id,
            actor_type="system",
            actor_id="ovis_runtime",
            created_at=datetime.now(UTC),
            payload_inline={
                "provider": "openai",
                "model": self._config.model.model_name,
                "has_input": bool(request.input_payload),
            },
        )
        return emit_event(event, self._hooks.event_writer)

    def _emit_runtime_response_received(
        self,
        requested_event: dict[str, object] | None,
        request: RuntimeRequest,
        provider_result: OpenAIProviderResult,
    ) -> None:
        if requested_event is None or self._hooks.event_writer is None:
            return
        parent_event_id = str(requested_event["event_id"])
        parent_event = build_root_event(
            event_id=parent_event_id,
            event_type=EventType.RUNTIME_REQUESTED,
            correlation_id=request.turn_context.correlation_id,
            object_type=ObjectType.BRANCH,
            object_id=request.turn_context.branch_id,
            branch_id=request.turn_context.branch_id,
            actor_type="system",
            actor_id="ovis_runtime",
            created_at=datetime.now(UTC),
            payload_inline={
                "provider": "openai",
                "model": self._config.model.model_name,
                "has_input": bool(request.input_payload),
            },
        )
        event = build_child_event(
            parent_event=parent_event,
            event_id=generate_event_id(),
            event_type=EventType.RUNTIME_RESPONSE_RECEIVED,
            object_type=ObjectType.BRANCH,
            object_id=request.turn_context.branch_id,
            actor_type="system",
            actor_id="ovis_runtime",
            created_at=datetime.now(UTC),
            payload_inline={
                "provider": provider_result.provider_name,
                "provider_response_id": provider_result.provider_response_id,
                "output_count": 1 if provider_result.output_text else 0,
                "finish_reason": provider_result.finish_reason,
            },
        )
        emit_event(event, self._hooks.event_writer)

    def _emit_runtime_error(
        self,
        requested_event: dict[str, object] | None,
        request: RuntimeRequest,
        exc: Exception,
    ) -> None:
        if requested_event is None or self._hooks.event_writer is None:
            return
        parent_event_id = str(requested_event["event_id"])
        parent_event = build_root_event(
            event_id=parent_event_id,
            event_type=EventType.RUNTIME_REQUESTED,
            correlation_id=request.turn_context.correlation_id,
            object_type=ObjectType.BRANCH,
            object_id=request.turn_context.branch_id,
            branch_id=request.turn_context.branch_id,
            actor_type="system",
            actor_id="ovis_runtime",
            created_at=datetime.now(UTC),
            payload_inline={
                "provider": "openai",
                "model": self._config.model.model_name,
                "has_input": bool(request.input_payload),
            },
        )
        event = build_child_event(
            parent_event=parent_event,
            event_id=generate_event_id(),
            event_type=EventType.RUNTIME_ERROR,
            object_type=ObjectType.BRANCH,
            object_id=request.turn_context.branch_id,
            actor_type="system",
            actor_id="ovis_runtime",
            created_at=datetime.now(UTC),
            payload_inline={
                "provider": "openai",
                "error_type": type(exc).__name__,
                "message": str(exc),
            },
        )
        emit_event(event, self._hooks.event_writer)
