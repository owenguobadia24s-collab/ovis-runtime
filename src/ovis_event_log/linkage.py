# ---
# id: MODULE-EVENT-0009
# title: Linkage Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: event
# repo: ovis-runtime
# path: src/ovis_event_log/linkage.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-EVENT-0009.yaml
# module_id: MOD-EVENT-LOG-0001
# module_slug: event_log
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Helpers for parent-event and correlation linkage."""

from __future__ import annotations

from ovis_state_models import Event


def derive_child_event_linkage(parent_event: Event) -> dict[str, object]:
    """Derive child-event lineage fields from a parent event."""

    return {
        "correlation_id": parent_event.correlation_id,
        "branch_id": parent_event.branch_id,
        "parent_event_id": parent_event.event_id,
    }


def has_correlation_continuity(parent_event: Event, child_event: Event) -> bool:
    """Return whether the child preserves the parent's correlation lineage."""

    return child_event.correlation_id == parent_event.correlation_id


def validate_parent_child_linkage(parent_event: Event, child_event: Event) -> None:
    """Validate canonical parent-child event linkage."""

    if child_event.parent_event_id != parent_event.event_id:
        raise ValueError("Child event must link to the parent's event_id.")
    if child_event.parent_event_id == child_event.event_id:
        raise ValueError("Child event cannot reference itself as parent_event_id.")
    if child_event.branch_id != parent_event.branch_id:
        raise ValueError("Child event must preserve the parent's branch_id.")
    if not has_correlation_continuity(parent_event, child_event):
        raise ValueError("Child event must preserve the parent's correlation_id.")
