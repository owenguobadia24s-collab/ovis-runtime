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
