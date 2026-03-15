"""Policy hook placeholder interfaces for the OVIS tool gateway."""

from __future__ import annotations

from typing import Protocol

from .types import ExecutionRequest, PolicyDecision


class PolicyHook(Protocol):
    def evaluate(self, request: ExecutionRequest) -> PolicyDecision:
        """Evaluate a request before execution."""


class PlaceholderPolicyHook:
    """Placeholder-only policy hook."""

    def evaluate(self, request: ExecutionRequest) -> PolicyDecision:
        raise NotImplementedError("CJ-001 scaffold only: no policy evaluation implementation.")
