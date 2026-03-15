"""Append-only event writer interfaces for the scaffold."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from ovis_state_models import Event


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
