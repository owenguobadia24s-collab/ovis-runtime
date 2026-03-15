"""Canonical WorkObject model."""

from __future__ import annotations

from ..base import OvisBaseModel, Timestamp
from ..enums import WorkObjectStatus
from ..ids import BranchId, ExecuteJobId, PlanJobId, SignalId, WorkObjectId


class WorkObject(OvisBaseModel):
    work_object_id: WorkObjectId
    title: str
    objective: str
    status: WorkObjectStatus
    priority: str
    branch_id: BranchId
    parent_signal_ids: tuple[SignalId, ...]
    dependency_ids: tuple[WorkObjectId, ...] = ()
    current_plan_id: PlanJobId | None = None
    current_execute_job_id: ExecuteJobId | None = None
    owner: str
    created_at: Timestamp
    updated_at: Timestamp
