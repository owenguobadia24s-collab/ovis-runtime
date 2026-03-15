"""Validation helpers for append-only event logging."""

from __future__ import annotations

from ovis_state_models import Event


def _validate_prefix(field_name: str, value: str, prefix: str) -> None:
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must use the canonical {prefix} prefix.")


def validate_event_for_append(event: Event) -> None:
    """Validate that an event is append-ready under the scaffold contract."""

    if not isinstance(event, Event):
        raise TypeError("append-only validation requires a canonical Event instance.")
    if not event.event_id:
        raise ValueError("Event requires an event_id.")
    _validate_prefix("event_id", str(event.event_id), "evt_")
    if not event.correlation_id:
        raise ValueError("Event requires a correlation_id.")
    _validate_prefix("correlation_id", str(event.correlation_id), "corr_")
    if not event.branch_id:
        raise ValueError("Event requires a branch_id.")
    _validate_prefix("branch_id", str(event.branch_id), "br_")
    if not event.created_at:
        raise ValueError("Event requires created_at.")
    if not event.payload_ref and not event.payload_hash:
        raise ValueError("Event requires payload_ref or payload_hash.")
    if event.parent_event_id == event.event_id:
        raise ValueError("Event cannot reference itself as parent_event_id.")


def is_event_append_ready(event: object) -> bool:
    """Return whether an event passes append-only readiness checks."""

    try:
        validate_event_for_append(event)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return True
