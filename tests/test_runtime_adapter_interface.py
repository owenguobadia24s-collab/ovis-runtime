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
