# ---
# id: MODULE-STATE-0009
# title: Branch Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: src/ovis_state_models/models/branch.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-STATE-0009.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Canonical Branch model."""

from __future__ import annotations

from ..base import OvisBaseModel, Timestamp
from ..ids import BranchId, CompactionId, SignalId


class Branch(OvisBaseModel):
    branch_id: BranchId
    root_signal_id: SignalId
    current_state_ref: str
    latest_compaction_id: CompactionId | None = None
    status: str
    created_at: Timestamp
    updated_at: Timestamp
