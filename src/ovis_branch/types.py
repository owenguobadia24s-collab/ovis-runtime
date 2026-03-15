"""Thin lifecycle types for canonical branch management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from ovis_state_models import Branch


class BranchStatus(StrEnum):
    """Minimum canonical status surface for the first branch lifecycle."""

    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True)
class CreateBranchInput:
    """Explicit branch creation input when no canonical Signal instance is passed."""

    root_signal_id: str
    correlation_id: str | None = None
    current_state_ref: str | None = None


@dataclass(frozen=True)
class BranchEventReference:
    """Thin append-order-preserving reference to an event linked to a branch."""

    event_id: str
    event_type: str | None = None
    created_at: datetime | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class BranchState:
    """Public read surface for branch lifecycle state."""

    branch: Branch
    correlation_id: str | None
    event_refs: tuple[BranchEventReference, ...]
    latest_event: BranchEventReference | None
