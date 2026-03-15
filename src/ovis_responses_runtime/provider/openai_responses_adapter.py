"""OpenAI-specific Responses API adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from ..config import RuntimeAdapterConfig
from ..session import SessionMode
from ..types import RuntimeRequest


@dataclass(frozen=True)
class OpenAIProviderResult:
    """Thin normalized provider result for the canonical runtime adapter."""

    provider_name: str
    provider_response_id: str | None
    output_text: str
    finish_reason: str | None = None


class OpenAIResponsesProviderAdapter:
    """Provider adapter that is the only OpenAI-aware runtime component."""

    def __init__(self, client: Any | None = None) -> None:
        self._client = client

    def invoke(self, request: RuntimeRequest, config: RuntimeAdapterConfig) -> OpenAIProviderResult:
        client = self._client or OpenAI()
        provider_request = self._build_provider_request(request, config)
        response = client.responses.create(**provider_request)
        provider_response_id = getattr(response, "id", None)
        output_text = getattr(response, "output_text", "") or ""
        finish_reason = getattr(response, "finish_reason", None)
        return OpenAIProviderResult(
            provider_name="openai",
            provider_response_id=provider_response_id,
            output_text=output_text,
            finish_reason=finish_reason,
        )

    def _build_provider_request(self, request: RuntimeRequest, config: RuntimeAdapterConfig) -> dict[str, Any]:
        input_value = request.input_payload.get("input", request.input_payload.get("prompt"))
        if input_value is None:
            raise ValueError("RuntimeRequest.input_payload must include 'input' or 'prompt'.")

        session_mode = request.session_mode_override or config.session.session_mode
        store = False
        if session_mode == SessionMode.DURABLE_OPTIONAL:
            store = config.session.store_enabled

        provider_request: dict[str, Any] = {
            "model": config.model.model_name,
            "input": input_value,
            "store": store,
        }
        instructions = request.input_payload.get("instructions")
        if instructions is not None:
            provider_request["instructions"] = instructions
        if request.continuation and request.continuation.previous_response_id:
            provider_request["previous_response_id"] = request.continuation.previous_response_id
        return provider_request
