"""Canonical Signal model."""

from __future__ import annotations

from pydantic import model_validator

from ..base import OvisBaseModel, Timestamp
from ..ids import BranchId, SignalId


class Signal(OvisBaseModel):
    signal_id: SignalId
    source_type: str
    source_ref: str
    raw_input_ref: str | None = None
    raw_input_hash: str | None = None
    compressed_summary: str
    extracted_signals: tuple[str, ...]
    nuance: str | None = None
    branch_id: BranchId
    created_at: Timestamp
    created_by: str

    @model_validator(mode="after")
    def validate_raw_input_locator(self) -> "Signal":
        if not self.raw_input_ref and not self.raw_input_hash:
            raise ValueError("Signal requires raw_input_ref or raw_input_hash.")
        return self
