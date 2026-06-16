# ---
# id: MODULE-GATEWAY-0010
# title: Bridge Dry Run Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gateway
# repo: ovis-runtime
# path: src/ovis_tool_gateway/bridge_dry_run.py
# owner: Owen Vitae
# created: '2026-06-16'
# last_updated: '2026-06-16'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GATEWAY-0010.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
"""Dry-run-only Bridge Action preview service."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ovis_event_log import AppendOnlyEventWriter, EventAppendReceipt, build_root_event
from ovis_ids import generate_event_id, generate_prefixed_id
from ovis_state_models import (
    ActorType,
    BridgeAction,
    BridgeActionId,
    BridgeActionStatus,
    EventType,
    ExecuteJobId,
    ObjectType,
)

from .policy_hooks import PolicyHook
from .types import CapabilityDefinition, ExecutionRequest

_ACTOR_ID = "ovis_bridge_dry_run.service"
_SECRET_MARKERS = (
    ".env",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "token",
    "tokens",
    "private_key",
    ".pem",
    ".key",
)


@dataclass(frozen=True)
class BridgeDryRunRequest:
    execute_job_id: str
    target_system: str
    action_type: str
    payload: Mapping[str, Any]
    correlation_id: str | None = None
    branch_id: str | None = None
    actor_id: str = _ACTOR_ID
    dry_run: bool = True
    policy_context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BridgeDryRunResult:
    allowed: bool
    reason: str
    dry_run: bool
    would_dispatch: bool
    bridge_action: BridgeAction | None
    policy_disposition: str
    event_receipt: EventAppendReceipt | None = None


class BridgeDryRunService:
    """Build local BridgeAction previews without executing external effects."""

    def __init__(
        self,
        *,
        policy_hook: PolicyHook | None = None,
        event_writer: AppendOnlyEventWriter | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._policy_hook = policy_hook
        self._event_writer = event_writer
        self._clock = clock or (lambda: datetime.now(UTC))

    def preview(self, request: BridgeDryRunRequest) -> BridgeDryRunResult:
        target_system = _normalize_token(request.target_system)
        action_type = _normalize_token(request.action_type)
        if not target_system:
            return _blocked(request, "target_system is required.", "defer")
        if not action_type:
            return _blocked(request, "action_type is required.", "defer")
        if not request.dry_run:
            return _blocked(request, "bridge dispatch is disabled; dry_run must be true.", "deny")
        if _has_secret_marker(target_system) or _has_secret_marker(action_type) or _payload_has_secret_key(request.payload):
            return _blocked(request, "secrets or credentials are forbidden in bridge previews.", "deny")
        if _is_ovc_target(target_system, request.payload) and _is_ovis_governance_context(request.policy_context):
            return _blocked(request, "OVC bridge targets are forbidden for OVIS governance jobs.", "deny")

        policy_disposition, policy_reason = self._evaluate_policy(request, target_system, action_type)
        if self._policy_hook is not None and policy_disposition in {"deny", "defer"}:
            return _blocked(request, policy_reason, policy_disposition)

        now = self._clock()
        bridge_action = BridgeAction(
            bridge_action_id=BridgeActionId(generate_prefixed_id("bridge_")),
            execute_job_id=ExecuteJobId(request.execute_job_id),
            target_system=target_system,
            action_type=action_type,
            status=BridgeActionStatus.PENDING,
            request_ref=None,
            response_ref=None,
            created_at=now,
            updated_at=now,
        )
        receipt = self._emit_preview_event(request, bridge_action, now)
        return BridgeDryRunResult(
            allowed=True,
            reason="bridge dry-run preview created; no external dispatch performed.",
            dry_run=True,
            would_dispatch=False,
            bridge_action=bridge_action,
            policy_disposition=policy_disposition,
            event_receipt=receipt,
        )

    def _evaluate_policy(
        self,
        request: BridgeDryRunRequest,
        target_system: str,
        action_type: str,
    ) -> tuple[str, str]:
        if self._policy_hook is None:
            return "defer", "no policy hook configured for dry-run preview."

        payload = {
            "action": "plan",
            "target_system": target_system,
            "action_type": action_type,
            "dry_run": True,
            **dict(request.policy_context),
        }
        if "target_path" not in payload and "path" in request.payload:
            payload["target_path"] = request.payload["path"]
        policy_request = ExecutionRequest(
            capability_name="bridge.preview",
            input_payload=payload,
            correlation_id=request.correlation_id or "corr_bridge_dry_run",
            idempotency_key=f"bridge-preview:{request.execute_job_id}:{target_system}:{action_type}",
            object_context={"execute_job_id": request.execute_job_id},
            branch_context={"branch_id": request.branch_id} if request.branch_id else {},
        )
        definition = CapabilityDefinition(
            name="bridge.preview",
            version="v1",
            schema_ref="schemas/bridge.preview.dry_run.json",
            side_effect_class="read-only",
        )
        decision = self._policy_hook.evaluate(policy_request, definition)
        return decision.disposition, decision.rationale

    def _emit_preview_event(
        self,
        request: BridgeDryRunRequest,
        bridge_action: BridgeAction,
        created_at: datetime,
    ) -> EventAppendReceipt | None:
        if self._event_writer is None:
            return None
        if not request.correlation_id or not request.correlation_id.startswith("corr_"):
            return None
        if not request.branch_id or not request.branch_id.startswith("br_"):
            return None

        event = build_root_event(
            event_id=generate_event_id(),
            event_type=EventType.BRIDGE_ACTION_DISPATCHED,
            correlation_id=request.correlation_id,
            object_type=ObjectType.BRIDGE_ACTION,
            object_id=str(bridge_action.bridge_action_id),
            branch_id=request.branch_id,
            actor_type=ActorType.BRIDGE,
            actor_id=request.actor_id,
            created_at=created_at,
            payload_inline={
                "dry_run": True,
                "would_dispatch": False,
                "target_system": bridge_action.target_system,
                "action_type": bridge_action.action_type,
                "status": str(bridge_action.status),
            },
        )
        return self._event_writer.append(event)


def _blocked(request: BridgeDryRunRequest, reason: str, policy_disposition: str) -> BridgeDryRunResult:
    return BridgeDryRunResult(
        allowed=False,
        reason=reason,
        dry_run=request.dry_run,
        would_dispatch=False,
        bridge_action=None,
        policy_disposition=policy_disposition,
    )


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _has_secret_marker(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _SECRET_MARKERS)


def _payload_has_secret_key(payload: Mapping[str, Any]) -> bool:
    for key, value in payload.items():
        if _has_secret_marker(str(key)):
            return True
        if isinstance(value, Mapping) and _payload_has_secret_key(value):
            return True
    return False


def _is_ovc_target(target_system: str, payload: Mapping[str, Any]) -> bool:
    if "ovc" in target_system:
        return True
    for value in payload.values():
        if isinstance(value, str) and "ovc" in value.lower():
            return True
        if isinstance(value, Mapping) and _is_ovc_target("", value):
            return True
    return False


def _is_ovis_governance_context(policy_context: Mapping[str, Any]) -> bool:
    job_type = str(policy_context.get("job_type", "")).upper()
    cj_id = str(policy_context.get("cj_id", "")).upper()
    return "GOV" in job_type or "REG" in job_type or cj_id.startswith(("CJ-GOV", "CJ-REG"))
