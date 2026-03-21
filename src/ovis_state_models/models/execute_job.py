# ---
# id: MODULE-STATE-0013
# title: Execute Job Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: src/ovis_state_models/models/execute_job.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-STATE-0013.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
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
