# ---
# id: MODULE-STATE-0017
# title: References Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: src/ovis_state_models/references.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-STATE-0017.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Shared reference and context models for OVIS state objects."""

from __future__ import annotations

from .base import OvisBaseModel
from .enums import ObjectType
from .ids import BranchId, CorrelationId


class ObjectRef(OvisBaseModel):
    """Reference to another canonical object."""

    object_type: ObjectType
    object_id: str


class BranchContext(OvisBaseModel):
    """Branch continuity context."""

    branch_id: BranchId


class CorrelationContext(OvisBaseModel):
    """Correlation context for lineage and audit."""

    correlation_id: CorrelationId
