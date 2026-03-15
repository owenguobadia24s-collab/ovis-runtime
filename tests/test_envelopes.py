from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_tool_gateway.envelopes import placeholder_result  # noqa: E402


def test_placeholder_result_returns_placeholder_envelope() -> None:
    envelope = placeholder_result("example.capability", "corr-001")

    assert envelope.capability_name == "example.capability"
    assert envelope.execution_status == "placeholder"
    assert envelope.policy_disposition == "defer"
