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
