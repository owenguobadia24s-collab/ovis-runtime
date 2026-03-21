# ---
# id: TEST-GATEWAY-0002
# title: Test Executor Interface Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gateway
# repo: ovis-runtime
# path: tests/test_executor_interface.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-GATEWAY-0002.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_tool_gateway.executor import PlaceholderExecutionWrapper  # noqa: E402
from ovis_tool_gateway.types import ExecutionRequest  # noqa: E402


def test_placeholder_execution_wrapper_is_explicitly_unimplemented() -> None:
    wrapper = PlaceholderExecutionWrapper()
    request = ExecutionRequest(
        capability_name="example.capability",
        input_payload={},
        correlation_id="corr-001",
        idempotency_key="idem-001",
    )

    with pytest.raises(NotImplementedError):
        wrapper.execute(request)
