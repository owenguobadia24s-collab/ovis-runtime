# ---
# id: MODULE-STATE-0019
# title: Transitions Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: src/ovis_state_models/validators/transitions.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-STATE-0019.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Pure transition validation helpers for canonical OVIS statuses."""

from __future__ import annotations

from collections.abc import Mapping

from ..enums import BridgeActionStatus, ExecuteJobStatus, PlanJobStatus, WorkObjectStatus

WORK_OBJECT_TRANSITIONS: Mapping[WorkObjectStatus, frozenset[WorkObjectStatus]] = {
    WorkObjectStatus.INBOX: frozenset({WorkObjectStatus.ROUTED, WorkObjectStatus.BLOCKED}),
    WorkObjectStatus.ROUTED: frozenset({WorkObjectStatus.PLANNING, WorkObjectStatus.BLOCKED}),
    WorkObjectStatus.PLANNING: frozenset({WorkObjectStatus.AWAITING_REVIEW, WorkObjectStatus.BLOCKED}),
    WorkObjectStatus.AWAITING_REVIEW: frozenset({WorkObjectStatus.APPROVED, WorkObjectStatus.BLOCKED}),
    WorkObjectStatus.APPROVED: frozenset({WorkObjectStatus.EXECUTING, WorkObjectStatus.BLOCKED}),
    WorkObjectStatus.EXECUTING: frozenset(
        {WorkObjectStatus.COMPLETED, WorkObjectStatus.FAILED, WorkObjectStatus.BLOCKED}
    ),
    WorkObjectStatus.BLOCKED: frozenset(
        {
            WorkObjectStatus.ROUTED,
            WorkObjectStatus.PLANNING,
            WorkObjectStatus.AWAITING_REVIEW,
            WorkObjectStatus.APPROVED,
            WorkObjectStatus.EXECUTING,
            WorkObjectStatus.FAILED,
            WorkObjectStatus.ARCHIVED,
        }
    ),
    WorkObjectStatus.COMPLETED: frozenset({WorkObjectStatus.ARCHIVED}),
    WorkObjectStatus.FAILED: frozenset({WorkObjectStatus.BLOCKED}),
    WorkObjectStatus.ARCHIVED: frozenset(),
}

PLAN_JOB_TRANSITIONS: Mapping[PlanJobStatus, frozenset[PlanJobStatus]] = {
    PlanJobStatus.DRAFT: frozenset({PlanJobStatus.READY_FOR_REVIEW, PlanJobStatus.SUPERSEDED}),
    PlanJobStatus.READY_FOR_REVIEW: frozenset(
        {PlanJobStatus.APPROVED, PlanJobStatus.REJECTED, PlanJobStatus.SUPERSEDED}
    ),
    PlanJobStatus.APPROVED: frozenset({PlanJobStatus.SUPERSEDED}),
    PlanJobStatus.REJECTED: frozenset({PlanJobStatus.DRAFT, PlanJobStatus.SUPERSEDED}),
    PlanJobStatus.SUPERSEDED: frozenset(),
}

EXECUTE_JOB_TRANSITIONS: Mapping[ExecuteJobStatus, frozenset[ExecuteJobStatus]] = {
    ExecuteJobStatus.DRAFT: frozenset({ExecuteJobStatus.PLANNED, ExecuteJobStatus.CANCELLED}),
    ExecuteJobStatus.PLANNED: frozenset({ExecuteJobStatus.READY, ExecuteJobStatus.CANCELLED}),
    ExecuteJobStatus.READY: frozenset({ExecuteJobStatus.RUNNING, ExecuteJobStatus.CANCELLED}),
    ExecuteJobStatus.RUNNING: frozenset(
        {ExecuteJobStatus.REVIEW, ExecuteJobStatus.COMPLETED, ExecuteJobStatus.FAILED}
    ),
    ExecuteJobStatus.REVIEW: frozenset(
        {ExecuteJobStatus.COMPLETED, ExecuteJobStatus.FAILED, ExecuteJobStatus.CANCELLED}
    ),
    ExecuteJobStatus.COMPLETED: frozenset(),
    ExecuteJobStatus.FAILED: frozenset({ExecuteJobStatus.CANCELLED}),
    ExecuteJobStatus.CANCELLED: frozenset(),
}

BRIDGE_ACTION_TRANSITIONS: Mapping[BridgeActionStatus, frozenset[BridgeActionStatus]] = {
    BridgeActionStatus.PENDING: frozenset(
        {BridgeActionStatus.DISPATCHED, BridgeActionStatus.CANCELLED}
    ),
    BridgeActionStatus.DISPATCHED: frozenset(
        {
            BridgeActionStatus.ACKNOWLEDGED,
            BridgeActionStatus.FAILED,
            BridgeActionStatus.CANCELLED,
        }
    ),
    BridgeActionStatus.ACKNOWLEDGED: frozenset(),
    BridgeActionStatus.FAILED: frozenset(),
    BridgeActionStatus.CANCELLED: frozenset(),
}


def is_allowed_transition(
    current_status: WorkObjectStatus | PlanJobStatus | ExecuteJobStatus | BridgeActionStatus,
    next_status: WorkObjectStatus | PlanJobStatus | ExecuteJobStatus | BridgeActionStatus,
) -> bool:
    """Return whether a transition is allowed for the matching status family."""

    transition_maps = (
        WORK_OBJECT_TRANSITIONS,
        PLAN_JOB_TRANSITIONS,
        EXECUTE_JOB_TRANSITIONS,
        BRIDGE_ACTION_TRANSITIONS,
    )
    for transition_map in transition_maps:
        if current_status in transition_map:
            return next_status in transition_map[current_status]
    return False
