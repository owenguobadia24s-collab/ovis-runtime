"""Canonical Responses runtime adapter interfaces."""

from __future__ import annotations

from typing import Protocol

from .types import RuntimeRequest, RuntimeResponse


class ResponsesRuntimeAdapter(Protocol):
    """Canonical runtime adapter boundary for governed model invocation."""

    def invoke(self, request: RuntimeRequest) -> RuntimeResponse:
        """Invoke the runtime adapter with an explicit governed request."""


class PlaceholderResponsesRuntimeAdapter:
    """Placeholder-only adapter with no provider behavior."""

    def invoke(self, request: RuntimeRequest) -> RuntimeResponse:
        raise NotImplementedError("CJ-004 scaffold only: no Responses runtime implementation.")
