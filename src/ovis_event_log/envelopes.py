"""Thin helpers for constructing canonical event envelopes."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from ovis_state_models import ActorType, BranchId, CorrelationId, Event, EventId, EventType, ObjectType

from .linkage import derive_child_event_linkage


def _normalize_event_type(value: EventType | str) -> EventType:
    return value if isinstance(value, EventType) else EventType(value)


def _normalize_object_type(value: ObjectType | str) -> ObjectType:
    return value if isinstance(value, ObjectType) else ObjectType(value)


def _normalize_actor_type(value: ActorType | str) -> ActorType:
    return value if isinstance(value, ActorType) else ActorType(value)


def build_root_event(
    *,
    event_id: EventId,
    event_type: EventType | str,
    correlation_id: CorrelationId,
    object_type: ObjectType | str,
    object_id: str,
    branch_id: BranchId,
    actor_type: ActorType | str,
    actor_id: str,
    created_at: datetime,
    payload_ref: str | None = None,
    payload_hash: str | None = None,
    payload_inline: Mapping[str, Any] | None = None,
) -> Event:
    """Construct a canonical root event with explicit branch and correlation context."""

    return Event(
        event_id=event_id,
        event_type=_normalize_event_type(event_type),
        correlation_id=correlation_id,
        object_type=_normalize_object_type(object_type),
        object_id=object_id,
        branch_id=branch_id,
        actor_type=_normalize_actor_type(actor_type),
        actor_id=actor_id,
        payload_ref=payload_ref,
        payload_hash=payload_hash,
        payload_inline=payload_inline,
        created_at=created_at,
    )


def build_child_event(
    *,
    parent_event: Event,
    event_id: EventId,
    event_type: EventType | str,
    object_type: ObjectType | str,
    object_id: str,
    actor_type: ActorType | str,
    actor_id: str,
    created_at: datetime,
    payload_ref: str | None = None,
    payload_hash: str | None = None,
    payload_inline: Mapping[str, Any] | None = None,
) -> Event:
    """Construct a canonical child event that inherits parent lineage by default."""

    linkage = derive_child_event_linkage(parent_event)
    return Event(
        event_id=event_id,
        event_type=_normalize_event_type(event_type),
        correlation_id=linkage["correlation_id"],
        parent_event_id=linkage["parent_event_id"],
        object_type=_normalize_object_type(object_type),
        object_id=object_id,
        branch_id=linkage["branch_id"],
        actor_type=_normalize_actor_type(actor_type),
        actor_id=actor_id,
        payload_ref=payload_ref,
        payload_hash=payload_hash,
        payload_inline=payload_inline,
        created_at=created_at,
    )
