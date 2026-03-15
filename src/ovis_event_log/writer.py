"""Append-only event writer interfaces and internal persistence helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from ovis_state_models import Event

PersistedEventRecord = dict[str, object]


def normalize_event_for_persistence(event: Event) -> PersistedEventRecord:
    """Project a canonical Event into the persisted JSONL record shape."""

    created_at = event.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    else:
        created_at = created_at.astimezone(UTC)

    return {
        "event_id": str(event.event_id),
        "event_type": str(event.event_type),
        "timestamp": created_at.isoformat(),
        "correlation_id": str(event.correlation_id),
        "branch_id": str(event.branch_id),
        "payload": {
            "parent_event_id": str(event.parent_event_id) if event.parent_event_id is not None else None,
            "object_type": str(event.object_type),
            "object_id": event.object_id,
            "actor_type": str(event.actor_type),
            "actor_id": event.actor_id,
            "payload_ref": event.payload_ref,
            "payload_hash": event.payload_hash,
            "payload_inline": dict(event.payload_inline) if event.payload_inline is not None else None,
        },
    }


@dataclass(frozen=True)
class EventAppendReceipt:
    event_id: str
    correlation_id: str
    object_type: str
    object_id: str
    created_at: object


class AppendOnlyEventWriter(Protocol):
    """Append-only writer interface for canonical Event instances."""

    def append(self, event: Event) -> EventAppendReceipt:
        """Append one canonical event."""

    def append_many(self, events: Sequence[Event]) -> tuple[EventAppendReceipt, ...]:
        """Append a small correlated batch of canonical events."""


class PlaceholderAppendOnlyEventWriter:
    """Explicitly unimplemented scaffold writer."""

    def append(self, event: Event) -> EventAppendReceipt:
        raise NotImplementedError("CJ-003 scaffold only: no persistence backend is implemented.")

    def append_many(self, events: Sequence[Event]) -> tuple[EventAppendReceipt, ...]:
        raise NotImplementedError("CJ-003 scaffold only: no persistence backend is implemented.")


def build_event_append_receipt(record: PersistedEventRecord) -> EventAppendReceipt:
    """Build the stable public receipt from a persisted event record."""

    payload = record["payload"]
    assert isinstance(payload, dict)
    return EventAppendReceipt(
        event_id=str(record["event_id"]),
        correlation_id=str(record["correlation_id"]),
        object_type=str(payload["object_type"]),
        object_id=str(payload["object_id"]),
        created_at=record["timestamp"],
    )


class LastPersistedRecordProvider(Protocol):
    """Internal helper for emit_event to recover the last persisted record."""

    def get_last_persisted_record(self) -> PersistedEventRecord | None:
        """Return the last persisted event record if available."""
