# ---
# id: TEST-GATEWAY-0008
# title: Test Bridge Dry Run Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gateway
# repo: ovis-runtime
# path: tests/test_bridge_dry_run.py
# owner: Owen Vitae
# created: '2026-06-16'
# last_updated: '2026-06-16'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-GATEWAY-0008.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
from datetime import UTC, datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_event_log import MemoryEventWriter  # noqa: E402
from ovis_tool_gateway import (  # noqa: E402
    BridgeDryRunRequest,
    BridgeDryRunService,
    CapabilityDefinition,
    CapabilityDispatcher,
    CapabilityRegistry,
    DEFAULT_CAPABILITY_REGISTRY,
    ExecutionRequest,
    PolicyDecision,
)


class _PolicyHook:
    def __init__(self, disposition: str) -> None:
        self.disposition = disposition
        self.requests: list[ExecutionRequest] = []

    def evaluate(self, request, definition):
        self.requests.append(request)
        return PolicyDecision(
            disposition=self.disposition,
            risk_class="R0" if self.disposition == "allow" else "R3",
            policy_profile="bridge-dry-run:test",
            approval_required=self.disposition != "allow",
            rationale=f"policy {self.disposition}",
        )


def _request(**overrides: object) -> BridgeDryRunRequest:
    values: dict[str, object] = {
        "execute_job_id": "job_execute_001",
        "target_system": "notion",
        "action_type": "create_row",
        "payload": {"database": "cockpit"},
        "correlation_id": "corr_001",
        "branch_id": "br_001",
    }
    values.update(overrides)
    return BridgeDryRunRequest(**values)


def test_bridge_dry_run_preview_allowed_and_never_dispatches() -> None:
    policy = _PolicyHook("allow")
    service = BridgeDryRunService(policy_hook=policy, clock=lambda: datetime(2026, 6, 16, tzinfo=UTC))

    result = service.preview(_request())

    assert result.allowed is True
    assert result.dry_run is True
    assert result.would_dispatch is False
    assert result.bridge_action is not None
    assert result.bridge_action.target_system == "notion"
    assert result.bridge_action.action_type == "create_row"
    assert result.bridge_action.status == "pending"
    assert result.event_receipt is None
    assert policy.requests[0].input_payload["dry_run"] is True


def test_bridge_dry_run_false_is_denied() -> None:
    result = BridgeDryRunService(policy_hook=_PolicyHook("allow")).preview(_request(dry_run=False))

    assert result.allowed is False
    assert result.would_dispatch is False
    assert result.bridge_action is None
    assert "dry_run must be true" in result.reason


def test_preview_without_policy_hook_is_allowed_with_deferred_policy() -> None:
    result = BridgeDryRunService().preview(_request())

    assert result.allowed is True
    assert result.policy_disposition == "defer"
    assert result.would_dispatch is False


def test_policy_denial_blocks_preview() -> None:
    result = BridgeDryRunService(policy_hook=_PolicyHook("deny")).preview(_request())

    assert result.allowed is False
    assert result.policy_disposition == "deny"
    assert result.bridge_action is None
    assert result.reason == "policy deny"


def test_notion_preview_remains_local() -> None:
    result = BridgeDryRunService(policy_hook=_PolicyHook("allow")).preview(
        _request(target_system="Notion", action_type="Update Page")
    )

    assert result.allowed is True
    assert result.would_dispatch is False
    assert result.bridge_action is not None
    assert result.bridge_action.target_system == "notion"
    assert result.bridge_action.action_type == "update_page"


def test_ovc_target_is_denied_for_ovis_governance_context() -> None:
    result = BridgeDryRunService(policy_hook=_PolicyHook("allow")).preview(
        _request(
            target_system="ovc-infra",
            payload={"path": "ovc-infra/README.md"},
            policy_context={"job_type": "GOVERNANCE", "cj_id": "CJ-GOV-0001"},
        )
    )

    assert result.allowed is False
    assert result.policy_disposition == "deny"
    assert "OVC bridge targets are forbidden" in result.reason


def test_secret_payload_keys_are_denied() -> None:
    result = BridgeDryRunService(policy_hook=_PolicyHook("allow")).preview(
        _request(payload={"api_token": "redacted"})
    )

    assert result.allowed is False
    assert result.policy_disposition == "deny"
    assert "secrets or credentials" in result.reason


def test_event_writer_records_local_bridge_audit_event_when_context_is_valid() -> None:
    writer = MemoryEventWriter()
    service = BridgeDryRunService(
        policy_hook=_PolicyHook("allow"),
        event_writer=writer,
        clock=lambda: datetime(2026, 6, 16, tzinfo=UTC),
    )

    result = service.preview(_request())

    assert result.event_receipt is not None
    records = writer.records()
    assert len(records) == 1
    assert records[0]["event_type"] == "bridge_action.previewed"
    assert records[0]["payload"]["payload_inline"]["dry_run"] is True
    assert records[0]["payload"]["payload_inline"]["would_dispatch"] is False
    assert records[0]["payload"]["payload_inline"]["target_system"] == "notion"
    assert records[0]["payload"]["payload_inline"]["action_type"] == "create_row"
    assert records[0]["payload"]["payload_inline"]["status"] == "pending"


def test_event_writer_is_skipped_without_valid_event_context() -> None:
    writer = MemoryEventWriter()
    result = BridgeDryRunService(policy_hook=_PolicyHook("allow"), event_writer=writer).preview(
        _request(correlation_id=None, branch_id=None)
    )

    assert result.allowed is True
    assert result.event_receipt is None
    assert writer.records() == ()


def test_bridge_dry_run_can_run_through_local_dispatcher_registration() -> None:
    registry = CapabilityRegistry()
    service = BridgeDryRunService(policy_hook=_PolicyHook("allow"))

    def handler(payload: dict[str, object]) -> dict[str, object]:
        preview = service.preview(BridgeDryRunRequest(**payload))
        return {
            "allowed": preview.allowed,
            "dry_run": preview.dry_run,
            "would_dispatch": preview.would_dispatch,
            "reason": preview.reason,
        }

    registry.register(
        CapabilityDefinition(
            name="bridge.preview",
            version="v1",
            schema_ref="schemas/bridge.preview.dry_run.json",
            side_effect_class="read-only",
        ),
        handler=handler,
    )
    dispatcher = CapabilityDispatcher(registry=registry, policy_hook=_PolicyHook("allow"))

    result = dispatcher.execute(
        ExecutionRequest(
            capability_name="bridge.preview",
            input_payload={
                "execute_job_id": "job_execute_001",
                "target_system": "notion",
                "action_type": "create_row",
                "payload": {"database": "cockpit"},
                "correlation_id": "corr_001",
                "branch_id": "br_001",
            },
            correlation_id="corr_002",
            idempotency_key="idem_001",
        )
    )

    assert result.execution_status == "success"
    assert result.result_payload["allowed"] is True
    assert result.result_payload["would_dispatch"] is False


def test_bridge_preview_is_not_registered_in_default_capability_registry() -> None:
    assert DEFAULT_CAPABILITY_REGISTRY.get("bridge.preview") is None
