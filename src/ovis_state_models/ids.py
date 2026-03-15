"""Canonical ID aliases for OVIS state models."""

from __future__ import annotations

from typing import NewType
from uuid import uuid4

SignalId = NewType("SignalId", str)
WorkObjectId = NewType("WorkObjectId", str)
PlanJobId = NewType("PlanJobId", str)
ApprovalId = NewType("ApprovalId", str)
ExecuteJobId = NewType("ExecuteJobId", str)
EventId = NewType("EventId", str)
BridgeActionId = NewType("BridgeActionId", str)
BranchId = NewType("BranchId", str)
CompactionId = NewType("CompactionId", str)
CorrelationId = NewType("CorrelationId", str)


def generate_prefixed_id(prefix: str) -> str:
    """Generate a canonical prefixed OVIS ID using a lowercase UUID4 suffix."""

    return f"{prefix}{uuid4()}"


def generate_event_id() -> EventId:
    """Generate a canonical event_id."""

    return EventId(generate_prefixed_id("evt_"))


def generate_branch_id() -> BranchId:
    """Generate a canonical branch_id."""

    return BranchId(generate_prefixed_id("br_"))
