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
