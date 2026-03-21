# ---
# id: MODULE-STATE-0011
# title: Compaction Record Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: src/ovis_state_models/models/compaction_record.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-STATE-0011.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Canonical CompactionRecord model."""

from __future__ import annotations

from ..base import OvisBaseModel, Timestamp
from ..ids import BranchId, CompactionId
from ..references import ObjectRef


class CompactionRecord(OvisBaseModel):
    compaction_id: CompactionId
    branch_id: BranchId
    source_range: str
    compacted_state_ref: str
    preserved_reference_index: tuple[ObjectRef, ...]
    created_at: Timestamp
