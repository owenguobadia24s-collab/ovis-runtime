# ---
# id: MODULE-EVENT-0001
# title: Ovis Event Log Package Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: event
# repo: ovis-runtime
# path: src/ovis_event_log/__init__.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-EVENT-0001.yaml
# module_id: MOD-EVENT-LOG-0001
# module_slug: event_log
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Append-only event log utility package for canonical OVIS events."""

from .backends import FileEventWriter, MemoryEventWriter
from .constants import (
    BRANCH_EVENT_FAMILIES,
    BRIDGE_EVENT_FAMILIES,
    CAPABILITY_EVENT_FAMILIES,
    COMPACTION_EVENT_FAMILIES,
    EXECUTION_EVENT_FAMILIES,
    PLAN_EVENT_FAMILIES,
    RUNTIME_EVENT_FAMILIES,
    SIGNAL_EVENT_FAMILIES,
    WORK_OBJECT_EVENT_FAMILIES,
)
from .emit import emit_event
from .envelopes import build_child_event, build_root_event
from .hash import compute_event_hash
from .linkage import derive_child_event_linkage, has_correlation_continuity, validate_parent_child_linkage
from .validation import is_event_append_ready, validate_event_for_append
from .writer import AppendOnlyEventWriter, EventAppendReceipt, PlaceholderAppendOnlyEventWriter

__all__ = [
    "AppendOnlyEventWriter",
    "BRANCH_EVENT_FAMILIES",
    "BRIDGE_EVENT_FAMILIES",
    "CAPABILITY_EVENT_FAMILIES",
    "COMPACTION_EVENT_FAMILIES",
    "EXECUTION_EVENT_FAMILIES",
    "EventAppendReceipt",
    "FileEventWriter",
    "MemoryEventWriter",
    "PLAN_EVENT_FAMILIES",
    "PlaceholderAppendOnlyEventWriter",
    "RUNTIME_EVENT_FAMILIES",
    "SIGNAL_EVENT_FAMILIES",
    "WORK_OBJECT_EVENT_FAMILIES",
    "build_child_event",
    "build_root_event",
    "compute_event_hash",
    "derive_child_event_linkage",
    "emit_event",
    "has_correlation_continuity",
    "is_event_append_ready",
    "validate_event_for_append",
    "validate_parent_child_linkage",
]
