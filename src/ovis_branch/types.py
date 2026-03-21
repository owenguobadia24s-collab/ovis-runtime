# ---
# id: MODULE-BRANCH-0004
# title: Types Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: branch
# repo: ovis-runtime
# path: src/ovis_branch/types.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-BRANCH-0004.yaml
# module_id: MOD-BRANCH-CONTINUITY-0001
# module_slug: branch_continuity
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# related_module_ids:
# - MOD-EVENT-LOG-0001
# ---
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
