from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_responses_runtime import (  # noqa: E402
    build_chained_continuation,
    build_root_continuation,
    has_explicit_continuation,
)


def test_root_continuation_has_no_previous_response_id() -> None:
    continuation = build_root_continuation(branch_id="br-001", correlation_id="corr-001")

    assert continuation.previous_response_id is None
    assert has_explicit_continuation(continuation) is False


def test_chained_continuation_preserves_branch_and_correlation() -> None:
    continuation = build_chained_continuation(
        previous_response_id="resp-001",
        branch_id="br-001",
        correlation_id="corr-001",
    )

    assert continuation.previous_response_id == "resp-001"
    assert continuation.branch_id == "br-001"
    assert continuation.correlation_id == "corr-001"
    assert has_explicit_continuation(continuation) is True
