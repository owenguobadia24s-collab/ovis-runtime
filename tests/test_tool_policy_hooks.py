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
    CapabilityDefinition,
    CapabilityDispatcher,
    CapabilityRegistry,
    ExecutionRequest,
    PolicyDecision,
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
