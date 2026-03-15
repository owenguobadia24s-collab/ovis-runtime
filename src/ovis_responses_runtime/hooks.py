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
