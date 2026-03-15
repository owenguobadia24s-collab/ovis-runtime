"""Append-only event log utility package for canonical OVIS events."""

from .constants import (
    BRIDGE_EVENT_FAMILIES,
    COMPACTION_EVENT_FAMILIES,
    EXECUTION_EVENT_FAMILIES,
    PLAN_EVENT_FAMILIES,
    SIGNAL_EVENT_FAMILIES,
    WORK_OBJECT_EVENT_FAMILIES,
)
from .envelopes import build_child_event, build_root_event
from .linkage import derive_child_event_linkage, has_correlation_continuity, validate_parent_child_linkage
from .validation import is_event_append_ready, validate_event_for_append
from .writer import AppendOnlyEventWriter, EventAppendReceipt, PlaceholderAppendOnlyEventWriter

__all__ = [
    "AppendOnlyEventWriter",
    "BRIDGE_EVENT_FAMILIES",
    "COMPACTION_EVENT_FAMILIES",
    "EXECUTION_EVENT_FAMILIES",
    "EventAppendReceipt",
    "PLAN_EVENT_FAMILIES",
    "PlaceholderAppendOnlyEventWriter",
    "SIGNAL_EVENT_FAMILIES",
    "WORK_OBJECT_EVENT_FAMILIES",
    "build_child_event",
    "build_root_event",
    "derive_child_event_linkage",
    "has_correlation_continuity",
    "is_event_append_ready",
    "validate_event_for_append",
    "validate_parent_child_linkage",
]
