# ---
# id: TEST-GATEWAY-0006
# title: Test Tool Policy Hooks Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gateway
# repo: ovis-runtime
# path: tests/test_tool_policy_hooks.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-GATEWAY-0006.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_event_log import MemoryEventWriter  # noqa: E402
from ovis_tool_gateway import (  # noqa: E402
    AIWritePolicyContext,
    CapabilityDefinition,
    CapabilityDispatcher,
    CapabilityRegistry,
    ExecutionRequest,
    PolicyDecision,
    StaticAIWritePolicyHook,
)


class _RecordingPolicyHook:
    def __init__(self, disposition: str) -> None:
        self.disposition = disposition
        self.calls: list[tuple[str, str]] = []

    def evaluate(self, request, definition):
        self.calls.append((request.capability_name, definition.name))
        return PolicyDecision(
            disposition=self.disposition,
            risk_class="R2",
            policy_profile="patch-only",
            approval_required=self.disposition != "allow",
            rationale=f"policy {self.disposition}",
        )


def _make_definition() -> CapabilityDefinition:
    return CapabilityDefinition(
        name="echo.return",
        version="v1",
        schema_ref="schemas/echo.return.json",
        side_effect_class="read-only",
    )


def _make_request() -> ExecutionRequest:
    return ExecutionRequest(
        capability_name="echo.return",
        input_payload={"value": "hello"},
        correlation_id="corr_001",
        idempotency_key="idem_001",
        branch_context={"branch_id": "br_001"},
    )


def _make_policy_context(**overrides: object) -> AIWritePolicyContext:
    values: dict[str, object] = {
        "actor": "CODEX_EXECUTOR",
        "action": "read",
        "target_path": "README.md",
        "allowed_read_paths": ("README.md",),
        "allowed_write_paths": (),
        "commit_authority": False,
        "push_authority": False,
        "broad_staging_authorized": False,
        "external_side_effect_authorized": False,
        "job_type": None,
        "cj_id": None,
    }
    values.update(overrides)
    return AIWritePolicyContext(**values)


def test_policy_allow_runs_after_resolution_and_allows_execution() -> None:
    registry = CapabilityRegistry()
    registry.register(_make_definition(), handler=lambda payload: payload)
    policy = _RecordingPolicyHook("allow")
    dispatcher = CapabilityDispatcher(
        registry=registry,
        policy_hook=policy,
        event_writer=MemoryEventWriter(),
    )

    result = dispatcher.execute(_make_request())

    assert result.execution_status == "success"
    assert result.policy_disposition == "allow"
    assert policy.calls == [("echo.return", "echo.return")]


def test_policy_deny_blocks_execution() -> None:
    registry = CapabilityRegistry()
    executed = {"value": False}

    def handler(payload: dict[str, object]) -> dict[str, object]:
        executed["value"] = True
        return payload

    registry.register(_make_definition(), handler=handler)
    dispatcher = CapabilityDispatcher(
        registry=registry,
        policy_hook=_RecordingPolicyHook("deny"),
        event_writer=MemoryEventWriter(),
    )

    result = dispatcher.execute(_make_request())

    assert result.execution_status == "blocked"
    assert result.policy_disposition == "deny"
    assert result.error_details == "policy deny"
    assert executed["value"] is False


def test_policy_defer_blocks_execution_pending_later_governance() -> None:
    registry = CapabilityRegistry()
    executed = {"value": False}

    def handler(payload: dict[str, object]) -> dict[str, object]:
        executed["value"] = True
        return payload

    registry.register(_make_definition(), handler=handler)
    dispatcher = CapabilityDispatcher(
        registry=registry,
        policy_hook=_RecordingPolicyHook("defer"),
        event_writer=MemoryEventWriter(),
    )

    result = dispatcher.execute(_make_request())

    assert result.execution_status == "blocked"
    assert result.policy_disposition == "defer"
    assert result.error_details == "policy defer"
    assert executed["value"] is False


def test_static_ai_write_policy_allows_read_inside_allowed_read_paths() -> None:
    decision = StaticAIWritePolicyHook().evaluate_context(
        _make_policy_context(action="read", target_path="README.md", allowed_read_paths=("README.md",))
    )

    assert decision.allowed is True
    assert decision.permission_level == "READ_ONLY"
    assert decision.exit_decision_hint is None


def test_static_ai_write_policy_allows_write_inside_allowed_write_paths() -> None:
    decision = StaticAIWritePolicyHook().evaluate_context(
        _make_policy_context(
            action="write",
            target_path="src/ovis_tool_gateway/policy_hooks.py",
            allowed_write_paths=("src/ovis_tool_gateway/**",),
        )
    )

    assert decision.allowed is True
    assert decision.permission_level == "SCOPED_EDIT"


