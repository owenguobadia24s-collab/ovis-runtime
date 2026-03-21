# ---
# id: MODULE-EVENT-0005
# title: Constants Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: event
# repo: ovis-runtime
# path: src/ovis_event_log/constants.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-EVENT-0005.yaml
# module_id: MOD-EVENT-LOG-0001
# module_slug: event_log
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Canonical event family groupings derived from the shared EventType enum."""

from __future__ import annotations

from ovis_state_models.enums import EventType

SIGNAL_EVENT_FAMILIES = (
    EventType.SIGNAL_CREATED,
    EventType.SIGNAL_COMPRESSED,
)

BRANCH_EVENT_FAMILIES = (
    EventType.BRANCH_CREATED,
    EventType.BRANCH_EVENT_APPENDED,
    EventType.BRANCH_CLOSED,
)

WORK_OBJECT_EVENT_FAMILIES = (
    EventType.WORK_OBJECT_CREATED,
    EventType.WORK_OBJECT_UPDATED,
)

PLAN_EVENT_FAMILIES = (
    EventType.PLAN_JOB_CREATED,
    EventType.APPROVAL_RECORDED,
)

EXECUTION_EVENT_FAMILIES = (
    EventType.EXECUTE_JOB_CREATED,
    EventType.EXECUTE_JOB_STATUS_CHANGED,
)

CAPABILITY_EVENT_FAMILIES = (
    EventType.CAPABILITY_REQUESTED,
    EventType.CAPABILITY_COMPLETED,
    EventType.CAPABILITY_ERROR,
)

RUNTIME_EVENT_FAMILIES = (
    EventType.RUNTIME_REQUESTED,
    EventType.RUNTIME_RESPONSE_RECEIVED,
    EventType.RUNTIME_ERROR,
)

BRIDGE_EVENT_FAMILIES = (
    EventType.BRIDGE_ACTION_DISPATCHED,
    EventType.BRIDGE_ACTION_COMPLETED,
    EventType.BRIDGE_ACTION_FAILED,
)

COMPACTION_EVENT_FAMILIES = (
    EventType.COMPACTION_CREATED,
)
