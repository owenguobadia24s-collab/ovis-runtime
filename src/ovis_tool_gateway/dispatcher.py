"""Canonical governed dispatcher for OVIS capability execution."""

from __future__ import annotations

from datetime import UTC, datetime

from ovis_event_log import AppendOnlyEventWriter, build_child_event, build_root_event, emit_event
from ovis_ids import generate_event_id
from ovis_state_models import ActorType, Event, EventType, ObjectType

from .envelopes import build_blocked_envelope, build_error_envelope, build_success_envelope
from .executor import ExecutionWrapper
from .policy_hooks import PolicyHook
from .registry import CapabilityRegistry
from .types import CapabilityDefinition, ExecutionRequest, ExecutionResultEnvelope, PolicyDecision

_DISPATCHER_ACTOR_ID = "ovis_tool_gateway.dispatcher"


class CapabilityDispatcher(ExecutionWrapper):
    """Minimal governed capability dispatcher."""

    def __init__(
        self,
        *,
        registry: CapabilityRegistry,
        policy_hook: PolicyHook | None = None,
        event_writer: AppendOnlyEventWriter | None = None,
    ) -> None:
        self._registry = registry
        self._policy_hook = policy_hook
        self._event_writer = event_writer

    def execute(self, request: ExecutionRequest) -> ExecutionResultEnvelope:
        try:
            self._validate_request(request)
        except ValueError as exc:
            self._emit_error_event(request=request, error_type="ValueError", message=str(exc))
            return self._error_envelope(request=request, error_details=str(exc), policy_disposition="defer")

        try:
            definition, handler = self._registry.resolve(request.capability_name)
        except KeyError as exc:
            message = str(exc)
            self._emit_error_event(request=request, error_type="ResolutionError", message=message)
            return self._error_envelope(request=request, error_details=message, policy_disposition="defer")

        requested_event = self._emit_requested_event(request)

        policy_decision = self._evaluate_policy(request, definition)
        if policy_decision is not None and policy_decision.disposition in {"deny", "defer"}:
            self._emit_error_event(
                request=request,
                parent_event=requested_event,
                error_type="PolicyBlocked",
                message=policy_decision.rationale,
            )
            return build_blocked_envelope(
                capability_name=request.capability_name,
                correlation_id=request.correlation_id,
                policy_disposition=policy_decision.disposition,
                object_refs=request.object_context,
                branch_ref=request.branch_context.get("branch_id"),
                error_details=policy_decision.rationale,
            )

        policy_disposition = "allow" if policy_decision is not None else "defer"

        try:
            result_payload = handler(dict(request.input_payload))
        except Exception as exc:
            self._emit_error_event(
                request=request,
                parent_event=requested_event,
                error_type=type(exc).__name__,
                message=str(exc),
            )
            return self._error_envelope(
                request=request,
                error_details=str(exc),
                policy_disposition=policy_disposition,
            )

        self._emit_completed_event(request=request, parent_event=requested_event)
        return build_success_envelope(
            capability_name=request.capability_name,
            correlation_id=request.correlation_id,
            policy_disposition=policy_disposition,
            object_refs=request.object_context,
            branch_ref=request.branch_context.get("branch_id"),
            result_payload=result_payload,
        )

    def _validate_request(self, request: ExecutionRequest) -> None:
        if not request.capability_name:
            raise ValueError("ExecutionRequest.capability_name is required.")
        if not request.correlation_id or not request.correlation_id.startswith("corr_"):
            raise ValueError("ExecutionRequest.correlation_id must use the corr_ prefix.")
        branch_id = request.branch_context.get("branch_id")
        if branch_id is not None and not branch_id.startswith("br_"):
            raise ValueError("ExecutionRequest.branch_context['branch_id'] must use the br_ prefix.")

    def _evaluate_policy(
        self,
        request: ExecutionRequest,
        definition: CapabilityDefinition,
    ) -> PolicyDecision | None:
        if self._policy_hook is None:
            return None
        return self._policy_hook.evaluate(request, definition)

    def _error_envelope(
        self,
        *,
        request: ExecutionRequest,
        error_details: str,
        policy_disposition: str,
    ) -> ExecutionResultEnvelope:
        return build_error_envelope(
            capability_name=request.capability_name,
            correlation_id=request.correlation_id,
            policy_disposition=policy_disposition,
            object_refs=request.object_context,
            branch_ref=request.branch_context.get("branch_id"),
            error_details=error_details,
        )

    def _emit_requested_event(self, request: ExecutionRequest) -> Event | None:
        return self._emit_event(
            request=request,
            event_type=EventType.CAPABILITY_REQUESTED,
            payload_inline={
                "capability_name": request.capability_name,
                "has_args": bool(request.input_payload),
            },
        )

    def _emit_completed_event(self, *, request: ExecutionRequest, parent_event: Event | None) -> Event | None:
        return self._emit_event(
            request=request,
            event_type=EventType.CAPABILITY_COMPLETED,
            payload_inline={
                "capability_name": request.capability_name,
                "success": True,
            },
            parent_event=parent_event,
        )

    def _emit_error_event(
        self,
        *,
        request: ExecutionRequest,
        error_type: str,
        message: str,
        parent_event: Event | None = None,
    ) -> Event | None:
        return self._emit_event(
            request=request,
            event_type=EventType.CAPABILITY_ERROR,
            payload_inline={
                "capability_name": request.capability_name,
                "error_type": error_type,
                "message": message,
            },
            parent_event=parent_event,
        )

    def _emit_event(
        self,
        *,
        request: ExecutionRequest,
        event_type: EventType,
        payload_inline: dict[str, object],
        parent_event: Event | None = None,
    ) -> Event | None:
        if self._event_writer is None:
            return None

        branch_id = request.branch_context.get("branch_id")
        if branch_id is None:
            return None
        if not request.correlation_id.startswith("corr_"):
            return None
        if not branch_id.startswith("br_"):
            return None

        created_at = datetime.now(UTC)
        if parent_event is None:
            event = build_root_event(
                event_id=generate_event_id(),
                event_type=event_type,
                correlation_id=request.correlation_id,
                object_type=ObjectType.EVENT,
                object_id=request.capability_name,
                branch_id=branch_id,
                actor_type=ActorType.TOOL,
                actor_id=_DISPATCHER_ACTOR_ID,
                created_at=created_at,
                payload_inline=payload_inline,
            )
        else:
            event = build_child_event(
                parent_event=parent_event,
                event_id=generate_event_id(),
                event_type=event_type,
                object_type=ObjectType.EVENT,
                object_id=request.capability_name,
                actor_type=ActorType.TOOL,
                actor_id=_DISPATCHER_ACTOR_ID,
                created_at=created_at,
                payload_inline=payload_inline,
            )

        emit_event(event, self._event_writer)
        return event
