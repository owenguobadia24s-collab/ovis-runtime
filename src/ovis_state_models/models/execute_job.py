"""Canonical ExecuteJob model."""

from __future__ import annotations

from ..base import OvisBaseModel, Timestamp
from ..enums import ExecuteJobStatus
from ..ids import ExecuteJobId, PlanJobId, WorkObjectId


class ExecuteJob(OvisBaseModel):
    execute_job_id: ExecuteJobId
    work_object_id: WorkObjectId
    parent_plan_job_id: PlanJobId
    status: ExecuteJobStatus
    job_kind: str
    execution_profile: str
    input_ref: str | None
    output_ref: str | None
    run_id: str | None
    created_at: Timestamp
    updated_at: Timestamp
