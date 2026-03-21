# ---
# id: TEST-RUNTIME-0003
# title: Test Runtime Adapter Interface Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: runtime
# repo: ovis-runtime
# path: tests/test_runtime_adapter_interface.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-RUNTIME-0003.yaml
# module_id: MOD-RUNTIME-GATEWAY-0001
# module_slug: runtime_gateway
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_responses_runtime import (  # noqa: E402
    PlaceholderResponsesRuntimeAdapter,
    RuntimeRequest,
    RuntimeTurnContext,
)


def test_placeholder_runtime_adapter_is_explicitly_unimplemented() -> None:
    adapter = PlaceholderResponsesRuntimeAdapter()
    request = RuntimeRequest(
        input_payload={"prompt": "hello"},
        turn_context=RuntimeTurnContext(
            branch_id="br-001",
            correlation_id="corr-001",
        ),
    )

    with pytest.raises(NotImplementedError):
        adapter.invoke(request)
