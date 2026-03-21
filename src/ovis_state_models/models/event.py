# ---
# id: MODULE-STATE-0012
# title: Event Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: src/ovis_state_models/models/event.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-STATE-0012.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Canonical Event model."""

from __future__ import annotations

import json
from typing import Any, Mapping

from pydantic import model_validator

from ..base import OvisBaseModel, Timestamp
from ..enums import ActorType, EventType, ObjectType
from ..ids import BranchId, CorrelationId, EventId


class Event(OvisBaseModel):
    event_id: EventId
    event_type: EventType
    correlation_id: CorrelationId
    parent_event_id: EventId | None = None
    object_type: ObjectType
    object_id: str
    branch_id: BranchId
    actor_type: ActorType
    actor_id: str
    payload_ref: str | None = None
    payload_hash: str | None = None
    payload_inline: Mapping[str, Any] | None = None
    created_at: Timestamp

    @model_validator(mode="after")
    def validate_payload_locator(self) -> "Event":
        if not self.payload_ref and not self.payload_hash and self.payload_inline is None:
            raise ValueError("Event requires payload_ref, payload_hash, or payload_inline.")
        if self.payload_inline is not None:
            try:
                json.dumps(self.payload_inline, sort_keys=True, separators=(",", ":"))
            except TypeError as exc:
                raise ValueError("Event payload_inline must be JSON-serializable.") from exc
        return self
