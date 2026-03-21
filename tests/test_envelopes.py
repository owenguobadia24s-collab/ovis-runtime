# ---
# id: TEST-GATEWAY-0001
# title: Test Envelopes Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gateway
# repo: ovis-runtime
# path: tests/test_envelopes.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-GATEWAY-0001.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_tool_gateway.envelopes import placeholder_result  # noqa: E402


def test_placeholder_result_returns_placeholder_envelope() -> None:
    envelope = placeholder_result("example.capability", "corr-001")

    assert envelope.capability_name == "example.capability"
    assert envelope.execution_status == "placeholder"
    assert envelope.policy_disposition == "defer"
