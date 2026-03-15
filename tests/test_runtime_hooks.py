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
