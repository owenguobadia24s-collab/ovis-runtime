# ---
# id: MODULE-RUNTIME-0005
# title: Hooks Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: runtime
# repo: ovis-runtime
# path: src/ovis_responses_runtime/hooks.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-RUNTIME-0005.yaml
# module_id: MOD-RUNTIME-GATEWAY-0001
# module_slug: runtime_gateway
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Hook containers for event emission and future gateway integration."""

from __future__ import annotations

from dataclasses import dataclass

from ovis_event_log.writer import AppendOnlyEventWriter
from ovis_tool_gateway.executor import ExecutionWrapper


@dataclass(frozen=True)
class RuntimeHooks:
    """Attach optional event and gateway hooks without executing them."""

    event_writer: AppendOnlyEventWriter | None = None
    gateway_executor: ExecutionWrapper | None = None
