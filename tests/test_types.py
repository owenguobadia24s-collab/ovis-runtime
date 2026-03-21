# ---
# id: TEST-STATE-0005
# title: Test Types Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: tests/test_types.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-STATE-0005.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_tool_gateway.types import (  # noqa: E402
    CapabilityDefinition,
    ExecutionRequest,
    ExecutionResultEnvelope,
    PolicyDecision,
)


def test_type_instances_are_constructible() -> None:
    capability = CapabilityDefinition(
        name="example.capability",
        version="v1",
        schema_ref="schemas/example.json",
        side_effect_class="read-only",
    )
    request = ExecutionRequest(
        capability_name=capability.name,
        input_payload={"sample": "value"},
        correlation_id="corr-001",
        idempotency_key="idem-001",
        object_context={"work_object_id": "wo-001"},
        branch_context={"branch_id": "br-001"},
    )
    decision = PolicyDecision(
        disposition="defer",
        risk_class="R2",
        policy_profile="patch-only",
        approval_required=True,
        rationale="Placeholder decision for scaffold testing.",
    )
    envelope = ExecutionResultEnvelope(
        capability_name=capability.name,
        execution_status="placeholder",
        correlation_id=request.correlation_id,
        idempotency_outcome="not-evaluated",
        policy_disposition=decision.disposition,
    )

    assert capability.name == "example.capability"
    assert request.branch_context["branch_id"] == "br-001"
    assert decision.policy_profile == "patch-only"
    assert envelope.execution_status == "placeholder"
