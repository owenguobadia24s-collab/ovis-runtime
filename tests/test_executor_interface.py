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
