"""Canonical Event model."""

from __future__ import annotations

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
    created_at: Timestamp

    @model_validator(mode="after")
    def validate_payload_locator(self) -> "Event":
        if not self.payload_ref and not self.payload_hash:
            raise ValueError("Event requires payload_ref or payload_hash.")
        return self
