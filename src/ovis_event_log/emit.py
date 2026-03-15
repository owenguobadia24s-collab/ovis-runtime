"""Minimal append-only event emission helper."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime

from ovis_state_models import Event

from .hash import compute_event_hash
from .validation import validate_event_for_append
from .writer import AppendOnlyEventWriter, PersistedEventRecord, normalize_event_for_persistence


def emit_event(event: Event, writer: AppendOnlyEventWriter) -> PersistedEventRecord:
    """Validate, emit, and return the persisted event record."""

    event_to_emit = event
    if getattr(event_to_emit, "created_at", None) is None:
        event_to_emit = event_to_emit.model_copy(update={"created_at": datetime.now(UTC)})

    validate_event_for_append(event_to_emit)
    record = normalize_event_for_persistence(event_to_emit)
    record["hash"] = compute_event_hash(record)
    writer.append(event_to_emit)

    if hasattr(writer, "get_last_persisted_record"):
        persisted_record = writer.get_last_persisted_record()
        if persisted_record is None:
            raise RuntimeError("Writer did not expose the persisted event record.")
        return deepcopy(persisted_record)

    raise TypeError("emit_event requires a writer that exposes the last persisted record.")
