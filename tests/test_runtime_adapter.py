# ---
# id: TEST-RUNTIME-0002
# title: Test Runtime Adapter Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: runtime
# repo: ovis-runtime
# path: tests/test_runtime_adapter.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-RUNTIME-0002.yaml
# module_id: MOD-RUNTIME-GATEWAY-0001
# module_slug: runtime_gateway
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_event_log import MemoryEventWriter  # noqa: E402
from ovis_responses_runtime import (  # noqa: E402
    OpenAIProviderResult,
    RuntimeAdapter,
    RuntimeAdapterConfig,
    RuntimeHooks,
    RuntimeModelConfig,
    RuntimeRequest,
    RuntimeSessionConfig,
    RuntimeTurnContext,
    SessionMode,
)


class _FakeProviderAdapter:
    def __init__(self, result: OpenAIProviderResult | Exception) -> None:
        self.result = result
        self.calls = 0

    def invoke(self, request, config):
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_runtime_adapter_invoke_is_canonical_entrypoint_and_emits_events() -> None:
    writer = MemoryEventWriter()
    adapter = RuntimeAdapter(
        config=RuntimeAdapterConfig(
            model=RuntimeModelConfig(model_name="gpt-5"),
            session=RuntimeSessionConfig(
                session_mode=SessionMode.ZDR_FIRST,
                store_enabled=False,
                durable_state_allowed=False,
            ),
        ),
        hooks=RuntimeHooks(event_writer=writer),
        provider_adapter=_FakeProviderAdapter(
            OpenAIProviderResult(
                provider_name="openai",
                provider_response_id="resp_external_001",
                output_text="hello world",
                finish_reason="stop",
            )
        ),
    )

    response = adapter.invoke(
        RuntimeRequest(
            input_payload={"prompt": "hello"},
            turn_context=RuntimeTurnContext(branch_id="br_001", correlation_id="corr_001"),
        )
    )

    records = writer.records()
    assert response.provider_name == "openai"
    assert response.response_id is None
    assert response.provider_response_ref == "resp_external_001"
    assert response.continuation is not None
    assert response.continuation.previous_response_id == "resp_external_001"
    assert len(records) == 2
    assert records[0]["event_type"] == "runtime.requested"
    assert records[1]["event_type"] == "runtime.response_received"
    assert records[0]["correlation_id"] == "corr_001"
    assert records[0]["branch_id"] == "br_001"
    assert records[0]["event_id"].startswith("evt_")
    assert records[1]["payload"]["payload_inline"]["provider_response_id"] == "resp_external_001"


def test_runtime_adapter_emits_error_and_reraises() -> None:
    writer = MemoryEventWriter()
    adapter = RuntimeAdapter(
        config=RuntimeAdapterConfig(
            model=RuntimeModelConfig(model_name="gpt-5"),
            session=RuntimeSessionConfig(
                session_mode=SessionMode.ZDR_FIRST,
                store_enabled=False,
                durable_state_allowed=False,
            ),
        ),
        hooks=RuntimeHooks(event_writer=writer),
        provider_adapter=_FakeProviderAdapter(RuntimeError("provider failure")),
    )

    with pytest.raises(RuntimeError):
        adapter.invoke(
            RuntimeRequest(
                input_payload={"prompt": "hello"},
                turn_context=RuntimeTurnContext(branch_id="br_001", correlation_id="corr_001"),
            )
        )

    records = writer.records()
    assert len(records) == 2
    assert records[0]["event_type"] == "runtime.requested"
    assert records[1]["event_type"] == "runtime.error"
    assert records[1]["payload"]["payload_inline"]["error_type"] == "RuntimeError"


def test_runtime_adapter_fails_before_dispatch_on_invalid_turn_context() -> None:
    provider = _FakeProviderAdapter(
        OpenAIProviderResult(
            provider_name="openai",
            provider_response_id="resp_external_001",
            output_text="hello world",
            finish_reason="stop",
        )
    )
    adapter = RuntimeAdapter(
        config=RuntimeAdapterConfig(
            model=RuntimeModelConfig(model_name="gpt-5"),
            session=RuntimeSessionConfig(
                session_mode=SessionMode.ZDR_FIRST,
                store_enabled=False,
                durable_state_allowed=False,
            ),
        ),
        provider_adapter=provider,
    )

    with pytest.raises(ValueError):
        adapter.invoke(
            RuntimeRequest(
                input_payload={"prompt": "hello"},
                turn_context=RuntimeTurnContext(branch_id="bad_001", correlation_id="corr_001"),
            )
        )

    assert provider.calls == 0
