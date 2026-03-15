from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_responses_runtime import (  # noqa: E402
    RuntimeContinuationRef,
    RuntimeRequest,
    RuntimeResponse,
    RuntimeTurnContext,
    SessionMode,
)
from ovis_tool_gateway.types import ExecutionRequest  # noqa: E402


def test_runtime_types_are_constructible() -> None:
    turn_context = RuntimeTurnContext(
        branch_id="br-001",
        correlation_id="corr-001",
        object_context={"work_object_id": "wo-001"},
    )
    continuation = RuntimeContinuationRef(
        previous_response_id="resp-000",
        branch_id="br-001",
        correlation_id="corr-001",
    )
    gateway_request = ExecutionRequest(
        capability_name="example.capability",
        input_payload={"sample": "value"},
        correlation_id="corr-001",
        idempotency_key="idem-001",
    )
    request = RuntimeRequest(
        input_payload={"prompt": "hello"},
        turn_context=turn_context,
        continuation=continuation,
        session_mode_override=SessionMode.DURABLE_PROHIBITED,
    )
    response = RuntimeResponse(
        response_id="resp-001",
        provider_name="openai",
        output_text="placeholder",
        continuation=continuation,
        provider_response_ref="provider-resp-001",
        gateway_requests=(gateway_request,),
    )

    assert request.turn_context.branch_id == "br-001"
    assert response.gateway_requests[0].capability_name == "example.capability"
