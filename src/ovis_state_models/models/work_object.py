# ---
# id: MODULE-STATE-0016
# title: Work Object Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: src/ovis_state_models/models/work_object.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-STATE-0016.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
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
