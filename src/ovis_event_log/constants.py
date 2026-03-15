"""Canonical event family groupings derived from the shared EventType enum."""

from __future__ import annotations

from ovis_state_models.enums import EventType

SIGNAL_EVENT_FAMILIES = (
    EventType.SIGNAL_CREATED,
    EventType.SIGNAL_COMPRESSED,
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

BRIDGE_EVENT_FAMILIES = (
    EventType.BRIDGE_ACTION_DISPATCHED,
    EventType.BRIDGE_ACTION_COMPLETED,
    EventType.BRIDGE_ACTION_FAILED,
)

COMPACTION_EVENT_FAMILIES = (
    EventType.COMPACTION_CREATED,
)
