# ---
# id: MODULE-STATE-0014
# title: Plan Job Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: src/ovis_state_models/models/plan_job.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-STATE-0014.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
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
