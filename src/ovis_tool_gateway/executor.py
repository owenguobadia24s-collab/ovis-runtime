# ---
# id: MODULE-GATEWAY-0005
# title: Executor Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gateway
# repo: ovis-runtime
# path: src/ovis_tool_gateway/executor.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GATEWAY-0005.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
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
