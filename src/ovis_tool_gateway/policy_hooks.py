# ---
# id: MODULE-GATEWAY-0006
# title: Policy Hooks Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gateway
# repo: ovis-runtime
# path: src/ovis_tool_gateway/policy_hooks.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GATEWAY-0006.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
"""Policy hook placeholder interfaces for the OVIS tool gateway."""

from __future__ import annotations

from typing import Protocol

from .types import CapabilityDefinition
from .types import ExecutionRequest, PolicyDecision


class PolicyHook(Protocol):
    def evaluate(self, request: ExecutionRequest, definition: CapabilityDefinition) -> PolicyDecision:
        """Evaluate a request before execution."""


class PlaceholderPolicyHook:
    """Placeholder-only policy hook."""

    def evaluate(self, request: ExecutionRequest, definition: CapabilityDefinition) -> PolicyDecision:
        raise NotImplementedError("CJ-001 scaffold only: no policy evaluation implementation.")