def test_static_ai_write_policy_denies_write_outside_allowed_write_paths() -> None:
    decision = StaticAIWritePolicyHook().evaluate_context(
        _make_policy_context(
            action="write",
            target_path="src/ovis_tool_gateway/policy_hooks.py",
            allowed_write_paths=("tests/**",),
        )
    )

    assert decision.allowed is False
    assert decision.permission_level == "FORBIDDEN"
    assert decision.exit_decision_hint == "HOLD-REPAIR"
    assert "outside allowed write paths" in decision.reason


def test_static_ai_write_policy_denies_commit_without_authority() -> None:
    decision = StaticAIWritePolicyHook().evaluate_context(_make_policy_context(action="commit"))

    assert decision.allowed is False
    assert decision.exit_decision_hint == "HOLD-REPAIR"
    assert "commit requires explicit authority" in decision.reason


def test_static_ai_write_policy_denies_push_without_authority() -> None:
    decision = StaticAIWritePolicyHook().evaluate_context(_make_policy_context(action="push"))

    assert decision.allowed is False
    assert decision.exit_decision_hint == "HOLD-REPAIR"
    assert "push requires explicit authority" in decision.reason


def test_static_ai_write_policy_denies_broad_staging_without_authorization() -> None:
    decision = StaticAIWritePolicyHook().evaluate_context(_make_policy_context(action="stage_all", target_path="."))

    assert decision.allowed is False
    assert decision.exit_decision_hint == "HOLD-REPAIR"
    assert "broad staging requires explicit authority" in decision.reason


def test_static_ai_write_policy_denies_secret_paths_even_when_in_scope() -> None:
    decision = StaticAIWritePolicyHook().evaluate_context(
        _make_policy_context(
            action="write",
            target_path=".env",
            allowed_write_paths=(".env",),
        )
    )

    assert decision.allowed is False
    assert decision.exit_decision_hint == "HOLD-REPAIR"
    assert "secrets or credentials" in decision.reason


def test_static_ai_write_policy_denies_ovc_paths_for_ovis_governance_jobs() -> None:
    decision = StaticAIWritePolicyHook().evaluate_context(
        _make_policy_context(
            action="write",
            target_path="ovc-infra/README.md",
            allowed_write_paths=("ovc-infra/**",),
            job_type="GOVERNANCE",
            cj_id="CJ-GOV-AI-0001",
        )
    )

    assert decision.allowed is False
    assert decision.exit_decision_hint == "HOLD-REPAIR"
    assert "OVC paths are forbidden" in decision.reason


def test_static_ai_write_policy_denies_external_side_effect_without_authorization() -> None:
    decision = StaticAIWritePolicyHook().evaluate_context(
        _make_policy_context(action="write_notion", external_side_effect_authorized=False)
    )

    assert decision.allowed is False
    assert decision.exit_decision_hint == "HOLD-REPAIR"
    assert "external side effects require explicit authority" in decision.reason


def test_static_ai_write_policy_integrates_with_dispatcher_block_and_allow_paths() -> None:
    registry = CapabilityRegistry()
    executed = {"count": 0}

    def handler(payload: dict[str, object]) -> dict[str, object]:
        executed["count"] += 1
        return payload

    registry.register(
        CapabilityDefinition(
            name="repo.patch",
            version="v1",
            schema_ref="schemas/repo.patch.json",
            side_effect_class="state-write",
        ),
        handler=handler,
    )
    dispatcher = CapabilityDispatcher(
        registry=registry,
        policy_hook=StaticAIWritePolicyHook(),
        event_writer=MemoryEventWriter(),
    )

    blocked = dispatcher.execute(
        ExecutionRequest(
            capability_name="repo.patch",
            input_payload={
                "action": "write",
                "target_path": "src/ovis_tool_gateway/policy_hooks.py",
                "allowed_write_paths": ("tests/**",),
            },
            correlation_id="corr_002",
            idempotency_key="idem_002",
            branch_context={"branch_id": "br_002"},
        )
    )
    allowed = dispatcher.execute(
        ExecutionRequest(
            capability_name="repo.patch",
            input_payload={
                "action": "write",
                "target_path": "src/ovis_tool_gateway/policy_hooks.py",
                "allowed_write_paths": ("src/ovis_tool_gateway/**",),
            },
            correlation_id="corr_003",
            idempotency_key="idem_003",
            branch_context={"branch_id": "br_003"},
        )
    )

    assert blocked.execution_status == "blocked"
    assert blocked.policy_disposition == "deny"
    assert "outside allowed write paths" in blocked.error_details
    assert allowed.execution_status == "success"
    assert allowed.policy_disposition == "allow"
    assert executed["count"] == 1
