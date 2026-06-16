# ---
# id: MODULE-GATEWAY-0006
# title: Policy Hooks Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gateway
# repo: ovis-runtime
# path: src/ovis_tool_gateway/policy_hooks.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GATEWAY-0006.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
"""Policy hook interfaces for the OVIS tool gateway."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Protocol

from .types import CapabilityDefinition
from .types import ExecutionRequest, PolicyDecision

PermissionLevel = Literal[
    "READ_ONLY",
    "PLAN_ONLY",
    "DRAFT_ONLY",
    "SCOPED_EDIT",
    "STAGE_ONLY",
    "COMMIT_AUTHORIZED",
    "PUSH_AUTHORIZED",
    "EXECUTE_LOCAL_COMMANDS",
    "EXTERNAL_SIDE_EFFECT",
    "FORBIDDEN",
]

_DEFAULT_ACTOR = "CODEX_EXECUTOR"
_READ_ACTIONS = {"read", "inspect", "search", "list", "validate", "plan", "review"}
_WRITE_ACTIONS = {"write", "edit", "apply_patch", "patch", "create", "delete", "move"}
_STAGE_ACTIONS = {"stage", "git_add"}
_BROAD_STAGE_ACTIONS = {"stage_all", "git_add_dot", "git_add_all"}
_COMMIT_ACTIONS = {"commit", "git_commit"}
_PUSH_ACTIONS = {"push", "git_push"}
_LOCAL_EXEC_ACTIONS = {"execute_local_command", "local_exec", "run_command", "shell"}
_EXTERNAL_ACTIONS = {
    "external_side_effect",
    "write_notion",
    "send_email",
    "deploy",
    "call_production_api",
    "trigger_bridge_dispatch",
}
_SECRET_PATH_MARKERS = {
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
}


@dataclass(frozen=True)
class AIWritePolicyContext:
    actor: str
    action: str
    target_path: str | None = None
    allowed_read_paths: tuple[str, ...] = ()
    allowed_write_paths: tuple[str, ...] = ()
    commit_authority: bool = False
    push_authority: bool = False
    broad_staging_authorized: bool = False
    external_side_effect_authorized: bool = False
    job_type: str | None = None
    cj_id: str | None = None


@dataclass(frozen=True)
class AIWritePolicyDecision:
    allowed: bool
    reason: str
    actor: str
    permission_level: PermissionLevel
    action: str
    target_path: str | None
    exit_decision_hint: str | None = None


class PolicyHook(Protocol):
    def evaluate(self, request: ExecutionRequest, definition: CapabilityDefinition) -> PolicyDecision:
        """Evaluate a request before execution."""


class PlaceholderPolicyHook:
    """Placeholder-only policy hook."""

    def evaluate(self, request: ExecutionRequest, definition: CapabilityDefinition) -> PolicyDecision:
        raise NotImplementedError("CJ-001 scaffold only: no policy evaluation implementation.")


class StaticAIWritePolicyHook:
    """Deterministic AI write policy hook for bounded runtime capability execution."""

    def __init__(self, *, default_actor: str = _DEFAULT_ACTOR) -> None:
        self._default_actor = default_actor

    def evaluate_context(self, context: AIWritePolicyContext) -> AIWritePolicyDecision:
        action = _normalize_action(context.action)
        target_path = _normalize_path(context.target_path)

        if _is_secret_path(target_path):
            return _deny(context, action, target_path, "secrets or credentials paths are forbidden.", "HOLD-REPAIR")

        if _is_ovc_path(target_path) and _is_ovis_governance_context(context):
            return _deny(context, action, target_path, "OVC paths are forbidden for OVIS governance jobs.", "HOLD-REPAIR")

        if action in _EXTERNAL_ACTIONS:
            if context.external_side_effect_authorized:
                return _allow(context, action, target_path, "EXTERNAL_SIDE_EFFECT", "external side effect authorized.")
            return _deny(context, action, target_path, "external side effects require explicit authority.", "HOLD-REPAIR")

        if action in _PUSH_ACTIONS:
            if context.push_authority:
                return _allow(context, action, target_path, "PUSH_AUTHORIZED", "push authority granted.")
            return _deny(context, action, target_path, "push requires explicit authority.", "HOLD-REPAIR")

        if action in _COMMIT_ACTIONS:
            if context.commit_authority:
                return _allow(context, action, target_path, "COMMIT_AUTHORIZED", "commit authority granted.")
            return _deny(context, action, target_path, "commit requires explicit authority.", "HOLD-REPAIR")

        if action in _BROAD_STAGE_ACTIONS or (action in _STAGE_ACTIONS and _is_broad_stage_target(target_path)):
            if context.broad_staging_authorized:
                return _allow(context, action, target_path, "STAGE_ONLY", "broad staging authority granted.")
            return _deny(context, action, target_path, "broad staging requires explicit authority.", "HOLD-REPAIR")

        if action in _STAGE_ACTIONS:
            if _path_is_allowed(target_path, context.allowed_write_paths):
                return _allow(context, action, target_path, "STAGE_ONLY", "target is inside allowed write paths.")
            return _deny(context, action, target_path, "staging target is outside allowed write paths.", "HOLD-REPAIR")

        if action in _WRITE_ACTIONS:
            if _path_is_allowed(target_path, context.allowed_write_paths):
                return _allow(context, action, target_path, "SCOPED_EDIT", "target is inside allowed write paths.")
            return _deny(context, action, target_path, "write target is outside allowed write paths.", "HOLD-REPAIR")

        if action in _LOCAL_EXEC_ACTIONS:
            return _allow(context, action, target_path, "EXECUTE_LOCAL_COMMANDS", "local command execution action.")

        if action in _READ_ACTIONS:
            if target_path is None or _path_is_allowed(target_path, context.allowed_read_paths):
                return _allow(context, action, target_path, "READ_ONLY", "read target is inside allowed read paths.")
            return _deny(context, action, target_path, "read target is outside allowed read paths.", "HOLD-REPAIR")

        return _deny(context, action, target_path, "unknown mutating or external action.", "HOLD-REPAIR")

    def evaluate(self, request: ExecutionRequest, definition: CapabilityDefinition) -> PolicyDecision:
        context = self._context_from_request(request, definition)
        decision = self.evaluate_context(context)
        return PolicyDecision(
            disposition="allow" if decision.allowed else "deny",
            risk_class=_risk_class(decision),
            policy_profile="ai-write-permissions:v1",
            approval_required=not decision.allowed,
            rationale=decision.reason,
        )

    def _context_from_request(
        self,
        request: ExecutionRequest,
        definition: CapabilityDefinition,
    ) -> AIWritePolicyContext:
        payload = request.input_payload
        object_context = request.object_context
        return AIWritePolicyContext(
            actor=_string_value(payload, object_context, "actor", default=self._default_actor),
            action=_string_value(payload, object_context, "action", default=_default_action(definition)),
            target_path=_optional_string_value(payload, object_context, "target_path", "path"),
            allowed_read_paths=_path_tuple(payload, object_context, "allowed_read_paths"),
            allowed_write_paths=_path_tuple(payload, object_context, "allowed_write_paths"),
            commit_authority=_bool_value(payload, object_context, "commit_authority"),
            push_authority=_bool_value(payload, object_context, "push_authority"),
            broad_staging_authorized=_bool_value(payload, object_context, "broad_staging_authorized"),
            external_side_effect_authorized=_bool_value(payload, object_context, "external_side_effect_authorized"),
            job_type=_optional_string_value(payload, object_context, "job_type"),
            cj_id=_optional_string_value(payload, object_context, "cj_id"),
        )


def _allow(
    context: AIWritePolicyContext,
    action: str,
    target_path: str | None,
    permission_level: PermissionLevel,
    reason: str,
) -> AIWritePolicyDecision:
    return AIWritePolicyDecision(
        allowed=True,
        reason=reason,
        actor=context.actor,
        permission_level=permission_level,
        action=action,
        target_path=target_path,
    )


def _deny(
    context: AIWritePolicyContext,
    action: str,
    target_path: str | None,
    reason: str,
    exit_decision_hint: str,
) -> AIWritePolicyDecision:
    return AIWritePolicyDecision(
        allowed=False,
        reason=reason,
        actor=context.actor,
        permission_level="FORBIDDEN",
        action=action,
        target_path=target_path,
        exit_decision_hint=exit_decision_hint,
    )


def _default_action(definition: CapabilityDefinition) -> str:
    if definition.side_effect_class == "read-only":
        return "read"
    if definition.side_effect_class == "external-bridge":
        return "external_side_effect"
    if definition.side_effect_class == "local-exec":
        return "execute_local_command"
    return "write"


def _risk_class(decision: AIWritePolicyDecision) -> str:
    if not decision.allowed:
        return "R3"
    if decision.permission_level == "READ_ONLY":
        return "R0"
    if decision.permission_level in {"COMMIT_AUTHORIZED", "PUSH_AUTHORIZED", "EXTERNAL_SIDE_EFFECT"}:
        return "R4"
    if decision.permission_level == "EXECUTE_LOCAL_COMMANDS":
        return "R3"
    return "R2"


def _string_value(
    payload: Mapping[str, Any],
    object_context: Mapping[str, str],
    key: str,
    *,
    default: str,
) -> str:
    value = payload.get(key, object_context.get(key, default))
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _optional_string_value(
    payload: Mapping[str, Any],
    object_context: Mapping[str, str],
    *keys: str,
) -> str | None:
    for key in keys:
        value = payload.get(key, object_context.get(key))
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _bool_value(payload: Mapping[str, Any], object_context: Mapping[str, str], key: str) -> bool:
    value = payload.get(key, object_context.get(key, False))
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def _path_tuple(payload: Mapping[str, Any], object_context: Mapping[str, str], key: str) -> tuple[str, ...]:
    value = payload.get(key, object_context.get(key, ()))
    if isinstance(value, str):
        return tuple(_normalize_path(part) for part in value.split(";") if _normalize_path(part) is not None)
    try:
        return tuple(path for item in value if (path := _normalize_path(str(item))) is not None)
    except TypeError:
        return ()


def _normalize_action(action: str) -> str:
    return action.strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_path(path: str | None) -> str | None:
    if path is None:
        return None
    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.rstrip("/") if normalized not in {"", "/", "."} else normalized


def _path_is_allowed(target_path: str | None, allowed_paths: tuple[str, ...]) -> bool:
    if target_path is None:
        return False
    normalized_allowed_paths = tuple(path for item in allowed_paths if (path := _normalize_path(item)) is not None)
    if not normalized_allowed_paths:
        return False
    for allowed_path in normalized_allowed_paths:
        if allowed_path.endswith("/**"):
            prefix = allowed_path[:-3].rstrip("/")
            if target_path == prefix or target_path.startswith(f"{prefix}/"):
                return True
        elif allowed_path.endswith("/"):
            prefix = allowed_path.rstrip("/")
            if target_path == prefix or target_path.startswith(f"{prefix}/"):
                return True
        elif target_path == allowed_path:
            return True
    return False


def _is_secret_path(target_path: str | None) -> bool:
    if target_path is None:
        return False
    lower_path = target_path.lower()
    path_parts = tuple(part for part in lower_path.split("/") if part)
    return any(_path_part_matches_secret_marker(part, marker) for part in path_parts for marker in _SECRET_PATH_MARKERS)


def _path_part_matches_secret_marker(path_part: str, marker: str) -> bool:
    return (
        path_part == marker
        or path_part.startswith(f"{marker}.")
        or path_part.endswith(f".{marker}")
        or path_part.endswith(marker)
    )


def _is_ovc_path(target_path: str | None) -> bool:
    if target_path is None:
        return False
    lower_path = target_path.lower()
    return lower_path == "ovc" or lower_path.startswith("ovc/") or "ovc-infra" in lower_path


def _is_ovis_governance_context(context: AIWritePolicyContext) -> bool:
    job_type = (context.job_type or "").upper()
    cj_id = (context.cj_id or "").upper()
    return "GOV" in job_type or "REG" in job_type or cj_id.startswith(("CJ-GOV", "CJ-REG"))


def _is_broad_stage_target(target_path: str | None) -> bool:
    return target_path in {None, "", ".", "/"}
