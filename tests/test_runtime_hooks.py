# ---
# id: TEST-RUNTIME-0006
# title: Test Runtime Hooks Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: runtime
# repo: ovis-runtime
# path: tests/test_runtime_hooks.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-RUNTIME-0006.yaml
# module_id: MOD-RUNTIME-GATEWAY-0001
# module_slug: runtime_gateway
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_event_log import PlaceholderAppendOnlyEventWriter  # noqa: E402
from ovis_responses_runtime import RuntimeHooks  # noqa: E402
from ovis_tool_gateway.executor import PlaceholderExecutionWrapper  # noqa: E402


def test_runtime_hooks_attach_existing_placeholder_surfaces() -> None:
    hooks = RuntimeHooks(
        event_writer=PlaceholderAppendOnlyEventWriter(),
        gateway_executor=PlaceholderExecutionWrapper(),
    )

    assert hooks.event_writer is not None
    assert hooks.gateway_executor is not None
