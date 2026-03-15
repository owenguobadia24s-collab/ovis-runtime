from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_responses_runtime import (  # noqa: E402
    OpenAIResponsesProviderAdapter,
    RuntimeAdapterConfig,
    RuntimeModelConfig,
    RuntimeRequest,
    RuntimeSessionConfig,
    RuntimeTurnContext,
    SessionMode,
)
from ovis_responses_runtime.continuation import build_chained_continuation  # noqa: E402


class _FakeResponsesClient:
    def __init__(self) -> None:
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return type(
            "FakeResponse",
            (),
            {
                "id": "resp_external_001",
                "output_text": "hello world",
                "finish_reason": "stop",
            },
        )()


class _FakeClient:
    def __init__(self) -> None:
        self.responses = _FakeResponsesClient()


def test_openai_provider_adapter_maps_runtime_request_and_response() -> None:
    client = _FakeClient()
    adapter = OpenAIResponsesProviderAdapter(client=client)
    config = RuntimeAdapterConfig(
        model=RuntimeModelConfig(model_name="gpt-5"),
        session=RuntimeSessionConfig(
            session_mode=SessionMode.DURABLE_OPTIONAL,
            store_enabled=True,
            durable_state_allowed=True,
        ),
    )
    request = RuntimeRequest(
        input_payload={"prompt": "hello", "instructions": "be concise"},
        turn_context=RuntimeTurnContext(branch_id="br_001", correlation_id="corr_001"),
        continuation=build_chained_continuation(
            previous_response_id="resp_prev_001",
            branch_id="br_001",
            correlation_id="corr_001",
        ),
    )

    result = adapter.invoke(request=request, config=config)

    assert client.responses.last_request["model"] == "gpt-5"
    assert client.responses.last_request["input"] == "hello"
    assert client.responses.last_request["instructions"] == "be concise"
    assert client.responses.last_request["previous_response_id"] == "resp_prev_001"
    assert client.responses.last_request["store"] is True
    assert result.provider_name == "openai"
    assert result.provider_response_id == "resp_external_001"
    assert result.output_text == "hello world"
    assert result.finish_reason == "stop"
