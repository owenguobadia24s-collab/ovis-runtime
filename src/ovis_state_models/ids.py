"""Canonical ID aliases for OVIS state models."""

from __future__ import annotations

from typing import NewType

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
