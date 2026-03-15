"""Canonical PlanJob model."""

from __future__ import annotations

from ..base import OvisBaseModel, Timestamp
from ..enums import PlanJobStatus
from ..ids import PlanJobId, WorkObjectId


class PlanJob(OvisBaseModel):
    plan_job_id: PlanJobId
    work_object_id: WorkObjectId
    status: PlanJobStatus
    objective: str
    assumptions: tuple[str, ...]
    constraints: tuple[str, ...]
    output_ref: str | None
    created_at: Timestamp
    updated_at: Timestamp
