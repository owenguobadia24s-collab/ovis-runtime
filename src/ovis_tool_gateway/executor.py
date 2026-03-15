"""Execution wrapper interfaces for the scaffolded tool gateway."""

from __future__ import annotations

from typing import Protocol

from .types import ExecutionRequest, ExecutionResultEnvelope


class ExecutionWrapper(Protocol):
    def execute(self, request: ExecutionRequest) -> ExecutionResultEnvelope:
        """Execute a capability request through the gateway wrapper."""


class PlaceholderExecutionWrapper:
    """Placeholder-only execution wrapper."""

    def execute(self, request: ExecutionRequest) -> ExecutionResultEnvelope:
        raise NotImplementedError("CJ-001 scaffold only: no execution dispatch implementation.")
